"""P01 text in the value column, drawn at the left edge (P01 §3, §7; TODO #15)."""

import warnings

import numpy as np
import pytest

import hangtu as ht

VALUE = "water_content"


def text_collections(ax):
    """The text-value markers: collections placed in axes x, data y."""
    return [
        c
        for c in ax.collections
        if len(c.get_offsets()) and c.get_offset_transform() is not ax.transData
    ]


def text_points(ax):
    offsets = [c.get_offsets() for c in text_collections(ax)]
    return np.concatenate(offsets) if offsets else np.empty((0, 2))


def data_points(ax):
    offsets = [
        c.get_offsets()
        for c in ax.collections
        if len(c.get_offsets()) and c.get_offset_transform() is ax.transData
    ]
    return np.concatenate(offsets) if offsets else np.empty((0, 2))


def legend_texts(ax):
    return [text.get_text() for text in ax.get_legend().get_texts()]


def water(frame, values, **columns):
    return frame(VALUE, values, None, **columns)


def test_np_and_refusal_are_drawn_at_the_left_edge_without_a_warning(frame):
    df = water(frame, [20.0, "NP", " refusal", 35.0])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _, ax = ht.plot.profile(df, VALUE, vs="depth")

    assert len(data_points(ax)) == 2
    points = text_points(ax)
    assert points[:, 0].tolist() == [0.0, 0.0]
    assert sorted(points[:, 1]) == [10.0, 15.0]
    assert legend_texts(ax)[-2:] == ["NP (1)", "refusal (1)"]
    assert ax.ags_notes == {"non_plastic": 1, "refusal": 1}
    footnote = ax.texts[-1].get_text().splitlines()
    assert footnote == [
        "1 refusal, shown at the left edge",
        "1 non-plastic (NP) value, shown at the left edge",
    ]


def test_markers_sit_four_points_inside_the_left_edge(frame):
    df = water(frame, [20.0, "NP", 30.0, 35.0])
    fig, ax = ht.plot.profile(df, VALUE, vs="depth")
    fig.draw_without_rendering()
    [markers] = text_collections(ax)
    x_screen, y_screen = markers.get_offset_transform().transform((0.0, 10.0))
    left = ax.transAxes.transform((0.0, 0.0))[0]
    assert x_screen - left == pytest.approx(4.0 * fig.dpi / 72)
    assert y_screen == pytest.approx(ax.transData.transform((0.0, 10.0))[1])


@pytest.mark.parametrize("log", [False, True])
@pytest.mark.parametrize("vs", ["depth", "elevation"])
def test_text_values_stay_at_the_edge_on_any_axis(frame, log, vs):
    df = water(frame, [20.0, "NP", 30.0, "dry"])
    with pytest.warns(UserWarning, match="'dry'"):
        _, ax = ht.plot.profile(df, VALUE, vs=vs, log=log)
    points = text_points(ax)
    assert points[:, 0].tolist() == [0.0, 0.0]
    expected = [10.0, 20.0] if vs == "depth" else [100.0, 110.0]
    assert sorted(points[:, 1]) == expected
    assert ax.get_xscale() == ("log" if log else "linear")


def test_one_shape_per_text_in_order_and_unit_colors(frame):
    df = water(frame, ["dry", "NP", "refusal", "NP"])
    with pytest.warns(UserWarning):
        _, ax = ht.plot.profile(df, VALUE, vs="depth")
    shapes = {}
    for collection in text_collections(ax):
        assert collection.get_facecolor().size == 0  # open markers
        shapes.setdefault(collection.get_paths()[0].vertices.tobytes(), []).append(
            collection
        )
    assert len(shapes) == 3
    # NP, refusal, then other text, whatever order they appear in.
    assert legend_texts(ax)[-3:] == ["NP (2)", "refusal (1)", "'dry' (1)"]
    colors = {tuple(c.get_edgecolor()[0]) for c in text_collections(ax)}
    assert len(colors) == 2  # Fill and Clay


def test_unrecognized_text_is_warned_about_once_naming_rows(frame):
    df = water(frame, ["dry", 25.0, "n/a", "dry"])
    with pytest.warns(UserWarning) as record:
        _, ax = ht.plot.profile(df, VALUE, vs="depth")
    messages = [str(w.message) for w in record if "text in rows" in str(w.message)]
    assert messages == [
        "Column 'water_content' has text in rows 0, 2, 3: 'dry' (2), 'n/a' (1). "
        "They are drawn at the left edge and counted; clean the column to "
        "remove them."
    ]
    assert ax.ags_notes == {"text_value": 3}
    assert "3 text values, shown at the left edge" in ax.texts[-1].get_text()


def test_more_than_six_texts_list_six_and_the_footnote_names_the_rest(frame):
    texts = ["a", "b", "c", "d", "e", "f", "g"]
    df = frame(
        VALUE,
        texts,
        None,
        loca_id=["A"] * 7,
        depth=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
        ground_level=[120.0] * 7,
        geology_unit=["Fill"] * 7,
    )
    with pytest.warns(UserWarning):
        _, ax = ht.plot.profile(df, VALUE, vs="depth")
    assert legend_texts(ax) == ["Fill", *(f"'{t}' (1)" for t in texts[:6])]
    assert "Not in the legend: 'g' (1)" in ax.texts[-1].get_text()
    assert len(text_points(ax)) == 7
    assert "No data" not in [text.get_text() for text in ax.texts]


def test_a_text_row_with_a_blank_depth_is_counted_blank(frame):
    df = water(frame, [20.0, "NP", 30.0, 35.0], depth=[5.0, np.nan, 15.0, 20.0])
    _, ax = ht.plot.profile(df, VALUE, vs="depth")
    assert ax.ags_notes == {"nan": 1}
    assert not len(text_points(ax))


def test_a_qualifier_on_a_text_row_is_an_error(frame):
    df = water(frame, [20.0, "NP", 30.0, 35.0], qualifier=["", "<", "", ""])
    with pytest.raises(ht.ColumnError, match=r"Rows 1 have a qualifier and text"):
        ht.plot.profile(df, VALUE, vs="depth")


def test_text_values_set_the_vertical_limits(frame):
    df = water(frame, [20.0, 25.0, 30.0, "NP"], depth=[5.0, 10.0, 15.0, 48.0])
    _, ax = ht.plot.profile(df, VALUE, vs="depth")
    assert max(ax.get_ylim()) >= 48.0


def test_text_values_beyond_ylim_are_drawn_at_the_limit(frame):
    df = water(frame, [20.0, 25.0, 30.0, "NP"], depth=[5.0, 10.0, 15.0, 40.0])
    _, ax = ht.plot.profile(df, VALUE, vs="depth", ylim=(0, 30))
    assert ax.ags_notes == {"non_plastic": 1, "beyond_limit": 1}
    [edge] = text_collections(ax)
    assert edge.get_offsets().tolist() == [[0.0, 30.0]]
    [arrow] = [t for t in ax.texts if t.get_text() == ""]
    assert arrow.xyann == (0, -10)  # down, on an inverted depth axis


def test_marker_by_and_connect_leave_text_values_alone(frame):
    df = water(frame, [20.0, "NP", 30.0, 35.0], source=["lab", "lab", "field", "lab"])
    _, ax = ht.plot.profile(df, VALUE, vs="depth", marker_by="source", connect=True)
    assert len(text_points(ax)) == 1
    for line in ax.lines:
        assert 10.0 not in line.get_ydata()


def test_a_column_of_text_only_draws_text_markers(frame):
    df = water(frame, ["NP", "NP", "NP", "NP"])
    _, ax = ht.plot.profile(df, VALUE, vs="depth")
    assert len(text_points(ax)) == 4
    assert not len(data_points(ax))
    assert "No data" not in [text.get_text() for text in ax.texts]
    assert legend_texts(ax) == ["Clay", "Fill", "NP (4)"]
