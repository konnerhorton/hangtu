"""The Mohr-Coulomb fit of triaxial failure points (docs/work/m11b-envelope-fit.md)."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import flag_column, numeric_column, rows_text
from hangtu.analysis._derived import _DerivedResult
from hangtu.analysis._line_fit import line_fit
from hangtu.analysis._triaxial import STRESS_COLUMNS
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.stats._rows import breakdown, group_keys

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
    "count_multistage_left_out",
)
_STAGES = ("all", "single_stage")


def mohr_coulomb_fit(
    df: pd.DataFrame,
    *,
    stress: str = "effective",
    group_by: str | Sequence[str] | None = None,
    cohesion: float | None = None,
    multistage: bool = True,
    pool: str | Sequence[str] | None = None,
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

    **Multistage stages are fitted with and without.** A group with a
    multistage stage (``multistage_test`` True) gets two fits, ``"all"`` and
    ``"single_stage"``; ``multistage`` picks the main one, and both are on the
    result. Fit with and without them and compare: a later stage starts from a
    specimen already sheared.

    **Not pooled unawares.** A group whose fitted rows hold more than one
    ``failure_criterion`` (a blank is a value of its own) is an error naming
    each, as is more than one ``test_type`` in a total-stress fit (UU and CU
    total envelopes differ). ``pool=`` pools those columns on purpose, and the
    result records it. CU and CD stages pool without asking in effective
    stress: both give effective-stress failure points.

    **Valid for:** triaxial compression at failure; 2 points or more (1 with
    ``cohesion=0``) at different $s'$, and a slope $0 \le \tan\alpha < 1$
    (else no angle has $\sin\phi' = \tan\alpha$). A group outside these has no
    fit and a ``no_fit_reason``; the other groups are fitted. A negative
    intercept is reported as fitted, with a warning; a point with
    $\sigma'_3 < 0$ (tension) is fitted, with a warning. Nothing is clipped,
    forced or extrapolated. **Scatter:** ``r_squared`` (centered, so a fit
    with ``cohesion=0`` can have a low or negative one); a fit of 2 points
    passes through both, so its R² is 1 by construction. **Judgments taken:**
    none; ``cohesion=0`` is an argument recorded on the result.

    **Assumptions:** a straight envelope over the stresses tested; the
    principal stresses at failure as ``triaxial_failure_stresses()`` wrote
    them, by the lab's failure criterion, read as given.

    **The lab's values** (``reported_effective_cohesion`` and
    ``reported_effective_friction_angle``) are listed beside the fit, each
    distinct pair with its number of stages, and not compared with it.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per stage, with the principal stresses at failure that
        ``ht.analysis.triaxial_failure_stresses()`` writes (``p.triaxial()``
        has them): ``minor_principal_stress_at_failure`` and
        ``major_principal_stress_at_failure``, and their ``effective_`` pair.
        Where present, ``multistage_test``, ``failure_criterion``,
        ``test_type`` and the lab's reported pair are read, and the stage's
        identifiers kept.
    stress : {"effective", "total"}
        Which pair to fit. A total-stress fit gives ``total_stress_cohesion``
        and ``total_stress_friction_angle`` and doesn't list the lab's values.
    group_by : str or list of str, optional
        One fit per group, such as ``"geology_unit"`` or ``"sample_reference"``,
        in sorted order with a blank group last. None fits every row together.
    cohesion : None or 0
        None fits the intercept; 0 fixes c′ = 0 (the line through the origin).
        Another value is an error: c′ fixed at a non-zero value makes
        $a = c' \cos\phi'$ depend on the slope, so the fit isn't a line.
    multistage : bool
        True makes the fit with multistage stages the main one; False the fit
        without them.
    pool : str or list of str, optional
        ``"failure_criterion"`` (and, in total stress, ``"test_type"``) to
        fit rows with different values together on purpose.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.
    display_units : {"SI", "US"}, optional
        Fit in kPa (SI) or psf (US). None fits in the minor principal stress's
        unit. φ′ doesn't depend on the unit.

    Returns
    -------
    MohrCoulombFit
        ``.to_frame()`` has one row per group and fit; ``print()`` reads it;
        ``.groups`` holds the points fitted.

    Raises
    ------
    HangtuError
        For a frame without the principal stresses, a row with
        σ′1 < σ′3, sources mixed without ``pool=``, a stress column without
        units or in a unit that isn't a stress, a ``group_by`` column the frame
        doesn't have, or an argument out of its range.

    Examples
    --------
    The effective-stress envelope of each geology unit's triaxial tests:

    >>> p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
    >>> p.set_geology_map(ht.examples.path("strata.csv"))
    >>> fit = ht.analysis.mohr_coulomb_fit(p.triaxial(), group_by="geology_unit")
    >>> print(fit)
    >>> fit.to_frame()[["geology_unit", "effective_cohesion"]]
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
    by = _names(group_by)
    missing = [column for column in by if column not in df.columns]
    if missing:
        raise ColumnError(
            f"{_FUNCTION} can't group by {', '.join(map(repr, missing))}: df has no "
            f"such column. Available columns: {', '.join(map(str, df.columns))}."
        )
    checked = ["failure_criterion"] + (["test_type"] if stress == "total" else [])
    pooled = _names(pool)
    wrong = [column for column in pooled if column not in checked]
    if wrong:
        raise HangtuError(
            f"{_FUNCTION} can't pool {', '.join(map(repr, wrong))}: pool= takes "
            f"{' and '.join(map(repr, checked))}, the columns it checks."
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
    has_multistage = "multistage_test" in df.columns
    staged = np.array(
        flag_column(df, "multistage_test", "Fill it in, or drop the column."),
        dtype=object,
    )
    multistaged = staged == True  # noqa: E712 (None is blank)
    reported = _reported(df, units, unit) if stress == "effective" else None

    notes = []
    for column in checked:
        if column not in df.columns:
            notes.append(
                f"{column} not given: the fit couldn't check that the stages share one."
            )
    if not has_multistage:
        notes.append("multistage_test not given: multistage stages weren't told apart.")
    if pooled:
        notes.append(f"Pooled on purpose: {', '.join(pooled)}.")

    groups, negative, tension = [], [], []
    for key, rows in group_keys(df, by):
        candidates = rows & (reasons == "")
        _check_sources(df, key, candidates, checked, pooled)
        left_out = {name: int((rows & (reasons == name)).sum()) for name in _LEFT_OUT}
        fits = {"all": _fit(df, candidates, minor, major, cohesion, reported)}
        fits["all"].update(left_out)
        if (candidates & multistaged).any():
            single_stages = candidates & ~multistaged
            single = _fit(df, single_stages, minor, major, cohesion, reported)
            single.update(left_out)
            single[_LEFT_OUT[2]] = int((candidates & multistaged).sum())
            if not single_stages.any():
                single["no_fit_reason"] = "every stage is multistage"
            fits["single_stage"] = single
        main = "all" if multistage or "single_stage" not in fits else "single_stage"
        order = [main, *(name for name in _STAGES if name in fits and name != main)]
        for name in order:
            fits[name]["stages"] = name
        label = _label(key)
        if any(
            fit["no_fit_reason"] is None and fit["line_intercept"] < 0
            for fit in fits.values()
        ):
            negative.append(label)
        tension.extend(
            row for row in df.index[candidates & (minor < 0)] if row not in tension
        )
        groups.append(
            {
                "key": key,
                "count_rows": int(rows.sum()),
                "fits": [fits[name] for name in order],
            }
        )

    prime = "′" if stress == "effective" else ""
    if negative:
        warn(
            f"{_FUNCTION}: the fitted intercept is negative in {', '.join(negative)}, "
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
        by=tuple(by),
        pooled=tuple(pooled),
        cohesion=cohesion,
        multistage=multistage,
        display_units=display_units,
        groups=tuple(groups),
    )


def _names(value: str | Sequence[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


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


def _reported(
    df: pd.DataFrame, units: Mapping[str, str] | None, unit: str
) -> tuple[np.ndarray, np.ndarray]:
    """Return the lab's c′ in the fit's unit and φ′ in degrees, NaN where not given."""
    to = {
        "reported_effective_cohesion": unit,
        "reported_effective_friction_angle": "deg",
    }
    quantity = {
        "reported_effective_cohesion": "stress",
        "reported_effective_friction_angle": "angle",
    }
    result = []
    for column, target in to.items():
        if column not in df.columns or df[column].isna().all():
            result.append(np.full(len(df), np.nan))
            continue
        declared = _units.resolve_units(df, [column], units, analysis=True)[column]
        source = _units.parse_unit(declared, column)
        _units.check_dimension(source, quantity[column], column)
        result.append(
            _units.convert(
                numeric_column(df, column),
                source,
                quantity[column],
                _units.parse_unit(target),
            )
        )
    return result[0], result[1]


def _check_sources(
    df: pd.DataFrame,
    key: dict[str, Any],
    rows: np.ndarray,
    checked: list[str],
    pooled: list[str],
) -> None:
    """Raise if a group's fitted rows mix failure criteria or test types (D4)."""
    lines, mixed = [], []
    for column in checked:
        if column in pooled or column not in df.columns:
            continue
        counts = breakdown(df.loc[rows, column])
        if len(counts) < 2:
            continue
        mixed.append(column)
        listed = [f"{value!r} ({count} rows)" for value, count in counts.items()]
        indent = " " * (len(column) + 4)
        lines.append(f"  {column}: " + f",\n{indent}".join(listed))
    if not mixed:
        return
    label = _label(key) if key else ""
    where = f" in group {label!r}" if label else ""
    raise HangtuError(
        f"{_FUNCTION} can't fit rows from different sources together{where}:\n"
        + "\n".join(lines)
        + f"\nFit each with group_by={[*key, mixed[0]]!r}, filter the rows, "
        f"or pool them on purpose with pool={mixed!r}."
    )


def _fit(
    df: pd.DataFrame,
    fitted: np.ndarray,
    minor: np.ndarray,
    major: np.ndarray,
    cohesion: float | None,
    reported: tuple[np.ndarray, np.ndarray] | None,
) -> dict[str, Any]:
    """Fit one set of stages: the line in s′-t, then c′ and φ′ (Derivations 1-3)."""
    mean = (major[fitted] + minor[fitted]) / 2
    radius = (major[fitted] - minor[fitted]) / 2
    line = line_fit(mean, radius, intercept=cohesion, x_name="mean stress")
    reason = line.no_fit_reason
    if reason is not None and cohesion is None and line.count < 2:
        plural = "" if line.count == 1 else "s"
        reason = f"{line.count} point{plural} (2 needed, or cohesion=0)"
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
        "reported_pairs": _pairs(reported, fitted),
        "no_fit_reason": reason,
        "notes": notes,
        "points": points,
    }


def _pairs(
    reported: tuple[np.ndarray, np.ndarray] | None, fitted: np.ndarray
) -> list[dict[str, Any]] | None:
    """Return the distinct (c′, φ′) the lab reported for the fitted stages."""
    if reported is None:
        return None
    counts: dict[tuple[float, float], int] = {}
    for cohesion, angle in zip(reported[0][fitted], reported[1][fitted], strict=True):
        if np.isnan(cohesion) and np.isnan(angle):
            continue
        pair = (float(cohesion), float(angle))
        match = next((known for known in counts if _same(known, pair)), pair)
        counts[match] = counts.get(match, 0) + 1
    return [
        {"cohesion": cohesion, "friction_angle": angle, "count": count}
        for (cohesion, angle), count in counts.items()
    ]


def _same(first: tuple[float, float], second: tuple[float, float]) -> bool:
    return all(
        (np.isnan(a) and np.isnan(b)) or a == b
        for a, b in zip(first, second, strict=True)
    )


def _cell(value: Any) -> Any:
    return None if pd.isna(value) else value


def _label(key: dict[str, Any]) -> str:
    return ", ".join(map(str, key.values())) or "All"


@dataclass(frozen=True, repr=False)
class MohrCoulombFit(_DerivedResult):
    """The fit ``ht.analysis.mohr_coulomb_fit()`` returns.

    Use ``.to_frame()`` for a table with one row per group and fit,
    ``.to_dict()`` for a report, or ``print(fit)`` to read it. ``.groups``
    holds each group's fits and the points of each, with their tangent points
    on the envelope. The text is a view of the same numbers.
    """

    #: ``"effective"`` or ``"total"``.
    stress: str
    #: The columns grouped by, in order.
    by: tuple[str, ...]
    #: The columns pooled on purpose (``pool=``).
    pooled: tuple[str, ...]
    #: None for a fitted intercept, 0 for c′ fixed at 0.
    cohesion: float | None
    #: Whether the fit with multistage stages is the main one.
    multistage: bool
    #: The system the stresses were converted to before fitting, None if not.
    display_units: str | None
    #: One record per group: its key, its number of rows and its fits, the
    #: main one first. Each fit has ``stages`` (``"all"`` or
    #: ``"single_stage"``), the values of ``.to_frame()``, ``reported_pairs``
    #: and ``points``.
    groups: tuple[dict[str, Any], ...]

    def _value_names(self) -> tuple[str, str]:
        if self.stress == "effective":
            return "effective_cohesion", "effective_friction_angle"
        return "total_stress_cohesion", "total_stress_friction_angle"

    def _columns(self) -> list[str]:
        cohesion, angle = self._value_names()
        reported = (
            [
                "reported_effective_cohesion",
                "reported_effective_friction_angle",
                "count_reported_pairs",
            ]
            if self.stress == "effective"
            else []
        )
        left_out = [
            name
            for name in _LEFT_OUT
            if self.stress == "effective" or name != "count_no_effective_stresses"
        ]
        return [
            *self.by,
            "stages",
            cohesion,
            angle,
            "line_intercept",
            "line_slope",
            "r_squared",
            "count",
            "lowest_normal_stress",
            "highest_normal_stress",
            *reported,
            *left_out,
            "no_fit_reason",
        ]

    def to_frame(self) -> pd.DataFrame:
        """Return one row per group and fit, the main fit of each group first.

        ``stages`` is ``"all"`` or ``"single_stage"`` (a group with a
        multistage stage has both). The lab's pair is given when the group's
        fitted stages report one; with more, it is blank and
        ``count_reported_pairs`` says how many. ``attrs["units"]`` gives the
        unit of each column that has one; angles are in degrees.
        """
        cohesion, angle = self._value_names()
        rows = []
        for group in self.groups:
            for fit in group["fits"]:
                row = {
                    **group["key"],
                    "stages": fit["stages"],
                    cohesion: fit["cohesion"],
                    angle: fit["friction_angle"],
                    **{
                        name: fit[name]
                        for name in (
                            "line_intercept",
                            "line_slope",
                            "r_squared",
                            "count",
                            "lowest_normal_stress",
                            "highest_normal_stress",
                            "no_fit_reason",
                        )
                    },
                    **_left_out_counts(fit, self.stress),
                }
                pairs = fit["reported_pairs"]
                if pairs is not None:
                    one = pairs[0] if len(pairs) == 1 else None
                    row["reported_effective_cohesion"] = (
                        one["cohesion"] if one else np.nan
                    )
                    row["reported_effective_friction_angle"] = (
                        one["friction_angle"] if one else np.nan
                    )
                    row["count_reported_pairs"] = len(pairs)
                rows.append(row)
        frame = pd.DataFrame(rows, columns=self._columns())
        stresses = [
            cohesion,
            "line_intercept",
            "lowest_normal_stress",
            "highest_normal_stress",
        ]
        if self.stress == "effective":
            stresses.append("reported_effective_cohesion")
        angles = [angle] + (
            ["reported_effective_friction_angle"] if self.stress == "effective" else []
        )
        frame.attrs["units"] = {
            **(dict.fromkeys(stresses, self.unit) if self.unit else {}),
            **dict.fromkeys(angles, "deg"),
        }
        return frame

    def __str__(self) -> str:
        from hangtu.plot._overlays import format_number  # plot imports analysis

        prime = "′" if self.stress == "effective" else ""
        unit = f" {self.unit}" if self.unit else ""
        title = f"Mohr-Coulomb fit, {self.stress} stress"
        if self.cohesion == 0:
            title += f", c{prime} = 0 fixed"
        lines = [title]
        for group in self.groups:
            if self.by:
                lines.append(f"{_label(group['key'])}: {group['count_rows']} rows")
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
                for pair in fit["reported_pairs"] or []:
                    lines.append(
                        f"    lab: c′ = {_reported_text(pair['cohesion'])}{unit}, "
                        f"φ′ = {_reported_text(pair['friction_angle'])}° "
                        f"({pair['count']} stage{'s' if pair['count'] > 1 else ''})"
                    )
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


def _reported_text(value: float) -> str:
    return "—" if math.isnan(value) else f"{value:g}"
