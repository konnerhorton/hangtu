"""P05 fraction band, dividers, sieve labels and axes (P05 §6, §8, §12)."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError

EMPTY = pd.DataFrame()


def dividers(ax, gid):
    return sorted(line.get_xdata()[0] for line in ax.lines if line.get_gid() == gid)


def texts(ax, gid):
    return [t.get_text() for t in ax.texts if t.get_gid() == gid]


def sieve_labels(ax):
    return {t.get_text(): t.xy[0] for t in ax.texts if t.get_gid() == "sieve_label"}


# --- Band (§12) --------------------------------------------------------------


def test_astm_uscs_boundaries():
    _, ax = ht.plot.grain_size(EMPTY)
    assert dividers(ax, "fraction_divider") == [0.075, 4.75, 75]
    assert dividers(ax, "part_divider") == [0.425, 2.0, 19]
    header = ax.grain_size_header
    assert texts(header, "fraction_name") == ["Fines", "Sand", "Gravel"]
    assert texts(header, "part_name") == [
        "Fine",
        "Medium",
        "Coarse",
        "Fine",
        "Coarse",
    ]


def test_iso14688_boundaries():
    _, ax = ht.plot.grain_size(EMPTY, fractions="iso14688")
    both = dividers(ax, "fraction_divider") + dividers(ax, "part_divider")
    assert sorted(both) == [0.002, 0.0063, 0.02, 0.063, 0.2, 0.63, 2.0, 6.3, 20, 63]
    # Cobbles (63-200 mm) shows only 63-100 mm, too narrow to name.
    assert texts(ax.grain_size_header, "fraction_name") == [
        "Clay",
        "Silt",
        "Sand",
        "Gravel",
    ]


def test_aashto_has_one_row():
    _, ax = ht.plot.grain_size(EMPTY, fractions="aashto")
    header = ax.grain_size_header
    assert texts(header, "fraction_name") == [
        "Silt clay",
        "Fine sand",
        "Coarse sand",
        "Gravel",
    ]
    assert texts(header, "part_name") == []
    assert {t.get_position()[1] for t in header.texts} == {0.5}
    assert dividers(ax, "fraction_divider") == [0.075, 0.425, 2.0, 75]


def test_a_users_system():
    system = {
        "name": "project_bands",
        "fractions": [
            {"name": "fines", "lower": 0, "upper": 0.075},
            {
                "name": "sand",
                "lower": 0.075,
                "upper": 2.0,
                "parts": [
                    {"name": "fine", "upper": 0.25},
                    {"name": "rest", "upper": 2.0},
                ],
            },
            {"name": "coarse", "lower": 2.0, "upper": None},
        ],
    }
    _, ax = ht.plot.grain_size(EMPTY, fractions=system)
    assert texts(ax.grain_size_header, "fraction_name") == ["Fines", "Sand", "Coarse"]
    assert texts(ax.grain_size_header, "part_name") == ["Fine", "Rest"]
    assert dividers(ax, "fraction_divider") == [0.075, 2.0]
    assert dividers(ax, "part_divider") == [0.25]


def test_unknown_system_is_the_analysis_error():
    with pytest.raises(HangtuError, match="no fraction system 'unified'"):
        ht.plot.grain_size(EMPTY, fractions="unified")


def test_fractions_none_hides_band_and_dividers():
    fig, ax = ht.plot.grain_size(EMPTY, fractions=None)
    assert ax.grain_size_header is None
    assert len(fig.axes) == 1
    assert dividers(ax, "fraction_divider") == []
    assert dividers(ax, "part_divider") == []


def test_only_fractions_in_range_are_named():
    _, ax = ht.plot.grain_size(EMPTY, xlim=(0.1, 10))
    assert texts(ax.grain_size_header, "fraction_name") == ["Sand", "Gravel"]
    assert dividers(ax, "fraction_divider") == [4.75]


# --- Header ------------------------------------------------------------------


def test_header_is_045_in_and_shares_x():
    fig, ax = ht.plot.grain_size(EMPTY)
    fig.canvas.draw()
    header = ax.grain_size_header
    box = header.get_window_extent()
    assert box.height / fig.dpi == pytest.approx(0.45, abs=0.01)
    assert header.get_xlim() == ax.get_xlim()
    assert box.y0 == pytest.approx(ax.get_window_extent().y1, abs=1)


def test_header_composes_on_a_sheet():
    sheet = ht.Sheet("letter", layout=(2, 1))
    panel = sheet[0]
    fig, ax = ht.plot.grain_size(EMPTY, ax=panel)
    assert ax is panel and fig is sheet.figure
    assert ax.grain_size_header in sheet.figure.axes
    fig.canvas.draw()
    top = ax.grain_size_header.get_window_extent()
    lower = sheet[1]
    fig.canvas.draw()
    assert top.y1 <= fig.bbox.y1
    assert ax.get_window_extent().y0 > lower.get_window_extent().y1
    plt.close(fig)


# --- Axes (§6) ---------------------------------------------------------------


def test_axes_defaults():
    _, ax = ht.plot.grain_size(EMPTY)
    assert ax.get_xscale() == "log"
    np.testing.assert_allclose(ax.get_xlim(), (0.001, 100))
    assert ax.get_ylim() == (0, 100)
    assert ax.get_xlabel() == "Particle size (mm)"
    assert ax.get_ylabel() == "Percent passing (%)"
    ax.figure.canvas.draw()
    low, high = ax.get_xlim()
    labels = [
        t.get_text()
        for t in ax.get_xticklabels()
        if t.get_text() and low <= t.get_position()[0] <= high
    ]
    assert labels == ["0.001", "0.01", "0.1", "1", "10", "100"]
    ticks = ax.get_yticks()
    np.testing.assert_allclose(
        ticks[(ticks >= 0) & (ticks <= 100)], np.arange(0, 101, 10)
    )
    assert "No data" in [t.get_text() for t in ax.texts]


def test_reverse_puts_coarse_on_the_left():
    _, ax = ht.plot.grain_size(EMPTY, reverse=True)
    to_screen = ax.transData.transform
    assert to_screen((100, 0))[0] < to_screen((0.1, 0))[0]
    assert ax.grain_size_header.xaxis_inverted()


def test_xlim_is_used_as_given():
    _, ax = ht.plot.grain_size(EMPTY, xlim=(0.01, 10))
    np.testing.assert_allclose(ax.get_xlim(), (0.01, 10))


@pytest.mark.parametrize("xlim", [(0, 10), (1,), "wide"])
def test_bad_xlim_is_an_error(xlim):
    with pytest.raises(HangtuError, match="xlim"):
        ht.plot.grain_size(EMPTY, xlim=xlim)


# --- Sieve labels (§8, §12) --------------------------------------------------


def test_us_sieve_labels():
    _, ax = ht.plot.grain_size(EMPTY, display_units="US")
    labels = sieve_labels(ax)
    assert labels["#200"] == 0.075
    assert labels["#4"] == 4.75
    assert len(labels) == 12


def test_si_sieve_labels():
    _, ax = ht.plot.grain_size(EMPTY, display_units="SI")
    labels = sieve_labels(ax)
    assert labels["0.063"] == 0.063
    assert "#200" not in labels


def test_sieve_list_by_name_and_none():
    _, ax = ht.plot.grain_size(EMPTY, display_units="US", sieves="iso")
    assert "0.063" in sieve_labels(ax)
    _, ax = ht.plot.grain_size(EMPTY, sieves=None)
    assert sieve_labels(ax) == {}


def test_users_sieve_list_and_range():
    _, ax = ht.plot.grain_size(
        EMPTY, sieves=[(0.0005, "tiny"), (1.0, "one"), (500, "big")]
    )
    assert sieve_labels(ax) == {"one": 1.0}


@pytest.mark.parametrize(
    "sieves", ["metric", [(0, "zero")], [(1.0,)], [("1", "one")], 5]
)
def test_bad_sieves_is_an_error(sieves):
    with pytest.raises(HangtuError, match="sieves must be"):
        ht.plot.grain_size(EMPTY, sieves=sieves)


# --- Contract ----------------------------------------------------------------


def test_bad_display_units_is_an_error():
    with pytest.raises(HangtuError, match="display_units"):
        ht.plot.grain_size(EMPTY, display_units="metric")


def test_no_global_state(assert_no_global_state):
    assert_no_global_state(ht.plot.grain_size, EMPTY)
    sheet = ht.Sheet("letter")
    assert_no_global_state(ht.plot.grain_size, EMPTY, ax=sheet[0])
    plt.close(sheet.figure)
