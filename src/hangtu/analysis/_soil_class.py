"""Each row's ``soil_class``, and rows whose class a method doesn't apply to.

A check reads the class the user supplied, from the ``soil_class`` column or
a Project's ``attrs["soil_classes"]`` by ``geology_unit`` (SPEC §8.3), and
never derives one. Only the classes in ``CHECKED`` are compared: fill
behaves as its dominant soil and organic clay is still a clay, so neither
contradicts a method (docs/analysis/correlations.md §2,
docs/analysis/index-and-spt.md §1.4).
"""

from collections.abc import Iterable, Sequence

import numpy as np
import pandas as pd

#: The classes a check compares; any other class, or none, is never flagged.
CHECKED = ("coarse", "fine", "rock")


def row_classes(df: pd.DataFrame) -> np.ndarray:
    """Return each row's ``soil_class`` as text, or None where it isn't known."""
    if "soil_class" in df.columns:
        classes = df["soil_class"].astype(object)
    elif "geology_unit" in df.columns and df.attrs.get("soil_classes"):
        mapping = dict(df.attrs["soil_classes"])
        classes = df["geology_unit"].astype(object).map(mapping)
    else:
        return np.full(len(df), None, dtype=object)
    return np.array(
        [value.strip() if isinstance(value, str) else None for value in classes],
        dtype=object,
    )


def contradicting(
    classes: np.ndarray, allowed: Iterable[str] | np.ndarray
) -> np.ndarray:
    """Return the rows whose class is checked and not allowed.

    ``allowed`` is one list of classes for every row, or an array holding a
    list (or None, for no check) per row.
    """
    if isinstance(allowed, np.ndarray):
        per_row: Sequence[Iterable[str] | None] = list(allowed)
    else:
        per_row = [list(allowed)] * len(classes)
    return np.array(
        [
            value in CHECKED and keep is not None and value not in keep
            for value, keep in zip(classes, per_row, strict=True)
        ],
        dtype=bool,
    )


def by_unit(df: pd.DataFrame, rows: np.ndarray, classes: np.ndarray) -> str:
    """Write the flagged rows as ``"Alluvium (fine): 12"``, one per unit and class."""
    if "geology_unit" in df.columns:
        units = df["geology_unit"].astype(object).to_numpy()
    else:
        units = np.full(len(df), None, dtype=object)
    counts: dict[tuple[str, str], int] = {}
    for unit, value in zip(units[rows], classes[rows], strict=True):
        key = ("no geology unit" if pd.isna(unit) else str(unit), str(value))
        counts[key] = counts.get(key, 0) + 1
    return "; ".join(f"{unit} ({value}): {n}" for (unit, value), n in counts.items())
