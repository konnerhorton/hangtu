"""Reading input columns (hangtu._data)."""

import numpy as np
import pandas as pd

from hangtu._data import text_values


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
