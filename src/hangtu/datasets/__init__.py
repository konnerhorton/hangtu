"""Datasets: canonical tables joined for the plots (docs/data/datasets.md)."""

from hangtu.datasets._frame import locations
from hangtu.datasets._index import index_properties
from hangtu.datasets._lab import atterberg, grain_size, grain_size_summary
from hangtu.datasets._permeability import permeability
from hangtu.datasets._spt import spt
from hangtu.datasets._stratigraphy import stratigraphy

__all__ = [
    "atterberg",
    "grain_size",
    "grain_size_summary",
    "index_properties",
    "locations",
    "permeability",
    "spt",
    "stratigraphy",
]
