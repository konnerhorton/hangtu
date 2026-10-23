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
    """
    xlim = tuple(sorted(ax.get_xlim()))
    lower, upper = bounds
    beyond = np.zeros(len(y), dtype=bool)
    if ylim is not None:
        low, high = sorted(ylim)
        beyond = rows & ((y < low) | (y > high))
    shown = rows & ~beyond
    both = shown & np.isfinite(lower) & np.isfinite(upper)
    for group, color in colors.items():
        these = shown & (groups == group) if group is not None else shown
        bars = np.flatnonzero(these & both)
        if bars.size:
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
            )
            ends = np.concatenate([bars, bars])
            edge = edge_markers(
                ax,
                np.concatenate([lower[bars], upper[bars]]),
                y[ends],
                {"x": xlim},
                color,
                END,
            )
            beyond[ends[edge]] = True
        for mask, marker in (
            (these & ~both & np.isfinite(lower), LOWER_ONLY),
            (these & ~both & np.isfinite(upper), UPPER_ONLY),
        ):
            single = np.flatnonzero(mask)
            if not single.size:
                continue
            x = lower[single] if marker == LOWER_ONLY else upper[single]
            edge = edge_markers(ax, x, y[single], {"x": xlim}, color, marker)
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
            )
    if not shown.any():
        return [], beyond
    handle = Line2D(
        [],
        [],
        color=_values.NEUTRAL,
        linewidth=BAR_WIDTH,
        solid_capstyle="butt",
        label=LEGEND_TEXT,
    )
    return [handle], beyond
