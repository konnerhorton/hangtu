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
        assert any(Path(p).contains_point(text.get_position()) for p in pieces)


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
