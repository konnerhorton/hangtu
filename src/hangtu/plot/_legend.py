"""Legend layout (docs/plots/P00-framework.md §11)."""

import math
from collections.abc import Sequence
from typing import Literal

from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.legend import Legend
from matplotlib.transforms import offset_copy

from hangtu.plot._notes import Notes

MAX_ROWS = 12
MAX_ENTRIES = 30
BOTTOM_COLUMNS = 4  # legend columns below the axes
#: Points from the bottom of the axes to below the tick labels and the x label.
BELOW_X_LABEL = 32.0


def add_legend(
    ax: Axes,
    sections: Sequence[Sequence[Artist]],
    notes: Notes,
    offset: float = 0.0,
    where: Literal["right", "bottom"] = "right",
) -> Legend | None:
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
        Extra space in points between the axes and the legend, e.g. for a
        secondary axis on the right.
    where
        ``"right"`` (the default), or ``"bottom"``: centered under the x
        label in up to four columns, for plots whose width is precious (P05).

    Returns
    -------
    The legend, or None when there are no entries or too many.
    """
    handles = [handle for section in sections for handle in section]
    if not handles:
        return None
    if len(handles) > MAX_ENTRIES:
        units = len(sections[0])
        notes.add_text(
            f"{units} geology units: see ht.plot.legend_handles()"
            if units
            else f"{len(handles)} legend entries not shown"
        )
        return None
    if where == "bottom":
        return ax.legend(
            handles=handles,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.0),
            bbox_transform=offset_copy(
                ax.transAxes, ax.figure, y=-BELOW_X_LABEL - offset, units="points"
            ),
            borderaxespad=0.0,
            frameon=False,
            fontsize=8,
            ncols=min(len(handles), BOTTOM_COLUMNS),
        )
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
