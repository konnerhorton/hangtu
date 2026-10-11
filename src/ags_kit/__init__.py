"""Plots, analyses and data tools for geotechnical engineers."""

from importlib.metadata import version

from ags_kit._settings import settings
from ags_kit.errors import AgsKitError, AgsKitHint, ColumnError, UnitsError

__version__ = version("ags-kit")

__all__ = [
    "AgsKitError",
    "AgsKitHint",
    "ColumnError",
    "UnitsError",
    "settings",
]
