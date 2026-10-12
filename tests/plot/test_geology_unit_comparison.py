"""P07 property by geology unit: rows, points, axes and units (P07 §3, §6, §7)."""

from functools import partial

import matplotlib as mpl
import numpy as np
import pandas as pd
import pytest

import hangtu as ht

plot = partial(ht.plot.geology_unit_comparison, summary=None)

PRESETS = {
    # preset: (values, declared unit)
    "hydraulic_conductivity": ([1e-5, 3e-6, 2e-4, 5e-7, 1e-6, 4e-5], "cm/s"),
    "undrained_shear_strength": ([500.0, 1000.0, 1500.0, 2000.0, 800.0, 900.0], "psf"),
    "water_content": ([20.0, 25.0, 30.0, 35.0, 12.0, 18.0], None),
    "bulk_unit_weight": ([110.0, 115.0, 120.0, 125.0, 118.0, 122.0], "pcf"),
}


def row_names(ax):
    return [label.get_text() for label in ax.get_yticklabels()]


def points_by_unit(ax):
    """{unit: (n, 2) offsets} for the data point collections."""
    return {
        c.get_label().lstrip("_"): c.get_offsets().data
        for c in ax.collections
        if c.get_label().startswith("_")
    }


# --- renders ------------------------------------------------------------------


@pytest.mark.parametrize("name", PRESETS)
def test_renders_for_every_preset_picked_by_column_name(name, comparison, points):
    values, unit = PRESETS[name]
    fig, ax = plot(comparison(name, values, unit), name)
    assert isinstance(fig, mpl.figure.Figure)
    assert len(points(ax)) == 6
    assert ax.get_xscale() == ("log" if name == "hydraulic_conductivity" else "linear")
    assert ax.ags_notes == {}


def test_preset_and_log_override_the_column_name(comparison):
    df = comparison("hydraulic_conductivity", *PRESETS["hydraulic_conductivity"])
    _, ax = plot(df, "hydraulic_conductivity", log=False)
    assert ax.get_xscale() == "linear"
    _, ax = plot(comparison(), "undrained_shear_strength", log=True)
    assert ax.get_xscale() == "log"
    with pytest.raises(ht.HangtuError, match="preset='water_content'"):
        plot(comparison(), "undrained_shear_strength", preset="water_content")


def test_default_size_is_the_default_figure_size(comparison):
    fig, _ = plot(comparison(), "undrained_shear_strength")
    assert tuple(fig.get_size_inches()) == pytest.approx((6.5, 4.5))
    fig, _ = plot(comparison(), "undrained_shear_strength", figsize=(4, 3))
    assert tuple(fig.get_size_inches()) == pytest.approx((4, 3))


# --- rows ---------------------------------------------------------------------


def test_rows_are_sorted_by_name_first_at_the_top(comparison):
    _, ax = plot(comparison(), "undrained_shear_strength")
    assert row_names(ax) == ["Clay", "Fill", "Sand"]
    assert ax.get_ylim() == (2.5, -0.5)
    assert ax.yaxis_inverted()


def test_order_comes_first_then_the_rest_by_name(comparison):
    _, ax = plot(comparison(), "undrained_shear_strength", order=["Sand", "Gravel"])
    assert row_names(ax) == ["Sand", "Clay", "Fill"]


def test_blank_unit_is_a_row_at_the_bottom(comparison):
    df = comparison(geology_unit=["Fill", None, "Clay", "Clay", "Sand", None])
    _, ax = plot(df, "undrained_shear_strength", order=["Sand"])
    assert row_names(ax) == ["Sand", "Clay", "Fill", "(blank)"]
    blank = points_by_unit(ax)["(blank)"]
    assert np.allclose(blank[:, 1].round(), 3)
    assert mpl.colors.same_color(
        ax.collections[-1].get_facecolor()[0][:3], mpl.colors.to_rgb("0.3")
    )


def test_a_unit_with_only_blank_values_gets_no_row(comparison):
    df = comparison(values=(500.0, 1000.0, 1500.0, 2000.0, np.nan, np.nan))
    _, ax = plot(df, "undrained_shear_strength")
    assert row_names(ax) == ["Clay", "Fill"]


def test_no_horizontal_gridlines(comparison):
    fig, ax = plot(comparison(), "undrained_shear_strength")
    fig.draw_without_rendering()
    assert not any(line.get_visible() for line in ax.get_ygridlines())
    assert any(line.get_visible() for line in ax.get_xgridlines())


# --- points -------------------------------------------------------------------


def test_points_are_jittered_within_their_row(comparison):
    _, ax = plot(comparison(), "undrained_shear_strength", order=["Fill", "Clay"])
    for row, unit in enumerate(["Fill", "Clay", "Sand"]):
        offsets = points_by_unit(ax)[unit][:, 1] - row
        assert np.all(np.abs(offsets) <= 0.15)
        assert offsets.std() > 0


def test_jitter_is_the_same_on_two_calls(comparison, points):
    _, first = plot(comparison(), "undrained_shear_strength")
    _, second = plot(comparison(), "undrained_shear_strength")
    np.testing.assert_array_equal(points(first), points(second))


def test_points_take_the_unit_color(comparison):
    _, ax = plot(comparison(), "undrained_shear_strength")
    colors = ht.plot.legend_handles(["Clay", "Fill", "Sand"])
    for handle in colors:
        (collection,) = [
            c for c in ax.collections if c.get_label() == f"_{handle.get_label()}"
        ]
        assert mpl.colors.same_color(
            collection.get_facecolor()[0][:3], handle.get_facecolor()[:3]
        )


def test_color_by_none_draws_every_unit_in_neutral_gray(comparison):
    _, ax = plot(comparison(), "undrained_shear_strength", color_by=None)
    for collection in ax.collections:
        assert mpl.colors.same_color(
            collection.get_facecolor()[0][:3], mpl.colors.to_rgb("0.3")
        )


def test_points_false_draws_no_points(comparison, points):
    _, ax = plot(comparison(), "undrained_shear_strength", points=False)
    assert len(points(ax)) == 0
    assert row_names(ax) == ["Clay", "Fill", "Sand"]


# --- values, units and notes --------------------------------------------------


def test_label_has_units_and_values_are_converted(comparison, points):
    _, ax = plot(comparison(), "undrained_shear_strength", display_units="SI")
    assert ax.get_xlabel() == "Undrained shear strength, s_u (kPa)"
    assert points(ax)[:, 0].max() == pytest.approx(95.76, abs=0.01)


def test_unknown_units_say_so_and_warn(comparison):
    with pytest.warns(UserWarning, match="undrained_shear_strength"):
        _, ax = plot(comparison(unit=None), "undrained_shear_strength")
    assert ax.get_xlabel() == "Undrained shear strength, s_u (units unknown)"


def test_values_at_or_below_zero_are_counted_on_a_log_axis(comparison, points):
    values = (1e-5, 0.0, -1e-6, 2e-4, 5e-7, 1e-6)
    _, ax = plot(
        comparison("hydraulic_conductivity", values, "cm/s"), "hydraulic_conductivity"
    )
    assert ax.ags_notes == {"log_nonpositive": 2}
    assert len(points(ax)) == 4


def test_blank_values_are_skipped_and_not_counted(comparison, points):
    df = comparison(values=(500.0, np.nan, 1500.0, np.nan, 800.0, 1200.0))
    _, ax = plot(df, "undrained_shear_strength")
    assert len(points(ax)) == 4
    assert ax.ags_notes == {}


def test_empty_input_says_no_data(comparison):
    df = comparison().iloc[0:0]
    _, ax = plot(df, "undrained_shear_strength")
    assert "No data" in [text.get_text() for text in ax.texts]
    assert row_names(ax) == []


def test_us_and_si_put_points_in_the_same_place(comparison, assert_us_si_equivalent):
    assert_us_si_equivalent(
        plot,
        comparison(),
        ("stress", "dimensionless"),
        value="undrained_shear_strength",
    )


def test_no_global_state(comparison, assert_no_global_state):
    assert_no_global_state(plot, comparison(), value="undrained_shear_strength")


def test_draws_into_a_sheet_panel(comparison, assert_no_global_state):
    sheet = ht.Sheet(size="letter", layout=(1, 2))
    assert_no_global_state(
        plot, comparison(), value="undrained_shear_strength", ax=sheet[1]
    )
    assert row_names(sheet[1]) == ["Clay", "Fill", "Sand"]


# --- errors -------------------------------------------------------------------


@pytest.mark.parametrize("missing", ["undrained_shear_strength", "geology_unit"])
def test_missing_column_lists_the_columns(missing, comparison):
    df = comparison().drop(columns=missing)
    with pytest.raises(ht.ColumnError, match=f"Column '{missing}' not found"):
        plot(df, "undrained_shear_strength")


def test_text_in_the_value_column_is_an_error(comparison):
    df = comparison(values=("NP", 1000.0, 1500.0, 2000.0, 800.0, 1200.0))
    with pytest.raises(ht.HangtuError, match="0"):
        plot(df, "undrained_shear_strength")


def test_color_by_another_column_is_an_error(comparison):
    df = comparison(source=["lab"] * 6)
    with pytest.raises(ht.HangtuError, match='"geology_unit" or None'):
        plot(df, "undrained_shear_strength", color_by="source")


def test_frame_is_not_changed(comparison):
    df = comparison(geology_unit=["Fill", None, "Clay", "Clay", "Sand", None])
    before = df.copy()
    plot(df, "undrained_shear_strength")
    pd.testing.assert_frame_equal(df, before)
