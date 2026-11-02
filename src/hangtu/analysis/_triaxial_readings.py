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

    Reads the readings taken during shearing, one row per strain step, as
    ``ht.template("triaxial_readings")`` lays them out, and returns one row
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

    **The failure reading**, one per stage, by the first rule that applies:

    1. ``failure_criterion="max_deviator_stress"``: the reading with the
       largest $q$; ``"max_stress_ratio"``: the largest
       $\sigma'_1 / \sigma'_3$. The lab's ``reported_failure_reading`` is then
       ignored, with a warning when the readings have one.
    2. Otherwise the reading the lab marked in ``reported_failure_reading``.
    3. Otherwise an error. There is no default criterion: on an undrained
       curve the two pick different readings, and which is right depends on
       the test standard and the lab's report (TODO #53).

    Ties go to the first reading at the maximum, the lowest strain. A reading
    with a blank strain or deviator stress, or (for the ratio) a blank
    effective stress, is never picked.

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
        ``volumetric_strain`` and ``reported_failure_reading``. Every other
        column is the stage's, the same on each of its readings. Stresses need
        declared units.
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
        ($u_b + \Delta u$, blank where $\Delta u$ is; in ``cell_pressure``'s
        unit), ``axial_strain_at_failure``, ``volumetric_strain_at_failure``,
        ``multistage_test`` (a multistage type, or a specimen with more than
        one stage) and ``failure_criterion`` ("Maximum deviator stress" or
        "Maximum principal stress ratio" where a criterion was given, else the
        readings' own), in ``ht.template("triaxial")``'s order.

    Raises
    ------
    HangtuError
        For a missing column; a stage column that differs between a stage's
        readings; strain that decreases within a stage; a stage with no
        failure reading, or two marked; ``"max_stress_ratio"`` on a stage
        without effective stresses or a reading with $\sigma'_3 \le 0$; a
        stress column without units or in a unit that isn't a stress.

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
    return reduce_readings(df, failure_criterion, units).rows


class Reduced(NamedTuple):
    """The readings, their stages, each stage's failure reading and the rows."""

    readings: "Readings"
    stages: dict[tuple, np.ndarray]
    picks: dict[tuple, int]
    rows: pd.DataFrame


def reduce_readings(
    df: pd.DataFrame, failure_criterion: str | None, units: Mapping[str, str] | None
) -> Reduced:
    """``triaxial_failure_from_readings()``, keeping what P12 draws from."""
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
    return Reduced(readings, stages, picks, rows)


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
        drained = types.isin(DRAINED).to_numpy()
        excess = np.where(drained & np.isnan(self.excess), 0.0, self.excess)
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
        self._check_strain(result)
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

    def _check_strain(self, stages: dict[tuple, np.ndarray]) -> None:
        bad = []
        for key, rows in stages.items():
            strain = self.strain[rows]
            strain = strain[~np.isnan(strain)]
            if (np.diff(strain) < 0).any():
                bad.append(_name(key))
        if bad:
            raise HangtuError(
                "axial_strain decreases within a stage, in "
                f"{', '.join(bad[:5])}. Readings go in strain order within a "
                "stage: sort them, or give two stages under one specimen_id their "
                "own test_stage."
            )

    def marked(self) -> np.ndarray:
        if "reported_failure_reading" not in self.df.columns:
            return np.zeros(len(self.df), dtype=bool)
        column = self.df["reported_failure_reading"]
        return column.fillna(False).astype(bool).to_numpy()

    def pick(self, stages: dict[tuple, np.ndarray], criterion: str) -> dict:
        usable = ~np.isnan(self.strain) & ~np.isnan(self.deviator)
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
        pore = self.back[chosen] + self.excess[chosen]
        result["pore_pressure_at_failure"] = pore
        result["axial_strain_at_failure"] = self.strain[chosen]
        result["volumetric_strain_at_failure"] = self.volumetric[chosen]
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


def _key(key: tuple) -> tuple:
    return tuple(None if pd.isna(part) else part for part in key)


def _name(key: tuple) -> str:
    specimen, stage = key
    return str(specimen) if stage is None else f"{specimen} stage {stage}"
