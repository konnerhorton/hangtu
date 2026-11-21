"""P14 consolidation coefficients (docs/plots/P14-consolidation-coefficients.md)."""

import math
import textwrap
from collections.abc import Sequence
from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.typing import LineStyleType

from hangtu import units as _units
from hangtu._data import numeric_column
from hangtu._settings import _display_units, figure_size, settings
from hangtu.analysis._oedometer import LOADING, RELOADING, UNLOADING
from hangtu.analysis._oedometer_increments import (
    FIRST_INCREMENT,
    NOT_POSITIVE,
    SPANS,
    STRESS_AT_START,
    VOLUME_COMPRESSIBILITY,
    _label,
    oedometer_increments,
)
from hangtu.errors import HangtuError
from hangtu.plot import _layers, _values, style
from hangtu.plot._hints import hint_missing
from hangtu.plot._labels import axis_label
from hangtu.plot._legend import CORNERS, _corner_obstacles, add_legend
from hangtu.plot._limits import log_limits, set_log_axis
from hangtu.plot._notes import Notes
from hangtu.plot._palette import resolve_palette
from hangtu.stats._rows import group_keys

BRANCHES = (LOADING, UNLOADING, RELOADING)
_STRESS = "applied_vertical_stress"
_IN_SITU = "effective_vertical_stress"
_REPORTED_VOLUME = "reported_coefficient_of_volume_compressibility"
#: (column, gid, linestyle, legend text) of each c_v the lab reports (P14 §7).
CONSOLIDATION: tuple[tuple[str, str, LineStyleType, str], ...] = (
    (
        "reported_coefficient_of_consolidation_root_time",
        "consolidation_root_time",
        "-",
        "c_v, root time (lab)",
    ),
    (
        "reported_coefficient_of_consolidation_log_time",
        "consolidation_log_time",
        ":",
        "c_v, log time (lab)",
    ),
)
LEGEND_COLOR = "black"
LINE_WIDTH = 1.6
UNLOAD_WIDTH = 0.9
#: The increments spanning σ′v0 are drawn this many times wider (P14 §7).
SPANNING_FACTOR = 2.2
UNLOAD_ALPHA = 0.55
CROSS_SIZE = 6.0
IN_SITU_WIDTH = 0.9
NO_DATA_COLOR = "0.4"
#: Characters per line of a y label: two panels leave too little height for one.
LABEL_WIDTH = 32
#: Each blank m_v's reason, as the footnote shortens it.
SHORT_REASON = {
    FIRST_INCREMENT: "start stress not given",
    NOT_POSITIVE: "m_v not positive",
}


def consolidation_coefficients(
    df: pd.DataFrame,
    *,
    reported: bool = True,
    branches: Sequence[str] = BRANCHES,
    note: str | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    **style_overrides: Any,
) -> tuple[Figure, np.ndarray]:
    """Plot m_v and c_v of each oedometer increment against log σ′v.

    Two panels share a log σ′v axis: the coefficient of volume
    compressibility m_v above and the lab's coefficient of consolidation
    c_v below, both on log axes. Each increment is a horizontal segment
    from its start stress σ′1 to its end stress σ′2, since each value is a
    secant over the increment, not a value at one stress. m_v is the one
    ``ht.analysis.oedometer_increments()`` recomputes from the void ratios,
    drawn, never recomputed here:

    - loading increments solid; unloading and reloading increments thin,
      dashed and lighter, since BS 1377-5:1990 defines m_v on loading
      increments only;
    - the lab's m_v as a × at each segment's geometric midpoint,
      √(σ′1 σ′2), so a value that doesn't follow from the void ratios shows
      apart from its segment;
    - c_v by root time solid and by log time dotted, as the lab reports
      them. The first increment, whose start stress isn't given, has no
      m_v; its c_v is a × at its end stress;
    - σ′v0, where the rows have it (from ``ht.analysis.vertical_stress()``),
      as a dotted vertical line through both panels, with the increments
      spanning it (``spans_effective_vertical_stress``) drawn thicker: those
      give m_v, c_v and k at the in situ stress.

    The footnote names each increment whose m_v isn't drawn, and why: the
    first (its start stress isn't given), a constant stress, an m_v of 0 or
    less, which a log axis can't show.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per increment, as ``p.oedometer()`` gives or a CSV in
        ``ht.template("oedometer")``'s shape: ``specimen_id``,
        ``applied_vertical_stress`` and ``void_ratio_at_increment_end``, in
        the order the increments were applied.
    reported : bool
        Draw the lab's m_v (``reported_coefficient_of_volume_compressibility``)
        as × marks.
    branches : sequence of str
        The load branches drawn, from ``"loading"``, ``"unloading"`` and
        ``"reloading"``; ``("loading",)`` draws the loading increments only.
    note : str, optional
        Free text, added to the footnote.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.
    display_units : {"US", "SI"}, optional
        Stresses in psf or kPa (or the unit
        ``ht.settings.display_overrides["stress"]`` names), m_v in ft²/kip or
        m²/MN and c_v in ft²/yr or m²/yr. Defaults to
        ``ht.settings.display_units``.
    figsize : tuple, optional
        Figure size in inches. Defaults to
        ``ht.settings.figure_sizes["stacked"]``.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, axs
        ``axs`` holds the m_v axes and the c_v axes, in that order.

    Raises
    ------
    HangtuError
        For a ``branches`` that is empty or names a branch other than the
        three, and as ``ht.analysis.oedometer_increments()`` raises.

    Examples
    --------
    >>> oed = ht.analysis.vertical_stress(p.oedometer(), p.stratigraphy())
    >>> fig, axs = ht.plot.consolidation_coefficients(oed)
    >>> fig, axs = ht.plot.consolidation_coefficients(oed, branches=("loading",))
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    chosen = _check_branches(branches)
    system = _display_units(display_units or settings.display_units)

    with style.context(**style_overrides):
        hint_missing(
            df,
            {
                _IN_SITU: "no σ′v0 line; run ht.analysis.vertical_stress() on the "
                "rows first"
            },
        )
        increments = oedometer_increments(df, units=units, display_units=system)
        fig, axs = plt.subplots(
            2,
            1,
            sharex=True,
            figsize=figsize or figure_size("stacked"),
            layout="constrained",
        )
        upper, lower = axs
        for ax in axs:
            style.style_axes(ax)
        notes = Notes()
        frame_units = increments.attrs["units"]
        consolidation = {
            column: _reported(increments, column, units, system, notes)
            for column, *_ in CONSOLIDATION
        }
        lab = (
            _reported(increments, _REPORTED_VOLUME, units, system, notes)
            if reported
            else (None, None)
        )
        specimens = _specimens(increments)
        drawn = [s for s in specimens if s["drawable"]]
        colors = _colors(increments, [s["label"] for s in drawn])

        stresses: list[float] = []
        volumes: list[float] = []
        coefficients: list[float] = []
        marks: set[str] = set()
        for specimen in drawn:
            color = colors[specimen["label"]]
            marks |= _draw_volume(
                upper,
                increments,
                specimen,
                chosen,
                color,
                lab[0],
                stresses,
                volumes,
            )
            marks |= _draw_consolidation(
                lower,
                increments,
                specimen,
                chosen,
                color,
                consolidation,
                stresses,
                coefficients,
            )
            if _draw_in_situ(axs, specimen, color, stresses):
                marks.add(_IN_SITU)
        _set_axes(
            axs,
            stresses,
            volumes,
            coefficients,
            axis_label("Effective vertical stress, σ′v", frame_units.get(_STRESS)),
            axis_label(
                "Coefficient of volume compressibility, m_v",
                frame_units.get(VOLUME_COMPRESSIBILITY),
            ),
            axis_label(
                "Coefficient of consolidation, c_v",
                next((unit for _, unit in consolidation.values() if unit), None),
            ),
        )
        if not volumes:
            _no_data(upper, "No data")
        if not any(values is not None for values, _ in consolidation.values()):
            _no_data(lower, "No c_v reported")
        elif not coefficients:
            _no_data(lower, "No c_v drawn")
        _footnote(increments, specimens, chosen, notes)
        if note is not None:
            notes.add_text(str(note))

        handles = (
            [
                _values.legend_marker("s", colors[s["label"]], s["label"], CROSS_SIZE)
                for s in drawn
            ]
            if len(drawn) > 1
            else []
        )
        lower_sections = [[], _consolidation_handles(marks)]
        if not _legend_in_a_clear_corner(upper, [handles, _volume_handles(marks)]):
            lower_sections = [handles, _volume_handles(marks) + lower_sections[1]]
        placed = add_legend(lower, lower_sections, notes)
        notes.render(lower, where=placed.where, below=placed.legend)
    return fig, np.asarray(axs)


def _legend_in_a_clear_corner(ax: Axes, sections: list[list[Line2D]]) -> bool:
    """Put the m_v panel's legend in a clear corner of it, or draw none (P14 §5).

    Returns False when no corner is clear: the entries then join the c_v
    panel's legend, which goes below the x label if that panel has no clear
    corner either, so no legend covers a segment.
    """
    legend = add_legend(ax, sections, Notes(), where="inside").legend
    if legend is None:
        return True
    counts = _corner_obstacles(ax, legend)
    clear = [corner for corner in CORNERS if counts[corner] == 0]
    if clear:
        legend.set_loc(clear[0])
        return True
    legend.remove()
    return False


def _check_branches(branches: Sequence[str] | str) -> tuple[str, ...]:
    chosen = (branches,) if isinstance(branches, str) else tuple(branches)
    unknown = [branch for branch in chosen if branch not in BRANCHES]
    if not chosen or unknown:
        what = "is empty" if not chosen else f"has {', '.join(map(repr, unknown))}"
        raise HangtuError(
            f"branches= {what}: give one or more of {', '.join(map(repr, BRANCHES))}."
        )
    return chosen


def _reported(
    df: pd.DataFrame,
    column: str,
    units: dict[str, str] | None,
    system: str,
    notes: Notes,
) -> tuple[np.ndarray | None, str | None]:
    """Return a lab's column in the display unit, and the unit; None if absent.

    A column without a unit isn't drawn, and the footnote says so: its
    values can't be placed on an axis in the display unit.
    """
    if column not in df.columns or df[column].isna().all():
        return None, None
    declared = (units or {}).get(column) or _units.units_of(df).get(column)
    if declared is None:
        notes.add_text(f"{column} not drawn: its unit isn't given.")
        return None, None
    kind = (
        "volume_compressibility"
        if column == _REPORTED_VOLUME
        else "consolidation_coefficient"
    )
    values, unit = _units.to_display(numeric_column(df, column), declared, kind, system)
    return np.asarray(values, dtype=float), unit


def _specimens(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Each specimen's label, rows in order, σ′v0 and whether it has increments."""
    specimens = []
    in_situ = (
        numeric_column(df, _IN_SITU)
        if _IN_SITU in df.columns
        else np.full(len(df), np.nan)
    )
    stress = numeric_column(df, _STRESS)
    for _, rows in group_keys(df, ["specimen_id"]):
        positions = np.flatnonzero(rows)
        values = in_situ[positions]
        given = values[~np.isnan(values)]
        specimens.append(
            {
                "label": _label(df, positions),
                "positions": positions,
                "in_situ": float(given[0]) if len(given) else math.nan,
                "drawable": bool((~np.isnan(stress[positions])).any()),
            }
        )
    return specimens


def _colors(df: pd.DataFrame, labels: list[str]) -> dict[str, Any]:
    return resolve_palette(labels, None, labels, df.attrs.get("palette"))


def _branch_of(df: pd.DataFrame, row: int) -> Any:
    value = df["load_branch"].iloc[row]
    return None if pd.isna(value) else value


def _spanning(df: pd.DataFrame, row: int) -> bool:
    value = df[SPANS].iloc[row]
    return bool(value) if not pd.isna(value) else False


def _segment_style(branch: Any, spanning: bool) -> dict[str, Any]:
    loading = branch == LOADING
    width = LINE_WIDTH if loading else UNLOAD_WIDTH
    return {
        "linewidth": width * (SPANNING_FACTOR if spanning else 1.0),
        "linestyle": "-" if loading else "--",
        "alpha": 1.0 if loading else UNLOAD_ALPHA,
    }


def _draw_volume(
    ax: Axes,
    df: pd.DataFrame,
    specimen: dict[str, Any],
    chosen: tuple[str, ...],
    color: Any,
    lab: np.ndarray | None,
    stresses: list[float],
    volumes: list[float],
) -> set[str]:
    """Draw one specimen's m_v segments and the lab's marks (P14 §7)."""
    marks = set()
    start = numeric_column(df, STRESS_AT_START)
    end = numeric_column(df, _STRESS)
    volume = numeric_column(df, VOLUME_COMPRESSIBILITY)
    for position in specimen["positions"]:
        row = int(position)
        branch = _branch_of(df, row)
        if branch not in chosen:
            continue
        s1, s2, value = start[row], end[row], volume[row]
        if not (np.isnan(s1) or np.isnan(s2) or np.isnan(value)) and value > 0:
            name = "volume_loading" if branch == LOADING else "volume_unload_reload"
            ax.plot(
                [min(s1, s2), max(s1, s2)],
                [value, value],
                color=color,
                gid=name,
                solid_capstyle="butt",
                zorder=_layers.LINES,
                **_segment_style(branch, _spanning(df, row)),
            )
            marks.add(name)
            stresses.extend([s1, s2])
            volumes.append(value)
        if lab is not None and lab[row] > 0 and not np.isnan(s2) and s2 > 0:
            x = math.sqrt(s1 * s2) if s1 > 0 else s2  # False for NaN
            ax.plot(
                [x],
                [lab[row]],
                marker="x",
                markersize=CROSS_SIZE,
                color=color,
                linestyle="none",
                gid="volume_reported",
                zorder=_layers.MARKERS,
            )
            marks.add("volume_reported")
            stresses.append(x)
            volumes.append(float(lab[row]))
    return marks


def _draw_consolidation(
    ax: Axes,
    df: pd.DataFrame,
    specimen: dict[str, Any],
    chosen: tuple[str, ...],
    color: Any,
    consolidation: dict[str, tuple[np.ndarray | None, str | None]],
    stresses: list[float],
    coefficients: list[float],
) -> set[str]:
    """Draw one specimen's c_v by each method: segments, or × without a span."""
    marks = set()
    start = numeric_column(df, STRESS_AT_START)
    end = numeric_column(df, _STRESS)
    for column, gid, linestyle, _ in CONSOLIDATION:
        values = consolidation[column][0]
        if values is None:
            continue
        for position in specimen["positions"]:
            row = int(position)
            branch = _branch_of(df, row)
            s1, s2, value = start[row], end[row], values[row]
            if branch not in chosen or np.isnan(s2) or not value > 0 or not s2 > 0:
                continue
            spanning = _spanning(df, row)
            if s1 > 0 and s1 != s2:  # False for NaN
                style_ = _segment_style(branch, spanning)
                style_["linestyle"] = linestyle
                ax.plot(
                    [min(s1, s2), max(s1, s2)],
                    [value, value],
                    color=color,
                    gid=gid,
                    solid_capstyle="butt",
                    zorder=_layers.LINES,
                    **style_,
                )
                stresses.extend([s1, s2])
            else:
                ax.plot(
                    [s2],
                    [value],
                    marker="x",
                    markersize=CROSS_SIZE,
                    color=color,
                    linestyle="none",
                    gid=f"{gid}_point",
                    zorder=_layers.MARKERS,
                )
                stresses.append(s2)
            coefficients.append(float(value))
            marks.add(gid)
    return marks


def _draw_in_situ(
    axs: Sequence[Axes], specimen: dict[str, Any], color: Any, stresses: list[float]
) -> bool:
    value = specimen["in_situ"]
    if not value > 0:  # False for NaN
        return False
    for ax in axs:
        ax.axvline(
            value,
            color=color,
            linewidth=IN_SITU_WIDTH,
            linestyle=":",
            gid=_IN_SITU,
            zorder=_layers.RANGES,  # a legend may cover it
        )
    stresses.append(value)
    return True


def _set_axes(
    axs: Sequence[Axes],
    stresses: list[float],
    volumes: list[float],
    coefficients: list[float],
    x_label: str,
    upper_label: str,
    lower_label: str,
) -> None:
    """Log axes: σ′v shared, m_v above and c_v below (P14 §6)."""
    upper, lower = axs
    positive = [s for s in stresses if s > 0]
    x = log_limits(min(positive), max(positive)) if positive else (1.0, 100.0)
    for ax, values, label in (
        (upper, volumes, upper_label),
        (lower, coefficients, lower_label),
    ):
        set_log_axis(ax, "x", x)
        y = log_limits(min(values), max(values)) if values else (0.01, 1.0)
        set_log_axis(ax, "y", y)
        ax.set_ylabel(textwrap.fill(label, LABEL_WIDTH, break_on_hyphens=False))
    lower.set_xlabel(x_label)


def _no_data(ax: Axes, text: str) -> None:
    ax.text(
        0.5,
        0.5,
        text,
        transform=ax.transAxes,
        ha="center",
        va="center",
        color=NO_DATA_COLOR,
        gid="no_data",
        zorder=_layers.ANNOTATIONS,
    )


def _footnote(
    df: pd.DataFrame,
    specimens: list[dict[str, Any]],
    chosen: tuple[str, ...],
    notes: Notes,
) -> None:
    """Name the increments whose m_v isn't drawn, and why (P14 §8, §11)."""
    volume = numeric_column(df, VOLUME_COMPRESSIBILITY)
    reasons = df[f"{VOLUME_COMPRESSIBILITY}_reason"]
    consolidation = [df[c] for c, *_ in CONSOLIDATION if c in df.columns]
    for specimen in specimens:
        if not specimen["drawable"]:
            continue
        parts = []
        for number, position in enumerate(specimen["positions"], start=1):
            row = int(position)
            branch = _branch_of(df, row)
            if branch in BRANCHES and branch not in chosen:
                continue  # left out by branches=; a constant stress is named
            value = volume[row]
            if np.isnan(value):
                why = reasons.iloc[row]
                text = SHORT_REASON.get(why, why)
            elif value <= 0:
                text = SHORT_REASON[NOT_POSITIVE]
            else:
                continue
            parts.append(f"increment {number} ({text})")
        if parts:
            notes.add_text(f"Not drawn for {specimen['label']}: {', '.join(parts)}")
        not_positive = sum(
            int((pd.to_numeric(column.iloc[specimen["positions"]]) <= 0).sum())
            for column in consolidation
        )
        if not_positive:
            s = "s" if not_positive > 1 else ""
            notes.add_text(
                f"Not drawn for {specimen['label']}: {not_positive} c_v value{s} "
                "not positive"
            )
        in_situ = specimen["in_situ"]
        if (
            in_situ > 0
            and not df[SPANS].iloc[specimen["positions"]].fillna(False).any()
        ):
            notes.add_text(f"No increment of {specimen['label']} spans σ′v0")
    missing = [s["label"] for s in specimens if not s["drawable"]]
    if missing:
        notes.add_text(f"Not drawn, no increments to draw: {', '.join(missing)}")


def _volume_handles(marks: set[str]) -> list[Line2D]:
    handles = []
    for name, text in (
        ("volume_loading", "m_v, loading"),
        ("volume_unload_reload", "m_v, unloading or reloading"),
    ):
        if name in marks:
            branch = LOADING if name == "volume_loading" else UNLOADING
            handles.append(
                Line2D(
                    [],
                    [],
                    color=LEGEND_COLOR,
                    label=text,
                    **_segment_style(branch, False),
                )
            )
    if "volume_reported" in marks:
        handles.append(
            _values.legend_marker(
                "x", LEGEND_COLOR, "m_v reported by the lab", CROSS_SIZE
            )
        )
    if _IN_SITU in marks:
        handles.append(
            Line2D(
                [],
                [],
                color=LEGEND_COLOR,
                linewidth=IN_SITU_WIDTH,
                linestyle=":",
                label="σ′v0",
            )
        )
    return handles


def _consolidation_handles(marks: set[str]) -> list[Line2D]:
    return [
        Line2D(
            [],
            [],
            color=LEGEND_COLOR,
            linewidth=LINE_WIDTH,
            linestyle=linestyle,
            label=text,
        )
        for _, gid, linestyle, text in CONSOLIDATION
        if gid in marks
    ]
