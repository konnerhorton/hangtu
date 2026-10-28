"""Activity of the clay fraction (docs/work/m14b-phase-relations.md, Decision 7)."""

import numpy as np
import pandas as pd

from hangtu._data import flag_column, numeric_column
from hangtu.analysis._classification import _check_system
from hangtu.analysis._plasticity import _NOT_PLASTIC_HINT
from hangtu.errors import ColumnError, HangtuError, warn

#: The fraction system whose clay is finer than 0.002 mm.
SYSTEM = "iso14688"


def clay_activity(df: pd.DataFrame) -> pd.DataFrame:
    r"""Add the activity of the clay, its plasticity index per percent of clay.

    $$
    A = \frac{PI}{CF}
    $$

    where $PI$ is the plasticity index (%) and $CF$ the clay fraction, the
    percentage by dry mass finer than 0.002 mm. Activity separates clay
    minerals: about 0.4 for kaolinite to about 8 for sodium montmorillonite,
    with most natural soils 0.4 to 2.5 (Loehr et al. 2016, Table 4-6). Source:
    Skempton (1953), as given in Loehr et al. (2016), Geotechnical Site
    Characterization, FHWA NHI-16-072, eq. 4.16, p. 4-14.

    **Inputs:** ``plasticity_index``, ``clay_content`` and ``non_plastic``,
    with ``fraction_system`` = ``"iso14688"``, the system whose clay is finer
    than 0.002 mm (``gradation(curves, fractions="iso14688")``). A grading
    with no hydrometer stage doesn't reach 0.002 mm, so its clay content is
    blank and so is its activity.

    **Blank, counted by reason:** non-plastic rows (NP is never $A = 0$), a
    blank PI or clay content, and a clay content of 0.

    **Assumptions:** PI is measured on the fraction finer than 0.425 mm and
    the clay content on the whole sample; the ratio is used as published,
    not corrected for the coarse fraction.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per specimen with ``plasticity_index``, ``clay_content`` and
        ``fraction_system``, and optionally ``non_plastic``. Clay contents
        typed in from a lab report need a ``fraction_system`` column saying
        ``iso14688``, confirming they are the fraction finer than 0.002 mm.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``clay_activity``. No row is dropped or
        reordered.

    Raises
    ------
    HangtuError
        For a missing column, or a ``fraction_system`` other than
        ``iso14688``.

    Examples
    --------
    >>> fractions = ht.analysis.gradation(curves, fractions="iso14688")
    >>> soils = fractions.merge(limits, on=["loca_id", "specimen_id"])
    >>> ht.analysis.clay_activity(soils)[["specimen_id", "clay_activity"]]
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    missing = [c for c in ("plasticity_index", "clay_content") if c not in df.columns]
    if missing:
        raise ColumnError(
            f"df has no column {', '.join(map(repr, missing))}. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}."
        )
    _check_system(df, SYSTEM, ("clay_content",))
    index = numeric_column(df, "plasticity_index")
    clay = numeric_column(df, "clay_content")
    non_plastic = np.array(
        [flag is True for flag in flag_column(df, "non_plastic", _NOT_PLASTIC_HINT)],
        dtype=bool,
    )
    reasons = {
        "non-plastic": non_plastic,
        "no plasticity index": np.isnan(index),
        "no clay content": np.isnan(clay),
        "a clay content of 0": clay == 0,
    }
    blank = np.zeros(len(df), bool)
    counted = []
    for reason, mask in reasons.items():
        new = mask & ~blank
        blank |= mask
        if new.any():
            counted.append(f"{int(new.sum())} {reason}")
    if counted:
        warn(
            f"clay_activity is blank for rows: {'; '.join(counted)}. Activity "
            "needs a plastic specimen and its clay content finer than 0.002 mm, "
            "from a hydrometer stage."
        )
    result = df.copy()
    with np.errstate(divide="ignore", invalid="ignore"):
        result["clay_activity"] = np.where(blank, np.nan, index / clay)
    return result
