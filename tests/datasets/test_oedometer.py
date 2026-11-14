"""p.oedometer() (datasets.md §6.14).

Acceptance criteria are those of docs/work/m19a-oedometer-data.md (AC n). The
values are the test files' (tests/data/ags/_make_files.py): BH1-U3's
specimen OED1 is the spec's table of twelve increments. Unit weights are
density × 9.80665; 1 psf = 0.45359237 × 9.80665 / 0.3048² Pa (exact).
"""

import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import hangtu as ht

from .conftest import make_files

#: 1 kPa in psf, from 1 psf in kPa (exact).
PSF_PER_KPA = 1 / (0.45359237 * 9.80665 / 0.3048**2 / 1000)
#: 1 m²/MN in ft²/kip, and 1 m²/yr in ft²/yr.
FT2_PER_KIP = 10.7639104 / 224.808943
FT2 = 10.7639104
STRESSES = [25, 50, 100, 200, 400, 800, 200, 50, 200, 800, 1600, 400]
STARTS = [0.800, 0.795, 0.788, 0.776, 0.748, 0.690, 0.612, 0.625, 0.638, 0.630]
STARTS += [0.608, 0.520]
ENDS = [0.795, 0.788, 0.776, 0.748, 0.690, 0.612, 0.625, 0.638, 0.630, 0.608]
ENDS += [0.520, 0.538]
MV = [np.nan, 0.16, 0.13, 0.16, 0.17, 0.12] + [np.nan] * 4 + [0.068, np.nan]
BRANCHES = ["loading"] * 6 + ["unloading"] * 2 + ["reloading"] * 2
BRANCHES += ["loading", "unloading"]
INCREMENT_COLUMNS = [
    "test_stage",
    "applied_vertical_stress",
    "void_ratio_at_increment_start",
    "void_ratio_at_increment_end",
    "reported_coefficient_of_volume_compressibility",
    "load_branch",
]


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


@pytest.fixture
def site(fresh):
    project = fresh("site_si")
    project.set_geology_map(make_files.HERE / "strata.csv")
    return project


@pytest.fixture
def joins(fresh):
    return fresh("joins")


def _joins(project, **kwargs):
    with pytest.warns(UserWarning, match="Left out 1 of 2 CONS records") as caught:
        df = project.oedometer(**kwargs)
    assert len(caught) == 1, [str(w.message) for w in caught]
    return df


def test_ac1_one_row_per_increment_with_the_specimen(site):
    df = _quiet(site.oedometer)
    assert len(df) == 12
    assert df["test_stage"].tolist() == [str(i) for i in range(1, 13)]
    assert list(df["source_line"]) == sorted(df["source_line"])
    assert df["applied_vertical_stress"].tolist() == STRESSES
    assert df["void_ratio_at_increment_start"].tolist() == STARTS
    assert df["void_ratio_at_increment_end"].tolist() == ENDS
    np.testing.assert_array_equal(
        df["reported_coefficient_of_volume_compressibility"], MV
    )
    assert df["reported_coefficient_of_consolidation_root_time"].iloc[3] == 2.1
    assert df["reported_coefficient_of_consolidation_log_time"].iloc[3] == 1.8
    assert df["reported_coefficient_of_consolidation_root_time"].drop(3).isna().all()
    # The specimen's values, on every increment.
    assert set(df["loca_id"]) == {"BH1"}
    assert set(df["sample_reference"]) == {"BH1-U3"}
    assert set(df["specimen_reference"]) == {"OED1"}
    assert set(df["depth"]) == {5.20}
    assert set(df["depth_basis"]) == {"spec_depth"}
    assert set(df["test_type"]) == {"OEDOMETER"}
    assert set(df["sample_condition"]) == {"UNDISTURBED"}
    specimen = df.iloc[0]
    assert specimen["bulk_unit_weight"] == pytest.approx(1.92 * 9.80665, rel=1e-9)
    assert specimen["dry_unit_weight"] == pytest.approx(1.50 * 9.80665, rel=1e-9)
    assert specimen["bulk_unit_weight"] == pytest.approx(18.82877, rel=1e-6)
    assert specimen["dry_unit_weight"] == pytest.approx(14.70998, rel=1e-6)
    assert specimen["water_content"] == 28.0
    assert specimen["final_water_content"] == 22.1
    assert specimen["particle_density"] == 2.70
    assert not specimen["particle_density_assumed"]
    assert specimen["degree_of_saturation"] == 95
    assert specimen["void_ratio"] == 0.800
    assert specimen["specimen_height"] == 20.00
    assert specimen["specimen_diameter"] == 75.00
    assert specimen["equipment_deformation_corrected"]
    assert df[INCREMENT_COLUMNS[1:]].notna().any().all()


def test_ac2_load_branches(site):
    df = _quiet(site.oedometer)
    assert df["load_branch"].tolist() == BRANCHES
    # Increment 10 is back at the earlier maximum, 800 kPa: still reloading.
    assert df.loc[9, ["applied_vertical_stress", "load_branch"]].tolist() == [
        800,
        "reloading",
    ]


def test_ac4_us_display(fresh):
    df = _quiet(fresh("site_si", display_units="US").oedometer)
    units = df.attrs["units"]
    assert units["applied_vertical_stress"] == "psf"
    assert units["reported_coefficient_of_volume_compressibility"] == "ft2/kip"
    assert units["reported_coefficient_of_consolidation_root_time"] == "ft2/yr"
    assert units["specimen_height"] == "in"
    assert df["applied_vertical_stress"].iloc[5] == pytest.approx(16708.35, rel=1e-6)
    assert df["applied_vertical_stress"].iloc[5] == pytest.approx(
        800 * PSF_PER_KPA, rel=1e-9
    )
    mv = df["reported_coefficient_of_volume_compressibility"].iloc[1]
    assert mv == pytest.approx(0.16 * FT2_PER_KIP, rel=1e-6)
    cv = df["reported_coefficient_of_consolidation_root_time"].iloc[3]
    assert cv == pytest.approx(22.60421, rel=1e-6)
    assert df["load_branch"].tolist() == BRANCHES


@pytest.mark.parametrize("display_units", ["SI", "US"])
def test_ac5_twins_agree(fresh, display_units):
    si = _quiet(fresh("site_si", display_units=display_units).oedometer)
    us = _quiet(fresh("site_us", display_units=display_units).oedometer)
    numeric = si.select_dtypes("number").columns.drop("source_line")
    np.testing.assert_allclose(
        si[numeric].to_numpy(float), us[numeric].to_numpy(float), rtol=1e-9
    )
    texts = ["test_type", "test_stage", "load_branch", "particle_density_assumed"]
    pd.testing.assert_frame_equal(si[texts], us[texts])
    assert si.attrs["units"] == us.attrs["units"]


def test_the_404_file_gives_the_same_increments(fresh):
    df = _quiet(fresh("site_v404").oedometer)
    assert df["applied_vertical_stress"].tolist() == STRESSES
    assert df["void_ratio_at_increment_end"].tolist() == ENDS
    assert df["load_branch"].tolist() == BRANCHES
    assert df["equipment_deformation_corrected"].isna().all()  # 4.1's heading


def test_ac6_a_specimen_with_no_increments_is_one_row(joins):
    df = _joins(joins)
    swell = df[df["specimen_reference"] == "SW1"]
    assert len(swell) == 1
    row = swell.iloc[0]
    assert row["swelling_pressure"] == 150
    assert row["test_type"] == "SWELLPRESS"
    assert row["test_stage"] is None and row["load_branch"] is None
    assert np.isnan(row["applied_vertical_stress"])
    assert np.isnan(row["void_ratio_at_increment_end"])
    assert row["void_ratio"] == 0.700


def test_ac7_every_type_is_kept_as_written(joins):
    df = _joins(joins).set_index("specimen_reference")
    assert df.loc["SS1", "test_type"] == "SETTLESAT"
    assert df.loc["SS1", "height_change_on_saturation"] == -1.1
    assert df.loc["L1", "test_type"] == "LOW STRESS"


def test_ac8_an_assumed_particle_density_is_kept_and_flagged(joins):
    df = _joins(joins).set_index("specimen_reference")
    assert df.loc["SS1", "particle_density"] == 2.65
    assert df.loc["SS1", "particle_density_assumed"]
    assert not df.loc["L1", "particle_density_assumed"]


def test_ac9_an_increment_with_no_end_void_ratio_is_incomplete(joins):
    df = _joins(joins)
    assert df[df["specimen_reference"] == "L1"]["test_stage"].tolist() == ["1"]
    kept = _quiet(joins.oedometer, include_incomplete=True)
    rows = kept[kept["specimen_reference"] == "L1"]
    assert rows["test_stage"].tolist() == ["1", "2"]
    assert rows["applied_vertical_stress"].tolist() == [5, 10]
    assert np.isnan(rows["void_ratio_at_increment_end"].iloc[1])
    assert rows["load_branch"].tolist() == ["loading", "loading"]


def test_a_specimen_whose_increments_are_all_left_out_gives_no_row(fresh, tmp_path):
    # Its increments exist; leaving them out mustn't make it look like a
    # swelling test with none.
    rows = [list(row) for row in make_files.CONS["rows"][:1]]
    ince = [h for h, _, _ in make_files.CONS_HEADINGS].index("CONS_INCE")
    rows[0][ince] = None
    cons = {**make_files.CONS, "rows": rows}
    path = tmp_path / "blank.ags"
    groups = [make_files.LOCA, make_files.SAMP, make_files.CONG, cons]
    make_files.write_file(path, "4.2", groups)
    project = ht.Project.from_ags(path, db=tmp_path / "blank.sqlite")
    with pytest.warns(UserWarning, match="Left out 1 of 1 CONS records"):
        df = project.oedometer(display_units="SI")
    assert df.empty
    assert "applied_vertical_stress" in df.columns


def test_ac12_no_cong_gives_an_empty_frame(fresh):
    with pytest.warns(UserWarning, match="No CONG group"):
        df = fresh("defects").oedometer()
    assert df.empty
    assert set(INCREMENT_COLUMNS) <= set(df.columns)


def test_ac12_an_increment_with_no_cong_row_is_kept(tmp_path):
    # A CONS row with no CONG row breaks AGS Rule 10c, so the file is built
    # here (tests/data/ags/README.md).
    cons = {**make_files.CONS, "rows": make_files.CONS["rows"][:2]}
    path = tmp_path / "orphan.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA, make_files.SAMP, cons])
    project = ht.Project.from_ags(path, db=tmp_path / "orphan.sqlite")
    df = _quiet(project.oedometer, display_units="SI")
    assert df["applied_vertical_stress"].tolist() == [25, 50]
    assert df["load_branch"].tolist() == ["loading", "loading"]
    assert df["test_type"].isna().all() and df["void_ratio"].isna().all()
    assert df["particle_density_assumed"].isna().all()


def test_ac13_feeds_the_plots(site):
    df = _quiet(site.oedometer)
    for figure in (
        _quiet(ht.plot.profile, df, "void_ratio"),
        _quiet(
            ht.plot.geology_unit_comparison,
            df.drop_duplicates("specimen_id"),
            "void_ratio",
        ),
    ):
        plt.close(figure[0])


def test_ac15_common_arguments_filter(site):
    everything = _quiet(site.oedometer)
    assert len(_quiet(site.oedometer, where={"test_type": "OEDOMETER"})) == 12
    assert _quiet(site.oedometer, where={"test_type": "SWELLPRESS"}).empty
    assert len(_quiet(site.oedometer, holes="BH1")) == 12
    assert _quiet(site.oedometer, holes="BH2").empty
    assert len(_quiet(site.oedometer, depth=(5, 5.5))) == 12
    assert _quiet(site.oedometer, depth=(0, 5)).empty
    unit = everything["geology_unit"].iloc[0]
    assert len(_quiet(site.oedometer, geology=unit)) == 12
