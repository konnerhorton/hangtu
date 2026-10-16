"""User regions on the plasticity chart (P04 §8).

A region is a polygon in LL-PI space, such as a project's own soil group:
one row per vertex, in order, with rows sharing a ``label`` making one
polygon.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from os import PathLike

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
from matplotlib.patches import Polygon

from hangtu import units as _units
from hangtu._data import rows_text
from hangtu.errors import ColumnError, HangtuError
from hangtu.plot import _layers

FIELDS = ("label", "liquid_limit", "plasticity_index")
COLOR = "0.5"
FILL_ALPHA = 0.12
LINE_WIDTH = 1.0
LABEL_SIZE = 8
_START = 'Start one with ht.template("plasticity_regions").'


@dataclass(frozen=True)
class Region:
    """One polygon: its label and its vertices as an (n, 2) array of LL, PI."""

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


def _read(regions: pd.DataFrame | str | PathLike[str]) -> pd.DataFrame:
    if isinstance(regions, pd.DataFrame):
        return regions
    if isinstance(regions, str | PathLike):
        return _units.read_csv(regions)
    raise HangtuError(
        "regions must be a DataFrame or the path of a CSV file, not "
        f"{type(regions).__name__}. {_START}"
    )


def read_regions(regions: pd.DataFrame | str | PathLike[str]) -> list[Region]:
    """Read and check the regions table; return the regions in table order."""
    table = _read(regions)
    missing = [field for field in FIELDS if field not in table.columns]
    if missing:
        raise ColumnError(
            f"The regions table has no {', '.join(map(repr, missing))} column. It "
            "needs label, liquid_limit and plasticity_index: one row per vertex, "
            f"in order around the polygon. {_START}"
        )
    blank = table["label"].isna()
    if blank.any():
        raise HangtuError(
            f"Rows {rows_text(table.index[blank])} of the regions table have no "
            "label, so they can't be given to a region. Fill in the label of "
            "each vertex."
        )
    result = []
    for label, rows in table.groupby("label", sort=False):
        vertices = rows[["liquid_limit", "plasticity_index"]].apply(
            pd.to_numeric, errors="coerce"
        )
        if vertices.isna().any(axis=None):
            raise HangtuError(
                f"Region {label!r} has a blank or non-numeric liquid_limit or "
                f"plasticity_index in rows {rows_text(rows.index)}. Every vertex "
                "needs both, as numbers in percent."
            )
        if len(rows) < 3:
            raise HangtuError(
                f"Region {label!r} has {len(rows)} vertices; a polygon needs at "
                "least three. Add rows with its label, in order around the "
                "polygon."
            )
        result.append(Region(str(label), vertices.to_numpy(dtype=float)))
    return result


def draw_regions(ax: Axes, regions: list[Region], colors: Mapping[str, str]) -> None:
    """Draw each region as an outlined, lightly filled polygon with its label."""
    for region in regions:
        color = colors[region.label]
        ax.add_patch(
            Polygon(
                region.vertices,
                closed=True,
                facecolor=to_rgba(color, FILL_ALPHA),
                edgecolor=color,
                linewidth=LINE_WIDTH,
                gid="region",
                zorder=_layers.REGIONS,
            )
        )
        ax.text(
            *region.centroid(),
            region.label,
            ha="center",
            va="center",
            fontsize=LABEL_SIZE,
            color=color,
            gid="region_label",
            clip_on=True,
            zorder=_layers.ZONE_LABELS,
        )
