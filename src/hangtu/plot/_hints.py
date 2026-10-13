"""Hints about optional columns (docs/plots/P00-framework.md §11)."""

from collections.abc import Mapping

import pandas as pd

from hangtu._settings import settings
from hangtu.errors import HangtuHint, warn


def hint_missing(
    df: pd.DataFrame,
    optional: Mapping[str, str],
    missing: Mapping[str, str] | None = None,
) -> list[str]:
    """Issue one hint listing the optional columns ``df`` lacks.

    Parameters
    ----------
    df
        The plot's data.
    optional
        ``{column: what is missing without it}``, e.g.
        ``{"geology_unit": "points are not colored by geology"}``.
    missing
        ``{column: what is missing without it}`` for columns the caller has
        already found missing, e.g. in the data before an analysis added
        them. Listed after ``optional``'s.

    Returns
    -------
    The missing columns, whether or not a hint was shown.
    """
    reasons_by_column = {
        column: reason
        for column, reason in optional.items()
        if column not in df.columns
    }
    reasons_by_column.update(missing or {})
    if reasons_by_column and settings.hints:
        reasons = " ".join(
            f"No {column!r} column: {reason}."
            for column, reason in reasons_by_column.items()
        )
        warn(
            f"{reasons} (Turn hints off with ht.settings.hints = False.)",
            HangtuHint,
        )
    return list(reasons_by_column)
