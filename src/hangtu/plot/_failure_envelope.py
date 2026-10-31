"""P11 failure envelope (docs/plots/P11-failure-envelope.md)."""

import math
from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Arc

from hangtu._settings import _display_units, settings
from hangtu.analysis._mohr_coulomb import MohrCoulombFit, mohr_coulomb_fit
from hangtu.errors import HangtuError
from hangtu.plot import _layers, _values, style
from hangtu.plot._labels import axis_label
from hangtu.plot._legend import add_legend
from hangtu.plot._limits import nice_limits
from hangtu.plot._notes import Notes
from hangtu.plot._spt_profile import _check_choice

SPACES = ("mohr", "s_t", "p_q")
ENVELOPE_COLOR = "black"
LINE_WIDTH = 1.2
CIRCLE_WIDTH = 0.9
MARKER_SIZE = 4.0
#: Axis texts by space and stress basis: (x, y), with {p} the prime.
AXES = {
    "mohr": ("{E}normal stress, σ{p}", "Shear stress, τ"),
    "s_t": ("Mean {e}stress, s{p}", "Shear stress, t"),
    "p_q": ("Mean {e}stress, p{p}", "Deviator stress, q"),
}


def failure_envelope(
    df: pd.DataFrame,
    *,
    space: Literal["mohr", "s_t", "p_q"] = "mohr",
    stress: Literal["effective", "total"] = "effective",
    cohesion: float | None = None,
    multistage: bool = True,
    pool: str | list[str] | None = None,
    fit: bool = True,
    note: str | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes, MohrCoulombFit | None]:
    r"""Plot triaxial failure states with the fitted Mohr-Coulomb envelope (P11).

    Draws the same failure points and the same fit in one of three spaces:
    Mohr circles in σ′-τ (``"mohr"``), points in s′-t (``"s_t"``), or points
    in p′-q (``"p_q"``). The fit is ``ht.analysis.mohr_coulomb_fit()``, made
    in s′-t; the other spaces draw it transformed, never refitted:

    $$
    \tau = c' + \sigma' \tan\phi', \quad t = c' \cos\phi' + s' \sin\phi',
    \quad q = \frac{6 c' \cos\phi'}{3 - \sin\phi'}
    + p' \frac{6 \sin\phi'}{3 - \sin\phi'}
    $$

    The p′-q line is for triaxial compression. The envelope is solid over
    the range of the tangent points and dashed beyond: c′ is an intercept,
    outside the stresses tested. Equal aspect in every space, so circles are
    circles and slopes read true.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per stage with the principal stresses at failure, as
        ``p.triaxial()`` or ``ht.analysis.triaxial_failure_stresses()``.
    space : {"mohr", "s_t", "p_q"}
        The space drawn.
    stress, cohesion, multistage, pool, units
        Passed to ``ht.analysis.mohr_coulomb_fit()``, which explains them.
    fit : bool
        False draws the points or circles only, and returns None for the fit.
    note : str, optional
        Free text, added to the footnote.
    display_units : {"US", "SI"}, optional
        Stresses in psf (US) or kPa (SI); the fit is made in them. Defaults to
        ``ht.settings.display_units``.
    figsize : tuple, optional
        Figure size in inches. Defaults to ``ht.settings.figure_sizes["default"]``.
    ax : matplotlib.axes.Axes, optional
        Draw into this axes, e.g. a ``Sheet`` panel.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, ax, fit
        ``fit`` is the ``MohrCoulombFit`` drawn, or None with ``fit=False``.

    Examples
    --------
    >>> stages = p.triaxial()
    >>> fig, ax, fit = ht.plot.failure_envelope(stages)
    >>> fig, ax, fit = ht.plot.failure_envelope(stages, space="s_t")
    """
    _check_choice("space", space, SPACES)
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    system = _display_units(display_units or settings.display_units)

    with style.context(**style_overrides):
        checked = ["failure_criterion"] + (["test_type"] if stress == "total" else [])
        result = mohr_coulomb_fit(
            df,
            stress=stress,
            cohesion=cohesion,
            multistage=multistage,
            pool=pool if fit else checked,
            units=units,
            display_units=system,
        )
        if ax is None:
            fig, ax = plt.subplots(
                figsize=figsize or settings.figure_sizes["default"],
                layout="constrained",
            )
        else:
            fig = ax.figure
        style.style_axes(ax)
        notes = Notes()
        xlim, ylim = _limits(result, space)
        _set_axes(ax, space, stress, result.unit, xlim, ylim)
        xlim = ax.get_xlim()
        _draw_points(ax, result, space)
        handles = []
        if fit:
            handles += _draw_fits(ax, result, space, xlim)
        _footnote(result, notes)
        if note is not None:
            notes.add_text(str(note))
        if not any(group["fits"][0]["points"] for group in result.groups):
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
        placed = add_legend(ax, [handles], notes)
        notes.render(ax, where=placed.where, below=placed.legend)
    return fig, ax, result if fit else None


def _all(group: dict[str, Any]) -> dict[str, Any]:
    return next(fit for fit in group["fits"] if fit["stages"] == "all")


def _coordinates(space: str, point: dict[str, Any]) -> tuple[float, float]:
    """Return a failure point in the space: (s, t), or (p, q)."""
    mean, radius = point["mean_stress"], point["radius"]
    if space == "p_q":
        return mean - radius / 3, 2 * radius
    return mean, radius


def _line(space: str, cohesion: float, angle: float) -> tuple[float, float]:
    """Return an envelope's intercept and slope in the space (P11 §4)."""
    sine, cosine = math.sin(angle), math.cos(angle)
    if space == "mohr":
        return cohesion, math.tan(angle)
    if space == "s_t":
        return cohesion * cosine, sine
    return 6 * cohesion * cosine / (3 - sine), 6 * sine / (3 - sine)


def _limits(
    result: MohrCoulombFit, space: str
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return the axes' limits: from 0, past the largest σ1, s or p (P11 §6)."""
    points = [point for group in result.groups for point in _all(group)["points"]]
    if not points:
        return (0.0, 1.0), (0.0, 1.0)
    minor = np.array([point["minor_principal_stress"] for point in points])
    xy = np.array([_coordinates(space, point) for point in points])
    x_high = (
        max(point["major_principal_stress"] for point in points)
        if space == "mohr"
        else float(xy[:, 0].max())
    )
    x_low = min(0.0, float(minor.min()))
    xlim = nice_limits(x_low, x_high, start_at_zero=True)
    ylim = nice_limits(0.0, float(xy[:, 1].max()), start_at_zero=True)
    return xlim, ylim


def _set_axes(
    ax: Axes,
    space: str,
    stress: str,
    unit: str | None,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
) -> None:
    effective = stress == "effective"
    words = {
        "p": "′" if effective else "",
        "e": "effective " if effective else "",
        "E": "Effective normal stress, σ′" if effective else "Normal stress, σ",
    }
    x_text, y_text = AXES[space]
    if space == "mohr":
        x_text = words["E"]
    ax.set_xlabel(axis_label(x_text.format(**words), unit))
    ax.set_ylabel(axis_label(y_text, unit))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, which="major")
    # Equal aspect leaves one axis short of the space it has; extend it
    # (P11 §6), which also gives the result box room above the envelope.
    ax.figure.draw_without_rendering()
    box = ax.get_position(original=True)
    width, height = ax.figure.get_size_inches()
    ratio = (box.height * height) / (box.width * width)
    if ylim[0] + (xlim[1] - xlim[0]) * ratio > ylim[1]:
        ax.set_ylim(ylim[0], ylim[0] + (xlim[1] - xlim[0]) * ratio)
    else:
        ax.set_xlim(xlim[0], xlim[0] + (ylim[1] - ylim[0]) / ratio)


def _draw_points(ax: Axes, result: MohrCoulombFit, space: str) -> None:
    """Draw each stage: a circle and its top in ``mohr``, else a point."""
    for group in result.groups:
        for point in _all(group)["points"]:
            x, y = _coordinates(space, point)
            if space == "mohr":
                ax.add_patch(
                    Arc(
                        (point["mean_stress"], 0.0),
                        2 * point["radius"],
                        2 * point["radius"],
                        theta1=0.0,
                        theta2=180.0,
                        color=_values.NEUTRAL,
                        linewidth=CIRCLE_WIDTH,
                        gid="mohr_circle",
                        zorder=_layers.MARKERS,
                    )
                )
            ax.plot(
                [x],
                [y],
                marker="o",
                markersize=MARKER_SIZE,
                color=_values.NEUTRAL,
                linestyle="none",
                gid="failure_point",
                zorder=_layers.MARKERS,
            )


def _draw_fits(
    ax: Axes,
    result: MohrCoulombFit,
    space: str,
    xlim: tuple[float, float],
) -> list[Line2D]:
    """Draw the envelope: solid over the fitted range, dashed beyond."""
    handles = []
    color = ENVELOPE_COLOR
    for group in result.groups:
        main, *others = group["fits"]
        if main["no_fit_reason"] is None:
            intercept, slope = _line(
                space, main["cohesion"], math.radians(main["friction_angle"])
            )
            low, high = _fitted_range(space, main, slope)
            for x0, x1, dashes, gid in (
                (xlim[0], low, "--", "envelope_beyond"),
                (low, high, "-", "envelope"),
                (high, xlim[1], "--", "envelope_beyond"),
            ):
                if x1 > x0:
                    ax.plot(
                        [x0, x1],
                        [intercept + slope * x0, intercept + slope * x1],
                        color=color,
                        linewidth=LINE_WIDTH,
                        linestyle=dashes,
                        gid=gid,
                        zorder=_layers.EDGE,
                    )
            handles.append(
                Line2D(
                    [],
                    [],
                    color=color,
                    linewidth=LINE_WIDTH,
                    label="Fit",
                )
            )
        for other in others:
            if other["no_fit_reason"] is not None or _same_fit(main, other):
                continue
            intercept, slope = _line(
                space, other["cohesion"], math.radians(other["friction_angle"])
            )
            text = (
                "Fit without multistage stages"
                if other["stages"] == "single_stage"
                else "Fit with multistage stages"
            )
            handles += ax.plot(
                xlim,
                [intercept + slope * x for x in xlim],
                color=color,
                linewidth=LINE_WIDTH,
                linestyle=":",
                gid="envelope_other",
                label=text,
                zorder=_layers.EDGE,
            )
    return handles


def _same_fit(first: dict[str, Any], second: dict[str, Any]) -> bool:
    return first["no_fit_reason"] is None and np.allclose(
        [first["cohesion"], first["friction_angle"]],
        [second["cohesion"], second["friction_angle"]],
    )


def _fitted_range(space: str, fit: dict[str, Any], slope: float) -> tuple[float, float]:
    """Return the tangent points' range on the space's x axis (P11 §4).

    σ′n and p′ of the tangent points both rise with s′, so the lowest and
    highest come from the points of lowest and highest s′.
    """
    if space == "mohr":
        return fit["lowest_normal_stress"], fit["highest_normal_stress"]
    means = [point["mean_stress"] for point in fit["points"]]
    ends = []
    for mean in (min(means), max(means)):
        radius = fit["line_intercept"] + fit["line_slope"] * mean
        ends.append(mean if space == "s_t" else mean - radius / 3)
    return ends[0], ends[1]


def _footnote(result: MohrCoulombFit, notes: Notes) -> None:
    """Count the rows left out, as the result does (P11 §8)."""
    totals = {"principal": 0, "effective": 0, "multistage": 0}
    for group in result.groups:
        everything, main = _all(group), group["fits"][0]
        totals["principal"] += everything["count_no_principal_stresses"]
        totals["effective"] += everything["count_no_effective_stresses"]
        totals["multistage"] += main["count_multistage_left_out"]
    parts = [
        text.format(n=totals[name])
        for name, text in (
            ("principal", "{n} without principal stresses"),
            ("effective", "{n} without effective stresses"),
            ("multistage", "{n} multistage stages from the main fit"),
        )
        if totals[name]
    ]
    if parts:
        notes.add_text("Left out: " + ", ".join(parts))
