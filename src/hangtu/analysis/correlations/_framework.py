"""The correlations framework (SPEC §4; docs/work/m13b1-spt-framework.md, Decision 5).

Each correlation function reads its inputs with ``inputs()``, computes its
estimate in the units its entry gives, and returns ``estimate()``'s frame: the
target column, ``correlation_name`` and ``correlation_note``, with NaN and a
count by reason wherever there is no estimate.
"""

import copy
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from hangtu import _config
from hangtu import units as _units
from hangtu._data import flag_column, numeric_column
from hangtu._settings import _display_units, settings
from hangtu.analysis._overburden import check_columns
from hangtu.errors import HangtuError, warn
from hangtu.registry import column_info

CONFIG = "config/correlations.yaml"
OUTPUT_COLUMNS = ("correlation_name", "correlation_note")
#: correlation_note's reasons, in priority order: a row gets the first that applies.
INPUT_BLANK = "input blank"
REFUSAL = "refusal"
BELOW_RANGE = "below range"
ABOVE_RANGE = "above range"
REASONS = (INPUT_BLANK, REFUSAL, BELOW_RANGE, ABOVE_RANGE)
#: What adds each input column, for the error when it's missing (Decision 3).
MADE_BY = {
    "spt_n60": "ht.analysis.spt() or p.spt(), with an energy ratio",
    "spt_n1_60": 'ht.analysis.spt_n1_60(df, method="...")',
    "effective_vertical_stress": "ht.analysis.vertical_stress()",
}
#: Per bound: its sign as written in a range (low first), the test for outside it,
#: and the reason given.
_BOUNDS = {
    "at_least": ("≤", np.less, BELOW_RANGE),
    "greater_than": ("<", np.less_equal, BELOW_RANGE),
    "at_most": ("≤", np.greater, ABOVE_RANGE),
    "less_than": ("<", np.greater_equal, ABOVE_RANGE),
}


def catalog() -> dict[str, dict[str, Any]]:
    """Return every entry in ``config/correlations.yaml``, by name.

    The result is shared and cached: copy it before changing it.
    """
    return _config.load(CONFIG)


def entry(name: str) -> dict[str, Any]:
    """Return a copy of one correlation's entry; an unknown name lists them all."""
    entries = catalog()
    if name not in entries:
        raise HangtuError(
            f"There is no correlation named {name!r}. Correlations: "
            f"{', '.join(map(repr, entries))}. "
            'Example: ht.analysis.correlations.describe("hatanaka_uchida_1996")'
        )
    return copy.deepcopy(entries[name])


def range_text(item: Mapping[str, Any]) -> str:
    """Write an entry's range as ``"4.55 ≤ spt_n1_60 ≤ 39"``, joined by ``"; "``."""
    parts = []
    for column, bounds in item["range"].items():
        text = column
        for key, bound in bounds.items():
            sign = _BOUNDS[key][0]
            if key in ("at_least", "greater_than"):
                text = f"{bound:g} {sign} {text}"
            else:
                text = f"{text} {sign} {bound:g}"
        parts.append(text)
    return "; ".join(parts)


def inputs(
    df: pd.DataFrame, item: Mapping[str, Any], units: Mapping[str, str] | None
) -> dict[str, np.ndarray]:
    """Return each input column by its registry name, in the units the entry gives.

    A missing column is an error naming it and what adds it: there is no
    argument to read another column instead (Decision 3).
    """
    check_columns(df, list(item["inputs"]), MADE_BY)
    values = {}
    for column, spec in item["inputs"].items():
        data = numeric_column(df, column)
        if spec["unit"] is not None:
            unit = _units.resolve_units(df, [column], units, analysis=True)[column]
            quantity = column_info(column)["quantity"]
            data = _units.convert(
                data,
                _units.parse_unit(unit, column),
                quantity,
                _units.parse_unit(spec["unit"]),
            )
        values[column] = data
    return values


def notes(
    df: pd.DataFrame, item: Mapping[str, Any], values: Mapping[str, np.ndarray]
) -> np.ndarray:
    """Return each row's ``correlation_note``: None, or the first reason in REASONS."""
    found = {reason: np.zeros(len(df), dtype=bool) for reason in REASONS}
    for data in values.values():
        found[INPUT_BLANK] |= np.isnan(data)
    if "spt_refusal" in df.columns:
        flags = flag_column(
            df, "spt_refusal", "Leave the cell blank when you don't know."
        )
        found[REFUSAL] = np.array([flag is True for flag in flags], dtype=bool)
    for column, bounds in item["range"].items():
        data = values[column]
        for key, bound in bounds.items():
            _, outside, reason = _BOUNDS[key]
            with np.errstate(invalid="ignore"):
                found[reason] |= outside(data, bound)
    result = np.full(len(df), None, dtype=object)
    for reason in reversed(REASONS):
        result[found[reason]] = reason
    return result


def estimate(
    df: pd.DataFrame,
    name: str,
    values: np.ndarray,
    note: np.ndarray,
    display_units: str | None,
) -> pd.DataFrame:
    """Return a copy of ``df`` with the estimate and the correlation's columns.

    ``values`` are in the entry's target unit; rows with a note get NaN. One
    warning counts the rows without an estimate by reason.
    """
    item = entry(name)
    target = item["target"]["column"]
    system = _display_units(display_units or settings.display_units)
    noted = np.array([reason is not None for reason in note], dtype=bool)
    values = np.where(noted, np.nan, np.asarray(values, dtype=float))
    quantity = column_info(target)["quantity"]
    shown, unit_text = _units.to_display(
        values, item["target"]["unit"], quantity, system
    )

    if noted.any():
        counts = pd.Series(note[noted]).value_counts()
        reasons = ", ".join(
            f"{counts[reason]} {reason}" for reason in REASONS if reason in counts
        )
        warn(
            f"{name} gave no estimate for {int(noted.sum())} of {len(df)} rows "
            f"({reasons}; see 'correlation_note'). Its range is "
            f"{range_text(item)}; outside it the estimate is blank, never "
            "extrapolated."
        )
    replaced = [column for column in (target, *OUTPUT_COLUMNS) if column in df.columns]
    if replaced:
        warn(f"Replaced the existing columns {', '.join(map(repr, replaced))}.")

    result = df.copy()
    result[target] = shown
    result["correlation_name"] = name
    result["correlation_note"] = pd.Series(note, index=df.index, dtype=object)
    result.attrs["units"] = {**_units.units_of(df), target: unit_text}
    # Every entry, not only this one, so results from one input have equal attrs
    # and pd.concat keeps them (units too); correlation_name says which applies.
    result.attrs["correlations"] = copy.deepcopy(catalog())
    return result
