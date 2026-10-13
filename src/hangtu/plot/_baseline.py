"""The baseline table: a report's range per geology unit (P07 §8).

It is read, checked and converted here, so the single panel and the grid
treat it the same way.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from os import PathLike
from typing import Any

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.plot._overlays import ValueScale
from hangtu.registry import column_info

RANGE_FIELDS = ("low", "central", "high")


@dataclass(frozen=True)
class Baseline:
    """The baseline rows for one property, in display units.

    ``low`` and ``high`` are NaN where a row has no bar, ``central`` where it
    has no central value. ``source`` is the table's only source, if it has one.
    """

    units: list[Any]
    low: np.ndarray
    central: np.ndarray
    high: np.ndarray
    source: str | None

    def values(self) -> np.ndarray:
        """Return every finite range value, for the axis limits."""
        every = np.concatenate([self.low, self.central, self.high])
        return every[np.isfinite(every)]


def _read(baseline: pd.DataFrame | str | PathLike[str]) -> pd.DataFrame:
    if isinstance(baseline, pd.DataFrame):
        return baseline
    if isinstance(baseline, str | PathLike):
        return _units.read_csv(baseline)
    raise HangtuError(
        "baseline must be a DataFrame or the path of a CSV file, not "
        f'{type(baseline).__name__}. Start one with ht.template("baseline").'
    )


def _check_fields(table: pd.DataFrame) -> None:
    columns = set(table.columns)
    if "geology_unit" not in columns or not (
        {"low", "high"} <= columns or "central" in columns
    ):
        raise ColumnError(
            "The baseline table needs 'geology_unit' plus 'low' and 'high' "
            "(the report's range), 'central', or all three. Its columns are "
            f"{', '.join(map(str, table.columns)) or 'none'}. Start one with "
            'ht.template("baseline").'
        )


def check_baseline_units(
    baseline_units: Mapping[str, str] | None,
    properties: set[str],
    quantities: Mapping[str, str | None],
) -> None:
    """Check ``baseline_units`` keys are properties and their units fit them."""
    if baseline_units is None:
        return
    if not isinstance(baseline_units, Mapping):
        raise HangtuError(
            "baseline_units must be a dict of {property: unit}, not "
            f'{baseline_units!r}. Example: baseline_units={{"bulk_unit_weight": '
            '"kN/m3"}'
        )
    unknown = [key for key in baseline_units if key not in properties]
    if unknown:
        raise HangtuError(
            f"baseline_units names {unknown}, which isn't a property in the "
            f"baseline table or the plot. Properties: {', '.join(sorted(properties))}."
        )
    for key, text in baseline_units.items():
        unit = _units.parse_unit(text, key)
        quantity = quantities.get(key)
        if quantity is not None:
            _units.check_dimension(unit, quantity, key)


def _range_units(
    table: pd.DataFrame,
    value: str,
    baseline_units: Mapping[str, str] | None,
    scale: ValueScale,
) -> dict[str, str | None]:
    """Return the unit of ``low``, ``central`` and ``high`` for ``value`` (P07 §8).

    ``baseline_units``, then the table's declared units, then the value
    column's units with a warning.
    """
    if baseline_units and value in baseline_units:
        return dict.fromkeys(RANGE_FIELDS, baseline_units[value])
    declared = _units.units_of(table)
    fields = [field for field in RANGE_FIELDS if field in table.columns]
    missing = [field for field in fields if field not in declared]
    if missing and scale.unit is not None:
        warn(
            f"The baseline table has no units for {value}, so its ranges are taken "
            f"to be in the plot data's units ({scale.unit}). Declare them to "
            f'silence this: baseline_units={{"{value}": "{scale.unit}"}}, or '
            f"baseline = ht.set_units(baseline, "
            + "{"
            + ", ".join(f'"{field}": "{scale.unit}"' for field in missing)
            + "})."
        )
    return {field: declared.get(field, scale.unit) for field in RANGE_FIELDS}


def read_baseline(
    baseline: pd.DataFrame | str | PathLike[str],
    value: str,
    scale: ValueScale,
    baseline_units: Mapping[str, str] | None = None,
) -> Baseline:
    """Return the baseline rows for ``value``, checked and in display units.

    Rows that can't be drawn are left out with a warning naming them;
    two rows for one unit are an error (P07 §8).
    """
    table = _read(baseline)
    _check_fields(table)
    properties = {value}
    if "property" in table.columns:
        properties |= set(table["property"].dropna().astype(str))
    quantities = {
        name: (info or {}).get("quantity")
        for name in properties
        if (info := column_info(name)) is not None
    }
    quantities[value] = scale.quantity
    check_baseline_units(baseline_units, properties, quantities)
    if "property" in table.columns:
        table = table[table["property"] == value]
    units = _range_units(table, value, baseline_units, scale)
    converted = {}
    for field in RANGE_FIELDS:
        raw = (
            numeric_column(table, field)
            if field in table.columns
            else np.full(len(table), np.nan)
        )
        converted[field] = scale.to_display(raw, units[field])
    low, central, high = (converted[field] for field in RANGE_FIELDS)

    unit_names = table["geology_unit"].to_numpy(dtype=object)
    blank = pd.isna(unit_names)
    bar = np.isfinite(low) & np.isfinite(high)
    half = np.isfinite(low) != np.isfinite(high)
    swapped = bar & (low > high)
    empty = ~blank & ~(bar & ~swapped) & ~np.isfinite(central)
    for mask, problem in (
        (blank, "have no geology_unit, so they aren't drawn"),
        (swapped, "have low above high, so their bars aren't drawn"),
        (half & ~blank, "give only one end of the range, so their bars aren't drawn"),
        (empty & ~swapped & ~half, "have no range or central value to draw"),
    ):
        if mask.any():
            warn(f"Baseline rows {rows_text(table.index[mask])} {problem}.")
    bar &= ~swapped
    keep = ~blank & (bar | np.isfinite(central))

    names = pd.Series(unit_names[keep], index=table.index[keep])
    repeated = names.duplicated(keep=False)
    if repeated.any():
        raise HangtuError(
            f"The baseline table has more than one row for {value} in geology units "
            f"{', '.join(map(str, dict.fromkeys(names[repeated])))} (rows "
            f"{rows_text(names.index[repeated])}). Keep one row per unit and property."
        )

    source = None
    if "source" in table.columns:
        sources = table["source"][keep].dropna().unique()
        source = str(sources[0]) if len(sources) == 1 else None
    return Baseline(
        units=list(names),
        low=np.where(bar, low, np.nan)[keep],
        central=central[keep],
        high=np.where(bar, high, np.nan)[keep],
        source=source,
    )


def legend_text(baseline_label: str | None, baselines: list[Baseline]) -> str:
    """Return the baseline's legend text: the label, the one source, or "Baseline"."""
    if baseline_label is not None:
        return str(baseline_label)
    sources = {baseline.source for baseline in baselines}
    if len(sources) == 1 and None not in sources:
        return str(sources.pop())
    return "Baseline"
