"""SPT analysis (docs/drafts/analysis.md §1)."""

from collections.abc import Mapping
from numbers import Real
from typing import Any

import numpy as np
import pandas as pd

from hangtu import _config
from hangtu import units as _units
from hangtu._data import flag_column, numeric_column, rows_text
from hangtu._settings import settings
from hangtu.errors import ColumnError, HangtuError, warn

REFUSAL_PENETRATION = 450.0  # mm: seating plus test drive (§1.3)
#: Slack on the refusal comparison, so 450 mm written in another unit (17.71653543
#: in) isn't a refusal because of rounding in the conversion.
SLACK = 1e-6  # mm
REFUSAL_CLASS = "Refusal"
N_COLUMNS = ("spt_n", "spt_n60", "spt_n_capped")


def n60(n: Any, energy_ratio: Any) -> Any:
    """Return N60 = N * ER / 60, with the energy ratio ER in percent (§1.3).

    Shared with QC rule S005, so the analysis and the check can't disagree.
    """
    return n * energy_ratio / 60


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
            f"most 100, not {value!r}. Example: {name}=80, or by hole "
            f'{name}={{"BH01": 80, "BH02": 72}}'
        )
    return float(value)


def _check_hammer_efficiency(
    value: Any, df: pd.DataFrame
) -> float | dict[str, float] | None:
    """Check ``hammer_efficiency``: a number, ``{loca_id: ER}`` or None."""
    if not isinstance(value, Mapping):
        return _check_energy_ratio("hammer_efficiency", value)
    if "loca_id" not in df.columns:
        raise ColumnError(
            "hammer_efficiency is given by hole, but there is no 'loca_id' "
            "column to match the holes to. Add 'loca_id', or give one number "
            "for every test: hammer_efficiency=80"
        )
    checked = {}
    for hole, ratio in value.items():
        checked[str(hole)] = _check_energy_ratio(f"hammer_efficiency[{hole!r}]", ratio)
    unknown = [hole for hole in checked if hole not in set(df["loca_id"].astype(str))]
    if unknown:
        warn(
            f"hammer_efficiency names holes that aren't in the data: "
            f"{', '.join(map(repr, unknown))}. Check the spelling of the hole IDs "
            "('loca_id')."
        )
    return checked


def _energy_ratios(
    df: pd.DataFrame, hammer_efficiency: float | Mapping[str, float] | None
) -> tuple[np.ndarray, np.ndarray]:
    """Return each row's energy ratio and a mask of the rows it was filled for.

    The ratio is the row's ``energy_ratio``, else ``hammer_efficiency`` (one
    number, or the value for the row's hole), else
    ``ht.settings.hammer_efficiency``, else blank. The mask is True where the
    argument or the setting filled a blank. Shared with ``p.spt()``, whose
    ``energy_source`` follows the same order.
    """
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
    blank = np.isnan(energy)
    if isinstance(hammer_efficiency, Mapping):
        by_hole = df["loca_id"].astype(str).map(hammer_efficiency)
        energy = np.where(blank, by_hole.to_numpy(dtype=float), energy)
    elif hammer_efficiency is not None:
        energy = np.where(blank, hammer_efficiency, energy)
    if settings.hammer_efficiency is not None:
        energy = np.where(np.isnan(energy), settings.hammer_efficiency, energy)
    return energy, blank & ~np.isnan(energy)


def _warn_filled(df: pd.DataFrame, energy: np.ndarray, used: np.ndarray) -> None:
    """Warn that the argument or the setting gave N60's energy ratio."""
    if not used.any():
        return
    if "loca_id" in df.columns:
        rows = pd.DataFrame({"hole": df["loca_id"].astype(str), "ratio": energy})[used]
        parts = []
        for ratio, group in rows.groupby("ratio", sort=False):
            counts = group["hole"].value_counts(sort=False)
            holes = ", ".join(
                f"{hole} ({count} test{'s' if count != 1 else ''})"
                for hole, count in counts.items()
            )
            parts.append(f"{ratio:g} % used for {holes}")
        used_for = "; ".join(parts)
    else:
        count = int(used.sum())
        ratios = ", ".join(f"{ratio:g} %" for ratio in pd.unique(energy[used]))
        used_for = f"{ratios} used for {count} test{'s' if count != 1 else ''}"
    warn(
        f"Energy ratio {used_for}: no 'energy_ratio' in the data for these "
        "tests, so hammer_efficiency or ht.settings.hammer_efficiency gave it. "
        "Measured values ('energy_ratio', AGS ISPT_ERAT) are used first."
    )


def _check_cap(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise HangtuError(
            f"cap must be a positive whole number of blows, not {value!r}. "
            "Example: cap=100"
        )
    return value


def _refusal_flags(df: pd.DataFrame) -> list[bool | None]:
    """Return each row's ``spt_refusal``: True, False or None for blank."""
    return flag_column(
        df,
        "spt_refusal",
        "Leave the cell blank when you don't know: refusal is then found from "
        "'spt_penetration'.",
    )


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
    hammer_efficiency: float | Mapping[str, float] | None = None,
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
      ``hammer_efficiency`` (one number, or the value for the row's hole),
      else ``ht.settings.hammer_efficiency``. With no energy ratio, N60 stays
      blank: there is no default. When the argument or the setting gives a
      test's ER, a warning names the holes, the ratio and the number of tests.
    - **Capped N** = min(N, cap), and the cap for every refusal.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test, as ``ht.template("spt")``. Only ``spt_n`` is
        required.
    hammer_efficiency : float or dict, optional
        Energy ratio in percent for rows without ``energy_ratio``: one number
        for every hole, or ``{loca_id: ER}`` by hole (``df`` then needs
        ``loca_id``). Holes not in the dict, and every row when it's None, use
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
    >>> spt = ht.analysis.spt(spt, hammer_efficiency={"BH01": 80, "BH02": 72})
    >>> spt[["depth", "spt_n", "spt_n60", "spt_refusal"]]
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if "spt_n" not in df.columns:
        raise ColumnError(
            "Column 'spt_n' (N as reported) not found. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}."
        )
    hammer_efficiency = _check_hammer_efficiency(hammer_efficiency, df)
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
        refusal |= blank & (penetration < REFUSAL_PENETRATION - SLACK)

    energy, filled = _energy_ratios(df, hammer_efficiency)
    computed = n60(n, energy)
    used = filled & ~np.isnan(n)
    if "spt_n60" in df.columns:
        given = numeric_column(df, "spt_n60")
        computed = np.where(np.isnan(given), computed, given)
        used &= np.isnan(given)
    _warn_filled(df, energy, used)

    capped = np.where(refusal, float(cap), np.minimum(n, cap))

    result = df.copy()
    result["spt_refusal"] = refusal
    result["spt_n60"] = computed
    result["spt_n_capped"] = capped
    return result


def class_table(table: str) -> tuple[list[str], np.ndarray]:
    """Return a class table's names and lower bounds, from the lowest N up."""
    tables = _config.load("config/spt_classes.yaml")
    if table not in tables:
        raise HangtuError(
            f"There is no SPT class table named {table!r}. Tables: "
            f'{", ".join(map(repr, tables))}. Example: table="cohesive"'
        )
    classes = tables[table]["classes"]
    names = [entry["name"] for entry in classes]
    lowers = np.array([entry["lower"] for entry in classes], dtype=float)
    return names, lowers


def spt_class(
    df: pd.DataFrame, *, n: str = "spt_n", table: str = "cohesionless"
) -> pd.Series:
    """Classify SPT tests by relative density or consistency (analysis.md §1.4).

    Each class runs from its lower bound up to, not including, the next one, so
    N = 0 is "Very loose" and N = 10 is "Medium dense". A refusal is
    "Refusal", whatever its N, and a blank value gives a blank class.

    Which table applies is the engineer's call: pick ``table`` and pass the rows
    it applies to. The data first goes through ``ht.analysis.spt()``, so the
    refusal rule is the same.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test, as for ``ht.analysis.spt()``.
    n : {"spt_n", "spt_n60", "spt_n_capped"}
        The value classified. For N60, set ``ht.settings.hammer_efficiency``,
        fill in ``energy_ratio``, or run ``ht.analysis.spt()`` first with
        ``hammer_efficiency=``.
    table : {"cohesionless", "cohesive"}
        Relative density (very loose to very dense) or consistency (very soft
        to hard). The tables are in ``config/spt_classes.yaml``.

    Returns
    -------
    pandas.Series
        An ordered categorical named ``spt_class``, with the table's classes
        from the lowest N up and "Refusal" last, on the index of ``df``.

    Examples
    --------
    >>> sand = spt[spt["geology_unit"] == "Alluvial sand"]
    >>> ht.analysis.spt_class(sand, table="cohesionless").value_counts(sort=False)
    """
    if n not in N_COLUMNS:
        raise HangtuError(
            f"n must be one of {', '.join(map(repr, N_COLUMNS))}, not {n!r}. "
            'Example: n="spt_n60"'
        )
    names, lowers = class_table(table)
    result = spt(df)
    values = numeric_column(result, n)
    negative = values < 0
    if negative.any():
        raise HangtuError(
            f"Column {n!r} has negative values in rows "
            f"{rows_text(result.index[negative])}. Blow counts are 0 or more."
        )
    refusal = result["spt_refusal"].to_numpy(dtype=bool)
    blank = np.isnan(values) & ~refusal
    position = np.searchsorted(lowers, np.nan_to_num(values), side="right") - 1
    categories = [*names, REFUSAL_CLASS]
    codes = np.where(refusal, len(names), np.where(blank, -1, position))
    return pd.Series(
        pd.Categorical.from_codes(codes, categories=categories, ordered=True),
        index=df.index,
        name="spt_class",
    )
