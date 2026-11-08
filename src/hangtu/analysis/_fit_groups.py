"""What the envelope fits share: groups, the pooling check and the lab's pairs.

``mohr_coulomb_fit()``, ``shear_box_fit()`` and ``hoek_brown_fit()`` group rows
the same way, refuse to pool unlike sources the same way and list the lab's
reported pairs beside the fit the same way (docs/analysis/strength.md §3).
"""

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import numeric_column
from hangtu.errors import HangtuError
from hangtu.stats._rows import breakdown

#: The columns that place a fitted point in the ground, kept with it when given
#: (docs/analysis/strength.md §3).
PLACE = ("depth", "elevation", "ground_level")


def _place_units(df: pd.DataFrame, units: Mapping[str, str] | None) -> dict[str, str]:
    """Return the unit of each ``PLACE`` column df has, where one is declared.

    A point's depth is kept as given, so its unit is recorded with the fit; a
    column with no declared unit is left out of the record, never guessed.
    """
    declared = {**_units.units_of(df), **(units or {})}
    return {
        column: declared[column]
        for column in PLACE
        if column in df.columns and column in declared
    }


def _names(value: str | Sequence[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def _cell(value: Any) -> Any:
    return None if pd.isna(value) else value


def _label(key: dict[str, Any]) -> str:
    return ", ".join(map(str, key.values())) or "All"


def _reported(
    df: pd.DataFrame,
    units: Mapping[str, str] | None,
    unit: str | None,
    cohesion_column: str,
    angle_column: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Return the lab's c in the fit's unit and φ in degrees, NaN where not given."""
    to = {cohesion_column: unit, angle_column: "deg"}
    quantity = {cohesion_column: "stress", angle_column: "angle"}
    result = []
    for column, target in to.items():
        if column not in df.columns or df[column].isna().all():
            result.append(np.full(len(df), np.nan))
            continue
        declared = _units.resolve_units(df, [column], units, analysis=True)[column]
        source = _units.parse_unit(declared, column)
        _units.check_dimension(source, quantity[column], column)
        result.append(
            _convert_reported(
                numeric_column(df, column),
                source,
                quantity[column],
                _units.parse_unit(target),
            )
        )
    return result[0], result[1]


def _convert_reported(
    values: np.ndarray, source: Any, quantity: str, target: Any
) -> np.ndarray:
    """Convert the lab's values, each to as many significant figures as it had.

    64 MPa is 9282.42 psi, which claims digits the lab didn't report; it
    converts to 9300 psi. Figures are counted from the value as read, so
    trailing zeros before the decimal point don't count (1200 has 2): a
    float can't say whether the lab meant them.
    """
    values = np.asarray(values, dtype=float)
    converted = np.asarray(_units.convert(values, source, quantity, target), float)
    return np.array(
        [
            _round_like(value, original)
            for value, original in zip(converted, values, strict=True)
        ],
        dtype=float,
    )


def _round_like(value: float, original: float) -> float:
    """Round ``value`` to the significant figures of ``original``."""
    if not np.isfinite(value) or not np.isfinite(original) or original == 0:
        return float(value)
    return float(f"{value:.{_significant_figures(original)}g}")


def _significant_figures(value: float) -> int:
    """Count a value's significant figures from its shortest decimal form."""
    text = np.format_float_positional(abs(value), trim="-")
    digits = text.replace(".", "").lstrip("0")
    if "." not in text:
        digits = digits.rstrip("0")
    return max(len(digits), 1)


def _check_sources(
    function: str,
    df: pd.DataFrame,
    key: dict[str, Any],
    rows: np.ndarray,
    checked: list[str],
    pooled: list[str],
    what: str = "",
) -> None:
    """Raise if a group's fitted rows mix the values of a ``checked`` column.

    ``what`` names the rows in the message (``" peak"``), when a group's rows
    are checked in parts.
    """
    lines, mixed = [], []
    for column in checked:
        if column in pooled or column not in df.columns:
            continue
        counts = breakdown(df.loc[rows, column])
        if len(counts) < 2:
            continue
        mixed.append(column)
        listed = [f"{value!r} ({count} rows)" for value, count in counts.items()]
        indent = " " * (len(column) + 4)
        lines.append(f"  {column}: " + f",\n{indent}".join(listed))
    if not mixed:
        return
    label = _label(key) if key else ""
    where = f" in group {label!r}" if label else ""
    raise HangtuError(
        f"{function} can't fit{what} rows from different sources together{where}:\n"
        + "\n".join(lines)
        + f"\nFit each with group_by={[*key, mixed[0]]!r}, filter the rows, "
        f"or pool them on purpose with pool={mixed!r}."
    )


def _pairs(
    reported: tuple[np.ndarray, np.ndarray] | None,
    fitted: np.ndarray,
    names: tuple[str, str] = ("cohesion", "friction_angle"),
) -> list[dict[str, Any]] | None:
    """Return the distinct pairs the lab reported for the fitted rows.

    ``names`` names the pair's values: (c, φ), or (σci, mi) for Hoek-Brown.
    """
    if reported is None:
        return None
    counts: dict[tuple[float, float], int] = {}
    for first, second in zip(reported[0][fitted], reported[1][fitted], strict=True):
        if np.isnan(first) and np.isnan(second):
            continue
        pair = (float(first), float(second))
        match = next((known for known in counts if _same(known, pair)), pair)
        counts[match] = counts.get(match, 0) + 1
    return [
        {names[0]: first, names[1]: second, "count": count}
        for (first, second), count in counts.items()
    ]


def _same(first: tuple[float, float], second: tuple[float, float]) -> bool:
    return all(
        (np.isnan(a) and np.isnan(b)) or a == b
        for a, b in zip(first, second, strict=True)
    )
