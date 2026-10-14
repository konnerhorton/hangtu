"""Plots take a project's geology map from the data (datasets.md §5.2, P00 §10).

A dataset carries the map's colors in ``df.attrs["palette"]`` and its order as
the categories of ``geology_unit``.
"""

import matplotlib.pyplot as plt
import pandas as pd
import pytest
from matplotlib.colors import to_rgba

import hangtu as ht

ORDER = ["Fill", "Alluvium", "Terrace"]  # not alphabetical
COLORS = {"Fill": "#a0a0a0", "Alluvium": "tan", "Terrace": "#d9b26f"}


@pytest.fixture
def data():
    df = pd.DataFrame(
        {
            "loca_id": ["BH1"] * 6,
            "ground_level": [10.0] * 6,
            "depth": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "spt_refusal": [False] * 6,
            "spt_n": [5, 10, 15, 20, 25, 30],
            "water_content": [20.0, 25.0, 30.0, 22.0, 28.0, 18.0],
            "geology_unit": pd.Categorical(
                ["Terrace", "Alluvium", "Fill", "Terrace", "Alluvium", "Fill"],
                categories=ORDER,
                ordered=True,
            ),
        }
    )
    df = ht.set_units(df, {"depth": "m", "ground_level": "m", "water_content": "%"})
    df.attrs["palette"] = COLORS
    return df


def _legend(ax):
    return [text.get_text() for text in ax.get_legend().get_texts()]


def _close(fig):
    plt.close(fig)


def test_profile_uses_the_map_colors_and_order(data):
    fig, ax = ht.plot.profile(data, "water_content")
    labels = _legend(ax)
    assert [label for label in labels if label in ORDER] == ORDER
    colors = {
        c.get_label(): c.get_facecolor()[0]
        for c in ax.collections
        if c.get_label() in ORDER
    }
    assert colors["Alluvium"] == pytest.approx(to_rgba("tan"))
    _close(fig)


def test_spt_histogram_follows_the_map_order(data):
    fig, ax = ht.plot.spt_histogram(data)
    labels = [label.split(" (n = ")[0] for label in _legend(ax)]  # "Fill (n = 2)"
    assert labels == ORDER
    _close(fig)


def test_geology_unit_comparison_rows_follow_the_map_order(data):
    fig, ax = ht.plot.geology_unit_comparison(data, "water_content")
    rows = [label.get_text().split("\n")[0] for label in ax.get_yticklabels()]
    assert [row for row in rows if row in ORDER] == ORDER
    _close(fig)


def test_session_palette_still_wins(data):
    ht.settings.palette = {"Alluvium": "black"}
    fig, ax = ht.plot.profile(data, "water_content")
    colors = {
        c.get_label(): c.get_facecolor()[0]
        for c in ax.collections
        if c.get_label() in ORDER
    }
    assert colors["Alluvium"] == pytest.approx(to_rgba("black"))
    _close(fig)
