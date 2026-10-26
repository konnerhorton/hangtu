"""legend= on every plot with a legend (docs/work/p00-layout-defaults.md, AC 7-9)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.plot._profile import SECONDARY_SPACE

LENGTHS = {"depth": "ft", "ground_level": "ft"}


def spt():
    df = pd.DataFrame(
        {
            "loca_id": ["A", "A", "B", "B"],
            "depth": [5.0, 10.0, 15.0, 20.0],
            "ground_level": [120.0] * 4,
            "geology_unit": ["Fill", "Fill", "Sand", "Sand"],
            "spt_n": [4.0, 9.0, 22.0, 35.0],
            "spt_refusal": [False] * 4,
        }
    )
    return ht.set_units(df, LENGTHS)


def atterberg():
    df = pd.DataFrame(
        {
            "depth": [5.0, 10.0, 15.0, 20.0],
            "geology_unit": ["Clay", "Clay", "Silt", "Silt"],
            "water_content": [25.0, 30.0, 22.0, 35.0],
            "plastic_limit": [18.0, 20.0, 15.0, 24.0],
            "liquid_limit": [40.0, 45.0, 30.0, 52.0],
        }
    )
    return ht.set_units(df, {"depth": "ft"})


def grading():
    df = pd.DataFrame(
        {
            "specimen_id": ["S1"] * 3 + ["S2"] * 3,
            "particle_size": [0.1, 1.0, 10.0] * 2,
            "percent_passing": [10.0, 50.0, 100.0, 5.0, 30.0, 90.0],
        }
    )
    return ht.set_units(df, {"particle_size": "mm"})


NAMES = [
    "profile",
    "spt_profile",
    "water_content_profile",
    "spt_histogram",
    "plasticity_chart",
    "geology_unit_comparison",
    "grain_size",
]


@pytest.fixture
def plots(frame, comparison):
    """Each plot with a legend, drawn from small data, by name."""
    return {
        "profile": lambda **kw: ht.plot.profile(
            frame(), "undrained_shear_strength", **kw
        ),
        "spt_profile": lambda **kw: ht.plot.spt_profile(spt(), **kw),
        "water_content_profile": lambda **kw: ht.plot.water_content_profile(
            atterberg(), vs="depth", **kw
        ),
        "spt_histogram": lambda **kw: ht.plot.spt_histogram(spt(), **kw),
        "plasticity_chart": lambda **kw: ht.plot.plasticity_chart(atterberg(), **kw),
        "geology_unit_comparison": lambda **kw: ht.plot.geology_unit_comparison(
            comparison(), "undrained_shear_strength", **kw
        ),
        "grain_size": lambda **kw: ht.plot.grain_size(grading(), **kw),
    }


@pytest.fixture(autouse=True)
def _no_hints():
    ht.settings.hints = False


@pytest.mark.parametrize("name", NAMES)
def test_a_bad_legend_raises_naming_the_choices(plots, name):
    with pytest.raises(ht.HangtuError, match=r'"auto", "inside", "bottom", "right"'):
        plots[name](legend="left")


@pytest.mark.parametrize("name", NAMES)
def test_legend_false_draws_none_and_keeps_the_counts(plots, name):
    _, shown = plots[name]()
    _, ax = plots[name](legend=False)
    assert ax.get_legend() is None
    assert ax.ags_notes == shown.ags_notes


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("legend", ["auto", "inside", "bottom", "right", True])
def test_every_choice_draws_a_legend(plots, name, legend):
    _, ax = plots[name](legend=legend)
    assert ax.get_legend() is not None


def test_legend_false_still_writes_the_footnote_below_the_x_label(frame):
    df = frame(values=(500.0, np.nan, 1500.0, 2000.0))
    _, ax = ht.plot.profile(df, "undrained_shear_strength", legend=False)
    (footnote,) = [t for t in ax.texts if "blank" in t.get_text()]
    ax.figure.draw_without_rendering()
    renderer = ax.figure.canvas.get_renderer()
    assert footnote.get_window_extent(renderer).y1 < ax.bbox.y0
    assert ax.ags_notes == {"nan": 1}


def anchor_x(ax):
    """The display x of a right legend's anchor, after drawing."""
    ax.figure.draw_without_rendering()
    return ax.get_legend().get_bbox_to_anchor().x0


@pytest.mark.parametrize("secondary", [None, "depth"])
def test_right_is_where_the_legend_used_to_go(frame, secondary):
    _, ax = ht.plot.profile(
        frame(), "undrained_shear_strength", secondary=secondary, legend="right"
    )
    offset = SECONDARY_SPACE if secondary else 0.0
    x = anchor_x(ax)
    points = ax.figure.dpi / 72
    expected = ax.bbox.x0 + 1.02 * ax.bbox.width + offset * points
    assert x == pytest.approx(expected, abs=1 * points)
    assert ax.get_legend()._loc == 2  # upper left of the anchor
    assert not ax.get_legend().get_frame_on()


def test_grain_size_puts_its_legend_below_by_default():
    _, ax = ht.plot.grain_size(grading())
    ax.figure.draw_without_rendering()
    assert ax.get_legend().get_window_extent().y1 < ax.bbox.y0
