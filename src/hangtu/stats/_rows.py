"""Reading the rows a statistics function summarizes or fits.

Spec: docs/work/m15a-describe.md, Decisions 1, 3, 5 and 6. ``describe()`` and
``fit()`` read their input here, so both choose the same rows. Each message
names the calling function (``function="describe()"``).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import TEXT_FLAGS, flag_column, text_values
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.registry import column_info, statistics_roles

#: The counts of rows not summarized, or summarized as bounds, in their order
#: of checks (Decision 6). ``count_not_positive`` is added with ``positive_only``.
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
class Input:
    frame: pd.DataFrame
    #: The value's name in the result, None for a list or array.
    value: str | None
    #: The column read in ``frame``.
    column: str
    by: list[str]
    unit: str | None
    quantity: str | None
    unit_given: bool


def read_input(
    data: Any,
    value: str | None,
    by: Any,
    pool: Any,
    units: str | Mapping[str, str] | None,
    function: str,
) -> Input:
    """Read the three input forms: a DataFrame and ``value=``, a Series, values."""
    name = function.removesuffix("()")
    by_columns = [] if by is None else [by] if isinstance(by, str) else list(by)
    if isinstance(data, pd.Series):
        if value is not None:
            raise HangtuError(
                f"{function} reads a Series as its own value, so value= is for a "
                "DataFrame. Pass the frame and value=, or the Series alone."
            )
        if data.name is not None:
            value = str(data.name)
            frame = data.to_frame(value)
            frame.attrs = dict(data.attrs)
            return _frame_input(frame, value, by_columns, units, function)
        data = data.to_numpy()
    if isinstance(data, pd.DataFrame):
        if not isinstance(value, str):
            raise HangtuError(
                f"{function} needs value=, the column to summarize, with a "
                f"DataFrame. Example: ht.stats.{name}(df, "
                'value="plasticity_index")'
            )
        return _frame_input(data, value, by_columns, units, function)
    if value is not None or by_columns or pool is not None:
        raise HangtuError(
            f"{function} takes value=, by= and pool= only with a DataFrame, which "
            "has columns to name. Pass a DataFrame, or the values alone."
        )
    if isinstance(units, Mapping):
        raise HangtuError(
            f"{function} takes the unit of a list or array as text, e.g. "
            'units="kPa", since it has no columns to name.'
        )
    try:
        numbers = np.asarray(data, dtype=float)
    except (TypeError, ValueError):
        numbers = None
    if numbers is None or numbers.ndim != 1:
        raise HangtuError(
            f"{function} takes a DataFrame, a Series, or a list or 1-D array of "
            f"numbers, not {type(data).__name__}. "
            f"Example: ht.stats.{name}([10, 12, 15])"
        )
    if units is not None:
        _units.parse_unit(units)
    return Input(
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
    function: str,
) -> Input:
    missing = [column for column in (value, *by) if column not in frame.columns]
    if missing:
        raise ColumnError(
            f"{function} needs the column {', '.join(map(repr, missing))}, which "
            f"the data doesn't have. Available columns: "
            f"{', '.join(map(str, frame.columns)) or 'none'}."
        )
    if value in by:
        raise HangtuError(
            f"{function} can't group {value!r} by itself. Choose another by= column."
        )
    info = column_info(value) or {}
    if info.get("type") == "bool" or pd.api.types.is_bool_dtype(frame[value]):
        raise ColumnError(
            f"Column {value!r} holds True or False, which {function} doesn't "
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
            f'{function} units must be text such as "kPa", or a dict, not {units!r}.'
        )
    quantity = info.get("quantity")
    unit = _units.resolve_units(frame, [value], explicit, analysis=True)[value]
    return Input(
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


def convert(
    numbers: np.ndarray, read: Input, display_units: str | None, function: str
) -> tuple[np.ndarray, str | None]:
    """Convert to ``display_units``, and name the statistics' unit."""
    kind = _units.quantity_kind(read.quantity) if read.quantity else None
    if display_units is None:
        if kind is not None and kind["canonical"] is None:
            return numbers, kind["SI"]["text"]
        return numbers, read.unit
    if display_units not in ("US", "SI"):
        raise HangtuError(
            f'{function} display_units must be "US", "SI" or None, not '
            f"{display_units!r}."
        )
    if read.quantity is None and read.unit is not None:
        raise HangtuError(
            f"{function} can't convert {read.column!r} to {display_units} units: "
            "it isn't a registered column, so its kind of quantity is unknown. "
            "Convert it yourself, or leave display_units=None."
        )
    return _units.to_display(numbers, read.unit, read.quantity, display_units)


def scale(value: str | None) -> tuple[bool, bool]:
    """Return whether the column is on an interval scale, and whether that is known."""
    info = column_info(value) if value else None
    if info is None or "scale" not in info:
        return False, False
    return info["scale"] == "interval", True


def _assign(reasons: np.ndarray, mask: np.ndarray, name: str) -> None:
    """Count rows under ``name`` unless an earlier check already counted them."""
    reasons[mask & (reasons == "")] = name


def choose_rows(
    numbers: np.ndarray,
    texts: np.ndarray,
    flags: "Flags",
    *,
    include_assumed: bool,
    positive_only: bool,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Return each row's reason for being left out ("" if kept), and the marks.

    Decision 6: each row is counted once, under the first reason that applies.
    The marks are the kept rows counted as bounds, and as assumed when
    ``include_assumed``.
    """
    reasons = np.full(len(numbers), "", dtype=object)
    _assign(reasons, flags.band & np.isnan(numbers) & (texts == ""), "count_range")
    _assign(reasons, flags.non_plastic | (texts == "NP"), "count_non_plastic")
    if not include_assumed:
        _assign(reasons, flags.assumed, "count_assumed")
    _assign(reasons, texts != "", "count_text")
    _assign(reasons, np.isnan(numbers), "count_blank")
    if positive_only:
        _assign(reasons, numbers <= 0, "count_not_positive")
    included = reasons == ""
    marks = {
        "count_at_least": flags.at_least & included,
        "count_at_most": flags.at_most & included,
    }
    if include_assumed:
        marks["count_assumed"] = flags.assumed & included
    return reasons, marks


def group_keys(
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
class Flags:
    """Each row's flags on the value column, from the registry's roles."""

    at_least: np.ndarray
    at_most: np.ndarray
    non_plastic: np.ndarray
    assumed: np.ndarray
    band: np.ndarray

    @classmethod
    def none(cls, frame: pd.DataFrame) -> "Flags":
        empty = np.zeros(len(frame), bool)
        return cls(empty, empty, empty, empty, empty)


def read_flags(frame: pd.DataFrame, value: str, function: str = "describe()") -> Flags:
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
            hint = f"{function} reads it as a {role.replace('_', ' ')} flag."
            masks[role] |= np.array(
                [flag is True for flag in flag_column(frame, column, hint)], bool
            )
    band = np.zeros(len(frame), bool)
    for column in (f"{value}_lower", f"{value}_upper"):
        if column in frame.columns:
            band |= pd.to_numeric(frame[column], errors="coerce").notna().to_numpy()
    return Flags(
        at_least=masks["at_least"],
        at_most=at_most,
        non_plastic=masks["non_plastic"],
        assumed=masks["assumed"],
        band=band,
    )


_ROLE_MASKS = ("at_least", "non_plastic", "assumed")


def _source_columns() -> list[str]:
    return [c for c, f in statistics_roles().items() if f["role"] == "source"]


def check_pool(pool: Any, read: Input, function: str) -> list[str]:
    """Return the ``pool=`` columns, or raise if one can't be pooled."""
    if pool is None:
        return []
    columns = [pool] if isinstance(pool, str) else list(pool)
    sources = _source_columns()
    for column in columns:
        if column == read.value or column in read.by:
            raise HangtuError(
                f"{function} can't pool across {column!r} and also summarize or "
                "group by it. Remove it from pool= or from by=."
            )
        if column not in sources:
            raise HangtuError(
                f"{function} pools only across source columns, and {column!r} "
                f"isn't one. Source columns: {', '.join(sources)}. To summarize "
                "rows of different groups together, leave them out of by=."
            )
        if column not in read.frame.columns:
            raise ColumnError(
                f"{function} can't pool across {column!r}: the data has no such "
                f"column. Available columns: {', '.join(map(str, read.frame.columns))}."
            )
    return columns


def _source_values(values: pd.Series) -> pd.Series:
    """Write a source column's blanks as ``"(blank)"``."""
    text = values.astype("string").str.strip()
    return text.where(text.notna() & (text != ""), BLANK_GROUP).astype(object)


def breakdown(values: pd.Series) -> dict[str, int]:
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


def check_sources(
    frame: pd.DataFrame,
    keys: list[tuple[dict[str, Any], np.ndarray]],
    included: np.ndarray,
    read: Input,
    pooled: list[str],
    function: str,
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
                for value, count in breakdown(these[column]).items()
            ]
            indent = " " * (len(column) + 4)
            lines.append(f"  {column}: " + f",\n{indent}".join(listed))
        grouped = [*read.by, mixed[0]]
        raise HangtuError(
            f"{function} can't pool rows from different sources{where}:\n"
            + "\n".join(lines)
            + f"\nSummarize each with by={grouped!r}, filter the rows, "
            f"or pool them on purpose with pool={mixed!r}."
        )


def warn_left_out(reasons: np.ndarray, column: str, function: str) -> None:
    """Warn about assumed values and bands left out."""
    assumed = int((reasons == "count_assumed").sum())
    if assumed:
        warn(
            f"{function} left out {assumed} assumed values of {column!r}: assumed "
            "values aren't pooled with measured ones. They are counted in "
            "count_assumed; pass include_assumed=True to summarize them too."
        )
    ranges = int((reasons == "count_range").sum())
    if ranges:
        warn(
            f"{function} left out {ranges} rows of {column!r} that give only a "
            "range (_lower, _upper): a range is an interval, not a value. They "
            "are counted in count_range."
        )


def spellings(texts: np.ndarray) -> dict[str, int]:
    """Count the text cells by spelling, NP excepted (it is non-plastic)."""
    found = [text for text in texts if text not in ("", "NP")]
    return {text: found.count(text) for text in dict.fromkeys(found)}


def warn_text(texts: np.ndarray, column: str, function: str) -> None:
    """Warn about text cells that aren't a recognized flag."""
    unknown = [text for text in texts if text and text not in TEXT_FLAGS.values()]
    if unknown:
        found = ", ".join(
            f"{text!r} ({unknown.count(text)})" for text in dict.fromkeys(unknown)
        )
        warn(
            f"{function} found text in {column!r} that isn't a number: {found}. "
            "It is counted in count_text and left out. Replace it with a number, or "
            "leave the cell blank, if it is one."
        )
