"""crosstab(): the table (m15e-crosstab, AC 1, 4, 5, 7, 8 and 9)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError


def _table(frame):
    """The counts as nested lists, with the labels, for one comparison."""
    return frame.index.tolist(), frame.columns.tolist(), frame.to_numpy().tolist()


def test_legend_code_against_uscs(example_index):
    # AC 1: hand counts from the 20 rows listed in the spec.
    result = ht.stats.crosstab(example_index, "legend_code", "uscs_symbol")
    frame = result.to_frame()
    assert _table(frame) == (
        ["CL", "FILL", "SP", "(total)"],
        ["CH", "CL", "ML", "SC", "(blank)", "(total)"],
        [
            [3, 2, 1, 0, 6, 12],
            [0, 0, 0, 2, 0, 2],
            [0, 0, 0, 0, 6, 6],
            [3, 2, 1, 2, 12, 20],
        ],
    )
    assert frame.index.name == "legend_code"
    assert frame.columns.name == "uscs_symbol"
    assert result.row_values == ("CL", "FILL", "SP")
    assert result.column_values == ("CH", "CL", "ML", "SC")
    assert result.agree is None
    assert result.count_compared is None
    assert result.proportion_agreeing is None
    assert result.mismatches.empty
    assert any(note.startswith("No agreement counted") for note in result.notes)


def test_geology_unit_keeps_the_map_order(example_index):
    # AC 4: Fill, Alluvium, Terrace is the map's order, not alphabetical.
    frame = ht.stats.crosstab(example_index, "geology_unit", "legend_code").to_frame()
    assert _table(frame) == (
        ["Fill", "Alluvium", "Terrace", "(total)"],
        ["CL", "FILL", "SP", "(total)"],
        [[0, 2, 0, 2], [12, 0, 0, 12], [0, 0, 6, 6], [12, 2, 6, 20]],
    )


def test_categorical_order_blanks_and_case():
    # AC 5: category order with no row for the unused Z; X and x stay apart.
    rows = pd.Categorical(
        ["B", "a", None, "B", "a", "C"], categories=["C", "B", "a", "Z"], ordered=True
    )
    df = pd.DataFrame({"first": rows, "second": ["x", "X", "x", None, "X", "y"]})
    frame = ht.stats.crosstab(df, "first", "second").to_frame()
    assert _table(frame) == (
        ["C", "B", "a", "(blank)", "(total)"],
        ["X", "x", "y", "(blank)", "(total)"],
        [
            [0, 0, 1, 0, 1],
            [0, 1, 0, 1, 2],
            [2, 0, 0, 0, 2],
            [0, 1, 0, 0, 1],
            [2, 2, 1, 1, 6],
        ],
    )


def test_spaces_and_case_are_kept():
    # AC 6's table: "CL " is its own class; spaces alone are blank.
    df = pd.DataFrame({"logged": ["CL", "CL ", "  ", "cl"], "lab": ["CL"] * 4})
    frame = ht.stats.crosstab(df, "logged", "lab").to_frame()
    assert frame.index.tolist() == ["CL", "CL ", "cl", "(blank)", "(total)"]


def test_whole_numbers_without_a_decimal():
    # AC 7: integer and float codes read as the same text.
    df = pd.DataFrame({"code": [101, 101, 102], "other": [101.0, np.nan, 102.0]})
    frame = ht.stats.crosstab(df, "code", "other").to_frame()
    assert _table(frame) == (
        ["101", "102", "(total)"],
        ["101", "102", "(blank)", "(total)"],
        [[1, 0, 1, 2], [0, 1, 0, 1], [1, 1, 1, 3]],
    )


def test_empty_frame():
    # AC 10's empty frame: only the totals, 0.
    frame = ht.stats.crosstab(pd.DataFrame({"a": [], "b": []}), "a", "b").to_frame()
    assert _table(frame) == (["(total)"], ["(total)"], [[0]])


def test_counts_add_up(example_index):
    # AC 9: every row is counted once.
    for rows, columns in [
        ("legend_code", "uscs_symbol"),
        ("geology_unit", "legend_code"),
        ("geology_code", "plasticity_class_uscs"),
    ]:
        frame = ht.stats.crosstab(example_index, rows, columns).to_frame()
        assert frame.loc["(total)", "(total)"] == len(example_index)
        body = frame.drop(index="(total)", columns="(total)")
        assert body.to_numpy().sum() == len(example_index)


def test_missing_column():
    # AC 8.
    df = pd.DataFrame({"legend_code": ["CL"], "uscs_symbol": ["CL"]})
    with pytest.raises(ColumnError, match=r"'geology_code'.*Available columns: "):
        ht.stats.crosstab(df, "geology_code", "uscs_symbol")


def test_same_column_twice():
    df = pd.DataFrame({"legend_code": ["CL"]})
    with pytest.raises(HangtuError, match="against itself"):
        ht.stats.crosstab(df, "legend_code", "legend_code")


def test_a_measurement_is_an_error():
    df = pd.DataFrame({"legend_code": ["CL"], "plasticity_index": [20.0]})
    with pytest.raises(ColumnError, match=r"compare\(\).*pd\.cut"):
        ht.stats.crosstab(df, "legend_code", "plasticity_index")


@pytest.mark.parametrize("data", [pd.Series(["CL"]), ["CL"], np.array(["CL"])])
def test_not_a_frame(data):
    with pytest.raises(HangtuError, match="takes a DataFrame and the names"):
        ht.stats.crosstab(data, "legend_code", "uscs_symbol")
