"""Envelope drawing shared by P11 and P12: axes, fits, result box, footnote.

Moved from ``_failure_envelope.py`` (P11) so ``triaxial_shearing()`` (P12)
draws the same envelope, box and counts from the same fit.
"""

import math
from typing import Any

import numpy as np
from matplotlib.axes import Axes
from matplotlib.lines import Line2D

from hangtu.analysis._mohr_coulomb import MohrCoulombFit
from hangtu.errors import HangtuError
from hangtu.plot import _layers, _values
from hangtu.plot._labels import axis_label
from hangtu.plot._limits import nice_limits
from hangtu.plot._notes import Notes
from hangtu.plot._overlays import format_number

ENVELOPE_COLOR = "black"
LINE_WIDTH = 1.2
TEXT_SIZE = 7.5
#: Axis texts by space and stress basis: (x, y), with {p} the prime.
AXES = {
    "mohr": ("{E}normal stress, σ{p}", "Shear stress, τ"),
    "s_t": ("Mean {e}stress, s{p}", "Shear stress, t"),
    "p_q": ("Mean {e}stress, p{p}", "Deviator stress, q"),
}


def check_envelopes(envelopes: Any) -> list[tuple[float, float, str]]:
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


def all_stages_fit(group: dict[str, Any]) -> dict[str, Any]:
    return next(fit for fit in group["fits"] if fit["stages"] == "all")


def group_key(group: dict[str, Any]) -> Any:
    values = tuple(group["key"].values())
    return values[0] if len(values) == 1 else values


def coordinates(space: str, point: dict[str, Any]) -> tuple[float, float]:
    """Return a failure point in the space: (s, t), or (p, q)."""
    mean, radius = point["mean_stress"], point["radius"]
    if space == "p_q":
        return mean - radius / 3, 2 * radius
    return mean, radius


def line(space: str, cohesion: float, angle: float) -> tuple[float, float]:
    """Return an envelope's intercept and slope in the space (P11 §4)."""
    sine, cosine = math.sin(angle), math.cos(angle)
    if space == "mohr":
        return cohesion, math.tan(angle)
    if space == "s_t":
        return cohesion * cosine, sine
    return 6 * cohesion * cosine / (3 - sine), 6 * sine / (3 - sine)


def limits(
    result: MohrCoulombFit, space: str
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return the axes' limits: from 0, past the largest σ1, s or p (P11 §6)."""
    points = [
        point for group in result.groups for point in all_stages_fit(group)["points"]
    ]
    if not points:
        return (0.0, 1.0), (0.0, 1.0)
    minor = np.array([point["minor_principal_stress"] for point in points])
    xy = np.array([coordinates(space, point) for point in points])
    x_high = (
        max(point["major_principal_stress"] for point in points)
        if space == "mohr"
        else float(xy[:, 0].max())
    )
    x_low = min(0.0, float(minor.min()))
    xlim = nice_limits(x_low, x_high, start_at_zero=True)
    ylim = nice_limits(0.0, float(xy[:, 1].max()), start_at_zero=True)
    return xlim, ylim


def set_axes(
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


def draw_fits(
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
        label = _values.group_text(group_key(group)) if result.by else None
        color = colors[label] if label is not None and several else ENVELOPE_COLOR
        main, *others = group["fits"]
        if main["no_fit_reason"] is None:
            intercept, slope = line(
                space, main["cohesion"], math.radians(main["friction_angle"])
            )
            low, high = fitted_range(space, main, slope)
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
            if other["no_fit_reason"] is not None or same_fit(main, other):
                continue
            intercept, slope = line(
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


def same_fit(first: dict[str, Any], second: dict[str, Any]) -> bool:
    return first["no_fit_reason"] is None and np.allclose(
        [first["cohesion"], first["friction_angle"]],
        [second["cohesion"], second["friction_angle"]],
    )


def fitted_range(space: str, fit: dict[str, Any], slope: float) -> tuple[float, float]:
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


def draw_box(ax: Axes, result: MohrCoulombFit) -> None:
    """Write each group's c′, φ′, n, R², range and the lab's values (P11 §8)."""
    prime = "′" if result.stress == "effective" else ""
    unit = f" {result.unit}" if result.unit else ""
    lines = []
    for group in result.groups:
        head = f"{_values.group_text(group_key(group))}: " if result.by else ""
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


def footnote(result: MohrCoulombFit, notes: Notes) -> None:
    """Count the rows left out, as the result does (P11 §8)."""
    totals = {"principal": 0, "effective": 0, "multistage": 0}
    for group in result.groups:
        everything, main = all_stages_fit(group), group["fits"][0]
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
