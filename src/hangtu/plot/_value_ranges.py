"""P01 value ranges: a value reported as a range at one depth (P01 §3, §7).

A correlation that gives a band (``ht.analysis.correlations``) writes
``<value>_lower`` and ``<value>_upper`` beside ``<value>``. P01 draws the two
bounds as a bar at the row's depth, and one bound alone as a caret at it.
"""

from collections.abc import Mapping
from typing import Any, NamedTuple

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.transforms import ScaledTranslation, Transform

from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu.errors import ColumnError
from hangtu.plot import _layers, _values
from hangtu.plot._notes import edge_markers

BAR_WIDTH = 1.2  # points
END = "|"  # a bar's end drawn at the edge of fixed limits
LOWER_ONLY = ">"  # ▷: the value is at least the bound
UPPER_ONLY = "<"  # ◁: the value is at most the bound
LEGEND_TEXT = "range"
LEGEND_LENGTH = 14.0  # points
# Between the ranges of two groups at one depth: about two and a half bars.
GROUP_SPACING = 3.0  # points


class Bounds(NamedTuple):
    """Each row's bounds in display units, NaN where blank."""

    lower: np.ndarray
    upper: np.ndarray

    def any(self) -> np.ndarray:
        """Rows with at least one bound."""
        return np.isfinite(self.lower) | np.isfinite(self.upper)

    def x(self, log: bool) -> np.ndarray:
        """Return the bounds the automatic x limits cover (positive ones on log)."""
        values = np.concatenate([self.lower, self.upper])
        values = values[np.isfinite(values)]
        return values[values > 0] if log else values


def columns(value: str) -> tuple[str, str]:
    """``(<value>_lower, <value>_upper)``."""
    return f"{value}_lower", f"{value}_upper"


def read(
    df: pd.DataFrame,
    value: str,
    units: Mapping[str, str] | None,
    quantity: str | None,
    system: str,
) -> Bounds | None:
    """Return the rows' bounds in display units, or None when ``df`` has neither column.

    Each bound's unit resolves as the value's does (``units=``, then
    ``df.attrs["units"]``). A row with its lower bound above its upper bound
    is an error naming it.
    """
    names = [column for column in columns(value) if column in df.columns]
    if not names:
        return None
    quantities = dict.fromkeys(names, quantity) if quantity else None
    resolved = _units.resolve_units(df, names, units, quantities=quantities)
    found = {}
    for column in columns(value):
        if column in df.columns:
            found[column], _ = _units.to_display(
                numeric_column(df, column), resolved[column], quantity, system
            )
        else:
            found[column] = np.full(len(df), np.nan)
    lower, upper = found.values()
    swapped = lower > upper
    if swapped.any():
        raise ColumnError(
            f"Rows {rows_text(df.index[swapped])} have {names[0]!r} above "
            f"{columns(value)[1]!r}. Swap the two bounds on those rows."
        )
    return Bounds(lower, upper)


def check_qualifiers(
    df: pd.DataFrame, value: str, bounds: Bounds, flags: np.ndarray
) -> None:
    """Raise when a row has both a qualifier and a bound: a range carries its own."""
    both = bounds.any() & (flags != "")
    if both.any():
        lower, upper = columns(value)
        raise ColumnError(
            f"Rows {rows_text(df.index[both])} have a qualifier and a bound in "
            f"{lower!r} or {upper!r}. A range carries its own bounds: clear "
            "'qualifier' on those rows, or the bounds."
        )


def offsets(
    y: np.ndarray, shown: np.ndarray, groups: np.ndarray, order: list[Any]
) -> np.ndarray:
    """Each row's vertical offset in points, so ranges at one depth stay apart.

    At a depth where two or more groups draw a range, the groups there are
    spread ``GROUP_SPACING`` points apart, centered on the depth, the first in
    legend order highest on the page. Everywhere else a range is drawn at
    its depth.
    """
    moved = np.zeros(len(y))
    rank = {group: k for k, group in enumerate(order)}
    for depth in np.unique(y[shown]):
        here = shown & (y == depth)
        present = sorted(dict.fromkeys(groups[here]), key=rank.__getitem__)
        if len(present) < 2:
            continue
        middle = (len(present) - 1) / 2
        for k, group in enumerate(present):
            moved[here & (groups == group)] = (middle - k) * GROUP_SPACING
    return moved


def shifted(ax: Axes, points: float) -> Transform:
    """Return data coordinates moved ``points`` up the page."""
    if not points:
        return ax.transData
    return ax.transData + ScaledTranslation(0, points / 72, ax.figure.dpi_scale_trans)


def draw(
    ax: Axes,
    bounds: Bounds,
    y: np.ndarray,
    rows: np.ndarray,
    groups: np.ndarray,
    colors: Mapping[Any, Any],
    ylim: tuple[float, float] | None,
) -> tuple[list[Line2D], np.ndarray]:
    """Draw each row's range in its group's color, after the axis limits are set.

    A bound beyond the x-axis limits (fixed ones, or a bound ≤ 0 on a log
    axis) is drawn at the edge with an outward arrow, and the bar stops
    there. A row beyond ``ylim`` isn't drawn. Returns the legend entry and
    the mask of rows at or beyond the edge, to count as beyond the limit.

    Where two or more groups draw a range at one depth, their bars and
    carets are moved apart up and down the page (``offsets()``), so a narrow
    band isn't hidden under a wide one. The data, and a value's marker, stay
    at the row's depth.
    """
    xlim = tuple(sorted(ax.get_xlim()))
    lower, upper = bounds
    beyond = np.zeros(len(y), dtype=bool)
    if ylim is not None:
        low, high = sorted(ylim)
        beyond = rows & ((y < low) | (y > high))
    shown = rows & ~beyond
    both = shown & np.isfinite(lower) & np.isfinite(upper)
    moved = offsets(y, shown, groups, list(colors))
    for group, color in colors.items():
        these = shown & (groups == group) if group is not None else shown
        for points in np.unique(moved[these]):
            here = these & (moved == points)
            transform = shifted(ax, float(points))
            beyond |= _draw_bars(ax, bounds, y, here & both, color, xlim, transform)
            beyond |= _draw_carets(ax, bounds, y, here & ~both, color, xlim, transform)
    if not shown.any():
        return [], beyond
    return [legend_bar(_values.NEUTRAL, LEGEND_TEXT)], beyond


def _draw_bars(
    ax: Axes,
    bounds: Bounds,
    y: np.ndarray,
    rows: np.ndarray,
    color: Any,
    xlim: tuple[float, float],
    transform: Transform,
) -> np.ndarray:
    """Draw a bar for each row with both bounds; return the rows at the edge."""
    lower, upper = bounds
    beyond = np.zeros(len(y), dtype=bool)
    bars = np.flatnonzero(rows)
    if not bars.size:
        return beyond
    gaps = np.full(bars.size, np.nan)
    ax.plot(
        np.column_stack(
            [np.clip(lower[bars], *xlim), np.clip(upper[bars], *xlim), gaps]
        ).ravel(),
        np.column_stack([y[bars], y[bars], gaps]).ravel(),
        color=color,
        linewidth=BAR_WIDTH,
        solid_capstyle="butt",
        zorder=_layers.INTERVALS,
        gid="value_range",
        transform=transform,
    )
    ends = np.concatenate([bars, bars])
    edge = edge_markers(
        ax,
        np.concatenate([lower[bars], upper[bars]]),
        y[ends],
        {"x": xlim},
        color,
        END,
        transform=transform,
    )
    beyond[ends[edge]] = True
    return beyond


def _draw_carets(
    ax: Axes,
    bounds: Bounds,
    y: np.ndarray,
    rows: np.ndarray,
    color: Any,
    xlim: tuple[float, float],
    transform: Transform,
) -> np.ndarray:
    """Draw a caret at each row's one bound; return the rows at the edge."""
    lower, upper = bounds
    beyond = np.zeros(len(y), dtype=bool)
    for mask, marker in (
        (rows & np.isfinite(lower), LOWER_ONLY),
        (rows & np.isfinite(upper), UPPER_ONLY),
    ):
        single = np.flatnonzero(mask)
        if not single.size:
            continue
        x = lower[single] if marker == LOWER_ONLY else upper[single]
        edge = edge_markers(
            ax, x, y[single], {"x": xlim}, color, marker, transform=transform
        )
        beyond[single[edge]] = True
        ax.scatter(
            x[~edge],
            y[single][~edge],
            s=_values.CARET_SIZE**2,
            marker=marker,
            color=color,
            edgecolors="white",
            linewidths=0.4,
            zorder=_layers.QUALIFIERS,
            gid="value_range_bound",
            transform=transform,
        )
    return beyond


def legend_bar(color: Any, label: str) -> Line2D:
    """Return a legend entry drawn as a range bar."""
    return Line2D(
        [], [], color=color, linewidth=BAR_WIDTH, solid_capstyle="butt", label=label
    )
