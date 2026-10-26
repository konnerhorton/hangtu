"""Legend layout (docs/plots/P00-framework.md §11)."""

import math
import textwrap
from collections.abc import Collection, Sequence
from typing import Literal, NamedTuple

import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.legend import Legend
from matplotlib.path import Path
from matplotlib.transforms import Bbox, offset_copy

from hangtu.errors import HangtuError
from hangtu.plot import _layers
from hangtu.plot._notes import (
    BELOW_X_LABEL,
    Notes,
    Placement,
    below_x_label,
    renderer,
)

__all__ = ["BELOW_X_LABEL", "Placed", "add_legend", "check_legend"]

MAX_ROWS = 12
MAX_ENTRIES = 30
BOTTOM_COLUMNS = 4  # legend columns below the axes
#: Corners tried in order for a legend inside the axes; the first clear one wins.
CORNERS = ("upper right", "upper left", "lower right", "lower left")
CLEARANCE = 4.0  # points around an inside legend that must be clear of data
FRAME_ALPHA = 0.85  # an inside legend's white frame, so gridlines don't cross it
#: Characters per legend line; a longer entry wraps at spaces, never shortened.
WRAP = 28

Where = Literal["auto", "inside", "bottom", "right"]
WHERE = ("auto", "inside", "bottom", "right")


def check_legend(value: object) -> Where | None:
    """Return a plot's ``legend=`` as a placement, or None for no legend."""
    if value is True:
        return "auto"
    if value is False:
        return None
    if isinstance(value, str) and value in WHERE:
        return value  # type: ignore[return-value]
    raise HangtuError(
        f'legend= must be "auto", "inside", "bottom", "right", True or False, '
        f'not {value!r}. Example: legend="bottom" puts it below the x label.'
    )


class Placed(NamedTuple):
    """The legend ``add_legend`` drew, and where; None for both when none."""

    legend: Legend | None
    where: Placement


def add_legend(
    ax: Axes,
    sections: Sequence[Sequence[Artist]],
    notes: Notes,
    offset: float = 0.0,
    where: Where | None = "auto",
) -> Placed:
    """Add the legend inside the axes in a clear corner, or outside it.

    Parameters
    ----------
    ax
        The axes.
    sections
        Labeled artists in legend order: geology units (colors), then marker
        groups, then special markers such as qualifiers and edge markers.
    notes
        The plot's notes. With more than 30 entries the legend is left out
        and a note points to ``ht.plot.legend_handles()`` instead. For
        ``"auto"`` and ``"inside"`` the footnote is drawn for a moment, so the
        layout leaves room for it before the corners are measured.
    offset
        Extra space in points between the axes and a ``"right"`` legend, e.g.
        for a secondary axis on the right.
    where
        ``"auto"`` (the default): the first clear corner in ``CORNERS``, else
        below the x label. ``"inside"``: the first clear corner, else the one
        with the fewest obstacles. ``"right"``: outside on the right.
        ``"bottom"``: centered under the x label in up to four columns.
        None: no legend.

    Returns
    -------
    The legend and the placement chosen, both None when there are no
    entries or too many. Pass the placement to ``Notes.render``.
    """
    handles = [handle for section in sections for handle in section]
    if where is None or not handles:
        return Placed(None, None)
    if len(handles) > MAX_ENTRIES:
        units = len(sections[0])
        notes.add_text(
            f"{units} geology units: see ht.plot.legend_handles()"
            if units
            else f"{len(handles)} legend entries not shown"
        )
        return Placed(None, None)
    labels = [_wrap(handle.get_label()) for handle in handles]
    if where == "right":
        return Placed(_right(ax, handles, labels, offset), "right")
    if where == "bottom":
        return Placed(_bottom(ax, handles, labels), "bottom")
    # The footnote below the x label shortens the axes, so it takes its room
    # before the layout engine sets the axes' final size.
    footnote = notes.render(ax, where="inside")
    ax.figure.draw_without_rendering()
    legend = _inside(ax, handles, labels)
    counts = _corner_obstacles(ax, legend, exclude={footnote})
    if footnote is not None:
        footnote.remove()
    clear = [corner for corner, count in counts.items() if count == 0]
    if clear:
        legend.set_loc(clear[0])
        return Placed(legend, "inside")
    if where == "auto":
        legend.remove()
        return Placed(_bottom(ax, handles, labels), "bottom")
    legend.set_loc(min(counts, key=counts.__getitem__))
    return Placed(legend, "inside")


def _wrap(label: str) -> str:
    """Wrap a long entry at word boundaries onto as many lines as it needs."""
    if len(label) <= WRAP:
        return label
    return textwrap.fill(label, WRAP, break_long_words=False, break_on_hyphens=False)


def _right(ax: Axes, handles: list[Artist], labels: list[str], offset: float) -> Legend:
    return ax.legend(
        handles=handles,
        labels=labels,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        bbox_transform=offset_copy(ax.transAxes, ax.figure, x=offset, units="points"),
        borderaxespad=0.0,
        frameon=False,
        fontsize=8,
        ncols=math.ceil(len(handles) / MAX_ROWS),
    )


def _bottom(ax: Axes, handles: list[Artist], labels: list[str]) -> Legend:
    return ax.legend(
        handles=handles,
        labels=labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.0),
        bbox_transform=offset_copy(
            ax.transAxes, ax.figure, y=-below_x_label(ax), units="points"
        ),
        borderaxespad=0.0,
        frameon=False,
        fontsize=8,
        ncols=min(len(handles), BOTTOM_COLUMNS),
    )


def _inside(ax: Axes, handles: list[Artist], labels: list[str]) -> Legend:
    return ax.legend(
        handles=handles,
        labels=labels,
        loc=CORNERS[0],
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=FRAME_ALPHA,
        fontsize=8,
        ncols=math.ceil(len(handles) / MAX_ROWS),
    )


def _corner_obstacles(
    ax: Axes, legend: Legend, exclude: Collection[Artist | None] = ()
) -> dict[str, int]:
    """Count what each corner's legend box would cover, by corner, in order.

    The box is padded by ``CLEARANCE``. Obstacles are markers (padded by
    their radius), line segments crossing the box, data patches, and texts;
    artists below ``_layers.LINES`` (bands, regions, envelopes) don't count.
    """
    draw = renderer(ax.figure)
    pad = CLEARANCE * ax.figure.dpi / 72
    points, radii, lines, shapes, boxes = _obstacles(ax, draw, exclude)
    counts = {}
    for corner in CORNERS:
        legend.set_loc(corner)
        box = legend.get_window_extent(draw).padded(pad)
        near = (
            (points[:, 0] + radii >= box.x0)
            & (points[:, 0] - radii <= box.x1)
            & (points[:, 1] + radii >= box.y0)
            & (points[:, 1] - radii <= box.y1)
        )
        counts[corner] = (
            int(near.sum())
            + sum(line.intersects_bbox(box, filled=False) for line in lines)
            + sum(shape.intersects_bbox(box, filled=True) for shape in shapes)
            + sum(box.overlaps(other) for other in boxes)
        )
    return counts


def _obstacles(
    ax: Axes, draw: object, exclude: Collection[Artist | None]
) -> tuple[np.ndarray, np.ndarray, list[Path], list[Path], list[Bbox]]:
    """Return the data a legend mustn't cover, in display coordinates.

    Marker centers and radii, polylines, filled shapes, and text boxes.
    """
    to_pixels = ax.figure.dpi / 72
    points, radii, lines, shapes, boxes = [], [], [], [], []

    def counted(artist: Artist) -> bool:
        return (
            artist.get_visible()
            and artist not in exclude
            and artist.get_zorder() >= _layers.LINES
        )

    for line in ax.lines:
        if not counted(line):
            continue
        xy = line.get_transform().transform(line.get_xydata())
        if line.get_marker() not in (None, "None", "none", "", " "):
            finite = np.isfinite(xy).all(axis=1)
            points.append(xy[finite])
            radii.append(np.full(finite.sum(), line.get_markersize() / 2 * to_pixels))
        if line.get_linestyle() not in ("None", "none", "", " "):
            lines += _runs(xy)
    for collection in ax.collections:
        if not counted(collection):
            continue
        if isinstance(collection, PathCollection):
            offsets = np.ma.filled(
                np.ma.asarray(collection.get_offsets(), dtype=float), np.nan
            )
            xy = collection.get_offset_transform().transform(offsets)
            # Sizes are marker areas in points², cycled over the points.
            sizes = collection.get_sizes()
            diameters = np.resize(np.sqrt(sizes) if len(sizes) else [0.0], len(xy))
            finite = np.isfinite(xy).all(axis=1)
            points.append(xy[finite])
            radii.append(diameters[finite] / 2 * to_pixels)
        elif isinstance(collection, LineCollection):
            transform = collection.get_transform()
            for segment in collection.get_segments():
                lines += _runs(transform.transform(segment))
        else:
            transform = collection.get_transform()
            shapes += [path.transformed(transform) for path in collection.get_paths()]
    for patch in ax.patches:
        if not counted(patch):
            continue
        shape = patch.get_path().transformed(patch.get_transform())
        extent = shape.get_extents()
        if extent.width > 0 and extent.height > 0:
            shapes.append(shape)
    for text in ax.texts:
        if not text.get_visible() or text in exclude or not text.get_text().strip():
            continue
        extent = text.get_window_extent(draw)
        frame = text.get_bbox_patch()
        if frame is not None:
            extent = Bbox.union([extent, frame.get_window_extent(draw)])
        boxes.append(extent)
    return (
        np.concatenate(points) if points else np.empty((0, 2)),
        np.concatenate(radii) if radii else np.empty(0),
        lines,
        shapes,
        boxes,
    )


def _runs(xy: np.ndarray) -> list[Path]:
    """Split a polyline at non-finite points into paths of two or more points."""
    finite = np.isfinite(xy).all(axis=1)
    breaks = np.flatnonzero(np.diff(finite.astype(int)) != 0) + 1
    return [
        Path(run)
        for run, keep in zip(
            np.split(xy, breaks), np.split(finite, breaks), strict=True
        )
        if keep.all() and len(run) >= 2
    ]
