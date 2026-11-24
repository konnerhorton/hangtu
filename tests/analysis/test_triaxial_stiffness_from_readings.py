"""ht.analysis.triaxial_stiffness_from_readings() (docs/analysis/stiffness.md §1-2).

Golden values are the M23 (b) spec's hand calculations: G1 a drained stage on
PLAXIS's hyperbola, G3 G1 with q_0 = 50 kPa, G2 the example's B-1-U5 specimen 1.
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError, UnitsError

from .conftest import STRESSES, g1, stage_frame, stages_frame, triaxial_goldens

DATA = Path(ht.examples.path("site.ags")).parent
#: 1 psf in kPa (exact).
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000
MODULUS = "secant_modulus_at_50_percent_peak"
STRAIN = "axial_strain_at_50_percent_peak"
MODULUS_REASON = "secant_modulus_at_50_percent_peak_reason"
RATIO = "failure_ratio"
ASYMPTOTE = "asymptotic_deviator_stress"
R_SQUARED = "failure_ratio_r_squared"
RATIO_REASON = "failure_ratio_reason"
ADDED = [MODULUS, STRAIN, MODULUS_REASON, RATIO, ASYMPTOTE, R_SQUARED, RATIO_REASON]
MAX_Q = "max_deviator_stress"
EXAMPLE_STRESSES = [
    "cell_pressure",
    "back_pressure",
    "effective_consolidation_stress",
    "deviator_stress",
    "excess_pore_pressure",
]


def stiffness(df, **kwargs):
    """The analysis, failing on any warning."""
    kwargs.setdefault("failure_criterion", MAX_Q)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return ht.analysis.triaxial_stiffness_from_readings(df, **kwargs)


def assert_value_or_reason(rows):
    """AC 7: each pair has a value or a reason, never both and never neither."""
    for value, reason in ((MODULUS, MODULUS_REASON), (RATIO, RATIO_REASON)):
        has_value = rows[value].notna()
        has_reason = rows[reason].notna()
        assert (has_value ^ has_reason).all(), (value, rows[[value, reason]])


# --- AC 1-2: G1 and G3 ----------------------------------------------------------------


@pytest.mark.parametrize("offset", [0.0, 50.0])
def test_g1_and_g3(offset):
    row = stiffness(g1(offset)).iloc[0]
    assert row[STRAIN] == pytest.approx(0.7545, abs=1e-4)
    assert row[MODULUS] == pytest.approx(19881, abs=1)
    assert row[ASYMPTOTE] == pytest.approx(333.35, abs=0.2)
    assert row[RATIO] == pytest.approx(0.9000, abs=5e-4)
    assert row[R_SQUARED] > 0.9999
    assert row[MODULUS_REASON] is None and row[RATIO_REASON] is None


# --- AC 3: G2, the example's B-1-U5 specimen 1 ----------------------------------------


@pytest.fixture(scope="module")
def site_readings(tmp_path_factory):
    p = ht.Project.from_ags(
        DATA / "site.ags",
        db=tmp_path_factory.mktemp("site") / "site.sqlite",
        display_units="US",
    )
    p.set_readings_map(ht.examples.path("readings_map.csv"))
    return p.triaxial_readings(), p.triaxial()


def csv_readings():
    return ht.read_csv(
        ht.examples.path("triaxial_readings.csv"),
        units=dict.fromkeys(EXAMPLE_STRESSES, "psf"),
    )


def example_stiffness(readings):
    with pytest.warns(UserWarning) as record:
        rows = ht.analysis.triaxial_stiffness_from_readings(
            readings, failure_criterion=MAX_Q
        )
    # The interpolation note (and the lab's marks on the CSV) only: no Rf > 1.
    assert not [r for r in record if "above 1" in str(r.message)]
    return rows


@pytest.mark.parametrize("source", ["project", "csv"])
def test_g2(source, site_readings):
    readings = site_readings[0] if source == "project" else csv_readings()
    rows = example_stiffness(readings)
    if source == "project":
        row = rows[rows["sample_reference"].eq("B-1-U5")].iloc[0]
    else:
        row = rows[rows["specimen_id"].eq("B-1-U5-1")].iloc[0]
    units = rows.attrs["units"]
    assert units[MODULUS] == "psf" and units[ASYMPTOTE] == "psf"
    assert row[MODULUS] / 1000 == pytest.approx(470.0, abs=0.1)
    assert row[STRAIN] == pytest.approx(0.4386, abs=1e-4)
    assert row[ASYMPTOTE] == pytest.approx(4498, abs=1)
    assert row[RATIO] == pytest.approx(0.917, abs=1e-3)
    assert_value_or_reason(rows)


# --- AC 9: the lab's E50 on site.ags --------------------------------------------------


def test_the_labs_e50_on_the_example(site_readings):
    readings, stages = site_readings
    rows = example_stiffness(readings)
    lab = "reported_secant_modulus_at_50_percent_peak"
    lab_strain = "reported_axial_strain_at_50_percent_peak"
    key = ["specimen_id", "test_stage"]
    merged = rows.merge(stages[[*key, lab, lab_strain]], on=key, validate="1:1")
    both = merged[merged[lab].notna()]
    assert len(both) == 9
    assert stages.attrs["units"][lab] == "ksf"
    # Within each heading's half place: TRET_EP50 2DP, TRET_E50 1DP.
    assert (both[STRAIN] - both[lab_strain]).abs().max() <= 0.005
    assert (both[MODULUS] / 1000 - both[lab]).abs().max() <= 0.05


# --- AC 5: Rf's limits ----------------------------------------------------------------


def test_two_readings_in_the_range_give_a_reason():
    df = stage_frame("S", "CD", [(0, 0), (1, 50), (2, 80), (3, 90), (4, 100)])
    row = stiffness(df).iloc[0]
    assert np.isnan(row[RATIO]) and np.isnan(row[ASYMPTOTE])
    assert row[RATIO_REASON].startswith("2 readings between 0.7 and 0.95")
    assert row[MODULUS] == pytest.approx(50 / 0.01)


def test_a_falling_transformed_line_gives_a_reason():
    curve = [(0, 0), (0.5, 20), (1.0, 75), (1.1, 85), (1.2, 94), (2, 100)]
    row = stiffness(stage_frame("S", "CD", curve)).iloc[0]
    assert np.isnan(row[RATIO]) and np.isnan(row[ASYMPTOTE])
    assert "no asymptote" in row[RATIO_REASON]
    assert not np.isnan(row[R_SQUARED])


def test_rf_above_1_is_kept_with_one_warning():
    # ε1/q = 1e-5 + ε1/90 at 1, 2 and 3 %: q_a = 90 below q_f = 100.
    curve = [(0, 0), (1, 82.57), (2, 86.12), (3, 87.38), (10, 100)]
    df = stages_frame(
        stage_frame("S1", "CD", curve),
        stage_frame("S2", "CD", curve),
        g1(),
    )
    with pytest.warns(UserWarning, match="above 1") as record:
        rows = ht.analysis.triaxial_stiffness_from_readings(df, failure_criterion=MAX_Q)
    assert len(record) == 1
    assert "In 2 stages" in str(record[0].message)
    assert "S1 stage 1, S2 stage 1" in str(record[0].message)
    assert rows[RATIO][:2].tolist() == pytest.approx([1.111, 1.111], abs=1e-3)
    assert rows[RATIO_REASON][:2].isna().all()


# --- AC 7: E50's limits ---------------------------------------------------------------


def test_q_never_above_its_start_gives_a_reason():
    row = stiffness(stage_frame("S", "CD", [(0, 50), (1, 40), (2, 45)])).iloc[0]
    assert np.isnan(row[MODULUS]) and np.isnan(row[STRAIN])
    assert "never rises above" in row[MODULUS_REASON]
    assert "isn't above its value at zero strain" in row[RATIO_REASON]


def test_no_reading_below_half_the_peak_gives_a_reason():
    curve = [(1, 80), (2, 90), (2.5, 94), (3, 95), (4, 100)]
    row = stiffness(stage_frame("S", "CD", curve)).iloc[0]
    assert np.isnan(row[MODULUS]) and np.isnan(row[STRAIN])
    assert row[MODULUS_REASON].startswith("no reading below half the peak")
    assert row[RATIO] > 0  # read where E50 isn't


def test_every_row_has_a_value_or_a_reason():
    df = stages_frame(
        g1(),
        stage_frame("A", "CD", [(0, 50), (1, 40), (2, 45)]),
        stage_frame("B", "CD", [(1, 80), (2, 90), (3, 95), (4, 100)]),
        stage_frame("C", "CD", [(0, 0), (1, 50), (2, 80), (3, 90), (4, 100)]),
    )
    assert_value_or_reason(stiffness(df))


# --- AC 8: the failure rows, and E50 at the largest q ---------------------------------


@pytest.mark.parametrize("criterion", ["max_deviator_stress", "max_stress_ratio"])
def test_the_failure_rows_are_unchanged(criterion):
    df = triaxial_goldens("A", "B")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        failure = ht.analysis.triaxial_failure_from_readings(
            df, failure_criterion=criterion
        )
    rows = stiffness(df, failure_criterion=criterion)
    assert list(rows.columns) == [*failure.columns, *ADDED]
    pd.testing.assert_frame_equal(rows[failure.columns], failure)
    for column, unit in failure.attrs["units"].items():
        assert rows.attrs["units"][column] == unit


def ratio_first():
    """A CU stage whose stress ratio peaks at 4 % (q 180) and q at 8 % (200)."""
    curve = [(0, 0), (1, 100), (1.5, 130), (2, 150), (3, 165), (4, 180), (8, 200)]
    excess = {0: 0, 1: 20, 1.5: 50, 2: 90, 3: 120, 4: 150, 8: 100}
    return stage_frame("R", "CU", curve, cell=400, back=200, excess=excess)


def test_e50_is_at_half_the_largest_q_under_the_stress_ratio():
    by_ratio = stiffness(ratio_first(), failure_criterion="max_stress_ratio").iloc[0]
    by_q = stiffness(ratio_first()).iloc[0]
    assert by_ratio["deviator_stress_at_failure"] == 180
    # q_50 = 100, read at 1 %: E50 = 100 / 0.01 under either criterion.
    for row in (by_ratio, by_q):
        assert row[STRAIN] == pytest.approx(1.0)
        assert row[MODULUS] == pytest.approx(10000)
    # Rf from q_f = 180: the readings at 130, 150 and 165 (126 to 171 kPa).
    x = np.array([1.5, 2, 3]) / 100
    slope = np.polyfit(x, x / np.array([130, 150, 165]), 1)[0]
    assert by_ratio[RATIO] == pytest.approx(180 * slope, rel=1e-9)
    assert by_ratio[ASYMPTOTE] == pytest.approx(1 / slope, rel=1e-9)
    assert by_q[RATIO] != pytest.approx(by_ratio[RATIO])


def test_every_stage_type_gets_e50_and_rf():
    df = triaxial_goldens()
    rows = stiffness(df, failure_criterion=MAX_Q)
    assert set(rows["test_type"]) >= {"CU", "CD", "UU"}
    assert_value_or_reason(rows)


# --- AC 10: units and arguments -------------------------------------------------------


def test_units_and_the_range_in_attrs():
    rows = stiffness(g1(), failure_ratio_range=(0.6, 0.9))
    assert rows.attrs["units"][MODULUS] == "kPa"
    assert rows.attrs["units"][ASYMPTOTE] == "kPa"
    assert rows.attrs["units"][STRAIN] == "%"
    assert rows.attrs["failure_ratio_range"] == (0.6, 0.9)
    assert stiffness(g1()).attrs["failure_ratio_range"] == (0.7, 0.95)


def test_psf_readings_give_the_same_e50():
    kpa = stiffness(g1()).iloc[0]
    df = g1()
    df[STRESSES] = df[STRESSES] / PSF
    df.attrs["units"] = dict.fromkeys(STRESSES, "psf")
    psf = stiffness(df).iloc[0]
    assert psf[MODULUS] * PSF == pytest.approx(kpa[MODULUS], rel=1e-9)
    assert psf[ASYMPTOTE] * PSF == pytest.approx(kpa[ASYMPTOTE], rel=1e-9)
    assert psf[RATIO] == pytest.approx(kpa[RATIO], rel=1e-9)


@pytest.mark.parametrize("column", ["axial_strain", "volumetric_strain"])
def test_a_strain_in_another_unit_raises(column):
    df = g1()
    df.attrs["units"] = {**df.attrs["units"], column: "mm"}
    with pytest.raises(UnitsError, match=column):
        ht.analysis.triaxial_stiffness_from_readings(df, failure_criterion=MAX_Q)
    with pytest.raises(UnitsError, match=column):
        ht.analysis.triaxial_stiffness_from_readings(
            g1(), failure_criterion=MAX_Q, units={column: "mm"}
        )


def test_strain_declared_in_percent_reads():
    df = g1()
    df.attrs["units"] = {**df.attrs["units"], "axial_strain": "%"}
    assert stiffness(df).iloc[0][MODULUS] == pytest.approx(19881, abs=1)


@pytest.mark.parametrize(
    "bad", [(0.95, 0.7), (0, 0.9), (0.7, 1.1), (0.7,), "0.7, 0.95", (0.7, None)]
)
def test_a_bad_range_raises(bad):
    with pytest.raises(HangtuError, match="failure_ratio_range"):
        ht.analysis.triaxial_stiffness_from_readings(
            g1(), failure_criterion=MAX_Q, failure_ratio_range=bad
        )
