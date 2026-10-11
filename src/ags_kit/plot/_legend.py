"""Legend layout (docs/plots/P00-framework.md §11)."""

import math
from collections.abc import Sequence

from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.legend import Legend

from ags_kit.plot._notes import Notes

MAX_ROWS = 12
MAX_ENTRIES = 30


def add_legend(
    ax: Axes, sections: Sequence[Sequence[Artist]], notes: Notes
) -> Legend | None:
    """Add the legend outside the axes on the right.

    Parameters
    ----------
    ax
        The axes.
    sections
        Labeled artists in legend order: geology units (colors), then marker
        groups, then special markers such as qualifiers and edge markers.
    notes
        The plot's notes. With more than 30 entries the legend is left out
        and a note points to ``ak.plot.legend_handles()`` instead.

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
            f"{units} geology units: see ak.plot.legend_handles()"
            if units
            else f"{len(handles)} legend entries not shown"
        )
        return None
    return ax.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0.0,
        frameon=False,
        fontsize=8,
        ncols=math.ceil(len(handles) / MAX_ROWS),
    )
