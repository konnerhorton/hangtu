"""CrosstabResult: frozen, the dict and the text (m15e-crosstab, AC 10)."""

import dataclasses
import json

import pandas as pd
import pytest

import hangtu as ht


@pytest.fixture
def result():
    df = pd.DataFrame(
        {"legend_code": ["CL", "CL", "SP"], "uscs_symbol": ["CL", None, "SP"]}
    )
    return ht.stats.crosstab(df, "legend_code", "uscs_symbol")


def test_frozen(result):
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.rows = "other"


def test_dict_is_json(result):
    record = json.loads(json.dumps(result.to_dict()))
    assert record["function"] == "crosstab"
    assert record["kind"] == "property"
    assert record["counts"] == {
        "CL": {"CL": 1, "SP": 0, "(blank)": 1},
        "SP": {"CL": 0, "SP": 1, "(blank)": 0},
    }
    assert record["agree"] is None


def test_text(result):
    assert str(result).splitlines() == [
        "legend_code × uscs_symbol",
        "legend_code  CL  SP  (blank)  (total)",
        "CL            1   0        1        2",
        "SP            0   1        0        1",
        "(total)       1   1        1        3",
        'No agreement counted: pass agree="same" if the two columns use one '
        "vocabulary, or a mapping of which pairs agree.",
    ]
    assert result._repr_html_().startswith("<pre>legend_code × uscs_symbol")
