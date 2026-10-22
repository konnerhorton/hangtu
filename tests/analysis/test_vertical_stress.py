"""ht.analysis.vertical_stress() (docs/work/m13a-judgments.md, Decisions 6 and 7)."""

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
