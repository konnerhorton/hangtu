"""Overlays drawn on profiles (P01 §8).

Each overlay takes the axes and the ``Vertical`` reference of the main data,
so P02, P06 and P09 can draw them without going through ``profile()``. Marks
are lines, patches and text, never scatter collections: those hold the data
points (plan decision 8).
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from os import PathLike
from typing import Any, Literal

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.colors import to_rgb
from matplotlib.patches import Rectangle
from matplotlib.text import Text
from matplotlib.transforms import blended_transform_factory, offset_copy

from hangtu.errors import AgsKitError, ColumnError, warn
from hangtu.plot import _layers
from hangtu.plot._data import numeric_column, rows_text
from hangtu.plot._palette import resolve_palette
from hangtu.plot._vertical import VS, Vertical, convert_pair, convert_vertical
from hangtu.units import parse_quantity, read_csv, to_display, units_of

TEXT_SIZE = 7  # points
STRATA_ALPHA = 0.12
WATER_COLOR = "#2166ac"
WATER_WIDTH = 0.8  # points
WATER_SYMBOL_SIZE = 6  # points
WATER_LABEL = "GWL"
MAX_HOLE_LABELS = 6
NEUTRAL = "0.3"
RANGE_COLOR = "0.45"
RANGE_ALPHA = 0.15
DESIGN_COLOR = "0.2"
DESIGN_WIDTH = 1.5  # points
REFERENCE_COLOR = "0.3"
REFERENCE_WIDTH = 0.6  # points


@dataclass(frozen=True)
class ValueScale:
    """How the main data's values are drawn, for overlays given in values.

    Attributes
    ----------
    unit
        The declared unit of the value column; None when it is unknown or not
        needed, and overlay values are then drawn as given.
    quantity
        The quantity kind, or None for an unregistered column.
    display_units
        ``"US"`` or ``"SI"``.
    log
        True on a log axis.
    """

    unit: str | None
    quantity: str | None
    display_units: str
    log: bool

    def to_display(self, values: Any, unit: str | None) -> np.ndarray:
        """Convert values in ``unit`` to the display units of the main data."""
        if self.unit is None or unit is None:
            return np.asarray(values, dtype=float)
        return to_display(values, unit, self.quantity, self.display_units)[0]


PAIRS = {vs: (f"{vs}_top", f"{vs}_base") for vs in VS}


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


def pair_reference(
    table: pd.DataFrame, overlay: str, *, required: bool
) -> Literal["depth", "elevation"] | None:
    """Return which pair an overlay gives: ``"depth"``, ``"elevation"`` or None.

    Exactly one of ``depth_top, depth_base`` and ``elevation_top,
    elevation_base`` may be given; a pair whose columns are all blank counts
    as absent. None means neither, which is an error when ``required``.
    """
    given = [vs for vs, pair in PAIRS.items() if _given(table, pair)]
    if len(given) == 1 or (not given and not required):
        return given[0] if given else None
    problem = "both" if given else "neither"
    raise ColumnError(
        f"The {overlay} table has {problem} of the depth pair (depth_top, "
        "depth_base) and the elevation pair (elevation_top, elevation_base). "
        f"Give one pair and leave the other out or blank. "
        f'ak.template("{overlay}") lists the columns.'
    )


def vertical_pair(
    table: pd.DataFrame,
    overlay: str,
    vertical: Vertical,
    from_vs: Literal["depth", "elevation"],
    units: Mapping[str, str | None],
    *,
    full_height_rows: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Read an overlay's top and base, drawn in ``vertical.vs``.

    Rows with top and base the wrong way round, or a blank bound, are NaN
    and named in a warning. With ``full_height_rows``, a row with both bounds
    blank is NaN without a warning: it covers the full height.
    """
    pair = PAIRS[from_vs]
    top, base = (
        vertical.to_display(numeric_column(table, column), units[column] or "")
        for column in pair
    )
    top, base = convert_pair(top, base, from_vs, vertical, overlay)
    blank = np.isnan(top) | np.isnan(base)
    if full_height_rows:
        blank &= ~(np.isnan(top) & np.isnan(base))
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
    from_vs = pair_reference(strata, "strata", required=True)
    units = overlay_units(
        strata, "strata", dict.fromkeys(PAIRS[from_vs], vertical.unit)
    )
    top, base = vertical_pair(strata, "strata", vertical, from_vs, units)
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


def _top_label(
    ax: Axes,
    x: float,
    y: float,
    text: str,
    transform: Any,
    *,
    ha: str = "center",
    above_axes: bool = False,
) -> None:
    """Write ``text`` at ``x``, just below ``y``.

    With ``above_axes``, the text goes just above the top of the axes
    instead, clear of the strata labels inside the top edge. Use it for
    full-height marks when the x-axis is at the bottom.
    """
    shift = 2 if ha == "left" else 0
    ax.text(
        x,
        y,
        text,
        transform=offset_copy(
            transform, ax.figure, x=shift, y=2 if above_axes else -2, units="points"
        ),
        ha=ha,
        va="bottom" if above_axes else "top",
        fontsize=TEXT_SIZE,
        color="0.25",
        clip_on=not above_axes,
        zorder=_layers.ANNOTATIONS,
    )


def _top_is_free(ax: Axes) -> bool:
    """Return True when nothing is drawn above the axes (x-axis at the bottom)."""
    return ax.xaxis.get_label_position() == "bottom"


def draw_ranges(
    ax: Axes,
    ranges: pd.DataFrame | str | PathLike[str],
    vertical: Vertical,
    scale: ValueScale,
) -> None:
    """Draw published ranges as translucent hatched bands from low to high.

    A band covers its depth or elevation pair, or the full height without
    one, and is labeled at its top with ``label`` and, when given, ``source``.
    A path is read with ``ak.read_csv``; declare units on the table with
    ``ak.set_units`` to read a file in other units.
    """
    if not isinstance(ranges, pd.DataFrame):
        ranges = read_csv(ranges)
    _require(ranges, "ranges", ["low", "high", "label"])
    from_vs = pair_reference(ranges, "ranges", required=False)
    assumed = {"low": scale.unit, "high": scale.unit}
    if from_vs is not None:
        assumed |= dict.fromkeys(PAIRS[from_vs], vertical.unit)
    units = overlay_units(ranges, "ranges", assumed)
    low, high = (
        scale.to_display(numeric_column(ranges, column), units[column])
        for column in ("low", "high")
    )
    if from_vs is None:
        top = base = np.full(len(ranges), np.nan)
    else:
        top, base = vertical_pair(
            ranges, "ranges", vertical, from_vs, units, full_height_rows=True
        )
    full_height = (
        np.ones(len(ranges), dtype=bool)
        if from_vs is None
        else ranges[list(PAIRS[from_vs])].isna().all(axis=1).to_numpy()
    )
    sources = ranges["source"] if "source" in ranges.columns else None
    axes_height = blended_transform_factory(ax.transData, ax.transAxes)
    for i, (lo, hi, label) in enumerate(zip(low, high, ranges["label"], strict=True)):
        if np.isnan(lo) or np.isnan(hi) or (not full_height[i] and np.isnan(top[i])):
            continue
        lo, hi = sorted((lo, hi))
        if scale.log and lo <= 0:
            lo = min(ax.get_xlim())
        if full_height[i]:
            y, height, transform = 0.0, 1.0, axes_height
            label_y = 1.0
        else:
            # top is the upper edge on screen in both depth and elevation.
            y, height, transform = base[i], top[i] - base[i], ax.transData
            label_y = top[i]
        ax.add_patch(
            Rectangle(
                (lo, y),
                hi - lo,
                height,
                transform=transform,
                facecolor=(*to_rgb(RANGE_COLOR), RANGE_ALPHA),
                edgecolor=(*to_rgb(RANGE_COLOR), 0.5),
                hatch="//",
                linewidth=0.6,
                zorder=_layers.RANGES,
            )
        )
        text = str(label)
        if sources is not None and pd.notna(sources.iloc[i]):
            text += f" ({sources.iloc[i]})"
        # Start the label at the left of the part of the band inside the axes.
        left, right = sorted(ax.get_xlim())
        if max(lo, left) < min(hi, right):
            _top_label(
                ax,
                max(lo, left),
                label_y,
                text,
                transform,
                ha="left",
                above_axes=bool(full_height[i]) and _top_is_free(ax),
            )


def _inside(ax: Axes, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    (left, right), (bottom, top) = sorted(ax.get_xlim()), sorted(ax.get_ylim())
    return (x >= left) & (x <= right) & (y >= bottom) & (y <= top)


def draw_design_lines(
    ax: Axes, design_lines: pd.DataFrame, vertical: Vertical, scale: ValueScale
) -> None:
    """Draw one dashed polyline per ``label``, labeled at its deepest end.

    The table has ``label``, ``value`` and one of ``depth`` or ``elevation``
    (P09 produces it). A column that doesn't match ``vs`` is converted with
    the single ground level.
    """
    _require(design_lines, "design_lines", ["label", "value"])
    given = [vs for vs in VS if _given(design_lines, [vs])]
    if len(given) != 1:
        problem = "both" if given else "neither"
        raise ColumnError(
            f"The design_lines table has {problem} of 'depth' and 'elevation'. "
            'Give one column. ak.template("design_lines") lists the columns.'
        )
    from_vs = given[0]
    units = overlay_units(
        design_lines, "design_lines", {from_vs: vertical.unit, "value": scale.unit}
    )
    positions = vertical.to_display(
        numeric_column(design_lines, from_vs), units[from_vs] or ""
    )
    positions = convert_vertical(
        positions, from_vs, vertical, "design_lines", vertical.vs
    )
    values = scale.to_display(numeric_column(design_lines, "value"), units["value"])
    labels = design_lines["label"].to_numpy(dtype=object)
    depth_order = 1.0 if vertical.vs == "depth" else -1.0
    for label in dict.fromkeys(labels):
        rows = (labels == label) & ~np.isnan(positions) & ~np.isnan(values)
        if not rows.any():
            continue
        order = np.argsort(depth_order * positions[rows], kind="stable")
        x, y = values[rows][order], positions[rows][order]
        ax.plot(
            x,
            y,
            color=DESIGN_COLOR,
            linewidth=DESIGN_WIDTH,
            linestyle="--",
            zorder=_layers.LINES,
        )
        # Label the deepest point inside the axes.
        inside = _inside(ax, x, y)
        if not inside.any():
            continue
        end = np.flatnonzero(inside)[-1]
        ax.annotate(
            str(label),
            xy=(x[end], y[end]),
            # Up and left of the deepest point, which is at the bottom on screen.
            xytext=(-3, 3),
            textcoords="offset points",
            ha="right",
            va="bottom",
            fontsize=TEXT_SIZE,
            color=DESIGN_COLOR,
            annotation_clip=True,
            zorder=_layers.ANNOTATIONS,
        )


def draw_reference_lines(
    ax: Axes, reference_lines: Sequence[tuple[float | str, str]], scale: ValueScale
) -> None:
    """Draw thin dotted vertical lines at values, labeled at the top.

    A number is in the main data's units; a string such as ``"2000 psf"``
    carries its own unit.
    """
    top = blended_transform_factory(ax.transData, ax.transAxes)
    for entry in reference_lines:
        if not (isinstance(entry, tuple | list) and len(entry) == 2):
            raise AgsKitError(
                "reference_lines must be a list of (value, label) pairs, not "
                f'{reference_lines!r}. Example: reference_lines=[(2000, "limit")]'
            )
        value, label = entry
        if isinstance(value, str):
            number, unit = parse_quantity(value, scale.quantity)
            x = float(scale.to_display([number], unit)[0])
        elif isinstance(value, int | float) and not isinstance(value, bool):
            x = float(scale.to_display([value], scale.unit)[0])
        else:
            raise AgsKitError(
                f"The reference line {value!r} must be a number in the plot data's "
                'units, or a number with a unit such as "2000 psf".'
            )
        ax.axvline(
            x,
            color=REFERENCE_COLOR,
            linewidth=REFERENCE_WIDTH,
            linestyle=":",
            zorder=_layers.LINES,
        )
        _top_label(ax, x, 1.0, str(label), top, above_axes=_top_is_free(ax))


def draw_note(ax: Axes, note: str) -> None:
    """Write a note at the lower left inside the axes."""
    ax.text(
        0.02,
        0.02,
        note,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=TEXT_SIZE,
        color="0.25",
        zorder=_layers.ANNOTATIONS,
    )


STATISTICS = ("count", "mean", "std", "cov", "median", "min", "max")
DEFAULT_STATISTICS = ("count", "mean", "std", "median", "min", "max")
_STATISTIC_HEADINGS = {"count": "n", "cov": "CoV"}
MAX_STATS_UNITS = 6
NOTE_LINE_HEIGHT = 8.5  # points, for 7 pt text


def statistics_list(stats_box: bool | Sequence[str]) -> list[str]:
    """Return the statistics a ``stats_box`` argument asks for."""
    if stats_box is True:
        return list(DEFAULT_STATISTICS)
    if isinstance(stats_box, str) or not isinstance(stats_box, Sequence):
        raise AgsKitError(
            f"stats_box must be True, False or a list of statistics, not "
            f'{stats_box!r}. Example: stats_box=["count", "mean", "cov"]'
        )
    unknown = [name for name in stats_box if name not in STATISTICS]
    if unknown or not stats_box:
        raise AgsKitError(
            f"stats_box can't show {unknown or 'an empty list'}. Statistics: "
            f"{', '.join(STATISTICS)}."
        )
    return list(stats_box)


def format_number(value: float) -> str:
    """Write a statistic to 3 significant figures: ``1,290``, ``0.0123``, ``2.30e-05``.

    Values below 0.01 or from a million up are in scientific notation, so a
    column of small values such as k reads consistently.
    """
    if value == 0 or not np.isfinite(value):
        return f"{value:g}"
    exponent = math.floor(math.log10(abs(value)))
    if not -2 <= exponent < 6:
        return f"{value:.2e}"
    rounded = float(f"{value:.3g}")
    return f"{rounded:,.{max(0, 2 - exponent)}f}"


def _statistic(values: np.ndarray, name: str, interval: bool) -> str:
    n = values.size
    if name == "count":
        return str(n)
    if n == 0 or (name in ("std", "cov") and n < 2):
        return "—"
    if name == "cov":
        mean = values.mean()
        # CoV needs a true zero (TODO #9).
        if interval or mean == 0:
            return "—"
        return f"{values.std(ddof=1) / abs(mean):.2f}"
    result = {
        "mean": np.mean,
        "std": lambda v: np.std(v, ddof=1),
        "median": np.median,
        "min": np.min,
        "max": np.max,
    }[name](values)
    return format_number(float(result))


def stats_table(
    values: np.ndarray,
    groups: np.ndarray,
    statistics: Sequence[str],
    *,
    order: Sequence[Any] | None = None,
    interval: bool = False,
) -> list[list[str]]:
    """Return the stats box rows: a heading, one row per group, and "All".

    Groups are listed when there are at most 6 (with "All" after them when
    there are several); otherwise only "All". ``groups`` holds None for
    ungrouped data; ``order`` is the legend order of the groups. std is the
    sample standard deviation, and shows "—" when n < 2.
    """
    present = set(groups)
    names = [g for g in (order or dict.fromkeys(groups)) if g in present]
    names = [g for g in names if g is not None]
    rows = [["", *(_STATISTIC_HEADINGS.get(name, name) for name in statistics)]]
    listed = names if len(names) <= MAX_STATS_UNITS else []
    for name in listed:
        these = values[groups == name]
        rows.append([str(name), *(_statistic(these, s, interval) for s in statistics)])
    if len(listed) != 1:
        rows.append(["All", *(_statistic(values, s, interval) for s in statistics)])
    return rows


def draw_stats_box(ax: Axes, rows: Sequence[Sequence[str]], note: str | None) -> Text:
    """Write the stats table in a box at the lower left, above any ``note``."""
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    lines = [
        "  ".join(
            cell.ljust(width) if i == 0 else cell.rjust(width)
            for i, (cell, width) in enumerate(zip(row, widths, strict=True))
        )
        for row in rows
    ]
    above_note = 0.0 if note is None else NOTE_LINE_HEIGHT * (note.count("\n") + 1) + 4
    return ax.text(
        0.02,
        0.02,
        "\n".join(lines),
        transform=offset_copy(ax.transAxes, ax.figure, y=above_note, units="points"),
        ha="left",
        va="bottom",
        fontsize=TEXT_SIZE,
        family="monospace",
        color="0.15",
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": "white",
            "edgecolor": "0.7",
            "linewidth": 0.5,
            "alpha": 0.9,
        },
        zorder=_layers.ANNOTATIONS,
    )
