"""Overlays drawn on profiles (P01 §8).

Each overlay takes the axes and the ``Vertical`` reference of the main data,
so P02, P06 and P09 can draw them without going through ``profile()``. Marks
are lines, patches and text, never scatter collections: those hold the data
points (plan decision 8).
"""

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.transforms import blended_transform_factory, offset_copy

from ags_kit.errors import AgsKitError, ColumnError, warn
from ags_kit.plot import _layers
from ags_kit.plot._data import numeric_column, rows_text
from ags_kit.plot._palette import resolve_palette
from ags_kit.plot._vertical import VS, Vertical, convert_pair
from ags_kit.units import parse_quantity, units_of

TEXT_SIZE = 7  # points
STRATA_ALPHA = 0.12
WATER_COLOR = "#2166ac"
WATER_WIDTH = 0.8  # points
WATER_SYMBOL_SIZE = 6  # points
WATER_LABEL = "GWL"
MAX_HOLE_LABELS = 6
NEUTRAL = "0.3"

_PAIRS = {vs: (f"{vs}_top", f"{vs}_base") for vs in VS}


def _require(table: pd.DataFrame, overlay: str, columns: Sequence[str]) -> None:
    missing = [column for column in columns if column not in table.columns]
    if missing:
        template = (
            f' Start from ak.template("{overlay}").' if overlay != "water_level" else ""
        )
        raise ColumnError(
            f"The {overlay} table has no {', '.join(map(repr, missing))} column. "
            f"Its columns: {', '.join(map(str, table.columns)) or 'none'}.{template}"
        )


def _given(table: pd.DataFrame, columns: Sequence[str]) -> bool:
    """Return True when ``table`` has all ``columns`` and they aren't all blank."""
    return set(columns) <= set(table.columns) and bool(
        table[list(columns)].notna().to_numpy().any()
    )


def overlay_units(
    table: pd.DataFrame,
    overlay: str,
    assumed: Mapping[str, str | None],
) -> dict[str, str | None]:
    """Return the units of an overlay's columns (plan decision 2).

    Units declared on the overlay table win. Others are taken to be the main
    data's units, ``assumed``, with one warning that names them.
    """
    declared = units_of(table)
    missing = {
        column: unit
        for column, unit in assumed.items()
        if column not in declared and unit is not None
    }
    if missing:
        example = ", ".join(f'"{column}": "{unit}"' for column, unit in missing.items())
        warn(
            f"The {overlay} table has no units for {', '.join(missing)}, so they are "
            f"taken to be in the plot data's units. Declare them to silence this: "
            f"{overlay} = ak.set_units({overlay}, {{{example}}})."
        )
    return {column: declared.get(column, unit) for column, unit in assumed.items()}


def vertical_pair(
    table: pd.DataFrame,
    overlay: str,
    vertical: Vertical,
    *,
    required: bool,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Read an overlay's depth or elevation pair, drawn in ``vertical.vs``.

    Exactly one of ``depth_top, depth_base`` and ``elevation_top,
    elevation_base`` may be given; a pair whose columns are all blank counts
    as absent. Rows with top and base the wrong way round, or a blank bound,
    are NaN and named in a warning. Returns None when no pair is given and
    none is ``required``.
    """
    given = [vs for vs, pair in _PAIRS.items() if _given(table, pair)]
    if len(given) != 1:
        if not given and not required:
            return None
        problem = "both" if given else "neither"
        raise ColumnError(
            f"The {overlay} table has {problem} of the depth pair (depth_top, "
            "depth_base) and the elevation pair (elevation_top, elevation_base). "
            f"Give one pair and leave the other out or blank. "
            f'ak.template("{overlay}") lists the columns.'
        )
    from_vs = given[0]
    pair = _PAIRS[from_vs]
    units = overlay_units(table, overlay, dict.fromkeys(pair, vertical.unit))
    top, base = (
        vertical.to_display(numeric_column(table, column), units[column] or "")
        for column in pair
    )
    top, base = convert_pair(top, base, from_vs, vertical, overlay)
    blank = np.isnan(top) | np.isnan(base)
    swapped = (top < base) if vertical.vs == "elevation" else (top > base)
    if blank.any():
        warn(
            f"Rows {rows_text(table.index[blank])} of the {overlay} table have a "
            "blank top or base, so they aren't drawn."
        )
    if swapped.any():
        order = "above" if from_vs == "elevation" else "shallower than"
        warn(
            f"Rows {rows_text(table.index[swapped])} of the {overlay} table have "
            f"{pair[0]} and {pair[1]} the wrong way round, so they aren't drawn. "
            f"The top must be {order} the base."
        )
    keep = ~blank & ~swapped
    return np.where(keep, top, np.nan), np.where(keep, base, np.nan)


def draw_strata(
    ax: Axes,
    strata: pd.DataFrame,
    vertical: Vertical,
    palette: Mapping[Any, Any] | None = None,
) -> None:
    """Draw full-width strata bands, labeled at the top right inside the axes."""
    _require(strata, "strata", ["geology_unit"])
    top, base = vertical_pair(strata, "strata", vertical, required=True)
    units = strata["geology_unit"].to_numpy(dtype=object)
    colors = resolve_palette(units, palette)
    edge = blended_transform_factory(ax.transAxes, ax.transData)
    below_top = offset_copy(edge, ax.figure, y=-2, units="points")
    for unit, t, b in zip(units, top, base, strict=True):
        if np.isnan(t):
            continue
        blank = pd.isna(unit)
        ax.axhspan(
            t,
            b,
            facecolor=NEUTRAL if blank else colors[unit],
            alpha=STRATA_ALPHA,
            linewidth=0,
            zorder=_layers.STRATA,
        )
        if not blank:
            # At the top of the band, so a water level mid-band stays clear.
            ax.text(
                0.98,
                t,
                str(unit),
                transform=below_top,
                ha="right",
                va="top",
                fontsize=TEXT_SIZE,
                color="0.25",
                clip_on=True,
                zorder=_layers.ANNOTATIONS,
            )


def _water_levels(
    water_level: float | str | Sequence[tuple[float | str, str]], vertical: Vertical
) -> list[tuple[float, str]]:
    """Return ``(position, label)`` pairs in display units."""
    entries = (
        [(water_level, WATER_LABEL)]
        if isinstance(water_level, int | float | str)
        else list(water_level)
    )
    levels = []
    for entry in entries:
        if not (isinstance(entry, tuple | list) and len(entry) == 2):
            raise AgsKitError(
                "water_level must be a number, a list of (value, label) pairs, or a "
                f"table of water levels by hole, not {water_level!r}. "
                'Example: water_level=[(112.5, "GWL (2026-03)")]'
            )
        value, label = entry
        if isinstance(value, str):
            number, unit = parse_quantity(value, "length")
            position = float(vertical.to_display([number], unit)[0])
        elif isinstance(value, int | float) and not isinstance(value, bool):
            position = float(value)
            if vertical.unit is not None and not vertical.unknown:
                position = float(vertical.to_display([value], vertical.unit)[0])
        else:
            raise AgsKitError(
                f"The water level {value!r} must be a number in the plot data's "
                'units, or a number with a unit such as "112.5 ft".'
            )
        levels.append((position, str(label)))
    return levels


def _water_symbol(ax: Axes, x: float, y: float) -> None:
    """Draw ▽ with its tip on the water level at axes fraction ``x``."""
    edge = blended_transform_factory(ax.transAxes, ax.transData)
    ax.plot(
        [x],
        [y],
        marker="v",
        markersize=WATER_SYMBOL_SIZE,
        markerfacecolor="white",
        markeredgecolor=WATER_COLOR,
        markeredgewidth=WATER_WIDTH,
        linestyle="none",
        transform=offset_copy(edge, ax.figure, y=WATER_SYMBOL_SIZE / 2, units="points"),
        clip_on=True,
        zorder=_layers.WATER_LEVEL,
    )


def _water_label(ax: Axes, x: float, y: float, text: str) -> None:
    edge = blended_transform_factory(ax.transAxes, ax.transData)
    ax.text(
        x,
        y,
        text,
        transform=offset_copy(
            edge, ax.figure, x=-WATER_SYMBOL_SIZE, y=1, units="points"
        ),
        ha="right",
        va="bottom",
        fontsize=TEXT_SIZE,
        color=WATER_COLOR,
        clip_on=True,
        zorder=_layers.ANNOTATIONS,
    )


def _hole_water_levels(
    table: pd.DataFrame,
    vertical: Vertical,
    ground_levels: Mapping[Any, float],
) -> list[tuple[float, str]]:
    """Return ``(position, label)`` per hole, in display units (plan decision 3).

    The label is the ``label`` column where given, else the ``loca_id``.
    """
    _require(table, "water_level", ["loca_id"])
    given = [vs for vs in VS if _given(table, [vs])]
    if len(given) != 1:
        problem = "both" if given else "neither"
        raise ColumnError(
            f"The water_level table has {problem} of 'depth' and 'elevation'. "
            "Give one column with each hole's water level."
        )
    from_vs = given[0]
    units = overlay_units(table, "water_level", {from_vs: vertical.unit})
    values = vertical.to_display(numeric_column(table, from_vs), units[from_vs] or "")
    holes = table["loca_id"].to_numpy(dtype=object)
    labels = (
        table["label"].where(table["label"].notna(), table["loca_id"])
        if "label" in table.columns
        else table["loca_id"]
    ).to_numpy(dtype=object)
    levels, missing = [], []
    for hole, label, value in zip(holes, labels, values, strict=True):
        if np.isnan(value):
            continue
        if from_vs != vertical.vs:
            if hole not in ground_levels:
                missing.append(str(hole))
                continue
            value = ground_levels[hole] - value
        levels.append((float(value), str(label)))
    if missing:
        warn(
            f"Water levels for {', '.join(missing)} aren't drawn: they are given in "
            f"{from_vs}, and the plot data have no ground level for "
            f"{'that hole' if len(missing) == 1 else 'those holes'}. Add ground_level "
            f"for them, or give the water levels in {vertical.vs}."
        )
    return levels


def draw_water_level(
    ax: Axes,
    water_level: float | str | Sequence[tuple[float | str, str]] | pd.DataFrame,
    vertical: Vertical,
    ground_levels: Mapping[Any, float] | None = None,
) -> None:
    """Draw water levels (P01 §8).

    A number, a string such as ``"112.5 ft"``, or a list of ``(value, label)``
    draws a dashed line across the axes with ▽ and the label at the right
    end. A number is in the main data's units, in ``vertical.vs``. A table of
    ``loca_id`` and ``depth`` or ``elevation`` draws a short ▽ tick per hole at
    the right edge, labeled with its ``label`` or ``loca_id`` when there are at
    most 6.

    Parameters
    ----------
    ground_levels
        ``{loca_id: ground level}`` of the main data, in display units, to
        convert per-hole water levels between depth and elevation.
    """
    if isinstance(water_level, pd.DataFrame):
        levels = _hole_water_levels(water_level, vertical, ground_levels or {})
        edge = blended_transform_factory(ax.transAxes, ax.transData)
        for y, hole in levels:
            ax.plot(
                [0.95, 1.0],
                [y, y],
                color=WATER_COLOR,
                linewidth=WATER_WIDTH,
                transform=edge,
                zorder=_layers.WATER_LEVEL,
            )
            _water_symbol(ax, 0.97, y)
            if len(levels) <= MAX_HOLE_LABELS:
                _water_label(ax, 0.95, y, hole)
        return
    for y, label in _water_levels(water_level, vertical):
        ax.axhline(
            y,
            color=WATER_COLOR,
            linewidth=WATER_WIDTH,
            linestyle="--",
            zorder=_layers.WATER_LEVEL,
        )
        _water_symbol(ax, 0.97, y)
        _water_label(ax, 0.97, y, label)
