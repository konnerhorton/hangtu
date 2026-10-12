"""Geology unit colors (docs/plots/P00-framework.md §10).

A unit keeps the same color in every plot of the session.
"""

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import matplotlib as mpl
import pandas as pd
from matplotlib.colors import ListedColormap, is_color_like
from matplotlib.patches import Patch

from hangtu._settings import settings
from hangtu.errors import AgsKitError, warn

# tab20 comes in dark/light pairs; use the 10 dark shades first.
_TAB20 = list(mpl.colormaps["tab20"].colors)
AUTOMATIC = _TAB20[0::2] + _TAB20[1::2]

_assigned: dict[Any, Any] = {}


def reset_palette() -> None:
    """Forget the automatic colors given to geology units in this session."""
    _assigned.clear()


def _ordered(units: Iterable[Any], order: Sequence[Any] | None) -> list[Any]:
    unique = list(dict.fromkeys(unit for unit in units if not pd.isna(unit)))
    position = {unit: i for i, unit in enumerate(order or [])}
    known = sorted((u for u in unique if u in position), key=position.__getitem__)
    rest = sorted((u for u in unique if u not in position), key=str)
    return known + rest


def resolve_palette(
    units: Iterable[Any],
    palette: Mapping[Any, Any] | None = None,
    order: Sequence[Any] | None = None,
) -> dict[Any, Any]:
    """Return ``{unit: color}`` for ``units``, in stratigraphic or name order.

    Colors come from ``palette``, then ``ak.settings.palette``, then automatic
    colors from tab20. Automatic colors are remembered, so a unit keeps its
    color in later plots until ``ak.plot.reset_palette()``.

    Parameters
    ----------
    units
        Geology unit names; blanks are ignored.
    palette
        Colors given in the plot call.
    order
        Units in stratigraphic order. Units not in it follow, sorted by name.
    """
    palette = palette or {}
    bad = [unit for unit, color in palette.items() if not is_color_like(color)]
    if bad:
        raise AgsKitError(
            f"palette has colors matplotlib doesn't recognize for {bad}. "
            'Use a color name ("tan"), a hex string ("#d2b48c") or an RGB tuple.'
        )
    resolved = {}
    repeated = False
    for unit in _ordered(units, order):
        if unit in palette:
            resolved[unit] = palette[unit]
        elif unit in settings.palette:
            resolved[unit] = settings.palette[unit]
        else:
            if unit not in _assigned:
                repeated |= len(_assigned) >= len(AUTOMATIC)
                _assigned[unit] = AUTOMATIC[len(_assigned) % len(AUTOMATIC)]
            resolved[unit] = _assigned[unit]
    if repeated:
        warn(
            f"More than {len(AUTOMATIC)} geology units have automatic colors, so "
            "some colors repeat. Choose colors with "
            'ak.settings.palette = {"Alluvium": "tan", ...}.'
        )
    return resolved


def _known_units() -> list[Any]:
    units = list(dict.fromkeys([*settings.palette, *_assigned]))
    if not units:
        raise AgsKitError(
            "No geology units have colors yet. Pass the units, e.g. "
            'ak.plot.palette_cmap(["Alluvium", "Till"]).'
        )
    return units


def palette_cmap(units: Sequence[Any] | None = None) -> ListedColormap:
    """Return the geology unit colors as a colormap, one color per unit in order.

    Use it to color your own matplotlib plots consistently with hangtu's.
    Without ``units``, every unit colored so far in this session is included.
    """
    units = _known_units() if units is None else list(units)
    colors = resolve_palette(units, order=units)
    return ListedColormap([colors[unit] for unit in units], name="hangtu_geology")


def legend_handles(units: Sequence[Any] | None = None) -> list[Patch]:
    """Return legend patches for geology units, for a stand-alone legend.

    Examples
    --------
    >>> fig.legend(handles=ak.plot.legend_handles(), loc="outside right")
    """
    units = _known_units() if units is None else list(units)
    colors = resolve_palette(units, order=units)
    return [Patch(facecolor=colors[u], edgecolor="none", label=str(u)) for u in units]
