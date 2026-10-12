"""The vertical reference of a profile: depth or elevation (SPEC §8.1, P01 §6).

Overlays and the profile plots built on P01 take a ``Vertical`` so they draw in
the same reference and display units as the main data.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from ags_kit._settings import _display_units, settings
from ags_kit.errors import AgsKitError, ColumnError
from ags_kit.plot._data import numeric_column
from ags_kit.plot._labels import axis_label
from ags_kit.units import to_display

VS = ("depth", "elevation")
# Every length column a profile reads. They are converted together, so one
# with unknown units isn't mixed with converted ones.
LENGTH_COLUMNS = ("depth", "elevation", "ground_level", "depth_top", "depth_base")


@dataclass(frozen=True)
class Vertical:
    """How the main data are drawn vertically.

    Attributes
    ----------
    vs
        ``"depth"`` or ``"elevation"``.
    display_units
        ``"US"`` or ``"SI"``.
    unit
        The declared unit of the main data's vertical values, or None.
    unit_text
        The display unit text, e.g. ``"ft"``; None when units are unknown.
    unknown
        True when any length column has no units. Lengths are then drawn as
        given, unconverted, and labels say "(units unknown)".
    ground_level
        The ground level in display units when every row shares one, else None.
    """

    vs: Literal["depth", "elevation"]
    display_units: str
    unit: str | None
    unit_text: str | None
    unknown: bool
    ground_level: float | None

    def label(self) -> str:
        """Return the vertical axis label, with the datum on elevation labels only."""
        datum = settings.vertical_datum if self.vs == "elevation" else None
        return axis_label(self.vs.capitalize(), self.unit_text, datum, self.unknown)

    def to_display(self, values: ArrayLike, unit: str) -> np.ndarray:
        """Convert lengths in ``unit`` to the display units of the main data."""
        if self.unknown:
            return np.asarray(values, dtype=float)
        return to_display(values, unit, "length", self.display_units)[0]


def _columns_text(df: pd.DataFrame) -> str:
    return ", ".join(map(str, df.columns)) or "none"


def choose_vs(df: pd.DataFrame, vs: str | None) -> Literal["depth", "elevation"]:
    """Return the vertical reference to plot against.

    ``None`` picks elevation when there is an ``elevation`` column or
    ``depth`` plus ``ground_level``, and depth otherwise.
    """
    if vs is not None and vs not in VS:
        raise AgsKitError(f'vs must be "depth", "elevation" or None, not {vs!r}.')
    has = set(df.columns)
    if not has & set(VS):
        raise ColumnError(
            "The data need a 'depth' or an 'elevation' column to plot against. "
            "Add depths below ground level as 'depth', or elevations as "
            "'elevation' (or 'depth' plus 'ground_level', and elevations are "
            f"computed). Columns: {_columns_text(df)}."
        )
    can_elevation = "elevation" in has or {"depth", "ground_level"} <= has
    can_depth = "depth" in has or {"elevation", "ground_level"} <= has
    if vs is None:
        return "elevation" if can_elevation else "depth"
    if vs == "elevation" and not can_elevation:
        raise ColumnError(
            "vs='elevation' needs an 'elevation' column, or 'depth' plus "
            "'ground_level' to compute it (elevation = ground_level - depth). "
            "Add one of these, or plot with vs='depth'."
        )
    if vs == "depth" and not can_depth:
        raise ColumnError(
            "vs='depth' needs a 'depth' column, or 'elevation' plus "
            "'ground_level' to compute it (depth = ground_level - elevation). "
            "Add one of these, or plot with vs='elevation'."
        )
    return vs


def length_columns(df: pd.DataFrame) -> list[str]:
    """Return the length columns of ``df`` a profile reads, to resolve units for."""
    return [column for column in LENGTH_COLUMNS if column in df.columns]


def length_values(
    df: pd.DataFrame, units: Mapping[str, str | None], display_units: str
) -> tuple[dict[str, np.ndarray], bool]:
    """Return every length column in display units, and whether units are unknown.

    When any length column has no units, all are returned as given.
    """
    columns = length_columns(df)
    values = {column: numeric_column(df, column) for column in columns}
    unknown = any(units.get(column) is None for column in columns)
    if not unknown:
        values = {
            column: to_display(raw, units[column], "length", display_units)[0]
            for column, raw in values.items()
        }
    return values, unknown


def row_ground_levels(lengths: Mapping[str, np.ndarray]) -> np.ndarray | None:
    """Each row's ground level: ``ground_level``, or ``elevation + depth``."""
    if "ground_level" in lengths:
        return lengths["ground_level"]
    if "elevation" in lengths and "depth" in lengths:
        return lengths["elevation"] + lengths["depth"]
    return None


def single_ground_level(levels: np.ndarray | None) -> float | None:
    """Return the ground level all rows share, or None for several or none."""
    if levels is None:
        return None
    known = levels[np.isfinite(levels)]
    if not known.size:
        return None
    lo, hi = known.min(), known.max()
    if hi - lo > 1e-9 * max(1.0, abs(hi)):
        return None
    return float(known[0])


def vertical_values(
    df: pd.DataFrame,
    vs: Literal["depth", "elevation"],
    units: Mapping[str, str | None],
    display_units: str | None = None,
) -> tuple[np.ndarray, Vertical]:
    """Return the vertical position of each row in display units, and the reference.

    Elevation is ``ground_level - depth`` when there is no ``elevation``
    column (SPEC §8.1), and depth is ``ground_level - elevation`` when there
    is no ``depth`` column. Both are converted to display units before
    subtracting (P00 §4.3 #3).

    Parameters
    ----------
    df
        The main data; ``choose_vs`` has checked it has what ``vs`` needs.
    vs
        From ``choose_vs``.
    units
        Resolved units of ``length_columns(df)``.
    display_units
        ``"US"`` or ``"SI"``; defaults to the setting.
    """
    system = _display_units(display_units or settings.display_units)
    lengths, unknown = length_values(df, units, system)
    source = vs if vs in lengths else "depth" if vs == "elevation" else "elevation"
    values = lengths[vs] if vs in lengths else lengths["ground_level"] - lengths[source]
    unit = units.get(source)
    text = None if unknown else to_display([], unit, "length", system)[1]
    vertical = Vertical(
        vs=vs,
        display_units=system,
        unit=unit,
        unit_text=text,
        unknown=unknown,
        ground_level=single_ground_level(row_ground_levels(lengths)),
    )
    return values, vertical


def convert_vertical(
    values: ArrayLike,
    from_vs: Literal["depth", "elevation"],
    vertical: Vertical,
    overlay: str,
    columns: str,
) -> np.ndarray:
    """Draw overlay positions in ``vertical.vs``, converting through the ground level.

    ``values`` are in display units. Positions that already match ``vs`` are
    returned as given; the others become ``ground_level - values``, which needs
    one ground level for all the main data (P01 §8).

    Parameters
    ----------
    overlay, columns
        For the error message: the overlay argument (``"strata"``) and the
        columns that would match ``vs`` (``"elevation_top and elevation_base"``).
    """
    values = np.asarray(values, dtype=float)
    if from_vs == vertical.vs:
        return values
    if vertical.ground_level is None:
        raise AgsKitError(
            f"The {overlay} overlay is given in {from_vs} but the plot is against "
            f"{vertical.vs}, and the data don't share one ground level, so it can't "
            f"be converted. Give {columns} instead, or plot with vs={from_vs!r}."
        )
    return vertical.ground_level - values


def convert_pair(
    top: ArrayLike,
    base: ArrayLike,
    from_vs: Literal["depth", "elevation"],
    vertical: Vertical,
    overlay: str,
) -> tuple[np.ndarray, np.ndarray]:
    """``convert_vertical`` for a top and base pair, such as a stratum."""
    columns = f"{vertical.vs}_top and {vertical.vs}_base"
    return (
        convert_vertical(top, from_vs, vertical, overlay, columns),
        convert_vertical(base, from_vs, vertical, overlay, columns),
    )
