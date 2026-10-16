"""Envelopes on the grain size plot (P05 §8).

An envelope is a band of percent passing between a lower and an upper curve,
such as a filter or grout specification: one row per size, with rows sharing
a ``label`` making one band.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from os import PathLike

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
from matplotlib.patches import Patch

from hangtu import units as _units
from hangtu._data import rows_text
from hangtu.errors import ColumnError, HangtuError
from hangtu.plot import _layers
from hangtu.plot._overlays import overlay_units

FIELDS = ("label", "particle_size", "low", "high")
COLOR = "0.5"
FILL_ALPHA = 0.2
LINE_WIDTH = 0.8
_START = 'Start one with ht.template("envelopes").'


@dataclass(frozen=True)
class Envelope:
    """One band: its label, sizes in mm from the finest up, and the passing bounds."""

    label: str
    sizes: np.ndarray
    low: np.ndarray
    high: np.ndarray


def _read(envelopes: pd.DataFrame | str | PathLike[str]) -> pd.DataFrame:
    if isinstance(envelopes, pd.DataFrame):
        return envelopes
    if isinstance(envelopes, str | PathLike):
        return _units.read_csv(envelopes)
    raise HangtuError(
        "envelopes must be a DataFrame or the path of a CSV file, not "
        f"{type(envelopes).__name__}. {_START}"
    )


def _sizes_mm(table: pd.DataFrame, data_unit: str | None) -> np.ndarray:
    unit = overlay_units(table, "envelopes", {"particle_size": data_unit})
    if unit["particle_size"] is None:
        raise HangtuError(
            "The envelopes table has no units for particle_size, and neither "
            "does the plot data. Declare them: envelopes = "
            'ht.set_units(envelopes, {"particle_size": "mm"}).'
        )
    source = _units.parse_unit(unit["particle_size"], "particle_size")
    values = pd.to_numeric(table["particle_size"], errors="coerce").to_numpy(float)
    return _units.convert(values, source, "particle_size", _units.ureg.millimeter)


def _check(label: str, rows: pd.Index, sizes, low, high) -> None:
    def bad(problem: str, where: np.ndarray | None = None) -> HangtuError:
        at = rows if where is None else rows[where]
        return HangtuError(f"Envelope {label!r} {problem} (rows {rows_text(at)}).")

    if np.isnan(sizes).any() or np.isnan(low).any() or np.isnan(high).any():
        raise bad(
            "has a blank or non-numeric particle_size, low or high. Every row "
            "needs all three"
        )
    if (sizes <= 0).any():
        raise bad("has sizes of 0 or less; particle sizes are greater than 0")
    outside = (low < 0) | (high > 100)
    if outside.any():
        raise bad("has percent passing outside 0 to 100", outside)
    reversed_ = low > high
    if reversed_.any():
        raise bad("has low above high", reversed_)
    if len(sizes) < 2:
        raise bad("has one size; a band needs at least two")
    repeated = pd.Series(sizes).duplicated(keep=False).to_numpy()
    if repeated.any():
        raise bad("has the same particle size twice", repeated)


def read_envelopes(
    envelopes: pd.DataFrame | str | PathLike[str], data_unit: str | None
) -> list[Envelope]:
    """Read and check the envelopes table; return the bands in table order.

    ``particle_size`` units come from the table, else ``data_unit`` (the plot
    data's) with a warning.
    """
    table = _read(envelopes)
    missing = [field for field in FIELDS if field not in table.columns]
    if missing:
        raise ColumnError(
            f"The envelopes table has no {', '.join(map(repr, missing))} column. It "
            "needs label, particle_size, low and high: one row per size, with low "
            f"and high the percent passing at that size. {_START}"
        )
    blank = table["label"].isna()
    if blank.any():
        raise HangtuError(
            f"Rows {rows_text(table.index[blank])} of the envelopes table have no "
            "label, so they can't be given to an envelope. Fill in the label of "
            "each row."
        )
    sizes = _sizes_mm(table, data_unit)
    bounds = table[["low", "high"]].apply(pd.to_numeric, errors="coerce")
    result = []
    for label, rows in table.groupby("label", sort=False).indices.items():
        band_sizes = sizes[rows]
        low = bounds["low"].to_numpy(float)[rows]
        high = bounds["high"].to_numpy(float)[rows]
        _check(str(label), table.index[rows], band_sizes, low, high)
        order = np.argsort(band_sizes, kind="stable")
        result.append(Envelope(str(label), band_sizes[order], low[order], high[order]))
    return result


def draw_envelopes(
    ax: Axes, envelopes: list[Envelope], colors: Mapping[str, str]
) -> list[Patch]:
    """Fill each band between its lower and upper curves; return legend handles."""
    handles = []
    for envelope in envelopes:
        color = colors[envelope.label]
        ax.fill_between(
            envelope.sizes,
            envelope.low,
            envelope.high,
            facecolor=to_rgba(color, FILL_ALPHA),
            edgecolor=color,
            linewidth=LINE_WIDTH,
            gid="envelope",
            zorder=_layers.ENVELOPES,
        )
        handles.append(
            Patch(
                facecolor=to_rgba(color, FILL_ALPHA),
                edgecolor=color,
                linewidth=LINE_WIDTH,
                label=envelope.label,
            )
        )
    return handles
