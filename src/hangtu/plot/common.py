"""Helpers shared by every plot. Private API: tested, but free to change."""

from hangtu.plot._hints import hint_missing
from hangtu.plot._labels import axis_label
from hangtu.plot._legend import add_legend
from hangtu.plot._limits import (
    apply_vertical_axis,
    log_limits,
    nice_limits,
    nice_step,
    set_linear_axis,
    set_log_axis,
)
from hangtu.plot._notes import Notes, edge_markers
from hangtu.plot._palette import resolve_palette

__all__ = [
    "Notes",
    "add_legend",
    "apply_vertical_axis",
    "axis_label",
    "edge_markers",
    "hint_missing",
    "log_limits",
    "nice_limits",
    "nice_step",
    "resolve_palette",
    "set_linear_axis",
    "set_log_axis",
]
