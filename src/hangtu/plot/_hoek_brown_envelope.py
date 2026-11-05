"""P32 Hoek-Brown envelope (docs/plots/P32-hoek-brown-envelope.md)."""

import math
import warnings
from collections.abc import Mapping, Sequence
from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from hangtu._settings import settings
from hangtu.analysis._hoek_brown_fit import HoekBrownFit, hoek_brown_fit
from hangtu.errors import HangtuError
from hangtu.plot import _layers, _values, style
from hangtu.plot._labels import axis_label
from hangtu.plot._legend import add_legend
from hangtu.plot._limits import nice_limits
from hangtu.plot._notes import Notes, figure_of
from hangtu.plot._palette import resolve_palette

#: The column the fit checks its rows share (its decision 7).
CHECKED = "failure_criterion"
LEGEND_COLOR = "black"
MARKER_SIZE = 5.0
LINE_WIDTH = 1.2
OTHER_WIDTH = 0.8
OTHER_ALPHA = 0.6
#: Points along each curve: σ1 is curved in σ3, unlike P31's straight lines.
CURVE_POINTS = 200
AXES = {
    "total": (
        "Minor principal stress at failure, σ3f",
        "Major principal stress at failure, σ1f",
    ),
    "effective": (
        "Effective minor principal stress at failure, σ′3f",
        "Effective major principal stress at failure, σ′1f",
    ),
}


def hoek_brown_envelope(
    df: pd.DataFrame,
    *,
    group_by: str | list[str] | None = None,
    color_by: str | None = None,
    failure_modes: Sequence[str | None] | None = None,
    fixed_intact_compressive_strength: str | Mapping[Any, str] | None = None,
    judgments: Any = None,
    multistage: bool = True,
    stress: Literal["total", "effective"] = "total",
    pool: str | list[str] | None = None,
    fit: bool = True,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes, HoekBrownFit | None]:
    r"""Plot rock UCS and triaxial tests in σ1-σ3 with the Hoek-Brown curves (P32).

    Each test is a point at its principal stresses at failure, a UCS test on
    the σ1 axis. The curves are ``ht.analysis.hoek_brown_fit()``'s, drawn,
    never refitted, from the intact criterion (Hoek 2007, ch. 11, eq. 5):

    $$
    \sigma_1 = \sigma_3 + \sigma_{ci}
    \left(m_i \frac{\sigma_3}{\sigma_{ci}} + 1\right)^{0.5}
    $$

    The free curve is solid over the σ3 its points cover and dashed beyond,
    so σ1 past the last test reads as extrapolation. The curve with σci
    fixed is thin and dotted, so the two compare. Points the fit left out
    for their failure mode (or, with ``multistage=False``, multistage
    stages) are drawn open, with their reason in the legend. Single-stage
    points are circles and multistage stages squares.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per stage at failure, a UCS test with a cell pressure of 0:
        a CSV in ``ht.template("triaxial")``'s shape through
        ``ht.analysis.triaxial_failure_stresses()``, or ``p.triaxial()``.
    group_by, failure_modes, fixed_intact_compressive_strength, judgments, \
multistage, stress, pool, units
        Passed to ``ht.analysis.hoek_brown_fit()``, which explains them.
    color_by : str, optional
        Colors the points when there is no ``group_by``. Defaults to
        ``geology_unit`` when the rows have it. An error with ``group_by``:
        each set of curves has one color.
    fit : bool
        False draws the points only, and returns None for the fit.
    display_units : {"US", "SI"}, optional
        Stresses in psf (US) or kPa (SI), or the unit
        ``ht.settings.display_overrides["stress"]`` names (psi, MPa); the fit
        is made in them. None keeps the frame's unit, as rock is often in
        MPa already.
    figsize : tuple, optional
        Figure size in inches. Defaults to ``ht.settings.figure_sizes["default"]``.
    ax : matplotlib.axes.Axes, optional
        Draw into this axes, e.g. a ``Sheet`` panel.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, ax, fit
        ``fit`` is the ``HoekBrownFit`` drawn, or None with ``fit=False``.

    Examples
    --------
    >>> rock = ht.analysis.triaxial_failure_stresses(
    ...     ht.read_csv(ht.examples.path("rock_triaxial.csv"), units={...})
    ... )
    >>> fig, ax, fit = ht.plot.hoek_brown_envelope(
    ...     rock,
    ...     group_by="geology_unit",
    ...     failure_modes=["Shear"],
    ...     judgments=ht.examples.path("judgments.yaml"),
    ... )
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if group_by is not None and color_by is not None:
        raise HangtuError(
            "color_by= can't be used with group_by=: each set of curves is drawn in "
            "its group's color. Use one or the other."
        )
    if color_by is None and group_by is None and "geology_unit" in df.columns:
        color_by = "geology_unit"
    if color_by is not None and color_by not in df.columns:
        raise HangtuError(
            f"color_by={color_by!r}, but df has no such column. Available "
            f"columns: {', '.join(map(str, df.columns))}."
        )

    with style.context(**style_overrides):
        with warnings.catch_warnings():
            if not fit:  # no curve is drawn, so its warnings would mislead
                warnings.simplefilter("ignore")
            result = hoek_brown_fit(
                df,
                group_by=group_by,
                failure_modes=failure_modes,
                fixed_intact_compressive_strength=fixed_intact_compressive_strength,
                judgments=judgments,
                multistage=multistage,
                stress=stress,
                pool=pool if fit or CHECKED not in df.columns else CHECKED,
                units=units,
                display_units=display_units,
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
        xlim, ylim = _limits(result, fit)
        x_text, y_text = AXES[result.stress]
        ax.set_xlabel(axis_label(x_text, result.unit))
        ax.set_ylabel(axis_label(y_text, result.unit))
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.grid(True, which="major")
        color_handles, marks = _draw_points(ax, df, result, color_by, colors)
        handles: list[Line2D] = []
        if fit:
            handles = _draw_curves(ax, result, colors, xlim) + handles
        if not marks:
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


def _major(x: np.ndarray, intercept: float, slope: float) -> np.ndarray:
    """σ1 = σ3 + (σci² + mi σci σ3)^0.5, the criterion on Hoek's line."""
    return x + np.sqrt(intercept + slope * x)


def _curve_x(low: float, high: float) -> np.ndarray:
    return np.linspace(low, high, CURVE_POINTS)


def _group_label(result: HoekBrownFit, group: dict[str, Any]) -> str | None:
    if not result.by:
        return None
    values = tuple(group["key"].values())
    return _values.group_text(values[0] if len(values) == 1 else values)


def _colors(
    df: pd.DataFrame, result: HoekBrownFit, color_by: str | None
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
    result: HoekBrownFit,
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


def _main(group: dict[str, Any], kind: str = "free") -> dict[str, Any]:
    """Return the main stage set's fit of a kind: the first stage set listed."""
    stages = group["fits"][0]["stages"]
    return next(
        fit
        for fit in group["fits"]
        if fit["stages"] == stages and fit["line_kind"] == kind
    )


def _all_stages(group: dict[str, Any]) -> dict[str, Any]:
    return next(
        fit
        for fit in group["fits"]
        if fit["stages"] == "all" and fit["line_kind"] == "free"
    )


def _drawn_points(group: dict[str, Any]) -> list[tuple[dict[str, Any], str | None]]:
    """Each point drawn, with the reason it was left out (None if fitted).

    The all-stages fit has every candidate row; a multistage stage is left
    out when the single-stage fit is the main one. Rows left out before
    fitting are drawn where they have both stresses.
    """
    main = _main(group)
    drawn: list[tuple[dict[str, Any], str | None]] = [
        (
            point,
            "multistage"
            if main["stages"] == "single_stage" and point["multistage_test"]
            else None,
        )
        for point in _all_stages(group)["points"]
    ]
    for row in group["left_out"]:
        if row["reason"] != "count_other_failure_mode":
            continue
        if math.isnan(row["minor_principal_stress"]) or math.isnan(
            row["major_principal_stress"]
        ):
            continue
        mode = row["failure_mode"]
        drawn.append((row, _values.BLANK_GROUP if mode is None else str(mode)))
    return drawn


def _fitted_curves(result: HoekBrownFit) -> list[dict[str, Any]]:
    return [
        fit
        for group in result.groups
        for fit in (_main(group), _main(group, "fixed_strength"))
        if fit["no_fit_reason"] is None
    ]


def _limits(
    result: HoekBrownFit, fit: bool
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return the axes' limits: from 0 past the largest σ3 and σ1 (P32 §6)."""
    points = [point for group in result.groups for point, _ in _drawn_points(group)]
    if not points:
        return (0.0, 1.0), (0.0, 1.0)
    x_high = max(point["minor_principal_stress"] for point in points)
    y_high = max(point["major_principal_stress"] for point in points)
    xlim = nice_limits(0.0, x_high if x_high > 0 else y_high / 4, start_at_zero=True)
    edge = np.array([xlim[1]])
    if fit:
        y_high = max(
            [
                y_high,
                *(
                    float(_major(edge, c["line_intercept"], c["line_slope"])[0])
                    for c in _fitted_curves(result)
                    if c["line_kind"] == "free"
                ),
            ]
        )
    ylim = nice_limits(0.0, y_high, start_at_zero=True)
    return xlim, ylim


def _draw_points(
    ax: Axes,
    df: pd.DataFrame,
    result: HoekBrownFit,
    color_by: str | None,
    colors: dict[Any, Any],
) -> tuple[list[Line2D], list[Line2D]]:
    """Draw each point: circles single stage, squares multistage, open if left out.

    Returns the color handles and the mark handles for the legend.
    """
    seen: dict[Any, Line2D] = {}
    shapes = {"o": False, "s": False}
    left_out: dict[str, tuple[int, str]] = {}
    for group in result.groups:
        for point, reason in _drawn_points(group):
            label, color = _point_color(
                df, result, group, point["row"], color_by, colors
            )
            marker = "s" if point.get("multistage_test") is True else "o"
            filled = reason is None
            ax.plot(
                [point["minor_principal_stress"]],
                [point["major_principal_stress"]],
                marker=marker,
                markersize=MARKER_SIZE,
                color=color,
                markerfacecolor=color if filled else "white",
                linestyle="none",
                gid="point" if filled else "left_out_point",
                clip_on=False,  # UCS points sit on the σ1 axis
                zorder=_layers.MARKERS,
            )
            if filled:
                shapes[marker] = True
            else:
                assert reason is not None  # a point is open only with a reason
                count, first = left_out.get(reason, (0, marker))
                left_out[reason] = (count + 1, first)
            if label is not None and label not in seen:
                seen[label] = _values.legend_marker(
                    "s", color, _values.group_text(label), MARKER_SIZE
                )
    marks = []
    if shapes["o"]:
        marks.append(
            _values.legend_marker("o", LEGEND_COLOR, "Single stage", MARKER_SIZE)
        )
    if shapes["s"]:
        marks.append(
            _values.legend_marker("s", LEGEND_COLOR, "Multistage", MARKER_SIZE)
        )
    for reason, (count, marker) in left_out.items():
        marks.append(
            _values.legend_marker(
                marker,
                LEGEND_COLOR,
                f"Left out: {reason} ({count})",
                MARKER_SIZE,
                filled=False,
            )
        )
    return (list(seen.values()) if len(seen) > 1 else []), marks


def _draw_curves(
    ax: Axes,
    result: HoekBrownFit,
    colors: dict[Any, Any],
    xlim: tuple[float, float],
) -> list[Line2D]:
    """Draw each group's free curve, solid over its range, and the fixed one."""
    several = len(result.groups) > 1
    drawn = {"free": False, "fixed_strength": False}
    for group in result.groups:
        label = _group_label(result, group)
        color = colors[label] if label is not None and several else LEGEND_COLOR
        free, fixed = _main(group), _main(group, "fixed_strength")
        if free["no_fit_reason"] is None:
            drawn["free"] = True
            a, b = free["line_intercept"], free["line_slope"]
            low = free["lowest_minor_principal_stress"]
            high = free["highest_minor_principal_stress"]
            for x0, x1, dashes, gid in (
                (xlim[0], low, "--", "free_beyond"),
                (low, high, "-", "free"),
                (high, xlim[1], "--", "free_beyond"),
            ):
                if x1 > x0:
                    x = _curve_x(x0, x1)
                    ax.plot(
                        x,
                        _major(x, a, b),
                        color=color,
                        linewidth=LINE_WIDTH,
                        linestyle=dashes,
                        gid=gid,
                        zorder=_layers.EDGE,
                    )
        if fixed["no_fit_reason"] is None:
            drawn["fixed_strength"] = True
            x = _curve_x(xlim[0], xlim[1])
            ax.plot(
                x,
                _major(x, fixed["line_intercept"], fixed["line_slope"]),
                color=color,
                linewidth=OTHER_WIDTH,
                linestyle=":",
                alpha=OTHER_ALPHA,
                gid="fixed_strength",
                zorder=_layers.EDGE,
            )
    handles = []
    if drawn["free"]:
        handles.append(
            Line2D(
                [],
                [],
                color=LEGEND_COLOR,
                linewidth=LINE_WIDTH,
                label="Free fit (dashed beyond the points)",
            )
        )
    if drawn["fixed_strength"]:
        handles.append(
            Line2D(
                [],
                [],
                color=LEGEND_COLOR,
                linewidth=OTHER_WIDTH,
                linestyle=":",
                alpha=OTHER_ALPHA,
                label="σci fixed",
            )
        )
    return handles
