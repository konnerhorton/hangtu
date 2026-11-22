"""c_v from settlement-time readings (docs/analysis/compressibility.md §9).

One row per oedometer increment from its readings, as
``triaxial_failure_from_readings()`` gives one row per stage. Each construction
is a fixed rule on the readings, so the same readings give the same c_v.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu.analysis._oedometer import (
    CONSTANT_STRESS,
    branches,
    oedometer_load_branch,
    specimen_label,
)
from hangtu.errors import ColumnError, HangtuError
from hangtu.registry import column_info, template

_FUNCTION = "consolidation_coefficient_from_readings()"
_TEMPLATE = 'ht.template("oedometer_readings")'
TIME = "elapsed_time"
DISPLACEMENT = "vertical_displacement"
HEIGHT = "specimen_height"
_INITIAL = "void_ratio"
_START = "void_ratio_at_increment_start"
_END = "void_ratio_at_increment_end"
_STRESS = "applied_vertical_stress"
_REQUIRED = ("specimen_id", "test_stage", TIME, DISPLACEMENT)
_IDENTIFIERS = ("specimen_id", "sample_reference", "specimen_reference")
#: The columns that change from reading to reading; every other is the increment's.
_READING_COLUMNS = (TIME, DISPLACEMENT, "source_line")

AVERAGE_HEIGHT = "average_specimen_height"
ROOT_TIME = "coefficient_of_consolidation_root_time"
ROOT_TIME_ZERO = "corrected_zero_displacement_root_time"
DISPLACEMENT_90 = "displacement_at_90_percent_consolidation"
TIME_90 = "time_to_90_percent_consolidation"

#: BS 1377-5:1990, 3.6.3.3.3: c_v = 0.111 H̄²/t90, H̄ in mm, t90 in min, m²/year.
ROOT_TIME_COEFFICIENT = 0.111
#: The 1.15 line's abscissae are 1.15 times the early line's (3.6.3.3.2).
ROOT_TIME_RATIO = 1.15
#: The fewest readings a line is fitted to.
FEWEST = 3

#: The reasons a value is blank, worded as the result gives them.
CONSTANT = "constant stress increment"
NO_DISPLACEMENT = "no displacement over the increment"
FEW_READINGS = "fewer than 3 readings after the load was applied"
FEW_EARLY = "fewer than 3 readings in the first half of the increment's movement"
EARLY_NOT_MOVING = "the early readings don't move with the increment"
BELOW_EARLY = (
    "the curve is below the 1.15 line in its early portion: no straight early line"
)
AFTER_LAST = "t90 after the last reading"
NO_HEIGHT = "no specimen height or void ratio for H̄"

RULE = "rule"

# Canonical units the constructions work in: the standard's mm and minutes.
_MM = "mm"
_MINUTE = "min"
_CV_UNIT = "m2/yr"


@dataclass(frozen=True)
class Readings:
    """One increment's readings, sorted by time and oriented by its movement.

    ``times`` are in minutes, ``movement`` is y = s (d - d_first) in mm, with
    d_first the displacement at the smallest time and s the sign of the
    increment's movement, so y grows with it. ``rows`` are the frame's rows in
    time order.
    """

    times: np.ndarray
    movement: np.ndarray
    first: float
    sign: float
    rows: pd.Index

    def displacement(self, movement: float) -> float:
        """Write a movement back as a displacement in the readings' datum, mm."""
        return self.first + self.sign * movement

    @property
    def after_load(self) -> np.ndarray:
        """True on the readings after the load was applied, t > 0."""
        return self.times > 0

    @property
    def early(self) -> np.ndarray:
        """True on the early portion: t > 0 and y at most half the last y."""
        return self.after_load & (self.movement <= self.movement[-1] / 2)


@dataclass(frozen=True)
class RootTime:
    """The root time construction on one increment (BS 1377-5:1990, 3.6.3.3).

    Movements are y in mm, the time in minutes. ``fitted`` is True on the
    readings the early line was fitted to. Blank (NaN) where the construction
    stopped, with its ``reason``.
    """

    zero: float = np.nan
    slope: float = np.nan
    fitted: np.ndarray | None = None
    time: float = np.nan
    movement: float = np.nan
    reason: str | None = None


def consolidation_coefficient_from_readings(
    df: pd.DataFrame,
    *,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Recompute each oedometer increment's c_v from its settlement-time readings.

    Reads the readings a lab takes during each load increment, as
    ``p.oedometer_readings()`` or ``ht.template("oedometer_readings")`` lays
    them out (one row per reading, its increment's values on each row), and
    returns one row per increment with the coefficient of consolidation by
    the **root time** construction of BS 1377-5:1990, 3.6.3.3, with the
    construction's points, beside the lab's reported values. The lab reports
    only the result; the construction behind it is a graphical judgment
    (3.6.3.1, note), and here it is a stated rule, so the same readings
    always give the same $c_v$ and a reviewer can check each point by hand.

    **Readings and increments.** Readings are grouped by ``specimen_id`` and
    ``test_stage`` (the increment), increments in the order they first
    appear, and each increment's readings sorted by ``elapsed_time``: time
    order is the only order a consolidation curve has. Left out, each kind
    counted in one note: a reading with a blank ``elapsed_time``, with a
    blank ``vertical_displacement``, and with a negative ``elapsed_time``
    (before the load was applied). An increment's ``load_branch`` is read
    from the rows, else added by ``ht.analysis.oedometer_load_branch()``
    over the increments the rows hold, with a note. A ``constant_stress``
    increment gives no $c_v$. Unloading and reloading increments get $c_v$
    by the same construction, oriented by their own movement: BS 1377-5
    describes it for load increments, so those values are an extension of
    it.

    **Orientation and datum.** ``vertical_displacement`` keeps the datum and
    sign the rows give it. Per increment, with $d_{first}$ the reading at the
    smallest time and $d_{last}$ at the largest, the construction works on

    $$
    y = s\,(d - d_{first}), \quad s = \operatorname{sign}(d_{last} - d_{first})
    $$

    so $y$ grows with the increment's movement, and every point is written
    back as $d = d_{first} + s\,y$, in the rows' datum and sign. A dial gauge
    reading down and a settlement reading up give the same $c_v$. The
    **early portion** is the readings with $t > 0$ and
    $y \le \tfrac{1}{2} y_{last}$ ("usually within the first 50 % of
    compression", 3.6.3.3.1), taken on the increment's whole movement since
    $d_{100}$ isn't known yet. A reading at $t = 0$ sets $d_{first}$ only: it
    is taken before the immediate compression, so it isn't on the early
    line.

    **Root time** (3.6.3.3), in $x = \sqrt{t}$:

    1. The early line: the least squares line of $y$ on $\sqrt{t}$ over the
       early portion, $y = d_0 + b\sqrt{t}$; $d_0$, its intercept, is the
       corrected zero point (3.6.3.3.1).
    2. The 1.15 line, $y = d_0 + (b/1.15)\sqrt{t}$: through $d_0$, with
       abscissae 1.15 times the early line's (3.6.3.3.2).
    3. The curve is the readings joined by straight lines in $\sqrt{t}$. At
       the first reading after the early portion's last at which the curve
       is at or below the 1.15 line, the crossing between it and the
       reading before is interpolated linearly in $\sqrt{t}$: $t_{90}$ is
       its $x^2$ and $d_{90}$ the 1.15 line there (3.6.3.3.2). Linear, as a
       hand construction on the standard's plot joins the points.
    4. The coefficient (3.6.3.3.3), with $\bar{H}$ in mm and $t_{90}$ in
       minutes:

       $$
       c_v = \frac{0.111\,\bar{H}^2}{t_{90}} \quad \text{m}^2/\text{year}
       $$

       From $c_v = T_{90} (\bar{H}/2)^2 / t_{90}$, with a drainage path of
       $\bar{H}/2$ (the standard's cell drains at both faces, and double
       drainage is assumed) and 525 960 minutes in a year, the coefficient
       is $T_{90} \times 525\,960 \times 10^{-6} / 4 = 0.1115$ with
       Terzaghi's $T_{90} = 0.848$ (Abuel-Naga & Pender 2012, Table 1,
       p. 45). 0.111 is BS 1377-5's rounding of it, and is used so the value
       matches a BS lab's to the figure; Terzaghi's $T_{90}$ would give a
       $c_v$ 0.45 % higher.

    **The average height** is $\bar{H} = (H_1 + H_2)/2$ (3.6.3.2.4), with
    $H = H_0 (1 + e)/(1 + e_0)$: $H_0$ the ``specimen_height``, $e_0$ the
    initial ``void_ratio``, $e_1$ the increment's
    ``void_ratio_at_increment_start`` (else the previous increment's
    ``void_ratio_at_increment_end`` in the rows, with a note) and $e_2$ its
    ``void_ratio_at_increment_end``. It comes from the void ratios, not the
    readings, since an increment's readings needn't start at its start. Any
    of them blank: $c_v$ is blank, the construction's points and $t_{90}$
    are still given.

    **When an increment gives no value,** its $c_v$ is blank with the first
    reason that applies, in ``coefficient_of_consolidation_root_time_reason``:

    - ``"constant stress increment"``;
    - ``"no displacement over the increment"``: $y_{last} = 0$;
    - ``"fewer than 3 readings after the load was applied"``;
    - ``"fewer than 3 readings in the first half of the increment's
      movement"``: the early line needs three;
    - ``"the early readings don't move with the increment"``: the early
      line's slope is 0 or less;
    - ``"the curve is below the 1.15 line in its early portion: no straight
      early line"``: at the early portion's last reading, the curve is
      already at or below it. The root time plot sometimes has no straight
      early portion (3.6.3.1, note); the log time construction may serve;
    - ``"t90 after the last reading"``: the curve never reaches the 1.15
      line. Nothing is extrapolated past the readings;
    - ``"no specimen height or void ratio for H̄"``: $t_{90}$ is given, $c_v$
      isn't.

    **Valid for:** incremental-load oedometer tests in a double-drained
    cell, one increment's readings timed from the moment its load was
    applied. **Assumptions:** Terzaghi's one-dimensional consolidation with
    constant $c_v$ over the increment; double drainage. **Judgments taken:**
    none: the construction is a stated rule, and whether to accept it is
    the reviewer's, on the time curves it draws.

    Sources: BS 1377-5:1990, Methods of test for soils for civil engineering
    purposes, Part 5: Compressibility, permeability and durability tests,
    3.6.3.1 and its note, 3.6.3.2.4 (the average height), 3.6.3.3.1 to
    3.6.3.3.3. Abuel-Naga, H.M. & Pender, M.J. (2012). Modified Terzaghi
    consolidation curves with effective stress-dependent coefficient of
    consolidation. *Géotechnique Letters* 2, 43-48, Table 1 (Terzaghi's
    $T_{90} = 0.848$), https://doi.org/10.1680/geolett.12.00005.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per reading: ``specimen_id``, ``test_stage``,
        ``elapsed_time`` (since the increment's load was applied) and
        ``vertical_displacement`` (from any datum, with any sign), with the
        increment's ``specimen_height``, ``void_ratio``,
        ``void_ratio_at_increment_start`` and ``void_ratio_at_increment_end``
        for $\bar{H}$, and its ``load_branch`` or ``applied_vertical_stress``,
        repeated on each of its readings. The identity columns and the lab's
        ``reported_coefficient_of_consolidation_root_time`` and
        ``_log_time`` are carried to the result where present.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.
    display_units : {"SI", "US"}, optional
        Write the displacements and $\bar{H}$ in mm or in and $c_v$ in m²/yr
        or ft²/yr (the carried columns too, where their units are known);
        times stay in minutes in both. None writes the new columns in mm,
        minutes and m²/yr and keeps the carried columns as given.

    Returns
    -------
    pandas.DataFrame
        One row per increment with readings, in the order they first appear:
        the increment's columns from its first reading, then
        ``average_specimen_height``,
        ``corrected_zero_displacement_root_time``,
        ``displacement_at_90_percent_consolidation``,
        ``time_to_90_percent_consolidation``,
        ``coefficient_of_consolidation_root_time``, its ``_basis``
        (``"rule"``) and its ``_reason``. ``attrs["units"]`` names each unit;
        ``attrs["consolidation_coefficient_from_readings"]["notes"]`` holds
        the notes.

    Raises
    ------
    ColumnError
        For a missing ``specimen_id``, ``test_stage``, ``elapsed_time`` or
        ``vertical_displacement``, or a cell that isn't a number.
    HangtuError
        For a reading with a blank ``specimen_id`` or ``test_stage``, a
        ``load_branch`` value it doesn't know, a ``display_units`` other than
        "SI", "US" or None, or a time, displacement or height without units
        or in a unit of the wrong kind.

    Examples
    --------
    Each increment's c_v from its readings, beside the lab's:

    >>> p.set_readings_map("readings_map.csv")
    >>> rows = ht.analysis.consolidation_coefficient_from_readings(
    ...     p.oedometer_readings()
    ... )
    >>> rows[
    ...     [
    ...         "test_stage",
    ...         "time_to_90_percent_consolidation",
    ...         "coefficient_of_consolidation_root_time",
    ...         "reported_coefficient_of_consolidation_root_time",
    ...     ]
    ... ]
    """
    _check(df, display_units)
    notes: list[str] = []
    times = _in_unit(df, TIME, "time", _MINUTE, units)
    displacements = _in_unit(df, DISPLACEMENT, "small_length", _MM, units)
    kept = _kept(df, times, displacements, notes)
    groups = _groups(df, kept)
    first_rows = [int(positions[0]) for positions in groups]
    increments = df.iloc[first_rows]
    branch = _branches(increments, notes)
    heights = _average_heights(df, increments, units, notes)

    n = len(groups)
    zero = np.full(n, np.nan)
    at_90 = np.full(n, np.nan)
    time_90 = np.full(n, np.nan)
    coefficient = np.full(n, np.nan)
    reason = np.full(n, None, dtype=object)
    for i, positions in enumerate(groups):
        if branch[i] == CONSTANT_STRESS:
            reason[i] = CONSTANT
            continue
        readings = increment_readings(df.index, positions, times, displacements)
        root = root_time(readings)
        reason[i] = root.reason
        if root.reason is not None:
            continue
        zero[i] = readings.displacement(root.zero)
        at_90[i] = readings.displacement(root.movement)
        time_90[i] = root.time
        if np.isnan(heights[i]):
            reason[i] = NO_HEIGHT
        else:
            coefficient[i] = ROOT_TIME_COEFFICIENT * heights[i] ** 2 / root.time

    result = _carried(increments, units, display_units)
    if "load_branch" not in result.columns:
        result["load_branch"] = pd.Series(branch, dtype=object)
    written_units: dict[str, str | None] = {}
    for column, values, canonical, quantity in (
        (AVERAGE_HEIGHT, heights, _MM, "small_length"),
        (ROOT_TIME_ZERO, zero, _MM, "small_length"),
        (DISPLACEMENT_90, at_90, _MM, "small_length"),
        (TIME_90, time_90, _MINUTE, "time"),
        (ROOT_TIME, coefficient, _CV_UNIT, "consolidation_coefficient"),
    ):
        result[column], written_units[column] = _written(
            values, canonical, quantity, display_units
        )
    result[f"{ROOT_TIME}_basis"] = pd.Series([RULE] * n, dtype=object)
    result[f"{ROOT_TIME}_reason"] = pd.Series(reason, dtype=object)
    result.attrs["units"] = {**result.attrs.get("units", {}), **written_units}
    result.attrs["consolidation_coefficient_from_readings"] = {"notes": notes}
    return result


def increment_readings(
    index: pd.Index,
    positions: np.ndarray,
    times: np.ndarray,
    displacements: np.ndarray,
) -> Readings:
    """Return one increment's readings, sorted stably by time and oriented."""
    order = positions[np.argsort(times[positions], kind="stable")]
    t = times[order]
    d = displacements[order]
    first, last = d[0], d[-1]
    sign = 1.0 if last >= first else -1.0
    return Readings(t, sign * (d - first), float(first), sign, index[order])


def root_time(readings: Readings) -> RootTime:
    """Make the root time construction (BS 1377-5:1990, 3.6.3.3) on one increment."""
    whole = _whole_reason(readings)
    if whole is not None:
        return RootTime(reason=whole)
    early = readings.early
    if early.sum() < FEWEST:
        return RootTime(fitted=early, reason=FEW_EARLY)
    x = np.sqrt(readings.times)
    y = readings.movement
    zero, slope = _least_squares(x[early], y[early])
    if not slope > 0:
        return RootTime(zero, slope, early, reason=EARLY_NOT_MOVING)
    # How far the curve is above the 1.15 line at each reading.
    above = y - (zero + slope / ROOT_TIME_RATIO * x)
    last_early = int(np.flatnonzero(early)[-1])
    if above[last_early] <= 0:
        return RootTime(zero, slope, early, reason=BELOW_EARLY)
    for j in range(last_early + 1, len(y)):
        if above[j] <= 0:
            share = above[j - 1] / (above[j - 1] - above[j])
            root = x[j - 1] + (x[j] - x[j - 1]) * share
            movement = zero + slope / ROOT_TIME_RATIO * root
            return RootTime(zero, slope, early, float(root**2), float(movement))
    return RootTime(zero, slope, early, reason=AFTER_LAST)


def _whole_reason(readings: Readings) -> str | None:
    """Return why no construction can be made on the increment, else None."""
    if readings.after_load.sum() < FEWEST:
        return FEW_READINGS
    if readings.movement[-1] == 0:
        return NO_DISPLACEMENT
    return None


def _least_squares(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Return the intercept and slope of the least squares line of y on x."""
    dx = x - x.mean()
    spread = float(np.sum(dx**2))
    if spread == 0:
        return float(y.mean()), np.nan
    slope = float(np.sum(dx * (y - y.mean())) / spread)
    return float(y.mean() - slope * x.mean()), slope


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
            f"df has no column {', '.join(map(repr, missing))}. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}. Each reading needs its "
            "specimen, its increment (test_stage), its elapsed time and its "
            f"vertical displacement; {_TEMPLATE} has the columns."
        )
    blank = df["specimen_id"].isna() | df["test_stage"].isna()
    blank |= df["specimen_id"].astype(str).str.strip().eq("")
    blank |= df["test_stage"].astype(str).str.strip().eq("")
    if blank.any():
        raise HangtuError(
            f"Rows {rows_text(df.index[blank.to_numpy()])} have a blank specimen_id "
            "or test_stage, so hangtu can't tell which increment their readings "
            "belong to. Fill them in, or drop the rows."
        )


def _in_unit(
    df: pd.DataFrame,
    column: str,
    quantity: str,
    target: str,
    units: Mapping[str, str] | None,
) -> np.ndarray:
    """Return ``df[column]`` in ``target``; a column blank throughout needs no unit."""
    values = numeric_column(df, column)
    if np.isnan(values).all():
        return values
    declared = _units.resolve_units(df, [column], units, analysis=True)[column]
    parsed = _units.parse_unit(declared, column)
    _units.check_dimension(parsed, quantity, column)
    return _units.convert(values, parsed, quantity, _units.parse_unit(target))


def _kept(
    df: pd.DataFrame, times: np.ndarray, displacements: np.ndarray, notes: list[str]
) -> np.ndarray:
    """Return True on the readings the constructions use; note each kind left out."""
    no_time = np.isnan(times)
    no_displacement = np.isnan(displacements) & ~no_time
    negative = times < 0
    for rows, why in (
        (no_time, f"a blank {TIME}"),
        (no_displacement, f"a blank {DISPLACEMENT}"),
        (negative, f"a negative {TIME}, before the load was applied"),
    ):
        if rows.any():
            count = int(rows.sum())
            readings = "reading" if count == 1 else "readings"
            notes.append(
                f"Left out {count} {readings} with {why} (rows "
                f"{rows_text(df.index[rows])})."
            )
    return ~(no_time | no_displacement | negative)


def _groups(df: pd.DataFrame, kept: np.ndarray) -> list[np.ndarray]:
    """Each increment's kept readings' positions, in order of first appearance.

    An increment whose readings were all left out keeps its first reading's
    position, so it still gets a row with its reason.
    """
    keys = list(
        zip(df["specimen_id"].astype(str), df["test_stage"].astype(str), strict=True)
    )
    positions: dict[tuple[str, str], list[int]] = {}
    for position, key in enumerate(keys):
        positions.setdefault(key, []).append(position)
    groups = []
    for rows in positions.values():
        used = [row for row in rows if kept[row]]
        groups.append(np.array(used if used else rows[:1], dtype=int))
    return groups


def _branches(increments: pd.DataFrame, notes: list[str]) -> np.ndarray:
    """Each increment's ``load_branch``: as given, else from the stresses."""
    if "load_branch" in increments.columns:
        return branches(increments, _FUNCTION)
    if _STRESS not in increments.columns:
        notes.append(
            "No load_branch or applied_vertical_stress column, so no increment is "
            "read as a constant stress one."
        )
        return np.full(len(increments), None, dtype=object)
    notes.append(
        "load_branch added by ht.analysis.oedometer_load_branch(), over the "
        "increments the rows hold, in the order they first appear."
    )
    return branches(oedometer_load_branch(increments), _FUNCTION)


def _average_heights(
    df: pd.DataFrame,
    increments: pd.DataFrame,
    units: Mapping[str, str] | None,
    notes: list[str],
) -> np.ndarray:
    """H̄ in mm per increment, from the specimen's height and void ratios."""
    n = len(increments)

    def column(name: str) -> np.ndarray:
        if name not in increments.columns:
            return np.full(n, np.nan)
        return numeric_column(increments, name)

    if HEIGHT in increments.columns:
        height = _in_unit(increments, HEIGHT, "small_length", _MM, units or {})
    else:
        height = np.full(n, np.nan)
    initial, start, end = column(_INITIAL), column(_START), column(_END)
    borrowed: list[str] = []
    previous: dict[str, int] = {}
    specimens = increments["specimen_id"].astype(str).to_numpy()
    for i in range(n):
        before = previous.get(specimens[i])
        if np.isnan(start[i]) and before is not None and not np.isnan(end[before]):
            start[i] = end[before]
            borrowed.append(_increment_label(increments, i))
        previous[specimens[i]] = i
    if borrowed:
        notes.append(
            f"{', '.join(borrowed)} {'has' if len(borrowed) == 1 else 'have'} no "
            f"{_START}: each takes the previous increment's {_END}."
        )
    h1 = height * (1 + start) / (1 + initial)
    h2 = height * (1 + end) / (1 + initial)
    return (h1 + h2) / 2


def _increment_label(increments: pd.DataFrame, i: int) -> str:
    row = increments.iloc[i]
    key = {
        column: None if pd.isna(row[column]) else row[column]
        for column in _IDENTIFIERS
        if column in increments.columns
    }
    return f"{specimen_label(key)} increment {row['test_stage']}"


def _carried(
    increments: pd.DataFrame,
    units: Mapping[str, str] | None,
    display_units: str | None,
) -> pd.DataFrame:
    """Return the increment's columns from its first reading, in template order.

    With ``display_units``, a carried column with a unit and a kind is
    converted to the display system.
    """
    order = [
        c
        for c in template("oedometer_readings").columns
        if c in increments.columns and c not in _READING_COLUMNS
    ]
    others = [
        c for c in increments.columns if c not in order and c not in _READING_COLUMNS
    ]
    result = increments[[*order, *others]].reset_index(drop=True)
    declared = {**_units.units_of(increments), **(units or {})}
    carried_units = {c: u for c, u in declared.items() if c in result.columns}
    if display_units is not None:
        for name in result.columns:
            info = column_info(name)
            quantity = None if info is None else info.get("quantity")
            unit = carried_units.get(name)
            if quantity is None or unit is None:
                continue
            if _units.quantity_kind(quantity)["canonical"] is None:
                continue
            values = numeric_column(result, name)
            result[name], text = _units.to_display(
                values, unit, quantity, display_units
            )
            if text is not None:
                carried_units[name] = text
    result.attrs = {"units": carried_units}
    return result


def _written(
    values: np.ndarray, canonical: str, quantity: str, display_units: str | None
) -> tuple[np.ndarray, str]:
    """Return values in canonical units in the display system's, and the unit."""
    if display_units is None:
        return values, canonical
    converted, text = _units.to_display(values, canonical, quantity, display_units)
    assert text is not None  # a kind with a canonical unit has a display unit
    return converted, text
