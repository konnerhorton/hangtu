"""CompareGroupsResult: the pairs, overall and groups frames (m15d, Decision 11)."""

import json

import pytest

from hangtu.stats import CompareGroupsResult

COUNTS = dict.fromkeys(
    [
        "count_at_least",
        "count_at_most",
        "count_non_plastic",
        "count_assumed",
        "count_range",
        "count_text",
        "count_blank",
    ],
    0,
)


def _group(label, count, mean, deviation, reason=None):
    return {
        "label": label,
        "key": {"geology_unit": label},
        "statistics": {
            "count": count,
            "mean": mean,
            "standard_deviation": deviation,
        },
        "counts": dict(COUNTS),
        "text": {},
        "sources": {},
        "reason": reason,
    }


@pytest.fixture
def result():
    return CompareGroupsResult(
        kind="property",
        function="compare_groups",
        value="undrained_shear_strength",
        unit="kPa",
        notes=("A note.",),
        judgments={},
        hangtu_version="0",
        by=("geology_unit",),
        groups=(
            _group("A", 5, 17.4, 3.97),
            _group("B", 6, 33.8, 7.52),
            _group("D", 1, 50.0, float("nan"), "fewer than 2 values (1)"),
        ),
        log=False,
        pooled=(),
        include_assumed=False,
        significance_level=0.05,
        confidence_level=0.95,
        significance_level_source="argument",
        overall_tests={
            "welch_f_statistic": 9.5,
            "welch_degrees_of_freedom_numerator": 1,
            "welch_degrees_of_freedom_denominator": 7.5,
            "welch_p_value": 0.016,
            "kruskal_wallis_statistic": 6.5,
            "kruskal_wallis_degrees_of_freedom": 1,
            "kruskal_wallis_p_value": 0.011,
        },
        pairs=(
            {
                "group_1": "A",
                "group_2": "B",
                "difference": -16.4,
                "difference_lower": -26.6,
                "difference_upper": -6.25,
                "games_howell_p_value": 0.016,
                "dunn_z_statistic": -2.5,
                "dunn_p_value": 0.012,
            },
        ),
    )


def test_pairs_frame(result):
    frame = result.to_frame()
    assert frame.columns.tolist() == [
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
        "games_howell_p_value",
        "dunn_z_statistic",
        "dunn_p_value",
        "significance_level",
        "confidence_level",
    ]
    row = frame.iloc[0]
    assert (row["count_1"], row["mean_2"]) == (5, 33.8)
    assert frame.attrs["units"]["difference_lower"] == "kPa"
    assert frame.attrs["units"]["mean_1"] == "kPa"
    assert "count_1" not in frame.attrs["units"]


def test_overall_frame(result):
    row = result.overall().iloc[0]
    assert row["welch_f_statistic"] == 9.5
    assert row["kruskal_wallis_degrees_of_freedom"] == 1
    assert row["significance_level"] == 0.05


def test_groups_frame_keeps_a_group_left_out(result):
    frame = result.groups_frame()
    assert frame["geology_unit"].tolist() == ["A", "B", "D"]
    assert frame["reason_not_tested"].tolist()[2] == "fewer than 2 values (1)"
    assert frame["count_blank"].tolist() == [0, 0, 0]


def test_to_dict_is_json(result):
    data = result.to_dict()
    json.dumps(data)
    assert data["groups"][2]["statistics"]["standard_deviation"] is None


def test_text(result):
    text = str(result)
    assert text.splitlines()[0] == "undrained_shear_strength (kPa)"
    assert "Welch's ANOVA: F = 9.50, df = 1 and 7.50, p = 0.0160" in text
    assert "Kruskal-Wallis: H = 6.50, df = 1, p = 0.0110" in text
    assert "Pairs, 95 % intervals, family-wise p-values (kPa):" in text
    assert "A - B" in text and "-26.6" in text
    assert text.endswith("Significance level 0.05 (argument)\nA note.")
