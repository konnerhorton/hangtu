"""P01 marker groups and connecting lines (P01 §7)."""

from functools import partial

import numpy as np
import pytest
from matplotlib.colors import to_rgba
from matplotlib.markers import MarkerStyle
from matplotlib.patches import Patch

import hangtu as ak

CYCLE = ["o", "s", "^", "D", "v", "P", "X", "p", "h", "*", "<", ">"]


def shape_of(collection):
    """The matplotlib marker whose path the collection draws."""
    vertices = collection.get_paths()[0].vertices
    for marker in CYCLE:
        style = MarkerStyle(marker)
        path = style.get_path().transformed(style.get_transform())
        if path.vertices.shape == vertices.shape and np.allclose(
            path.vertices, vertices
        ):
            return marker
    raise AssertionError("unknown marker")


def shapes_by_point(ax):
    """{(x, y): marker} for every filled point."""
    found = {}
    for collection in ax.collections:
        if len(collection.get_facecolor()) == 0:
            continue
        for xy in collection.get_offsets().tolist():
            found[tuple(xy)] = shape_of(collection)
    return found


def legend(ax):
    return [text.get_text() for text in ax.get_legend().get_texts()]


# --- marker_by ------------------------------------------------------------------


def test_each_group_gets_a_shape_from_the_cycle(frame):
    df = frame(source=["lab", "field", "lab", "field"])
    _, ax = ak.plot.profile(df, "undrained_shear_strength", marker_by="source")
    # Groups are sorted by name: field is ●, lab is ■.
    assert shapes_by_point(ax) == {
        (500.0, 115.0): "s",
        (1000.0, 110.0): "o",
        (1500.0, 105.0): "s",
        (2000.0, 100.0): "o",
    }


def test_legend_lists_units_then_gray_marker_groups(frame):
    df = frame(source=["lab", "field", "lab", "field"])
    _, ax = ak.plot.profile(df, "undrained_shear_strength", marker_by="source")
    assert legend(ax) == ["Clay", "Fill", "field", "lab"]
    handles = ax.get_legend().legend_handles
    assert all(isinstance(handle, Patch) for handle in handles[:2])
    assert [handle.get_marker() for handle in handles[2:]] == ["o", "s"]
    assert {to_rgba(handle.get_color()) for handle in handles[2:]} == {to_rgba("0.3")}


def test_unit_colors_still_match_legend_handles(frame):
    df = frame(source=["lab", "field", "lab", "field"])
    _, ax = ak.plot.profile(df, "undrained_shear_strength", marker_by="source")
    patches = {p.get_label(): p.get_facecolor() for p in ak.plot.legend_handles()}
    for collection in ax.collections:
        unit = collection.get_label().lstrip("_").split(" ")[0]
        assert tuple(collection.get_facecolor()[0]) == patches[unit]


def test_more_than_ten_groups_repeat_shapes_and_warn(frame):
    df = frame(
        values=[100.0 * i for i in range(1, 12)],
        loca_id=["A"] * 11,
        depth=[float(i) for i in range(1, 12)],
        ground_level=[120.0] * 11,
        geology_unit=["Fill"] * 11,
        test_type=[f"type {i:02d}" for i in range(1, 12)],
    )
    with pytest.warns(UserWarning, match=r"11 groups.*connect=True.*split the data"):
        _, ax = ak.plot.profile(df, "undrained_shear_strength", marker_by="test_type")
    shapes = shapes_by_point(ax)
    assert shapes[(100.0, 119.0)] == "o"
    assert shapes[(1100.0, 109.0)] == "o"
    assert len(set(shapes.values())) == 10


def test_a_blank_group_is_listed_last(frame):
    df = frame(source=["lab", None, "lab", "field"])
    _, ax = ak.plot.profile(df, "undrained_shear_strength", marker_by="source")
    assert legend(ax) == ["Clay", "Fill", "field", "lab", "(blank)"]
    assert shapes_by_point(ax)[(1000.0, 110.0)] == "^"


def test_a_group_with_nothing_drawn_has_no_legend_entry(frame):
    df = frame(values=[500.0, np.nan, 1500.0, 2000.0])
    df["source"] = ["lab", "field", "lab", "lab"]
    _, ax = ak.plot.profile(df, "undrained_shear_strength", marker_by="source")
    assert legend(ax) == ["Clay", "Fill", "lab"]


def test_a_qualifier_caret_replaces_the_group_shape(frame):
    df = frame(source=["lab", "field", "lab", "field"], qualifier=["<", "", "", ""])
    _, ax = ak.plot.profile(df, "undrained_shear_strength", marker_by="source")
    assert shapes_by_point(ax)[(500.0, 115.0)] == "<"
    assert legend(ax) == ["Clay", "Fill", "field", "lab", "less than (1)"]


def test_marker_by_a_missing_column_is_an_error(frame):
    with pytest.raises(ak.ColumnError, match="marker_by='source' isn't a column"):
        ak.plot.profile(frame(), "undrained_shear_strength", marker_by="source")


def test_edge_markers_keep_the_group_shape(frame):
    df = frame(source=["lab", "field", "lab", "field"])
    _, ax = ak.plot.profile(
        df, "undrained_shear_strength", marker_by="source", xlim=(0, 1800)
    )
    (edge,) = [c for c in ax.collections if len(c.get_facecolor()) == 0]
    assert shape_of(edge) == "o"
    assert edge.get_offsets().tolist() == [[1800.0, 100.0]]


# --- connect --------------------------------------------------------------------


def test_one_gray_line_per_hole_in_vertical_order(frame):
    df = frame(loca_id=["A", "B", "A", "B"]).iloc[[2, 1, 0, 3]]
    _, ax = ak.plot.profile(df, "undrained_shear_strength", connect=True)
    # Rows are shuffled; each hole's points are still joined in vertical order.
    holes = {
        tuple(sorted(line.get_xdata())): list(line.get_ydata()) for line in ax.lines
    }
    assert holes == {(500.0, 1500.0): [105.0, 115.0], (1000.0, 2000.0): [100.0, 110.0]}
    for line in ax.lines:
        assert to_rgba(line.get_color()) == to_rgba("0.3")
        assert line.get_linewidth() == 0.6
        assert line.get_alpha() == 0.6
        assert line.get_zorder() < min(c.get_zorder() for c in ax.collections)


def test_lines_follow_only_drawn_points(frame):
    df = frame(values=[500.0, np.nan, 1500.0, 2000.0], loca_id=["A"] * 4)
    _, ax = ak.plot.profile(df, "undrained_shear_strength", connect=True)
    (line,) = ax.lines
    assert sorted(line.get_ydata()) == [100.0, 105.0, 115.0]


def test_connect_off_by_default(frame):
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength")
    assert len(ax.lines) == 0


def test_connect_without_loca_id_is_an_error(frame):
    df = frame().drop(columns="loca_id")
    with pytest.raises(ak.ColumnError, match=r"connect=True.*'loca_id'"):
        ak.plot.profile(df, "undrained_shear_strength", connect=True)


def test_us_and_si_agree_with_groups(frame, assert_us_si_equivalent):
    df = frame(source=["lab", "field", "lab", "field"])
    plot = partial(
        ak.plot.profile,
        value="undrained_shear_strength",
        marker_by="source",
        connect=True,
    )
    assert_us_si_equivalent(plot, df, ("stress", "length"))
