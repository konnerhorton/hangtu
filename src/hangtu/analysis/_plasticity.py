"""Atterberg indices and plasticity classes (docs/drafts/analysis.md §2.3 to 2.5)."""

from typing import Any

import numpy as np
import pandas as pd

from hangtu import _config
from hangtu._data import flag_column, numeric_column, rows_text
from hangtu.errors import ColumnError, HangtuError, warn

#: Slack on the A-line comparison, so a point exactly on the line is a clay
#: whatever the floating-point noise (§2.5).
SLACK = 1e-9
#: PI given more than this far from LL - PL is warned about (§2.8), as QC A002.
PLASTICITY_INDEX_TOLERANCE = 1.0
_INPUTS = ("liquid_limit", "plastic_limit", "plasticity_index", "water_content")
_NOT_PLASTIC_HINT = "Leave the cell blank, or False, for a plastic specimen."


def plasticity_system(name: str) -> dict[str, Any]:
    """Return a plasticity chart system from ``config/plasticity_systems.yaml``."""
    systems = _config.load("config/plasticity_systems.yaml")
    if name not in systems:
        raise HangtuError(
            f"There is no plasticity system named {name!r}. Systems: "
            f'{", ".join(map(repr, systems))}. Example: system="uscs"'
        )
    return systems[name]


def a_line(liquid_limit: Any, system: str = "uscs") -> Any:
    """Return the A-line's PI at ``liquid_limit``: PI = 0.73 (LL - 20)."""
    line = plasticity_system(system)["a_line"]
    return line["slope"] * (np.asarray(liquid_limit, dtype=float) - line["intercept"])


def on_or_above_a_line(
    liquid_limit: Any, plasticity_index: Any, system: str = "uscs"
) -> np.ndarray:
    """Return True where (LL, PI) is on or above the A-line (the clay side)."""
    index = np.asarray(plasticity_index, dtype=float)
    return index >= a_line(liquid_limit, system) - SLACK


def _uscs_classes(liquid: np.ndarray, index: np.ndarray) -> np.ndarray:
    """USCS fine-grained class from LL and PI (NP already given as PI = 0)."""
    system = plasticity_system("uscs")
    silty = system["silty_clay"]
    above = on_or_above_a_line(liquid, index, "uscs")
    high = liquid >= system["high_plasticity_from"]
    classes = np.full(len(liquid), None, dtype=object)
    classes[~high] = "ML"
    classes[~high & above & (index >= silty["lower"]) & (index <= silty["upper"])] = (
        "CL-ML"
    )
    classes[~high & above & (index > system["clay_above"])] = "CL"
    classes[high & above] = "CH"
    classes[high & ~above] = "MH"
    return classes


def _bs5930_classes(liquid: np.ndarray, index: np.ndarray) -> np.ndarray:
    """BS 5930 class: C or M, then the plasticity term from LL."""
    bands = plasticity_system("bs5930")["bands"]
    names = [band["name"] for band in bands]
    lowers = np.array([band["lower"] for band in bands], dtype=float)
    above = on_or_above_a_line(liquid, index, "bs5930")
    position = np.searchsorted(lowers, np.nan_to_num(liquid), side="right") - 1
    return np.array(
        [
            ("C" if clay else "M") + names[max(where, 0)]
            for clay, where in zip(above, position, strict=True)
        ],
        dtype=object,
    )


def _classes(
    liquid: np.ndarray, index: np.ndarray, non_plastic: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Return the USCS and BS 5930 classes (§2.5), blank where they can't be found."""
    for_class = np.where(non_plastic, 0.0, index)
    known = ~np.isnan(liquid) & ~np.isnan(for_class)
    uscs = np.full(len(liquid), None, dtype=object)
    bs5930 = np.full(len(liquid), None, dtype=object)
    if known.any():
        uscs[known] = _uscs_classes(liquid[known], for_class[known])
        bs5930[known] = _bs5930_classes(liquid[known], for_class[known])
    # NP with no LL: ML in USCS (D2487 puts non-plastic fines with ML); the BS
    # 5930 term needs LL, so it stays blank.
    uscs[non_plastic & np.isnan(liquid)] = "ML"
    return uscs, bs5930


def _read(df: pd.DataFrame) -> dict[str, np.ndarray]:
    values = {}
    for column in _INPUTS:
        if column not in df.columns:
            values[column] = np.full(len(df), np.nan)
            continue
        numbers = numeric_column(df, column)
        negative = numbers < 0
        if negative.any():
            raise HangtuError(
                f"Column {column!r} has negative values in rows "
                f"{rows_text(df.index[negative])}. Atterberg limits and water "
                "content are percentages, 0 or more."
            )
        values[column] = numbers
    return values


def plasticity(df: pd.DataFrame) -> pd.DataFrame:
    """Add the plasticity index, LI, Ic and plasticity classes (analysis.md §2.4).

    Returns a copy of ``df`` with these columns added, or their blanks filled
    in. No row is dropped or reordered, other columns are unchanged, and
    declared units are kept.

    - **plasticity_index**: kept where given; else LL - PL. Blank for NP.
    - **liquidity_index** = (w - PL) / PI; **consistency_index** = (LL - w) / PI.
      Blank for NP and where PI is 0.
    - **plasticity_class_uscs**: CL, CL-ML, ML, CH or MH from LL and PI (ASTM
      D2487). This is the inorganic class: OL and OH are never given, since
      they need the oven-dried liquid limit. Identify organic soils yourself.
    - **plasticity_class_bs5930**: C (on or above the A-line) or M, then the
      plasticity term from LL: L, I, H, V or E (BS 5930), e.g. CI, MH.

    An NP specimen is classed as PI = 0 (USCS puts non-plastic fines with ML or
    MH), while its ``plasticity_index`` stays blank, so NP stays distinct from a
    measured PI everywhere else. A point on the A-line counts as a clay.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per specimen, as ``ht.template("atterberg")`` or
        ``p.atterberg()``. Only ``liquid_limit`` is required. Values are in
        percent. ``non_plastic`` marks NP specimens (True/False, yes/no, 1/0).

    Returns
    -------
    pandas.DataFrame

    Examples
    --------
    >>> limits = ht.read_csv("atterberg.csv")
    >>> limits = ht.analysis.plasticity(limits)
    >>> limits[["liquid_limit", "plasticity_index", "plasticity_class_uscs"]]
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if "liquid_limit" not in df.columns:
        raise ColumnError(
            "Column 'liquid_limit' not found. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}."
        )
    values = _read(df)
    liquid = values["liquid_limit"]
    plastic = values["plastic_limit"]
    given = values["plasticity_index"]
    water = values["water_content"]
    non_plastic = np.array(
        [flag is True for flag in flag_column(df, "non_plastic", _NOT_PLASTIC_HINT)],
        dtype=bool,
    )

    contradicts = non_plastic & ~np.isnan(given)
    if contradicts.any():
        raise HangtuError(
            f"Rows {rows_text(df.index[contradicts])} are marked non_plastic but "
            "also have a plasticity_index. A non-plastic specimen has no PI: "
            "blank the PI, or set non_plastic to False."
        )
    difference = liquid - plastic
    inverted = ~non_plastic & (difference < 0)
    if inverted.any():
        raise HangtuError(
            f"Rows {rows_text(df.index[inverted])} have a plastic_limit above "
            "their liquid_limit, which is impossible. Check the two columns, or "
            "mark the specimens non_plastic."
        )
    off = ~np.isnan(given) & (np.abs(given - difference) > PLASTICITY_INDEX_TOLERANCE)
    if off.any():
        warn(
            f"Rows {rows_text(df.index[off])} have a plasticity_index more than "
            f"{PLASTICITY_INDEX_TOLERANCE:g} percentage point from liquid_limit - "
            "plastic_limit. The plasticity_index given is used."
        )
    index = np.where(np.isnan(given) & ~non_plastic, difference, given)
    above_liquid = index > liquid
    if above_liquid.any():
        warn(
            f"Rows {rows_text(df.index[above_liquid])} have a plasticity_index "
            "above their liquid_limit, which is impossible. They are kept; check "
            "the values."
        )

    usable = ~non_plastic & (index > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        liquidity = np.where(usable, (water - plastic) / index, np.nan)
        consistency = np.where(usable, (liquid - water) / index, np.nan)
    uscs, bs5930 = _classes(liquid, index, non_plastic)

    result = df.copy()
    result["plasticity_index"] = index
    result["liquidity_index"] = liquidity
    result["consistency_index"] = consistency
    result["plasticity_class_uscs"] = uscs
    result["plasticity_class_bs5930"] = bs5930
    return result
