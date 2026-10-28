"""Legend placement inside the axes (docs/work/p00-layout-defaults.md, AC 1-6, 16)."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D

from hangtu.plot import _layers
from hangtu.plot.common import Notes, add_legend

# Legend._loc codes for the corners.
UPPER_RIGHT, UPPER_LEFT, LOWER_LEFT, LOWER_RIGHT = 1, 2, 3, 4


def entries(n=2):
    return [Line2D([], [], marker="o", label=f"Unit {i}") for i in range(n)]


@pytest.fixture
def ax():
    """A profile-sized axes from 0 to 10 both ways."""
    _, ax = plt.subplots(figsize=(4.5, 6.0), layout="constrained")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_xlabel("Value")
    return ax


def points(ax, xy):
    x, y = zip(*xy, strict=True)
    ax.scatter(x, y, s=25, zorder=_layers.MARKERS)


def place(ax, where="auto", notes=None):
    return add_legend(ax, [entries()], notes or Notes(), where=where)


def test_points_in_the_lower_half_give_the_upper_right_and_a_footnote_below(ax):
    points(ax, [(2, 1), (5, 2), (8, 3), (9.5, 4.5)])
    notes = Notes()
    notes.add("nan", 2)
    legend, where = place(ax, notes=notes)
    assert where == "inside"
    assert legend._loc == UPPER_RIGHT
    footnote = notes.render(ax, where=where)
    ax.figure.draw_without_rendering()
    renderer = ax.figure.canvas.get_renderer()
    label = ax.xaxis.get_tightbbox(renderer)
    assert footnote.get_window_extent(renderer).y1 < label.y0
    assert ax.ags_notes == {"nan": 2}


def test_an_inside_legend_has_a_white_frame_without_an_edge(ax):
    legend, _ = place(ax)
    assert legend.get_frame_on()
    frame = legend.get_frame()
    assert frame.get_facecolor() == pytest.approx(to_rgba("white", 0.85))
    assert frame.get_edgecolor()[3] == 0


CORNER_POINTS = [(9.5, 9.6), (9.0, 9.6), (0.5, 9.6), (1.0, 9.6), (9.5, 0.4), (9, 0.4)]


def test_a_point_in_each_corner_sends_auto_below_the_x_label(ax):
    points(ax, [*CORNER_POINTS, (0.5, 0.4)])
    legend, where = place(ax)
    assert where == "bottom"
    assert legend._loc == 9  # upper center, under the axes
    assert legend.get_bbox_to_anchor().y1 < ax.bbox.y0


def test_inside_takes_the_corner_with_the_fewest_obstacles(ax):
    points(ax, [*CORNER_POINTS, (0.5, 0.4)])  # two in each corner but the lower left
    legend, where = place(ax, where="inside")
    assert where == "inside"
    assert legend._loc == LOWER_LEFT


def test_inside_ties_go_to_the_earlier_corner(ax):
    points(ax, [(9.5, 9.6), (0.5, 9.6), (9.5, 0.4), (0.5, 0.4)])
    legend, _ = place(ax, where="inside")
    assert legend._loc == UPPER_RIGHT


def test_a_line_crossing_a_corner_blocks_it_though_its_ends_are_outside(ax):
    # From (6.5, 12) to (12, 6.5), both beyond the axes: it crosses the upper right.
    ax.plot([6.5, 12], [12, 6.5], color="k", zorder=_layers.CHART_LINES)
    legend, _ = place(ax)
    assert legend._loc == UPPER_LEFT


def test_a_strata_band_doesnt_block_a_corner_but_its_label_does(ax):
    ax.axhspan(8, 10, color="tan", zorder=_layers.STRATA)
    legend, _ = place(ax)
    assert legend._loc == UPPER_RIGHT
    legend.remove()
    # Well inside the legend's box: its height differs by a few pixels between
    # matplotlib versions.
    ax.text(9.8, 9.5, "Fill", ha="right", va="center", zorder=_layers.ANNOTATIONS)
    legend, _ = place(ax)
    assert legend._loc == UPPER_LEFT


def test_the_stats_box_blocks_the_lower_left(ax):
    points(ax, [(9.5, 9.6), (0.5, 9.6), (9.5, 0.4)])
    legend, _ = place(ax)
    assert legend._loc == LOWER_LEFT
    legend.remove()
    ax.text(
        0.02,
        0.02,
        "n = 3\nmean 4.2",
        transform=ax.transAxes,
        fontsize=7,
        bbox={"facecolor": "white", "edgecolor": "0.6"},
        zorder=_layers.ANNOTATIONS,
    )
    _, where = place(ax)
    assert where == "bottom"


def test_a_bar_reaching_into_a_corner_blocks_it(ax):
    ax.bar([9.0], [9.8], width=0.8, zorder=_layers.MARKERS)
    legend, _ = place(ax)
    assert legend._loc == UPPER_LEFT


def test_a_short_bar_doesnt_block_the_corner_above_it(ax):
    ax.bar([9.0], [3.0], width=0.8, zorder=_layers.MARKERS)
    legend, _ = place(ax)
    assert legend._loc == UPPER_RIGHT


def test_marker_lines_count_their_markers(ax):
    ax.plot([9.5], [9.6], "o", zorder=_layers.MARKERS)
    legend, _ = place(ax)
    assert legend._loc == UPPER_LEFT


def test_the_corner_search_leaves_rcparams_unchanged(ax):
    points(ax, CORNER_POINTS)
    before = dict(mpl.rcParams)
    place(ax)
    place(ax, where="inside")
    assert dict(mpl.rcParams) == before
