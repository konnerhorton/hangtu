"""crosstab(agree=): agreement and mismatches (m15e-crosstab, AC 2, 3, 6-10)."""

import json
import math

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError

LISTING = [
    "loca_id",
    "sample_reference",
    "depth",
    "water_content_specimen_id",
    "atterberg_specimen_id",
    "grain_size_specimen_id",
    "legend_code",
    "uscs_symbol",
    "source_line",
]
MAPPING = {"CL": "CL", "FILL": ["SC", "SM", "GC"], "SP": ["SP", "SP-SM"]}


def _counts(result):
    return {
        name: getattr(result, name)
        for name in (
            "count_compared",
            "count_agreeing",
            "count_disagreeing",
            "count_blank_in_rows",
            "count_blank_in_columns",
            "count_blank_in_both",
        )
    }


def _add_up(result, rows):
    # AC 9: the compared rows and the three blank counts are every row.
    counts = _counts(result)
    assert (
        counts["count_compared"]
        + counts["count_blank_in_rows"]
        + counts["count_blank_in_columns"]
        + counts["count_blank_in_both"]
        == rows
    )
    assert (
        counts["count_agreeing"] + counts["count_disagreeing"]
        == counts["count_compared"]
    )


def test_same_text(example_index):
    # AC 2: hand counts from the 20 rows listed in the spec.
    result = ht.stats.crosstab(
        example_index, "legend_code", "uscs_symbol", agree="same"
    )
    assert _counts(result) == {
        "count_compared": 8,
        "count_agreeing": 2,
        "count_disagreeing": 6,
        "count_blank_in_rows": 0,
        "count_blank_in_columns": 12,
        "count_blank_in_both": 0,
    }
    assert result.proportion_agreeing == 0.25
    assert result.agree == "same"
    _add_up(result, len(example_index))
    mismatches = result.mismatches
    assert mismatches.columns.tolist() == LISTING
    assert list(
        zip(
            mismatches["loca_id"],
            mismatches["legend_code"],
            mismatches["uscs_symbol"],
            strict=True,
        )
    ) == [
        ("B-1", "FILL", "SC"),
        ("B-1", "CL", "CH"),
        ("B-2", "CL", "CH"),
        ("B-3", "FILL", "SC"),
        ("B-4", "CL", "CH"),
        ("B-6", "CL", "ML"),
    ]
    # Depths in ft, converted from the file's m (tolerance for the conversion).
    assert mismatches["depth"].tolist() == pytest.approx([1.5, 13, 13, 1.5, 13, 13])
    full = example_index.loc[mismatches.index]
    assert full["loca_id"].tolist() == mismatches["loca_id"].tolist()
    assert full["depth"].tolist() == mismatches["depth"].tolist()
    text = str(result)
    assert "Agree (same text): 2 of 8 rows with both values (25 %)." in text
    assert "12 rows have a legend_code but no uscs_symbol." in text
    assert "6 rows disagree:" in text


def test_mapping(example_index):
    # AC 3: FILL agrees with SC by the mapping; the CH and ML rows don't.
    result = ht.stats.crosstab(
        example_index, "legend_code", "uscs_symbol", agree=MAPPING
    )
    assert result.count_agreeing == 4
    assert result.count_compared == 8
    assert result.proportion_agreeing == 0.5
    assert result.mismatches["uscs_symbol"].tolist() == ["CH", "CH", "CH", "ML"]
    assert result.agree == {
        "CL": ["CL"],
        "FILL": ["SC", "SM", "GC"],
        "SP": ["SP", "SP-SM"],
    }
    assert "Agree (by the mapping): 4 of 8" in str(result)
    _add_up(result, len(example_index))


def test_mapping_to_nothing(example_index):
    # AC 3: [] agrees with nothing.
    result = ht.stats.crosstab(
        example_index,
        "legend_code",
        "uscs_symbol",
        agree={"CL": "CL", "FILL": [], "SP": []},
    )
    assert (result.count_agreeing, result.count_compared) == (2, 8)


def test_mapping_missing_a_class(example_index):
    # AC 3, AC 8: SP has no rows to compare, so only FILL is missing.
    with pytest.raises(HangtuError, match=r"'FILL' \(2 rows\).*with \[\]"):
        ht.stats.crosstab(
            example_index, "legend_code", "uscs_symbol", agree={"CL": "CL"}
        )


def test_spaces_and_case():
    # AC 6: "CL " and "cl" disagree with "CL"; spaces alone are blank.
    df = pd.DataFrame({"logged": ["CL", "CL ", "  ", "cl"], "lab": ["CL"] * 4})
    result = ht.stats.crosstab(df, "logged", "lab", agree="same")
    assert result.count_compared == 3
    assert result.count_agreeing == 1
    assert result.count_blank_in_rows == 1
    assert "1 row has a lab but no logged." in str(result)
    _add_up(result, 4)


def test_whole_numbers():
    # AC 7: integer and float codes agree as text, and so do the mapping's.
    df = pd.DataFrame({"code": [101, 101, 102], "other": [101.0, np.nan, 102.0]})
    same = ht.stats.crosstab(df, "code", "other", agree="same")
    assert (same.count_agreeing, same.count_compared) == (2, 2)
    mapped = ht.stats.crosstab(df, "code", "other", agree={101: "101", "102": [102]})
    assert (mapped.count_agreeing, mapped.count_compared) == (2, 2)
    assert mapped.agree == {"101": ["101"], "102": ["102"]}


@pytest.mark.parametrize("agree", [True, "equal", ["CL"], 1])
def test_agree_of_another_kind(agree):
    # AC 8.
    df = pd.DataFrame({"logged": ["CL"], "lab": ["CL"]})
    with pytest.raises(HangtuError, match=r'agree="same".*a mapping'):
        ht.stats.crosstab(df, "logged", "lab", agree=agree)


def test_nothing_compared():
    # AC 10: every row blank on one side, so the proportion is NaN (null).
    df = pd.DataFrame({"logged": ["CL", "SP"], "lab": [None, None]})
    result = ht.stats.crosstab(df, "logged", "lab", agree="same")
    assert result.count_compared == 0
    assert math.isnan(result.proportion_agreeing)
    assert json.loads(json.dumps(result.to_dict()))["proportion_agreeing"] is None
    assert "Agree (same text): no row has both values." in str(result)
    _add_up(result, 2)


def test_records_round_trip(example_index):
    # AC 10: the dict holds the listing, and rebuilds it.
    result = ht.stats.crosstab(
        example_index, "legend_code", "uscs_symbol", agree="same"
    )
    record = json.loads(json.dumps(result.to_dict()))
    rebuilt = pd.DataFrame(
        record["mismatch_values"],
        index=record["mismatch_index"],
        columns=record["mismatch_columns"],
    )
    pd.testing.assert_frame_equal(rebuilt, result.mismatches)


def test_index_labels_kept():
    # Decision 7: the input's own labels; a label not str or int as text.
    df = pd.DataFrame(
        {"logged": ["CL", "CL"], "lab": ["CL", "CH"]},
        index=pd.Index(["first", "second"]),
    )
    result = ht.stats.crosstab(df, "logged", "lab", agree="same")
    assert result.mismatches.index.tolist() == ["second"]
    dated = df.set_index(pd.DatetimeIndex(["2026-01-01", "2026-01-02"]))
    result = ht.stats.crosstab(dated, "logged", "lab", agree="same")
    assert result.mismatch_index == ("2026-01-02 00:00:00",)


def test_summary_shows_the_first_20():
    # Decision 9: 25 mismatches, 20 shown.
    df = pd.DataFrame({"logged": ["CL"] * 25, "lab": ["CH"] * 25})
    text = str(ht.stats.crosstab(df, "logged", "lab", agree="same"))
    assert "25 rows disagree:" in text
    assert text.splitlines()[-1] == ("… and 5 more: result.mismatches lists them all.")
    assert "  19" in text
    assert "  20 " not in text
