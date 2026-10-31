"""Triaxial stresses at failure (datasets.md §6.10; M11 a)."""

from collections.abc import Mapping

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu.errors import ColumnError, HangtuError, warn

#: The AGS pick lists ``TREG_TYPE`` and ``TRIG_TYPE`` (4.2, and 4.0.4's
#: ``UNC``), by what a rule needs to know of a test. A type the lists don't
#: have is none of these.
DRAINED = frozenset({"CD", "CDM", "CIDC", "CADC"})
UNDRAINED = frozenset({"CU", "CUM", "CIUC", "CIUCM", "CAUC", "CAUE", "UUP"})
EXTENSION = frozenset({"CIDE", "CADE", "CAUE"})
MULTISTAGE = frozenset({"CDM", "CUM", "CIUCM", "UUM"})
#: Every type in the two pick lists: ``TREG_TYPE``'s, then ``TRIG_TYPE``'s.
LISTED = DRAINED | UNDRAINED | EXTENSION | {"UU", "UUM", "UNC"}

REQUIRED = ("test_type", "cell_pressure", "deviator_stress_at_failure")
#: The stresses read where present, besides the cell pressure and deviator stress.
OPTIONAL = ("pore_pressure_at_failure", "back_pressure")
STRESS_COLUMNS = (
    "minor_principal_stress_at_failure",
    "major_principal_stress_at_failure",
    "effective_minor_principal_stress_at_failure",
    "effective_major_principal_stress_at_failure",
)


def triaxial_failure_stresses(
    df: pd.DataFrame, *, units: Mapping[str, str] | None = None
) -> pd.DataFrame:
    r"""Add the principal stresses at failure of each triaxial stage.

    In triaxial compression the cell pressure is the minor principal stress
    and the deviator stress at failure $q_f$ is added to it axially; the
    effective stresses take off the pore pressure at failure $u_f$:

    $$
    \sigma_3 = \sigma_{cell}, \qquad \sigma_1 = \sigma_3 + q_f, \qquad
    \sigma'_3 = \sigma_3 - u_f, \qquad \sigma'_1 = \sigma'_3 + q_f
    $$

    These are definitions (effective stress, $\sigma' = \sigma - u$), used
    without a correlation or coefficient.

    **The pore pressure at failure** $u_f$ is ``pore_pressure_at_failure``,
    the total pore pressure with the back pressure in it (AGS ``TRET_PWPF``).
    Where it is blank and the test is drained (``CD``, ``CDM``, ``CIDC``,
    ``CADC``), $u_f$ is ``back_pressure``: a drained test holds the pore
    pressure at the back pressure. One warning counts those rows, and
    ``effective_stress_basis`` says which was used on each row. Otherwise,
    as in an undrained test without a pore pressure or a total-stress test
    (``UU``), the effective stresses are blank: nothing is guessed.

    **Extension tests** (``CIDE``, ``CADE``, ``CAUE``) get blank principal
    stresses, with a warning naming the rows: the AGS dictionary gives no sign
    for the deviator stress in extension, where the axial stress is the minor
    one, so the compression formulas would be wrong. Any other type,
    including a blank one, is read as compression.

    **Valid for:** triaxial compression at failure, effective-stress stages
    (``CU``, ``CD`` and their variants) and total-stress ones (``UU``). Blank
    cells give blank stresses; nothing is clipped. **Judgments taken:** none.

    **Assumptions:** the values are the lab's, read as given: the deviator
    stress already corrected for area change and membrane, and the cell and
    pore pressures measured at failure, by the lab's failure criterion
    (``failure_criterion``, which this doesn't check).

    Parameters
    ----------
    df : pandas.DataFrame
        One row per stage, as ``ht.template("triaxial")`` or ``p.triaxial()``:
        ``test_type`` (the AGS ``TREG_TYPE`` or ``TRIG_TYPE`` code),
        ``cell_pressure`` and ``deviator_stress_at_failure``, and where known
        ``pore_pressure_at_failure`` and ``back_pressure``, each stress with its
        unit declared.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``minor_principal_stress_at_failure``,
        ``major_principal_stress_at_failure``,
        ``effective_minor_principal_stress_at_failure``,
        ``effective_major_principal_stress_at_failure`` and
        ``effective_stress_basis`` (``pore_pressure_at_failure``,
        ``back_pressure`` or blank). The stresses are in ``cell_pressure``'s
        unit. No row is dropped or reordered.

    Raises
    ------
    HangtuError
        For a missing column, a deviator stress of 0 or less in a compression
        test (naming the rows), or a stress column without units or in a unit
        that isn't a stress.

    Examples
    --------
    ``p.triaxial()`` calls it already. On stages typed into the template:

    >>> stages = ht.read_csv(
    ...     "triaxial.csv",
    ...     units={
    ...         "cell_pressure": "kPa",
    ...         "back_pressure": "kPa",
    ...         "deviator_stress_at_failure": "kPa",
    ...         "pore_pressure_at_failure": "kPa",
    ...     },
    ... )
    >>> stresses = ht.analysis.triaxial_failure_stresses(stages)
    >>> stresses[["test_stage", "effective_minor_principal_stress_at_failure"]]
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    missing = [column for column in REQUIRED if column not in df.columns]
    if missing:
        raise ColumnError(
            f"df has no column {', '.join(map(repr, missing))}. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}. A triaxial stage needs "
            "its test type, cell pressure and deviator stress at failure; "
            'ht.template("triaxial") has the columns.'
        )
    present = [column for column in OPTIONAL if column in df.columns]
    stresses = ["cell_pressure", "deviator_stress_at_failure", *present]
    declared = _units.resolve_units(df, stresses, units, analysis=True)
    parsed = {
        column: _units.parse_unit(declared[column], column) for column in stresses
    }
    for column, unit in parsed.items():
        _units.check_dimension(unit, "stress", column)
    to = parsed["cell_pressure"]

    def values(column: str) -> np.ndarray:
        if column not in parsed:
            return np.full(len(df), np.nan)
        return _units.convert(numeric_column(df, column), parsed[column], "stress", to)

    types = df["test_type"].astype(object).where(df["test_type"].notna(), None)
    extension = types.isin(EXTENSION).to_numpy()
    cell = values("cell_pressure")
    deviator = values("deviator_stress_at_failure")
    not_positive = ~extension & (deviator <= 0)
    if not_positive.any():
        raise HangtuError(
            f"Rows {rows_text(df.index[not_positive])} have a "
            "deviator_stress_at_failure of 0 or less in a compression test, which "
            "can't be a failure state. Check the values and their sign (in an AGS "
            "file, p.qc() lists them as X003)."
        )
    pore = values("pore_pressure_at_failure")
    back = values("back_pressure")
    from_back = np.isnan(pore) & types.isin(DRAINED).to_numpy() & ~np.isnan(back)
    pore = np.where(from_back, back, pore)
    basis = np.where(
        from_back,
        "back_pressure",
        np.where(np.isnan(pore), None, "pore_pressure_at_failure"),
    ).astype(object)

    minor = np.where(extension, np.nan, cell)
    major = minor + deviator
    effective_minor = minor - pore
    effective_major = effective_minor + deviator
    basis[extension | np.isnan(effective_minor)] = None
    if extension.any():
        named = ", ".join(dict.fromkeys(types[extension]))
        warn(
            f"Rows {rows_text(df.index[extension])} are extension tests ({named}), "
            "so their principal stresses are blank: the deviator stress has no "
            "agreed sign in extension, where the axial stress is the minor one."
        )
    used = int((from_back & ~extension).sum())
    if used:
        warn(
            f"{used} drained stage{'s' if used > 1 else ''} had no "
            "pore_pressure_at_failure, so the back_pressure was used: a drained "
            "test holds the pore pressure at the back pressure. "
            "effective_stress_basis says which was used."
        )

    result = df.copy()
    for column, column_values in zip(
        STRESS_COLUMNS,
        (minor, major, effective_minor, effective_major),
        strict=True,
    ):
        result[column] = column_values
    result["effective_stress_basis"] = basis
    result.attrs["units"] = {
        **_units.units_of(df),
        **(units or {}),
        **dict.fromkeys(STRESS_COLUMNS, declared["cell_pressure"]),
    }
    return result
