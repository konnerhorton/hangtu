"""P01 property profile (docs/plots/P01-property-profile.md)."""

import math
from collections.abc import Mapping
from numbers import Real
from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text

from ags_kit import units as _units
from ags_kit._settings import _display_units, settings
from ags_kit.errors import AgsKitError, ColumnError, warn
from ags_kit.plot import _layers, _presets, style
from ags_kit.plot._data import numeric_column, rows_text
from ags_kit.plot._hints import hint_missing
from ags_kit.plot._labels import axis_label
from ags_kit.plot._legend import add_legend
from ags_kit.plot._limits import (
    apply_vertical_axis,
    log_limits,
    nice_limits,
    nice_step,
    set_linear_axis,
    set_log_axis,
)
from ags_kit.plot._notes import Notes, edge_markers
from ags_kit.plot._overlays import (
    ValueScale,
    draw_design_lines,
    draw_note,
    draw_ranges,
    draw_reference_lines,
    draw_stats_box,
    draw_strata,
    draw_water_level,
    statistics_list,
    stats_table,
)
from ags_kit.plot._palette import resolve_palette
from ags_kit.plot._presets import Preset
from ags_kit.plot._vertical import (
    Vertical,
    add_secondary_depth,
    check_secondary_depth,
    choose_vs,
    hole_ground_levels,
    interval_bounds,
    length_columns,
    vertical_values,
)
from ags_kit.registry import column_info

LEGEND_WIDTH = 1.5  # inches added to the settings size for the outside legend
NEUTRAL = "0.3"  # points not colored by a group
MARKER_SIZE = 5.0  # points
CARET_SIZE = 6.0  # points
INTERVAL_WIDTH = 1.0  # points
BLANK_GROUP = "(blank)"
ROOM_MARGIN = 0.02  # axes fraction between the stats box and the lowest data
SECONDARY_SPACE = 42.0  # points between the axes and the legend for a depth axis
# Qualifier -> (marker, size, legend text, notes reason) (P01 §3, §7).
QUALIFIERS = {
    "<": ("<", CARET_SIZE, "less than", "less_than"),
    ">": (">", CARET_SIZE, "greater than", "greater_than"),
}
# Marker shapes for marker_by groups: ● ■ ▲ ◆ ▼ ✚ ✖ ⬟ ⬢ ★ (P01 §7).
MARKER_CYCLE = ("o", "s", "^", "D", "v", "P", "X", "p", "h", "*")
QUALIFIER_ORDER = [marker for marker, *_ in QUALIFIERS.values()]
CARETS = set(QUALIFIER_ORDER)
CONNECT_WIDTH = 0.6  # points
CONNECT_ALPHA = 0.6


def _check_limits(name: str, limits: Any, log: bool = False) -> tuple[float, float]:
    ok = (
        isinstance(limits, list | tuple)
        and len(limits) == 2
        and all(
            isinstance(v, Real) and not isinstance(v, bool) and math.isfinite(v)
            for v in limits
        )
        and limits[0] != limits[1]
    )
    if not ok:
        raise AgsKitError(
            f"{name} must be (low, high), two different numbers in display units, "
            f"not {limits!r}. Example: {name}=(0, 50)"
        )
    lo, hi = sorted(float(v) for v in limits)
    if log and lo <= 0:
        raise AgsKitError(
            f"{name}={limits!r} can't be used on a log axis, because the lower "
            f"limit must be greater than 0. Example: {name}=(1e-7, 1e-2)"
        )
    return lo, hi


def _quantity(value: str, preset: Preset | None) -> str | None:
    info = column_info(value)
    registered = info.get("quantity") if info else None
    if preset is None:
        return registered
    if registered is not None and registered != preset.quantity:
        raise AgsKitError(
            f"preset={preset.name!r} is for a {preset.quantity.replace('_', ' ')}, "
            f"but column {value!r} is a {registered.replace('_', ' ')}. "
            f"Use preset={value!r} if it exists, or leave preset out."
        )
    return preset.quantity


def _x_text(value: str, label: str | None, preset: Preset | None) -> str:
    if label is not None:
        return label
    if preset is not None:
        return preset.label
    info = column_info(value)
    return info["label"] if info and "label" in info else value


def _start_at_zero(value: str, preset: Preset | None) -> bool:
    if preset is not None:
        return preset.start_at_zero
    info = column_info(value)
    return bool(info) and info.get("scale") == "ratio"


def _typical(
    preset: Preset | None, x_unit: str | None, system: str
) -> tuple[float, float] | None:
    """Return the preset's typical range in display units, if it can be converted."""
    if preset is None:
        return None
    kind = _units.quantity_kind(preset.quantity)
    if kind["canonical"] is not None and x_unit is None:
        return None
    low, high = _units.to_display(
        preset.typical, kind["canonical"], preset.quantity, system
    )[0]
    return float(low), float(high)


def _x_limits(
    x: np.ndarray,
    *,
    log: bool,
    xlim: tuple[float, float] | None,
    start_at_zero: bool,
    typical: tuple[float, float] | None,
) -> tuple[float, float]:
    if xlim is not None:
        return xlim
    if not x.size:
        if typical is not None:
            if log:
                return log_limits(*typical)
            return nice_limits(*typical, start_at_zero=start_at_zero)
        return (1.0, 100.0) if log else (0.0, 1.0)
    vmin, vmax = float(x.min()), float(x.max())
    if vmin == vmax and typical is not None:
        # A single value: the typical range, widened to include it (P01 §11).
        vmin, vmax = min(typical[0], vmin), max(typical[1], vmax)
    if log:
        return log_limits(vmin, vmax)
    return nice_limits(vmin, vmax, start_at_zero=start_at_zero)


def _room_below_data(ax: Axes, box: Text, lowest: float) -> None:
    """Deepen the vertical axis so ``box`` sits below the lowest data.

    ``lowest`` is the data value nearest the bottom of the axes on screen
    (the deepest depth, or the lowest elevation). The bottom limit moves out
    to a nice value; the top limit only rounds out to the same step.
    """
    figure = ax.figure
    figure.draw_without_rendering()  # runs the layout, so sizes are final
    renderer = figure.canvas.get_renderer()
    box_top = box.get_bbox_patch().get_window_extent(renderer).y1
    needed = ax.transAxes.inverted().transform((0.0, box_top))[1] + ROOM_MARGIN
    bottom, top = ax.get_ylim()  # in screen order, for depth and elevation
    if (lowest - bottom) / (top - bottom) >= needed or not 0 < needed < 1:
        return

    def outward(value: float, step: float, away_from: float) -> float:
        n = value / step
        return (math.floor(n) if value < away_from else math.ceil(n)) * step

    wanted = (lowest - needed * top) / (1 - needed)
    step = nice_step(*sorted((wanted, top)))
    top = outward(top, step, wanted) if top % step else top
    wanted = (lowest - needed * top) / (1 - needed)
    step = nice_step(*sorted((wanted, top)))
    set_linear_axis(ax, "y", (outward(wanted, step, top), top))


def _set_vertical_axis(
    ax: Axes,
    vs: Literal["depth", "elevation"],
    y: np.ndarray,
    ylim: tuple[float, float] | None,
) -> None:
    if ylim is not None:
        lo, hi = ylim
        set_linear_axis(ax, "y", (hi, lo) if vs == "depth" else (lo, hi))
    elif y.size:
        apply_vertical_axis(ax, vs, float(y.min()), float(y.max()))
    else:
        apply_vertical_axis(ax, vs, 0.0, 1.0)


def _color_groups(
    df: pd.DataFrame, color_by: str | None, palette: Mapping[Any, Any] | None
) -> tuple[np.ndarray, dict[Any, Any]]:
    """Return each row's group, and ``{group: color}`` in legend order.

    Rows with a blank group are grouped as ``BLANK_GROUP`` in a neutral color.
    """
    if color_by is None or color_by not in df.columns:
        return np.full(len(df), None, dtype=object), {None: NEUTRAL}
    groups = df[color_by].to_numpy(dtype=object)
    blank = pd.isna(groups)
    colors = resolve_palette(groups[~blank], palette)
    groups = np.where(blank, BLANK_GROUP, groups)
    if blank.any():
        colors[BLANK_GROUP] = NEUTRAL
    return groups, colors


def _qualifiers(df: pd.DataFrame) -> np.ndarray:
    """Return each row's qualifier: ``"<"``, ``">"`` or ``""``."""
    if "qualifier" not in df.columns:
        return np.full(len(df), "", dtype=object)
    qualifiers = df["qualifier"].fillna("").astype(str).str.strip()
    bad = ~qualifiers.isin(["", *QUALIFIERS])
    if bad.any():
        found = ", ".join(repr(text) for text in dict.fromkeys(qualifiers[bad]))
        raise ColumnError(
            f'Column \'qualifier\' must hold "<", ">" or nothing, but rows '
            f"{rows_text(df.index[bad])} hold {found}. Put the qualifier only in "
            "'qualifier' and the number in the value column."
        )
    return qualifiers.to_numpy(dtype=object)


def _intervals(
    df: pd.DataFrame,
    intervals: bool | str,
    units: Mapping[str, str | None],
    vertical: Vertical,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Return the test interval of each row in the vertical reference, or None.

    Rows with no interval, or with ``depth_top`` below ``depth_base``, are NaN.
    """
    if intervals not in (True, False, "auto"):
        raise AgsKitError(
            f'intervals must be True, False or "auto", not {intervals!r}.'
        )
    if intervals is False:
        return None
    if not {"depth_top", "depth_base"} <= set(df.columns):
        if intervals is True:
            raise ColumnError(
                "intervals=True needs 'depth_top' and 'depth_base' columns with "
                "the top and base of each tested interval. Add them, or leave "
                "intervals out."
            )
        return None
    bounds = interval_bounds(df, units, vertical)
    if bounds is None:
        warn(
            "Test intervals aren't drawn: drawing them against elevation needs "
            "each hole's ground level, from a 'ground_level' column or from "
            "'elevation' and 'depth'. Add one, or plot with vs='depth'."
        )
        return None
    top, base = bounds
    swapped = (top < base) if vertical.vs == "elevation" else (top > base)
    if swapped.any():
        warn(
            f"Rows {rows_text(df.index[swapped])} have depth_top below "
            "depth_base, so their test intervals aren't drawn. Check those rows."
        )
    return np.where(swapped, np.nan, top), np.where(swapped, np.nan, base)


def _marker_groups(
    df: pd.DataFrame, marker_by: str | None
) -> tuple[np.ndarray, dict[Any, str]]:
    """Return each row's marker group, and ``{group: shape}`` in legend order.

    Rows with a blank group are grouped as ``BLANK_GROUP``. Without
    ``marker_by`` there are no groups.
    """
    if marker_by is None:
        return np.full(len(df), None, dtype=object), {}
    if marker_by not in df.columns:
        raise ColumnError(
            f"marker_by={marker_by!r} isn't a column. Available columns: "
            f"{', '.join(map(str, df.columns))}."
        )
    groups = df[marker_by].to_numpy(dtype=object)
    blank = pd.isna(groups)
    names = sorted(dict.fromkeys(groups[~blank]), key=str)
    if blank.any():
        names.append(BLANK_GROUP)
        groups = np.where(blank, BLANK_GROUP, groups)
    if len(names) > len(MARKER_CYCLE):
        warn(
            f"marker_by={marker_by!r} has {len(names)} groups but there are "
            f"{len(MARKER_CYCLE)} marker shapes, so some shapes repeat. Use "
            "connect=True to follow each hole, or split the data into several plots."
        )
    shapes = {name: MARKER_CYCLE[i % len(MARKER_CYCLE)] for i, name in enumerate(names)}
    return groups, shapes


def _draw_points(
    ax: Axes,
    x: np.ndarray,
    y: np.ndarray,
    rows: np.ndarray,
    markers: np.ndarray,
    color: Any,
    label: str,
    limits: Mapping[str, tuple[float, float] | None],
) -> np.ndarray:
    """Draw one color group's points, one collection per marker shape.

    Returns the mask of rows drawn at the edge of fixed limits.
    """
    edge = np.zeros(len(x), dtype=bool)
    present = set(markers[rows])
    shapes = [m for m in MARKER_CYCLE if m in present]
    shapes += [m for m in QUALIFIER_ORDER if m in present]
    for i, marker in enumerate(shapes):
        caret = marker in CARETS
        these = rows & (markers == marker)
        if any(limits.values()):
            edge[these] = edge_markers(ax, x[these], y[these], limits, color, marker)
        inside = these & ~edge
        ax.scatter(
            x[inside],
            y[inside],
            s=(CARET_SIZE if caret else MARKER_SIZE) ** 2,
            marker=marker,
            color=color,
            edgecolors="white",
            linewidths=0.4,
            label=label if i == 0 and not caret else f"_{label} {marker}",
            zorder=_layers.QUALIFIERS if caret else _layers.MARKERS,
        )
    return edge


def _legend_marker(marker: str, color: Any, label: str, size: float) -> Line2D:
    return Line2D(
        [],
        [],
        marker=marker,
        markersize=size,
        color=color,
        linestyle="none",
        label=label,
    )


def _draw_connections(
    ax: Axes, holes: np.ndarray, x: np.ndarray, y: np.ndarray, rows: np.ndarray
) -> None:
    """Draw one gray line through each hole's points, in vertical order."""
    for hole in dict.fromkeys(holes[rows & ~pd.isna(holes)]):
        these = np.flatnonzero(rows & (holes == hole))
        order = these[np.argsort(y[these], kind="stable")]
        ax.plot(
            x[order],
            y[order],
            color=NEUTRAL,
            linewidth=CONNECT_WIDTH,
            alpha=CONNECT_ALPHA,
            zorder=_layers.CONNECT,
        )


def _draw_intervals(
    ax: Axes, x: np.ndarray, top: np.ndarray, base: np.ndarray, color: Any
) -> None:
    """Draw test intervals as vertical bars: one line, broken by NaN."""
    if not x.size:
        return
    gaps = np.full(x.size, np.nan)
    ax.plot(
        np.column_stack([x, x, gaps]).ravel(),
        np.column_stack([top, base, gaps]).ravel(),
        color=color,
        linewidth=INTERVAL_WIDTH,
        solid_capstyle="round",
        zorder=_layers.INTERVALS,
    )


def _qualifier_handles(qualifiers: np.ndarray, notes: Notes) -> list[Line2D]:
    """Count qualified values and return their legend entries."""
    handles = []
    for qualifier, (marker, size, text, reason) in QUALIFIERS.items():
        n = notes.count(qualifiers == qualifier, reason)
        if n:
            handles.append(_legend_marker(marker, NEUTRAL, f"{text} ({n})", size))
    return handles


def _new_axes(figsize: tuple[float, float] | None) -> tuple[Figure, Axes]:
    if figsize is None:
        width, height = settings.figure_sizes["profile"]
        figsize = (width + LEGEND_WIDTH, height)
    return plt.subplots(figsize=figsize, layout="constrained")


def profile(
    df: pd.DataFrame,
    value: str,
    *,
    vs: Literal["elevation", "depth"] | None = None,
    preset: str | None = None,
    log: bool | None = None,
    label: str | None = None,
    color_by: str | None = "geology_unit",
    marker_by: str | None = None,
    connect: bool = False,
    intervals: bool | Literal["auto"] = "auto",
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    xaxis_position: Literal["top", "bottom"] = "bottom",
    secondary: Literal["depth"] | None = None,
    strata: pd.DataFrame | None = None,
    water_level: float | list[tuple[float, str]] | pd.DataFrame | None = None,
    ranges: pd.DataFrame | str | None = None,
    design_lines: pd.DataFrame | None = None,
    reference_lines: list[tuple[float, str]] | None = None,
    stats_box: bool | list[str] = False,
    stats_box_room: bool = True,
    note: str | None = None,
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes]:
    """Plot a property against depth or elevation (P01).

    Points are colored by geology unit. Nothing is dropped silently: blanks,
    values ≤ 0 on a log axis and values beyond fixed limits are counted in a
    footnote, and the counts are in ``ax.ags_notes``.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per observation: the ``value`` column, plus ``depth`` or
        ``elevation`` (or ``depth`` and ``ground_level``). See
        ``ak.template("profile")``.
    value : str
        The column to plot.
    vs : {"elevation", "depth"}, optional
        The vertical axis. By default elevation when it is available (an
        ``elevation`` column, or ``depth`` plus ``ground_level``), else depth.
    preset : str, optional
        ``"hydraulic_conductivity"``, ``"undrained_shear_strength"``,
        ``"water_content"`` or ``"bulk_unit_weight"``: the label, units, log or
        linear scale and default limits for that property.
    log : bool, optional
        Use a log x-axis. By default from the preset, else linear.
    label : str, optional
        The x-axis text; units are added automatically.
    color_by : str or None
        Column that colors the points; None for one neutral color.
    xlim, ylim : (low, high), optional
        Fixed limits in display units. Values beyond them are drawn at the
        edge with an arrow, and counted.
    xaxis_position : {"bottom", "top"}
        ``"top"`` puts the value axis at the top, as on a borehole log.
    stats_box : bool or list of str
        A box of statistics at the lower left: True for count, mean, std,
        median, min and max per unit, or a list chosen from those and
        ``"cov"``.
    stats_box_room : bool
        Deepen the vertical axis so the stats box sits below the lowest
        data instead of covering it. Ignored with ``ylim=``.
    palette : dict, optional
        ``{geology unit: color}`` for this plot.
    units : dict, optional
        ``{column: unit}``, overriding the units declared on ``df``.
    display_units : {"US", "SI"}, optional
        Defaults to ``ak.settings.display_units``.
    figsize : (width, height), optional
        Inches; by default the settings ``profile`` size plus room for the
        legend. Ignored with ``ax=``.
    ax : matplotlib Axes, optional
        Draw into this axes, e.g. a ``Sheet`` panel.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, ax

    Examples
    --------
    >>> k = ak.read_csv("perm.csv", units={"depth": "ft", "ground_level": "ft",
    ...                                    "hydraulic_conductivity": "cm/s"})
    >>> fig, ax = ak.plot.profile(k, "hydraulic_conductivity",
    ...                           preset="hydraulic_conductivity")
    """
    if value not in df.columns:
        raise ColumnError(
            f"Column {value!r} not found. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}."
        )
    if color_by is not None and color_by != "geology_unit" and color_by not in df:
        raise ColumnError(
            f"color_by={color_by!r} isn't a column. Available columns: "
            f"{', '.join(map(str, df.columns))}."
        )
    if xaxis_position not in ("top", "bottom"):
        raise AgsKitError(
            f'xaxis_position must be "top" or "bottom", not {xaxis_position!r}.'
        )
    if secondary not in (None, "depth"):
        raise AgsKitError(f'secondary must be "depth" or None, not {secondary!r}.')
    statistics = statistics_list(stats_box) if stats_box is not False else None

    system = _display_units(display_units or settings.display_units)
    chosen = _presets.preset(preset) if preset is not None else None
    quantity = _quantity(value, chosen)
    log = chosen.log if log is None and chosen is not None else bool(log)
    xlim = _check_limits("xlim", xlim, log) if xlim is not None else None
    ylim = _check_limits("ylim", ylim) if ylim is not None else None
    vs = choose_vs(df, vs)
    if connect and "loca_id" not in df.columns:
        raise ColumnError(
            "connect=True draws a line through each hole's points, so it needs a "
            "'loca_id' column naming the hole of each row. Add it, or leave "
            "connect out."
        )

    with style.context(**style_overrides):
        optional = {
            "loca_id": "connect= and per-hole water levels are unavailable",
        }
        if color_by == "geology_unit":
            optional = {"geology_unit": "points are not colored by geology", **optional}
        if vs == "depth":
            optional["ground_level"] = "elevations can't be computed"
        hint_missing(df, optional)

        resolved = _units.resolve_units(
            df,
            [value, *length_columns(df)],
            units,
            quantities={value: quantity} if quantity else None,
        )
        raw = numeric_column(df, value)
        x, x_unit_text = _units.to_display(raw, resolved[value], quantity, system)
        y, vertical = vertical_values(df, vs, resolved, system)
        if secondary == "depth":
            check_secondary_depth(vertical)
        qualifiers = _qualifiers(df)
        bounds = _intervals(df, intervals, resolved, vertical)

        notes = Notes()
        blank = np.isnan(x) | np.isnan(y)
        notes.count(blank, "nan")
        drawn = ~blank
        if log:
            nonpositive = drawn & (x <= 0)
            notes.count(nonpositive, "log_nonpositive")
            drawn &= ~nonpositive
        if bounds is None:
            bars = np.zeros(len(df), dtype=bool)
            top = base = np.full(len(df), np.nan)
        else:
            top, base = bounds
            bars = drawn & np.isfinite(top) & np.isfinite(base)

        if ax is None:
            fig, ax = _new_axes(figsize)
        else:
            fig = ax.figure
        style.style_axes(ax)

        limits = _x_limits(
            x[drawn],
            log=log,
            xlim=xlim,
            start_at_zero=_start_at_zero(value, chosen),
            typical=_typical(chosen, resolved[value], system),
        )
        if log:
            set_log_axis(ax, "x", limits)
        else:
            set_linear_axis(ax, "x", limits)
        _set_vertical_axis(
            ax, vs, np.concatenate([y[drawn], top[bars], base[bars]]), ylim
        )
        if xaxis_position == "top":
            ax.xaxis.tick_top()
            ax.xaxis.set_label_position("top")

        if strata is not None:
            draw_strata(ax, strata, vertical, palette)
        if water_level is not None:
            ground_levels = (
                hole_ground_levels(df, resolved, vertical)
                if isinstance(water_level, pd.DataFrame)
                else None
            )
            draw_water_level(ax, water_level, vertical, ground_levels)
        scale = ValueScale(resolved[value], quantity, system, log)
        if ranges is not None:
            draw_ranges(ax, ranges, vertical, scale)
        if design_lines is not None:
            draw_design_lines(ax, design_lines, vertical, scale)
        if reference_lines is not None:
            draw_reference_lines(ax, reference_lines, scale)
        if note is not None:
            draw_note(ax, str(note))

        groups, colors = _color_groups(df, color_by, palette)
        marker_groups, shapes = _marker_groups(df, marker_by)
        carets = {q: marker for q, (marker, *_) in QUALIFIERS.items()}
        markers = np.array(
            [
                carets.get(q, shapes.get(group, MARKER_CYCLE[0]))
                for q, group in zip(qualifiers, marker_groups, strict=True)
            ],
            dtype=object,
        )
        if connect:
            _draw_connections(ax, df["loca_id"].to_numpy(dtype=object), x, y, drawn)
        edge = np.zeros(len(df), dtype=bool)
        unit_handles = []
        for group, color in colors.items():
            rows = drawn & (groups == group) if group is not None else drawn
            group_edge = _draw_points(
                ax, x, y, rows, markers, color, str(group), {"x": xlim, "y": ylim}
            )
            edge |= group_edge
            these = bars & rows & ~group_edge
            _draw_intervals(ax, x[these], top[these], base[these], color)
            if group is not None and rows.any():
                unit_handles.append(
                    Patch(facecolor=color, edgecolor="none", label=str(group))
                    if shapes
                    else _legend_marker("o", color, str(group), MARKER_SIZE)
                )
        notes.count(edge, "beyond_limit")
        shape_handles = [
            _legend_marker(shape, NEUTRAL, str(group), MARKER_SIZE)
            for group, shape in shapes.items()
            if (drawn & (marker_groups == group)).any()
        ]
        qualified = _qualifier_handles(np.where(drawn, qualifiers, ""), notes)

        if not drawn.any():
            ax.text(
                0.5,
                0.5,
                "No data",
                transform=ax.transAxes,
                ha="center",
                va="center",
                color="0.4",
                zorder=_layers.ANNOTATIONS,
            )

        ax.set_xlabel(
            axis_label(
                _x_text(value, label, chosen),
                x_unit_text,
                unknown=resolved[value] is None and _units.needs_units(value, quantity),
            )
        )
        ax.set_ylabel(vertical.label())
        if statistics is not None:
            info = column_info(value)
            rows = stats_table(
                x[drawn],
                groups[drawn],
                statistics,
                order=list(colors),
                interval=bool(info) and info.get("scale") == "interval",
            )
            box = draw_stats_box(ax, rows, None if note is None else str(note))
            heights = np.concatenate([y[drawn], top[bars], base[bars]])
            if stats_box_room and ylim is None and heights.size:
                lowest = heights.max() if vs == "depth" else heights.min()
                _room_below_data(ax, box, float(lowest))
        if secondary == "depth":
            add_secondary_depth(ax, vertical)
        offset = SECONDARY_SPACE if secondary else 0.0
        add_legend(ax, [unit_handles, shape_handles, qualified], notes, offset)
        notes.render(ax, offset)
    return fig, ax
