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
from hangtu.analysis._triaxial_readings import reduce_readings
from hangtu.errors import ColumnError, HangtuError, UnitsError

GOLDENS = Path(__file__).parents[1] / "data" / "triaxial_readings_goldens.csv"
STRESSES = ["cell_pressure", "back_pressure", "deviator_stress", "excess_pore_pressure"]
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


def test_r2_decreasing_strain_warns():
    df = readings("E", axial_strain=[0, 4, 2, 6])
    with pytest.warns(
        UserWarning,
        match=r"axial_strain decreases within the loading part of 1 "
        r"stage: E stage 1",
    ):
        rows = ht.analysis.triaxial_failure_from_readings(
            df, failure_criterion="max_deviator_stress"
        )
    # Used in their order: the tie at q 150 goes to the first, at 4 %.
    assert rows["axial_strain_at_failure"].item() == 4


def test_r1_swapped_readings_warn_naming_stage_a():
    a = readings("A", "B")
    a.iloc[[2, 3]] = a.iloc[[3, 2]].to_numpy()
    with pytest.warns(UserWarning, match=r"loading part of 1 stage: A stage 1\."):
        ht.analysis.triaxial_failure_from_readings(
            a, failure_criterion="max_deviator_stress"
        )


def test_two_stages_under_one_specimen_still_raise():
    a = readings("A")
    two = pd.concat([a, a.assign(cell_pressure=500)]).drop(columns="test_stage")
    two.attrs["units"] = a.attrs["units"]
    with pytest.raises(HangtuError, match=r"differ.*in A \(cell_pressure\)"):
        failure(two, failure_criterion="max_deviator_stress")


def test_r2_a_differing_stage_column_raises():
    df = readings("E", cell_pressure=[400, 400, 410, 400])
    with pytest.raises(HangtuError, match=r"differ.*in E stage 1 \(cell_pressure\)"):
        failure(df, failure_criterion="max_deviator_stress")


def test_r3_drained_without_excess_pore_pressure():
    for criterion in ("max_deviator_stress", "max_stress_ratio"):
        rows = failure(readings("C"), failure_criterion=criterion)
        assert rows["axial_strain_at_failure"].item() == 6
        # Drained: a blank Δu is 0, so u_f is the back pressure.
        assert rows["pore_pressure_at_failure"].item() == 200
        assert rows["volumetric_strain_at_failure"].item() == -0.4
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


# --- M16: one quantity per row, unload tails, interpolation -------------------------
# The readings of docs/work/m16-curves.md's acceptance criteria, as
# p.triaxial_readings() gives them: each quantity in its own rows, at its own
# strains, in file order (q rows, then Δu or εv rows).

INTERPOLATED = r"interpolated in strain"
BH1_Q = [
    (0.0, 0), (2.0, 100), (4.0, 150), (6.0, 170), (8.5, 180),
    (10.0, 176), (12.0, 170), (11.8, 80), (11.6, 5),
]  # fmt: skip
BH1_DU = [(0.0, 0), (3.0, 40), (7.0, 56), (10.0, 64), (12.0, 66), (11.7, 60)]
BH2_Q = [(0, 0), (2, 500), (4, 800), (6, 900), (7, 880)]
BH2_EV = [(0, 0), (3, 2.0), (5, 3.0), (7, 3.8)]
J1_Q = [(0.0, 0), (1.0, 50), (2.0, 80), (1.9, 85), (3.0, 90), (4.0, 88)]
J1_DU = [(0.0, 0), (1.5, 20), (2.5, 30)]


def stage_rows(specimen, test_type, cell, back, quantities, stage="1"):
    """One stage's readings, each quantity's (strain, value) pairs in its rows."""
    rows = []
    for column, pairs in quantities:
        for strain, value in pairs:
            rows.append({"axial_strain": strain, column: value})
    df = pd.DataFrame(rows)
    for column in ("deviator_stress", "excess_pore_pressure", "volumetric_strain"):
        if column not in df.columns:
            df[column] = np.nan
    stage_values = {
        "specimen_id": specimen,
        "test_stage": stage,
        "test_type": test_type,
        "cell_pressure": cell,
        "back_pressure": back,
        "effective_consolidation_stress": cell - back,
    }
    return df.assign(**stage_values)[
        [*stage_values, "axial_strain", "deviator_stress", "excess_pore_pressure",
         "volumetric_strain"]
    ]  # fmt: skip


def ags_shaped(scale=1.0, unit="kPa"):
    """BH1-U3 stage 1 (CU) and BH2-U2 stage 3 (CDM), stresses times ``scale``."""
    df = pd.concat(
        [
            stage_rows(
                "BH1-U3", "CU", 400, 300,
                [("deviator_stress", BH1_Q), ("excess_pore_pressure", BH1_DU)],
            ),
            stage_rows(
                "BH2-U2", "CDM", 700, 300,
                [("deviator_stress", BH2_Q), ("volumetric_strain", BH2_EV)],
                stage="3",
            ),
        ],
        ignore_index=True,
    )  # fmt: skip
    df["source_line"] = range(200, 200 + len(df))
    stresses = [*STRESSES, "effective_consolidation_stress"]
    df[stresses] = df[stresses] * scale
    df.attrs["units"] = dict.fromkeys(stresses, unit)
    return df


def joins_shaped():
    """J1-U3 stage 1, with the readings p.triaxial_readings() leaves out removed."""
    df = stage_rows(
        "J1-U3", "CU", 400, 300,
        [("deviator_stress", J1_Q), ("excess_pore_pressure", J1_DU)],
    )  # fmt: skip
    df.attrs["units"] = dict.fromkeys(STRESSES, "kPa")
    return df


@pytest.mark.parametrize(("scale", "unit"), [(1.0, "kPa"), (1 / PSF, "psf")])
def test_ags_readings_max_deviator_stress(scale, unit):
    with pytest.warns(UserWarning, match=INTERPOLATED) as record:
        rows = ht.analysis.triaxial_failure_from_readings(
            ags_shaped(scale, unit), failure_criterion="max_deviator_stress"
        )
    assert len(record) == 1
    message = str(record[0].message)
    assert "2 stages" in message
    assert "BH1-U3 stage 1 (excess_pore_pressure)" in message
    assert "BH2-U2 stage 3 (volumetric_strain)" in message
    assert list(rows["axial_strain_at_failure"]) == [8.5, 6.0]
    assert list(rows["deviator_stress_at_failure"] / scale) == pytest.approx(
        [180, 900], rel=1e-9
    )
    # BH1-U3: Δu 56 + 8 × 1.5/3 = 60; BH2-U2 drained: u_f the back pressure.
    assert list(rows["pore_pressure_at_failure"] / scale) == pytest.approx(
        [360, 300], rel=1e-9
    )
    assert np.isnan(rows["volumetric_strain_at_failure"][0])
    assert rows["volumetric_strain_at_failure"][1] == pytest.approx(3.4, rel=1e-9)
    assert rows.attrs["units"]["pore_pressure_at_failure"] == unit
    assert "source_line" not in rows.columns


def test_ags_readings_values_at_each_q_reading():
    reduced = reduce_readings(ags_shaped(), "max_deviator_stress", None)
    readings = reduced.readings
    q_rows = np.arange(len(BH1_Q))
    expected = [0, 40 * 2 / 3, 44, 52, 60, 64, 66, np.nan, np.nan]
    assert readings.excess_at[q_rows] == pytest.approx(expected, rel=1e-9, nan_ok=True)
    assert list(readings.q_loading[q_rows]) == [True] * 7 + [False] * 2
    # Own value at 10.0 %, interpolated elsewhere, nothing on the tail.
    assert list(readings.interpolated_excess[q_rows]) == [
        True, True, True, True, True, True, True, False, False,
    ]  # fmt: skip
    # A Δu row keeps its own value; the q rows of BH2-U2 get εv.
    assert readings.excess_at[len(BH1_Q) + 5] == 60
    bh2 = len(BH1_Q) + len(BH1_DU) + np.arange(len(BH2_Q))
    assert readings.volumetric_at[bh2] == pytest.approx(
        [0, 2 / 3 * 2.0, 2.5, 3.4, 3.8], rel=1e-9
    )


def test_ags_readings_max_stress_ratio():
    with pytest.warns(UserWarning, match=INTERPOLATED) as record:
        rows = ht.analysis.triaxial_failure_from_readings(
            ags_shaped().query("specimen_id == 'BH1-U3'"),
            failure_criterion="max_stress_ratio",
        )
    assert len(record) == 1
    assert "1 stage had" in str(record[0].message)
    assert "BH1-U3 stage 1 (excess_pore_pressure)" in str(record[0].message)
    # σ′3 = 400 - 300 - 66 = 34, σ′1 = 204: ratio 6.0, above 5.5 and 5.888889.
    assert rows["axial_strain_at_failure"].item() == 12.0
    assert rows["deviator_stress_at_failure"].item() == 170
    assert rows["pore_pressure_at_failure"].item() == pytest.approx(366, rel=1e-9)


def test_a_tail_reading_with_the_largest_q_is_not_picked():
    df = joins_shaped()
    tail = df.iloc[[0]].assign(axial_strain=3.5, deviator_stress=500.0)
    df = pd.concat([df.iloc[: len(J1_Q)], tail, df.iloc[len(J1_Q) :]])
    df.attrs["units"] = dict.fromkeys(STRESSES, "kPa")
    with pytest.warns(UserWarning, match="decreases"):
        rows = ht.analysis.triaxial_failure_from_readings(
            df, failure_criterion="max_deviator_stress"
        )
    assert rows["deviator_stress_at_failure"].item() == 90


def test_equal_strains_in_the_readings_take_the_last():
    df = stage_rows(
        "S", "CU", 400, 300,
        [
            ("deviator_stress", [(0.0, 0), (1.0, 50), (2.0, 80)]),
            ("excess_pore_pressure", [(0.0, 0), (1.5, 10), (1.5, 20), (3.0, 50)]),
        ],
    )  # fmt: skip
    df.attrs["units"] = dict.fromkeys(STRESSES, "kPa")
    reduced = reduce_readings(df, "max_deviator_stress", None)
    # At 1.0 %: 0 + 20 × 1/1.5; at 2.0 %: 20 + 30 × 0.5/1.5.
    assert reduced.readings.excess_at[:3] == pytest.approx([0, 40 / 3, 30], rel=1e-9)


def test_joins_max_deviator_stress():
    with pytest.warns(UserWarning) as record:
        rows = ht.analysis.triaxial_failure_from_readings(
            joins_shaped(), failure_criterion="max_deviator_stress"
        )
    messages = [str(w.message) for w in record]
    assert len(messages) == 1
    assert (
        "axial_strain decreases within the loading part of 1 stage: J1-U3 stage 1"
        in (messages[0])
    )
    # 3.0 % is outside the Δu readings (0-2.5 %): u_f blank, nothing interpolated.
    assert rows["axial_strain_at_failure"].item() == 3.0
    assert rows["deviator_stress_at_failure"].item() == 90
    assert np.isnan(rows["pore_pressure_at_failure"].item())


def test_joins_max_stress_ratio():
    with pytest.warns(UserWarning) as record:
        rows = ht.analysis.triaxial_failure_from_readings(
            joins_shaped(), failure_criterion="max_stress_ratio"
        )
    messages = [str(w.message) for w in record]
    assert len(messages) == 2
    assert "decreases" in messages[0]
    assert "1 stage had" in messages[1] and "J1-U3 stage 1" in messages[1]
    with pytest.warns(UserWarning, match="decreases"):
        readings_ = reduce_readings(joins_shaped(), "max_stress_ratio", None).readings
    candidates = np.arange(4)
    ratio = readings_.effective_major / readings_.effective_minor
    assert ratio[candidates] == pytest.approx(
        [1, 136.666667 / 86.666667, 155 / 75, 161 / 76], rel=1e-8
    )
    # 3.0 and 4.0 % are outside the Δu readings: no ratio, not candidates.
    assert np.isnan(ratio[4:6]).all()
    assert rows["axial_strain_at_failure"].item() == 1.9
    assert rows["deviator_stress_at_failure"].item() == 85
    assert rows["pore_pressure_at_failure"].item() == pytest.approx(324, rel=1e-9)


def test_rows_with_every_quantity_warn_nothing_about_interpolation():
    failure(readings(), failure_criterion="max_deviator_stress")
    failure(readings("A", "B", "C", "E"), failure_criterion="max_stress_ratio")
