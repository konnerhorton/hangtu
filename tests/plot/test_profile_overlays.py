"""P01 overlays (P01 §8, §11): strata and water levels."""

import numpy as np
import pandas as pd
import pytest
from matplotlib.colors import to_rgb

import hangtu as ak
from hangtu.plot import _layers
from hangtu.plot._overlays import WATER_COLOR

FT = 0.3048


def strata_frame(pair="depth", units="ft", **columns):
    data = {
        "geology_unit": ["Fill", "Clay"],
        f"{pair}_top": [0.0, 10.0] if pair == "depth" else [120.0, 110.0],
        f"{pair}_base": [10.0, 30.0] if pair == "depth" else [110.0, 90.0],
        **columns,
    }
    df = pd.DataFrame(data)
    if units:
        df = ak.set_units(df, {f"{pair}_top": units, f"{pair}_base": units})
    return df


def bands(ax):
    """Each strata band as (low y, high y, rgb), sorted by low y."""
    found = []
    for patch in ax.patches:
        vertices = patch.get_transform().transform(patch.get_path().vertices)
        y = ax.transData.inverted().transform(vertices)[:, 1]
        found.append(
            (round(y.min(), 9), round(y.max(), 9), to_rgb(patch.get_facecolor()))
        )
    return sorted(found)


def water_lines(ax):
    """y of each full-width dashed water level line."""
    return sorted(
        line.get_ydata()[0] for line in ax.lines if line.get_linestyle() == "--"
    )


def texts(ax):
    return [text.get_text() for text in ax.texts]


def point_color(ax, unit):
    (collection,) = [c for c in ax.collections if c.get_label() == unit]
    return to_rgb(collection.get_facecolor()[0])


# --- strata ---------------------------------------------------------------------


def test_depth_strata_drawn_in_elevation_with_one_ground_level(frame):
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength", strata=strata_frame())
    assert [band[:2] for band in bands(ax)] == [(90.0, 110.0), (110.0, 120.0)]
    assert {"Fill", "Clay"} <= set(texts(ax))


def test_depth_strata_drawn_in_depth_as_given(frame):
    _, ax = ak.plot.profile(
        frame(), "undrained_shear_strength", vs="depth", strata=strata_frame()
    )
    assert [band[:2] for band in bands(ax)] == [(0.0, 10.0), (10.0, 30.0)]


def test_depth_strata_with_several_ground_levels_is_an_error(frame):
    df = frame(ground_level=[120.0, 120.0, 118.0, 118.0])
    with pytest.raises(ak.HangtuError) as error:
        ak.plot.profile(df, "undrained_shear_strength", strata=strata_frame())
    message = str(error.value)
    assert "strata overlay is given in depth" in message
    assert "elevation_top and elevation_base" in message


def test_elevation_strata_over_several_holes(frame):
    df = frame(ground_level=[120.0, 120.0, 118.0, 118.0])
    _, ax = ak.plot.profile(
        df, "undrained_shear_strength", strata=strata_frame("elevation")
    )
    assert [band[:2] for band in bands(ax)] == [(90.0, 110.0), (110.0, 120.0)]


def test_elevation_strata_drawn_in_depth_with_one_ground_level(frame):
    _, ax = ak.plot.profile(
        frame(),
        "undrained_shear_strength",
        vs="depth",
        strata=strata_frame("elevation"),
    )
    assert [band[:2] for band in bands(ax)] == [(0.0, 10.0), (10.0, 30.0)]


def test_strata_colors_match_the_point_colors(frame):
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength", strata=strata_frame())
    low, high = bands(ax)
    assert low[2] == point_color(ax, "Clay")
    assert high[2] == point_color(ax, "Fill")
    assert {patch.get_alpha() for patch in ax.patches} == {0.12}


@pytest.mark.parametrize(
    "columns",
    [
        {"elevation_top": [120.0, 110.0], "elevation_base": [110.0, 90.0]},
        {},
    ],
)
def test_both_pairs_or_neither_is_an_error(frame, columns):
    strata = strata_frame(**columns)
    if not columns:
        strata = strata.drop(columns=["depth_top", "depth_base"])
    with pytest.raises(ak.ColumnError, match=r"depth pair .* elevation pair"):
        ak.plot.profile(frame(), "undrained_shear_strength", strata=strata)


def test_a_blank_pair_from_the_template_counts_as_absent(frame):
    strata = pd.concat([ak.template("strata"), strata_frame()], ignore_index=True)
    strata = ak.set_units(strata, {"depth_top": "ft", "depth_base": "ft"})
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength", strata=strata)
    assert len(bands(ax)) == 2


def test_strata_need_a_geology_unit(frame):
    strata = strata_frame().drop(columns="geology_unit")
    with pytest.raises(ak.ColumnError, match=r"no 'geology_unit' column.*template"):
        ak.plot.profile(frame(), "undrained_shear_strength", strata=strata)


def test_a_swapped_stratum_warns_and_is_not_drawn(frame):
    strata = strata_frame(depth_top=[0.0, 40.0])
    strata = ak.set_units(strata, {"depth_top": "ft"})
    with pytest.warns(
        UserWarning, match=r"Rows 1 of the strata table.*wrong way round"
    ):
        _, ax = ak.plot.profile(frame(), "undrained_shear_strength", strata=strata)
    assert len(bands(ax)) == 1


def test_strata_without_units_take_the_data_units_with_a_warning(frame):
    with pytest.warns(UserWarning, match=r"strata table has no units.*ht\.set_units"):
        _, ax = ak.plot.profile(
            frame(),
            "undrained_shear_strength",
            vs="depth",
            strata=strata_frame(units=None),
            display_units="SI",
        )
    assert bands(ax)[0][:2] == pytest.approx((0.0, 10.0 * FT))


def test_strata_in_their_own_units_are_converted(frame):
    _, ax = ak.plot.profile(
        frame(), "undrained_shear_strength", vs="depth", strata=strata_frame(units="m")
    )
    assert bands(ax)[0][:2] == pytest.approx((0.0, 10.0 / FT))


def test_overlays_add_no_scatter_collections(frame):
    _, plain = ak.plot.profile(frame(), "undrained_shear_strength")
    _, ax = ak.plot.profile(
        frame(),
        "undrained_shear_strength",
        strata=strata_frame(),
        water_level=112.5,
    )
    assert len(ax.collections) == len(plain.collections)


# --- water level ----------------------------------------------------------------


def test_a_number_is_in_the_data_units(frame):
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength", water_level=112.5)
    assert water_lines(ax) == [112.5]
    assert "GWL" in texts(ax)
    (line,) = [line for line in ax.lines if line.get_linestyle() == "--"]
    assert line.get_color() == WATER_COLOR
    assert line.get_linewidth() == 0.8
    symbols = [line for line in ax.lines if line.get_marker() == "v"]
    assert len(symbols) == 1


def test_a_number_in_si(frame):
    _, ax = ak.plot.profile(
        frame(), "undrained_shear_strength", water_level=112.5, display_units="SI"
    )
    assert water_lines(ax) == pytest.approx([112.5 * FT])


def test_a_string_carries_its_own_unit(frame):
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength", water_level="34.29 m")
    assert water_lines(ax) == pytest.approx([112.5], rel=1e-4)


def test_a_list_of_labeled_levels(frame):
    _, ax = ak.plot.profile(
        frame(),
        "undrained_shear_strength",
        water_level=[(112.5, "GWL (2026-03)"), ("110 ft", "perched")],
    )
    assert water_lines(ax) == [110.0, 112.5]
    assert {"GWL (2026-03)", "perched"} <= set(texts(ax))


def test_a_water_level_against_depth(frame):
    _, ax = ak.plot.profile(
        frame(), "undrained_shear_strength", vs="depth", water_level=7.5
    )
    assert water_lines(ax) == [7.5]


@pytest.mark.parametrize("water_level", [[112.5], "high", [(None, "GWL")], True])
def test_a_bad_water_level_is_an_error(frame, water_level):
    with pytest.raises(ak.HangtuError):
        ak.plot.profile(frame(), "undrained_shear_strength", water_level=water_level)


def hole_ticks(ax):
    """{label: y} for per-hole water level ticks."""
    ticks = [line for line in ax.lines if list(line.get_xdata()) == [0.95, 1.0]]
    labels = [text for text in ax.texts if text.get_color() == WATER_COLOR]
    assert len(labels) in (0, len(ticks))
    return {
        (labels[i].get_text() if labels else i): tick.get_ydata()[0]
        for i, tick in enumerate(ticks)
    }


def test_per_hole_depths_use_each_hole_ground_level(frame):
    df = frame(ground_level=[120.0, 120.0, 118.0, 118.0])
    levels = ak.set_units(
        pd.DataFrame({"loca_id": ["A", "B"], "depth": [5.0, 6.0]}), {"depth": "ft"}
    )
    _, ax = ak.plot.profile(df, "undrained_shear_strength", water_level=levels)
    assert hole_ticks(ax) == {"A": 115.0, "B": 112.0}
    assert water_lines(ax) == []


def test_per_hole_label_replaces_the_hole_name(frame):
    levels = ak.set_units(
        pd.DataFrame(
            {"loca_id": ["A", "B"], "depth": [5.0, 6.0], "label": ["A (dry)", None]}
        ),
        {"depth": "ft"},
    )
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength", water_level=levels)
    assert hole_ticks(ax) == {"A (dry)": 115.0, "B": 114.0}


def test_per_hole_elevations_against_depth(frame):
    levels = ak.set_units(
        pd.DataFrame({"loca_id": ["A", "B"], "elevation": [115.0, 112.0]}),
        {"elevation": "ft"},
    )
    _, ax = ak.plot.profile(
        frame(), "undrained_shear_strength", vs="depth", water_level=levels
    )
    assert hole_ticks(ax) == {"A": 5.0, "B": 8.0}


def test_a_hole_without_a_ground_level_warns_and_is_not_drawn(frame):
    levels = ak.set_units(
        pd.DataFrame({"loca_id": ["A", "C"], "depth": [5.0, 6.0]}), {"depth": "ft"}
    )
    with pytest.warns(UserWarning, match=r"Water levels for C aren't drawn"):
        _, ax = ak.plot.profile(frame(), "undrained_shear_strength", water_level=levels)
    assert hole_ticks(ax) == {"A": 115.0}


def test_more_than_six_holes_are_not_labeled(frame):
    holes = [f"B-{i}" for i in range(7)]
    df = frame(
        values=[1000.0] * 7,
        loca_id=holes,
        depth=[5.0] * 7,
        ground_level=[120.0] * 7,
        geology_unit=["Fill"] * 7,
    )
    levels = ak.set_units(
        pd.DataFrame({"loca_id": holes, "depth": [3.0] * 7}), {"depth": "ft"}
    )
    _, ax = ak.plot.profile(df, "undrained_shear_strength", water_level=levels)
    assert len(hole_ticks(ax)) == 7
    assert not set(holes) & set(texts(ax))


def test_per_hole_table_needs_one_vertical_column(frame):
    levels = pd.DataFrame({"loca_id": ["A"], "level": [5.0]})
    with pytest.raises(ak.ColumnError, match="neither of 'depth' and 'elevation'"):
        ak.plot.profile(frame(), "undrained_shear_strength", water_level=levels)


def test_per_hole_table_without_units_warns(frame):
    levels = pd.DataFrame({"loca_id": ["A"], "depth": [5.0]})
    with pytest.warns(UserWarning, match="water_level table has no units for depth"):
        ak.plot.profile(frame(), "undrained_shear_strength", water_level=levels)


# --- US and SI ------------------------------------------------------------------


def test_overlay_positions_agree_in_us_and_si(frame):
    levels = ak.set_units(
        pd.DataFrame({"loca_id": ["A", "B"], "depth": [5.0, 6.0]}), {"depth": "ft"}
    )
    drawn = {}
    for system in ("US", "SI"):
        _, strata_ax = ak.plot.profile(
            frame(),
            "undrained_shear_strength",
            strata=strata_frame(),
            water_level=112.5,
            display_units=system,
        )
        _, hole_ax = ak.plot.profile(
            frame(),
            "undrained_shear_strength",
            water_level=levels,
            display_units=system,
        )
        drawn[system] = (
            np.array([band[:2] for band in bands(strata_ax)]),
            np.array(water_lines(strata_ax)),
            np.array(list(hole_ticks(hole_ax).values())),
        )
    for us, si in zip(drawn["US"], drawn["SI"], strict=True):
        np.testing.assert_allclose(us * FT, si)


# --- ranges ---------------------------------------------------------------------


def range_frame(units=("psf", "ft"), **columns):
    df = pd.DataFrame(
        {
            "low": [1000.0],
            "high": [2000.0],
            "label": ["stiff"],
            "source": ["Terzaghi & Peck"],
            **columns,
        }
    )
    value_unit, length_unit = units
    declared = {"low": value_unit, "high": value_unit}
    declared |= {c: length_unit for c in df.columns if c.startswith(("depth", "elev"))}
    return ak.set_units(df, declared)


def range_boxes(ax):
    """Each range as (x low, x high, y low, y high) in data or axes units."""
    found = []
    for patch in ax.patches:
        if patch.get_hatch() != "//":
            continue
        x, y = patch.get_x(), patch.get_y()
        w, h = patch.get_width(), patch.get_height()
        found.append((x, x + w, min(y, y + h), max(y, y + h)))
    return sorted(found)


def test_a_range_in_psf_is_drawn_in_kpa(frame):
    # P01 §12: 2,000 psf <-> 95.76 kPa.
    _, ax = ak.plot.profile(
        frame(), "undrained_shear_strength", ranges=range_frame(), display_units="SI"
    )
    ((low, high, bottom, top),) = range_boxes(ax)
    assert (low, high) == pytest.approx((47.88, 95.76), rel=1e-4)
    assert (bottom, top) == (0.0, 1.0)  # full height, in axes units
    assert "stiff (Terzaghi & Peck)" in texts(ax)


def test_a_range_over_a_depth_pair_drawn_in_elevation(frame):
    ranges = range_frame(depth_top=[10.0], depth_base=[20.0])
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength", ranges=ranges)
    assert range_boxes(ax) == [(1000.0, 2000.0, 100.0, 110.0)]


def test_a_range_row_without_bounds_covers_the_full_height(frame):
    ranges = range_frame(depth_top=[10.0], depth_base=[20.0])
    ranges = pd.concat([ranges, range_frame()], ignore_index=True)
    # concat drops declared units, so declare them again.
    ranges = ak.set_units(
        ranges,
        {"low": "psf", "high": "psf", "depth_top": "ft", "depth_base": "ft"},
    )
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength", ranges=ranges)
    assert range_boxes(ax) == [
        (1000.0, 2000.0, 0.0, 1.0),
        (1000.0, 2000.0, 100.0, 110.0),
    ]


def test_a_range_row_with_one_bound_warns(frame):
    ranges = range_frame(depth_top=[10.0], depth_base=[np.nan])
    with pytest.warns(UserWarning, match="Rows 0 of the ranges table have a blank"):
        _, ax = ak.plot.profile(frame(), "undrained_shear_strength", ranges=ranges)
    assert range_boxes(ax) == []


def test_a_range_without_a_source(frame):
    ranges = range_frame().drop(columns="source")
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength", ranges=ranges)
    assert "stiff" in texts(ax)


def test_ranges_from_a_csv_file(frame, tmp_path):
    path = tmp_path / "ranges.csv"
    range_frame().to_csv(path, index=False)
    with pytest.warns(UserWarning, match="ranges table has no units for low, high"):
        _, ax = ak.plot.profile(frame(), "undrained_shear_strength", ranges=str(path))
    assert range_boxes(ax)[0][:2] == (1000.0, 2000.0)


def test_one_units_warning_per_overlay(frame):
    ranges = pd.DataFrame(
        {"low": [1000.0], "high": [2000.0], "label": ["stiff"]}
        | {"depth_top": [10.0], "depth_base": [20.0]}
    )
    with pytest.warns(UserWarning) as record:
        ak.plot.profile(frame(), "undrained_shear_strength", ranges=ranges)
    assert len(record) == 1
    assert "low, high, depth_top, depth_base" in str(record[0].message)


def test_a_range_needs_low_high_and_label(frame):
    with pytest.raises(ak.ColumnError, match=r"no 'high' column.*template\(\"ranges"):
        ak.plot.profile(
            frame(),
            "undrained_shear_strength",
            ranges=range_frame().drop(columns="high"),
        )


def test_a_range_on_a_log_axis_starting_at_zero(frame):
    df = frame("hydraulic_conductivity", [1e-5, 3e-6, 2e-4, 5e-7], "cm/s")
    ranges = ak.set_units(
        pd.DataFrame({"low": [0.0], "high": [1e-4], "label": ["clean sand"]}),
        {"low": "cm/s", "high": "cm/s"},
    )
    _, ax = ak.plot.profile(
        df, "hydraulic_conductivity", preset="hydraulic_conductivity", ranges=ranges
    )
    ((low, high, _, _),) = range_boxes(ax)
    assert (low, high) == pytest.approx((1e-7, 1e-4))


# --- design and reference lines ---------------------------------------------------


def design_frame(**columns):
    df = pd.DataFrame(
        {
            "label": ["Design", "Design", "Design"],
            "depth": [20.0, 0.0, 10.0],
            "value": [2000.0, 500.0, 1200.0],
            **columns,
        }
    )
    return ak.set_units(df, {"depth": "ft", "value": "psf"})


def design_lines(ax):
    return [
        line
        for line in ax.lines
        if line.get_linewidth() == 1.5 and line.get_linestyle() == "--"
    ]


def test_a_design_line_in_depth_drawn_in_elevation(frame):
    _, ax = ak.plot.profile(
        frame(), "undrained_shear_strength", design_lines=design_frame()
    )
    (line,) = design_lines(ax)
    assert list(line.get_ydata()) == [120.0, 110.0, 100.0]
    assert list(line.get_xdata()) == [500.0, 1200.0, 2000.0]
    assert line.get_linestyle() == "--"
    assert "Design" in texts(ax)


def test_one_polyline_per_label(frame):
    df = design_frame(label=["Upper", "Lower", "Upper"])
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength", design_lines=df)
    assert len(design_lines(ax)) == 2


def test_a_design_line_needs_one_vertical_column(frame):
    df = design_frame(elevation=[100.0, 120.0, 110.0])
    with pytest.raises(ak.ColumnError, match="both of 'depth' and 'elevation'"):
        ak.plot.profile(frame(), "undrained_shear_strength", design_lines=df)


def test_a_design_line_in_depth_needs_one_ground_level(frame):
    df = frame(ground_level=[120.0, 120.0, 118.0, 118.0])
    with pytest.raises(ak.HangtuError, match="Give elevation instead"):
        ak.plot.profile(df, "undrained_shear_strength", design_lines=design_frame())


def test_reference_lines(frame):
    _, ax = ak.plot.profile(
        frame(),
        "undrained_shear_strength",
        reference_lines=[(1000.0, "limit"), ("95.76 kPa", "upper")],
    )
    lines = [line for line in ax.lines if line.get_linestyle() == ":"]
    assert [line.get_xdata()[0] for line in lines] == pytest.approx(
        [1000.0, 2000.0], rel=1e-4
    )
    assert {line.get_linewidth() for line in lines} == {0.6}
    assert {"limit", "upper"} <= set(texts(ax))


@pytest.mark.parametrize("reference_lines", [[1000.0], [("big", "limit")]])
def test_bad_reference_lines_are_an_error(frame, reference_lines):
    with pytest.raises(ak.HangtuError):
        ak.plot.profile(
            frame(), "undrained_shear_strength", reference_lines=reference_lines
        )


def test_note_is_written_at_the_lower_left(frame):
    _, ax = ak.plot.profile(frame(), "undrained_shear_strength", note="Draft")
    (note,) = [text for text in ax.texts if text.get_text() == "Draft"]
    assert note.get_position() == (0.02, 0.02)
    assert note.get_fontsize() == 7


# --- every overlay ------------------------------------------------------------------


def every_overlay():
    return {
        "strata": strata_frame(),
        "ranges": range_frame(),
        "design_lines": design_frame(),
        "reference_lines": [(1000.0, "limit")],
        "water_level": 112.5,
        "note": "Draft",
    }


@pytest.mark.parametrize("overlay", list(every_overlay()))
def test_each_overlay_on_and_off(frame, overlay):
    _, plain = ak.plot.profile(frame(), "undrained_shear_strength")
    _, ax = ak.plot.profile(
        frame(), "undrained_shear_strength", **{overlay: every_overlay()[overlay]}
    )
    drawn = len(ax.patches) + len(ax.lines) + len(ax.texts)
    assert drawn > len(plain.patches) + len(plain.lines) + len(plain.texts)
    assert len(ax.collections) == len(plain.collections)


def test_the_layers_follow_p01_draw_order():
    order = [
        _layers.STRATA,
        _layers.RANGES,
        _layers.LINES,
        _layers.WATER_LEVEL,
        _layers.INTERVALS,
        _layers.CONNECT,
        _layers.MARKERS,
        _layers.QUALIFIERS,
        _layers.ANNOTATIONS,
    ]
    assert order == sorted(order)
    assert len(set(order)) == len(order)


def test_each_mark_is_drawn_on_its_layer(frame):
    df = frame(depth_top=[4.0, 9.0, 10.0, 18.0], depth_base=[6.0, 11.0, 20.0, 30.0])
    df = ak.set_units(df, {"depth_top": "ft", "depth_base": "ft"})
    df["qualifier"] = ["<", "", "", ""]
    _, ax = ak.plot.profile(
        df, "undrained_shear_strength", connect=True, **every_overlay()
    )
    lines = ax.lines
    marks = {
        _layers.STRATA: [p for p in ax.patches if p.get_hatch() != "//"],
        _layers.RANGES: [p for p in ax.patches if p.get_hatch() == "//"],
        _layers.LINES: [line for line in lines if line.get_linestyle() == ":"]
        + design_lines(ax),
        _layers.WATER_LEVEL: [
            line for line in lines if line.get_color() == WATER_COLOR
        ],
        _layers.INTERVALS: [
            line for line in lines if line.get_solid_capstyle() == "round"
        ],
        _layers.CONNECT: [line for line in lines if line.get_alpha() == 0.6],
        _layers.MARKERS: [
            c for c in ax.collections if not c.get_label().startswith("_")
        ],
        _layers.QUALIFIERS: [
            c for c in ax.collections if c.get_label().startswith("_")
        ],
    }
    for layer, artists in marks.items():
        assert artists
        assert {artist.get_zorder() for artist in artists} == {layer}


def test_value_overlays_agree_in_us_and_si(frame):
    drawn = {}
    for system in ("US", "SI"):
        _, ax = ak.plot.profile(
            frame(),
            "undrained_shear_strength",
            ranges=range_frame(depth_top=[10.0], depth_base=[20.0]),
            design_lines=design_frame(),
            reference_lines=[(1000.0, "limit")],
            display_units=system,
        )
        (line,) = design_lines(ax)
        (reference,) = [x for x in ax.lines if x.get_linestyle() == ":"]
        drawn[system] = (
            np.array(range_boxes(ax)),
            np.column_stack([line.get_xdata(), line.get_ydata()]),
            np.array(reference.get_xdata()),
        )
    psf_to_kpa = 0.04788026
    np.testing.assert_allclose(
        drawn["US"][0] * [psf_to_kpa, psf_to_kpa, FT, FT], drawn["SI"][0], rtol=1e-6
    )
    np.testing.assert_allclose(
        drawn["US"][1] * [psf_to_kpa, FT], drawn["SI"][1], rtol=1e-6
    )
    np.testing.assert_allclose(drawn["US"][2] * psf_to_kpa, drawn["SI"][2], rtol=1e-6)
