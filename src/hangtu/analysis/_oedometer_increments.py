"""Per increment: m_v, Eoed, Eur,oed and k (docs/analysis/compressibility.md §8)."""

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu._settings import settings
from hangtu.analysis._oedometer import (
    CONSTANT_STRESS,
    LOADING,
    RELOADING,
    UNLOADING,
    branches,
    in_situ,
    oedometer_load_branch,
    one_value,
    specimen_label,
    stresses,
)
from hangtu.errors import ColumnError, HangtuError
from hangtu.stats._rows import group_keys

_FUNCTION = "oedometer_increments()"
_STRESS = "applied_vertical_stress"
_START = "void_ratio_at_increment_start"
_END = "void_ratio_at_increment_end"
_IN_SITU = "effective_vertical_stress"
_REQUIRED = ("specimen_id", _STRESS, _END)
_TEMPLATE = 'ht.template("oedometer") has the columns it reads.'

STRESS_AT_START = "applied_vertical_stress_at_increment_start"
VOLUME_COMPRESSIBILITY = "coefficient_of_volume_compressibility"
CONSTRAINED_MODULUS = "constrained_modulus"
UNLOAD_RELOAD_MODULUS = "unload_reload_constrained_modulus"
SPANS = "spans_effective_vertical_stress"
#: Each k column and the lab's c_v it comes from.
_REPORTED = "reported_coefficient_of_consolidation"
CONDUCTIVITY = {
    "hydraulic_conductivity_root_time": f"{_REPORTED}_root_time",
    "hydraulic_conductivity_log_time": f"{_REPORTED}_log_time",
}

#: The reasons a value is blank, worded as the result gives them.
FIRST_INCREMENT = "first increment: its start stress isn't given"
NO_STRESS = "no stress"
NO_PREVIOUS_STRESS = "the previous increment has no stress"
NO_STRESS_CHANGE = "no stress change"
NO_START_VOID_RATIO = "no void ratio at the increment's start"
NO_END_VOID_RATIO = "no void ratio at the increment's end"
NOT_POSITIVE = "m_v is not positive"
NO_BRANCH = "no load branch"
CONSTANT = "constant stress increment"
NO_CONSOLIDATION = "no c_v reported"
CONSOLIDATION_NOT_POSITIVE = "c_v is not positive"

#: The specimen's identifiers, read for its name in messages.
_IDENTIFIERS = ("specimen_id", "sample_reference", "specimen_reference")
#: Canonical units the values are computed in (1/kPa is 1000 m²/MN).
_KPA = "kPa"
_VOLUME_UNIT = "m2/MN"
_CONDUCTIVITY_UNIT = "m/s"


def oedometer_increments(
    df: pd.DataFrame,
    *,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Recompute m_v over each oedometer increment, with Eoed, Eur,oed and k.

    **The coefficient of volume compressibility** over an increment is the
    void-ratio form of BS 1377-5:1990, 3.6.2.2.4, which gives
    $m_v = \frac{H_1 - H_2}{H_1}\frac{1}{p_2 - p_1}$ "for each loading
    increment", $H_1$ the specimen's height at the start of the increment
    and $H_2$ at its end. With $H = H_s(1 + e)$,

    $$
    m_v = \frac{e_1 - e_2}{(1 + e_1)(\sigma'_2 - \sigma'_1)}
    $$

    with $e_1$ and $\sigma'_1$ at the increment's start and $e_2$ and
    $\sigma'_2$ at its end: the void ratio at the start of the increment,
    not the specimen's initial $e_0$. Per ``specimen_id``, in row order,
    $\sigma'_2$ is the row's ``applied_vertical_stress`` and $\sigma'_1$ the
    previous row's, written to ``applied_vertical_stress_at_increment_start``.
    $e_1$ is the row's ``void_ratio_at_increment_start``, else the previous
    row's ``void_ratio_at_increment_end`` (with a note naming the rows), and
    $e_2$ the row's ``void_ratio_at_increment_end``. The lab's own value
    stays in ``reported_coefficient_of_volume_compressibility``, apart.

    **Unloading and reloading increments** use the same equation: $\Delta e$
    and $\Delta\sigma'$ are both negative on an unload, so $m_v$ is
    positive. BS 1377-5 defines $m_v$ on loading increments only, so the
    unload and reload values, and the moduli and $k$ from them, are an
    extension of it.

    **The constrained modulus** is $E_{oed} = 1/m_v$ on ``loading`` rows
    (``constrained_modulus``) and $E_{ur,oed} = 1/m_v$ on ``unloading`` and
    ``reloading`` rows (``unload_reload_constrained_modulus``); each is
    blank on the other's rows, and both on ``constant_stress`` rows. Each
    is a secant over its increment, as $m_v$ is, so no single stress is
    chosen to report it at: the row gives $\sigma'_1$ and $\sigma'_2$. An
    increment's branch is read from ``load_branch``, else added by
    ``ht.analysis.oedometer_load_branch()`` with a note.

    **At the in situ stress.** Where the rows give the specimen's
    ``effective_vertical_stress`` $\sigma'_{v0}$ (from
    ``ht.analysis.vertical_stress()``), ``spans_effective_vertical_stress``
    is True on the first ``loading`` row with
    $\sigma'_1 < \sigma'_{v0} \le \sigma'_2$, and on the first ``unloading``
    or ``reloading`` row whose range of $\sigma'_1$ and $\sigma'_2$ holds
    $\sigma'_{v0}$ (above the lower, up to the higher); False on the rest.
    That increment's value is the one at $\sigma'_{v0}$: values of two
    increments are never interpolated, since each is a secant over its own
    range. In an overconsolidated specimen the loading increment at
    $\sigma'_{v0}$ is on recompression, so its $E_{oed}$ is stiffer than
    the virgin branch's. A $\sigma'_{v0}$ no increment spans gives all
    False and a note naming the specimens: nothing is extrapolated.
    Without the column, or with it blank, the flag is blank.

    **The hydraulic conductivity** over an increment follows from
    Terzaghi's coefficient of consolidation, $c_v = k/(m_v\gamma_w)$
    (Freeze & Cherry 1979, Eq. 8.22, there with the hydraulic conductivity
    $K'$, the vertical compressibility $\alpha'$ for $m_v$ and $\rho g$ for
    $\gamma_w$), rearranged:

    $$
    k = c_v\, m_v\, \gamma_w
    $$

    with $c_v$ the lab's (``reported_coefficient_of_consolidation_root_time``
    and ``reported_coefficient_of_consolidation_log_time``, each giving its
    own column, ``hydraulic_conductivity_root_time`` and
    ``hydraulic_conductivity_log_time``, so neither method is preferred),
    $m_v$ the recomputed one, and $\gamma_w$
    ``ht.settings.water_unit_weight`` (9.81 kN/m³ by default), recorded in
    ``attrs["oedometer_increments"]``. The units are converted exactly, with
    a year of 365.25 days. The relation holds for one-dimensional
    consolidation of a saturated soil, with the compressibility of the pore
    water neglected beside the soil's, as it is for clays. A $k$ from an
    oedometer is a vertical $k$ of a small specimen, which can miss the
    fabric (laminations, fissures, root holes) that drains the soil in situ
    (BS 1377-5:1990, 3.1.1, note 3), so it is usually below the field value:
    a check on other measurements, not a design value on its own. Unload and
    reload values are an extension, as their $m_v$ is. It is blank with
    ``"no c_v reported"`` or ``"c_v is not positive"``, else with $m_v$'s
    reason or ``"m_v is not positive"``, in its ``_reason`` column.

    **When an increment gives no value,** it is blank with the first
    reason that applies, in ``coefficient_of_volume_compressibility_reason``:

    - ``"no stress"``: the row's stress is blank;
    - ``"first increment: its start stress isn't given"``: a specimen's
      first row starts from the seating load, which the file doesn't give;
    - ``"the previous increment has no stress"``;
    - ``"no stress change"``: $\sigma'_2 = \sigma'_1$, as when the specimen
      is flooded or held for creep;
    - ``"no void ratio at the increment's start"``,
      ``"no void ratio at the increment's end"``.

    An $m_v$ of 0 or less (the void ratio moved against the stress change)
    is kept as computed. The moduli are blank where $m_v$ is, with its
    reason, and with ``"m_v is not positive"``, ``"constant stress
    increment"`` or ``"no load branch"`` in ``constrained_modulus_reason``.

    **Valid for:** incremental-load oedometer tests, rows in the order the
    increments were applied, void ratios as the lab reports them at each
    increment's start and end. **Assumptions:** one-dimensional compression;
    for $k$, a saturated specimen and the lab's $c_v$ as reported.
    **Judgments taken:** none ($\gamma_w$ is a setting).

    Sources: BS 1377-5:1990, Methods of test for soils for civil engineering
    purposes, Part 5: Compressibility, permeability and durability tests,
    3.6.2.2.4 and 3.1.1, note 3. Freeze, R.A. & Cherry, J.A. (1979).
    *Groundwater*. Prentice-Hall, §8.3, Eq. (8.22), after Terzaghi (1925).

    Parameters
    ----------
    df : pandas.DataFrame
        One row per increment, as ``p.oedometer()`` gives (or a CSV in
        ``ht.template("oedometer")``'s shape): ``specimen_id``,
        ``applied_vertical_stress`` and ``void_ratio_at_increment_end``, in
        the order the increments were applied.
        ``void_ratio_at_increment_start``, ``load_branch``,
        ``effective_vertical_stress`` (one value per specimen) and the two
        ``reported_coefficient_of_consolidation_`` columns are read where
        present.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.
    display_units : {"SI", "US"}, optional
        Write the stresses in kPa or psf, $m_v$ in m²/MN or ft²/kip, the
        moduli in MPa or ksf and $k$ in m/s or cm/s (or the units the
        settings' display overrides name); ``applied_vertical_stress`` is
        converted too, so a row's two stresses share a unit. None keeps the
        stresses in ``applied_vertical_stress``'s unit and writes $m_v$ in
        m²/MN, the moduli in kPa and $k$ in m/s.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df``, no row dropped or reordered, with
        ``applied_vertical_stress_at_increment_start``,
        ``coefficient_of_volume_compressibility``, ``constrained_modulus``,
        the two ``hydraulic_conductivity_`` columns,
        ``unload_reload_constrained_modulus``,
        ``spans_effective_vertical_stress`` and the ``_reason`` columns
        added (or replaced), ``load_branch`` where it was missing, and
        ``attrs["units"]`` naming each unit. ``attrs["oedometer_increments"]``
        holds the notes and the water unit weight.

    Raises
    ------
    HangtuError
        For a frame without ``specimen_id``, ``applied_vertical_stress`` or
        ``void_ratio_at_increment_end``, a row with a blank ``specimen_id``,
        a specimen with more than one ``effective_vertical_stress``, a
        ``load_branch`` value it doesn't know, a stress column without units
        or in a unit that isn't a stress, or a ``display_units`` other than
        "SI", "US" or None.

    Examples
    --------
    Each oedometer increment's m_v beside the lab's, and its modulus:

    >>> p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
    >>> increments = ht.analysis.oedometer_increments(p.oedometer())
    >>> increments[
    ...     [
    ...         "specimen_id",
    ...         "applied_vertical_stress",
    ...         "coefficient_of_volume_compressibility",
    ...         "reported_coefficient_of_volume_compressibility",
    ...         "constrained_modulus",
    ...     ]
    ... ]
    """
    _check(df, display_units)
    notes: list[str] = []
    if "load_branch" not in df.columns:
        df = oedometer_load_branch(df)
        notes.append(
            "load_branch added by ht.analysis.oedometer_load_branch(), reading the "
            "rows in the order the increments were applied."
        )
    branch = branches(df, _FUNCTION)
    stress, unit = stresses(df, units, display_units)
    stress_kpa = _in_kpa(stress, unit)
    end = numeric_column(df, _END)
    start = (
        numeric_column(df, _START) if _START in df.columns else np.full(len(df), np.nan)
    )
    in_situ_stress = in_situ(df, units, display_units, unit)

    n = len(df)
    at_start = np.full(n, np.nan)
    compressibility = np.full(n, np.nan)  # 1/kPa
    reason = np.full(n, None, dtype=object)
    borrowed: list[int] = []
    spans = np.full(n, None, dtype=object)
    spanning_none: list[str] = []
    for _, rows in group_keys(df, ["specimen_id"]):
        positions = np.flatnonzero(rows)
        for j, position in enumerate(positions):
            row = int(position)
            previous = int(positions[j - 1]) if j else None
            if previous is not None:
                at_start[row] = stress[previous]
            e1 = start[row]
            if np.isnan(e1) and previous is not None and not np.isnan(end[previous]):
                e1 = end[previous]
                borrowed.append(row)
            reason[row] = _blank_reason(stress_kpa, row, previous, e1, end[row])
            if reason[row] is None:
                assert previous is not None  # a first increment has a reason
                change = stress_kpa[row] - stress_kpa[previous]
                compressibility[row] = (e1 - end[row]) / ((1 + e1) * change)
        if in_situ_stress is not None:
            label = _label(df, positions)
            v0 = one_value(df, positions, in_situ_stress, _IN_SITU, {"label": label})
            if not np.isnan(v0):
                flags = _spans(positions, at_start, stress, branch, v0)
                spans[positions] = flags
                if not flags.any():
                    spanning_none.append(label)

    if borrowed:
        index = df.index[borrowed]
        notes.append(
            f"Rows {rows_text(index)} have no {_START}: each takes the previous "
            f"increment's {_END}."
        )
    if in_situ_stress is None:
        notes.append(
            f"No {_IN_SITU} column, so {SPANS} is blank: run "
            "ht.analysis.vertical_stress() on the rows first to mark the increment "
            "at the in situ stress."
        )
    if spanning_none:
        notes.append(
            f"No increment spans the {_IN_SITU} of {', '.join(spanning_none)}: "
            f"{SPANS} is False on all its rows, and nothing is extrapolated."
        )

    loading, unload_reload, modulus_reason = _moduli(compressibility, reason, branch)
    system = display_units
    volume, volume_unit = _written(1000 * compressibility, _VOLUME_UNIT, system)
    modulus_on_loading, modulus_unit = _written(loading, _KPA, system, "modulus")
    modulus_on_unload_reload, _ = _written(unload_reload, _KPA, system, "modulus")

    result = df.copy()
    if display_units is not None:
        result[_STRESS] = stress
    result[STRESS_AT_START] = at_start
    result[VOLUME_COMPRESSIBILITY] = volume
    result[f"{VOLUME_COMPRESSIBILITY}_reason"] = pd.Series(
        reason, index=df.index, dtype=object
    )
    result[CONSTRAINED_MODULUS] = modulus_on_loading
    result[UNLOAD_RELOAD_MODULUS] = modulus_on_unload_reload
    result[f"{CONSTRAINED_MODULUS}_reason"] = pd.Series(
        modulus_reason, index=df.index, dtype=object
    )
    result[SPANS] = pd.array(
        [pd.NA if flag is None else bool(flag) for flag in spans], dtype="boolean"
    )
    stress_units = {_STRESS: unit, STRESS_AT_START: unit} if unit else {}
    result.attrs["units"] = {
        **_units.units_of(df),
        **(units or {}),
        **stress_units,
        VOLUME_COMPRESSIBILITY: volume_unit,
        CONSTRAINED_MODULUS: modulus_unit,
        UNLOAD_RELOAD_MODULUS: modulus_unit,
    }
    if unit and in_situ_stress is not None and display_units is not None:
        result[_IN_SITU] = in_situ_stress
        result.attrs["units"][_IN_SITU] = unit
    for column, consolidation in CONDUCTIVITY.items():
        values, why = _conductivity(df, consolidation, units, compressibility, reason)
        result[column], conductivity_unit = _written(
            values, _CONDUCTIVITY_UNIT, system, "hydraulic_conductivity"
        )
        result[f"{column}_reason"] = pd.Series(why, index=df.index, dtype=object)
        result.attrs["units"][column] = conductivity_unit
    result.attrs["oedometer_increments"] = {
        "notes": notes,
        "water_unit_weight": settings.water_unit_weight,
    }
    return result


def _check(df: Any, display_units: str | None) -> None:
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if display_units not in (None, "SI", "US"):
        raise HangtuError(
            f'{_FUNCTION} display_units must be "SI", "US" or None, not '
            f"{display_units!r}."
        )
    missing = [column for column in _REQUIRED if column not in df.columns]
    if missing:
        raise ColumnError(
            f"{_FUNCTION} needs {', '.join(map(repr, missing))}: df has no such "
            f"column. Use p.oedometer(); {_TEMPLATE}"
        )
    blank = (
        df["specimen_id"].isna() | (df["specimen_id"].astype(str).str.strip() == "")
    ).to_numpy()
    if blank.any():
        raise HangtuError(
            f"Rows {rows_text(df.index[blank])} have no specimen_id, so {_FUNCTION} "
            "can't tell which specimen they belong to. Fill in specimen_id."
        )


def _in_kpa(stress: np.ndarray, unit: str | None) -> np.ndarray:
    """Return the stresses in kPa, the unit m_v is computed in."""
    if unit is None:
        return stress
    source, _ = _units._lookup(unit)
    if source is None:
        source = _units.parse_unit(unit, _STRESS)
    return _units.convert(stress, source, "stress", _units.ureg.Unit("kilopascal"))


def _blank_reason(
    stress: np.ndarray, row: int, previous: int | None, e1: float, e2: float
) -> str | None:
    """Return the first reason the increment ending at ``row`` gives no m_v."""
    if np.isnan(stress[row]):
        return NO_STRESS
    if previous is None:
        return FIRST_INCREMENT
    if np.isnan(stress[previous]):
        return NO_PREVIOUS_STRESS
    if stress[row] == stress[previous]:
        return NO_STRESS_CHANGE
    if np.isnan(e1):
        return NO_START_VOID_RATIO
    if np.isnan(e2):
        return NO_END_VOID_RATIO
    return None


def _moduli(
    compressibility: np.ndarray, reason: np.ndarray, branch: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Eoed and Eur,oed in kPa, each on its branch's rows, and why one is blank."""
    n = len(compressibility)
    loading, unload_reload = np.full(n, np.nan), np.full(n, np.nan)
    why = np.full(n, None, dtype=object)
    for row, (value, given) in enumerate(zip(compressibility, branch, strict=True)):
        if np.isnan(value):
            why[row] = reason[row]
        elif value <= 0:
            why[row] = NOT_POSITIVE
        elif given == LOADING:
            loading[row] = 1 / value
        elif given in (UNLOADING, RELOADING):
            unload_reload[row] = 1 / value
        elif given == CONSTANT_STRESS:
            why[row] = CONSTANT
        else:
            why[row] = NO_BRANCH
    return loading, unload_reload, why


def _spans(
    positions: np.ndarray,
    at_start: np.ndarray,
    stress: np.ndarray,
    branch: np.ndarray,
    in_situ_stress: float,
) -> np.ndarray:
    """Mark the first loading and the first unload or reload increment holding σ′v0."""
    flags = np.zeros(len(positions), dtype=bool)
    found_loading = found_unload_reload = False
    for j, row in enumerate(positions):
        s1, s2 = at_start[row], stress[row]
        if np.isnan(s1) or np.isnan(s2):
            continue
        holds = min(s1, s2) < in_situ_stress <= max(s1, s2)
        if not holds:
            continue
        if branch[row] == LOADING and s1 < s2 and not found_loading:
            flags[j] = found_loading = True
        elif branch[row] in (UNLOADING, RELOADING) and not found_unload_reload:
            flags[j] = found_unload_reload = True
    return flags


def _conductivity(
    df: pd.DataFrame,
    column: str,
    units: Mapping[str, str] | None,
    compressibility: np.ndarray,
    reason: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return k = c_v m_v γw in m/s from the lab's c_v in ``column``, and why blank.

    ``compressibility`` is m_v in 1/kPa. A column absent or blank throughout
    needs no unit.
    """
    n = len(df)
    if column not in df.columns or df[column].isna().all():
        return np.full(n, np.nan), np.full(n, NO_CONSOLIDATION, dtype=object)
    declared = _units.resolve_units(df, [column], units, analysis=True)[column]
    parsed = _units.parse_unit(declared, column)
    _units.check_dimension(parsed, "consolidation_coefficient", column)
    consolidation = _units.convert(
        numeric_column(df, column),
        parsed,
        "consolidation_coefficient",
        _units.ureg.Unit("meter**2 / year"),
    )
    value, unit = _units.parse_quantity(settings.water_unit_weight, "unit_weight")
    gamma_w = _units.convert(
        [value], _units.parse_unit(unit), "unit_weight", _units.ureg.Unit("kN/m^3")
    )[0]
    # m²/yr × 1/kPa × kN/m³ = 10⁻³ m/yr; a year of 365.25 days in pint.
    per_year = _units.ureg.Quantity(1.0, "meter**2 / year / kilopascal * kN / m**3")
    factor = float(per_year.to("meter / second").magnitude)
    conductivity = consolidation * compressibility * gamma_w * factor
    why = np.full(n, None, dtype=object)
    for row in range(n):
        if np.isnan(consolidation[row]):
            why[row] = NO_CONSOLIDATION
        elif consolidation[row] <= 0:
            why[row] = CONSOLIDATION_NOT_POSITIVE
        elif np.isnan(compressibility[row]):
            why[row] = reason[row]
        elif compressibility[row] <= 0:
            why[row] = NOT_POSITIVE
    conductivity[why != None] = np.nan  # noqa: E711 (an object array's None)
    return conductivity, why


def _label(df: pd.DataFrame, positions: np.ndarray) -> str:
    first = df.index[positions[0]]
    key = {
        column: None if pd.isna(df.at[first, column]) else df.at[first, column]
        for column in _IDENTIFIERS
        if column in df.columns
    }
    return specimen_label(key)


def _written(
    values: np.ndarray,
    canonical: str,
    display_units: str | None,
    quantity: str = "volume_compressibility",
) -> tuple[np.ndarray, str]:
    """Return values in canonical units in the display system's, and the unit."""
    if display_units is None:
        return values, canonical
    converted, text = _units.to_display(values, canonical, quantity, display_units)
    assert text is not None  # a kind with a canonical unit has a display unit
    return converted, text
