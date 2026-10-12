"""M1 "done when": a dummy plot built from the P00 helpers composes on a Sheet."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import hangtu as ak


@pytest.fixture
def water_content():
    frame = pd.DataFrame(
        {
            "loca_id": ["BH1", "BH1", "BH1", "BH2", "BH2"],
            "depth": [2.0, 6.5, 11.0, 4.0, np.nan],
            "water_content": [18.0, 24.5, 31.0, 140.0, 22.0],
            "geology_unit": ["Fill", "Alluvium", "Alluvium", "Till", "Till"],
        }
    )
    return ak.set_units(frame, {"depth": "ft"})


def test_dummy_plot_composes_on_a_sheet(dummy_plot, water_content):
    sheet = ak.Sheet("tabloid", layout=(1, 2), title="Site A")
    figures = plt.get_fignums()
    fig, ax = dummy_plot(water_content, "water_content", ax=sheet[0])
    dummy_plot(water_content, "water_content", ax=sheet[1], xlim=(0, 100))
    assert plt.get_fignums() == figures
    assert fig is sheet.figure
    assert ax.get_xlabel() == "Water content, w (%)"
    assert ax.get_ylabel() == "Depth (ft)"
    assert ax.ags_notes == {"nan": 1}
    assert sheet[1].ags_notes == {"nan": 1, "beyond_limit": 1}
    assert [t.get_text() for t in ax.get_legend().get_texts()] == [
        "Alluvium",
        "Fill",
        "Till",
    ]


def test_dummy_plot_leaves_no_global_state(
    dummy_plot, assert_no_global_state, water_content
):
    assert_no_global_state(dummy_plot, water_content, value="water_content")
    _, ax = plt.subplots()
    assert_no_global_state(dummy_plot, water_content, value="water_content", ax=ax)


def test_rcparams_restored_when_the_plot_raises(dummy_plot, water_content):
    before = dict(plt.rcParams)
    # No elevation column: warns about its units, then fails inside the plot.
    with pytest.warns(UserWarning, match="'elevation'"), pytest.raises(KeyError):
        dummy_plot(water_content, "water_content", vs="elevation")
    assert dict(plt.rcParams) == before


def test_dummy_plot_is_the_same_in_us_and_si(
    dummy_plot, assert_us_si_equivalent, water_content
):
    assert_us_si_equivalent(
        dummy_plot, water_content, ("percent", "length"), value="water_content"
    )


def test_units_are_unknown_after_merge(dummy_plot, water_content):
    ground = pd.DataFrame({"loca_id": ["BH1", "BH2"], "ground_level": [10.0, 12.0]})
    merged = water_content.merge(ground, on="loca_id")
    with pytest.warns(UserWarning, match="'depth' has no units"):
        _, ax = dummy_plot(merged, "water_content")
    assert ax.get_ylabel() == "Depth (units unknown)"


def test_missing_geology_gives_one_hint(dummy_plot, water_content):
    with pytest.warns(ak.AgsKitHint, match="'geology_unit'") as record:
        _, ax = dummy_plot(water_content.drop(columns="geology_unit"), "water_content")
    assert len(record) == 1
    assert ax.get_legend() is None


def test_panels_get_the_house_style(dummy_plot, water_content):
    sheet = ak.Sheet(layout=(1, 1))
    _, ax = dummy_plot(water_content, "water_content", ax=sheet[0])
    assert ax.xaxis.get_gridlines()[0].get_visible()
    assert ax.xaxis.get_major_ticks()[0]._tickdir == "in"


P00_API = [
    "settings",
    "read_csv",
    "set_units",
    "units_of",
    "add_unit_alias",
    "define_unit",
    "columns",
    "template",
    "Sheet",
    "AgsKitError",
    "UnitsError",
    "ColumnError",
    "AgsKitHint",
    "plot.palette_cmap",
    "plot.legend_handles",
    "plot.reset_palette",
    "plot.style.context",
]


@pytest.mark.parametrize("name", P00_API)
def test_p00_public_api_exists(name):
    target = ak
    for part in name.split("."):
        target = getattr(target, part)
