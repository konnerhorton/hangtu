"""E50, ε50 and Rf from triaxial readings (docs/analysis/stiffness.md §1-2)."""

import math
from collections.abc import Mapping
from typing import NamedTuple

import numpy as np
import pandas as pd

from hangtu.analysis._line_fit import line_fit
from hangtu.analysis._triaxial_readings import (
    Readings,
    _name,
    _warn_interpolated,
    check_strain_units,
    reduce_readings,
)
from hangtu.errors import HangtuError, warn

MODULUS = "secant_modulus_at_50_percent_peak"
STRAIN = "axial_strain_at_50_percent_peak"
MODULUS_REASON = "secant_modulus_at_50_percent_peak_reason"
RATIO = "failure_ratio"
ASYMPTOTE = "asymptotic_deviator_stress"
R_SQUARED = "failure_ratio_r_squared"
RATIO_REASON = "failure_ratio_reason"
#: The fewest readings the hyperbola is fitted to.
FEWEST = 3


def triaxial_stiffness_from_readings(
    df: pd.DataFrame,
    *,
    failure_criterion: str | None = None,
    failure_ratio_range: tuple[float, float] = (0.7, 0.95),
    units: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    r"""Read each triaxial stage's E50, ε50 and failure ratio Rf from its readings.

    Takes the readings during shearing, as ``p.triaxial_readings()`` or
    ``ht.template("triaxial_readings")`` lays them out, and returns
    ``ht.analysis.triaxial_failure_from_readings()``'s rows, one per stage,
    with the same ``failure_criterion=``, with the secant modulus, the strain
    it was read at, and the failure ratio of the hyperbola fitted to the curve
    added. The stages, their loading parts and the failure readings are the
    ones ``triaxial_failure_from_readings()`` and ``ht.plot.triaxial_shearing()``
    use (the failure analysis's docstring says how each is found).

    **The origin** is $(\varepsilon_1 = 0, q_0)$: $q_0$ is the deviator stress
    of the stage's first loading-part reading at zero strain, or 0 where it has
    none. On an isotropic stage $q_0 = 0$; on an anisotropically consolidated
    one whose lab gives $q$ from the consolidated state, measuring from $q_0$
    is Obrzud & Truty's $q_m = q - q_0$ (2018, Eqs. 2.12-2.14).

    **E50, the secant modulus at half the peak** (PLAXIS 2D 2026.1 Material
    Models Manual, §6.1, Eqs. 6-3 and 6-4 and Fig. 6-1, pp. 68-69). The peak
    $q_p$ is the largest $q$ of the stage's loading part (the first reading at
    it on a tie), whatever the failure criterion: that is E50's definition, and
    the one labs report it by (AGS ``TRET_E50``, "50 % peak deviator stress"),
    so on a stage failed by the stress ratio it is not the failure reading.

    $$
    q_{50} = q_0 + \frac{q_p - q_0}{2}, \qquad
    E_{50} = \frac{q_{50} - q_0}{\varepsilon_{50}}
    $$

    with $\varepsilon_{50}$ interpolated linearly between the last loading-part
    reading below $q_{50}$ before the peak and the next one, and taken as a
    fraction. A chord stands in for the curve between two readings, so E50
    differs from a smooth curve's by about 1 % at typical reading spacing: it
    is the method, not an error. A stage whose $q$ never rises above $q_0$, or
    with no reading below $q_{50}$ (a curve without its zero reading, whose
    first reading is already past half the peak), gets no E50 and a reason:
    nothing is extrapolated to an origin the lab didn't read.

    **Rf, the failure ratio** (PLAXIS 2026.1, Eqs. 6-3 and 6-6, p. 69).
    The hyperbola $\varepsilon_1 = (1/E_i)\, q / (1 - q/q_a)$ rearranges to a
    line, $\varepsilon_1 / q = 1/E_i + \varepsilon_1 / q_a$ (Obrzud & Truty
    2018, Eq. 2.11). With $q$ measured from $q_0$, the line is fitted by
    ordinary least squares to the loading-part readings up to the failure
    reading with

    $$
    r_{lo} \le \frac{q - q_0}{q_f - q_0} \le r_{hi}, \qquad
    q_a = \frac{1}{b}, \qquad R_f = \frac{q_f - q_0}{q_a}
    $$

    $b$ the line's slope, $q_f$ the failure reading's $q$ and
    $(r_{lo}, r_{hi})$ ``failure_ratio_range``. Only the slope is used: the
    sources disagree on the intercept (PLAXIS Eq. 6-4 gives
    $(2 - R_f)/(2 E_{50})$, Obrzud & Truty Eq. 2.10 gives $1/(2 E_{50})$), and
    both give $b = 1/q_a$, so Rf doesn't depend on which governs. The range is
    hangtu's rule, stated as such: neither source says which readings to fit.
    The lower bound leaves out the start, where bedding and seating errors
    dominate $\varepsilon_1 / q$; the upper leaves out the approach to failure,
    where the curve leaves the hyperbola. Fewer than 3 readings in the range,
    or a slope of 0 or less (no asymptote), gives no Rf and a reason. An Rf
    above 1 is kept, not clipped, and counted in a warning: PLAXIS says Rf
    "should obviously be smaller than or equal to 1" (p. 69), so a value above
    it says the curve isn't hyperbolic in the range.

    **Drained or undrained, as ``test_type`` says:** E50 is Eu50 on an
    undrained stage (``CU``, ``UU`` and their variants) and E′50 on a drained
    one, and neither is converted into the other here. Every stage gets a
    value, a ``UU`` stage at its cell pressure and each stage of a multistage
    test; a later stage's specimen was sheared in an earlier one, and
    ``test_type``, ``cell_pressure`` and ``multistage_test`` say which rows
    those are.

    **Judgments taken:** none; the failure criterion and the fit's range are
    the caller's. **Valid for:** triaxial compression stages, with the
    deviator stress already corrected for area change and membrane.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per reading, as for ``triaxial_failure_from_readings()``.
        Stresses need declared units; strains are in percent.
    failure_criterion : {"max_deviator_stress", "max_stress_ratio"}, optional
        How to pick each stage's failure reading, whose $q$ is $q_f$. Without
        it, the lab's ``reported_failure_reading`` is used.
    failure_ratio_range : tuple of two floats, default (0.7, 0.95)
        The fractions of $q_f - q_0$ between which the hyperbola is fitted,
        $0 < r_{lo} < r_{hi} \le 1$.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.

    Returns
    -------
    pandas.DataFrame
        ``triaxial_failure_from_readings()``'s rows, then
        ``secant_modulus_at_50_percent_peak`` (E50, in ``cell_pressure``'s
        unit), ``axial_strain_at_50_percent_peak`` (ε50, %),
        ``secant_modulus_at_50_percent_peak_reason``, ``failure_ratio``,
        ``asymptotic_deviator_stress`` ($q_a$, measured from $q_0$, in
        ``cell_pressure``'s unit), ``failure_ratio_r_squared`` (of the
        transformed line, wherever one was fitted) and
        ``failure_ratio_reason``. Each row has a value or a reason for E50 and
        for Rf. ``attrs["units"]`` names each unit and
        ``attrs["failure_ratio_range"]`` the range used.

    Raises
    ------
    HangtuError
        Whatever ``triaxial_failure_from_readings()`` raises, and for a
        ``failure_ratio_range`` that isn't two fractions in order.
    UnitsError
        For a strain declared in a unit other than percent.

    Examples
    --------
    >>> readings = ht.read_csv(
    ...     ht.examples.path("triaxial_readings.csv"),
    ...     units={
    ...         "cell_pressure": "psf",
    ...         "back_pressure": "psf",
    ...         "effective_consolidation_stress": "psf",
    ...         "deviator_stress": "psf",
    ...         "excess_pore_pressure": "psf",
    ...     },
    ... )
    >>> stiffness = ht.analysis.triaxial_stiffness_from_readings(
    ...     readings, failure_criterion="max_deviator_stress"
    ... )
    """
    lower, upper = _check_range(failure_ratio_range)
    check_strain_units(df, units)
    reduced = reduce_readings(df, failure_criterion, units)
    _warn_interpolated(reduced.interpolated)
    readings = reduced.readings
    results = [
        _stage(readings, rows, reduced.picks[key], lower, upper)
        for key, rows in reduced.stages.items()
    ]
    above = [
        _name(key)
        for key, stage in zip(reduced.stages, results, strict=True)
        if stage.ratio > 1
    ]
    if above:
        n = len(above)
        more = f", and {n - 10} more" if n > 10 else ""
        warn(
            f"In {n} stage{'s' if n > 1 else ''}, the failure ratio Rf = q_f / q_a "
            f"is above 1, kept as read: {', '.join(above[:10])}{more}. The asymptote "
            "of the hyperbola fitted between "
            f"{lower:g} and {upper:g} of q_f lies below q_f, so the curve isn't "
            "hyperbolic there; check the curve, or fit another range with "
            "failure_ratio_range=."
        )
    result = reduced.rows.copy()
    for column, field in (
        (MODULUS, "modulus"),
        (STRAIN, "strain"),
        (MODULUS_REASON, "modulus_reason"),
        (RATIO, "ratio"),
        (ASYMPTOTE, "asymptote"),
        (R_SQUARED, "r_squared"),
        (RATIO_REASON, "ratio_reason"),
    ):
        result[column] = [getattr(stage, field) for stage in results]
    result.attrs["units"] = {
        **reduced.rows.attrs["units"],
        MODULUS: readings.stress_unit,
        ASYMPTOTE: readings.stress_unit,
        STRAIN: "%",
    }
    result.attrs["failure_ratio_range"] = (lower, upper)
    return result


class _Stage(NamedTuple):
    modulus: float
    strain: float
    modulus_reason: str | None
    ratio: float
    asymptote: float
    r_squared: float
    ratio_reason: str | None


def _stage(
    readings: Readings, rows: np.ndarray, pick: int, lower: float, upper: float
) -> _Stage:
    loading = rows[readings.q_loading[rows]]
    strain, deviator = readings.strain, readings.deviator
    at_zero = loading[strain[loading] == 0]
    origin = float(deviator[at_zero[0]]) if len(at_zero) else 0.0
    modulus, at_half, modulus_reason = _secant(
        strain[loading], deviator[loading], origin
    )
    ratio, asymptote, r_squared, ratio_reason = _failure_ratio(
        strain[loading[loading <= pick]],
        deviator[loading[loading <= pick]],
        float(deviator[pick]),
        origin,
        lower,
        upper,
    )
    return _Stage(
        modulus, at_half, modulus_reason, ratio, asymptote, r_squared, ratio_reason
    )


def _secant(
    strain: np.ndarray, deviator: np.ndarray, origin: float
) -> tuple[float, float, str | None]:
    """E50 and ε50 (%) of one stage's loading-part q readings, or a reason."""
    peak_at = int(np.argmax(deviator))
    peak = float(deviator[peak_at])
    if peak <= origin:
        return (
            np.nan,
            np.nan,
            "the deviator stress never rises above its value at zero strain",
        )
    half = origin + (peak - origin) / 2
    below = np.flatnonzero(deviator[:peak_at] < half)
    if not len(below):
        return (
            np.nan,
            np.nan,
            "no reading below half the peak deviator stress, so the strain at "
            "half the peak can't be interpolated",
        )
    i = int(below[-1])
    s1, s2, q1, q2 = strain[i], strain[i + 1], deviator[i], deviator[i + 1]
    at_half = float(s1 + (half - q1) / (q2 - q1) * (s2 - s1))
    if at_half <= 0:
        return (
            np.nan,
            np.nan,
            f"the strain at half the peak deviator stress is {at_half:g} %, not "
            "above 0",
        )
    return (half - origin) / (at_half / 100), at_half, None


def _failure_ratio(
    strain: np.ndarray,
    deviator: np.ndarray,
    at_failure: float,
    origin: float,
    lower: float,
    upper: float,
) -> tuple[float, float, float, str | None]:
    """Rf, q_a and r² of the transformed hyperbola, or a reason."""
    if math.isnan(at_failure):
        return np.nan, np.nan, np.nan, "the failure reading has no deviator stress"
    span = at_failure - origin
    if span <= 0:
        return (
            np.nan,
            np.nan,
            np.nan,
            "the deviator stress at failure isn't above its value at zero strain",
        )
    fraction = (deviator - origin) / span
    inside = (fraction >= lower) & (fraction <= upper)
    count = int(inside.sum())
    if count < FEWEST:
        return (
            np.nan,
            np.nan,
            np.nan,
            f"{count} reading{'' if count == 1 else 's'} between {lower:g} and "
            f"{upper:g} of the deviator stress at failure: the hyperbola needs at "
            f"least {FEWEST}",
        )
    x = strain[inside] / 100
    line = line_fit(x, x / (deviator[inside] - origin), x_name="axial strain")
    if line.no_fit_reason is not None:
        return np.nan, np.nan, np.nan, f"no hyperbola: {line.no_fit_reason}"
    if line.slope <= 0:
        return (
            np.nan,
            np.nan,
            line.r_squared,
            "ε1/q doesn't rise with ε1 between "
            f"{lower:g} and {upper:g} of the deviator stress at failure, so the "
            "hyperbola has no asymptote",
        )
    asymptote = 1 / line.slope
    return span / asymptote, asymptote, line.r_squared, None


def _check_range(value: object) -> tuple[float, float]:
    rule = (
        "failure_ratio_range must be two fractions of the deviator stress at "
        "failure, lower then upper, with 0 < lower < upper <= 1, such as "
        f"(0.7, 0.95); got {value!r}."
    )
    if (
        not isinstance(value, tuple | list)
        or len(value) != 2
        or not all(_is_number(v) for v in value)
    ):
        raise HangtuError(rule)
    lower, upper = float(value[0]), float(value[1])
    if not 0 < lower < upper <= 1:
        raise HangtuError(rule)
    return lower, upper


def _is_number(value: object) -> bool:
    return (
        isinstance(value, int | float | np.integer | np.floating)
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )
