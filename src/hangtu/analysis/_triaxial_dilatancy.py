"""ψ from the rate of dilation in triaxial readings (docs/analysis/strength.md §9)."""

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

from hangtu.analysis._line_fit import line_fit
from hangtu.analysis._triaxial import DRAINED, UNDRAINED
from hangtu.analysis._triaxial_readings import (
    Readings,
    _warn_interpolated,
    check_strain_units,
    reduce_readings,
)
from hangtu.errors import HangtuError

ANGLE = "dilatancy_angle"
RATE = "dilation_rate"
REASON = "dilatancy_angle_reason"
#: Types with no volume change to read: the undrained ones, UU and unconfined.
NO_VOLUME_CHANGE = UNDRAINED | {"UU", "UUM", "UNC"}


def triaxial_dilatancy_from_readings(
    df: pd.DataFrame,
    *,
    failure_criterion: str | None = None,
    dilatancy_from: float = 0.95,
    units: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    r"""Read each drained triaxial stage's dilatancy angle ψ from its readings.

    Takes the readings during shearing, as ``p.triaxial_readings()`` or
    ``ht.template("triaxial_readings")`` lays them out, and returns
    ``ht.analysis.triaxial_failure_from_readings()``'s rows, one per stage,
    with the same ``failure_criterion=``, with the rate of dilation near the
    failure reading and the angle it gives added. The stages, their loading
    parts and the failure readings are the ones
    ``triaxial_failure_from_readings()`` and ``ht.plot.triaxial_shearing()``
    use.

    **The angle** (Vermeer & de Borst 1984, Eqs. 3.1-3.3, pp. 12-13). They
    define $\sin\psi = \dot\varepsilon_v^p / (-2\dot\varepsilon_1^p +
    \dot\varepsilon_v^p)$ with tension positive. With compression positive, as
    ``axial_strain`` and ``volumetric_strain`` are, and the rate of dilation
    $r = -d\varepsilon_v / d\varepsilon_1$ (positive when the specimen
    dilates), it reads

    $$
    \sin\psi = \frac{r}{2 + r}
    $$

    **Total strains stand in for plastic ones.** The source defines ψ by
    plastic strain rates; near the end of hardening "the elastic strain rate
    is almost zero, so that all further strain increments are of a plastic
    nature" (p. 12), and $\varepsilon_v$ against $\varepsilon_1$ is then a
    line, "the so-called rate of dilation is found to be a constant". So $r$
    is the least-squares slope of $\varepsilon_v$ against $\varepsilon_1$
    over the stage's loading-part $\varepsilon_v$ readings in a window ending
    at the failure reading: from the strain of the first loading-part $q$
    reading with $(q - q_0) \ge d\,(q_f - q_0)$ to the failure reading's
    strain, both included, with $d$ ``dilatancy_from``, $q_f$ the failure
    reading's $q$ and $q_0$ the $q$ of the stage's first reading at zero
    strain (0 where it has none). The window is hangtu's rule, stated as
    such: the source says where the rate is constant, not which readings to
    take. Strains between readings are never interpolated.

    **Limits:** a stage that isn't drained (``CU``, ``UU`` and their
    variants) has no volume change to read, and a stage whose ``test_type``
    is blank has unknown drainage: blank, with a reason. So does a drained
    stage with fewer than 2 $\varepsilon_v$ readings in the window, and one
    with $r \le -1$, contracting faster than it strains axially, where
    $\sin\psi \le -1$. A negative ψ (a stage still contracting at failure,
    $-1 < r < 0$) is kept: it is what the readings say.

    **Judgments taken:** none; the failure criterion and the window are the
    caller's. **Valid for:** drained triaxial compression stages (``CD``,
    ``CDM``, ``CIDC``, ``CADC``) with volumetric strain readings.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per reading, as for ``triaxial_failure_from_readings()``, with
        ``volumetric_strain``. Stresses need declared units; strains are in
        percent.
    failure_criterion : {"max_deviator_stress", "max_stress_ratio"}, optional
        How to pick each stage's failure reading, where the window ends.
        Without it, the lab's ``reported_failure_reading`` is used.
    dilatancy_from : float, default 0.95
        The fraction of $q_f - q_0$ at which the window starts,
        $0 < d \le 1$.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.

    Returns
    -------
    pandas.DataFrame
        ``triaxial_failure_from_readings()``'s rows, then ``dilatancy_angle``
        (ψ, degrees), ``dilation_rate`` ($r$, wherever a line was fitted) and
        ``dilatancy_angle_reason``. Each row has an angle or a reason.
        ``attrs["units"]`` names each unit and ``attrs["dilatancy_from"]`` the
        fraction used.

    Raises
    ------
    HangtuError
        Whatever ``triaxial_failure_from_readings()`` raises, and for a
        ``dilatancy_from`` that isn't a fraction above 0.
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
    >>> dilatancy = ht.analysis.triaxial_dilatancy_from_readings(
    ...     readings, failure_criterion="max_deviator_stress"
    ... )
    """
    start = _check_fraction(dilatancy_from)
    check_strain_units(df, units)
    reduced = reduce_readings(df, failure_criterion, units)
    _warn_interpolated(reduced.interpolated)
    readings = reduced.readings
    results = [
        _stage(readings, rows, reduced.picks[key], start)
        for key, rows in reduced.stages.items()
    ]
    result = reduced.rows.copy()
    result[ANGLE] = [angle for angle, _, _ in results]
    result[RATE] = [rate for _, rate, _ in results]
    result[REASON] = [reason for _, _, reason in results]
    result.attrs["units"] = {**reduced.rows.attrs["units"], ANGLE: "deg"}
    result.attrs["dilatancy_from"] = start
    return result


def _stage(
    readings: Readings, rows: np.ndarray, pick: int, start: float
) -> tuple[float, float, str | None]:
    """ψ (degrees), r and the reason for one stage."""
    test_type = readings.types.iloc[rows[0]]
    if test_type is None:
        return np.nan, np.nan, "test_type blank: drainage unknown"
    if test_type in NO_VOLUME_CHANGE:
        return np.nan, np.nan, "undrained: no volume change"
    if test_type not in DRAINED:
        return (
            np.nan,
            np.nan,
            f"test_type {test_type!r} isn't a drained compression stage",
        )
    strain, deviator = readings.strain, readings.deviator
    volumetric = rows[readings.volumetric_loading[rows]]
    if not len(volumetric):
        return np.nan, np.nan, "no volumetric strain readings"
    at_failure = float(deviator[pick])
    if math.isnan(at_failure):
        return np.nan, np.nan, "the failure reading has no deviator stress"
    loading = rows[readings.q_loading[rows]]
    at_zero = loading[strain[loading] == 0]
    origin = float(deviator[at_zero[0]]) if len(at_zero) else 0.0
    span = at_failure - origin
    if span <= 0:
        return (
            np.nan,
            np.nan,
            "the deviator stress at failure isn't above its value at zero strain",
        )
    reached = loading[deviator[loading] - origin >= start * span]
    # A lab's mark can fall on a tail reading, past every loading-part one.
    end = float(strain[pick])
    begin = float(strain[reached[0]]) if len(reached) else end
    window = volumetric[(strain[volumetric] >= begin) & (strain[volumetric] <= end)]
    count = len(window)
    if count < 2:
        return (
            np.nan,
            np.nan,
            f"{count} volumetric strain reading{'' if count == 1 else 's'} between "
            f"{begin:g} % and {end:g} % axial strain (from {start:g} of the deviator "
            "stress at failure to the failure reading): the rate needs at least 2",
        )
    line = line_fit(strain[window], readings.volumetric[window], x_name="axial strain")
    if line.no_fit_reason is not None:
        return np.nan, np.nan, f"no rate of dilation: {line.no_fit_reason}"
    rate = -line.slope
    if rate <= -1:
        return (
            np.nan,
            rate,
            f"the rate of dilation is {rate:.3g}: contracting faster than it "
            "strains axially, sin ψ = r / (2 + r) would be -1 or less",
        )
    return math.degrees(math.asin(rate / (2 + rate))), rate, None


def _check_fraction(value: object) -> float:
    if (
        isinstance(value, int | float | np.integer | np.floating)
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and 0 < float(value) <= 1
    ):
        return float(value)
    raise HangtuError(
        "dilatancy_from must be the fraction of the deviator stress at failure "
        f"where the rate of dilation's window starts, above 0 and at most 1, such "
        f"as 0.95; got {value!r}."
    )
