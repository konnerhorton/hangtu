"""Oedometer load branches (datasets.md §6.14; M19 a)."""

import numpy as np
import pandas as pd

from hangtu._data import numeric_column
from hangtu.errors import ColumnError, HangtuError

REQUIRED = ("specimen_id", "applied_vertical_stress")

LOADING = "loading"
UNLOADING = "unloading"
RELOADING = "reloading"
CONSTANT_STRESS = "constant_stress"


def oedometer_load_branch(df: pd.DataFrame) -> pd.DataFrame:
    r"""Mark each oedometer increment as loading, unloading or reloading.

    The preconsolidation stress and the compression index come from the
    loading branch of the curve, the swelling index and the unload-reload
    modulus from an unload-reload loop, so each increment says which branch
    it is on. Per specimen, in row order, each ``applied_vertical_stress``
    is compared with the previous increment's and with the largest before it:

    - ``loading``: the first increment, or a stress above every earlier one;
    - ``unloading``: a stress below the previous one;
    - ``reloading``: a stress above the previous one but not above the
      largest so far. Equal to the largest counts as reloading: the curve has
      only just come back to it;
    - ``constant_stress``: a stress equal to the previous one, as when the
      specimen is flooded or held at one stress for creep.

    A blank stress gives a blank branch, and the next increment is compared
    with the last stress given. A specimen with no increments (a single row
    with a blank stress) has a blank branch.

    The rule reads only the order of the stresses, so it needs no units: a
    file in kPa and its twin in psf give the same branches. **Valid for:**
    incremental-load oedometer tests whose rows are in the order the
    increments were applied. **Judgments taken:** none.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per increment, as ``ht.template("oedometer")`` or
        ``p.oedometer()``: ``specimen_id`` and ``applied_vertical_stress``
        (the stress at the end of each increment), in test order.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``load_branch`` added (or replaced). No row is
        dropped or reordered.

    Raises
    ------
    ColumnError
        For a missing column, or a stress that isn't a number.

    Examples
    --------
    ``p.oedometer()`` calls it already. On increments typed into the
    template:

    >>> increments = ht.read_csv(
    ...     "oedometer.csv", units={"applied_vertical_stress": "kPa"}
    ... )
    >>> increments = ht.analysis.oedometer_load_branch(increments)
    >>> increments[["test_stage", "applied_vertical_stress", "load_branch"]]
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    missing = [column for column in REQUIRED if column not in df.columns]
    if missing:
        raise ColumnError(
            f"df has no column {', '.join(map(repr, missing))}. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}. An oedometer increment "
            "needs its specimen and the applied vertical stress; "
            'ht.template("oedometer") has the columns.'
        )
    stress = numeric_column(df, "applied_vertical_stress")
    specimen = df["specimen_id"].to_numpy(dtype=object)
    branch = np.full(len(df), None, dtype=object)
    previous: dict[object, tuple[float, float]] = {}
    for row, (key, value) in enumerate(zip(specimen, stress, strict=True)):
        if np.isnan(value):
            continue
        key = None if pd.isna(key) else key
        if key not in previous:
            branch[row] = LOADING
            previous[key] = (value, value)
            continue
        last, largest = previous[key]
        if value > largest:
            branch[row] = LOADING
        elif value < last:
            branch[row] = UNLOADING
        elif value > last:
            branch[row] = RELOADING
        else:
            branch[row] = CONSTANT_STRESS
        previous[key] = (value, max(largest, value))
    result = df.copy()
    result["load_branch"] = pd.Series(branch, index=df.index, dtype=object)
    return result
