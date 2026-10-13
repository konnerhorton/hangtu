"""Value-axis helpers shared by the plots (P01, P02, P07).

Limits, labels, presets, unit colors and flagged values (qualifiers,
refusals) for the axis that carries the plotted property.
"""

import math
from collections.abc import Mapping
from numbers import Real
from typing import Any, NamedTuple

import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from hangtu import units as _units
from hangtu._data import rows_text
from hangtu.errors import ColumnError, HangtuError
from hangtu.plot._limits import log_limits, nice_limits
from hangtu.plot._notes import Notes
from hangtu.plot._palette import resolve_palette
from hangtu.plot._presets import Preset
from hangtu.registry import column_info

NEUTRAL = "0.3"  # points not colored by a group
CARET_SIZE = 6.0  # points
BLANK_GROUP = "(blank)"


class Flag(NamedTuple):
    """How a flagged value is drawn: in place of its marker, and counted."""

    marker: str
    size: float  # points
    text: str  # legend text, before the count
    reason: str  # notes reason (_notes.REASONS)


# Qualifier -> flag (P01 §3, §7).
QUALIFIERS = {
    "<": Flag("<", CARET_SIZE, "less than", "less_than"),
    ">": Flag(">", CARET_SIZE, "greater than", "greater_than"),
}


def check_limits(name: str, limits: Any, log: bool = False) -> tuple[float, float]:
    ok = (
        isinstance(limits, list | tuple)
        and len(limits) == 2
        and all(
            isinstance(v, Real) and not isinstance(v, bool) and math.isfinite(v)
            for v in limits
        )
        and limits[0] != limits[1]
    )
    if not ok:
        raise HangtuError(
            f"{name} must be (low, high), two different numbers in display units, "
            f"not {limits!r}. Example: {name}=(0, 50)"
        )
    lo, hi = sorted(float(v) for v in limits)
    if log and lo <= 0:
        raise HangtuError(
            f"{name}={limits!r} can't be used on a log axis, because the lower "
            f"limit must be greater than 0. Example: {name}=(1e-7, 1e-2)"
        )
    return lo, hi


def quantity_of(value: str, preset: Preset | None) -> str | None:
    info = column_info(value)
    registered = info.get("quantity") if info else None
    if preset is None:
        return registered
    if registered is not None and registered != preset.quantity:
        raise HangtuError(
            f"preset={preset.name!r} is for a {preset.quantity.replace('_', ' ')}, "
            f"but column {value!r} is a {registered.replace('_', ' ')}. "
            f"Use preset={value!r} if it exists, or leave preset out."
        )
    return preset.quantity


def axis_text(value: str, label: str | None, preset: Preset | None) -> str:
    if label is not None:
        return label
    if preset is not None:
        return preset.label
    info = column_info(value)
    return info["label"] if info and "label" in info else value


def start_at_zero(value: str, preset: Preset | None) -> bool:
    if preset is not None:
        return preset.start_at_zero
    info = column_info(value)
    return bool(info) and info.get("scale") == "ratio"


def typical_range(
    preset: Preset | None, x_unit: str | None, system: str
) -> tuple[float, float] | None:
    """Return the preset's typical range in display units, if it can be converted."""
    if preset is None:
        return None
    kind = _units.quantity_kind(preset.quantity)
    if kind["canonical"] is not None and x_unit is None:
        return None
    low, high = _units.to_display(
        preset.typical, kind["canonical"], preset.quantity, system
    )[0]
    return float(low), float(high)


def value_limits(
    x: np.ndarray,
    *,
    log: bool,
    xlim: tuple[float, float] | None,
    start_at_zero: bool,
    typical: tuple[float, float] | None,
) -> tuple[float, float]:
    if xlim is not None:
        return xlim
    if not x.size:
        if typical is not None:
            if log:
                return log_limits(*typical)
            return nice_limits(*typical, start_at_zero=start_at_zero)
        return (1.0, 100.0) if log else (0.0, 1.0)
    vmin, vmax = float(x.min()), float(x.max())
    if vmin == vmax and typical is not None:
        # A single value: the typical range, widened to include it (P01 §11).
        vmin, vmax = min(typical[0], vmin), max(typical[1], vmax)
    if log:
        return log_limits(vmin, vmax)
    return nice_limits(vmin, vmax, start_at_zero=start_at_zero)


def color_groups(
    df: pd.DataFrame, color_by: str | None, palette: Mapping[Any, Any] | None
) -> tuple[np.ndarray, dict[Any, Any]]:
    """Return each row's group, and ``{group: color}`` in legend order.

    Rows with a blank group are grouped as ``BLANK_GROUP`` in a neutral color.
    """
    if color_by is None or color_by not in df.columns:
        return np.full(len(df), None, dtype=object), {None: NEUTRAL}
    groups = df[color_by].to_numpy(dtype=object)
    blank = pd.isna(groups)
    colors = resolve_palette(groups[~blank], palette)
    groups = np.where(blank, BLANK_GROUP, groups)
    if blank.any():
        colors[BLANK_GROUP] = NEUTRAL
    return groups, colors


def qualifiers(df: pd.DataFrame) -> np.ndarray:
    """Return each row's qualifier: ``"<"``, ``">"`` or ``""``."""
    if "qualifier" not in df.columns:
        return np.full(len(df), "", dtype=object)
    qualifiers = df["qualifier"].fillna("").astype(str).str.strip()
    bad = ~qualifiers.isin(["", *QUALIFIERS])
    if bad.any():
        found = ", ".join(repr(text) for text in dict.fromkeys(qualifiers[bad]))
        raise ColumnError(
            f'Column \'qualifier\' must hold "<", ">" or nothing, but rows '
            f"{rows_text(df.index[bad])} hold {found}. Put the qualifier only in "
            "'qualifier' and the number in the value column."
        )
    return qualifiers.to_numpy(dtype=object)


def flag_handles(
    flags: np.ndarray, kinds: Mapping[str, Flag], notes: Notes
) -> list[Line2D]:
    """Count flagged values by kind and return their legend entries.

    ``flags`` holds each row's key into ``kinds``, or ``""`` for none.
    """
    handles = []
    for key, (marker, size, text, reason) in kinds.items():
        n = notes.count(flags == key, reason)
        if n:
            handles.append(legend_marker(marker, NEUTRAL, f"{text} ({n})", size))
    return handles


def qualifier_handles(qualifiers: np.ndarray, notes: Notes) -> list[Line2D]:
    """Count qualified values and return their legend entries."""
    return flag_handles(qualifiers, QUALIFIERS, notes)


def legend_marker(marker: str, color: Any, label: str, size: float) -> Line2D:
    return Line2D(
        [],
        [],
        marker=marker,
        markersize=size,
        color=color,
        linestyle="none",
        label=label,
    )
