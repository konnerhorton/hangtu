"""Reading input columns (hangtu._data)."""

import numpy as np
import pandas as pd
import pytest

from hangtu._data import is_bound, split_bound, text_values


def test_text_values_splits_numbers_blanks_and_text():
    df = pd.DataFrame(
        {"w": [12.5, " 30 ", "NP", "np ", " Refusal", "dry", "Dry", None, "  ", ""]}
    )
    numbers, texts = text_values(df, "w")

    np.testing.assert_array_equal(numbers, [12.5, 30.0] + [np.nan] * 8)
    assert texts.tolist() == [
        "", "", "NP", "NP", "refusal", "dry", "Dry", "", "", ""
    ]  # fmt: skip


def test_text_values_of_a_numeric_column_has_no_text():
    numbers, texts = text_values(pd.DataFrame({"w": [1.0, np.nan]}), "w")
    np.testing.assert_array_equal(numbers, [1.0, np.nan])
    assert texts.tolist() == ["", ""]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("<5", ("<", 5.0)),
        ("> 200", (">", 200.0)),
        ("<1e-9", ("<", 1e-9)),
        (" > 2.5E+3 ", (">", 2500.0)),
        ("<.5", ("<", 0.5)),
        ("< -3", ("<", -3.0)),
    ],
)
def test_split_bound_reads_a_sign_and_a_number(text, expected):
    assert split_bound(text) == expected
    assert is_bound(text)


@pytest.mark.parametrize("text", ["<", "<5 kPa", "≤5", "5<", "<e5", "NP", "12"])
def test_split_bound_leaves_other_text(text):
    assert split_bound(text) is None
    assert not is_bound(text)
