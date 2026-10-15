"""ht.analysis.plasticity(): indices and classes (docs/drafts/analysis.md §2.9)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.analysis._plasticity import a_line, on_or_above_a_line
from hangtu.errors import ColumnError, HangtuError


def classes(liquid, index, **columns):
    df = pd.DataFrame({"liquid_limit": liquid, "plasticity_index": index, **columns})
    out = ht.analysis.plasticity(df)
    return (
        out["plasticity_class_uscs"].tolist(),
        out["plasticity_class_bs5930"].tolist(),
    )


# --- Indices -----------------------------------------------------------------------


def test_indices_golden_values():
    df = pd.DataFrame(
        {"liquid_limit": [45.0], "plastic_limit": [20.0], "water_content": [30.0]}
    )
    out = ht.analysis.plasticity(df)
    # PI = 45 - 20 = 25; LI = (30 - 20) / 25 = 0.40; Ic = (45 - 30) / 25 = 0.60.
    assert out["plasticity_index"].tolist() == [25.0]
    assert out["liquidity_index"].tolist() == pytest.approx([0.40])
    assert out["consistency_index"].tolist() == pytest.approx([0.60])


def test_pi_given_is_kept_and_warned_when_off_by_more_than_one_point():
    df = pd.DataFrame(
        {
            "liquid_limit": [45.0, 45.0],
            "plastic_limit": [20.0, 20.0],
            "plasticity_index": [23.5, 26.0],
        }
    )
    with pytest.warns(UserWarning, match=r"Rows 0 have a plasticity_index more than 1"):
        out = ht.analysis.plasticity(df)
    assert out["plasticity_index"].tolist() == [23.5, 26.0]


def test_non_plastic_leaves_the_indices_blank():
    df = pd.DataFrame(
        {
            "liquid_limit": [30.0, np.nan],
            "plastic_limit": [np.nan, np.nan],
            "water_content": [20.0, 15.0],
            "non_plastic": ["yes", True],
        }
    )
    out = ht.analysis.plasticity(df)
    assert out["plasticity_index"].isna().all()
    assert out["liquidity_index"].isna().all()
    assert out["consistency_index"].isna().all()


def test_zero_pi_gives_blank_li_and_ic():
    df = pd.DataFrame(
        {"liquid_limit": [25.0], "plastic_limit": [25.0], "water_content": [20.0]}
    )
    out = ht.analysis.plasticity(df)
    assert out["plasticity_index"].tolist() == [0.0]
    assert out["liquidity_index"].isna().all()


def test_pi_above_ll_is_kept_and_warned():
    with pytest.warns(UserWarning, match="above their liquid_limit"):
        uscs, _ = classes([20.0], [25.0])
    assert uscs == ["CL"]


# --- USCS classes ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("liquid", "index", "expected"),
    [
        (45, 25, "CL"),
        (60, 20, "MH"),  # A-line at 29.2
        (22, 5, "CL-ML"),
        (30, 6, "ML"),  # A-line at 7.3
        (50, 30, "CH"),  # LL = 50 is high plasticity
        (49.9, 3.9, "ML"),
        (25, 4, "CL-ML"),
        (25, 7, "CL-ML"),
        (25, 7.5, "CL"),
        (15, 3, "ML"),  # above the A-line, but PI < 4
    ],
)
def test_uscs_class_golden_values(liquid, index, expected):
    uscs, _ = classes([float(liquid)], [float(index)])
    assert uscs == [expected]


def test_a_point_on_the_a_line_is_a_clay():
    # 0.73 * (40 - 20) = 14.6, computed in floating point.
    index = float(a_line(40.0))
    assert classes([40.0], [index])[0] == ["CL"]
    assert classes([40.0], [14.6])[0] == ["CL"]
    assert on_or_above_a_line([50.0], [21.9]).tolist() == [True]


def test_non_plastic_is_ml_or_mh():
    uscs, bs5930 = classes(
        [35.0, 55.0, np.nan], [np.nan, np.nan, np.nan], non_plastic=[True, True, True]
    )
    assert uscs == ["ML", "MH", "ML"]
    assert bs5930 == ["MI", "MH", None]


def test_blank_values_give_blank_classes():
    uscs, bs5930 = classes([np.nan, 40.0], [20.0, np.nan])
    assert uscs == [None, None]
    assert bs5930 == [None, None]


# --- BS 5930 classes ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("liquid", "index", "expected"),
    [
        (34.9, 15, "CL"),
        (35, 15, "CI"),
        (60, 20, "MH"),
        (70, 50, "CV"),
        (95, 70, "CE"),
        (90, 40, "ME"),
    ],
)
def test_bs5930_class_golden_values(liquid, index, expected):
    _, bs5930 = classes([float(liquid)], [float(index)])
    assert bs5930 == [expected]


# --- Rows --------------------------------------------------------------------------


def test_rows_order_units_and_input_are_kept():
    df = pd.DataFrame(
        {
            "loca_id": ["BH2", "BH1"],
            "depth": [3.0, 1.0],
            "liquid_limit": [45.0, 60.0],
            "plastic_limit": [20.0, 40.0],
        },
        index=[7, 3],
    )
    df = ht.set_units(df, {"depth": "ft"})
    before = df.copy()
    out = ht.analysis.plasticity(df)
    assert out.index.tolist() == [7, 3]
    assert out["loca_id"].tolist() == ["BH2", "BH1"]
    assert out.attrs["units"] == {"depth": "ft"}
    pd.testing.assert_frame_equal(df, before)
    assert "plasticity_index" not in df.columns


# --- Errors ------------------------------------------------------------------------


def test_missing_liquid_limit_lists_the_columns():
    with pytest.raises(ColumnError, match=r"'liquid_limit' not found.*plastic_limit"):
        ht.analysis.plasticity(pd.DataFrame({"plastic_limit": [20.0]}))


def test_negative_values_are_an_error():
    df = pd.DataFrame({"liquid_limit": [40.0, 30.0], "water_content": [10.0, -5.0]})
    with pytest.raises(
        HangtuError, match="'water_content' has negative values in rows 1"
    ):
        ht.analysis.plasticity(df)


def test_text_in_a_limit_is_an_error():
    with pytest.raises(ColumnError, match=r"'liquid_limit'.*'NP'"):
        ht.analysis.plasticity(pd.DataFrame({"liquid_limit": [40.0, "NP"]}))


def test_plastic_limit_above_liquid_limit_is_an_error():
    df = pd.DataFrame({"liquid_limit": [30.0], "plastic_limit": [35.0]})
    with pytest.raises(HangtuError, match="plastic_limit above their liquid_limit"):
        ht.analysis.plasticity(df)


def test_non_plastic_with_a_pi_is_an_error():
    df = pd.DataFrame(
        {"liquid_limit": [30.0], "plasticity_index": [5.0], "non_plastic": [True]}
    )
    with pytest.raises(HangtuError, match="marked non_plastic but also have"):
        ht.analysis.plasticity(df)


def test_bad_non_plastic_value_is_an_error():
    df = pd.DataFrame({"liquid_limit": [30.0], "non_plastic": ["maybe"]})
    with pytest.raises(ColumnError, match="'non_plastic' must hold True or False"):
        ht.analysis.plasticity(df)
