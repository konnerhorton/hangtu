"""Text in a value column, drawn at the left edge (P01 §3, §7; TODO #15).

A cell such as ``NP`` or ``dry`` has no position on the value axis, so it is
drawn as an open marker just inside the left edge at its depth, one shape
per text, and counted.
"""

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.transforms import offset_copy

from hangtu._data import TEXT_FLAGS, rows_text
from hangtu.errors import warn
from hangtu.plot import _layers, _values
from hangtu.plot._notes import Notes, edge_markers

# ◇ □ △ ▽ ⬠ ⬡, then repeating (P01 §7).
SHAPES = ("D", "s", "^", "v", "p", "h")
SIZE = 5.0  # points
INSET = 4.0  # points inside the left edge
MAX_LISTED = 6  # texts in the legend
WHERE = ", shown at the left edge"
# Recognized flags -> notes reason; other text is "text_value".
REASONS = {"NP": "non_plastic", "refusal": "refusal"}


def order(texts: np.ndarray) -> list[str]:
    """Return the distinct texts: NP, refusal, then the rest by first appearance."""
    present = dict.fromkeys(text for text in texts if text)
    flags = [flag for flag in TEXT_FLAGS.values() if flag in present]
    return flags + [text for text in present if text not in flags]


def label(text: str) -> str:
    """Legend text for a text value: ``NP``, ``refusal`` or ``'dry'``."""
    return text if text in REASONS else repr(text)


def warn_unrecognized(index: pd.Index, column: str, texts: np.ndarray) -> None:
    """Warn once about text that isn't a recognized flag, naming the rows."""
    other = np.array([bool(text) and text not in REASONS for text in texts])
    if not other.any():
        return
    found = ", ".join(
        f"{text!r} ({np.count_nonzero(texts == text)})" for text in order(texts[other])
    )
    warn(
        f"Column {column!r} has text in rows {rows_text(index[other])}: {found}. "
        "They are drawn at the left edge and counted; clean the column to "
        "remove them."
    )


def draw_text_values(
    ax: Axes,
    y: np.ndarray,
    texts: np.ndarray,
    groups: np.ndarray,
    colors: Mapping[Any, Any],
    ylim: tuple[float, float] | None,
    notes: Notes,
) -> tuple[list[Line2D], np.ndarray]:
    """Draw the text values at the left edge, count them, and return the legend.

    ``texts`` holds each row's text, or ``""``; rows with a blank ``y`` must
    already be cleared. Rows beyond ``ylim`` are drawn at the limit with an
    arrow. Returns the legend entries and the mask of rows drawn at the edge.
    """
    edge = np.zeros(len(texts), dtype=bool)
    distinct = order(texts)
    if not distinct:
        return [], edge
    transform = offset_copy(
        ax.get_yaxis_transform(), ax.figure, x=INSET, units="points"
    )
    handles = []
    for i, text in enumerate(distinct):
        shape = SHAPES[i % len(SHAPES)]
        rows = texts == text
        for group, color in colors.items():
            these = rows & (groups == group) if group is not None else rows
            if not these.any():
                continue
            x = np.zeros(np.count_nonzero(these))
            if ylim is not None:
                edge[these] = edge_markers(
                    ax, x, y[these], {"y": ylim}, color, shape, transform
                )
            inside = these & ~edge
            ax.scatter(
                np.zeros(np.count_nonzero(inside)),
                y[inside],
                s=SIZE**2,
                marker=shape,
                facecolors="none",
                edgecolors=color,
                linewidths=0.8,
                clip_on=False,
                transform=transform,
                zorder=_layers.MARKERS,
            )
        reason = REASONS.get(text, "text_value")
        n = notes.count(rows, reason)
        notes.set_where(reason, WHERE)
        if i < MAX_LISTED:
            handles.append(
                _values.legend_marker(
                    shape, _values.NEUTRAL, f"{label(text)} ({n})", SIZE, filled=False
                )
            )
    rest = distinct[MAX_LISTED:]
    if rest:
        notes.add_text(
            "Not in the legend: "
            + ", ".join(
                f"{label(text)} ({np.count_nonzero(texts == text)})" for text in rest
            )
        )
    return handles, edge
