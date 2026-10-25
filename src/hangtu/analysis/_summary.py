"""A small summary by group (docs/work/m13b2-spt-strength-history.md, Decision 12).

To inform a judgment such as a unit's PI. SPEC §5's ``describe`` (M15) is the
full version and may replace this.
"""

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu.errors import ColumnError

STATISTICS = ("n", "median", "min", "max")


def summary_by(
    df: pd.DataFrame, value: str, *, by: str = "geology_unit"
) -> pd.DataFrame:
    """Count, median, minimum and maximum of a column for each group.

    Shows what the tests say before you set a judgment, such as each geology
    unit's plasticity index for ``ht.analysis.add_judgment()``. It never
    writes a judgment: the value to use is yours.

    Blank cells and text (``NP``, ``dry``) are not counted, so ``n`` is the
    number of numbers. A group with none still has a row, with ``n`` 0. Rows
    with a blank group are summarized as ``"(blank)"``, last.

    Parameters
    ----------
    df : pandas.DataFrame
        Any dataset with ``value`` and ``by``, e.g. ``p.atterberg()``.
    value : str
        The column to summarize, e.g. ``"plasticity_index"``.
    by : str
        The column to group by.

    Returns
    -------
    pandas.DataFrame
        One row per group, sorted by name: ``by``, ``n``, ``median``, ``min``
        and ``max``. ``attrs["units"]`` gives the unit of the last three, the
        value's unit, when ``df`` declares it.

    Examples
    --------
    >>> ht.analysis.summary_by(p.atterberg(), "plasticity_index")
       geology_unit   n  median   min   max
    0      Alluvium   9    28.0  14.0  41.0
    1    Lacustrine   6    36.5  30.0  52.0
    """
    missing = [column for column in (value, by) if column not in df.columns]
    if missing:
        raise ColumnError(
            f"summary_by() needs the columns {', '.join(map(repr, missing))}, which "
            f"df doesn't have. Available columns: {', '.join(map(str, df.columns))}."
        )
    numbers = pd.to_numeric(df[value], errors="coerce")
    groups = df[by].astype(object).where(df[by].notna(), "(blank)")
    rows = []
    names = sorted({str(g) for g in groups if g != "(blank)"})
    if (groups == "(blank)").any():
        names.append("(blank)")
    for name in names:
        these = numbers[groups.astype(str) == name].dropna()
        rows.append(
            {
                by: name,
                "n": len(these),
                "median": these.median() if len(these) else np.nan,
                "min": these.min() if len(these) else np.nan,
                "max": these.max() if len(these) else np.nan,
            }
        )
    result = pd.DataFrame(rows, columns=[by, *STATISTICS])
    unit = _units.units_of(df).get(value)
    result.attrs["units"] = {} if unit is None else dict.fromkeys(STATISTICS[1:], unit)
    return result
