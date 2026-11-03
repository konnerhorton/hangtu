"""RepresentativeResult (docs/work/m18b-representative-values.md, criterion 9)."""

import json
import math

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError

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


def test_percentile_and_standard_deviations_are_recorded_and_named():
    frame = ht.set_units(
        pd.DataFrame({"effective_cohesion": COHESION}), {"effective_cohesion": "kPa"}
    )
    common = {"value": "effective_cohesion", "side": "low", "distribution": "normal"}
    low = ht.stats.representative(frame, method="percentile", percentile=5, **common)
    record = low.to_dict()
    json.dumps(record)
    assert (record["percentile"], record["standard_deviations"]) == (5, None)
    assert record["coefficient_of_variation_case"] is None
    assert "percentile 5 of the fitted distribution, normal, low" in str(low)
    k = ht.stats.representative(
        frame, method="standard_deviations", standard_deviations=0.5, **common
    )
    assert k.to_dict()["standard_deviations"] == 0.5
    assert "mean - 0.5 standard deviations, normal, low" in str(k)


# --- Criterion 8: the design_lines frame -------------------------------------------


def profile():
    """Clay from 2 to 10 m, Sand from 12 to 16 m: s_u in kPa."""
    frame = pd.DataFrame(
        {
            "geology_unit": ["Clay"] * 5 + ["Sand"] * 3,
            "depth": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0],
            "undrained_shear_strength": [20.0, 26.0, 29.0, 37.0, 40.0, 60, 70, 65],
        }
    )
    return ht.set_units(frame, {"depth": "m", "undrained_shear_strength": "kPa"})


def by_unit(data=None, **kwargs):
    kwargs = {
        "method": "characteristic",
        "estimate": "mean",
        "side": "low",
        "distribution": "normal",
        **kwargs,
    }
    return ht.stats.representative(
        profile() if data is None else data,
        value="undrained_shear_strength",
        by="geology_unit",
        **kwargs,
    )


def test_a_constant_is_two_points_over_the_groups_depths():
    found = by_unit()
    lines = found.design_lines()
    assert list(lines.columns) == ["label", "depth", "value"]
    clay = lines[lines["label"] == "Clay: characteristic, mean, low"]
    assert clay["depth"].tolist() == [2.0, 10.0]
    assert clay["value"].tolist() == [found.groups[0]["value"]] * 2
    sand = lines[lines["label"].str.startswith("Sand")]
    assert sand["depth"].tolist() == [12.0, 16.0]
    assert lines.attrs["units"] == {"depth": "m", "value": "kPa"}


def test_a_trend_is_fifty_points_over_the_groups_depths():
    lines = by_unit(trend="depth", estimate="fractile").design_lines()
    clay = lines[lines["label"] == "Clay: characteristic, fractile, low"]
    assert len(clay) == 50
    assert (clay["depth"].min(), clay["depth"].max()) == (2.0, 10.0)
    assert clay["value"].iloc[0] == pytest.approx(16.3187, abs=5e-5)
    assert clay["value"].iloc[-1] == pytest.approx(36.7187, abs=5e-5)


def test_mean_adds_the_mean_or_median_line():
    lines = by_unit(trend="depth").design_lines(mean=True)
    clay = lines[lines["label"] == "Clay: mean"]
    assert len(clay) == 50
    assert clay["value"].iloc[0] == pytest.approx(15.1 + 2.55 * 2, rel=1e-9)
    constant = by_unit(distribution="lognormal").design_lines(mean=True)
    median = constant[constant["label"] == "Clay: median"]
    logs = np.log([20.0, 26.0, 29.0, 37.0, 40.0])
    assert median["value"].tolist() == pytest.approx([math.exp(logs.mean())] * 2)


def test_the_labels_name_each_view():
    percentile = by_unit(method="percentile", percentile=5, estimate=None)
    assert percentile.design_lines()["label"].iloc[0] == "Clay: percentile 5, low"
    deviations = by_unit(
        method="standard_deviations", standard_deviations=0.5, estimate=None
    )
    assert (
        deviations.design_lines()["label"].iloc[0]
        == "Clay: 0.5 standard deviations, low"
    )


def test_a_group_with_no_value_has_no_line():
    frame = profile().iloc[:6]
    lines = by_unit(frame).design_lines()
    assert set(lines["label"]) == {"Clay: characteristic, mean, low"}


def test_elevation_is_used_when_there_is_no_depth():
    frame = profile().rename(columns={"depth": "elevation"})
    frame["elevation"] = 100.0 - frame["elevation"]
    frame = ht.set_units(frame, {"elevation": "m"})
    lines = by_unit(frame).design_lines()
    assert list(lines.columns) == ["label", "elevation", "value"]
    assert lines["elevation"].tolist()[:2] == [98.0, 90.0]


def test_design_lines_need_a_depth_or_elevation():
    with pytest.raises(HangtuError, match="no 'depth' or 'elevation' column"):
        result(estimate="mean").design_lines()
