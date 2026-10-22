"""P06 water content profile: limits bars, one limit, PL > LL, limits and errors."""

import numpy as np
import pandas as pd
import pytest
from matplotlib.colors import to_rgba

import hangtu as ht


def wc_frame(**columns):
    """Two holes, two units, depths in ft. Every row has w, PL and LL."""
    data = {
        "loca_id": ["A", "A", "B", "B"],
        "depth": [5.0, 10.0, 15.0, 20.0],
        "ground_level": [120.0, 120.0, 120.0, 120.0],
        "geology_unit": ["Clay", "Clay", "Silt", "Silt"],
        "water_content": [25.0, 30.0, 22.0, 35.0],
        "plastic_limit": [18.0, 20.0, 15.0, 24.0],
        "liquid_limit": [40.0, 45.0, 30.0, 52.0],
        **columns,
    }
    return ht.set_units(pd.DataFrame(data), {"depth": "ft", "ground_level": "ft"})


def bars(ax):
    """Each limits bar as (PL end, LL end, y), sorted by y."""
    segments = []
    for line in ax.lines:
        if line.get_gid() != "limits_bar":
            continue
        xy = line.get_xydata().reshape(-1, 3, 2)
        segments += [(row[0, 0], row[1, 0], row[0, 1]) for row in xy]
    return sorted(segments, key=lambda segment: segment[2])


def ticks(ax):
    """Every end tick drawn inside the axes, as sorted (x, y) pairs."""
    offsets = [
        c.get_offsets().data
        for c in ax.collections
        if c.get_gid() == "limits_tick" and len(c.get_offsets())
    ]
    if not offsets:
        return []
    return sorted(map(tuple, np.concatenate(offsets).tolist()))


def unit_points(ax, unit):
    (collection,) = [c for c in ax.collections if c.get_label() == unit]
    return collection.get_offsets().data.tolist()


def plot(df, **kwargs):
    """Plot against depth, with hints off."""
    ht.settings.hints = False
    return ht.plot.water_content_profile(df, vs="depth", **kwargs)


# --- bars ------------------------------------------------------------------------


def test_geometry():
    # P06 §12: PL 20, LL 45, w 30 at 10 ft.
    df = wc_frame().iloc[[1]]
    _, ax = plot(df)
    assert bars(ax) == [(20.0, 45.0, 10.0)]
    assert unit_points(ax, "Clay") == [[30.0, 10.0]]
    assert ticks(ax) == [(20.0, 10.0), (45.0, 10.0)]
    assert ax.ags_notes == {}


def test_label_and_default_limits():
    _, ax = plot(wc_frame())
    assert ax.get_xlabel() == "Water content, w, and Atterberg limits (%)"
    assert ax.get_xlim() == (0.0, 60.0)
    assert ax.get_ylabel() == "Depth (ft)"


def test_label_overrides():
    _, ax = plot(wc_frame(), label="w and limits")
    assert ax.get_xlabel() == "w and limits (%)"


def test_bars_are_under_the_markers_in_the_unit_color():
    _, ax = plot(wc_frame())
    (bar_line, *_) = [line for line in ax.lines if line.get_gid() == "limits_bar"]
    (points,) = [c for c in ax.collections if c.get_label() == "Clay"]
    assert bar_line.get_zorder() < points.get_zorder()
    assert to_rgba(bar_line.get_color()) == tuple(points.get_facecolor()[0])
    assert bar_line.get_linewidth() == 1.2


def test_legend_has_one_bar_entry_after_the_units():
    _, ax = plot(wc_frame())
    texts = [t.get_text() for t in ax.get_legend().get_texts()]
    assert texts == ["Clay", "Silt", "PL to LL"]


def test_limits_only_draw_bars_with_no_count():
    df = wc_frame(water_content=[np.nan] * 4)
    _, ax = plot(df)
    assert len(bars(ax)) == 4
    assert ax.ags_notes == {}
    assert "No data" not in [t.get_text() for t in ax.texts]
    assert ax.get_ylim() == (25.0, 0.0)
    assert [t.get_text() for t in ax.get_legend().get_texts()] == [
        "Clay",
        "Silt",
        "PL to LL",
    ]


def test_no_water_content_column_draws_the_bars():
    df = wc_frame().drop(columns="water_content")
    _, ax = plot(df)
    assert len(bars(ax)) == 4
    assert ax.ags_notes == {}


def test_water_content_only_draws_no_bars_and_hints():
    df = wc_frame().drop(columns=["plastic_limit", "liquid_limit"])
    with pytest.warns(ht.HangtuHint) as caught:
        _, ax = ht.plot.water_content_profile(df, vs="depth")
    message = str(caught[0].message)
    assert "No 'plastic_limit' column: the limits bars aren't drawn." in message
    assert "No 'liquid_limit' column: the limits bars aren't drawn." in message
    assert bars(ax) == []
    assert ax.ags_notes == {}


def test_a_row_with_neither_w_nor_limits_is_blank():
    df = wc_frame(
        water_content=[np.nan, 30.0, 22.0, 35.0],
        plastic_limit=[np.nan, 20.0, 15.0, 24.0],
        liquid_limit=[np.nan, 45.0, 30.0, 52.0],
    )
    _, ax = plot(df)
    assert ax.ags_notes == {"nan": 1}
    assert len(bars(ax)) == 3


# --- one limit -------------------------------------------------------------------


def test_one_limit_is_a_single_tick_counted_and_warned():
    df = wc_frame(plastic_limit=[18.0, np.nan, 15.0, 24.0])
    with pytest.warns(UserWarning, match=r"Rows 1 have only one Atterberg limit"):
        _, ax = plot(df)
    assert (45.0, 10.0) in ticks(ax)
    assert len(bars(ax)) == 3
    assert ax.ags_notes == {"one_limit": 1}
    footnote = ax.texts[-1].get_text()
    assert "1 specimen with one limit, shown as a single tick" in footnote


def test_pl_is_not_computed_from_pi():
    # P06 §12: LL 45, PI 25, PL blank.
    df = wc_frame(
        plastic_limit=[18.0, np.nan, 15.0, 24.0], plasticity_index=[22, 25, 15, 28]
    )
    with pytest.warns(UserWarning) as caught:
        _, ax = plot(df)
    (message,) = [str(w.message) for w in caught]
    assert "Rows 1" in message
    assert "The plastic limit isn't computed from LL - PI" in message
    assert (45.0, 10.0) in ticks(ax)
    assert ax.ags_notes == {"one_limit": 1}


def test_one_limit_with_pi_on_another_row_says_nothing_about_pi():
    df = wc_frame(
        liquid_limit=[40.0, np.nan, 30.0, 52.0], plasticity_index=[22, np.nan, 15, 28]
    )
    with pytest.warns(UserWarning) as caught:
        _, ax = plot(df)
    assert "LL - PI" not in str(caught[0].message)
    assert (20.0, 10.0) in ticks(ax)


# --- PL above LL -----------------------------------------------------------------


def test_pl_above_ll_is_not_drawn_and_is_counted():
    df = wc_frame(plastic_limit=[18.0, 50.0, 15.0, 24.0])
    with pytest.warns(UserWarning, match=r"Rows 1 have a plastic limit above"):
        _, ax = plot(df)
    assert len(bars(ax)) == 3
    assert all(y != 10.0 for _, y in ticks(ax))
    assert ax.ags_notes == {"limits_inverted": 1}
    assert "1 specimen with PL above LL, limits not shown" in ax.texts[-1].get_text()
    assert [30.0, 10.0] in unit_points(ax, "Clay")


# --- limits ----------------------------------------------------------------------


def test_default_x_limit_covers_ll():
    # P06 §12: an LL of 72 runs the axis to 80.
    df = wc_frame(liquid_limit=[40.0, 45.0, 30.0, 72.0])
    _, ax = plot(df)
    assert ax.get_xlim() == (0.0, 80.0)


def test_xlim_clips_a_bar_with_an_arrow_and_counts_it_once():
    df = wc_frame(liquid_limit=[40.0, 45.0, 30.0, 72.0])
    _, ax = plot(df, xlim=(0, 50))
    assert bars(ax)[-1] == (24.0, 50.0, 20.0)
    assert (72.0, 20.0) not in ticks(ax)
    assert (24.0, 20.0) in ticks(ax)
    arrows = [t for t in ax.texts if getattr(t, "arrow_patch", None) is not None]
    assert len(arrows) == 1
    assert ax.ags_notes == {"beyond_limit": 1}


def test_ylim_counts_a_bar_beyond_it():
    df = wc_frame(water_content=[25.0, 30.0, 22.0, np.nan])
    _, ax = plot(df, ylim=(0, 16))
    assert [segment[2] for segment in bars(ax)] == [5.0, 10.0, 15.0]
    assert ax.ags_notes == {"beyond_limit": 1}


# --- limits=False ----------------------------------------------------------------


def test_limits_false_is_p01():
    df = wc_frame()
    _, ours = plot(df, limits=False)
    _, p01 = ht.plot.profile(df, "water_content", vs="depth", preset="water_content")
    assert bars(ours) == []
    assert ours.get_xlabel() == p01.get_xlabel() == "Water content, w (%)"
    assert ours.get_xlim() == p01.get_xlim()
    assert [c.get_offsets().data.tolist() for c in ours.collections] == [
        c.get_offsets().data.tolist() for c in p01.collections
    ]
    assert len(ours.lines) == len(p01.lines)


# --- errors ----------------------------------------------------------------------


def test_neither_w_nor_both_limits_is_an_error():
    df = wc_frame().drop(columns=["water_content", "liquid_limit"])
    with pytest.raises(
        ht.ColumnError,
        match=r"needs a 'water_content' column, or both.*Found 'plastic_limit'",
    ):
        plot(df)


def test_text_in_a_limit_is_an_error():
    df = wc_frame(liquid_limit=[40.0, "NP", 30.0, 52.0])
    with pytest.raises(
        ht.ColumnError,
        match=r"'liquid_limit' has text in rows 1 \('NP'\).*'non_plastic' to True",
    ):
        plot(df)


@pytest.mark.parametrize(
    "argument", [{"value": "liquid_limit"}, {"preset": "water_content"}, {"log": True}]
)
def test_fixed_arguments_are_errors(argument):
    with pytest.raises(ht.HangtuError, match=r"use ht.plot.profile\(\)"):
        plot(wc_frame(), **argument)


# --- non-plastic -----------------------------------------------------------------


def np_points(ax):
    """The open non-plastic markers drawn inside the axes, as (x, y) pairs."""
    return [
        xy
        for c in ax.collections
        if c.get_label().startswith("_Silt D") or c.get_label().startswith("_Clay D")
        for xy in c.get_offsets().data.tolist()
    ]


def test_non_plastic_with_w_is_open_at_its_w_with_no_bar():
    # P06 §12: an NP specimen with w 18.
    df = wc_frame(
        water_content=[25.0, 30.0, 18.0, 35.0],
        plastic_limit=[18.0, 20.0, np.nan, 24.0],
        liquid_limit=[40.0, 45.0, np.nan, 52.0],
        non_plastic=[False, False, True, False],
    )
    _, ax = plot(df)
    assert np_points(ax) == [[18.0, 15.0]]
    (collection,) = [c for c in ax.collections if c.get_label() == "_Silt D"]
    assert collection.get_facecolor().size == 0
    assert [segment[2] for segment in bars(ax)] == [5.0, 10.0, 20.0]
    assert all(y != 15.0 for _, y in ticks(ax))
    texts = [t.get_text() for t in ax.get_legend().get_texts()]
    assert texts == ["Clay", "Silt", "PL to LL", "non-plastic (1)"]
    assert ax.ags_notes == {"non_plastic_drawn": 1}
    footnote = ax.texts[-1].get_text()
    assert "1 non-plastic (NP) specimen, shown open at their water content" in footnote


def test_non_plastic_without_w_is_at_the_left_edge_and_counted():
    df = wc_frame(
        water_content=[25.0, 30.0, np.nan, 35.0],
        plastic_limit=[18.0, 20.0, np.nan, 24.0],
        liquid_limit=[40.0, 45.0, np.nan, 52.0],
        non_plastic=[False, False, True, False],
    )
    _, ax = plot(df)
    assert np_points(ax) == []
    assert ax.ags_notes == {"non_plastic": 1}
    assert "1 non-plastic (NP) value, shown at the left edge" in ax.texts[-1].get_text()
    assert "NP (1)" in [t.get_text() for t in ax.get_legend().get_texts()]


def test_text_np_in_water_content_reads_the_same():
    df = wc_frame(
        water_content=[25.0, 30.0, "NP", 35.0],
        plastic_limit=[18.0, 20.0, np.nan, 24.0],
        liquid_limit=[40.0, 45.0, np.nan, 52.0],
    )
    _, text = plot(df)
    flagged = plot(
        df.assign(
            water_content=[25.0, 30.0, np.nan, 35.0],
            non_plastic=[False, False, True, False],
        )
    )[1]
    assert text.ags_notes == flagged.ags_notes == {"non_plastic": 1}


def test_non_plastic_does_not_change_the_input():
    df = wc_frame(
        water_content=[25.0, 30.0, np.nan, 35.0],
        non_plastic=[False, False, True, False],
    )
    before = df.copy()
    with pytest.warns(UserWarning):
        plot(df)
    pd.testing.assert_frame_equal(df, before)


def test_non_plastic_with_bad_values_is_an_error():
    df = wc_frame(non_plastic=[False, "maybe", False, False])
    with pytest.raises(ht.ColumnError, match=r"'non_plastic' must hold True or False"):
        plot(df)


def test_non_plastic_with_a_qualifier_is_an_error():
    df = wc_frame(non_plastic=[False, True, False, False], qualifier=["", "<", "", ""])
    with pytest.raises(ht.ColumnError, match=r"Rows 1 are marked non-plastic and have"):
        plot(df)


def test_qualifiers_still_work():
    _, ax = plot(wc_frame(qualifier=["", "<", "", ""]))
    assert ax.ags_notes == {"less_than": 1}


def test_non_plastic_with_limits_warns_and_draws_no_bar():
    df = wc_frame(non_plastic=[False, True, False, False])
    with pytest.warns(UserWarning, match=r"Rows 1 are marked non-plastic but have"):
        _, ax = plot(df)
    assert [segment[2] for segment in bars(ax)] == [5.0, 15.0, 20.0]
    assert np_points(ax) == [[30.0, 10.0]]
    assert ax.ags_notes == {"non_plastic_drawn": 1}


def test_non_plastic_beyond_xlim_is_open_at_the_edge():
    df = wc_frame(
        water_content=[25.0, 30.0, 70.0, 35.0],
        plastic_limit=[18.0, 20.0, np.nan, 24.0],
        liquid_limit=[40.0, 45.0, np.nan, 52.0],
        non_plastic=[False, False, True, False],
    )
    _, ax = plot(df, xlim=(0, 60))
    edge = [c for c in ax.collections if c.get_offsets().data.tolist() == [[60, 15]]]
    (marker,) = edge
    assert marker.get_facecolor().size == 0
    assert ax.ags_notes == {"beyond_limit": 1, "non_plastic_drawn": 1}


def test_non_plastic_and_a_marker_by_diamond_are_two_marks():
    # marker_by's fourth group ("d") is a diamond, as NP is: they stay apart.
    df = wc_frame(
        source=["a", "b", "c", "d"],
        plastic_limit=[18.0, 20.0, np.nan, 24.0],
        liquid_limit=[40.0, 45.0, np.nan, 52.0],
        non_plastic=[False, False, True, False],
    )
    _, ax = plot(df, marker_by="source")
    diamonds = {
        tuple(c.get_offsets().data.tolist()[0]): c.get_facecolor().size
        for c in ax.collections
        if c.get_label() in ("Silt", "_Silt D")
    }
    assert set(diamonds) == {(22.0, 15.0), (35.0, 20.0)}
    assert diamonds[(22.0, 15.0)] == 0  # NP, open
    assert diamonds[(35.0, 20.0)] > 0  # group "d", filled
