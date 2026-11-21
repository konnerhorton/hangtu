"""The oedometer fit: σ′p, Cc, Cr and Cs (docs/analysis/compressibility.md)."""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd

from hangtu._data import numeric_column, rows_text
from hangtu.analysis._derived import _DerivedResult, judgments_file, soil_classes
from hangtu.analysis._fit_groups import _cell, _place_units
from hangtu.analysis._line_fit import Line, line_fit
from hangtu.analysis._oedometer import (
    CONSTANT_STRESS,
    LOADING,
    RELOADING,
    UNLOADING,
    branches,
    in_situ,
    oedometer_load_branch,
    one_value,
    specimen_label,
    stress_text,
    stresses,
)
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.stats._rows import group_keys

_FUNCTION = "oedometer_fit()"
_STRESS = "applied_vertical_stress"
_VOID_RATIO = "void_ratio_at_increment_end"
_REQUIRED = ("specimen_id", _STRESS, _VOID_RATIO)
#: The specimen's initial void ratio, e0, before any load (CONG_IVR).
_INITIAL = "void_ratio"
_NO_INITIAL = "no initial void ratio"
_IN_SITU = "effective_vertical_stress"
#: Lunne et al.'s (1997) limits of Δe/e0 (l1, l2, l3) per OCR row, as Krage et
#: al. (2015, Table 1) give them: below l1 "very good to excellent", l1 to l2
#: "good to fair", l2 to l3 "poor", above l3 "very poor" (decision 13).
SAMPLE_QUALITY_LIMITS = {
    "OCR 1-2": (0.04, 0.07, 0.14),
    "OCR 2-4": (0.03, 0.05, 0.10),
}
SAMPLE_QUALITY_CLASSES = ("very good to excellent", "good to fair", "poor", "very poor")
_CAVEAT = (
    "The class uses this test's OCR: disturbance lowers σ′p and so the OCR, which "
    "can move a poor sample into the more lenient OCR 1-2 row."
)
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
    r"""Fit each oedometer specimen's curve: σ′p by Oikawa (1987), Cc, Cr and Cs.

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
    don't cross exactly at $\sigma'_p$. The compression ratio, for comparing
    with a lab's $C_R$ from a strain plot, is $CR = C_c / (1 + e_0)$, with
    $e_0$ the specimen's initial ``void_ratio``.

    **The swelling index** $C_s$ is the slope of $e$ against
    $\log_{10}\sigma'_v$ (positive) over an unload: the point the unload
    starts from and the consecutive ``unloading`` rows after it, at least 2
    points, by least squares. The specimen's $C_s$ is the first unload's,
    the loop the lab ran on purpose, rather than the final unload, often cut
    short; every unload's $C_s$ is on the result with the stress it starts
    from. A reload is never used: it is a different branch, with hysteresis.
    $C_s$ doesn't depend on $\sigma'_p$, so it is given when $\sigma'_p$
    isn't. $C_r$ and $C_s$ are kept apart because disturbance raises $C_r$.

    **The check on σ′p** is Pacheco Silva's (1970) construction, as
    Paniagua et al. (2016, §2.4) give it: (i) the virgin line
    $e = c - C_c\log_{10}\sigma'_v$ meets the horizontal $e = e_0$ at
    $\sigma_A$, $\log_{10}\sigma_A = (c - e_0)/C_c$; (ii) $e_B$ is the
    loading curve's void ratio at $\sigma_A$, interpolated linearly in $e$
    against $\log_{10}\sigma'_v$ between the loading points either side;
    (iii) the horizontal through $e_B$ meets the virgin line at the check's
    $\log_{10}\sigma'_p = (c - e_B)/C_c$. It reuses the fitted virgin line,
    so it is deterministic too. $e_0$ is the specimen's ``void_ratio``, "the
    specimen void ratio before any load has been applied", never the first
    increment's starting $e$, which already holds the seating load or a
    swell on flooding. With $e_0$ blank, or $\sigma_A$ outside the loading
    stresses, the check is blank with the reason: nothing is extrapolated.
    Both values are on the result, and neither is preferred by a warning.

    **OCR and sample quality,** where the rows give the specimen's
    ``effective_vertical_stress`` ($\sigma'_{v0}$, from
    ``ht.analysis.vertical_stress()`` run on the rows first):
    $OCR = \sigma'_p / \sigma'_{v0}$, kept and warned about below 1
    (disturbance, a wrong $\sigma'_{v0}$ or underconsolidation), never
    clipped. Without the column, or with it blank, OCR is blank with the
    reason; $\sigma'_{v0}$ is never assumed. The sample quality is Lunne et
    al.'s (1997) normalized change in void ratio on reconsolidation,

    $$
    \frac{\Delta e}{e_0} = \frac{e_0 - e(\sigma'_{v0})}{e_0}
    $$

    with $e(\sigma'_{v0})$ interpolated linearly in $e$ against
    $\log_{10}\sigma'_v$ between the loading points either side, and
    counted from $e_0$, so a swell on flooding counts. A $\sigma'_{v0}$
    below the first loading stress or above the highest gives a blank, not
    an extrapolation. Its class is read in the row of this test's OCR:

    | OCR | very good to excellent | good to fair | poor | very poor |
    |---|---|---|---|---|
    | 1 to < 2 | < 0.04 | 0.04 to < 0.07 | 0.07 to 0.14 | > 0.14 |
    | 2 to 4 | < 0.03 | 0.03 to < 0.05 | 0.05 to 0.10 | > 0.10 |

    Outside OCR 1-4, without an OCR, or below 0 (the specimen swelled past
    $e_0$), $\Delta e/e_0$ is given without a class, with the reason.
    **Caveat:** the OCR is this test's, the only one at hand, and
    disturbance lowers $\sigma'_p$ and so the OCR, which can move a poor
    sample into the more lenient OCR 1-2 row. The summary says so wherever
    a class is given.

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

    Sources: Oikawa, H. (1987). Compression curve of soft soils. *Soils and
    Foundations* 27(3), 99-104, doi:10.3208/sandf1972.27.3_99. Pacheco
    Silva, F. (1970). Uma nova construção gráfica para a determinação da
    pressão de pré-adensamento de uma amostra de solo. Proc. 4th Brazilian
    Conference on Soil Mechanics and Foundation Engineering, Rio de Janeiro,
    225-232; read in Paniagua, L'Heureux, Yang & Lunne (2016), Proc. 17th
    Nordic Geotechnical Meeting (NGM 2016), Reykjavik, §2.4, p. 548. Lunne,
    T., Berre, T. & Strandvik, S. (1997). Sample disturbance effects in soft
    low plastic Norwegian clay. Proc. Symposium on Recent Developments in
    Soil and Pavement Mechanics, Rio de Janeiro, 81-102; the classes as Krage,
    DeJong, DeGroot, Dyer & Lukas (2015) give them, Proc. 6th International
    Conference on Earthquake Geotechnical Engineering, Table 1.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per increment, as ``p.oedometer()`` gives (or a CSV in
        ``ht.template("oedometer")``'s shape): ``specimen_id``,
        ``applied_vertical_stress`` and ``void_ratio_at_increment_end``, in
        the order the increments were applied. ``load_branch`` and
        ``void_ratio`` (the specimen's initial $e_0$) and
        ``effective_vertical_stress`` ($\sigma'_{v0}$ at its depth), one
        value per specimen, are read where present. One fit per ``specimen_id``, in
        sorted order.
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

    Warns
    -----
    UserWarning
        For an OCR below 1, naming the specimens.

    Raises
    ------
    HangtuError
        For a frame without ``specimen_id``, ``applied_vertical_stress`` or
        ``void_ratio_at_increment_end``, a row with a blank ``specimen_id``, a
        negative void ratio, a specimen with more than one ``void_ratio`` or
        ``effective_vertical_stress``, a
        ``load_branch`` value the fit doesn't know, a stress column without
        units or in a unit that isn't a stress, or an argument out of its
        range.

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
    branch = branches(df, _FUNCTION)
    stress, unit = stresses(df, units, display_units)
    void_ratio = numeric_column(df, _VOID_RATIO)
    negative = void_ratio < 0
    if negative.any():
        raise HangtuError(
            f"Rows {rows_text(df.index[negative])} have a negative "
            f"{_VOID_RATIO}, which a soil can't have. Check those rows."
        )
    identifiers = tuple(column for column in _IDENTIFIERS if column in df.columns)
    initial = (
        numeric_column(df, _INITIAL)
        if _INITIAL in df.columns
        else np.full(len(df), np.nan)
    )
    in_situ_stress = in_situ(df, units, display_units, unit)
    text = f" {unit}" if unit else ""
    specimens = []
    for _, rows in group_keys(df, ["specimen_id"]):
        positions = np.flatnonzero(rows)
        record = _specimen(df, positions, stress, void_ratio, branch, identifiers, text)
        record["void_ratio"] = one_value(df, positions, initial, _INITIAL, record)
        record |= _compression_ratio(record)
        record |= _pacheco_silva(record, text)
        record["effective_vertical_stress"] = (
            np.nan
            if in_situ_stress is None
            else one_value(df, positions, in_situ_stress, _IN_SITU, record)
        )
        record |= _stress_history(record, in_situ_stress is not None, text)
        del record["_loading"]
        specimens.append(record)
    below = [r["label"] for r in specimens if r["overconsolidation_ratio"] < 1]
    if below:
        warn(
            f"{_FUNCTION}: OCR below 1 in {', '.join(below)}. It is kept as "
            "computed, not clipped: check for sample disturbance (which lowers "
            "σ′p), a wrong σ′v0, or an underconsolidated layer."
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
        specimens=tuple(specimens),
    )


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
        "label": specimen_label(key),
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
    record |= _swelling(points)
    record["_loading"] = (x, e)
    return record


def _stress_history(
    record: dict[str, Any], has_column: bool, unit: str
) -> dict[str, Any]:
    """OCR, Δe/e0 and Lunne et al.'s class (decisions 11-13), or why not."""
    in_situ = record["effective_vertical_stress"]
    stress = record["preconsolidation_stress"]
    e0 = record["void_ratio"]
    x, e = record["_loading"]
    if not has_column:
        no_in_situ = (
            "no effective_vertical_stress: run ht.analysis.vertical_stress() on "
            "the rows first"
        )
    else:
        no_in_situ = "no effective vertical stress at the specimen's depth"
    result: dict[str, Any] = {
        "overconsolidation_ratio": np.nan,
        "overconsolidation_ratio_reason": None,
        "void_ratio_at_effective_vertical_stress": np.nan,
        "normalized_void_ratio_change": np.nan,
        "normalized_void_ratio_change_reason": None,
        "sample_quality": None,
        "sample_quality_row": None,
        "sample_quality_reason": None,
    }
    if math.isnan(in_situ):
        result["overconsolidation_ratio_reason"] = no_in_situ
    elif math.isnan(stress):
        result["overconsolidation_ratio_reason"] = (
            f"no σ′p: {record['preconsolidation_stress_reason']}"
        )
    else:
        result["overconsolidation_ratio"] = stress / in_situ

    if math.isnan(e0) or e0 == 0:
        result["normalized_void_ratio_change_reason"] = _NO_INITIAL
    elif math.isnan(in_situ):
        result["normalized_void_ratio_change_reason"] = no_in_situ
    elif not len(x):
        result["normalized_void_ratio_change_reason"] = "no loading branch"
    elif in_situ < x[0]:
        result["normalized_void_ratio_change_reason"] = (
            f"σ′v0 = {stress_text(in_situ)}{unit} is below the first loading "
            f"stress ({stress_text(x[0])}{unit})"
        )
    elif in_situ > x[-1]:
        result["normalized_void_ratio_change_reason"] = (
            f"σ′v0 = {stress_text(in_situ)}{unit} is above the highest loading "
            f"stress ({stress_text(x[-1])}{unit})"
        )
    else:
        at = _on_curve(x, e, in_situ)
        result["void_ratio_at_effective_vertical_stress"] = at
        result["normalized_void_ratio_change"] = (e0 - at) / e0
    return result | _sample_quality(result, record)


def _sample_quality(result: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    """Grade Δe/e0 by Lunne et al. (1997) in this test's OCR row (decision 13)."""
    change = result["normalized_void_ratio_change"]
    ocr = result["overconsolidation_ratio"]
    if math.isnan(change):
        return {
            "sample_quality_reason": (
                f"no Δe/e0: {result['normalized_void_ratio_change_reason']}"
            )
        }
    if change < 0:
        record["notes"].append(
            "Δe/e0 is below 0: the specimen swelled past e0 by σ′v0 (on flooding, "
            "or a seating error), so it has no class."
        )
        return {"sample_quality_reason": "Δe/e0 below 0 has no class"}
    if math.isnan(ocr):
        reason = result["overconsolidation_ratio_reason"]
        return {"sample_quality_reason": f"no OCR: {reason}"}
    if 1 <= ocr < 2:
        row = "OCR 1-2"
    elif 2 <= ocr <= 4:
        row = "OCR 2-4"
    else:
        return {
            "sample_quality_reason": (
                f"OCR = {ocr:.3g} is outside the classes' range (1 to 4)"
            )
        }
    first, second, third = SAMPLE_QUALITY_LIMITS[row]
    if change < first:
        grade = 0
    elif change < second:
        grade = 1
    elif change <= third:
        grade = 2
    else:
        grade = 3
    return {
        "sample_quality": SAMPLE_QUALITY_CLASSES[grade],
        "sample_quality_row": row,
    }


def _swelling(points: list[dict[str, Any]]) -> dict[str, Any]:
    """Cs of every unload run; the specimen's is the first run's (decision 9).

    A run's points are the point it starts from and its unloading rows, each
    with a stress above 0 and a void ratio; reloading is never used.
    """
    numbers = sorted({p["unload_run"] for p in points} - {None})
    runs = []
    for number in numbers:
        members = [
            p
            for p in points
            if p["unload_run"] == number
            and not math.isnan(p["void_ratio"])
            and p["applied_vertical_stress"] > 0
        ]
        start = next(p for p in points if p["unload_run"] == number)
        run: dict[str, Any] = {
            "run": number,
            "start_stress": start["applied_vertical_stress"],
            "swelling_index": np.nan,
            "swelling_line": None,
            "reason": None,
            "notes": [],
        }
        if len(members) < 2:
            run["reason"] = (
                f"{len(members)} point{'' if len(members) == 1 else 's'} in the "
                "unload: a line needs at least 2"
            )
        else:
            x = np.array([p["applied_vertical_stress"] for p in members])
            e = np.array([p["void_ratio"] for p in members])
            line = _index_line(x, e)
            run["swelling_index"] = line["index"]
            run["swelling_line"] = line
            if len(members) == 2:
                run["notes"].append("2 points: the line passes through both.")
        runs.append(run)
    if not runs:
        return {
            "swelling_index": np.nan,
            "swelling_index_reason": "no unloading",
            "unload_runs": [],
        }
    first = runs[0]
    return {
        "swelling_index": first["swelling_index"],
        "swelling_index_reason": first["reason"],
        "unload_runs": runs,
    }


def _compression_ratio(record: dict[str, Any]) -> dict[str, Any]:
    """CR = Cc / (1 + e0) (decision 7), or blank with the reason."""
    if math.isnan(record["compression_index"]):
        reason = f"no Cc: {record['preconsolidation_stress_reason']}"
        return {"compression_ratio": np.nan, "compression_ratio_reason": reason}
    if math.isnan(record["void_ratio"]):
        return {"compression_ratio": np.nan, "compression_ratio_reason": _NO_INITIAL}
    return {
        "compression_ratio": record["compression_index"] / (1 + record["void_ratio"]),
        "compression_ratio_reason": None,
    }


def _pacheco_silva(record: dict[str, Any], unit: str) -> dict[str, Any]:
    """Check σ′p by Pacheco Silva (1970), decision 10, or give why it can't.

    (i) The virgin line e = c - Cc log10 σ′v meets e = e0 at σA; (ii) e_B is
    the loading curve's e at σA; (iii) the horizontal through e_B meets the
    virgin line at the check's σ′p.
    """
    result: dict[str, Any] = {
        "preconsolidation_stress_pacheco_silva": np.nan,
        "pacheco_silva_reason": None,
        "pacheco_silva": None,
        "void_ratio_at_preconsolidation_stress_pacheco_silva": np.nan,
    }
    line = record["compression_line"]
    e0 = record["void_ratio"]
    if line is None:
        result["pacheco_silva_reason"] = (
            f"no σ′p: {record['preconsolidation_stress_reason']}"
        )
        return result
    if math.isnan(e0):
        result["pacheco_silva_reason"] = _NO_INITIAL
        return result
    x, e = record["_loading"]
    c, index = line["intercept"], line["index"]
    stress_a = 10 ** ((c - e0) / index)
    if not x[0] <= stress_a <= x[-1]:
        where = (
            f"loading from {stress_text(x[0])}{unit}"
            if stress_a < x[0]
            else f"loading to {stress_text(x[-1])}{unit}"
        )
        result["pacheco_silva_reason"] = (
            "the construction falls outside the measured curve "
            f"(σA = {stress_text(stress_a)}{unit}, {where})"
        )
        result["pacheco_silva"] = {"stress_a": stress_a, "void_ratio_b": np.nan}
        return result
    void_ratio_b = _on_curve(x, e, stress_a)
    stress = 10 ** ((c - void_ratio_b) / index)
    result |= {
        "preconsolidation_stress_pacheco_silva": stress,
        "pacheco_silva": {"stress_a": stress_a, "void_ratio_b": void_ratio_b},
        "void_ratio_at_preconsolidation_stress_pacheco_silva": _on_curve(x, e, stress),
    }
    return result


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
    return (
        f"the lines cross at {stress_text(crossing)}{unit}, outside the loading "
        f"stresses ({stress_text(x[0])} to {stress_text(x[-1])}{unit})"
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
    check = record["preconsolidation_stress_pacheco_silva"]
    values = []
    if not math.isnan(stress):
        checked = (
            f"Pacheco Silva {format_number(check)}{unit}"
            if not math.isnan(check)
            else "Pacheco Silva not given"
        )
        values += [
            f"σ′p = {format_number(stress)}{unit} (Oikawa; {checked})",
            f"Cc = {_index_text(record['compression_index'])}",
            f"Cr = {_index_text(record['recompression_index'])}",
        ]
    if not math.isnan(record["swelling_index"]):
        values.append(f"Cs = {_index_text(record['swelling_index'])}")
    if not math.isnan(record["compression_ratio"]):
        values.append(f"CR = {_index_text(record['compression_ratio'])}")
    if math.isnan(stress):
        lines = [f"{label}: σ′p not given: {record['preconsolidation_stress_reason']}"]
        if values:
            lines.append(f"  {', '.join(values)}")
    else:
        lines = [f"{label}: {', '.join(values)}"]
        for name, reason in (
            ("Pacheco Silva", record["pacheco_silva_reason"]),
            ("CR", record["compression_ratio_reason"]),
        ):
            if reason:
                lines.append(f"  {name} not given: {reason}")
    if record["swelling_index_reason"]:
        lines.append(f"  Cs not given: {record['swelling_index_reason']}")
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
    lines.extend(_stress_history_text(record, unit, format_number))
    for run in record["unload_runs"]:
        text = f"Cs = {_index_text(run['swelling_index'])}"
        if run["reason"] is not None:
            text = f"no Cs: {run['reason']}"
        if run["notes"]:
            text += f" ({' '.join(run['notes']).rstrip('.')})"
        used = "used" if run["run"] == 1 else "not used"
        lines.append(
            f"  unload {run['run']} from {format_number(run['start_stress'])}{unit}"
            f", {used}: {text}"
        )
    lines.extend(f"  {note}" for note in record["notes"])
    return lines


def _stress_history_text(
    record: dict[str, Any], unit: str, format_number: Any
) -> list[str]:
    """Write OCR, Δe/e0 and the class, each or why it isn't given."""
    lines = []
    ocr = record["overconsolidation_ratio"]
    in_situ = record["effective_vertical_stress"]
    if math.isnan(ocr):
        lines.append(f"  OCR not given: {record['overconsolidation_ratio_reason']}")
    else:
        below = " (< 1)" if ocr < 1 else ""
        lines.append(
            f"  OCR = {ocr:.3g}{below} at σ′v0 = {format_number(in_situ)}{unit}"
        )
    change = record["normalized_void_ratio_change"]
    if math.isnan(change):
        reason = record["normalized_void_ratio_change_reason"]
        if reason != record["overconsolidation_ratio_reason"]:
            lines.append(f"  Δe/e0 not given: {reason}")
        return lines
    text = f"  Δe/e0 = {_index_text(change)}"
    if record["sample_quality"] is not None:
        text += f", {record['sample_quality']} ({record['sample_quality_row']} row)"
        lines += [text, f"  {_CAVEAT}"]
    else:
        lines.append(f"{text}, no class: {record['sample_quality_reason']}")
    return lines
