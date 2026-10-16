"""Exclusion notes and out-of-range markers (docs/plots/P00-framework.md §9).

Plots never drop data silently: every value that isn't drawn normally is
counted here and listed in a footnote.
"""

from collections.abc import Mapping

import numpy as np
from matplotlib.axes import Axes
from matplotlib.text import Annotation
from numpy.typing import ArrayLike

# Footnote wording by reason. {n} is the count, {s} the plural ending, and
# {where} optional detail a plot sets with Notes.set_where (P02: the cap).
REASONS = {
    "nan": "{n} blank value{s} not shown",
    "log_nonpositive": "{n} value{s} ≤ 0 not shown on log axis",
    "beyond_limit": "{n} value{s} beyond axis limit, shown at the edge",
    "less_than": "{n} value{s} reported as less than (<)",
    "greater_than": "{n} value{s} reported as greater than (>)",
    "refusal": "{n} refusal{s}{where}",
    "refusal_excluded": "{n} refusal{s} not shown",
    "no_energy_ratio": "{n} test{s} without an energy ratio not shown",
    "non_plastic": "{n} non-plastic (NP) value{s}",
    "non_plastic_excluded": "{n} non-plastic (NP) specimen{s} not shown",
}

FOOTNOTE_SIZE = 7
FOOTNOTE_COLOR = "0.4"
ARROW_LENGTH = 10  # points


class Notes:
    """Collects counts of values a plot couldn't draw normally, by reason.

    Examples
    --------
    >>> notes = Notes()
    >>> notes.count(np.isnan(values), "nan")
    >>> notes.render(ax)  # footnote, and ax.ags_notes == {"nan": 2}
    """

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.texts: list[str] = []
        self.where: dict[str, str] = {}

    def add(self, reason: str, n: int) -> None:
        """Add ``n`` values excluded or marked for ``reason`` (a key of REASONS)."""
        if reason not in REASONS:
            raise ValueError(
                f"Unknown reason {reason!r}. Reasons: {', '.join(REASONS)}."
            )
        if n:
            self.counts[reason] = self.counts.get(reason, 0) + int(n)

    def count(self, mask: ArrayLike, reason: str) -> int:
        """Add the number of True values in ``mask`` and return it."""
        n = int(np.count_nonzero(mask))
        self.add(reason, n)
        return n

    def set_where(self, reason: str, text: str) -> None:
        """Add detail to a reason's wording, e.g. ", shown at N = 100"."""
        if reason not in REASONS:
            raise ValueError(
                f"Unknown reason {reason!r}. Reasons: {', '.join(REASONS)}."
            )
        self.where[reason] = text

    def add_text(self, text: str) -> None:
        """Add a free-text line to the footnote, e.g. a note replacing the legend."""
        self.texts.append(text)

    def lines(self) -> list[str]:
        """Return the footnote lines, in the order of REASONS, then free text."""
        counts = [
            REASONS[reason].format(
                n=n, s="" if n == 1 else "s", where=self.where.get(reason, "")
            )
            for reason in REASONS
            if (n := self.counts.get(reason))
        ]
        return counts + self.texts

    def render(self, ax: Axes, offset: float = 0.0) -> Annotation | None:
        """Write the footnote to the right of the axes, below the legend.

        Also sets ``ax.ags_notes`` to the counts, so users and tests can read
        them. ``offset`` is extra space in points between the axes and the
        footnote, as for ``add_legend``. Returns the footnote, or None when
        there is nothing to note.
        """
        ax.ags_notes = dict(self.counts)
        lines = self.lines()
        if not lines:
            return None
        return ax.annotate(
            "\n".join(lines),
            xy=(1.02, 0.0),
            xycoords="axes fraction",
            xytext=(offset, 0.0),
            textcoords="offset points",
            ha="left",
            va="bottom",
            fontsize=FOOTNOTE_SIZE,
            color=FOOTNOTE_COLOR,
            annotation_clip=False,
        )


def _beyond(
    values: np.ndarray, limits: tuple[float, float] | None
) -> tuple[np.ndarray, np.ndarray]:
    """Return the values clipped to ``limits`` and the direction each was moved."""
    if limits is None:
        return values, np.zeros(values.shape)
    lo, hi = sorted(limits)
    direction = np.where(values > hi, 1.0, np.where(values < lo, -1.0, 0.0))
    return np.clip(values, lo, hi), direction


def edge_markers(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    limits: Mapping[str, tuple[float, float] | None],
    color: str,
    marker: str = "o",
) -> np.ndarray:
    """Draw values beyond fixed axis limits at the limit, with an outward arrow.

    Each such value becomes an open marker in the series color at the edge
    of the axes, with a short arrow pointing the way the true value lies.

    Parameters
    ----------
    ax
        The axes, with its limits and direction already set.
    x, y
        The values, in display units.
    limits
        ``{"x": (lo, hi), "y": (lo, hi)}``; an axis that is missing or None
        has no fixed limits.
    color, marker
        The series color and marker.

    Returns
    -------
    numpy.ndarray of bool
        True where a value was drawn at the edge. Draw the others normally,
        and count these with ``notes.count(mask, "beyond_limit")``.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x_edge, x_dir = _beyond(x, limits.get("x"))
    y_edge, y_dir = _beyond(y, limits.get("y"))
    mask = (x_dir != 0) | (y_dir != 0)
    if not mask.any():
        return mask
    # Arrows point the way the value lies on screen, so flip for inverted axes.
    x_dir = -x_dir if ax.xaxis_inverted() else x_dir
    y_dir = -y_dir if ax.yaxis_inverted() else y_dir
    ax.scatter(
        x_edge[mask],
        y_edge[mask],
        marker=marker,
        facecolors="none",
        edgecolors=color,
        clip_on=False,
        zorder=3,
    )
    for xi, yi, dx, dy in zip(
        x_edge[mask], y_edge[mask], x_dir[mask], y_dir[mask], strict=True
    ):
        ax.annotate(
            "",
            xy=(xi, yi),
            xytext=(dx * ARROW_LENGTH, dy * ARROW_LENGTH),
            textcoords="offset points",
            arrowprops={"arrowstyle": "<-", "color": color, "lw": 0.8, "shrinkB": 3},
            annotation_clip=False,
        )
    return mask
