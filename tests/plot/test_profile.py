"""P01 core profile: points, axes, labels, units and notes (P01 §6, §7, §11)."""

from functools import partial

import matplotlib as mpl
import numpy as np
import pandas as pd
import pytest

import ags_kit as ak

PRESETS = {
    # preset: (values, declared unit, quantity kind)
    "hydraulic_conductivity": (
        [1e-5, 3e-6, 2e-4, 5e-7],
        "cm/s",
        "hydraulic_conductivity",
    ),
    "undrained_shear_strength": ([500.0, 1000.0, 1500.0, 2000.0], "psf", "stress"),
    "water_content": ([20.0, 25.0, 30.0, 35.0], None, "percent"),
    "bulk_unit_weight": ([110.0, 115.0, 120.0, 125.0], "pcf", "unit_weight"),
}


def unit_color(ax, unit):
    (collection,) = [c for c in ax.collections if c.get_label() == unit]
    return tuple(collection.get_facecolor()[0])


# --- renders ------------------------------------------------------------------


@pytest.mark.parametrize("name", PRESETS)
@pytest.mark.parametrize("vs", ["depth", "elevation"])
def test_renders_for_every_preset_and_vs(name, vs, frame, points):
    values, unit, _ = PRESETS[name]
    fig, ax = ak.plot.profile(frame(name, values, unit), name, preset=name, vs=vs)
    assert isinstance(fig, mpl.figure.Figure)
    assert len(points(ax)) == 4
    assert ax.get_xscale() == ("log" if name == "hydraulic_conductivity" else "linear")
    assert ax.ags_notes == {}


def test_default_size_is_the_profile_size_plus_the_legend(frame):
    fig, _ = ak.plot.profile(frame(), "undrained_shear_strength")
    assert tuple(fig.get_size_inches()) == pytest.approx((5.5, 6.5))
    fig, _ = ak.plot.profile(frame(), "undrained_shear_strength", figsize=(4, 4))
    assert tuple(fig.get_size_inches()) == pytest.approx((4, 4))


# --- vertical axis ------------------------------------------------------------


def test_depth_axis_starts_at_zero_at_the_top(frame):
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength", vs="depth")
    bottom, top = ax.get_ylim()
    assert top == 0
    assert bottom == 20.0
    assert ax.yaxis_inverted()
    assert ax.get_ylabel() == "Depth (ft)"


def test_elevation_increases_upward_and_is_the_default(frame, points):
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength")
    bottom, top = ax.get_ylim()
    assert bottom < 100.0 and top > 115.0
    assert not ax.yaxis_inverted()
    # P01 §12: GL 120.0 ft, depth 15.0 ft -> 105.0 ft.
    assert sorted(points(ax)[:, 1]) == pytest.approx([100.0, 105.0, 110.0, 115.0])


def test_elevation_label_carries_the_datum(frame):
    with ak.settings.override(vertical_datum="NAVD88"):
        _, ax = ak.plot.profile(frame(), "undrained_shear_strength")
    assert ax.get_ylabel() == "Elevation (ft, NAVD88)"


# --- value axis ---------------------------------------------------------------


def test_ratio_scale_starts_at_zero_and_unit_weight_does_not(frame):
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength")
    assert ax.get_xlim() == (0.0, 2000.0)
    values, unit, _ = PRESETS["bulk_unit_weight"]
    df = frame("bulk_unit_weight", values, unit)
    _, ax = ak.plot.profile(df, "bulk_unit_weight", preset="bulk_unit_weight")
    assert ax.get_xlim()[0] > 100.0


def test_x_axis_is_at_the_bottom_by_default(frame):
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength")
    assert ax.xaxis.get_label_position() == "bottom"
    assert ax.xaxis.get_ticks_position() == "bottom"
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength", xaxis_position="top")
    assert ax.xaxis.get_label_position() == "top"
    assert ax.xaxis.get_ticks_position() == "top"


def test_value_label_comes_from_label_then_preset_then_registry_then_column(
    frame, points
):
    df = frame()
    _, ax = ak.plot.profile(df, "undrained_shear_strength", label="Lab s_u")
    assert ax.get_xlabel() == "Lab s_u (psf)"
    _, ax = ak.plot.profile(df, "undrained_shear_strength")
    assert ax.get_xlabel() == "Undrained shear strength, s_u (psf)"
    df = frame("su_lab", [500.0, 1000.0, 1500.0, 2000.0], "kPa")
    _, ax = ak.plot.profile(df, "su_lab", preset="undrained_shear_strength")
    assert ax.get_xlabel() == "Undrained shear strength, s_u (psf)"
    assert sorted(points(ax)[:, 0]) == pytest.approx(
        [10442.7, 20885.4, 31328.1, 41770.9], rel=1e-4
    )
    df = frame("vane_reading", [1.0, 2.0, 3.0, 4.0], "kPa")
    _, ax = ak.plot.profile(df, "vane_reading")
    assert ax.get_xlabel() == "vane_reading (kPa)"


def test_display_overrides_apply(frame, points):
    with ak.settings.override(display_overrides={"stress": "ksf"}):
        _, ax = ak.plot.profile(frame(), "undrained_shear_strength")
    assert ax.get_xlabel() == "Undrained shear strength, s_u (ksf)"
    assert points(ax)[:, 0].max() == pytest.approx(2.0)


# --- units unknown ------------------------------------------------------------


def test_unknown_value_units_label_and_warn(frame):
    df = frame(unit=None)
    with pytest.warns(UserWarning, match="'undrained_shear_strength' has no units"):
        _, ax = ak.plot.profile(df, "undrained_shear_strength")
    assert ax.get_xlabel() == "Undrained shear strength, s_u (units unknown)"


def test_unknown_vertical_units_label_and_warn(frame):
    df = frame().drop(columns="ground_level")
    df.attrs["units"].pop("depth")
    df.attrs["units"].pop("ground_level")
    with (
        ak.settings.override(hints=False),
        pytest.warns(UserWarning, match="'depth' has no units"),
    ):
        _, ax = ak.plot.profile(df, "undrained_shear_strength", color_by=None)
    assert ax.get_ylabel() == "Depth (units unknown)"


def test_percent_needs_no_units(frame):
    values, _, _ = PRESETS["water_content"]
    _, ax = ak.plot.profile(frame("water_content", values, None), "water_content")
    assert ax.get_xlabel() == "Water content, w (%)"


def test_units_argument_overrides_declared_units(frame, points):
    _, ax = ak.plot.profile(
        frame(), "undrained_shear_strength", units={"undrained_shear_strength": "kPa"}
    )
    assert points(ax)[:, 0].max() == pytest.approx(41770.9, rel=1e-4)


# --- notes and edges ----------------------------------------------------------


def test_zero_on_a_linear_axis_is_drawn(frame, points):
    df = frame(values=[0.0, 1000.0, 1500.0, 2000.0])
    _, ax = ak.plot.profile(df, "undrained_shear_strength")
    assert ax.ags_notes == {}
    assert len(points(ax)) == 4


def test_a_blank_depth_is_counted(frame):
    df = frame(depth=[5.0, np.nan, 15.0, 20.0])
    _, ax = ak.plot.profile(df, "undrained_shear_strength")
    assert ax.ags_notes == {"nan": 1}


# --- empty and single point ---------------------------------------------------


@pytest.mark.parametrize("rows", [0, 4])
def test_no_data_draws_labeled_empty_axes(rows, frame, points):
    df = frame(values=[np.nan] * 4).iloc[:rows]
    _, ax = ak.plot.profile(
        df, "undrained_shear_strength", preset="undrained_shear_strength"
    )
    assert len(points(ax)) == 0
    assert "No data" in [text.get_text() for text in ax.texts]
    assert ax.get_xlabel() == "Undrained shear strength, s_u (psf)"
    assert ax.ags_notes == ({"nan": 4} if rows else {})
    assert ax.get_legend() is None


def test_a_single_point_uses_the_typical_range(frame):
    df = frame().iloc[:1]
    _, ax = ak.plot.profile(
        df, "undrained_shear_strength", preset="undrained_shear_strength"
    )
    # 0-300 kPa is 0-6,266 psf, rounded out to a nice limit.
    assert ax.get_xlim() == (0.0, 7000.0)
    lo, hi = ax.get_ylim()
    assert lo < 115.0 < hi


def test_a_single_point_without_a_preset_is_off_the_frame(frame):
    _, ax = ak.plot.profile(frame().iloc[:1], "undrained_shear_strength")
    lo, hi = ax.get_xlim()
    assert lo < 500.0 < hi


# --- color --------------------------------------------------------------------


def test_unit_colors_match_legend_handles(frame):
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength")
    for handle in ak.plot.legend_handles(["Clay", "Fill"]):
        assert unit_color(ax, handle.get_label()) == tuple(handle.get_facecolor())
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert labels == ["Clay", "Fill"]


def test_palette_argument_colors_units(frame):
    _, ax = ak.plot.profile(
        frame(), "undrained_shear_strength", palette={"Fill": "tan", "Clay": "olive"}
    )
    assert unit_color(ax, "Fill") == mpl.colors.to_rgba("tan")


def test_color_by_none_draws_one_neutral_color_without_unit_legend(frame):
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength", color_by=None)
    (collection,) = ax.collections
    assert tuple(collection.get_facecolor()[0]) == mpl.colors.to_rgba("0.3")
    assert ax.get_legend() is None


def test_rows_with_a_blank_unit_are_drawn_gray_and_listed(frame, points):
    df = frame(geology_unit=["Fill", None, "Clay", "Clay"])
    _, ax = ak.plot.profile(df, "undrained_shear_strength")
    assert unit_color(ax, "(blank)") == mpl.colors.to_rgba("0.3")
    assert len(points(ax)) == 4
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert labels == ["Clay", "Fill", "(blank)"]


def test_a_unit_with_nothing_drawn_has_no_legend_entry(frame):
    df = frame(values=[500.0, 1000.0, np.nan, np.nan])
    _, ax = ak.plot.profile(df, "undrained_shear_strength")
    assert [t.get_text() for t in ax.get_legend().get_texts()] == ["Fill"]


def test_color_by_another_column(frame):
    df = frame(source=["lab", "field", "lab", "field"])
    _, ax = ak.plot.profile(df, "undrained_shear_strength", color_by="source")
    assert [t.get_text() for t in ax.get_legend().get_texts()] == ["field", "lab"]


# --- hints and errors ---------------------------------------------------------


def test_one_hint_lists_the_missing_optional_columns(frame):
    df = frame().drop(columns=["loca_id", "geology_unit", "ground_level"])
    with pytest.warns(ak.AgsKitHint) as record:
        ak.plot.profile(df, "undrained_shear_strength")
    assert len(record) == 1
    message = str(record[0].message)
    assert "'geology_unit'" in message
    assert "'loca_id'" in message
    assert "'ground_level'" in message


def test_no_ground_level_hint_when_plotting_elevation(frame):
    df = frame(elevation=[115.0, 110.0, 105.0, 100.0])
    df = ak.set_units(df.drop(columns=["ground_level", "loca_id"]), {"elevation": "ft"})
    with pytest.warns(ak.AgsKitHint) as record:
        ak.plot.profile(df, "undrained_shear_strength")
    assert "ground_level" not in str(record[0].message)


def test_missing_value_column_lists_the_columns(frame):
    with pytest.raises(ak.ColumnError, match=r"Column 'k' not found\. Available"):
        ak.plot.profile(frame(), "k")


def test_text_in_the_value_column_names_the_rows(frame):
    df = frame(values=[500.0, "NP", 1500.0, "2 ksf"])
    with pytest.raises(ak.ColumnError, match=r"rows 1 \('NP'\), 3 \('2 ksf'\)"):
        ak.plot.profile(df, "undrained_shear_strength")


def test_a_preset_for_another_quantity_is_an_error(frame):
    with pytest.raises(ak.AgsKitError, match=r"is for a percent.*is a stress"):
        ak.plot.profile(frame(), "undrained_shear_strength", preset="water_content")


def test_unknown_preset_is_an_error(frame):
    with pytest.raises(ak.AgsKitError, match="no preset named 'su'"):
        ak.plot.profile(frame(), "undrained_shear_strength", preset="su")


def test_color_by_a_missing_column_is_an_error(frame):
    with pytest.raises(ak.ColumnError, match="color_by='source' isn't a column"):
        ak.plot.profile(frame(), "undrained_shear_strength", color_by="source")


def test_bad_xaxis_position_is_an_error(frame):
    with pytest.raises(ak.AgsKitError, match="xaxis_position"):
        ak.plot.profile(frame(), "undrained_shear_strength", xaxis_position="left")


# --- contract -----------------------------------------------------------------


def test_no_global_state(assert_no_global_state, frame):
    assert_no_global_state(
        ak.plot.profile, frame(), value="undrained_shear_strength", font_size=12
    )


def test_draws_into_a_sheet_panel(assert_no_global_state, frame, points):
    sheet = ak.Sheet("letter", layout=(1, 2))
    assert_no_global_state(
        ak.plot.profile, frame(), value="undrained_shear_strength", ax=sheet[1]
    )
    fig, ax = ak.plot.profile(frame(), "undrained_shear_strength", ax=sheet[0])
    assert fig is sheet.figure
    assert ax is sheet[0]
    assert len(points(ax)) == 4


@pytest.mark.parametrize("name", PRESETS)
@pytest.mark.parametrize("vs", ["depth", "elevation"])
def test_us_and_si_put_points_in_the_same_place(
    name, vs, assert_us_si_equivalent, frame
):
    values, unit, quantity = PRESETS[name]
    df = frame(name, values, unit)
    plot = partial(ak.plot.profile, value=name, preset=name, vs=vs)
    assert_us_si_equivalent(plot, df, (quantity, "length"))


@pytest.mark.parametrize(
    "arguments",
    [
        {"marker_by": "source"},
        {"connect": True},
        {"secondary": "depth"},
        {"strata": pd.DataFrame()},
        {"water_level": 110.0},
        {"ranges": pd.DataFrame()},
        {"design_lines": pd.DataFrame()},
        {"reference_lines": [(1000.0, "limit")]},
        {"stats_box": True},
        {"note": "draft"},
    ],
)
def test_arguments_not_built_yet_say_so(arguments, frame):
    with pytest.raises(NotImplementedError, match="isn't available yet"):
        ak.plot.profile(frame(), "undrained_shear_strength", **arguments)
