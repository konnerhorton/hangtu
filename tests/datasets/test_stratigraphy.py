"""p.stratigraphy() (datasets.md §6.7; docs/work/m13a-judgments.md, Decision 4)."""

import warnings

import matplotlib.pyplot as plt
import pandas as pd
import pytest

import hangtu as ht

from .conftest import STRATA, make_files


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


@pytest.fixture
def mapped(fresh):
    def build(name="site_si", **settings):
        p = fresh(name, **settings)
        p.set_geology_map(STRATA)
        return p

    return build


def test_one_row_per_geol_layer_mapped_and_ordered(mapped):
    # Criterion 7.
    df = _quiet(mapped().stratigraphy)
    assert list(df.columns) == [
        *ht.template("stratigraphy").columns,
        "source_line",
    ]
    assert list(df["loca_id"]) == ["BH1", "BH1", "BH2", "BH3"]
    assert list(df["depth_top"]) == pytest.approx([0.0, 2.5, 0.0, 0.0])
    assert list(df["depth_base"]) == pytest.approx([2.5, 10.0, 8.5, 6.0])
    assert list(df["geology_unit"]) == ["Fill", "Alluvium", "Alluvium", "Terrace"]
    assert list(df["geology_unit"].cat.categories) == ["Fill", "Alluvium", "Terrace"]
    assert list(df["soil_class"]) == ["fill", "fine", "fine", "coarse"]
    assert df["geology_description"].iloc[0] == "Brown sandy CLAY with gravel"
    assert list(df["source_line"]) == [34, 35, 36, 37]
    assert df.attrs["units"] == {"depth_top": "m", "depth_base": "m"}
    assert df.attrs["palette"]["Alluvium"] == "tan"


def test_us_twin_agrees(mapped):
    si = _quiet(mapped("site_si").stratigraphy).drop(columns="source_line")
    us = _quiet(mapped("site_us").stratigraphy).drop(columns="source_line")
    pd.testing.assert_frame_equal(si, us, rtol=1e-9)


def test_us_display_units(mapped):
    df = _quiet(mapped().stratigraphy, display_units="US")
    assert df.attrs["units"] == {"depth_top": "ft", "depth_base": "ft"}
    assert df["depth_base"].iloc[0] == pytest.approx(2.5 / 0.3048)


def test_filters(mapped):
    p = mapped()
    assert list(_quiet(p.stratigraphy, holes="BH1")["geology_unit"]) == [
        "Fill",
        "Alluvium",
    ]
    assert list(_quiet(p.stratigraphy, geology="Terrace")["loca_id"]) == ["BH3"]
    assert list(_quiet(p.stratigraphy, contains="sand")["loca_id"]) == ["BH1", "BH3"]
    fields = _quiet(p.stratigraphy, geology_fields="GEOL_FORM")
    assert list(fields["geology_formation"]) == [
        "Fill",
        "Alluvium",
        "Alluvium",
        "Terrace",
    ]


def test_no_depth_filter():
    with pytest.raises(TypeError):
        ht.Project.stratigraphy(None, depth=(0, 3))


def test_overlaps_and_gaps_are_kept(fresh):
    # qc_defects.ags: BH1 has a gap 2.5 to 3.0 m, BH3 an overlap 3.5 to 4.0 m.
    p = fresh("qc_defects")
    with pytest.warns(UserWarning) as record:
        df = p.stratigraphy()
    messages = [str(w.message) for w in record]
    assert any("GEOL has no GEOL_GEOL heading" in m for m in messages)
    assert any("Left out 1 of 9 GEOL records" in m for m in messages)
    bh1 = df[df["loca_id"] == "BH1"]
    assert list(zip(bh1["depth_top"], bh1["depth_base"], strict=True)) == [
        (0.0, 2.5),
        (3.0, 10.0),
    ]
    bh3 = df[df["loca_id"] == "BH3"]
    assert list(bh3["depth_top"]) == [0.0, 2.0, 3.5]
    assert list(bh3["depth_base"]) == [2.0, 4.0, 6.0]


def test_unmapped_codes_warn(fresh):
    p = fresh()
    p.set_geology_map(pd.read_csv(STRATA).iloc[:2])  # no TRC
    with pytest.warns(UserWarning, match=r"codes not in the geology map: 'TRC'"):
        df = p.stratigraphy()
    assert df["geology_unit"].iloc[-1] == "TRC"


def test_no_geol_group_is_empty_with_a_warning(tmp_path):
    path = tmp_path / "no_geol.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA])
    with pytest.warns(UserWarning, match="No GEOL group in no_geol.ags"):
        df = ht.Project.from_ags(path).stratigraphy()
    assert df.empty
    assert list(df.columns) == [*ht.template("stratigraphy").columns, "source_line"]


def test_one_hole_feeds_p01_strata(mapped):
    # Criterion 9: filtered to one hole as in Decision 8, P01 draws it as it is.
    p = mapped()
    log = _quiet(p.stratigraphy)
    one_hole = log[log["loca_id"] == "BH1"]
    fig, ax = _quiet(ht.plot.spt_profile, _quiet(p.spt, holes="BH1"), strata=one_hole)
    labels = {text.get_text() for text in ax.texts}
    assert {"Fill", "Alluvium"} <= labels
    plt.close(fig)
