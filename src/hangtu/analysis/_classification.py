"""USCS group symbols and AASHTO groups (docs/drafts/analysis.md §2.6 to 2.7)."""

import operator
from collections.abc import Callable

import numpy as np
import pandas as pd

from hangtu._data import flag_column, numeric_column, rows_text
from hangtu.analysis._plasticity import plasticity
from hangtu.errors import ColumnError, HangtuError, warn

#: Slack on the fines boundaries (5 % and 12 %) and the Cu and Cc limits, so a
#: value exactly on one (Cc = 0.3² / (0.1 * 0.9) = 1) isn't moved across it by
#: floating-point noise.
SLACK = 1e-9
_USCS_FRACTIONS = ("gravel_content", "sand_content", "fines_content")
_OVERSIZE = ("cobbles_content", "boulders_content")
_AASHTO_FRACTIONS = (
    "silt_clay_content",
    "fine_sand_content",
    "coarse_sand_content",
    "gravel_content",
)
_LE, _GE, _LT = operator.le, operator.ge, operator.lt
#: AASHTO M 145 groups, tested left to right (§2.7): each condition is
#: (input, comparison, limit). "pi" is 0 for NP; "np" is 1 for NP, else 0.
_AASHTO_GROUPS: list[tuple[str, list[tuple[str, Callable, float]]]] = [
    ("A-1-a", [("p10", _LE, 50), ("p40", _LE, 30), ("p200", _LE, 15), ("pi", _LE, 6)]),
    ("A-1-b", [("p40", _LE, 50), ("p200", _LE, 25), ("pi", _LE, 6)]),
    ("A-3", [("p40", _GE, 51), ("p200", _LE, 10), ("np", _GE, 1)]),
    ("A-2-4", [("p200", _LE, 35), ("ll", _LE, 40), ("pi", _LE, 10)]),
    ("A-2-5", [("p200", _LE, 35), ("ll", _GE, 41), ("pi", _LE, 10)]),
    ("A-2-6", [("p200", _LE, 35), ("ll", _LE, 40), ("pi", _GE, 11)]),
    ("A-2-7", [("p200", _LE, 35), ("ll", _GE, 41), ("pi", _GE, 11)]),
    ("A-4", [("p200", _GE, 36), ("ll", _LE, 40), ("pi", _LE, 10)]),
    ("A-5", [("p200", _GE, 36), ("ll", _GE, 41), ("pi", _LE, 10)]),
    ("A-6", [("p200", _GE, 36), ("ll", _LE, 40), ("pi", _GE, 11)]),
    # A-7-5 when PI <= LL - 30, i.e. LL - PI >= 30; A-7-6 when PI > LL - 30.
    (
        "A-7-5",
        [("p200", _GE, 36), ("ll", _GE, 41), ("pi", _GE, 11), ("ll_pi", _GE, 30)],
    ),
    (
        "A-7-6",
        [("p200", _GE, 36), ("ll", _GE, 41), ("pi", _GE, 11), ("ll_pi", _LT, 30)],
    ),
]
_NO_GROUP_INDEX = {"A-1-a", "A-1-b", "A-2-4", "A-2-5", "A-3"}


def _column(df: pd.DataFrame, column: str) -> np.ndarray:
    if column not in df.columns:
        return np.full(len(df), np.nan)
    return numeric_column(df, column)


def _check_system(df: pd.DataFrame, system: str, columns: tuple[str, ...]) -> None:
    """Fractions must come from ``system`` (§2.6): check ``fraction_system``."""
    present = [column for column in columns if column in df.columns]
    if not present:
        return
    has_values = df[present].notna().any(axis=1).to_numpy()
    if "fraction_system" not in df.columns:
        raise ColumnError(
            f"Column 'fraction_system' not found. The fractions must follow the "
            f"{system} boundaries, and hangtu doesn't assume they do. Use "
            f'ht.analysis.gradation(curves, fractions="{system}"), or, if you '
            f"typed the fractions in from a lab report, add the column: "
            f'df["fraction_system"] = "{system}".'
        )
    named = df["fraction_system"].astype("string").str.strip()
    wrong = has_values & (named != system).fillna(True).to_numpy(dtype=bool)
    if wrong.any():
        found = ", ".join(dict.fromkeys(map(repr, df["fraction_system"][wrong][:5])))
        raise HangtuError(
            f"Rows {rows_text(df.index[wrong])} have fraction_system {found}, but "
            f"this classification needs {system} fractions. Run "
            f'ht.analysis.gradation(curves, fractions="{system}") on the curves.'
        )


def _coefficients(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Cu and Cc, from their columns or else from d10, d30 and d60."""
    uniformity = _column(df, "uniformity_coefficient")
    curvature = _column(df, "curvature_coefficient")
    d10, d30, d60 = (_column(df, f"d{p}") for p in (10, 30, 60))
    with np.errstate(divide="ignore", invalid="ignore"):
        uniformity = np.where(np.isnan(uniformity), d60 / d10, uniformity)
        curvature = np.where(np.isnan(curvature), d30**2 / (d10 * d60), curvature)
    return uniformity, curvature


def _fines_classes(df: pd.DataFrame) -> np.ndarray:
    if "plasticity_class_uscs" in df.columns:
        classes = df["plasticity_class_uscs"]
    elif "liquid_limit" in df.columns:
        classes = plasticity(df)["plasticity_class_uscs"]
    else:
        return np.full(len(df), None, dtype=object)
    return np.array(
        [value if isinstance(value, str) and value else None for value in classes],
        dtype=object,
    )


def _suffix(fines_class: str | None, dual: bool) -> str | None:
    """M or C from the fines' class (§2.6); CL-ML is C-M, or C in a dual symbol."""
    if fines_class in ("ML", "MH"):
        return "M"
    if fines_class in ("CL", "CH"):
        return "C"
    if fines_class == "CL-ML":
        return "C" if dual else "C-M"
    return None


def _symbol(
    gravel: float,
    sand: float,
    fines: float,
    fines_class: str | None,
    uniformity: float,
    curvature: float,
) -> tuple[str | None, str | None]:
    """Return (symbol, None) or (None, the reason it is blank)."""
    if fines >= 50 - SLACK:
        return (fines_class, None) if fines_class else (None, "no plasticity class")
    letter = "G" if gravel > sand else "S"
    if fines > 12 + SLACK:
        suffix = _suffix(fines_class, dual=False)
        if suffix is None:
            return None, "no plasticity class"
        if suffix == "C-M":
            return f"{letter}C-{letter}M", None
        return f"{letter}{suffix}", None
    if np.isnan(uniformity) or np.isnan(curvature):
        return None, "no Cu or Cc"
    least = 4 if letter == "G" else 6
    well = uniformity >= least - SLACK and 1 - SLACK <= curvature <= 3 + SLACK
    grading = "W" if well else "P"
    if fines < 5 - SLACK:
        return f"{letter}{grading}", None
    suffix = _suffix(fines_class, dual=True)
    if suffix is None:
        return None, "no plasticity class"
    return f"{letter}{grading}-{letter}{suffix}", None


def uscs(df: pd.DataFrame) -> pd.DataFrame:
    """Add the USCS group symbol, ``uscs_symbol`` (ASTM D2487, analysis.md §2.6).

    Returns a copy of ``df`` with ``uscs_symbol`` added: GW, GP, SW, SP, the
    dual symbols (GW-GM, SP-SC, ...), GM, GC, GC-GM, SM, SC, SC-SM, or for fine
    soils CL, CL-ML, ML, CH or MH. Group names ("lean clay with sand") aren't
    given. OL and OH are never given: they need the oven-dried liquid limit,
    so identify organic soils yourself.

    - **Fractions** are the ``astm_uscs`` ones from ``ht.analysis.gradation()``:
      ``gravel_content``, ``sand_content``, ``fines_content`` and, where
      present, ``cobbles_content`` and ``boulders_content``. USCS classifies the
      part finer than 75 mm, so the fractions are rescaled to it first.
    - **Fine-grained** (fines 50 % or more): the plasticity class from LL and PI.
    - **Coarse-grained**: G when gravel is more than sand, else S. W when Cu is
      at least 4 (gravel) or 6 (sand) and Cc is 1 to 3, else P. M or C from the
      fines' plasticity class. Fines under 5 %: GW, GP, SW, SP. Fines 5 to 12 %
      (both inclusive): dual symbols, with CL-ML fines counted as C. Over 12 %:
      GM, GC, SM, SC, or GC-GM and SC-SM for CL-ML fines.

    A symbol hangtu can't decide is left blank, counted in a warning with the
    reason, rather than guessed.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per specimen with its fractions and ``fraction_system`` (from
        ``gradation()``), Cu and Cc (or ``d10``, ``d30``, ``d60``), and its
        plasticity: ``plasticity_class_uscs``, or ``liquid_limit`` with
        ``plasticity_index`` or ``plastic_limit`` and ``non_plastic``.
        Fractions typed in from a lab report need a ``fraction_system`` column
        saying ``astm_uscs``, confirming they use the 4.75 mm and 0.075 mm
        boundaries.

    Returns
    -------
    pandas.DataFrame

    Examples
    --------
    >>> summary = ht.analysis.gradation(curves)                # fractions="astm_uscs"
    >>> soils = summary.merge(limits, on=["loca_id", "specimen_id"], how="left")
    >>> ht.analysis.uscs(soils)[["specimen_id", "uscs_symbol"]]
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    missing = [column for column in _USCS_FRACTIONS if column not in df.columns]
    if missing:
        raise ColumnError(
            f"Column{'s' if len(missing) > 1 else ''} {', '.join(map(repr, missing))} "
            "not found. USCS needs the astm_uscs fractions from "
            'ht.analysis.gradation(curves, fractions="astm_uscs"). Available '
            f"columns: {', '.join(map(str, df.columns)) or 'none'}."
        )
    _check_system(df, "astm_uscs", (*_USCS_FRACTIONS, *_OVERSIZE))
    gravel, sand, fines = (_column(df, column) for column in _USCS_FRACTIONS)
    oversize = np.nan_to_num(_column(df, "cobbles_content")) + np.nan_to_num(
        _column(df, "boulders_content")
    )
    for column in _OVERSIZE:
        if column in df.columns:
            oversize = np.where(np.isnan(_column(df, column)), np.nan, oversize)
    with np.errstate(divide="ignore", invalid="ignore"):
        scale = 100 / (100 - oversize)
    uniformity, curvature = _coefficients(df)
    fines_classes = _fines_classes(df)

    symbols: list[str | None] = []
    reasons: dict[str, int] = {}
    for i in range(len(df)):
        values = (gravel[i] * scale[i], sand[i] * scale[i], fines[i] * scale[i])
        if any(np.isnan(value) or np.isinf(value) for value in values):
            symbol, reason = None, "no fractions"
        else:
            symbol, reason = _symbol(
                *values, fines_classes[i], uniformity[i], curvature[i]
            )
        symbols.append(symbol)
        if reason:
            reasons[reason] = reasons.get(reason, 0) + 1
    if reasons:
        counts = ", ".join(
            f"{count} with {reason}" for reason, count in reasons.items()
        )
        warn(
            f"uscs_symbol is blank for {sum(reasons.values())} of {len(df)} "
            f"specimens: {counts}. A symbol that the data can't decide is left "
            "blank rather than guessed."
        )
    result = df.copy()
    result["uscs_symbol"] = np.array(symbols, dtype=object)
    return result


def _half_up(values: np.ndarray) -> np.ndarray:
    """Round to whole numbers, halves up (AASHTO M 145 limits are whole numbers)."""
    return np.floor(values + 0.5)


def _aashto_group(values: dict[str, float]) -> str | None:
    """Return the first group whose conditions all hold.

    None if a missing value could decide a group before it.
    """
    for group, conditions in _AASHTO_GROUPS:
        known = [not np.isnan(values[name]) for name, _, _ in conditions]
        fails = any(
            is_known and not compare(values[name], limit)
            for is_known, (name, compare, limit) in zip(known, conditions, strict=True)
        )
        if fails:
            continue
        return group if all(known) else None
    return None


def _group_index(group: str, fines: float, liquid: float, index: float) -> float:
    """AASHTO group index (§2.7): whole number, 0 or more."""
    if group in _NO_GROUP_INDEX:
        return 0.0
    plastic_part = 0.01 * (fines - 15) * (index - 10)
    if group in ("A-2-6", "A-2-7"):
        value = plastic_part
    else:
        value = (fines - 35) * (0.2 + 0.005 * (liquid - 40)) + plastic_part
    return float(max(_half_up(np.array(value)), 0.0))


def aashto(df: pd.DataFrame) -> pd.DataFrame:
    """Add the AASHTO group and group index (AASHTO M 145, analysis.md §2.7).

    Returns a copy of ``df`` with ``aashto_group`` (A-1-a to A-7-6) and
    ``aashto_group_index`` (a whole number, 0 or more) added.

    - **Inputs**: the percent passing 2.00, 0.425 and 0.075 mm, from the
      ``aashto`` fractions of ``ht.analysis.gradation()`` and rescaled to the
      part finer than 75 mm; LL and PI. NP counts as PI = 0, and A-3 needs NP.
    - **Rounding**: M 145's limits are whole numbers with gaps (LL 40 or less,
      41 or more), so LL, PI and the passing percentages are rounded to whole
      numbers, halves up, before they're compared.
    - **Groups** are tested left to right, and the first that fits is the group.
    - **Group index**: (F - 35)[0.2 + 0.005 (LL - 40)] + 0.01 (F - 15)(PI - 10),
      with F the passing 0.075 mm; only the PI term for A-2-6 and A-2-7; 0 for
      A-1-a, A-1-b, A-2-4, A-2-5 and A-3; never below 0.

    A group that a missing value could change is left blank, counted in a
    warning, rather than guessed.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per specimen with the ``aashto`` fractions and
        ``fraction_system`` (from ``gradation(curves, fractions="aashto")``),
        and ``liquid_limit`` with ``plasticity_index`` or ``plastic_limit``
        and ``non_plastic``.

    Returns
    -------
    pandas.DataFrame

    Examples
    --------
    >>> summary = ht.analysis.gradation(curves, fractions="aashto")
    >>> soils = summary.merge(limits, on=["loca_id", "specimen_id"], how="left")
    >>> ht.analysis.aashto(soils)[["specimen_id", "aashto_group", "aashto_group_index"]]
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    missing = [column for column in _AASHTO_FRACTIONS if column not in df.columns]
    if missing:
        raise ColumnError(
            f"Column{'s' if len(missing) > 1 else ''} {', '.join(map(repr, missing))} "
            "not found. AASHTO needs the aashto fractions from "
            'ht.analysis.gradation(curves, fractions="aashto"). Available '
            f"columns: {', '.join(map(str, df.columns)) or 'none'}."
        )
    _check_system(df, "aashto", (*_AASHTO_FRACTIONS, "boulders_content"))
    silt_clay, fine_sand, coarse_sand, _ = (
        _column(df, column) for column in _AASHTO_FRACTIONS
    )
    oversize = _column(df, "boulders_content") if "boulders_content" in df else 0.0
    with np.errstate(divide="ignore", invalid="ignore"):
        scale = 100 / (100 - oversize)
    passing_200 = silt_clay * scale
    passing_40 = passing_200 + fine_sand * scale
    passing_10 = passing_40 + coarse_sand * scale

    if "liquid_limit" in df.columns:
        limits = plasticity(df)
        liquid = numeric_column(limits, "liquid_limit")
        index = numeric_column(limits, "plasticity_index")
    else:
        liquid = index = np.full(len(df), np.nan)
    non_plastic = np.array(
        [
            flag is True
            for flag in flag_column(
                df, "non_plastic", "Leave the cell blank, or False, if it is plastic."
            )
        ],
        dtype=bool,
    )
    index = np.where(non_plastic, 0.0, index)
    rounded = {
        "p10": _half_up(passing_10),
        "p40": _half_up(passing_40),
        "p200": _half_up(passing_200),
        "ll": _half_up(liquid),
        "pi": _half_up(index),
        "np": non_plastic.astype(float),
    }
    rounded["ll_pi"] = rounded["ll"] - rounded["pi"]

    groups: list[str | None] = []
    indices: list[float] = []
    for i in range(len(df)):
        values = {name: float(column[i]) for name, column in rounded.items()}
        group = _aashto_group(values)
        groups.append(group)
        indices.append(
            np.nan
            if group is None
            else _group_index(group, values["p200"], values["ll"], values["pi"])
        )
    blank = sum(group is None for group in groups)
    if blank:
        warn(
            f"aashto_group is blank for {blank} of {len(df)} specimens: a passing "
            "percentage, LL or PI that could decide the group is missing. A "
            "group the data can't decide is left blank rather than guessed."
        )
    result = df.copy()
    result["aashto_group"] = np.array(groups, dtype=object)
    result["aashto_group_index"] = np.array(indices, dtype=float)
    return result
