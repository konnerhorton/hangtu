"""ht.analysis.vertical_stress() (docs/work/m13a-judgments.md, Decisions 6 and 7)."""

import hashlib
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.analysis._vertical_stress import _integrate

FOOT = 0.3048  # m
PCF = 0.15708746  # kN/m3 per lbf/ft3
PSF = 0.04788026  # kPa per lbf/ft2
DATA = Path(__file__).parents[1] / "data" / "ags"

# Criterion 1: BH01, Fill 0-2 m (18), Clay 2-6 m (19, saturated 20), Sand 6-10 m
# (19.5), water level 3.0 m, gamma_w 9.81 kN/m3. By hand:
#   z = 5:  sv = 18*2 + 19*1 + 20*2 = 95;  u = 9.81*2 = 19.62
#   z = 8:  sv = 36 + 19 + 20*3 + 19.5*2 = 154;  u = 9.81*5 = 49.05
#   z = 12: the Sand carried down, sv = 36 + 19 + 60 + 19.5*6 = 232; u = 88.29
GOLDEN = [
    (0.0, 0.0, 0.0, 0.0),
    (1.0, 18.0, 0.0, 18.0),
    (2.5, 45.5, 0.0, 45.5),
    (3.0, 55.0, 0.0, 55.0),
    (5.0, 95.0, 19.62, 75.38),
    (8.0, 154.0, 49.05, 104.95),
    (12.0, 232.0, 88.29, 143.71),
]
UNIT_WEIGHT = {
    "Fill": "18 kN/m3",
    "Clay": {"bulk_unit_weight": "19 kN/m3", "saturated_unit_weight": "20 kN/m3"},
    "Sand": "19.5 kN/m3",
}


def make_log(
    tops=(0.0, 2.0, 6.0),
    bases=(2.0, 6.0, 10.0),
    units=("Fill", "Clay", "Sand"),
    hole="BH01",
    unit="m",
):
    log = pd.DataFrame(
        {
            "loca_id": hole,
            "depth_top": list(tops),
            "depth_base": list(bases),
            "geology_unit": list(units),
        }
    )
    return ht.set_units(log, {"depth_top": unit, "depth_base": unit})


def make_tests(depths, hole="BH01", unit="m", **columns):
    df = pd.DataFrame({"loca_id": hole, "depth": list(depths), **columns})
    return ht.set_units(df, {"depth": unit, **dict.fromkeys(columns, unit)})


def quiet(*args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return ht.analysis.vertical_stress(*args, **kwargs)


def golden_call(depths, **kwargs):
    kwargs.setdefault("unit_weight", UNIT_WEIGHT)
    kwargs.setdefault("water_level", "3 m")
    kwargs.setdefault("display_units", "SI")
    return ht.analysis.vertical_stress(
        make_tests(depths), stratigraphy=make_log(), **kwargs
    )


def test_integrate_alone_gives_the_golden_values():
    total, pore = _integrate(
        np.array([0.0, 2.0, 6.0]),
        np.array([2.0, 6.0, 12.0]),
        np.array([18.0, 19.0, 19.5]),
        np.array([np.nan, 20.0, np.nan]),
        3.0,
        9.81,
        np.array([row[0] for row in GOLDEN]),
    )
    assert total == pytest.approx([row[1] for row in GOLDEN], abs=1e-9)
    assert pore == pytest.approx([row[2] for row in GOLDEN], abs=1e-9)


def test_integrate_with_water_above_ground():
    # 1.0 m above ground, z = 5 m: sv = 9.81 + 18*2 + 20*3 = 105.81; u = 9.81*6.
    total, pore = _integrate(
        np.array([0.0, 2.0, 6.0]),
        np.array([2.0, 6.0, 10.0]),
        np.array([18.0, 19.0, 19.5]),
        np.array([np.nan, 20.0, np.nan]),
        -1.0,
        9.81,
        np.array([0.0, 5.0]),
    )
    assert total == pytest.approx([9.81, 105.81])
    assert pore == pytest.approx([9.81, 58.86])


def test_golden_values():
    with pytest.warns(
        UserWarning, match=r"below the base of the log.*BH01 \(10 m to 12 m\)"
    ):
        df = golden_call([row[0] for row in GOLDEN])
    for column, i in [
        ("total_vertical_stress", 1),
        ("pore_pressure", 2),
        ("effective_vertical_stress", 3),
    ]:
        assert list(df[column]) == pytest.approx([row[i] for row in GOLDEN], abs=0.005)
    assert {
        column: df.attrs["units"][column]
        for column in (
            "total_vertical_stress",
            "pore_pressure",
            "effective_vertical_stress",
        )
    } == dict.fromkeys(
        ("total_vertical_stress", "pore_pressure", "effective_vertical_stress"), "kPa"
    )
    assert df.attrs["vertical_stress"] == {
        "pore_pressure": "hydrostatic",
        "water_unit_weight": "9.81 kN/m3",
    }


def test_us_twin_agrees():
    depths = [row[0] for row in GOLDEN[:-1]]
    df = make_tests([z / FOOT for z in depths], unit="ft")
    log = make_log(
        tops=[z / FOOT for z in (0.0, 2.0, 6.0)],
        bases=[z / FOOT for z in (2.0, 6.0, 10.0)],
        unit="ft",
    )
    unit_weight = {
        "Fill": f"{18 / PCF} pcf",
        "Clay": {
            "bulk_unit_weight": f"{19 / PCF} pcf",
            "saturated_unit_weight": f"{20 / PCF} pcf",
        },
        "Sand": f"{19.5 / PCF} pcf",
    }
    us = quiet(
        df,
        stratigraphy=log,
        unit_weight=unit_weight,
        water_level=3.0 / FOOT,
        display_units="US",
    )
    assert us.attrs["units"]["effective_vertical_stress"] == "psf"
    expected = [row[3] / PSF for row in GOLDEN[:-1]]
    assert list(us["effective_vertical_stress"]) == pytest.approx(expected, rel=1e-3)


def test_water_level_as_an_elevation_gives_the_same_result():
    depths = [row[0] for row in GOLDEN[:-1]]
    by_depth = quiet(
        make_tests(depths),
        stratigraphy=make_log(),
        unit_weight=UNIT_WEIGHT,
        water_level={"BH01": "3 m"},
        display_units="SI",
    )
    table = ht.set_units(
        pd.DataFrame({"loca_id": ["BH01"], "elevation": [97.0]}), {"elevation": "m"}
    )
    by_elevation = quiet(
        make_tests(depths, ground_level=[100.0] * len(depths)),
        stratigraphy=make_log(),
        unit_weight=UNIT_WEIGHT,
        water_level=table,
        display_units="SI",
    )
    for column in ("total_vertical_stress", "pore_pressure"):
        assert list(by_elevation[column]) == pytest.approx(list(by_depth[column]))


def test_water_above_ground():
    # 1.0 m above ground, z = 5 m: sv = 9.81 + 18*2 + 20*3 = 105.81; u = 9.81*6.
    with pytest.warns(
        UserWarning, match=r"BH01: water level 1 m above ground\. The water"
    ):
        df = golden_call([5.0], water_level=-1.0)
    row = df.iloc[0]
    assert row["total_vertical_stress"] == pytest.approx(105.81)
    assert row["pore_pressure"] == pytest.approx(58.86)
    assert row["effective_vertical_stress"] == pytest.approx(46.95)
    assert df.attrs["vertical_stress"]["water_above_ground"] == {"BH01": "1 m"}


def test_one_unit_weight_for_every_layer():
    df = quiet(
        make_tests([4.0]),
        stratigraphy=make_log(),
        unit_weight="19 kN/m3",
        water_level="10 m",
        display_units="SI",
    )
    assert df["total_vertical_stress"].iloc[0] == pytest.approx(76.0)
    assert df.attrs["judgments"]["unit_weight"] == {
        "source": "argument",
        "by": None,
        "values": {"all": {"bulk_unit_weight": "19 kN/m3"}},
    }


def test_water_unit_weight_setting_is_converted():
    with ht.settings.override(water_unit_weight="62.4 pcf"):
        df = golden_call([5.0])
    assert df["pore_pressure"].iloc[0] == pytest.approx(2 * 62.4 * PCF, rel=1e-6)
    assert df.attrs["vertical_stress"]["water_unit_weight"] == "62.4 pcf"


def test_display_units_default_to_the_session_setting():
    with ht.settings.override(display_units="US"):
        df = golden_call([5.0], display_units=None)
    assert df.attrs["units"]["total_vertical_stress"] == "psf"
    assert df["total_vertical_stress"].iloc[0] == pytest.approx(95 / PSF)


# --- The log (criterion 4) -----------------------------------------------------------


@pytest.mark.parametrize(
    ("log", "message"),
    [
        (make_log(hole="BH02"), r"BH01: no layers"),
        (make_log(tops=(0.5, 2.0, 6.0)), r"BH01: the log starts at 0.5 m, not at 0"),
        (
            make_log(tops=(0.0, 2.5, 6.0)),
            r"(?s)BH01: a gap from 2 m to 2.5 m.*p.qc\(\)",
        ),
        (
            make_log(tops=(0.0, 1.5, 6.0)),
            r"(?s)BH01: an overlap from 1.5 m to 2 m.*G003",
        ),
        (
            make_log(tops=(0.0, np.nan, 6.0)),
            r"BH01: a layer with a blank depth_top or depth_base",
        ),
        (
            make_log(tops=(0.0, 2.0, 6.0), bases=(2.0, 1.0, 10.0)),
            r"BH01: a layer with its base \(1 m\) above its top \(2 m\)",
        ),
        (
            make_log(units=("Fill", None, "Sand")),
            r"BH01: the layer from 2 m to 6 m has no geology_unit",
        ),
    ],
)
def test_log_errors(log, message):
    with pytest.raises(ht.HangtuError, match=message):
        ht.analysis.vertical_stress(
            make_tests([8.0]),
            stratigraphy=log,
            unit_weight=UNIT_WEIGHT,
            water_level="3 m",
        )


def test_one_error_lists_every_hole():
    log = pd.concat(
        [make_log(tops=(0.0, 2.5, 6.0)), make_log(hole="BH02", tops=(0.0, 1.0, 6.0))]
    )
    log = ht.set_units(log, {"depth_top": "m", "depth_base": "m"})
    tests = pd.concat([make_tests([8.0]), make_tests([8.0], hole="BH02")])
    tests = ht.set_units(tests, {"depth": "m"})
    with pytest.raises(
        ht.HangtuError, match=r"these holes:\n  BH01: a gap.*\n  BH02: an overlap"
    ):
        ht.analysis.vertical_stress(
            tests, stratigraphy=log, unit_weight=UNIT_WEIGHT, water_level="3 m"
        )


def test_a_gap_within_the_tolerance_is_rounding():
    log = make_log(tops=(0.0, 2.005, 6.0))
    df = quiet(
        make_tests([5.0]),
        stratigraphy=log,
        unit_weight=UNIT_WEIGHT,
        water_level="3 m",
        display_units="SI",
    )
    assert df["total_vertical_stress"].iloc[0] == pytest.approx(95.0)


def test_a_gap_below_the_deepest_test_is_ignored():
    log = make_log(tops=(0.0, 2.0, 7.0))
    df = quiet(
        make_tests([5.0]),
        stratigraphy=log,
        unit_weight=UNIT_WEIGHT,
        water_level="3 m",
        display_units="SI",
    )
    assert df["total_vertical_stress"].iloc[0] == pytest.approx(95.0)


def test_qc_defects_overlap_raises_through_p_stratigraphy(tmp_path):
    # Criterion 7: BH3's layers overlap from 3.5 to 4.0 m.
    p = ht.Project.from_ags(DATA / "qc_defects.ags", db=tmp_path / "q.sqlite")
    with pytest.warns(UserWarning):
        log = p.stratigraphy(display_units="SI")
    with pytest.raises(ht.HangtuError, match=r"BH3: an overlap from 3.5 m to 4 m"):
        ht.analysis.vertical_stress(
            make_tests([5.0], hole="BH3"),
            stratigraphy=log,
            unit_weight="19 kN/m3",
            water_level="2 m",
        )


def test_stratigraphy_needs_its_own_units():
    log = make_log()
    log.attrs = {}
    with pytest.raises(
        ht.UnitsError, match=r"stratigraphy: Column 'depth_top' has no units"
    ):
        ht.analysis.vertical_stress(
            make_tests([5.0]), stratigraphy=log, unit_weight="19 kN/m3", water_level=3
        )


def test_df_needs_depth_units():
    df = make_tests([5.0])
    df.attrs = {}
    with pytest.raises(ht.UnitsError, match=r"Column 'depth' has no units"):
        ht.analysis.vertical_stress(
            df, stratigraphy=make_log(), unit_weight="19 kN/m3", water_level=3
        )


def test_stratigraphy_needs_the_by_column():
    log = make_log().drop(columns="geology_unit")
    with pytest.raises(ht.ColumnError, match=r"keyed by 'geology_unit'"):
        ht.analysis.vertical_stress(
            make_tests([5.0]), stratigraphy=log, unit_weight=UNIT_WEIGHT, water_level=3
        )


# --- Arguments ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("unit_weight", r"needs unit weights, keyed by geology unit.*judgments="),
        ("water_level", r"needs water levels, keyed by hole.*p.set_judgments"),
    ],
)
def test_a_missing_judgment_raises_naming_it(name, message):
    given = {"unit_weight": UNIT_WEIGHT, "water_level": "3 m"}
    del given[name]
    with pytest.raises(ht.HangtuError, match=message):
        ht.analysis.vertical_stress(make_tests([5.0]), stratigraphy=make_log(), **given)


def test_a_unit_without_a_unit_weight_raises():
    with pytest.raises(
        ht.HangtuError, match=r"unit_weight= has no value for the geology unit 'Sand'"
    ):
        golden_call([8.0], unit_weight={"Fill": "18 kN/m3", "Clay": "19 kN/m3"})


def test_a_hole_without_a_water_level_raises():
    with pytest.raises(
        ht.HangtuError, match=r"water_level= has no value for the hole 'BH01'"
    ):
        golden_call([5.0], water_level={"BH02": "3 m"})


def test_an_entry_for_a_unit_not_in_the_log_warns():
    weights = {**UNIT_WEIGHT, "Peat": "11 kN/m3"}
    with pytest.warns(
        UserWarning, match=r"unit_weight has values for 'Peat'.*geology_unit"
    ):
        golden_call([5.0], unit_weight=weights)


@pytest.mark.parametrize(
    ("argument", "message"),
    [
        ({"unit_weight": 19}, r"unit_weight must be a unit weight with its unit"),
        ({"unit_weight": "19 kPa"}, r"unit_weight bulk_unit_weight: .*unit weight"),
        ({"unit_weight": "-19 kN/m3"}, r"must be positive"),
        (
            {"unit_weight": {"Fill": {"saturated_unit_weight": "20 kN/m3"}}},
            r"bulk_unit_weight",
        ),
        ({"water_level": "3 kPa"}, r"water_level: .*length"),
        ({"water_level": [3]}, r"water_level must be a depth"),
    ],
)
def test_bad_arguments(argument, message):
    given = {"unit_weight": UNIT_WEIGHT, "water_level": "3 m", **argument}
    with pytest.raises(ht.HangtuError, match=message):
        ht.analysis.vertical_stress(make_tests([5.0]), stratigraphy=make_log(), **given)


def test_water_level_table_without_units_takes_df_units():
    table = pd.DataFrame({"loca_id": ["BH01"], "depth": [3.0]})
    with pytest.warns(
        UserWarning, match=r"has no units, so it takes df's depth units \(m\)"
    ):
        df = golden_call([5.0], water_level=table)
    assert df["pore_pressure"].iloc[0] == pytest.approx(19.62)


def test_elevation_without_one_ground_level_per_hole_raises():
    table = ht.set_units(
        pd.DataFrame({"loca_id": ["BH01"], "elevation": [97.0]}), {"elevation": "m"}
    )
    df = make_tests([3.0, 5.0], ground_level=[100.0, 101.0])
    with pytest.raises(ht.HangtuError, match=r"exactly one ground_level"):
        ht.analysis.vertical_stress(
            df, stratigraphy=make_log(), unit_weight=UNIT_WEIGHT, water_level=table
        )


# --- The result -----------------------------------------------------------------------


def test_rows_kept_in_order_with_blanks_counted():
    df = pd.DataFrame(
        {"loca_id": ["BH01", None, "BH01", "BH01"], "depth": [5.0, 3.0, np.nan, 1.0]},
        index=[10, 11, 12, 13],
    )
    df = ht.set_units(df, {"depth": "m"})
    with pytest.warns(UserWarning, match=r"2 rows have no depth or loca_id"):
        result = ht.analysis.vertical_stress(
            df,
            stratigraphy=make_log(),
            unit_weight=UNIT_WEIGHT,
            water_level="3 m",
            display_units="SI",
        )
    assert list(result.index) == [10, 11, 12, 13]
    assert list(result["total_vertical_stress"]) == pytest.approx(
        [95.0, np.nan, np.nan, 18.0], nan_ok=True
    )
    assert "total_vertical_stress" not in df.columns


def test_existing_stress_columns_are_replaced_with_a_warning():
    df = make_tests([5.0])
    df["pore_pressure"] = 1.0
    with pytest.warns(
        UserWarning, match=r"Replaced the existing columns 'pore_pressure'"
    ):
        result = ht.analysis.vertical_stress(
            df,
            stratigraphy=make_log(),
            unit_weight=UNIT_WEIGHT,
            water_level="3 m",
            display_units="SI",
        )
    assert result["pore_pressure"].iloc[0] == pytest.approx(19.62)


def test_recorded_argument_judgments():
    df = golden_call([5.0])
    assert df.attrs["judgments"] == {
        "unit_weight": {
            "source": "argument",
            "by": "geology_unit",
            "values": {
                "Fill": {"bulk_unit_weight": "18 kN/m3"},
                "Clay": {
                    "bulk_unit_weight": "19 kN/m3",
                    "saturated_unit_weight": "20 kN/m3",
                },
            },
        },
        "water_level": {
            "source": "argument",
            "by": None,
            "values": {"all": {"depth": "3 m"}},
        },
    }


# --- The judgments file (criteria 2, 3 and 6) -----------------------------------------

JUDGMENTS = """\
unit_weight:
  by: geology_unit
  units: {bulk_unit_weight: kN/m3, saturated_unit_weight: kN/m3}
  values:
    Fill: {bulk_unit_weight: 18, reason: median LDEN}
    Clay: {bulk_unit_weight: 19, saturated_unit_weight: 20}
    Sand: {bulk_unit_weight: 19.5}
water_level:
  units: {depth: m}
  by_hole:
    BH01: {depth: 3.0, reason: standpipe reading}
"""


def write_judgments(tmp_path, text=JUDGMENTS, name="judgments.yaml"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def from_project(path, depths=(5.0,)):
    """Tests as a Project dataset would give them, carrying the file."""
    df = make_tests(list(depths))
    df.attrs["judgments_file"] = str(path)
    return df


def test_the_file_gives_the_golden_values(tmp_path):
    path = write_judgments(tmp_path)
    df = quiet(
        make_tests([5.0, 8.0]),
        stratigraphy=make_log(),
        judgments=ht.judgments(path),
        display_units="SI",
    )
    assert list(df["total_vertical_stress"]) == pytest.approx([95.0, 154.0])
    assert list(df["pore_pressure"]) == pytest.approx([19.62, 49.05])


def test_the_project_file_comes_from_df_attrs(tmp_path):
    path = write_judgments(tmp_path)
    df = quiet(from_project(path), stratigraphy=make_log(), display_units="SI")
    assert df["effective_vertical_stress"].iloc[0] == pytest.approx(75.38)


def test_judgments_takes_a_path(tmp_path):
    path = write_judgments(tmp_path)
    df = quiet(
        make_tests([5.0]), stratigraphy=make_log(), judgments=path, display_units="SI"
    )
    assert df["effective_vertical_stress"].iloc[0] == pytest.approx(75.38)


def test_an_argument_overrides_the_file_with_a_warning(tmp_path):
    # Criterion 2: per judgment; the other still comes from the file.
    path = write_judgments(tmp_path)
    with pytest.warns(
        UserWarning, match=r"water_level= replaces the water_level in judgments.yaml"
    ):
        df = ht.analysis.vertical_stress(
            from_project(path),
            stratigraphy=make_log(),
            water_level="4 m",
            display_units="SI",
        )
    assert df["pore_pressure"].iloc[0] == pytest.approx(9.81)
    assert df.attrs["judgments"]["water_level"]["source"] == "argument"
    assert df.attrs["judgments"]["unit_weight"]["source"] == str(path)


def test_judgments_differing_from_the_project_file_warns(tmp_path):
    project = write_judgments(tmp_path)
    other = write_judgments(
        tmp_path, JUDGMENTS.replace("depth: 3.0", "depth: 4.0"), "other.yaml"
    )
    with pytest.warns(
        UserWarning, match=r"judgments= is .*other.yaml', not the project's"
    ):
        df = ht.analysis.vertical_stress(
            from_project(project),
            stratigraphy=make_log(),
            judgments=ht.judgments(other),
            display_units="SI",
        )
    assert df["pore_pressure"].iloc[0] == pytest.approx(9.81)


def test_a_merged_frame_without_attrs_gets_the_hint(tmp_path):
    path = write_judgments(tmp_path)
    merged = pd.concat([from_project(path), make_tests([6.0])])
    merged.attrs = {"units": {"depth": "m"}}
    with pytest.raises(
        ht.HangtuError,
        match=r"merge and concat drop df.attrs: pass judgments=p.judgments",
    ):
        ht.analysis.vertical_stress(merged, stratigraphy=make_log())


def test_a_file_without_the_judgment_says_so(tmp_path):
    path = write_judgments(tmp_path, JUDGMENTS.split("water_level:")[0])
    with pytest.raises(
        ht.HangtuError, match=r"judgments.yaml' has no water_level.*Add water_level:"
    ):
        ht.analysis.vertical_stress(from_project(path), stratigraphy=make_log())


def test_project_values_fill_in_with_a_warning(tmp_path):
    # Criterion 3.
    text = (
        JUDGMENTS.replace(
            "    Sand: {bulk_unit_weight: 19.5}\n",
            "",
        )
        .replace(
            "  values:",
            "  project: {bulk_unit_weight: 19.5, reason: median of all units}\n"
            "  values:",
        )
        .replace(
            "  by_hole:\n    BH01: {depth: 3.0, reason: standpipe reading}\n",
            "  project: {depth: 3.0, reason: highest reading}\n",
        )
    )
    path = write_judgments(tmp_path, text)
    with pytest.warns(UserWarning) as record:
        df = ht.analysis.vertical_stress(
            from_project(path, depths=(8.0,)),
            stratigraphy=make_log(),
            display_units="SI",
        )
    messages = [str(w.message) for w in record]
    assert (
        "unit_weight: the project value 19.5 kN/m3 is used for the geology unit "
        "'Sand' not listed (median of all units)." in messages
    )
    assert (
        "water_level: the project value 3 m is used for the hole 'BH01' not listed "
        "(highest reading)." in messages
    )
    assert df["total_vertical_stress"].iloc[0] == pytest.approx(154.0)
    recorded = df.attrs["judgments"]["unit_weight"]["values"]
    assert recorded["project"] == {
        "bulk_unit_weight": "19.5 kN/m3",
        "reason": "median of all units",
        "used_for": "Sand",
    }


def test_missing_keys_without_a_project_value_are_named(tmp_path):
    path = write_judgments(
        tmp_path,
        JUDGMENTS.replace("    Sand: {bulk_unit_weight: 19.5}\n", "").replace(
            "    Clay: {bulk_unit_weight: 19, saturated_unit_weight: 20}\n", ""
        ),
    )
    with pytest.raises(
        ht.HangtuError,
        match=r"The judgments file's unit_weight has no value for the geology units "
        r"'Clay', 'Sand'.*project: entry",
    ):
        ht.analysis.vertical_stress(
            from_project(path, depths=(8.0,)), stratigraphy=make_log()
        )


def test_entries_for_units_and_holes_not_in_the_stratigraphy_warn(tmp_path):
    text = (
        JUDGMENTS.replace(
            "    Sand: {bulk_unit_weight: 19.5}\n",
            "    Sand: {bulk_unit_weight: 19.5}\n    sand: {bulk_unit_weight: 19.5}\n",
        )
        + "    BH9: {depth: 1.0}\n"
    )
    path = write_judgments(tmp_path, text)
    with pytest.warns(UserWarning) as record:
        ht.analysis.vertical_stress(from_project(path), stratigraphy=make_log())
    messages = " ".join(str(w.message) for w in record)
    assert (
        "unit_weight has values for 'sand', which is not in the stratigraphy's "
        "geology_unit" in messages
    )
    assert (
        "water_level has values for 'BH9', which is not in the stratigraphy's loca_id"
        in messages
    )


def test_recorded_values_and_hash(tmp_path):
    # Criterion 6.
    path = write_judgments(tmp_path)
    df = quiet(from_project(path), stratigraphy=make_log(), display_units="SI")
    sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    assert df.attrs["judgments"] == {
        "unit_weight": {
            "source": str(path),
            "sha256": sha256,
            "by": "geology_unit",
            "values": {
                "Fill": {"bulk_unit_weight": "18 kN/m3", "reason": "median LDEN"},
                "Clay": {
                    "bulk_unit_weight": "19 kN/m3",
                    "saturated_unit_weight": "20 kN/m3",
                },
            },
        },
        "water_level": {
            "source": str(path),
            "sha256": sha256,
            "by": "loca_id",
            "values": {"BH01": {"depth": "3 m", "reason": "standpipe reading"}},
        },
    }


def test_a_file_in_us_units_converts(tmp_path):
    text = """\
unit_weight:
  units: {bulk_unit_weight: pcf}
  project: {bulk_unit_weight: 120, reason: typical}
water_level:
  units: {elevation: ft}
  by_hole:
    BH01: {elevation: 90}
"""
    path = write_judgments(tmp_path, text)
    df = make_tests([5.0], ground_level=[100 * FOOT])
    df.attrs["judgments_file"] = str(path)
    with pytest.warns(
        UserWarning, match=r"project value 120 pcf is used for every geology unit"
    ):
        result = ht.analysis.vertical_stress(
            df, stratigraphy=make_log(), display_units="SI"
        )
    assert result["total_vertical_stress"].iloc[0] == pytest.approx(
        5 * 120 * PCF, rel=1e-6
    )
    assert result["pore_pressure"].iloc[0] == pytest.approx(9.81 * (5 - 10 * FOOT))


def test_unit_weights_by_another_column(tmp_path):
    text = (
        JUDGMENTS.replace("by: geology_unit", "by: uscs_symbol")
        .replace("Fill:", "GC:")
        .replace("Clay:", "CL:")
        .replace("Sand:", "SP:")
    )
    path = write_judgments(tmp_path, text)
    log = make_log()
    log["uscs_symbol"] = ["GC", "CL", "SP"]
    df = quiet(from_project(path), stratigraphy=log, display_units="SI")
    assert df["total_vertical_stress"].iloc[0] == pytest.approx(95.0)
    assert df.attrs["judgments"]["unit_weight"]["by"] == "uscs_symbol"


def test_editing_the_file_changes_the_next_result_without_reopening(tmp_path):
    # Criterion 6, end to end: p.set_judgments, then edit the file.
    p = ht.Project.from_ags(
        DATA / "site_si.ags", db=tmp_path / "site.sqlite", display_units="SI"
    )
    p.set_geology_map(DATA / "strata.csv")
    text = """\
unit_weight:
  by: geology_unit
  units: {bulk_unit_weight: kN/m3}
  values:
    Fill: {bulk_unit_weight: 18}
    Alluvium: {bulk_unit_weight: 19}
    Terrace: {bulk_unit_weight: 20}
water_level:
  units: {depth: m}
  project: {depth: 2.0, reason: assumed}
"""
    path = write_judgments(tmp_path, text)
    p.set_judgments(path)
    spt = p.spt(holes="BH2")  # depths 2.3 and 5.3 m in Alluvium
    log = p.stratigraphy()
    with pytest.warns(UserWarning, match="project value 2 m"):
        first = ht.analysis.vertical_stress(spt, stratigraphy=log, display_units="SI")
    assert list(first["total_vertical_stress"]) == pytest.approx([19 * 2.3, 19 * 5.3])
    path.write_text(
        text.replace(
            "Alluvium: {bulk_unit_weight: 19}", "Alluvium: {bulk_unit_weight: 17}"
        )
    )
    with pytest.warns(UserWarning, match="project value 2 m"):
        second = ht.analysis.vertical_stress(spt, stratigraphy=log, display_units="SI")
    assert list(second["total_vertical_stress"]) == pytest.approx([17 * 2.3, 17 * 5.3])
    assert (
        second.attrs["judgments"]["unit_weight"]["sha256"]
        != first.attrs["judgments"]["unit_weight"]["sha256"]
    )


def test_the_log_error_gives_the_tolerance_in_the_log_units():
    log = make_log(tops=(0.0, 8.0, 20.0), bases=(6.0, 20.0, 33.0), unit="ft")
    with pytest.raises(
        ht.HangtuError, match=r"(?s)a gap from 6 ft to 8 ft.*more than 0\.033 ft"
    ):
        ht.analysis.vertical_stress(
            make_tests([25.0], unit="ft"),
            stratigraphy=log,
            unit_weight=UNIT_WEIGHT,
            water_level="3 ft",
        )
