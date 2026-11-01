"""ht.analysis.triaxial_failure_from_readings() (docs/work/m11c-triaxial-shearing.md).

The readings are the spec's "Golden readings", in
``tests/data/triaxial_readings_goldens.csv`` (kPa and percent): R1 is stages A
and B (CU), R2 stage E (a tie), R3 stage C (CD, Δu blank), R4 stage D (UU).
Expected values are the spec's hand calculations: per reading
σ′3 = cell - (back + Δu), σ′1 = σ′3 + q.
"""

import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError, UnitsError

GOLDENS = Path(__file__).parents[1] / "data" / "triaxial_readings_goldens.csv"
STRESSES = ["cell_pressure", "back_pressure", "deviator_stress", "excess_pore_pressure"]
BACK_PRESSURE = r"1 drained stage had no pore_pressure_at_failure"
REL = 1e-7
#: 1 psf in kPa: 0.45359237 kg × 9.80665 m/s² / 0.3048² m² (exact).
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000


def readings(*stages, **columns):
    """The golden readings of ``stages`` (all when none), in kPa."""
    df = pd.read_csv(GOLDENS, dtype={"test_stage": str})
    if stages:
        df = df[df["specimen_id"].isin(stages)].reset_index(drop=True)
    for column, values in columns.items():
        df[column] = values
    df.attrs["units"] = dict.fromkeys(STRESSES, "kPa")
    return df


def failure(df, **kwargs):
    """Failure rows, failing on any warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return ht.analysis.triaxial_failure_from_readings(df, **kwargs)


def fit_of(rows):
    stresses = ht.analysis.triaxial_failure_stresses(rows)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return ht.analysis.mohr_coulomb_fit(stresses).to_frame().iloc[0]


# --- AC 1-3: R1 and the failure reading ---------------------------------------------


def test_r1_max_deviator_stress_gives_p11_golden_1():
    rows = failure(readings("A", "B"), failure_criterion="max_deviator_stress")
    assert list(rows["specimen_id"]) == ["A", "B"]
    assert list(rows["deviator_stress_at_failure"]) == [200, 300]
    assert list(rows["pore_pressure_at_failure"]) == [300, 300]
    assert list(rows["axial_strain_at_failure"]) == [8, 8]
    assert set(rows["failure_criterion"]) == {"Maximum deviator stress"}
    stresses = ht.analysis.triaxial_failure_stresses(rows)
    assert list(stresses["effective_minor_principal_stress_at_failure"]) == [100, 200]
    assert list(stresses["effective_major_principal_stress_at_failure"]) == [300, 500]
    fit = fit_of(rows)
    assert fit["effective_cohesion"] == pytest.approx(25 * math.sqrt(2), rel=REL)
    assert fit["effective_friction_angle"] == pytest.approx(19.471221, rel=REL)


def test_r1_max_stress_ratio():
    rows = failure(readings("A", "B"), failure_criterion="max_stress_ratio")
    assert list(rows["deviator_stress_at_failure"]) == [195, 290]
    assert list(rows["pore_pressure_at_failure"]) == [310, 315]
    assert list(rows["axial_strain_at_failure"]) == [12, 12]
    assert set(rows["failure_criterion"]) == {"Maximum principal stress ratio"}
    fit = fit_of(rows)
    assert fit["effective_cohesion"] == pytest.approx(37.123106, rel=REL)
    assert fit["effective_friction_angle"] == pytest.approx(19.471221, rel=REL)
    assert fit["lowest_normal_stress"] == pytest.approx(155, rel=REL)
    assert fit["highest_normal_stress"] == pytest.approx(281.66667, rel=REL)


def _marked_at_12():
    df = readings("A", "B")
    df["reported_failure_reading"] = df["axial_strain"] == 12
    return df


def test_the_lab_mark_is_used_without_an_argument():
    rows = failure(_marked_at_12())
    assert list(rows["deviator_stress_at_failure"]) == [195, 290]
    assert list(rows["axial_strain_at_failure"]) == [12, 12]
    assert set(rows["failure_criterion"]) == {"Maximum deviator stress"}


def test_an_argument_overrides_the_mark_with_a_warning():
    with pytest.warns(UserWarning, match="2 stages had a reported_failure_reading"):
        rows = ht.analysis.triaxial_failure_from_readings(
            _marked_at_12(), failure_criterion="max_deviator_stress"
        )
    assert list(rows["deviator_stress_at_failure"]) == [200, 300]


def test_no_mark_and_no_argument_raises():
    with pytest.raises(
        HangtuError,
        match=r"No failure reading in A stage 1, B stage 1.*failure_criterion=",
    ):
        failure(readings("A", "B"))


def test_two_marks_in_a_stage_raise():
    df = readings("A", "B")
    df["reported_failure_reading"] = df["axial_strain"] >= 12
    with pytest.raises(
        HangtuError,
        match=r"More than one reported_failure_reading is marked in A stage 1, B",
    ):
        failure(df)


# --- AC 4-6: R2, R3, R4 -------------------------------------------------------------


def test_r2_a_tie_goes_to_the_lowest_strain():
    rows = failure(readings("E"), failure_criterion="max_deviator_stress")
    assert rows["axial_strain_at_failure"].item() == 2
    assert rows["pore_pressure_at_failure"].item() == 250


def test_r2_decreasing_strain_raises():
    df = readings("E", axial_strain=[0, 4, 2, 6])
    with pytest.raises(
        HangtuError, match=r"axial_strain decreases within a stage, in E stage 1"
    ):
        failure(df, failure_criterion="max_deviator_stress")


def test_r2_a_differing_stage_column_raises():
    df = readings("E", cell_pressure=[400, 400, 410, 400])
    with pytest.raises(HangtuError, match=r"differ.*in E stage 1 \(cell_pressure\)"):
        failure(df, failure_criterion="max_deviator_stress")


def test_r3_drained_without_excess_pore_pressure():
    for criterion in ("max_deviator_stress", "max_stress_ratio"):
        rows = failure(readings("C"), failure_criterion=criterion)
        assert rows["axial_strain_at_failure"].item() == 6
        assert np.isnan(rows["pore_pressure_at_failure"].item())
        assert rows["volumetric_strain_at_failure"].item() == -0.4
    with pytest.warns(UserWarning, match=BACK_PRESSURE):
        stresses = ht.analysis.triaxial_failure_stresses(rows)
    assert stresses["effective_minor_principal_stress_at_failure"].item() == 100
    assert stresses["effective_major_principal_stress_at_failure"].item() == 350


def test_r4_undrained_total_stress():
    rows = failure(readings("D"), failure_criterion="max_deviator_stress")
    assert rows["axial_strain_at_failure"].item() == 5
    assert rows["deviator_stress_at_failure"].item() == 120
    stresses = ht.analysis.triaxial_failure_stresses(rows)
    assert stresses["minor_principal_stress_at_failure"].item() == 200
    assert stresses["major_principal_stress_at_failure"].item() == 320
    assert np.isnan(stresses["effective_minor_principal_stress_at_failure"].item())


def test_r4_max_stress_ratio_raises():
    with pytest.raises(
        HangtuError, match=r"needs effective stresses, and there are none in D stage 1"
    ):
        failure(readings("D"), failure_criterion="max_stress_ratio")


# --- AC 7-8: rows and errors --------------------------------------------------------


def test_rows_follow_the_triaxial_template():
    df = pd.concat([readings("B"), readings("A")], ignore_index=True)
    df["geology_unit"] = "ALV"
    df.attrs["units"] = dict.fromkeys(STRESSES, "kPa")
    rows = failure(df, failure_criterion="max_deviator_stress")
    assert list(rows["specimen_id"]) == ["B", "A"]
    assert (rows["geology_unit"] == "ALV").all()
    order = list(ht.template("triaxial").columns)
    assert list(rows.columns) == [c for c in order if c in rows.columns]
    for reading in ("axial_strain", "deviator_stress", "excess_pore_pressure"):
        assert reading not in rows.columns
    assert rows.attrs["units"]["deviator_stress_at_failure"] == "kPa"
    assert rows.attrs["units"]["pore_pressure_at_failure"] == "kPa"
    assert not rows["multistage_test"].any()


def test_multistage_by_type_and_by_stage_count():
    a = readings("A")
    two = pd.concat([a, a.assign(test_stage="2", cell_pressure=500)])
    two.attrs["units"] = a.attrs["units"]
    rows = failure(two, failure_criterion="max_deviator_stress")
    assert list(rows["test_stage"]) == ["1", "2"]
    assert rows["multistage_test"].all()
    cdm = readings("C", test_type="CDM")
    assert failure(cdm, failure_criterion="max_deviator_stress")[
        "multistage_test"
    ].item()


def test_without_test_stage_a_specimen_is_one_stage():
    df = readings("A").drop(columns="test_stage")
    rows = failure(df, failure_criterion="max_deviator_stress")
    assert len(rows) == 1
    assert "test_stage" not in rows.columns


def test_a_missing_column_names_the_template():
    df = readings("A").drop(columns="deviator_stress")
    with pytest.raises(ColumnError, match=r"'deviator_stress'.*triaxial_readings"):
        failure(df, failure_criterion="max_deviator_stress")


def test_stresses_need_units():
    df = readings("A")
    df.attrs["units"] = {}
    with pytest.raises(UnitsError, match="cell_pressure"):
        failure(df, failure_criterion="max_deviator_stress")


def test_a_blank_column_needs_no_units():
    df = readings("D")
    df.attrs["units"] = {"cell_pressure": "kPa", "deviator_stress": "kPa"}
    assert len(failure(df, failure_criterion="max_deviator_stress")) == 1


def test_converts_to_the_cell_pressure_unit():
    df = readings("A", "B")
    df["back_pressure"] = df["back_pressure"] / PSF
    df.attrs["units"] = {**df.attrs["units"], "back_pressure": "psf"}
    rows = failure(df, failure_criterion="max_deviator_stress")
    assert list(rows["pore_pressure_at_failure"]) == pytest.approx(
        [300, 300], rel=1e-12
    )
    assert rows.attrs["units"]["back_pressure"] == "psf"


def test_tension_under_the_ratio_raises():
    df = readings("A", excess_pore_pressure=[0, 50, 90, 100, 210, 112])
    with pytest.raises(HangtuError, match=r"Readings 4 have an effective minor"):
        failure(df, failure_criterion="max_stress_ratio")


def test_blank_readings_are_not_picked():
    df = readings("A", deviator_stress=[0, 100, 180, None, 195, 190])
    rows = failure(df, failure_criterion="max_deviator_stress")
    assert rows["axial_strain_at_failure"].item() == 12


def test_an_unknown_criterion_raises():
    with pytest.raises(HangtuError, match=r"'peak' isn't a criterion"):
        failure(readings("A"), failure_criterion="peak")
