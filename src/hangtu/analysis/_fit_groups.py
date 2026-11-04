"""What the envelope fits share: groups, the pooling check and the lab's pairs.

``mohr_coulomb_fit()`` and ``shear_box_fit()`` group rows the same way, refuse
to pool unlike sources the same way and list the lab's reported pairs beside
the fit the same way (docs/work/m17b-shear-box-fit.md, Decision 14).
"""

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import numeric_column
from hangtu.errors import HangtuError
from hangtu.stats._rows import breakdown


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
            _units.convert(
                numeric_column(df, column),
                source,
                quantity[column],
                _units.parse_unit(target),
            )
        )
    return result[0], result[1]


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
    reported: tuple[np.ndarray, np.ndarray] | None, fitted: np.ndarray
) -> list[dict[str, Any]] | None:
    """Return the distinct (c, φ) the lab reported for the fitted rows."""
    if reported is None:
        return None
    counts: dict[tuple[float, float], int] = {}
    for cohesion, angle in zip(reported[0][fitted], reported[1][fitted], strict=True):
        if np.isnan(cohesion) and np.isnan(angle):
            continue
        pair = (float(cohesion), float(angle))
        match = next((known for known in counts if _same(known, pair)), pair)
        counts[match] = counts.get(match, 0) + 1
    return [
        {"cohesion": cohesion, "friction_angle": angle, "count": count}
        for (cohesion, angle), count in counts.items()
    ]


def _same(first: tuple[float, float], second: tuple[float, float]) -> bool:
    return all(
        (np.isnan(a) and np.isnan(b)) or a == b
        for a, b in zip(first, second, strict=True)
    )
