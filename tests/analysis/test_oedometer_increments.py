"""ht.analysis.oedometer_increments() (docs/work/m19c-consolidation.md, Spec AC 1-11).

Golden values are the spec's, hand-calculated on BH1-U3 (site_si.ags):
m_v = 1000 Δe / ((1 + e1) Δσ′) m²/MN with e1 at the increment's start
(BS 1377-5:1990, 3.6.2.2.4), E = 1/m_v in kPa.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError

DATA = Path(__file__).parents[1] / "data" / "ags"
REL = 1e-9
#: 1 psf in kPa, from 1 ft = 0.3048 m and
#: 1 lbf = 4.4482216152605 N (exact).
PSF = 4.4482216152605 / 0.3048**2 / 1000

FIRST = "first increment: its start stress isn't given"

#: BH1-U3, AC table: (branch, σ′1, m_v m²/MN, Eoed kPa, Eur,oed kPa).
TABLE = [
    ("loading", np.nan, np.nan, np.nan, np.nan),
    ("loading", 25, 0.155988858, 6410.71429, np.nan),
    ("loading", 50, 0.134228188, 7450, np.nan),
    ("loading", 100, 0.157657658, 6342.85714, np.nan),
    ("loading", 200, 0.165903890, 6027.58621, np.nan),
    ("loading", 400, 0.115384615, 8666.66667, np.nan),
    ("unloading", 800, 0.0134408602, np.nan, 74400),
    ("unloading", 200, 0.0533333333, np.nan, 18750),
    ("reloading", 50, 0.0325600326, np.nan, 30712.5),
    ("reloading", 200, 0.0224948875, np.nan, 44454.5455),
    ("loading", 800, 0.0684079602, 14618.1818, np.nan),
    ("unloading", 1600, 0.00986842105, np.nan, 101333.333),
]
#: The table's values are written to 9 significant figures.
TABLE_REL = 1e-8


def _project(name, system, tmp_path_factory):
    return ht.Project.from_ags(
        DATA / f"{name}.ags",
        db=tmp_path_factory.mktemp(name) / f"{name}.sqlite",
        overwrite=True,
        display_units=system,
    )


@pytest.fixture(scope="module")
def site_si(tmp_path_factory):
    return _project("site_si", "SI", tmp_path_factory).oedometer()


@pytest.fixture(scope="module")
def site_us(tmp_path_factory):
    return _project("site_us", "US", tmp_path_factory).oedometer()


@pytest.fixture(scope="module")
def bh1_u3(site_si):
    return ht.analysis.oedometer_increments(site_si)


def _frame(stresses, void_ratios, specimen="S1", start=None):
    df = pd.DataFrame(
        {
            "specimen_id": [specimen] * len(stresses),
            "applied_vertical_stress": np.array(stresses, dtype=float),
            "void_ratio_at_increment_end": np.array(void_ratios, dtype=float),
        }
    )
    if start is not None:
        df["void_ratio_at_increment_start"] = np.array(start, dtype=float)
    df.attrs["units"] = {"applied_vertical_stress": "kPa"}
    return df


def _with_in_situ(df, value, unit="kPa"):
    out = df.copy()
    out["effective_vertical_stress"] = value
    out.attrs["units"] = {**df.attrs["units"], "effective_vertical_stress": unit}
    return out


def _notes(df):
    return df.attrs["oedometer_increments"]["notes"]


# --- AC 1: increments ---------------------------------------------------------


def test_ac1_stress_at_start(bh1_u3):
    expected = [row[1] for row in TABLE]
    np.testing.assert_allclose(
        bh1_u3["applied_vertical_stress_at_increment_start"], expected, rtol=REL
    )
    assert bh1_u3.attrs["units"]["applied_vertical_stress_at_increment_start"] == "kPa"


def test_ac1_volume_compressibility(bh1_u3):
    expected = [row[2] for row in TABLE]
    np.testing.assert_allclose(
        bh1_u3["coefficient_of_volume_compressibility"], expected, rtol=TABLE_REL
    )
    assert bh1_u3.attrs["units"]["coefficient_of_volume_compressibility"] == "m2/MN"
    # Increment 2 exactly: 0.007 / (1.795 × 25) × 1000.
    assert bh1_u3["coefficient_of_volume_compressibility"].iloc[1] == pytest.approx(
        7 / (1.795 * 25), rel=REL
    )


def test_ac1_moduli_on_their_branches(bh1_u3):
    assert list(bh1_u3["load_branch"]) == [row[0] for row in TABLE]
    np.testing.assert_allclose(
        bh1_u3["constrained_modulus"], [row[3] for row in TABLE], rtol=TABLE_REL
    )
    np.testing.assert_allclose(
        bh1_u3["unload_reload_constrained_modulus"],
        [row[4] for row in TABLE],
        rtol=TABLE_REL,
    )
    assert bh1_u3["constrained_modulus"].iloc[2] == pytest.approx(7450, rel=REL)
    assert bh1_u3["unload_reload_constrained_modulus"].iloc[7] == pytest.approx(
        18750, rel=REL
    )
    assert bh1_u3.attrs["units"]["constrained_modulus"] == "kPa"


def test_ac1_reasons(bh1_u3):
    reasons = bh1_u3["coefficient_of_volume_compressibility_reason"]
    assert reasons.iloc[0] == FIRST
    assert reasons.iloc[1:].isna().all()
    modulus = bh1_u3["constrained_modulus_reason"]
    assert modulus.iloc[0] == FIRST
    assert modulus.iloc[1:].isna().all()


def test_ac1_keeps_rows_and_columns(site_si, bh1_u3):
    assert list(bh1_u3.columns[: len(site_si.columns)]) == list(site_si.columns)
    assert bh1_u3.index.equals(site_si.index)
    assert "coefficient_of_volume_compressibility" not in site_si.columns


# --- AC 2: k -----------------------------------------------------------------

#: A year of 365.25 days, in seconds.
YEAR = 365.25 * 86400


def test_ac2_conductivity(bh1_u3):
    root = bh1_u3["hydraulic_conductivity_root_time"]
    log = bh1_u3["hydraulic_conductivity_log_time"]
    assert root.iloc[3] == pytest.approx(1.02919912e-10, rel=TABLE_REL)
    assert log.iloc[3] == pytest.approx(8.82170672e-11, rel=TABLE_REL)
    # From the inputs: c_v 2.1 m²/yr × m_v (m²/MN) × 9.81 kN/m³ × 10⁻³ m/yr.
    mv = bh1_u3["coefficient_of_volume_compressibility"].iloc[3]
    assert root.iloc[3] == pytest.approx(2.1 * mv * 9.81e-3 / YEAR, rel=REL)
    assert bh1_u3.attrs["units"]["hydraulic_conductivity_root_time"] == "m/s"
    assert bh1_u3.attrs["oedometer_increments"]["water_unit_weight"] == "9.81 kN/m3"
    for method in ("root_time", "log_time"):
        column = f"hydraulic_conductivity_{method}"
        others = bh1_u3[column].drop(index=bh1_u3.index[3])
        assert others.isna().all()
        reasons = bh1_u3[f"{column}_reason"]
        assert reasons.iloc[3] is None
        assert set(reasons.drop(index=bh1_u3.index[3])) == {"no c_v reported"}


def test_ac2_water_unit_weight_setting(site_si):
    ht.settings.water_unit_weight = "10 kN/m3"
    result = ht.analysis.oedometer_increments(site_si)
    assert result["hydraulic_conductivity_root_time"].iloc[3] == pytest.approx(
        1.04913264e-10, rel=TABLE_REL
    )
    assert result.attrs["oedometer_increments"]["water_unit_weight"] == "10 kN/m3"


def test_ac2_conductivity_reasons():
    df = _frame([25, 50, 100, 200], [0.795, 0.788, 0.788, 0.790])
    df["reported_coefficient_of_consolidation_root_time"] = [2.0, 2.0, 0.0, 2.0]
    df.attrs["units"]["reported_coefficient_of_consolidation_root_time"] = "m2/yr"
    result = ht.analysis.oedometer_increments(df)
    reasons = result["hydraulic_conductivity_root_time_reason"].tolist()
    assert reasons == [FIRST, None, "c_v is not positive", "m_v is not positive"]
    assert result["hydraulic_conductivity_root_time"].notna().tolist() == [
        False,
        True,
        False,
        False,
    ]
    # No log time column at all: every row says so.
    assert set(result["hydraulic_conductivity_log_time_reason"]) == {"no c_v reported"}


def test_ac2_conductivity_from_us_consolidation_units():
    df = _frame([100, 200], [0.776, 0.748])
    df["reported_coefficient_of_consolidation_root_time"] = [None, 2.1 * 10.7639104]
    df.attrs["units"]["reported_coefficient_of_consolidation_root_time"] = "ft2/yr"
    result = ht.analysis.oedometer_increments(df)
    assert result["hydraulic_conductivity_root_time"].iloc[1] == pytest.approx(
        1.02919912e-10, rel=1e-8
    )


# --- AC 3: US display ---------------------------------------------------------


def test_ac3_us_display(site_si):
    us = ht.analysis.oedometer_increments(site_si, display_units="US")
    row = us.iloc[3]
    assert row["coefficient_of_volume_compressibility"] == pytest.approx(
        0.00754868948, rel=1e-6
    )
    assert row["constrained_modulus"] == pytest.approx(132.473326, rel=1e-6)
    assert row["applied_vertical_stress_at_increment_start"] == pytest.approx(
        2088.54342, rel=1e-6
    )
    assert row["applied_vertical_stress"] == pytest.approx(200 / PSF, rel=REL)
    assert row["hydraulic_conductivity_root_time"] == pytest.approx(
        1.02919912e-8, rel=1e-6
    )
    assert us.attrs["units"]["hydraulic_conductivity_root_time"] == "cm/s"
    units = us.attrs["units"]
    assert units["coefficient_of_volume_compressibility"] == "ft²/kip"
    assert units["constrained_modulus"] == "ksf"
    assert units["applied_vertical_stress"] == "psf"
    assert units["applied_vertical_stress_at_increment_start"] == "psf"


def test_ac3_si_display_writes_moduli_in_mpa(site_si):
    si = ht.analysis.oedometer_increments(site_si, display_units="SI")
    assert si["constrained_modulus"].iloc[2] == pytest.approx(7.45, rel=REL)
    assert si.attrs["units"]["constrained_modulus"] == "MPa"


# --- AC 4: σ′v0 ---------------------------------------------------------------


@pytest.mark.parametrize(("in_situ", "rows"), [(80.0, [2, 7]), (150.0, [3, 7])])
def test_ac4_increments_spanning_in_situ(site_si, in_situ, rows):
    result = ht.analysis.oedometer_increments(_with_in_situ(site_si, in_situ))
    spans = result["spans_effective_vertical_stress"]
    assert str(spans.dtype) == "boolean"
    assert list(np.flatnonzero(spans.to_numpy(dtype=bool))) == rows
    assert not any("spans the" in note for note in _notes(result))


def test_ac4_in_situ_below_every_increment(site_si):
    result = ht.analysis.oedometer_increments(_with_in_situ(site_si, 20.0))
    assert not result["spans_effective_vertical_stress"].any()
    assert result["spans_effective_vertical_stress"].notna().all()
    (note,) = [n for n in _notes(result) if "spans the" in n]
    assert "BH1-U3" in note
    assert "nothing is extrapolated" in note


def test_ac4_without_in_situ(bh1_u3):
    assert bh1_u3["spans_effective_vertical_stress"].isna().all()
    assert any("ht.analysis.vertical_stress()" in note for note in _notes(bh1_u3))


def test_ac4_in_situ_in_another_unit(site_si):
    result = ht.analysis.oedometer_increments(
        _with_in_situ(site_si, 80.0 / PSF, unit="psf")
    )
    flags = result["spans_effective_vertical_stress"].to_numpy(dtype=bool)
    assert list(np.flatnonzero(flags)) == [2, 7]


# --- AC 5: start void ratio ---------------------------------------------------


def test_ac5_start_void_ratio_from_previous_end(site_si):
    df = site_si.copy()
    df.loc[df.index[3], "void_ratio_at_increment_start"] = np.nan
    result = ht.analysis.oedometer_increments(df)
    assert result["coefficient_of_volume_compressibility"].iloc[3] == pytest.approx(
        0.157657658, rel=TABLE_REL
    )
    (note,) = [n for n in _notes(result) if "void_ratio_at_increment_start" in n]
    assert f"Rows {df.index[3]} " in note


def test_ac5_frame_without_start_column():
    result = ht.analysis.oedometer_increments(_frame([100, 200], [0.776, 0.748]))
    assert result["coefficient_of_volume_compressibility"].iloc[1] == pytest.approx(
        28 / 177.6, rel=REL
    )


# --- AC 6: blank and odd rows -------------------------------------------------


def test_ac6_constant_stress():
    result = ht.analysis.oedometer_increments(_frame([100, 100], [0.776, 0.770]))
    assert result["load_branch"].iloc[1] == "constant_stress"
    assert np.isnan(result["coefficient_of_volume_compressibility"].iloc[1])
    assert result["coefficient_of_volume_compressibility_reason"].iloc[1] == (
        "no stress change"
    )
    assert result["constrained_modulus_reason"].iloc[1] == "no stress change"
    assert any("oedometer_load_branch()" in note for note in _notes(result))


def test_ac6_negative_volume_compressibility_kept():
    result = ht.analysis.oedometer_increments(_frame([100, 200], [0.776, 0.781]))
    assert result["coefficient_of_volume_compressibility"].iloc[1] == pytest.approx(
        -0.0281531532, rel=TABLE_REL
    )
    assert result["coefficient_of_volume_compressibility_reason"].isna().iloc[1]
    assert np.isnan(result["constrained_modulus"].iloc[1])
    assert result["constrained_modulus_reason"].iloc[1] == "m_v is not positive"


def test_ac6_blank_stress():
    df = _frame([50, np.nan, 200], [0.788, 0.776, 0.748])
    result = ht.analysis.oedometer_increments(df)
    reasons = result["coefficient_of_volume_compressibility_reason"]
    assert list(reasons.iloc[1:]) == [
        "no stress",
        "the previous increment has no stress",
    ]
    assert result["coefficient_of_volume_compressibility"].iloc[1:].isna().all()


def test_ac6_blank_void_ratio():
    df = _frame([50, 100, 200], [0.788, np.nan, 0.748])
    result = ht.analysis.oedometer_increments(df)
    reasons = result["coefficient_of_volume_compressibility_reason"]
    assert reasons.iloc[1] == "no void ratio at the increment's end"
    assert reasons.iloc[2] == "no void ratio at the increment's start"


def test_ac6_two_specimens_start_blank():
    df = pd.concat(
        [_frame([25, 50], [0.795, 0.788], "A"), _frame([25, 50], [0.795, 0.788], "B")],
        ignore_index=True,
    )
    df.attrs["units"] = {"applied_vertical_stress": "kPa"}
    result = ht.analysis.oedometer_increments(df)
    start = result["applied_vertical_stress_at_increment_start"]
    assert list(np.isnan(start)) == [True, False, True, False]
    reasons = result["coefficient_of_volume_compressibility_reason"]
    assert list(reasons.iloc[[0, 2]]) == [FIRST, FIRST]


def test_ac6_categorical_specimen_order():
    df = _frame([25, 50], [0.795, 0.788])
    df["specimen_id"] = pd.Categorical(df["specimen_id"])
    result = ht.analysis.oedometer_increments(df)
    assert result["coefficient_of_volume_compressibility"].notna().sum() == 1


# --- AC 7: errors -------------------------------------------------------------


def test_ac7_missing_end_void_ratio():
    df = _frame([25, 50], [0.795, 0.788]).drop(columns="void_ratio_at_increment_end")
    with pytest.raises(ColumnError, match="void_ratio_at_increment_end") as error:
        ht.analysis.oedometer_increments(df)
    assert 'ht.template("oedometer")' in str(error.value)


def test_ac7_two_in_situ_stresses():
    df = _with_in_situ(_frame([25, 50], [0.795, 0.788]), [80.0, 90.0])
    with pytest.raises(HangtuError, match="more than one effective_vertical_stress"):
        ht.analysis.oedometer_increments(df)


def test_ac7_blank_specimen_and_display_units():
    df = _frame([25, 50], [0.795, 0.788])
    with pytest.raises(HangtuError, match="display_units"):
        ht.analysis.oedometer_increments(df, display_units="metric")
    df.loc[0, "specimen_id"] = None
    with pytest.raises(HangtuError, match="no specimen_id"):
        ht.analysis.oedometer_increments(df)


# --- AC 10: twins -------------------------------------------------------------

_TWIN_COLUMNS = [
    "applied_vertical_stress",
    "applied_vertical_stress_at_increment_start",
    "coefficient_of_volume_compressibility",
    "constrained_modulus",
    "unload_reload_constrained_modulus",
    "hydraulic_conductivity_root_time",
    "hydraulic_conductivity_log_time",
]


@pytest.mark.parametrize("system", ["SI", "US"])
def test_ac10_twins_agree(site_si, site_us, system):
    si = ht.analysis.oedometer_increments(site_si, display_units=system)
    us = ht.analysis.oedometer_increments(site_us, display_units=system)
    for column in _TWIN_COLUMNS:
        np.testing.assert_allclose(si[column], us[column], rtol=REL, err_msg=column)
        assert si.attrs["units"][column] == us.attrs["units"][column]
    # The US lab's m_v is its own 2SF in ft2/kip (spec decision 10).
    # oedometer_increments() leaves the lab's columns in their own units.
    reported = "reported_coefficient_of_volume_compressibility"
    assert us.attrs["units"][reported] == "ft2/kip"
    assert [f"{v:.2g}" for v in us[reported].dropna()] == [
        "0.0075",
        "0.0064",
        "0.0075",
        "0.0079",
        "0.0055",
        "0.0033",
    ]
    for column in (
        "coefficient_of_volume_compressibility_reason",
        "constrained_modulus_reason",
        "hydraulic_conductivity_root_time_reason",
        "hydraulic_conductivity_log_time_reason",
    ):
        assert si[column].equals(us[column])


# --- AC 11: docstring ---------------------------------------------------------


def test_ac11_docstring():
    doc = ht.analysis.oedometer_increments.__doc__
    assert "BS 1377-5:1990, 3.6.2.2.4" in doc
    assert "Freeze" in doc and "Eq. (8.22)" in doc
    assert "3.1.1, note 3" in doc
    for reason in (
        FIRST,
        "no stress change",
        "the previous increment has no stress",
        "m_v is not positive",
        "no void ratio at the increment's start",
    ):
        assert reason in doc.replace("\n    ", " ")


# --- k from the recomputed c_v (docs/work/m19c2-cv-readings.md, AC 6) ---------------

MAP = DATA / "readings_map.csv"
FROM_READINGS = "hydraulic_conductivity_from_readings"


def _with_readings(name, system, tmp_path_factory, **kwargs):
    p = _project(name, system, tmp_path_factory)
    p.set_readings_map(MAP)
    reduced = ht.analysis.consolidation_coefficient_from_readings(
        p.oedometer_readings()
    )
    return ht.analysis.oedometer_increments(
        p.oedometer(), consolidation_coefficients=reduced, **kwargs
    ), reduced


@pytest.fixture(scope="module")
def with_readings(tmp_path_factory):
    return _with_readings("site_si", "SI", tmp_path_factory)[0]


def test_c2_ac6_k_from_the_recomputed_cv(with_readings, bh1_u3):
    rows = with_readings
    # 2.15039592 m²/yr × 0.157657658 m²/MN × 9.81 kN/m³ × 10⁻³ / 31 557 600 s.
    assert rows[f"{FROM_READINGS}_root_time"].iloc[3] == pytest.approx(
        1.05389790e-10, rel=TABLE_REL
    )
    assert rows[f"{FROM_READINGS}_log_time"].iloc[3] == pytest.approx(
        1.01127911e-10, rel=TABLE_REL
    )
    mv = rows["coefficient_of_volume_compressibility"].iloc[3]
    cv = rows["coefficient_of_consolidation_root_time"].iloc[3]
    assert cv == pytest.approx(2.15039592, rel=TABLE_REL)
    assert rows[f"{FROM_READINGS}_root_time"].iloc[3] == pytest.approx(
        cv * mv * 9.81e-3 / YEAR, rel=REL
    )
    # c1's k from the lab's c_v, beside it and unchanged.
    for column in (
        "hydraulic_conductivity_root_time",
        "hydraulic_conductivity_log_time",
    ):
        pd.testing.assert_series_equal(rows[column], bh1_u3[column])
    assert rows["hydraulic_conductivity_root_time"].iloc[3] == pytest.approx(
        1.02919912e-10, rel=TABLE_REL
    )
    assert rows.attrs["units"][f"{FROM_READINGS}_root_time"] == "m/s"
    assert rows.attrs["units"]["coefficient_of_consolidation_log_time"] == "m2/yr"


def test_c2_ac6_no_readings_on_the_other_increments(with_readings):
    rows = with_readings
    without = [0, *range(6, 12)]  # increments 1 and 7-12
    for method in ("root_time", "log_time"):
        k = rows[f"{FROM_READINGS}_{method}"]
        assert k.iloc[without].isna().all()
        assert not k.iloc[1:6].isna().any()
        assert set(rows[f"{FROM_READINGS}_{method}_reason"].iloc[without]) == {
            "no readings"
        }
        cv = f"coefficient_of_consolidation_{method}"
        assert set(rows[f"{cv}_reason"].iloc[without]) == {"no readings"}
        assert rows[f"{cv}_basis"].iloc[without].isna().all()
        assert list(rows[f"{cv}_basis"].iloc[1:6]) == ["rule"] * 5


def test_c2_without_consolidation_coefficients_the_frame_is_as_before(bh1_u3):
    assert not any(c.startswith(FROM_READINGS) for c in bh1_u3.columns)
    assert "coefficient_of_consolidation_root_time" not in bh1_u3.columns


def test_c2_a_blank_recomputed_cv_gives_its_reason(site_si):
    reduced = pd.DataFrame(
        {
            "specimen_id": [site_si["specimen_id"].iloc[3]],
            "test_stage": ["4"],
            "coefficient_of_consolidation_root_time": [np.nan],
            "coefficient_of_consolidation_root_time_basis": ["rule"],
            "coefficient_of_consolidation_root_time_reason": [
                "t90 after the last reading"
            ],
            "coefficient_of_consolidation_log_time": [2.0],
            "coefficient_of_consolidation_log_time_basis": ["override"],
            "coefficient_of_consolidation_log_time_reason": [None],
        }
    )
    reduced = ht.set_units(
        reduced,
        {
            "coefficient_of_consolidation_root_time": "m2/yr",
            "coefficient_of_consolidation_log_time": "ft2/yr",
        },
    )
    rows = ht.analysis.oedometer_increments(site_si, consolidation_coefficients=reduced)
    row = rows.iloc[3]
    assert row["coefficient_of_consolidation_root_time_reason"] == (
        "t90 after the last reading"
    )
    assert row[f"{FROM_READINGS}_root_time_reason"] == "no c_v from readings"
    assert row["coefficient_of_consolidation_log_time"] == pytest.approx(
        2.0 / 10.7639104, rel=1e-8
    )
    assert row["coefficient_of_consolidation_log_time_basis"] == "override"
    assert row[f"{FROM_READINGS}_log_time"] == pytest.approx(
        2.0
        / 10.7639104
        * row["coefficient_of_volume_compressibility"]
        * 9.81e-3
        / YEAR,
        rel=1e-8,
    )


def test_c2_reduced_rows_matching_no_increment_warn(site_si, tmp_path_factory):
    p = _project("site_si", "SI", tmp_path_factory)
    p.set_readings_map(MAP)
    reduced = ht.analysis.consolidation_coefficient_from_readings(
        p.oedometer_readings()
    )
    extra = reduced.iloc[[0]].copy()
    extra["test_stage"] = "99"
    both = pd.concat([reduced, extra], ignore_index=True)
    both.attrs = reduced.attrs
    with pytest.warns(UserWarning, match=r"increment 99, which df's increments"):
        rows = ht.analysis.oedometer_increments(
            site_si, consolidation_coefficients=both
        )
    assert rows[f"{FROM_READINGS}_root_time"].iloc[3] == pytest.approx(
        1.05389790e-10, rel=TABLE_REL
    )


def test_c2_twins(tmp_path_factory):
    si, _ = _with_readings("site_si", "SI", tmp_path_factory)
    us, _ = _with_readings("site_us", "US", tmp_path_factory)
    for method in ("root_time", "log_time"):
        np.testing.assert_allclose(
            si[f"{FROM_READINGS}_{method}"], us[f"{FROM_READINGS}_{method}"], rtol=1e-8
        )


def test_c2_display_units_us(tmp_path_factory):
    rows, _ = _with_readings("site_si", "SI", tmp_path_factory, display_units="US")
    assert rows["coefficient_of_consolidation_root_time"].iloc[3] == pytest.approx(
        23.1466690, rel=1e-6
    )
    assert rows.attrs["units"]["coefficient_of_consolidation_root_time"] == "ft²/yr"
    assert rows.attrs["units"][f"{FROM_READINGS}_root_time"] == "cm/s"
    assert rows[f"{FROM_READINGS}_root_time"].iloc[3] == pytest.approx(
        1.05389790e-8, rel=TABLE_REL
    )


@pytest.mark.parametrize(
    ("change", "error", "match"),
    [
        (
            lambda r: r.drop(columns="coefficient_of_consolidation_log_time_basis"),
            ColumnError,
            r"consolidation_coefficients has no column "
            r"'coefficient_of_consolidation_log_time_basis'",
        ),
        (
            lambda r: pd.concat([r, r.iloc[[0]]], ignore_index=True),
            HangtuError,
            r"more than one row for specimen .* increment '2'",
        ),
        (lambda r: r.to_dict(), HangtuError, "must be a pandas DataFrame"),
    ],
)
def test_c2_consolidation_coefficients_errors(
    site_si, tmp_path_factory, change, error, match
):
    p = _project("site_si", "SI", tmp_path_factory)
    p.set_readings_map(MAP)
    reduced = ht.analysis.consolidation_coefficient_from_readings(
        p.oedometer_readings()
    )
    with pytest.raises(error, match=match):
        ht.analysis.oedometer_increments(
            site_si, consolidation_coefficients=change(reduced)
        )


def test_c2_df_needs_test_stage(site_si):
    reduced = pd.DataFrame(
        columns=[
            "specimen_id",
            "test_stage",
            *[
                f"coefficient_of_consolidation_{m}{s}"
                for m in ("root_time", "log_time")
                for s in ("", "_basis", "_reason")
            ],
        ]
    )
    with pytest.raises(ColumnError, match=r"df has no column 'test_stage'"):
        ht.analysis.oedometer_increments(
            site_si.drop(columns="test_stage"), consolidation_coefficients=reduced
        )
