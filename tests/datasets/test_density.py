"""p.density() and p.particle_density() (datasets.md §6.8, §6.9).

Acceptance criteria are those of docs/work/m14a-density-data.md (AC n).
"""

import warnings

import pandas as pd
import pytest

import hangtu as ht

from .conftest import make_files


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


# --- p.particle_density() ------------------------------------------------------------


def test_particle_density_measured_and_assumed(fresh):
    # AC 4: "2.68" is measured; "#2.65" is assumed, with its number kept.
    df = _quiet(fresh("site_si").particle_density)
    assert list(df["loca_id"]) == ["BH1", "BH2"]
    assert list(df["particle_density"]) == pytest.approx([2.68, 2.65])
    assert list(df["particle_density_assumed"]) == [False, True]
    assert list(df["test_type"]) == ["SMALL PYK", "SMALL PYK"]
    assert (df["depth"].iloc[0], df["depth_basis"].iloc[0]) == (
        pytest.approx(1.65),
        "spec_depth",
    )
    assert df.attrs["units"]["particle_density"] == "Mg/m3"


def test_particle_density_in_us_units(fresh):
    # 2.68 Mg/m3 / (0.45359237 kg / 0.3048^3 m3 / 1000) = 167.307 pcf.
    df = _quiet(fresh("site_us", display_units="US").particle_density)
    assert df.attrs["units"]["particle_density"] == "pcf"
    assert df["particle_density"].iloc[0] == pytest.approx(167.307, rel=1e-5)


def test_particle_density_twins_agree(fresh):
    # AC 9.
    si = _quiet(fresh("site_si").particle_density).drop(columns="source_line")
    us = _quiet(fresh("site_us").particle_density).drop(columns="source_line")
    pd.testing.assert_frame_equal(si, us, rtol=1e-9)


def test_particle_density_filters_on_the_flag(fresh):
    df = _quiet(fresh("site_si").particle_density, where={"loca_id": "BH2"})
    assert list(df["particle_density_assumed"]) == [True]


def test_no_lpdn_group(tmp_path):
    # AC 11.
    path = tmp_path / "none.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA])
    with pytest.warns(UserWarning, match="No LPDN group in none.ags"):
        df = ht.Project.from_ags(path).particle_density()
    assert df.empty and "particle_density_assumed" in df.columns
    assert str(df["particle_density_assumed"].dtype) == "boolean"
