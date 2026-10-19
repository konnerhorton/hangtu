import matplotlib.pyplot as plt
import numpy as np
import pytest

from hangtu.plot.common import Notes, edge_markers, log_limits, set_log_axis


def test_notes_count_by_reason_and_skip_zero_counts():
    notes = Notes()
    assert notes.count([True, False, True], "nan") == 2
    notes.count([False, False], "refusal")
    notes.add("beyond_limit", 1)
    notes.add("beyond_limit", 2)
    assert notes.counts == {"nan": 2, "beyond_limit": 3}
    assert notes.lines() == [
        "2 blank values not shown",
        "3 values beyond axis limit, shown at the edge",
    ]


def test_singular_wording():
    notes = Notes()
    notes.add("log_nonpositive", 1)
    notes.add("refusal", 1)
    assert notes.lines() == ["1 value ≤ 0 not shown on log axis", "1 refusal"]


def test_unknown_reason_raises():
    with pytest.raises(ValueError, match="Unknown reason 'dropped'"):
        Notes().add("dropped", 1)


def test_render_with_nothing_to_note():
    _, ax = plt.subplots()
    assert Notes().render(ax) is None
    assert ax.ags_notes == {}


def test_free_text_follows_the_counts():
    _, ax = plt.subplots()
    notes = Notes()
    notes.add_text("35 units: see ht.plot.legend_handles()")
    notes.add("nan", 2)
    footnote = notes.render(ax)
    assert footnote.get_text() == (
        "2 blank values not shown\n35 units: see ht.plot.legend_handles()"
    )
    assert footnote.get_fontsize() == 7


def test_synthetic_log_plot_counts_every_excluded_value():
    # 6 values: 1 NaN, 2 that are ≤ 0, 1 beyond the fixed upper limit, 2 drawn.
    k = np.array([1e-6, np.nan, 0.0, -1e-5, 5e-2, 3e-7])
    depth = np.arange(6.0)
    _, ax = plt.subplots()
    notes = Notes()
    blank = notes.count(np.isnan(k), "nan")
    nonpositive = notes.count(k <= 0, "log_nonpositive")
    drawable = k > 0
    set_log_axis(ax, "x", log_limits(1e-7, 1e-2))
    edge = edge_markers(
        ax, k[drawable], depth[drawable], {"x": (1e-7, 1e-2)}, color="C0"
    )
    notes.count(edge, "beyond_limit")
    ax.scatter(k[drawable][~edge], depth[drawable][~edge])
    notes.render(ax)

    assert (blank, nonpositive, int(edge.sum())) == (1, 2, 1)
    assert ax.ags_notes == {"nan": 1, "log_nonpositive": 2, "beyond_limit": 1}
    assert blank + nonpositive + edge.sum() + (~edge).sum() == len(k)


def test_edge_markers_sit_at_the_limit_and_point_outward():
    _, ax = plt.subplots()
    ax.set_xlim(0, 10)
    ax.set_ylim(20, 0)  # inverted, like a depth axis
    x = np.array([5.0, 12.0, -3.0, 4.0])
    y = np.array([5.0, 6.0, 7.0, 25.0])
    mask = edge_markers(ax, x, y, {"x": (0, 10), "y": (20, 0)}, color="C1")

    assert mask.tolist() == [False, True, True, True]
    [markers] = ax.collections
    assert markers.get_offsets().tolist() == [[10, 6], [0, 7], [4, 20]]
    assert markers.get_facecolor().size == 0  # open markers
    arrows = [(a.xy, a.xyann) for a in ax.texts]
    assert arrows == [((10, 6), (10, 0)), ((0, 7), (-10, 0)), ((4, 20), (0, -10))]


def test_edge_markers_draw_in_the_transform_given():
    _, ax = plt.subplots()
    ax.set_ylim(20, 0)
    blended = ax.get_yaxis_transform()  # x in axes, y in data
    mask = edge_markers(
        ax, [0.0, 0.0], [5.0, 25.0], {"y": (20, 0)}, color="C1", transform=blended
    )

    assert mask.tolist() == [False, True]
    [markers] = ax.collections
    assert markers.get_offset_transform() == blended
    assert markers.get_offsets().tolist() == [[0, 20]]
    [arrow] = ax.texts
    assert arrow.xycoords == blended
    assert (arrow.xy, arrow.xyann) == ((0, 20), (0, -10))


def test_no_edge_markers_when_everything_fits():
    _, ax = plt.subplots()
    mask = edge_markers(ax, [1.0, 2.0], [1.0, np.nan], {"x": (0, 5)}, color="C0")
    assert not mask.any()
    assert not ax.collections


def test_where_adds_detail_to_a_reason():
    notes = Notes()
    notes.add("refusal", 2)
    notes.set_where("refusal", ", shown at N = 100")
    notes.add("refusal_excluded", 1)
    notes.add("no_energy_ratio", 3)
    assert notes.lines() == [
        "2 refusals, shown at N = 100",
        "1 refusal not shown",
        "3 tests without an energy ratio not shown",
    ]
    assert notes.counts == {"refusal": 2, "refusal_excluded": 1, "no_energy_ratio": 3}


def test_where_for_an_unknown_reason_raises():
    with pytest.raises(ValueError, match="Unknown reason 'cap'"):
        Notes().set_where("cap", "x")
