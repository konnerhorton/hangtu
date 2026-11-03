"""RepresentativeResult (docs/work/m18b-representative-values.md, criterion 9)."""

import json

import pandas as pd

import hangtu as ht

COHESION = [27.0, 45.0, 47.0, 46.0, 4.5, 9.5]


def result(**kwargs):
    frame = ht.set_units(
        pd.DataFrame({"effective_cohesion": COHESION}), {"effective_cohesion": "kPa"}
    )
    return ht.stats.representative(
        frame,
        value="effective_cohesion",
        method="characteristic",
        side="low",
        distribution="normal",
        **kwargs,
    )


def test_to_dict_is_json_and_records_every_input():
    record = result(
        estimate="intermediate", scale_of_fluctuation=3.0, failure_length=10.0
    ).to_dict()
    json.dumps(record)
    assert record["kind"] == "parameter"
    expected = {
        "method": "characteristic",
        "side": "low",
        "distribution": "normal",
        "trend": None,
        "estimate": "intermediate",
        "coefficient_of_variation": None,
        "coefficient_of_variation_case": 2,
        "scale_of_fluctuation": 3.0,
        "failure_length": 10.0,
    }
    assert {name: record[name] for name in expected} == expected
    assert record["sensitivity_index"] == 0.3
    statistics = record["groups"][0]["statistics"]
    assert set(statistics) >= {
        "mean",
        "standard_deviation",
        "coefficient_of_variation",
        "quantile_factor",
        "statistical_coefficient",
        "sensitivity_index",
    }


def test_to_frame_has_value_and_its_units():
    frame = result(estimate="mean").to_frame()
    assert frame.loc[0, "value"] > 0
    assert frame.attrs["units"]["value"] == "kPa"
    assert frame.attrs["units"]["standard_deviation"] == "kPa"
    assert "quantile_factor" not in frame.attrs["units"]


def test_the_summary_names_the_view():
    text = str(result(estimate="mean", coefficient_of_variation=0.4))
    assert text.startswith("effective_cohesion (kPa)\n")
    assert (
        "characteristic, mean (Type A), V_X assumed 0.4 (Case 3), normal, low" in text
    )
    assert "k_n" in text
    assert result(estimate="mean")._repr_html_().startswith("<pre>")
