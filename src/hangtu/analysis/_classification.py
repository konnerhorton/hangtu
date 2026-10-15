"""USCS group symbols (docs/drafts/analysis.md §2.6)."""

import numpy as np
import pandas as pd

from hangtu._data import numeric_column, rows_text
from hangtu.analysis._plasticity import plasticity
from hangtu.errors import ColumnError, HangtuError, warn

#: Slack on the fines boundaries (5 % and 12 %) and the Cu and Cc limits, so a
#: value exactly on one (Cc = 0.3² / (0.1 * 0.9) = 1) isn't moved across it by
#: floating-point noise.
SLACK = 1e-9
_USCS_FRACTIONS = ("gravel_content", "sand_content", "fines_content")
_OVERSIZE = ("cobbles_content", "boulders_content")


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
