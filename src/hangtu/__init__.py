"""Plots, analyses and data tools for geotechnical engineers."""

from importlib.metadata import version

from hangtu import analysis, plot
from hangtu._settings import settings
from hangtu.errors import AgsFileError, ColumnError, HangtuError, HangtuHint, UnitsError
from hangtu.project import Project
from hangtu.registry import columns, template
from hangtu.sheet import Sheet
from hangtu.units import (
    add_unit_alias,
    define_unit,
    read_csv,
    set_units,
    units_of,
)

__version__ = version("hangtu")

__all__ = [
    "AgsFileError",
    "ColumnError",
    "HangtuError",
    "HangtuHint",
    "Project",
    "Sheet",
    "UnitsError",
    "add_unit_alias",
    "analysis",
    "columns",
    "define_unit",
    "plot",
    "read_csv",
    "set_units",
    "settings",
    "template",
    "units_of",
]
