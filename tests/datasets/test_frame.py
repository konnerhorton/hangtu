"""What every dataset shares: joins, units, filters, warnings (datasets.md §2 to §8).

These tests build a minimal dataset (ISPT rows at their top depth) straight
through ``Build``, so the pipeline is tested apart from any one dataset.
"""

import warnings

import pandas as pd
import pytest

import hangtu as ht
from hangtu.datasets._frame import Build

from .conftest import STRATA

COLUMNS = ["loca_id", "ground_level", "depth", "elevation"]


def _dataset(project, display_units=None, include_incomplete=False, **common):
    build = Build(
        project.path,
        noun=("test", "tests"),
        display_units=display_units,
        include_incomplete=include_incomplete,
    )
    rows = build.rows("ISPT")
    frame = pd.DataFrame(
        {
            "location_id": rows["location_id"],
            "loca_id": rows["LOCA_ID"],
            "depth": build.numbers(rows, "ISPT_TOP"),
            "_line": rows["_line"],
        }
    )
    return build.finish(frame, COLUMNS, group="ISPT", **common)


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


# --- p.locations (§3) ------------------------------------------------------------


def test_locations(fresh):
    df = fresh().locations
    assert list(df.columns) == [
        "loca_id",
        "location_type",
        "ground_level",
        "final_depth",
        "easting",
        "northing",
        "latitude",
        "longitude",
        "remarks",
        "source_line",
    ]
    bh1 = df.iloc[0]
    assert (bh1["loca_id"], bh1["location_type"]) == ("BH1", "CP")
    assert (bh1["ground_level"], bh1["final_depth"]) == pytest.approx((12.40, 10.00))
    assert bh1["latitude"] == pytest.approx(37 + 47 / 60 + 36.1 / 3600)
    assert df.attrs["units"]["ground_level"] == "m"


def test_locations_twins_agree(fresh, tmp_path):
    si = fresh("site_si").locations
    us = fresh("site_us").locations  # both built with display_units="SI"
    pd.testing.assert_frame_equal(
        si.drop(columns="source_line"), us.drop(columns="source_line"), rtol=1e-9
    )


# --- Joins and units (§4, §5) -----------------------------------------------------


def test_ground_level_and_elevation(fresh):
    df = _quiet(_dataset, fresh())
    first = df.iloc[0]
    assert (first["ground_level"], first["depth"]) == pytest.approx((12.40, 3.00))
    assert first["elevation"] == pytest.approx(9.40)
    assert first["source_line"] == 98


def test_us_display_units_and_attrs(fresh):
    df = _quiet(_dataset, fresh(), display_units="US")
    assert df["depth"].iloc[0] == pytest.approx(3.00 / 0.3048)
    assert df.attrs["units"] == {"ground_level": "ft", "depth": "ft", "elevation": "ft"}
    for unit in df.attrs["units"].values():
        ht.units.parse_unit(unit)  # reads back without a warning


def test_the_project_datum_travels_with_the_dataset(fresh):
    df = _quiet(_dataset, fresh(vertical_datum="NAVD88"))
    assert df.attrs["vertical_datum"] == "NAVD88"
    assert "vertical_datum" not in _quiet(_dataset, fresh()).attrs


def test_geology_codes_without_a_map(fresh):
    df = _quiet(_dataset, fresh())
    assert list(df["geology_unit"]) == ["ALV", "ALV", "ALV", "ALV", "TRC"]
    assert df["geology_description"].iloc[4] == "Medium dense brown SAND"
    assert df["soil_class"].isna().all()
    assert "palette" not in df.attrs


def test_geology_map(fresh):
    p = fresh()
    p.set_geology_map(STRATA)
    df = _quiet(_dataset, p)
    assert list(df["geology_unit"]) == ["Alluvium"] * 4 + ["Terrace"]
    assert list(df["geology_unit"].cat.categories) == ["Fill", "Alluvium", "Terrace"]
    assert df["geology_unit"].cat.ordered
    assert list(df["soil_class"]) == ["fine"] * 4 + ["coarse"]
    assert df.attrs["palette"] == {
        "Fill": "#a0a0a0",
        "Alluvium": "tan",
        "Terrace": "#d9b26f",
    }


def test_geology_key_absent(fresh):
    p = fresh(geology_key="GEOL_LEG")
    with pytest.warns(UserWarning, match=r"GEOL has no GEOL_LEG heading.*GEOL_GEOL"):
        df = _dataset(p)
    assert df["geology_unit"].isna().all()
    assert df["geology_description"].notna().all()


def test_geology_key_setting(fresh):
    df = _quiet(_dataset, fresh(geology_key="GEOL_FORM"))
    assert df["geology_unit"].iloc[0] == "Alluvium"


def test_geology_fields(fresh):
    df = _quiet(_dataset, fresh(), geology_fields=["GEOL_FORM", "GEOL_GEOL"])
    assert list(df.columns[-3:]) == ["geology_formation", "geology_code", "source_line"]
    assert df["geology_formation"].iloc[0] == "Alluvium"
    with pytest.raises(ht.HangtuError, match=r"GEOL_DESC.*Headings: GEOL_GEOL"):
        _dataset(fresh(), geology_fields="GEOL_DESC")


def test_joins_warnings(fresh):
    p = fresh("joins")
    p.set_geology_map(STRATA)
    with pytest.warns(UserWarning) as caught:
        df = _dataset(p)
    messages = [str(w.message) for w in caught]
    assert any("codes not in the geology map: 'BED' (1 row)" in m for m in messages)
    assert any(
        "1 test in J1 is in overlapping GEOL layers" in m
        and "deepest top" in m
        and "(G003)" in m
        for m in messages
    )
    assert any(
        "Left out 1 of 9 ISPT records with a blank required field "
        "(ISPT_NVAL on line 82)"
        in m
        and "include_incomplete=True" in m
        for m in messages
    )
    assert len(messages) == 3
    assert list(df["geology_unit"].cat.categories)[-1] == "BED"
    assert len(df) == 8


def test_include_incomplete(fresh):
    p = fresh("joins")
    with pytest.warns(UserWarning, match="overlapping"):
        df = _dataset(p, include_incomplete=True)
    assert len(df) == 9


def test_empty_group(fresh):
    build = Build(
        fresh("joins").path, noun=("permeability result", "permeability results")
    )
    with pytest.warns(UserWarning, match="No PTST group in joins.ags, so there are no"):
        df = build.finish(pd.DataFrame(), COLUMNS, group="PTST")
    assert df.empty
    assert list(df.columns) == [*COLUMNS, *GEOLOGY, "source_line"]


GEOLOGY = ["geology_unit", "soil_class", "geology_description"]


# --- Filters (§2) ----------------------------------------------------------------


def test_holes_filter(fresh):
    df = _quiet(_dataset, fresh(), holes=["BH2", "BH3"])
    assert list(df["loca_id"]) == ["BH2", "BH2", "BH3"]
    assert _quiet(_dataset, fresh(), holes="BH3")["loca_id"].tolist() == ["BH3"]
    with pytest.raises(ht.HangtuError, match=r"'BH9'\. Holes: BH1, BH2, BH3"):
        _dataset(fresh(), holes=["BH9"])


def test_geology_filter(fresh):
    p = fresh()
    p.set_geology_map(STRATA)
    assert _quiet(_dataset, p, geology=["Terrace"])["loca_id"].tolist() == ["BH3"]
    # A mapped unit with no rows here is still a unit: an empty result, no error.
    assert _quiet(_dataset, p, geology="Fill").empty
    with pytest.raises(ht.HangtuError, match=r"'Till'\. Units: Fill, Alluvium"):
        _dataset(p, geology=["Till"])


@pytest.mark.parametrize(
    ("depth", "expected"),
    [
        ((2.0, 5.0), [3.0, 2.0, 5.0]),
        ((5.0, 2.0), [3.0, 2.0, 5.0]),  # either order
        ((None, 2.0), [2.0, 1.5]),
        ((5.0, None), [6.0, 5.0]),
        (("6.5 ft", "10 ft"), [3.0, 2.0]),  # 1.98 m to 3.05 m
    ],
)
def test_depth_filter(fresh, depth, expected):
    df = _quiet(_dataset, fresh(), depth=depth)
    assert list(df["depth"]) == pytest.approx(expected)


def test_depth_filter_in_us_units(fresh):
    df = _quiet(_dataset, fresh(), display_units="US", depth=(0, 6))  # ft
    assert list(df["loca_id"]) == ["BH3"]  # 1.50 m = 4.9 ft


@pytest.mark.parametrize(
    ("depth", "message"),
    [
        (3, r"must be a pair \(low, high\)"),
        ("0 ft", r"must be a pair"),
        ((0, "3 kPa"), r"depth=: .*Example: depth=\(0, 30\)"),
        ((0, [3]), r"numbers in the dataset's units, quantity strings or None"),
    ],
)
def test_depth_filter_errors(fresh, depth, message):
    with pytest.raises(ht.HangtuError, match=message):
        _dataset(fresh(), depth=depth)


def test_elevation_filter_counts_rows_with_no_elevation(fresh):
    with pytest.warns(UserWarning) as caught:
        df = _dataset(fresh("joins"), elevation=(0, 20))
    assert "J2" not in set(df["loca_id"])
    assert any(
        "Left out 1 test with no elevation (no LOCA_GL)" in str(w.message)
        for w in caught
    )


def test_where_and_contains(fresh):
    df = _quiet(_dataset, fresh(), where={"loca_id": ["BH1", "BH3"]})
    assert list(df["loca_id"]) == ["BH1", "BH1", "BH3"]
    assert _quiet(_dataset, fresh(), contains="sand")["loca_id"].tolist() == ["BH3"]
    assert len(_quiet(_dataset, fresh(), contains=["SAND", "silty"])) == 5
    with pytest.raises(ht.HangtuError, match=r"'spt_n'\. Columns: loca_id"):
        _dataset(fresh(), where={"spt_n": 10})
    with pytest.raises(ht.HangtuError, match="must be a dict"):
        _dataset(fresh(), where=["BH1"])
