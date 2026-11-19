"""The oedometer fit: σ′p, Cc, Cr and Cs (docs/analysis/compressibility.md)."""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu.analysis._derived import _DerivedResult, judgments_file, soil_classes
from hangtu.analysis._fit_groups import _cell, _place_units
from hangtu.analysis._line_fit import Line, line_fit
from hangtu.analysis._oedometer import (
    CONSTANT_STRESS,
    LOADING,
    RELOADING,
    UNLOADING,
    oedometer_load_branch,
)
from hangtu.errors import ColumnError, HangtuError
from hangtu.stats._rows import group_keys

_FUNCTION = "oedometer_fit()"
_STRESS = "applied_vertical_stress"
_VOID_RATIO = "void_ratio_at_increment_end"
_REQUIRED = ("specimen_id", _STRESS, _VOID_RATIO)
_TEMPLATE = 'ht.template("oedometer") has the columns it reads.'
#: The columns that identify a specimen, kept on its row where the frame has them.
_IDENTIFIERS = (
    "specimen_id",
    "sample_reference",
    "specimen_reference",
    "loca_id",
    "depth",
    "geology_unit",
    "test_type",
)
#: The counts of rows no line uses, in the order they're checked (decision 3).
_LEFT_OUT = (
    "count_no_applied_stress",
    "count_no_void_ratio",
    "count_stress_not_positive",
    "count_constant_stress",
    "count_reloading",
    "count_unloading_not_used",
)
_LEFT_OUT_TEXT = {
    "count_no_applied_stress": "no applied stress",
    "count_no_void_ratio": "no void ratio",
    "count_stress_not_positive": "stress not above 0",
    "count_constant_stress": "constant stress",
    "count_reloading": "reloading",
    "count_unloading_not_used": "unloading after the first run",
}
#: Each of Oikawa's two lines needs this many points (decision 5.1).
POINTS_PER_LINE = 3
#: The upper line is at least this many times as steep as the lower one, or
#: there is no clear break (decision 5.2).
SLOPE_RATIO = 2.0
#: The highest loading stress is at least this many times σ′p, or the virgin
#: line is too short (decision 5.4; sheet 06 §7 says 2-3).
STRESS_RATIO = 2.0
#: Below this ratio the summary says the virgin line is short (decision 5.4).
STRESS_RATIO_REMARK = 3.0
#: Splits whose sums of squares differ by less than this, relative, are a tie.
_TIE = 1e-9

# Roles of a point (decision 15).
RECOMPRESSION = "recompression"
VIRGIN = "virgin"
SWELLING = "swelling"
#: A loading point when the curve has no σ′p, so no groups.
LOADING_ROLE = "loading"
LEFT_OUT = "left_out"


def oedometer_fit(
    df: pd.DataFrame,
    *,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> "OedometerFit":
    r"""Fit each oedometer specimen's curve: σ′p by Oikawa (1987), Cc and Cr.

    **The preconsolidation stress** is found as Oikawa (1987) finds it: in a
    plot of $\log f$ against $\log \sigma'_v$, with $f = 1 + e$ the specific
    volume (p. 100), the loading curve of a soft soil is "essentially
    composed of two segments of straight line", and the stress where they
    intersect agrees well with the consolidation yield stress from
    Casagrande's construction (p. 103; conclusions 4-5, p. 104). With
    $x = \log_{10}\sigma'_v$ and $y = \log_{10}(1 + e)$, the lower line
    $y = a_1 + b_1 x$ and the upper line $y = a_2 + b_2 x$ cross at

    $$
    \sigma'_p = 10^{(a_2 - a_1)/(b_1 - b_2)}
    $$

    Oikawa states the construction but no fitting procedure, so the search
    is hangtu's: every split of the loading points, in stress order, into a
    lower and an upper group of at least 3 points each is fitted with one
    least-squares line per group ($b = S_{xy}/S_{xx}$,
    $a = \bar y - b\bar x$), and the split with the smallest total sum of
    squared residuals wins, the lower split on a tie. It needs no smoothing
    and no judgment, so the same increments always give the same
    $\sigma'_p$. Every split's sum of squares is on the result, to show how
    clearly one won.

    **The compression and recompression indexes** are slopes of $e$ against
    $\log_{10}\sigma'_v$, as the soil models define them, fitted by least
    squares to the same two groups of points: $C_c$ from the upper group
    (the virgin line), $C_r$ from the lower. Both are positive (the negated
    slopes). Their lines are fitted in another space than Oikawa's, so they
    don't cross exactly at $\sigma'_p$.

    **The rows each value reads.** Each increment's branch comes from
    ``load_branch`` (added by ``ht.analysis.oedometer_load_branch()`` when
    the frame doesn't have it, with a note). Only ``loading`` rows give
    $\sigma'_p$, $C_c$ and $C_r$; a reload slope is never $C_c$. A point is
    ``loading`` once its stress exceeds every earlier one, so the first
    points past an unload-reload loop are kept: leaving them out would take
    the virgin line's highest points. They are counted
    (``count_loading_after_reload``) and marked. The other rows are counted,
    each once under the first reason that applies: no applied stress, no
    void ratio at the increment's end, a stress not above 0 (its log is
    undefined), ``constant_stress`` (flooding, creep), ``reloading``, and
    unloading rows no line uses.

    **When a curve gives no σ′p.** $\sigma'_p$, $C_c$ and $C_r$ are blank
    with a reason, the first that applies of:

    1. no loading rows, or fewer than 6 loading points (3 per line);
    2. no clear break: the upper line isn't falling, or isn't at least 2
       times as steep as the lower one, $|b_2| \ge 2|b_1|$. Intact clays
       give about 3-10, a straight $e$-$\log\sigma'_v$ curve about 1.2;
    3. the lines cross outside the loading stresses: nothing is
       extrapolated;
    4. the highest loading stress is below $2\sigma'_p$, too short a virgin
       line to define $C_c$. Its ratio to $\sigma'_p$ is on the result, and
       the summary says so when it is below 3.

    **Valid for:** incremental-load oedometer tests on soil, rows in the
    order the increments were applied. Oikawa's data are soft soils of the
    Akita plain (sensitive clays, organic soils and peat) with natural water
    content 25-941 % and initial void ratio 0.7-17 (p. 100); the agreement
    with Casagrande's $\sigma'_p$ is shown for $w_n > 200\,\%$ (Figs. 9-10,
    p. 103), and below 200 % the $e$-$\log\sigma'_v$ curve is itself linear
    in the normally consolidated range (conclusion 1, p. 104). Nothing is
    refused by water content: the method is also run on ordinary clays.
    **Scatter:** each split's sum of squares; Oikawa gives no error for the
    construction. **Assumptions:** two straight lines in
    $\log f$-$\log\sigma'_v$; the void ratios as the lab reports them, at the
    end of each increment. **Judgments taken:** none.

    Source: Oikawa, H. (1987). Compression curve of soft soils. *Soils and
    Foundations* 27(3), 99-104, doi:10.3208/sandf1972.27.3_99.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per increment, as ``p.oedometer()`` gives (or a CSV in
        ``ht.template("oedometer")``'s shape): ``specimen_id``,
        ``applied_vertical_stress`` and ``void_ratio_at_increment_end``, in
        the order the increments were applied. ``load_branch`` is read where
        present. One fit per ``specimen_id``, in sorted order.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.
    display_units : {"SI", "US"}, optional
        Fit in kPa (SI) or psf (US), or the stress unit the settings' display
        overrides name. None fits in ``applied_vertical_stress``'s unit. The
        indexes don't depend on the unit.

    Returns
    -------
    OedometerFit
        ``.to_frame()`` has one row per specimen; ``print()`` reads it;
        ``.specimens`` holds each point's role, every split and every line.

    Raises
    ------
    HangtuError
        For a frame without ``specimen_id``, ``applied_vertical_stress`` or
        ``void_ratio_at_increment_end``, a row with a blank ``specimen_id``, a
        negative void ratio, a ``load_branch`` value the fit doesn't know, a
        stress column without units or in a unit that isn't a stress, or an
        argument out of its range.

    Examples
    --------
    σ′p, Cc and Cr of each oedometer specimen in the example project:

    >>> p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
    >>> fit = ht.analysis.oedometer_fit(p.oedometer())
    >>> print(fit)
    >>> fit.to_frame()[["specimen_id", "preconsolidation_stress", "compression_index"]]
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if display_units not in (None, "SI", "US"):
        raise HangtuError(
            f'{_FUNCTION} display_units must be "SI", "US" or None, not '
            f"{display_units!r}."
        )
    missing = [column for column in _REQUIRED if column not in df.columns]
    if missing:
        raise ColumnError(
            f"{_FUNCTION} needs {', '.join(map(repr, missing))}: df has no such "
            f"column. Use p.oedometer(); {_TEMPLATE}"
        )
    blank = (
        df["specimen_id"].isna() | (df["specimen_id"].astype(str).str.strip() == "")
    ).to_numpy()
    if blank.any():
        raise HangtuError(
            f"Rows {rows_text(df.index[blank])} have no specimen_id, so {_FUNCTION} "
            "can't tell which curve they belong to. Fill in specimen_id."
        )
    notes = []
    if "load_branch" not in df.columns:
        df = oedometer_load_branch(df)
        notes.append(
            "load_branch added by ht.analysis.oedometer_load_branch(), reading the "
            "rows in the order the increments were applied."
        )
    branch = _branches(df)
    stress, unit = _stresses(df, units, display_units)
    void_ratio = numeric_column(df, _VOID_RATIO)
    negative = void_ratio < 0
    if negative.any():
        raise HangtuError(
            f"Rows {rows_text(df.index[negative])} have a negative "
            f"{_VOID_RATIO}, which a soil can't have. Check those rows."
        )
    identifiers = tuple(column for column in _IDENTIFIERS if column in df.columns)
    text = f" {unit}" if unit else ""
    specimens = tuple(
        _specimen(
            df, np.flatnonzero(rows), stress, void_ratio, branch, identifiers, text
        )
        for _, rows in group_keys(df, ["specimen_id"])
    )
    return OedometerFit(
        function="oedometer_fit",
        unit=unit,
        notes=tuple(notes),
        judgments=dict(df.attrs.get("judgments", {})),
        hangtu_version=version("hangtu"),
        judgments_file=judgments_file(df),
        soil_classes=soil_classes(df),
        display_units=display_units,
        depth_units=_place_units(df, units),
        identifiers=identifiers,
        specimens=specimens,
    )


def _branches(df: pd.DataFrame) -> np.ndarray:
    """Return each row's ``load_branch``, None where blank, after checking them."""
    branch = df["load_branch"].astype(object).to_numpy()
    branch = np.array([None if pd.isna(b) else b for b in branch], dtype=object)
    known = (LOADING, UNLOADING, RELOADING, CONSTANT_STRESS, None)
    wrong = np.array([b not in known for b in branch], dtype=bool)
    if wrong.any():
        values = ", ".join(dict.fromkeys(map(repr, branch[wrong])))
        raise HangtuError(
            f"Rows {rows_text(df.index[wrong])} have load_branch {values}, which "
            f"{_FUNCTION} doesn't know: it reads {', '.join(map(repr, known[:-1]))}. "
            "Drop the column to have it worked out from the stresses."
        )
    return branch


def _stresses(
    df: pd.DataFrame, units: Mapping[str, str] | None, display_units: str | None
) -> tuple[np.ndarray, str | None]:
    """Return ``applied_vertical_stress`` in the fit's unit, and its name.

    A column blank throughout needs no unit (a template's CSV has every column).
    """
    if df[_STRESS].isna().all():
        return np.full(len(df), np.nan), None
    declared = _units.resolve_units(df, [_STRESS], units, analysis=True)[_STRESS]
    _units.check_dimension(_units.parse_unit(declared, _STRESS), "stress", _STRESS)
    values = numeric_column(df, _STRESS)
    if display_units is None:
        return values, declared
    return _units.to_display(values, declared, "stress", display_units)


def _specimen(
    df: pd.DataFrame,
    positions: np.ndarray,
    stress: np.ndarray,
    void_ratio: np.ndarray,
    branch: np.ndarray,
    identifiers: tuple[str, ...],
    unit: str,
) -> dict[str, Any]:
    """Fit one specimen's rows, in frame order (decisions 3-8)."""
    first = df.index[positions[0]]
    key = {column: _cell(df.at[first, column]) for column in identifiers}
    points = _points(df, positions, stress, void_ratio, branch)
    loading = [p for p in points if p["load_branch"] == LOADING and not p["reason"]]
    loading.sort(key=lambda p: p["applied_vertical_stress"])
    x = np.array([p["applied_vertical_stress"] for p in loading])
    e = np.array([p["void_ratio"] for p in loading])
    record: dict[str, Any] = {
        "key": key,
        "label": _specimen_label(key),
        **_oikawa(x, e, unit),
        "count_rows": len(positions),
        "count_loading_points": len(loading),
        "count_loading_after_reload": sum(p["after_reload"] for p in loading),
        "count_unload_runs": len({p["unload_run"] for p in points} - {None}),
        **{name: sum(p["reason"] == name for p in points) for name in _LEFT_OUT},
        "notes": [],
        "points": points,
    }
    lower = record["lower_count"]
    given = not math.isnan(record["preconsolidation_stress"])
    for j, point in enumerate(loading):
        if given:
            point["role"] = RECOMPRESSION if j < lower else VIRGIN
        else:
            point["role"] = LOADING_ROLE
    record |= _indexes(x, e, lower if given else None)
    record["void_ratio_at_preconsolidation_stress"] = (
        _on_curve(x, e, record["preconsolidation_stress"]) if given else np.nan
    )
    return record


def _points(
    df: pd.DataFrame,
    positions: np.ndarray,
    stress: np.ndarray,
    void_ratio: np.ndarray,
    branch: np.ndarray,
) -> list[dict[str, Any]]:
    """Return each row's point: its branch, role, reason and unload run.

    An unload run is the point the unload starts from (the row before it) and
    the consecutive ``unloading`` rows after it; rows with no stress have no
    branch and are passed over. A loading point after an unload is past a
    reload (decision 8).
    """
    run_of: dict[int, int] = {}
    after_reload: set[int] = set()
    previous: int | None = None
    runs = 0
    unloaded = False
    for pos in positions:
        if math.isnan(stress[pos]):
            continue
        if branch[pos] == UNLOADING:
            unloaded = True
            if previous is None or branch[previous] != UNLOADING:
                runs += 1
                if previous is not None:
                    run_of.setdefault(previous, runs)
            run_of[pos] = runs
        elif branch[pos] == LOADING:
            if unloaded:
                after_reload.add(pos)
            unloaded = False
        previous = pos
    points = []
    for pos in positions:
        s, e, b = float(stress[pos]), float(void_ratio[pos]), branch[pos]
        reason = None
        if math.isnan(s):
            reason = "count_no_applied_stress"
        elif math.isnan(e):
            reason = "count_no_void_ratio"
        elif s <= 0:
            reason = "count_stress_not_positive"
        elif b == CONSTANT_STRESS:
            reason = "count_constant_stress"
        elif b == RELOADING:
            reason = "count_reloading"
        elif b == UNLOADING and run_of[pos] > 1:
            reason = "count_unloading_not_used"
        role = LEFT_OUT if reason else (SWELLING if b == UNLOADING else LOADING_ROLE)
        points.append(
            {
                "row": _cell(df.index[pos]),
                "applied_vertical_stress": s,
                "void_ratio": e,
                "load_branch": b,
                "role": role,
                "reason": reason,
                "after_reload": pos in after_reload,
                "unload_run": run_of.get(pos),
            }
        )
    return points


def _specimen_label(key: dict[str, Any]) -> str:
    """Name a specimen as the lab does: its sample and specimen references."""
    parts = [key.get("sample_reference"), key.get("specimen_reference")]
    named = [str(part) for part in parts if part is not None and str(part).strip()]
    return "-".join(named) if named else str(key["specimen_id"])


def _oikawa(x: np.ndarray, e: np.ndarray, unit: str) -> dict[str, Any]:
    """σ′p by Oikawa (1987): the best split, its lines and the rules of decision 5.

    ``x`` and ``e`` are the loading points' stresses and void ratios, in stress
    order; ``unit`` is " kPa" or the like, for the reasons.
    """
    record: dict[str, Any] = {
        "preconsolidation_stress": np.nan,
        "preconsolidation_stress_reason": None,
        "splits": [],
        "lower_count": None,
        "lower_line": None,
        "upper_line": None,
        "slope_ratio": np.nan,
        "crossing_stress": np.nan,
        "highest_stress_over_preconsolidation_stress": np.nan,
    }
    count = len(x)
    needed = 2 * POINTS_PER_LINE
    if count == 0:
        record["preconsolidation_stress_reason"] = "no loading branch"
        return record
    if count < needed:
        record["preconsolidation_stress_reason"] = (
            f"{needed} loading points are needed ({POINTS_PER_LINE} per line), "
            f"{count} given"
        )
        return record
    log_stress = np.log10(x)
    log_volume = np.log10(1 + e)
    fits = []
    for lower in range(POINTS_PER_LINE, count - POINTS_PER_LINE + 1):
        first = line_fit(log_stress[:lower], log_volume[:lower])
        second = line_fit(log_stress[lower:], log_volume[lower:])
        total = sum(r**2 for r in first.residuals) + sum(r**2 for r in second.residuals)
        fits.append((lower, first, second, total))
    record["splits"] = [
        {"lower_count": lower, "upper_count": count - lower, "sum_of_squares": total}
        for lower, _, _, total in fits
    ]
    best = min(total for *_, total in fits)
    lower, first, second, _ = next(
        fit for fit in fits if fit[3] <= best * (1 + _TIE) + 1e-300
    )
    a1, b1, a2, b2 = first.intercept, first.slope, second.intercept, second.slope
    record |= {
        "lower_count": lower,
        "lower_line": _log_line(first),
        "upper_line": _log_line(second),
    }
    ratio = abs(b2) / abs(b1) if b1 != 0 else math.inf
    record["slope_ratio"] = ratio
    if b2 >= 0:
        record["preconsolidation_stress_reason"] = (
            "no clear break: the upper line isn't falling"
        )
        return record
    if ratio < SLOPE_RATIO:
        record["preconsolidation_stress_reason"] = (
            f"no clear break: the upper line is {ratio:.3g} times as steep as the "
            f"lower, at least {SLOPE_RATIO:g} is needed"
        )
        return record
    crossing = 10 ** ((a2 - a1) / (b1 - b2))
    record["crossing_stress"] = crossing
    if not x[0] <= crossing <= x[-1]:
        record["preconsolidation_stress_reason"] = _outside(crossing, x, unit)
        return record
    highest = x[-1] / crossing
    record["highest_stress_over_preconsolidation_stress"] = highest
    if highest < STRESS_RATIO:
        record["preconsolidation_stress_reason"] = (
            f"the highest loading stress is {highest:.3g} σ′p, at least "
            f"{STRESS_RATIO:g} is needed to define the virgin line"
        )
        return record
    record["preconsolidation_stress"] = crossing
    return record


def _outside(crossing: float, x: np.ndarray, unit: str) -> str:
    from hangtu.plot._overlays import format_number  # plot imports analysis

    return (
        f"the lines cross at {format_number(crossing)}{unit}, outside the loading "
        f"stresses ({format_number(x[0])} to {format_number(x[-1])}{unit})"
    )


def _log_line(line: Line) -> dict[str, Any]:
    """One of Oikawa's lines, log10(1 + e) = a + b log10 σ′v, and its points."""
    return {
        "intercept": line.intercept,
        "slope": line.slope,
        "count": line.count,
        "sum_of_squares": float(sum(r**2 for r in line.residuals)),
    }


def _index_line(x: np.ndarray, e: np.ndarray) -> dict[str, Any]:
    """Fit e = c - C log10 σ′v by least squares, over its points' stresses."""
    line = line_fit(np.log10(x), e, x_name="stress")
    return {
        "index": -line.slope,
        "intercept": line.intercept,
        "slope": line.slope,
        "count": line.count,
        "r_squared": line.r_squared,
        "lowest_stress": float(np.min(x)),
        "highest_stress": float(np.max(x)),
    }


def _indexes(x: np.ndarray, e: np.ndarray, lower: int | None) -> dict[str, Any]:
    """Cc from the upper group, Cr from the lower (decision 6), or blank."""
    if lower is None:
        return {
            "compression_index": np.nan,
            "recompression_index": np.nan,
            "compression_line": None,
            "recompression_line": None,
        }
    compression = _index_line(x[lower:], e[lower:])
    recompression = _index_line(x[:lower], e[:lower])
    return {
        "compression_index": compression["index"],
        "recompression_index": recompression["index"],
        "compression_line": compression,
        "recompression_line": recompression,
    }


def _on_curve(x: np.ndarray, e: np.ndarray, at: float) -> float:
    """Return e on the loading curve at a stress, linear in e against log10 σ′v.

    Between the loading points either side; NaN outside them (nothing is
    extrapolated).
    """
    if math.isnan(at) or not x[0] <= at <= x[-1]:
        return np.nan
    return float(np.interp(math.log10(at), np.log10(x), e))


#: The value columns of ``to_frame()``, in order (decision 15).
_VALUES = (
    "preconsolidation_stress",
    "preconsolidation_stress_pacheco_silva",
    "compression_index",
    "recompression_index",
    "swelling_index",
    "compression_ratio",
    "overconsolidation_ratio",
    "normalized_void_ratio_change",
    "sample_quality",
    "effective_vertical_stress",
    "void_ratio",
)
_COUNTS = (
    "count_loading_points",
    "count_loading_after_reload",
    "highest_stress_over_preconsolidation_stress",
    "count_unload_runs",
    *_LEFT_OUT,
)
_REASONS = (
    "preconsolidation_stress_reason",
    "swelling_index_reason",
    "compression_ratio_reason",
    "pacheco_silva_reason",
    "overconsolidation_ratio_reason",
    "normalized_void_ratio_change_reason",
    "sample_quality_reason",
)
_STRESS_COLUMNS = (
    "preconsolidation_stress",
    "preconsolidation_stress_pacheco_silva",
    "effective_vertical_stress",
)


@dataclass(frozen=True, repr=False)
class OedometerFit(_DerivedResult):
    """The fit ``ht.analysis.oedometer_fit()`` returns.

    Use ``.to_frame()`` for a table with one row per specimen, ``.to_dict()``
    for a report, or ``print(fit)`` to read it. ``.specimens`` holds each
    specimen's points, splits and lines. The text is a view of the same
    numbers.
    """

    #: The system the stresses were converted to before fitting, None if not.
    display_units: str | None
    #: ``{column: unit}`` of ``depth``, kept as given; missing when not declared.
    depth_units: dict[str, str]
    #: The identifying columns the frame had, first in each row.
    identifiers: tuple[str, ...]
    #: One record per specimen, in sorted ``specimen_id`` order: ``key`` (its
    #: identifiers), ``label``, the values and their reasons, ``splits`` (every
    #: split's ``lower_count``, ``upper_count`` and ``sum_of_squares``), Oikawa's
    #: ``lower_line`` and ``upper_line`` (log10(1 + e) = intercept + slope ×
    #: log10 σ′v), ``slope_ratio``, ``crossing_stress``, the
    #: ``compression_line`` and ``recompression_line`` (e = intercept + slope ×
    #: log10 σ′v, over ``lowest_stress`` to ``highest_stress``),
    #: ``void_ratio_at_preconsolidation_stress`` (on the loading curve), the
    #: counts, ``notes`` and ``points``: each row's ``applied_vertical_stress``,
    #: ``void_ratio``, ``load_branch``, ``role`` (``recompression``,
    #: ``virgin``, ``loading``, ``swelling`` or ``left_out``), ``reason`` (the
    #: count it is left out under), ``after_reload`` and ``unload_run``.
    specimens: tuple[dict[str, Any], ...]

    def _columns(self) -> list[str]:
        return [*self.identifiers, *_VALUES, *_COUNTS, *_REASONS]

    def to_frame(self) -> pd.DataFrame:
        """Return one row per specimen.

        A value that can't be given is blank, and its ``…_reason`` column says
        why. ``attrs["units"]`` gives the stress columns' unit; the indexes,
        ratios and void ratios are dimensionless.
        """
        rows = []
        for record in self.specimens:
            row = dict(record["key"])
            for column in [*_VALUES, *_COUNTS, *_REASONS]:
                row[column] = record.get(column, _blank(column))
            rows.append(row)
        frame = pd.DataFrame(rows, columns=self._columns())
        frame.attrs["units"] = (
            dict.fromkeys(_STRESS_COLUMNS, self.unit) if self.unit else {}
        )
        return frame

    def __str__(self) -> str:
        from hangtu.plot._overlays import format_number  # plot imports analysis

        unit = f" {self.unit}" if self.unit else ""
        lines = ["Oedometer fit"]
        for record in self.specimens:
            lines.extend(_specimen_text(record, unit, format_number))
        return "\n".join([*lines, *self.notes])


def _blank(column: str) -> Any:
    return None if column.endswith("_reason") or column == "sample_quality" else np.nan


def _index_text(value: float) -> str:
    return "—" if math.isnan(value) else f"{value:#.3g}"


def _specimen_text(record: dict[str, Any], unit: str, format_number: Any) -> list[str]:
    """Write the summary of one specimen (decision 16)."""
    label = record["label"]
    stress = record["preconsolidation_stress"]
    if math.isnan(stress):
        lines = [f"{label}: σ′p not given: {record['preconsolidation_stress_reason']}"]
    else:
        lines = [
            f"{label}: σ′p = {format_number(stress)}{unit} (Oikawa), "
            f"Cc = {_index_text(record['compression_index'])}, "
            f"Cr = {_index_text(record['recompression_index'])}"
        ]
    count = record["count_loading_points"]
    if count:
        text = f"  {count} loading point{'s' if count != 1 else ''}"
        if not math.isnan(stress):
            upper = count - record["lower_count"]
            highest = record["highest_stress_over_preconsolidation_stress"]
            text += f", {upper} on the virgin line, highest stress {highest:.3g} σ′p"
            if highest < STRESS_RATIO_REMARK:
                text += f" (below {STRESS_RATIO_REMARK:g}: a short virgin line)"
        after = record["count_loading_after_reload"]
        if after:
            text += f"; {after} past a reload"
        lines.append(text)
    left_out = [
        f"{record[name]} {_LEFT_OUT_TEXT[name]}" for name in _LEFT_OUT if record[name]
    ]
    if left_out:
        lines.append(f"  left out: {', '.join(left_out)}")
    lines.extend(f"  {note}" for note in record["notes"])
    return lines
