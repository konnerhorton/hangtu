"""``describe()``: count, mean, spread and percentiles by group.

Spec: docs/work/m15a-describe.md.

``summarize()`` is the arithmetic, on values already chosen. ``describe()``
chooses them from a frame; P01 and P07 call ``summarize()`` on the values they
draw, so a figure and a table of the same rows agree.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib.metadata import version
from itertools import pairwise
from typing import Any

import numpy as np
import pandas as pd

from hangtu._data import text_values
from hangtu.errors import HangtuError, warn
from hangtu.stats import _rows
from hangtu.stats._result import DescribeResult, _heading
from hangtu.stats._rows import COUNTS

PERCENTILE_METHOD = "Hyndman & Fan (1996) definition 7"
DEFAULT_PERCENTILES = (5, 25, 75, 95)


@dataclass(frozen=True)
class Summary:
    """The statistics of one group, and why each NaN one is NaN."""

    #: ``count`` is an int; the rest are floats, NaN when not reported.
    statistics: dict[str, float]
    #: Statistic -> the number of values it needs, or the reason it isn't reported.
    reasons: dict[str, int | str]


def percentile_name(p: float) -> str:
    """Name the column of percentile ``p``: ``percentile_25``, ``percentile_2_5``."""
    return "percentile_" + f"{p:g}".replace(".", "_")


def percentile_floor(p: float) -> int:
    """Return the fewest values for P``p``: one beyond it on each side."""
    return math.ceil(100 / min(p, 100 - p) - 1e-9)


def check_percentiles(percentiles: Any, function: str) -> tuple[float, ...]:
    """Return ``percentiles`` as floats; raise unless ascending in (0, 100)."""
    try:
        values = tuple(float(p) for p in percentiles)
    except (TypeError, ValueError):
        values = ()
    if (
        not values
        or not all(0 < p < 100 for p in values)
        or any(b <= a for a, b in pairwise(values))
    ):
        raise HangtuError(
            f"{function} percentiles must be numbers between 0 and 100, ascending "
            f"and without repeats, not {percentiles!r}. Example: percentiles=(10, 90)."
        )
    return values


def summarize(
    values: np.ndarray,
    *,
    percentiles: Sequence[float] = DEFAULT_PERCENTILES,
    interval: bool = False,
    log: bool = False,
) -> Summary:
    """Summarize finite values (Decision 1 of the spec).

    ``interval`` is True for a column with no true zero (``scale: interval``),
    which has no CoV. With ``log``, the values must all be above 0, and the
    geometric mean and standard deviation replace the mean, standard deviation
    and CoV. Percentiles are Hyndman & Fan (1996) definition 7.
    """
    values = np.asarray(values, dtype=float)
    n = values.size
    nan = float("nan")
    statistics: dict[str, float] = {"count": n}
    reasons: dict[str, int | str] = {}
    spread = (
        ("geometric_mean", "geometric_standard_deviation")
        if log
        else ("mean", "standard_deviation", "coefficient_of_variation")
    )
    for name in spread:
        statistics[name] = nan
    if log and n:
        logs = np.log(values)
        statistics["geometric_mean"] = float(np.exp(logs.mean()))
        if n >= 2:
            statistics["geometric_standard_deviation"] = float(np.exp(logs.std(ddof=1)))
    elif n:
        mean = float(values.mean())
        statistics["mean"] = mean
        if n >= 2:
            deviation = float(values.std(ddof=1))
            statistics["standard_deviation"] = deviation
            if interval:
                reasons["coefficient_of_variation"] = (
                    "isn't reported on an interval scale (no true zero)"
                )
            elif mean <= 0:
                reasons["coefficient_of_variation"] = "needs a mean above 0"
            else:
                statistics["coefficient_of_variation"] = deviation / mean
    if n == 1:
        reasons.update(
            dict.fromkeys(
                ["geometric_standard_deviation"]
                if log
                else ["standard_deviation", "coefficient_of_variation"],
                2,
            )
        )
    statistics["minimum"] = float(values.min()) if n else nan
    below = [p for p in percentiles if p < 50]
    above = [p for p in percentiles if p >= 50]
    for p in below:
        statistics[percentile_name(p)] = nan
    statistics["median"] = float(np.median(values)) if n else nan
    for p in above:
        statistics[percentile_name(p)] = nan
    statistics["maximum"] = float(values.max()) if n else nan
    for p in percentiles:
        floor = percentile_floor(p)
        if n >= floor:
            statistics[percentile_name(p)] = float(
                np.percentile(values, p, method="linear")
            )
        elif n:
            reasons[percentile_name(p)] = floor
    return Summary(statistics, reasons)


def describe(
    data: pd.DataFrame | pd.Series | Sequence[float] | np.ndarray,
    *,
    value: str | None = None,
    by: str | Sequence[str] | None = None,
    percentiles: Sequence[float] = DEFAULT_PERCENTILES,
    log: bool = False,
    pool: str | Sequence[str] | None = None,
    include_assumed: bool = False,
    units: str | Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> DescribeResult:
    r"""Count, mean, spread and percentiles of measured or estimated values, by group.

    Summarizes what the tests say, e.g. each geology unit's plasticity index
    before you set a judgment. It never selects a design value.

    **Statistics per group** (each NaN below its floor, with the reason in
    the summary):

    - ``count``, the number of numbers;
    - ``mean`` and ``minimum``, ``median``, ``maximum``, from 1 value;
    - ``standard_deviation`` (sample, $n - 1$) from 2 values, and
      ``coefficient_of_variation`` = standard deviation / mean, from 2
      values with a mean above 0, never for a column with no true zero
      (``scale: interval`` in ``ht.columns()``: elevation, depth);
    - each of ``percentiles`` as ``percentile_<p>``, reported only with at
      least one value beyond it on each side: $n \times \min(p, 100 - p) /
      100 \ge 1$. P25 and P75 need 4 values, P10 and P90 10, P5 and P95 20.

    Percentiles are Hyndman & Fan (1996) definition 7, the linear
    interpolation of ``numpy.percentile``, everywhere in hangtu, so two
    summaries of the same rows can't differ by method. Fewer than 3 values
    in a group warns.

    **Flagged values are counted, never dropped silently or pooled
    unawares.** The registry says which columns flag a value
    (``statistics:`` in ``columns.yaml``); a flag applies when its column is
    in the frame. Each row is counted once, under the first that applies:

    1. a band with no value (``<value>_lower`` or ``_upper`` only, from a
       correlation): left out, ``count_range``. A band is an interval, not
       two values or its midpoint;
    2. non-plastic (``non_plastic``, or ``NP`` in the cell): left out,
       ``count_non_plastic``, never a blank or 0;
    3. assumed (``particle_density_assumed``, or ``specific_gravity_source``
       ``assumed`` or ``judgment`` for Gs and what is derived from it): left
       out unless ``include_assumed=True``, ``count_assumed``, with a warning;
    4. other text: left out, ``count_text``, with a warning naming it;
    5. blank: left out, ``count_blank``. A refusal with a blank N is a blank;
    6. with ``log=True``, a value at or below 0: ``count_not_positive``.

    Refusals (``spt_refusal``) and ``>`` values (``qualifier``) are lower
    bounds, ``<`` values upper bounds: they are summarized at the value the
    column holds and counted (``count_at_least``, ``count_at_most``), and
    the summary says the mean is then an underestimate or an overestimate.
    ``count`` and the counts of rows left out add up to the group's rows.

    **Sources aren't mixed.** Rows from different sources in one group raise
    an error naming them: different ``correlation_name`` (blank for a
    measured value), ``source`` (lab or field) or ``test_type``. Group by
    the column, filter the rows, or pool them on purpose with ``pool=``,
    which the result records. The check reads only the rows summarized.

    Parameters
    ----------
    data : pandas.DataFrame, pandas.Series, list or array
        The values. A DataFrame needs ``value=``; a Series is its own value
        (its name is the column). ``by=`` needs a DataFrame.
    value : str
        The column to summarize, e.g. ``"plasticity_index"``.
    by : str or list of str, optional
        The column(s) to group by, e.g. ``"geology_unit"``. Groups are sorted
        by each column's categorical order, else by name, with a blank key as
        ``"(blank)"``, last. Without ``by``, all rows are one group.
    percentiles : sequence of float
        The percentiles to report, ascending, between 0 and 100. The median
        is always reported as ``median``.
    log : bool
        Summarize on a log scale, for values spanning orders of magnitude
        such as hydraulic conductivity: ``geometric_mean`` = exp(mean of ln
        x) and ``geometric_standard_deviation`` = exp(standard deviation of
        ln x), a factor with no unit, replace the mean, standard deviation and
        CoV. Minimum, median, maximum and percentiles stay those of the
        values. Values at or below 0 are counted (``count_not_positive``) and
        left out, with a warning.
    pool : str or list of str, optional
        Source columns to pool across on purpose, e.g. ``["source"]`` to
        summarize lab and field values together. The result's ``pooled`` and
        its summary record it, with each group's count per source.
    include_assumed : bool
        Summarize assumed values with the rest. They are still counted, and
        the summary says how many it includes.
    units : str or dict, optional
        The value's unit, e.g. ``"kPa"``, or ``{column: unit}``. Without it
        the unit comes from ``df.attrs["units"]``, then from the registry for
        counts, percentages and dimensionless columns; a column whose unit is
        unknown raises. A list or array without it is summarized with
        "(units not given)".
    display_units : {"US", "SI"}, optional
        Convert the values to this system's display unit before summarizing.
        None keeps the column's unit. ``ht.settings.display_units`` is never
        used, so a summary doesn't change with a session setting.

    Returns
    -------
    DescribeResult
        ``.to_frame()`` has one row per group: the ``by`` columns, the
        statistics, then the counts. ``print(result)`` shows the same numbers
        with their units and notes.

    Raises
    ------
    ColumnError
        For a missing column, a column that holds no numbers, or a true/false
        column.
    HangtuError
        For rows from different sources in one group, or a ``pool=`` column
        that isn't a source column.
    UnitsError
        For a value column whose unit is unknown.

    Examples
    --------
    >>> limits = p.atterberg()
    >>> ht.stats.describe(limits, value="plasticity_index", by="geology_unit")
    """
    function = "describe()"
    read = _rows.read_input(data, value, by, pool, units, function)
    frame, value = read.frame, read.value
    percentiles = check_percentiles(percentiles, function)
    pooled = _rows.check_pool(pool, read, function)
    numbers, texts = text_values(frame, read.column)
    numbers, unit = _rows.convert(numbers, read, display_units, function)
    interval, scale_known = _rows.scale(value)
    flags = (
        _rows.read_flags(frame, read.column)
        if value is not None
        else _rows.Flags.none(frame)
    )
    reasons, marks = _rows.choose_rows(
        numbers, texts, flags, include_assumed=include_assumed, positive_only=log
    )
    counted = (*COUNTS, "count_not_positive") if log else COUNTS
    included = reasons == ""

    keys = _rows.group_keys(frame, read.by)
    _rows.check_sources(frame, keys, included, read, pooled, function)
    groups, notes_by_reason, small = [], {}, []
    for key, rows in keys:
        summary = summarize(
            numbers[rows & included],
            percentiles=percentiles,
            interval=interval,
            log=log,
        )
        counts = {
            name: int(marks.get(name, reasons == name)[rows].sum()) for name in counted
        }
        groups.append(
            {
                "key": key,
                "statistics": summary.statistics,
                "counts": counts,
                "reasons": summary.reasons,
                "text": _rows.spellings(texts[rows]),
                "sources": {
                    column: _rows.breakdown(frame.loc[rows & included, column])
                    for column in pooled
                },
            }
        )
        label = ", ".join(map(str, key.values())) or "All"
        if summary.statistics["count"] < 3:
            small.append(f"{label} ({int(summary.statistics['count'])})")
        for name, why in summary.reasons.items():
            notes_by_reason.setdefault(why, {}).setdefault(name, []).append(label)

    _rows.warn_left_out(reasons, read.column, function)
    _rows.warn_text(texts, read.column, function)
    if small:
        warn(
            f"describe() has fewer than 3 values of {read.column!r} in: "
            f"{', '.join(small)}. Statistics of so few values say little; "
            "check the groups, or report the values themselves."
        )
    not_positive = int((reasons == "count_not_positive").sum())
    if not_positive:
        warn(
            f"describe(log=True) left out {not_positive} values of {read.column!r} "
            "at or below 0: a log scale has no place for them. They are counted "
            "in count_not_positive."
        )
    notes = _notes(
        notes_by_reason,
        unit_given=read.unit_given,
        scale_known=scale_known,
        log=log,
    )
    notes[-1:-1] = _flag_notes(groups, read.by, pooled, include_assumed)
    return DescribeResult(
        kind="property",
        function="describe",
        value=value,
        unit=unit,
        notes=tuple(notes),
        judgments=dict(frame.attrs.get("judgments", {})),
        hangtu_version=version("hangtu"),
        by=tuple(read.by),
        log=log,
        pooled=tuple(pooled),
        include_assumed=include_assumed,
        percentiles=percentiles,
        percentile_method=PERCENTILE_METHOD,
        groups=tuple(groups),
    )


def _flag_notes(
    groups: list[dict[str, Any]],
    by: list[str],
    pooled: list[str],
    include_assumed: bool,
) -> list[str]:
    """Return the notes on bounds, assumed values and pooling."""
    notes = []

    def total(name: str) -> int:
        return sum(group["counts"][name] for group in groups)

    if total("count_at_least"):
        notes.append(
            f"Lower bounds (refusal or '>'): {total('count_at_least')}. "
            "The mean and upper percentiles are underestimates."
        )
    if total("count_at_most"):
        notes.append(
            f"Upper bounds ('<'): {total('count_at_most')}. The mean and "
            "lower percentiles are overestimates."
        )
    if include_assumed and total("count_assumed"):
        notes.append(f"Assumed values included: {total('count_assumed')}.")
    for group in groups:
        label = ", ".join(map(str, group["key"].values()))
        for column in pooled:
            listed = ", ".join(
                f"{value} {count}" for value, count in group["sources"][column].items()
            )
            where = f" in {label}" if by else ""
            notes.append(f"Pooled across {column}{where}: {listed}.")
    return notes


def _notes(
    by_reason: dict[int | str, dict[str, list[str]]],
    *,
    unit_given: bool,
    scale_known: bool,
    log: bool,
) -> list[str]:
    """Return the summary's lines under the table."""
    notes = []
    if not unit_given:
        notes.append("(units not given)")
    for why, statistics in by_reason.items():
        names = list(statistics)
        headings = "/".join(_heading(name) for name in names)
        labels = list(
            dict.fromkeys(label for name in names for label in statistics[name])
        )
        if isinstance(why, int):
            verb = "needs" if len(names) == 1 else "need"
            text = f"{headings} {verb} {why} values"
        else:
            text = f"{headings} {why}"
        notes.append(f"{text}: {', '.join(labels)}.")
    if not scale_known and not log:
        notes.append(
            "CoV is reported, but the column's scale is unknown: "
            "check it has a true zero."
        )
    if log:
        notes.append(
            "Log scale: geometric mean and geometric standard deviation (a factor); "
            "minimum, median, maximum and percentiles are of the values."
        )
    notes.append(f"Percentiles: {PERCENTILE_METHOD}.")
    return notes
