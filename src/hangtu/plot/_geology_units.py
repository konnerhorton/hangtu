"""P07 property by geology unit (docs/plots/P07-geology-unit-comparison.md)."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from numbers import Real
from typing import Any, Literal

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
from hangtu._settings import _display_units, settings
from hangtu.errors import ColumnError, HangtuError
from hangtu.plot import _layers, _presets, _values, style
from hangtu.plot._data import numeric_column
from hangtu.plot._labels import axis_label
from hangtu.plot._legend import add_legend
from hangtu.plot._limits import set_linear_axis, set_log_axis
from hangtu.plot._notes import Notes
from hangtu.plot._palette import resolve_palette
from hangtu.plot._presets import Preset

POINT_SIZE = 3.0  # points
POINT_ALPHA = 0.4
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
LEGEND_GAP = 6.0  # points between the count labels and the legend
EMPTY_COLOR = "0.4"
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


def _not_built(**arguments: Any) -> None:
    """Refuse arguments whose behavior isn't built yet, instead of ignoring them."""
    given = [name for name, used in arguments.items() if used]
    if given:
        raise NotImplementedError(f"{', '.join(given)} isn't built yet (P07 plan).")


def _rows(
    df: pd.DataFrame, order: list[str] | None, palette: dict[str, str] | None
) -> tuple[np.ndarray, dict[Any, Any]]:
    """Return each row's geology unit, and ``{unit: color}`` in row order.

    Units in ``order`` come first, then the rest by name, then "(blank)".
    """
    groups = df["geology_unit"].to_numpy(dtype=object)
    blank = pd.isna(groups)
    colors = resolve_palette(groups[~blank], palette, order)
    if blank.any():
        groups = np.where(blank, _values.BLANK_GROUP, groups)
        colors[_values.BLANK_GROUP] = _values.NEUTRAL
    return groups, colors


def _set_unit_axis(ax: Axes, names: list[Any]) -> None:
    """One row per unit, first at the top, with no gridlines between them."""
    n = max(len(names), 1)
    ax.set_yticks(range(len(names)), [str(name) for name in names])
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_ylim(n - 0.5, -0.5)
    ax.grid(False, axis="y", which="both")


def _caps(ax: Axes, xs: Sequence[float], row: float, color: Any, width: float) -> None:
    """Draw short vertical end caps at ``xs`` on a row."""
    half = CAP_HEIGHT / 2
    gaps = [np.nan] * len(xs)
    ax.plot(
        np.column_stack([xs, xs, gaps]).ravel(),
        np.column_stack([[row - half] * len(xs), [row + half] * len(xs), gaps]).ravel(),
        color=color,
        linewidth=width,
        solid_capstyle="butt",
        zorder=_layers.SUMMARY,
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


def _count_label(ax: Axes, row: float, n: int, summarized: bool | None) -> Artist:
    """Write "n = 288" just outside the right edge of the axes, level with a row.

    ``summarized`` is False when a summary was asked for but n is too small.
    """
    text = f"n = {n}" + (" (no summary)" if n and summarized is False else "")
    return ax.annotate(
        text,
        xy=(1.0, row),
        xycoords=blended_transform_factory(ax.transAxes, ax.transData),
        xytext=(COUNT_GAP, 0.0),
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
    widest = max(label.get_window_extent(renderer).width for label in counts)
    return COUNT_GAP + widest * 72.0 / figure.dpi + LEGEND_GAP


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
    # Blank values are tests not done, so they are skipped, not counted (P07 §14).
    drawn = ~np.isnan(x)
    if log:
        nonpositive = drawn & (x <= 0)
        panel.notes.count(nonpositive, "log_nonpositive")
        drawn &= ~nonpositive
    groups, colors = _rows(df[drawn], order, palette)
    rows = list(colors)
    unit_of = np.full(len(df), None, dtype=object)
    unit_of[drawn] = groups
    row_of = {unit: i for i, unit in enumerate(rows)}
    jitter = np.random.default_rng(JITTER_SEED).uniform(-JITTER, JITTER, len(df))

    style.style_axes(ax)
    limits = _values.value_limits(
        x[drawn],
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

    draw_summary = {"percentiles": _draw_percentiles, "box": _draw_box}.get(
        summary.kind
    )
    summarized_any = False
    for unit, color in colors.items():
        these = drawn & (unit_of == unit)
        color = _values.NEUTRAL if color_by is None else color
        row = row_of[unit]
        if points and these.any():
            ax.scatter(
                x[these],
                row + jitter[these],
                s=POINT_SIZE**2,
                color=color,
                alpha=POINT_ALPHA,
                linewidths=0,
                label=f"_{unit}",
                zorder=_layers.MARKERS,
            )
        n = int(these.sum())
        summarized = None if draw_summary is None else n >= summary.min_count
        if summarized:
            draw_summary(ax, x[these], row, color, summary)
            summarized_any = True
        panel.counts.append(_count_label(ax, row, n, summarized))
    if summarized_any:
        panel.handles.append(_summary_handle(summary))
    if points and drawn.any():
        panel.handles.append(
            _values.legend_marker("o", _values.NEUTRAL, "Data", POINT_SIZE)
        )

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
    ax.set_xlabel(
        axis_label(
            _values.axis_text(value, label, chosen),
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
    _not_built(
        baseline=baseline is not None,
        baseline_label=baseline_label is not None,
        baseline_units=baseline_units is not None,
        xlim=xlim is not None,
        reference_lines=reference_lines is not None,
        note=note is not None,
        qualifier="qualifier" in df.columns,
        non_plastic="non_plastic" in df.columns,
    )
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
            palette=palette,
            units=units,
            system=system,
        )
        offset = _legend_offset(ax, panel.counts)
        add_legend(ax, [panel.handles], panel.notes, offset)
        panel.notes.render(ax, offset)
    return fig, ax
