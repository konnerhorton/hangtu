"""P04 plasticity chart (docs/plots/P04-plasticity-chart.md)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError
from hangtu.plot._plasticity_chart import zone_polygons, zones

EMPTY = pd.DataFrame()


def lines(ax, gid):
    return [line for line in ax.lines if line.get_gid() == gid]


def line_xy(ax, gid):
    (line,) = lines(ax, gid)
    return np.column_stack(line.get_data())


def texts(ax, gid):
    return sorted(t.get_text() for t in ax.texts if t.get_gid() == gid)


def screen_scale(ax):
    """Pixels per data unit in x and in y, after drawing."""
    ax.figure.canvas.draw()
    (x0, y0), (x1, y1) = ax.transData.transform([(0, 0), (10, 10)])
    return (x1 - x0) / 10, (y1 - y0) / 10


# --- USCS geometry (§12) -----------------------------------------------------


def test_uscs_a_line_starts_at_pi_4_and_crosses_zero_at_20():
    _, ax = ht.plot.plasticity_chart(EMPTY)
    xy = line_xy(ax, "a_line")
    np.testing.assert_allclose(xy[0], (20 + 4 / 0.73, 4))
    assert xy[0, 0] == pytest.approx(25.48, abs=0.005)
    slope, intercept = np.polyfit(xy[:, 0], xy[:, 1], 1)
    assert slope * 50 + intercept == pytest.approx(21.9)
    assert -intercept / slope == pytest.approx(20)


def test_uscs_u_line_is_vertical_to_7_2_then_sloped():
    _, ax = ht.plot.plasticity_chart(EMPTY)
    xy = line_xy(ax, "u_line")
    np.testing.assert_allclose(xy[:2], [(16, 0), (16, 7.2)])
    slope, intercept = np.polyfit(xy[1:, 0], xy[1:, 1], 1)
    assert slope * 50 + intercept == pytest.approx(37.8)
    assert xy[-1, 1] == pytest.approx(60)  # leaves through the top


def test_uscs_cl_ml_polygon():
    _, ax = ht.plot.plasticity_chart(EMPTY)
    (patch,) = [p for p in ax.patches if p.get_gid() == "cl_ml"]
    assert patch.get_hatch()
    vertices = {tuple(np.round(v, 2)) for v in patch.get_xy()}
    assert vertices == {(16.0, 4.0), (25.48, 4.0), (29.59, 7.0), (16.0, 7.0)}


def test_uscs_divider_stops_at_the_u_line():
    _, ax = ht.plot.plasticity_chart(EMPTY)
    np.testing.assert_allclose(line_xy(ax, "divider"), [(50, 0), (50, 37.8)])


def test_uscs_zone_labels():
    _, ax = ht.plot.plasticity_chart(EMPTY)
    assert texts(ax, "zone_label") == ["CH", "CL", "CL-ML", "MH", "ML"]
    assert texts(ax, "line_label") == ["A-line", "U-line"]


def test_equality_line_on_both_systems():
    for system in ("uscs", "bs5930"):
        _, ax = ht.plot.plasticity_chart(EMPTY, system=system)
        np.testing.assert_allclose(line_xy(ax, "equality"), [(0, 0), (60, 60)])


# --- BS 5930 geometry (§12) --------------------------------------------------


def test_bs5930_dividers_end_at_pi_equals_ll():
    _, ax = ht.plot.plasticity_chart(EMPTY, system="bs5930")
    ends = sorted(tuple(line.get_xydata()[-1]) for line in lines(ax, "divider"))
    assert ends == [(35, 35), (50, 50), (70, 70), (90, 90)]
    for line in lines(ax, "divider"):
        assert line.get_xydata()[0, 1] == 0


def test_bs5930_a_line_from_20_and_no_u_line():
    _, ax = ht.plot.plasticity_chart(EMPTY, system="bs5930")
    xy = line_xy(ax, "a_line")
    np.testing.assert_allclose(xy[0], (20, 0))
    assert xy[-1, 1] == pytest.approx(0.73 * 80)
    assert not lines(ax, "u_line")
    assert not [p for p in ax.patches if p.get_gid() == "cl_ml"]


def test_bs5930_labels():
    _, ax = ht.plot.plasticity_chart(EMPTY, system="bs5930")
    bands = "LIHVE"
    assert texts(ax, "zone_label") == sorted(
        [f"{kind}{band}" for kind in "CM" for band in bands]
    )
    assert texts(ax, "band_label") == sorted(bands)
    assert texts(ax, "line_label") == ["A-line"]


def test_zone_labels_off():
    _, ax = ht.plot.plasticity_chart(EMPTY, zone_labels=False)
    assert texts(ax, "zone_label") == []
    assert texts(ax, "line_label") == ["A-line", "U-line"]


# --- zones -------------------------------------------------------------------


@pytest.mark.parametrize("system", ["uscs", "bs5930"])
def test_zone_labels_sit_inside_their_zone(system):
    from matplotlib.path import Path

    _, ax = ht.plot.plasticity_chart(EMPTY, system=system)
    box = (0, 100, 0, 60)
    by_name = {zone.name: zone for zone in zones(system)}
    for text in ax.texts:
        if text.get_gid() != "zone_label":
            continue
        pieces = zone_polygons(by_name[text.get_text()], box)
        if text.get_text() == "CL-ML":
            continue  # beside its zone: test_cl_ml_label_sits_left_of_its_zone
        assert any(Path(p).contains_point(text.get_position()) for p in pieces)


def test_cl_ml_label_sits_left_of_its_zone():
    _, ax = ht.plot.plasticity_chart(EMPTY)
    (label,) = [t for t in ax.texts if t.get_text() == "CL-ML"]
    # Level with the trapezoid's centroid: bottom 9.479 wide at PI 4, top
    # 13.589 at PI 7, so 4 + 3 (9.479 + 2 x 13.589) / (3 (9.479 + 13.589)).
    bottom, top = 20 + 4 / 0.73 - 16, 20 + 7 / 0.73 - 16
    level = 4 + 3 * (bottom + 2 * top) / (3 * (bottom + top))
    assert label.get_position() == pytest.approx((15, level))
    assert level == pytest.approx(5.589, abs=1e-3)
    assert label.get_horizontalalignment() == "right"
    _, ax = ht.plot.plasticity_chart(EMPTY, xlim=(15.5, 60))  # no room: inside
    (label,) = [t for t in ax.texts if t.get_text() == "CL-ML"]
    assert label.get_horizontalalignment() == "center"
    assert 16 < label.get_position()[0] < 29.59


def test_zones_do_not_overlap():
    box = (0, 100, 0, 60)
    for system in ("uscs", "bs5930"):
        area = 0.0
        for zone in zones(system):
            for polygon in zone_polygons(zone, box):
                x, y = polygon[:, 0], polygon[:, 1]
                area += abs(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y)) / 2
        # USCS: the box right of LL 16 and below the U-line. BS 5930: below PI = LL.
        expected = {"uscs": 3491.2, "bs5930": 6000 - 60 * 60 / 2}[system]
        assert area == pytest.approx(expected, rel=1e-3)


# --- axes (§6) ---------------------------------------------------------------


def test_axes_limits_ticks_and_labels():
    _, ax = ht.plot.plasticity_chart(EMPTY)
    assert ax.get_xlim() == (0, 100)
    assert ax.get_ylim() == (0, 60)
    x_ticks = [t for t in ax.get_xticks() if 0 <= t <= 100]
    y_ticks = [t for t in ax.get_yticks() if 0 <= t <= 60]
    assert x_ticks == list(range(0, 101, 10))
    assert y_ticks == list(range(0, 61, 10))
    assert ax.get_xlabel() == "Liquid limit, LL (%)"
    assert ax.get_ylabel() == "Plasticity index, PI"


@pytest.mark.parametrize(
    "kwargs", [{}, {"xlim": (20, 80), "ylim": (0, 40)}, {"xlim": (0, 140)}]
)
def test_equal_aspect(kwargs):
    _, ax = ht.plot.plasticity_chart(EMPTY, **kwargs)
    x_scale, y_scale = screen_scale(ax)
    assert x_scale == pytest.approx(y_scale, rel=1e-6)


def test_equal_aspect_on_a_sheet_panel():
    sheet = ht.Sheet("letter", layout=(1, 2))
    ht.plot.plasticity_chart(EMPTY, ax=sheet[1])
    x_scale, y_scale = screen_scale(sheet[1])
    assert x_scale == pytest.approx(y_scale, rel=1e-6)


def test_user_limits_are_exact():
    _, ax = ht.plot.plasticity_chart(EMPTY, xlim=(20, 80), ylim=(0, 40))
    assert ax.get_xlim() == (20, 80)
    assert ax.get_ylim() == (0, 40)


def test_bad_limits_are_an_error():
    with pytest.raises(HangtuError, match="xlim must be"):
        ht.plot.plasticity_chart(EMPTY, xlim=(0, 0))


def test_unknown_system_is_an_error():
    with pytest.raises(HangtuError, match="'uscs', 'bs5930'"):
        ht.plot.plasticity_chart(EMPTY, system="casagrande")


def test_bad_display_units_is_an_error():
    with pytest.raises(HangtuError, match="display_units"):
        ht.plot.plasticity_chart(EMPTY, display_units="metric")


# --- contract ----------------------------------------------------------------


def test_empty_input_shows_no_data():
    _, ax = ht.plot.plasticity_chart(ht.template("atterberg"))
    assert "No data" in [t.get_text() for t in ax.texts]


def test_note_goes_in_the_footnote():
    _, ax = ht.plot.plasticity_chart(EMPTY, note="Lab B results")
    assert any("Lab B results" in t.get_text() for t in ax.texts)


def test_no_global_state(assert_no_global_state):
    assert_no_global_state(ht.plot.plasticity_chart, EMPTY)


def test_no_global_state_on_a_sheet_panel(assert_no_global_state):
    sheet = ht.Sheet("letter", layout=(1, 2))
    assert_no_global_state(ht.plot.plasticity_chart, EMPTY, ax=sheet[1])


# --- specimens ---------------------------------------------------------------


def limits(**columns):
    """Atterberg rows in two units; ``columns`` replace or add columns."""
    data = {
        "specimen_id": ["S1", "S2", "S3", "S4"],
        "geology_unit": ["Fill", "Fill", "Clay", "Clay"],
        "liquid_limit": [30.0, 45.0, 60.0, 80.0],
        "plastic_limit": [18.0, 20.0, 25.0, 40.0],
        **columns,
    }
    return pd.DataFrame(data)


def drawn(ax):
    """Filled specimen points, as an (n, 2) array (edge markers are open)."""
    offsets = [
        c.get_offsets()
        for c in ax.collections
        if len(c.get_offsets()) and len(c.get_facecolors())
    ]
    return np.concatenate(offsets) if offsets else np.empty((0, 2))


def legend_texts(ax):
    legend = ax.get_legend()
    return [t.get_text() for t in legend.get_texts()] if legend else []


def test_specimens_drawn_at_ll_and_pi():
    _, ax = ht.plot.plasticity_chart(limits())
    np.testing.assert_allclose(
        sorted(map(tuple, drawn(ax))), [(30, 12), (45, 25), (60, 35), (80, 40)]
    )
    assert "No data" not in [t.get_text() for t in ax.texts]


def test_legend_counts_per_unit_in_order():
    _, ax = ht.plot.plasticity_chart(limits())
    assert legend_texts(ax) == ["Clay (n = 2)", "Fill (n = 2)"]
    _, ax = ht.plot.plasticity_chart(limits(), order=["Fill", "Clay"])
    assert legend_texts(ax) == ["Fill (n = 2)", "Clay (n = 2)"]


def test_one_color_without_grouping():
    _, ax = ht.plot.plasticity_chart(limits(), color_by=None)
    assert legend_texts(ax) == ["All specimens (n = 4)"]


def test_palette_colors_the_units():
    _, ax = ht.plot.plasticity_chart(limits(), palette={"Fill": "tan"})
    from matplotlib.colors import to_rgba

    fill = [c for c in ax.collections if len(c.get_offsets()) == 2]
    assert to_rgba("tan") in [tuple(c.get_facecolors()[0]) for c in fill]


def test_blank_unit_is_gray_and_last():
    df = limits(geology_unit=["Fill", None, "Clay", "Clay"])
    _, ax = ht.plot.plasticity_chart(df)
    assert legend_texts(ax) == ["Clay (n = 2)", "Fill (n = 1)", "(blank) (n = 1)"]


def test_color_by_any_column():
    df = ht.analysis.plasticity(limits())
    _, ax = ht.plot.plasticity_chart(df, color_by="plasticity_class_uscs")
    assert legend_texts(ax) == ["CH (n = 1)", "CL (n = 2)", "MH (n = 1)"]


def test_color_by_missing_column_is_an_error():
    with pytest.raises(ht.ColumnError, match="color_by='lab'"):
        ht.plot.plasticity_chart(limits(), color_by="lab")


def test_hint_without_geology_unit():
    df = limits().drop(columns="geology_unit")
    with pytest.warns(ht.HangtuHint, match="one color") as record:
        _, ax = ht.plot.plasticity_chart(df)
    assert len(record) == 1
    assert legend_texts(ax) == ["All specimens (n = 4)"]


def test_no_hint_with_geology_unit_or_without_grouping(recwarn):
    ht.plot.plasticity_chart(limits())
    ht.plot.plasticity_chart(limits().drop(columns="geology_unit"), color_by=None)
    assert not recwarn


# --- counts (§7, §12) --------------------------------------------------------


def test_non_plastic_counted_not_drawn():
    df = limits(
        plastic_limit=[None, 20.0, 25.0, 40.0], non_plastic=[True, False, None, False]
    )
    _, ax = ht.plot.plasticity_chart(df)
    assert ax.ags_notes == {"non_plastic_excluded": 1}
    assert len(drawn(ax)) == 3
    footnote = ax.texts[-1].get_text()
    assert "1 non-plastic (NP) specimen not shown" in footnote


def test_blank_ll_or_pi_counted_once():
    df = limits(
        liquid_limit=[None, 45.0, 60.0, 80.0],
        plastic_limit=[18.0, None, 25.0, 40.0],
    )
    _, ax = ht.plot.plasticity_chart(df)
    assert ax.ags_notes == {"nan": 2}
    assert "2 blank values not shown" in ax.texts[-1].get_text()


def test_all_non_plastic_shows_no_data():
    df = limits(plastic_limit=[None] * 4, non_plastic=[True] * 4)
    _, ax = ht.plot.plasticity_chart(df)
    assert "No data" in [t.get_text() for t in ax.texts]
    assert ax.ags_notes == {"non_plastic_excluded": 4}


# --- limits (§6, §12) --------------------------------------------------------


@pytest.mark.parametrize(
    ("highest", "x_limit"), [(100.0, 100), (101.0, 120), (115.0, 120), (120.0, 120)]
)
def test_x_extends_in_steps_of_20(highest, x_limit):
    df = limits(liquid_limit=[30.0, 45.0, 60.0, highest])
    _, ax = ht.plot.plasticity_chart(df)
    assert ax.get_xlim() == (0, x_limit)
    assert ax.get_ylim() == (0, 60)


def test_pi_above_60_drawn_at_the_top_edge():
    df = limits(liquid_limit=[30.0, 45.0, 60.0, 95.0], plastic_limit=[18, 20, 25, 30])
    _, ax = ht.plot.plasticity_chart(df)
    assert ax.ags_notes == {"beyond_limit": 1}
    (edge,) = [c for c in ax.collections if not len(c.get_facecolors())]
    np.testing.assert_allclose(edge.get_offsets(), [(95, 60)])
    assert len(drawn(ax)) == 3
    assert legend_texts(ax) == ["Clay (n = 2)", "Fill (n = 2)"]


def test_user_xlim_moves_points_to_the_edge():
    _, ax = ht.plot.plasticity_chart(limits(), xlim=(20, 70))
    assert ax.get_xlim() == (20, 70)
    assert ax.ags_notes == {"beyond_limit": 1}
    assert "1 value beyond axis limit" in ax.texts[-1].get_text()


# --- the analysis's checks pass through --------------------------------------


def test_pi_above_ll_is_drawn_with_the_analysis_warning():
    df = limits(
        plastic_limit=[None, 20.0, 25.0, 40.0],
        plasticity_index=[35.0, None, None, None],
    )
    with pytest.warns(UserWarning, match="above their liquid_limit"):
        _, ax = ht.plot.plasticity_chart(df)
    assert (30, 35) in map(tuple, drawn(ax))


def test_text_in_liquid_limit_is_the_analysis_error():
    df = limits(liquid_limit=["NP", 45.0, 60.0, 80.0])
    with pytest.raises(ht.ColumnError, match="liquid_limit"):
        ht.plot.plasticity_chart(df)


def test_missing_liquid_limit_is_the_analysis_error():
    with pytest.raises(ht.ColumnError, match="'liquid_limit' not found"):
        ht.plot.plasticity_chart(limits().drop(columns="liquid_limit"))


# --- specimen labels ---------------------------------------------------------


def test_labels_name_each_specimen():
    df = limits(specimen_id=["S1", None, "S3", "S4"])
    _, ax = ht.plot.plasticity_chart(df, labels=True)
    assert texts(ax, "specimen_label") == ["S1", "S3", "S4"]


def test_labels_without_specimen_id_is_an_error():
    with pytest.raises(ht.ColumnError, match="specimen_id"):
        ht.plot.plasticity_chart(limits().drop(columns="specimen_id"), labels=True)


# --- agreement with the analysis (§12) ---------------------------------------


@pytest.mark.parametrize("system", ["uscs", "bs5930"])
def test_each_point_is_drawn_in_the_zone_of_its_class(system):
    from matplotlib.path import Path

    from hangtu.analysis._plasticity import a_line

    liquid, index = np.meshgrid(np.arange(0.3, 100, 1.0), np.arange(0.2, 60, 0.5))
    liquid, index = liquid.ravel(), index.ravel()
    keep = (index < liquid) & (np.abs(index - a_line(liquid, system)) > 1e-6)
    if system == "uscs":
        keep &= (liquid > 16) & (index < 0.9 * (liquid - 8))
    liquid, index = liquid[keep], index[keep]
    df = pd.DataFrame({"liquid_limit": liquid, "plasticity_index": index})
    classes = ht.analysis.plasticity(df)[f"plasticity_class_{system}"]

    _, ax = ht.plot.plasticity_chart(df, system=system, color_by=None)
    points = drawn(ax)
    np.testing.assert_allclose(points[:, 0], liquid)
    box = (0, 100, 0, 60)
    found = np.full(len(df), None, dtype=object)
    for zone in zones(system):
        for polygon in zone_polygons(zone, box):
            inside = Path(polygon).contains_points(points)
            assert not (inside & (found != None)).any()  # noqa: E711
            found[inside] = zone.name
    assert (found == classes.to_numpy()).all()


def test_us_and_si_are_the_same(assert_us_si_equivalent):
    assert_us_si_equivalent(
        ht.plot.plasticity_chart, limits(), ("dimensionless", "dimensionless")
    )


def test_no_global_state_with_data(assert_no_global_state):
    assert_no_global_state(ht.plot.plasticity_chart, limits())
