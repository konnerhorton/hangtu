"""p.triaxial() (datasets.md §6.10).

Acceptance criteria are those of docs/work/m11a-triaxial-data.md (AC n). The
golden values are hand-calculated from the test files' values, in
tests/data/ags/_make_files.py: σ3 is the cell pressure, σ1 = σ3 + q_f,
σ′3 = σ3 - u_f and σ′1 = σ′3 + q_f; unit weights are density × 9.80665.
"""

import re
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import hangtu as ht

from .conftest import make_files

#: 1 psf in kPa: 0.45359237 × 9.80665 / 0.3048² / 1000 (exact).
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000
BACK_PRESSURE = r"^1 drained triaxial stage had TRET_PWPF blank"
PRINCIPAL = [
    "minor_principal_stress_at_failure",
    "major_principal_stress_at_failure",
    "effective_minor_principal_stress_at_failure",
    "effective_major_principal_stress_at_failure",
]


def _site(project, **kwargs):
    """``p.triaxial()`` on a good file: its one warning is the back pressure's."""
    with pytest.warns(UserWarning, match=BACK_PRESSURE) as caught:
        df = project.triaxial(**kwargs)
    assert len(caught) == 1, [str(w.message) for w in caught]
    return df


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


@pytest.fixture
def site(fresh):
    project = fresh("site_si")
    project.set_geology_map(make_files.HERE / "strata.csv")
    return project


def test_one_row_per_stage_in_file_order(site):
    df = _site(site)
    assert list(df["loca_id"]) == ["BH1"] * 3 + ["BH2"] * 3 + ["BH1"] * 3
    assert list(df["test_type"]) == ["CU"] * 3 + ["CDM"] * 3 + ["UU"] * 3
    assert list(df["source_line"]) == sorted(df["source_line"])
    assert df["source_line"].iloc[6] > df["source_line"].iloc[5]  # TRIT after TRET


def test_1_cu_stage_golden_values(site):
    df = _site(site)
    row = df.iloc[0]
    assert (row["sample_reference"], row["specimen_reference"]) == ("BH1-U3", "1")
    assert row["depth"] == pytest.approx(5.05)
    assert row["depth_basis"] == "spec_depth"
    assert row[PRINCIPAL].tolist() == [400, 580, 40, 220]
    assert row["effective_stress_basis"] == "pore_pressure_at_failure"
    assert not row["multistage_test"]
    assert row["test_stage"] == "1"
    assert row["failure_criterion"] == "Maximum deviator stress"
    assert row["reported_effective_friction_angle"] == pytest.approx(27.0)
    assert row["reported_effective_cohesion"] == pytest.approx(5)
    # 2.05 and 1.62 Mg/m3 × 9.80665 m/s².
    assert row["bulk_unit_weight"] == pytest.approx(2.05 * 9.80665, rel=1e-9)
    assert row["bulk_unit_weight"] == pytest.approx(20.1036, abs=5e-5)
    assert row["dry_unit_weight"] == pytest.approx(15.8868, abs=5e-5)
    assert (row["water_content"], row["void_ratio"]) == pytest.approx((27, 0.654))
    assert row["pore_pressure_parameter_b"] == pytest.approx(0.97)
    assert row["sample_condition"] == "UNDISTURBED"


def test_2_drained_stage_takes_the_back_pressure(site):
    stages = _site(site, where={"test_type": "CDM"})
    effective = "effective_{}_principal_stress_at_failure"
    assert stages[effective.format("minor")].tolist() == [100, 200, 400]
    assert stages[effective.format("major")].tolist() == [400, 720, 1300]
    assert stages["effective_stress_basis"].tolist() == [
        "pore_pressure_at_failure",
        "back_pressure",
        "pore_pressure_at_failure",
    ]
    assert np.isnan(stages["pore_pressure_at_failure"].iloc[1])  # kept blank
    assert stages["multistage_test"].tolist() == [True, True, True]
    assert stages["test_stage"].tolist() == ["1", "2", "3"]
    assert stages["volumetric_strain_at_failure"].tolist() == [1.2, 2.1, 3.4]


def test_3_uu_stages_total_stresses_only(site):
    # The UU stages alone give no back pressure warning.
    stages = _quiet(site.triaxial, where={"test_type": "UU"})
    assert stages["major_principal_stress_at_failure"].tolist() == [220, 324, 418]
    assert stages[PRINCIPAL[2:]].isna().all().all()
    assert stages["effective_stress_basis"].isna().all()
    assert stages["failure_criterion"].isna().all()  # TRIG has no TRIG_FCR


def test_4_us_display(site):
    df = _site(site, display_units="US")
    row = df.iloc[0]
    assert df.attrs["units"]["effective_minor_principal_stress_at_failure"] == "psf"
    # 40 and 220 kPa ÷ 0.047880259 kPa per psf.
    assert row["effective_minor_principal_stress_at_failure"] == pytest.approx(
        835.4174, rel=1e-6
    )
    assert row["effective_major_principal_stress_at_failure"] == pytest.approx(
        4594.7955, rel=1e-6
    )
    assert row["cell_pressure"] == pytest.approx(400 / PSF, rel=1e-9)
    assert df.attrs["units"]["bulk_unit_weight"] == "pcf"
    assert df.attrs["units"]["axial_strain_at_failure"] == "%"
    assert df.attrs["units"]["reported_effective_friction_angle"] == "deg"


# --- 6, 7: blank, never guessed; incomplete ------------------------------------------


@pytest.fixture
def joins(fresh):
    return fresh("joins")


def _joins(project, **kwargs):
    with pytest.warns(UserWarning) as caught:
        df = project.triaxial(**kwargs)
    return df, [str(w.message) for w in caught]


def test_6_undrained_stage_without_pore_pressure(joins):
    df, _ = _joins(joins)
    row = df.set_index("sample_reference").loc["J1-U3"]
    assert row["test_type"] == "CU"
    assert row[PRINCIPAL[:2]].tolist() == [400, 560]
    assert row[PRINCIPAL[2:]].isna().all()
    assert row["effective_stress_basis"] is None


def test_6_extension_stage_is_blank_and_named(joins):
    df, messages = _joins(joins)
    row = df.set_index("sample_reference").loc["J1-U1"]
    assert row["test_type"] == "CIDE"
    assert row[PRINCIPAL].isna().all()
    assert row["deviator_stress_at_failure"] == 90  # the file's value is kept
    extension = [m for m in messages if m.startswith("Extension stages")]
    assert extension == [
        "Extension stages J1 J1-U1/T1 stage 1 (CIDE) have blank principal stresses: "
        "the deviator stress has no agreed sign in extension, where the axial "
        "stress is the minor one."
    ]


def test_6_stage_with_no_treg_row_is_kept(fresh, tmp_path):
    # A TRET row with no TREG row breaks AGS Rule 10c, so the file is built
    # here (tests/data/ags/README.md).
    tret = {**make_files.TRET, "rows": make_files.TRET["rows"][:1]}
    path = tmp_path / "orphan.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA, make_files.SAMP, tret])
    project = ht.Project.from_ags(path, db=tmp_path / "orphan.sqlite")
    df = _quiet(project.triaxial, display_units="SI")
    assert len(df) == 1
    row = df.iloc[0]
    assert row["test_type"] is None and row["failure_criterion"] is None
    assert np.isnan(row["reported_effective_friction_angle"])
    # Read as compression, with the file's pore pressure.
    assert row[PRINCIPAL].tolist() == [400, 580, 40, 220]
    assert not row["multistage_test"]


def test_7_incomplete_stage_left_out_and_kept_on_request(joins):
    _, messages = _joins(joins)
    assert any(
        re.match(r"Left out 1 of 3 TRET records .*TRET_CELL on line 128", m)
        for m in messages
    )
    df, _ = _joins(joins, include_incomplete=True)
    row = df.set_index("source_line").loc[128]
    assert np.isnan(row["cell_pressure"])
    assert row[PRINCIPAL].isna().all()
    assert row["deviator_stress_at_failure"] == 170


def test_deviator_stress_of_zero_is_blank_with_a_warning(tmp_path):
    rows = [list(make_files.TRET["rows"][0])]
    devf = [h for h, _, _ in make_files.TRET_HEADINGS].index("TRET_DEVF")
    rows[0][devf] = 0
    tret = {**make_files.TRET, "rows": rows}
    treg = {**make_files.TREG, "rows": make_files.TREG["rows"][:1]}
    path = tmp_path / "zero.ags"
    groups = [make_files.LOCA, make_files.SAMP, treg, tret]
    make_files.write_file(path, "4.2", groups)
    project = ht.Project.from_ags(path, db=tmp_path / "zero.sqlite")
    with pytest.warns(UserWarning, match=r"Stages BH1 BH1-U3/1 stage 1 have a devi"):
        df = project.triaxial()
    assert df[PRINCIPAL].isna().all().all()


# --- 11, 12, 14 --------------------------------------------------------------------


def test_11_no_triaxial_group(tmp_path):
    path = tmp_path / "none.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA])
    with pytest.warns(UserWarning, match="No TRET or TRIT group in none.ags"):
        df = ht.Project.from_ags(path).triaxial()
    assert df.empty
    assert "effective_minor_principal_stress_at_failure" in df.columns
    assert str(df["multistage_test"].dtype) == "boolean"


@pytest.mark.parametrize("name", ["site_si", "site_us", "site_v404"])
def test_12_feeds_the_plots(fresh, name):
    project = fresh(name)
    project.set_geology_map(make_files.HERE / "strata.csv")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # the back pressure count
        stages = project.triaxial()
    for plot, column in [
        (ht.plot.profile, "deviator_stress_at_failure"),
        (ht.plot.geology_unit_comparison, "axial_strain_at_failure"),
    ]:
        fig, _ax = _quiet(plot, stages, column)
        plt.close(fig)


def test_14_common_arguments(site):
    # The back pressure warning counts the rows returned: BH2's CDM test only.
    assert _site(site, holes=["BH2"])["test_type"].tolist() == ["CDM"] * 3
    assert len(_site(site, geology=["Alluvium"])) == 9
    in_range = _quiet(site.triaxial, depth=(5, 6))
    assert in_range["depth"].tolist() == pytest.approx([5.05, 5.15, 5.25])
    cu = _quiet(site.triaxial, where={"test_type": "CU"})
    assert cu["specimen_reference"].tolist() == ["1", "2", "3"]


def test_v404_without_back_pressure_leaves_the_stage_blank(fresh):
    # 4.0.4 has no TRET_BACK, so the CDM stage 2 has no u_f and no warning.
    df = _quiet(fresh("site_v404").triaxial)
    stage = df[df["test_type"] == "CDM"].iloc[1]
    assert np.isnan(stage["effective_minor_principal_stress_at_failure"])
    assert stage["minor_principal_stress_at_failure"] == 500


def test_initial_state_has_its_own_columns(site):
    # The specimen's initial water content, not LNMC's.
    df = _site(site)
    assert df["water_content"].tolist()[:3] == [27, 26, 25]


def test_10_template_frame_gives_the_dataset_stresses(site):
    # AC 10: AC 1's and AC 2's stages typed into ht.template("triaxial").
    dataset = _site(site, where={"test_type": ["CU", "CDM"]})
    template = ht.template("triaxial")
    typed = dataset[list(template.columns)]
    typed = ht.set_units(
        typed.reset_index(drop=True),
        {c: u for c, u in dataset.attrs["units"].items() if c in template.columns},
    )
    with pytest.warns(UserWarning, match=r"^1 drained stage had no pore_pressure"):
        result = ht.analysis.triaxial_failure_stresses(typed)
    columns = [*PRINCIPAL, "effective_stress_basis"]
    pd.testing.assert_frame_equal(result[columns], dataset[columns])
