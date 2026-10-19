"""Reading input columns, shared by the plots and the analyses."""

from numbers import Real
from typing import Any

import numpy as np
import pandas as pd

from hangtu.errors import ColumnError

_SHOWN = 5
_TRUE = {"true", "yes", "1", "1.0"}
_FALSE = {"false", "no", "0", "0.0"}
#: Text a value column may hold in place of a number, by lowercase text:
#: the key each is counted under (P01 §3, TODO #15).
TEXT_FLAGS = {"np": "NP", "refusal": "refusal"}


def rows_text(index: pd.Index) -> str:
    """Name rows by their index labels, at most five: ``"3, 7 and 2 more"``."""
    rows = [str(row) for row in index]
    more = f" and {len(rows) - _SHOWN} more" if len(rows) > _SHOWN else ""
    return ", ".join(rows[:_SHOWN]) + more


def numeric_column(df: pd.DataFrame, column: str) -> np.ndarray:
    """Return ``df[column]`` as floats, with blanks as NaN.

    Raises ``ColumnError`` naming the rows whose cells aren't numbers, such as
    ``"12 ft"`` or ``"NP"``.
    """
    values = df[column]
    numbers = pd.to_numeric(values, errors="coerce")
    bad = numbers.isna() & values.notna()
    if bad.any():
        rows = list(values.index[bad])
        shown = ", ".join(f"{row} ({values[row]!r})" for row in rows[:_SHOWN])
        more = f" and {len(rows) - _SHOWN} more" if len(rows) > _SHOWN else ""
        raise ColumnError(
            f"Column {column!r} has values that aren't numbers in rows {shown}{more}. "
            "Remove units or text from those cells, or leave them blank."
        )
    return numbers.to_numpy(dtype=float)


def text_values(df: pd.DataFrame, column: str) -> tuple[np.ndarray, np.ndarray]:
    """Return ``df[column]`` as floats, and the text of cells that aren't numbers.

    The floats are NaN for blanks and for text. The texts are ``""`` for
    numbers and blanks, ``"NP"`` or ``"refusal"`` for the recognized flags
    (trimmed, any case: ``TEXT_FLAGS``), and the trimmed text, as written,
    otherwise. A cell holding only spaces is blank.
    """
    values = df[column]
    numbers = pd.to_numeric(values, errors="coerce")
    texts = np.full(len(values), "", dtype=object)
    for i in np.flatnonzero((numbers.isna() & values.notna()).to_numpy()):
        text = str(values.iloc[i]).strip()
        texts[i] = TEXT_FLAGS.get(text.lower(), text)
    return numbers.to_numpy(dtype=float), texts


def _flag(value: Any) -> bool | None:
    """Read one true/false cell: True, False, or None for blank."""
    if (
        value is None
        or value is pd.NA
        or (isinstance(value, float) and np.isnan(value))
    ):
        return None
    if isinstance(value, bool | np.bool_):
        return bool(value)
    if isinstance(value, Real) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text == "":
            return None
        if text in _TRUE:
            return True
        if text in _FALSE:
            return False
    raise ValueError(value)


def flag_column(df: pd.DataFrame, column: str, hint: str) -> list[bool | None]:
    """Return ``df[column]`` as True, False or None (blank) for each row.

    Accepts True/False, 1/0 and the text true/false/yes/no in any case. A
    missing column is all blank. Raises ``ColumnError`` naming the rows holding
    anything else, followed by ``hint``.
    """
    if column not in df.columns:
        return [None] * len(df)
    flags, bad, found = [], [], []
    for row, value in df[column].items():
        try:
            flags.append(_flag(value))
        except ValueError:
            flags.append(None)
            bad.append(row)
            found.append(repr(value))
    if bad:
        shown = ", ".join(dict.fromkeys(found[:_SHOWN]))
        raise ColumnError(
            f"Column {column!r} must hold True or False (or 1/0, yes/no), or be "
            f"blank, but rows {rows_text(pd.Index(bad))} hold {shown}. {hint}"
        )
    return flags
