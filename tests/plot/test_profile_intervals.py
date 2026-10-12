"""P01 test intervals and qualified values (P01 §3, §7, §11, §12)."""

from functools import partial

import numpy as np
import pandas as pd
import pytest
from matplotlib.colors import to_rgba

import hangtu as ht

TOPS = {"depth_top": [4.0, 9.0, 10.0, 18.0], "depth_base": [6.0, 11.0, 20.0, 30.0]}


def interval_frame(frame, **columns):
    df = frame(**{**TOPS, **columns})
    declared = {column: "ft" for column in TOPS if column in df}
    return ht.set_units(df, declared)


def bars(ax):
    """Each interval drawn, as (x, top, base), sorted."""
    found = []
    for line in ax.lines:
        xs, ys = line.get_xdata(), line.get_ydata()
        for i in range(0, len(xs), 3):
            found.append((xs[i], ys[i], ys[i + 1]))
    return sorted(found)


def caret_tip(collection):
    """The x of the vertex on the marker's axis: negative points left."""
    vertices = collection.get_paths()[0].vertices
    return vertices[np.abs(vertices[:, 1]) < 1e-9, 0]


# --- intervals ------------------------------------------------------------------


def test_interval_bounds_convert_to_elevation(frame):
    # P01 §12: top 10.0 ft, base 20.0 ft, GL 120.0 ft -> 110.0 to 100.0 ft.
    _, ax = ht.plot.profile(interval_frame(frame), "undrained_shear_strength")
    assert (1500.0, 110.0, 100.0) in bars(ax)
    assert len(bars(ax)) == 4


def test_intervals_against_depth(frame):
    _, ax = ht.plot.profile(
        interval_frame(frame), "undrained_shear_strength", vs="depth"
    )
    assert bars(ax) == [
        (500.0, 4.0, 6.0),
        (1000.0, 9.0, 11.0),
        (1500.0, 10.0, 20.0),
        (2000.0, 18.0, 30.0),
    ]


def test_intervals_in_si(frame):
    _, ax = ht.plot.profile(
        interval_frame(frame), "undrained_shear_strength", display_units="SI"
    )
    x, top, base = bars(ax)[2]
    assert (x, top, base) == pytest.approx(
        (71.82, 110.0 * 0.3048, 100.0 * 0.3048), rel=1e-4
    )


def test_each_hole_uses_its_own_ground_level(frame):
    df = interval_frame(frame, ground_level=[120.0, 120.0, 100.0, 100.0])
    _, ax = ht.plot.profile(df, "undrained_shear_strength")
    assert (1500.0, 90.0, 80.0) in bars(ax)


def test_ground_level_can_come_from_elevation_and_depth(frame):
    df = interval_frame(frame, elevation=[115.0, 110.0, 105.0, 100.0])
    df = ht.set_units(df.drop(columns="ground_level"), {"elevation": "ft"})
    _, ax = ht.plot.profile(df, "undrained_shear_strength")
    assert (1500.0, 110.0, 100.0) in bars(ax)


def test_intervals_count_toward_the_vertical_limits(frame):
    _, ax = ht.plot.profile(
        interval_frame(frame), "undrained_shear_strength", vs="depth"
    )
    assert ax.get_ylim() == (30.0, 0.0)


def test_intervals_are_the_marker_color(frame):
    _, ax = ht.plot.profile(interval_frame(frame), "undrained_shear_strength")
    for line in ax.lines:
        unit = "Fill" if line.get_xdata()[0] < 1200 else "Clay"
        (points,) = [c for c in ax.collections if c.get_label() == unit]
        assert to_rgba(line.get_color()) == tuple(points.get_facecolor()[0])
    assert {line.get_solid_capstyle() for line in ax.lines} == {"round"}
    assert {line.get_linewidth() for line in ax.lines} == {1.0}


def test_a_swapped_row_warns_and_is_not_drawn(frame, points):
    df = interval_frame(frame, depth_top=[4.0, 12.0, 10.0, 18.0])
    with pytest.warns(UserWarning, match="Rows 1 have depth_top below depth_base"):
        _, ax = ht.plot.profile(df, "undrained_shear_strength")
    assert len(bars(ax)) == 3
    assert len(points(ax)) == 4


def test_a_row_without_bounds_has_no_bar(frame):
    df = interval_frame(frame, depth_top=[4.0, np.nan, 10.0, 18.0])
    _, ax = ht.plot.profile(df, "undrained_shear_strength")
    assert len(bars(ax)) == 3


def test_intervals_false_draws_none(frame):
    _, ax = ht.plot.profile(
        interval_frame(frame), "undrained_shear_strength", intervals=False
    )
    assert bars(ax) == []


def test_intervals_true_without_the_columns_is_an_error(frame):
    with pytest.raises(ht.ColumnError, match="'depth_top' and 'depth_base'"):
        ht.plot.profile(frame(), "undrained_shear_strength", intervals=True)


def test_bad_intervals_value_is_an_error(frame):
    with pytest.raises(ht.HangtuError, match="intervals must be"):
        ht.plot.profile(frame(), "undrained_shear_strength", intervals="yes")


def test_elevation_without_ground_levels_warns_and_skips_bars(frame, points):
    df = interval_frame(frame, elevation=[115.0, 110.0, 105.0, 100.0])
    df = ht.set_units(df.drop(columns=["ground_level", "depth"]), {"elevation": "ft"})
    with pytest.warns(UserWarning, match="Test intervals aren't drawn"):
        _, ax = ht.plot.profile(df, "undrained_shear_strength")
    assert bars(ax) == []
    assert len(points(ax)) == 4


def test_no_bar_for_a_value_at_the_edge(frame):
    _, ax = ht.plot.profile(
        interval_frame(frame), "undrained_shear_strength", xlim=(0, 1800)
    )
    assert len(bars(ax)) == 3
    assert ax.ags_notes == {"beyond_limit": 1}


# --- qualifiers -----------------------------------------------------------------


def test_qualified_values_are_carets_pointing_the_right_way(frame):
    df = frame(qualifier=["<", None, ">", ""])
    _, ax = ht.plot.profile(df, "undrained_shear_strength")
    less = [c for c in ax.collections if c.get_label().endswith(" <")]
    more = [c for c in ax.collections if c.get_label().endswith(" >")]
    assert [c.get_offsets().tolist() for c in less] == [[[500.0, 115.0]]]
    assert [c.get_offsets().tolist() for c in more] == [[[1500.0, 105.0]]]
    assert caret_tip(less[0]).max() < 0
    assert caret_tip(more[0]).min() > 0


def test_qualified_values_are_counted_in_notes_and_legend(frame):
    df = frame(qualifier=["<", "<", ">", None])
    _, ax = ht.plot.profile(df, "undrained_shear_strength")
    assert ax.ags_notes == {"less_than": 2, "greater_than": 1}
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert labels == ["Clay", "Fill", "less than (2)", "greater than (1)"]
    footnote = ax.texts[-1].get_text()
    assert "2 values reported as less than (<)" in footnote


def test_a_qualified_blank_counts_only_as_blank(frame):
    df = frame(values=[np.nan, 1000.0, 1500.0, 2000.0], qualifier=["<", "", "", ""])
    _, ax = ht.plot.profile(df, "undrained_shear_strength")
    assert ax.ags_notes == {"nan": 1}


def test_a_qualified_value_beyond_the_limit_keeps_its_caret(frame):
    df = frame(qualifier=["", "", "", ">"])
    _, ax = ht.plot.profile(df, "undrained_shear_strength", xlim=(0, 1800))
    (edge,) = [c for c in ax.collections if len(c.get_facecolor()) == 0]
    assert caret_tip(edge).min() > 0
    assert ax.ags_notes == {"beyond_limit": 1, "greater_than": 1}


def test_an_unknown_qualifier_lists_the_rows(frame):
    df = frame(qualifier=["<", "~", "", "approx"])
    with pytest.raises(ht.ColumnError, match=r"rows 1, 3 hold '~', 'approx'"):
        ht.plot.profile(df, "undrained_shear_strength")


def test_us_and_si_agree_with_intervals_and_qualifiers(frame, assert_us_si_equivalent):
    df = interval_frame(frame, qualifier=["<", "", ">", ""])
    plot = partial(ht.plot.profile, value="undrained_shear_strength")
    assert_us_si_equivalent(plot, df, ("stress", "length"))


def test_the_input_frame_is_unchanged(frame, assert_no_global_state):
    df = interval_frame(frame, qualifier=["<", "", ">", ""])
    assert_no_global_state(ht.plot.profile, df, value="undrained_shear_strength")


def test_qualifier_column_of_blanks_draws_plain_markers(frame):
    df = frame(qualifier=pd.Series([None] * 4, dtype=object))
    _, ax = ht.plot.profile(df, "undrained_shear_strength")
    assert ax.ags_notes == {}
    assert all(not c.get_label().startswith("_") for c in ax.collections)
