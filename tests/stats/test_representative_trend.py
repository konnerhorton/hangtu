"""representative() with a trend (docs/work/m18b-representative-values.md).

G5 is the spec's: a least-squares line through five values, with the JRC's
confidence and prediction bands (Equations 39-43, pp. 83-85), hand-calculated
here with NumPy and SciPy from the formulas, not from the implementation;
1e-6 relative, and the spec's printed values to their rounding.
"""

import json
import math

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError, UnitsError
from hangtu.stats._result import trend_at

#: G5: depth (m) and undrained shear strength (kPa).
DEPTH = [2.0, 4.0, 6.0, 8.0, 10.0]
STRENGTH = [20.0, 26.0, 29.0, 37.0, 40.0]
AT = [2.0, 6.0, 10.0]
REL = 1e-6


def profile(depth=DEPTH, strength=STRENGTH, **columns):
    frame = pd.DataFrame(
        {"depth": depth, "undrained_shear_strength": strength, **columns}
    )
    return ht.set_units(frame, {"depth": "m", "undrained_shear_strength": "kPa"})


def representative(data, **kwargs):
    kwargs.setdefault("value", "undrained_shear_strength")
    kwargs.setdefault("side", "low")
    kwargs.setdefault("distribution", "normal")
    kwargs.setdefault("trend", "depth")
    return ht.stats.representative(data, **kwargs)


def characteristic(data, estimate, **kwargs):
    return representative(data, method="characteristic", estimate=estimate, **kwargs)


def line(result, group=0):
    return result.groups[group]["line"]


def hand(z, x, at, *, band=None, multiple):
    """The JRC's line and band at ``at``, from the formulas (Equations 39-43)."""
    z, x, at = (np.asarray(v, dtype=float) for v in (z, x, at))
    n = len(z)
    slope, intercept = np.polyfit(z, x, 1)
    deviation = math.sqrt(np.sum((x - intercept - slope * z) ** 2) / (n - 2))
    fitted = intercept + slope * at
    if band is None:
        return fitted + multiple * deviation
    width = 1 / n + (at - z.mean()) ** 2 / np.sum((z - z.mean()) ** 2)
    if band == "prediction":
        width = width + 1
    return fitted + multiple * deviation * np.sqrt(width)


# --- Criterion 7: G5, at three depths --------------------------------------------


def test_g5_the_line_and_its_statistics():
    table = characteristic(profile(), "mean").to_frame()
    row = table.iloc[0]
    assert row["line_slope"] == pytest.approx(2.55, rel=REL)
    assert row["line_intercept"] == pytest.approx(15.1, rel=REL)
    assert row["residual_standard_deviation"] == pytest.approx(1.30384, abs=5e-6)
    assert row["quantile_factor"] == pytest.approx(2.35336, abs=5e-6)
    assert row["quantile_factor"] == pytest.approx(stats.t.ppf(0.95, 3), rel=REL)
    assert (row["depth_top"], row["depth_base"], row["count"]) == (2.0, 10.0, 5)


@pytest.mark.parametrize(
    ("estimate", "band", "printed"),
    [
        ("mean", "confidence", [17.8232, 29.0278, 38.2232]),
        ("fractile", "prediction", [16.3187, 27.0387, 36.7187]),
    ],
)
def test_g5_the_characteristic_mean_and_fractile_on_the_low_side(
    estimate, band, printed
):
    result = characteristic(profile(), estimate)
    expected = hand(DEPTH, STRENGTH, AT, band=band, multiple=-stats.t.ppf(0.95, 3))
    got = trend_at(line(result), AT)
    assert got == pytest.approx(expected, rel=REL)
    assert got == pytest.approx(printed, abs=5e-5)
    row = result.to_frame().iloc[0]
    assert (row["value_top"], row["value_base"]) == pytest.approx(
        (expected[0], expected[-1]), rel=REL
    )


def test_g5_one_standard_deviation_below_the_line():
    result = representative(
        profile(), method="standard_deviations", standard_deviations=1
    )
    got = trend_at(line(result), AT)
    assert got == pytest.approx(hand(DEPTH, STRENGTH, AT, multiple=-1), rel=REL)
    assert got == pytest.approx([18.8962, 29.0962, 39.2962], abs=5e-5)
    assert "quantile_factor" not in result.to_frame().columns


def test_the_high_side_mirrors_the_low_about_the_line():
    low = trend_at(line(characteristic(profile(), "fractile")), AT)
    high_result = characteristic(profile(), "fractile", side="high")
    high = trend_at(line(high_result), AT)
    fitted = trend_at(line(high_result), AT, mean=True)
    assert high == pytest.approx(2 * fitted - low, rel=REL)
    assert fitted == pytest.approx(15.1 + 2.55 * np.array(AT), rel=REL)


def test_the_percentile_is_the_line_plus_z_p_residual_deviations():
    result = representative(profile(), method="percentile", percentile=10)
    z_p = stats.norm.ppf(0.10)
    assert trend_at(line(result), AT) == pytest.approx(
        hand(DEPTH, STRENGTH, AT, multiple=z_p), rel=REL
    )
    assert result.to_frame().iloc[0]["quantile_factor"] == pytest.approx(z_p)


def test_a_lognormal_trend_is_a_line_through_ln_x_transformed_back():
    result = characteristic(profile(), "mean", distribution="lognormal")
    expected = np.exp(
        hand(
            DEPTH,
            np.log(STRENGTH),
            AT,
            band="confidence",
            multiple=-stats.t.ppf(0.95, 3),
        )
    )
    assert trend_at(line(result), AT) == pytest.approx(expected, rel=REL)
    assert any("median of x" in note for note in result.notes)
    assert "line_intercept" not in result.to_frame().attrs["units"]


def test_elevation_gives_the_same_line_mirrored():
    frame = profile()
    frame["elevation"] = 100.0 - frame["depth"]
    frame = ht.set_units(frame, {"elevation": "m"})
    by_depth = characteristic(frame, "fractile")
    by_elevation = characteristic(frame, "fractile", trend="elevation")
    elevations = [100.0 - z for z in AT]
    assert trend_at(line(by_elevation), elevations) == pytest.approx(
        trend_at(line(by_depth), AT), rel=REL
    )
    row = by_elevation.to_frame().iloc[0]
    assert (row["elevation_top"], row["elevation_base"]) == (98.0, 90.0)
    assert row["line_slope"] == pytest.approx(-2.55, rel=REL)
    assert by_elevation.to_frame().attrs["units"]["elevation_top"] == "m"


# --- Criterion 7: what a trend can't take, and too few values --------------------


def test_a_group_with_two_values_has_no_line_with_the_reason():
    frame = profile(
        depth=[*DEPTH, 3.0, 5.0],
        strength=[*STRENGTH, 22.0, 27.0],
        geology_unit=["Clay"] * 5 + ["Sand"] * 2,
    )
    result = characteristic(frame, "mean", by="geology_unit")
    sand = result.groups[1]
    assert "fewer than 3 values with a depth (2)" in sand["reason"]
    assert "line" not in sand
    assert any("Sand: no value, fewer than 3" in note for note in result.notes)
    assert math.isnan(result.to_frame().iloc[1]["value_top"])


def test_values_all_at_one_depth_have_no_line():
    result = characteristic(profile(depth=[5.0] * 5), "mean")
    assert "all points at the same depth" in result.groups[0]["reason"]


def test_a_trend_needs_its_column():
    frame = profile().drop(columns="depth")
    with pytest.raises(ColumnError, match="trend='depth' needs the column 'depth'"):
        characteristic(frame, "mean")
    with pytest.raises(ColumnError, match="needs the column 'elevation'"):
        characteristic(profile(), "mean", trend="elevation")


def test_a_trend_needs_the_unit_of_its_depth():
    frame = pd.DataFrame({"depth": DEPTH, "undrained_shear_strength": STRENGTH})
    frame = ht.set_units(frame, {"undrained_shear_strength": "kPa"})
    with pytest.raises(UnitsError, match="'depth' has no units"):
        characteristic(frame, "mean")
    result = characteristic(
        frame, "mean", units={"undrained_shear_strength": "kPa", "depth": "m"}
    )
    assert result.vertical_unit == "m"


def test_display_units_convert_the_depth_too():
    result = characteristic(profile(), "mean", display_units="US")
    row = result.to_frame().iloc[0]
    assert row["depth_base"] == pytest.approx(10.0 / 0.3048, rel=REL)
    assert result.vertical_unit == "ft"
    metric = trend_at(line(characteristic(profile(), "mean")), [10.0])
    us = trend_at(line(result), [10.0 / 0.3048])
    assert us == pytest.approx(metric * 1000 / 47.880258980, rel=1e-6)


@pytest.mark.parametrize(
    "given",
    [
        {"coefficient_of_variation": 0.2},
        {"estimate": "intermediate", "sensitivity_index": 0.5},
    ],
)
def test_a_trend_with_an_assumed_v_x_or_type_c_is_an_error(given):
    given = {"estimate": "mean", **given}
    with pytest.raises(HangtuError, match="trend"):
        representative(profile(), method="characteristic", **given)


# --- Criterion 6, trend: censored values left out, counted and noted -------------


def test_refusals_are_left_out_of_the_trend_counted_and_noted():
    frame = pd.DataFrame(
        {
            "geology_unit": ["Terrace"] * 7,
            "depth": [*DEPTH, 11.0, 12.0],
            "spt_n60": [*STRENGTH, 66.7, 66.7],
            "spt_refusal": [False] * 5 + [True] * 2,
        }
    )
    frame = ht.set_units(frame, {"depth": "m"})
    with pytest.warns(UserWarning, match="left 2 censored values .* out of the trend"):
        result = representative(
            frame,
            value="spt_n60",
            by="geology_unit",
            method="characteristic",
            estimate="mean",
        )
    counts = result.groups[0]["counts"]
    assert (counts["count"], counts["count_censored"]) == (5, 2)
    assert trend_at(line(result), AT) == pytest.approx(
        hand(DEPTH, STRENGTH, AT, band="confidence", multiple=-stats.t.ppf(0.95, 3)),
        rel=REL,
    )
    assert any(
        "Terrace: 2 censored values left out of the trend" in note
        and "a low-side line is more cautious" in note
        for note in result.notes
    )


def test_values_with_no_depth_are_left_out_and_the_counts_add_up():
    frame = profile(
        depth=[*DEPTH, None, 7.0, 9.0],
        strength=[*STRENGTH, 30.0, 12.0, None],
        qualifier=[None] * 6 + ["<", None],
    )
    with pytest.warns(UserWarning, match=r"1 values with no depth \(count_blank_depth"):
        result = characteristic(frame, "mean")
    table = result.to_frame()
    assert table.loc[0, "count_blank_depth"] == 1
    assert table.loc[0, "count_censored"] == 1
    added = table.loc[
        0, ["count", "count_censored", "count_blank_depth", "count_blank"]
    ].sum()
    assert added == len(frame)
    assert any("higher than the data" in note for note in result.notes)


# --- Warnings and the record ------------------------------------------------------


def test_a_normal_trend_at_or_below_zero_warns():
    with pytest.warns(UserWarning, match="at or below 0 from a normal"):
        representative(profile(), method="standard_deviations", standard_deviations=20)


def test_the_assumptions_are_noted_and_the_record_is_json():
    result = characteristic(profile(), "fractile")
    assert any("look at the residuals" in note for note in result.notes)
    record = result.to_dict()
    json.dumps(record)
    assert record["trend"] == "depth"
    assert record["vertical_unit"] == "m"
    assert len(record["groups"][0]["line"]["residuals"]) == 5
    assert "a line with depth" in str(result)
    units = result.to_frame().attrs["units"]
    assert units["depth_top"] == "m"
    assert units["value_base"] == units["line_intercept"] == "kPa"
    assert "line_slope" not in units
