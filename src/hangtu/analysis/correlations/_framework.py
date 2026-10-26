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
from functools import cache
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
OUTPUT_COLUMNS = (
    "correlation_name",
    "correlation_note",
    "correlation_input",
    "correlation_soil",
)
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
#: The column a soil= mapping is keyed by (docs/work/m13b3-spt-stiffness.md, D3).
SOIL_KEY = "geology_unit"
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


@cache
def catalog() -> dict[str, dict[str, Any]]:
    """Return every entry in ``config/correlations.yaml``, by name.

    Each entry has a ``label``, its legend text: the entry's own ``label:``,
    else its first source's ``cite``. The result is shared and cached: copy
    it before changing it.
    """
    entries = copy.deepcopy(_config.load(CONFIG))
    for item in entries.values():
        item.setdefault("label", item["sources"][0]["cite"])
    return entries


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
    """Write an entry's range as ``"4.55 ≤ (N1)60 ≤ 39"``, joined by ``"; "``.

    Each input or term is named by its ``labels`` entry, as the docstring
    writes it, and followed by its unit where it has one (TODO #41).
    """
    labels = item.get("labels") or {}
    parts = []
    for column, bounds in item["range"].items():
        text = labels.get(column, column)
        if set(bounds) <= {"at_least", "greater_than"}:
            # A lower bound alone reads "σ′v0 > 0 kPa", so the unit follows a number.
            for key, bound in bounds.items():
                text = f"{text} {'≥' if key == 'at_least' else '>'} {bound:g}"
            bounds = {}
        for key, bound in bounds.items():
            sign = _BOUNDS[key][0]
            if key in ("at_least", "greater_than"):
                text = f"{bound:g} {sign} {text}"
            else:
                text = f"{text} {sign} {bound:g}"
        unit = item["inputs"].get(column, {}).get("unit") or (
            item.get("terms", {}).get(column, {}).get("unit")
        )
        parts.append(f"{text} {unit}" if unit else text)
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
        if not item.get("uscs"):
            raise HangtuError(
                "This correlation is for all soils in its source, so hangtu "
                "proposes no USCS groups for it. Pass the groups to keep, e.g. "
                'uscs=["SP", "SM"], or leave uscs= out.'
            )
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


def soil_rows(df: pd.DataFrame, item: Mapping[str, Any], soil: Any) -> np.ndarray:
    """Return the source's soil row for each row of ``df``, from ``soil=``.

    ``soil`` names one of the entry's ``rows`` for every row, or maps each
    ``geology_unit`` to one. It is required: the row is the engineer's reading
    of the log, never inferred (docs/work/m13b3-spt-stiffness.md, Decision 3).
    """
    rows = item["rows"]
    listed = "; ".join(f"{name!r} ({row['wording']})" for name, row in rows.items())
    example = next(iter(rows))
    if soil is None:
        raise HangtuError(
            "soil= is required: name the source's soil row the coefficient is "
            f"taken from. Its rows: {listed}. Example: soil={example!r}, or "
            f'soil={{"Alluvium": {example!r}}} by geology unit.'
        )
    names = list(soil.values()) if isinstance(soil, Mapping) else [soil]
    unknown = [name for name in names if name not in rows]
    if unknown:
        raise HangtuError(
            f"soil= names {', '.join(map(repr, unknown))}, which isn't one of the "
            f"source's rows: {listed}."
        )
    if not isinstance(soil, Mapping):
        return np.full(len(df), soil, dtype=object)
    if SOIL_KEY not in df.columns:
        raise ColumnError(
            "soil= maps geology units to rows, and df has no 'geology_unit' "
            "column. Add it (p.spt() has it), or give one row name for every row."
        )
    units = df[SOIL_KEY].astype("string").str.strip()
    blank = int((units.isna() | (units == "")).sum())
    if blank:
        raise HangtuError(
            f"soil= maps geology units to rows, and {blank} rows have no "
            "'geology_unit'. Fill it, or pass those rows separately with one row "
            "name."
        )
    unmapped = sorted(set(units) - set(soil))
    if unmapped:
        raise HangtuError(
            f"soil= gives no row for the geology units "
            f"{', '.join(map(repr, unmapped))}. Add them to the mapping, or leave "
            "their rows out of df."
        )
    return units.map(soil).to_numpy(dtype=object)


def notes(
    df: pd.DataFrame,
    item: Mapping[str, Any],
    values: Mapping[str, np.ndarray],
    uscs: Any = None,
    rows: np.ndarray | None = None,
) -> np.ndarray:
    """Return each row's ``correlation_note``: None, or the first reason in REASONS.

    ``values`` holds the inputs and any term the entry's ``range`` limits
    (Decision 5), each computed by the function before this is called.
    ``uscs`` is the function's argument (Decision 10). ``rows``, from
    ``soil_rows()``, gives each row's soil row; with ``uscs="proposed"`` each
    row is checked against its own soil row's groups, which ``uscs=`` checks
    but never chooses (docs/work/m13b3-spt-stiffness.md, Decision 3).
    """
    missing = [key for key in item["range"] if key not in values]
    if missing:
        raise KeyError(f"The range names {missing}, which the function didn't compute.")
    found = {reason: np.zeros(len(df), dtype=bool) for reason in REASONS}
    if rows is not None and uscs == "proposed":
        _, found[SOIL_UNKNOWN] = soil(df, [])
        for name in dict.fromkeys(rows):
            outside, _ = soil(df, item["rows"][name]["uscs"])
            found[NOT_FOR_SOIL] |= outside & (rows == name)
    else:
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
    rows: np.ndarray | None = None,
) -> pd.DataFrame:
    """Return a copy of ``df`` with the estimate and the correlation's columns.

    ``values`` are in the entry's target unit; rows with a note get NaN. One
    warning counts the rows without an estimate by reason. ``lower`` and
    ``upper``, for a band, are written as ``<target>_lower`` and
    ``<target>_upper`` in the same unit; NaN in ``upper`` is an open band.
    ``uscs`` is recorded as given in ``attrs["correlation_uscs"]``, so results
    of calls with the same argument keep equal attrs under ``pd.concat``.
    ``rows``, each row's soil row, goes in ``correlation_soil`` (blank
    without one) and not in attrs: two correlations' soil rows always
    differ, and unequal attrs would make ``pd.concat`` drop them all, units
    too.
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
        # The range explains only the rows outside it (TODO #41).
        outside = BELOW_RANGE in counts or ABOVE_RANGE in counts
        warn(
            f"{name} gave no estimate for {int(noted.sum())} of {len(df)} rows "
            f"({reasons}; see 'correlation_note')."
            + (
                f" Its range is {range_text(item)}; outside it the estimate is "
                "blank, never extrapolated."
                if outside
                else ""
            )
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
    result["correlation_soil"] = pd.Series(
        np.full(len(df), None, dtype=object) if rows is None else rows,
        index=df.index,
        dtype=object,
    )
    # A dimensionless target (OCR, K0) has no unit to record.
    result.attrs["units"] = {
        **_units.units_of(df),
        **({} if unit_text is None else dict.fromkeys(shown, unit_text)),
    }
    # Every entry, not only this one, so results from one input have equal attrs
    # and pd.concat keeps them (units too); correlation_name says which applies.
    result.attrs["correlations"] = copy.deepcopy(catalog())
    result.attrs["correlation_uscs"] = (
        uscs if uscs is None or isinstance(uscs, str) else list(uscs)
    )
    return result
