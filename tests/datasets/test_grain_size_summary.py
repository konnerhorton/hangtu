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
    "grading_source",
    "geology_unit",
    "soil_class",
    "geology_description",
]


def test_one_row_per_specimen_as_gradation_gives(fresh):
    # AC 15 still holds for the curves; BH2-D1, a reported grading, follows.
    p = fresh("site_si")
    summary = _quiet(p.grain_size_summary)
    assert list(summary.columns) == COLUMNS
    expected = _quiet(ht.analysis.gradation, _quiet(p.grain_size))
    curves = summary[summary["grading_source"] == "curve"]
    assert len(curves) == _quiet(p.grain_size)["specimen_id"].nunique() == 1
    for column in [c for c in COLUMNS if c != "grading_source"]:
        assert curves[column].tolist() == expected[column].tolist(), column
    row = summary.iloc[0]
    assert (row["sample_reference"], row["depth"]) == ("BH3-B1", pytest.approx(1.00))
    assert row["fraction_system"] == "astm_uscs"
    assert row["geology_unit"] == "TRC"
    assert summary["sample_reference"].tolist() == ["BH3-B1", "BH2-D1"]


def test_units(fresh):
    summary = _quiet(fresh("site_us", display_units="US").grain_size_summary)
    units = summary.attrs["units"]
    assert (units["d10"], units["depth"], units["fines_content"]) == ("mm", "ft", "%")
    assert "qualifier" not in summary and "source_line" not in summary


def test_aashto_fractions_and_other_d_values(fresh):
    # BH2-D1 is reported as astm_uscs, so its aashto sand split and gravel are
    # blank (datasets.md §6.13).
    with pytest.warns(UserWarning, match="1 grading is reported as astm_uscs"):
        summary = fresh("site_si").grain_size_summary(
            fractions="aashto", d_values=(15, 85)
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
    assert len(_quiet(p.grain_size_summary, depth=(2, 3))) == 1  # BH2-D1
    empty = _quiet(p.grain_size_summary, depth=(3, 4))
    assert empty.empty
    assert list(empty.columns) == COLUMNS


def test_no_grat_or_grag_is_empty_with_one_warning(tmp_path):
    path = tmp_path / "no_grat.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA, make_files.SAMP])
    p = ht.Project.from_ags(path, db=tmp_path / "no_grat.sqlite", display_units="SI")
    with pytest.warns(
        UserWarning, match="No GRAT or GRAG group in no_grat.ags, so there are no"
    ) as caught:
        summary = p.grain_size_summary(d_values=(15, 85))
    assert len(caught) == 1
    assert summary.empty
    assert list(summary.columns[8:10]) == ["d15", "d85"]
    assert summary.attrs["units"]["d15"] == "mm"
    assert summary["d15"].dtype == float
    assert list(summary.columns) == [
        *COLUMNS[:8],
        "d15",
        "d85",
        *COLUMNS[11:],
    ]


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


# --- Reported gradings (datasets.md §6.13; golden values in the grag-fractions
# work file) ---------------------------------------------------------------------

GRAG_NAMES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7"]


def _by_sample(summary):
    return summary.set_index("sample_reference")


def _fractions(row, names):
    return {
        name: (None if pd.isna(row[f"{name}_content"]) else row[f"{name}_content"])
        for name in names
    }


ASTM = ["fines", "sand", "gravel", "cobbles", "boulders"]


def test_reported_gradings_follow_the_curves(fresh):
    # AC 18 (summary half), 22, 23.
    summary = _quiet(fresh("grag").grain_size_summary)
    assert list(summary.columns) == COLUMNS
    assert summary["sample_reference"].tolist() == ["G8", *GRAG_NAMES]
    assert summary["grading_source"].tolist() == ["curve", *["reported"] * 7]
    assert (summary["fraction_system"] == "astm_uscs").all()
    rows = _by_sample(summary)
    expected = {
        "G1": [33.0, 45.0, 22.0, 0.0, 0.0],
        "G3": [3.0, 87.0, 10.0, 0.0, 0.0],
        "G5": [33.0, 45.0, 22.0, 0.0, 0.0],
        "G6": [31.5, 45.0, 22.0, 0.0, 0.0],
        "G7": [30.0, 45.0, 20.0, None, None],
    }
    for name, values in expected.items():
        assert _fractions(rows.loc[name], ASTM) == dict(
            zip(ASTM, values, strict=True)
        ), name
    g3 = rows.loc["G3"]
    assert (g3["uniformity_coefficient"], g3["curvature_coefficient"]) == (8.0, 1.5)
    assert rows.loc[GRAG_NAMES, ["d10", "d30", "d60"]].isna().all().all()
    # G8: the curve, not its GRAG row (fines 8 %): 88 % passes 2 mm.
    curve = _quiet(ht.analysis.gradation, _quiet(fresh("grag").grain_size))
    assert rows.loc["G8", "fines_content"] == pytest.approx(
        curve["fines_content"].iloc[0]
    )
    assert rows.loc["G8", "fines_content"] != 8.0
    assert rows.loc["G8", "d60"] > 0


def test_iso14688_reported_gradings(fresh):
    # AC 18: G4 as the lab reported it.
    p = fresh("grag", grag_fraction_system="iso14688")
    with pytest.warns(UserWarning, match="clay in 1 curve"):  # G8, no hydrometer
        summary = p.grain_size_summary(fractions="iso14688")
    names = ["clay", "silt", "sand", "gravel", "cobbles", "boulders"]
    assert _fractions(_by_sample(summary).loc["G4"], names) == dict(
        zip(names, [8.0, 20.0, 40.0, 32.0, 0.0, 0.0], strict=True)
    )


def test_another_system_than_the_stated_one(fresh):
    # AC 19: G1 asked as aashto.
    p = fresh("grag")
    with pytest.warns(UserWarning) as caught:
        summary = p.grain_size_summary(fractions="aashto", depth=(0.5, 1.5))
    assert [str(w.message) for w in caught] == [
        "1 grading is reported as astm_uscs fractions (GRAG), so the aashto "
        "fractions with other boundaries are blank: fine_sand, coarse_sand, gravel."
    ]
    names = ["silt_clay", "fine_sand", "coarse_sand", "gravel", "boulders"]
    assert summary["sample_reference"].tolist() == ["G1"]
    assert _fractions(summary.iloc[0], names) == dict(
        zip(names, [33.0, None, None, None, 0.0], strict=True)
    )
    assert summary["fraction_system"].tolist() == ["aashto"]


def test_no_stated_system(fresh):
    # AC 21 (summary half).
    p = fresh("grag", grag_fraction_system=None)
    with pytest.warns(UserWarning) as caught:
        summary = p.grain_size_summary()
    assert len(caught) == 1
    assert str(caught[0].message).startswith(
        "7 gradings are reported only as fractions (GRAG), and their fractions "
        "are blank because the project's GRAG fraction system isn't set."
    )
    reported = summary[summary["grading_source"] == "reported"]
    assert reported["sample_reference"].tolist() == GRAG_NAMES
    assert reported[[f"{name}_content" for name in ASTM]].isna().all().all()
    assert (reported["fraction_system"] == "astm_uscs").all()
    # Cu and Cc are read without a system.
    assert reported["uniformity_coefficient"].notna().sum() == 1


def test_setting_changes_the_next_summary_without_reingest(fresh):
    # AC 17.
    p = fresh("grag", grag_fraction_system=None)
    with pytest.warns(UserWarning, match="isn't set"):
        assert p.grain_size_summary()["fines_content"].isna().sum() == 7
    p.settings.grag_fraction_system = "astm_uscs"
    assert _quiet(p.grain_size_summary)["fines_content"].isna().sum() == 0


def test_an_incomplete_curve_does_not_become_a_reported_grading(tmp_path):
    # AC 22: G8's GRAT rows left out (blank GRAT_PERP, C001).
    groups = make_files.grag_groups()
    grat = groups[-1]
    grat["rows"] = [[*row[:-1], None] for row in grat["rows"]]
    path = tmp_path / "grag_incomplete.ags"
    make_files.write_file(path, "4.2", groups)
    p = ht.Project.from_ags(
        path, db=tmp_path / "g.sqlite", grag_fraction_system="astm_uscs"
    )
    with pytest.warns(UserWarning, match="Left out 4 of 4 GRAT records"):
        summary = p.grain_size_summary()
    assert summary["sample_reference"].tolist() == GRAG_NAMES
    assert (summary["grading_source"] == "reported").all()


def test_filters_act_on_reported_gradings(fresh):
    p = fresh("grag")
    assert _quiet(p.grain_size_summary, depth=(2.5, 4.5))[
        "sample_reference"
    ].tolist() == ["G3", "G4"]
    assert _quiet(p.grain_size_summary, where={"specimen_reference": "9"}).empty
    assert len(_quiet(p.grain_size_summary, geology="TRC")) == 8


def test_good_files_reported_grading(fresh):
    # AC 24 (summary half): BH2-D1 is 0, 35, 65 %.
    for name in ("site_si", "site_us"):
        row = _by_sample(_quiet(fresh(name).grain_size_summary)).loc["BH2-D1"]
        assert _fractions(row, ASTM) == dict(
            zip(ASTM, [65.0, 35.0, 0.0, 0.0, 0.0], strict=True)
        )
        assert row["grading_source"] == "reported"


def test_good_files_without_the_setting(fresh):
    # AC 24: the no-system warning counts BH2-D1; the curves are unchanged.
    p = fresh("site_si", grag_fraction_system=None)
    with pytest.warns(UserWarning, match="^1 grading is reported only") as caught:
        summary = p.grain_size_summary()
    assert len(caught) == 1
    assert summary["grading_source"].tolist() == ["curve", "reported"]
    assert pd.isna(summary.loc[1, "fines_content"])
