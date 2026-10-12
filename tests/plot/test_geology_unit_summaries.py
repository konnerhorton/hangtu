"""P07 summaries: percentile bars, boxes, counts and the legend (P07 §4, §7, §12)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht

ONE_TO_TEN = [float(v) for v in range(1, 11)]
SIX = [2.0, 4.0, 4.0, 5.0, 7.0, 9.0]
DASH = "\N{EN DASH}"


def frame(values, unit="A"):
    return pd.DataFrame({"geology_unit": [unit] * len(values), "water_content": values})


def bars(ax):
    """Horizontal two-point lines (summary bars and whisker halves), as (x0, x1)."""
    found = []
    for line in ax.lines:
        x, y = (np.asarray(a, dtype=float) for a in line.get_data())
        if line.get_marker() in ("None", "none", "") and len(x) == 2 and y[0] == y[1]:
            found.append(tuple(x))
    return found


def centrals(ax):
    return [float(line.get_xdata()[0]) for line in ax.lines if line.get_marker() == "o"]


def count_labels(ax):
    return [text.get_text() for text in ax.texts if text.get_text().startswith("n =")]


def legend_texts(ax):
    legend = ax.get_legend()
    return [] if legend is None else [text.get_text() for text in legend.get_texts()]


# --- golden values (P07 §12) -------------------------------------------------


def test_linear_percentiles_of_one_to_ten():
    _, ax = ht.plot.geology_unit_comparison(frame(ONE_TO_TEN), "water_content")
    assert bars(ax) == [pytest.approx((1.9, 9.1))]
    assert centrals(ax) == [pytest.approx(5.5)]


def test_linear_percentiles_of_six_values():
    _, ax = ht.plot.geology_unit_comparison(frame(SIX), "water_content")
    assert bars(ax) == [pytest.approx((3.0, 8.0))]
    assert centrals(ax) == [pytest.approx(4.5)]


def test_hazen_percentiles_of_six_values():
    _, ax = ht.plot.geology_unit_comparison(
        frame(SIX), "water_content", percentile_method="hazen"
    )
    assert bars(ax) == [pytest.approx((2.2, 8.8))]
    assert centrals(ax) == [pytest.approx(4.5)]


def test_other_percentiles():
    _, ax = ht.plot.geology_unit_comparison(
        frame(ONE_TO_TEN), "water_content", percentiles=(25, 50, 75)
    )
    assert bars(ax) == [pytest.approx((3.25, 7.75))]


def test_box_quartiles_median_and_whiskers():
    _, ax = ht.plot.geology_unit_comparison(frame(SIX), "water_content", summary="box")
    (box,) = ax.patches
    assert box.get_x() == pytest.approx(4.0)
    assert box.get_width() == pytest.approx(2.5)
    assert box.get_y() == pytest.approx(-0.15)
    assert box.get_height() == pytest.approx(0.3)
    whiskers = [
        tuple(line.get_xdata())
        for line in ax.lines
        if len(line.get_xdata()) == 5 and line.get_marker() in ("None", "")
    ]
    assert whiskers == [pytest.approx((2.0, 4.0, np.nan, 6.5, 9.0), nan_ok=True)]
    medians = [
        line.get_xdata()[0]
        for line in ax.lines
        if len(line.get_xdata()) == 2 and line.get_xdata()[0] == line.get_xdata()[1]
    ]
    assert medians == [pytest.approx(4.5)]


def test_box_whiskers_stop_within_one_and_a_half_iqr():
    values = [*ONE_TO_TEN, 40.0]  # q1 3.5, q3 8.5, IQR 5: reach 1 to 16
    _, ax = ht.plot.geology_unit_comparison(
        frame(values), "water_content", summary="box"
    )
    (whisker,) = [line for line in ax.lines if len(line.get_xdata()) == 5]
    assert whisker.get_xdata()[[0, 4]] == pytest.approx([1.0, 10.0])


def test_equal_values_give_a_zero_length_bar_with_caps():
    _, ax = ht.plot.geology_unit_comparison(frame([12.0] * 6), "water_content")
    assert bars(ax) == [pytest.approx((12.0, 12.0))]
    caps = [line for line in ax.lines if len(line.get_xdata()) == 6]
    assert caps[0].get_xdata()[[0, 3]] == pytest.approx([12.0, 12.0])


def test_bars_sit_on_each_rows_center_line():
    df = pd.concat([frame(ONE_TO_TEN, "A"), frame(SIX, "B")], ignore_index=True)
    _, ax = ht.plot.geology_unit_comparison(df, "water_content")
    rows = sorted(
        float(line.get_ydata()[0]) for line in ax.lines if line.get_marker() == "o"
    )
    assert rows == [0.0, 1.0]


# --- small samples and counts -------------------------------------------------


def test_too_few_values_get_points_and_a_note_but_no_summary(points):
    _, ax = ht.plot.geology_unit_comparison(frame(SIX[:4]), "water_content")
    assert bars(ax) == []
    assert len(points(ax)) == 4
    assert count_labels(ax) == ["n = 4 (no summary)"]
    assert "Data" in legend_texts(ax)
    assert not any(text.startswith("Data p") for text in legend_texts(ax))


def test_summary_min_count_from_the_argument_and_the_settings():
    _, ax = ht.plot.geology_unit_comparison(
        frame(SIX[:4]), "water_content", summary_min_count=4
    )
    assert len(bars(ax)) == 1
    with ht.settings.override(summary_min_count=7):
        _, ax = ht.plot.geology_unit_comparison(frame(SIX), "water_content")
    assert bars(ax) == []
    assert count_labels(ax) == ["n = 6 (no summary)"]


def test_counts_sit_outside_the_right_edge_level_with_their_rows():
    df = pd.concat([frame(ONE_TO_TEN, "A"), frame(SIX, "B")], ignore_index=True)
    _, ax = ht.plot.geology_unit_comparison(df, "water_content")
    labels = [text for text in ax.texts if text.get_text().startswith("n =")]
    assert [label.get_text() for label in labels] == ["n = 10", "n = 6"]
    assert [label.xy for label in labels] == [(1.0, 0), (1.0, 1)]


def test_summary_none_draws_points_and_plain_counts(points):
    _, ax = ht.plot.geology_unit_comparison(frame(SIX), "water_content", summary=None)
    assert bars(ax) == []
    assert count_labels(ax) == ["n = 6"]


def test_legend_and_footnote_clear_the_count_labels():
    fig, ax = ht.plot.geology_unit_comparison(frame(ONE_TO_TEN), "water_content")
    fig.draw_without_rendering()
    renderer = fig.canvas.get_renderer()
    (label,) = [text for text in ax.texts if text.get_text().startswith("n =")]
    legend = ax.get_legend().get_window_extent(renderer)
    assert legend.x0 > label.get_window_extent(renderer).x1


# --- legend text -------------------------------------------------------------


@pytest.mark.parametrize(
    ("arguments", "text"),
    [
        ({}, f"Data p10{DASH}p90, p50"),
        ({"percentiles": (5, 50, 95)}, f"Data p5{DASH}p95, p50"),
        ({"percentile_method": "hazen"}, f"Data p10{DASH}p90, p50 (Hazen)"),
        (
            {"percentile_method": "median_unbiased"},
            f"Data p10{DASH}p90, p50 (Median unbiased)",
        ),
        ({"summary": "box"}, "Data: quartiles, median, 1.5 IQR whiskers"),
    ],
)
def test_legend_names_the_summary(arguments, text):
    _, ax = ht.plot.geology_unit_comparison(frame(SIX), "water_content", **arguments)
    assert legend_texts(ax) == [text, "Data"]


# --- errors -------------------------------------------------------------------


@pytest.mark.parametrize(
    "percentiles", [(10, 90), (90, 50, 10), (10, 50, 120), (-5, 50, 90), "10,50,90"]
)
def test_bad_percentiles_are_an_error(percentiles):
    with pytest.raises(ht.HangtuError, match="three ascending numbers"):
        ht.plot.geology_unit_comparison(
            frame(SIX), "water_content", percentiles=percentiles
        )


def test_unknown_percentile_method_lists_numpys_methods():
    with pytest.raises(ht.HangtuError, match="hazen, weibull, linear"):
        ht.plot.geology_unit_comparison(
            frame(SIX), "water_content", percentile_method="tukey"
        )


@pytest.mark.parametrize("count", [0, -1, 2.5, True])
def test_bad_summary_min_count_is_an_error(count):
    with pytest.raises(ht.HangtuError, match="at least 1"):
        ht.plot.geology_unit_comparison(
            frame(SIX), "water_content", summary_min_count=count
        )


def test_unknown_summary_is_an_error():
    with pytest.raises(ht.HangtuError, match='"percentiles", "box" or None'):
        ht.plot.geology_unit_comparison(frame(SIX), "water_content", summary="mean")
