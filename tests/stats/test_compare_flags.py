"""compare(): flags and counts per group, as describe() (m15d-compare, AC 11)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.analysis import correlations

LEFT_OUT = ["count_non_plastic", "count_assumed", "count_range", "count_text"]


def _adds_up(result, rows):
    # count and the counts of rows left out add up to each group's rows.
    row = result.to_frame().iloc[0]
    for i, n in enumerate(rows, start=1):
        left_out = sum(row[f"{name}_{i}"] for name in [*LEFT_OUT, "count_blank"])
        assert row[f"count_{i}"] + left_out == n


def _compare(df, value, **kwargs):
    return ht.stats.compare(
        df, value=value, by="geology_unit", significance_level=0.05, **kwargs
    )


def test_refusals_are_counted_with_the_note():
    df = pd.DataFrame(
        {
            "geology_unit": ["A"] * 5 + ["B"] * 5,
            "spt_n_capped": [12, 18, 25, 100, 30, 10, 11, 14, 16, 20],
            "spt_refusal": [False, False, False, True, False] + [False] * 5,
        }
    )
    result = _compare(df, "spt_n_capped")
    row = result.to_frame().iloc[0]
    assert (row["count_at_least_1"], row["count_at_least_2"]) == (1, 0)
    assert row["count_1"] == 5
    assert row["mean_1"] == pytest.approx((12 + 18 + 25 + 100 + 30) / 5)
    note = next(note for note in result.notes if note.startswith("Lower bounds"))
    assert "A 1, entered at their value" in note
    assert "mean is an underestimate" in note
    assert "at least" in str(result)
    _adds_up(result, [5, 5])


def test_np_text_and_blanks_are_left_out_per_group():
    df = pd.DataFrame(
        {
            "geology_unit": ["A"] * 7 + ["B"] * 6,
            "plasticity_index": [
                *[20, "NP", 30, 25, np.nan, 22, 27],
                *[35, 40, "dry", 38, 41, 39],
            ],
        }
    )
    with pytest.warns(UserWarning, match="'dry' \\(1\\)"):
        result = _compare(df, "plasticity_index")
    row = result.to_frame().iloc[0]
    assert (row["count_non_plastic_1"], row["count_blank_1"]) == (1, 1)
    assert row["count_text_2"] == 1
    assert (row["count_1"], row["count_2"]) == (5, 5)
    _adds_up(result, [7, 6])


def test_assumed_values_are_left_out_unless_asked():
    df = pd.DataFrame(
        {
            "geology_unit": ["A"] * 6 + ["B"] * 6,
            "specific_gravity": [
                *[2.65, 2.70, 2.68, 2.72, 2.66, 2.69],
                *[2.60, 2.62, 2.61, 2.63, 2.64, 2.59],
            ],
            "specific_gravity_source": ["judgment"] + ["measured"] * 11,
        }
    )
    with pytest.warns(UserWarning, match="left out 1 assumed"):
        left_out = _compare(df, "specific_gravity").to_frame().iloc[0]
    assert (left_out["count_1"], left_out["count_assumed_1"]) == (5, 1)
    included = _compare(df, "specific_gravity", include_assumed=True)
    row = included.to_frame().iloc[0]
    assert (row["count_1"], row["count_assumed_1"]) == (6, 1)
    assert "Assumed values included: A 1." in included.notes


def test_bands_are_left_out_and_counted():
    df = pd.DataFrame(
        {
            "spt_n60": [10, 20, 30, 10, 12, 40, 45, 50, 35, 33],
            "plasticity_index": [40, 35, 31, 20, 25, 40, 35, 31, 45, 50],
            "geology_unit": ["A"] * 5 + ["B"] * 5,
        }
    )
    estimates = correlations.undrained_shear_strength_stroud_1974(
        df, display_units="SI"
    )
    with pytest.warns(UserWarning) as record:
        result = _compare(estimates, "undrained_shear_strength")
    messages = [str(w.message) for w in record]
    assert any("left out 2 rows" in message for message in messages)
    row = result.to_frame().iloc[0]
    assert (row["count_range_1"], row["count_1"]) == (2, 3)
    _adds_up(result, [5, 5])


def test_a_group_all_bounds_at_one_value_has_no_tests():
    df = pd.DataFrame(
        {
            "geology_unit": ["A"] * 5 + ["B"] * 5,
            "spt_n_capped": [50] * 5 + [10, 11, 14, 16, 20],
            "spt_refusal": [True] * 5 + [False] * 5,
        }
    )
    result = _compare(df, "spt_n_capped")
    row = result.to_frame().iloc[0]
    assert row["count_1"] == 5
    assert np.isnan(row["welch_p_value"])
    assert "A: every value is a bound at 50, so neither test is run." in result.notes
