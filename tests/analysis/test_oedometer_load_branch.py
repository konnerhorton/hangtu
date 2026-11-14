"""oedometer_load_branch() (datasets.md §6.14; M19 a)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError

# The spec's specimen (M19 a, acceptance criteria table): twelve increments,
# 800 kPa reached again at increment 10 before 1600 kPa.
TABLE_STRESSES_KPA = [25, 50, 100, 200, 400, 800, 200, 50, 200, 800, 1600, 400]
TABLE_BRANCHES = [
    "loading",
    "loading",
    "loading",
    "loading",
    "loading",
    "loading",
    "unloading",
    "unloading",
    "reloading",
    "reloading",
    "loading",
    "unloading",
]
PSF_PER_KPA = 20.8854342


def branches(stresses, specimens=None):
    df = pd.DataFrame(
        {
            "specimen_id": specimens or [1] * len(stresses),
            "applied_vertical_stress": stresses,
        }
    )
    return ht.analysis.oedometer_load_branch(df)["load_branch"].tolist()


def test_ac2_the_table_specimen():
    assert branches(TABLE_STRESSES_KPA) == TABLE_BRANCHES


def test_ac2_the_same_branches_in_psf():
    psf = [stress * PSF_PER_KPA for stress in TABLE_STRESSES_KPA]
    assert branches(psf) == TABLE_BRANCHES


def test_ac3_constant_unloading_blank_reloading():
    assert branches([100, 100, 50, np.nan, 100, 200]) == [
        "loading",
        "constant_stress",
        "unloading",
        None,
        "reloading",
        "loading",
    ]


def test_ac3_each_specimen_starts_at_loading():
    result = branches([100, 50, 200, 100], specimens=[1, 1, 2, 2])
    assert result == ["loading", "unloading", "loading", "unloading"]


def test_interleaved_specimens_are_followed_separately():
    result = branches([100, 400, 200, 300], specimens=[1, 2, 1, 2])
    assert result == ["loading", "loading", "loading", "unloading"]


def test_a_specimen_with_no_increments_has_a_blank_branch():
    assert branches([np.nan]) == [None]


@pytest.mark.parametrize("column", ["applied_vertical_stress", "specimen_id"])
def test_ac3_a_missing_column_is_named(column):
    df = pd.DataFrame({"specimen_id": [1], "applied_vertical_stress": [100.0]})
    with pytest.raises(ColumnError, match=column):
        ht.analysis.oedometer_load_branch(df.drop(columns=column))


def test_returns_a_copy_and_keeps_the_index():
    df = pd.DataFrame(
        {"specimen_id": [1, 1], "applied_vertical_stress": [100.0, 200.0]},
        index=[7, 3],
    )
    result = ht.analysis.oedometer_load_branch(df)
    assert "load_branch" not in df.columns
    assert result.index.tolist() == [7, 3]
