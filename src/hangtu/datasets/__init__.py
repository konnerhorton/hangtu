"""Datasets: canonical tables joined for the plots (docs/data/datasets.md)."""

from hangtu.datasets._frame import locations
from hangtu.datasets._lab import atterberg, grain_size
from hangtu.datasets._spt import spt

__all__ = ["atterberg", "grain_size", "locations", "spt"]
