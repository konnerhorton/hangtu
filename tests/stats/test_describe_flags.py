"""describe(): refusals, qualifiers, NP, assumed values and bands (m15a, D3-6)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.analysis import correlations

#: Counts of rows left out; with ``count`` they add up to the group's rows.
LEFT_OUT = ["count_non_plastic", "count_range", "count_text", "count_blank"]


def _adds_up(result, rows, *, assumed_left_out=True):
    left_out = [*LEFT_OUT, *(["count_assumed"] if assumed_left_out else [])]
    frame = result.to_frame()
    assert (frame["count"] + frame[left_out].sum(axis=1)).tolist() == rows


def test_refusals_are_included_at_the_cap_and_counted():
    # AC 6: (12 + 18 + 25 + 100) / 4 = 38.75; median (18 + 25) / 2 = 21.5.
    df = pd.DataFrame(
        {
            "spt_n_capped": [12, 18, 25, 100],
            "spt_n": [12, 18, 25, np.nan],
            "spt_refusal": [False, False, False, True],
        }
    )
    result = ht.stats.describe(df, value="spt_n_capped")
    row = result.to_frame().iloc[0]
    assert row["count"] == 4
    assert row["count_at_least"] == 1
    assert row["mean"] == pytest.approx(38.75)
    assert row["median"] == pytest.approx(21.5)
    assert any("Lower bounds (refusal or '>'): 1." in note for note in result.notes)
    _adds_up(result, [4])


def test_a_refusal_with_a_blank_n_is_a_blank():
    df = pd.DataFrame(
        {"spt_n": [12, 18, 25, np.nan], "spt_refusal": [False, False, False, True]}
    )
    row = ht.stats.describe(df, value="spt_n").to_frame().iloc[0]
    assert row["count"] == 3
    assert row["count_blank"] == 1
    assert row["count_at_least"] == 0


def test_a_refusal_flag_doesnt_apply_to_other_columns():
    df = pd.DataFrame({"water_content": [20, 25, 30], "spt_refusal": [True] * 3})
    row = ht.stats.describe(df, value="water_content").to_frame().iloc[0]
    assert row["count_at_least"] == 0


def test_qualifiers_are_bounds():
    # AC 7
    df = pd.DataFrame(
        {
            "hydraulic_conductivity": [0.1, 2.0, 500.0, 3.0],
            "qualifier": ["<", None, ">", " "],
        }
    )
    df = ht.set_units(df, {"hydraulic_conductivity": "cm/s"})
    result = ht.stats.describe(df, value="hydraulic_conductivity")
    row = result.to_frame().iloc[0]
    assert row["count"] == 4
    assert row["count_at_most"] == 1
    assert row["count_at_least"] == 1
    assert any("Upper bounds ('<'): 1." in note for note in result.notes)


def test_non_plastic_rows_are_left_out(fresh):
    # AC 8: site_si has two NP specimens, with PI 26 and 30 the rest.
    limits = fresh("site_si").atterberg()
    with pytest.warns(UserWarning, match="fewer than 3"):
        result = ht.stats.describe(limits, value="plasticity_index")
    row = result.to_frame().iloc[0]
    assert row["count_non_plastic"] == 2
    assert row["count"] == 2
    assert row["mean"] == pytest.approx(28)
    plastic = limits[limits["non_plastic"] != True]  # noqa: E712
    with pytest.warns(UserWarning, match="fewer than 3"):
        other = ht.stats.describe(plastic, value="plasticity_index")
    other = other.to_frame().iloc[0]
    assert other[["count", "mean", "median"]].tolist() == [2, 28, 28]
    _adds_up(result, [4])


def test_np_text_counts_as_non_plastic():
    df = pd.DataFrame({"plasticity_index": [20, "NP", 30, " np ", 25]})
    row = ht.stats.describe(df, value="plasticity_index").to_frame().iloc[0]
    assert row["count_non_plastic"] == 2
    assert row["count_text"] == 0


def test_assumed_values_are_left_out_by_default(fresh):
    # AC 9: site_si has 2.68 measured and #2.65 assumed.
    density = fresh("site_si").particle_density()
    with pytest.warns(UserWarning) as record:
        result = ht.stats.describe(density, value="particle_density")
    messages = [str(w.message) for w in record]
    assert sum("left out 1 assumed values" in m for m in messages) == 1
    assert any("include_assumed=True" in m for m in messages)
    assert any("fewer than 3" in m for m in messages)
    row = result.to_frame().iloc[0]
    assert row["count"] == 1 and row["mean"] == pytest.approx(2.68)
    assert row["count_assumed"] == 1
    assert not result.include_assumed
    _adds_up(result, [2])


def test_assumed_values_included_on_request(fresh):
    density = fresh("site_si").particle_density()
    with pytest.warns(UserWarning, match="fewer than 3"):
        result = ht.stats.describe(
            density, value="particle_density", include_assumed=True
        )
    row = result.to_frame().iloc[0]
    assert row["count"] == 2
    assert row["mean"] == pytest.approx((2.68 + 2.65) / 2)
    assert row["count_assumed"] == 1
    assert result.include_assumed
    assert "Assumed values included: 1." in result.notes
    _adds_up(result, [2], assumed_left_out=False)


def test_gs_from_a_judgment_is_assumed():
    df = pd.DataFrame(
        {
            "specific_gravity": [2.65, 2.70, 2.68, 2.72],
            "specific_gravity_source": ["judgment", "measured", "Assumed", "measured"],
            "void_ratio": [0.6, 0.7, 0.8, 0.9],
        }
    )
    for column in ("specific_gravity", "void_ratio"):
        with pytest.warns(UserWarning) as record:
            row = ht.stats.describe(df, value=column).to_frame().iloc[0]
        assert any("left out 2 assumed" in str(w.message) for w in record)
        assert row["count"] == 2 and row["count_assumed"] == 2


def test_band_only_rows_are_left_out():
    # AC 10: Stroud gives a band for 15 <= PI < 30, a value for PI >= 30.
    df = pd.DataFrame(
        {"spt_n60": [10, 20, 30, 10, 12], "plasticity_index": [40, 35, 31, 20, 25]}
    )
    estimates = correlations.undrained_shear_strength_stroud_1974(
        df, display_units="SI"
    )
    with pytest.warns(UserWarning, match="left out 2 rows") as record:
        result = ht.stats.describe(estimates, value="undrained_shear_strength")
    assert len(record) == 1
    row = result.to_frame().iloc[0]
    assert row["count_range"] == 2
    assert row["count"] == 3
    assert row["mean"] == pytest.approx(4.5 * 20)
    _adds_up(result, [5])


def test_a_row_with_a_value_and_a_band_gives_its_value():
    df = pd.DataFrame(
        {
            "undrained_shear_strength": [40.0, 50.0, 60.0],
            "undrained_shear_strength_lower": [35.0, np.nan, np.nan],
            "undrained_shear_strength_upper": [45.0, np.nan, np.nan],
        }
    )
    row = (
        ht.stats.describe(df, value="undrained_shear_strength", units="kPa")
        .to_frame()
        .iloc[0]
    )
    assert row["count"] == 3 and row["count_range"] == 0


def test_flags_and_text_count_once_in_order():
    # AC 12: band before NP before assumed before text before blank.
    df = pd.DataFrame(
        {
            "geology_unit": ["A"] * 7,
            "plasticity_index": [np.nan, "NP", 20, "dry", np.nan, 30, 25],
            "plasticity_index_lower": [10, 10, np.nan, np.nan, np.nan, np.nan, 20],
            "non_plastic": [True, False, True, False, False, False, False],
        }
    )
    with pytest.warns(UserWarning):
        result = ht.stats.describe(df, value="plasticity_index", by="geology_unit")
    row = result.to_frame().iloc[0]
    assert row["count_range"] == 1
    assert row["count_non_plastic"] == 2
    assert row["count_text"] == 1
    assert row["count_blank"] == 1
    assert row["count"] == 2
    _adds_up(result, [7])
