"""Legend layout (docs/plots/P00-framework.md §11)."""

import math
from collections.abc import Sequence
from typing import Literal, NamedTuple

from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.legend import Legend
from matplotlib.transforms import offset_copy

from hangtu.plot._notes import BELOW_X_LABEL, Notes, Placement, below_x_label

__all__ = ["BELOW_X_LABEL", "Placed", "add_legend"]

MAX_ROWS = 12
MAX_ENTRIES = 30
BOTTOM_COLUMNS = 4  # legend columns below the axes

Where = Literal["bottom", "right"]


class Placed(NamedTuple):
    """The legend ``add_legend`` drew, and where; None for both when none."""

    legend: Legend | None
    where: Placement


def add_legend(
    ax: Axes,
    sections: Sequence[Sequence[Artist]],
    notes: Notes,
    offset: float = 0.0,
    where: Where = "right",
) -> Placed:
    """Add the legend outside the axes, on the right or below the x label.

    Parameters
    ----------
    ax
        The axes.
    sections
        Labeled artists in legend order: geology units (colors), then marker
        groups, then special markers such as qualifiers and edge markers.
    notes
        The plot's notes. With more than 30 entries the legend is left out
        and a note points to ``ht.plot.legend_handles()`` instead.
    offset
        Extra space in points between the axes and a ``"right"`` legend, e.g.
        for a secondary axis on the right.
    where
        ``"right"`` (the default): outside on the right. ``"bottom"``:
        centered under the x label in up to four columns, for plots whose
        width is precious (P05).

    Returns
    -------
    The legend and the placement chosen, both None when there are no
    entries or too many. Pass the placement to ``Notes.render``.
    """
    handles = [handle for section in sections for handle in section]
    if not handles:
        return Placed(None, None)
    if len(handles) > MAX_ENTRIES:
        units = len(sections[0])
        notes.add_text(
            f"{units} geology units: see ht.plot.legend_handles()"
            if units
            else f"{len(handles)} legend entries not shown"
        )
        return Placed(None, None)
    if where == "bottom":
        return Placed(_bottom(ax, handles, offset), "bottom")
    return Placed(_right(ax, handles, offset), "right")


def _right(ax: Axes, handles: list[Artist], offset: float) -> Legend:
    return ax.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        bbox_transform=offset_copy(ax.transAxes, ax.figure, x=offset, units="points"),
        borderaxespad=0.0,
        frameon=False,
        fontsize=8,
        ncols=math.ceil(len(handles) / MAX_ROWS),
    )


def _bottom(ax: Axes, handles: list[Artist], offset: float) -> Legend:
    return ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.0),
        bbox_transform=offset_copy(
            ax.transAxes, ax.figure, y=-below_x_label(ax) - offset, units="points"
        ),
        borderaxespad=0.0,
        frameon=False,
        fontsize=8,
        ncols=min(len(handles), BOTTOM_COLUMNS),
    )
