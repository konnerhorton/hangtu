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

from hangtu import units as _units
from hangtu._settings import _display_units, settings
from hangtu.analysis._fractions import fraction_system
from hangtu.analysis._gradation import (
    Curve,
    _check_d_values,
    d_value,
    drop_tolerance,
    grading_curves,
)
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.plot import _envelopes, _fraction_band, _layers, _values, style
from hangtu.plot._hints import hint_missing
from hangtu.plot._legend import BELOW_X_LABEL, add_legend
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
D_COLOR = "black"
D_LEADER_WIDTH = 0.6  # points
D_TICK_SIZE = 6.0  # points
D_LABEL_SIZE = 7
DEFAULT_D_VALUES = (10, 30, 60)


def _decade_label(value: float, _position: Any) -> str:
    """Write a decade in plain numbers: 0.001, 0.01, ..., 100.

    Rounded to 12 significant figures first, since a tick can arrive as
    0.09999999999999999 (matplotlib 3.8).
    """
    return np.format_float_positional(float(f"{value:.12g}"), trim="-")


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


def _d_percents(d_values: Any) -> tuple[int, ...]:
    """Resolve ``d_values=``: False or None for none, True for D10, D30 and D60."""
    if d_values is None or d_values is False:
        return ()
    if d_values is True:
        return DEFAULT_D_VALUES
    if isinstance(d_values, list | tuple) and not d_values:
        return ()
    return _check_d_values(d_values)


def _d_text(percent: int, size: float) -> str:
    """Label a D-value to 3 significant figures: "D60 = 0.711 mm"."""
    return f"D{percent} = {f'{size:#.3g}'.rstrip('.')} mm"


def _draw_d_values(
    ax: Axes,
    curves: list[Curve],
    percents: tuple[int, ...],
    limits: tuple[float, float],
    notes: Notes,
) -> None:
    """Mark each curve's D-values: leaders and labels for one curve, else ticks (§7).

    Curves the analysis can't use (short, or rising toward finer sizes) get
    none. A D-value a curve doesn't reach is counted, never extrapolated.
    """
    drawn = [curve for curve in curves if len(curve.sizes) >= 2]
    single = len(drawn) == 1
    left = ax.get_xlim()[0]  # the y axis's side, whichever way x runs
    unreached: dict[int, int] = {}
    for curve in drawn:
        if not curve.usable:
            continue
        for percent in percents:
            size = d_value(curve.sizes, curve.passing, percent)
            if np.isnan(size):
                unreached[percent] = unreached.get(percent, 0) + 1
                continue
            if not min(limits) <= size <= max(limits):
                notes.add("beyond_limit", 1)
                continue
            if not single:
                ax.plot(
                    [size],
                    [percent],
                    marker="|",
                    markersize=D_TICK_SIZE,
                    color=D_COLOR,
                    linestyle="none",
                    gid="d_value",
                    zorder=_layers.D_VALUES,
                )
                continue
            ax.plot(
                [size, size, left],
                [0.0, percent, percent],
                color=D_COLOR,
                linewidth=D_LEADER_WIDTH,
                linestyle="--",
                gid="d_value",
                zorder=_layers.D_VALUES,
            )
            ax.annotate(
                _d_text(percent, size),
                xy=(size, percent),
                xytext=(4, -2),
                textcoords="offset points",
                ha="left",
                va="top",
                fontsize=D_LABEL_SIZE,
                gid="d_value_label",
                zorder=_layers.ANNOTATIONS,
            )
    if unreached:
        notes.add("d_value_unreached", sum(unreached.values()))
        detail = ", ".join(
            f"D{percent} by {n} curve{'s' if n > 1 else ''}"
            for percent, n in sorted(unreached.items())
        )
        notes.set_where("d_value_unreached", f" ({detail})")


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

    One curve per specimen (told apart by ``loca_id`` and ``specimen_id``),
    drawn through its points sorted by size as rows, with the size fractions
    named in a band above. The band, its dividers and the D-values come from
    the same code as ``ht.analysis.gradation()``, so they agree with its
    numbers. Particle size is shown in mm in both unit systems; only the sieve
    labels change. Nothing is reshaped: a curve that rises toward finer sizes
    is drawn as measured, with a warning, and gets no D-values. Short curves,
    blank points and D-values a curve doesn't reach are counted in the
    footnote.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per point on a curve, as ``ht.template("grain_size")`` or
        ``p.grain_size()``. ``particle_size`` needs units. An empty frame
        draws the axes and the band alone, e.g. as a base on a ``Sheet``.
    fractions : str, dict, path or None
        The band's size-fraction system: ``"astm_uscs"`` (fines as one band;
        USCS has no clay-silt boundary), ``"aashto"``, ``"iso14688"``, or your
        own as for ``gradation(fractions=)``. None hides the band and the
        dividers.
    sieves : {"auto", "us", "iso"}, list or None
        Sieve labels along the top: ``"auto"`` is ``"us"`` (ASTM E11) in US
        display and ``"iso"`` in SI; or your own ``[(size_mm, label), ...]``.
    d_values : bool or list of int
        Mark D-values: True for D10, D30 and D60, or a list of percentages.
        With one curve, dashed leaders to both axes and a label; with several,
        a tick on each curve. Never extrapolated.
    envelopes : DataFrame or str, optional
        Bands to compare the curves with, e.g. a filter specification: a
        table or CSV path with one row per size (``ht.template("envelopes")``),
        ``low`` and ``high`` the percent passing at that size. Drawn in gray.
    envelope_colors : dict, optional
        ``{envelope label: color}``.
    color_by : str or None
        The column curves are colored by, the same for all of a curve's
        points; ``"specimen_id"`` colors each curve; None for one color.
    order : list of str, optional
        Units in stratigraphic order, for the legend. Units not in it follow,
        by name.
    reverse : bool
        Put coarse sizes on the left, as on some US forms.
    xlim : tuple, optional
        Size limits in mm, exactly. Points beyond them are drawn at the edge
        and counted.
    note : str, optional
        Free text, added to the footnote.
    palette : dict, optional
        ``{unit: color}``, overriding the session's colors.
    units : dict, optional
        ``{column: unit}``, overriding the units declared on ``df``.
    display_units : {"US", "SI"}, optional
        Picks the sieve labels with ``sieves="auto"``.
    figsize : tuple, optional
        Figure size in inches. Defaults to ``ht.settings.figure_sizes["default"]``.
    ax : matplotlib.axes.Axes, optional
        Draw into this axes, e.g. a ``Sheet`` panel. The band's axes and the
        sieve strip are carved from its top and kept as
        ``ax.grain_size_header`` and ``ax.grain_size_sieves``.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, ax

    Examples
    --------
    >>> curves = p.grain_size(geology=["Alluvium"])
    >>> fig, ax = ht.plot.grain_size(curves, d_values=True)
    >>> fig, ax = ht.plot.grain_size(
    ...     curves, fractions="iso14688", envelopes="filter_band.csv"
    ... )
    """
    system = _display_units(display_units or settings.display_units)
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    percents = _d_percents(d_values)
    data_unit = (units or {}).get("particle_size") or _units.units_of(df).get(
        "particle_size"
    )
    bands = (
        _envelopes.read_envelopes(envelopes, data_unit) if envelopes is not None else []
    )
    band_colors = _values.label_colors(
        [band.label for band in bands],
        envelope_colors,
        "envelope_colors",
        "envelopes",
        _envelopes.COLOR,
    )
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
        # The strip first, so it sits between the frame and the band.
        ax.grain_size_sieves = _fraction_band.add_sieve_strip(ax, sieve_list, limits)
        ax.grain_size_header = None
        if fractions is not None:
            ax.grain_size_header = _fraction_band.add_header(ax)
            _fraction_band.draw_band(ax.grain_size_header, ax, system_fractions, limits)
        envelope_handles = _envelopes.draw_envelopes(ax, bands, band_colors)
        handles = _draw_curves(
            ax,
            curves,
            groups,
            colors,
            limits,
            color_by == "specimen_id",
            notes,
        )
        _draw_d_values(ax, curves, percents, limits, notes)
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
        # Below the axes: a legend on the right crowds the log axis (§5).
        legend = add_legend(ax, [handles, envelope_handles], notes, where="bottom")
        notes.render(ax, BELOW_X_LABEL, where="bottom", below=legend)
    return fig, ax
