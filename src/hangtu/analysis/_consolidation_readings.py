"""c_v from settlement-time readings (docs/analysis/compressibility.md §9).

One row per oedometer increment from its readings, as
``triaxial_failure_from_readings()`` gives one row per stage. Each construction
is a fixed rule on the readings, so the same readings give the same c_v.
"""

import dataclasses
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
LOG_TIME = "coefficient_of_consolidation_log_time"
LOG_TIME_ZERO = "corrected_zero_displacement_log_time"
DISPLACEMENT_100 = "displacement_at_100_percent_primary_consolidation"
DISPLACEMENT_50 = "displacement_at_50_percent_consolidation"
TIME_50 = "time_to_50_percent_consolidation"

#: BS 1377-5:1990, 3.6.3.3.3: c_v = 0.111 H̄²/t90, H̄ in mm, t90 in min, m²/year.
ROOT_TIME_COEFFICIENT = 0.111
#: The 1.15 line's abscissae are 1.15 times the early line's (3.6.3.3.2).
ROOT_TIME_RATIO = 1.15
#: BS 1377-5:1990, 3.6.3.2.4: c_v = 0.026 H̄²/t50, H̄ in mm, t50 in min, m²/year.
LOG_TIME_COEFFICIENT = 0.026
#: The fewest readings a line is fitted to, and the fewest 1:4 pairs averaged.
FEWEST = 3
#: The pairs' times are in the ratio 1:4 (3.6.3.2.1).
PAIR_RATIO = 4.0
#: The tangent at the inflexion is at least this many times as steep as the
#: secondary line, as ``oedometer_fit()``'s break (compressibility.md §3).
STEEPER = 2.0
#: Times that differ by less than this, relative, are the same time, so that
#: times converted from another unit still pair (4 x 0.1 min against 0.4 min).
_SAME_TIME = 1e-9

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
FEW_SECONDARY = "fewer than 3 readings in the last log cycle of time"
NO_TANGENT = "no three readings before the last log cycle"
NO_SECONDARY = (
    "no clear secondary portion: the tangent is less than twice as steep as the "
    "last log cycle"
)
FEW_PAIRS = "fewer than 3 pairs of times in the ratio 1:4 before the inflexion"
OUTSIDE_100 = "d100 outside the readings"
BEFORE_FIRST = "t50 before the first reading"
AFTER_LAST_50 = "t50 after the last reading"
NO_PAIR_IN_RANGE = "the override for early holds no pair of times in the ratio 1:4"

#: The overrides (``ht.template("consolidation_overrides")``).
_OVERRIDES_TEMPLATE = 'ht.template("consolidation_overrides")'
_METHOD = "consolidation_method"
_PORTION = "curve_portion"
_START_TIME = "elapsed_time_start"
_END_TIME = "elapsed_time_end"
_OVERRIDE_REASON = "override_reason"
ROOT_METHOD = "root_time"
LOG_METHOD = "log_time"
EARLY = "early"
INFLEXION = "inflexion"
SECONDARY = "secondary"
#: The parts of each construction an override can give the range of.
PORTIONS = {ROOT_METHOD: (EARLY,), LOG_METHOD: (EARLY, INFLEXION, SECONDARY)}
#: The fewest readings an overridden line is fitted to.
OVERRIDE_FEWEST = 2
OVERRIDE = "override"

#: An override's time range, (start, end) in minutes.
Range = tuple[float, float]

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


@dataclass(frozen=True)
class Line:
    """A least squares line y = intercept + slope x over the ``fitted`` readings."""

    intercept: float
    slope: float
    fitted: np.ndarray

    def at(self, x: float) -> float:
        return self.intercept + self.slope * x


@dataclass(frozen=True)
class LogTime:
    """The log time construction on one increment (BS 1377-5:1990, 3.6.3.2).

    Movements are y in mm, times in minutes, and the lines in x = log10 t.
    ``pairs`` are the positions (in time order) of the readings whose times
    t_i paired with 4 t_i gave d0. Blank (NaN or None) where the construction
    stopped, with its ``reason``.
    """

    secondary: Line | None = None
    tangent: Line | None = None
    pairs: np.ndarray | None = None
    zero: float = np.nan
    time_100: float = np.nan
    movement_100: float = np.nan
    movement_50: float = np.nan
    time: float = np.nan
    reason: str | None = None


def consolidation_coefficient_from_readings(
    df: pd.DataFrame,
    *,
    overrides: pd.DataFrame | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Recompute each oedometer increment's c_v from its settlement-time readings.

    Reads the readings a lab takes during each load increment, as
    ``p.oedometer_readings()`` or ``ht.template("oedometer_readings")`` lays
    them out (one row per reading, its increment's values on each row), and
    returns one row per increment with the coefficient of consolidation by
    the **root time** and **log time** constructions of BS 1377-5:1990,
    3.6.3.3 and 3.6.3.2, with each construction's points, beside the lab's
    reported values. The lab reports
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
    by the same constructions, oriented by their own movement: BS 1377-5
    describes them for load increments, so those values are an extension of
    it.

    **Orientation and datum.** ``vertical_displacement`` keeps the datum and
    sign the rows give it. Per increment, with $d_{first}$ the reading at the
    smallest time and $d_{last}$ at the largest, both constructions work on

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

    **Log time** (3.6.3.2), in $x = \log_{10} t$ over the readings with
    $t > 0$ (the $t = 0$ reading has no place on a log scale):

    1. The secondary line: the least squares line of $y$ on $\log_{10} t$
       over the readings in the last log cycle of time,
       $t \ge t_{last}/10$ (one cycle, as 3.6.5.2 extends the same line over
       one cycle for the secondary compression coefficient).
    2. The tangent at the point of inflexion: of every three consecutive
       readings ending before the secondary line's first, the least squares
       line with the largest slope, the earlier on a tie. The inflexion is
       where the curve is steepest in $\log t$, and three readings fit a line
       without one stray reading deciding it.
    3. The tangent must be at least twice as steep as the secondary line, or
       the curve has no clear secondary portion to draw the second line on.
    4. The corrected zero point (3.6.3.2.1): for each reading time $t_i$
       with $4 t_i$ at or before the tangent's middle reading (the
       convex-upward portion ends at the inflexion),
       $d_{0,i} = 2\,y(t_i) - y(4 t_i)$, with $y(4 t_i)$ interpolated linearly
       in $\log t$ when no reading has that time; $d_0$ is the mean over the
       three largest $t_i$ (the standard's pair and "two other pairs"). The
       largest are used because their differences are largest against the
       gauge's resolution. The construction assumes the early curve is
       parabolic (3.6.3.2.1, note).
    5. $d_{100}$: where the tangent and the secondary line cross (3.6.3.2.2).
    6. $d_{50} = (d_0 + d_{100})/2$, and $t_{50}$ where the curve first
       reaches it, the readings joined by straight lines in $\log t$
       (3.6.3.2.3).
    7. The coefficient (3.6.3.2.4), with $\bar{H}$ in mm and $t_{50}$ in
       minutes:

       $$
       c_v = \frac{0.026\,\bar{H}^2}{t_{50}} \quad \text{m}^2/\text{year}
       $$

       0.026 is BS 1377-5's rounding of
       $T_{50} \times 525\,960 \times 10^{-6} / 4 = 0.0259$, with
       Terzaghi's $T_{50} = 0.197$ (Abuel-Naga & Pender 2012, Table 1,
       p. 45); Terzaghi's $T_{50}$ would give a $c_v$ 0.37 % lower.

    The two constructions generally agree, but the root time plot sometimes
    has no straight early portion and log time serves better, or the reverse
    where secondary compression is large (3.6.3.1, note), so both are given.

    **The average height** is $\bar{H} = (H_1 + H_2)/2$ (3.6.3.2.4), with
    $H = H_0 (1 + e)/(1 + e_0)$: $H_0$ the ``specimen_height``, $e_0$ the
    initial ``void_ratio``, $e_1$ the increment's
    ``void_ratio_at_increment_start`` (else the previous increment's
    ``void_ratio_at_increment_end`` in the rows, with a note) and $e_2$ its
    ``void_ratio_at_increment_end``. It comes from the void ratios, not the
    readings, since an increment's readings needn't start at its start. Any
    of them blank: $c_v$ is blank, the constructions' points and times are
    still given.

    **Overrides.** Each rule above is a reading of the curve, and where an
    increment's curve calls for another reading, ``overrides`` gives the
    time range for one part of one construction, in
    ``ht.template("consolidation_overrides")``'s shape: ``specimen_id``,
    ``test_stage``, ``consolidation_method`` (``"root_time"`` or
    ``"log_time"``), ``curve_portion``, ``elapsed_time_start`` and
    ``elapsed_time_end`` (inclusive, in the units its ``attrs["units"]``
    declares) and ``override_reason``, required. An override replaces the
    rule's range for its part only, and the other steps run as above:

    - ``"early"``, root time: the early line is fitted to the readings in
      the range, at least 2;
    - ``"early"``, log time: $d_0$ is the mean over every pair with both
      $t_i$ and $4 t_i$ in the range, at least one;
    - ``"inflexion"``, log time: the tangent is fitted to the readings in the
      range, at least 2; its middle reading (the earlier of two) ends the
      convex-upward portion for the pairs and for $d_{100}$'s check;
    - ``"secondary"``, log time: the secondary line is fitted to the readings
      in the range, at least 2.

    A range with too few readings gives the method its reason, such as
    ``"the override for early holds 1 reading"`` or ``"the override for
    early holds no pair of times in the ratio 1:4"``. Each method's
    ``_basis`` is ``"override"`` on an increment where any of its parts was
    overridden and ``"rule"`` elsewhere, and the overrides are recorded on
    the result. They are passed on each call: the result is reproducible
    only with the same overrides.

    **When an increment gives no value,** its $c_v$ by each method is blank
    with the first reason that applies, in
    ``coefficient_of_consolidation_root_time_reason`` and
    ``coefficient_of_consolidation_log_time_reason``, and the construction's
    points are blank too. For both methods:

    - ``"constant stress increment"``;
    - ``"fewer than 3 readings after the load was applied"``;
    - ``"no displacement over the increment"``: $y_{last} = 0$;
    - ``"no specimen height or void ratio for H̄"``: the points and times are
      given, $c_v$ isn't.

    For root time, in this order:

    - ``"fewer than 3 readings in the first half of the increment's
      movement"``: the early line needs three;
    - ``"the early readings don't move with the increment"``: the early
      line's slope is 0 or less;
    - ``"the curve is below the 1.15 line in its early portion: no straight
      early line"``: at the early portion's last reading, the curve is
      already at or below it. The root time plot sometimes has no straight
      early portion (3.6.3.1, note); the log time construction may serve;
    - ``"t90 after the last reading"``: the curve never reaches the 1.15
      line. Nothing is extrapolated past the readings.

    For log time, in this order:

    - ``"fewer than 3 readings in the last log cycle of time"``;
    - ``"no three readings before the last log cycle"``: no tangent;
    - ``"no clear secondary portion: the tangent is less than twice as steep
      as the last log cycle"`` (or the tangent doesn't rise at all);
    - ``"fewer than 3 pairs of times in the ratio 1:4 before the
      inflexion"``: the readings start too late, or primary consolidation
      ends too soon, for the times to resolve the curve's start;
    - ``"d100 outside the readings"``: the lines cross before the tangent's
      middle reading or after the last reading;
    - ``"t50 before the first reading"``: the curve is at or past $d_{50}$ at
      its first reading after the load;
    - ``"t50 after the last reading"``: the curve never reaches $d_{50}$.

    **Valid for:** incremental-load oedometer tests in a double-drained
    cell, one increment's readings timed from the moment its load was
    applied. **Assumptions:** Terzaghi's one-dimensional consolidation with
    constant $c_v$ over the increment; double drainage. **Judgments taken:**
    none: the construction is a stated rule, and whether to accept it is
    the reviewer's, on the time curves it draws.

    Sources: BS 1377-5:1990, Methods of test for soils for civil engineering
    purposes, Part 5: Compressibility, permeability and durability tests,
    3.6.3.1 and its note, 3.6.3.2.1 to 3.6.3.2.4, 3.6.3.3.1 to 3.6.3.3.3,
    3.6.5.2 (the secondary line over one cycle). Abuel-Naga, H.M. & Pender,
    M.J. (2012). Modified Terzaghi consolidation curves with effective
    stress-dependent coefficient of consolidation. *Géotechnique Letters* 2,
    43-48, Table 1 (Terzaghi's $T_{50} = 0.197$ and $T_{90} = 0.848$),
    https://doi.org/10.1680/geolett.12.00005.

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
    overrides : pandas.DataFrame, optional
        One row per overridden part of a construction, as above. Its times'
        units come from its ``attrs["units"]`` (``ht.read_csv(...,
        units=...)`` or ``ht.set_units()``).
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
        (``"rule"`` or ``"override"``) and its ``_reason``, then
        ``corrected_zero_displacement_log_time``,
        ``displacement_at_100_percent_primary_consolidation``,
        ``displacement_at_50_percent_consolidation``,
        ``time_to_50_percent_consolidation``,
        ``coefficient_of_consolidation_log_time``, its ``_basis`` and its
        ``_reason``. ``attrs["units"]`` names each unit;
        ``attrs["consolidation_coefficient_from_readings"]`` holds the
        ``"notes"`` and the ``"overrides"`` used, as records.

    Raises
    ------
    ColumnError
        For a missing ``specimen_id``, ``test_stage``, ``elapsed_time`` or
        ``vertical_displacement``, an overrides column missing, or a cell
        that isn't a number.
    HangtuError
        For a reading with a blank ``specimen_id`` or ``test_stage``, a
        ``load_branch`` value it doesn't know, a ``display_units`` other than
        "SI", "US" or None, or a time, displacement or height without units
        or in a unit of the wrong kind. For an override, naming its row as a
        spreadsheet numbers it (the header is row 1): one for an increment
        the readings don't have (a typo would otherwise leave the rule in
        place silently), one repeating another's increment, method and part,
        an unknown ``consolidation_method`` or ``curve_portion``,
        ``"inflexion"`` or ``"secondary"`` for root time, a blank time, a
        start after its end, or a blank ``override_reason``.

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
    ...         "time_to_50_percent_consolidation",
    ...         "coefficient_of_consolidation_log_time",
    ...         "reported_coefficient_of_consolidation_log_time",
    ...     ]
    ... ]
    """
    return constructions(
        df, overrides=overrides, units=units, display_units=display_units
    )[0]


@dataclass(frozen=True)
class Construction:
    """One increment's constructions, for a plot to draw the fit the result holds.

    ``row`` is the position in the rows of the increment's first reading.
    ``readings``, ``root`` and ``log`` are None for a constant stress
    increment. ``ranges`` maps each overridden method to its parts' ranges,
    in minutes.
    """

    key: tuple[str, str]
    row: int
    readings: Readings | None
    root: RootTime | None
    log: LogTime | None
    ranges: Mapping[str, Mapping[str, Range]]


def constructions(
    df: pd.DataFrame,
    *,
    overrides: pd.DataFrame | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> tuple[pd.DataFrame, list[Construction]]:
    """Return the analysis's result and the constructions behind each row.

    The result is ``consolidation_coefficient_from_readings()``'s; a plot
    draws the constructions, so it shows the fit the result holds.
    """
    _check(df, display_units)
    notes: list[str] = []
    times = _in_unit(df, TIME, "time", _MINUTE, units)
    displacements = _in_unit(df, DISPLACEMENT, "small_length", _MM, units)
    kept = _kept(df, times, displacements, notes)
    groups = _groups(df, kept)
    keys = [_key(df, int(positions[0])) for positions in groups]
    ranges, records = _overrides(overrides, keys)
    first_rows = [int(positions[0]) for positions in groups]
    increments = df.iloc[first_rows]
    branch = _branches(increments, notes)
    heights = _average_heights(df, increments, units, notes)

    n = len(groups)
    values = {
        column: np.full(n, np.nan)
        for column in (
            ROOT_TIME_ZERO,
            DISPLACEMENT_90,
            TIME_90,
            ROOT_TIME,
            LOG_TIME_ZERO,
            DISPLACEMENT_100,
            DISPLACEMENT_50,
            TIME_50,
            LOG_TIME,
        )
    }
    reasons = {
        method: np.full(n, None, dtype=object) for method in (ROOT_TIME, LOG_TIME)
    }
    bases = {
        column: np.array(
            [OVERRIDE if method in ranges.get(key, {}) else RULE for key in keys],
            dtype=object,
        )
        for column, method in ((ROOT_TIME, ROOT_METHOD), (LOG_TIME, LOG_METHOD))
    }
    built: list[Construction] = []
    for i, positions in enumerate(groups):
        given = ranges.get(keys[i], {})
        if branch[i] == CONSTANT_STRESS:
            reasons[ROOT_TIME][i] = reasons[LOG_TIME][i] = CONSTANT
            built.append(Construction(keys[i], first_rows[i], None, None, None, given))
            continue
        readings = increment_readings(df.index, positions, times, displacements)
        root = root_time(readings, given.get(ROOT_METHOD, {}).get(EARLY))
        reasons[ROOT_TIME][i] = root.reason
        if root.reason is None:
            values[ROOT_TIME_ZERO][i] = readings.displacement(root.zero)
            values[DISPLACEMENT_90][i] = readings.displacement(root.movement)
            values[TIME_90][i] = root.time
            values[ROOT_TIME][i] = ROOT_TIME_COEFFICIENT * heights[i] ** 2 / root.time
        log = log_time(readings, given.get(LOG_METHOD))
        reasons[LOG_TIME][i] = log.reason
        if log.reason is None:
            values[LOG_TIME_ZERO][i] = readings.displacement(log.zero)
            values[DISPLACEMENT_100][i] = readings.displacement(log.movement_100)
            values[DISPLACEMENT_50][i] = readings.displacement(log.movement_50)
            values[TIME_50][i] = log.time
            values[LOG_TIME][i] = LOG_TIME_COEFFICIENT * heights[i] ** 2 / log.time
        built.append(Construction(keys[i], first_rows[i], readings, root, log, given))
        if np.isnan(heights[i]):
            for method in (ROOT_TIME, LOG_TIME):
                if reasons[method][i] is None:
                    reasons[method][i] = NO_HEIGHT

    result = _carried(increments, units, display_units)
    if "load_branch" not in result.columns:
        result["load_branch"] = pd.Series(branch, dtype=object)
    written_units: dict[str, str | None] = {}

    def write(column: str, data: np.ndarray, canonical: str, quantity: str) -> None:
        result[column], written_units[column] = _written(
            data, canonical, quantity, display_units
        )

    write(AVERAGE_HEIGHT, heights, _MM, "small_length")
    for method, columns in (
        (
            ROOT_TIME,
            ((ROOT_TIME_ZERO, _MM), (DISPLACEMENT_90, _MM), (TIME_90, _MINUTE)),
        ),
        (
            LOG_TIME,
            (
                (LOG_TIME_ZERO, _MM),
                (DISPLACEMENT_100, _MM),
                (DISPLACEMENT_50, _MM),
                (TIME_50, _MINUTE),
            ),
        ),
    ):
        for column, canonical in columns:
            quantity = "time" if canonical == _MINUTE else "small_length"
            write(column, values[column], canonical, quantity)
        write(method, values[method], _CV_UNIT, "consolidation_coefficient")
        result[f"{method}_basis"] = pd.Series(bases[method], dtype=object)
        result[f"{method}_reason"] = pd.Series(reasons[method], dtype=object)
    result.attrs["units"] = {**result.attrs.get("units", {}), **written_units}
    result.attrs["consolidation_coefficient_from_readings"] = {
        "notes": notes,
        "overrides": records,
    }
    return result, built


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


def root_time(readings: Readings, early_range: Range | None = None) -> RootTime:
    """Make the root time construction (BS 1377-5:1990, 3.6.3.3) on one increment.

    ``early_range``, (start, end) in minutes, overrides the early portion.
    """
    whole = _whole_reason(readings)
    if whole is not None:
        return RootTime(reason=whole)
    if early_range is None:
        early = readings.early
        if early.sum() < FEWEST:
            return RootTime(fitted=early, reason=FEW_EARLY)
    else:
        early = readings.after_load & _within(readings.times, early_range)
        if early.sum() < OVERRIDE_FEWEST:
            return RootTime(fitted=early, reason=_holds(EARLY, early.sum()))
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


def log_time(readings: Readings, ranges: Mapping[str, Range] | None = None) -> LogTime:
    """Make the log time construction (BS 1377-5:1990, 3.6.3.2) on one increment.

    ``ranges`` maps ``early``, ``inflexion`` and ``secondary`` to the (start,
    end) in minutes that override that part's rule.
    """
    ranges = ranges or {}
    whole = _whole_reason(readings)
    if whole is not None:
        return LogTime(reason=whole)
    t, y = readings.times, readings.movement
    positive = readings.after_load
    # Readings are sorted and none is negative, so those with t > 0 are the last ones.
    x = np.full(len(t), np.nan)
    x[positive] = np.log10(t[positive])
    last = t[-1]

    # The secondary line: the last log cycle of time (3.6.3.2.2, 3.6.5.2).
    if SECONDARY in ranges:
        in_last = positive & _within(t, ranges[SECONDARY])
        if in_last.sum() < OVERRIDE_FEWEST:
            return LogTime(reason=_holds(SECONDARY, in_last.sum()))
    else:
        in_last = positive & (t >= last / 10 * (1 - _SAME_TIME))
        if in_last.sum() < FEWEST:
            return LogTime(reason=FEW_SECONDARY)
    secondary = _line(x, y, in_last)

    # The tangent at the inflexion: the steepest three consecutive readings
    # before the last cycle, the earlier on a tie.
    tangent: Line | None = None
    if INFLEXION in ranges:
        fitted = positive & _within(t, ranges[INFLEXION])
        if fitted.sum() < OVERRIDE_FEWEST:
            return LogTime(secondary, reason=_holds(INFLEXION, fitted.sum()))
        tangent = _line(x, y, fitted)
    else:
        before = np.flatnonzero(positive[: int(np.flatnonzero(in_last)[0])])
        for k in range(len(before) - FEWEST + 1):
            fitted = np.zeros(len(t), dtype=bool)
            fitted[before[k : k + FEWEST]] = True
            line = _line(x, y, fitted)
            steeper = tangent is None or line.slope > tangent.slope
            if not np.isnan(line.slope) and steeper:
                tangent = line
    if tangent is None:
        return LogTime(secondary, reason=NO_TANGENT)
    if not (tangent.slope > 0 and tangent.slope >= STEEPER * secondary.slope):
        return LogTime(secondary, tangent, reason=NO_SECONDARY)

    # d0 from the three latest pairs t_i, 4 t_i on the convex-upward portion,
    # which ends at the tangent's middle reading (3.6.3.2.1).
    tangent_readings = np.flatnonzero(tangent.fitted)
    middle = t[tangent_readings[(len(tangent_readings) - 1) // 2]]
    if EARLY in ranges:
        # Every pair with both its times in the range.
        early_start, early_end = ranges[EARLY]
        both = _within(t, (early_start, early_end / PAIR_RATIO))
        pairs = np.flatnonzero(positive & both)
        if len(pairs) == 0:
            return LogTime(secondary, tangent, pairs, reason=NO_PAIR_IN_RANGE)
    else:
        paired = np.flatnonzero(
            positive & (PAIR_RATIO * t <= middle * (1 + _SAME_TIME))
        )
        if len(paired) < FEWEST:
            return LogTime(secondary, tangent, paired, reason=FEW_PAIRS)
        pairs = paired[-FEWEST:]
    later = np.interp(np.log10(PAIR_RATIO * t[pairs]), x[positive], y[positive])
    zero = float(np.mean(2 * y[pairs] - later))

    # d100 where the tangent and the secondary line cross (3.6.3.2.2).
    x_100 = (secondary.intercept - tangent.intercept) / (
        tangent.slope - secondary.slope
    )
    time_100 = float(10**x_100)
    movement_100 = tangent.at(x_100)
    if not middle <= time_100 <= last:
        return LogTime(secondary, tangent, pairs, zero, reason=OUTSIDE_100)

    # d50 midway, and t50 where the curve first reaches it (3.6.3.2.3).
    partial = LogTime(secondary, tangent, pairs, zero, time_100, movement_100)
    movement_50 = float((zero + movement_100) / 2)
    reached = np.flatnonzero(positive & (y >= movement_50))
    first = int(np.flatnonzero(positive)[0])
    if len(reached) == 0:
        return dataclasses.replace(
            partial, movement_50=movement_50, reason=AFTER_LAST_50
        )
    j = int(reached[0])
    if j == first:
        return dataclasses.replace(
            partial, movement_50=movement_50, reason=BEFORE_FIRST
        )
    share = (movement_50 - y[j - 1]) / (y[j] - y[j - 1])
    time_50 = float(10 ** (x[j - 1] + (x[j] - x[j - 1]) * share))
    return dataclasses.replace(partial, movement_50=movement_50, time=time_50)


def _within(times: np.ndarray, time_range: Range) -> np.ndarray:
    """Return True on the times in ``time_range``, inclusive, to their rounding."""
    start, end = time_range
    return (times >= start * (1 - _SAME_TIME)) & (times <= end * (1 + _SAME_TIME))


def _holds(portion: str, count: int) -> str:
    readings = "reading" if count == 1 else "readings"
    return f"the override for {portion} holds {count} {readings}"


def _line(x: np.ndarray, y: np.ndarray, fitted: np.ndarray) -> Line:
    intercept, slope = _least_squares(x[fitted], y[fitted])
    return Line(intercept, slope, fitted)


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


def _key(df: pd.DataFrame, position: int) -> tuple[str, str]:
    row = df.iloc[position]
    return str(row["specimen_id"]).strip(), str(row["test_stage"]).strip()


def _overrides(
    overrides: Any, keys: list[tuple[str, str]]
) -> tuple[dict[tuple[str, str], dict[str, dict[str, Range]]], list[dict[str, Any]]]:
    """Check the overrides; return each increment's ranges, in minutes, and the rows.

    Every error names the override's row as a spreadsheet numbers it (the
    header is row 1), so it can be found in the CSV it was read from.
    """
    if overrides is None:
        return {}, []
    if not isinstance(overrides, pd.DataFrame):
        raise HangtuError(
            f"overrides must be a pandas DataFrame, not {type(overrides).__name__}; "
            f"{_OVERRIDES_TEMPLATE} has its columns."
        )
    columns = template("consolidation_overrides").columns
    missing = [c for c in columns if c not in overrides.columns]
    if missing:
        raise ColumnError(
            f"overrides has no column {', '.join(map(repr, missing))}. Each override "
            "needs the increment (specimen_id, test_stage), the construction and "
            "part it overrides, the time range and the reason; "
            f"{_OVERRIDES_TEMPLATE} has the columns."
        )
    table = overrides.reset_index(drop=True)
    table.attrs = overrides.attrs
    starts = _override_times(table, _START_TIME)
    ends = _override_times(table, _END_TIME)
    known = set(keys)
    ranges: dict[tuple[str, str], dict[str, dict[str, Range]]] = {}
    seen: dict[tuple[str, str, str, str], int] = {}
    for i, row in table.iterrows():
        assert isinstance(i, int)  # reset_index gives a RangeIndex
        where = f"Override row {i + 2} (the header is row 1)"
        key = (_text(row["specimen_id"]), _text(row["test_stage"]))
        method, portion = _text(row[_METHOD]), _text(row[_PORTION])
        if key not in known:
            raise HangtuError(
                f"{where} is for specimen {key[0]!r} increment {key[1]!r}, which "
                "the readings don't have. Check its specimen_id and test_stage "
                "against the readings'; an override for no increment would leave "
                "the rule in place without saying so."
            )
        if method not in PORTIONS:
            raise HangtuError(
                f"{where} has {_METHOD} {method!r}. Use "
                f"{' or '.join(map(repr, PORTIONS))}."
            )
        if portion not in PORTIONS[LOG_METHOD]:
            raise HangtuError(
                f"{where} has {_PORTION} {portion!r}. Use "
                f"{', '.join(map(repr, PORTIONS[LOG_METHOD]))}."
            )
        if portion not in PORTIONS[method]:
            raise HangtuError(
                f"{where} gives the {portion} line for {method}, which has only an "
                f"early line. Use {_PORTION} 'early', or {_METHOD} 'log_time'."
            )
        start, end = float(starts[i]), float(ends[i])
        if np.isnan(start) or np.isnan(end):
            raise HangtuError(
                f"{where} has a blank {_START_TIME} or {_END_TIME}. Give both ends "
                "of the range."
            )
        if start > end:
            raise HangtuError(
                f"{where} has {_START_TIME} {start:g} after {_END_TIME} {end:g} "
                "(in minutes). Swap them."
            )
        if _text(row[_OVERRIDE_REASON]) == "":
            raise HangtuError(
                f"{where} has a blank {_OVERRIDE_REASON}. Say why the range "
                "replaces the rule's, so a reviewer reading the result knows."
            )
        full = (*key, method, portion)
        if full in seen:
            raise HangtuError(
                f"{where} repeats row {seen[full] + 2}: both give the {portion} line "
                f"of {method} for specimen {key[0]!r} increment {key[1]!r}. Keep "
                "one."
            )
        seen[full] = i
        ranges.setdefault(key, {}).setdefault(method, {})[portion] = (start, end)
    return ranges, overrides.to_dict("records")


def _override_times(table: pd.DataFrame, column: str) -> np.ndarray:
    """Return an override time column in minutes, its unit from ``attrs``."""
    values = numeric_column(table, column)
    declared = _units.resolve_units(table, [column], analysis=True)[column]
    parsed = _units.parse_unit(declared, column)
    _units.check_dimension(parsed, "time", column)
    return _units.convert(values, parsed, "time", _units.parse_unit(_MINUTE))


def _text(value: Any) -> str:
    return "" if pd.isna(value) else str(value).strip()


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
