"""compare(): Welch's t-test, inputs, groups and units (m15d-compare, AC 1, 9-13)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError

KPA_PER_PSF = 0.04788026


def _row(result):
    return result.to_frame().iloc[0]


def _frame(values, unit="kPa", **columns):
    frame = pd.DataFrame({"undrained_shear_strength": values, **columns})
    return ht.set_units(frame, {"undrained_shear_strength": unit})


def test_welch_reproduces_helsel_example_5_3(helsel):
    # AC 1: Helsel et al. (2020) Example 5.3, industrial first.
    row = _row(ht.stats.compare(*helsel, significance_level=0.05))
    assert row["difference"] == pytest.approx(0.028, rel=1e-9)
    assert row["welch_t_statistic"] == pytest.approx(0.029044, abs=5e-7)
    assert row["welch_degrees_of_freedom"] == pytest.approx(11.555, abs=5e-4)
    assert row["welch_p_value"] == pytest.approx(0.9773, abs=5e-5)
    assert row["difference_lower"] == pytest.approx(-2.081479, abs=5e-7)
    assert row["difference_upper"] == pytest.approx(2.137479, abs=5e-7)
    assert row["mean_1"] == pytest.approx(1.666)
    assert row["mean_2"] == pytest.approx(1.638)
    assert (row["group_1"], row["group_2"]) == ("first", "second")


def test_welch_on_logs_reproduces_helsel_example_5_4(helsel):
    # AC 1: the ratio of geometric means and its interval.
    result = ht.stats.compare(*helsel, significance_level=0.05, log=True)
    row = _row(result)
    assert "difference" not in row.index
    assert row["welch_t_statistic"] == pytest.approx(1.3578, abs=5e-5)
    assert row["welch_degrees_of_freedom"] == pytest.approx(14.684, abs=5e-4)
    assert row["welch_p_value"] == pytest.approx(0.195, abs=5e-4)
    assert row["ratio"] == pytest.approx(1.6168603, rel=1e-6)
    assert row["ratio_lower"] == pytest.approx(0.7594506, rel=1e-6)
    assert row["ratio_upper"] == pytest.approx(3.4422730, rel=1e-6)
    assert row["geometric_mean_1"] / row["geometric_mean_2"] == pytest.approx(
        row["ratio"]
    )
    assert "geometric_standard_deviation_1" in row.index


def test_log_with_a_value_at_or_below_zero_is_an_error(helsel):
    industrial, residential = helsel
    with pytest.raises(HangtuError, match=r"found 1 values .* at or below 0"):
        ht.stats.compare(
            industrial, [*residential, 0.0], significance_level=0.05, log=True
        )


def test_a_smaller_significance_level_widens_the_interval_only(helsel):
    # AC 9: an interval at α = 0.10 is narrower than at 0.05; p is unchanged.
    at_05 = _row(ht.stats.compare(*helsel, significance_level=0.05))
    at_10 = _row(ht.stats.compare(*helsel, significance_level=0.10))
    assert at_10["difference_upper"] - at_10["difference_lower"] < (
        at_05["difference_upper"] - at_05["difference_lower"]
    )
    assert at_10["welch_p_value"] == at_05["welch_p_value"]
    assert at_10["confidence_level"] == pytest.approx(0.90)


def test_the_result_records_the_significance_level_and_its_source(helsel, tmp_path):
    # AC 9: the result records 0.05, its source, and confidence_level 0.95.
    path = tmp_path / "judgments.yaml"
    path.write_text(
        "significance_level:\n"
        '  project: {significance_level: 0.05, reason: "the usual convention"}\n',
        encoding="utf-8",
    )
    result = ht.stats.compare(*helsel, judgments=path)
    assert result.significance_level == 0.05
    assert result.confidence_level == pytest.approx(0.95)
    assert result.significance_level_source == str(path)
    assert result.judgments["significance_level"]["reason"] == "the usual convention"
    assert "Significance level 0.05 (judgments.yaml)" in str(result)


def test_no_significance_level_is_an_error(helsel):
    with pytest.raises(HangtuError, match="compare\\(\\) tests at the significance"):
        ht.stats.compare(*helsel)


def test_the_three_input_forms_agree(helsel):
    # AC 10: compare(a, b), two frames, and by= give the same numbers.
    industrial, residential = helsel
    arrays = ht.stats.compare(
        industrial, residential, units="kPa", significance_level=0.05
    )
    frames = ht.stats.compare(
        _frame(industrial),
        _frame(residential),
        value="undrained_shear_strength",
        significance_level=0.05,
    )
    grouped = ht.stats.compare(
        _frame(
            industrial + residential,
            geology_unit=["Industrial"] * 10 + ["Residential"] * 10,
        ),
        value="undrained_shear_strength",
        by="geology_unit",
        significance_level=0.05,
    )
    numbers = [
        name
        for name in arrays.to_frame().columns
        if name not in ("group_1", "group_2", "brunner_munzel_method")
    ]
    for result in (frames, grouped):
        pd.testing.assert_series_equal(
            _row(result)[numbers], _row(arrays)[numbers], check_names=False
        )
    assert (_row(grouped)["group_1"], _row(grouped)["group_2"]) == (
        "Industrial",
        "Residential",
    )
    assert frames.value == grouped.value == "undrained_shear_strength"


def test_named_series_name_the_groups(helsel):
    industrial, residential = helsel
    result = ht.stats.compare(
        pd.Series(industrial, name="industrial"),
        pd.Series(residential, name="residential"),
        units="kPa",
        significance_level=0.05,
    )
    assert [group["label"] for group in result.groups] == ["industrial", "residential"]
    assert "Difference in means, industrial - residential" in str(result)


def test_by_with_three_groups_and_no_groups_is_an_error(three_groups):
    # AC 10
    with pytest.raises(HangtuError) as error:
        ht.stats.compare(
            three_groups,
            value="undrained_shear_strength",
            by="geology_unit",
            significance_level=0.05,
        )
    message = str(error.value)
    assert "by='geology_unit' gives 3: 'A', 'B', 'C'" in message
    assert "groups=" in message
    assert "compare_groups()" in message


def test_groups_chooses_and_orders_two(three_groups):
    # AC 10: groups=("C", "A") reverses the sign of the difference.
    def run(groups):
        with pytest.warns(UserWarning, match=r"fewer than 5 .* C \(4\)"):
            return _row(
                ht.stats.compare(
                    three_groups,
                    value="undrained_shear_strength",
                    by="geology_unit",
                    groups=groups,
                    significance_level=0.05,
                )
            )

    forward, backward = run(("A", "C")), run(("C", "A"))
    assert (backward["group_1"], backward["group_2"]) == ("C", "A")
    assert backward["difference"] == pytest.approx(-forward["difference"])
    assert backward["difference_lower"] == pytest.approx(-forward["difference_upper"])
    assert backward["welch_p_value"] == pytest.approx(forward["welch_p_value"])
    # A: mean 17.4; C: mean 17.
    assert forward["difference"] == pytest.approx(0.4)


@pytest.mark.parametrize(
    ("groups", "message"),
    [
        (("A", "D"), r"names 'D', which isn't a group of by='geology_unit'.*'A', 'B'"),
        (("A", "A"), "names 'A' twice"),
        ("AB", "takes two keys"),
        (("A", "B", "C"), "takes two keys"),
    ],
)
def test_groups_errors(three_groups, groups, message):
    with pytest.raises(HangtuError, match=message):
        ht.stats.compare(
            three_groups,
            value="undrained_shear_strength",
            by="geology_unit",
            groups=groups,
            significance_level=0.05,
        )


def test_groups_with_several_by_columns_takes_tuples(three_groups):
    three_groups["hole"] = "BH01"
    result = ht.stats.compare(
        three_groups,
        value="undrained_shear_strength",
        by=["geology_unit", "hole"],
        groups=[("B", "BH01"), ("A", "BH01")],
        significance_level=0.05,
    )
    assert _row(result)["group_1"] == "B, BH01"


def test_two_frames_in_different_units_are_an_error(helsel):
    # AC 10
    industrial, residential = helsel
    with pytest.raises(
        HangtuError, match="can't compare values in kPa with values in psf"
    ):
        ht.stats.compare(
            _frame(industrial),
            _frame(residential, unit="psf"),
            value="undrained_shear_strength",
            significance_level=0.05,
        )


def test_display_units_bring_two_frames_to_one_unit(helsel):
    industrial, residential = helsel
    result = ht.stats.compare(
        _frame(industrial),
        _frame(residential, unit="psf"),
        value="undrained_shear_strength",
        display_units="SI",
        significance_level=0.05,
    )
    assert result.unit == "kPa"
    assert _row(result)["mean_2"] == pytest.approx(1.638 * KPA_PER_PSF, rel=1e-6)


def test_units_scale_the_difference_and_leave_the_tests(helsel):
    # AC 13: psf in psf; SI in kPa; the difference scales, the tests don't.
    industrial, residential = helsel
    frames = (_frame(industrial, unit="psf"), _frame(residential, unit="psf"))
    psf = ht.stats.compare(
        *frames, value="undrained_shear_strength", significance_level=0.05
    )
    kpa = ht.stats.compare(
        *frames,
        value="undrained_shear_strength",
        display_units="SI",
        significance_level=0.05,
    )
    assert (psf.unit, kpa.unit) == ("psf", "kPa")
    for name in ("difference", "difference_lower", "difference_upper", "mean_1"):
        assert _row(kpa)[name] == pytest.approx(_row(psf)[name] * KPA_PER_PSF, rel=1e-6)
    for name in ("welch_t_statistic", "welch_degrees_of_freedom", "welch_p_value"):
        assert _row(kpa)[name] == pytest.approx(_row(psf)[name], rel=1e-9)
    assert kpa.to_frame().attrs["units"]["difference"] == "kPa"


def test_a_source_mix_within_a_group_is_an_error():
    # AC 10: a two-source group is the source error.
    first = _frame(
        [10.0, 11, 12, 13, 14, 15],
        correlation_name=["undrained_shear_strength_stroud_1974"] * 3
        + ["undrained_shear_strength_terzaghi_peck_1967"] * 3,
    )
    with pytest.raises(HangtuError, match="can't pool rows from different sources"):
        ht.stats.compare(
            first,
            _frame([20.0, 21, 22, 23, 24]),
            value="undrained_shear_strength",
            significance_level=0.05,
        )


def test_one_source_per_group_is_not_a_mix():
    # AC 10: two groups of one source each are compared.
    df = _frame(
        [10.0, 11, 12, 13, 14, 20, 21, 22, 23, 24],
        correlation_name=["undrained_shear_strength_stroud_1974"] * 5
        + ["undrained_shear_strength_terzaghi_peck_1967"] * 5,
    )
    result = ht.stats.compare(
        df,
        value="undrained_shear_strength",
        by="correlation_name",
        significance_level=0.05,
    )
    assert _row(result)["difference"] == pytest.approx(-10)
    first = df.iloc[:5]
    second = df.iloc[5:]
    two = ht.stats.compare(
        first, second, value="undrained_shear_strength", significance_level=0.05
    )
    assert _row(two)["difference"] == pytest.approx(-10)


def test_a_group_of_one_is_an_error():
    # AC 12
    with pytest.raises(HangtuError, match=r"at least 2 values .* 'second' has 1"):
        ht.stats.compare([1.0, 2, 3, 4, 5], [3.0], significance_level=0.05)


def test_small_groups_warn_once_naming_them():
    # AC 12: groups of 3 and 4 warn once.
    with pytest.warns(UserWarning) as record:
        ht.stats.compare([1.0, 2, 3], [3.0, 4, 5, 7], significance_level=0.05)
    messages = [str(w.message) for w in record]
    assert len(messages) == 1
    assert (
        "fewer than 5 values of 'the values' in: first (3), second (4)" in messages[0]
    )


def test_no_spread_in_either_group_leaves_welch_blank():
    result = ht.stats.compare(
        [2.0, 2, 2, 2, 2], [3.0, 3, 3, 3, 3], significance_level=0.05
    )
    assert np.isnan(_row(result)["welch_p_value"])
    assert any("no spread" in note for note in result.notes)


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (
            lambda df: ht.stats.compare(df, value="undrained_shear_strength"),
            "needs two groups",
        ),
        (
            lambda df: ht.stats.compare(
                df, df, value="undrained_shear_strength", by="geology_unit"
            ),
            "takes by= with one DataFrame",
        ),
        (
            lambda df: ht.stats.compare(
                df, [1.0, 2.0], value="undrained_shear_strength"
            ),
            "not one of each",
        ),
        (
            lambda df: ht.stats.compare([1.0, 2], [3.0, 4], groups=("A", "B")),
            "takes groups= with by=",
        ),
    ],
)
def test_input_errors(three_groups, call, message):
    with pytest.raises(HangtuError, match=message):
        call(three_groups)
