"""Triaxial failure rows from readings during shearing (M11 c; P12 §4)."""

from collections.abc import Mapping
from typing import NamedTuple

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu.analysis._triaxial import DRAINED, is_multistage
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.registry import template

#: The columns that change from reading to reading; every other is the stage's.
READING_COLUMNS = (
    "axial_strain",
    "deviator_stress",
    "excess_pore_pressure",
    "volumetric_strain",
    "reported_failure_reading",
    "source_line",
)
REQUIRED = (
    "specimen_id",
    "test_type",
    "cell_pressure",
    "axial_strain",
    "deviator_stress",
)
#: Stress columns converted to ``cell_pressure``'s unit where present.
STRESSES = (
    "cell_pressure",
    "back_pressure",
    "deviator_stress",
    "excess_pore_pressure",
)
#: Each criterion, and how the failure rows write it (``TREG_FCR``'s wording).
CRITERIA = {
    "max_deviator_stress": "Maximum deviator stress",
    "max_stress_ratio": "Maximum principal stress ratio",
}


def triaxial_failure_from_readings(
    df: pd.DataFrame,
    *,
    failure_criterion: str | None = None,
    units: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    r"""Pick each triaxial stage's failure reading and return it as a stage row.

    Reads the readings taken during shearing, as
    ``ht.template("triaxial_readings")`` or ``p.triaxial_readings()`` lays
    them out, and returns one row
    per stage at failure in ``ht.template("triaxial")``'s shape, ready for
    ``ht.analysis.triaxial_failure_stresses()`` and then
    ``ht.analysis.mohr_coulomb_fit()`` or ``ht.plot.failure_envelope()``.
    ``ht.plot.triaxial_shearing()`` draws the same readings and marks the same
    failure reading.

    At each reading, with $\sigma_c$ the cell pressure, $u_b$ the back pressure,
    $q$ the deviator stress and $\Delta u$ the excess pore pressure:

    $$
    \sigma_3 = \sigma_c, \quad \sigma_1 = \sigma_3 + q, \quad
    u = u_b + \Delta u, \quad \sigma'_3 = \sigma_3 - u, \quad
    \sigma'_1 = \sigma'_3 + q
    $$

    These are definitions (effective stress, $\sigma' = \sigma - u$), used
    without a correlation or coefficient, as ``triaxial_failure_stresses()``
    uses them at failure. In a drained stage (``CD``, ``CDM``, ``CIDC``,
    ``CADC``) a blank $\Delta u$ is read as 0, the drained condition.

    **Each quantity has its own readings:** the rows with a $q$, the rows
    with a $\Delta u$ and the rows with an $\varepsilon_v$. A row may carry
    all three (a lab's export usually does) or one (``p.triaxial_readings()``
    from a file that gives each in its own group, at its own strains). For
    each quantity, the stage's **loading part** runs, in row order, to the
    last reading at its largest strain; the readings after it are the
    **unload tail** before the next stage of a multistage test, never a
    failure candidate and never interpolated from. Strain that decreases
    within a loading part (a reading out of place) gives a warning naming the
    stages, and the readings are used in their order.

    **$\Delta u$ and $\varepsilon_v$ at a $q$ reading** are the row's own
    where it has one. Otherwise, on a loading-part $q$ reading, they are
    interpolated linearly in strain between the stage's loading-part readings
    on either side (where several share a strain, the last in row order is
    used); outside those readings, and on a tail reading, they stay blank,
    never extrapolated. A warning names the stages whose value at the failure
    reading was interpolated rather than read.

    **The failure reading**, one per stage, by the first rule that applies:

    1. ``failure_criterion="max_deviator_stress"``: the reading with the
       largest $q$; ``"max_stress_ratio"``: the largest
       $\sigma'_1 / \sigma'_3$. The lab's ``reported_failure_reading`` is then
       ignored, with a warning when the readings have one.
    2. Otherwise the reading the lab marked in ``reported_failure_reading``.
    3. Otherwise an error. There is no default criterion: on an undrained
       curve the two pick different readings, and which is right depends on
       the test standard and the lab's report, not yet checked against the
       standards.

    Ties go to the first reading at the maximum, the lowest strain. Only
    loading-part $q$ readings are candidates: a tail reading, a reading with
    a blank strain or deviator stress, or (for the ratio) one with a blank
    effective stress, is never picked. Readings from a project's AGS file
    carry no lab mark, so they need ``failure_criterion=``.

    **Valid for:** triaxial compression, effective-stress stages (``CU``,
    ``CD`` and their variants) and total-stress ones (``UU``, with
    ``"max_deviator_stress"`` or a lab's mark). **Judgments taken:** none; the
    criterion is the caller's.

    **Assumptions:** the readings are the lab's, read as given: the deviator
    stress already corrected for area change and membrane, the cell and back
    pressure constant during the stage, the strains and $\Delta u$ measured
    from the start of shearing. ``effective_consolidation_stress`` is carried
    but not used: the effective stresses start at $\sigma_c - u_b$, so the
    failure row and the reading's stresses agree.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per reading: ``specimen_id`` (and ``test_stage`` for
        multistage tests), ``test_type``, ``cell_pressure``, ``axial_strain``
        and ``deviator_stress``; for effective stresses ``back_pressure`` and,
        in undrained stages, ``excess_pore_pressure``; optionally
        ``volumetric_strain``, ``reported_failure_reading`` and
        ``source_line``. Every other column is the stage's, the same on each
        of its readings. Stresses need declared units.
    failure_criterion : {"max_deviator_stress", "max_stress_ratio"}, optional
        How to pick each stage's failure reading. Without it, the lab's
        ``reported_failure_reading`` is used.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.

    Returns
    -------
    pandas.DataFrame
        One row per stage, in order of its first reading: the stage's columns,
        then ``deviator_stress_at_failure`` and ``pore_pressure_at_failure``
        ($u_b + \Delta u$, with $\Delta u$ 0 in a drained stage where it is
        blank, else blank where $\Delta u$ is; in ``cell_pressure``'s unit),
        ``axial_strain_at_failure``, ``volumetric_strain_at_failure``,
        ``multistage_test`` (a multistage type, or a specimen with more than
        one stage) and ``failure_criterion`` ("Maximum deviator stress" or
        "Maximum principal stress ratio" where a criterion was given, else the
        readings' own), in ``ht.template("triaxial")``'s order.

    Raises
    ------
    HangtuError
        For a missing column; a stage column that differs between a stage's
        readings; a stage with no failure reading, or two marked;
        ``"max_stress_ratio"`` on a stage without effective stresses or a
        reading with $\sigma'_3 \le 0$; a stress column without units or in a
        unit that isn't a stress.

    Examples
    --------
    >>> readings = ht.read_csv(
    ...     ht.examples.path("triaxial_readings.csv"),
    ...     units={
    ...         "cell_pressure": "psf",
    ...         "back_pressure": "psf",
    ...         "effective_consolidation_stress": "psf",
    ...         "deviator_stress": "psf",
    ...         "excess_pore_pressure": "psf",
    ...     },
    ... )
    >>> stages = ht.analysis.triaxial_failure_from_readings(
    ...     readings, failure_criterion="max_deviator_stress"
    ... )
    >>> fit = ht.analysis.mohr_coulomb_fit(
    ...     ht.analysis.triaxial_failure_stresses(stages)
    ... )
    """
    reduced = reduce_readings(df, failure_criterion, units)
    _warn_interpolated(reduced.interpolated)
    return reduced.rows


class Reduced(NamedTuple):
    """The readings, their stages, each stage's failure reading and the rows.

    ``interpolated`` names, per stage, the columns whose value at the failure
    reading was interpolated in strain rather than read (``strength.md`` §2).
    """

    readings: "Readings"
    stages: dict[tuple, np.ndarray]
    picks: dict[tuple, int]
    rows: pd.DataFrame
    interpolated: dict[tuple, list[str]]


def reduce_readings(
    df: pd.DataFrame, failure_criterion: str | None, units: Mapping[str, str] | None
) -> Reduced:
    """``triaxial_failure_from_readings()``, keeping what P12 draws from.

    Warns where strain decreases in a loading part, but not about
    interpolation at failure: the caller does (P12 draws without it).
    """
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if failure_criterion is not None and failure_criterion not in CRITERIA:
        raise HangtuError(
            f"failure_criterion={failure_criterion!r} isn't a criterion. Use "
            '"max_deviator_stress" or "max_stress_ratio", or leave it out to use '
            "the lab's reported_failure_reading."
        )
    missing = [column for column in REQUIRED if column not in df.columns]
    if missing:
        raise ColumnError(
            f"df has no column {', '.join(map(repr, missing))}. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}. Readings need their "
            "stage, test type, cell pressure, axial strain and deviator stress; "
            'ht.template("triaxial_readings") has the columns.'
        )
    readings = Readings(df, units)
    stages = readings.stages()
    marked = readings.marked()
    if failure_criterion is not None:
        picks = readings.pick(stages, failure_criterion)
        with_mark = [key for key, rows in stages.items() if marked[rows].any()]
        if with_mark:
            warn(
                f"{len(with_mark)} stage{'s' if len(with_mark) > 1 else ''} had a "
                f"reported_failure_reading, ignored for failure_criterion="
                f"{failure_criterion!r}. Leave the argument out to use the lab's."
            )
    else:
        picks = readings.marks(stages, marked)
    rows = readings.failure_rows(stages, picks, failure_criterion)
    interpolated = {
        key: names
        for key, pick in picks.items()
        if (names := readings.interpolated_at(pick))
    }
    return Reduced(readings, stages, picks, rows, interpolated)


def _warn_interpolated(interpolated: dict[tuple, list[str]]) -> None:
    """Name the stages whose Δu or εv at failure is another reading's (§2)."""
    if not interpolated:
        return
    n = len(interpolated)
    named = [
        f"{_name(key)} ({', '.join(names)})" for key, names in interpolated.items()
    ]
    more = f", and {n - 10} more" if n > 10 else ""
    warn(
        f"In {n} stage{'s' if n > 1 else ''}, the failure reading had no value of "
        f"its own for the quantity named, so its value was interpolated in strain "
        f"from that quantity's readings: {'; '.join(named[:10])}{more}. The failure "
        "row's pore_pressure_at_failure or volumetric_strain_at_failure is then "
        "not a value the lab read."
    )


class Readings:
    """The readings as arrays in one stress unit, and their stages."""

    def __init__(self, df: pd.DataFrame, units: Mapping[str, str] | None) -> None:
        self.df = df
        self.units = dict(units or {})
        # A column left blank (excess_pore_pressure in a file of drained or UU
        # stages) needs no unit; cell_pressure always does.
        present = [
            column
            for column in STRESSES
            if column in df.columns
            and (column == "cell_pressure" or df[column].notna().any())
        ]
        declared = _units.resolve_units(df, present, units, analysis=True)
        parsed = {
            column: _units.parse_unit(declared[column], column) for column in present
        }
        for column, unit in parsed.items():
            _units.check_dimension(unit, "stress", column)
        self.stress_unit = declared["cell_pressure"]
        to = parsed["cell_pressure"]

        def values(column: str) -> np.ndarray:
            if column not in df.columns or (
                column in STRESSES and column not in parsed
            ):
                return np.full(len(df), np.nan)
            if column in parsed:
                return _units.convert(
                    numeric_column(df, column), parsed[column], "stress", to
                )
            return numeric_column(df, column)

        self.cell = values("cell_pressure")
        self.back = values("back_pressure")
        self.deviator = values("deviator_stress")
        self.excess = values("excess_pore_pressure")
        self.strain = values("axial_strain")
        self.volumetric = values("volumetric_strain")
        types = df["test_type"].astype(object).where(df["test_type"].notna(), None)
        self.types = types
        self.drained = types.isin(DRAINED).to_numpy()
        # Set per stage by stages(): Δu and εv at each reading (own, or
        # interpolated at a loading-part q reading), which were interpolated,
        # and the loading-part q readings, the failure candidates.
        self.excess_at = self.excess.copy()
        self.volumetric_at = self.volumetric.copy()
        self.interpolated_excess = np.zeros(len(df), dtype=bool)
        self.interpolated_volumetric = np.zeros(len(df), dtype=bool)
        self.q_loading = np.zeros(len(df), dtype=bool)
        self._stresses()

    def _stresses(self) -> None:
        excess = np.where(self.drained & np.isnan(self.excess_at), 0.0, self.excess_at)
        self.pore = self.back + excess
        self.effective_minor = self.cell - self.pore
        self.effective_major = self.effective_minor + self.deviator

    def stages(self) -> dict[tuple, np.ndarray]:
        """Each stage's row positions, in order of its first reading."""
        df = self.df
        specimen = df["specimen_id"].astype(object).where(df["specimen_id"].notna())
        stage = (
            df["test_stage"].astype(object).where(df["test_stage"].notna())
            if "test_stage" in df.columns
            else pd.Series(None, index=df.index, dtype=object)
        )
        keys = list(zip(specimen, stage, strict=True))
        stages: dict[tuple, list[int]] = {}
        for position, key in enumerate(keys):
            stages.setdefault(_key(key), []).append(position)
        result = {key: np.array(rows) for key, rows in stages.items()}
        self._check_stage_columns(result)
        decreasing = [key for key, rows in result.items() if self._read_stage(rows)]
        self._stresses()
        if decreasing:
            n = len(decreasing)
            more = f", and {n - 10} more" if n > 10 else ""
            warn(
                f"axial_strain decreases within the loading part of {n} "
                f"stage{'s' if n > 1 else ''}: "
                f"{', '.join(_name(key) for key in decreasing[:10])}{more}. The "
                "readings are used in their order; check the file for a reading "
                "out of place."
            )
        return result

    def _check_stage_columns(self, stages: dict[tuple, np.ndarray]) -> None:
        columns = [c for c in self.df.columns if c not in READING_COLUMNS]
        differing = []
        for key, rows in stages.items():
            part = self.df.iloc[rows][columns]
            varies = [c for c in columns if part[c].nunique(dropna=False) > 1]
            if varies:
                differing.append(f"{_name(key)} ({', '.join(varies)})")
        if differing:
            raise HangtuError(
                f"Stage values differ between the readings of one stage, in "
                f"{'; '.join(differing[:5])}. Each stage's values (everything but "
                f"{', '.join(READING_COLUMNS)}) repeat on each of its readings; "
                "check the file, or give each stage its own test_stage."
            )

    def _read_stage(self, rows: np.ndarray) -> bool:
        """Find one stage's loading parts and fill Δu and εv at its q readings.

        Returns whether strain decreases within a loading part.
        """
        strain = self.strain
        has_strain = ~np.isnan(strain[rows])
        q_loading, _ = _loading_part(
            strain, rows[has_strain & ~np.isnan(self.deviator[rows])]
        )
        self.q_loading[q_loading] = True
        decreasing = _decreases(strain, q_loading)
        for values, filled, flags in (
            (self.excess, self.excess_at, self.interpolated_excess),
            (self.volumetric, self.volumetric_at, self.interpolated_volumetric),
        ):
            loading, _ = _loading_part(
                strain, rows[has_strain & ~np.isnan(values[rows])]
            )
            decreasing = decreasing or _decreases(strain, loading)
            targets = q_loading[np.isnan(values[q_loading])]
            if not len(loading) or not len(targets):
                continue
            at = _interpolate(strain[loading], values[loading], strain[targets])
            filled[targets] = at
            flags[targets] = ~np.isnan(at)
        return decreasing

    def interpolated_at(self, row: int) -> list[str]:
        """Return the columns whose value at ``row`` was interpolated."""
        names = []
        if self.interpolated_excess[row]:
            names.append("excess_pore_pressure")
        if self.interpolated_volumetric[row]:
            names.append("volumetric_strain")
        return names

    def marked(self) -> np.ndarray:
        if "reported_failure_reading" not in self.df.columns:
            return np.zeros(len(self.df), dtype=bool)
        # A blank column reads from a CSV as object; eq() leaves it all False
        # where fillna(False) would downcast it, with pandas' FutureWarning.
        return (
            self.df["reported_failure_reading"]
            .eq(True)
            .to_numpy(dtype=bool, na_value=False)
        )

    def pick(self, stages: dict[tuple, np.ndarray], criterion: str) -> dict:
        usable = self.q_loading.copy()
        if criterion == "max_deviator_stress":
            score = self.deviator
        else:
            no_effective = [
                _name(key)
                for key, rows in stages.items()
                if np.isnan(self.effective_minor[rows][usable[rows]]).all()
            ]
            if no_effective:
                raise HangtuError(
                    f'failure_criterion="max_stress_ratio" needs effective stresses, '
                    f"and there are none in {', '.join(no_effective[:5])} (a "
                    "total-stress test, or an undrained one without "
                    "excess_pore_pressure). Use "
                    '"max_deviator_stress", or leave those stages out.'
                )
            tension = usable & (self.effective_minor <= 0)
            if tension.any():
                raise HangtuError(
                    f"Readings {rows_text(self.df.index[tension])} have an effective "
                    "minor principal stress of 0 or less, where the principal stress "
                    "ratio has no meaning. The usual cause is a pore pressure with the "
                    "back pressure in it given as excess_pore_pressure."
                )
            usable = usable & ~np.isnan(self.effective_minor)
            with np.errstate(divide="ignore", invalid="ignore"):
                score = self.effective_major / self.effective_minor
        picks = {}
        empty = []
        for key, rows in stages.items():
            candidates = rows[usable[rows]]
            if not len(candidates):
                empty.append(_name(key))
                continue
            picks[key] = candidates[int(np.argmax(score[candidates]))]
        if empty:
            raise HangtuError(
                f"No reading has the values {criterion!r} needs in "
                f"{', '.join(empty[:5])}, so no failure reading can be picked."
            )
        return picks

    def marks(self, stages: dict[tuple, np.ndarray], marked: np.ndarray) -> dict:
        picks, none, several = {}, [], []
        for key, rows in stages.items():
            hits = rows[marked[rows]]
            if len(hits) == 1:
                picks[key] = hits[0]
            elif len(hits):
                several.append(_name(key))
            else:
                none.append(_name(key))
        if several:
            raise HangtuError(
                f"More than one reported_failure_reading is marked in "
                f"{', '.join(several[:5])}. Mark one reading per stage, or pick by "
                'failure_criterion="max_deviator_stress" or "max_stress_ratio".'
            )
        if none:
            raise HangtuError(
                f"No failure reading in {', '.join(none[:5])}: no "
                "reported_failure_reading is marked. Pick one with "
                'failure_criterion="max_deviator_stress" or "max_stress_ratio"; '
                "there's no default, since the two differ on undrained curves."
            )
        return picks

    def failure_rows(
        self, stages: dict[tuple, np.ndarray], picks: dict, criterion: str | None
    ) -> pd.DataFrame:
        df = self.df
        first = [rows[0] for rows in stages.values()]
        chosen = np.array([picks[key] for key in stages])
        carried = [c for c in df.columns if c not in READING_COLUMNS]
        result = df.iloc[first][carried].reset_index(drop=True)
        result["deviator_stress_at_failure"] = self.deviator[chosen]
        result["pore_pressure_at_failure"] = self.pore[chosen]
        result["axial_strain_at_failure"] = self.strain[chosen]
        result["volumetric_strain_at_failure"] = self.volumetric_at[chosen]
        specimens = pd.Series([key[0] for key in stages])
        counts = specimens.map(specimens.value_counts())
        result["multistage_test"] = is_multistage(
            result["test_type"], counts
        ).to_numpy()
        if criterion is not None:
            result["failure_criterion"] = CRITERIA[criterion]
        elif "failure_criterion" not in result.columns:
            result["failure_criterion"] = None
        order = list(template("triaxial").columns)
        known = [c for c in order if c in result.columns]
        result = result[known + [c for c in result.columns if c not in known]]
        declared = {**_units.units_of(df), **self.units}
        units: dict[str, str | None] = {
            c: u for c, u in declared.items() if c in result.columns
        }
        units.update(
            dict.fromkeys(
                ["deviator_stress_at_failure", "pore_pressure_at_failure"],
                self.stress_unit,
            )
        )
        for reading, failure in (
            ("axial_strain", "axial_strain_at_failure"),
            ("volumetric_strain", "volumetric_strain_at_failure"),
        ):
            if reading in declared:
                units[failure] = declared[reading]
        result.attrs["units"] = units
        return result


def _loading_part(
    strain: np.ndarray, rows: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Split one quantity's readings, in row order, into loading part and tail.

    The loading part runs to the last reading at the largest strain; the
    readings after it are the unload tail (``strength.md`` §2).
    """
    if not len(rows):
        return rows, rows
    values = strain[rows]
    last = int(np.flatnonzero(values == values.max())[-1])
    return rows[: last + 1], rows[last + 1 :]


def _decreases(strain: np.ndarray, rows: np.ndarray) -> bool:
    return bool((np.diff(strain[rows]) < 0).any())


def _interpolate(strains: np.ndarray, values: np.ndarray, at: np.ndarray) -> np.ndarray:
    """Linear in strain, the last of equal strains in row order; blank outside."""
    order = np.argsort(strains, kind="stable")
    strains, values = strains[order], values[order]
    last = np.append(strains[1:] != strains[:-1], True)
    strains, values = strains[last], values[last]
    result = np.interp(at, strains, values)
    result[(at < strains[0]) | (at > strains[-1])] = np.nan
    return result


def _key(key: tuple) -> tuple:
    return tuple(None if pd.isna(part) else part for part in key)


def _name(key: tuple) -> str:
    specimen, stage = key
    return str(specimen) if stage is None else f"{specimen} stage {stage}"
