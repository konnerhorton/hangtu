"""Exclusion notes and out-of-range markers (docs/plots/P00-framework.md §9).

Plots never drop data silently: every value that isn't drawn normally is
counted here and listed in a footnote.
"""

from collections.abc import Mapping
from typing import Any, Literal

import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.markers import MarkerStyle
from matplotlib.text import Annotation
from matplotlib.transforms import Transform
from numpy.typing import ArrayLike

# Footnote wording by reason. {n} is the count, {s} the plural ending, and
# {where} optional detail a plot sets with Notes.set_where (P02: the cap).
REASONS = {
    "nan": "{n} blank value{s} not shown",
    # A correlation's rows with no estimate, by correlation_note (P01 §11).
    "correlation_not_for_this_soil": "{n} not for this soil, no estimate",
    "correlation_soil_type_unknown": "{n} with soil type unknown, no estimate",
    "correlation_input_blank": "{n} with a blank input, no estimate",
    "correlation_refusal": "{n} refusal{s}, no estimate",
    "correlation_below_range": "{n} below range, no estimate",
    "correlation_above_range": "{n} above range, no estimate",
    # A value reported as a range, <value>_lower and <value>_upper (P01 §7).
    "value_range": "{n} shown as a range",
    "short_curve": "{n} curve{s} with fewer than two points not shown",
    "d_value_unreached": "{n} D-value{s} not reached{where}",
    "log_nonpositive": "{n} value{s} ≤ 0 not shown on log axis",
    "beyond_limit": "{n} value{s} beyond axis limit, shown at the edge",
    "less_than": "{n} value{s} reported as less than (<)",
    "greater_than": "{n} value{s} reported as greater than (>)",
    "refusal": "{n} refusal{s}{where}",
    "refusal_excluded": "{n} refusal{s} not shown",
    "no_energy_ratio": "{n} test{s} without an energy ratio not shown",
    "non_plastic": "{n} non-plastic (NP) value{s}{where}",
    "non_plastic_drawn": (
        "{n} non-plastic (NP) specimen{s}, shown open at their water content"
    ),
    "non_plastic_excluded": "{n} non-plastic (NP) specimen{s} not shown",
    "assumed_excluded": "{n} assumed value{s} shown, not in the summaries",
    "zero_plasticity": "{n} specimen{s} with PI = 0 not shown",
    "no_water_content": "{n} specimen{s} without water content not shown",
    "text_value": "{n} text value{s}{where}",
    "one_limit": "{n} specimen{s} with one limit, shown as a single tick",
    "limits_inverted": "{n} specimen{s} with PL above LL, limits not shown",
}

FOOTNOTE_SIZE = 7
FOOTNOTE_COLOR = "0.4"
#: Points from the bottom of the axes to below the tick labels and the x label,
#: at least; below_x_label() measures the axes and may give more.
BELOW_X_LABEL = 32.0
GAP = 4.0  # points between the x label and what goes below it

Placement = Literal["right", "bottom", "inside"] | None


def renderer(figure: Figure) -> Any:
    """Return the figure's renderer, to measure text before the figure is drawn."""
    canvas = figure.canvas
    if hasattr(canvas, "get_renderer"):
        return canvas.get_renderer()
    return figure._get_renderer()


def below_x_label(ax: Axes) -> float:
    """Return the points from the bottom of the axes to below its x label.

    Measured from the tick labels and x label (several lines in P03), plus a
    small gap; at least ``BELOW_X_LABEL``. The depth doesn't change when the
    layout engine resizes the axes.
    """
    box = ax.xaxis.get_tightbbox(renderer(ax.figure))
    depth = 0.0 if box is None else (ax.bbox.y0 - box.y0) * 72 / ax.figure.dpi
    return max(BELOW_X_LABEL, depth + GAP)


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

    def render(
        self,
        ax: Axes,
        offset: float = 0.0,
        where: Placement = "right",
        below: Artist | None = None,
    ) -> Annotation | None:
        """Write the footnote where the legend's placement leaves room.

        ``where`` is the placement ``add_legend`` chose. ``"right"``: to the
        right of the axes, below the legend. ``"bottom"``: under the axes,
        centered below ``below`` (the bottom legend) or, without one,
        ``offset`` points under the axes. ``"inside"`` or None (no legend):
        centered below the x label.

        Also sets ``ax.ags_notes`` to the counts, so users and tests can read
        them. ``offset`` is extra space in points between the axes and the
        footnote, as for ``add_legend``. Returns the footnote, or None when
        there is nothing to note.
        """
        ax.ags_notes = dict(self.counts)
        lines = self.lines()
        if not lines:
            return None
        if where in ("inside", None):
            where, offset, below = "bottom", below_x_label(ax), None
        if where == "bottom":
            anchor = {"xy": (0.5, 0.0), "xytext": (0.0, -4.0)}
            if below is None:
                anchor["xycoords"] = "axes fraction"
                anchor["xytext"] = (0.0, -offset)
            else:
                anchor["xycoords"] = below
            return ax.annotate(
                "\n".join(lines),
                textcoords="offset points",
                ha="center",
                va="top",
                fontsize=FOOTNOTE_SIZE,
                color=FOOTNOTE_COLOR,
                annotation_clip=False,
                **anchor,
            )
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
    transform: Transform | None = None,
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
    transform
        The coordinates of ``x`` and ``y``; data coordinates by default. P01
        text values use x in axes coordinates and y in data.

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
    # A line marker such as "|" has no face, so it takes the color itself.
    if MarkerStyle(marker).is_filled():
        colors = {"facecolors": "none", "edgecolors": color}
    else:
        colors = {"color": color}
    ax.scatter(
        x_edge[mask],
        y_edge[mask],
        marker=marker,
        **colors,
        clip_on=False,
        zorder=3,
        transform=ax.transData if transform is None else transform,
    )
    for xi, yi, dx, dy in zip(
        x_edge[mask], y_edge[mask], x_dir[mask], y_dir[mask], strict=True
    ):
        ax.annotate(
            "",
            xy=(xi, yi),
            xycoords="data" if transform is None else transform,
            xytext=(dx * ARROW_LENGTH, dy * ARROW_LENGTH),
            textcoords="offset points",
            arrowprops={"arrowstyle": "<-", "color": color, "lw": 0.8, "shrinkB": 3},
            annotation_clip=False,
        )
    return mask
