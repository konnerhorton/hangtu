"""ht.analysis.spt(): refusal, N60 and the cap (docs/drafts/analysis.md §1.3, §1.6)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht


def frame(**columns):
    return pd.DataFrame(columns)


# --- N60 -----------------------------------------------------------------------------


def test_n60_golden_values_from_the_row():
    out = ht.analysis.spt(frame(spt_n=[30, 25], energy_ratio=[80, 55]))
    # 30 * 80 / 60 = 40.0; 25 * 55 / 60 = 22.9167
    assert out["spt_n60"].tolist() == pytest.approx([40.0, 22.917], abs=5e-4)


def test_n60_from_the_argument_then_the_setting():
    df = frame(spt_n=[30])
    assert ht.analysis.spt(df, hammer_efficiency=80)["spt_n60"].tolist() == [40.0]
    ht.settings.hammer_efficiency = 90
    assert ht.analysis.spt(df)["spt_n60"].tolist() == [45.0]
    # The argument wins over the setting.
    assert ht.analysis.spt(df, hammer_efficiency=60)["spt_n60"].tolist() == [30.0]


def test_the_row_energy_ratio_wins_over_argument_and_setting():
    ht.settings.hammer_efficiency = 90
    df = frame(spt_n=[30, 30], energy_ratio=[80, np.nan])
    out = ht.analysis.spt(df, hammer_efficiency=60)
    assert out["spt_n60"].tolist() == [40.0, 30.0]


def test_no_energy_ratio_anywhere_leaves_n60_blank():
    out = ht.analysis.spt(frame(spt_n=[30, 12]))
    assert out["spt_n60"].isna().all()


def test_n60_already_filled_in_is_kept_and_blanks_are_computed():
    df = frame(spt_n=[30, 30], energy_ratio=[80, 80], spt_n60=[33.0, np.nan])
    assert ht.analysis.spt(df)["spt_n60"].tolist() == [33.0, 40.0]


def test_n60_is_computed_for_refusals_and_not_capped():
    df = frame(spt_n=[90, 38], energy_ratio=[80, 80], spt_refusal=[False, True])
    out = ht.analysis.spt(df)
    # 90 * 80 / 60 = 120, above the cap and kept; 38 * 80 / 60 = 50.667.
    assert out["spt_n60"].tolist() == pytest.approx([120.0, 50.667], abs=5e-4)


# --- Refusal --------------------------------------------------------------------------


def test_refusal_given_is_kept():
    df = frame(spt_n=[12, 60], spt_refusal=[True, False])
    assert ht.analysis.spt(df)["spt_refusal"].tolist() == [True, False]


def test_refusal_found_from_penetration_in_mm():
    df = ht.set_units(
        frame(spt_n=[50, 40], spt_penetration=[300, 450]),
        {"spt_penetration": "mm"},
    )
    assert ht.analysis.spt(df)["spt_refusal"].tolist() == [True, False]


def test_refusal_found_from_penetration_in_inches():
    # 12 in = 304.8 mm < 450 → refusal; 18 in = 457.2 mm → not.
    df = frame(spt_n=[50, 40], spt_penetration=[12, 18])
    out = ht.analysis.spt(df, units={"spt_penetration": "in"})
    assert out["spt_refusal"].tolist() == [True, False]


def test_given_refusal_wins_over_penetration():
    df = frame(
        spt_n=[50, 40, 30],
        spt_refusal=[False, True, None],
        spt_penetration=[300, 450, 300],
    )
    out = ht.analysis.spt(df, units={"spt_penetration": "mm"})
    assert out["spt_refusal"].tolist() == [False, True, True]


def test_blank_refusal_and_blank_penetration_is_not_a_refusal():
    df = frame(spt_n=[50, 40], spt_refusal=[None, None], spt_penetration=[np.nan, None])
    assert ht.analysis.spt(df)["spt_refusal"].tolist() == [False, False]


def test_no_refusal_columns_means_no_refusals():
    out = ht.analysis.spt(frame(spt_n=[50, 150]))
    assert out["spt_refusal"].dtype == bool
    assert out["spt_refusal"].tolist() == [False, False]


@pytest.mark.parametrize(
    ("cell", "expected"),
    [
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        (1.0, True),
        ("TRUE", True),
        ("False", False),
        (" yes ", True),
        ("No", False),
        ("1", True),
        ("", False),
    ],
)
def test_refusal_cells_accepted(cell, expected):
    df = frame(spt_n=[20], spt_refusal=pd.Series([cell], dtype=object))
    assert ht.analysis.spt(df)["spt_refusal"].tolist() == [expected]


def test_refusal_read_from_csv_with_blanks(tmp_path):
    path = tmp_path / "spt.csv"
    path.write_text("spt_n,spt_refusal\n12,TRUE\n30,\n45,FALSE\n")
    out = ht.analysis.spt(ht.read_csv(path))
    assert out["spt_refusal"].tolist() == [True, False, False]


def test_units_are_needed_only_when_a_row_uses_penetration():
    # Every refusal filled in: penetration without units is fine.
    df = frame(spt_n=[50], spt_refusal=[True], spt_penetration=[300])
    assert ht.analysis.spt(df)["spt_refusal"].tolist() == [True]


# --- Capped N -------------------------------------------------------------------------


def test_capped_n_golden_values():
    df = frame(spt_n=[120, 38, np.nan, 20], spt_refusal=[False, True, True, False])
    out = ht.analysis.spt(df)
    assert out["spt_n_capped"].tolist() == [100.0, 100.0, 100.0, 20.0]


def test_blank_n_that_is_not_a_refusal_stays_blank():
    out = ht.analysis.spt(frame(spt_n=[np.nan]))
    assert np.isnan(out["spt_n_capped"].iloc[0])


def test_cap_from_the_argument_and_the_setting():
    df = frame(spt_n=[60, 20], spt_refusal=[False, True])
    assert ht.analysis.spt(df, cap=50)["spt_n_capped"].tolist() == [50.0, 50.0]
    ht.settings.spt_cap = 50
    assert ht.analysis.spt(df)["spt_n_capped"].tolist() == [50.0, 50.0]


# --- Rows -----------------------------------------------------------------------------


def test_rows_order_columns_and_units_are_kept_and_df_is_unchanged():
    df = ht.set_units(
        pd.DataFrame(
            {"loca_id": ["BH2", "BH1"], "depth": [10.0, 5.0], "spt_n": [12, 30]},
            index=[7, 3],
        ),
        {"depth": "ft"},
    )
    before = df.copy()
    out = ht.analysis.spt(df)
    pd.testing.assert_frame_equal(df, before)
    assert list(out.index) == [7, 3]
    assert list(out.columns) == [
        "loca_id",
        "depth",
        "spt_n",
        "spt_refusal",
        "spt_n60",
        "spt_n_capped",
    ]
    assert ht.units_of(out) == {"depth": "ft"}


# --- Errors ---------------------------------------------------------------------------


def test_missing_spt_n_lists_the_columns():
    with pytest.raises(ht.ColumnError, match=r"'spt_n'.*Available columns: depth, n"):
        ht.analysis.spt(frame(depth=[1.0], n=[12]))


def test_non_numeric_n_names_the_row():
    with pytest.raises(ht.ColumnError, match=r"'spt_n'.*rows 1 \('50/75'\)"):
        ht.analysis.spt(frame(spt_n=["12", "50/75"]))


def test_negative_n_names_the_row():
    with pytest.raises(ht.HangtuError, match=r"negative blow counts in rows 1\b"):
        ht.analysis.spt(frame(spt_n=[12, -3]))


def test_energy_ratio_of_zero_is_an_error():
    with pytest.raises(ht.HangtuError, match=r"rows 0 aren't.*0\.8 should be.*80"):
        ht.analysis.spt(frame(spt_n=[12], energy_ratio=[0]))


def test_energy_ratio_over_100_is_an_error():
    with pytest.raises(ht.HangtuError, match=r"'energy_ratio'.*rows 1 aren't"):
        ht.analysis.spt(frame(spt_n=[12, 12], energy_ratio=[80, 120]))


@pytest.mark.parametrize("value", [0, 120, "80", True])
def test_bad_hammer_efficiency_argument(value):
    with pytest.raises(ht.HangtuError, match=r"hammer_efficiency must be.*=80"):
        ht.analysis.spt(frame(spt_n=[12]), hammer_efficiency=value)


@pytest.mark.parametrize("value", [0, -5, 50.5, True])
def test_bad_cap_argument(value):
    with pytest.raises(ht.HangtuError, match=r"cap must be.*cap=100"):
        ht.analysis.spt(frame(spt_n=[12]), cap=value)


def test_bad_refusal_cell_names_rows_and_values():
    df = frame(spt_n=[12, 20, 30], spt_refusal=["yes", "R", "50/75"])
    with pytest.raises(
        ht.ColumnError, match=r"'spt_refusal'.*rows 1, 2 hold 'R', '50/75'"
    ):
        ht.analysis.spt(df)


def test_penetration_without_units_shows_how_to_declare_them():
    df = frame(spt_n=[50], spt_penetration=[300])
    with pytest.raises(
        ht.UnitsError, match=r"'spt_penetration' has no units.*set_units"
    ):
        ht.analysis.spt(df)


def test_penetration_in_the_wrong_dimension_is_an_error():
    df = frame(spt_n=[50], spt_penetration=[300])
    with pytest.raises(ht.UnitsError):
        ht.analysis.spt(df, units={"spt_penetration": "kPa"})


def test_not_a_dataframe():
    with pytest.raises(ht.HangtuError, match="pandas DataFrame, not list"):
        ht.analysis.spt([12, 30])
