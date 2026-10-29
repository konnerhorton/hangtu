"""P17 clogging diagram (docs/plots/P17-clogging-diagram.md)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu import _config, _polygons
from hangtu.errors import HangtuError

EMPTY = pd.DataFrame()
CONFIG = _config.load("config/clogging_methods.yaml")["thewes_burger_2004"]


def zone_patches(ax):
    return {p.get_label(): p for p in ax.patches if p.get_gid() == "clogging_zone"}


def zone_labels(ax):
    return {
        t.get_text(): t.get_position() for t in ax.texts if t.get_gid() == "zone_label"
    }


def visible(ticks, limits):
    low, high = limits
    return [t for t in ticks if low - 1e-9 <= t <= high + 1e-9]


# --- zones (criteria 2 and 8) ------------------------------------------------


def test_zone_patches_match_the_config():
    _, ax = ht.plot.clogging_diagram(EMPTY)
    patches = zone_patches(ax)
    assert list(patches) == ["low", "medium", "medium-high", "high"]
    for zone in CONFIG["zones"]:
        xy = patches[zone["name"]].get_xy()
        np.testing.assert_allclose(xy[0], xy[-1])  # closed
        np.testing.assert_allclose(xy[:-1], zone["vertices"])


def test_each_label_is_inside_its_zone():
    _, ax = ht.plot.clogging_diagram(EMPTY)
    labels = zone_labels(ax)
    assert set(labels) == {"low", "medium", "medium-high", "high"}
    for zone in CONFIG["zones"]:
        vertices = np.array(zone["vertices"], dtype=float)
        point = np.array(labels[zone["name"]])
        # Clear of the edges too: 1 PI and 0.02 Ic either way are still inside.
        around = point + np.array([(0, 0), (1, 0), (-1, 0), (0, 0.02), (0, -0.02)])
        assert _polygons.contains(vertices, around, tolerance=0).all(), zone["name"]


def test_colors_run_from_green_to_red():
    _, ax = ht.plot.clogging_diagram(EMPTY)
    patches = zone_patches(ax)
    low = patches["low"].get_edgecolor()
    high = patches["high"].get_edgecolor()
    assert low[1] > low[0]  # green over red
    assert high[0] > high[1]  # red over green
    for patch in patches.values():
        assert patch.get_facecolor()[3] == pytest.approx(0.2)


def test_zone_labels_can_be_hidden():
    _, ax = ht.plot.clogging_diagram(EMPTY, zone_labels=False)
    assert zone_labels(ax) == {}


# --- axes (§6) ---------------------------------------------------------------


def test_axes_are_the_papers():
    _, ax = ht.plot.clogging_diagram(EMPTY)
    assert ax.get_xlim() == (0, 70)
    assert ax.get_ylim() == pytest.approx((0.3, 1.5))
    assert ax.get_xlabel() == "Plasticity index, PI"
    assert ax.get_ylabel() == "Consistency index, Ic"
    np.testing.assert_allclose(
        visible(ax.get_xticks(), ax.get_xlim()), range(0, 71, 10)
    )
    np.testing.assert_allclose(
        visible(ax.get_yticks(), ax.get_ylim()),
        sorted([*np.round(np.arange(0.3, 1.51, 0.1), 6), 0.75]),
    )


def test_user_limits_are_exact():
    _, ax = ht.plot.clogging_diagram(EMPTY, xlim=(0, 100), ylim=(-0.5, 2))
    assert ax.get_xlim() == (0, 100)
    assert ax.get_ylim() == (-0.5, 2)


def test_bad_limits_are_an_error():
    with pytest.raises(HangtuError, match="ylim must be"):
        ht.plot.clogging_diagram(EMPTY, ylim=(1, 1))


def test_unknown_method_is_an_error():
    with pytest.raises(HangtuError, match="'thewes_burger_2004'"):
        ht.plot.clogging_diagram(EMPTY, method="hollmann")


# --- zones= (criterion 9) ----------------------------------------------------

USER_ZONES = pd.DataFrame(
    {
        "label": ["dry"] * 4 + ["sticky"] * 4,
        "plasticity_index": [0, 50, 50, 0, 0, 50, 50, 0],
        "consistency_index": [0, 0, 1, 1, 1, 1, 2, 2],
    }
)


def test_user_zones_replace_the_drawn_zones(tmp_path):
    path = tmp_path / "zones.csv"
    USER_ZONES.to_csv(path, index=False)
    for zones in (USER_ZONES, path):
        _, ax = ht.plot.clogging_diagram(EMPTY, zones=zones)
        assert list(zone_patches(ax)) == ["dry", "sticky"]
        assert ax.get_xlim() == (0, 50)
        assert ax.get_ylim() == (0, 2)
        np.testing.assert_allclose(zone_labels(ax)["sticky"], (25, 1.5))


# --- contract (criterion 11) -------------------------------------------------


def test_empty_input_shows_no_data():
    _, ax = ht.plot.clogging_diagram(ht.template("atterberg"))
    assert "No data" in [t.get_text() for t in ax.texts]


def test_note_goes_in_the_footnote():
    _, ax = ht.plot.clogging_diagram(EMPTY, note="Lab B results")
    assert any("Lab B results" in t.get_text() for t in ax.texts)


def test_no_global_state(assert_no_global_state):
    assert_no_global_state(ht.plot.clogging_diagram, EMPTY)


def test_draws_into_a_sheet_panel(assert_no_global_state):
    sheet = ht.Sheet("letter", layout=(1, 2))
    _, ax = ht.plot.clogging_diagram(EMPTY, ax=sheet[1])
    assert ax is sheet[1]
    assert len(zone_patches(sheet[1])) == 4
    assert_no_global_state(ht.plot.clogging_diagram, EMPTY, ax=sheet[1])


def test_us_and_si_are_the_same_figure():
    _, us = ht.plot.clogging_diagram(EMPTY, display_units="US")
    _, si = ht.plot.clogging_diagram(EMPTY, display_units="SI")
    assert us.get_xlim() == si.get_xlim()
    assert us.get_ylim() == si.get_ylim()
    assert us.get_xlabel() == si.get_xlabel()
    assert us.get_ylabel() == si.get_ylabel()
