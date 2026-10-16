"""P05 grain size distribution (docs/plots/P05-grain-size.md)."""

import os
from collections.abc import Sequence
from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MultipleLocator

from hangtu._settings import _display_units, settings
from hangtu.analysis._fractions import fraction_system
from hangtu.analysis._gradation import Curve, drop_tolerance, grading_curves
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.plot import _fraction_band, _layers, _values, style
from hangtu.plot._hints import hint_missing
from hangtu.plot._legend import add_legend
from hangtu.plot._limits import clear_of_data, log_limits, set_log_axis
from hangtu.plot._notes import Notes, edge_markers
from hangtu.plot._palette import AUTOMATIC
from hangtu.plot._plasticity_chart import _check_color_by

MIN_LIMITS = (0.001, 100.0)  # mm; the x axis covers at least these (§6)
MIN_DECADES = 5
Y_LIMITS = (0.0, 100.0)
Y_STEP = 10.0
LINE_WIDTH = 1.0  # points
MARKER_SIZE = 3.0  # points
MAX_NAMED = 5  # curves named in a warning


def _decade_label(value: float, _position: Any) -> str:
    """Write a decade in plain numbers: 0.001, 0.01, ..., 100."""
    return np.format_float_positional(value, trim="-")


def x_limits(xlim: Any, sizes: np.ndarray) -> tuple[float, float]:
    """Return ``xlim`` as given, else whole decades over the data and 0.001-100 mm.

    A point on a whole decade moves that limit out one decade (P00 §8).
    """
    if xlim is not None:
        return _values.check_limits("xlim", xlim, log=True)
    if not sizes.size:
        return MIN_LIMITS
    finest, coarsest = float(sizes.min()), float(sizes.max())
    limits = log_limits(
        min(finest, MIN_LIMITS[0]),
        max(coarsest, MIN_LIMITS[1]),
        MIN_DECADES,
        clear=False,
    )
    return clear_of_data(limits, finest, coarsest, log=True)


def _set_axes(ax: Axes, limits: tuple[float, float], reverse: bool) -> None:
    set_log_axis(ax, "x", limits[::-1] if reverse else limits)
    ax.xaxis.set_major_formatter(FuncFormatter(_decade_label))
    ax.set_ylim(*Y_LIMITS)
    ax.yaxis.set_major_locator(MultipleLocator(Y_STEP))
    ax.grid(True, which="major")
    ax.set_xlabel("Particle size (mm)")
    ax.set_ylabel("Percent passing (%)")


def _curve_groups(
    df: pd.DataFrame,
    curves: list[Curve],
    groups: list[np.ndarray],
    color_by: str | None,
) -> pd.DataFrame:
    """Return one row per curve, its first point's, checking ``color_by`` is constant.

    The rows keep the column types and ``attrs``, so a categorical unit order
    and a project's palette carry through to the colors.
    """
    first = df.iloc[[rows[0] for rows in groups]].reset_index(drop=True)
    first.attrs = df.attrs
    if color_by is None or color_by not in df.columns:
        return first
    varying = [
        curve.name
        for curve, rows in zip(curves, groups, strict=True)
        if df[color_by].iloc[rows].nunique(dropna=False) > 1
    ]
    if varying:
        raise ColumnError(
            f"Column {color_by!r} changes within the curve"
            f"{'s' if len(varying) > 1 else ''} {_names(varying)}, so it can't "
            "give each curve one color. Make it the same for every point of a "
            "curve, or pick another color_by."
        )
    return first


def _names(names: Sequence[str]) -> str:
    shown = ", ".join(names[:MAX_NAMED])
    more = len(names) - MAX_NAMED
    return f"{shown} and {more} more" if more > 0 else shown


def _curve_colors(
    first: pd.DataFrame,
    curves: list[Curve],
    color_by: str | None,
    palette: dict[str, str] | None,
    order: list[str] | None,
) -> tuple[list[Any], dict[Any, Any]]:
    """Return each curve's group and ``{group: color}`` in legend order (§7).

    By ``specimen_id``, each curve is its own group, colored from the
    automatic cycle in curve order, so specimens don't take session unit
    colors.
    """
    if color_by == "specimen_id":
        names = [curve.name for curve in curves]
        if len(names) > len(AUTOMATIC):
            warn(
                f"{len(names)} curves are colored one by one, so colors repeat "
                f'after {len(AUTOMATIC)}. Use color_by="geology_unit" to color '
                "them by unit."
            )
        colors = {name: AUTOMATIC[i % len(AUTOMATIC)] for i, name in enumerate(names)}
        return names, colors
    groups, colors = _values.color_groups(first, color_by, palette, order)
    return list(groups), colors


def _draw_curves(
    ax: Axes,
    curves: list[Curve],
    groups: list[Any],
    colors: dict[Any, Any],
    limits: tuple[float, float],
    by_curve: bool,
    notes: Notes,
) -> list[Line2D]:
    """Draw each curve with two or more points; return the legend handles."""
    counts: dict[Any, int] = {}
    for curve, group in zip(curves, groups, strict=True):
        if len(curve.sizes) < 2:
            continue
        color = colors[group]
        edge = edge_markers(ax, curve.sizes, curve.passing, {"x": limits}, color)
        notes.count(edge, "beyond_limit")
        ax.plot(
            curve.sizes,
            curve.passing,
            color=color,
            linewidth=LINE_WIDTH,
            marker="o",
            markersize=MARKER_SIZE,
            markevery=list(~edge),
            label=curve.name,
            gid="curve",
            zorder=_layers.MARKERS,
        )
        counts[group] = counts.get(group, 0) + 1
    handles = []
    for group, color in colors.items():
        n = counts.get(group, 0)
        if not n:
            continue
        if by_curve:
            text = str(group)
        elif group is None:
            text = f"All curves (n = {n})"
        else:
            text = f"{group} (n = {n} curve{'s' if n > 1 else ''})"
        handles.append(
            Line2D(
                [],
                [],
                color=color,
                linewidth=LINE_WIDTH,
                marker="o",
                markersize=MARKER_SIZE,
                label=text,
            )
        )
    return handles


def _warn_falling(falling: list[str]) -> None:
    if falling:
        warn(
            f"Percent passing rises by more than {drop_tolerance():g} percentage "
            f"points toward finer sizes in {_names(falling)}. Drawn as measured, "
            "without D-values; check the curves (QC rule P001)."
        )


def _count_points(df: pd.DataFrame, blank: np.ndarray, notes: Notes) -> None:
    """Count blank points and qualified values (§11)."""
    notes.count(blank, "nan")
    qualifiers = _values.qualifiers(df)
    for symbol, flag in _values.QUALIFIERS.items():
        notes.count((qualifiers == symbol) & ~blank, flag.reason)


def grain_size(
    df: pd.DataFrame,
    *,
    fractions: str | dict | os.PathLike | None = "astm_uscs",
    sieves: Literal["auto", "us", "iso"] | list[tuple[float, str]] | None = "auto",
    d_values: bool | list[int] = False,
    envelopes: pd.DataFrame | str | None = None,
    envelope_colors: dict[str, str] | None = None,
    color_by: str | None = "geology_unit",
    order: list[str] | None = None,
    reverse: bool = False,
    xlim: tuple[float, float] | None = None,
    note: str | None = None,
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes]:
    """Plot grading curves on a log size axis with the soil fractions above (P05).

    Not finished: D-values and envelopes come next.
    """
    system = _display_units(display_units or settings.display_units)
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if d_values or envelopes is not None or envelope_colors:
        raise NotImplementedError("D-values and envelopes come next (P05).")
    system_fractions = fraction_system(fractions)[1] if fractions is not None else []
    sieve_list = _fraction_band.sieve_list(sieves, system)
    _check_color_by(df, color_by)

    with style.context(**style_overrides):
        notes = Notes()
        curves: list[Curve] = []
        groups: list[Any] = []
        colors: dict[Any, Any] = {}
        if len(df):
            if color_by == "geology_unit":
                hint_missing(df, {"geology_unit": "all curves are drawn in one color"})
            found = grading_curves(df, units)
            curves = found.curves
            first = _curve_groups(df, curves, found.groups, color_by)
            groups, colors = _curve_colors(first, curves, color_by, palette, order)
            _count_points(df, found.blank, notes)
            notes.add("short_curve", len(found.short))
            _warn_falling(found.falling)
        drawn = [curve.sizes for curve in curves if len(curve.sizes) >= 2]
        limits = x_limits(xlim, np.concatenate(drawn) if drawn else np.empty(0))
        if note is not None:
            notes.add_text(str(note))
        if ax is None:
            fig, ax = plt.subplots(
                figsize=figsize or settings.figure_sizes["default"],
                layout="constrained",
            )
        else:
            fig = ax.figure
        style.style_axes(ax)
        _set_axes(ax, limits, reverse)
        ax.grain_size_header = None
        if fractions is not None:
            ax.grain_size_header = _fraction_band.add_header(ax)
            _fraction_band.draw_band(ax.grain_size_header, ax, system_fractions, limits)
        _fraction_band.draw_sieves(ax, sieve_list, limits)
        handles = _draw_curves(
            ax,
            curves,
            groups,
            colors,
            limits,
            color_by == "specimen_id",
            notes,
        )
        if not handles:
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
        add_legend(ax, [handles], notes)
        notes.render(ax)
    return fig, ax
