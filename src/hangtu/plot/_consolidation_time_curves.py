"""P15 consolidation time curves (docs/plots/P15-consolidation-time-curves.md)."""

import math
import textwrap
from collections.abc import Sequence
from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.layout_engine import ConstrainedLayoutEngine
from matplotlib.lines import Line2D

from hangtu import units as _units
from hangtu._data import numeric_column
from hangtu._settings import _display_units, figure_size, settings
from hangtu.analysis._consolidation_readings import (
    DISPLACEMENT_50,
    DISPLACEMENT_90,
    DISPLACEMENT_100,
    EARLY,
    INFLEXION,
    LOG_METHOD,
    LOG_TIME,
    LOG_TIME_ZERO,
    NO_HEIGHT,
    OVERRIDE,
    PAIR_RATIO,
    ROOT_METHOD,
    ROOT_TIME,
    ROOT_TIME_RATIO,
    ROOT_TIME_ZERO,
    SECONDARY,
    TIME_50,
    TIME_90,
    Construction,
    constructions,
)
from hangtu.analysis._oedometer import LOADING, specimen_label, stress_text
from hangtu.errors import HangtuError
from hangtu.plot import _layers, style
from hangtu.plot._geology_units import (
    BAND_PAD,
    FOOTNOTE_LINE,
    LEGEND_COLUMNS,
    LEGEND_ROW,
)
from hangtu.plot._labels import axis_label
from hangtu.plot._limits import log_limits, nice_limits, set_linear_axis, set_log_axis
from hangtu.plot._notes import (
    FOOTNOTE_COLOR,
    FOOTNOTE_SIZE,
    Notes,
    edge_markers,
    renderer,
)
from hangtu.plot._overlays import format_number
from hangtu.plot._palette import resolve_palette

METHODS = (ROOT_METHOD, LOG_METHOD)
#: The most increments one figure holds (P15 §5).
MAX_INCREMENTS = 6
#: The root time panel's x axis reaches this many times √t90 (P15 §6).
ROOT_REACH = 2.5
#: Inches per row of panels, and for the title, x label, legend and footnote.
ROW_HEIGHT = 2.4
EXTRA_HEIGHT = 1.1
LINE_COLOR = "0.2"
POINT_COLOR = "0.5"
LINE_WIDTH = 0.9
POINT_WIDTH = 0.8
CURVE_WIDTH = 0.6
MARKER_SIZE = 4.0
TEXT_SIZE = 7.5
#: Characters per line of a reason or a y label in a panel.
WRAP = 34
LABEL_WIDTH = 24
_REPORTED = {
    ROOT_METHOD: "reported_coefficient_of_consolidation_root_time",
    LOG_METHOD: "reported_coefficient_of_consolidation_log_time",
}
_COLUMNS = {ROOT_METHOD: ROOT_TIME, LOG_METHOD: LOG_TIME}
_STRESS = "applied_vertical_stress"
#: The line styles of the constructions (P15 §7).
EARLY_STYLE = "-"
RATIO_STYLE = "--"
OVERRIDE_STYLE = "-."
POINT_STYLE = ":"


def consolidation_time_curves(
    df: pd.DataFrame,
    *,
    specimen: str | None = None,
    increments: Sequence[str] | None = None,
    methods: Sequence[str] = METHODS,
    overrides: pd.DataFrame | None = None,
    reported: bool = True,
    note: str | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    **style_overrides: Any,
) -> tuple[Figure, np.ndarray]:
    """Plot each oedometer increment's time curves with its c_v constructions.

    For the increments of one specimen, one row of panels each: the vertical
    displacement against the square root of time (the root time
    construction, left) and against log time (the log time construction,
    right), each with the construction of BS 1377-5:1990, 3.6.3 that
    ``ht.analysis.consolidation_coefficient_from_readings()`` made on it,
    drawn, never recomputed here. A reviewer sees which readings each line
    was fitted to, where t50 and t90 came from, and how the result compares
    with the lab's.

    - The readings: filled where a line was fitted to them or they are in a
      pair of times in the ratio 1:4, open otherwise, joined by straight
      lines as the constructions interpolate them. The t = 0 reading is on
      the root time panel only: log t has no place for it.
    - Root time: the early line, extended to t = 0, and the 1.15 line
      dashed; d0 and d90 as dotted levels and t90 as a dotted line down to
      the axis. Its x axis stops past 2.5 √t90, so the construction isn't
      squeezed against t = 0 by a day's readings; the later readings are
      drawn at its edge and counted in the footnote.
    - Log time: the tangent at the inflexion and the secondary line, drawn
      to their crossing; d0, d50 and d100 as dotted levels and t50 down to
      the axis.
    - In each panel, c_v to 3 significant figures beside the lab's value as
      the lab wrote it, with "(override)" where a part of the construction
      was overridden; that part's line is dash-dotted. Where a construction
      gives no c_v, its reason is written in the panel and the lines it got
      to are drawn.

    The movement points down: the y axis is inverted where the readings rise
    over the increment (a settlement reading), not where they fall (a dial
    gauge reading down). The two panels of a row share their y axis.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per reading, as ``p.oedometer_readings()`` gives or a CSV in
        ``ht.template("oedometer_readings")``'s shape, with the columns
        ``ht.analysis.consolidation_coefficient_from_readings()`` reads.
    specimen : str, optional
        The specimen drawn, by its ``specimen_id`` or its name (sample and
        specimen references, "BH1-U3-OED1"). Required when the rows hold
        more than one.
    increments : sequence of str, optional
        The increments drawn, by ``test_stage``, at most 6. Defaults to every
        increment of the specimen with readings.
    methods : sequence of str
        ``"root_time"``, ``"log_time"`` or both: one column of panels each.
    overrides : pandas.DataFrame, optional
        Passed to the analysis: the time range for a part of a construction,
        in ``ht.template("consolidation_overrides")``'s shape.
    reported : bool
        Write the lab's c_v beside hangtu's.
    note : str, optional
        Free text, added to the footnote.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.
    display_units : {"US", "SI"}, optional
        Displacements in in or mm and c_v in ft²/yr or m²/yr; times are in
        minutes in both. Defaults to ``ht.settings.display_units``.
    figsize : tuple, optional
        Figure size in inches. Defaults to the ``default`` width and 2.4 in
        per row, plus room for the title, legend and footnote.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, axs
        ``axs`` is shaped (increments, methods).

    Raises
    ------
    HangtuError
        For rows holding more than one specimen without ``specimen=``, a
        specimen or increment the rows don't have, more than 6 increments, a
        ``methods`` other than the two, and as
        ``ht.analysis.consolidation_coefficient_from_readings()`` raises.

    Examples
    --------
    >>> readings = p.oedometer_readings()
    >>> fig, axs = ht.plot.consolidation_time_curves(
    ...     readings, specimen="BH1-U3-OED1", increments=["3", "4", "5"]
    ... )
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    chosen = _check_methods(methods)
    system = _display_units(display_units or settings.display_units)

    with style.context(**style_overrides):
        result, built = constructions(
            df, overrides=overrides, units=units, display_units=system
        )
        label, specimen_rows = _specimen_rows(result, specimen)
        rows = _increment_rows(result, specimen_rows, label, increments)
        notes = Notes()
        for text in result.attrs["consolidation_coefficient_from_readings"]["notes"]:
            notes.add_text(text)
        constant = [i for i in rows if built[i].readings is None]
        drawn = [i for i in rows if built[i].readings is not None]
        if constant:
            named = ", ".join(str(result["test_stage"].iloc[i]) for i in constant)
            s = "s" if len(constant) > 1 else ""
            notes.add_text(f"Not drawn: increment{s} {named} (constant stress)")
        if not drawn:
            raise HangtuError(
                f"Specimen {label} has no increment with readings to draw: "
                "a constant stress increment has no consolidation curve."
            )
        if len(drawn) > MAX_INCREMENTS:
            stages = [str(result["test_stage"].iloc[i]) for i in drawn]
            raise HangtuError(
                f"Specimen {label} has {len(drawn)} increments to draw, more than "
                f"the {MAX_INCREMENTS} one figure holds. Choose up to "
                f"{MAX_INCREMENTS} with increments=, e.g. increments="
                f"{stages[:3]!r}, and draw the others in a second figure."
            )

        width = figure_size("default")[0]
        fig, axs = plt.subplots(
            len(drawn),
            len(chosen),
            squeeze=False,
            sharey="row",
            figsize=figsize or (width, ROW_HEIGHT * len(drawn) + EXTRA_HEIGHT),
            layout="constrained",
        )
        scale, length_unit = _units.to_display(
            np.array([1.0]), "mm", "small_length", system
        )
        _, time_unit = _units.to_display(np.array([1.0]), "min", "time", system)
        frame_units = result.attrs["units"]
        cv_unit = frame_units.get(ROOT_TIME)
        color = resolve_palette([label], None, [label], df.attrs.get("palette"))[label]
        marks: set[str] = set()
        zero_readings = 0
        for r, i in enumerate(drawn):
            construction = built[i]
            readings = construction.readings
            assert readings is not None  # constant stress increments aren't drawn
            panel = _Panel(construction, float(scale[0]), color, marks)
            levels: list[float] = list(panel.displacements)
            times: list[tuple[Axes, float, float, str]] = []
            for c, method in enumerate(chosen):
                ax = axs[r, c]
                style.style_axes(ax)
                if method == ROOT_METHOD:
                    levels += panel.root(ax, result, i, times)
                else:
                    levels += panel.log(ax, result, i, times)
                    zero_readings += int((readings.times == 0).any())
                text = _result_text(
                    df,
                    result,
                    i,
                    construction,
                    method,
                    reported,
                    cv_unit,
                    units,
                    system,
                )
                _write_result(ax, result, i, method, text)
                if c > 0:
                    ax.tick_params(labelleft=False)
            _set_y(axs[r], levels, readings.sign > 0)
            for ax, x, y, name in times:
                _time_mark(ax, x, y, name)
            for ax, xs, ys, limits in panel.edges:
                edge = edge_markers(ax, xs, ys, {"x": limits}, color)
                notes.count(edge, "beyond_limit")
            axs[r, 0].set_title(
                _row_title(result, i, specimen_rows, frame_units.get(_STRESS)),
                loc="left",
                fontsize=9,
            )
            axs[r, 0].set_ylabel(
                textwrap.fill(
                    axis_label("Vertical displacement, δ_v", length_unit),
                    LABEL_WIDTH,
                    break_on_hyphens=False,
                )
            )
        for c, method in enumerate(chosen):
            if method == ROOT_METHOD:
                axs[-1, c].set_xlabel(
                    axis_label(
                        "Square root of time, √t",
                        f"√{time_unit}" if time_unit else None,
                    )
                )
            else:
                axs[-1, c].set_xlabel(axis_label("Time, t", time_unit))
        fig.suptitle(_figure_title(result, drawn[0], label, frame_units), fontsize=10)
        if zero_readings:
            s = "s" if zero_readings > 1 else ""
            notes.add_text(
                f"{zero_readings} t = 0 reading{s} on the root time panels only: "
                "log t has no place for t = 0"
            )
        if note is not None:
            notes.add_text(str(note))
        axs[-1, 0].ags_notes = dict(notes.counts)
        _legend(fig, _handles(marks, color), notes.lines())
    return fig, axs


def _check_methods(methods: Sequence[str] | str) -> tuple[str, ...]:
    chosen = (methods,) if isinstance(methods, str) else tuple(methods)
    unknown = [method for method in chosen if method not in METHODS]
    if not chosen or unknown or len(set(chosen)) < len(chosen):
        what = (
            "is empty"
            if not chosen
            else f"has {', '.join(map(repr, unknown))}"
            if unknown
            else "repeats a method"
        )
        raise HangtuError(
            f"methods= {what}: give one or both of {', '.join(map(repr, METHODS))}."
        )
    return chosen


def _label(result: pd.DataFrame, i: int) -> str:
    key = {
        column: None if pd.isna(result[column].iloc[i]) else result[column].iloc[i]
        for column in ("specimen_id", "sample_reference", "specimen_reference")
        if column in result.columns
    }
    return specimen_label(key)


def _specimen_rows(result: pd.DataFrame, specimen: str | None) -> tuple[str, list[int]]:
    """Return the specimen's name and its rows in the result."""
    ids = result["specimen_id"].astype(str).tolist()
    labels = [_label(result, i) for i in range(len(result))]
    names = list(dict.fromkeys(labels))
    if specimen is None:
        if len(set(ids)) > 1:
            raise HangtuError(
                f"The rows hold {len(set(ids))} specimens ({', '.join(names)}); "
                f"give specimen= one of them, e.g. specimen={names[0]!r}."
            )
        return labels[0], list(range(len(result)))
    wanted = str(specimen).strip()
    rows = [i for i in range(len(result)) if wanted in (ids[i].strip(), labels[i])]
    if not rows:
        raise HangtuError(
            f"No specimen {specimen!r} in the rows. Specimens: {', '.join(names)}."
        )
    if len({ids[i] for i in rows}) > 1:
        raise HangtuError(
            f"More than one specimen is named {specimen!r}; give its specimen_id: "
            f"{', '.join(sorted({ids[i] for i in rows}))}."
        )
    return labels[rows[0]], rows


def _increment_rows(
    result: pd.DataFrame,
    rows: list[int],
    label: str,
    increments: Sequence[str] | None,
) -> list[int]:
    """Return the rows of the increments asked for, in the order asked."""
    if increments is None:
        return rows
    wanted = (increments,) if isinstance(increments, str) else tuple(increments)
    stages = {str(result["test_stage"].iloc[i]).strip(): i for i in rows}
    unknown = [str(stage) for stage in wanted if str(stage).strip() not in stages]
    if not wanted or unknown:
        what = "is empty" if not wanted else f"has {', '.join(map(repr, unknown))}"
        raise HangtuError(
            f"increments= {what}. Specimen {label} has readings for increments "
            f"{', '.join(stages)}."
        )
    return [stages[str(stage).strip()] for stage in wanted]


class _Panel:
    """Draws one increment's readings and constructions, in the display unit."""

    def __init__(
        self, construction: Construction, scale: float, color: Any, marks: set[str]
    ) -> None:
        assert construction.readings is not None
        self.construction = construction
        self.readings = construction.readings
        self.scale = scale
        self.color = color
        self.marks = marks
        self.displacements = self.at(self.readings.movement)
        #: Readings beyond the x limit: (axes, x, y, limits), drawn at the edge
        #: once the row's y axis is set.
        self.edges: list[tuple[Axes, np.ndarray, np.ndarray, tuple[float, float]]] = []

    def at(self, movement: Any) -> np.ndarray:
        """Write movements (y, mm) as displacements in the display unit."""
        readings = self.readings
        return (readings.first + readings.sign * np.asarray(movement)) * self.scale

    def root(
        self,
        ax: Axes,
        result: pd.DataFrame,
        i: int,
        times: list[tuple[Axes, float, float, str]],
    ) -> list[float]:
        """Draw the root time panel; return the levels its points add."""
        root = self.construction.root
        assert root is not None
        x = np.sqrt(self.readings.times)
        # Filled only where the early line was fitted to them.
        used = np.zeros(len(x), dtype=bool)
        if root.fitted is not None and not math.isnan(root.slope):
            used = root.fitted
        # From 0 to past t90 (or the early readings), not to the last reading:
        # at the standard's times that would squeeze the construction into the
        # panel's first eighth. Later readings go at the edge (P15 §6).
        if root.reason is None:
            reach = math.sqrt(root.time)
        else:
            reach = float(x[used].max() if used.any() else x.max())
        right = min(float(x.max()), ROOT_REACH * reach) if reach > 0 else x.max()
        limits = nice_limits(0.0, float(right), start_at_zero=True)
        set_linear_axis(ax, "x", limits)
        beyond = x > limits[1]
        self.draw_readings(ax, x, self.displacements, used, ~beyond)
        if beyond.any():
            self.edges.append((ax, x[beyond], self.displacements[beyond], limits))
        if root.slope > 0:  # False for NaN: the lines it got to
            ends = np.array([0.0, 1.25 * reach])
            overridden = EARLY in self.construction.ranges.get(ROOT_METHOD, {})
            self.line(
                ax,
                ends,
                self.at(root.zero + root.slope * ends),
                OVERRIDE_STYLE if overridden else EARLY_STYLE,
                "early_line",
                "override" if overridden else "early",
            )
            self.line(
                ax,
                ends,
                self.at(root.zero + root.slope / ROOT_TIME_RATIO * ends),
                RATIO_STYLE,
                "ratio_line",
                "ratio",
            )
        if root.reason is not None:
            return []
        row = result.iloc[i]
        zero, d90 = float(row[ROOT_TIME_ZERO]), float(row[DISPLACEMENT_90])
        self.level(ax, zero, "d0")
        self.level(ax, d90, "d90")
        times.append((ax, math.sqrt(float(row[TIME_90])), d90, "t90"))
        return [zero, d90]

    def log(
        self,
        ax: Axes,
        result: pd.DataFrame,
        i: int,
        times: list[tuple[Axes, float, float, str]],
    ) -> list[float]:
        """Draw the log time panel; return the levels its points add."""
        log = self.construction.log
        assert log is not None
        t = self.readings.times
        after = self.readings.after_load
        used = np.zeros(len(t), dtype=bool)
        for line in (log.secondary, log.tangent):
            if line is not None:
                used |= line.fitted
        if log.pairs is not None and not math.isnan(log.zero):
            for pair in log.pairs:
                used[pair] = True
                used |= np.isclose(t, PAIR_RATIO * t[pair], rtol=1e-9, atol=0.0)
        self.draw_readings(ax, t[after], self.displacements[after], used[after])
        first, last = float(t[after].min()), float(t[after].max())
        # From the decade at or below the first reading to beyond the last (§6).
        limits = (log_limits(first, last, clear=False)[0], log_limits(first, last)[1])
        set_log_axis(ax, "x", limits)
        crossing = log.time_100 if not math.isnan(log.time_100) else None
        ranges = self.construction.ranges.get(LOG_METHOD, {})
        for line, portion, name in (
            (log.tangent, INFLEXION, "tangent"),
            (log.secondary, SECONDARY, "secondary_line"),
        ):
            if line is None:
                continue
            fitted = t[line.fitted]
            if name == "tangent":
                ends = np.array([fitted.min() / 2, crossing or fitted.max()])
            else:
                ends = np.array([crossing or fitted.min(), t[after].max()])
            overridden = portion in ranges
            self.line(
                ax,
                ends,
                self.at(line.intercept + line.slope * np.log10(ends)),
                OVERRIDE_STYLE if overridden else EARLY_STYLE,
                name,
                "override" if overridden else "tangent",
            )
        if log.reason is not None:
            return []
        row = result.iloc[i]
        zero, d50, d100 = (
            float(row[LOG_TIME_ZERO]),
            float(row[DISPLACEMENT_50]),
            float(row[DISPLACEMENT_100]),
        )
        for value, name in ((zero, "d0"), (d50, "d50"), (d100, "d100")):
            self.level(ax, value, name)
        times.append((ax, float(row[TIME_50]), d50, "t50"))
        return [zero, d50, d100]

    def draw_readings(
        self,
        ax: Axes,
        x: np.ndarray,
        y: np.ndarray,
        used: np.ndarray,
        shown: np.ndarray | None = None,
    ) -> None:
        """Draw the readings, joined; ``shown`` False on those drawn at the edge."""
        shown = np.ones(len(x), dtype=bool) if shown is None else shown
        ax.plot(
            x,
            y,
            color=self.color,
            linewidth=CURVE_WIDTH,
            gid="curve",
            zorder=_layers.CONNECT,
        )
        for mask, name, face in (
            (used & shown, "readings_used", self.color),
            (~used & shown, "readings", "white"),
        ):
            if mask.any():
                ax.plot(
                    x[mask],
                    y[mask],
                    marker="o",
                    markersize=MARKER_SIZE,
                    markerfacecolor=face,
                    markeredgecolor=self.color,
                    markeredgewidth=0.8,
                    linestyle="none",
                    gid=name,
                    zorder=_layers.MARKERS,
                )
                self.marks.add(name)

    def line(
        self,
        ax: Axes,
        x: np.ndarray,
        y: np.ndarray,
        linestyle: str,
        gid: str,
        mark: str,
    ) -> None:
        ax.plot(
            x,
            y,
            color=LINE_COLOR,
            linewidth=LINE_WIDTH,
            linestyle=linestyle,
            gid=gid,
            zorder=_layers.LINES,
        )
        self.marks.add(mark)

    def level(self, ax: Axes, value: float, name: str) -> None:
        """Draw a point's displacement: a dotted level across the panel, labeled."""
        ax.axhline(
            value,
            color=POINT_COLOR,
            linewidth=POINT_WIDTH,
            linestyle=POINT_STYLE,
            gid=f"level_{name}",
            zorder=_layers.RANGES,
        )
        ax.text(
            1.01,
            value,
            name,
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="center",
            fontsize=TEXT_SIZE,
            color=POINT_COLOR,
            clip_on=False,
            gid=f"label_{name}",
        )
        self.marks.add("points")


def _set_y(axs: Sequence[Axes], levels: list[float], invert: bool) -> None:
    """Set the row's shared y limits over its readings and points (P15 §6)."""
    values = [v for v in levels if math.isfinite(v)]
    limits = nice_limits(min(values), max(values), start_at_zero=False)
    set_linear_axis(axs[0], "y", limits[::-1] if invert else limits)


def _time_mark(ax: Axes, x: float, y: float, name: str) -> None:
    """Draw a point's time: a dotted line from the curve down to the axis."""
    bottom = ax.get_ylim()[0]
    ax.plot(
        [x, x],
        [y, bottom],
        color=POINT_COLOR,
        linewidth=POINT_WIDTH,
        linestyle=POINT_STYLE,
        gid=f"time_{name}",
        zorder=_layers.RANGES,
    )
    ax.annotate(
        name,
        xy=(x, bottom),
        xytext=(2.0, 2.0),
        textcoords="offset points",
        ha="left",
        va="bottom",
        fontsize=TEXT_SIZE,
        color=POINT_COLOR,
        gid=f"label_{name}",
    )


def _result_text(
    df: pd.DataFrame,
    result: pd.DataFrame,
    i: int,
    construction: Construction,
    method: str,
    reported: bool,
    unit: str | None,
    units: dict[str, str] | None,
    system: str,
) -> str | None:
    """Write the result, "c_v 2.15 m²/yr (lab 2.1)"; None where it stopped."""
    row = result.iloc[i]
    reason = row[f"{_COLUMNS[method]}_reason"]
    if isinstance(reason, str) and reason != NO_HEIGHT:
        return None
    if reason == NO_HEIGHT:
        text = f"c_v not computed: {NO_HEIGHT}"
    else:
        value = format_number(float(row[_COLUMNS[method]]))
        text = f"c_v {value}{f' {unit}' if unit else ''}"
        if reported:
            text += f" (lab {_lab_text(df, construction.row, method, units, system)})"
    if row[f"{_COLUMNS[method]}_basis"] == OVERRIDE:
        text += " (override)"
    return text


def _lab_text(
    df: pd.DataFrame,
    row: int,
    method: str,
    units: dict[str, str] | None,
    system: str,
) -> str:
    """Write the lab's c_v as read, in the display unit with its figures."""
    column = _REPORTED[method]
    if column not in df.columns:
        return "—"
    value = float(numeric_column(df, column)[row])
    if math.isnan(value):
        return "—"
    declared = (units or {}).get(column) or _units.units_of(df).get(column)
    if declared is None:
        return f"{value:g}, units unknown"
    shown = float(
        _units.to_display(
            np.array([value]), declared, "consolidation_coefficient", system
        )[0][0]
    )
    return _in_figures(shown, _figures(value))


def _figures(value: float) -> int:
    """Count the significant figures of a value as read: 2.1 and 4200 have 2."""
    text = f"{abs(value):.12g}"
    mantissa = text.split("e")[0]
    digits = mantissa.replace(".", "").lstrip("0")
    if "." not in mantissa:
        digits = digits.rstrip("0")
    return max(len(digits), 1)


def _in_figures(value: float, figures: int) -> str:
    if value == 0 or not math.isfinite(value):
        return f"{value:g}"
    rounded = float(f"{value:.{figures}g}")
    exponent = math.floor(math.log10(abs(rounded)))
    return f"{rounded:,.{max(0, figures - 1 - exponent)}f}"


def _write_result(
    ax: Axes, result: pd.DataFrame, i: int, method: str, text: str | None
) -> None:
    """Write the result in the upper right, or the reason in the middle."""
    if text is not None:
        ax.text(
            0.98,
            0.96,
            text,
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=TEXT_SIZE,
            color="black",
            gid="result",
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "linewidth": 0},
            zorder=_layers.ANNOTATIONS,
        )
        return
    reason = str(result[f"{_COLUMNS[method]}_reason"].iloc[i])
    ax.text(
        0.5,
        0.5,
        textwrap.fill(reason, WRAP),
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=TEXT_SIZE,
        color="0.3",
        gid="reason",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "linewidth": 0},
        zorder=_layers.ANNOTATIONS,
    )


def _row_title(result: pd.DataFrame, i: int, rows: list[int], unit: str | None) -> str:
    """Title a row "Increment 4: 100 → 200 kPa", σ′1 from the one before it."""
    stage = str(result["test_stage"].iloc[i])
    title = f"Increment {stage}"
    if _STRESS in result.columns:
        end = float(numeric_column(result, _STRESS)[i])
        if math.isfinite(end):
            start = _stress_before(result, rows, stage)
            unit_text = f" {unit}" if unit else ""
            if start is None:
                title += f": to {stress_text(end)}{unit_text}"
            else:
                title += f": {stress_text(start)} → {stress_text(end)}{unit_text}"
    branch = result["load_branch"].iloc[i] if "load_branch" in result else None
    if isinstance(branch, str) and branch != LOADING:
        title += f" ({branch.replace('_', ' ')})"
    return title


def _stress_before(result: pd.DataFrame, rows: list[int], stage: str) -> float | None:
    """σ′1: the stress of the increment numbered one before, where the rows have it."""
    try:
        before = str(int(stage) - 1)
    except ValueError:
        return None
    stresses = numeric_column(result, _STRESS)
    for k in rows:
        if str(result["test_stage"].iloc[k]).strip() == before:
            value = float(stresses[k])
            return value if math.isfinite(value) else None
    return None


def _figure_title(
    result: pd.DataFrame, i: int, label: str, frame_units: dict[str, Any]
) -> str:
    """Name the specimen as P13 does: its name and, where given, its depth."""
    if "depth" not in result.columns or pd.isna(result["depth"].iloc[i]):
        return label
    unit = frame_units.get("depth")
    depth = format_number(float(result["depth"].iloc[i]))
    return f"{label}, {depth}{f' {unit}' if unit else ''}"


def _handles(marks: set[str], color: Any) -> list[Artist]:
    entries: list[tuple[str, dict[str, Any], str]] = [
        (
            "readings_used",
            {
                "marker": "o",
                "markerfacecolor": color,
                "markeredgecolor": color,
                "color": color,
                "linestyle": "none",
                "markersize": MARKER_SIZE,
            },
            "Reading used",
        ),
        (
            "readings",
            {
                "marker": "o",
                "markerfacecolor": "white",
                "markeredgecolor": color,
                "color": color,
                "linewidth": CURVE_WIDTH,
                "markersize": MARKER_SIZE,
            },
            "Reading",
        ),
        ("early", {"color": LINE_COLOR, "linestyle": EARLY_STYLE}, "Early line"),
        ("ratio", {"color": LINE_COLOR, "linestyle": RATIO_STYLE}, "1.15 line"),
        (
            "tangent",
            {"color": LINE_COLOR, "linestyle": EARLY_STYLE},
            "Tangent and secondary line",
        ),
        (
            "override",
            {"color": LINE_COLOR, "linestyle": OVERRIDE_STYLE},
            "Line over an override range",
        ),
        (
            "points",
            {"color": POINT_COLOR, "linestyle": POINT_STYLE, "linewidth": POINT_WIDTH},
            "d0, d50, d90, d100; t50, t90",
        ),
    ]
    return [
        Line2D([], [], label=text, **{"linewidth": LINE_WIDTH, **kwargs})
        for name, kwargs, text in entries
        if name in marks
    ]


def _legend(fig: Figure, handles: list[Artist], footnote: list[str]) -> None:
    """Put one legend below the panels, in as many columns as fit, then the footnote.

    A band at the bottom of the figure is kept free of panels for them, as
    the geology unit grid keeps one (P07), with fewer columns when long
    entries would run past the figure's edges.
    """
    if not handles and not footnote:
        return
    columns = min(len(handles), LEGEND_COLUMNS)
    while handles:
        legend = fig.legend(
            handles=handles,
            loc="upper center",
            ncols=columns,
            frameon=False,
            fontsize=8,
            borderaxespad=0.0,
        )
        legend.set_in_layout(False)
        wide = legend.get_window_extent(renderer(fig)).width > fig.bbox.width
        if columns == 1 or not wide:
            break
        legend.remove()
        columns -= 1
    rows = -(-len(handles) // columns) if handles else 0
    band = (rows * LEGEND_ROW + len(footnote) * FOOTNOTE_LINE + 2 * BAND_PAD) / (
        72.0 * fig.get_figheight()
    )
    engine = fig.get_layout_engine()
    assert isinstance(engine, ConstrainedLayoutEngine)  # the figure is made so
    engine.set(rect=(0.0, band, 1.0, 1.0 - band))
    if handles:
        legend.set_bbox_to_anchor((0.5, band), transform=fig.transFigure)
    if footnote:
        fig.text(
            0.5,
            BAND_PAD / (72.0 * fig.get_figheight()),
            "\n".join(footnote),
            ha="center",
            va="bottom",
            fontsize=FOOTNOTE_SIZE,
            color=FOOTNOTE_COLOR,
            gid="footnote",
        )
