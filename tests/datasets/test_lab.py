"""p.atterberg() and p.grain_size() (datasets.md §6.2, §6.3)."""

import warnings

import pandas as pd
import pytest

import hangtu as ht

from .conftest import make_files


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


@pytest.fixture
def atterberg(fresh):
    return _quiet(fresh("site_si").atterberg)


def test_atterberg_values(atterberg):
    bh1 = atterberg.iloc[0]
    assert (bh1["liquid_limit"], bh1["plastic_limit"]) == (48, 22)
    assert bh1["plasticity_index"] == 26
    assert bh1["water_content"] == 32  # LNMC on the same specimen
    # LI = (32 - 22) / 26 = 0.3846; Ic = (48 - 32) / 26 = 0.6154.
    assert bh1["liquidity_index"] == pytest.approx(10 / 26)
    assert bh1["consistency_index"] == pytest.approx(16 / 26)
    assert (bh1["depth"], bh1["depth_basis"]) == (pytest.approx(1.60), "spec_depth")
    assert bh1["elevation"] == pytest.approx(12.40 - 1.60)
    assert bh1["sample_reference"] == "BH1-U1"
    assert bh1["specimen_reference"] == "1"


def test_non_plastic_is_not_blank(atterberg):
    np_row = atterberg.iloc[1]
    assert bool(np_row["non_plastic"]) is True
    assert np_row["liquid_limit"] == 31  # given, so kept
    assert pd.isna(np_row["plastic_limit"]) and pd.isna(np_row["plasticity_index"])
    assert pd.isna(np_row["liquidity_index"])
    assert atterberg["non_plastic"].tolist() == [False, True, False, True]


def test_water_content_needs_the_same_specimen(atterberg):
    # BH2-D1 has no LNMC row; BH3-B1 has both, on the same specimen.
    assert pd.isna(atterberg.iloc[1]["water_content"])
    assert atterberg.iloc[2]["water_content"] == 41
    assert atterberg.iloc[3]["water_content"] == 12


def test_specimen_ids_are_shared_with_grain_size(fresh):
    p = fresh("site_si")
    curves = _quiet(p.grain_size)
    assert curves["specimen_id"].nunique() == 1
    # BH3-B1's grading and limits are on one specimen.
    assert curves["specimen_id"].iloc[0] == _quiet(p.atterberg)["specimen_id"].iloc[3]


def test_lab_depth_fallbacks(fresh):
    df = _quiet(fresh("joins").atterberg).iloc[:3]
    assert list(df["depth"]) == pytest.approx([1.10, 1.25, 3.00])
    assert list(df["depth_basis"]) == ["spec_depth", "sample_mid", "sample_top"]
    assert df["depth_top"].isna().all()  # no SPEC_BASE


def _build(tmp_path, *groups):
    path = tmp_path / "lab.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA, *groups])
    return ht.Project.from_ags(path, db=tmp_path / "lab.sqlite", display_units="SI")


SPEC = ["BH1", 1.50, "1", "U", "BH1-U1", "1", 1.60]


def test_plasticity_index_filled_and_its_limits(tmp_path):
    llpl = make_files.group(
        "LLPL",
        [
            *make_files.SPECIMEN,
            ("LLPL_LL", "0DP", "%"),
            ("LLPL_PL", "0DP", "%"),
            ("LLPL_PI", "0DP", ""),
        ],
        [[*SPEC, 40, 25, None], [*SPEC[:5], "2", 1.70, 30, 30, None]],
    )
    lnmc = make_files.group(
        "LNMC", [*make_files.SPECIMEN, ("LNMC_MC", "0DP", "%")], [[*SPEC, 20]]
    )
    df = _quiet(_build(tmp_path, make_files.SAMP, llpl, lnmc).atterberg)
    assert list(df["plasticity_index"]) == [15, 0]  # 40 - 25, 30 - 30
    assert df["liquidity_index"].iloc[0] == pytest.approx((20 - 25) / 15)
    assert pd.isna(df["liquidity_index"].iloc[1])  # PI = 0


def test_several_water_contents_warn(tmp_path):
    # Two LNMC rows on one specimen break AGS Rule 10a (datasets.md §12), so
    # the file is built here rather than kept as a test file.
    llpl = make_files.group(
        "LLPL",
        [*make_files.SPECIMEN, ("LLPL_LL", "0DP", "%"), ("LLPL_PL", "0DP", "%")],
        [[*SPEC, 40, 25]],
    )
    lnmc = make_files.group(
        "LNMC",
        [*make_files.SPECIMEN, ("LNMC_MC", "0DP", "%")],
        [[*SPEC, 20], [*SPEC, 22]],
    )
    p = _build(tmp_path, make_files.SAMP, llpl, lnmc)
    with pytest.warns(UserWarning, match=r"more than one water content .*BH1 BH1-U1/1"):
        df = p.atterberg()
    assert pd.isna(df["water_content"].iloc[0])


def test_sample_reference_without_samp_id(tmp_path):
    headings = [h for h in make_files.SPECIMEN if h[0] != "SAMP_ID"]
    llpl = make_files.group(
        "LLPL",
        [*headings, ("LLPL_LL", "0DP", "%"), ("LLPL_PL", "0DP", "%")],
        [["BH1", 1.50, "1", "U", "1", 1.60, 40, 25]],
    )
    # SAMP_ID is part of the sample key, which min_fields requires, so the
    # record is incomplete and kept only on request.
    p = _build(tmp_path, llpl)
    with pytest.warns(UserWarning, match="SAMP_ID on line"):
        assert p.atterberg().empty
    df = _quiet(p.atterberg, include_incomplete=True)
    assert df["sample_reference"].iloc[0] == "U1 at 1.50 m"
    assert df["depth"].iloc[0] == pytest.approx(1.60)


def test_grain_size(fresh):
    curves = _quiet(fresh("site_si").grain_size)
    assert list(curves["particle_size"]) == pytest.approx([20.0, 2.0, 0.425, 0.063])
    assert list(curves["percent_passing"]) == [100, 88, 40, 8]
    assert list(curves["source_line"]) == sorted(curves["source_line"])
    assert set(curves["qualifier"]) == {""}


def test_grain_size_in_us_keeps_mm(fresh):
    curves = _quiet(fresh("site_us", display_units="US").grain_size)
    assert curves.attrs["units"]["particle_size"] == "mm"
    assert curves["particle_size"].iloc[2] == pytest.approx(0.425)
    assert curves.attrs["units"]["depth"] == "ft"


def test_grain_size_qualifier(tmp_path):
    grat = make_files.group(
        "GRAT",
        [*make_files.SPECIMEN, ("GRAT_SIZE", "3SF", "mm"), ("GRAT_PERP", "XN", "%")],
        [[*SPEC, 2.0, "100"], [*SPEC, 0.063, "<5"]],
    )
    df = _quiet(_build(tmp_path, make_files.SAMP, grat).grain_size)
    assert list(df["qualifier"]) == ["", "<"]
    assert df["percent_passing"].iloc[1] == 5


def test_twins_agree(fresh):
    for name in ("atterberg", "grain_size"):
        si = _quiet(getattr(fresh("site_si"), name)).drop(columns="source_line")
        us = _quiet(getattr(fresh("site_us"), name)).drop(columns="source_line")
        si = si.drop(columns="sample_reference")
        us = us.drop(columns="sample_reference")
        pd.testing.assert_frame_equal(si, us, rtol=1e-9)
