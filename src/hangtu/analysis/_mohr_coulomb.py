"""The Mohr-Coulomb fit of triaxial failure points (docs/work/m11b-envelope-fit.md)."""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu.analysis._derived import _DerivedResult
from hangtu.analysis._line_fit import line_fit
from hangtu.analysis._triaxial import STRESS_COLUMNS
from hangtu.errors import ColumnError, HangtuError, warn

_FUNCTION = "mohr_coulomb_fit()"
#: The columns that identify a fitted point, kept with its stresses.
_IDENTIFIERS = (
    "loca_id",
    "specimen_id",
    "sample_reference",
    "specimen_reference",
    "test_type",
    "test_stage",
)
#: The counts of rows left out, in the order a row is counted (Decision 6).
_LEFT_OUT = (
    "count_no_principal_stresses",
    "count_no_effective_stresses",
)


def mohr_coulomb_fit(
    df: pd.DataFrame,
    *,
    stress: str = "effective",
    cohesion: float | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> "MohrCoulombFit":
    r"""Fit a Mohr-Coulomb envelope to triaxial failure points: c′ and φ′.

    Each stage's Mohr circle at failure has center $s'$ and radius $t$; the
    envelope $\tau = c' + \sigma'_n \tan\phi'$ touches every circle when
    $t = c' \cos\phi' + s' \sin\phi'$, a straight line in $s'$-$t$. The fit
    is that line, by ordinary least squares, and its intercept $a$ and slope
    $\tan\alpha$ give the parameters back:

    $$
    s' = \frac{\sigma'_1 + \sigma'_3}{2}, \quad t = \frac{\sigma'_1 - \sigma'_3}{2},
    \quad t = a + s' \tan\alpha, \quad
    \phi' = \arcsin(\tan\alpha), \quad c' = \frac{a}{\cos\phi'}
    $$

    $c' = a / \cos\phi'$, not $a / \cos\alpha$: $\alpha$ is the slope angle of
    the line in $s'$-$t$, not the friction angle. Each circle's tangent point
    is $\sigma'_n = s' - \hat t \sin\phi'$, $\tau = \hat t \cos\phi'$, with
    $\hat t$ the fitted radius; their range, ``lowest_normal_stress`` to
    ``highest_normal_stress``, is the range the fit holds over. $c'$ is an
    intercept at $\sigma'_n = 0$, outside it.

    These follow from the circle's geometry and the definitions of $s'$ and
    $t$, without a coefficient or a cited value; the steps are written out in
    docs/work/m11b-envelope-fit.md, "Derivations".

    **Rows left out**, each counted once under the first reason that applies:
    a total principal stress blank (extension and incomplete rows,
    ``count_no_principal_stresses``); in an effective fit, an effective one
    blank (UU, or CU without a pore pressure, ``count_no_effective_stresses``);
    multistage stages when ``multistage=False``
    (``count_multistage_left_out``). ``count`` plus these is the group's rows.

    **Valid for:** triaxial compression at failure; 2 points or more (1 with
    ``cohesion=0``) at different $s'$, and a slope $0 \le \tan\alpha < 1$
    (else no angle has $\sin\phi' = \tan\alpha$). Outside these there is no
    fit, and ``no_fit_reason`` says why. A negative
    intercept is reported as fitted, with a warning; a point with
    $\sigma'_3 < 0$ (tension) is fitted, with a warning. Nothing is clipped,
    forced or extrapolated. **Scatter:** ``r_squared`` (centered, so a fit
    with ``cohesion=0`` can have a low or negative one); a fit of 2 points
    passes through both, so its R² is 1 by construction. **Judgments taken:**
    none; ``cohesion=0`` is an argument recorded on the result.

    **Assumptions:** a straight envelope over the stresses tested; the
    principal stresses at failure as ``triaxial_failure_stresses()`` wrote
    them, by the lab's failure criterion, read as given.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per stage, with the principal stresses at failure that
        ``ht.analysis.triaxial_failure_stresses()`` writes (``p.triaxial()``
        has them): ``minor_principal_stress_at_failure`` and
        ``major_principal_stress_at_failure``, and their ``effective_`` pair.
        Where present, the stage's identifiers are kept.
    stress : {"effective", "total"}
        Which pair to fit. A total-stress fit gives ``total_stress_cohesion``
        and ``total_stress_friction_angle``.
    cohesion : None or 0
        None fits the intercept; 0 fixes c′ = 0 (the line through the origin).
        Another value is an error: c′ fixed at a non-zero value makes
        $a = c' \cos\phi'$ depend on the slope, so the fit isn't a line.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.
    display_units : {"SI", "US"}, optional
        Fit in kPa (SI) or psf (US). None fits in the minor principal stress's
        unit. φ′ doesn't depend on the unit.

    Returns
    -------
    MohrCoulombFit
        ``print()`` reads it; ``.groups`` holds the fit and the points fitted.

    Raises
    ------
    HangtuError
        For a frame without the principal stresses, a row with
        σ′1 < σ′3, a stress column without units or in a unit that isn't a
        stress, or an argument out of its range.

    Examples
    --------
    The effective-stress envelope of a project's triaxial tests:

    >>> fit = ht.analysis.mohr_coulomb_fit(p.triaxial())
    >>> print(fit)
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if stress not in ("effective", "total"):
        raise HangtuError(
            f'{_FUNCTION} stress must be "effective" or "total", not {stress!r}. '
            'A drained test gives effective-stress points: use stress="effective".'
        )
    if cohesion is not None and cohesion != 0:
        raise HangtuError(
            f"{_FUNCTION} cohesion must be None (fitted) or 0, not {cohesion!r}. "
            "With c′ fixed at a non-zero value the intercept a = c′ cos φ′ depends "
            "on the slope, so the s′-t fit is no longer a line; fit it free and "
            "compare, or fix it at 0."
        )
    if display_units not in (None, "SI", "US"):
        raise HangtuError(
            f'{_FUNCTION} display_units must be "SI", "US" or None, not '
            f"{display_units!r}."
        )
    stresses, unit = _stresses(df, stress, units, display_units)
    total_minor, total_major, minor, major = stresses
    reversed_ = major < minor
    if reversed_.any():
        prime = "′" if stress == "effective" else ""
        raise HangtuError(
            f"Rows {rows_text(df.index[reversed_])} have σ{prime}1 < σ{prime}3, which "
            "can't be a compression failure. Check the cell pressure, deviator "
            "stress and pore pressure of those rows."
        )
    reasons = np.full(len(df), "", dtype=object)
    reasons[np.isnan(total_minor) | np.isnan(total_major)] = _LEFT_OUT[0]
    reasons[(reasons == "") & (np.isnan(minor) | np.isnan(major))] = _LEFT_OUT[1]
    fitted = reasons == ""
    fit = _fit(df, fitted, minor, major, cohesion)
    fit.update({name: int((reasons == name).sum()) for name in _LEFT_OUT})
    fit["stages"] = "all"
    negative = fit["no_fit_reason"] is None and fit["line_intercept"] < 0
    tension = list(df.index[fitted & (minor < 0)])
    groups = [{"key": {}, "count_rows": len(df), "fits": [fit]}]
    notes = []

    prime = "′" if stress == "effective" else ""
    if negative:
        warn(
            f"{_FUNCTION}: the fitted intercept is negative, "
            f"so c{prime} < 0. It is reported as fitted; if the ground has no "
            "cohesion, fit again with cohesion=0."
        )
    if tension:
        warn(
            f"{_FUNCTION}: rows {rows_text(pd.Index(tension))} have σ{prime}3 < 0 "
            "(tension) and are fitted as given. Check their pore pressures."
        )
    notes.append(
        f"c{prime} is an intercept at σ{prime}n = 0, outside each fit's range of "
        f"σ{prime}n (lowest_normal_stress to highest_normal_stress); the fit holds "
        "over that range."
    )
    return MohrCoulombFit(
        function="mohr_coulomb_fit",
        unit=unit,
        notes=tuple(notes),
        judgments=dict(df.attrs.get("judgments", {})),
        hangtu_version=version("hangtu"),
        stress=stress,
        cohesion=cohesion,
        display_units=display_units,
        groups=tuple(groups),
    )


def _stresses(
    df: pd.DataFrame,
    stress: str,
    units: Mapping[str, str] | None,
    display_units: str | None,
) -> tuple[list[np.ndarray], str]:
    """Return the total pair and the fitted pair, in one unit, and its name."""
    total = list(STRESS_COLUMNS[:2])
    fitted = list(STRESS_COLUMNS[2:] if stress == "effective" else STRESS_COLUMNS[:2])
    columns = list(dict.fromkeys([*total, *fitted]))
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ColumnError(
            f"df has no column {', '.join(map(repr, missing))}. {_FUNCTION} fits the "
            "principal stresses at failure: call "
            "ht.analysis.triaxial_failure_stresses() on the stages first "
            "(p.triaxial() has them already)."
        )
    declared = _units.resolve_units(df, columns, units, analysis=True)
    parsed = {column: _units.parse_unit(declared[column], column) for column in columns}
    for column, unit in parsed.items():
        _units.check_dimension(unit, "stress", column)
    values = {}
    if display_units is None:
        unit = declared[fitted[0]]
        for column in columns:
            values[column] = _units.convert(
                numeric_column(df, column), parsed[column], "stress", parsed[fitted[0]]
            )
    else:
        for column in columns:
            values[column], unit = _units.to_display(
                numeric_column(df, column), declared[column], "stress", display_units
            )
    return [values[column] for column in [*total, *fitted]], unit


def _fit(
    df: pd.DataFrame,
    fitted: np.ndarray,
    minor: np.ndarray,
    major: np.ndarray,
    cohesion: float | None,
) -> dict[str, Any]:
    """Fit one set of stages: the line in s′-t, then c′ and φ′ (Derivations 1-3)."""
    mean = (major[fitted] + minor[fitted]) / 2
    radius = (major[fitted] - minor[fitted]) / 2
    line = line_fit(mean, radius, intercept=cohesion, x_name="mean stress")
    reason = line.no_fit_reason
    slope = line.slope
    if reason is None and not 0 <= slope < 1:
        reason = (
            f"slope tan α = {float(f'{slope:.4g}')} is outside 0 ≤ tan α < 1: "
            "no friction angle fits"
        )
    if reason is None:
        angle = math.asin(slope)
        intercept = line.intercept / math.cos(angle)
        fitted_radius = line.intercept + mean * slope
        normal = mean - fitted_radius * math.sin(angle)
        shear = fitted_radius * math.cos(angle)
    else:
        angle = intercept = np.nan
        normal = shear = np.full(len(mean), np.nan)
    notes = []
    if reason is None and line.count == 2 and cohesion is None:
        notes.append("2 points: the line passes through both, so R² = 1.")
    identifiers = [column for column in _IDENTIFIERS if column in df.columns]
    points = [
        {
            "row": row,
            **{column: _cell(df.at[row, column]) for column in identifiers},
            "minor_principal_stress": float(minor[i]),
            "major_principal_stress": float(major[i]),
            "mean_stress": float(mean[j]),
            "radius": float(radius[j]),
            "normal_stress": float(normal[j]),
            "shear_stress": float(shear[j]),
        }
        for j, (i, row) in enumerate(
            zip(np.flatnonzero(fitted), df.index[fitted], strict=True)
        )
    ]
    return {
        "cohesion": float(intercept),
        "friction_angle": float(math.degrees(angle)),
        "line_intercept": float(line.intercept),
        "line_slope": float(slope),
        "r_squared": float(line.r_squared),
        "count": line.count,
        "lowest_normal_stress": float(np.min(normal)) if reason is None else np.nan,
        "highest_normal_stress": float(np.max(normal)) if reason is None else np.nan,
        "no_fit_reason": reason,
        "notes": notes,
        "points": points,
    }


def _cell(value: Any) -> Any:
    return None if pd.isna(value) else value


@dataclass(frozen=True, repr=False)
class MohrCoulombFit(_DerivedResult):
    """The fit ``ht.analysis.mohr_coulomb_fit()`` returns.

    Use ``.to_dict()`` for a report, or ``print(fit)`` to read it. ``.groups``
    holds the fit and its points, with their tangent points on the envelope.
    The text is a view of the same numbers.
    """

    #: ``"effective"`` or ``"total"``.
    stress: str
    #: None for a fitted intercept, 0 for c′ fixed at 0.
    cohesion: float | None
    #: The system the stresses were converted to before fitting, None if not.
    display_units: str | None
    #: One record per group: its key, its number of rows and its fits. Each
    #: fit has ``stages``, its values and ``points``.
    groups: tuple[dict[str, Any], ...]

    def __str__(self) -> str:
        from hangtu.plot._overlays import format_number  # plot imports analysis

        prime = "′" if self.stress == "effective" else ""
        unit = f" {self.unit}" if self.unit else ""
        title = f"Mohr-Coulomb fit, {self.stress} stress"
        if self.cohesion == 0:
            title += f", c{prime} = 0 fixed"
        lines = [title]
        for group in self.groups:
            for fit in group["fits"]:
                stages = "all stages" if fit["stages"] == "all" else "single stages"
                if fit["no_fit_reason"]:
                    lines.append(f"  {stages}: not fitted: {fit['no_fit_reason']}")
                else:
                    lines.append(
                        f"  {stages}: "
                        f"c{prime} = {format_number(fit['cohesion'])}{unit}, "
                        f"φ{prime} = {format_number(fit['friction_angle'])}°, "
                        f"R² = {_r_squared(fit['r_squared'])}, {fit['count']} points, "
                        f"σ{prime}n {format_number(fit['lowest_normal_stress'])} to "
                        f"{format_number(fit['highest_normal_stress'])}{unit}"
                    )
                left_out = [
                    f"{count} {name.removeprefix('count_').replace('_', ' ')}"
                    for name, count in _left_out_counts(fit, self.stress).items()
                    if count
                ]
                if left_out:
                    lines.append(f"    left out: {', '.join(left_out)}")
                lines.extend(f"    {note}" for note in fit["notes"])
        return "\n".join([*lines, *self.notes])


def _left_out_counts(fit: dict[str, Any], stress: str) -> dict[str, int]:
    """Return the group's rows a fit left out, by reason; they add up with count."""
    return {
        name: fit[name]
        for name in _LEFT_OUT
        if stress == "effective" or name != "count_no_effective_stresses"
    }


def _r_squared(value: float) -> str:
    return "—" if math.isnan(value) else f"{value:.3f}"
