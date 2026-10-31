"""``crosstab()``: two classifications of the same rows, counted against each other.

Spec: docs/work/m15e-crosstab.md. A value is its text as written; a blank is
the category ``"(blank)"``, as ``describe()`` labels a blank group.
"""

import math
import numbers
from collections import Counter
from collections.abc import Iterable, Mapping
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd

from hangtu.errors import ColumnError, HangtuError
from hangtu.registry import column_info
from hangtu.stats._result import CrosstabResult
from hangtu.stats._rows import BLANK_GROUP

EXAMPLE = 'ht.stats.crosstab(df, "legend_code", "uscs_symbol")'


def crosstab(
    df: pd.DataFrame,
    rows: str,
    columns: str,
    *,
    agree: str | Mapping[Any, Any] | None = None,
) -> CrosstabResult:
    """Count two classifications of the same rows against each other.

    Each row of ``df`` is counted once, in the cell of its ``rows`` value and
    its ``columns`` value, so the logged legend code can be read against the
    lab's USCS symbol, or one GEOL key against another (SPEC §8.3). It counts
    and runs no test.

    Values are compared as text, exactly as written: case and spaces count,
    so ``CL`` and ``cl`` are two classes, never merged. A whole number is
    written without a decimal, so geology codes a CSV read as numbers still
    work (``101``, not ``101.0``). A blank (NaN, None, or text of only spaces)
    is the class ``"(blank)"``, counted like any other, never dropped.

    Each side lists only the classes present: in category order for a
    categorical (``geology_unit`` keeps the geology map's order), else
    sorted as text, with ``"(blank)"`` last and the totals in ``"(total)"``.

    **Agreement is counted only when you say what agrees** (``agree=``):
    ``"same"`` when the two columns use one vocabulary (a logged USCS symbol
    against the lab's), or a mapping of which pairs agree when they don't (a
    GEOL code against a formation), since "is CL a mismatch for Alluvium?"
    has no answer hangtu could give. A row blank on either side is never a
    mismatch: it wasn't classified, which is not the same as disagreeing. It
    is counted on its own, and ``count_compared`` and the three blank counts
    add up to the rows.

    No chance-corrected statistic (Cohen's kappa) is given: it assumes the
    two classifications were made independently, and a log written after the
    lab results isn't independent of them. The share that agree, with the
    rows that don't, is what a reviewer checks.

    Parameters
    ----------
    df : pandas.DataFrame
        The rows to count, e.g. ``p.index_properties()`` with
        ``ht.analysis.uscs()`` applied.
    rows : str
        The column whose classes are the table's rows, e.g.
        ``"legend_code"``.
    columns : str
        The column whose classes are the table's columns, e.g.
        ``"uscs_symbol"``.
    agree : "same" or dict, optional
        ``"same"``: a row agrees when its two values are the same text. A
        dict maps each ``rows`` class to the ``columns`` class or list of
        classes it agrees with, e.g. ``{"CL": ["CL", "CL-ML"], "FILL": []}``
        (``[]``: agrees with nothing). Every ``rows`` class with rows to
        compare must be a key; keys and classes not in the data are allowed,
        so one mapping serves several projects. Keys and classes are compared
        as text, so ``101`` and ``"101"`` are the same. Without it, the
        result is the table alone.

    Returns
    -------
    CrosstabResult
        ``.to_frame()`` for the counts with totals, ``.to_dict()`` for a
        report, ``print(result)`` to read it.

    Raises
    ------
    ColumnError
        A column is missing, or the registry knows it as a measurement (use
        ``ht.stats.compare()`` for values).
    HangtuError
        ``df`` isn't a DataFrame, ``rows`` and ``columns`` are the same,
        ``agree=`` is neither form, or the mapping misses a class it needs.

    See Also
    --------
    describe : A property's values summarized by group.
    compare : Whether two groups' values differ.

    Examples
    --------
    >>> import pandas as pd
    >>> import hangtu as ht
    >>> soils = pd.DataFrame(
    ...     {
    ...         "legend_code": ["CL", "CL", "CL", "SP"],
    ...         "uscs_symbol": ["CL", "CH", None, "SP"],
    ...     }
    ... )
    >>> table = ht.stats.crosstab(soils, "legend_code", "uscs_symbol")
    >>> table.to_frame()  # doctest: +NORMALIZE_WHITESPACE
    uscs_symbol  CH  CL  SP  (blank)  (total)
    legend_code
    CL            1   1   0        1        3
    SP            0   0   1        0        1
    (total)       1   1   1        1        4
    >>> table = ht.stats.crosstab(soils, "legend_code", "uscs_symbol", agree="same")
    >>> table.count_agreeing, table.count_compared
    (2, 3)
    >>> table.mismatches
      legend_code uscs_symbol
    1          CL          CH
    """
    _check(df, rows, columns)
    row_text = _text(df[rows])
    column_text = _text(df[columns])
    row_values = _order(df[rows], row_text)
    column_values = _order(df[columns], column_text)
    counts = {
        row: {column: 0 for column in _labels(column_values, column_text)}
        for row in _labels(row_values, row_text)
    }
    for row, column in zip(row_text, column_text, strict=True):
        counts[row][column] += 1
    agreeing = _agreement(agree, row_text, column_text, rows, columns)
    listing = _listing_columns(df, rows, columns)
    if agreeing is None:
        return _result(
            df,
            rows,
            columns,
            row_values,
            column_values,
            counts,
            listing,
            notes=[
                'No agreement counted: pass agree="same" if the two columns use '
                "one vocabulary, or a mapping of which pairs agree."
            ],
        )
    blank_rows = np.array([value == BLANK_GROUP for value in row_text], bool)
    blank_columns = np.array([value == BLANK_GROUP for value in column_text], bool)
    compared = ~blank_rows & ~blank_columns
    disagreeing = compared & ~agreeing
    tally = {
        "count_compared": int(compared.sum()),
        "count_agreeing": int((compared & agreeing).sum()),
        "count_disagreeing": int(disagreeing.sum()),
        "count_blank_in_rows": int((blank_rows & ~blank_columns).sum()),
        "count_blank_in_columns": int((blank_columns & ~blank_rows).sum()),
        "count_blank_in_both": int((blank_rows & blank_columns).sum()),
    }
    proportion = (
        tally["count_agreeing"] / tally["count_compared"]
        if tally["count_compared"]
        else math.nan
    )
    frame = df.loc[disagreeing, list(listing)]
    return _result(
        df,
        rows,
        columns,
        row_values,
        column_values,
        counts,
        listing,
        notes=_notes(agree, tally, proportion, rows, columns),
        agree=_stored(agree),
        tally=tally,
        proportion=proportion,
        index=tuple(_label(label) for label in frame.index),
        values=tuple(
            tuple(_plain_value(value) for value in row)
            for row in frame.itertuples(index=False, name=None)
        ),
    )


def _result(
    df: pd.DataFrame,
    rows: str,
    columns: str,
    row_values: tuple[str, ...],
    column_values: tuple[str, ...],
    counts: dict[str, dict[str, int]],
    listing: tuple[str, ...],
    *,
    notes: list[str],
    agree: str | dict[str, list[str]] | None = None,
    tally: dict[str, int] | None = None,
    proportion: float | None = None,
    index: tuple[Any, ...] = (),
    values: tuple[tuple[Any, ...], ...] = (),
) -> CrosstabResult:
    tally = tally or {}
    return CrosstabResult(
        kind="property",
        function="crosstab",
        value=None,
        unit=None,
        notes=tuple(notes),
        judgments=dict(df.attrs.get("judgments", {})),
        hangtu_version=version("hangtu"),
        rows=rows,
        columns=columns,
        agree=agree,
        row_values=row_values,
        column_values=column_values,
        counts=counts,
        count_compared=tally.get("count_compared"),
        count_agreeing=tally.get("count_agreeing"),
        count_disagreeing=tally.get("count_disagreeing"),
        count_blank_in_rows=tally.get("count_blank_in_rows"),
        count_blank_in_columns=tally.get("count_blank_in_columns"),
        count_blank_in_both=tally.get("count_blank_in_both"),
        proportion_agreeing=proportion,
        mismatch_columns=listing,
        mismatch_index=index,
        mismatch_values=values,
    )


def _agreement(
    agree: Any, row_text: list[str], column_text: list[str], rows: str, columns: str
) -> np.ndarray | None:
    """Return whether each row agrees (Decision 6), or None without ``agree=``."""
    if agree is None:
        return None
    pairs = list(zip(row_text, column_text, strict=True))
    if isinstance(agree, str) and agree == "same":
        return np.array([row == column for row, column in pairs], bool)
    if not isinstance(agree, Mapping):
        raise HangtuError(
            'crosstab() takes agree="same" (a row agrees when its two values are '
            "the same text) or a mapping of which pairs agree, e.g. "
            'agree={"CL": ["CL", "CL-ML"], "FILL": []}. '
            f"Got {agree!r}."
        )
    mapping = _mapping(agree)
    needed = Counter(
        row
        for row, column in pairs
        if BLANK_GROUP not in (row, column) and row not in mapping
    )
    if needed:
        listed = ", ".join(f"{row!r} ({_rows_text(n)})" for row, n in needed.items())
        raise HangtuError(
            f"agree= doesn't say which {columns} classes agree with these "
            f"{rows} classes: {listed}. Add each to the mapping, with [] if it "
            "agrees with nothing."
        )
    return np.array([column in mapping.get(row, ()) for row, column in pairs], bool)


def _mapping(agree: Mapping[Any, Any]) -> dict[str, list[str]]:
    """Read a mapping as text on both sides, a single class as a list of one."""
    mapping = {}
    for key, classes in agree.items():
        if isinstance(classes, str) or not isinstance(classes, Iterable):
            classes = [classes]
        mapping[text(key)] = [text(name) for name in classes]
    return mapping


def _stored(agree: str | Mapping[Any, Any]) -> str | dict[str, list[str]]:
    return agree if isinstance(agree, str) else _mapping(agree)


def _notes(
    agree: Any,
    tally: dict[str, int],
    proportion: float,
    rows: str,
    columns: str,
) -> list[str]:
    how = "same text" if isinstance(agree, str) else "by the mapping"
    compared = tally["count_compared"]
    if compared:
        share = f"{proportion * 100:.3g} %"
        notes = [
            f"Agree ({how}): {tally['count_agreeing']} of {compared} rows with "
            f"both values ({share})."
        ]
    else:
        notes = [f"Agree ({how}): no row has both values."]
    blanks = [
        ("count_blank_in_columns", f"a {rows} but no {columns}"),
        ("count_blank_in_rows", f"a {columns} but no {rows}"),
        ("count_blank_in_both", f"neither a {rows} nor a {columns}"),
    ]
    for name, what in blanks:
        if tally[name]:
            verb = "row has" if tally[name] == 1 else "rows have"
            notes.append(f"{tally[name]} {verb} {what}.")
    return notes


def _rows_text(n: int) -> str:
    return f"{n} row" if n == 1 else f"{n} rows"


def _label(label: Any) -> Any:
    """Keep an index label JSON-safe: a str or int as it is, else its text."""
    if isinstance(label, str):
        return label
    if isinstance(label, numbers.Integral) and not isinstance(label, bool):
        return int(label)
    return str(label)


def _plain_value(value: Any) -> Any:
    if value is None or (pd.api.types.is_scalar(value) and pd.isna(value)):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def _check(df: Any, rows: Any, columns: Any) -> None:
    if (
        not isinstance(df, pd.DataFrame)
        or not isinstance(rows, str)
        or not isinstance(columns, str)
    ):
        raise HangtuError(
            "crosstab() takes a DataFrame and the names of two of its columns, "
            f"e.g. {EXAMPLE}."
        )
    missing = [column for column in (rows, columns) if column not in df.columns]
    if missing:
        raise ColumnError(
            f"crosstab() needs the column {', '.join(map(repr, missing))}, which "
            f"the data doesn't have. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}."
        )
    if rows == columns:
        raise HangtuError(
            f"crosstab() can't count {rows!r} against itself. Choose two "
            "different columns."
        )
    for column in (rows, columns):
        if (column_info(column) or {}).get("quantity"):
            raise ColumnError(
                f"Column {column!r} is a measurement, and crosstab() counts "
                "classes. To test whether two groups' values differ, use "
                "ht.stats.compare(); to count values in ranges, bin them first, "
                f"e.g. df[{column!r}] = pd.cut(df[{column!r}], bins)."
            )


def text(value: Any) -> str:
    """Return a value as the text it is compared by, or ``"(blank)"``."""
    if isinstance(value, str):
        return value if value.strip() else BLANK_GROUP
    if value is None or (pd.api.types.is_scalar(value) and pd.isna(value)):
        return BLANK_GROUP
    if isinstance(value, bool | np.bool_):
        return str(bool(value))
    if isinstance(value, numbers.Real) and float(value).is_integer():
        return str(int(value))
    return str(value)


def _text(values: pd.Series) -> list[str]:
    return [text(value) for value in values.astype(object)]


def _order(values: pd.Series, texts: list[str]) -> tuple[str, ...]:
    """Return the classes present, without blank, in Decision 4's order."""
    present = set(texts) - {BLANK_GROUP}
    if isinstance(values.dtype, pd.CategoricalDtype):
        ordered = [text(category) for category in values.cat.categories]
        return tuple(dict.fromkeys(name for name in ordered if name in present))
    return tuple(sorted(present))


def _labels(values: tuple[str, ...], texts: list[str]) -> list[str]:
    return [*values, *([BLANK_GROUP] if BLANK_GROUP in texts else [])]


def _listing_columns(df: pd.DataFrame, rows: str, columns: str) -> tuple[str, ...]:
    """Return the mismatch listing's columns (Decision 7)."""
    identifiers = {"loca_id", "depth", "sample_reference", "specimen_id"}
    found = [
        str(column)
        for column in df.columns
        if column in identifiers or str(column).endswith("_specimen_id")
    ]
    listed = [*found, *(name for name in (rows, columns) if name not in found)]
    if "source_line" in df.columns and "source_line" not in listed:
        listed.append("source_line")
    return tuple(listed)
