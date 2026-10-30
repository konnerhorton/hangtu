"""``crosstab()``: two classifications of the same rows, counted against each other.

Spec: docs/work/m15e-crosstab.md. A value is its text as written; a blank is
the category ``"(blank)"``, as ``describe()`` labels a blank group.
"""

import numbers
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd

from hangtu.errors import ColumnError, HangtuError
from hangtu.registry import column_info
from hangtu.stats._result import CrosstabResult
from hangtu.stats._rows import BLANK_GROUP

EXAMPLE = 'ht.stats.crosstab(df, "legend_code", "uscs_symbol")'


def crosstab(df: pd.DataFrame, rows: str, columns: str) -> CrosstabResult:
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
        ``df`` isn't a DataFrame, or ``rows`` and ``columns`` are the same.

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
    notes = [
        'No agreement counted: pass agree="same" if the two columns use one '
        "vocabulary, or a mapping of which pairs agree."
    ]
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
        agree=None,
        row_values=row_values,
        column_values=column_values,
        counts=counts,
        count_compared=None,
        count_agreeing=None,
        count_disagreeing=None,
        count_blank_in_rows=None,
        count_blank_in_columns=None,
        count_blank_in_both=None,
        proportion_agreeing=None,
        mismatch_columns=_listing_columns(df, rows, columns),
        mismatch_index=(),
        mismatch_values=(),
    )


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
