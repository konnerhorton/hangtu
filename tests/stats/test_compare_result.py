"""CompareResult: the frame, the dict and the text (m15d-compare, AC 14)."""

import json

import numpy as np
import pytest

import hangtu as ht
from hangtu.plot._overlays import format_number

COLUMNS = [
    "group_1",
    "group_2",
    "count_1",
    "count_2",
    "mean_1",
    "mean_2",
    "standard_deviation_1",
    "standard_deviation_2",
    "difference",
    "difference_lower",
    "difference_upper",
    "welch_t_statistic",
    "welch_degrees_of_freedom",
    "welch_p_value",
    "probability_of_superiority",
    "probability_of_superiority_lower",
    "probability_of_superiority_upper",
    "brunner_munzel_statistic",
    "brunner_munzel_degrees_of_freedom",
    "brunner_munzel_p_value",
    "brunner_munzel_method",
    "significance_level",
    "confidence_level",
]
COUNTS = [
    "count_at_least",
    "count_at_most",
    "count_non_plastic",
    "count_assumed",
    "count_range",
    "count_text",
    "count_blank",
]


@pytest.fixture
def result(helsel):
    return ht.stats.compare(*helsel, units="kPa", significance_level=0.05)


def test_frame_columns(result):
    # AC 14: Decision 11's columns, then each count for each group.
    frame = result.to_frame()
    assert len(frame) == 1
    counts = [f"{name}_{i}" for name in COUNTS for i in (1, 2)]
    assert frame.columns.tolist() == [*COLUMNS, *counts]
    assert frame.attrs["units"] == dict.fromkeys(
        [
            "mean_1",
            "mean_2",
            "standard_deviation_1",
            "standard_deviation_2",
            "difference",
            "difference_lower",
            "difference_upper",
        ],
        "kPa",
    )


def test_log_frame_names_the_geometric_statistics(helsel):
    frame = ht.stats.compare(*helsel, significance_level=0.05, log=True).to_frame()
    assert frame.columns[2:10].tolist() == [
        "count_1",
        "count_2",
        "geometric_mean_1",
        "geometric_mean_2",
        "geometric_standard_deviation_1",
        "geometric_standard_deviation_2",
        "ratio",
        "ratio_lower",
    ]


def test_kind_and_function(result):
    assert result.kind == "property"
    assert result.function == "compare"


def test_to_dict_is_json(result):
    # AC 14
    data = result.to_dict()
    text = json.dumps(data)
    assert data["significance_level"] == 0.05
    assert data["welch"]["difference"] == pytest.approx(0.028)
    assert "NaN" not in text


def test_text_shows_every_number_of_the_frame(result):
    # AC 14: every number in the frame, to 3 significant figures.
    text = str(result)
    row = result.to_frame().iloc[0]
    for name, value in row.items():
        if isinstance(value, str) or value is None:
            assert value is None or value in text
            continue
        if name.startswith("count_") and name not in ("count_1", "count_2"):
            continue
        if isinstance(value, float) and np.isnan(value):
            continue
        if name in ("significance_level", "confidence_level"):
            # Levels read as written: "Significance level 0.05", "95 % interval".
            assert f"{value:g}" in text or f"{value * 100:g} %" in text
            continue
        shown = str(int(value)) if name.startswith("count") else format_number(value)
        assert shown in text, name
    assert text.splitlines()[0] == "Values (kPa)"
    assert "Difference in means, first - second: 0.0280 kPa; 95 % interval" in text


def test_repr_html_escapes_the_text(result):
    assert result._repr_html_().startswith("<pre>Values (kPa)")
