"""Plots, analyses and data tools for geotechnical engineers."""

from importlib.metadata import version

from ags_kit._settings import settings
from ags_kit.errors import AgsKitError, AgsKitHint, ColumnError, UnitsError
from ags_kit.registry import columns, template
from ags_kit.units import add_unit_alias, define_unit

__version__ = version("ags-kit")

__all__ = [
    "AgsKitError",
    "AgsKitHint",
    "ColumnError",
    "UnitsError",
    "add_unit_alias",
    "columns",
    "define_unit",
    "settings",
    "template",
]
