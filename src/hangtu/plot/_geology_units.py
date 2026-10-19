"""P07 property by geology unit (docs/plots/P07-geology-unit-comparison.md)."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from numbers import Real
from typing import Any, Literal

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import NullLocator
from matplotlib.transforms import blended_transform_factory

from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu._settings import _display_units, settings
from hangtu.errors import ColumnError, HangtuError
from hangtu.plot import _layers, _presets, _values, style
from hangtu.plot._baseline import Baseline, legend_text, read_baseline
from hangtu.plot._labels import axis_label
from hangtu.plot._legend import add_legend
from hangtu.plot._limits import set_linear_axis, set_log_axis
from hangtu.plot._notes import ARROW_LENGTH, Notes, edge_markers
from hangtu.plot._overlays import ValueScale, draw_note, draw_reference_lines
from hangtu.plot._palette import data_order, resolve_palette
from hangtu.plot._presets import Preset

POINT_SIZE = 3.0  # points
POINT_ALPHA = 0.4
CARET_SIZE = 5.0  # points
# Values that don't exist for a non-plastic (NP) specimen (P07 §3).
ATTERBERG = {
    "liquid_limit",
    "plastic_limit",
    "plasticity_index",
    "liquidity_index",
    "consistency_index",
}
JITTER = 0.15  # row heights either side of the center line (P07 §7)
JITTER_SEED = 0  # the same data always gives the same figure (plan decision 4)
BAR_WIDTH = 2.0  # points
CAP_HEIGHT = 0.16  # row heights
CENTRAL_SIZE = 6.0  # points
CENTRAL_EDGE = 0.8  # points, white
BOX_HEIGHT = 0.3  # row heights
BOX_WIDTH = 1.0  # points
BOX_FILL = (1.0, 1.0, 1.0, 0.6)
WHISKER_REACH = 1.5  # times the IQR (Tukey 1977)
COUNT_SIZE = 7  # points
COUNT_GAP = 4.0  # points between the axes and a count label
EDGE_GAP = ARROW_LENGTH + 4.0  # more, to clear an edge marker's arrow on the right
LEGEND_GAP = 6.0  # points between the count labels and the legend
EMPTY_COLOR = "0.4"
BASELINE_COLOR = "0.25"
BASELINE_OFFSET = 0.28  # row heights above the center line
BASELINE_WIDTH = 1.2  # points
BASELINE_CAP_HEIGHT = 0.12  # row heights
BASELINE_MARKER_SIZE = 5.0  # points
# numpy.percentile(method=...) choices; NumPy has no public list (plan decision 6).
PERCENTILE_METHODS = (
    "inverted_cdf",
    "averaged_inverted_cdf",
    "closest_observation",
    "interpolated_inverted_cdf",
    "hazen",
    "weibull",
    "linear",
    "median_unbiased",
    "normal_unbiased",
    "lower",
    "higher",
    "midpoint",
    "nearest",
)


@dataclass(frozen=True)
class _Summary:
    """How each unit's values are summarized (P07 §4)."""

    kind: Literal["percentiles", "box"] | None
    percentiles: tuple[float, float, float]
    method: str
    min_count: int

    def legend_text(self) -> str:
        """Return the legend text for the summary mark, e.g. "Data p10-p90, p50"."""
        if self.kind == "box":
            text = "Data: quartiles, median, 1.5 IQR whiskers"
        else:
            low, mid, high = (f"p{p:g}" for p in self.percentiles)
            text = f"Data {low}\N{EN DASH}{high}, {mid}"
        if self.method != "linear":
            text += f" ({self.method.replace('_', ' ').capitalize()})"
        return text


@dataclass
class _Panel:
    """What one panel drew, for the legend and footnote around it."""

    handles: list[Artist] = field(default_factory=list)
    notes: Notes = field(default_factory=Notes)
    counts: list[Artist] = field(default_factory=list)
    baseline: Baseline | None = None
    flags: list[Artist] = field(default_factory=list)  # qualifier entries
    title: str = ""  # the value axis text without units, for grid footnotes


def _choose_preset(value: str, preset: str | None) -> Preset | None:
    """Return the preset given, else the one named after the value column (P07 §6)."""
    if preset is not None:
        return _presets.preset(preset)
    if value in _presets.preset_names():
        return _presets.preset(value)
    return None


def _check_columns(df: pd.DataFrame, value: str, color_by: str | None) -> None:
    available = ", ".join(map(str, df.columns)) or "none"
    for column in (value, "geology_unit"):
        if column not in df.columns:
            raise ColumnError(
                f"Column {column!r} not found. Available columns: {available}. "
                + (
                    "This plot groups values by geology unit, so it needs a "
                    "'geology_unit' column."
                    if column == "geology_unit"
                    else ""
                )
            )
    if color_by not in ("geology_unit", None):
        raise HangtuError(
            f'color_by must be "geology_unit" or None, not {color_by!r}. Rows are '
            "always geology units; color_by=None draws them in one neutral color."
        )


def _check_summary(
    summary: Any,
    percentiles: Any,
    percentile_method: Any,
    summary_min_count: Any,
) -> _Summary:
    if summary not in ("percentiles", "box", None):
        raise HangtuError(
            f'summary must be "percentiles", "box" or None, not {summary!r}.'
        )
    ok = (
        isinstance(percentiles, Sequence)
        and not isinstance(percentiles, str)
        and len(percentiles) == 3
        and all(isinstance(p, Real) and not isinstance(p, bool) for p in percentiles)
        and 0 <= percentiles[0] < percentiles[1] < percentiles[2] <= 100
    )
    if not ok:
        raise HangtuError(
            "percentiles must be three ascending numbers from 0 to 100: the bar's "
            f"low end, its center marker and its high end, not {percentiles!r}. "
            "Example: percentiles=(10, 50, 90)"
        )
    if percentile_method not in PERCENTILE_METHODS:
        raise HangtuError(
            f"percentile_method={percentile_method!r} isn't one of NumPy's "
            f"percentile methods: {', '.join(PERCENTILE_METHODS)}. "
            'Example: percentile_method="hazen"'
        )
    if summary_min_count is None:
        summary_min_count = settings.summary_min_count
    elif (
        not isinstance(summary_min_count, int)
        or isinstance(summary_min_count, bool)
        or summary_min_count < 1
    ):
        raise HangtuError(
            "summary_min_count must be a whole number of at least 1, not "
            f"{summary_min_count!r}. Example: summary_min_count=5"
        )
    low, mid, high = (float(p) for p in percentiles)
    return _Summary(summary, (low, mid, high), percentile_method, summary_min_count)


def _rows(
    df: pd.DataFrame,
    order: list[str] | None,
    palette: dict[str, str] | None,
    extra: list[Any],
) -> tuple[np.ndarray, dict[Any, Any]]:
    """Return each row's geology unit, and ``{unit: color}`` in row order.

    ``extra`` are units with a baseline but perhaps no data. Units in
    ``order`` come first, then the rest by name, then "(blank)".
    """
    groups = df["geology_unit"].to_numpy(dtype=object)
    blank = pd.isna(groups)
    colors = resolve_palette(
        [*groups[~blank], *extra],
        palette,
        order or data_order(df["geology_unit"]),
        df.attrs.get("palette"),
    )
    if blank.any():
        groups = np.where(blank, _values.BLANK_GROUP, groups)
        colors[_values.BLANK_GROUP] = _values.NEUTRAL
    return groups, colors


def _non_plastic(df: pd.DataFrame, value: str) -> np.ndarray:
    """Return True for rows reported non-plastic (NP), for Atterberg values.

    Other values of an NP specimen, such as its water content, still count.
    """
    if value not in ATTERBERG or "non_plastic" not in df.columns:
        return np.zeros(len(df), dtype=bool)
    flags = df["non_plastic"]
    known = flags.isna() | flags.isin([True, False])
    if not known.all():
        raise ColumnError(
            f"Column 'non_plastic' must hold True, False or nothing, but rows "
            f"{rows_text(df.index[~known])} hold something else. Mark NP "
            "specimens True and leave their value blank."
        )
    return flags.eq(True).to_numpy(dtype=bool)


def _set_unit_axis(ax: Axes, names: list[Any]) -> None:
    """One row per unit, first at the top, with no gridlines between them."""
    n = max(len(names), 1)
    ax.set_yticks(range(len(names)), [str(name) for name in names])
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_ylim(n - 0.5, -0.5)
    ax.grid(False, axis="y", which="both")


def _caps(
    ax: Axes,
    xs: Sequence[float],
    row: float,
    color: Any,
    width: float,
    height: float = CAP_HEIGHT,
    zorder: float = _layers.SUMMARY,
) -> None:
    """Draw short vertical end caps at ``xs`` on a row."""
    half = height / 2
    gaps = [np.nan] * len(xs)
    ax.plot(
        np.column_stack([xs, xs, gaps]).ravel(),
        np.column_stack([[row - half] * len(xs), [row + half] * len(xs), gaps]).ravel(),
        color=color,
        linewidth=width,
        solid_capstyle="butt",
        zorder=zorder,
    )


def _central(ax: Axes, x: float, row: float, color: Any) -> None:
    ax.plot(
        [x],
        [row],
        marker="o",
        markersize=CENTRAL_SIZE,
        markerfacecolor=color,
        markeredgecolor="white",
        markeredgewidth=CENTRAL_EDGE,
        linestyle="none",
        zorder=_layers.CENTRAL,
    )


def _draw_percentiles(
    ax: Axes, values: np.ndarray, row: float, color: Any, summary: _Summary
) -> None:
    """Draw the bar from the first to the third percentile, circle at the second."""
    low, mid, high = np.percentile(values, summary.percentiles, method=summary.method)
    ax.plot(
        [low, high],
        [row, row],
        color=color,
        linewidth=BAR_WIDTH,
        solid_capstyle="butt",
        zorder=_layers.SUMMARY,
    )
    _caps(ax, [low, high], row, color, BAR_WIDTH)
    _central(ax, mid, row, color)


def _draw_box(
    ax: Axes, values: np.ndarray, row: float, color: Any, summary: _Summary
) -> None:
    """Draw a box from the quartiles, the median, and 1.5 IQR whiskers.

    Drawn with a patch and lines, not ``ax.bxp``, whose arguments changed in
    matplotlib 3.10 (plan decision 5). No outlier marks: every point is drawn.
    """
    q1, median, q3 = np.percentile(values, (25, 50, 75), method=summary.method)
    reach = WHISKER_REACH * (q3 - q1)
    low = values[values >= q1 - reach].min()
    high = values[values <= q3 + reach].max()
    half = BOX_HEIGHT / 2
    ax.add_patch(
        Rectangle(
            (q1, row - half),
            q3 - q1,
            BOX_HEIGHT,
            facecolor=BOX_FILL,
            edgecolor=color,
            linewidth=BOX_WIDTH,
            zorder=_layers.SUMMARY,
        )
    )
    ax.plot(
        [median, median],
        [row - half, row + half],
        color=color,
        linewidth=BAR_WIDTH,
        solid_capstyle="butt",
        zorder=_layers.CENTRAL,
    )
    ax.plot(
        [low, q1, np.nan, q3, high],
        [row, row, np.nan, row, row],
        color=color,
        linewidth=BOX_WIDTH,
        zorder=_layers.SUMMARY,
    )
    _caps(ax, [low, high], row, color, BOX_WIDTH)


def _draw_points(
    ax: Axes,
    x: np.ndarray,
    y: np.ndarray,
    rows: np.ndarray,
    qualifiers: np.ndarray,
    carets: dict[str, str],
    color: Any,
    unit: Any,
    xlim: tuple[float, float] | None,
) -> np.ndarray:
    """Draw one unit's points, with carets for qualified values.

    Values beyond ``xlim`` are drawn at the edge instead. Returns the mask of
    rows drawn at the edge.
    """
    edge = np.zeros(len(x), dtype=bool)
    for qualifier in ("", *carets):
        these = rows & (qualifiers == qualifier)
        if not these.any():
            continue
        marker = carets.get(qualifier, "o")
        if xlim is not None:
            edge[these] = edge_markers(
                ax, x[these], y[these], {"x": xlim}, color, marker
            )
        inside = these & ~edge
        ax.scatter(
            x[inside],
            y[inside],
            s=(CARET_SIZE if qualifier else POINT_SIZE) ** 2,
            marker=marker,
            color=color,
            alpha=1.0 if qualifier else POINT_ALPHA,
            linewidths=0,
            label=f"_{unit}" if not qualifier else f"_{unit} {marker}",
            zorder=_layers.QUALIFIERS if qualifier else _layers.MARKERS,
        )
    return edge


def _draw_baseline(
    ax: Axes, baseline: Baseline, row_of: dict[Any, int], log: bool
) -> None:
    """Draw each unit's baseline bar above its row, with a diamond at ``central``.

    On a log axis a ``low`` at or below 0 starts the bar at the axis edge.
    """
    left = ax.get_xlim()[0]
    for unit, low, central, high in zip(
        baseline.units, baseline.low, baseline.central, baseline.high, strict=True
    ):
        y = row_of[unit] - BASELINE_OFFSET
        if np.isfinite(low):
            if log and low <= 0:
                low = left
            ax.plot(
                [low, high],
                [y, y],
                color=BASELINE_COLOR,
                linewidth=BASELINE_WIDTH,
                solid_capstyle="butt",
                zorder=_layers.BASELINE,
            )
            _caps(
                ax,
                [low, high],
                y,
                BASELINE_COLOR,
                BASELINE_WIDTH,
                BASELINE_CAP_HEIGHT,
                _layers.BASELINE,
            )
        if np.isfinite(central) and not (log and central <= 0):
            ax.plot(
                [central],
                [y],
                marker="D",
                markersize=BASELINE_MARKER_SIZE,
                color=BASELINE_COLOR,
                linestyle="none",
                zorder=_layers.BASELINE,
            )


def _baseline_handle(label: str) -> Artist:
    return Line2D(
        [],
        [],
        color=BASELINE_COLOR,
        linewidth=BASELINE_WIDTH,
        marker="D",
        markersize=BASELINE_MARKER_SIZE,
        label=label,
    )


def _count_label(
    ax: Axes, row: float, n: int, summarized: bool | None, gap: float
) -> Artist:
    """Write "n = 288" just outside the right edge of the axes, level with a row.

    ``summarized`` is False when a summary was asked for but n is too small.
    """
    text = f"n = {n}" + (" (no summary)" if n and summarized is False else "")
    return ax.annotate(
        text,
        xy=(1.0, row),
        xycoords=blended_transform_factory(ax.transAxes, ax.transData),
        xytext=(gap, 0.0),
        textcoords="offset points",
        ha="left",
        va="center",
        fontsize=COUNT_SIZE,
        color=EMPTY_COLOR if n == 0 else "black",
        annotation_clip=False,
        zorder=_layers.ANNOTATIONS,
    )


def _summary_handle(summary: _Summary) -> Artist:
    text = summary.legend_text()
    if summary.kind == "box":
        return Rectangle(
            (0, 0),
            1,
            1,
            facecolor=BOX_FILL,
            edgecolor=_values.NEUTRAL,
            linewidth=BOX_WIDTH,
            label=text,
        )
    return Line2D(
        [],
        [],
        color=_values.NEUTRAL,
        linewidth=BAR_WIDTH,
        marker="o",
        markersize=CENTRAL_SIZE,
        markerfacecolor=_values.NEUTRAL,
        markeredgecolor="white",
        markeredgewidth=CENTRAL_EDGE,
        label=text,
    )


def _legend_offset(ax: Axes, counts: Sequence[Artist]) -> float:
    """Return the space in points the legend needs to clear the count labels."""
    if not counts:
        return 0.0
    figure = ax.figure
    figure.draw_without_rendering()
    renderer = figure.canvas.get_renderer()
    right = ax.get_window_extent(renderer).x1
    reach = max(label.get_window_extent(renderer).x1 for label in counts) - right
    return reach * 72.0 / figure.dpi + LEGEND_GAP


def _draw_panel(
    ax: Axes,
    df: pd.DataFrame,
    value: str,
    *,
    preset: str | None,
    log: bool | None,
    label: str | None,
    xlim: tuple[float, float] | None,
    order: list[str] | None,
    color_by: str | None,
    points: bool,
    summary: _Summary,
    baseline: pd.DataFrame | str | None,
    baseline_units: dict[str, str] | None,
    reference_lines: list[tuple[float, str]] | None,
    note: str | None,
    palette: dict[str, str] | None,
    units: dict[str, str] | None,
    system: str,
) -> _Panel:
    """Draw one property by geology unit into ``ax``."""
    panel = _Panel()
    chosen = _choose_preset(value, preset)
    quantity = _values.quantity_of(value, chosen)
    log = chosen.log if log is None and chosen is not None else bool(log)
    xlim = _values.check_limits("xlim", xlim, log) if xlim is not None else None

    resolved = _units.resolve_units(
        df, [value], units, quantities={value: quantity} if quantity else None
    )
    x, x_unit_text = _units.to_display(
        numeric_column(df, value), resolved[value], quantity, system
    )
    qualifiers = _values.qualifiers(df)
    non_plastic = _non_plastic(df, value)
    panel.notes.count(non_plastic, "non_plastic")
    # Blank values are tests not done, so they are skipped, not counted (P07 §14).
    drawn = ~np.isnan(x) & ~non_plastic
    if log:
        nonpositive = drawn & (x <= 0)
        panel.notes.count(nonpositive, "log_nonpositive")
        drawn &= ~nonpositive
    scale = ValueScale(resolved[value], quantity, system, log)
    if baseline is not None:
        panel.baseline = read_baseline(baseline, value, scale, baseline_units)
    groups, colors = _rows(
        df[drawn], order, palette, panel.baseline.units if panel.baseline else []
    )
    rows = list(colors)
    unit_of = np.full(len(df), None, dtype=object)
    unit_of[drawn] = groups
    row_of = {unit: i for i, unit in enumerate(rows)}
    jitter = np.random.default_rng(JITTER_SEED).uniform(-JITTER, JITTER, len(df))

    style.style_axes(ax)
    extent = x[drawn]
    if panel.baseline is not None:
        extent = np.concatenate([extent, panel.baseline.values()])
        if log:
            extent = extent[extent > 0]
    limits = _values.value_limits(
        extent,
        log=log,
        xlim=xlim,
        start_at_zero=_values.start_at_zero(value, chosen),
        typical=_values.typical_range(chosen, resolved[value], system),
    )
    if log:
        set_log_axis(ax, "x", limits)
    else:
        set_linear_axis(ax, "x", limits)
    _set_unit_axis(ax, rows)
    if panel.baseline is not None:
        _draw_baseline(ax, panel.baseline, row_of, log)

    draw_summary = {"percentiles": _draw_percentiles, "box": _draw_box}.get(
        summary.kind
    )
    summarized_any = False
    carets = {q: marker for q, (marker, *_) in _values.QUALIFIERS.items()}
    right_edge = points and xlim is not None and bool((x[drawn] > xlim[1]).any())
    gap = COUNT_GAP + (EDGE_GAP if right_edge else 0.0)
    if points and xlim is not None and (x[drawn] < xlim[0]).any():
        # Clear the edge arrows on the left, so they don't cover the unit names.
        ax.yaxis.set_tick_params(pad=mpl.rcParams["ytick.major.pad"] + EDGE_GAP)
    edge = np.zeros(len(df), dtype=bool)
    for unit, color in colors.items():
        these = drawn & (unit_of == unit)
        color = _values.NEUTRAL if color_by is None else color
        row = row_of[unit]
        if points and these.any():
            edge |= _draw_points(
                ax, x, row + jitter, these, qualifiers, carets, color, unit, xlim
            )
        n = int(these.sum())
        summarized = None if draw_summary is None else n >= summary.min_count
        if summarized:
            draw_summary(ax, x[these], row, color, summary)
            summarized_any = True
        panel.counts.append(_count_label(ax, row, n, summarized, gap))
    panel.notes.count(edge, "beyond_limit")
    if summarized_any:
        panel.handles.append(_summary_handle(summary))
    if points and drawn.any():
        panel.handles.append(
            _values.legend_marker("o", _values.NEUTRAL, "Data", POINT_SIZE)
        )
    panel.flags = _values.qualifier_handles(
        np.where(drawn, qualifiers, ""), panel.notes
    )
    if reference_lines is not None:
        draw_reference_lines(ax, reference_lines, scale)
    if note is not None:
        draw_note(ax, str(note))

    if not rows:
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
    panel.title = _values.axis_text(value, label, chosen)
    ax.set_xlabel(
        axis_label(
            panel.title,
            x_unit_text,
            unknown=resolved[value] is None and _units.needs_units(value, quantity),
        )
    )
    return panel


def _new_axes(figsize: tuple[float, float] | None) -> tuple[Figure, Axes]:
    return plt.subplots(
        figsize=figsize or settings.figure_sizes["default"], layout="constrained"
    )


def geology_unit_comparison(
    df: pd.DataFrame,
    value: str,
    *,
    baseline: pd.DataFrame | str | None = None,
    baseline_label: str | None = None,
    baseline_units: dict[str, str] | None = None,
    summary: Literal["percentiles", "box"] | None = "percentiles",
    percentiles: tuple[float, float, float] = (10, 50, 90),
    percentile_method: str = "linear",
    summary_min_count: int | None = None,
    points: bool = True,
    preset: str | None = None,
    log: bool | None = None,
    label: str | None = None,
    xlim: tuple[float, float] | None = None,
    order: list[str] | None = None,
    color_by: Literal["geology_unit"] | None = "geology_unit",
    reference_lines: list[tuple[float, str]] | None = None,
    note: str | None = None,
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes]:
    """Compare a property's values by geology unit with a report's ranges (P07).

    Each geology unit is a row: its values as jittered points, a summary bar,
    and the report's baseline range above it. Nothing is dropped silently:
    values ≤ 0 on a log axis, values beyond fixed limits and flagged values
    are counted in a footnote, and the counts are in ``ax.ags_notes``.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per observation, with the ``value`` column and
        ``geology_unit``.
    value : str
        The column to compare.
    baseline : DataFrame or path, optional
        The report's range per geology unit: ``geology_unit``, ``low``,
        ``high``, and optionally ``central``, ``property`` and ``source``.
        See ``ht.template("baseline")``.
    baseline_label : str, optional
        The baseline's legend text, saying what the report's range is, e.g.
        ``"GBR baseline p10-p90, p50"``. By default the table's source.
    baseline_units : dict, optional
        ``{property: unit}`` for the baseline's ranges, e.g.
        ``{"undrained_shear_strength": "kPa"}``. By default the units declared
        on the table, else the value column's units, with a warning.
    summary : {"percentiles", "box", None}
        Each unit's summary: a percentile bar, a box plot, or none.
    percentiles : (low, center, high)
        The bar's ends and center marker, as percentiles from 0 to 100.
    percentile_method : str
        Passed to ``numpy.percentile(method=...)``, e.g. ``"hazen"``.
    summary_min_count : int, optional
        The fewest values a unit needs for a summary. By default
        ``ht.settings.summary_min_count`` (5).
    points : bool
        Draw every value as a point.
    preset : str, optional
        By default the preset named after ``value``, if there is one.
    log : bool, optional
        Use a log value axis. By default from the preset, else linear.
    label : str, optional
        The value axis text; units are added automatically.
    xlim : (low, high), optional
        Fixed value axis limits in display units.
    order : list of str, optional
        Geology units in stratigraphic order, top first. Other units follow,
        sorted by name.
    color_by : {"geology_unit", None}
        None draws every unit in one neutral color.
    palette : dict, optional
        ``{geology unit: color}`` for this plot.
    units : dict, optional
        ``{column: unit}``, overriding the units declared on ``df``.
    display_units : {"US", "SI"}, optional
        Defaults to ``ht.settings.display_units``.
    figsize : (width, height), optional
        Inches; by default the settings ``default`` size. Ignored with ``ax=``.
    ax : matplotlib Axes, optional
        Draw into this axes, e.g. a ``Sheet`` panel.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, ax

    Examples
    --------
    >>> index = ht.read_csv("index.csv", units={"bulk_unit_weight": "pcf"})
    >>> fig, ax = ht.plot.geology_unit_comparison(
    ...     index, "bulk_unit_weight", order=["Fill", "Alluvium", "Till"])
    """
    _check_columns(df, value, color_by)
    chosen_summary = _check_summary(
        summary, percentiles, percentile_method, summary_min_count
    )
    system = _display_units(display_units or settings.display_units)

    with style.context(**style_overrides):
        if ax is None:
            fig, ax = _new_axes(figsize)
        else:
            fig = ax.figure
        panel = _draw_panel(
            ax,
            df,
            value,
            preset=preset,
            log=log,
            label=label,
            xlim=xlim,
            order=order,
            color_by=color_by,
            points=points,
            summary=chosen_summary,
            baseline=baseline,
            baseline_units=baseline_units,
            reference_lines=reference_lines,
            note=note,
            palette=palette,
            units=units,
            system=system,
        )
        handles = [*panel.handles, *panel.flags]
        if panel.baseline is not None and panel.baseline.units:
            text = legend_text(baseline_label, [panel.baseline])
            handles = [_baseline_handle(text), *handles]
        offset = _legend_offset(ax, panel.counts)
        add_legend(ax, [handles], panel.notes, offset)
        panel.notes.render(ax, offset)
    return fig, ax


GRID_PANEL = (3.75, 2.75)  # inches per panel, when settings has no "grid" size
GRID_LEGEND = 0.6  # inches below the panels for the shared legend
FOOTNOTE_LINE = 8.5  # points per footnote line (7 pt text)
LEGEND_COLUMNS = 4
LEGEND_ROW = 14.0  # points per row of the shared legend
BAND_PAD = 6.0  # points above and below the legend and footnote


def _per_panel(name: str, given: Any, values: list[str]) -> dict[str, Any]:
    """Check a per-panel argument: a dict keyed by value (P07 §10)."""
    if given is None:
        return {}
    if not isinstance(given, dict):
        raise HangtuError(
            f"{name} must be a dict of {{value: setting}} so each panel gets its own, "
            f"not {given!r}. Example: {name}={{{values[0]!r}: ...}}"
        )
    unknown = [key for key in given if key not in values]
    if unknown:
        raise HangtuError(
            f"{name} has settings for {unknown}, which aren't in values "
            f"({', '.join(values)})."
        )
    return given


def _tables(
    data: pd.DataFrame | dict[str, pd.DataFrame], values: list[str]
) -> dict[str, pd.DataFrame]:
    """Return the table for each value: the one table, or one per value."""
    if isinstance(data, pd.DataFrame):
        return dict.fromkeys(values, data)
    if not isinstance(data, dict):
        raise HangtuError(
            "data must be a DataFrame, or a dict of {value: DataFrame} with one "
            f"table per panel, not {type(data).__name__}."
        )
    missing = [value for value in values if value not in data]
    extra = [key for key in data if key not in values]
    if missing or extra:
        raise HangtuError(
            "data must have one table for each value. "
            + (f"Missing: {', '.join(missing)}. " if missing else "")
            + (f"Not in values: {', '.join(map(str, extra))}." if extra else "")
        )
    return data


def _grid_flags(panels: list[_Panel]) -> list[Artist]:
    """Return qualifier legend entries with counts summed over the panels."""
    handles = []
    for marker, size, text, reason in _values.QUALIFIERS.values():
        n = sum(panel.notes.counts.get(reason, 0) for panel in panels)
        if n:
            handles.append(
                _values.legend_marker(marker, _values.NEUTRAL, f"{text} ({n})", size)
            )
    return handles


def _grid_footnote(panels: list[_Panel]) -> list[str]:
    """Return each panel's note lines, prefixed with its quantity."""
    return [
        f"{panel.title}: {line}" for panel in panels for line in panel.notes.lines()
    ]


def _grid_legend(fig: Figure, handles: list[Artist], footnote: list[str]) -> None:
    """Put one legend below the panels, and the footnote below it.

    A band at the bottom of the figure is kept free of panels for them.
    """
    if not handles and not footnote:
        return
    legend_rows = -(-len(handles) // LEGEND_COLUMNS)
    band = (legend_rows * LEGEND_ROW + len(footnote) * FOOTNOTE_LINE + 2 * BAND_PAD) / (
        72.0 * fig.get_figheight()
    )
    fig.get_layout_engine().set(rect=(0.0, band, 1.0, 1.0 - band))
    if handles:
        legend = fig.legend(
            handles=handles,
            loc="upper center",
            bbox_to_anchor=(0.5, band),
            bbox_transform=fig.transFigure,
            ncols=min(len(handles), LEGEND_COLUMNS),
            frameon=False,
            fontsize=8,
            borderaxespad=0.0,
        )
        legend.set_in_layout(False)
    if footnote:
        fig.text(
            0.5,
            BAND_PAD / (72.0 * fig.get_figheight()),
            "\n".join(footnote),
            ha="center",
            va="bottom",
            fontsize=7,
            color="0.4",
        )


def geology_unit_comparisons(
    data: pd.DataFrame | dict[str, pd.DataFrame],
    values: list[str],
    *,
    columns: int = 2,
    baseline: pd.DataFrame | str | None = None,
    baseline_label: str | None = None,
    baseline_units: dict[str, str] | None = None,
    summary: Literal["percentiles", "box"] | None = "percentiles",
    percentiles: tuple[float, float, float] = (10, 50, 90),
    percentile_method: str = "linear",
    summary_min_count: int | None = None,
    points: bool = True,
    preset: dict[str, str] | None = None,
    log: dict[str, bool] | None = None,
    label: dict[str, str] | None = None,
    xlim: dict[str, tuple[float, float]] | None = None,
    reference_lines: dict[str, list[tuple[float, str]]] | None = None,
    order: list[str] | None = None,
    color_by: Literal["geology_unit"] | None = "geology_unit",
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    **style_overrides: Any,
) -> tuple[Figure, np.ndarray]:
    """Compare several properties by geology unit, one panel each (P07).

    Each panel is a ``geology_unit_comparison``. The panels share one legend,
    below the grid, and one footnote that names the panel of each note.

    The arguments not listed below are those of ``geology_unit_comparison``
    and apply to every panel.

    Parameters
    ----------
    data : DataFrame or dict
        One table holding every value column, or ``{value: table}`` when the
        properties come from different tests. Each table keeps its own units.
    values : list of str
        The columns to compare, one panel each, in this order.
    columns : int
        Panels per row.
    baseline : DataFrame or path, optional
        The report's ranges, with a ``property`` column naming the value of
        each row when there is more than one value.
    preset, log, label, xlim, reference_lines : dict, optional
        Per-panel settings, keyed by value, e.g. ``log={"hydraulic_conductivity":
        True}``.
    figsize : (width, height), optional
        The whole figure, in inches. By default the settings ``grid`` size
        per panel, plus room for the legend.

    Returns
    -------
    fig, axs
        ``axs[i]`` is the panel of ``values[i]``.

    Examples
    --------
    >>> fig, axs = ht.plot.geology_unit_comparisons(
    ...     {"water_content": index, "undrained_shear_strength": vane},
    ...     ["water_content", "undrained_shear_strength"],
    ...     baseline=gbr, baseline_label="GBR baseline p10-p90, p50")
    """
    if (
        isinstance(values, str)
        or not isinstance(values, list | tuple)
        or not values
        or len(set(values)) != len(values)
    ):
        raise HangtuError(
            "values must be a list of different value columns, one per panel, not "
            f'{values!r}. Example: values=["water_content", "bulk_unit_weight"]'
        )
    values = list(values)
    if not isinstance(columns, int) or isinstance(columns, bool) or columns < 1:
        raise HangtuError(
            f"columns must be a whole number of at least 1, not {columns!r}."
        )
    tables = _tables(data, values)
    settings_for = {
        name: _per_panel(name, given, values)
        for name, given in (
            ("preset", preset),
            ("log", log),
            ("label", label),
            ("xlim", xlim),
            ("reference_lines", reference_lines),
        )
    }
    for value in values:
        _check_columns(tables[value], value, color_by)
    if baseline is not None and not isinstance(baseline, pd.DataFrame):
        baseline = _units.read_csv(baseline)
    if baseline is not None and len(values) > 1 and "property" not in baseline.columns:
        raise ColumnError(
            "The baseline table covers several values here, so it needs a "
            "'property' column naming the value of each row, e.g. water_content."
        )
    chosen_summary = _check_summary(
        summary, percentiles, percentile_method, summary_min_count
    )
    system = _display_units(display_units or settings.display_units)
    n_rows = -(-len(values) // columns)
    n_columns = min(columns, len(values))

    with style.context(**style_overrides):
        grow = figsize is None
        if figsize is None:
            width, height = settings.figure_sizes.get("grid", GRID_PANEL)
            figsize = (n_columns * width, n_rows * height + GRID_LEGEND)
        fig, grid = plt.subplots(
            n_rows, n_columns, figsize=figsize, layout="constrained", squeeze=False
        )
        cells = list(grid.ravel())
        for unused in cells[len(values) :]:
            unused.remove()
        axs = np.array(cells[: len(values)], dtype=object)
        panels = []
        for ax, value in zip(axs, values, strict=True):
            panel = _draw_panel(
                ax,
                tables[value],
                value,
                preset=settings_for["preset"].get(value),
                log=settings_for["log"].get(value),
                label=settings_for["label"].get(value),
                xlim=settings_for["xlim"].get(value),
                order=order,
                color_by=color_by,
                points=points,
                summary=chosen_summary,
                baseline=baseline,
                baseline_units=baseline_units,
                reference_lines=settings_for["reference_lines"].get(value),
                note=None,
                palette=palette,
                units=units,
                system=system,
            )
            ax.ags_notes = dict(panel.notes.counts)
            panels.append(panel)

        handles: dict[str, Artist] = {}
        drawn = [
            p.baseline for p in panels if p.baseline is not None and p.baseline.units
        ]
        if drawn:
            text = legend_text(baseline_label, drawn)
            handles[text] = _baseline_handle(text)
        for panel in panels:
            for handle in panel.handles:
                handles.setdefault(handle.get_label(), handle)
        legend_handles = [*handles.values(), *_grid_flags(panels)]
        footnote = _grid_footnote(panels)
        if footnote and grow:
            width, height = fig.get_size_inches()
            fig.set_size_inches(width, height + len(footnote) * FOOTNOTE_LINE / 72.0)
        _grid_legend(fig, legend_handles, footnote)
    return fig, axs
