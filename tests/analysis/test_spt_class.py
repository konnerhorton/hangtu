"""ht.analysis.spt_class(): SPT class tables (docs/drafts/analysis.md §1.4, §1.6)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu import _config

COHESIONLESS = ["Very loose", "Loose", "Medium dense", "Dense", "Very dense"]
COHESIVE = ["Very soft", "Soft", "Medium stiff", "Stiff", "Very stiff", "Hard"]


def test_cohesionless_golden_values():
    df = pd.DataFrame({"spt_n": [0, 4, 10, 29, 30, 50, 51]})
    assert ht.analysis.spt_class(df).tolist() == [
        "Very loose",
        "Loose",
        "Medium dense",
        "Medium dense",
        "Dense",
        "Very dense",
        "Very dense",
    ]


def test_cohesionless_golden_counts_keep_n_equal_zero():
    # pd.cut's right-closed default drops N = 0 and gives a total of 6 (§1.4).
    df = pd.DataFrame({"spt_n": [0, 4, 10, 29, 30, 50, 51]})
    counts = ht.analysis.spt_class(df).value_counts(sort=False)
    assert counts.tolist() == [1, 1, 2, 1, 2, 0]
    assert counts.sum() == 7


def test_cohesive_golden_values():
    df = pd.DataFrame({"spt_n": [0, 1, 2, 4, 8, 15, 30, 31]})
    assert ht.analysis.spt_class(df, table="cohesive").tolist() == [
        "Very soft",
        "Very soft",
        "Soft",
        "Medium stiff",
        "Stiff",
        "Very stiff",
        "Hard",
        "Hard",
    ]


def test_categories_are_in_table_order_with_refusal_last():
    df = pd.DataFrame({"spt_n": [12]})
    classes = ht.analysis.spt_class(df, table="cohesive")
    assert classes.cat.ordered
    assert list(classes.cat.categories) == [*COHESIVE, "Refusal"]
    assert classes.name == "spt_class"


def test_refusal_is_refusal_only_whatever_its_n():
    df = pd.DataFrame({"spt_n": [12, np.nan, 12], "spt_refusal": [True, True, False]})
    assert ht.analysis.spt_class(df).tolist() == ["Refusal", "Refusal", "Medium dense"]


def test_blank_value_gives_a_blank_class():
    df = pd.DataFrame({"spt_n": [np.nan, 5]})
    classes = ht.analysis.spt_class(df)
    assert pd.isna(classes.iloc[0])
    assert classes.iloc[1] == "Loose"


def test_every_row_with_a_value_lands_in_exactly_one_class():
    rng = np.random.default_rng(0)
    n = rng.integers(0, 120, size=200).astype(float)
    n[::17] = np.nan
    refusal = rng.random(200) < 0.1
    df = pd.DataFrame({"spt_n": n, "spt_refusal": refusal})
    classes = ht.analysis.spt_class(df)
    expected = int((~np.isnan(n) | refusal).sum())
    assert classes.value_counts().sum() == expected
    assert classes.notna().sum() == expected


def test_classifies_n60():
    # N = 8 is loose; N60 = 8 * 80 / 60 = 10.667 is medium dense.
    df = pd.DataFrame({"spt_n": [8], "energy_ratio": [80]})
    assert ht.analysis.spt_class(df).tolist() == ["Loose"]
    assert ht.analysis.spt_class(df, n="spt_n60").tolist() == ["Medium dense"]


def test_n60_with_no_energy_ratio_is_blank():
    df = pd.DataFrame({"spt_n": [8]})
    assert ht.analysis.spt_class(df, n="spt_n60").isna().all()


def test_classifies_capped_n():
    df = pd.DataFrame({"spt_n": [120]})
    assert ht.analysis.spt_class(df, n="spt_n_capped").tolist() == ["Very dense"]


def test_keeps_the_index_and_leaves_df_unchanged():
    df = pd.DataFrame({"spt_n": [3, 40]}, index=["a", "b"])
    before = df.copy()
    classes = ht.analysis.spt_class(df)
    assert list(classes.index) == ["a", "b"]
    pd.testing.assert_frame_equal(df, before)


def test_unknown_table_lists_the_tables():
    with pytest.raises(
        ht.HangtuError, match=r"'clay'.*'cohesionless', 'cohesive'.*table="
    ):
        ht.analysis.spt_class(pd.DataFrame({"spt_n": [5]}), table="clay")


def test_unknown_n_lists_the_columns():
    with pytest.raises(ht.HangtuError, match=r"'spt_n', 'spt_n60'.*not 'N'"):
        ht.analysis.spt_class(pd.DataFrame({"spt_n": [5]}), n="N")


def test_negative_n60_given_is_an_error():
    df = pd.DataFrame({"spt_n": [5, 5], "spt_n60": [6.0, -1.0]})
    with pytest.raises(ht.HangtuError, match=r"'spt_n60' has negative.*rows 1\b"):
        ht.analysis.spt_class(df, n="spt_n60")


@pytest.mark.parametrize(
    ("table", "names"), [("cohesionless", COHESIONLESS), ("cohesive", COHESIVE)]
)
def test_config_tables_start_at_zero_and_rise(table, names):
    entry = _config.load("config/spt_classes.yaml")[table]
    lowers = [c["lower"] for c in entry["classes"]]
    assert [c["name"] for c in entry["classes"]] == names
    assert lowers[0] == 0
    assert lowers == sorted(set(lowers))
    assert entry["source"]
