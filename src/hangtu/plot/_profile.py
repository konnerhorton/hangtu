"""P01 property profile (docs/plots/P01-property-profile.md)."""

import math
from collections.abc import Callable, Mapping
from typing import Any, Literal, NamedTuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Patch
from matplotlib.text import Text

from hangtu import units as _units
from hangtu._data import rows_text, text_values
from hangtu._settings import _display_units, figure_size, settings
from hangtu.analysis.correlations._framework import REASONS as CORRELATION_REASONS
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.plot import _layers, _presets, _text_values, _value_ranges, _values, style
from hangtu.plot._hints import hint_missing
from hangtu.plot._labels import axis_label
from hangtu.plot._legend import add_legend, check_legend
from hangtu.plot._limits import (
    apply_vertical_axis,
    nice_limits,
    nice_step,
    set_linear_axis,
    set_log_axis,
)
from hangtu.plot._notes import Notes, edge_markers
from hangtu.plot._overlays import (
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
from hangtu.plot._vertical import (
    Vertical,
    add_secondary_depth,
    check_secondary_depth,
    choose_vs,
    hole_ground_levels,
    interval_bounds,
    length_columns,
    vertical_values,
)
from hangtu.registry import column_info

MARKER_SIZE = 5.0  # points
INTERVAL_WIDTH = 1.0  # points
ROOM_MARGIN = 0.02  # axes fraction between the stats box and the lowest data
SECONDARY_SPACE = 42.0  # points between the axes and the legend for a depth axis
# Marker shapes for marker_by groups: ● ■ ▲ ◆ ▼ ✚ ✖ ⬟ ⬢ ★ (P01 §7).
MARKER_CYCLE = ("o", "s", "^", "D", "v", "P", "X", "p", "h", "*")
CONNECT_WIDTH = 0.6  # points
CONNECT_ALPHA = 0.6
CLEAR_FACTOR = 1.05  # x-limit at least the nice value above 1.05 x clear_of (P02 §6)


class Companion(NamedTuple):
    """Marks a plot built on the profile draws per row (P06 limits bars).

    - ``rows``: the rows it draws. A row here with a blank value isn't
      counted as blank: it sets the vertical limits, gives its unit a legend
      entry and means there is data.
    - ``x``: values in display units that the automatic x limits cover.
    - ``draw(ax, y, groups, colors, notes)``: draws the marks, given each
      row's vertical position in display units and its color group. Called
      after the points and text values, before the legend; returns the
      legend entries and the mask of rows it drew at the edge of fixed
      limits (or left out beyond them). Those are counted with the points
      drawn at the edge, so a row counts once.
    """

    rows: np.ndarray
    x: np.ndarray
    draw: Callable[
        [Axes, np.ndarray, np.ndarray, Mapping, Notes],
        tuple[list[Artist], np.ndarray],
    ]


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
        apply_vertical_axis(ax, vs, 0.0, 1.0, clear=False)


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
        raise HangtuError(
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

    Rows with a blank group are grouped as ``_values.BLANK_GROUP``. Without
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
        names.append(_values.BLANK_GROUP)
        groups = np.where(blank, _values.BLANK_GROUP, groups)
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
    flags: Mapping[str, _values.Flag],
) -> np.ndarray:
    """Draw one color group's points, one collection per marker.

    ``markers`` holds each row's marker shape, or a key into ``flags`` for a
    flagged value (qualifier caret, refusal), so a flag never shares a shape
    with a ``marker_by`` group. Returns the mask of rows drawn at the edge of
    fixed limits.
    """
    edge = np.zeros(len(x), dtype=bool)
    present = set(markers[rows])
    keys = [m for m in MARKER_CYCLE if m in present]
    keys += [m for m in flags if m in present]
    for i, key in enumerate(keys):
        flag = flags.get(key)
        shape = key if flag is None else flag.marker
        these = rows & (markers == key)
        if any(limits.values()):
            edge[these] = edge_markers(ax, x[these], y[these], limits, color, shape)
        inside = these & ~edge
        if flag is None or flag.filled:
            colors = {"color": color, "edgecolors": "white", "linewidths": 0.4}
        else:
            colors = {"facecolors": "none", "edgecolors": color, "linewidths": 0.8}
        ax.scatter(
            x[inside],
            y[inside],
            s=(MARKER_SIZE if flag is None else flag.size) ** 2,
            marker=shape,
            **colors,
            label=label if i == 0 and flag is None else f"_{label} {shape}",
            zorder=_layers.MARKERS if flag is None else _layers.QUALIFIERS,
        )
    return edge


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
            color=_values.NEUTRAL,
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


def _new_axes(figsize: tuple[float, float] | None) -> tuple[Figure, Axes]:
    return plt.subplots(figsize=figsize or figure_size("profile"), layout="constrained")


def _count_no_estimate(df: pd.DataFrame, blank: np.ndarray, notes: Notes) -> np.ndarray:
    """Count blank estimates by ``correlation_note``; return the rows counted.

    A correlation's result says why each blank estimate is blank, so the
    footnote gives the reasons ("refusal", "above range") instead of one
    count of blank values. Other blank rows are left to the caller.
    """
    counted = np.zeros(len(df), dtype=bool)
    if "correlation_note" not in df.columns:
        return counted
    reasons = df["correlation_note"].to_numpy(dtype=object)
    for reason in CORRELATION_REASONS:
        rows = blank & (reasons == reason)
        notes.count(rows, f"correlation_{reason.replace(' ', '_')}")
        counted |= rows
    return counted


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
    legend: Literal["auto", "inside", "bottom", "right"] | bool = "auto",
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes]:
    """Plot a property against depth or elevation (P01).

    Points are colored by geology unit. Nothing is dropped silently: blanks,
    values ≤ 0 on a log axis and values beyond fixed limits are counted in a
    footnote, and the counts are in ``ax.ags_notes``.

    Text in the value column is drawn at the left edge at its depth, one
    marker shape per text, and counted: ``NP`` and ``refusal`` (any case) as
    flags, any other text (``dry``) with a warning so you can clean it.
    ``ht.read_csv`` reads ``n/a``, ``NA`` and ``null`` as blanks, so those are
    counted as blank, not as text.

    A value reported as a range, such as a correlation's band, is drawn from
    the columns ``<value>_lower`` and ``<value>_upper`` when ``df`` has either:
    a bar between the two bounds at the row's depth, with the marker where
    ``<value>`` isn't blank, or a caret at a bound given alone (▷ at a lower
    bound, ◁ at an upper). Where two or more ``color_by`` groups have a range
    at one depth, such as two correlations' bands for one test, their bars
    are drawn a little apart up and down the page so neither hides the other.
    The rows are counted in the footnote and left out of the stats box.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per observation: the ``value`` column, plus ``depth`` or
        ``elevation`` (or ``depth`` and ``ground_level``). See
        ``ht.template("profile")``.
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
    marker_by : str, optional
        Column whose groups get different marker shapes, e.g. ``"source"``
        for lab and field tests.
    connect : bool
        Join each hole's points (by ``loca_id``) with a thin gray line.
    intervals : {"auto", True, False}
        Draw each test's interval, ``depth_top`` to ``depth_base``, as a
        vertical bar. ``"auto"`` draws them when both columns exist.
    xlim, ylim : (low, high), optional
        Fixed limits in display units. Values beyond them are drawn at the
        edge with an arrow, and counted.
    xaxis_position : {"bottom", "top"}
        ``"top"`` puts the value axis at the top, as on a borehole log.
    secondary : {"depth"}, optional
        Add a depth axis to an elevation plot. Needs one ground level for
        all rows.
    strata : pandas.DataFrame, optional
        Geology bands across the plot: ``geology_unit`` with a depth or
        elevation top and base. See ``ht.template("strata")``.
    water_level : float, list of (value, label), or pandas.DataFrame, optional
        A water level line, several labeled ones, or a table of
        ``loca_id`` and depth or elevation for a level per hole.
    ranges : pandas.DataFrame or path, optional
        Published ranges as bands: ``low``, ``high``, ``label``, and an
        optional depth or elevation pair. See ``ht.template("ranges")``.
    design_lines : pandas.DataFrame, optional
        Design lines: ``label``, depth or elevation, and ``value``, one line
        per label. See ``ht.template("design_lines")``.
    reference_lines : list of (value, label), optional
        Vertical lines at fixed values, such as a code limit. A string such
        as ``"2000 psf"`` carries its own unit.
    stats_box : bool or list of str
        A box of statistics at the lower left: True for count, mean, std,
        median, min and max per unit, or a list chosen from those and
        ``"cov"``.
    stats_box_room : bool
        Deepen the vertical axis so the stats box sits below the lowest
        data instead of covering it. Ignored with ``ylim=``.
    note : str, optional
        Free text, added to the footnote.
    palette : dict, optional
        ``{geology unit: color}`` for this plot.
    units : dict, optional
        ``{column: unit}``, overriding the units declared on ``df``.
    display_units : {"US", "SI"}, optional
        Defaults to ``ht.settings.display_units``.
    legend : {"auto", "inside", "bottom", "right"} or bool
        Where the legend goes. ``"auto"`` (the default, or True): inside
        the axes, in the first corner clear of data (upper right, upper left,
        lower right, lower left), else below the x label. ``"inside"``: a
        corner even when none is clear, the one covering least. ``"bottom"``:
        below the x label. ``"right"``: outside on the right. False: no
        legend; the footnote still gives every count. With ``ax=``, the
        corner is chosen for the axes as they are when plotted: pass
        ``"bottom"`` or ``"right"`` if the figure is resized afterwards.
    figsize : (width, height), optional
        Inches, the whole figure; by default the settings ``profile`` size.
        Ignored with ``ax=``.
    ax : matplotlib Axes, optional
        Draw into this axes, e.g. a ``Sheet`` panel.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, ax

    Examples
    --------
    >>> k = ht.read_csv("perm.csv", units={"depth": "ft", "ground_level": "ft",
    ...                                    "hydraulic_conductivity": "cm/s"})
    >>> fig, ax = ht.plot.profile(k, "hydraulic_conductivity",
    ...                           preset="hydraulic_conductivity")
    """
    return _draw_profile(
        df,
        value,
        vs=vs,
        preset=preset,
        log=log,
        label=label,
        color_by=color_by,
        marker_by=marker_by,
        connect=connect,
        intervals=intervals,
        xlim=xlim,
        ylim=ylim,
        xaxis_position=xaxis_position,
        secondary=secondary,
        strata=strata,
        water_level=water_level,
        ranges=ranges,
        design_lines=design_lines,
        reference_lines=reference_lines,
        stats_box=stats_box,
        stats_box_room=stats_box_room,
        note=note,
        palette=palette,
        units=units,
        display_units=display_units,
        legend=legend,
        figsize=figsize,
        ax=ax,
        value_ranges=True,
        **style_overrides,
    )


def _draw_profile(
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
    legend: Literal["auto", "inside", "bottom", "right"] | bool = "auto",
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    flags: np.ndarray | None = None,
    flag_kinds: Mapping[str, _values.Flag] = _values.QUALIFIERS,
    clear_of: float | None = None,
    extra_hints: Mapping[str, str] | None = None,
    notes: Notes | None = None,
    companion: Companion | None = None,
    value_ranges: bool = False,
    **style_overrides: Any,
) -> tuple[Figure, Axes]:
    """Draw a profile: ``profile()`` and the plots built on it (P02).

    The arguments are ``profile()``'s, plus:

    - ``flags``: each row's key into ``flag_kinds``, or ``""``. None reads the
      ``qualifier`` column (P01).
    - ``flag_kinds``: ``{key: Flag}``, how each flag is drawn and counted.
    - ``clear_of``: a value the x-axis upper limit stays clear of, so markers
      drawn there aren't on the frame (P02 refusals at the cap).
    - ``extra_hints``: ``{column: what is lost without it}`` for columns the
      caller found missing (P02 checks its input before the analysis adds
      columns). They join the one optional-column hint.
    - ``notes``: footnote counts and text the caller has already collected,
      e.g. rows it left out (P02 excluded refusals). None starts empty.
    - ``companion``: marks the caller draws per row (P06), as ``Companion``.
    - ``value_ranges``: draw ``<value>_lower`` and ``<value>_upper`` (P01 only).
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
        raise HangtuError(
            f'xaxis_position must be "top" or "bottom", not {xaxis_position!r}.'
        )
    if secondary not in (None, "depth"):
        raise HangtuError(f'secondary must be "depth" or None, not {secondary!r}.')
    statistics = statistics_list(stats_box) if stats_box is not False else None
    where = check_legend(legend)

    system = _display_units(display_units or settings.display_units)
    chosen = _presets.preset(preset) if preset is not None else None
    quantity = _values.quantity_of(value, chosen)
    log = chosen.log if log is None and chosen is not None else bool(log)
    xlim = _values.check_limits("xlim", xlim, log) if xlim is not None else None
    ylim = _values.check_limits("ylim", ylim) if ylim is not None else None
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
        hint_missing(df, optional, extra_hints)

        resolved = _units.resolve_units(
            df,
            [value, *length_columns(df)],
            units,
            quantities={value: quantity} if quantity else None,
        )
        raw, texts = text_values(df, value)
        x, x_unit_text = _units.to_display(raw, resolved[value], quantity, system)
        y, vertical = vertical_values(df, vs, resolved, system)
        if secondary == "depth":
            check_secondary_depth(vertical)
        if flags is None:
            flags = _values.qualifiers(df)
        qualified_text = (texts != "") & (flags != "")
        if qualified_text.any():
            found = ", ".join(map(repr, dict.fromkeys(texts[qualified_text])))
            raise ColumnError(
                f"Rows {rows_text(df.index[qualified_text])} have a qualifier and "
                f"text in {value!r} ({found}). A qualifier needs a number: put the "
                f"number in {value!r}, or clear 'qualifier' on those rows."
            )
        _text_values.warn_unrecognized(df.index, value, texts)
        bounds = _intervals(df, intervals, resolved, vertical)
        ranges_read = (
            _value_ranges.read(df, value, units, quantity, system)
            if value_ranges
            else None
        )
        ranged = np.zeros(len(df), dtype=bool)
        if ranges_read is not None:
            _value_ranges.check_qualifiers(df, value, ranges_read, flags)
            ranged = ranges_read.any()

        notes = Notes() if notes is None else notes
        extra = ranged & ~np.isnan(y)
        if companion is not None:
            extra |= companion.rows & ~np.isnan(y)
        notes.count(extra & ranged, "value_range")
        blank = (np.isnan(x) & (texts == "") & ~extra) | np.isnan(y)
        notes.count(blank & ~_count_no_estimate(df, blank & ~np.isnan(y), notes), "nan")
        texts = np.where(blank, "", texts)
        drawn = ~blank & (texts == "") & ~np.isnan(x)
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

        covered = x[drawn] if companion is None else np.append(x[drawn], companion.x)
        if ranges_read is not None:
            covered = np.append(covered, ranges_read.x(log))
        limits = _values.value_limits(
            covered,
            log=log,
            xlim=xlim,
            start_at_zero=_values.start_at_zero(value, chosen),
            typical=_values.typical_range(chosen, resolved[value], system),
        )
        if clear_of is not None and xlim is None and not log:
            # Leave room beyond clear_of so markers there aren't on the frame.
            clear = nice_limits(
                limits[0],
                CLEAR_FACTOR * clear_of,
                start_at_zero=limits[0] >= 0,
                clear=False,
            )[1]
            limits = (limits[0], max(limits[1], clear))
        if log:
            set_log_axis(ax, "x", limits)
        else:
            set_linear_axis(ax, "x", limits)
        heights = np.concatenate(
            [y[drawn | (texts != "") | extra], top[bars], base[bars]]
        )
        _set_vertical_axis(ax, vs, heights, ylim)
        if xaxis_position == "top":
            ax.xaxis.tick_top()
            ax.xaxis.set_label_position("top")

        if strata is not None:
            draw_strata(ax, strata, vertical, palette, df.attrs.get("palette"))
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

        groups, colors = _values.color_groups(df, color_by, palette)
        marker_groups, shapes = _marker_groups(df, marker_by)
        flag_markers = {f"flag {key}": kind for key, kind in flag_kinds.items()}
        markers = np.array(
            [
                f"flag {key}"
                if key in flag_kinds
                else shapes.get(group, MARKER_CYCLE[0])
                for key, group in zip(flags, marker_groups, strict=True)
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
                ax,
                x,
                y,
                rows,
                markers,
                color,
                str(group),
                {"x": xlim, "y": ylim},
                flag_markers,
            )
            edge |= group_edge
            these = bars & rows & ~group_edge
            _draw_intervals(ax, x[these], top[these], base[these], color)
            others = (texts != "") | extra
            if group is not None and (rows | (others & (groups == group))).any():
                # A group drawn only as ranges has no marker to show: a bar.
                only_ranges = not (rows | ((texts != "") & (groups == group))).any()
                text = _values.group_text(group)
                if shapes:
                    handle = Patch(facecolor=color, edgecolor="none", label=text)
                elif only_ranges:
                    handle = _value_ranges.legend_bar(color, text)
                else:
                    handle = _values.legend_marker("o", color, text, MARKER_SIZE)
                unit_handles.append(handle)
        text_handles, text_edge = _text_values.draw_text_values(
            ax, y, texts, groups, colors, ylim, notes
        )
        companion_handles = []
        if companion is not None:
            companion_handles, companion_edge = companion.draw(
                ax, y, groups, colors, notes
            )
            edge |= companion_edge
        if ranges_read is not None:
            range_handles, range_edge = _value_ranges.draw(
                ax, ranges_read, y, extra & ranged, groups, colors, ylim
            )
            companion_handles += range_handles
            edge |= range_edge
        notes.count(edge | text_edge, "beyond_limit")
        shape_handles = [
            _values.legend_marker(
                shape, _values.NEUTRAL, _values.group_text(group), MARKER_SIZE
            )
            for group, shape in shapes.items()
            if (drawn & (marker_groups == group)).any()
        ]
        flagged = _values.flag_handles(np.where(drawn, flags, ""), flag_kinds, notes)

        if not (drawn | (texts != "") | extra).any():
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
                _values.axis_text(value, label, chosen),
                x_unit_text,
                unknown=resolved[value] is None and _units.needs_units(value, quantity),
            )
        )
        ax.set_ylabel(vertical.label())
        if statistics is not None:
            info = column_info(value)
            counted = drawn & ~ranged
            rows = stats_table(
                x[counted],
                groups[counted],
                statistics,
                order=list(colors),
                interval=bool(info) and info.get("scale") == "interval",
            )
            also = [_text_values.also_line(texts)]
            if (extra & ranged).any():
                also.append(f"Ranges not included: {int((extra & ranged).sum())}")
            box = draw_stats_box(
                ax,
                rows,
                None if note is None else str(note),
                "\n".join(line for line in also if line) or None,
            )
            if stats_box_room and ylim is None and heights.size:
                lowest = heights.max() if vs == "depth" else heights.min()
                _room_below_data(ax, box, float(lowest))
        if secondary == "depth":
            add_secondary_depth(ax, vertical)
        offset = SECONDARY_SPACE if secondary else 0.0
        placed = add_legend(
            ax,
            [unit_handles, companion_handles, shape_handles, flagged, text_handles],
            notes,
            offset,
            where,
        )
        notes.render(ax, offset, placed.where, placed.legend)
    return fig, ax
