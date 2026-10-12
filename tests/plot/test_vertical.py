import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.plot._data import numeric_column
from hangtu.plot._vertical import (
    Vertical,
    choose_vs,
    convert_pair,
    convert_vertical,
    length_columns,
    vertical_values,
)
from hangtu.units import resolve_units


def _resolve(df, vs, display_units="US"):
    units = resolve_units(df, length_columns(df))
    return vertical_values(df, vs, units, display_units)


def _vertical(vs="elevation", ground_level=120.0, unknown=False):
    return Vertical(
        vs=vs,
        display_units="US",
        unit="ft",
        unit_text="ft",
        unknown=unknown,
        ground_level=ground_level,
    )


# --- choose_vs ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("columns", "expected"),
    [
        (["elevation"], "elevation"),
        (["depth", "ground_level"], "elevation"),
        (["depth", "elevation"], "elevation"),
        (["depth"], "depth"),
    ],
)
def test_vs_none_prefers_elevation_when_available(columns, expected):
    assert choose_vs(pd.DataFrame(columns=columns), None) == expected


@pytest.mark.parametrize("vs", ["depth", "elevation"])
def test_vs_given_is_kept(vs):
    df = pd.DataFrame(columns=["depth", "ground_level"])
    assert choose_vs(df, vs) == vs


def test_depth_can_come_from_elevation_and_ground_level():
    df = pd.DataFrame(columns=["elevation", "ground_level"])
    assert choose_vs(df, "depth") == "depth"


def test_neither_depth_nor_elevation_names_both_and_the_columns():
    df = pd.DataFrame(columns=["loca_id", "hydraulic_conductivity"])
    with pytest.raises(ht.ColumnError) as error:
        choose_vs(df, None)
    message = str(error.value)
    assert "'depth'" in message
    assert "'elevation'" in message
    assert "'ground_level'" in message
    assert "Columns: loca_id, hydraulic_conductivity" in message


def test_elevation_without_a_way_to_get_it_explains_both_ways():
    with pytest.raises(ht.ColumnError) as error:
        choose_vs(pd.DataFrame(columns=["depth"]), "elevation")
    message = str(error.value)
    assert "'elevation' column" in message
    assert "'depth' plus 'ground_level'" in message
    assert "vs='depth'" in message


def test_depth_without_a_way_to_get_it_explains_both_ways():
    with pytest.raises(ht.ColumnError, match=r"'depth' column.*'elevation' plus"):
        choose_vs(pd.DataFrame(columns=["elevation"]), "depth")


def test_unknown_vs_is_an_error():
    with pytest.raises(ht.HangtuError, match=r"vs must be.*'elev'"):
        choose_vs(pd.DataFrame(columns=["depth"]), "elev")


# --- vertical_values -----------------------------------------------------------------


def test_elevation_is_ground_level_minus_depth():
    # P01 §12 golden value: GL 120.0 ft, depth 15.0 ft -> 105.0 ft.
    df = ht.set_units(
        pd.DataFrame({"depth": [15.0], "ground_level": [120.0]}),
        {"depth": "ft", "ground_level": "ft"},
    )
    values, vertical = _resolve(df, "elevation")
    assert values == pytest.approx([105.0])
    assert vertical.ground_level == pytest.approx(120.0)
    assert vertical.unit == "ft"
    assert vertical.label() == "Elevation (ft)"


def test_depth_is_ground_level_minus_elevation():
    df = ht.set_units(
        pd.DataFrame({"elevation": [105.0], "ground_level": [120.0]}),
        {"elevation": "ft", "ground_level": "ft"},
    )
    values, _ = _resolve(df, "depth")
    assert values == pytest.approx([15.0])


def test_an_elevation_column_is_used_as_given():
    df = ht.set_units(
        pd.DataFrame({"depth": [15.0], "ground_level": [120.0], "elevation": [99.0]}),
        {"depth": "ft", "ground_level": "ft", "elevation": "ft"},
    )
    values, _ = _resolve(df, "elevation")
    assert values == pytest.approx([99.0])


@pytest.mark.parametrize(
    ("display_units", "expected", "text"), [("US", 10.0, "ft"), ("SI", 3.048, "m")]
)
def test_depth_is_converted_to_display_units(display_units, expected, text):
    # P01 §12 golden value: 10.0 ft <-> 3.048 m.
    df = ht.set_units(pd.DataFrame({"depth": [10.0]}), {"depth": "ft"})
    values, vertical = _resolve(df, "depth", display_units)
    assert values == pytest.approx([expected])
    assert vertical.unit_text == text
    assert vertical.label() == f"Depth ({text})"


def test_depth_and_ground_level_convert_before_subtracting():
    df = ht.set_units(
        pd.DataFrame({"depth": [10.0], "ground_level": [30.0]}),
        {"depth": "ft", "ground_level": "m"},
    )
    values, vertical = _resolve(df, "elevation", "SI")
    assert values == pytest.approx([30.0 - 3.048])
    assert vertical.ground_level == pytest.approx(30.0)


def test_the_datum_is_on_elevation_labels_only():
    df = ht.set_units(
        pd.DataFrame({"depth": [10.0], "ground_level": [30.0]}),
        {"depth": "ft", "ground_level": "ft"},
    )
    with ht.settings.override(vertical_datum="NAVD88"):
        assert _resolve(df, "elevation")[1].label() == "Elevation (ft, NAVD88)"
        assert _resolve(df, "depth")[1].label() == "Depth (ft)"


def test_any_length_without_units_leaves_all_lengths_unconverted():
    df = ht.set_units(
        pd.DataFrame({"depth": [10.0], "ground_level": [30.0]}), {"depth": "ft"}
    )
    with pytest.warns(UserWarning, match="'ground_level' has no units"):
        values, vertical = _resolve(df, "elevation", "SI")
    assert values == pytest.approx([20.0])
    assert vertical.unknown
    assert vertical.unit_text is None
    assert vertical.label() == "Elevation (units unknown)"


@pytest.mark.parametrize(
    ("columns", "expected"),
    [
        ({"ground_level": [120.0, 120.0]}, 120.0),
        ({"ground_level": [120.0, np.nan]}, 120.0),
        ({"ground_level": [120.0, 118.0]}, None),
        ({"elevation": [105.0, 100.0]}, 120.0),  # elevation + depth
        ({"elevation": [105.0, 101.0]}, None),
        ({}, None),
    ],
)
def test_single_ground_level(columns, expected):
    df = pd.DataFrame({"depth": [15.0, 20.0], **columns})
    df = ht.set_units(df, dict.fromkeys(df.columns, "ft"))
    vs = "elevation" if columns else "depth"
    assert _resolve(df, vs)[1].ground_level == expected


def test_text_in_a_vertical_column_names_the_rows():
    df = pd.DataFrame({"depth": [1.0, "12 ft", None, "abc"]})
    with pytest.raises(ht.ColumnError) as error:
        numeric_column(df, "depth")
    message = str(error.value)
    assert "rows 1 ('12 ft'), 3 ('abc')" in message
    assert "leave them blank" in message


# --- convert_pair --------------------------------------------------------------


def test_a_pair_matching_vs_is_drawn_as_given():
    top, base = convert_pair([10.0], [20.0], "depth", _vertical("depth"), "strata")
    assert (top, base) == ([10.0], [20.0])


def test_a_depth_pair_converts_with_the_ground_level():
    # P01 §12: interval bounds convert like points (top 10, base 20 ft, GL 120 ft).
    top, base = convert_pair([10.0], [20.0], "depth", _vertical(), "strata")
    assert top == pytest.approx([110.0])
    assert base == pytest.approx([100.0])


def test_an_elevation_pair_converts_to_depth():
    top, base = convert_pair(
        [110.0], [100.0], "elevation", _vertical("depth"), "ranges"
    )
    assert top == pytest.approx([10.0])
    assert base == pytest.approx([20.0])


def test_a_pair_that_cant_be_converted_says_what_to_give():
    with pytest.raises(ht.HangtuError) as error:
        convert_pair([10.0], [20.0], "depth", _vertical(ground_level=None), "strata")
    message = str(error.value)
    assert "strata overlay is given in depth" in message
    assert "don't share one ground level" in message
    assert "Give elevation_top and elevation_base instead" in message
    assert "vs='depth'" in message


def test_a_single_position_names_its_own_column():
    with pytest.raises(ht.HangtuError, match="Give elevation instead"):
        convert_vertical(
            [10.0], "depth", _vertical(ground_level=None), "design_lines", "elevation"
        )


def test_overlay_lengths_follow_the_display_units():
    assert _vertical().to_display([10.0], "m") == pytest.approx([32.808399])
    assert _vertical(unknown=True).to_display([10.0], "m") == pytest.approx([10.0])
