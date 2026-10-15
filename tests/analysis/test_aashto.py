"""ht.analysis.aashto(): AASHTO group and group index (analysis.md §2.7, §2.9)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError


def soil(passing_10, passing_40, passing_200, **columns):
    """One specimen from its passing 2.00, 0.425 and 0.075 mm."""
    return pd.DataFrame(
        {
            "silt_clay_content": [passing_200],
            "fine_sand_content": [passing_40 - passing_200],
            "coarse_sand_content": [passing_10 - passing_40],
            "gravel_content": [100 - passing_10],
            "boulders_content": [0.0],
            "fraction_system": "aashto",
            **{name: [value] for name, value in columns.items()},
        }
    )


def classify(*args, **kwargs):
    row = ht.analysis.aashto(soil(*args, **kwargs)).iloc[0]
    return row["aashto_group"], row["aashto_group_index"]


@pytest.mark.parametrize(
    ("passing", "limits", "group", "index"),
    [
        # F = 60, LL 45, PI 20: PI > LL - 30, so A-7-6.
        # GI = 25 * 0.225 + 0.01 * 45 * 10 = 5.625 + 4.5 = 10.125 -> 10.
        ((100, 80, 60), {"liquid_limit": 45, "plasticity_index": 20}, "A-7-6", 10),
        # F = 60, LL 60, PI 25: PI <= LL - 30, so A-7-5.
        # GI = 25 * 0.3 + 0.01 * 45 * 15 = 7.5 + 6.75 = 14.25 -> 14.
        ((100, 80, 60), {"liquid_limit": 60, "plasticity_index": 25}, "A-7-5", 14),
        # PI = LL - 30 exactly: A-7-5. GI = 25 * 0.25 + 0.01 * 45 * 10 = 10.75 -> 11.
        ((100, 80, 60), {"liquid_limit": 50, "plasticity_index": 20}, "A-7-5", 11),
        # F = 30, LL 35, PI 15: A-2-6, GI = 0.01 * 15 * 5 = 0.75 -> 1.
        ((100, 60, 30), {"liquid_limit": 35, "plasticity_index": 15}, "A-2-6", 1),
        # F = 40, LL 25, PI 5: A-4, GI = 0.625 - 1.25 < 0 -> 0.
        ((100, 80, 40), {"liquid_limit": 25, "plasticity_index": 5}, "A-4", 0),
        ((40, 20, 10), {"liquid_limit": 20, "plasticity_index": 4}, "A-1-a", 0),
        ((60, 45, 20), {"liquid_limit": 20, "plasticity_index": 4}, "A-1-b", 0),
        ((100, 80, 5), {"liquid_limit": np.nan, "non_plastic": True}, "A-3", 0),
        ((100, 80, 5), {"liquid_limit": 20, "plasticity_index": 2}, "A-2-4", 0),
        # LL 40.4 rounds to 40: A-2-4, not A-2-5.
        ((100, 60, 30), {"liquid_limit": 40.4, "plasticity_index": 8}, "A-2-4", 0),
        ((100, 60, 30), {"liquid_limit": 40.5, "plasticity_index": 8}, "A-2-5", 0),
        # GI = 15 * 0.225 + 0.01 * 35 * -5 = 3.375 - 1.75 = 1.625 -> 2.
        ((100, 80, 50), {"liquid_limit": 45, "plasticity_index": 5}, "A-5", 2),
        # GI = 15 * 0.15 + 0.01 * 35 * 5 = 2.25 + 1.75 = 4.0.
        ((100, 80, 50), {"liquid_limit": 30, "plasticity_index": 15}, "A-6", 4),
    ],
)
def test_group_golden_values(passing, limits, group, index):
    assert classify(*passing, **limits) == (group, index)


def test_boulders_are_left_out_before_classifying():
    df = soil(100, 80, 30, liquid_limit=35, plasticity_index=15)
    # 10 % boulders: passing 0.075 mm of the part finer than 75 mm is 30 / 0.9 = 33.
    df["silt_clay_content"] = 27.0
    df["fine_sand_content"] = 45.0
    df["coarse_sand_content"] = 18.0
    df["gravel_content"] = 0.0
    df["boulders_content"] = 10.0
    out = ht.analysis.aashto(df).iloc[0]
    assert out["aashto_group"] == "A-2-6"
    # GI = 0.01 * (30 - 15) * (15 - 10) = 0.75 -> 1, with F = 30.
    assert out["aashto_group_index"] == 1


def test_missing_value_that_could_decide_the_group_leaves_it_blank():
    # Passing 0.425 mm unknown could make it A-1-b, so the group isn't guessed.
    df = soil(60, 45, 20, liquid_limit=20, plasticity_index=4)
    df["fine_sand_content"] = np.nan
    with pytest.warns(UserWarning, match="blank for 1 of 1"):
        out = ht.analysis.aashto(df).iloc[0]
    assert out["aashto_group"] is None
    assert np.isnan(out["aashto_group_index"])


def test_missing_value_that_cant_decide_the_group_is_fine():
    # F = 60 fails every granular group, so the passing 2.00 mm isn't needed.
    df = soil(100, 80, 60, liquid_limit=45, plasticity_index=20)
    df["coarse_sand_content"] = np.nan
    assert ht.analysis.aashto(df).iloc[0]["aashto_group"] == "A-7-6"


def test_wrong_fraction_system_is_an_error():
    df = soil(100, 80, 60, liquid_limit=45, plasticity_index=20)
    df["fraction_system"] = "astm_uscs"
    with pytest.raises(HangtuError, match="needs aashto fractions"):
        ht.analysis.aashto(df)


def test_missing_fractions_list_the_columns():
    df = soil(100, 80, 60).drop(columns="fine_sand_content")
    with pytest.raises(ColumnError, match="'fine_sand_content' not found"):
        ht.analysis.aashto(df)


def test_end_to_end_from_a_curve():
    df = pd.DataFrame(
        {
            "specimen_id": "A",
            "particle_size": [0.075, 0.15, 0.3, 0.6, 1.18, 2.36, 4.75],
            "percent_passing": [4, 12, 30, 55, 75, 90, 100],
            "non_plastic": True,
            "liquid_limit": np.nan,
        }
    )
    summary = ht.analysis.gradation(
        ht.set_units(df, {"particle_size": "mm"}), fractions="aashto"
    )
    # Passing 2.00/0.425/0.075 mm = 86/43/4, NP: A-1-b needs 0.425 <= 50, so
    # A-1-b (A-1-a needs passing 2.00 mm <= 50).
    out = ht.analysis.aashto(summary).iloc[0]
    assert (out["aashto_group"], out["aashto_group_index"]) == ("A-1-b", 0)
