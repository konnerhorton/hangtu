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


# --- specimens (criteria 3, 5, 6 and 7) ---------------------------------------

NAN = np.nan
# The golden table (docs/work/m12-clogging-diagram.md): w, LL, PL.
GOLDEN = [
    (30, 60, 25),
    (8, 50, 20),
    (20, 35, 20),
    (32, 60, 20),
    (20, 40, 20),
    (8, 60, 20),
    (30, 60, 20),
    (36, 60, 20),
    (20, 28, 20),
    (8, 40, 20),  # Ic 1.6, top edge
    (50, 40, 20),  # Ic -0.5, bottom edge
    (25, 100, 25),  # PI 75, right edge
    (30, 30, 30),  # PI = 0
    (25, NAN, NAN),  # NP
    (31, 40, 20),
    (34, 40, 20),
]


def golden_frame():
    frame = pd.DataFrame(
        GOLDEN, columns=["water_content", "liquid_limit", "plastic_limit"]
    )
    frame["non_plastic"] = [False] * 13 + [True] + [False] * 2
    frame["specimen_id"] = [f"S{i}" for i in range(1, 17)]
    frame["geology_unit"] = ["Clay"] * 8 + ["Silt"] * 8
    return frame


def drawn(ax):
    """Filled specimen points, as an (n, 2) array (edge markers are open)."""
    offsets = [
        c.get_offsets()
        for c in ax.collections
        if len(c.get_offsets()) and len(c.get_facecolors())
    ]
    return np.concatenate(offsets) if offsets else np.empty((0, 2))


def edges(ax):
    offsets = [
        c.get_offsets()
        for c in ax.collections
        if len(c.get_offsets()) and not len(c.get_facecolors())
    ]
    return np.concatenate(offsets) if offsets else np.empty((0, 2))


def footnote(ax):
    return ax.texts[-1].get_text()


def legend_texts(ax):
    legend = ax.get_legend()
    return [t.get_text() for t in legend.get_texts()] if legend else []


def test_beyond_the_axes_drawn_at_the_edge_and_counted():
    # Criterion 5: rows 10-12 at the top, bottom and right edges.
    _, ax = ht.plot.clogging_diagram(golden_frame())
    np.testing.assert_allclose(
        sorted(map(tuple, edges(ax))), sorted([(20, 1.5), (20, 0.3), (70, 1.0)])
    )
    assert len(drawn(ax)) == 11
    assert ax.ags_notes["beyond_limit"] == 3
    assert "3 values beyond axis limit, shown at the edge" in footnote(ax)


def test_rows_not_drawn_are_counted_each_on_their_own_line():
    # Criterion 6.
    frame = golden_frame()
    frame.loc[0, "water_content"] = NAN
    frame.loc[1, "plastic_limit"] = NAN
    _, ax = ht.plot.clogging_diagram(frame)
    assert ax.ags_notes == {
        "nan": 1,
        "non_plastic_excluded": 1,
        "zero_plasticity": 1,
        "no_water_content": 1,
        "beyond_limit": 3,
    }
    text = footnote(ax)
    for line in (
        "1 blank value not shown",
        "1 non-plastic (NP) specimen not shown",
        "1 specimen with PI = 0 not shown",
        "1 specimen without water content not shown",
    ):
        assert line in text


def test_zone_counts_match_the_analysis():
    # Criterion 7: the golden counts, highest zone first.
    frame = golden_frame()
    _, ax = ht.plot.clogging_diagram(frame)
    assert (
        "High: 4 · Medium-high: 1 · Medium: 3 · Low: 3 · outside the diagram: 3 "
        "of 14 specimens" in footnote(ax)
    )
    with pytest.warns(UserWarning, match="clogging_potential is blank"):
        result = ht.analysis.clogging_potential(frame)
    counts = result["clogging_potential"].value_counts()
    assert counts.to_dict() == {"high": 4, "low": 3, "medium": 3, "medium-high": 1}


def test_zone_counts_can_be_hidden():
    _, ax = ht.plot.clogging_diagram(golden_frame(), zone_counts=False)
    assert "High:" not in footnote(ax)


def test_each_point_is_drawn_in_its_zone():
    # Criterion 3: a 50 x 50 grid over the axes, Ic given directly.
    pi, ic = np.meshgrid(np.linspace(0.5, 70, 50), np.linspace(0.3, 1.5, 50))
    frame = pd.DataFrame(
        {
            "liquid_limit": pi.ravel() + 20,
            "plastic_limit": 20.0,
            "consistency_index": ic.ravel(),
            "geology_unit": "Clay",
        }
    )
    _, ax = ht.plot.clogging_diagram(frame)
    points = drawn(ax)
    assert len(points) == 2500
    patches = list(zone_patches(ax).items())
    drawn_in = np.full(len(points), None, dtype=object)
    for name, patch in reversed(patches):  # highest first, as boundaries go
        inside = pd.isna(drawn_in) & _polygons.contains(patch.get_xy()[:-1], points)
        drawn_in[inside] = name
    result = ht.analysis.clogging_potential(frame)
    order = np.lexsort((result["consistency_index"], result["plasticity_index"]))
    expected = result["clogging_potential"].to_numpy(dtype=object)[order]
    found = drawn_in[np.lexsort((points[:, 1], points[:, 0]))]
    assert found.tolist() == expected.tolist()


def test_legend_counts_specimens_by_unit():
    _, ax = ht.plot.clogging_diagram(golden_frame())
    assert legend_texts(ax) == ["Clay (n = 8)", "Silt (n = 6)"]


def test_specimen_labels():
    _, ax = ht.plot.clogging_diagram(golden_frame().iloc[:2], labels=True)
    labels = [t.get_text() for t in ax.texts if t.get_gid() == "specimen_label"]
    assert labels == ["S1", "S2"]


def test_labels_without_specimen_id_is_an_error():
    frame = golden_frame().drop(columns="specimen_id")
    with pytest.raises(ht.ColumnError, match="specimen_id"):
        ht.plot.clogging_diagram(frame, labels=True)


def test_no_water_content_is_an_error():
    frame = golden_frame().drop(columns="water_content")
    with pytest.raises(ht.ColumnError, match="water_content"):
        ht.plot.clogging_diagram(frame)


def test_no_geology_unit_gives_a_hint():
    frame = golden_frame().drop(columns="geology_unit")
    with pytest.warns(ht.HangtuHint, match="geology_unit"):
        _, ax = ht.plot.clogging_diagram(frame)
    assert legend_texts(ax) == ["All specimens (n = 14)"]


def test_the_plot_does_not_repeat_the_analysis_warning():
    # The footnote counts the blank rows; warnings are errors in this suite.
    ht.plot.clogging_diagram(golden_frame())
