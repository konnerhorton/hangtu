"""Datasets against the acceptance criteria of docs/data/datasets.md §13.

Criteria tested in detail elsewhere are checked end to end here, and point to
the file with the cases.
"""

import warnings

import matplotlib.pyplot as plt
import pandas as pd
import pytest

import hangtu as ht
from hangtu.registry import column_info

from .conftest import DATA, STRATA

DATASETS = (
    "spt",
    "atterberg",
    "grain_size",
    "permeability",
    "grain_size_summary",
    "index_properties",
)


@pytest.fixture(scope="module")
def projects(tmp_path_factory):
    """The good files with the geology map, display units SI. Don't modify them."""
    folder = tmp_path_factory.mktemp("acceptance")
    built = {}
    for name in ("site_si", "site_us", "site_v404"):
        p = ht.Project.from_ags(
            DATA / f"{name}.ags", db=folder / f"{name}.sqlite", display_units="SI"
        )
        p.set_geology_map(STRATA)
        built[name] = p
    return built


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # HangtuHint is a warning too
        return call(*args, **kwargs)


def _legend(ax):
    return [text.get_text() for text in ax.get_legend().get_texts()]


# 1. Feeds the plots unchanged, with no error, warning or hint.
@pytest.mark.parametrize("name", ["site_si", "site_us"])
@pytest.mark.parametrize("system", ["SI", "US"])
def test_1_feeds_the_plots(projects, name, system):
    p = projects[name]
    spt = _quiet(p.spt, display_units=system)
    atterberg = _quiet(p.atterberg, display_units=system)
    calls = [
        (ht.plot.spt_profile, spt),
        (ht.plot.spt_histogram, spt),
        (
            ht.plot.profile,
            _quiet(p.permeability, display_units=system),
            "hydraulic_conductivity",
        ),
        (ht.plot.profile, atterberg, "liquid_limit"),
        (ht.plot.geology_unit_comparison, atterberg, "plasticity_index"),
    ]
    for plot, *args in calls:
        fig, _ax = _quiet(plot, *args)
        plt.close(fig)


def test_1_with_the_map_colors_and_order(projects):
    fig, ax = _quiet(ht.plot.spt_profile, _quiet(projects["site_si"].spt))
    units = [label for label in _legend(ax) if label in ("Fill", "Alluvium", "Terrace")]
    assert units == ["Alluvium", "Terrace"]  # map order; no Fill SPT here
    plt.close(fig)


# 2. Twin files give equal datasets, in SI and in US.
@pytest.mark.parametrize("system", ["SI", "US"])
def test_2_twin_files(projects, system):
    si, us = projects["site_si"], projects["site_us"]
    for name in DATASETS:
        a = _quiet(getattr(si, name), display_units=system)
        b = _quiet(getattr(us, name), display_units=system)
        # sample_reference quotes SAMP_TOP as each file wrote it, in its unit.
        drop = ["source_line", "sample_reference"]
        pd.testing.assert_frame_equal(
            a.drop(columns=drop, errors="ignore"),
            b.drop(columns=drop, errors="ignore"),
            rtol=1e-9,
            obj=name,
        )
        assert a.attrs == b.attrs
    pd.testing.assert_frame_equal(
        si.locations.drop(columns="source_line"),
        us.locations.drop(columns="source_line"),
        rtol=1e-9,
    )


# 3. An older version: IPRG gives one field row per stage.
def test_3_older_version(projects):
    k = _quiet(projects["site_v404"].permeability)
    field = k[k["source"] == "field"]
    assert len(field) == 2
    assert (field["test_type"] == "Falling head").all()


# 4. Golden depths with their basis (test_joins.py has every case).
def test_4_depths(projects):
    p = projects["site_si"]
    spt = _quiet(p.spt)
    assert list(spt["depth"][:3]) == pytest.approx([3.300, 6.2125, 2.300])
    assert list(spt["depth_basis"][:3]) == [
        "mid_drive",
        "mid_drive",
        "mid_drive_nominal",
    ]
    assert _quiet(p.atterberg)["depth_basis"].eq("spec_depth").all()
    k = _quiet(p.permeability)
    assert k["depth"].iloc[-1] == pytest.approx(3.50)
    assert k["depth_basis"].iloc[-1] == "zone_mid"


# 5. to 7. Geology: boundaries, gaps, overlaps, the map and the key.
def test_5_to_7_geology_on_joins(tmp_path):
    p = ht.Project.from_ags(DATA / "joins.ags", db=tmp_path / "j.sqlite")
    p.set_geology_map(STRATA)
    with pytest.warns(UserWarning) as caught:
        spt = p.spt(display_units="SI", geology_fields=["GEOL_GEOL"])
    by_line = spt.set_index("source_line")
    assert by_line.loc[45, "geology_unit"] == "Alluvium"  # on the 2.00 m boundary
    assert by_line.loc[47, "geology_unit"] == "Terrace"  # overlap: deepest top
    assert pd.isna(by_line.loc[49, "geology_unit"])  # in the gap
    assert by_line.loc[50, "geology_unit"] == "BED"  # unmapped, kept
    assert by_line.loc[45, "soil_class"] == "fine"
    assert by_line.loc[45, "geology_code"] == "ALV"
    assert list(spt["geology_unit"].cat.categories) == [
        "Fill",
        "Alluvium",
        "Terrace",
        "BED",
    ]
    messages = " ".join(str(w.message) for w in caught)
    assert "overlapping GEOL layers" in messages
    assert "codes not in the geology map: 'BED'" in messages
    assert "G004" in set(p.qc().findings["rule_id"])


def test_6_session_palette_beats_the_map(projects):
    spt = _quiet(projects["site_si"].spt)
    with ht.settings.override(palette={"Alluvium": "black"}):
        fig, ax = _quiet(ht.plot.spt_profile, spt)
    colors = {
        c.get_label(): tuple(c.get_facecolor()[0])
        for c in ax.collections
        if c.get_label() in ("Alluvium", "Terrace")
    }
    assert colors["Alluvium"] == pytest.approx((0.0, 0.0, 0.0, 1.0))
    plt.close(fig)


def test_7_geology_key_absent(tmp_path):
    p = ht.Project.from_ags(
        DATA / "site_si.ags", db=tmp_path / "k.sqlite", geology_key="GEOL_BGS"
    )
    with pytest.warns(UserWarning, match="has GEOL_GEOL, GEOL_FORM"):
        spt = p.spt()
    assert spt["geology_unit"].isna().all()


# 8. Flags are columns, never blanks.
def test_8_flags(projects):
    p = projects["site_si"]
    spt = _quiet(p.spt)
    assert bool(spt["spt_refusal"].iloc[1]) and spt["spt_n"].iloc[1] == 50
    atterberg = _quiet(p.atterberg)
    np_row = atterberg[atterberg["non_plastic"]].iloc[0]
    assert pd.isna(np_row["plastic_limit"])


@pytest.fixture(scope="module")
def joins_spt(tmp_path_factory):
    db = tmp_path_factory.mktemp("joins") / "j.sqlite"
    p = ht.Project.from_ags(DATA / "joins.ags", db=db, display_units="SI")
    with pytest.warns(UserWarning) as caught:
        spt = p.spt()
    assert any("Left out 1 of 9 ISPT records" in str(w.message) for w in caught)
    return spt


def test_8_refusal_with_a_blank_n(joins_spt):
    # Line 53: ISPT_NVAL blank, ISPT_REP "22-30-50/3\"", NPEN 376 mm.
    row = joins_spt.set_index("source_line").loc[53]
    assert pd.isna(row["spt_n"])
    assert bool(row["spt_refusal"]) is True
    assert row["spt_n_capped"] == ht.settings.spt_cap
    assert row["depth"] == pytest.approx(7.263)  # 7.00 + 0.150 + 0.226 / 2
    assert 48 not in set(joins_spt["source_line"])  # blank report: still incomplete


def test_8_plots_draw_a_refusal_with_a_blank_n(joins_spt):
    # Refusals at lines 46, 49 and 53; J2's (51) has no elevation, so it is
    # one of the blanks.
    _, ax = ht.plot.spt_profile(joins_spt)
    assert ax.ags_notes == {"nan": 1, "refusal": 3}
    plt.close("all")
    # Refusals at 80, 83, 85 and 87: 4 of the 8 tests kept.
    _, ax = ht.plot.spt_histogram(joins_spt, color_by=None)
    assert [t.get_text() for t in ax.get_xticklabels()][-1] == "Refusal"
    assert ax.containers[0][-1].get_height() == pytest.approx(50.0)
    plt.close("all")


# 9. Filters (test_frame.py has every argument and error).
def test_9_filters(projects):
    p = projects["site_si"]
    spt = _quiet(p.spt, geology=["Alluvium"], holes=["BH1", "BH2"], depth=(0, 4))
    assert list(spt["source_line"]) == [55, 57]


# 10. Incomplete records left out, or kept on request.
def test_10_incomplete(tmp_path):
    p = ht.Project.from_ags(DATA / "joins.ags", db=tmp_path / "i.sqlite")
    with pytest.warns(UserWarning) as caught:
        assert 48 not in set(p.spt()["source_line"])
    assert any("Left out 1 of 9 ISPT records" in str(w.message) for w in caught)
    with pytest.warns(UserWarning, match="overlapping"):
        assert 48 in set(p.spt(include_incomplete=True)["source_line"])


# 11. N60 provenance (test_spt.py has all four cases).
def test_11_energy_source(projects):
    with pytest.warns(UserWarning, match="Energy ratio 70 % used for"):
        sources = projects["site_si"].spt(hammer_efficiency=70)["energy_source"]
    assert list(sources) == [
        "file_n60",
        "file_energy_ratio",
        "file_n60",
        "file_n60",
        "hammer_efficiency",
    ]


# 12. Units on every numeric column; particle size in mm in US.
@pytest.mark.parametrize("name", DATASETS)
def test_12_units(projects, name):
    df = _quiet(getattr(projects["site_si"], name), display_units="US")
    with_units = {
        column
        for column in df.columns
        if (info := column_info(column))
        and info.get("quantity") not in (None, "count", "dimensionless")
    }
    assert with_units <= set(df.attrs["units"])
    if name == "grain_size":
        assert df.attrs["units"]["particle_size"] == "mm"


# 13. A missing group gives an empty dataset and a warning (test_spt.py).
def test_13_empty(tmp_path):
    path = tmp_path / "loca_only.ags"
    text = (DATA / "joins.ags").read_text(encoding="utf-8")
    path.write_text(text.split('"GROUP","GEOL"')[0], encoding="utf-8")
    p = ht.Project.from_ags(path)
    for name in DATASETS:
        with pytest.warns(UserWarning, match="No .* group in loca_only.ags"):
            assert getattr(p, name)().empty


# 14. The M8 datasets feed the plots, with no error, warning or hint.
@pytest.mark.parametrize("name", ["site_si", "site_us"])
@pytest.mark.parametrize("system", ["SI", "US"])
def test_14_m8_datasets_feed_the_plots(projects, name, system):
    p = projects[name]
    calls = [
        (ht.plot.plasticity_chart, _quiet(p.atterberg, display_units=system)),
        (ht.plot.grain_size, _quiet(p.grain_size, display_units=system)),
    ]
    for plot, *args in calls:
        fig, _ax = _quiet(plot, *args)
        plt.close(fig)
    index = _quiet(p.index_properties, display_units=system)
    assert index["uscs_symbol"].dropna().tolist() == ["SP-SM"]
    fig, _ax = _quiet(ht.plot.water_content_profile, index, display_units=system)
    plt.close(fig)


# 15. The summary: one row per GRAT specimen, as gradation() gives it on the
# curves, and the same on the twins (test 2; test_grain_size_summary.py).
@pytest.mark.parametrize("name", ["site_si", "site_us"])
def test_15_summary(projects, name):
    p = projects[name]
    summary = _quiet(p.grain_size_summary)
    curves = _quiet(p.grain_size)
    assert len(summary) == curves["specimen_id"].nunique()
    expected = _quiet(ht.analysis.gradation, curves)
    for column in ("d10", "d30", "d60", "fines_content", "sand_content"):
        assert summary[column].tolist() == pytest.approx(expected[column].tolist())


# 16. Combining a sample's specimens on joins.ags (test_index_properties.py).
def test_16_combining(tmp_path):
    p = ht.Project.from_ags(
        DATA / "joins.ags", db=tmp_path / "joins.sqlite", display_units="SI"
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        index = p.index_properties().set_index("sample_reference")
    messages = [str(w.message) for w in caught]
    assert any(m.startswith("3 samples had more than one specimen") for m in messages)
    atterberg = _quiet(p.atterberg).set_index(
        ["sample_reference", "specimen_reference"]
    )["specimen_id"]
    # The Atterberg specimen nearest the water content specimen's 1.15.
    assert index.loc["J1-U1", "atterberg_specimen_id"] == atterberg["J1-U1", "1"]
    # A tie goes to the lower SPEC_REF.
    assert index.loc["J1-U3", "atterberg_specimen_id"] == atterberg["J1-U3", "A"]
    # A sample with only a grading has blank limits.
    assert pd.isna(index.loc["J1-B4", "liquid_limit"])
    assert index.loc["J1-B4", "grain_size_specimen_id"] is not None
    # A specimen with both tests keeps its water content and limits together.
    row = index.loc["J2-U1"]
    assert row["water_content_specimen_id"] == row["atterberg_specimen_id"]
    assert row["atterberg_specimen_id"] == atterberg["J2-U1", "2"]
