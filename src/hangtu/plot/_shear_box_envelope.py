"""P31 shear box envelope (docs/plots/P31-shear-box-envelope.md)."""

import warnings
from typing import Any, Literal

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from hangtu._settings import _display_units, settings
from hangtu.analysis._shear_box_fit import ShearBoxFit, shear_box_fit
from hangtu.errors import HangtuError
from hangtu.plot import _envelope_drawing as envelope
from hangtu.plot import _layers, _values, style
from hangtu.plot._labels import axis_label
from hangtu.plot._legend import add_legend
from hangtu.plot._limits import nice_limits
from hangtu.plot._notes import Notes, figure_of
from hangtu.plot._palette import resolve_palette

STRENGTHS = ("peak", "residual")
#: The columns the fit checks a line's rows share (its decision 6).
CHECKED = ["test_type", "failure_criterion"]
LEGEND_COLOR = "black"
MARKER_SIZE = 5.0
OTHER_WIDTH = 0.8
OTHER_ALPHA = 0.6
KIND_TEXT = {"free": "Free fit", "through_origin": "Through the origin"}


def shear_box_envelope(
    df: pd.DataFrame,
    *,
    group_by: str | list[str] | None = None,
    color_by: str | None = None,
    cohesion: float | None = None,
    normal_stress: Literal["at_peak_or_residual", "applied"] = "at_peak_or_residual",
    pool: str | list[str] | None = None,
    fit: bool = True,
    note: str | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes, ShearBoxFit | None]:
    r"""Plot shear box stages in τ-σn with the fitted peak and residual lines (P31).

    Peak points are filled and residual points open, each at the normal
    stress the fit used for it. The lines are ``ht.analysis.shear_box_fit()``'s,
    drawn, never refitted:

    $$
    \tau = c + \sigma_n \tan\phi
    $$

    Each strength has two lines: the free fit and the fit through the origin.
    The main one (free, unless ``cohesion=0``) is solid over the normal
    stresses tested and dashed beyond: c is an intercept, outside them. The
    other is thin and dotted, so the two compare. A box gives each group's
    c, φ, n, R², the range of σn, and the lab's own values where the rows
    have them. Equal aspect, so a slope reads as its angle.

    The stresses aren't labeled effective, and a direct shear φ isn't a
    triaxial φ′: selection converts one to the other (M18).

    Parameters
    ----------
    df : pandas.DataFrame
        One row per stage, as ``p.shear_box()`` or a CSV in
        ``ht.template("shear_box")``'s shape.
    group_by, cohesion, normal_stress, pool, units
        Passed to ``ht.analysis.shear_box_fit()``, which explains them.
    color_by : str, optional
        Colors the points when there is no ``group_by``. Defaults to
        ``geology_unit`` when the rows have it. An error with ``group_by``:
        each set of lines has one color.
    fit : bool
        False draws the points only, and returns None for the fit.
    note : str, optional
        Free text, added to the footnote.
    display_units : {"US", "SI"}, optional
        Stresses in psf (US) or kPa (SI), or the unit
        ``ht.settings.display_overrides["stress"]`` names; the fit is made in
        them. Defaults to ``ht.settings.display_units``.
    figsize : tuple, optional
        Figure size in inches. Defaults to ``ht.settings.figure_sizes["default"]``.
    ax : matplotlib.axes.Axes, optional
        Draw into this axes, e.g. a ``Sheet`` panel.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, ax, fit
        ``fit`` is the ``ShearBoxFit`` drawn, or None with ``fit=False``.

    Examples
    --------
    >>> fig, ax, fit = ht.plot.shear_box_envelope(
    ...     p.shear_box(), group_by="geology_unit"
    ... )
    >>> with ht.settings.override(display_overrides={"stress": "MPa"}):
    ...     fig, ax, fit = ht.plot.shear_box_envelope(
    ...         p.shear_box(geology=["Sandstone"]), display_units="SI"
    ...     )
    """
    drawn = list(STRENGTHS)
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if group_by is not None and color_by is not None:
        raise HangtuError(
            "color_by= can't be used with group_by=: each set of lines is drawn in "
            "its group's color. Use one or the other."
        )
    system = _display_units(display_units or settings.display_units)
    if color_by is None and group_by is None and "geology_unit" in df.columns:
        color_by = "geology_unit"
    if color_by is not None and color_by not in df.columns:
        raise HangtuError(
            f"color_by={color_by!r}, but df has no such column. Available "
            f"columns: {', '.join(map(str, df.columns))}."
        )

    with style.context(**style_overrides):
        with warnings.catch_warnings():
            if not fit:  # no line is drawn, so its warnings would mislead
                warnings.simplefilter("ignore")
            result = shear_box_fit(
                df,
                group_by=group_by,
                cohesion=cohesion,
                normal_stress=normal_stress,
                pool=pool if fit else CHECKED,
                units=units,
                display_units=system,
            )
        if ax is None:
            fig, ax = plt.subplots(
                figsize=figsize or settings.figure_sizes["default"],
                layout="constrained",
            )
        else:
            fig = figure_of(ax)
        style.style_axes(ax)
        notes = Notes()
        colors = _colors(df, result, color_by)
        xlim, ylim = _limits(result, drawn, fit)
        # P11's axes in its Mohr space (σ-τ, no prime), with σn on the label.
        envelope.set_axes(ax, "mohr", "total", result.unit, xlim, ylim)
        ax.set_xlabel(axis_label("Normal stress, σn", result.unit))
        xlim = ax.get_xlim()
        color_handles = _draw_points(ax, df, result, drawn, color_by, colors)
        handles = []
        if fit:
            handles = _draw_lines(ax, result, drawn, colors, xlim)
        if note is not None:
            notes.add_text(str(note))
        marks = [
            _values.legend_marker(
                "o", LEGEND_COLOR, strength.capitalize(), MARKER_SIZE, filled=filled
            )
            for strength, filled in (("peak", True), ("residual", False))
            if strength in drawn
        ]
        if not any(
            group["strengths"][s]["points"] for group in result.groups for s in drawn
        ):
            marks = []
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
        placed = add_legend(ax, [color_handles, marks, handles], notes)
        notes.render(ax, where=placed.where, below=placed.legend)
    return fig, ax, result if fit else None


def _group_label(result: ShearBoxFit, group: dict[str, Any]) -> str | None:
    return _values.group_text(envelope.group_key(group)) if result.by else None


def _colors(
    df: pd.DataFrame, result: ShearBoxFit, color_by: str | None
) -> dict[Any, Any]:
    """Return ``{group or color_by value: color}``."""
    if result.by:
        labels = [_group_label(result, group) for group in result.groups]
        if len(labels) == 1:
            return {labels[0]: LEGEND_COLOR}
        return resolve_palette(labels, None, labels, df.attrs.get("palette"))
    _, colors = _values.color_groups(df, color_by, None)
    return colors


def _point_color(
    df: pd.DataFrame,
    result: ShearBoxFit,
    group: dict[str, Any],
    row: Any,
    color_by: str | None,
    colors: dict[Any, Any],
) -> tuple[Any, Any]:
    """Return the legend label and color of one point."""
    if result.by:
        label = _group_label(result, group)
        return label, colors[label]
    if color_by is None:
        return None, colors[None]
    value = df.at[row, color_by]
    label = _values.BLANK_GROUP if pd.isna(value) else value
    return label, colors[label]


def _drawn_lines(result: ShearBoxFit, drawn: list[str]) -> list[dict[str, Any]]:
    return [
        line
        for group in result.groups
        for s in drawn
        for line in group["strengths"][s]["lines"]
        if line["no_fit_reason"] is None
    ]


def _limits(
    result: ShearBoxFit, drawn: list[str], fit: bool
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return the axes' limits: from 0 past the largest σn and τ (P31 §6)."""
    points = [
        point
        for group in result.groups
        for s in drawn
        for point in group["strengths"][s]["points"]
    ]
    if not points:
        return (0.0, 1.0), (0.0, 1.0)
    x_high = max(point["normal_stress"] for point in points)
    y_high = max(point["shear_stress"] for point in points)
    lowest = min(
        [0.0, *(line["cohesion"] for line in _drawn_lines(result, drawn))]
        if fit
        else [0.0]
    )
    xlim = nice_limits(0.0, x_high, start_at_zero=True)
    ylim = nice_limits(lowest, y_high, start_at_zero=True)
    return xlim, ylim


def _draw_points(
    ax: Axes,
    df: pd.DataFrame,
    result: ShearBoxFit,
    drawn: list[str],
    color_by: str | None,
    colors: dict[Any, Any],
) -> list[Line2D]:
    """Draw each strength's points, filled for peak and open for residual."""
    seen: dict[Any, Line2D] = {}
    for group in result.groups:
        for s in drawn:
            for point in group["strengths"][s]["points"]:
                label, color = _point_color(
                    df, result, group, point["row"], color_by, colors
                )
                ax.plot(
                    [point["normal_stress"]],
                    [point["shear_stress"]],
                    marker="o",
                    markersize=MARKER_SIZE,
                    color=color,
                    markerfacecolor=color if s == "peak" else "white",
                    linestyle="none",
                    gid=f"{s}_point",
                    zorder=_layers.MARKERS,
                )
                if label is not None and label not in seen:
                    seen[label] = _values.legend_marker(
                        "s", color, _values.group_text(label), MARKER_SIZE
                    )
    return list(seen.values()) if len(seen) > 1 else []


def _draw_lines(
    ax: Axes,
    result: ShearBoxFit,
    drawn: list[str],
    colors: dict[Any, Any],
    xlim: tuple[float, float],
) -> list[Line2D]:
    """Draw each line: the main one solid over its range, the other dotted."""
    several = len(result.groups) > 1
    kinds: list[str] = []
    for group in result.groups:
        label = _group_label(result, group)
        color = colors[label] if label is not None and several else LEGEND_COLOR
        for s in drawn:
            main, other = group["strengths"][s]["lines"]
            kinds = [main["line_kind"], other["line_kind"]]
            if main["no_fit_reason"] is None:
                c, slope = main["cohesion"], main["line_slope"]
                low, high = main["lowest_normal_stress"], main["highest_normal_stress"]
                gid = f"{s}_{main['line_kind']}"
                for x0, x1, dashes, part in (
                    (xlim[0], low, "--", "_beyond"),
                    (low, high, "-", ""),
                    (high, xlim[1], "--", "_beyond"),
                ):
                    if x1 > x0:
                        ax.plot(
                            [x0, x1],
                            [c + slope * x0, c + slope * x1],
                            color=color,
                            linewidth=envelope.LINE_WIDTH,
                            linestyle=dashes,
                            gid=gid + part,
                            zorder=_layers.EDGE,
                        )
            if other["no_fit_reason"] is None:
                c, slope = other["cohesion"], other["line_slope"]
                ax.plot(
                    xlim,
                    [c + slope * x for x in xlim],
                    color=color,
                    linewidth=OTHER_WIDTH,
                    linestyle=":",
                    alpha=OTHER_ALPHA,
                    gid=f"{s}_{other['line_kind']}",
                    zorder=_layers.EDGE,
                )
    if not kinds:
        return []
    return [
        Line2D(
            [],
            [],
            color=LEGEND_COLOR,
            linewidth=envelope.LINE_WIDTH,
            label=KIND_TEXT[kinds[0]] + " (dashed beyond the points)",
        ),
        Line2D(
            [],
            [],
            color=LEGEND_COLOR,
            linewidth=OTHER_WIDTH,
            linestyle=":",
            alpha=OTHER_ALPHA,
            label=KIND_TEXT[kinds[1]],
        ),
    ]
