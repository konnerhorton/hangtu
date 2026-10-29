"""User regions on the plasticity chart (P04 §8).

A region is a polygon in LL-PI space, such as a project's own soil group:
one row per vertex, in order, with rows sharing a ``label`` making one
polygon.
"""

from collections.abc import Mapping
from os import PathLike

import pandas as pd
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
from matplotlib.patches import Polygon

from hangtu import _polygons
from hangtu.plot import _layers

COLOR = "0.5"
FILL_ALPHA = 0.12
LINE_WIDTH = 1.0
LABEL_SIZE = 8
KIND = _polygons.TableKind(
    argument="regions",
    item="Region",
    axes=("liquid_limit", "plasticity_index"),
    numbers=" in percent",
    start='Start one with ht.template("plasticity_regions").',
)

#: One region: its label and its vertices as an (n, 2) array of LL, PI.
Region = _polygons.Polygon


def read_regions(regions: pd.DataFrame | str | PathLike[str]) -> list[Region]:
    """Read and check the regions table; return the regions in table order."""
    return _polygons.read_polygons(regions, KIND)


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
