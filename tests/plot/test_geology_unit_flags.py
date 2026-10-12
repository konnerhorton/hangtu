"""P07 out-of-range and flagged values, reference lines and notes (P07 §3, §7, §8)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht

ONE_TO_TEN = [float(v) for v in range(1, 11)]


def frame(values, unit="A", **columns):
    data = {"geology_unit": [unit] * len(values), "consistency_index": values}
    return pd.DataFrame({**data, **columns})


def central(ax):
    (line,) = [line for line in ax.lines if line.get_marker() == "o"]
    return float(line.get_xdata()[0])


def count_label(ax):
    (label,) = [text for text in ax.texts if text.get_text().startswith("n =")]
    return label


# --- fixed limits -------------------------------------------------------------


def test_values_beyond_xlim_are_drawn_at_the_edge_and_counted(points):
    _, ax = ht.plot.geology_unit_comparison(
        frame([*ONE_TO_TEN, -4.0, 25.0]), "consistency_index", xlim=(0, 12)
    )
    assert ax.ags_notes == {"beyond_limit": 2}
    edges = [
        c
        for c in ax.collections
        if c.get_facecolor().size == 0 and len(c.get_offsets())
    ]
    assert sorted(float(x) for c in edges for x, _ in c.get_offsets()) == [0.0, 12.0]


def test_the_summary_uses_the_true_values_beyond_xlim():
    values = [*ONE_TO_TEN[:9], 100.0]
    _, ax = ht.plot.geology_unit_comparison(
        frame(values), "consistency_index", xlim=(0, 12), percentiles=(10, 90, 100)
    )
    assert central(ax) == pytest.approx(np.percentile(values, 90))


def test_a_bar_past_the_limit_is_cut_at_the_edge():
    fig, ax = ht.plot.geology_unit_comparison(
        frame([*ONE_TO_TEN, 30.0, 40.0]), "consistency_index", xlim=(0, 8)
    )
    fig.draw_without_rendering()
    (bar,) = [
        line
        for line in ax.lines
        if len(line.get_xdata()) == 2 and line.get_marker() in ("None", "")
    ]
    assert bar.get_clip_on()
    assert bar.get_xdata()[1] > 8


def test_count_labels_clear_an_arrow_at_the_right_edge():
    _, ax = ht.plot.geology_unit_comparison(
        frame(ONE_TO_TEN), "consistency_index", xlim=(0, 12)
    )
    plain = count_label(ax).xyann[0]
    _, ax = ht.plot.geology_unit_comparison(
        frame([*ONE_TO_TEN, 25.0]), "consistency_index", xlim=(0, 12)
    )
    assert count_label(ax).xyann[0] > plain + 10


def test_bad_xlim_is_an_error():
    with pytest.raises(ht.HangtuError, match="xlim must be"):
        ht.plot.geology_unit_comparison(
            frame(ONE_TO_TEN), "consistency_index", xlim=(5, 5)
        )


# --- qualifiers ---------------------------------------------------------------


def test_qualified_values_are_carets_counted_and_summarized():
    qualifiers = ["<", "", "", "", "", "", "", "", ">", ">"]
    _, ax = ht.plot.geology_unit_comparison(
        frame(ONE_TO_TEN, qualifier=qualifiers), "consistency_index"
    )
    markers = {
        c.get_label(): len(c.get_offsets())
        for c in ax.collections
        if len(c.get_offsets())
    }
    assert markers == {"_A": 7, "_A <": 1, "_A >": 2}
    assert ax.ags_notes == {"less_than": 1, "greater_than": 2}
    assert central(ax) == pytest.approx(5.5)
    texts = [text.get_text() for text in ax.get_legend().get_texts()]
    assert texts[-2:] == ["less than (1)", "greater than (2)"]


def test_bad_qualifier_is_an_error():
    with pytest.raises(ht.ColumnError, match="'qualifier'"):
        ht.plot.geology_unit_comparison(
            frame(ONE_TO_TEN, qualifier=["~"] * 10), "consistency_index"
        )


# --- non-plastic ----------------------------------------------------------------


def test_non_plastic_rows_are_counted_not_drawn_or_summarized(points):
    values = [*ONE_TO_TEN, np.nan, np.nan]
    flags = [False] * 10 + [True, True]
    _, ax = ht.plot.geology_unit_comparison(
        frame(values, non_plastic=flags), "consistency_index"
    )
    assert ax.ags_notes == {"non_plastic": 2}
    assert len(points(ax)) == 10
    assert count_label(ax).get_text() == "n = 10"


def test_a_value_flagged_non_plastic_is_left_out():
    flags = [True] + [False] * 9
    _, ax = ht.plot.geology_unit_comparison(
        frame(ONE_TO_TEN, non_plastic=flags), "consistency_index"
    )
    assert count_label(ax).get_text() == "n = 9"
    assert central(ax) == pytest.approx(6.0)


def test_non_plastic_only_applies_to_atterberg_values(points):
    df = pd.DataFrame(
        {
            "geology_unit": ["A"] * 6,
            "water_content": [20.0, 21.0, 22.0, 23.0, 24.0, 25.0],
            "plasticity_index": [np.nan, 8.0, 9.0, 10.0, 11.0, 12.0],
            "non_plastic": [True, False, False, False, False, False],
        }
    )
    _, ax = ht.plot.geology_unit_comparison(df, "water_content")
    assert ax.ags_notes == {}
    assert len(points(ax)) == 6
    _, ax = ht.plot.geology_unit_comparison(df, "plasticity_index")
    assert ax.ags_notes == {"non_plastic": 1}


def test_non_plastic_must_be_true_or_false():
    with pytest.raises(ht.ColumnError, match="'non_plastic'"):
        ht.plot.geology_unit_comparison(
            frame(ONE_TO_TEN, non_plastic=["NP"] * 10), "consistency_index"
        )


# --- reference lines and notes ------------------------------------------------


def test_reference_line_given_in_psf_is_drawn_in_kpa(comparison):
    _, ax = ht.plot.geology_unit_comparison(
        comparison(),
        "undrained_shear_strength",
        reference_lines=[("2000 psf", "design")],
        display_units="SI",
    )
    (line,) = [line for line in ax.lines if line.get_linestyle() == ":"]
    assert line.get_xdata()[0] == pytest.approx(95.76, abs=0.01)
    assert "design" in [text.get_text() for text in ax.texts]


def test_note_is_written_inside_the_axes():
    _, ax = ht.plot.geology_unit_comparison(
        frame(ONE_TO_TEN), "consistency_index", note="Phase 2 data"
    )
    assert "Phase 2 data" in [text.get_text() for text in ax.texts]


def test_draw_order_puts_summaries_over_points_over_the_baseline():
    baseline = pd.DataFrame({"geology_unit": ["A"], "low": [2.0], "high": [8.0]})
    _, ax = ht.plot.geology_unit_comparison(
        frame(ONE_TO_TEN), "consistency_index", baseline=baseline
    )
    points = max(c.get_zorder() for c in ax.collections)
    baseline_z = min(line.get_zorder() for line in ax.lines)
    summary_z = max(line.get_zorder() for line in ax.lines)
    assert baseline_z < points < summary_z
