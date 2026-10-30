"""FitResult: frame, distribution, dict and text (m15c-fit.md, Decision 10)."""

import json
import math

import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError
from hangtu.plot._overlays import format_number

COLUMNS = [
    "geology_unit",
    "distribution",
    "rank",
    "count",
    "count_censored",
    "mean",
    "standard_deviation",
    "median",
    "percentile_5",
    "percentile_95",
    "parameters",
    "log_likelihood",
    "aicc",
    "delta_aicc",
    "akaike_weight",
    "anderson_darling_statistic",
    "anderson_darling_p_value",
    "probability_below_lower_bound",
    "probability_above_upper_bound",
    "count_at_least",
    "count_at_most",
    "count_non_plastic",
    "count_assumed",
    "count_range",
    "count_text",
    "count_blank",
]
NUMBERS = [
    "mean",
    "standard_deviation",
    "median",
    "percentile_5",
    "percentile_95",
    "log_likelihood",
    "aicc",
    "delta_aicc",
    "akaike_weight",
    "anderson_darling_statistic",
    "anderson_darling_p_value",
    "probability_below_lower_bound",
]


@pytest.fixture(scope="module")
def result():
    """One fit, shared: its bootstrap takes about 0.4 s."""
    df = pd.DataFrame(
        {
            "geology_unit": ["A"] * 5 + ["B"] * 6,
            "undrained_shear_strength": [10, 12, 15, 20, 23, 40, 41.5, 47, 55, 60, 90],
        }
    )
    df = ht.set_units(df, {"undrained_shear_strength": "kPa"})
    df.attrs["judgments"] = {"bulk_unit_weight": {"source": "judgments.yaml"}}
    with pytest.warns(UserWarning, match="fewer than 10"):
        return ht.stats.fit(df, value="undrained_shear_strength", by="geology_unit")


def test_frame_columns_ranked_within_each_group(result):
    # AC 11
    frame = result.to_frame()
    assert list(frame.columns) == COLUMNS
    for _, group in frame.groupby("geology_unit"):
        assert list(group["rank"]) == [1, 2, 3, 4]
        assert group["aicc"].is_monotonic_increasing
        assert group["akaike_weight"].sum() == pytest.approx(1)
    assert frame.attrs["units"] == dict.fromkeys(NUMBERS[:5], "kPa")


def test_parameters_read_with_their_units(result):
    frame = result.to_frame().set_index(["geology_unit", "distribution"])
    assert frame.loc[("A", "lognormal"), "parameters"] == (
        "median = 15.3 kPa, σ of ln x = 0.309"
    )
    assert frame.loc[("A", "normal"), "parameters"] == (
        "mean = 16.0 kPa, standard deviation = 4.86 kPa"
    )
    assert frame.loc[("A", "gamma"), "parameters"].startswith("shape = ")


def test_to_dict_is_json(result):
    record = result.to_dict()
    json.dumps(record)
    assert record["function"] == "fit"
    assert record["kind"] == "property"
    assert record["bounds"] == [0.0, None]
    assert record["groups"][0]["fits"][0]["anderson_darling_p_value"] > 0
    assert record["judgments"] == {"bulk_unit_weight": {"source": "judgments.yaml"}}


def test_distribution_is_the_fitted_scipy_distribution(result):
    lognormal = result.distribution("lognormal", group="A")
    assert lognormal.dist.name == "lognorm"
    assert lognormal.median() == pytest.approx(15.2618109, rel=1e-8)
    assert math.log(lognormal.median()) == pytest.approx(2.72535369, rel=1e-8)
    assert lognormal.std() > 0


def test_distribution_needs_a_group_with_several(result):
    with pytest.raises(HangtuError, match="name one with group=, from: A, B"):
        result.distribution("normal")
    with pytest.raises(HangtuError, match="no group 'C'"):
        result.distribution("normal", group="C")
    with pytest.raises(HangtuError, match="has no beta fit"):
        result.distribution("beta", group="A")


def test_text_shows_every_number_to_three_figures(result):
    text = str(result)
    assert text.startswith("undrained_shear_strength (kPa)\nA: 5 values")
    frame = result.to_frame()
    for name in NUMBERS:
        for value in frame[name]:
            assert format_number(float(value)) in text, name
    for parameters in frame["parameters"]:
        assert parameters in text
    assert "A²" in text
    assert "AD p" in text
    assert "P(< 0)" in text
    assert text.endswith("AICc compares fits within a group, never across groups.")
    assert result._repr_html_().startswith("<pre>undrained_shear_strength")
