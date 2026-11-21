"""Oedometer load branches and the frame readers the oedometer analyses share.

Specs: datasets.md §6.14 (the branches), docs/analysis/compressibility.md.
"""

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu.errors import ColumnError, HangtuError

REQUIRED = ("specimen_id", "applied_vertical_stress")

LOADING = "loading"
UNLOADING = "unloading"
RELOADING = "reloading"
CONSTANT_STRESS = "constant_stress"

_STRESS = "applied_vertical_stress"
_IN_SITU = "effective_vertical_stress"


def oedometer_load_branch(df: pd.DataFrame) -> pd.DataFrame:
    r"""Mark each oedometer increment as loading, unloading or reloading.

    The preconsolidation stress and the compression index come from the
    loading branch of the curve, the swelling index and the unload-reload
    modulus from an unload-reload loop, so each increment says which branch
    it is on. Per specimen, in row order, each ``applied_vertical_stress``
    is compared with the previous increment's and with the largest before it:

    - ``loading``: the first increment, or a stress above every earlier one;
    - ``unloading``: a stress below the previous one;
    - ``reloading``: a stress above the previous one but not above the
      largest so far. Equal to the largest counts as reloading: the curve has
      only just come back to it;
    - ``constant_stress``: a stress equal to the previous one, as when the
      specimen is flooded or held at one stress for creep.

    A blank stress gives a blank branch, and the next increment is compared
    with the last stress given. A specimen with no increments (a single row
    with a blank stress) has a blank branch.

    The rule reads only the order of the stresses, so it needs no units: a
    file in kPa and its twin in psf give the same branches. **Valid for:**
    incremental-load oedometer tests whose rows are in the order the
    increments were applied. **Judgments taken:** none.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per increment, as ``ht.template("oedometer")`` or
        ``p.oedometer()``: ``specimen_id`` and ``applied_vertical_stress``
        (the stress at the end of each increment), in test order.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``load_branch`` added (or replaced). No row is
        dropped or reordered.

    Raises
    ------
    ColumnError
        For a missing column, or a stress that isn't a number.

    Examples
    --------
    ``p.oedometer()`` calls it already. On increments typed into the
    template:

    >>> increments = ht.read_csv(
    ...     "oedometer.csv", units={"applied_vertical_stress": "kPa"}
    ... )
    >>> increments = ht.analysis.oedometer_load_branch(increments)
    >>> increments[["test_stage", "applied_vertical_stress", "load_branch"]]
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    missing = [column for column in REQUIRED if column not in df.columns]
    if missing:
        raise ColumnError(
            f"df has no column {', '.join(map(repr, missing))}. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}. An oedometer increment "
            "needs its specimen and the applied vertical stress; "
            'ht.template("oedometer") has the columns.'
        )
    stress = numeric_column(df, "applied_vertical_stress")
    specimen = df["specimen_id"].to_numpy(dtype=object)
    branch = np.full(len(df), None, dtype=object)
    previous: dict[object, tuple[float, float]] = {}
    for row, (key, value) in enumerate(zip(specimen, stress, strict=True)):
        if np.isnan(value):
            continue
        key = None if pd.isna(key) else key
        if key not in previous:
            branch[row] = LOADING
            previous[key] = (value, value)
            continue
        last, largest = previous[key]
        if value > largest:
            branch[row] = LOADING
        elif value < last:
            branch[row] = UNLOADING
        elif value > last:
            branch[row] = RELOADING
        else:
            branch[row] = CONSTANT_STRESS
        previous[key] = (value, max(largest, value))
    result = df.copy()
    result["load_branch"] = pd.Series(branch, index=df.index, dtype=object)
    return result


def branches(df: pd.DataFrame, function: str) -> np.ndarray:
    """Return each row's ``load_branch``, None where blank, after checking them."""
    branch = df["load_branch"].astype(object).to_numpy()
    branch = np.array([None if pd.isna(b) else b for b in branch], dtype=object)
    known = (LOADING, UNLOADING, RELOADING, CONSTANT_STRESS, None)
    wrong = np.array([b not in known for b in branch], dtype=bool)
    if wrong.any():
        values = ", ".join(dict.fromkeys(map(repr, branch[wrong])))
        raise HangtuError(
            f"Rows {rows_text(df.index[wrong])} have load_branch {values}, which "
            f"{function} doesn't know: it reads {', '.join(map(repr, known[:-1]))}. "
            "Drop the column to have it worked out from the stresses."
        )
    return branch


def stresses(
    df: pd.DataFrame, units: Mapping[str, str] | None, display_units: str | None
) -> tuple[np.ndarray, str | None]:
    """Return ``applied_vertical_stress`` in the analysis' unit, and its name.

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


def one_value(
    df: pd.DataFrame,
    positions: np.ndarray,
    values: np.ndarray,
    column: str,
    record: dict[str, Any],
) -> float:
    """Return a specimen's one value of ``column``, NaN if blank on every row."""
    given = values[positions][~np.isnan(values[positions])]
    distinct = np.unique(given)
    if len(distinct) > 1:
        listed = ", ".join(f"{value:g}" for value in distinct)
        raise HangtuError(
            f"Specimen {record['label']} has more than one {column} on its rows "
            f"({listed}), in rows {rows_text(df.index[positions])}. A specimen has "
            f"one; correct {column} on those rows."
        )
    return float(distinct[0]) if len(distinct) else np.nan


def in_situ(
    df: pd.DataFrame,
    units: Mapping[str, str] | None,
    display_units: str | None,
    unit: str | None,
) -> np.ndarray | None:
    """Return σ′v0 in the analysis' unit (``unit``), None without the column.

    A column blank throughout needs no unit.
    """
    if _IN_SITU not in df.columns:
        return None
    if df[_IN_SITU].isna().all():
        return np.full(len(df), np.nan)
    declared = _units.resolve_units(df, [_IN_SITU], units, analysis=True)[_IN_SITU]
    parsed = _units.parse_unit(declared, _IN_SITU)
    _units.check_dimension(parsed, "stress", _IN_SITU)
    values = numeric_column(df, _IN_SITU)
    if display_units is not None:
        return _units.to_display(values, declared, "stress", display_units)[0]
    if unit is None:
        return values
    return _units.convert(values, parsed, "stress", _units.parse_unit(unit))


def specimen_label(key: dict[str, Any]) -> str:
    """Name a specimen as the lab does: its sample and specimen references."""
    parts = [key.get("sample_reference"), key.get("specimen_reference")]
    named = [str(part) for part in parts if part is not None and str(part).strip()]
    return "-".join(named) if named else str(key["specimen_id"])


def stress_text(value: float) -> str:
    """Write a stress in a reason to 3 significant figures: ``20``, ``7.94``."""
    from hangtu.plot._overlays import format_number  # plot imports analysis

    text = format_number(value)
    if "." in text and "e" not in text:
        text = text.rstrip("0").rstrip(".")
    return text
