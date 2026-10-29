"""ht.stats.describe(): statistics, units and inputs (docs/work/m15a-describe.md)."""

import math

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError, UnitsError

STRENGTH = [10, 12, 15, 20, 23]
KPA_PER_PSF = 0.04788026


def _strength(values=STRENGTH, unit="kPa", **columns):
    df = pd.DataFrame({"undrained_shear_strength": values, **columns})
    return ht.set_units(df, {"undrained_shear_strength": unit})


def _row(result, index=0):
    return result.to_frame().iloc[index]


def test_statistics_of_five_values():
    # AC 1: mean 16, std sqrt(29.5), P25 and P75 by linear interpolation.
    row = _row(ht.stats.describe(_strength(), value="undrained_shear_strength"))
    assert row["count"] == 5
    assert row["mean"] == pytest.approx(16, rel=1e-9)
    assert row["standard_deviation"] == pytest.approx(math.sqrt(29.5), rel=1e-9)
    assert row["standard_deviation"] == pytest.approx(5.4313902, rel=1e-7)
    assert row["coefficient_of_variation"] == pytest.approx(0.33946189, rel=1e-7)
    assert [row["minimum"], row["median"], row["maximum"]] == [10, 15, 23]
    assert [row["percentile_25"], row["percentile_75"]] == [12, 20]
    assert np.isnan(row["percentile_5"]) and np.isnan(row["percentile_95"])


def test_the_summary_says_why_a_percentile_is_missing():
    result = ht.stats.describe(_strength(), value="undrained_shear_strength")
    assert "P5/P95 need 20 values: All." in result.notes


def test_p5_and_p95_from_twenty_values():
    # AC 2: (n - 1) p / 100 + 1 is the position of P_p in the sorted values.
    row = _row(ht.stats.describe(np.arange(1, 21)))
    assert row["mean"] == pytest.approx(10.5)
    assert row["standard_deviation"] == pytest.approx(math.sqrt(35), rel=1e-9)
    expected = {
        "percentile_5": 1.95,
        "percentile_25": 5.75,
        "median": 10.5,
        "percentile_75": 15.25,
        "percentile_95": 19.05,
    }
    for name, value in expected.items():
        assert row[name] == pytest.approx(value, rel=1e-9), name


def test_p5_and_p95_are_missing_from_nineteen_values():
    row = _row(ht.stats.describe(np.arange(1, 20)))
    assert np.isnan(row["percentile_5"]) and np.isnan(row["percentile_95"])
    assert not np.isnan(row["percentile_25"])


def test_chosen_percentiles():
    frame = ht.stats.describe(np.arange(1, 21), percentiles=(10, 90)).to_frame()
    assert [c for c in frame.columns if c.startswith("percentile_")] == [
        "percentile_10",
        "percentile_90",
    ]
    assert frame.loc[0, "percentile_10"] == pytest.approx(2.9, rel=1e-9)
    assert frame.loc[0, "percentile_90"] == pytest.approx(18.1, rel=1e-9)


@pytest.mark.parametrize(("n", "reported"), [(9, False), (10, True)])
def test_p10_needs_ten_values(n, reported):
    row = _row(ht.stats.describe(np.arange(1, n + 1), percentiles=(10, 90)))
    assert np.isnan(row["percentile_10"]) != reported
    assert np.isnan(row["percentile_90"]) != reported


@pytest.mark.parametrize(("n", "reported"), [(39, False), (40, True)])
def test_p2_5_needs_forty_values(n, reported):
    row = _row(ht.stats.describe(np.arange(1, n + 1), percentiles=(2.5,)))
    assert np.isnan(row["percentile_2_5"]) != reported


@pytest.mark.parametrize("percentiles", [(90, 10), (0, 50), (25, 25), (), ("a",)])
def test_percentiles_must_be_ascending_between_0_and_100(percentiles):
    with pytest.raises(HangtuError, match="ascending"):
        ht.stats.describe(STRENGTH, percentiles=percentiles)


def test_fifty_adds_a_percentile_equal_to_the_median():
    row = _row(ht.stats.describe(STRENGTH, percentiles=(50,)))
    assert row["percentile_50"] == row["median"] == 15


def test_one_value():
    # AC 3
    with pytest.warns(UserWarning, match=r"fewer than 3 values .*All \(1\)"):
        row = _row(ht.stats.describe([7.5]))
    assert row["mean"] == row["median"] == 7.5
    assert np.isnan(row["standard_deviation"])
    assert np.isnan(row["coefficient_of_variation"])


def test_small_groups_warn_once_naming_them():
    df = _strength(
        [10, 12, 15, 20, 23, 30, np.nan],
        geology_unit=["A", "A", "A", "B", "B", "C", "D"],
    )
    with pytest.warns(UserWarning) as record:
        frame = ht.stats.describe(
            df, value="undrained_shear_strength", by="geology_unit"
        ).to_frame()
    assert len(record) == 1
    assert "B (2), C (1), D (0)" in str(record[0].message)
    assert frame.set_index("geology_unit")["count"].to_dict() == {
        "A": 3,
        "B": 2,
        "C": 1,
        "D": 0,
    }
    assert frame.set_index("geology_unit").loc["D", "count_blank"] == 1


@pytest.mark.parametrize("column", ["elevation"])
def test_no_cov_on_an_interval_scale(column):
    # AC 4
    df = ht.set_units(pd.DataFrame({column: [10.0, 12.0, 15.0]}), {column: "m"})
    result = ht.stats.describe(df, value=column)
    assert np.isnan(_row(result)["coefficient_of_variation"])
    assert any("interval scale" in note for note in result.notes)


def test_cov_needs_a_mean_above_zero():
    df = ht.set_units(pd.DataFrame({"undrained_shear_strength": [-1, 0, -2]}), {})
    result = ht.stats.describe(df, value="undrained_shear_strength", units="kPa")
    assert np.isnan(_row(result)["coefficient_of_variation"])
    assert any("mean above 0" in note for note in result.notes)


def test_cov_on_an_unregistered_column_is_reported_with_a_note():
    result = ht.stats.describe([1.0, 2.0, 3.0])
    assert _row(result)["coefficient_of_variation"] == pytest.approx(0.5)
    assert any("scale is unknown" in note for note in result.notes)


def test_log_scale():
    # AC 5: ln 1, ln 10, ln 100 have mean ln 10 and standard deviation ln 10.
    df = ht.set_units(
        pd.DataFrame({"shear_wave_velocity": [1, 10, 100, 0, -1]}),
        {"shear_wave_velocity": "m/s"},
    )
    with pytest.warns(UserWarning, match="left out 2 values") as record:
        result = ht.stats.describe(df, value="shear_wave_velocity", log=True)
    assert len(record) == 1
    frame = result.to_frame()
    row = frame.iloc[0]
    assert row["geometric_mean"] == pytest.approx(10, rel=1e-9)
    assert row["geometric_standard_deviation"] == pytest.approx(10, rel=1e-9)
    assert row["median"] == 10
    assert row["count_not_positive"] == 2
    assert {"mean", "standard_deviation", "coefficient_of_variation"}.isdisjoint(
        frame.columns
    )
    assert "geometric_standard_deviation" not in frame.attrs["units"]


def test_blanks_and_text_are_counted():
    df = _strength([10, 12, "NP", "refusal", "dry", None, " ", 15, 20, 23])
    with pytest.warns(UserWarning, match=r"'dry' \(1\)") as record:
        result = ht.stats.describe(df, value="undrained_shear_strength")
    assert len(record) == 1
    row = _row(result)
    assert row["count"] == 5
    assert row["mean"] == pytest.approx(16)
    assert row["count_non_plastic"] == 1
    assert row["count_text"] == 2
    assert row["count_blank"] == 2
    assert result.groups[0]["text"] == {"refusal": 1, "dry": 1}


def test_counts_add_up_to_the_rows():
    # AC 12, for blanks and text
    df = _strength(
        [10, "NP", "refusal", None, 15, 20, 23, "x", 8],
        geology_unit=["A", "A", "B", "B", None, "A", "B", "A", "B"],
    )
    with pytest.warns(UserWarning):
        result = ht.stats.describe(
            df, value="undrained_shear_strength", by="geology_unit"
        )
    frame = result.to_frame()
    counts = [c for c in frame.columns if c.startswith("count")]
    assert frame[counts].sum(axis=1).tolist() == [4, 4, 1]


def test_groups_by_name_with_blank_last():
    df = _strength(
        [10, 12, 15, 20, 23, 30, 31, 32, 33],
        geology_unit=["B", "A", None, "A", "B", "", "A", "B", "A"],
    )
    with pytest.warns(UserWarning, match="fewer than 3"):
        frame = ht.stats.describe(
            df, value="undrained_shear_strength", by="geology_unit"
        ).to_frame()
    assert frame["geology_unit"].tolist() == ["A", "B", "(blank)"]
    assert frame["count"].tolist() == [4, 3, 2]


def test_groups_follow_a_categorical_order():
    units = pd.Categorical(["Till", "Alluvium", "Till"], ["Till", "Alluvium"])
    df = _strength([10, 12, 15], geology_unit=units)
    with pytest.warns(UserWarning, match="fewer than 3"):
        frame = ht.stats.describe(
            df, value="undrained_shear_strength", by="geology_unit"
        ).to_frame()
    assert frame["geology_unit"].tolist() == ["Till", "Alluvium"]


def test_groups_by_several_columns():
    df = _strength(
        [10, 12, 15, 20, 23, 30],
        geology_unit=["A", "A", "B", "B", "A", "A"],
        test_type=["UU", "vane", "UU", "UU", "UU", "UU"],
    )
    with pytest.warns(UserWarning, match="fewer than 3"):
        frame = ht.stats.describe(
            df, value="undrained_shear_strength", by=["geology_unit", "test_type"]
        ).to_frame()
    assert frame[["geology_unit", "test_type", "count"]].values.tolist() == [
        ["A", "UU", 3],
        ["A", "vane", 1],
        ["B", "UU", 2],
    ]


def test_units_follow_the_frame():
    # AC 13
    result = ht.stats.describe(_strength(unit="psf"), value="undrained_shear_strength")
    assert result.unit == "psf"
    assert _row(result)["mean"] == pytest.approx(16)


def test_display_units_convert_before_the_statistics():
    result = ht.stats.describe(
        _strength(unit="psf"), value="undrained_shear_strength", display_units="SI"
    )
    row = _row(result)
    assert result.unit == "kPa"
    assert row["mean"] == pytest.approx(16 * KPA_PER_PSF, rel=1e-6)
    assert row["percentile_75"] == pytest.approx(20 * KPA_PER_PSF, rel=1e-6)
    assert row["coefficient_of_variation"] == pytest.approx(0.33946189, rel=1e-7)


def test_display_units_never_come_from_the_settings():
    ht.settings.display_units = "SI"
    result = ht.stats.describe(_strength(unit="psf"), value="undrained_shear_strength")
    assert result.unit == "psf"


def test_units_argument_wins():
    df = pd.DataFrame({"undrained_shear_strength": STRENGTH})
    for units in ("kPa", {"undrained_shear_strength": "kPa"}):
        result = ht.stats.describe(df, value="undrained_shear_strength", units=units)
        assert result.unit == "kPa"


def test_a_column_with_no_unit_raises_naming_it():
    df = pd.DataFrame({"undrained_shear_strength": STRENGTH})
    with pytest.raises(UnitsError, match="'undrained_shear_strength' has no units"):
        ht.stats.describe(df, value="undrained_shear_strength")


def test_counts_and_percentages_need_no_unit():
    df = pd.DataFrame({"spt_n": [10, 20, 30], "water_content": [20, 25, 30]})
    assert ht.stats.describe(df, value="spt_n").unit is None
    assert ht.stats.describe(df, value="water_content").unit == "%"


def test_a_list_without_units_says_so():
    result = ht.stats.describe(STRENGTH)
    assert result.unit is None
    assert "(units not given)" in result.notes
    assert ht.stats.describe(STRENGTH, units="kPa").unit == "kPa"


def test_an_unregistered_column_cant_be_converted():
    with pytest.raises(HangtuError, match="isn't a registered column"):
        ht.stats.describe(STRENGTH, units="kPa", display_units="SI")


def test_display_units_must_be_us_or_si():
    with pytest.raises(HangtuError, match='"US", "SI" or None'):
        ht.stats.describe(
            _strength(), value="undrained_shear_strength", display_units="x"
        )


def test_a_series_and_an_array_give_the_same_numbers():
    # AC 15
    expected = _row(
        ht.stats.describe(_strength(), value="undrained_shear_strength")
    ).drop("count_blank")
    series = _strength()["undrained_shear_strength"]
    series.attrs = {"units": {"undrained_shear_strength": "kPa"}}
    for data in (series, np.array(STRENGTH), STRENGTH, pd.Series(STRENGTH)):
        row = _row(ht.stats.describe(data)).drop("count_blank")
        pd.testing.assert_series_equal(row, expected, check_names=False)


def test_a_named_series_is_its_column():
    series = pd.Series(STRENGTH, name="undrained_shear_strength")
    with pytest.raises(UnitsError, match="has no units"):
        ht.stats.describe(series)
    assert ht.stats.describe(series, units="kPa").value == "undrained_shear_strength"


def test_value_with_a_series_is_an_error():
    with pytest.raises(HangtuError, match="its own value"):
        ht.stats.describe(pd.Series(STRENGTH), value="x")


@pytest.mark.parametrize("argument", [{"by": "geology_unit"}, {"value": "x"}])
def test_by_and_value_need_a_dataframe(argument):
    with pytest.raises(HangtuError, match="only with a DataFrame"):
        ht.stats.describe(STRENGTH, **argument)


def test_a_dataframe_needs_value():
    with pytest.raises(HangtuError, match="needs value="):
        ht.stats.describe(_strength())


def test_a_missing_column_lists_the_available_ones():
    with pytest.raises(ColumnError, match="Available columns: undrained_shear"):
        ht.stats.describe(_strength(), value="plasticity_index")
    with pytest.raises(ColumnError, match="'geology_unit'"):
        ht.stats.describe(
            _strength(), value="undrained_shear_strength", by="geology_unit"
        )


def test_a_bool_column_is_an_error():
    df = pd.DataFrame({"spt_refusal": [True, False], "flag": [True, True]})
    for column in ("spt_refusal", "flag"):
        with pytest.raises(ColumnError, match="True or False"):
            ht.stats.describe(df, value=column)


def test_a_text_column_is_an_error():
    df = pd.DataFrame({"geology_unit": ["A", "B"], "remarks_x": ["wet", "dry"]})
    for column in ("geology_unit", "remarks_x"):
        with pytest.raises(ColumnError, match="no numbers"):
            ht.stats.describe(df, value=column)


def test_a_value_cant_group_itself():
    with pytest.raises(HangtuError, match="by itself"):
        ht.stats.describe(
            _strength(), value="undrained_shear_strength", by="undrained_shear_strength"
        )


def test_the_input_is_unchanged():
    df = _strength(geology_unit=["A"] * 5)
    before = df.copy()
    ht.stats.describe(df, value="undrained_shear_strength", by="geology_unit")
    pd.testing.assert_frame_equal(df, before)
