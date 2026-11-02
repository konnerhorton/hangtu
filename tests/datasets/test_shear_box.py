"""p.shear_box() (datasets.md §6.12).

Acceptance criteria are those of docs/work/m17a-strength-data.md (AC n). The
values are the test files' (tests/data/ags/_make_files.py): BH2-D1's small
shear box set at SHBT_NORM 50, 100 and 200 kPa; unit weights are density ×
9.80665; 1 in = 25.4 mm.
"""

import warnings

import numpy as np
import pytest

from .conftest import make_files

#: 1 psf in kPa: 0.45359237 × 9.80665 / 0.3048² / 1000 (exact).
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


@pytest.fixture
def site(fresh):
    project = fresh("site_si")
    project.set_geology_map(make_files.HERE / "strata.csv")
    return project


def test_one_row_per_stage_with_its_test(site):
    # AC 11
    df = _quiet(site.shear_box)
    assert df["test_stage"].tolist() == ["1", "2", "3"]
    assert set(df["test_type"]) == {"SMALL SBOX"}
    assert set(df["sample_condition"]) == {"RECOMPACTED"}
    assert df["applied_normal_stress"].tolist() == [50, 100, 200]
    assert df["normal_stress_at_peak"].tolist() == [50, 100, 200]
    assert df["normal_stress_at_residual"].tolist() == [50, 100, 200]
    assert df["peak_shear_stress"].tolist() == [38, 68, 128]
    assert df["residual_shear_stress"].tolist() == [30, 58, 112]
    assert set(df["reported_peak_cohesion"]) == {8}
    assert set(df["reported_peak_friction_angle"]) == {31.0}
    assert set(df["reported_residual_friction_angle"]) == {28.5}
    assert df["bulk_unit_weight"].tolist() == pytest.approx([19.1229675] * 3, rel=1e-9)
    assert df["peak_displacement_rate"].tolist() == pytest.approx([0.024] * 3)
    assert df["vertical_displacement_at_peak"].tolist() == pytest.approx(
        [0.30, 0.10, -0.15]
    )
    assert set(df["shear_traverses"]) == {3}
    assert set(df["failure_criterion"]) == {"Maximum shear stress"}
    assert not df["particle_density_assumed"].any()
    assert df["depth"].tolist() == pytest.approx([2.10] * 3)
    assert set(df["geology_unit"]) == {"Alluvium"}
    assert "multistage_test" not in df.columns


def test_us_display(fresh):
    # AC 11: 68 kPa = 1420.2095 psf; 0.024 mm/min = 0.024 / 25.4 in/min.
    df = _quiet(fresh("site_si", display_units="US").shear_box)
    assert df.attrs["units"]["peak_shear_stress"] == "psf"
    assert df.attrs["units"]["peak_displacement_rate"] == "in/min"
    assert df.attrs["units"]["horizontal_displacement_at_peak"] == "in"
    assert df["peak_shear_stress"].iloc[1] == pytest.approx(1420.2095, rel=1e-6)
    assert df["peak_displacement_rate"].iloc[0] == pytest.approx(0.024 / 25.4)
    assert df["reported_peak_friction_angle"].iloc[0] == 31.0


@pytest.mark.parametrize("display_units", ["SI", "US"])
def test_twins_agree(fresh, display_units):
    # AC 6 (shear box half)
    si = _quiet(fresh("site_si", display_units=display_units).shear_box)
    us = _quiet(fresh("site_us", display_units=display_units).shear_box)
    numeric = si.select_dtypes("number").columns.drop("source_line")
    np.testing.assert_allclose(
        si[numeric].to_numpy(float), us[numeric].to_numpy(float), rtol=1e-9
    )
    assert si.attrs["units"] == us.attrs["units"]


def test_a_rock_joint_and_a_ring_shear_test(fresh):
    # AC 12: J1-U3 R1 in MPa, set in resin; J1-D2 R2 a ring shear residual.
    df = _quiet(fresh("joins").shear_box)
    joint = df[df["specimen_reference"] == "R1"].iloc[0]
    assert joint["applied_normal_stress"] == pytest.approx(500)
    assert joint["peak_shear_stress"] == pytest.approx(420)
    assert joint["encapsulation"] == "Resin"
    assert joint["specimen_diameter_along_shear"] == pytest.approx(85.2)
    assert joint["specimen_diameter_across_shear"] == pytest.approx(89.3)
    assert joint["test_type"] is None
    ring = df[df["specimen_reference"] == "R2"].iloc[0]
    assert ring["test_type"] == "SMALL RSHEAR"
    assert np.isnan(ring["peak_shear_stress"])
    assert ring["residual_shear_stress"] == pytest.approx(21)


def test_no_shbt_gives_an_empty_frame(fresh):
    # AC 15 (shear box half)
    with pytest.warns(UserWarning, match="No SHBT group"):
        df = fresh("defects").shear_box()
    assert df.empty
    assert "peak_shear_stress" in df.columns


def test_common_arguments_filter(site):
    # AC 19
    df = _quiet(site.shear_box, where={"test_stage": "2"})
    assert df["applied_normal_stress"].tolist() == [100]
    assert _quiet(site.shear_box, holes="BH1").empty
    assert len(_quiet(site.shear_box, depth=(2, 3), geology="Alluvium")) == 3
