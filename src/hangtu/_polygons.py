"""Polygon tables: P04's user regions and P17's clogging zones.

A polygon table has one row per vertex, in order around the polygon, with
rows sharing a ``label`` making one polygon (closed automatically).
"""

from dataclasses import dataclass
from os import PathLike

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import rows_text
from hangtu.errors import ColumnError, HangtuError

#: A point this close to an edge counts as on it, as QC's tolerance.
SLACK = 1e-9


@dataclass(frozen=True)
class Polygon:
    """One polygon: its label and its vertices as an (n, 2) array."""

    label: str
    vertices: np.ndarray

    def centroid(self) -> np.ndarray:
        """Return the polygon's area centroid (its vertex mean if it has no area)."""
        x, y = self.vertices[:, 0], self.vertices[:, 1]
        cross = x * np.roll(y, -1) - np.roll(x, -1) * y
        area = cross.sum() / 2
        if abs(area) < 1e-12:
            return self.vertices.mean(axis=0)
        return np.array(
            [
                ((x + np.roll(x, -1)) * cross).sum() / (6 * area),
                ((y + np.roll(y, -1)) * cross).sum() / (6 * area),
            ]
        )


@dataclass(frozen=True)
class TableKind:
    """What a polygon table is called in messages, and its axis columns.

    ``argument`` names the table ("regions"), ``item`` one polygon
    ("Region"), ``numbers`` how vertices are given (" in percent") and
    ``start`` how to start one.
    """

    argument: str
    item: str
    axes: tuple[str, str]
    numbers: str
    start: str


def _read(table: pd.DataFrame | str | PathLike[str], kind: TableKind) -> pd.DataFrame:
    if isinstance(table, pd.DataFrame):
        return table
    if isinstance(table, str | PathLike):
        return _units.read_csv(table)
    raise HangtuError(
        f"{kind.argument} must be a DataFrame or the path of a CSV file, not "
        f"{type(table).__name__}. {kind.start}"
    )


def read_polygons(
    table: pd.DataFrame | str | PathLike[str], kind: TableKind
) -> list[Polygon]:
    """Read and check a polygon table; return the polygons in table order."""
    table = _read(table, kind)
    x, y = kind.axes
    missing = [field for field in ("label", x, y) if field not in table.columns]
    if missing:
        raise ColumnError(
            f"The {kind.argument} table has no {', '.join(map(repr, missing))} "
            f"column. It needs label, {x} and {y}: one row per vertex, in order "
            f"around the polygon. {kind.start}"
        )
    blank = table["label"].isna()
    if blank.any():
        raise HangtuError(
            f"Rows {rows_text(table.index[blank])} of the {kind.argument} table "
            f"have no label, so they can't be given to a {kind.item.lower()}. "
            "Fill in the label of each vertex."
        )
    result = []
    for label, rows in table.groupby("label", sort=False):
        vertices = rows[[x, y]].apply(pd.to_numeric, errors="coerce")
        if vertices.isna().any(axis=None):
            raise HangtuError(
                f"{kind.item} {label!r} has a blank or non-numeric {x} or {y} "
                f"in rows {rows_text(rows.index)}. Every vertex needs both, as "
                f"numbers{kind.numbers}."
            )
        if len(rows) < 3:
            raise HangtuError(
                f"{kind.item} {label!r} has {len(rows)} vertices; a polygon needs "
                "at least three. Add rows with its label, in order around the "
                "polygon."
            )
        result.append(Polygon(str(label), vertices.to_numpy(dtype=float)))
    return result


def contains(
    vertices: np.ndarray, points: np.ndarray, tolerance: float = SLACK
) -> np.ndarray:
    """Return True for each point inside the polygon or on its edge.

    Even-odd ray casting, so any simple polygon works, convex or not. A
    point within ``tolerance`` of an edge is inside. NaN points are outside.
    """
    points = np.asarray(points, dtype=float).reshape(-1, 2)
    px, py = points[:, 0], points[:, 1]
    inside = np.zeros(len(points), dtype=bool)
    on_edge = np.zeros(len(points), dtype=bool)
    with np.errstate(invalid="ignore", divide="ignore"):
        for (x0, y0), (x1, y1) in zip(
            vertices, np.roll(vertices, -1, axis=0), strict=True
        ):
            dx, dy = x1 - x0, y1 - y0
            length = dx * dx + dy * dy
            if length == 0:
                t = np.zeros(len(points))
            else:
                t = np.clip(((px - x0) * dx + (py - y0) * dy) / length, 0.0, 1.0)
            distance = np.hypot(px - (x0 + t * dx), py - (y0 + t * dy))
            on_edge |= distance <= tolerance
            crosses = (y0 > py) != (y1 > py)
            inside ^= crosses & (px < x0 + (py - y0) * dx / dy)
    return inside | on_edge
