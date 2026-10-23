"""ht.analysis.summary_by() (docs/work/m13b2-spt-strength-history.md, Decision 12)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht


def test_count_median_min_and_max_by_group():
    df = pd.DataFrame(
        {
            "geology_unit": ["B", "A", "A", "A", "B", None, "A"],
            "plasticity_index": [30, 14, 28, 41, "NP", 20, np.nan],
        }
    )
    df = ht.set_units(df, {"plasticity_index": "%"})
    out = ht.analysis.summary_by(df, "plasticity_index")
    assert out.to_dict("list") == {
        "geology_unit": ["A", "B", "(blank)"],
        "n": [3, 1, 1],
        "median": [28.0, 30.0, 20.0],
        "min": [14.0, 30.0, 20.0],
        "max": [41.0, 30.0, 20.0],
    }
    assert out.attrs["units"] == {"median": "%", "min": "%", "max": "%"}


def test_a_group_with_no_numbers_has_n_zero():
    df = pd.DataFrame({"geology_unit": ["A", "B"], "plasticity_index": [10, "NP"]})
    out = ht.analysis.summary_by(df, "plasticity_index")
    assert out["n"].tolist() == [1, 0]
    assert np.isnan(out["median"].iloc[1])


def test_another_group_column():
    df = pd.DataFrame({"uscs_symbol": ["CL", "CH", "CL"], "liquid_limit": [30, 60, 40]})
    out = ht.analysis.summary_by(df, "liquid_limit", by="uscs_symbol")
    assert out["uscs_symbol"].tolist() == ["CH", "CL"]
    assert out["median"].tolist() == [60.0, 35.0]


def test_missing_columns_raise_naming_them():
    with pytest.raises(ht.ColumnError, match=r"'geology_unit'"):
        ht.analysis.summary_by(
            pd.DataFrame({"plasticity_index": [1]}), "plasticity_index"
        )
