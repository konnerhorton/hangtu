"""Plots, analyses and data tools for geotechnical engineers."""

from importlib.metadata import version

from hangtu import analysis, examples, plot, stats
from hangtu._judgments import Judgments, judgments
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
from hangtu.vertical_datums import add_vertical_datum

__version__ = version("hangtu")

__all__ = [
    "AgsFileError",
    "ColumnError",
    "HangtuError",
    "HangtuHint",
    "Judgments",
    "Project",
    "Sheet",
    "UnitsError",
    "add_unit_alias",
    "add_vertical_datum",
    "analysis",
    "columns",
    "define_unit",
    "examples",
    "judgments",
    "plot",
    "read_csv",
    "set_units",
    "settings",
    "stats",
    "template",
    "units_of",
]
