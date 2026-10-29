"""Put a keyed judgment on the rows (docs/work/m13b2-spt-strength-history.md).

A correlation reads its inputs as columns. A judgment such as the plasticity
index of a geology unit becomes one with ``add_judgment()``: from the call,
else a column already on the rows, else the judgments file, else an error
(SPEC §4).
"""

import math
from collections.abc import Mapping
from numbers import Real
from typing import Any

import numpy as np
import pandas as pd

from hangtu import _judgments
from hangtu._data import numeric_column, rows_text
from hangtu.analysis._judgment_values import (
    ALL,
    Values,
    from_file,
    read_judgments,
    take,
    warn_unused,
)
from hangtu.errors import ColumnError, HangtuError, warn

#: Judgments add_judgment() puts on rows: name -> (field, the key column of value=).
ADDABLE = {"plasticity_index": ("plasticity_index", "geology_unit")}
EXAMPLES = {"plasticity_index": 'value={"Alluvium": 28, "Lacustrine clay": 35}'}


def add_judgment(
    df: pd.DataFrame,
    name: str,
    *,
    value: float | Mapping[str, float] | None = None,
    judgments: Any = None,
) -> pd.DataFrame:
    """Put a judgment on each row as a column, keyed by the row's geology unit.

    Some correlations read an input that is a judgment, not a test result at
    the row: Stroud (1974) reads the plasticity index of the clay at each
    SPT. A judgment has no default (SPEC §4); this puts it on the rows, as
    ``vertical_stress()`` puts σ′v, so the correlation reads it as a column.
    In this version it takes ``"plasticity_index"``.

    **Where the value comes from**, first that applies:

    1. ``value=``: one number for every row, or ``{key: number}`` keyed by
       ``geology_unit``. A key missing for a row is an error.
    2. A ``plasticity_index`` column already on the rows, where filled: data
       you put there is the more specific choice. Its blanks are filled from
       the judgments file, with one warning counting the filled rows where the
       column and the file differ.
    3. The judgments file (``judgments=``, else the project's): its
       ``plasticity_index`` entry, keyed by the column it names in ``by:``.
       A key the file doesn't list takes its ``project`` value, with a
       warning, or is an error when there is none.
    4. Otherwise an error naming the judgment and how to set it.

    ``ht.stats.describe(p.atterberg(), value="plasticity_index",
    by="geology_unit")`` shows each unit's tested PI (count, median, spread)
    to inform the judgment. It never
    fills one in, and neither does this: the nearest test isn't used.

    Parameters
    ----------
    df : pandas.DataFrame
        The rows to put the judgment on, e.g. SPT tests, with the key column
        (``geology_unit``, or the file's ``by:``).
    name : {"plasticity_index"}
        The judgment, and the column written.
    value : float or dict, optional
        The judgment given in the call. It replaces the file's and any
        column's, with a warning.
    judgments : Judgments or path, optional
        A judgments file, as ``ht.judgments(path)``. By default the project's
        file that ``df.attrs`` carries.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with the ``plasticity_index`` column filled. No row
        is dropped or reordered. ``df.attrs["judgments"]["plasticity_index"]``
        records the source (the argument, the column, or the file's path and
        SHA-256), the key column and the values used.

    Raises
    ------
    HangtuError
        For a name it doesn't take, a missing judgment, a key without a
        value, a key column missing from ``df``, or a value that isn't a
        number of 0 or more.

    Examples
    --------
    >>> spt = ht.analysis.add_judgment(spt, "plasticity_index")
    >>> clay = ht.analysis.add_judgment(
    ...     clay, "plasticity_index", value={"Alluvium": 28}
    ... )
    """
    if name not in ADDABLE:
        raise HangtuError(
            f"add_judgment() takes {', '.join(map(repr, ADDABLE))}, not {name!r}. "
            "Unit weights and water levels are used by vertical_stress() directly, "
            "and specific gravity by phase_relations()."
        )
    field, key_column = ADDABLE[name]
    read = read_judgments(judgments, df)
    in_file = None if read is None else read.judgments.get(name)
    result = df.copy()

    if value is not None:
        given = _argument(name, field, value)
        if in_file is not None:
            warn(f"value= replaces the {name} in {read.path.name}.")
        if name in df.columns and df[name].notna().any():
            warn(
                f"value= replaces the {name} on {int(df[name].notna().sum())} rows "
                f"that already had one in the {name!r} column."
            )
        result[name] = _lookup(df, given, field, key_column, np.ones(len(df), bool))
        return _recorded(result, df, name, given.record())

    column = (
        numeric_column(df, name) if name in df.columns else np.full(len(df), np.nan)
    )
    blank = np.isnan(column)
    from_rows: dict[str, Any] = {"source": f"the {name!r} column on the rows"}
    if in_file is None:
        if name in df.columns and not blank.any():
            return _recorded(result, df, name, from_rows)
        raise HangtuError(_missing(name, read, df, int(blank.sum())))

    values = from_file(in_file, read)
    if name in df.columns:
        _warn_differ(name, column, _listed(df, values, field), ~blank, read)
    if not blank.any():
        return _recorded(result, df, name, from_rows)
    looked_up = _lookup(df, values, field, None, blank)
    result[name] = np.where(blank, looked_up, column)
    record = values.record()
    if (~blank).any():
        record["from_column"] = int((~blank).sum())
    return _recorded(result, df, name, record)


def _number(name: str, number: Any, where: str) -> float:
    if (
        isinstance(number, bool)
        or not isinstance(number, Real)
        or not math.isfinite(number)
        or number < 0
    ):
        raise HangtuError(
            f"{where} must be a number of 0 or more, not {number!r}. "
            f"Example: {EXAMPLES[name]}"
        )
    return float(number)


def _argument(name: str, field: str, value: Any) -> Values:
    """Read ``value=``: one number for all rows, or numbers keyed by geology unit."""
    if isinstance(value, Mapping):
        if not value:
            raise HangtuError(f"value= is empty. Example: {EXAMPLES[name]}")
        entries = {
            str(key): {field: _number(name, number, f"value[{key!r}]")}
            for key, number in value.items()
        }
        texts = {key: {field: f"{entry[field]:g}"} for key, entry in entries.items()}
        return Values(
            name, "argument", ADDABLE[name][1], entries, texts, argument="value"
        )
    number = _number(name, value, "value=")
    return Values(
        name, "argument", None, {ALL: {field: number}}, {ALL: {field: f"{number:g}"}}
    )


def _lookup(
    df: pd.DataFrame,
    values: Values,
    field: str,
    key_column: str | None,
    rows: np.ndarray,
) -> np.ndarray:
    """Return each of ``rows``' value by its key; NaN on the other rows."""
    by = values.by if key_column is None or values.by is None else key_column
    out = np.full(len(df), np.nan)
    if not rows.any():
        return out
    if by is None:
        entry = take(values, [ALL], "row")[ALL]
        out[rows] = entry[field]
        return out
    if by not in df.columns:
        raise ColumnError(
            f"The {values.name} values are keyed by {by!r}, and df has no {by!r} "
            "column. Add it to the rows, e.g. from p.stratigraphy() by depth."
        )
    keys = df[by].to_numpy(dtype=object)
    no_key = rows & pd.isna(keys)
    if no_key.any():
        raise ColumnError(
            f"Rows {rows_text(df.index[no_key])} have a blank {by!r}, so their "
            f"{values.name} can't be looked up. Fill {by!r} on those rows, or give "
            f"their {values.name} in a {values.name!r} column."
        )
    keys = np.array([str(key) for key in keys], dtype=object)
    noun = "geology unit" if by == "geology_unit" else by
    found = take(values, keys[rows], noun)
    warn_unused(values, keys, f"df's {by}")
    out[rows] = [found[key][field] for key in keys[rows]]
    return out


def _listed(df: pd.DataFrame, values: Values, field: str) -> np.ndarray:
    """Each row's value from the file where it gives one, else NaN; never warns."""
    if values.project_only or values.by is None:
        return np.full(len(df), values.entries[ALL][field])
    if values.by not in df.columns:
        return np.full(len(df), np.nan)
    fallback = np.nan if values.project is None else values.project[field]
    return np.array(
        [
            values.entries[str(key)][field] if str(key) in values.entries else fallback
            for key in df[values.by].to_numpy(dtype=object)
        ],
        dtype=float,
    )


def _warn_differ(
    name: str,
    column: np.ndarray,
    from_file_: np.ndarray,
    filled: np.ndarray,
    read: "_judgments.Read",
) -> None:
    differ = filled & np.isfinite(from_file_) & ~np.isclose(column, from_file_)
    if differ.any():
        warn(
            f"The {name!r} column differs from {read.path.name} on "
            f"{int(differ.sum())} of its {int(filled.sum())} filled rows; the "
            "column is used there. Clear those cells to use the file."
        )


def _missing(
    name: str, read: "_judgments.Read | None", df: pd.DataFrame, blank: int
) -> str:
    rows = f" ({blank} rows have none)" if name in df.columns else ""
    where = (
        f"The judgments file {str(read.path)!r} has no {name}, and"
        if read is not None
        else "There is no judgments file, and"
    )
    hint = (
        ""
        if read is not None or "judgments_file" in df.attrs
        else " If df came from a Project dataset, merge and concat drop df.attrs: "
        "pass judgments=p.judgments."
    )
    return (
        f"{where} the rows need a {name}{rows}, a judgment with no default "
        f"(SPEC §4). Give it in the call, {EXAMPLES[name]}, or in a judgments "
        f"file under {name}: keyed by geology unit, and pass "
        f"judgments=ht.judgments(path) or set it with p.set_judgments(path).{hint}"
    )


def _recorded(
    result: pd.DataFrame, df: pd.DataFrame, name: str, record: dict[str, Any]
) -> pd.DataFrame:
    result.attrs["judgments"] = {**df.attrs.get("judgments", {}), name: record}
    return result
