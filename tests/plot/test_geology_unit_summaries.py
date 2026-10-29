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


def test_quartiles_of_one_to_ten_by_default():
    # Linear: P25 at position 1 + 9 x 0.25 = 3.25, P75 at 7.75.
    _, ax = ht.plot.geology_unit_comparison(frame(ONE_TO_TEN), "water_content")
    assert bars(ax) == [pytest.approx((3.25, 7.75))]
    assert centrals(ax) == [pytest.approx(5.5)]


def test_quartiles_of_six_values():
    _, ax = ht.plot.geology_unit_comparison(frame(SIX), "water_content")
    assert bars(ax) == [pytest.approx((4.0, 6.5))]
    assert centrals(ax) == [pytest.approx(4.5)]


def test_the_bar_is_describes_numbers():
    # AC 17
    values = [3.0, 8.0, 1.0, 9.5, 4.0, 4.0, 12.0]
    _, ax = ht.plot.geology_unit_comparison(frame(values), "water_content")
    row = ht.stats.describe(values, percentiles=(25, 75)).to_frame().iloc[0]
    assert bars(ax) == [pytest.approx((row["percentile_25"], row["percentile_75"]))]
    assert centrals(ax) == [pytest.approx(row["median"])]


def test_p10_to_p90_on_twenty_values():
    values = [float(v) for v in range(1, 21)]
    _, ax = ht.plot.geology_unit_comparison(
        frame(values), "water_content", percentiles=(10, 50, 90)
    )
    assert bars(ax) == [pytest.approx((2.9, 18.1))]


def test_p10_on_six_values_draws_points_and_says_why(points):
    _, ax = ht.plot.geology_unit_comparison(
        frame(SIX), "water_content", percentiles=(10, 50, 90)
    )
    assert bars(ax) == []
    assert len(points(ax)) == 6
    assert count_labels(ax) == ["n = 6 (no summary: p10 needs 10 values)"]


def test_box_quartiles_median_and_whiskers():
    _, ax = ht.plot.geology_unit_comparison(frame(SIX), "water_content", summary="box")
    (box,) = ax.patches
    # The quartiles are describe()'s: P25 4.0, P75 6.5.
    q = ht.stats.describe(SIX, percentiles=(25, 75)).to_frame().iloc[0]
    assert box.get_x() == pytest.approx(q["percentile_25"]) == 4.0
    assert box.get_width() == pytest.approx(q["percentile_75"] - 4.0) == 2.5
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


def test_a_right_legend_clears_the_count_labels():
    fig, ax = ht.plot.geology_unit_comparison(
        frame(ONE_TO_TEN), "water_content", legend="right"
    )
    fig.draw_without_rendering()
    renderer = fig.canvas.get_renderer()
    (label,) = [text for text in ax.texts if text.get_text().startswith("n =")]
    legend = ax.get_legend().get_window_extent(renderer)
    assert legend.x0 > label.get_window_extent(renderer).x1


# --- legend text -------------------------------------------------------------


@pytest.mark.parametrize(
    ("arguments", "text"),
    [
        ({}, f"Data p25{DASH}p75, p50"),
        ({"percentiles": (20, 50, 80)}, f"Data p20{DASH}p80, p50"),
        ({"summary": "box"}, "Data: quartiles, median, 1.5 IQR whiskers"),
    ],
)
def test_legend_names_the_summary(arguments, text):
    _, ax = ht.plot.geology_unit_comparison(frame(SIX), "water_content", **arguments)
    # A long entry wraps onto two lines (P00 §11); every word is kept.
    assert [" ".join(entry.split()) for entry in legend_texts(ax)] == [text, "Data"]


# --- errors -------------------------------------------------------------------


@pytest.mark.parametrize(
    "percentiles",
    [(10, 90), (90, 50, 10), (10, 50, 120), (-5, 50, 90), (0, 50, 100), "10,50,90"],
)
def test_bad_percentiles_are_an_error(percentiles):
    with pytest.raises(ht.HangtuError, match="three ascending numbers"):
        ht.plot.geology_unit_comparison(
            frame(SIX), "water_content", percentiles=percentiles
        )


@pytest.mark.parametrize(
    "plot", ["geology_unit_comparison", "geology_unit_comparisons"]
)
def test_percentile_method_was_removed(plot):
    values = "water_content" if plot == "geology_unit_comparison" else ["water_content"]
    with pytest.raises(ht.HangtuError, match="Hyndman & Fan \\(1996\\) definition 7"):
        getattr(ht.plot, plot)(frame(SIX), values, percentile_method="hazen")


def test_a_unit_mixing_sources_draws_points_only(points):
    df = frame(ONE_TO_TEN).assign(source=["lab"] * 5 + ["field"] * 5)
    _, ax = ht.plot.geology_unit_comparison(df, "water_content")
    assert bars(ax) == []
    assert len(points(ax)) == 10
    assert count_labels(ax) == ["n = 10 (mixes sources)"]


def test_assumed_values_are_drawn_and_left_out_of_the_summary(points):
    df = pd.DataFrame(
        {
            "geology_unit": ["A"] * 6,
            "particle_density": [2.60, 2.65, 2.70, 2.75, 2.80, 3.50],
            "particle_density_assumed": [False] * 5 + [True],
        }
    )
    df = ht.set_units(df, {"particle_density": "Mg/m3"})
    _, ax = ht.plot.geology_unit_comparison(df, "particle_density", display_units="SI")
    assert len(points(ax)) == 6
    assert centrals(ax) == [pytest.approx(2.70)]
    assert ax.ags_notes["assumed_excluded"] == 1


@pytest.mark.parametrize("count", [0, -1, 2.5, True])
def test_bad_summary_min_count_is_an_error(count):
    with pytest.raises(ht.HangtuError, match="at least 1"):
        ht.plot.geology_unit_comparison(
            frame(SIX), "water_content", summary_min_count=count
        )


def test_unknown_summary_is_an_error():
    with pytest.raises(ht.HangtuError, match='"percentiles", "box" or None'):
        ht.plot.geology_unit_comparison(frame(SIX), "water_content", summary="mean")
