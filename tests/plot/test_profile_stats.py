"""P01 secondary depth axis and stats box (P01 §6, §8)."""

import matplotlib.pyplot as plt
import numpy as np
import pytest

import ags_kit as ak
from ags_kit.plot._overlays import format_number, stats_table

# --- secondary depth axis ------------------------------------------------------------


def secondary_axis(ax):
    (child,) = ax.child_axes
    return child


@pytest.mark.parametrize(("system", "level"), [("US", 120.0), ("SI", 120.0 * 0.3048)])
def test_secondary_depth_is_ground_level_minus_elevation(frame, system, level):
    fig, ax = ak.plot.profile(
        frame(), "undrained_shear_strength", secondary="depth", display_units=system
    )
    fig.canvas.draw()
    depth = secondary_axis(ax)
    assert depth.get_ylabel() == f"Depth ({'ft' if system == 'US' else 'm'})"
    # Depth d is drawn at elevation ground level - d, so it increases downward.
    for d in depth.get_yticks():
        drawn = depth.transData.transform((0.0, d))[1]
        assert drawn == pytest.approx(ax.transData.transform((0.0, level - d))[1])
    first, last = depth.get_yticks()[[0, -1]]
    assert (
        depth.transData.transform((0.0, first))[1]
        > depth.transData.transform((0.0, last))[1]
    )


def test_secondary_depth_ticks_are_nice_steps(frame):
    fig, ax = ak.plot.profile(frame(), "undrained_shear_strength", secondary="depth")
    fig.canvas.draw()
    ticks = secondary_axis(ax).get_yticks()
    steps = np.diff(ticks)
    assert np.allclose(steps, steps[0])
    assert steps[0] in (1.0, 2.0, 5.0, 10.0)


def test_secondary_moves_the_legend_and_footnote_clear(frame):
    df = frame(values=[np.nan, 1000.0, 1500.0, 2000.0])
    fig, plain = ak.plot.profile(df, "undrained_shear_strength")
    fig.canvas.draw()
    fig2, ax = ak.plot.profile(df, "undrained_shear_strength", secondary="depth")
    fig2.canvas.draw()

    def gap(axes, artist):
        return (
            (artist.get_window_extent().x0 - axes.get_window_extent().x1)
            * 72
            / axes.figure.dpi
        )

    assert gap(ax, ax.get_legend()) - gap(plain, plain.get_legend()) == pytest.approx(
        42.0, abs=2
    )
    assert gap(ax, ax.texts[-1]) - gap(plain, plain.texts[-1]) == pytest.approx(
        42.0, abs=2
    )


def test_secondary_with_several_ground_levels_is_an_error(frame):
    df = frame(ground_level=[120.0, 120.0, 118.0, 118.0])
    figures = plt.get_fignums()
    with pytest.raises(ak.AgsKitError, match="needs one ground level"):
        ak.plot.profile(df, "undrained_shear_strength", secondary="depth")
    assert plt.get_fignums() == figures


def test_secondary_on_a_depth_plot_is_an_error(frame):
    with pytest.raises(ak.AgsKitError, match="already against depth"):
        ak.plot.profile(
            frame(), "undrained_shear_strength", vs="depth", secondary="depth"
        )


def test_secondary_must_be_depth(frame):
    with pytest.raises(ak.AgsKitError, match='secondary must be "depth"'):
        ak.plot.profile(frame(), "undrained_shear_strength", secondary="elevation")


def test_secondary_leaves_no_global_state(frame, assert_no_global_state):
    assert_no_global_state(
        ak.plot.profile, frame(), value="undrained_shear_strength", secondary="depth"
    )


# --- stats box ----------------------------------------------------------------------


def stats_text(ax):
    (box,) = [text for text in ax.texts if text.get_bbox_patch() is not None]
    return box


def rows(ax):
    return [line.split() for line in stats_text(ax).get_text().splitlines()]


# Hand-calculated for frame(): Fill 500, 1000; Clay 1500, 2000 (psf).
#   Fill: mean 750, sample std 353.55, median 750.
#   Clay: mean 1750, std 353.55, median 1750.
#   All:  mean 1250, std sqrt(1,250,000 / 3) = 645.50, median 1250.
GOLDEN = [
    ["n", "mean", "std", "median", "min", "max"],
    ["Clay", "2", "1,750", "354", "1,750", "1,500", "2,000"],
    ["Fill", "2", "750", "354", "750", "500", "1,000"],
    ["All", "4", "1,250", "645", "1,250", "500", "2,000"],
]


def test_stats_box_golden_values(frame):
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength", stats_box=True)
    assert rows(ax) == GOLDEN
    box = stats_text(ax)
    assert box.get_fontsize() == 7
    assert box.get_position() == (0.02, 0.02)


def test_stats_box_with_chosen_statistics(frame):
    _, ax = ak.plot.profile(
        frame(), "undrained_shear_strength", stats_box=["count", "mean", "cov"]
    )
    # CoV = 353.55 / 750 = 0.47 and 353.55 / 1750 = 0.20; all 645.50 / 1250 = 0.52.
    assert rows(ax) == [
        ["n", "mean", "CoV"],
        ["Clay", "2", "1,750", "0.20"],
        ["Fill", "2", "750", "0.47"],
        ["All", "4", "1,250", "0.52"],
    ]


def test_stats_are_in_display_units(frame):
    _, ax = ak.plot.profile(
        frame(), "undrained_shear_strength", stats_box=["mean"], display_units="SI"
    )
    # 750 psf = 35.91 kPa; 1250 psf = 59.85 kPa.
    assert rows(ax)[2] == ["Fill", "35.9"]
    assert rows(ax)[3] == ["All", "59.9"]


def test_std_is_a_dash_for_a_single_value(frame):
    df = frame().iloc[:3]
    _, ax = ak.plot.profile(df, "undrained_shear_strength", stats_box=["count", "std"])
    assert rows(ax)[1] == ["Clay", "1", "—"]


def test_one_unit_has_no_all_row(frame):
    df = frame(geology_unit=["Fill"] * 4)
    _, ax = ak.plot.profile(df, "undrained_shear_strength", stats_box=["count"])
    assert rows(ax) == [["n"], ["Fill", "4"]]


def test_ungrouped_data_shows_all_only(frame):
    _, ax = ak.plot.profile(
        frame(), "undrained_shear_strength", color_by=None, stats_box=["count"]
    )
    assert rows(ax) == [["n"], ["All", "4"]]


def test_more_than_six_units_shows_all_only():
    groups = np.array([f"unit {i}" for i in range(7)], dtype=object)
    table = stats_table(np.arange(7.0), groups, ["count"])
    assert table == [["", "n"], ["All", "7"]]


def test_six_units_are_listed():
    groups = np.array([f"unit {i}" for i in range(6)], dtype=object)
    table = stats_table(np.arange(6.0), groups, ["count"])
    assert len(table) == 8


def test_cov_is_a_dash_on_an_interval_scale():
    table = stats_table(
        np.array([1.0, 2.0]), np.array([None, None]), ["cov"], interval=True
    )
    assert table[1] == ["All", "—"]


def test_stats_are_of_the_values_drawn(frame):
    df = frame(
        "hydraulic_conductivity",
        [1e-5, np.nan, 0.0, 2e-4],
        "cm/s",
        qualifier=["", "", "", ">"],
    )
    _, ax = ak.plot.profile(
        df,
        "hydraulic_conductivity",
        preset="hydraulic_conductivity",
        stats_box=["count", "max"],
        xlim=(1e-6, 1e-4),
    )
    # The blank and the 0 aren't drawn; 2e-4 is beyond the limit, drawn at the
    # edge, and counts at its reported value.
    assert rows(ax)[-1] == ["All", "2", "2.00e-04"]


def test_stats_box_sits_above_the_note(frame):
    _, ax = ak.plot.profile(
        frame(), "undrained_shear_strength", stats_box=True, note="Draft\nfor review"
    )
    fig = ax.figure
    fig.canvas.draw()
    box = stats_text(ax).get_bbox_patch().get_window_extent()
    (note,) = [t for t in ax.texts if t.get_text() == "Draft\nfor review"]
    assert box.y0 > note.get_window_extent().y1


@pytest.mark.parametrize("stats_box", [["count", "mode"], [], "mean", 3])
def test_bad_stats_box_lists_the_statistics(frame, stats_box):
    with pytest.raises(ak.AgsKitError, match="stats_box"):
        ak.plot.profile(frame(), "undrained_shear_strength", stats_box=stats_box)


def test_unknown_statistic_names_the_allowed_ones(frame):
    with pytest.raises(ak.AgsKitError, match="count, mean, std, cov, median, min, max"):
        ak.plot.profile(frame(), "undrained_shear_strength", stats_box=["mode"])


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (1290.4, "1,290"),
        (344.0, "344"),
        (15.63, "15.6"),
        (0.01234, "0.0123"),
        (2.3e-5, "2.30e-05"),
        (-15.6, "-15.6"),
        (1234567.0, "1.23e+06"),
        (0.0, "0"),
    ],
)
def test_format_number(value, text):
    assert format_number(value) == text
