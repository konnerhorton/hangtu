"""P11 failure envelope (docs/plots/P11-failure-envelope.md)."""

import math
from collections.abc import Sequence
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
from hangtu.analysis._triaxial import DRAINED
from hangtu.errors import HangtuError
from hangtu.plot import _layers, _values, style
from hangtu.plot._hints import hint_missing
from hangtu.plot._labels import axis_label
from hangtu.plot._legend import add_legend
from hangtu.plot._limits import nice_limits
from hangtu.plot._notes import Notes
from hangtu.plot._overlays import format_number
from hangtu.plot._palette import resolve_palette
from hangtu.plot._spt_profile import _check_choice

SPACES = ("mohr", "s_t", "p_q")
PATHS = ("idealized_drained",)
ENVELOPE_COLOR = "black"
USER_ENVELOPE_COLOR = "0.55"
LINE_WIDTH = 1.2
CIRCLE_WIDTH = 0.9
PATH_WIDTH = 0.7
MARKER_SIZE = 4.0
TEXT_SIZE = 7.5
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
    group_by: str | list[str] | None = None,
    color_by: str | None = None,
    cohesion: float | None = None,
    multistage: bool = True,
    pool: str | list[str] | None = None,
    fit: bool = True,
    paths: Literal["idealized_drained"] | None = None,
    result_box: bool = True,
    envelopes: Sequence[tuple[float, float, str]] | None = None,
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
    outside the stresses tested. A box gives each group's c′, φ′, n, R², the
    fitted range, and the lab's own values where the rows have them. Equal
    aspect in every space, so circles are circles and slopes read true.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per stage with the principal stresses at failure, as
        ``p.triaxial()`` or ``ht.analysis.triaxial_failure_stresses()``.
    space : {"mohr", "s_t", "p_q"}
        The space drawn.
    stress, group_by, cohesion, multistage, pool, units
        Passed to ``ht.analysis.mohr_coulomb_fit()``, which explains them.
    color_by : str, optional
        Colors circles and points when there is no ``group_by``. Defaults to
        ``geology_unit`` when the rows have it. An error with ``group_by``:
        each fit has one color.
    fit : bool
        False draws the points or circles only, and returns None for the fit.
    paths : {"idealized_drained"}, optional
        In ``s_t`` and ``p_q``, each stage's path as a drained compression test
        at constant cell pressure would have taken it, from (σ′3, 0): slope 1
        in s′-t, 3 in p′-q. Not the measured path, and labeled so. Only for
        drained tests (``CD``, ``CDM``, ``CIDC``, ``CADC``); a blank type is
        drawn as "assumed CD".
    result_box : bool
        Write the fit's numbers in the upper left.
    envelopes : list of (cohesion, friction_angle, label), optional
        Your own envelopes, cohesion in the display units and the angle in
        degrees, transformed into the space like the fit.
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
    >>> fig, ax, fit = ht.plot.failure_envelope(
    ...     stages, space="s_t", group_by="geology_unit"
    ... )
    >>> fig, ax, fit = ht.plot.failure_envelope(
    ...     stages, space="p_q", paths="idealized_drained"
    ... )
    """
    _check_choice("space", space, SPACES)
    if paths is not None:
        _check_choice("paths", paths, PATHS)
        if space == "mohr":
            raise HangtuError(
                'paths= draws stress paths in s′-t or p′-q: use space="s_t" or '
                'space="p_q", or leave paths=None for Mohr circles.'
            )
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if group_by is not None and color_by is not None:
        raise HangtuError(
            "color_by= can't be used with group_by=: each fit is drawn in its "
            "group's color. Use one or the other."
        )
    user_envelopes = _check_envelopes(envelopes)
    system = _display_units(display_units or settings.display_units)
    if color_by is None and group_by is None and "geology_unit" in df.columns:
        color_by = "geology_unit"
    if color_by is not None and color_by not in df.columns:
        raise HangtuError(
            f"color_by={color_by!r}, but df has no such column. Available "
            f"columns: {', '.join(map(str, df.columns))}."
        )

    with style.context(**style_overrides):
        hint_missing(
            df,
            {
                "failure_criterion": "the fit can't check that the stages share one",
                "multistage_test": "multistage stages aren't fitted apart",
                **(
                    {"geology_unit": "the stages are drawn in one color"}
                    if group_by is None
                    else {}
                ),
            },
        )
        checked = ["failure_criterion"] + (["test_type"] if stress == "total" else [])
        result = mohr_coulomb_fit(
            df,
            stress=stress,
            group_by=group_by,
            cohesion=cohesion,
            multistage=multistage,
            pool=pool if fit else checked,
            units=units,
            display_units=system,
        )
        if paths is not None:
            _check_drained(df, result)
        if ax is None:
            fig, ax = plt.subplots(
                figsize=figsize or settings.figure_sizes["default"],
                layout="constrained",
            )
        else:
            fig = ax.figure
        style.style_axes(ax)
        notes = Notes()
        colors = _colors(df, result, color_by)
        xlim, ylim = _limits(result, space)
        _set_axes(ax, space, stress, result.unit, xlim, ylim)
        xlim = ax.get_xlim()
        handles = _draw_points(ax, df, result, space, color_by, colors)
        if paths is not None:
            handles += _draw_paths(ax, df, result, space, color_by, colors)
        for cohesion_value, angle, label in user_envelopes:
            intercept, slope = _line(space, cohesion_value, math.radians(angle))
            handles += ax.plot(
                xlim,
                [intercept + slope * x for x in xlim],
                color=USER_ENVELOPE_COLOR,
                linewidth=LINE_WIDTH,
                label=label,
                gid="user_envelope",
                zorder=_layers.LINES,
            )
        if fit:
            handles += _draw_fits(ax, result, space, colors, xlim)
            if result_box:
                _draw_box(ax, result)
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


def _check_envelopes(envelopes: Any) -> list[tuple[float, float, str]]:
    if envelopes is None:
        return []
    checked = []
    for envelope in envelopes:
        try:
            cohesion, angle, label = envelope
            cohesion, angle = float(cohesion), float(angle)
        except (TypeError, ValueError):
            raise HangtuError(
                "envelopes= takes a list of (cohesion, friction_angle, label), "
                f'such as [(0, 30, "Design, c′ = 0, φ′ = 30°")], not {envelope!r}.'
            ) from None
        if not 0 <= angle < 90:
            raise HangtuError(
                f"envelopes= has a friction angle of {angle:g}° in {label!r}; it "
                "must be from 0 to below 90 degrees."
            )
        checked.append((cohesion, angle, str(label)))
    return checked


def _check_drained(df: pd.DataFrame, result: MohrCoulombFit) -> None:
    """Raise if a drawn stage isn't a drained test (P11 §11)."""
    if "test_type" not in df.columns:
        return
    types = df["test_type"]
    named = {
        str(value)
        for value in types.loc[_rows(result)].dropna()
        if str(value).strip() and str(value) not in DRAINED
    }
    if named:
        raise HangtuError(
            f"paths='idealized_drained' draws the path of a drained test at "
            f"constant cell pressure, but the stages include {sorted(named)}, "
            "whose paths differ: it would mislead. Draw only the drained stages "
            f"({', '.join(sorted(DRAINED))}), or leave paths=None."
        )


def _rows(result: MohrCoulombFit) -> list[Any]:
    """Return the index labels of every stage drawn (each group's "all" fit)."""
    return [point["row"] for group in result.groups for point in _all(group)["points"]]


def _all(group: dict[str, Any]) -> dict[str, Any]:
    return next(fit for fit in group["fits"] if fit["stages"] == "all")


def _colors(
    df: pd.DataFrame, result: MohrCoulombFit, color_by: str | None
) -> dict[Any, Any]:
    """Return ``{group or color_by value: color}``."""
    if result.by:
        labels = [_values.group_text(_key(group)) for group in result.groups]
        if len(labels) == 1:
            return {labels[0]: ENVELOPE_COLOR}
        return resolve_palette(labels, None, labels, df.attrs.get("palette"))
    _, colors = _values.color_groups(df, color_by, None)
    return colors


def _key(group: dict[str, Any]) -> Any:
    values = tuple(group["key"].values())
    return values[0] if len(values) == 1 else values


def _point_color(
    df: pd.DataFrame,
    group: dict[str, Any],
    row: Any,
    color_by: str | None,
    colors: dict[Any, Any],
) -> tuple[Any, Any]:
    """Return the legend label and color of one stage."""
    if group["key"]:
        label = _values.group_text(_key(group))
        return label, colors[label]
    if color_by is None:
        return None, colors[None]
    value = df.at[row, color_by]
    label = _values.BLANK_GROUP if pd.isna(value) else value
    return label, colors[label]


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


def _draw_points(
    ax: Axes,
    df: pd.DataFrame,
    result: MohrCoulombFit,
    space: str,
    color_by: str | None,
    colors: dict[Any, Any],
) -> list[Line2D]:
    """Draw each stage: a circle and its top in ``mohr``, else a point."""
    seen: dict[Any, Line2D] = {}
    for group in result.groups:
        for point in _all(group)["points"]:
            label, color = _point_color(df, group, point["row"], color_by, colors)
            x, y = _coordinates(space, point)
            if space == "mohr":
                ax.add_patch(
                    Arc(
                        (point["mean_stress"], 0.0),
                        2 * point["radius"],
                        2 * point["radius"],
                        theta1=0.0,
                        theta2=180.0,
                        color=color,
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
                color=color,
                linestyle="none",
                gid="failure_point",
                zorder=_layers.MARKERS,
            )
            if label is not None and label not in seen:
                seen[label] = _values.legend_marker(
                    "o", color, _values.group_text(label), MARKER_SIZE
                )
    return list(seen.values()) if len(seen) > 1 or result.by else []


def _draw_paths(
    ax: Axes,
    df: pd.DataFrame,
    result: MohrCoulombFit,
    space: str,
    color_by: str | None,
    colors: dict[Any, Any],
) -> list[Line2D]:
    """Draw each stage's idealized drained path from (σ′3, 0) (P11 §4)."""
    typed = "test_type" in df.columns
    assumed = False
    for group in result.groups:
        for point in _all(group)["points"]:
            _, color = _point_color(df, group, point["row"], color_by, colors)
            if not typed or pd.isna(df.at[point["row"], "test_type"]):
                assumed = True
            x, y = _coordinates(space, point)
            ax.plot(
                [point["minor_principal_stress"], x],
                [0.0, y],
                color=color,
                linewidth=PATH_WIDTH,
                linestyle="--",
                gid="idealized_path",
                zorder=_layers.CONNECT,
            )
    label = "Idealized drained path" + (" (assumed CD)" if assumed else "")
    return [Line2D([], [], color="0.3", linewidth=PATH_WIDTH, ls="--", label=label)]


def _draw_fits(
    ax: Axes,
    result: MohrCoulombFit,
    space: str,
    colors: dict[Any, Any],
    xlim: tuple[float, float],
) -> list[Line2D]:
    """Draw each group's envelope: solid over the fitted range, dashed beyond."""
    handles = []
    several = len(result.groups) > 1
    for group in result.groups:
        label = _values.group_text(_key(group)) if result.by else None
        color = colors[label] if label is not None and several else ENVELOPE_COLOR
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
                    label="Fit" + (f", {label}" if label is not None else ""),
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
                label=text + (f", {label}" if label is not None else ""),
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


def _draw_box(ax: Axes, result: MohrCoulombFit) -> None:
    """Write each group's c′, φ′, n, R², range and the lab's values (P11 §8)."""
    prime = "′" if result.stress == "effective" else ""
    unit = f" {result.unit}" if result.unit else ""
    lines = []
    for group in result.groups:
        head = f"{_values.group_text(_key(group))}: " if result.by else ""
        for i, fit in enumerate(group["fits"]):
            lead = head if i == 0 else "  without multistage: "
            if i and fit["stages"] == "all":
                lead = "  with multistage: "
            if fit["no_fit_reason"] is not None:
                lines.append(f"{lead}no fit: {fit['no_fit_reason']}")
                continue
            sign = f" (c{prime} < 0)" if fit["cohesion"] < 0 else ""
            values = (
                f"c{prime} = {format_number(fit['cohesion'])}{unit}{sign}, "
                f"φ{prime} = {fit['friction_angle']:.1f}°"
            )
            if i:
                lines.append(lead + values)
                continue
            r_squared = (
                "—" if math.isnan(fit["r_squared"]) else f"{fit['r_squared']:.3f}"
            )
            lines.append(f"{lead}{values}, n = {fit['count']}, R² = {r_squared}")
            lines.append(
                f"  σ{prime}n {format_number(fit['lowest_normal_stress'])} to "
                f"{format_number(fit['highest_normal_stress'])}{unit}"
            )
            for pair in fit["reported_pairs"] or []:
                stages = f"{pair['count']} stage{'s' if pair['count'] > 1 else ''}"
                lines.append(
                    f"  Lab: c′ = {pair['cohesion']:g}{unit}, "
                    f"φ′ = {pair['friction_angle']:.1f}° ({stages})"
                )
    ax.annotate(
        "\n".join(lines),
        xy=(0.02, 0.98),
        xycoords="axes fraction",
        ha="left",
        va="top",
        fontsize=TEXT_SIZE,
        color="0.15",
        gid="result_box",
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": "white",
            "edgecolor": "0.7",
            "linewidth": 0.5,
        },
        zorder=_layers.ANNOTATIONS,
    )


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
