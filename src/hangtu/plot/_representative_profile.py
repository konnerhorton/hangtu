"""P09 representative value profile (docs/plots/P09-representative-profile.md)."""

from collections.abc import Mapping
from typing import Any, Literal

import numpy as np
import pandas as pd
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from hangtu._settings import settings
from hangtu.errors import HangtuError
from hangtu.plot import _layers, _values
from hangtu.plot._notes import Notes
from hangtu.plot._overlays import ValueScale
from hangtu.plot._profile import Overlay, _draw_profile
from hangtu.plot._vertical import Vertical
from hangtu.registry import column_info
from hangtu.stats._representative import representative
from hangtu.stats._result import RepresentativeResult, _label

REPRESENTATIVE_WIDTH = 1.5  # points (P09 §7)
MEAN_WIDTH = 0.8  # points
BAND_ALPHA = 0.15
STYLE_COLOR = "0.4"  # the gray legend entries naming each mark


def representative_profile(
    df: pd.DataFrame,
    *,
    value: str,
    by: str | None = None,
    method: str | None = None,
    side: str | None = None,
    distribution: str | None = None,
    trend: str | None = None,
    estimate: str | None = None,
    coefficient_of_variation: float | None = None,
    scale_of_fluctuation: float | None = None,
    failure_length: float | None = None,
    sensitivity_index: float | None = None,
    percentile: float | None = None,
    standard_deviations: float | None = None,
    pool: str | list[str] | None = None,
    include_assumed: bool = False,
    spt_refusal_upper_limit: float | str | Mapping[str, float | str] | None = None,
    judgments: Any = None,
    mean: bool = True,
    band: bool = True,
    vs: Literal["elevation", "depth"] | None = None,
    preset: str | None = None,
    log: bool | None = None,
    label: str | None = None,
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
    reference_lines: list[tuple[float, str]] | None = None,
    note: str | None = None,
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    legend: Literal["auto", "inside", "bottom", "right"] | bool = "auto",
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes, RepresentativeResult]:
    """Plot a property's representative value per unit on its profile (P09).

    Computes the representative values with
    :func:`hangtu.stats.representative` and draws them over the values, as
    :func:`profile` draws them: each geology unit's representative value,
    constant or a line with depth, solid, beside the mean (the median, for a
    lognormal distribution) it came from, dashed, with the band between them
    shaded, all in the unit's color. The lines span only the depths of their
    unit's values. The plot computes nothing of its own: the lines are
    ``result.design_lines(mean=True)``.

    Every judgment is passed to ``representative()`` unchanged and none has
    a default (SPEC §4), so its errors are this function's.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per value, as for :func:`hangtu.stats.representative` and
        :func:`profile`.
    value : str
        The column, e.g. ``"undrained_shear_strength"``.
    by : str, optional
        The column grouping the values, e.g. ``"geology_unit"``; it also
        colors them, so a line and its values share a color. One column:
        filter the rows or make one column to group by several. None is one
        group, drawn in one color.
    method, side, distribution, trend, estimate : str
        The view, as for ``representative()``.
    coefficient_of_variation, scale_of_fluctuation, failure_length : float, optional
        As for ``representative()``.
    sensitivity_index, percentile, standard_deviations : float, optional
        As for ``representative()``.
    pool : str or list of str, optional
        As for ``representative()``.
    include_assumed : bool
        As for ``representative()``. Assumed values are drawn either way.
    spt_refusal_upper_limit : float, "none" or dict, optional
        As for ``representative()``.
    judgments : Judgments or path, optional
        As for ``representative()``.
    mean : bool
        Draw each unit's mean (median) line.
    band : bool
        Shade between the mean (median) and the representative line, under
        the values.
    vs : {"depth", "elevation"}, optional
        The vertical axis. A trend is drawn against its own column, the
        default; the other is an error. A constant defaults to the column
        ``result.vertical`` names; the other needs one ground level for all
        rows.
    preset, log, label, marker_by, connect, intervals : optional
        As for :func:`profile`.
    xlim, ylim : (low, high), optional
        As for :func:`profile`. A line beyond them is clipped at the axis
        and counted in the footnote.
    xaxis_position, secondary, strata, water_level, ranges : optional
        As for :func:`profile`.
    reference_lines, note, palette : optional
        As for :func:`profile`.
    units : dict, optional
        ``{column: unit}``, overriding the units declared on ``df``.
    display_units : {"US", "SI"}, optional
        Defaults to ``ht.settings.display_units``. The values, the lines
        and their statistics are in these units.
    legend : {"auto", "inside", "bottom", "right"} or bool
        As for :func:`profile`.
    figsize : (width, height), optional
        Inches; ignored with ``ax=``.
    ax : matplotlib Axes, optional
        Draw into this axes.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, ax, result
        ``result`` is the :class:`~hangtu.stats.RepresentativeResult` the
        lines were drawn from.

    Raises
    ------
    HangtuError
        For ``by=`` with several columns, a ``vs`` other than a trend's
        column, a constant drawn against the other column without one ground
        level, and as ``representative()`` and ``profile()``.

    Examples
    --------
    >>> fig, ax, result = ht.plot.representative_profile(
    ...     strength, value="undrained_shear_strength", by="geology_unit",
    ...     method="characteristic", estimate="mean", side="low",
    ...     distribution="normal", trend="depth")
    """
    if by is not None and not isinstance(by, str):
        raise HangtuError(
            f"representative_profile() colors each unit's line and values alike, so "
            f"by= is one column, not {by!r}. Filter the rows to one value of the "
            "others, or make one column that combines them."
        )
    system = display_units or settings.display_units
    info = column_info(value) or {}
    result = representative(
        df,
        value=value,
        by=by,
        method=method,
        side=side,
        distribution=distribution,
        trend=trend,
        estimate=estimate,
        coefficient_of_variation=coefficient_of_variation,
        scale_of_fluctuation=scale_of_fluctuation,
        failure_length=failure_length,
        sensitivity_index=sensitivity_index,
        percentile=percentile,
        standard_deviations=standard_deviations,
        pool=pool,
        include_assumed=include_assumed,
        spt_refusal_upper_limit=spt_refusal_upper_limit,
        judgments=judgments,
        units=units,
        # An unregistered column has no kind of quantity to convert.
        display_units=system if "quantity" in info else display_units,
    )
    lines = result.design_lines(mean=True)
    vs = _choose_vs(result, vs)
    fig, ax = _draw_profile(
        df,
        value,
        vs=vs,
        preset=preset,
        log=log,
        label=label,
        color_by=by,
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
        reference_lines=reference_lines,
        note=note,
        palette=palette,
        units=units,
        display_units=display_units,
        legend=legend,
        figsize=figsize,
        ax=ax,
        value_ranges=True,
        overlay=_overlay(result, lines, mean=mean, band=band, xlim=xlim, ylim=ylim),
        cover_x=lines["value"].to_numpy(dtype=float),
        **style_overrides,
    )
    return fig, ax, result


def _choose_vs(
    result: RepresentativeResult, vs: Literal["elevation", "depth"] | None
) -> Literal["elevation", "depth"]:
    """Return the vertical axis: a trend's own column, or a constant's default."""
    own = result.trend or result.vertical
    # representative() records "depth" or "elevation"; design_lines() raised
    # without either.
    assert own == "depth" or own == "elevation"
    if result.trend is not None and vs is not None and vs != own:
        raise HangtuError(
            f"The lines are a trend with {own}, so they are drawn against {own}, "
            f"not vs={vs!r}. Leave vs out, or compute the trend with trend={vs!r}."
        )
    return vs or ("depth" if own == "depth" else "elevation")


def _short_name(result: RepresentativeResult) -> str:
    """Name the view in a legend entry: ``characteristic``, ``percentile 10``."""
    if result.method == "characteristic":
        return "characteristic"
    if result.method == "percentile":
        return f"percentile {result.percentile:g}"
    sign = "-" if result.side == "low" else "+"
    of = " of ln x" if result.distribution == "lognormal" else ""
    return f"mean {sign} {result.standard_deviations:g} std{of}"


def _overlay(
    result: RepresentativeResult,
    lines: pd.DataFrame,
    *,
    mean: bool,
    band: bool,
    xlim: tuple[float, float] | None,
    ylim: tuple[float, float] | None,
) -> Overlay:
    """Return the overlay that draws each unit's lines and band."""

    def draw(
        ax: Axes,
        vertical: Vertical,
        scale: ValueScale,
        colors: Mapping[Any, Any],
        notes: Notes,
    ) -> list[Artist]:
        return _draw_lines(
            ax, result, lines, vertical, scale, colors, notes, mean, band, xlim, ylim
        )

    return draw


def _draw_lines(
    ax: Axes,
    result: RepresentativeResult,
    lines: pd.DataFrame,
    vertical: Vertical,
    scale: ValueScale,
    colors: Mapping[Any, Any],
    notes: Notes,
    mean: bool,
    band: bool,
    xlim: tuple[float, float] | None,
    ylim: tuple[float, float] | None,
) -> list[Artist]:
    """Draw the band, mean and representative line per unit; return legend entries."""
    assert result.vertical is not None  # design_lines() raised without one
    units = lines.attrs.get("units", {})
    positions = vertical.to_display(
        lines[result.vertical].to_numpy(dtype=float), units.get(result.vertical, "")
    )
    if result.vertical != vertical.vs:
        if vertical.ground_level is None:
            raise HangtuError(
                f"The lines are at the {result.vertical} of each unit's values, and "
                f"the plot is against {vertical.vs}, but the rows don't share one "
                f"ground level to convert them. Plot with vs={result.vertical!r}."
            )
        positions = vertical.ground_level - positions
    values = scale.to_display(lines["value"].to_numpy(dtype=float), units.get("value"))
    labels = lines["label"].to_numpy(dtype=object)
    center = "median" if result.distribution == "lognormal" else "mean"
    view = result._line_name()
    drawn = False
    for group in result.groups:
        name = _label(group["key"])
        these = labels == f"{name}: {view}"
        if not these.any():
            continue
        drawn = True
        key = group["key"].get(result.by[0]) if result.by else None
        color = colors.get(key, _values.NEUTRAL)
        y = positions[these]
        x = _cut(values[these], scale.log, notes, xlim, ylim, y)
        middle = _cut(
            values[labels == f"{name}: {center}"], scale.log, notes, xlim, ylim, y
        )
        if band:
            ax.fill_betweenx(
                y,
                x,
                middle,
                where=np.isfinite(x) & np.isfinite(middle),
                color=color,
                alpha=BAND_ALPHA,
                linewidth=0,
                zorder=_layers.REPRESENTATIVE_BAND,
            )
        if mean:
            ax.plot(
                middle,
                y,
                color=color,
                linewidth=MEAN_WIDTH,
                linestyle="--",
                zorder=_layers.REPRESENTATIVE_MEAN,
            )
        ax.plot(
            x,
            y,
            color=color,
            linewidth=REPRESENTATIVE_WIDTH,
            zorder=_layers.REPRESENTATIVE,
        )
    if not drawn:
        return []
    short = _short_name(result)
    handles: list[Artist] = [
        Line2D([], [], color=STYLE_COLOR, linewidth=REPRESENTATIVE_WIDTH, label=short)
    ]
    if mean:
        handles.append(
            Line2D(
                [],
                [],
                color=STYLE_COLOR,
                linewidth=MEAN_WIDTH,
                linestyle="--",
                label=center,
            )
        )
    if band:
        handles.append(
            Patch(
                facecolor=STYLE_COLOR,
                alpha=BAND_ALPHA,
                edgecolor="none",
                label=f"{center} to {short}",
            )
        )
    return handles


def _cut(
    x: np.ndarray,
    log: bool,
    notes: Notes,
    xlim: tuple[float, float] | None,
    ylim: tuple[float, float] | None,
    y: np.ndarray,
) -> np.ndarray:
    """Return a line's values with the part ≤ 0 on a log axis blank, counted.

    A line reaching beyond fixed limits is left for matplotlib to clip at
    the axis, and counted.
    """
    if log and (x <= 0).any():
        notes.add("line_log_nonpositive", 1)
        x = np.where(x > 0, x, np.nan)
    shown = np.isfinite(x)
    beyond = False
    if xlim is not None:
        low, high = sorted(xlim)
        beyond |= bool(((x[shown] < low) | (x[shown] > high)).any())
    if ylim is not None:
        low, high = sorted(ylim)
        beyond |= bool(((y[shown] < low) | (y[shown] > high)).any())
    if beyond:
        notes.add("line_beyond_limit", 1)
    return x
