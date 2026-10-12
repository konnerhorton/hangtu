"""Reading plot input columns."""

import numpy as np
import pandas as pd

from ags_kit.errors import ColumnError

_SHOWN = 5


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
