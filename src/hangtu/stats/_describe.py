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

from hangtu import units as _units
from hangtu._data import TEXT_FLAGS, flag_column, text_values
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.registry import column_info, statistics_roles
from hangtu.stats._result import DescribeResult, _heading

PERCENTILE_METHOD = "Hyndman & Fan (1996) definition 7"
DEFAULT_PERCENTILES = (5, 25, 75, 95)
#: The counts of rows not summarized, or summarized as bounds, in their order
#: of checks (Decision 6). ``count_not_positive`` is added with ``log=True``.
COUNTS = (
    "count_at_least",
    "count_at_most",
    "count_non_plastic",
    "count_assumed",
    "count_range",
    "count_text",
    "count_blank",
)
BLANK_GROUP = "(blank)"


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
    read = _read_input(data, value, by, pool, units)
    frame, value = read.frame, read.value
    percentiles = check_percentiles(percentiles, "describe()")
    pooled = _check_pool(pool, read)
    numbers, texts = text_values(frame, read.column)
    numbers, unit = _convert(numbers, read, display_units)
    interval, scale_known = _scale(value)
    flags = _flags(frame, read.column) if value is not None else _Flags.none(frame)

    # Decision 6: each row is counted once, under the first reason that applies.
    reasons = np.full(len(frame), "", dtype=object)
    _assign(reasons, flags.band & np.isnan(numbers) & (texts == ""), "count_range")
    _assign(reasons, flags.non_plastic | (texts == "NP"), "count_non_plastic")
    if not include_assumed:
        _assign(reasons, flags.assumed, "count_assumed")
    _assign(reasons, texts != "", "count_text")
    _assign(reasons, np.isnan(numbers), "count_blank")
    if log:
        _assign(reasons, numbers <= 0, "count_not_positive")
    counted = (*COUNTS, "count_not_positive") if log else COUNTS
    included = reasons == ""
    marks = {
        "count_at_least": flags.at_least & included,
        "count_at_most": flags.at_most & included,
    }
    if include_assumed:
        marks["count_assumed"] = flags.assumed & included

    keys = _group_keys(frame, read.by)
    _check_sources(frame, keys, included, read, pooled)
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
                "text": _spellings(texts[rows]),
                "sources": {
                    column: _breakdown(frame.loc[rows & included, column])
                    for column in pooled
                },
            }
        )
        label = ", ".join(map(str, key.values())) or "All"
        if summary.statistics["count"] < 3:
            small.append(f"{label} ({int(summary.statistics['count'])})")
        for name, why in summary.reasons.items():
            notes_by_reason.setdefault(why, {}).setdefault(name, []).append(label)

    _warn_left_out(reasons, read.column)
    _warn_text(texts, read.column)
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


@dataclass(frozen=True)
class _Input:
    frame: pd.DataFrame
    #: The value's name in the result, None for a list or array.
    value: str | None
    #: The column read in ``frame``.
    column: str
    by: list[str]
    unit: str | None
    quantity: str | None
    unit_given: bool


def _read_input(
    data: Any,
    value: str | None,
    by: Any,
    pool: Any,
    units: str | Mapping[str, str] | None,
) -> _Input:
    by_columns = [] if by is None else [by] if isinstance(by, str) else list(by)
    if isinstance(data, pd.Series):
        if value is not None:
            raise HangtuError(
                "describe() reads a Series as its own value, so value= is for a "
                "DataFrame. Pass the frame and value=, or the Series alone."
            )
        if data.name is not None:
            value = str(data.name)
            frame = data.to_frame(value)
            frame.attrs = dict(data.attrs)
            return _frame_input(frame, value, by_columns, units)
        data = data.to_numpy()
    if isinstance(data, pd.DataFrame):
        if not isinstance(value, str):
            raise HangtuError(
                "describe() needs value=, the column to summarize, with a DataFrame. "
                'Example: ht.stats.describe(df, value="plasticity_index")'
            )
        return _frame_input(data, value, by_columns, units)
    if value is not None or by_columns or pool is not None:
        raise HangtuError(
            "describe() takes value=, by= and pool= only with a DataFrame, which has "
            "columns to name. Pass a DataFrame, or the values alone."
        )
    if isinstance(units, Mapping):
        raise HangtuError(
            "describe() takes the unit of a list or array as text, e.g. "
            'units="kPa", since it has no columns to name.'
        )
    try:
        numbers = np.asarray(data, dtype=float)
    except (TypeError, ValueError):
        numbers = None
    if numbers is None or numbers.ndim != 1:
        raise HangtuError(
            "describe() takes a DataFrame, a Series, or a list or 1-D array of "
            f"numbers, not {type(data).__name__}. "
            "Example: ht.stats.describe([10, 12, 15])"
        )
    if units is not None:
        _units.parse_unit(units)
    return _Input(
        frame=pd.DataFrame({"value": numbers}),
        value=None,
        column="value",
        by=[],
        unit=units,
        quantity=None,
        unit_given=units is not None,
    )


def _frame_input(
    frame: pd.DataFrame,
    value: str,
    by: list[str],
    units: str | Mapping[str, str] | None,
) -> _Input:
    missing = [column for column in (value, *by) if column not in frame.columns]
    if missing:
        raise ColumnError(
            f"describe() needs the column {', '.join(map(repr, missing))}, which the "
            f"data doesn't have. Available columns: "
            f"{', '.join(map(str, frame.columns)) or 'none'}."
        )
    if value in by:
        raise HangtuError(
            f"describe() can't group {value!r} by itself. Choose another by= column."
        )
    info = column_info(value) or {}
    if info.get("type") == "bool" or pd.api.types.is_bool_dtype(frame[value]):
        raise ColumnError(
            f"Column {value!r} holds True or False, which describe() doesn't "
            "summarize. Count the rows instead, e.g. df[column].value_counts()."
        )
    if info.get("type") == "text" or _holds_no_numbers(frame, value):
        raise ColumnError(
            f"Column {value!r} holds no numbers to summarize. Choose a column of "
            "numbers, e.g. one listed by ht.columns()."
        )
    explicit = {}
    if isinstance(units, str):
        explicit = {value: units}
    elif isinstance(units, Mapping):
        explicit = {column: unit for column, unit in units.items() if column == value}
    elif units is not None:
        raise HangtuError(
            f'describe() units must be text such as "kPa", or a dict, not {units!r}.'
        )
    quantity = info.get("quantity")
    unit = _units.resolve_units(frame, [value], explicit, analysis=True)[value]
    return _Input(
        frame=frame,
        value=value,
        column=value,
        by=by,
        unit=unit,
        quantity=quantity,
        unit_given=True,
    )


def _holds_no_numbers(frame: pd.DataFrame, column: str) -> bool:
    """Return whether the cells that aren't blank are all unrecognized text."""
    numbers, texts = text_values(frame, column)
    filled = texts != ""
    recognized = np.isin(texts, list(TEXT_FLAGS.values()))
    return bool(filled.any() and np.isnan(numbers).all() and not recognized.any())


def _convert(
    numbers: np.ndarray, read: _Input, display_units: str | None
) -> tuple[np.ndarray, str | None]:
    """Convert to ``display_units``, and name the statistics' unit."""
    kind = _units.quantity_kind(read.quantity) if read.quantity else None
    if display_units is None:
        if kind is not None and kind["canonical"] is None:
            return numbers, kind["SI"]["text"]
        return numbers, read.unit
    if display_units not in ("US", "SI"):
        raise HangtuError(
            f'describe() display_units must be "US", "SI" or None, not '
            f"{display_units!r}."
        )
    if read.quantity is None and read.unit is not None:
        raise HangtuError(
            f"describe() can't convert {read.column!r} to {display_units} units: "
            "it isn't a registered column, so its kind of quantity is unknown. "
            "Convert it yourself, or leave display_units=None."
        )
    return _units.to_display(numbers, read.unit, read.quantity, display_units)


def _scale(value: str | None) -> tuple[bool, bool]:
    """Return whether the column is on an interval scale, and whether that is known."""
    info = column_info(value) if value else None
    if info is None or "scale" not in info:
        return False, False
    return info["scale"] == "interval", True


def _assign(reasons: np.ndarray, mask: np.ndarray, name: str) -> None:
    """Count rows under ``name`` unless an earlier check already counted them."""
    reasons[mask & (reasons == "")] = name


def _group_keys(
    frame: pd.DataFrame, by: list[str]
) -> list[tuple[dict[str, Any], np.ndarray]]:
    """Return each group's key and rows, in order (Decision 1)."""
    if not by:
        return [({}, np.ones(len(frame), bool))]
    columns = []
    for column in by:
        values = frame[column]
        blank = (
            values.isna().to_numpy() | (values.astype(str).str.strip() == "").to_numpy()
        )
        keys = values.astype(object).to_numpy()
        keys[blank] = BLANK_GROUP
        if isinstance(values.dtype, pd.CategoricalDtype):
            order = {category: i for i, category in enumerate(values.cat.categories)}
        else:
            order = {name: i for i, name in enumerate(sorted({str(k) for k in keys}))}

        def position(key, order=order):
            if key == BLANK_GROUP:
                return (1, 0)
            return (0, order.get(key, order.get(str(key), 0)))

        columns.append((keys, position))
    combinations = sorted(
        {tuple(keys[i] for keys, _ in columns) for i in range(len(frame))},
        key=lambda combination: [
            position(key)
            for key, (_, position) in zip(combination, columns, strict=True)
        ],
    )
    result = []
    for combination in combinations:
        rows = np.ones(len(frame), bool)
        for key, (keys, _) in zip(combination, columns, strict=True):
            rows &= keys == key
        result.append((dict(zip(by, combination, strict=True)), rows))
    return result


@dataclass(frozen=True)
class _Flags:
    """Each row's flags on the value column, from the registry's roles."""

    at_least: np.ndarray
    at_most: np.ndarray
    non_plastic: np.ndarray
    assumed: np.ndarray
    band: np.ndarray

    @classmethod
    def none(cls, frame: pd.DataFrame) -> "_Flags":
        empty = np.zeros(len(frame), bool)
        return cls(empty, empty, empty, empty, empty)


def _flags(frame: pd.DataFrame, value: str) -> _Flags:
    """Read the flag columns of the registry (Decision 3) that apply to ``value``."""
    masks = {role: np.zeros(len(frame), bool) for role in _ROLE_MASKS}
    at_most = np.zeros(len(frame), bool)
    for column, field in statistics_roles().items():
        role = field["role"]
        if role == "source" or column not in frame.columns:
            continue
        if value not in field.get("values", [value]):
            continue
        if role == "qualifier":
            text = frame[column].astype("string").str.strip()
            masks["at_least"] |= (text == ">").fillna(False).to_numpy(bool)
            at_most |= (text == "<").fillna(False).to_numpy(bool)
        elif "when" in field:
            text = frame[column].astype("string").str.strip().str.lower()
            when = [item.lower() for item in field["when"]]
            masks[role] |= text.isin(when).fillna(False).to_numpy(bool)
        else:
            hint = f"describe() reads it as a {role.replace('_', ' ')} flag."
            masks[role] |= np.array(
                [flag is True for flag in flag_column(frame, column, hint)], bool
            )
    band = np.zeros(len(frame), bool)
    for column in (f"{value}_lower", f"{value}_upper"):
        if column in frame.columns:
            band |= pd.to_numeric(frame[column], errors="coerce").notna().to_numpy()
    return _Flags(
        at_least=masks["at_least"],
        at_most=at_most,
        non_plastic=masks["non_plastic"],
        assumed=masks["assumed"],
        band=band,
    )


_ROLE_MASKS = ("at_least", "non_plastic", "assumed")


def _source_columns() -> list[str]:
    return [c for c, f in statistics_roles().items() if f["role"] == "source"]


def _check_pool(pool: Any, read: _Input) -> list[str]:
    """Return the ``pool=`` columns, or raise if one can't be pooled."""
    if pool is None:
        return []
    columns = [pool] if isinstance(pool, str) else list(pool)
    sources = _source_columns()
    for column in columns:
        if column == read.value or column in read.by:
            raise HangtuError(
                f"describe() can't pool across {column!r} and also summarize or "
                "group by it. Remove it from pool= or from by=."
            )
        if column not in sources:
            raise HangtuError(
                f"describe() pools only across source columns, and {column!r} "
                f"isn't one. Source columns: {', '.join(sources)}. To summarize "
                "rows of different groups together, leave them out of by=."
            )
        if column not in read.frame.columns:
            raise ColumnError(
                f"describe() can't pool across {column!r}: the data has no such "
                f"column. Available columns: {', '.join(map(str, read.frame.columns))}."
            )
    return columns


def _source_values(values: pd.Series) -> pd.Series:
    """Write a source column's blanks as ``"(blank)"``."""
    text = values.astype("string").str.strip()
    return text.where(text.notna() & (text != ""), BLANK_GROUP).astype(object)


def _breakdown(values: pd.Series) -> dict[str, int]:
    """Count each source's rows, in order of appearance."""
    return {
        str(key): int(count)
        for key, count in _source_values(values).value_counts(sort=False).items()
    }


def source_mix(frame: pd.DataFrame, exclude: Sequence[str] = ()) -> list[str]:
    """Return the source columns holding more than one value in ``frame``.

    ``frame`` holds the rows one summary would read; ``exclude`` the columns
    grouped by or pooled. For the plots, which summarize the groups they draw.
    """
    return [
        column
        for column in _source_columns()
        if column in frame.columns
        and column not in exclude
        and _source_values(frame[column]).nunique() > 1
    ]


def _check_sources(
    frame: pd.DataFrame,
    keys: list[tuple[dict[str, Any], np.ndarray]],
    included: np.ndarray,
    read: _Input,
    pooled: list[str],
) -> None:
    """Raise if a group's summarized rows come from different sources (Decision 5)."""
    exclude = [*read.by, *pooled]
    for key, rows in keys:
        these = frame.loc[rows & included]
        mixed = source_mix(these, exclude)
        if not mixed:
            continue
        label = ", ".join(map(str, key.values()))
        where = f" in group {label!r}" if label else ""
        lines = []
        for column in mixed:
            listed = [
                f"{value!r} ({count} rows)"
                for value, count in _breakdown(these[column]).items()
            ]
            indent = " " * (len(column) + 4)
            lines.append(f"  {column}: " + f",\n{indent}".join(listed))
        grouped = [*read.by, mixed[0]]
        raise HangtuError(
            f"describe() can't pool rows from different sources{where}:\n"
            + "\n".join(lines)
            + f"\nSummarize each with by={grouped!r}, filter the rows, "
            f"or pool them on purpose with pool={mixed!r}."
        )


def _warn_left_out(reasons: np.ndarray, column: str) -> None:
    assumed = int((reasons == "count_assumed").sum())
    if assumed:
        warn(
            f"describe() left out {assumed} assumed values of {column!r}: assumed "
            "values aren't pooled with measured ones. They are counted in "
            "count_assumed; pass include_assumed=True to summarize them too."
        )
    ranges = int((reasons == "count_range").sum())
    if ranges:
        warn(
            f"describe() left out {ranges} rows of {column!r} that give only a "
            "range (_lower, _upper): a range is an interval, not a value. They "
            "are counted in count_range."
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


def _spellings(texts: np.ndarray) -> dict[str, int]:
    """Count the text cells by spelling, NP excepted (it is non-plastic)."""
    found = [text for text in texts if text not in ("", "NP")]
    return {text: found.count(text) for text in dict.fromkeys(found)}


def _warn_text(texts: np.ndarray, column: str) -> None:
    unknown = [text for text in texts if text and text not in TEXT_FLAGS.values()]
    if unknown:
        found = ", ".join(
            f"{text!r} ({unknown.count(text)})" for text in dict.fromkeys(unknown)
        )
        warn(
            f"describe() found text in {column!r} that isn't a number: {found}. "
            "It is counted in count_text and left out. Replace it with a number, or "
            "leave the cell blank, if it is one."
        )


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
