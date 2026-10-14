"""p.permeability() (datasets.md §6.4)."""

import warnings

import pandas as pd
import pytest

import hangtu as ht

from .conftest import make_files


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


def test_lab_and_field(fresh):
    df = _quiet(fresh("site_si").permeability)
    assert list(df["source"]) == ["lab", "lab", "field"]
    lab, field = df.iloc[0], df.iloc[2]
    assert lab["hydraulic_conductivity"] == pytest.approx(2.3e-9)
    assert (lab["depth"], lab["depth_basis"]) == (pytest.approx(1.60), "spec_depth")
    # FGHG 3.00 to 4.00 m: zone midpoint 3.50 m.
    assert field["depth"] == pytest.approx(3.50)
    assert (field["depth_top"], field["depth_base"]) == pytest.approx((3.0, 4.0))
    assert field["depth_basis"] == "zone_mid"
    assert field["test_type"] == "Falling head"
    assert field["hydraulic_conductivity"] == pytest.approx(4.2e-6)


def test_fghs_stages_are_not_included(fresh):
    df = _quiet(fresh("site_si").permeability)
    assert (df["source"] == "field").sum() == 1  # FGHG only, not its two stages


def test_iprg_one_row_per_stage(fresh):
    df = _quiet(fresh("site_v404").permeability)
    field = df[df["source"] == "field"]
    assert list(field["hydraulic_conductivity"]) == pytest.approx([4.0e-6, 4.4e-6])
    assert list(field["depth"]) == pytest.approx([3.50, 3.50])


def test_us_units(fresh):
    df = _quiet(fresh("site_us", display_units="US").permeability)
    assert df.attrs["units"]["hydraulic_conductivity"] == "cm/s"
    assert df["hydraulic_conductivity"].iloc[0] == pytest.approx(2.3e-7)


def test_twins_agree(fresh):
    si = _quiet(fresh("site_si").permeability).drop(columns="source_line")
    us = _quiet(fresh("site_us").permeability).drop(columns="source_line")
    pd.testing.assert_frame_equal(si, us, rtol=1e-9)


def test_qualifier(tmp_path):
    fghg = make_files.group(
        "FGHG",
        [*make_files.FGHG_KEY, ("FGHG_IPRM", "XN", "m/s")],
        [["BH1", 3.00, 4.00, "1", "<1E-9"], ["BH1", 5.00, 6.00, "2", "2E-6"]],
    )
    path = tmp_path / "k.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA, fghg])
    df = _quiet(ht.Project.from_ags(path, display_units="SI").permeability)
    assert list(df["qualifier"]) == ["<", ""]
    assert df["hydraulic_conductivity"].iloc[0] == pytest.approx(1e-9)


def test_no_permeability_groups(tmp_path):
    path = tmp_path / "none.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA])
    with pytest.warns(UserWarning, match="No PTST, FGHG or IPRG group in none.ags"):
        df = ht.Project.from_ags(path).permeability()
    assert df.empty and "hydraulic_conductivity" in df.columns
