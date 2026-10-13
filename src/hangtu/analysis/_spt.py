"""SPT analysis (docs/drafts/analysis.md §1)."""

from collections.abc import Mapping
from numbers import Real
from typing import Any

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu._settings import settings
from hangtu.errors import ColumnError, HangtuError

REFUSAL_PENETRATION = 450.0  # mm: seating plus test drive (§1.3)
_TRUE = {"true", "yes", "1", "1.0"}
_FALSE = {"false", "no", "0", "0.0"}


def _check_energy_ratio(name: str, value: Any) -> float | None:
    if value is None:
        return None
    if (
        not isinstance(value, Real)
        or isinstance(value, bool)
        or not 0 < float(value) <= 100
    ):
        raise HangtuError(
            f"{name} must be the energy ratio in percent, greater than 0 and at "
            f"most 100, not {value!r}. Example: {name}=80"
        )
    return float(value)


def _check_cap(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise HangtuError(
            f"cap must be a positive whole number of blows, not {value!r}. "
            "Example: cap=100"
        )
    return value


def _flag(value: Any) -> bool | None:
    """Read one ``spt_refusal`` cell: True, False, or None for blank."""
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


def _refusal_flags(df: pd.DataFrame) -> list[bool | None]:
    """Return each row's ``spt_refusal``: True, False or None for blank."""
    if "spt_refusal" not in df.columns:
        return [None] * len(df)
    flags, bad, found = [], [], []
    for row, value in df["spt_refusal"].items():
        try:
            flags.append(_flag(value))
        except ValueError:
            flags.append(None)
            bad.append(row)
            found.append(repr(value))
    if bad:
        shown = ", ".join(dict.fromkeys(found[:5]))
        raise ColumnError(
            "Column 'spt_refusal' must hold True or False (or 1/0, yes/no), or be "
            f"blank, but rows {rows_text(pd.Index(bad))} hold {shown}. Leave the "
            "cell blank when you don't know: refusal is then found from "
            "'spt_penetration'."
        )
    return flags


def _penetration_mm(
    df: pd.DataFrame, needed: np.ndarray, units: Mapping[str, str] | None
) -> np.ndarray:
    """Return ``spt_penetration`` in mm, resolving its units only if needed."""
    values = numeric_column(df, "spt_penetration")
    if not (needed & ~np.isnan(values)).any():
        return values
    unit = _units.resolve_units(df, ["spt_penetration"], units, analysis=True)
    source = _units.parse_unit(unit["spt_penetration"], "spt_penetration")
    return _units.convert(values, source, "small_length", _units.ureg.millimeter)


def spt(
    df: pd.DataFrame,
    *,
    hammer_efficiency: float | None = None,
    cap: int | None = None,
    units: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """Add refusal, N60 and capped N to SPT results (analysis.md §1.3).

    Returns a copy of ``df`` with the columns ``spt_refusal``, ``spt_n60`` and
    ``spt_n_capped`` added, or their blanks filled in. No row is dropped or
    reordered, other columns are unchanged, and declared units are kept.

    - **Refusal:** ``spt_refusal`` where it is filled in; else True when
      ``spt_penetration`` is under 450 mm; else False.
    - **N60** = N * ER / 60, with ER from the row's ``energy_ratio``, else
      ``hammer_efficiency``, else ``ht.settings.hammer_efficiency``. With no
      energy ratio, N60 stays blank: there is no default.
    - **Capped N** = min(N, cap), and the cap for every refusal.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test, as ``ht.template("spt")``. Only ``spt_n`` is
        required.
    hammer_efficiency : float, optional
        Energy ratio in percent for rows without ``energy_ratio``. Defaults to
        ``ht.settings.hammer_efficiency``.
    cap : int, optional
        Blow count refusals are capped at. Defaults to ``ht.settings.spt_cap``.
    units : dict, optional
        ``{column: unit}``, overriding the units declared on ``df``. Only
        ``spt_penetration`` needs units, and only when refusal is found from it.

    Returns
    -------
    pandas.DataFrame

    Examples
    --------
    >>> spt = ht.read_csv("spt.csv", units={"depth": "ft", "spt_penetration": "in"})
    >>> spt = ht.analysis.spt(spt, hammer_efficiency=80)
    >>> spt[["depth", "spt_n", "spt_n60", "spt_refusal"]]
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if "spt_n" not in df.columns:
        raise ColumnError(
            "Column 'spt_n' (N as reported) not found. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}."
        )
    hammer_efficiency = _check_energy_ratio("hammer_efficiency", hammer_efficiency)
    if hammer_efficiency is None:
        hammer_efficiency = settings.hammer_efficiency
    cap = settings.spt_cap if cap is None else _check_cap(cap)

    n = numeric_column(df, "spt_n")
    negative = n < 0
    if negative.any():
        raise HangtuError(
            f"Column 'spt_n' has negative blow counts in rows "
            f"{rows_text(df.index[negative])}. N is the number of blows, 0 or more."
        )

    flags = _refusal_flags(df)
    blank = np.array([flag is None for flag in flags], dtype=bool)
    refusal = np.array([flag is True for flag in flags], dtype=bool)
    if "spt_penetration" in df.columns and blank.any():
        penetration = _penetration_mm(df, blank, units)
        refusal |= blank & (penetration < REFUSAL_PENETRATION)

    energy = np.full(len(df), np.nan)
    if "energy_ratio" in df.columns:
        energy = numeric_column(df, "energy_ratio")
        bad = ~np.isnan(energy) & ((energy <= 0) | (energy > 100))
        if bad.any():
            raise HangtuError(
                "Column 'energy_ratio' must be in percent, greater than 0 and at "
                f"most 100, but rows {rows_text(df.index[bad])} aren't. An energy "
                "ratio of 0.8 should be entered as 80."
            )
    if hammer_efficiency is not None:
        energy = np.where(np.isnan(energy), hammer_efficiency, energy)
    n60 = n * energy / 60
    if "spt_n60" in df.columns:
        given = numeric_column(df, "spt_n60")
        n60 = np.where(np.isnan(given), n60, given)

    capped = np.where(refusal, float(cap), np.minimum(n, cap))

    result = df.copy()
    result["spt_refusal"] = refusal
    result["spt_n60"] = n60
    result["spt_n_capped"] = capped
    return result
