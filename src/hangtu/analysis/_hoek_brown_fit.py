"""The intact Hoek-Brown fit of rock triaxial and UCS failures.

The spec is docs/work/m17c-hoek-brown-fit.md; decisions cited by number are its
Spec's.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd

from hangtu import _judgments
from hangtu import units as _units
from hangtu._data import flag_column, numeric_column, rows_text
from hangtu.analysis._derived import _DerivedResult, judgments_file
from hangtu.analysis._fit_groups import (
    _cell,
    _check_sources,
    _convert_reported,
    _label,
    _names,
    _pairs,
)
from hangtu.analysis._judgment_values import read_judgments
from hangtu.analysis._line_fit import line_fit
from hangtu.analysis._triaxial import STRESS_COLUMNS
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.stats._rows import group_keys

_FUNCTION = "hoek_brown_fit()"
_ARGUMENT = "fixed_intact_compressive_strength"
_KINDS = ("free", "fixed_strength")
_STAGES = ("all", "single_stage")
_STRESS = ("total", "effective")
_MODE = "failure_mode"
#: The columns a fit's rows must share one value of, unless pooled (decision 7).
_CHECKED = ["failure_criterion"]
#: The columns that identify a fitted point, kept with its stresses.
_IDENTIFIERS = (
    "loca_id",
    "specimen_id",
    "sample_reference",
    "specimen_reference",
    "test_type",
    "test_stage",
)
#: The counts of rows left out, in the order a row is counted (decision 9).
_LEFT_OUT = (
    "count_no_principal_stresses",
    "count_no_effective_stresses",
    "count_other_failure_mode",
    "count_multistage_left_out",
)
_REPORTED = (
    "reported_intact_compressive_strength",
    "reported_intact_hoek_brown_constant",
)
_PAIR = ("intact_compressive_strength", "intact_hoek_brown_constant")
_NO_STRENGTH = f"no σci given: pass {_ARGUMENT}= or add it to the judgments file"
#: Hoek (2007), ch. 11: the regression's quality mark (p. 4).
_GOOD_R_SQUARED = 0.9
#: Hoek (2007), ch. 11, p. 2: the points a fit should have.
_ENOUGH_POINTS = 5


def hoek_brown_fit(
    df: pd.DataFrame,
    *,
    group_by: str | Sequence[str] | None = None,
    failure_modes: str | Sequence[str | None] | None = None,
    fixed_intact_compressive_strength: str | Mapping[Any, str] | None = None,
    judgments: Any = None,
    multistage: bool = True,
    stress: str = "total",
    pool: str | Sequence[str] | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> "HoekBrownFit":
    r"""Fit σci and mi of intact rock to triaxial and UCS failures, free and σci fixed.

    The Hoek-Brown criterion for intact rock (Hoek 2007, ch. 11, eq. 5, p. 2):

    $$
    \sigma_1 = \sigma_3 + \sigma_{ci}
        \left( m_i \frac{\sigma_3}{\sigma_{ci}} + 1 \right)^{0.5}
    $$

    with $\sigma_1$ and $\sigma_3$ the major and minor principal stresses at
    failure, $\sigma_{ci}$ the intact compressive strength and $m_i$ the
    Hoek-Brown constant of intact rock. Moving $\sigma_3$ across and squaring
    gives a straight line (eq. 6, p. 4):

    $$
    (\sigma_1 - \sigma_3)^2 = m_i \sigma_{ci}\, \sigma_3 + \sigma_{ci}^2
    $$

    so with $x = \sigma_3$ and $y = (\sigma_1 - \sigma_3)^2$, the
    least-squares line $y = a + b\,x$ gives $\sigma_{ci} = \sqrt{a}$ and
    $m_i = b / \sigma_{ci}$ (eqs. 7-8). **Two fits per group:** ``"free"``,
    with $b = S_{xy}/S_{xx}$ and $a = \bar y - b \bar x$, which reproduces
    Hoek's eqs. 7-8; and ``"fixed_strength"``, with $\sigma_{ci}$ fixed by
    the engineer and

    $$
    m_i = \frac{\sum \sigma_3 \left( (\sigma_1 - \sigma_3)^2
        - \sigma_{ci}^2 \right)}{\sigma_{ci} \sum \sigma_3^2}
    $$

    R² is the centered one of the line in $x$-$y$, which for the free fit is
    Hoek's eq. 9: "high quality triaxial test data will usually give a
    coefficient of determination r² of greater than 0.9" (p. 4). A fit below
    0.9 gets a note.

    **UCS tests are points at $\sigma_3 = 0$** in the same fit, as Hoek's
    regression treats them: a row with ``cell_pressure`` 0. The fitted rows
    at $\sigma_3 = 0$ also give ``uniaxial_count`` and ``uniaxial_mean``,
    printed beside the free σci as a check; they never fix it.

    **σci fixed** is a judgment (SPEC §4), so nothing picks it from the data.
    It comes from ``fixed_intact_compressive_strength=``, else the judgments
    file's ``fixed_intact_compressive_strength`` (keyed by one of the
    ``group_by`` columns, with a ``project:`` value used, with a warning, for
    a group not listed). An argument replaces the file's, with a warning.
    Without either, the fixed fit is missing, with a reason, and the free fit
    is the result. Each value fixed is recorded with its source.

    **Not pooled unawares.** A group's fitted rows with more than one
    ``failure_criterion`` (a blank is a value of its own) are an error naming
    each; ``pool="failure_criterion"`` fits them together on purpose, and
    the result records it. ``test_type`` isn't checked: UCS and triaxial
    tests are one method's points by design.

    **Failure modes are as written; you name the ones to fit.** The criterion
    holds only for shear failures: "remove the results of tests exhibiting
    other types of failure", such as axial splitting or failure along a
    defect (Hoek 2023, ch. 3, p. 6). ``failure_mode`` is the lab's own text,
    so hangtu doesn't guess which values mean shear. When the column has any
    value, ``failure_modes=`` is required and lists the values to fit,
    matched exactly (``None`` fits rows with a blank mode); the other rows
    are left out and counted by mode. When the column is missing or blank,
    every row is fitted, with a note.

    **Rows left out**, each counted once under the first reason that
    applies: σ3 or σ1 blank (``count_no_principal_stresses``), then, with
    ``stress="effective"``, σ′3 or σ′1 blank
    (``count_no_effective_stresses``), then a mode not named
    (``count_other_failure_mode``), then, in the single-stage fit, a
    multistage stage (``count_multistage_left_out``). ``count`` plus these is
    the group's rows.

    **Multistage stages are fitted with and without.** Later stages of a
    multistage test can bias mi low (a judgment for review, unsourced). A
    group with a multistage stage (``multistage_test`` True) gets the fits
    ``"all"`` and ``"single_stage"``; ``multistage`` picks the main one, and
    both are on the result and in the summary.

    **Valid for:** $0 \le \sigma_3 < 0.5\,\sigma_{ci}$ and "at least five
    well spaced data points" (Hoek 2007, ch. 11, p. 2), shear failures only
    (Hoek 2023, ch. 3, p. 6). Fewer than 5 points is fitted, with a warning;
    points at $\sigma_3 \ge 0.5\,\sigma_{ci}$ of that fit's own σci are
    kept and counted (``count_beyond_confining_range``), with a warning. To
    refit without them, filter the rows and call again: the limit moves with
    the σci each fit gives, so nothing drops them automatically. A free fit
    needs 2 points at different σ3, a fixed fit 1 point with $\sigma_3 > 0$;
    an intercept $a \le 0$ (no real σci) or a slope $b \le 0$ (mi not
    positive) isn't fitted. Such a fit has a ``no_fit_reason``. A negative
    σ3 (tension) or σ1 < σ3 is an error. Each fit holds over its range of σ3
    (``lowest_minor_principal_stress`` to
    ``highest_minor_principal_stress``). **Judgments taken:** σci, for the
    fixed fit only.

    **The back-calculated mi of each point,**
    $m_i = ((\sigma_1 - \sigma_3)^2 - \sigma_{ci}^2) / (\sigma_{ci}\sigma_3)$
    with that fit's σci, is on the fit's points
    (``back_calculated_hoek_brown_constant``), NaN at σ3 = 0. It shows whether
    one curve suits the group, but it is ill-conditioned at small
    σ3/σci: with σci = 50 MPa and a true mi of 8, a 5 % error in σ1 at
    σ3 = 0.5 MPa gives mi = 19.2. Below about 0.1 σci, read it with care.
    Nothing is fitted to it.

    **Assumptions:** the stresses as the lab reported them at failure.
    Hoek's criterion is in effective stress; the default ``stress="total"``
    fits the total pair, which assumes no pore pressure in the specimen, as
    in a dry rock test (ASTM D7012 measures none).

    **Names:** the fitted values take the parameter's names,
    ``intact_compressive_strength`` and ``intact_hoek_brown_constant``: UCS
    and triaxial points are one method's input (SPEC §5). σci here is a
    fitted parameter, not soil's ``unconfined_compressive_strength`` (q_u).
    The lab's own pairs (``reported_intact_compressive_strength`` and
    ``reported_intact_hoek_brown_constant``) are listed beside the fit, each
    distinct pair with its count of rows, and not compared with it.

    The fit uses no coefficient or cited value: it is least squares on
    Hoek's own line, derived in docs/work/m17c-hoek-brown-fit.md,
    "Derivation"; Hoek (2007, ch. 11) eq. 5 is the criterion and eqs. 6-8
    the regression it reproduces.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per specimen or stage at failure, as ``p.triaxial()`` gives
        or a CSV in ``ht.template("triaxial")``'s shape after
        ``ht.analysis.triaxial_failure_stresses()``: the principal stresses
        at failure (``minor_principal_stress_at_failure`` and
        ``major_principal_stress_at_failure``, or the effective pair). Where
        present, ``failure_mode``, ``multistage_test``, the lab's reported
        pair and the identifiers are read.
    group_by : str or list of str, optional
        One set of fits per group, such as ``"geology_unit"`` or
        ``"specimen_id"``, in sorted order with a blank group last. None fits
        every row together.
    failure_modes : str or list of str, optional
        The ``failure_mode`` values to fit, as written; ``None`` in the list
        fits rows with a blank mode. Required when the column has any value.
    fixed_intact_compressive_strength : str or dict, optional
        σci for the fixed fit, with its unit: ``"61 MPa"`` for every group,
        or a mapping from a group's key (its value, or a tuple of values with
        several ``group_by`` columns) to one, such as
        ``{"Sandstone": "61 MPa"}``. A key that matches no group warns; a
        group the mapping doesn't list has no fixed fit, with that reason.
    judgments : Judgments or path, optional
        ``ht.judgments(path)``, ``p.judgments`` or a path to a judgments file,
        for the fixed σci when the argument doesn't give it. By default the
        project's, from ``df.attrs["judgments_file"]``.
    multistage : bool
        True makes the fit with multistage stages the main one; False the fit
        of single-stage rows only. Both are made when a group has multistage
        stages.
    stress : {"total", "effective"}
        Which principal stresses are fitted (above).
    pool : str, optional
        ``"failure_criterion"``, to fit rows with different criteria together
        on purpose.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.
    display_units : {"SI", "US"}, optional
        Fit in kPa (SI) or psf (US), or the stress unit the settings' display
        overrides name, such as MPa or psi. None fits in σ3's unit. mi doesn't
        depend on the unit.

    Returns
    -------
    HoekBrownFit
        ``.to_frame()`` has one row per group, stage set and fit;
        ``print()`` reads it; ``.groups`` holds the points.

    Raises
    ------
    HangtuError
        For a frame without the principal stresses, a negative σ3 or
        σ1 < σ3, a ``failure_mode`` column with values and no
        ``failure_modes=``, a mode named that no row has, a fixed σci without
        a unit or not positive, rows with different failure criteria without
        ``pool=``, a ``group_by`` column the frame doesn't have,
        a stress column without units or in a unit that isn't a stress, or an
        argument out of its range.

    Examples
    --------
    A hand-built set in MPa: one UCS test and four triaxial tests, all shear
    failures (Hoek 2007, ch. 11, Table 1):

    >>> df = pd.DataFrame({
    ...     "test_type": ["UCS", *["Triaxial"] * 4],
    ...     "cell_pressure": [0, 5, 7.5, 15, 20],
    ...     "deviator_stress_at_failure": [38.3, 67.4, 73.0, 100.6, 114.3],
    ... })
    >>> df = ht.set_units(df, {"cell_pressure": "MPa",
    ...                        "deviator_stress_at_failure": "MPa"})
    >>> df = ht.analysis.triaxial_failure_stresses(df)
    >>> fit = ht.analysis.hoek_brown_fit(
    ...     df, fixed_intact_compressive_strength="38.3 MPa"
    ... )
    >>> print(fit)
    >>> fit.to_frame()[["line_kind", "intact_compressive_strength",
    ...                 "intact_hoek_brown_constant", "r_squared"]]

    Each geology unit of a project, σci fixed from its judgments file:

    >>> fit = ht.analysis.hoek_brown_fit(
    ...     rock, group_by="geology_unit", failure_modes=["Shear"],
    ...     judgments=p.judgments,
    ... )
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if stress not in _STRESS:
        raise HangtuError(
            f"{_FUNCTION} stress must be {' or '.join(map(repr, _STRESS))}, not "
            f"{stress!r}."
        )
    if not isinstance(multistage, bool):
        raise HangtuError(
            f"{_FUNCTION} multistage must be True or False, not {multistage!r}."
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
            f"{' and '.join(map(repr, _CHECKED))}, the column it checks. UCS and "
            "triaxial test types pool without asking."
        )
    total_minor, total_major, minor, major, unit = _stresses(
        df, stress, units, display_units
    )
    prime = "′" if stress == "effective" else ""
    negative = minor < 0
    if negative.any():
        raise HangtuError(
            f"Rows {rows_text(df.index[negative])} have σ{prime}3 < 0 (tension), "
            "which this fit doesn't take: it fits compression failures, UCS at "
            "σ3 = 0. Check the sign of those rows' cell pressures, or leave them out."
        )
    reversed_ = major < minor
    if reversed_.any():
        raise HangtuError(
            f"Rows {rows_text(df.index[reversed_])} have σ{prime}1 < σ{prime}3, which "
            "can't be a compression failure. Check the cell pressure and deviator "
            "stress of those rows."
        )
    other_mode, modes, mode_note = _modes(df, failure_modes)
    reasons = np.full(len(df), "", dtype=object)
    reasons[np.isnan(total_minor) | np.isnan(total_major)] = _LEFT_OUT[0]
    reasons[(reasons == "") & (np.isnan(minor) | np.isnan(major))] = _LEFT_OUT[1]
    reasons[(reasons == "") & other_mode] = _LEFT_OUT[2]
    has_multistage = "multistage_test" in df.columns
    staged = np.array(
        flag_column(df, "multistage_test", "Fill it in, or drop the column."),
        dtype=object,
    )
    multistaged = staged == True  # noqa: E712 (None is blank)
    keyed = group_keys(df, by)
    strengths, record = _strengths(
        fixed_intact_compressive_strength, judgments, df, by, keyed, unit
    )
    reported = _reported(df, units, unit)

    notes = []
    if mode_note:
        notes.append(mode_note)
    notes.extend(
        f"{column} not given: the fit couldn't check that the rows share one."
        for column in _CHECKED
        if column not in df.columns
    )
    if pooled:
        notes.append(f"Pooled on purpose: {', '.join(pooled)}.")
    if not has_multistage:
        notes.append("multistage_test not given: multistage stages weren't told apart.")
    if stress == "total":
        notes.append(
            "Total stresses fitted: Hoek's criterion is in effective stress, so the "
            "fit assumes no pore pressure in the specimen."
        )

    groups: list[dict[str, Any]] = []
    few: list[str] = []
    beyond: list[str] = []
    for (key, rows), strength in zip(keyed, strengths, strict=True):
        candidates = rows & (reasons == "")
        _check_sources(_FUNCTION, df, key, candidates, _CHECKED, pooled)
        left_out = {
            name: int((rows & (reasons == name)).sum()) for name in _LEFT_OUT[:3]
        }
        sets = {"all": candidates}
        if (candidates & multistaged).any():
            sets["single_stage"] = candidates & ~multistaged
        main = "all" if multistage or "single_stage" not in sets else "single_stage"
        order = [main, *(name for name in _STAGES if name in sets and name != main)]
        label = _label(key)
        fits = []
        for name in order:
            fitted = sets[name]
            counts = {
                **left_out,
                _LEFT_OUT[3]: int((candidates & ~fitted).sum()),
            }
            pairs = _pairs(reported, fitted, _PAIR)
            stage_fits = [
                _fit(df, fitted, minor, major, kind, strength, multistaged)
                for kind in _KINDS
            ]
            if name == "single_stage" and not fitted.any():
                for fit in stage_fits:
                    fit["no_fit_reason"] = "every stage is multistage"
            for fit in stage_fits:
                fit.update(counts)
                fit["stages"] = name
                fit["reported_pairs"] = pairs
            where = label if name == "all" else f"{label}, single stage"
            if any(
                fit["no_fit_reason"] is None and fit["count"] < _ENOUGH_POINTS
                for fit in stage_fits
            ):
                few.append(f"{where} ({stage_fits[0]['count']} points)")
            outside = [
                f"{fit['count_beyond_confining_range']} "
                f"({_kind_text(fit['line_kind'])})"
                for fit in stage_fits
                if fit["count_beyond_confining_range"]
            ]
            if outside:
                beyond.append(f"{where}: {', '.join(outside)}")
            fits.extend(stage_fits)
        excluded = rows & (reasons != "")
        groups.append(
            {
                "key": key,
                "count_rows": int(rows.sum()),
                "fits": fits,
                "count_by_failure_mode": _mode_counts(df, rows & other_mode, reasons),
                "left_out": _left_out_rows(df, excluded, reasons, minor, major),
            }
        )

    if few:
        warn(
            f"{_FUNCTION}: fewer than {_ENOUGH_POINTS} points in {'; '.join(few)}. "
            'Hoek (2007, ch. 11, p. 2): "At least five well spaced data points '
            'should be included in the analysis."'
        )
    if beyond:
        warn(
            f"{_FUNCTION}: points at σ3 ≥ 0.5 σci of their fit in {'; '.join(beyond)}, "
            "beyond the range 0 < σ3 < 0.5 σci of Hoek (2007, ch. 11, p. 2). They "
            "are kept and counted (count_beyond_confining_range). To fit without "
            "them, filter the rows on σ3 and call again."
        )
    return HoekBrownFit(
        function="hoek_brown_fit",
        unit=unit,
        notes=tuple(notes),
        judgments={
            **df.attrs.get("judgments", {}),
            **({_ARGUMENT: record} if record else {}),
        },
        hangtu_version=version("hangtu"),
        judgments_file=judgments_file(df),
        stress=stress,
        by=tuple(by),
        pooled=tuple(pooled),
        failure_modes=modes,
        multistage=multistage,
        display_units=display_units,
        groups=tuple(groups),
    )


def _stresses(
    df: pd.DataFrame,
    stress: str,
    units: Mapping[str, str] | None,
    display_units: str | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, str]:
    """Return the total pair and the fitted pair in σ3's unit, and its name."""
    total = list(STRESS_COLUMNS[:2])
    fitted = list(STRESS_COLUMNS[2:] if stress == "effective" else STRESS_COLUMNS[:2])
    columns = list(dict.fromkeys([*total, *fitted]))
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ColumnError(
            f"df has no column {', '.join(map(repr, missing))}. {_FUNCTION} fits the "
            "principal stresses at failure: call "
            "ht.analysis.triaxial_failure_stresses() on the rows first (p.triaxial() "
            'has them already). ht.template("triaxial") has the columns it reads.'
        )
    declared = _units.resolve_units(df, columns, units, analysis=True)
    parsed = {column: _units.parse_unit(declared[column], column) for column in columns}
    for column, parsed_unit in parsed.items():
        _units.check_dimension(parsed_unit, "stress", column)
    values = {}
    unit = declared[fitted[0]]
    assert unit is not None  # resolve_units(analysis=True) raises for a missing one
    if display_units is None:
        for column in columns:
            values[column] = _units.convert(
                numeric_column(df, column), parsed[column], "stress", parsed[fitted[0]]
            )
    else:
        for column in columns:
            values[column], shown = _units.to_display(
                numeric_column(df, column), declared[column], "stress", display_units
            )
            assert shown is not None  # a stress has a display unit in both systems
            unit = shown
    total_minor, total_major = (values[column] for column in total)
    minor, major = (values[column] for column in fitted)
    return total_minor, total_major, minor, major, unit


def _modes(
    df: pd.DataFrame, failure_modes: str | Sequence[str | None] | None
) -> tuple[np.ndarray, tuple[str | None, ...] | None, str | None]:
    """Return the rows of a mode not named, the modes named and a note (decision 5)."""
    names = (
        None
        if failure_modes is None
        else [failure_modes]
        if isinstance(failure_modes, str)
        else list(failure_modes)
    )
    values = (
        df[_MODE].astype(object)
        if _MODE in df.columns
        else pd.Series(None, index=df.index, dtype=object)
    )
    blank = (values.isna() | (values.astype(str).str.strip() == "")).to_numpy()
    if blank.all():
        if names is not None:
            state = "blank throughout" if _MODE in df.columns else "missing"
            raise HangtuError(
                f"{_FUNCTION} failure_modes= names the modes to fit, but df's "
                f"{_MODE} column is {state}, so no row has a mode to match. Leave "
                "failure_modes= out to fit every row, or fill in the column."
            )
        note = (
            f"{_MODE} not given: every row is fitted, so splitting and defect "
            "failures can't be told from shear (Hoek 2023, ch. 3, p. 6)."
        )
        return np.zeros(len(df), bool), None, note
    counts = values.where(~blank, None).value_counts(dropna=False, sort=False)
    listed = ", ".join(
        f"{'blank' if pd.isna(mode) else repr(mode)} ({count} "
        f"row{'s' if count != 1 else ''})"
        for mode, count in counts.items()
    )
    if names is None:
        shear = next((mode for mode in counts.index if not pd.isna(mode)), "Shear")
        raise HangtuError(
            f"{_FUNCTION} needs failure_modes= because df's {_MODE} column has "
            f"values: {listed}. The criterion holds for shear failures only (Hoek "
            "2023, ch. 3, p. 6), and the modes are the lab's own words, so name the "
            f"shear ones as written, e.g. failure_modes=[{shear!r}]."
        )
    present = {mode for mode in values[~blank]}
    unknown = [name for name in names if name is not None and name not in present]
    if unknown:
        raise HangtuError(
            f"{_FUNCTION} failure_modes= names {', '.join(map(repr, unknown))}, which "
            f"no row has. The {_MODE} values are {listed}. They match exactly, by "
            "case too."
        )
    named = [name for name in names if name is not None]
    keep = values.isin(named).to_numpy() & ~blank
    if None in names:
        keep |= blank
    return ~keep, tuple(names), None


def _mode_counts(
    df: pd.DataFrame, rows: np.ndarray, reasons: np.ndarray
) -> dict[str, int]:
    """Count the rows left out for their mode, by mode ("blank" for none)."""
    rows = rows & (reasons == _LEFT_OUT[2])
    if not rows.any():
        return {}
    values = df.loc[rows, _MODE].astype(object)
    values = values.where(
        values.notna() & (values.astype(str).str.strip() != ""), "blank"
    )
    return {str(mode): int(n) for mode, n in values.value_counts(sort=False).items()}


def _left_out_rows(
    df: pd.DataFrame,
    rows: np.ndarray,
    reasons: np.ndarray,
    minor: np.ndarray,
    major: np.ndarray,
) -> list[dict[str, Any]]:
    """Each row left out, with its stresses in the fit's unit (NaN if blank)."""
    identifiers = [column for column in _IDENTIFIERS if column in df.columns]
    return [
        {
            "row": row,
            **{column: _cell(df.at[row, column]) for column in identifiers},
            "minor_principal_stress": float(minor[i]),
            "major_principal_stress": float(major[i]),
            _MODE: _cell(df.at[row, _MODE]) if _MODE in df.columns else None,
            "multistage_test": _cell(df.at[row, "multistage_test"])
            if "multistage_test" in df.columns
            else None,
            "reason": str(reasons[i]),
        }
        for i, row in zip(np.flatnonzero(rows), df.index[rows], strict=True)
    ]


def _strengths(
    argument: Any,
    judgments: Any,
    df: pd.DataFrame,
    by: list[str],
    keyed: list[tuple[dict[str, Any], np.ndarray]],
    unit: str,
) -> tuple[list[dict[str, Any] | str], dict[str, Any] | None]:
    """Return each group's fixed σci, or why it has none, and the record (decision 8).

    A group's σci is a dict with its value in the fit's unit and its source;
    a string is the reason the group has no fixed fit.
    """
    keys = [key for key, _ in keyed]
    if argument is not None:
        read = read_judgments(judgments, df)
        if read is not None and _ARGUMENT in read.judgments:
            warn(f"{_ARGUMENT}= replaces the {_ARGUMENT} in {read.path.name}.")
        return _from_argument(argument, by, keys, unit)
    read = read_judgments(judgments, df)
    if read is None or _ARGUMENT not in read.judgments:
        return [_NO_STRENGTH] * len(keys), None
    return _from_file(read.judgments[_ARGUMENT], read, keys, unit)


def _quantity(given: Any, unit: str, where: str) -> dict[str, Any]:
    """Read one σci written with its unit, in the fit's unit."""
    if isinstance(given, int | float):  # bool too
        raise HangtuError(
            f"{_FUNCTION} {where} needs its unit: write it as text, e.g. "
            f'"{given:g} MPa", not {given!r}. A unit is never guessed (SPEC §2.6).'
        )
    if not isinstance(given, str):
        raise HangtuError(
            f'{_FUNCTION} {where} takes σci with its unit, e.g. "61 MPa", not '
            f"{type(given).__name__}."
        )
    try:
        value, written = _units.parse_quantity(given.strip(), "stress")
    except HangtuError as error:
        raise HangtuError(f"{_FUNCTION} {where}: {error}") from None
    if not value > 0:
        raise HangtuError(
            f"{_FUNCTION} {where} must be positive, not {given!r}: σci is a "
            "compressive strength."
        )
    converted = _units.convert(
        [value], _units.parse_unit(written), "stress", _units.parse_unit(unit)
    )[0]
    return {
        "value": float(converted),
        "text": given.strip(),
        "source": "argument",
        "source_text": "argument",
    }


def _from_argument(
    argument: Any, by: list[str], keys: list[dict[str, Any]], unit: str
) -> tuple[list[dict[str, Any] | str], dict[str, Any]]:
    """Each group's σci from the argument: one value, or a mapping by group."""
    if not isinstance(argument, Mapping):
        one = _quantity(argument, unit, f"{_ARGUMENT}=")
        return [one] * len(keys), {
            "source": "argument",
            "by": None,
            "values": {"all": one["text"]},
        }
    given = {
        key: _quantity(text, unit, f"{_ARGUMENT}={{{key!r}: ...}}")
        for key, text in argument.items()
    }
    strengths: list[dict[str, Any] | str] = []
    matched = set()
    used = {}
    for key in keys:
        found = next((k for k in given if _matches(k, key)), _UNMATCHED)
        if found is _UNMATCHED:
            strengths.append(
                f"no σci for this group in {_ARGUMENT}=: add {_key_text(key)} to "
                "the mapping"
            )
            continue
        matched.add(found)
        strengths.append(given[found])
        used[_label(key)] = given[found]["text"]
    unmatched = [key for key in given if key not in matched]
    if unmatched:
        groups = ", ".join(_key_text(key) for key in keys) or "one group of every row"
        warn(
            f"{_FUNCTION} {_ARGUMENT}= has values for "
            f"{', '.join(map(repr, unmatched))}, which match no group "
            f"(group_by={by!r}: {groups}). Check the spelling: keys match exactly, "
            "by case too."
        )
    return strengths, {"source": "argument", "by": by, "values": used}


_UNMATCHED = object()


def _matches(given: Any, key: dict[str, Any]) -> bool:
    """Whether a mapping key names a group: its value, or a tuple of values."""
    values = list(key.values())
    if not values:
        return False
    wanted = list(given) if isinstance(given, tuple) else [given]
    return len(wanted) == len(values) and all(
        w == v or str(w) == str(v) for w, v in zip(wanted, values, strict=True)
    )


def _key_text(key: dict[str, Any]) -> str:
    values = tuple(key.values())
    return repr(values[0]) if len(values) == 1 else repr(values)


def _from_file(
    judgment: "_judgments.Judgment",
    read: "_judgments.Read",
    keys: list[dict[str, Any]],
    unit: str,
) -> tuple[list[dict[str, Any] | str], dict[str, Any]]:
    """Each group's σci from the judgments file, by its ``by:`` column."""
    field = "intact_compressive_strength"
    written = judgment.units[field]

    def entry(value: "_judgments.Entry") -> dict[str, Any]:
        number = value.values[field]
        converted = _units.convert(
            [number], _units.parse_unit(written), "stress", _units.parse_unit(unit)
        )[0]
        return {
            "value": float(converted),
            "text": _judgments.quantity_text(number, written),
            "reason": value.reason,
            "source": "judgments file",
            "source_text": read.path.name,
            "path": str(read.path),
            "sha256": read.sha256,
        }

    record: dict[str, Any] = {
        "source": str(read.path),
        "sha256": read.sha256,
        "by": judgment.by,
        "values": {},
    }
    project = None if judgment.project is None else entry(judgment.project)
    strengths: list[dict[str, Any] | str] = []
    filled = []
    for key in keys:
        if judgment.by is None or not judgment.values:
            if project is None:
                strengths.append(_NO_STRENGTH)
                continue
            strengths.append(project)
            filled.append(_label(key))
            continue
        if judgment.by not in key:
            strengths.append(
                f"the judgments file's {_ARGUMENT} is keyed by {judgment.by!r}: "
                f"group by it (group_by={judgment.by!r}) to use it"
            )
            continue
        value = key[judgment.by]
        name = None if pd.isna(value) else str(value)
        if name is not None and name in judgment.values:
            found = entry(judgment.values[name])
            strengths.append(found)
            record["values"][name] = found["text"]
        elif project is not None:
            strengths.append(project)
            filled.append(_label(key))
        else:
            strengths.append(
                f"the judgments file's {_ARGUMENT} has no value for "
                f"{judgment.by} {value!r}: add it, or a project: entry with its reason"
            )
    if filled:
        assert project is not None  # filled only from the project value
        reason = f" ({project['reason']})" if project["reason"] else ""
        warn(
            f"{_ARGUMENT}: the project value {project['text']} is used for "
            f"{', '.join(filled)}{reason}."
        )
        record["values"]["project"] = {
            "value": project["text"],
            "used_for": ", ".join(filled),
        }
    return strengths, record


def _reported(
    df: pd.DataFrame, units: Mapping[str, str] | None, unit: str
) -> tuple[np.ndarray, np.ndarray] | None:
    """Return the lab's σci in the fit's unit and its mi, NaN where not given."""
    strength_column, constant_column = _REPORTED
    if not any(
        column in df.columns and not df[column].isna().all() for column in _REPORTED
    ):
        return None
    strength = np.full(len(df), np.nan)
    if strength_column in df.columns and not df[strength_column].isna().all():
        declared = _units.resolve_units(df, [strength_column], units, analysis=True)
        source = _units.parse_unit(declared[strength_column], strength_column)
        _units.check_dimension(source, "stress", strength_column)
        strength = _convert_reported(
            numeric_column(df, strength_column),
            source,
            "stress",
            _units.parse_unit(unit),
        )
    constant = (
        numeric_column(df, constant_column)
        if constant_column in df.columns
        else np.full(len(df), np.nan)
    )
    return strength, np.asarray(constant, dtype=float)


def _fit(
    df: pd.DataFrame,
    fitted: np.ndarray,
    minor: np.ndarray,
    major: np.ndarray,
    kind: str,
    strength: dict[str, Any] | str,
    multistaged: np.ndarray,
) -> dict[str, Any]:
    """Fit one line, free or σci fixed, and back-transform it (Derivation)."""
    x = minor[fitted]
    s1 = major[fitted]
    y = (s1 - x) ** 2
    source: str | None = "fitted"
    fixed: float = np.nan
    if kind == "free":
        line = line_fit(x, y, x_name="minor principal stress")
        reason = line.no_fit_reason
        if reason is None and line.intercept <= 0:
            reason = f"intercept σci² = {line.intercept:.4g} is 0 or below: no σci"
    elif isinstance(strength, str):
        line = None
        reason = strength
        source = None
    else:
        fixed = strength["value"]
        source = strength["source"]
        line = line_fit(x, y, intercept=fixed**2, x_name="minor principal stress")
        reason = line.no_fit_reason
    if reason is None:
        assert line is not None  # a reason is set wherever there is no line
        if line.slope <= 0:
            reason = (
                f"slope mi σci = {line.slope:.4g} is 0 or below: mi must be positive"
            )
    count = len(x)
    if reason is None:
        assert line is not None  # as above
        strength_value = math.sqrt(line.intercept) if kind == "free" else fixed
        constant = line.slope / strength_value
        r_squared = float(line.r_squared)
        intercept, slope = float(line.intercept), float(line.slope)
    else:
        strength_value = fixed
        constant = r_squared = intercept = slope = np.nan
    at_zero = x == 0
    with np.errstate(divide="ignore", invalid="ignore"):
        back = (
            np.where(x > 0, (y - strength_value**2) / (strength_value * x), np.nan)
            if reason is None
            else np.full(count, np.nan)
        )
    beyond = int((x >= 0.5 * strength_value).sum()) if reason is None else 0
    notes = []
    if reason is None:
        if count < _ENOUGH_POINTS:
            notes.append(
                f"{count} points: Hoek (2007, ch. 11, p. 2) asks for at least five "
                "well spaced ones."
            )
        if kind == "free" and count == 2:
            notes.append("2 points: the line passes through both, so R² = 1.")
        if beyond:
            notes.append(
                f"{beyond} point{'s' if beyond != 1 else ''} at σ3 ≥ 0.5 σci = "
                f"{0.5 * strength_value:.4g}, beyond Hoek's (2007) range."
            )
        if r_squared < _GOOD_R_SQUARED:
            notes.append(
                f"R² = {r_squared:.3f} is below 0.9, Hoek's (2007, ch. 11, p. 4) mark "
                "of high quality triaxial data."
            )
    identifiers = [column for column in _IDENTIFIERS if column in df.columns]
    points = [
        {
            "row": row,
            **{column: _cell(df.at[row, column]) for column in identifiers},
            "minor_principal_stress": float(x[j]),
            "major_principal_stress": float(s1[j]),
            _MODE: _cell(df.at[row, _MODE]) if _MODE in df.columns else None,
            "multistage_test": bool(multistaged[i]),
            "back_calculated_hoek_brown_constant": float(back[j]),
        }
        for j, (i, row) in enumerate(
            zip(np.flatnonzero(fitted), df.index[fitted], strict=True)
        )
    ]
    return {
        "line_kind": kind,
        "intact_compressive_strength": float(strength_value),
        "intact_hoek_brown_constant": float(constant),
        "r_squared": float(r_squared),
        "count": count,
        "lowest_minor_principal_stress": float(np.min(x)) if count else np.nan,
        "highest_minor_principal_stress": float(np.max(x)) if count else np.nan,
        "count_beyond_confining_range": beyond,
        "uniaxial_count": int(at_zero.sum()),
        "uniaxial_mean": float(np.mean(s1[at_zero])) if at_zero.any() else np.nan,
        "intact_compressive_strength_source": source,
        "fixed_strength": strength if isinstance(strength, dict) else None,
        "line_intercept": intercept,
        "line_slope": slope,
        "no_fit_reason": reason,
        "notes": notes,
        "points": points,
    }


@dataclass(frozen=True, repr=False)
class HoekBrownFit(_DerivedResult):
    """The fit ``ht.analysis.hoek_brown_fit()`` returns.

    Use ``.to_frame()`` for a table with one row per group, stage set and
    fit, ``.to_dict()`` for a report, or ``print(fit)`` to read it.
    ``.groups`` holds each group's fits with their points, and the rows left
    out with their reasons. The text is a view of the same numbers.
    """

    #: ``"total"`` or ``"effective"``: the principal stresses fitted.
    stress: str
    #: The columns grouped by, in order.
    by: tuple[str, ...]
    #: The columns pooled on purpose (``pool=``).
    pooled: tuple[str, ...]
    #: The ``failure_mode`` values fitted, as named; None when the frame has
    #: no mode and every row was fitted.
    failure_modes: tuple[str | None, ...] | None
    #: Whether the fit with multistage stages is the main one.
    multistage: bool
    #: The system the stresses were converted to before fitting, None if not.
    display_units: str | None
    #: One record per group: its ``key``, ``count_rows``, its ``fits`` in the
    #: order of ``.to_frame()`` (each with the frame's values, the line's
    #: ``line_intercept`` σci² and ``line_slope`` mi σci, ``fixed_strength``,
    #: ``reported_pairs``, ``notes`` and ``points``), ``count_by_failure_mode``
    #: of the rows left out for their mode, and ``left_out``, each row left
    #: out with its reason and its σ3 and σ1 (NaN where blank).
    groups: tuple[dict[str, Any], ...]

    def _columns(self) -> list[str]:
        return [
            *self.by,
            "stages",
            "line_kind",
            "intact_compressive_strength",
            "intact_hoek_brown_constant",
            "r_squared",
            "count",
            "lowest_minor_principal_stress",
            "highest_minor_principal_stress",
            "count_beyond_confining_range",
            "uniaxial_count",
            "uniaxial_mean",
            "intact_compressive_strength_source",
            *_REPORTED,
            "count_reported_pairs",
            *_LEFT_OUT,
            "no_fit_reason",
        ]

    def to_frame(self) -> pd.DataFrame:
        """Return one row per group, stage set and fit, the main stage set first.

        ``stages`` is ``"all"`` or ``"single_stage"`` (a group with a
        multistage stage has both); ``line_kind`` is ``"free"`` or
        ``"fixed_strength"``, free first. With σci fixed,
        ``intact_compressive_strength`` is the value fixed and
        ``intact_compressive_strength_source`` says where it came from. The
        lab's pair is given when the fitted rows report one; with more, it is
        blank and ``count_reported_pairs`` says how many. ``attrs["units"]``
        gives the unit of each stress column; mi is dimensionless.
        """
        rows = []
        for group in self.groups:
            for fit in group["fits"]:
                pairs = fit["reported_pairs"] or []
                one = pairs[0] if len(pairs) == 1 else None
                row: dict[str, Any] = {
                    **group["key"],
                    **{
                        column: fit[column]
                        for column in self._columns()
                        if column in fit and column not in group["key"]
                    },
                    _REPORTED[0]: one[_PAIR[0]] if one else np.nan,
                    _REPORTED[1]: one[_PAIR[1]] if one else np.nan,
                    "count_reported_pairs": len(pairs),
                }
                rows.append(row)
        frame = pd.DataFrame(rows, columns=self._columns())
        stresses = [
            "intact_compressive_strength",
            "lowest_minor_principal_stress",
            "highest_minor_principal_stress",
            "uniaxial_mean",
            _REPORTED[0],
        ]
        frame.attrs["units"] = dict.fromkeys(stresses, self.unit) if self.unit else {}
        return frame

    def __str__(self) -> str:
        from hangtu.plot._overlays import format_number  # plot imports analysis

        unit = f" {self.unit}" if self.unit else ""
        prime = "′" if self.stress == "effective" else ""
        lines = [f"Hoek-Brown fit of intact rock, {self.stress} stresses"]
        for group in self.groups:
            indent = "  " if self.by else ""
            if self.by:
                lines.append(f"{_label(group['key'])}: {group['count_rows']} rows")
            fits = group["fits"]
            staged = len({fit["stages"] for fit in fits}) > 1
            sub = indent + "  "
            for free, fixed in zip(fits[::2], fits[1::2], strict=True):
                stages = (
                    ("all stages, " if free["stages"] == "all" else "single stage, ")
                    if staged
                    else ""
                )
                head = f"{indent}{stages}free: "
                if free["no_fit_reason"]:
                    lines.append(f"{head}not fitted: {free['no_fit_reason']}")
                else:
                    count = free["count"]
                    lines.append(
                        head
                        + f"σci = {format_number(free['intact_compressive_strength'])}"
                        f"{unit}, "
                        + _constant_text(free, format_number)
                        + f", {count} point{'s' if count != 1 else ''}, σ{prime}3 "
                        f"{format_number(free['lowest_minor_principal_stress'])} to "
                        f"{format_number(free['highest_minor_principal_stress'])}"
                        f"{unit}"
                    )
                lines.append(sub + _fixed_text(fixed, unit, format_number))
                if free["stages"] == "single_stage" and free[_LEFT_OUT[3]]:
                    lines.append(
                        f"{sub}{free[_LEFT_OUT[3]]} multistage stages left out"
                    )
                notes = [*free["notes"], *fixed["notes"]]
                lines.extend(f"{sub}{note}" for note in dict.fromkeys(notes))
            main = fits[0]
            if main["uniaxial_count"]:
                n = main["uniaxial_count"]
                lines.append(
                    f"{indent}UCS (σ3 = 0): {n} test{'s' if n != 1 else ''}, mean "
                    f"{format_number(main['uniaxial_mean'])}{unit}"
                )
            left_out = [
                f"{main[name]} {name.removeprefix('count_').replace('_', ' ')}"
                for name in _LEFT_OUT[:3]
                if main[name]
            ]
            if group["count_by_failure_mode"]:
                modes = ", ".join(
                    f"{mode} {n}" for mode, n in group["count_by_failure_mode"].items()
                )
                left_out = [
                    f"{text} ({modes})" if text.endswith("failure mode") else text
                    for text in left_out
                ]
            if left_out:
                lines.append(f"{indent}left out: {', '.join(left_out)}")
            for pair in main["reported_pairs"] or []:
                n = pair["count"]
                lines.append(
                    f"{indent}lab: σci = {_reported_text(pair[_PAIR[0]])}{unit}, "
                    f"mi = {_reported_text(pair[_PAIR[1]])} "
                    f"({n} row{'s' if n != 1 else ''})"
                )
        return "\n".join([*lines, *self.notes])


def _kind_text(kind: str) -> str:
    return "free" if kind == "free" else "σci fixed"


def _constant_text(fit: dict[str, Any], format_number: Any) -> str:
    r_squared = fit["r_squared"]
    r_text = "—" if math.isnan(r_squared) else f"{r_squared:.3f}"
    return f"mi = {format_number(fit['intact_hoek_brown_constant'])}, R² = {r_text}"


def _fixed_text(fit: dict[str, Any], unit: str, format_number: Any) -> str:
    strength = fit["fixed_strength"]
    if strength is None:
        return f"σci fixed: not fitted: {fit['no_fit_reason']}"
    head = (
        f"σci fixed at {format_number(fit['intact_compressive_strength'])}{unit} "
        f"({strength['source_text']})"
    )
    if fit["no_fit_reason"]:
        return f"{head}: not fitted: {fit['no_fit_reason']}"
    return f"{head}: {_constant_text(fit, format_number)}"


def _reported_text(value: float) -> str:
    return "—" if math.isnan(value) else f"{value:g}"
