"""P13 consolidation curve (docs/plots/P13-consolidation-curve.md)."""

import math
import textwrap
import warnings
from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

from hangtu._settings import _display_units, settings
from hangtu.analysis._oedometer_fit import (
    _LEFT_OUT,
    _LEFT_OUT_TEXT,
    OedometerFit,
    oedometer_fit,
)
from hangtu.errors import HangtuError
from hangtu.plot import _layers, _values, style
from hangtu.plot._hints import hint_missing
from hangtu.plot._labels import axis_label
from hangtu.plot._legend import add_legend
from hangtu.plot._limits import log_limits, nice_limits, nice_step, set_log_axis
from hangtu.plot._notes import Notes, figure_of
from hangtu.plot._overlays import format_number
from hangtu.plot._palette import resolve_palette

SPACES = ("void_ratio", "log_specific_volume")
LEGEND_COLOR = "black"
CONSTRUCTION_COLOR = "0.55"
MARKER_SIZE = 5.0
CROSS_SIZE = 4.0
TRIANGLE_SIZE = 7.0
#: Pacheco Silva's open triangle is larger and under Oikawa's, so where the two
#: σ′p nearly agree the filled one shows inside its outline.
CHECK_SIZE = 10.0
CURVE_WIDTH = 0.7
LINE_WIDTH = 1.2
BEYOND_WIDTH = 0.7
SWELLING_ALPHA = 0.55
CONSTRUCTION_WIDTH = 0.6
TICK_LENGTH = 0.025  # the e0 tick, in axes fraction
TEXT_SIZE = 7.5
BOX_WIDTH = 66  # characters per line of the result box
#: Under the gridline-free layer that counts as an obstacle for the legend
#: (``_layers.LINES``): the dashed parts cross the axes, and would push the
#: legend out of every corner.
BEYOND_LAYER = _layers.RANGES
CAVEAT = (
    "The Δe/e0 class uses this test's OCR: disturbance lowers σ′p and so the OCR,\n"
    "which can move a poor sample into the more lenient OCR 1-2 row."
)
#: The start of the fit's reason when the frame has no σ′v0 column.
NO_COLUMN = "no effective_vertical_stress"
#: (gid, marker, filled, size, legend text) of each kind of point (P13 §7).
POINT_KINDS = {
    "loading": ("o", True, MARKER_SIZE, "Loading"),
    "loading_after_reload": ("D", True, MARKER_SIZE - 0.5, "Loading past a reload"),
    "unloading": ("o", False, MARKER_SIZE, "Unloading"),
    "reloading": ("D", False, MARKER_SIZE - 0.5, "Reloading"),
    "constant_stress": ("x", True, CROSS_SIZE, "Constant stress"),
}
#: The reasons a point isn't drawn at all: it has no place on the axes.
NOT_DRAWN = (
    "count_no_applied_stress",
    "count_no_void_ratio",
    "count_stress_not_positive",
)


def consolidation_curve(
    df: pd.DataFrame,
    *,
    space: Literal["void_ratio", "log_specific_volume"] = "void_ratio",
    fit: bool = True,
    construction: bool = False,
    result_box: bool = True,
    note: str | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes, OedometerFit | None]:
    r"""Plot oedometer curves, e against log σ′v, with σ′p, Cc, Cr and Cs.

    Every increment is drawn by its branch: loading points filled and joined
    in order, the first loading points past an unload-reload loop as filled
    diamonds, unloading points open circles, reloading points open diamonds
    and constant-stress points crosses. The fit is
    ``ht.analysis.oedometer_fit()``'s, drawn, never refitted:

    - the Cc and Cr lines, $e = c - C\log_{10}\sigma'_v$, solid over the
      points each was fitted to and thin and dashed beyond them;
    - the Cs line of the first unload, solid over its points;
    - σ′p by Oikawa (1987) as a filled triangle and by Pacheco Silva (1970)
      as an open one, both on the loading curve (linear in e against
      log σ′v between the points either side), not where the Cc and Cr lines
      cross: those lines are fitted in e, Oikawa's in log(1 + e);
    - e0 as a tick on the left edge, and σ′v0, where the rows have it, as a
      dotted vertical line.

    A box in the upper right gives each specimen's values, and why any of
    them isn't given; the footnote counts the rows no line used. Look at the
    plot before using σ′p or Cc: the fit is computed whether or not the
    curve has a clear break, and the box says when it hasn't.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per increment, as ``p.oedometer()`` gives or a CSV in
        ``ht.template("oedometer")``'s shape; run
        ``ht.analysis.vertical_stress()`` on it first for OCR, Δe/e0 and the
        σ′v0 line.
    space : {"void_ratio", "log_specific_volume"}
        ``"log_specific_volume"`` draws log(1 + e) against log σ′v with
        Oikawa's two lines, which cross at σ′p, instead of the Cc and Cr
        lines; Cs and the construction aren't drawn there.
    fit : bool
        False draws the points only, and returns None for the fit.
    construction : bool
        Draw Pacheco Silva's construction in thin gray lines: the horizontal
        through e0 to the virgin line, down to the curve, across to the
        virgin line and down to σ′p.
    result_box : bool
        Write each specimen's values in the upper right.
    note : str, optional
        Free text, added to the footnote.
    units : dict, optional
        Passed to ``ht.analysis.oedometer_fit()``.
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
        ``fit`` is the ``OedometerFit`` drawn, or None with ``fit=False``.

    Examples
    --------
    >>> oed = ht.analysis.vertical_stress(p.oedometer(), p.stratigraphy())
    >>> fig, ax, fit = ht.plot.consolidation_curve(oed)
    >>> fig, ax, fit = ht.plot.consolidation_curve(oed, space="log_specific_volume")
    """
    if space not in SPACES:
        raise HangtuError(
            f"space={space!r} isn't one the plot draws: give "
            f'"{SPACES[0]}" (e against log σ′v) or "{SPACES[1]}" (log(1 + e) '
            "against log σ′v)."
        )
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    system = _display_units(display_units or settings.display_units)
    log_space = space == "log_specific_volume"

    with style.context(**style_overrides):
        if fit:
            hint_missing(
                df,
                {
                    "void_ratio": "no CR, Pacheco Silva check, Δe/e0 or e0 tick",
                    "effective_vertical_stress": "no OCR, Δe/e0 or σ′v0 line; run "
                    "ht.analysis.vertical_stress() on the rows first",
                },
            )
        with warnings.catch_warnings():
            if not fit:  # no fit is drawn, so its warnings would mislead
                warnings.simplefilter("ignore")
            result = oedometer_fit(df, units=units, display_units=system)
        if ax is None:
            fig, ax = plt.subplots(
                figsize=figsize or settings.figure_sizes["default"],
                layout="constrained",
            )
        else:
            fig = figure_of(ax)
        style.style_axes(ax)
        notes = Notes()
        drawn = [record for record in result.specimens if _drawable(record)]
        colors = _colors(df, drawn)
        line_color = (
            (lambda label: LEGEND_COLOR)
            if len(drawn) == 1
            else (lambda label: colors[label])
        )
        _set_axes(ax, result, drawn, log_space)
        xlim = ax.get_xlim()
        kinds: set[str] = set()
        for record in drawn:
            kinds |= _draw_points(ax, record, colors[record["label"]], log_space)
        marks: set[str] = set()
        for record in drawn:
            marks |= _draw_stress_history(
                ax, record, colors[record["label"]], log_space, fit
            )
            if not fit:
                continue
            color = line_color(record["label"])
            if log_space:
                marks |= _draw_oikawa(ax, record, color, xlim)
            else:
                marks |= _draw_indexes(ax, record, color, xlim)
                if construction:
                    _draw_construction(ax, record, xlim)
            marks |= _draw_marks(ax, record, colors[record["label"]], log_space)
        if fit and result_box:
            _draw_box(ax, result, drawn)
        _footnote(result, drawn, fit, notes)
        if note is not None:
            notes.add_text(str(note))
        if not drawn:
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
        specimens = (
            [
                _values.legend_marker("s", colors[r["label"]], r["label"], MARKER_SIZE)
                for r in drawn
            ]
            if len(drawn) > 1
            else []
        )
        placed = add_legend(
            ax, [specimens, _point_handles(kinds), _mark_handles(marks)], notes
        )
        notes.render(ax, where=placed.where, below=placed.legend)
    return fig, ax, result if fit else None


def _drawable(record: dict[str, Any]) -> bool:
    return any(point["reason"] not in NOT_DRAWN for point in record["points"])


def _colors(df: pd.DataFrame, drawn: list[dict[str, Any]]) -> dict[str, Any]:
    """Return ``{specimen label: color}``, one color per specimen drawn."""
    labels = [record["label"] for record in drawn]
    return resolve_palette(labels, None, labels, df.attrs.get("palette"))


def _y(void_ratio: Any, log_space: bool) -> Any:
    """Return the y value of a void ratio: e, or 1 + e in log specific volume."""
    return np.asarray(void_ratio, dtype=float) + 1 if log_space else void_ratio


def _kind(point: dict[str, Any]) -> str | None:
    """Return the kind of mark a point is drawn as, or None if it isn't drawn."""
    if point["reason"] in NOT_DRAWN:
        return None
    branch = point["load_branch"]
    if branch == "loading":
        return "loading_after_reload" if point["after_reload"] else "loading"
    return branch


def _set_axes(
    ax: Axes, result: OedometerFit, drawn: list[dict[str, Any]], log_space: bool
) -> None:
    """Log σ′v from decade to decade; e (or 1 + e, log) on nice limits (P13 §6)."""
    stresses, void_ratios = [], []
    for record in drawn:
        for point in record["points"]:
            if _kind(point) is not None:
                stresses.append(point["applied_vertical_stress"])
                void_ratios.append(point["void_ratio"])
        if record["effective_vertical_stress"] > 0:  # False for NaN
            stresses.append(record["effective_vertical_stress"])
        if not math.isnan(record["void_ratio"]):
            void_ratios.append(record["void_ratio"])
    xlim = log_limits(min(stresses), max(stresses)) if stresses else (1.0, 100.0)
    set_log_axis(ax, "x", xlim)
    ax.set_xlabel(axis_label("Effective vertical stress, σ′v", result.unit))
    if not void_ratios:
        low, high = (0.0, 1.0)
    else:
        values = _y(np.array(void_ratios), log_space)
        low, high = nice_limits(
            float(values.min()), float(values.max()), start_at_zero=False
        )
    if log_space:
        low = max(low, 1.0)
        ax.set_yscale("log")
        ax.set_ylim(low, high)
        step = nice_step(low, high)
        ticks = np.arange(
            math.ceil(low / step - 1e-9), math.floor(high / step + 1e-9) + 1
        )
        ax.yaxis.set_major_locator(
            FixedLocator([float(f"{t * step:.12g}") for t in ticks])
        )
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
        ax.yaxis.set_minor_locator(NullLocator())
        ax.set_ylabel("Specific volume, 1 + e (log scale)")
    else:
        ax.set_ylim(low, high)
        ax.yaxis.set_major_locator(FixedLocator(_ticks(low, high)))
        ax.set_ylabel("Void ratio, e")


def _ticks(low: float, high: float) -> list[float]:
    step = nice_step(low, high)
    first, last = math.ceil(low / step - 1e-9), math.floor(high / step + 1e-9)
    return [float(f"{i * step:.12g}") for i in range(first, last + 1)]


def _draw_points(
    ax: Axes, record: dict[str, Any], color: Any, log_space: bool
) -> set[str]:
    """Draw a specimen's points by kind, and join its loading points in order."""
    by_kind: dict[str, list[dict[str, Any]]] = {}
    for point in record["points"]:
        kind = _kind(point)
        if kind is not None:
            by_kind.setdefault(kind, []).append(point)
    loading = [
        point
        for point in record["points"]
        if _kind(point) in ("loading", "loading_after_reload")
    ]
    if len(loading) > 1:
        ax.plot(
            [p["applied_vertical_stress"] for p in loading],
            _y([p["void_ratio"] for p in loading], log_space),
            color=color,
            linewidth=CURVE_WIDTH,
            gid="loading_curve",
            zorder=_layers.CONNECT,
        )
    for kind, points in by_kind.items():
        marker, filled, size, _ = POINT_KINDS[kind]
        ax.plot(
            [p["applied_vertical_stress"] for p in points],
            _y([p["void_ratio"] for p in points], log_space),
            marker=marker,
            markersize=size,
            color=color,
            markerfacecolor=color if filled else "white",
            linestyle="none",
            gid=f"{kind}_point",
            zorder=_layers.MARKERS,
        )
    return set(by_kind)


def _solid_and_beyond(
    ax: Axes,
    y: Any,
    low: float,
    high: float,
    xlim: tuple[float, float],
    color: Any,
    gid: str,
) -> None:
    """Draw ``y(σ′v)`` solid from ``low`` to ``high``, thin and dashed beyond."""
    for x0, x1, dashes, part, width, layer in (
        (xlim[0], low, "--", "_beyond", BEYOND_WIDTH, BEYOND_LAYER),
        (low, high, "-", "", LINE_WIDTH, _layers.LINES),
        (high, xlim[1], "--", "_beyond", BEYOND_WIDTH, BEYOND_LAYER),
    ):
        if x1 > x0:
            ax.plot(
                [x0, x1],
                [y(x0), y(x1)],
                color=color,
                linewidth=width,
                linestyle=dashes,
                gid=gid + part,
                zorder=layer,
            )


def _index_y(line: dict[str, Any]) -> Any:
    return lambda x: line["intercept"] + line["slope"] * math.log10(x)


def _draw_indexes(
    ax: Axes, record: dict[str, Any], color: Any, xlim: tuple[float, float]
) -> set[str]:
    """Draw the Cc and Cr lines (solid over their points) and the first Cs."""
    drawn = set()
    for name in ("compression", "recompression"):
        line = record[f"{name}_line"]
        if line is None:
            continue
        _solid_and_beyond(
            ax,
            _index_y(line),
            line["lowest_stress"],
            line["highest_stress"],
            xlim,
            color,
            f"{name}_index",
        )
        drawn.add(f"{name}_index")
    runs = record["unload_runs"]
    if runs and runs[0]["swelling_line"] is not None:
        line = runs[0]["swelling_line"]
        y = _index_y(line)
        low, high = line["lowest_stress"], line["highest_stress"]
        ax.plot(
            [low, high],
            [y(low), y(high)],
            color=color,
            linewidth=LINE_WIDTH,
            alpha=SWELLING_ALPHA,
            gid="swelling_index",
            zorder=_layers.LINES,
        )
        drawn.add("swelling_index")
    return drawn


def _draw_oikawa(
    ax: Axes, record: dict[str, Any], color: Any, xlim: tuple[float, float]
) -> set[str]:
    """Draw Oikawa's two lines, log10(1 + e) = a + b log10 σ′v, where σ′p is given."""
    if math.isnan(record["preconsolidation_stress"]):
        return set()
    for name, role in (("lower_line", "recompression"), ("upper_line", "virgin")):
        line = record[name]
        stresses = [
            p["applied_vertical_stress"] for p in record["points"] if p["role"] == role
        ]
        a, b = line["intercept"], line["slope"]
        _solid_and_beyond(
            ax,
            lambda x, a=a, b=b: 10 ** (a + b * math.log10(x)),
            min(stresses),
            max(stresses),
            xlim,
            color,
            f"oikawa_{name}",
        )
    return {"oikawa"}


def _draw_marks(
    ax: Axes, record: dict[str, Any], color: Any, log_space: bool
) -> set[str]:
    """Draw σ′p by Oikawa (filled) and by Pacheco Silva (open) on the curve."""
    drawn = set()
    for name, filled, size, layer in (
        ("preconsolidation_stress", True, TRIANGLE_SIZE, _layers.MARKERS + 0.06),
        (
            "preconsolidation_stress_pacheco_silva",
            False,
            CHECK_SIZE,
            _layers.MARKERS + 0.05,
        ),
    ):
        stress = record[name]
        on_curve = record[
            name.replace(
                "preconsolidation_stress", "void_ratio_at_preconsolidation_stress"
            )
        ]
        if math.isnan(stress) or math.isnan(on_curve):
            continue
        ax.plot(
            [stress],
            [_y(on_curve, log_space)],
            marker="v",
            markersize=size,
            color=color,
            markerfacecolor=color if filled else "none",
            markeredgewidth=1.0,
            linestyle="none",
            gid=name,
            zorder=layer,
        )
        drawn.add(name)
    return drawn


def _draw_stress_history(
    ax: Axes, record: dict[str, Any], color: Any, log_space: bool, fit: bool
) -> set[str]:
    """Draw the e0 tick at the left edge and the σ′v0 line (P13 §7)."""
    drawn = set()
    e0 = record["void_ratio"]
    if not math.isnan(e0):
        ax.plot(
            [0.0, TICK_LENGTH],
            [_y(e0, log_space)] * 2,
            color=color,
            linewidth=1.5,
            transform=ax.get_yaxis_transform(),
            clip_on=False,
            gid="initial_void_ratio",
            zorder=_layers.MARKERS,
        )
    in_situ = record["effective_vertical_stress"]
    if not math.isnan(in_situ) and in_situ > 0:
        ax.axvline(
            in_situ,
            color=color,
            linewidth=0.9,
            linestyle=":",
            gid="effective_vertical_stress",
            zorder=BEYOND_LAYER,  # a legend may cover it, as the dashed lines
        )
        drawn.add("effective_vertical_stress")
    return drawn


def _draw_construction(
    ax: Axes, record: dict[str, Any], xlim: tuple[float, float]
) -> None:
    """Draw Pacheco Silva's steps: e0 across, down, across, down to σ′p."""
    stress = record["preconsolidation_stress_pacheco_silva"]
    check = record["pacheco_silva"]
    if math.isnan(stress) or check is None:
        return
    e0, stress_a, void_ratio_b = (
        record["void_ratio"],
        check["stress_a"],
        check["void_ratio_b"],
    )
    on_curve = record["void_ratio_at_preconsolidation_stress_pacheco_silva"]
    for xs, ys in (
        ((xlim[0], stress_a), (e0, e0)),
        ((stress_a, stress_a), (e0, void_ratio_b)),
        ((stress_a, stress), (void_ratio_b, void_ratio_b)),
        ((stress, stress), (void_ratio_b, on_curve)),
    ):
        ax.plot(
            xs,
            ys,
            color=CONSTRUCTION_COLOR,
            linewidth=CONSTRUCTION_WIDTH,
            gid="construction",
            zorder=BEYOND_LAYER,
        )


def _point_handles(kinds: set[str]) -> list[Line2D]:
    handles = []
    for kind, (marker, filled, size, text) in POINT_KINDS.items():
        if kind in kinds:
            handles.append(
                _values.legend_marker(marker, LEGEND_COLOR, text, size, filled=filled)
            )
    return handles


def _mark_handles(marks: set[str]) -> list[Line2D]:
    handles = []
    for name, text in (
        ("compression_index", "Cc and Cr (dashed beyond their points)"),
        ("swelling_index", "Cs"),
        ("oikawa", "Oikawa's lines (dashed beyond their points)"),
    ):
        if name in marks:
            handles.append(
                Line2D(
                    [],
                    [],
                    color=LEGEND_COLOR,
                    linewidth=LINE_WIDTH,
                    alpha=SWELLING_ALPHA if name == "swelling_index" else 1.0,
                    label=text,
                )
            )
    for name, filled, text in (
        ("preconsolidation_stress", True, "σ′p (Oikawa)"),
        ("preconsolidation_stress_pacheco_silva", False, "σ′p (Pacheco Silva)"),
    ):
        if name in marks:
            handles.append(
                _values.legend_marker(
                    "v",
                    LEGEND_COLOR,
                    text,
                    TRIANGLE_SIZE if filled else CHECK_SIZE,
                    filled,
                )
            )
    if "effective_vertical_stress" in marks:
        handles.append(
            Line2D(
                [], [], color=LEGEND_COLOR, linewidth=0.9, linestyle=":", label="σ′v0"
            )
        )
    return handles


def _index_text(value: float) -> str:
    return f"{value:#.3g}"


def _specimen_name(result: OedometerFit, record: dict[str, Any]) -> str:
    """Name a specimen by its label and, where the rows give one, its depth."""
    depth = record["key"].get("depth")
    if depth is None or (isinstance(depth, float) and math.isnan(depth)):
        return record["label"]
    unit = result.depth_units.get("depth")
    return (
        f"{record['label']}, {format_number(float(depth))}{f' {unit}' if unit else ''}"
    )


def _box_lines(result: OedometerFit, record: dict[str, Any]) -> list[str]:
    """Write one specimen's values, and why any isn't given (P13 §8)."""
    unit = f" {result.unit}" if result.unit else ""
    name = _specimen_name(result, record)
    stress = record["preconsolidation_stress"]
    lines = []
    if math.isnan(stress):
        lines.append(
            f"{name}: σ′p not given: {record['preconsolidation_stress_reason']}"
        )
    else:
        lines.append(f"{name}: σ′p = {format_number(stress)}{unit} (Oikawa)")
        check = record["preconsolidation_stress_pacheco_silva"]
        if math.isnan(check):
            lines.append(f"Pacheco Silva not given: {record['pacheco_silva_reason']}")
        else:
            lines.append(f"Pacheco Silva: {format_number(check)}{unit}")
    values = [
        f"{symbol} = {_index_text(record[column])}"
        for symbol, column in (
            ("Cc", "compression_index"),
            ("Cr", "recompression_index"),
            ("Cs", "swelling_index"),
            ("CR", "compression_ratio"),
        )
        if not math.isnan(record[column])
    ]
    if values:
        lines.append(", ".join(values))
    if math.isnan(record["swelling_index"]):
        lines.append(f"Cs: {record['swelling_index_reason']}")
    if not math.isnan(stress) and math.isnan(record["compression_ratio"]):
        lines.append(f"CR not given: {record['compression_ratio_reason']}")
    lines.extend(_stress_history_lines(record, unit))
    head, *rest = lines
    return [head, *(f"  {line}" for line in rest)]


def _stress_history_lines(record: dict[str, Any], unit: str) -> list[str]:
    """Write OCR, Δe/e0 and the class with its row, or why each isn't given.

    A frame without ``effective_vertical_stress`` is said once, in the
    footnote, rather than for each specimen.
    """
    ocr = record["overconsolidation_ratio"]
    change = record["normalized_void_ratio_change"]
    stress_given = not math.isnan(record["preconsolidation_stress"])
    parts = []
    reasons = []
    if not math.isnan(ocr):
        parts.append(f"OCR = {ocr:.3g}{' (< 1)' if ocr < 1 else ''}")
    elif stress_given and not _no_column(record["overconsolidation_ratio_reason"]):
        reasons.append(f"OCR not given: {record['overconsolidation_ratio_reason']}")
    if not math.isnan(change):
        text = f"Δe/e0 = {_index_text(change)}"
        if record["sample_quality"] is not None:
            text += f": {record['sample_quality']} ({record['sample_quality_row']} row)"
        elif stress_given or not math.isnan(ocr):
            reasons.append(f"no class: {record['sample_quality_reason']}")
        else:
            reasons.append("no class without an OCR")
        parts.append(text)
    else:
        reason = record["normalized_void_ratio_change_reason"]
        repeated = reason == record["overconsolidation_ratio_reason"] and stress_given
        if not repeated and not _no_column(reason):
            reasons.append(f"Δe/e0 not given: {reason}")
    return ([", ".join(parts)] if parts else []) + reasons


def _no_column(reason: str | None) -> bool:
    return reason is not None and reason.startswith(NO_COLUMN)


def _draw_box(ax: Axes, result: OedometerFit, drawn: list[dict[str, Any]]) -> None:
    """Write each specimen's values in the upper right (P13 §8)."""
    lines = []
    for record in drawn:
        for line in _box_lines(result, record):
            indent = " " * (len(line) - len(line.lstrip()))
            lines += textwrap.wrap(
                line.strip(),
                BOX_WIDTH,
                initial_indent=indent,
                subsequent_indent=indent + "    ",
                break_on_hyphens=False,
            )
    if not lines:
        return
    ax.annotate(
        "\n".join(lines),
        xy=(0.98, 0.98),
        xycoords="axes fraction",
        ha="right",
        va="top",
        multialignment="left",
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


def _footnote(
    result: OedometerFit, drawn: list[dict[str, Any]], fit: bool, notes: Notes
) -> None:
    """Count the rows no line used, name the specimens not drawn (P13 §8, §11)."""
    for record in drawn:
        reasons = _LEFT_OUT if fit else NOT_DRAWN
        parts = [
            f"{record[name]} {_LEFT_OUT_TEXT[name]}" for name in reasons if record[name]
        ]
        if parts:
            what = "Left out of" if fit else "Not drawn from"
            notes.add_text(f"{what} {record['label']}: {', '.join(parts)}")
    missing = [
        record["label"]
        for record in result.specimens
        if all(record is not other for other in drawn)
    ]
    if missing:
        notes.add_text(f"Not drawn, no increments to draw: {', '.join(missing)}")
    if fit and any(
        _no_column(record["normalized_void_ratio_change_reason"]) for record in drawn
    ):
        notes.add_text(
            "No OCR or Δe/e0: run ht.analysis.vertical_stress() on the rows for σ′v0."
        )
    if fit and any(record["sample_quality"] is not None for record in drawn):
        notes.add_text(CAVEAT)
