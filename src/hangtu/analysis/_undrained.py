"""Undrained shear strength from each test's result (datasets.md §6.11; M17 a)."""

from collections.abc import Mapping

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu.errors import HangtuError, warn

#: The inputs to s_u, in the order the output's unit is taken from, with the
#: factor applied and the basis recorded (docs/work/m17a-strength-data.md,
#: Decision 3). The hand penetrometer's factor depends on its scale.
INPUTS = {
    "deviator_stress_at_failure": (0.5, "half_deviator_stress"),
    "unconfined_compressive_strength": (0.5, "half_unconfined_compressive_strength"),
    "hand_penetrometer_reading": (None, None),
    "undrained_shear_strength": (1.0, "as_reported"),
}
SCALES = {
    "unconfined_compressive_strength": (0.5, "half_hand_penetrometer_reading"),
    "undrained_shear_strength": (1.0, "hand_penetrometer_reading"),
}
#: Bases the function writes itself; a row with one of these has its s_u
#: computed again, so a second call gives the same result.
COMPUTED = frozenset(
    basis for _, basis in [*INPUTS.values(), *SCALES.values()] if basis
) - {"as_reported"}
STRESSES = (*INPUTS, "remolded_undrained_shear_strength")
FLAGGED = ("<", ">")


def undrained_shear_strength_from_tests(
    df: pd.DataFrame,
    *,
    hand_penetrometer_scale: str | None = None,
    units: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    r"""Give each test result's undrained shear strength $s_u$, and its sensitivity.

    Each row has one input, and $s_u$ follows from it, with
    ``undrained_shear_strength_basis`` saying how:

    - ``deviator_stress_at_failure`` (UU triaxial): $s_u = q_f / 2$,
      ``half_deviator_stress``;
    - ``unconfined_compressive_strength``: $s_u = q_u / 2$,
      ``half_unconfined_compressive_strength``;
    - ``hand_penetrometer_reading``: half the reading with the scale
      ``"unconfined_compressive_strength"`` (``half_hand_penetrometer_reading``),
      the reading with ``"undrained_shear_strength"``
      (``hand_penetrometer_reading``);
    - ``undrained_shear_strength`` alone (vanes, fall cone): as given,
      ``as_reported``.

    **Why q / 2.** In total stress with $\phi_u = 0$ the failure envelope is
    the horizontal line $\tau = s_u$. It touches each Mohr circle, of center
    $s$ and radius $t = (\sigma_1 - \sigma_3)/2$, at its top, so
    $s_u = t = q_f / 2$ at any cell pressure; unconfined compression is the
    case $\sigma_3 = 0$, $s_u = q_u / 2$. This is a derivation, not a
    correlation, so it has no coefficient and no source to cite.

    **Sensitivity** $S_t = s_u / s_{u,r}$, ``strength_sensitivity``, is given
    where a row has both its peak and its remolded strength
    (``remolded_undrained_shear_strength``: vanes, fall cone), neither of them
    a bound (``qualifier``, ``remolded_qualifier``), and $s_{u,r} > 0$.
    Otherwise it is blank, and one warning counts the rows; both values stay.

    **Valid for:** saturated, intact specimens tested undrained. Each test
    measures its own $s_u$ (mode, rate, specimen size), so the rows keep their
    ``test_type`` and aren't combined or converted between tests here. Field
    vane values are as measured: Bjerrum's correction $\mu$ is a judgment,
    applied in selection, not here. **Judgments taken:** none.

    **Assumptions:** the lab's values are read as given (the deviator stress
    corrected for area change and membrane by the lab). A bound (``>200``)
    stays a bound: ``qualifier`` is the input's and so applies to $s_u$.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per test result, as ``ht.template("strength")`` or
        ``p.undrained_strength()``: one of the inputs above on each row, and
        ``remolded_undrained_shear_strength`` where the test gives one, each
        stress with its unit declared. A row whose
        ``undrained_shear_strength_basis`` is one this function writes has its
        $s_u$ computed again, so a second call changes nothing.
    hand_penetrometer_scale : str, optional
        ``"undrained_shear_strength"`` or ``"unconfined_compressive_strength"``:
        what the hand penetrometer read, which instruments differ in by a factor
        of 2. Required when a row has ``hand_penetrometer_reading``; there is no
        default.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``undrained_shear_strength``,
        ``undrained_shear_strength_basis`` and ``strength_sensitivity``. $s_u$ is
        in ``undrained_shear_strength``'s declared unit, else the first input's
        in the table's order. No row is dropped or reordered.

    Raises
    ------
    HangtuError
        For a row with more than one input, an input of 0 or less, a hand
        penetrometer reading without ``hand_penetrometer_scale=``, each naming
        the rows; for a stress without units or in a unit that isn't a stress.

    Examples
    --------
    ``p.undrained_strength()`` calls it already. On results typed into the
    template:

    >>> tests = ht.read_csv(
    ...     "strength.csv",
    ...     units={
    ...         "deviator_stress_at_failure": "kPa",
    ...         "undrained_shear_strength": "kPa",
    ...     },
    ... )
    >>> su = ht.analysis.undrained_shear_strength_from_tests(tests)
    >>> su[["test_type", "undrained_shear_strength", "undrained_shear_strength_basis"]]
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if hand_penetrometer_scale is not None and hand_penetrometer_scale not in SCALES:
        raise HangtuError(
            f"hand_penetrometer_scale={hand_penetrometer_scale!r} isn't one of "
            f"{', '.join(map(repr, SCALES))}. Say what the instrument read: check "
            "its scale, or IPEN_METH and IPEN_REM in an AGS file."
        )
    raw = {
        column: numeric_column(df, column) if column in df.columns else None
        for column in STRESSES
    }
    if raw["undrained_shear_strength"] is not None:
        # s_u this function wrote before is computed again, not read as an input.
        basis = df.get("undrained_shear_strength_basis")
        if basis is not None:
            own = basis.astype(object).isin(COMPUTED).to_numpy()
            raw["undrained_shear_strength"] = np.where(
                own, np.nan, raw["undrained_shear_strength"]
            )
    given = [c for c in STRESSES if (v := raw[c]) is not None and not np.isnan(v).all()]
    declared = _units.resolve_units(df, given, units, analysis=True) if given else {}
    known = {**_units.units_of(df), **(units or {}), **declared}
    # s_u in its own declared unit, else in the first input's (Decision 3).
    order = ["undrained_shear_strength", *(c for c in INPUTS if c in given)]
    target_column = next((c for c in order if c in known), None)
    target = known.get(target_column) if target_column else None

    def values(column: str) -> np.ndarray:
        if column not in given or target is None:
            return np.full(len(df), np.nan)
        unit = _units.parse_unit(declared[column], column)
        _units.check_dimension(unit, "stress", column)
        return _units.convert(
            raw[column], unit, "stress", _units.parse_unit(target, target_column)
        )

    inputs = {column: values(column) for column in INPUTS}
    present = np.column_stack([~np.isnan(v) for v in inputs.values()])
    several = present.sum(axis=1) > 1
    if several.any():
        names = [c for c, v in inputs.items() if (~np.isnan(v) & several).any()]
        raise HangtuError(
            f"Rows {rows_text(df.index[several])} have more than one input to s_u "
            f"({', '.join(names)}). Give one per row: a lab's own s_u beside q_f "
            "goes in reported_undrained_shear_strength."
        )
    for column, column_values in inputs.items():
        not_positive = column_values <= 0
        if not_positive.any():
            raise HangtuError(
                f"Rows {rows_text(df.index[not_positive])} have a {column} of 0 or "
                "less, which can't be a strength. Check the values and their sign "
                "(in an AGS file, p.qc() lists them as X003 or Q003)."
            )
    reading = ~np.isnan(inputs["hand_penetrometer_reading"])
    if reading.any() and hand_penetrometer_scale is None:
        raise HangtuError(
            f"Rows {rows_text(df.index[reading])} have a hand_penetrometer_reading, "
            "and instruments read either s_u or q_u, a factor of 2 apart. Say which "
            'with hand_penetrometer_scale="undrained_shear_strength" or '
            '"unconfined_compressive_strength".'
        )

    strength = np.full(len(df), np.nan)
    basis = np.full(len(df), None, dtype=object)
    for column, (factor, name) in INPUTS.items():
        if column == "hand_penetrometer_reading":
            if hand_penetrometer_scale is None:
                continue
            factor, name = SCALES[hand_penetrometer_scale]
        has = ~np.isnan(inputs[column])
        strength[has] = inputs[column][has] * factor
        basis[has] = name

    remolded = values("remolded_undrained_shear_strength")
    pair = ~np.isnan(strength) & ~np.isnan(remolded)
    bound = _flagged(df, "qualifier") | _flagged(df, "remolded_qualifier")
    usable = pair & ~bound & (remolded > 0)
    sensitivity = np.full(len(df), np.nan)
    sensitivity[usable] = strength[usable] / remolded[usable]
    blank = int((pair & ~usable).sum())
    if blank:
        warn(
            f"strength_sensitivity left blank on {blank} "
            f"row{'s' if blank > 1 else ''}: "
            "a peak or remolded value beyond the instrument's range (a '<' or '>' "
            "qualifier), or a remolded strength of 0. Both values stay on the row."
        )

    result = df.copy()
    result["undrained_shear_strength"] = strength
    result["undrained_shear_strength_basis"] = basis
    result["strength_sensitivity"] = sensitivity
    result.attrs["units"] = {**_units.units_of(df), **(units or {})}
    if target:
        result.attrs["units"]["undrained_shear_strength"] = target
    return result


def _flagged(df: pd.DataFrame, column: str) -> np.ndarray:
    """Return True where ``column`` holds a ``<`` or ``>`` qualifier."""
    if column not in df.columns:
        return np.zeros(len(df), bool)
    text = df[column].astype("string").str.strip()
    return text.isin(FLAGGED).fillna(False).to_numpy(bool)
