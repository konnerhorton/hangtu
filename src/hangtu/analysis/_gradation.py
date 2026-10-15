"""Grain size: D-values, Cu, Cc and size fractions (docs/drafts/analysis.md §3)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from functools import cache
from numbers import Integral
from typing import Any

import numpy as np
import pandas as pd

from hangtu import _config
from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu.analysis._fractions import content_column, fraction_system, passing_at
from hangtu.errors import ColumnError, HangtuError, warn

_REQUIRED = ("specimen_id", "particle_size", "percent_passing")
#: Columns that are never carried to the one-row-per-curve output (§3.4).
_POINT_COLUMNS = ("particle_size", "percent_passing")
#: D-values Cu and Cc need, found whether or not they are asked for.
_FOR_COEFFICIENTS = (10, 30, 60)


@cache
def drop_tolerance() -> float:
    """Largest drop in % passing toward finer sizes that counts as noise (§3.3).

    QC P001's default (``qc/rules.yaml``), so the analysis and the check agree.
    """
    text = _config.load("qc/rules.yaml")["rules"]["P001"]["thresholds"][
        "percent_passing_tolerance"
    ]
    value, _ = _units.parse_quantity(text, "percent")
    return value


def d_value(sizes: np.ndarray, passing: np.ndarray, percent: float) -> float:
    """Return the size at ``percent`` passing, or NaN where the curve doesn't reach it.

    ``sizes`` (mm) are sorted from the finest up, with ``passing`` in the same
    order. Log-linear between the two points around ``percent``; a point exactly
    at it gives its size; never extrapolated. Where the curve crosses
    ``percent`` more than once, the finest crossing is used (§3.3).
    """
    reached = np.flatnonzero(passing >= percent)
    if reached.size == 0:
        return np.nan
    i = reached[0]
    if passing[i] == percent:
        return float(sizes[i])
    if i == 0:
        return np.nan
    low, high = np.log10(sizes[i - 1]), np.log10(sizes[i])
    share = (percent - passing[i - 1]) / (passing[i] - passing[i - 1])
    return float(10 ** (low + share * (high - low)))


def _largest_drop(passing: np.ndarray) -> float:
    """Largest rise in % passing toward finer sizes (sizes sorted from the finest)."""
    return float(np.max(np.maximum.accumulate(passing) - passing, initial=0))


@dataclass
class _Curve:
    """One specimen's points, sorted by size as rows, in mm."""

    name: str
    sizes: np.ndarray
    passing: np.ndarray
    usable: bool = True
    values: dict[str, float] = field(default_factory=dict)


def _check_d_values(d_values: Any) -> tuple[int, ...]:
    if isinstance(d_values, str | bytes) or not isinstance(d_values, Sequence):
        d_values = (d_values,)
    for value in d_values:
        if (
            not isinstance(value, Integral)
            or isinstance(value, bool)
            or not 1 <= value <= 99
        ):
            raise HangtuError(
                "d_values must be whole-number percentages from 1 to 99, not "
                f"{value!r}. Example: d_values=(10, 30, 60)"
            )
    return tuple(dict.fromkeys(int(value) for value in d_values))


def _check_columns(df: pd.DataFrame) -> None:
    missing = [column for column in _REQUIRED if column not in df.columns]
    if missing:
        raise ColumnError(
            f"Column{'s' if len(missing) > 1 else ''} "
            f"{', '.join(map(repr, missing))} not found: a grading curve needs "
            "specimen_id, particle_size and percent_passing, one row per point. "
            f"Available columns: {', '.join(map(str, df.columns)) or 'none'}."
        )


def _sizes_mm(df: pd.DataFrame, units: Mapping[str, str] | None) -> np.ndarray:
    values = numeric_column(df, "particle_size")
    unit = _units.resolve_units(df, ["particle_size"], units, analysis=True)
    source = _units.parse_unit(unit["particle_size"], "particle_size")
    sizes = _units.convert(values, source, "particle_size", _units.ureg.millimeter)
    bad = sizes <= 0
    if bad.any():
        raise HangtuError(
            f"Column 'particle_size' has sizes of 0 or less in rows "
            f"{rows_text(df.index[bad])}. Particle sizes are greater than 0."
        )
    return sizes


def _passing(df: pd.DataFrame) -> np.ndarray:
    passing = numeric_column(df, "percent_passing")
    bad = (passing < 0) | (passing > 100)
    if bad.any():
        raise HangtuError(
            f"Column 'percent_passing' is outside 0 to 100 in rows "
            f"{rows_text(df.index[bad])}. Enter the percentage passing, e.g. 85 "
            "for 85 %."
        )
    return passing


def _keys(df: pd.DataFrame) -> list[str]:
    keys = ["loca_id", "specimen_id"] if "loca_id" in df.columns else ["specimen_id"]
    blank = df["specimen_id"].isna() | (df["specimen_id"].astype(str).str.strip() == "")
    if blank.any():
        raise HangtuError(
            f"Rows {rows_text(df.index[blank])} have a blank specimen_id, so their "
            "points can't be put on a curve. Fill in each point's specimen_id."
        )
    return keys


def _groups(df: pd.DataFrame, keys: list[str]) -> list[np.ndarray]:
    """Row positions of each curve, curves in order of first appearance."""
    codes = df.groupby(keys, sort=False, dropna=False).ngroup().to_numpy()
    order = np.argsort(codes, kind="stable")
    return np.split(order, np.flatnonzero(np.diff(codes[order])) + 1)


def _curve_name(df: pd.DataFrame, keys: list[str], rows: np.ndarray) -> str:
    return " ".join(str(df[key].iloc[rows[0]]) for key in keys)


def _build_curves(
    df: pd.DataFrame,
    keys: list[str],
    groups: list[np.ndarray],
    sizes: np.ndarray,
    passing: np.ndarray,
) -> list[_Curve]:
    """Group the points into curves, sorted by size as rows (§3.3)."""
    curves: list[_Curve] = []
    duplicates: list[Any] = []
    for rows in groups:
        name = _curve_name(df, keys, rows)
        rows = rows[~np.isnan(sizes[rows]) & ~np.isnan(passing[rows])]
        order = rows[np.argsort(sizes[rows], kind="stable")]
        curve_sizes, curve_passing = sizes[order], passing[order]
        repeated = np.flatnonzero(np.diff(curve_sizes) == 0)
        if repeated.size:
            duplicates.extend(df.index[order[np.union1d(repeated, repeated + 1)]])
        curves.append(_Curve(name, curve_sizes, curve_passing))
    if duplicates:
        raise HangtuError(
            f"Rows {rows_text(pd.Index(duplicates))} are two points at the same "
            "particle size in one curve. Keep one point per size, or check the "
            "specimen_id."
        )
    return curves


def _check_curves(curves: list[_Curve]) -> None:
    """Mark the curves the D-values can't use, and warn about them (§3.3)."""
    tolerance = drop_tolerance()
    short, falling = [], []
    for curve in curves:
        if len(curve.sizes) < 2:
            short.append(curve.name)
        elif _largest_drop(curve.passing) > tolerance:
            falling.append(curve.name)
        else:
            continue
        curve.usable = False
    if short:
        warn(
            f"{len(short)} curve{'s have' if len(short) > 1 else ' has'} fewer than "
            f"two points ({', '.join(short[:5])}), so "
            "their D-values and fractions are blank."
        )
    if falling:
        warn(
            f"Percent passing rises by more than {tolerance:g} percentage points "
            "toward finer sizes in "
            f"{', '.join(falling[:5])}"
            f"{' and more' if len(falling) > 5 else ''}. Their D-values and "
            "fractions are blank; check the curves (QC rule P001)."
        )


def _d_values(curves: list[_Curve], wanted: tuple[int, ...]) -> None:
    """Find each curve's D-values, Cu and Cc, and warn about those left blank."""
    unreached: dict[int, int] = {}
    for curve in curves:
        for percent in dict.fromkeys((*wanted, *_FOR_COEFFICIENTS)):
            value = (
                d_value(curve.sizes, curve.passing, percent) if curve.usable else np.nan
            )
            curve.values[f"d{percent}"] = value
            if curve.usable and np.isnan(value) and percent in wanted:
                unreached[percent] = unreached.get(percent, 0) + 1
        d10, d30, d60 = (curve.values[f"d{p}"] for p in _FOR_COEFFICIENTS)
        curve.values["uniformity_coefficient"] = d60 / d10
        curve.values["curvature_coefficient"] = d30**2 / (d10 * d60)
    if unreached:
        counts = ", ".join(
            f"D{percent} in {count} curve{'s' if count > 1 else ''}"
            for percent, count in unreached.items()
        )
        warn(
            f"Left blank because the curve doesn't reach that percentage: {counts}. "
            "D-values are never extrapolated beyond the finest or coarsest point."
        )


def _fractions(curves: list[_Curve], fractions: list[dict[str, Any]]) -> None:
    """Find each curve's fractions, and warn about those left blank (§3.5)."""
    unreached: dict[str, int] = {}
    for curve in curves:
        for fraction in fractions:
            column = content_column(fraction["name"])
            value = np.nan
            if curve.usable:
                upper = passing_at(curve.sizes, curve.passing, fraction["upper"])
                lower = passing_at(curve.sizes, curve.passing, fraction["lower"])
                value = upper - lower
                if np.isnan(value):
                    unreached[fraction["name"]] = unreached.get(fraction["name"], 0) + 1
            curve.values[column] = value
    if unreached:
        counts = ", ".join(
            f"{name} in {count} curve{'s' if count > 1 else ''}"
            for name, count in unreached.items()
        )
        warn(
            f"Fractions left blank because the curve doesn't reach their sizes: "
            f"{counts}. Fractions are never extrapolated (e.g. clay and silt need a "
            "hydrometer test)."
        )


def _carried(df: pd.DataFrame, keys: list[str], groups: list[np.ndarray]) -> list[str]:
    """Columns other than the points' that are constant within every curve."""
    others = [c for c in df.columns if c not in keys and c not in _POINT_COLUMNS]
    return [
        column
        for column in others
        if all(df[column].iloc[rows].nunique(dropna=False) <= 1 for rows in groups)
    ]


def gradation(
    df: pd.DataFrame,
    *,
    fractions: Any = "astm_uscs",
    d_values: Sequence[int] = (10, 30, 60),
    units: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """Summarize grading curves: D-values, Cu, Cc and fractions (analysis.md §3).

    Returns one row per curve (specimen), in order of first appearance.

    - **D-values** (``d10``, ``d30``, ``d60`` by default): the particle size at
      that percentage passing, in mm, interpolated log-linearly between the two
      points around it. Never extrapolated: a curve that doesn't reach the
      percentage gives a blank. Where a curve crosses the percentage more than
      once, the finest crossing is used.
    - **uniformity_coefficient** Cu = D60 / D10; **curvature_coefficient**
      Cc = D30² / (D10 · D60).
    - **Size fractions**: one column ``<fraction>_content`` (% of the whole
      sample) per fraction of the system, and ``fraction_system`` naming it.
      A fraction's percentage is the passing at its upper size minus the
      passing at its lower size. It is blank where the curve doesn't reach
      those sizes (clay and silt need a hydrometer test); it is never estimated.

    Points are sorted by size as rows, never one column at a time. A curve
    whose percent passing rises by more than 0.5 percentage points toward finer
    sizes (QC rule P001) gets blank values and a warning; smaller rises are
    treated as noise. Curves are told apart by ``loca_id`` and ``specimen_id``.

    The output carries every other column that is the same for all of a curve's
    points (depth, elevation, geology unit, ...). Columns that change within a
    curve (``particle_size``, ``percent_passing``, and often ``qualifier``)
    aren't carried.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per point on a curve, as ``ht.template("grain_size")`` or
        ``p.grain_size()``.
    fractions : str, dict or path
        The size-fraction system: ``"astm_uscs"`` (fines, sand, gravel, cobbles,
        boulders; USCS has no clay-silt boundary), ``"aashto"`` or
        ``"iso14688"``; or your own, as a dict or the path to a YAML file in the
        structure of ``config/fraction_systems.yaml``, with a ``name``. A
        fraction name means different sizes in different systems (gravel starts
        at 4.75 mm in USCS and 2 mm in ISO), so check ``fraction_system``.
    d_values : sequence of int
        Percentages passing to find sizes for, each a whole number from 1 to 99.
        Each gives a column ``d<x>``. ``d10``, ``d15``, ``d30``, ``d50``,
        ``d60`` and ``d85`` are registry columns; others aren't.
    units : dict, optional
        ``{column: unit}``, overriding the units declared on ``df``.
        ``particle_size`` needs units; it is converted to mm.

    Returns
    -------
    pandas.DataFrame

    Examples
    --------
    >>> curves = ht.read_csv("grain_size.csv", units={"particle_size": "mm"})
    >>> summary = ht.analysis.gradation(curves)
    >>> summary[["specimen_id", "d10", "d60", "uniformity_coefficient"]]
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    wanted = _check_d_values(d_values)
    system, system_fractions = fraction_system(fractions)
    _check_columns(df)
    keys = _keys(df)
    sizes = _sizes_mm(df, units)
    passing = _passing(df)

    blank = np.isnan(sizes) | np.isnan(passing)
    if blank.any():
        warn(
            f"Left out {int(blank.sum())} point{'s' if blank.sum() > 1 else ''} "
            f"with a blank particle_size or percent_passing (rows "
            f"{rows_text(df.index[blank])})."
        )
    groups = _groups(df, keys)
    curves = _build_curves(df, keys, groups, sizes, passing)
    _check_curves(curves)
    _d_values(curves, wanted)
    _fractions(curves, system_fractions)

    first_rows = [rows[0] for rows in groups]
    result = df.iloc[first_rows][[*keys, *_carried(df, keys, groups)]]
    result = result.reset_index(drop=True)
    columns = [*(f"d{percent}" for percent in wanted), "uniformity_coefficient"]
    columns.append("curvature_coefficient")
    columns += [content_column(fraction["name"]) for fraction in system_fractions]
    for column in columns:
        result[column] = [curve.values[column] for curve in curves]
    result["fraction_system"] = system

    declared = _units.units_of(df)
    result.attrs["units"] = {
        **{c: u for c, u in declared.items() if c in result.columns},
        **{f"d{percent}": "mm" for percent in wanted},
    }
    return result
