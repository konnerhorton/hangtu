import warnings

import matplotlib.pyplot as plt
import pandas as pd
import pytest
from matplotlib.lines import Line2D

import ags_kit as ak
from ags_kit.plot.common import Notes, add_legend, hint_missing


def entries(n, prefix="Unit"):
    return [Line2D([], [], label=f"{prefix} {i}") for i in range(n)]


@pytest.mark.parametrize(("n", "columns"), [(1, 1), (12, 1), (13, 2), (30, 3)])
def test_legend_columns_hold_up_to_12_entries(n, columns):
    _, ax = plt.subplots()
    legend = add_legend(ax, [entries(n)], Notes())
    assert legend._ncols == columns
    assert len(legend.get_texts()) == n


def test_legend_sits_outside_right_without_a_frame():
    _, ax = plt.subplots()
    legend = add_legend(ax, [entries(2), entries(1, "Marker")], Notes())
    assert not legend.get_frame_on()
    assert legend.get_texts()[0].get_fontsize() == 8
    assert legend._loc == 2  # upper left of the anchor
    assert tuple(legend.get_bbox_to_anchor()._bbox.p0) == (1.02, 1.0)


def test_sections_keep_their_order():
    _, ax = plt.subplots()
    legend = add_legend(ax, [entries(2), entries(1, "Edge")], Notes())
    assert [t.get_text() for t in legend.get_texts()] == ["Unit 0", "Unit 1", "Edge 0"]


def test_more_than_30_entries_gives_a_note_instead():
    _, ax = plt.subplots()
    notes = Notes()
    assert add_legend(ax, [entries(29), entries(2, "Marker")], notes) is None
    assert ax.get_legend() is None
    assert notes.lines() == ["29 geology units: see ak.plot.legend_handles()"]


def test_no_entries_no_legend():
    _, ax = plt.subplots()
    assert add_legend(ax, [[], []], Notes()) is None


OPTIONAL = {
    "geology_unit": "points are not colored by geology",
    "loca_id": "connect= is unavailable",
    "depth": "unused",
}


def test_one_hint_per_call_listing_every_missing_column():
    df = pd.DataFrame({"depth": [1.0]})
    with pytest.warns(ak.AgsKitHint) as record:
        missing = hint_missing(df, OPTIONAL)
    assert missing == ["geology_unit", "loca_id"]
    assert len(record) == 1
    assert str(record[0].message) == (
        "No 'geology_unit' column: points are not colored by geology. "
        "No 'loca_id' column: connect= is unavailable. "
        "(Turn hints off with ak.settings.hints = False.)"
    )
    assert record[0].filename == __file__


def test_no_hint_when_nothing_is_missing():
    df = pd.DataFrame(columns=list(OPTIONAL))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert hint_missing(df, OPTIONAL) == []


def test_no_hint_when_hints_are_off():
    ak.settings.hints = False
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert hint_missing(pd.DataFrame(), OPTIONAL) == list(OPTIONAL)
