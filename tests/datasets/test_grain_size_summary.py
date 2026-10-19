"""p.grain_size_summary() (datasets.md §6.5)."""

import warnings

import pandas as pd
import pytest

import hangtu as ht

from .conftest import make_files


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


COLUMNS = [
    "loca_id",
    "specimen_id",
    "sample_reference",
    "specimen_reference",
    "ground_level",
    "depth",
    "depth_basis",
    "elevation",
    "d10",
    "d30",
    "d60",
    "uniformity_coefficient",
    "curvature_coefficient",
    "fines_content",
    "sand_content",
    "gravel_content",
    "cobbles_content",
    "boulders_content",
    "fraction_system",
    "geology_unit",
    "soil_class",
    "geology_description",
]


def test_one_row_per_specimen_as_gradation_gives(fresh):
    p = fresh("site_si")
    summary = _quiet(p.grain_size_summary)
    assert list(summary.columns) == COLUMNS
    expected = _quiet(ht.analysis.gradation, _quiet(p.grain_size))
    assert len(summary) == _quiet(p.grain_size)["specimen_id"].nunique() == 1
    for column in COLUMNS:
        assert summary[column].tolist() == expected[column].tolist(), column
    row = summary.iloc[0]
    assert (row["sample_reference"], row["depth"]) == ("BH3-B1", pytest.approx(1.00))
    assert row["fraction_system"] == "astm_uscs"
    assert row["geology_unit"] == "TRC"


def test_units(fresh):
    summary = _quiet(fresh("site_us", display_units="US").grain_size_summary)
    units = summary.attrs["units"]
    assert (units["d10"], units["depth"], units["fines_content"]) == ("mm", "ft", "%")
    assert "qualifier" not in summary and "source_line" not in summary


def test_aashto_fractions_and_other_d_values(fresh):
    summary = _quiet(
        fresh("site_si").grain_size_summary, fractions="aashto", d_values=(15, 85)
    )
    assert list(summary.columns[8:10]) == ["d15", "d85"]
    assert "d10" not in summary
    assert "silt_clay_content" in summary and "fines_content" not in summary
    assert summary["fraction_system"].iloc[0] == "aashto"
    assert summary.attrs["units"]["d85"] == "mm"


def test_filters_keep_or_drop_whole_curves(fresh):
    p = fresh("site_si")
    assert len(_quiet(p.grain_size_summary, geology=["TRC"])) == 1
    assert len(_quiet(p.grain_size_summary, holes=["BH3"], depth=(0.5, 1.5))) == 1
    empty = _quiet(p.grain_size_summary, depth=(2, 3))
    assert empty.empty
    assert list(empty.columns) == COLUMNS


def test_no_grat_is_empty_with_one_warning(tmp_path):
    path = tmp_path / "no_grat.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA, make_files.SAMP])
    p = ht.Project.from_ags(path, db=tmp_path / "no_grat.sqlite", display_units="SI")
    with pytest.warns(UserWarning, match="No GRAT group") as caught:
        summary = p.grain_size_summary(d_values=(15, 85))
    assert len(caught) == 1
    assert summary.empty
    assert list(summary.columns[8:10]) == ["d15", "d85"]
    assert summary.attrs["units"]["d15"] == "mm"
    assert summary["d15"].dtype == float


def test_twins_agree(fresh):
    si = _quiet(fresh("site_si").grain_size_summary).drop(columns="sample_reference")
    us = _quiet(fresh("site_us").grain_size_summary).drop(columns="sample_reference")
    pd.testing.assert_frame_equal(si, us, rtol=1e-9)


def test_a_curve_gradation_rejects_is_kept_blank(tmp_path):
    # QC P002: 104 % passing. gradation() rejects the table; the dataset keeps
    # the curve with blank values, so the other curve is still summarized.
    spec_1 = ["BH1", 1.50, "1", "U", "BH1-U1", "1", 1.60]
    spec_2 = ["BH1", 1.50, "1", "U", "BH1-U1", "2", 1.70]
    grat = make_files.group(
        "GRAT",
        [*make_files.SPECIMEN, ("GRAT_SIZE", "3SF", "mm"), ("GRAT_PERP", "0DP", "%")],
        [
            [*spec_1, 20.0, 104],
            [*spec_1, 0.063, 50],
            [*spec_2, 20.0, 100],
            [*spec_2, 0.063, 5],
        ],
    )
    path = tmp_path / "p002.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA, make_files.SAMP, grat])
    p = ht.Project.from_ags(path, db=tmp_path / "p002.sqlite", display_units="SI")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        summary = p.grain_size_summary()
    messages = [str(w.message) for w in caught]
    assert any(
        "outside 0 to 100" in m and "BH1 BH1-U1/1." in m and "(P002)" in m
        for m in messages
    )
    assert summary["specimen_reference"].tolist() == ["1", "2"]
    assert summary.loc[0, ["d60", "fines_content"]].isna().all()
    assert summary["fraction_system"].tolist() == ["astm_uscs", "astm_uscs"]
    assert summary["d60"][1] > 0
