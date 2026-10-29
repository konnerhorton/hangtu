"""P17 clogging diagram (docs/plots/P17-clogging-diagram.md)."""

from os import PathLike
from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import colormaps
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
from matplotlib.ticker import FixedLocator, MultipleLocator

from hangtu import _polygons
from hangtu._settings import _display_units, settings
from hangtu.analysis._clogging import (
    METHODS,
    Diagram,
    Zone,
    _check,
    _place,
    diagram,
)
from hangtu.errors import ColumnError, HangtuError
from hangtu.plot import _layers, _values, style
from hangtu.plot._hints import hint_missing
from hangtu.plot._legend import add_legend, check_legend
from hangtu.plot._notes import Notes
from hangtu.plot._plasticity_chart import _check_color_by, _draw_specimens
from hangtu.plot._spt_profile import _check_choice

PI_STEP = 10.0
IC_STEP = 0.1
#: Zone edges labeled on the Ic axis besides the 0.1 steps (§6).
IC_EDGES = (0.75,)
FILL_ALPHA = 0.2
LINE_WIDTH = 0.8
LABEL_SIZE = 8
LABEL_COLOR = "0.3"
#: Zones are colored from green (lowest potential) to red (highest), §8.
ZONE_COLORS = colormaps["RdYlGn_r"]
COLOR_RANGE = (0.1, 0.9)
#: Rows ``_place()`` leaves blank and the plot doesn't draw, by footnote reason.
NOT_DRAWN = {
    "non-plastic": "non_plastic_excluded",
    "no liquid or plastic limit": "nan",
    "a plasticity index of 0": "zero_plasticity",
    "no water content": "no_water_content",
}


def zone_colors(n: int) -> list[tuple[float, float, float, float]]:
    """Return ``n`` colors from green to red, in the zones' order."""
    if n == 1:
        return [ZONE_COLORS(COLOR_RANGE[1])]
    return [ZONE_COLORS(v) for v in np.linspace(*COLOR_RANGE, n)]


def label_position(zone: Zone) -> np.ndarray:
    """Where a zone's name goes: ``label_at``, else its centroid if inside it.

    An L-shaped zone's centroid can fall in another zone, so then the label
    goes at the vertex mean, the best simple guess.
    """
    if zone.label_at is not None:
        return zone.label_at
    centroid = _polygons.Polygon(zone.name, zone.vertices).centroid()
    if _polygons.contains(zone.vertices, centroid)[0]:
        return centroid
    return zone.vertices.mean(axis=0)


def _specimens(
    df: pd.DataFrame, figure: Diagram, labels: bool, notes: Notes
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Place the specimens; return their rows, PI and Ic (NaN where not drawn)."""
    if not len(df):
        return df, np.empty(0), np.empty(0)
    _check(df)
    if labels and "specimen_id" not in df.columns:
        raise ColumnError(
            "labels=True writes each specimen's 'specimen_id', but there is no "
            "such column. Available columns: "
            f"{', '.join(map(str, df.columns))}. Add it, or use labels=False."
        )
    data, reasons = _place(df, figure)
    hidden = np.zeros(len(df), dtype=bool)
    for reason, key in NOT_DRAWN.items():
        notes.count(reasons[reason], key)
        hidden |= reasons[reason]
    index = data["plasticity_index"].to_numpy(dtype=float)
    consistency = data["consistency_index"].to_numpy(dtype=float)
    return (
        data,
        np.where(hidden, np.nan, index),
        np.where(hidden, np.nan, consistency),
    )


def zone_counts_text(data: pd.DataFrame, figure: Diagram, drawn: np.ndarray) -> str:
    """Return the footnote line counting the drawn specimens in each zone.

    Highest potential first, e.g. "High: 4 · Medium: 3 · outside the
    diagram: 1 of 8 specimens".
    """
    names = data["clogging_potential"].to_numpy(dtype=object)[drawn]
    parts = [
        f"{zone.name[0].upper()}{zone.name[1:]}: {int((names == zone.name).sum())}"
        for zone in reversed(figure.zones)
    ]
    outside = int(pd.isna(names).sum())
    if outside:
        parts.append(f"outside the diagram: {outside}")
    total = int(drawn.sum())
    return f"{' · '.join(parts)} of {total} specimen{'' if total == 1 else 's'}"


def _box(figure: Diagram, xlim: Any, ylim: Any) -> tuple[float, float, float, float]:
    """Return the axes box: ``xlim``/``ylim`` exactly, else the method's (§6).

    User zones have no box of their own, so they get their extent.
    """
    if figure.box is not None:
        x0, x1, y0, y1 = figure.box
    else:
        vertices = np.vstack([zone.vertices for zone in figure.zones])
        (x0, y0), (x1, y1) = vertices.min(axis=0), vertices.max(axis=0)
    if xlim is not None:
        x0, x1 = _values.check_limits("xlim", xlim)
    if ylim is not None:
        y0, y1 = _values.check_limits("ylim", ylim)
    return float(x0), float(x1), float(y0), float(y1)


def _set_axes(ax: Axes, box: tuple[float, float, float, float]) -> None:
    x0, x1, y0, y1 = box
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.xaxis.set_major_locator(MultipleLocator(PI_STEP))
    steps = np.arange(np.ceil(y0 / IC_STEP - 1e-9), np.floor(y1 / IC_STEP + 1e-9) + 1)
    ticks = sorted({round(v * IC_STEP, 6) for v in steps} | set(IC_EDGES))
    ax.yaxis.set_major_locator(FixedLocator([t for t in ticks if y0 <= t <= y1]))
    ax.grid(True, which="major")
    ax.set_xlabel("Plasticity index, PI")
    ax.set_ylabel("Consistency index, Ic")


def _draw_zones(ax: Axes, figure: Diagram, zone_labels: bool) -> None:
    for zone, color in zip(figure.zones, zone_colors(len(figure.zones)), strict=True):
        ax.add_patch(
            Polygon(
                zone.vertices,
                closed=True,
                facecolor=to_rgba(color, FILL_ALPHA),
                edgecolor=color,
                linewidth=LINE_WIDTH,
                gid="clogging_zone",
                label=zone.name,
                zorder=_layers.ZONES,
            )
        )
        if zone_labels:
            ax.text(
                *label_position(zone),
                zone.name,
                ha="center",
                va="center",
                fontsize=LABEL_SIZE,
                color=LABEL_COLOR,
                gid="zone_label",
                clip_on=True,
                # Keeps the label legible over gridlines, as on P04.
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.0},
                zorder=_layers.ZONE_LABELS,
            )


def clogging_diagram(
    df: pd.DataFrame,
    *,
    method: Literal["thewes_burger_2004"] = "thewes_burger_2004",
    zones: pd.DataFrame | str | PathLike[str] | None = None,
    color_by: str | None = "geology_unit",
    order: list[str] | None = None,
    labels: bool = False,
    zone_labels: bool = True,
    zone_counts: bool = True,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    note: str | None = None,
    palette: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    legend: Literal["auto", "inside", "bottom", "right"] | bool = "auto",
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes]:
    """Plot specimens on the Thewes & Burger (2004) clay clogging diagram (P17).

    Plasticity index across, consistency index at in situ water content up,
    with the zones of ``ht.analysis.clogging_potential()``: each specimen is
    drawn in the zone of its ``clogging_potential``. The zones, their source
    and validity are in that function's docstring.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per specimen, as ``p.atterberg()``: ``water_content``,
        ``liquid_limit`` and ``plastic_limit`` or ``plasticity_index``.
    method : {"thewes_burger_2004"}
        The diagram, from ``config/clogging_methods.yaml``.
    zones : DataFrame or str, optional
        Your own zones instead (``ht.template("clogging_zones")``), listed
        from the lowest potential to the highest. The axes then fit them.
    color_by : str or None
        The column points are colored by; None for one color.
    order : list of str, optional
        Units in stratigraphic order, for the legend.
    labels : bool
        Write each specimen's ``specimen_id`` beside its point.
    zone_labels : bool
        Name each zone inside it.
    zone_counts : bool
        Add a footnote line with the number of specimens in each zone.
    xlim, ylim : tuple, optional
        Axis limits, exactly. Specimens beyond are drawn at the edge.
    note : str, optional
        Free text, added to the footnote.
    palette : dict, optional
        ``{unit: color}``, overriding the session's colors.
    display_units : {"US", "SI"}, optional
        Accepted for the plot contract. PI is a percentage and Ic is
        dimensionless, so it changes nothing.
    legend : {"auto", "inside", "bottom", "right"} or bool
        Where the legend goes, as for ``plasticity_chart()``.
    figsize : tuple, optional
        Figure size in inches. Defaults to ``ht.settings.figure_sizes["default"]``.
    ax : matplotlib.axes.Axes, optional
        Draw into this axes, e.g. a ``Sheet`` panel.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, ax

    Examples
    --------
    >>> limits = p.atterberg()
    >>> fig, ax = ht.plot.clogging_diagram(limits)
    >>> fig, ax = ht.plot.clogging_diagram(limits, zones="other_source.csv")
    """
    _check_choice("method", method, METHODS)
    _display_units(display_units or settings.display_units)
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    figure = diagram(method, zones)
    _check_color_by(df, color_by)
    where = check_legend(legend)

    with style.context(**style_overrides):
        if len(df) and color_by == "geology_unit":
            hint_missing(df, {"geology_unit": "all specimens are drawn in one color"})
        notes = Notes()
        data, index, consistency = _specimens(df, figure, labels, notes)
        drawn = np.isfinite(index) & np.isfinite(consistency)
        if zone_counts and drawn.any():
            notes.add_text(zone_counts_text(data, figure, drawn))
        if note is not None:
            notes.add_text(str(note))
        groups, colors = _values.color_groups(data, color_by, palette, order)
        box = _box(figure, xlim, ylim)
        if ax is None:
            fig, ax = plt.subplots(
                figsize=figsize or settings.figure_sizes["default"],
                layout="constrained",
            )
        else:
            fig = ax.figure
        style.style_axes(ax)
        _set_axes(ax, box)
        _draw_zones(ax, figure, zone_labels)
        handles = _draw_specimens(
            ax, data, index, consistency, groups, colors, box, labels, notes
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
        placed = add_legend(ax, [handles], notes, where=where)
        notes.render(ax, where=placed.where, below=placed.legend)
    return fig, ax
