"""Hints about optional columns (docs/plots/P00-framework.md §11)."""

from collections.abc import Mapping

import pandas as pd

from ags_kit._settings import settings
from ags_kit.errors import AgsKitHint, warn


def hint_missing(df: pd.DataFrame, optional: Mapping[str, str]) -> list[str]:
    """Issue one hint listing the optional columns ``df`` lacks.

    Parameters
    ----------
    df
        The plot's data.
    optional
        ``{column: what is missing without it}``, e.g.
        ``{"geology_unit": "points are not colored by geology"}``.

    Returns
    -------
    The missing columns, whether or not a hint was shown.
    """
    missing = [column for column in optional if column not in df.columns]
    if missing and settings.hints:
        reasons = " ".join(
            f"No {column!r} column: {optional[column]}." for column in missing
        )
        warn(
            f"{reasons} (Turn hints off with ak.settings.hints = False.)",
            AgsKitHint,
        )
    return missing
