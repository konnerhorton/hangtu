"""ht.analysis.clay_activity() (docs/work/m14b-phase-relations.md, AC 11)."""

import warnings

import numpy as np
import pandas as pd
import pytest

import hangtu as ht


def _rows(**columns):
    columns.setdefault("fraction_system", ["iso14688"] * len(columns["clay_content"]))
    return pd.DataFrame(columns)


def test_golden_values():
    df = _rows(plasticity_index=[30.0, 28.0], clay_content=[40.0, 12.0])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = ht.analysis.clay_activity(df)
    assert list(result["clay_activity"]) == pytest.approx([0.75, 28 / 12])
    assert result["clay_activity"].iloc[1] == pytest.approx(2.333333, rel=1e-6)


def test_blanks_are_counted_by_reason():
    df = _rows(
        plasticity_index=[np.nan, 20.0, 20.0, np.nan],
        clay_content=[30.0, 0.0, np.nan, 30.0],
        non_plastic=[True, False, False, False],
    )
    with pytest.warns(UserWarning) as caught:
        result = ht.analysis.clay_activity(df)
    message = str(caught[0].message)
    for part in (
        "1 non-plastic",
        "1 no plasticity index",
        "1 no clay content",
        "1 a clay content of 0",
    ):
        assert part in message
    assert result["clay_activity"].isna().all()


def test_another_fraction_system_is_an_error():
    df = _rows(
        plasticity_index=[20.0], clay_content=[30.0], fraction_system=["astm_uscs"]
    )
    with pytest.raises(ht.HangtuError, match="needs iso14688 fractions"):
        ht.analysis.clay_activity(df)


def test_a_missing_fraction_system_is_an_error():
    df = pd.DataFrame({"plasticity_index": [20.0], "clay_content": [30.0]})
    with pytest.raises(ht.ColumnError, match="'fraction_system' not found"):
        ht.analysis.clay_activity(df)


def test_a_missing_column_is_named():
    with pytest.raises(ht.ColumnError, match="'clay_content'"):
        ht.analysis.clay_activity(pd.DataFrame({"plasticity_index": [20.0]}))
