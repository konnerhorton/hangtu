"""The correlations framework (SPEC §4; docs/work/m13b1-spt-framework.md, Decision 5).

Each correlation function reads its inputs with ``inputs()``, computes its
estimate in the units its entry gives, and returns ``estimate()``'s frame: the
target column, ``correlation_name`` and ``correlation_note``, with NaN and a
count by reason wherever there is no estimate. A correlation published as a
band also gives ``<target>_lower`` and ``<target>_upper``
(docs/work/m13b2-spt-strength-history.md, Decision 6).
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
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.registry import column_info

CONFIG = "config/correlations.yaml"
OUTPUT_COLUMNS = ("correlation_name", "correlation_note", "correlation_input")
#: correlation_note's reasons, in priority order: a row gets the first that applies.
#: The soil comes first: outside its soils, the correlation doesn't apply at all.
NOT_FOR_SOIL = "not for this soil"
SOIL_UNKNOWN = "soil type unknown"
INPUT_BLANK = "input blank"
REFUSAL = "refusal"
BELOW_RANGE = "below range"
ABOVE_RANGE = "above range"
REASONS = (NOT_FOR_SOIL, SOIL_UNKNOWN, INPUT_BLANK, REFUSAL, BELOW_RANGE, ABOVE_RANGE)
#: The column the opt-in USCS map reads (Decision 10). It is never derived.
USCS = "uscs_symbol"
#: What adds each input column, for the error when it's missing (Decision 3).
MADE_BY = {
    "spt_n": "p.spt(), or a CSV column of N as reported",
    "spt_n60": "ht.analysis.spt() or p.spt(), with an energy ratio",
    "spt_n1_60": 'ht.analysis.spt_n1_60(df, method="...")',
    "effective_vertical_stress": "ht.analysis.vertical_stress()",
    "plasticity_index": 'ht.analysis.add_judgment(df, "plasticity_index")',
}
#: Per bound: its sign as written in a range (low first), the test for outside it,
#: and the reason given.
_BOUNDS = {
    "at_least": ("≤", np.less, BELOW_RANGE),
    "greater_than": ("<", np.less_equal, BELOW_RANGE),
    "at_most": ("≤", np.greater, ABOVE_RANGE),
    "less_than": ("<", np.greater_equal, ABOVE_RANGE),
}
#: A value this close to an inclusive bound (relative) is on it, so a value on a
#: bound stays inside after a unit round trip (60 in kPa through psf).
BOUND_TOLERANCE = 1e-9


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
            "Example: ht.analysis.correlations.describe("
            '"effective_friction_angle_hatanaka_uchida_1996")'
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


def uscs_groups(item: Mapping[str, Any], uscs: Any) -> list[str] | None:
    """Return the USCS groups a ``uscs=`` argument selects, or None to read none."""
    if uscs is None:
        return None
    if uscs == "proposed":
        return list(item["uscs"])
    if (
        isinstance(uscs, list | tuple)
        and uscs
        and all(isinstance(group, str) for group in uscs)
    ):
        return [group.strip().upper() for group in uscs]
    raise HangtuError(
        f'uscs= takes "proposed" or a list of USCS group symbols, not {uscs!r}. '
        'Examples: uscs="proposed", or uscs=["CL", "CH", "CL-ML"].'
    )


def soil(df: pd.DataFrame, groups: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Return the rows whose ``uscs_symbol`` is outside ``groups``, and those blank."""
    if USCS not in df.columns:
        raise ColumnError(
            "uscs= reads each row's USCS group from a 'uscs_symbol' column, and "
            "df has none. Add it from your classification (hangtu doesn't derive "
            "it from the log or soil_class), or leave uscs= out and pass only the "
            "rows the correlation applies to."
        )
    symbols = df[USCS].astype("string").str.strip().str.upper()
    unknown = (symbols.isna() | (symbols == "")).to_numpy(dtype=bool)
    outside = ~unknown & ~symbols.isin(groups).fillna(False).to_numpy(dtype=bool)
    return outside, unknown


def notes(
    df: pd.DataFrame,
    item: Mapping[str, Any],
    values: Mapping[str, np.ndarray],
    uscs: Any = None,
) -> np.ndarray:
    """Return each row's ``correlation_note``: None, or the first reason in REASONS.

    ``values`` holds the inputs and any term the entry's ``range`` limits
    (Decision 5), each computed by the function before this is called.
    ``uscs`` is the function's argument (Decision 10).
    """
    missing = [key for key in item["range"] if key not in values]
    if missing:
        raise KeyError(f"The range names {missing}, which the function didn't compute.")
    found = {reason: np.zeros(len(df), dtype=bool) for reason in REASONS}
    groups = uscs_groups(item, uscs)
    if groups is not None:
        found[NOT_FOR_SOIL], found[SOIL_UNKNOWN] = soil(df, groups)
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
                beyond = outside(data, bound)
            if key in ("at_least", "at_most"):
                beyond &= ~np.isclose(data, bound, rtol=BOUND_TOLERANCE, atol=0)
            found[reason] |= beyond
    result = np.full(len(df), None, dtype=object)
    for reason in reversed(REASONS):
        result[found[reason]] = reason
    return result


def chained(df: pd.DataFrame, item: Mapping[str, Any]) -> np.ndarray:
    """Return each row's upstream correlation, where an input is its estimate.

    An input is an estimate on the rows whose ``correlation_name`` is a
    correlation with that input as its target (Decision 8): a frame from
    ``effective_friction_angle_hatanaka_uchida_1996`` read for
    ``effective_friction_angle``. Its other columns are data. One warning
    names each such input and where it came from; the call still runs.
    """
    upstream = np.full(len(df), None, dtype=object)
    if "correlation_name" not in df.columns:
        return upstream
    names = df["correlation_name"].to_numpy(dtype=object)
    targets = {name: found["target"]["column"] for name, found in catalog().items()}
    found = []
    for column in item["inputs"]:
        rows = np.array([targets.get(name) == column for name in names], dtype=bool)
        if rows.any():
            upstream[rows] = names[rows]
            sources = ", ".join(map(repr, dict.fromkeys(names[rows])))
            found.append(
                f"{column!r} on {int(rows.sum())} rows is an estimate from {sources}"
            )
    if found:
        warn(
            f"{'; '.join(found)}. Chaining correlations compounds their errors, "
            "and the result reads as more certain than it is: prefer an input "
            "from test data. The upstream correlation is in 'correlation_input'."
        )
    return upstream


def estimate(
    df: pd.DataFrame,
    name: str,
    values: np.ndarray,
    note: np.ndarray,
    display_units: str | None,
    *,
    lower: np.ndarray | None = None,
    upper: np.ndarray | None = None,
    uscs: Any = None,
) -> pd.DataFrame:
    """Return a copy of ``df`` with the estimate and the correlation's columns.

    ``values`` are in the entry's target unit; rows with a note get NaN. One
    warning counts the rows without an estimate by reason. ``lower`` and
    ``upper``, for a band, are written as ``<target>_lower`` and
    ``<target>_upper`` in the same unit; NaN in ``upper`` is an open band.
    ``uscs`` is recorded as given in ``attrs["correlation_uscs"]``, so results
    of calls with the same argument keep equal attrs under ``pd.concat``.
    """
    item = entry(name)
    target = item["target"]["column"]
    upstream = chained(df, item)
    system = _display_units(display_units or settings.display_units)
    noted = np.array([reason is not None for reason in note], dtype=bool)
    quantity = column_info(target)["quantity"]
    columns = {target: values}
    if lower is not None or upper is not None:
        nan = np.full(len(df), np.nan)
        columns[f"{target}_lower"] = nan if lower is None else lower
        columns[f"{target}_upper"] = nan if upper is None else upper
    shown = {}
    for column, data in columns.items():
        data = np.where(noted, np.nan, np.asarray(data, dtype=float))
        shown[column], unit_text = _units.to_display(
            data, item["target"]["unit"], quantity, system
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
    replaced = [column for column in (*shown, *OUTPUT_COLUMNS) if column in df.columns]
    if replaced:
        warn(f"Replaced the existing columns {', '.join(map(repr, replaced))}.")

    result = df.copy()
    for column, data in shown.items():
        result[column] = data
    result["correlation_name"] = name
    result["correlation_note"] = pd.Series(note, index=df.index, dtype=object)
    result["correlation_input"] = pd.Series(upstream, index=df.index, dtype=object)
    result.attrs["units"] = {
        **_units.units_of(df),
        **dict.fromkeys(shown, unit_text),
    }
    # Every entry, not only this one, so results from one input have equal attrs
    # and pd.concat keeps them (units too); correlation_name says which applies.
    result.attrs["correlations"] = copy.deepcopy(catalog())
    result.attrs["correlation_uscs"] = (
        uscs if uscs is None or isinstance(uscs, str) else list(uscs)
    )
    return result
