"""P04 plasticity chart (docs/plots/P04-plasticity-chart.md)."""

import math
from dataclasses import dataclass
from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
from matplotlib.ticker import MultipleLocator

from hangtu._settings import _display_units, settings
from hangtu.analysis._plasticity import plasticity_system
from hangtu.errors import HangtuError
from hangtu.plot import _layers, _values, style
from hangtu.plot._legend import add_legend
from hangtu.plot._notes import Notes
from hangtu.plot._spt_profile import _check_choice

SYSTEMS = ("uscs", "bs5930")
X_LIMITS = (0.0, 100.0)
Y_LIMITS = (0.0, 60.0)
X_STEP = 20.0  # x extends in these steps for an LL above 100 (§6)
TICK_STEP = 10.0
LINE_COLOR = "black"
LINE_WIDTH = 0.8
EQUALITY_COLOR = "0.6"  # the PI = LL line
LABEL_SIZE = 8
LABEL_COLOR = "0.4"
HATCH = "////"

#: A half-plane a * LL + b * PI <= c.
HalfPlane = tuple[float, float, float]
Box = tuple[float, float, float, float]  # x0, x1, y0, y1


@dataclass(frozen=True)
class Zone:
    """A class's area on the chart: one or more convex pieces, as half-planes."""

    name: str
    pieces: tuple[tuple[HalfPlane, ...], ...]


def _left_of(liquid_limit: float) -> HalfPlane:
    return (1.0, 0.0, liquid_limit)


def _right_of(liquid_limit: float) -> HalfPlane:
    return (-1.0, 0.0, -liquid_limit)


def _below(plasticity_index: float) -> HalfPlane:
    return (0.0, 1.0, plasticity_index)


def _above(plasticity_index: float) -> HalfPlane:
    return (0.0, -1.0, -plasticity_index)


def _above_line(slope: float, intercept: float) -> HalfPlane:
    """PI >= slope * (LL - intercept)."""
    return (slope, -1.0, slope * intercept)


def _below_line(slope: float, intercept: float) -> HalfPlane:
    """PI <= slope * (LL - intercept)."""
    return (-slope, 1.0, -slope * intercept)


#: PI can't exceed LL.
_NOT_ABOVE_EQUALITY = _below_line(1.0, 0.0)


def zones(system: str) -> list[Zone]:
    """Return the chart's zones, built from ``config/plasticity_systems.yaml``.

    Each zone is the area ``plasticity()`` gives that class, so the drawing
    and the classes can't disagree (P04 §4). USCS zones are bounded on the
    left and above by the U-line; BS 5930 zones by PI = LL.
    """
    config = plasticity_system(system)
    a = (config["a_line"]["slope"], config["a_line"]["intercept"])
    if system == "bs5930":
        bands = config["bands"]
        result = []
        for i, band in enumerate(bands):
            sides = [_right_of(band["lower"]), _above(0.0)]
            if i + 1 < len(bands):
                sides.append(_left_of(bands[i + 1]["lower"]))
            result.append(
                Zone(
                    "C" + band["name"],
                    ((*sides, _above_line(*a), _NOT_ABOVE_EQUALITY),),
                )
            )
            result.append(Zone("M" + band["name"], ((*sides, _below_line(*a)),)))
        return result
    u_line = config["u_line"]
    u = (u_line["slope"], u_line["intercept"])
    inside = (_right_of(u_line["vertical"]["liquid_limit"]), _below_line(*u))
    high = config["high_plasticity_from"]
    silty = config["silty_clay"]
    low = (*inside, _left_of(high))
    return [
        Zone("CL", ((*low, _above(config["clay_above"]), _above_line(*a)),)),
        Zone(
            "CL-ML",
            ((*low, _above(silty["lower"]), _below(silty["upper"]), _above_line(*a)),),
        ),
        # ML is not convex: below the A-line, plus the strip under CL-ML.
        Zone(
            "ML",
            (
                (*low, _above(0.0), _below_line(*a)),
                (*low, _above(0.0), _below(silty["lower"]), _above_line(*a)),
            ),
        ),
        Zone("CH", ((*inside, _right_of(high), _above_line(*a)),)),
        Zone("MH", ((*inside, _right_of(high), _above(0.0), _below_line(*a)),)),
    ]


def _clip(vertices: list[tuple[float, float]], side: HalfPlane) -> list:
    """Clip a convex polygon by one half-plane (Sutherland-Hodgman)."""
    a, b, c = side
    result = []
    for i, current in enumerate(vertices):
        previous = vertices[i - 1]
        here = a * current[0] + b * current[1] - c
        there = a * previous[0] + b * previous[1] - c
        if (here <= 0) != (there <= 0):
            t = there / (there - here)
            result.append(
                (
                    previous[0] + t * (current[0] - previous[0]),
                    previous[1] + t * (current[1] - previous[1]),
                )
            )
        if here <= 0:
            result.append(current)
    return result


def _area_and_centroid(vertices: np.ndarray) -> tuple[float, np.ndarray]:
    x, y = vertices[:, 0], vertices[:, 1]
    cross = x * np.roll(y, -1) - np.roll(x, -1) * y
    area = cross.sum() / 2
    if abs(area) < 1e-12:
        return 0.0, vertices.mean(axis=0)
    cx = ((x + np.roll(x, -1)) * cross).sum() / (6 * area)
    cy = ((y + np.roll(y, -1)) * cross).sum() / (6 * area)
    return abs(area), np.array([cx, cy])


def zone_polygons(zone: Zone, box: Box) -> list[np.ndarray]:
    """Return the zone's pieces clipped to ``box``, each as an (n, 2) array.

    Pieces with no area inside the box are left out.
    """
    x0, x1, y0, y1 = box
    polygons = []
    for piece in zone.pieces:
        vertices = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for side in piece:
            vertices = _clip(vertices, side)
            if not vertices:
                break
        if len(vertices) >= 3:
            array = np.array(vertices, dtype=float)
            if _area_and_centroid(array)[0] > 1e-9:
                polygons.append(array)
    return polygons


def zone_label_position(zone: Zone, box: Box) -> np.ndarray | None:
    """Return the centroid of the zone's largest piece in ``box``, or None."""
    polygons = zone_polygons(zone, box)
    if not polygons:
        return None
    measured = [_area_and_centroid(polygon) for polygon in polygons]
    return max(measured, key=lambda item: item[0])[1]


def _line(ax: Axes, x: Any, y: Any, gid: str, **style_: Any) -> None:
    style_ = {"color": LINE_COLOR, "linewidth": LINE_WIDTH, **style_}
    ax.plot(x, y, gid=gid, zorder=_layers.CHART_LINES, **style_)


def _line_label(
    ax: Axes, text: str, start: tuple[float, float], slope: float, box: Box
) -> None:
    """Write ``text`` along a line, rotated to its angle, near its visible end."""
    x0, x1, y0, y1 = box
    end_x = min(x1, start[0] + (y1 - start[1]) / slope)
    x = start[0] + 0.85 * (end_x - start[0])
    y = start[1] + slope * (x - start[0])
    if not (x0 <= x <= x1 and y0 <= y <= y1):
        return
    ax.text(
        x,
        y,
        text,
        rotation=math.degrees(math.atan(slope)),
        rotation_mode="anchor",
        transform_rotates_text=True,
        ha="right",
        va="bottom",
        fontsize=LABEL_SIZE,
        color=LABEL_COLOR,
        gid="line_label",
        clip_on=True,
        zorder=_layers.ZONE_LABELS,
    )


def _sloped_end(slope: float, intercept: float, box: Box) -> tuple[float, float]:
    """Where PI = slope (LL - intercept) leaves the top or right of ``box``."""
    x1, y1 = box[1], box[3]
    x = min(x1, intercept + y1 / slope)
    return x, slope * (x - intercept)


def _draw_uscs(ax: Axes, box: Box) -> None:
    config = plasticity_system("uscs")
    slope, intercept = config["a_line"]["slope"], config["a_line"]["intercept"]
    silty = config["silty_clay"]
    # The A-line starts where it meets the bottom of CL-ML (§4).
    start = (intercept + silty["lower"] / slope, float(silty["lower"]))
    end = _sloped_end(slope, intercept, box)
    _line(ax, [start[0], end[0]], [start[1], end[1]], "a_line")
    _line_label(ax, "A-line", start, slope, box)

    u_line = config["u_line"]
    u_slope, u_intercept = u_line["slope"], u_line["intercept"]
    vertical = float(u_line["vertical"]["liquid_limit"])
    # The vertical part ends where the sloped part starts, 0.9 x (16 - 8) = 7.2,
    # not at D2487's rounded 7 (P04 §14 #1).
    joint = u_slope * (vertical - u_intercept)
    u_end = _sloped_end(u_slope, u_intercept, box)
    _line(ax, [vertical, vertical, u_end[0]], [0.0, joint, u_end[1]], "u_line")
    _line_label(ax, "U-line", (vertical, joint), u_slope, box)

    high = float(config["high_plasticity_from"])
    _line(ax, [high, high], [0.0, u_slope * (high - u_intercept)], "divider")

    for zone in zones("uscs"):
        if zone.name != "CL-ML":
            continue
        for polygon in zone_polygons(zone, box):
            ax.add_patch(
                Polygon(
                    polygon,
                    closed=True,
                    facecolor="none",
                    edgecolor=LINE_COLOR,
                    linewidth=LINE_WIDTH,
                    hatch=HATCH,
                    gid="cl_ml",
                    zorder=_layers.ZONES,
                )
            )


def _draw_bs5930(ax: Axes, box: Box) -> None:
    config = plasticity_system("bs5930")
    slope, intercept = config["a_line"]["slope"], config["a_line"]["intercept"]
    end = _sloped_end(slope, intercept, box)
    _line(ax, [intercept, end[0]], [0.0, end[1]], "a_line")
    _line_label(ax, "A-line", (float(intercept), 0.0), slope, box)

    bands = config["bands"]
    x0, x1, _, y1 = box
    for i, band in enumerate(bands):
        lower = float(band["lower"])
        if lower > 0:
            _line(ax, [lower, lower], [0.0, lower], "divider")
        upper = float(bands[i + 1]["lower"]) if i + 1 < len(bands) else x1
        middle = (max(lower, x0) + min(upper, x1)) / 2
        if x0 < middle < x1:
            ax.annotate(
                band["name"],
                xy=(middle, y1),
                xytext=(0, 2),
                textcoords="offset points",
                ha="center",
                va="bottom",
                annotation_clip=False,
                fontsize=LABEL_SIZE,
                color=LABEL_COLOR,
                gid="band_label",
                zorder=_layers.ZONE_LABELS,
            )


def _draw_zone_labels(ax: Axes, system: str, box: Box) -> None:
    for zone in zones(system):
        position = zone_label_position(zone, box)
        if position is None:
            continue
        ax.text(
            *position,
            zone.name,
            ha="center",
            va="center",
            fontsize=LABEL_SIZE,
            color=LABEL_COLOR,
            gid="zone_label",
            clip_on=True,
            # The CL-ML label sits on the hatch.
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.0},
            zorder=_layers.ZONE_LABELS,
        )


def _set_axes(ax: Axes, box: Box) -> None:
    x0, x1, y0, y1 = box
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_locator(MultipleLocator(TICK_STEP))
    ax.grid(True, which="major")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Liquid limit, LL (%)")
    ax.set_ylabel("Plasticity index, PI")


def _box(xlim: Any, ylim: Any) -> Box:
    x0, x1 = _values.check_limits("xlim", xlim) if xlim is not None else X_LIMITS
    y0, y1 = _values.check_limits("ylim", ylim) if ylim is not None else Y_LIMITS
    return x0, x1, y0, y1


def plasticity_chart(
    df: pd.DataFrame,
    *,
    system: Literal["uscs", "bs5930"] = "uscs",
    color_by: str | None = "geology_unit",
    order: list[str] | None = None,
    labels: bool = False,
    zone_labels: bool = True,
    regions: pd.DataFrame | str | None = None,
    region_colors: dict[str, str] | None = None,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    note: str | None = None,
    palette: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes]:
    """Plot liquid limit against plasticity index on the Casagrande chart (P04).

    Parameters
    ----------
    df : pandas.DataFrame
        One row per specimen, as ``ht.template("atterberg")`` or
        ``p.atterberg()``.
    system : {"uscs", "bs5930"}
        The lines and zones: ASTM D2487 or BS 5930, from
        ``config/plasticity_systems.yaml``.
    zone_labels : bool
        Name each zone (CL, CH, ML, ...).
    xlim, ylim : tuple, optional
        Axis limits, exactly. The aspect stays equal.
    note : str, optional
        Free text, added to the footnote.
    display_units : {"US", "SI"}, optional
        Accepted for the plot contract. LL and PI are percentages, so it
        changes nothing.
    figsize : tuple, optional
        Figure size in inches. Defaults to ``ht.settings.figure_sizes["default"]``.
    ax : matplotlib.axes.Axes, optional
        Draw into this axes, e.g. a ``Sheet`` panel.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, ax
    """
    _check_choice("system", system, SYSTEMS)
    _display_units(display_units or settings.display_units)
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if regions is not None or region_colors is not None:
        raise NotImplementedError("regions= is not built yet.")
    if labels:
        raise NotImplementedError("labels= is not built yet.")
    if len(df):
        raise NotImplementedError("Drawing specimens is not built yet.")
    box = _box(xlim, ylim)

    with style.context(**style_overrides):
        notes = Notes()
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
        _set_axes(ax, box)

        x0, x1, y0, y1 = box
        top = min(x1, y1)
        if top > max(x0, y0):
            _line(
                ax,
                [max(x0, y0), top],
                [max(x0, y0), top],
                "equality",
                color=EQUALITY_COLOR,
                linestyle=":",
            )
        (_draw_uscs if system == "uscs" else _draw_bs5930)(ax, box)
        if zone_labels:
            _draw_zone_labels(ax, system, box)

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
        add_legend(ax, [[]], notes)
        notes.render(ax)
    return fig, ax
