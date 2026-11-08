"""The SPT refusal upper limit: an optional judgment for ``fit()`` (SPEC §4, §5).

Spec: docs/analysis/judgments.md §5.6 and docs/analysis/statistics.md §1. ``fit()``
reads it as ``spt_refusal_upper_limit=``, then ``judgments=``, then the
Project's file the frame carries. Unset is not an error: refusals stay
right-censored, the test's own result (ASTM D1586), and a note says the tail
above them is then the distribution's.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from numbers import Real
from typing import Any

import numpy as np
import pandas as pd

from hangtu import _judgments
from hangtu._data import flag_column, numeric_column, rows_text
from hangtu.analysis._judgment_values import (
    ALL,
    Values,
    from_file,
    read_judgments,
    take,
)
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.registry import column_info

NAME = "spt_refusal_upper_limit"
FIELD = "spt_n"
KEY = "geology_unit"
#: The N columns whose value carries factors on field N (ER / 60, then C_N), so
#: a row's limit is scaled by its value / spt_n. spt_n is field N, and
#: spt_n_capped holds the cap at a refusal, not a scaled N: both take the limit
#: as it is.
SCALED = ("spt_n60", "spt_n1_60")
EXAMPLE = 'spt_refusal_upper_limit=120, or {"Terrace": 120, "Alluvium": "none"}'


@dataclass(frozen=True)
class Limits:
    """Each row's upper limit, in the fitted column's terms, with its record.

    ``upper`` is NaN where no limit applies (not a refusal, or no judgment)
    and infinite where the judgment is ``none``: both stay right-censored.
    """

    upper: np.ndarray
    record: dict[str, Any] | None = None
    notes: list[str] = field(default_factory=list)


def refusal_rows(frame: pd.DataFrame) -> np.ndarray:
    """Return the rows ``spt_refusal`` marks True (none without the column)."""
    if "spt_refusal" not in frame.columns:
        return np.zeros(len(frame), bool)
    hint = "fit() reads it to find the refusals."
    return np.array([flag is True for flag in flag_column(frame, "spt_refusal", hint)])


def n_columns() -> list[str]:
    """Return the N columns ``spt_refusal`` flags, from the registry."""
    info = column_info("spt_refusal")
    assert info is not None  # registered
    return list(info["statistics"]["values"])


def resolve(
    argument: Any,
    judgments: Any,
    frame: pd.DataFrame,
    column: str,
    numbers: np.ndarray,
    refusals: np.ndarray,
) -> Limits:
    """Return each row's upper limit for ``refusals``, the rows fitted as refusals.

    ``numbers`` are the fitted values, in the column's terms.
    """
    none = Limits(np.full(len(frame), np.nan))
    if column not in n_columns():
        if argument is not None:
            raise HangtuError(
                f"spt_refusal_upper_limit= bounds SPT refusals, and {column!r} "
                f"isn't an SPT N column ({', '.join(n_columns())}). Leave it out."
            )
        return none
    read = read_judgments(judgments, frame)
    in_file = read is not None and NAME in read.judgments
    if argument is not None:
        if in_file:
            assert read is not None  # in_file
            warn(f"spt_refusal_upper_limit= replaces the one in {read.path.name}.")
        values = _argument(argument, frame)
    elif in_file:
        assert read is not None  # in_file
        values = from_file(read.judgments[NAME], read)
    else:
        if not refusals.any():
            return none
        return Limits(
            none.upper,
            notes=[
                f"The tail above the {int(refusals.sum())} refusals is the "
                "distribution's: they are fitted as at least their value. Set "
                "spt_refusal_upper_limit, in field N per geology unit, to limit "
                "it (the judgments guide)."
            ],
        )
    if not refusals.any():
        return none
    keys = _keys(values, frame, refusals)
    found = take(values, keys[refusals], "geology unit")
    limit = np.full(len(frame), np.nan)
    limit[refusals] = [found[key][FIELD] for key in keys[refusals]]
    upper = limit * _scale(frame, column, numbers, refusals)
    _check_above(frame, column, numbers, upper, limit)
    return Limits(upper, values.record(), _notes(values, column, keys, refusals, limit))


def _argument(argument: Any, frame: pd.DataFrame) -> Values:
    def number(value: Any, where: str) -> float:
        if isinstance(value, str) and value.strip() == _judgments.NONE:
            return math.inf
        if (
            isinstance(value, bool)
            or not isinstance(value, Real)
            or not math.isfinite(value)
            or value <= 0
        ):
            raise HangtuError(
                f"{where} must be a positive number of blows per foot (field N), "
                f'or "none" for no limit on purpose, not {value!r}. '
                f"Example: {EXAMPLE}"
            )
        return float(value)

    if isinstance(argument, Mapping):
        if not argument:
            raise HangtuError(f"spt_refusal_upper_limit= is empty. Example: {EXAMPLE}")
        entries = {
            str(key): {FIELD: number(value, f"spt_refusal_upper_limit[{key!r}]")}
            for key, value in argument.items()
        }
        present = set(_column(frame).dropna().astype(str)) if KEY in frame else set()
        unknown = [key for key in entries if key not in present]
        if unknown:
            raise HangtuError(
                f"spt_refusal_upper_limit= names {', '.join(map(repr, unknown))}, "
                f"which {'is' if len(unknown) == 1 else 'are'} not a geology unit "
                f"in the rows ({', '.join(map(repr, sorted(present))) or 'none'}). "
                "Keys match geology_unit exactly, by case too."
            )
        texts = {
            key: {FIELD: _judgments.quantity_text(entry[FIELD], "")}
            for key, entry in entries.items()
        }
        return Values(NAME, "argument", KEY, entries, texts)
    value = number(argument, "spt_refusal_upper_limit=")
    text = _judgments.quantity_text(value, "")
    return Values(NAME, "argument", None, {ALL: {FIELD: value}}, {ALL: {FIELD: text}})


def _column(frame: pd.DataFrame) -> pd.Series:
    return frame[KEY].astype("string").str.strip().replace("", pd.NA)


def _keys(values: Values, frame: pd.DataFrame, refusals: np.ndarray) -> np.ndarray:
    """Return each row's key: its geology unit, or ``ALL`` for one value."""
    if values.by is None:
        return np.full(len(frame), ALL, dtype=object)
    if KEY not in frame.columns:
        raise ColumnError(
            "spt_refusal_upper_limit is keyed by geology unit, and the rows have "
            "no 'geology_unit' column. Add it (p.spt() has it when the project "
            "has a geology map), or give one limit for every row, e.g. "
            "spt_refusal_upper_limit=120."
        )
    units = _column(frame)
    blank = refusals & units.isna().to_numpy(bool)
    if blank.any():
        raise HangtuError(
            f"Refusals in rows {rows_text(frame.index[blank])} have no geology_unit, "
            "so spt_refusal_upper_limit has no key for them. Fill it, or give one "
            "limit for every row, e.g. spt_refusal_upper_limit=120."
        )
    return units.fillna("").to_numpy(dtype=object)


def _scale(
    frame: pd.DataFrame, column: str, numbers: np.ndarray, refusals: np.ndarray
) -> np.ndarray:
    """Return each refusal's factor from field N to ``column``: value / spt_n."""
    if column not in SCALED:
        return np.ones(len(frame))
    if FIELD not in frame.columns:
        raise ColumnError(
            f"spt_refusal_upper_limit is field N, and each refusal's limit in "
            f"{column} is the limit x {column} / spt_n, its own factors. The rows "
            "have no 'spt_n' column: keep it from p.spt(), or fit spt_n itself."
        )
    n = numeric_column(frame, FIELD)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = numbers / n
    bad = refusals & ~(np.isfinite(ratio) & (ratio > 0))
    if bad.any():
        raise HangtuError(
            f"Refusals in rows {rows_text(frame.index[bad])} have no positive spt_n, "
            f"so their limit in {column} (the limit x {column} / spt_n) can't be "
            "found. Fill spt_n with the blows recorded at refusal."
        )
    return ratio


def _check_above(
    frame: pd.DataFrame,
    column: str,
    numbers: np.ndarray,
    upper: np.ndarray,
    limit: np.ndarray,
) -> None:
    """Raise if a refusal's limit isn't above its value: no interval to fit."""
    with np.errstate(invalid="ignore"):
        low = upper <= numbers
    if low.any():
        first = int(np.flatnonzero(low)[0])
        raise HangtuError(
            f"spt_refusal_upper_limit isn't above the refusal in rows "
            f"{rows_text(frame.index[low])}: in row {frame.index[first]!r}, "
            f"{column} is {numbers[first]:g} and the limit {upper[first]:g} "
            f"({limit[first]:g} blows/ft as field N). The limit is the most the "
            "refusal could be, above the value recorded (the cap, not the "
            "limit, is where a refusal is recorded): raise it."
        )


def _notes(
    values: Values,
    column: str,
    keys: np.ndarray,
    refusals: np.ndarray,
    limit: np.ndarray,
) -> list[str]:
    notes = []
    scaled = f", scaled by each row's {column} / spt_n" if column in SCALED else ""
    for key in dict.fromkeys(keys[refusals]):
        rows = refusals & (keys == key)
        count = int(rows.sum())
        label = "All" if key == ALL else key
        value = float(limit[rows][0])
        plural = "refusal" if count == 1 else "refusals"
        if math.isinf(value):
            entry = values.texts.get(key) or values.project_text or {}
            reason = entry.get("reason")
            notes.append(
                f"{label}: {count} {plural} right-censored on purpose: "
                f"spt_refusal_upper_limit is none"
                + (f" ({reason})." if reason else ".")
            )
        else:
            notes.append(
                f"{label}: {count} {plural} fitted between their {column} and the "
                f"upper limit ({value:g} blows/ft as field N{scaled})."
            )
    return notes
