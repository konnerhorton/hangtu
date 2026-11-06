"""The shear box fit of peak and residual stages (docs/work/m17b-shear-box-fit.md)."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu.analysis._derived import _DerivedResult, judgments_file
from hangtu.analysis._fit_groups import (
    PLACE,
    _cell,
    _check_sources,
    _label,
    _names,
    _pairs,
    _place_units,
    _reported,
)
from hangtu.analysis._line_fit import line_fit
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.stats._rows import group_keys

_FUNCTION = "shear_box_fit()"
_STRENGTHS = ("peak", "residual")
_KINDS = ("free", "through_origin")
_SHEAR = {"peak": "peak_shear_stress", "residual": "residual_shear_stress"}
_AT = {"peak": "normal_stress_at_peak", "residual": "normal_stress_at_residual"}
_APPLIED = "applied_normal_stress"
_NORMAL_STRESS = ("at_peak_or_residual", "applied")
#: The columns a line's rows must share one value of, unless pooled.
_CHECKED = ["test_type", "failure_criterion"]
#: The columns that identify a fitted point, kept with its stresses.
_IDENTIFIERS = (
    "loca_id",
    "specimen_id",
    "sample_reference",
    "specimen_reference",
    "test_type",
    "test_stage",
    *PLACE,
)


def _left_out(strength: str) -> tuple[str, str]:
    """Return a strength's counts of rows left out, in the order they're counted."""
    return (f"count_no_{strength}_shear_stress", f"count_no_{strength}_normal_stress")


def shear_box_fit(
    df: pd.DataFrame,
    *,
    group_by: str | Sequence[str] | None = None,
    cohesion: float | None = None,
    normal_stress: str = "at_peak_or_residual",
    pool: str | Sequence[str] | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> "ShearBoxFit":
    r"""Fit peak and residual lines to shear box stages: c and φ, free and through 0.

    The linear criterion of a shear box test, peak and residual (Hoek 2023,
    ch. 4, eqs. 1-2), is a straight line in $\sigma_n$-$\tau$:

    $$
    \tau_p = c_p + \sigma_n \tan\phi_p, \qquad \tau_r = c_r + \sigma_n \tan\phi_r
    $$

    with $\tau$ the shear stress at peak or residual, $\sigma_n$ the normal
    stress on the shear plane, $c$ the intercept and $\phi$ the friction
    angle. The fit is that line by ordinary least squares, $\tau = a + b\,
    \sigma_n$, so $c = a$ and $\phi = \arctan b$. Free, $b = S_{xy}/S_{xx}$
    and $a = \bar\tau - b\bar\sigma_n$; through the origin, $a = 0$ and

    $$
    \tan\phi = \frac{\sum \sigma_n \tau}{\sum \sigma_n^2}
    $$

    **Four lines per group, always:** peak and residual, each ``"free"`` and
    ``"through_origin"``. Report them together: a large intercept from a few
    stages is usually roughness, not cohesion. ``cohesion`` only picks which
    comes first. Each point also has its secant angle,
    $\phi_{sec} = \arctan(\tau/\sigma_n)$, which shows a curved envelope that
    one straight line hides; nothing is fitted to it.

    **The normal stress of each point:** a peak point takes
    ``normal_stress_at_peak`` where the row has it (the lab's stress on the
    corrected contact area), else ``applied_normal_stress``; a residual point
    ``normal_stress_at_residual``, else ``applied_normal_stress``. Each point
    records its ``normal_stress_basis``, and a line whose points mix bases
    says so. ``normal_stress="applied"`` takes ``applied_normal_stress``
    throughout.

    **Rows left out**, per strength, each counted once under the first reason
    that applies: the shear stress blank (``count_no_peak_shear_stress``),
    then no normal stress by the rule above (``count_no_peak_normal_stress``),
    and the same for residual. A stage with a peak and no residual is in the
    peak lines only. A strength's ``count`` plus these is the group's rows.

    **Valid for:** shear box and ring shear stages, soil or rock joint, with
    $\tau \ge 0$ and $\sigma_n \ge 0$ (a negative one is an error: check the
    sign). A free line needs 2 points or more at different $\sigma_n$, a line
    through the origin 1 point with $\sigma_n > 0$, and both a slope
    $b \ge 0$; a line outside these isn't fitted and has a ``no_fit_reason``.
    Every $b \ge 0$ has an angle below 90°, so there is no upper limit. A
    negative free intercept is reported as fitted, with a warning pointing to
    the line through the origin; nothing is forced. Each line holds over its
    range of $\sigma_n$ (``lowest_normal_stress`` to
    ``highest_normal_stress``); $c$ is an intercept at $\sigma_n = 0$, outside
    it. **Scatter:** ``r_squared``, centered, so a line through the origin can
    have a low or negative one; a free line of 2 points passes through both,
    so its R² is 1 by construction, and a line through the origin of 1 point
    has none. **Judgments taken:** none.

    **Assumptions:** a straight envelope over the stresses tested; the shear
    stresses as the lab picked them, by its failure criterion, read as given.
    Nothing labels a test as soil or rock joint, multistage, or effective or
    total stress: separate them with ``group_by=`` or a filter.

    **Not pooled unawares.** A strength's fitted rows in a group with more
    than one ``test_type`` (shear box and ring shear residuals differ) or
    ``failure_criterion`` (a blank is a value of its own) are an error naming
    each; peak and residual are checked apart. ``pool=`` pools those columns
    on purpose, and the result records it. ``multistage_test`` isn't read:
    group by it, or filter, to fit a multistage test apart.

    **Names:** the values are ``peak_friction_angle`` and the like, not
    ``effective_friction_angle``: a direct shear φ′ isn't a triaxial φ′ until
    selection converts it (SPEC §5). The lab's own pairs
    (``reported_peak_cohesion`` and ``reported_peak_friction_angle``, and the
    residual's) are listed beside the fit, each distinct pair with its count
    of stages, and not compared with it.

    The fit uses no coefficient or cited value: it is least squares on the
    criterion's own line, derived in docs/work/m17b-shear-box-fit.md,
    "Derivation".

    Parameters
    ----------
    df : pandas.DataFrame
        One row per stage, as ``p.shear_box()`` gives (or a CSV in
        ``ht.template("shear_box")``'s shape): ``peak_shear_stress`` and
        ``residual_shear_stress``, and ``applied_normal_stress``,
        ``normal_stress_at_peak`` and ``normal_stress_at_residual``, any of
        them blank. Where present, ``test_type``, ``failure_criterion`` and
        the lab's reported pairs are read, and the stage's identifiers kept.
    group_by : str or list of str, optional
        One set of lines per group, such as ``"specimen_id"`` (one test),
        ``"geology_unit"`` or ``"test_type"``, in sorted order with a blank
        group last. None fits every row together.
    cohesion : None or 0
        None makes the free line the main one, 0 the line through the origin;
        both are fitted either way.
    normal_stress : {"at_peak_or_residual", "applied"}
        Which normal stress each point is fitted against (above).
    pool : str or list of str, optional
        ``"test_type"`` and ``"failure_criterion"``, to fit rows with
        different values together on purpose.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.
    display_units : {"SI", "US"}, optional
        Fit in kPa (SI) or psf (US), or the stress unit the settings' display
        overrides name. None fits in ``peak_shear_stress``'s unit. φ doesn't
        depend on the unit.

    Returns
    -------
    ShearBoxFit
        ``.to_frame()`` has one row per group and line kind, peak and residual
        side by side; ``print()`` reads it; ``.groups`` holds the points.

    Raises
    ------
    HangtuError
        For a frame without a shear stress or a normal stress column, a
        negative stress on a row the fit uses, sources mixed without
        ``pool=``, a ``group_by`` column the frame doesn't have, a stress
        column without units or in a unit that isn't a stress, or an argument
        out of its range.

    Examples
    --------
    The peak and residual lines of each geology unit's shear box tests:

    >>> p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
    >>> p.set_geology_map(ht.examples.path("strata.csv"))
    >>> fit = ht.analysis.shear_box_fit(p.shear_box(), group_by="geology_unit")
    >>> print(fit)
    >>> fit.to_frame()[["line_kind", "peak_cohesion", "peak_friction_angle"]]
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if cohesion is not None and cohesion != 0:
        raise HangtuError(
            f"{_FUNCTION} cohesion must be None (the free line first) or 0 (the line "
            f"through the origin first), not {cohesion!r}. The fit is free or through "
            "the origin, and both lines are on the result."
        )
    if normal_stress not in _NORMAL_STRESS:
        raise HangtuError(
            f"{_FUNCTION} normal_stress must be "
            f"{' or '.join(map(repr, _NORMAL_STRESS))}, not {normal_stress!r}."
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
    pooled = _names(pool)
    wrong = [column for column in pooled if column not in _CHECKED]
    if wrong:
        raise HangtuError(
            f"{_FUNCTION} can't pool {', '.join(map(repr, wrong))}: pool= takes "
            f"{' and '.join(map(repr, _CHECKED))}, the columns it checks."
        )
    stresses, unit = _stresses(df, normal_stress, units, display_units)
    applied = stresses[_APPLIED]

    points: dict[str, dict[str, Any]] = {}
    negative = np.zeros(len(df), bool)
    for strength in _STRENGTHS:
        shear = stresses[_SHEAR[strength]]
        if normal_stress == "applied":
            normal = applied
            basis = np.where(np.isnan(applied), "", "applied")
        else:
            at = stresses[_AT[strength]]
            normal = np.where(np.isnan(at), applied, at)
            basis = np.where(
                ~np.isnan(at),
                f"at_{strength}",
                np.where(np.isnan(applied), "", "applied"),
            )
        no_shear, no_normal = _left_out(strength)
        reasons = np.full(len(df), "", dtype=object)
        reasons[np.isnan(shear)] = no_shear
        reasons[(reasons == "") & np.isnan(normal)] = no_normal
        usable = reasons == ""
        negative |= usable & ((shear < 0) | (normal < 0))
        reported = (
            _reported(
                df,
                units,
                unit,
                f"reported_{strength}_cohesion",
                f"reported_{strength}_friction_angle",
            )
            if unit is not None
            else None
        )
        points[strength] = {
            "shear": shear,
            "normal": normal,
            "basis": basis,
            "reasons": reasons,
            "reported": reported,
        }
    if negative.any():
        raise HangtuError(
            f"Rows {rows_text(df.index[negative])} have a negative shear or normal "
            "stress, which a shear box test can't give: it shears under compression, "
            "and the residual is a magnitude. Check the sign of those rows' stresses."
        )

    notes = [
        f"{column} not given: the fit couldn't check that a line's rows share one."
        for column in _CHECKED
        if column not in df.columns
    ]
    if pooled:
        notes.append(f"Pooled on purpose: {', '.join(pooled)}.")
    groups: list[dict[str, Any]] = []
    negative_intercepts: list[str] = []
    for key, rows in group_keys(df, by):
        strengths = {}
        for strength in _STRENGTHS:
            fitted = rows & (points[strength]["reasons"] == "")
            _check_sources(
                _FUNCTION, df, key, fitted, _CHECKED, pooled, what=f" {strength}"
            )
            record = _strength(df, rows, strength, points[strength], cohesion)
            strengths[strength] = record
            free = next(line for line in record["lines"] if line["line_kind"] == "free")
            if free["no_fit_reason"] is None and free["cohesion"] < 0:
                negative_intercepts.append(f"{_label(key)} ({strength})")
        groups.append(
            {"key": key, "count_rows": int(rows.sum()), "strengths": strengths}
        )

    if negative_intercepts:
        warn(
            f"{_FUNCTION}: the free line's intercept is negative in "
            f"{', '.join(negative_intercepts)}, so c < 0. It is reported as fitted; "
            'the line through the origin (line_kind "through_origin") is on the '
            "result beside it."
        )
    notes.append(
        "c is an intercept at σn = 0, outside each line's range of σn "
        "(lowest_normal_stress to highest_normal_stress); the line holds over that "
        "range."
    )
    return ShearBoxFit(
        function="shear_box_fit",
        unit=unit,
        notes=tuple(notes),
        judgments=dict(df.attrs.get("judgments", {})),
        hangtu_version=version("hangtu"),
        judgments_file=judgments_file(df),
        by=tuple(by),
        pooled=tuple(pooled),
        cohesion=cohesion,
        normal_stress=normal_stress,
        display_units=display_units,
        depth_units=_place_units(df, units),
        groups=tuple(groups),
    )


def _stresses(
    df: pd.DataFrame,
    normal_stress: str,
    units: Mapping[str, str] | None,
    display_units: str | None,
) -> tuple[dict[str, np.ndarray], str | None]:
    """Return the shear and normal stresses in the fit's unit, and its name.

    A column the frame doesn't have, or that is blank throughout, is all NaN
    and needs no unit (a template's CSV has every column).
    """
    shear = list(_SHEAR.values())
    normal = [_APPLIED] if normal_stress == "applied" else [*_AT.values(), _APPLIED]
    template = 'ht.template("shear_box") has the columns it reads.'
    if not any(column in df.columns for column in shear):
        raise ColumnError(
            f"{_FUNCTION} needs a shear stress: df has neither "
            f"{' nor '.join(map(repr, shear))}. Use p.shear_box(); {template}"
        )
    if not any(column in df.columns for column in normal):
        raise ColumnError(
            f"{_FUNCTION} with normal_stress={normal_stress!r} needs a normal stress: "
            f"df has no {' or '.join(map(repr, normal))}. Use p.shear_box(); {template}"
        )
    columns = [*shear, *normal]
    given = [
        column
        for column in columns
        if column in df.columns and not df[column].isna().all()
    ]
    declared = _units.resolve_units(df, given, units, analysis=True)
    parsed = {column: _units.parse_unit(declared[column], column) for column in given}
    for column, parsed_unit in parsed.items():
        _units.check_dimension(parsed_unit, "stress", column)
    blank = np.full(len(df), np.nan)
    values = {column: blank for column in [*_SHEAR.values(), *_AT.values(), _APPLIED]}
    unit = None
    if display_units is None:
        reference = next(
            (column for column in [*shear, *normal] if column in given), None
        )
        if reference is not None:
            unit = declared[reference]
            for column in given:
                values[column] = _units.convert(
                    numeric_column(df, column),
                    parsed[column],
                    "stress",
                    parsed[reference],
                )
    else:
        for column in given:
            values[column], unit = _units.to_display(
                numeric_column(df, column), declared[column], "stress", display_units
            )
    return values, unit


def _strength(
    df: pd.DataFrame,
    rows: np.ndarray,
    strength: str,
    data: dict[str, Any],
    cohesion: float | None,
) -> dict[str, Any]:
    """Fit one group's peak or residual: both lines, its points and what was left."""
    reasons = data["reasons"]
    fitted = rows & (reasons == "")
    normal = data["normal"][fitted]
    shear = data["shear"][fitted]
    bases = data["basis"][fitted]
    lines = {
        kind: _line(normal, shear, None if kind == "free" else 0.0, kind)
        for kind in _KINDS
    }
    order = list(_KINDS) if cohesion is None else list(reversed(_KINDS))
    counted = dict(zip(*np.unique(bases, return_counts=True), strict=True))
    notes = []
    if len(counted) > 1:
        listed = ", ".join(
            f"{basis} ({count} point{'s' if count > 1 else ''})"
            for basis, count in counted.items()
        )
        notes.append(f"σn from more than one basis: {listed}.")
    basis = (
        "mixed" if len(counted) > 1 else (str(next(iter(counted))) if counted else None)
    )
    identifiers = [column for column in _IDENTIFIERS if column in df.columns]
    with np.errstate(divide="ignore", invalid="ignore"):
        secant = np.where(normal > 0, np.degrees(np.arctan(shear / normal)), np.nan)
    points = [
        {
            "row": row,
            **{column: _cell(df.at[row, column]) for column in identifiers},
            "normal_stress": float(normal[j]),
            "shear_stress": float(shear[j]),
            "normal_stress_basis": str(bases[j]),
            "secant_friction_angle": float(secant[j]),
        }
        for j, row in enumerate(df.index[fitted])
    ]
    return {
        "strength": strength,
        "lines": [lines[kind] for kind in order],
        "normal_stress_basis": basis,
        "reported_pairs": _pairs(data["reported"], fitted),
        **{name: int((rows & (reasons == name)).sum()) for name in _left_out(strength)},
        "notes": notes,
        "points": points,
    }


def _line(
    normal: np.ndarray, shear: np.ndarray, intercept: float | None, kind: str
) -> dict[str, Any]:
    """Fit one line τ = c + σn tan φ, free or through the origin (Derivation)."""
    line = line_fit(normal, shear, intercept=intercept, x_name="normal stress")
    reason = line.no_fit_reason
    slope = line.slope
    if reason is None and slope < 0:
        reason = f"slope tan φ = {float(f'{slope:.4g}')} is below 0: no friction angle"
    notes = []
    if reason is None and kind == "free" and line.count == 2:
        notes.append("2 points: the line passes through both, so R² = 1.")
    fitted = reason is None
    return {
        "line_kind": kind,
        "cohesion": float(line.intercept) if fitted else np.nan,
        "friction_angle": math.degrees(math.atan(slope)) if fitted else np.nan,
        "line_slope": float(slope) if fitted else np.nan,
        "r_squared": float(line.r_squared) if fitted else np.nan,
        "count": line.count,
        "lowest_normal_stress": float(np.min(normal)) if len(normal) else np.nan,
        "highest_normal_stress": float(np.max(normal)) if len(normal) else np.nan,
        "no_fit_reason": reason,
        "notes": notes,
    }


@dataclass(frozen=True, repr=False)
class ShearBoxFit(_DerivedResult):
    """The fit ``ht.analysis.shear_box_fit()`` returns.

    Use ``.to_frame()`` for a table with one row per group and line kind,
    peak and residual side by side, ``.to_dict()`` for a report, or
    ``print(fit)`` to read it. ``.groups`` holds each group's lines and the
    points of each strength. The text is a view of the same numbers.
    """

    #: The columns grouped by, in order.
    by: tuple[str, ...]
    #: The columns pooled on purpose (``pool=``).
    pooled: tuple[str, ...]
    #: None for the free line first, 0 for the line through the origin first.
    cohesion: float | None
    #: ``"at_peak_or_residual"`` or ``"applied"``: the normal stress fitted.
    normal_stress: str
    #: The system the stresses were converted to before fitting, None if not.
    display_units: str | None
    #: ``{column: unit}`` of the points' ``depth``, ``elevation`` and
    #: ``ground_level``, kept as given; a column with no declared unit is
    #: missing here.
    depth_units: dict[str, str]
    #: One record per group: its key, its number of rows and, under
    #: ``strengths``, a record for ``"peak"`` and ``"residual"``, each with its
    #: two ``lines`` (the main one first), ``normal_stress_basis``,
    #: ``reported_pairs``, its counts of rows left out, ``notes`` and
    #: ``points``.
    groups: tuple[dict[str, Any], ...]

    def _columns(self) -> list[str]:
        columns = [*self.by, "line_kind"]
        for s in _STRENGTHS:
            columns += [
                f"{s}_cohesion",
                f"{s}_friction_angle",
                f"{s}_r_squared",
                f"{s}_count",
                f"{s}_lowest_normal_stress",
                f"{s}_highest_normal_stress",
                f"{s}_normal_stress_basis",
                f"reported_{s}_cohesion",
                f"reported_{s}_friction_angle",
                f"count_reported_{s}_pairs",
                *_left_out(s),
                f"{s}_no_fit_reason",
            ]
        return columns

    def to_frame(self) -> pd.DataFrame:
        """Return one row per group and line kind, the main line of each group first.

        ``line_kind`` is ``"free"`` or ``"through_origin"``; through the origin,
        the cohesion columns are 0. Peak and residual are side by side, so
        ``peak_friction_angle`` is one column. The lab's pair is given when a
        strength's fitted stages report one; with more, it is blank and
        ``count_reported_…_pairs`` says how many. ``attrs["units"]`` gives the
        unit of each column that has one; angles are in degrees.
        """
        rows = []
        for group in self.groups:
            strengths = group["strengths"]
            for index, kind in enumerate(
                line["line_kind"] for line in strengths["peak"]["lines"]
            ):
                row: dict[str, Any] = {**group["key"], "line_kind": kind}
                for s in _STRENGTHS:
                    record = strengths[s]
                    line = record["lines"][index]
                    pairs = record["reported_pairs"] or []
                    one = pairs[0] if len(pairs) == 1 else None
                    row |= {
                        f"{s}_cohesion": line["cohesion"],
                        f"{s}_friction_angle": line["friction_angle"],
                        f"{s}_r_squared": line["r_squared"],
                        f"{s}_count": line["count"],
                        f"{s}_lowest_normal_stress": line["lowest_normal_stress"],
                        f"{s}_highest_normal_stress": line["highest_normal_stress"],
                        f"{s}_normal_stress_basis": record["normal_stress_basis"],
                        f"reported_{s}_cohesion": one["cohesion"] if one else np.nan,
                        f"reported_{s}_friction_angle": (
                            one["friction_angle"] if one else np.nan
                        ),
                        f"count_reported_{s}_pairs": len(pairs),
                        **{name: record[name] for name in _left_out(s)},
                        f"{s}_no_fit_reason": line["no_fit_reason"],
                    }
                rows.append(row)
        frame = pd.DataFrame(rows, columns=self._columns())
        stresses = [
            f"{prefix}{s}_{name}"
            for s in _STRENGTHS
            for prefix, name in (
                ("", "cohesion"),
                ("", "lowest_normal_stress"),
                ("", "highest_normal_stress"),
                ("reported_", "cohesion"),
            )
        ]
        angles = [
            f"{prefix}{s}_friction_angle"
            for s in _STRENGTHS
            for prefix in ("", "reported_")
        ]
        frame.attrs["units"] = {
            **(dict.fromkeys(stresses, self.unit) if self.unit else {}),
            **dict.fromkeys(angles, "deg"),
        }
        return frame

    def __str__(self) -> str:
        from hangtu.plot._overlays import format_number  # plot imports analysis

        unit = f" {self.unit}" if self.unit else ""
        title = "Shear box fit"
        if self.cohesion == 0:
            title += ", the line through the origin first"
        lines = [title]
        for group in self.groups:
            indent = "  " if self.by else ""
            if self.by:
                lines.append(f"{_label(group['key'])}: {group['count_rows']} rows")
            for s in _STRENGTHS:
                record = group["strengths"][s]
                main, other = record["lines"]
                head = f"{indent}{s}, {_kind_text(main['line_kind'])}: "
                if main["no_fit_reason"]:
                    lines.append(f"{head}not fitted: {main['no_fit_reason']}")
                else:
                    lines.append(
                        head
                        + _line_text(main, unit, format_number)
                        + f", {main['count']} point{'s' if main['count'] != 1 else ''}"
                        f", σn {format_number(main['lowest_normal_stress'])} to "
                        f"{format_number(main['highest_normal_stress'])}{unit}"
                    )
                sub = indent + "  "
                other_head = f"{sub}{_kind_text(other['line_kind'])}: "
                if other["no_fit_reason"]:
                    lines.append(f"{other_head}not fitted: {other['no_fit_reason']}")
                else:
                    lines.append(other_head + _line_text(other, unit, format_number))
                left_out = [
                    f"{record[name]} {name.removeprefix('count_').replace('_', ' ')}"
                    for name in _left_out(s)
                    if record[name]
                ]
                if left_out:
                    lines.append(f"{sub}left out: {', '.join(left_out)}")
                for pair in record["reported_pairs"] or []:
                    lines.append(
                        f"{sub}lab: c = {_reported_text(pair['cohesion'])}{unit}, "
                        f"φ = {_reported_text(pair['friction_angle'])}° "
                        f"({pair['count']} stage{'s' if pair['count'] > 1 else ''})"
                    )
                notes = [*record["notes"], *main["notes"], *other["notes"]]
                lines.extend(f"{sub}{note}" for note in notes)
        return "\n".join([*lines, *self.notes])


def _kind_text(kind: str) -> str:
    return "free" if kind == "free" else "through the origin"


def _line_text(line: dict[str, Any], unit: str, format_number: Any) -> str:
    cohesion = (
        f"c = {format_number(line['cohesion'])}{unit}, "
        if line["line_kind"] == "free"
        else ""
    )
    r_squared = line["r_squared"]
    r_text = "—" if math.isnan(r_squared) else f"{r_squared:.3f}"
    return f"{cohesion}φ = {format_number(line['friction_angle'])}°, R² = {r_text}"


def _reported_text(value: float) -> str:
    return "—" if math.isnan(value) else f"{value:g}"
