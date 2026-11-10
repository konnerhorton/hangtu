"""SelectionResult's views: docs/work/m18e-selection.md, decision 15, AC 11 and 13.

The data are G1's and G3's from test_select_fitted.py: source A (selected, the
characteristic mean, 34.868 deg) and B in ``Sand`` at 1-5 m, and the G3 fit's
CD stages at 3-5 m.
"""

import json
import warnings

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError
from hangtu.plot._overlays import DESIGN_COLOR

from .conftest import FIT, FITTED, G1, PHI, g3_fit, phi, sources

G1_VALUE = 34.868
GIVEN = {"method": "value", "value": "32 deg", "reason": "cautious"}


def _quiet(call, *args, **kwargs):
    """Call, failing on any warning; P01's ground-level hint is turned off."""
    with ht.settings.override(hints=False), warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


def _dashed(ax):
    """Each design line drawn, as (x, y) arrays."""
    return [
        (line.get_xdata(), line.get_ydata())
        for line in ax.lines
        if line.get_linestyle() == "--" and line.get_color() == DESIGN_COLOR
    ]


def two_units():
    a, b = sources()
    clay = phi("A", [24.0, 25.0, 27.0, 28.0]).assign(geology_unit="Clay")
    a = ht.set_units(pd.concat([a, clay], ignore_index=True), a.attrs["units"])
    return a, b


# --- The views agree (AC 13) ---------------------------------------------------------


def test_frame_dict_and_summary_give_the_same_values():
    a, b = sources()
    result = ht.stats.select(a, b, g3_fit(), value=PHI, selection={"Sand": G1})
    row = result.to_frame().iloc[0]
    assert row["value"] == pytest.approx(G1_VALUE, abs=0.001)
    as_dict = result.to_dict()
    json.dumps(as_dict)  # JSON-serializable
    assert as_dict["rows"][0]["value"] == row["value"]
    assert as_dict["rows"][0]["entry"]["method"] == "characteristic"
    assert as_dict["representatives"]["Sand"] == result.representative("Sand").to_dict()
    assert as_dict["comparison"] == result.comparison.to_dict()
    positions = result.positions()
    assert [p["parameter_source"] for p in as_dict["positions"]] == (
        positions["parameter_source"].tolist()
    )
    assert as_dict["positions"][1]["difference"] == positions["difference"].iloc[1]
    text = str(result)
    assert text.splitlines()[0] == f"{PHI} (deg), selected by geology_unit"
    assert "Against the other sources" in text
    assert "Sand: 34.9 is within B (33.0 to 41.0, at P23)" in text
    assert f"Sand: 34.9 is 4.87 above {FIT}, 30.0" in text
    assert text.index("Against the other sources") < text.index(result.notes[0])
    assert result._repr_html_().startswith("<pre>")


def test_a_lines_summary_says_it_has_no_position():
    a, b = sources()
    entry = {**G1, "trend": "depth"}
    text = str(ht.stats.select(a, b, value=PHI, selection={"Sand": entry}))
    assert "Sand: B: no position (a line with depth)" in text


# --- design_lines() (decision 15; AC 11, second half) --------------------------------


def test_a_constant_view_is_drawn_over_its_sources_depths():
    a, b = sources()
    lines = ht.stats.select(a, b, value=PHI, selection={"Sand": G1}).design_lines()
    assert lines.columns.tolist() == ["label", "depth", "value"]
    assert lines["label"].unique().tolist() == ["Sand: selected, characteristic"]
    assert lines["depth"].tolist() == [1.0, 5.0]
    assert lines["value"].to_numpy() == pytest.approx([G1_VALUE] * 2, abs=0.001)
    assert lines.attrs["units"] == {"depth": "m", "value": "deg"}


def test_a_trends_lines_equal_representatives():
    a, b = sources()
    entry = {**G1, "trend": "depth"}
    result = ht.stats.select(a, b, value=PHI, selection={"Sand": entry})
    lines = result.design_lines()
    direct = ht.stats.representative(
        a,
        value=PHI,
        by="geology_unit",
        method="characteristic",
        estimate="mean",
        side="low",
        distribution="normal",
        trend="depth",
    ).design_lines()
    assert lines["label"].unique().tolist() == ["Sand: selected, characteristic"]
    pd.testing.assert_frame_equal(
        lines[["depth", "value"]], direct[["depth", "value"]], check_exact=False
    )
    assert lines.attrs["units"] == direct.attrs["units"]


def test_a_fitted_value_is_drawn_over_its_points_depths():
    lines = ht.stats.select(
        g3_fit(), value=PHI, selection={"Sand": FITTED}
    ).design_lines()
    assert lines["label"].unique().tolist() == ["Sand: selected, fitted"]
    assert lines["depth"].tolist() == [3.0, 5.0]
    assert lines["value"].to_numpy() == pytest.approx([30.0, 30.0], abs=0.0005)


def test_a_given_value_is_drawn_over_every_sources_depths():
    a, b = sources()
    b = b.assign(depth=b["depth"] + 2.0)  # B at 3-7 m
    result = ht.stats.select(a, b, g3_fit(), value=PHI, selection={"Sand": GIVEN})
    lines = result.design_lines()
    assert lines["label"].unique().tolist() == ["Sand: selected, value"]
    assert lines["depth"].tolist() == [1.0, 7.0]
    assert lines["value"].tolist() == [32.0, 32.0]


def test_a_unit_with_no_depths_has_no_line_and_a_note():
    a, b = sources()
    selection = {"Sand": G1, "Gravel": {**GIVEN, "value": "38 deg"}}
    result = ht.stats.select(a, b, value=PHI, selection=selection)
    lines = result.design_lines()
    assert lines["label"].unique().tolist() == ["Sand: selected, characteristic"]
    assert (
        "Gravel: no source has rows with a depth in this unit, so .design_lines() "
        "has no line for its selected value."
    ) in result.notes
    assert not any(note.startswith("Sand: no source") for note in result.notes)


def test_none_and_no_value_have_no_line():
    a, b = sources()
    none = {"method": "none", "reason": "not used"}
    lines = ht.stats.select(a, b, value=PHI, selection={"Sand": none}).design_lines()
    assert lines.empty
    assert lines.columns.tolist() == ["label", "depth", "value"]


def test_lines_are_in_the_comparisons_units():
    a, b = sources()
    a = ht.set_units(a.assign(depth=a["depth"] / 0.3048), {PHI: "deg", "depth": "ft"})
    result = ht.stats.select(b, a, value=PHI, selection={"Sand": {**G1, "source": "A"}})
    lines = result.design_lines()
    assert lines.attrs["units"]["depth"] == "m"
    assert lines["depth"].to_numpy() == pytest.approx([1.0, 5.0])
    assert lines["value"].iloc[0] == pytest.approx(G1_VALUE, abs=0.001)


# --- profile() (AC 13) ---------------------------------------------------------------


def test_profile_draws_the_sources_and_the_selected_line():
    a, b = sources()
    result = ht.stats.select(a, b, value=PHI, selection={"Sand": G1})
    _, ax = _quiet(result.profile)
    ((x, y),) = _dashed(ax)
    assert x == pytest.approx([G1_VALUE] * 2, abs=0.001)
    assert sorted(y) == pytest.approx([1.0 / 0.3048, 5.0 / 0.3048])  # P01 in US
    labels = [text.get_text() for text in ax.texts]
    assert "Sand: selected, characteristic" in labels


def test_profile_draws_only_the_named_units_line():
    a, b = two_units()
    given = {**GIVEN, "value": "25 deg"}
    result = ht.stats.select(a, b, value=PHI, selection={"Sand": G1, "Clay": given})
    _, ax = _quiet(result.profile, geology_unit="Clay")
    ((x, _),) = _dashed(ax)
    assert x == pytest.approx([25.0, 25.0])
    with pytest.raises(HangtuError, match=r"draws one unit.*geology_unit="):
        result.profile()


def test_profile_takes_design_lines_of_your_own():
    a, b = sources()
    result = ht.stats.select(a, b, value=PHI, selection={"Sand": G1})
    own = pd.DataFrame({"label": "mine", "depth": [1.0, 5.0], "value": [31.0, 31.0]})
    own.attrs["units"] = {"depth": "m", "value": "deg"}
    _, ax = _quiet(result.profile, design_lines=own)
    ((x, _),) = _dashed(ax)
    assert x == pytest.approx([31.0, 31.0])


def test_a_categorical_geology_unit_raises_no_warning():
    # A Project's datasets give geology_unit the geology map's categories,
    # some with no rows here.
    a, b = two_units()
    categories = ["Fill", "Clay", "Sand"]
    for frame in (a, b):
        frame["geology_unit"] = pd.Categorical(
            frame["geology_unit"], categories=categories
        )
    selection = {"Sand": G1, "Clay": {**GIVEN, "value": "25 deg"}}
    result = _quiet(ht.stats.select, a, b, value=PHI, selection=selection)
    assert result.to_frame()["geology_unit"].tolist() == ["Clay", "Sand"]
    lines = result.design_lines()
    assert lines["label"].unique().tolist() == [
        "Clay: selected, value",
        "Sand: selected, characteristic",
    ]
    _, ax = _quiet(result.profile, geology_unit="Sand")
    ((x, _),) = _dashed(ax)
    assert x == pytest.approx([G1_VALUE] * 2, abs=0.001)
    str(result)
    assert np.isfinite(result.to_frame()["value"]).all()


def test_profile_draws_against_depth_when_ground_levels_differ():
    # A Project's holes: elevation and ground levels that differ, so P01 would
    # draw against elevation, where depth lines can't be placed.
    a, b = sources()
    for frame, ground in ((a, 100.0), (b, 95.0)):
        frame["ground_level"] = ground
        frame["elevation"] = ground - frame["depth"]
        frame["loca_id"] = f"B-{int(ground)}"
        frame.attrs["units"] |= {"ground_level": "m", "elevation": "m"}
    result = ht.stats.select(a, b, value=PHI, selection={"Sand": G1})
    _, ax = _quiet(result.profile, display_units="SI")
    assert ax.get_ylabel().startswith("Depth")
    ((x, _),) = _dashed(ax)
    assert x == pytest.approx([G1_VALUE] * 2, abs=0.001)
