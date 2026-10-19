"""p.index_properties(), one row per sample (datasets.md §6.6)."""

import warnings

import pandas as pd
import pytest

import hangtu as ht

from .conftest import make_files

CHOSEN = "3 samples had more than one specimen of a test; the one nearest"
#: J1-B4 has a grading with about 11 % fines and no limits (decision 8).
UNCLASSIFIED = [
    "uscs_symbol is blank for 1 of 1 specimens: 1 with no plasticity class.",
    "aashto_group is blank for 1 of 1 specimens",
]


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


@pytest.fixture
def joins(fresh):
    return fresh("joins")


def _with_warnings(call, **kwargs):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        df = call(**kwargs)
    return df, [str(w.message) for w in caught]


@pytest.fixture
def index(joins):
    df, messages = _with_warnings(joins.index_properties)
    assert len(messages) == 3
    for expected in [*UNCLASSIFIED, CHOSEN]:
        assert sum(m.startswith(expected) for m in messages) == 1, expected
    return df.set_index("sample_reference")


def _specimen(project, sample, specimen, dataset="atterberg"):
    """The specimen_id of a sample's specimen, looked up in another dataset."""
    df = _quiet(getattr(project, dataset))
    found = df[
        (df["sample_reference"] == sample) & (df["specimen_reference"] == specimen)
    ]
    assert len(found) == 1
    return found["specimen_id"].iloc[0]


def test_one_row_per_sample_in_order_of_first_test(index):
    # LNMC first (J1-U1, J2-U1), then LLPL (J1-D2, J1-U3), then GRAT (J1-B4).
    assert list(index.index) == ["J1-U1", "J2-U1", "J1-D2", "J1-U3", "J1-B4"]


def test_nearest_atterberg_specimen_to_the_water_content(joins, index):
    # Water content specimen 3 at 1.15: specimen 1 at 1.10 is 0.05 away,
    # specimen 2 (no depth, so at the sample's 1.25) 0.10.
    row = index.loc["J1-U1"]
    assert row["atterberg_specimen_id"] == _specimen(joins, "J1-U1", "1")
    assert (row["liquid_limit"], row["plastic_limit"]) == (45, 20)
    assert row["water_content"] == 28
    assert (row["depth"], row["depth_basis"]) == (pytest.approx(1.15), "spec_depth")
    assert row["grain_size_specimen_id"] is None


def test_a_tie_goes_to_the_lower_spec_ref(joins, index):
    # B at 6.30 and A at 6.20 are both 0.05 from the sample's 6.25; B has the
    # lower specimen key (it's first in the file), so SPEC_REF decides.
    row = index.loc["J1-U3"]
    assert row["atterberg_specimen_id"] == _specimen(joins, "J1-U3", "A")
    assert row["liquid_limit"] == 36
    assert (row["depth"], row["depth_basis"]) == (pytest.approx(6.25), "sample_mid")
    assert row["water_content_specimen_id"] is None
    assert pd.isna(row["water_content"])


def test_a_specimen_keeps_its_water_content_and_limits_together(joins, index):
    # Specimen 2 has both; specimen 1, at the same depth, has the lower SPEC_REF.
    row = index.loc["J2-U1"]
    both = _specimen(joins, "J2-U1", "2")
    assert row["water_content_specimen_id"] == row["atterberg_specimen_id"] == both
    assert (row["water_content"], row["liquid_limit"]) == (30, 40)
    assert pd.isna(row["elevation"])  # J2 has no ground level


def test_a_sample_with_only_a_grading(joins, index):
    row = index.loc["J1-B4"]
    assert row["grain_size_specimen_id"] == _specimen(
        joins, "J1-B4", "1", "grain_size_summary"
    )
    assert row[["liquid_limit", "plastic_limit", "water_content"]].isna().all()
    assert bool(row["non_plastic"]) is False
    assert row["atterberg_specimen_id"] is None


def test_a_sample_with_one_specimen_of_each_test(index):
    # J1-D2 has no base and one Atterberg specimen with no depth: sample_top.
    row = index.loc["J1-D2"]
    assert (row["depth"], row["depth_basis"]) == (pytest.approx(3.00), "sample_top")
    assert row["liquid_limit"] == 38


def test_source_line_is_the_samples(joins, index):
    samp = joins.table("SAMP").set_index("SAMP_ID")["_line"]
    for sample, line in index["source_line"].items():
        assert line == samp[sample]


def test_columns_and_units(joins):
    df, _ = _with_warnings(joins.index_properties)
    assert list(df.columns) == [
        "loca_id",
        "sample_reference",
        "ground_level",
        "depth",
        "depth_basis",
        "elevation",
        "water_content",
        "liquid_limit",
        "plastic_limit",
        "plasticity_index",
        "non_plastic",
        "liquidity_index",
        "consistency_index",
        "plasticity_class_uscs",
        "plasticity_class_bs5930",
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
        "uscs_symbol",
        "aashto_group",
        "aashto_group_index",
        "water_content_specimen_id",
        "atterberg_specimen_id",
        "grain_size_specimen_id",
        "geology_unit",
        "soil_class",
        "geology_description",
        "source_line",
    ]
    units = df.attrs["units"]
    assert (units["depth"], units["water_content"], units["d10"]) == ("m", "%", "mm")
    assert units["fines_content"] == "%"


def test_the_good_files(fresh):
    df = _quiet(fresh("site_si").index_properties).set_index("sample_reference")
    assert list(df.index) == ["BH1-U1", "BH2-U2", "BH3-B1", "BH2-D1"]
    # BH3-B1 has all three tests on one specimen.
    row = df.loc["BH3-B1"]
    assert (
        row["water_content_specimen_id"]
        == row["atterberg_specimen_id"]
        == row["grain_size_specimen_id"]
    )
    # BH2-D1 has no water content, so its depth is the sample's midpoint, not
    # its specimen's 2.00: (2.00 + 2.45) / 2.
    assert df.loc["BH2-D1", "depth"] == pytest.approx(2.225)
    assert df.loc["BH2-D1", "depth_basis"] == "sample_mid"


def test_filters_act_on_the_reference_depth(joins):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        shallow = joins.index_properties(depth=(1.12, 1.20))
        alluvium = joins.index_properties(geology=["ALV"])
    assert shallow["sample_reference"].tolist() == ["J1-U1"]
    assert alluvium["sample_reference"].tolist() == ["J2-U1", "J1-D2"]


def test_the_chosen_count_follows_the_filters(joins):
    _quiet(joins.index_properties, where={"sample_reference": "J1-D2"})


def test_good_file_sample_is_classified(fresh):
    p = fresh("site_si")
    row = _quiet(p.index_properties).set_index("sample_reference").loc["BH3-B1"]
    # About 11 % fines (5 to 12 %), sand over gravel, Cu 11.4 but Cc 0.95
    # (under 1): SP, and NP fines (ML): SP-SM. AASHTO: 40 % passing 0.425 mm
    # and about 11 % passing 0.075 mm, NP: A-1-b, group index 0.
    assert row["uscs_symbol"] == "SP-SM"
    assert (row["aashto_group"], row["aashto_group_index"]) == ("A-1-b", 0)
    summary = _quiet(p.grain_size_summary).iloc[0]
    for column in [
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
    ]:
        assert row[column] == summary[column], column


def test_classes_use_another_specimens_water_content(index):
    # J1-U1: water content 28 (specimen 3), limits LL 45, PL 20 (specimen 1).
    row = index.loc["J1-U1"]
    assert row["plasticity_index"] == 25
    assert row["liquidity_index"] == pytest.approx((28 - 20) / 25)
    assert row["consistency_index"] == pytest.approx((45 - 28) / 25)
    assert (row["plasticity_class_uscs"], row["plasticity_class_bs5930"]) == (
        "CL",
        "CI",
    )


def test_only_samples_with_a_grading_are_classified(index):
    # Samples with only limits get no symbol and aren't counted in the
    # warnings (1 of 1 specimens, the fixture's messages).
    assert index["uscs_symbol"].isna().all()
    assert index.drop("J1-B4")["fraction_system"].isna().all()
    assert index.loc["J1-B4", "fraction_system"] == "astm_uscs"
    # 5 to 12 % fines need the fines' plasticity, which J1-B4 hasn't.
    assert 5 < index.loc["J1-B4", "fines_content"] < 12


def test_no_lab_groups_is_empty_with_one_warning(tmp_path):
    path = tmp_path / "no_lab.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA, make_files.SAMP])
    p = ht.Project.from_ags(path, db=tmp_path / "no_lab.sqlite", display_units="SI")
    with pytest.warns(UserWarning, match="No LNMC, LLPL or GRAT group") as caught:
        df = p.index_properties()
    assert len(caught) == 1
    assert df.empty
    assert "atterberg_specimen_id" in df.columns
    assert df.attrs["units"]["depth"] == "m"


SAMPLE = ["BH1", 1.50, "1", "U", "BH1-U1"]  # 1.50 to 1.95 in make_files.SAMP


def _project(tmp_path, *groups):
    path = tmp_path / "lab.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA, *groups])
    return ht.Project.from_ags(path, db=tmp_path / "lab.sqlite", display_units="SI")


def _lnmc(*rows):
    return make_files.group(
        "LNMC", [*make_files.SPECIMEN, ("LNMC_MC", "0DP", "%")], list(rows)
    )


def _llpl(*rows):
    return make_files.group(
        "LLPL",
        [*make_files.SPECIMEN, ("LLPL_LL", "0DP", "%"), ("LLPL_PL", "0DP", "%")],
        list(rows),
    )


def test_one_water_content_specimen_with_no_depth(tmp_path):
    # Its depth, and basis, are the sample's: (1.50 + 1.95) / 2.
    p = _project(tmp_path, make_files.SAMP, _lnmc([*SAMPLE, "1", None, 20]))
    row = _quiet(p.index_properties).iloc[0]
    assert (row["depth"], row["depth_basis"]) == (pytest.approx(1.725), "sample_mid")


def test_several_water_content_specimens(tmp_path):
    # The reference is the sample's 1.725; the water content at 1.70 is used,
    # and the limits nearest 1.725, at 1.80, not those of the 1.55 specimen.
    p = _project(
        tmp_path,
        make_files.SAMP,
        _lnmc([*SAMPLE, "1", 1.55, 20], [*SAMPLE, "2", 1.70, 25]),
        _llpl([*SAMPLE, "1", 1.55, 40, 20], [*SAMPLE, "3", 1.80, 45, 22]),
    )
    with pytest.warns(UserWarning, match=r"^1 sample had more than one"):
        row = p.index_properties().iloc[0]
    assert (row["depth"], row["depth_basis"]) == (pytest.approx(1.725), "sample_mid")
    assert (row["water_content"], row["liquid_limit"]) == (25, 45)


def test_a_sample_with_no_samp_row(tmp_path):
    # Ingest gives it no sample or specimen key; it is still a sample, with
    # a blank source_line and specimen IDs.
    p = _project(tmp_path, _lnmc([*SAMPLE, "1", 1.60, 20]))
    row = _quiet(p.index_properties).iloc[0]
    assert row["water_content"] == 20
    assert row["sample_reference"] == "BH1-U1"
    assert pd.isna(row["source_line"])
    assert row["water_content_specimen_id"] is None


def test_include_incomplete(tmp_path):
    # The LLPL row nearer the water content has a blank LL (C001): left out by
    # default, so the other specimen's limits are used.
    p = _project(
        tmp_path,
        make_files.SAMP,
        _lnmc([*SAMPLE, "1", 1.60, 20]),
        _llpl([*SAMPLE, "1", 1.60, None, 20], [*SAMPLE, "2", 1.90, 45, 22]),
    )
    with pytest.warns(UserWarning, match="Left out 1 of 2 LLPL records"):
        assert p.index_properties()["liquid_limit"].iloc[0] == 45
    with pytest.warns(UserWarning, match=r"^1 sample had more than one"):
        row = p.index_properties(include_incomplete=True).iloc[0]
    assert pd.isna(row["liquid_limit"]) and row["plastic_limit"] == 20


def test_where_can_name_a_symbol(fresh):
    df = _quiet(fresh("site_si").index_properties, where={"uscs_symbol": "SP-SM"})
    assert df["sample_reference"].tolist() == ["BH3-B1"]


def test_classification_warnings_follow_the_filters(joins):
    # J1-B4 can't be classified, but holes= leaves it out, so only the chosen
    # count (J2-U1) is warned about.
    _, messages = _with_warnings(joins.index_properties, holes=["J2"])
    assert len(messages) == 1
    assert messages[0].startswith("1 sample had more than one specimen")
