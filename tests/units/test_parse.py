import itertools

import pytest

import hangtu as ht
from hangtu import _config, units
from hangtu.units import check_dimension, parse_unit, ureg


@pytest.mark.parametrize("text", _config.load("units/aliases.yaml"))
def test_every_shipped_alias_parses_silently(text):
    assert isinstance(parse_unit(text), type(ureg.Unit("m")))


def test_pint_only_string_is_accepted_with_a_warning():
    with pytest.warns(
        UserWarning, match=r'"feet" for column \'depth\' was read as foot'
    ):
        unit = parse_unit("feet", "depth")
    assert unit == ureg.Unit("foot")


def test_warning_from_inside_the_package_points_at_the_users_line():
    with pytest.warns(UserWarning, match="kip/ft") as record:
        ht.settings.display_overrides = {"stress": "kip/ft**2"}
    assert record[0].filename == __file__


def test_unknown_string_raises_naming_the_column_and_the_fix():
    with pytest.raises(
        ht.UnitsError, match=r"'depth'.*Did you mean \"ft\".*add_unit_alias"
    ):
        parse_unit("Ft", "depth")


@pytest.mark.parametrize("text", ["", "   ", None, 3])
def test_non_strings_raise(text):
    with pytest.raises(ht.UnitsError, match="must be a unit string"):
        parse_unit(text)


def test_add_unit_alias_makes_a_string_parse_silently():
    ht.add_unit_alias("Ft", "foot")
    assert parse_unit("Ft") == ureg.Unit("foot")


def test_add_unit_alias_rejects_an_unknown_pint_expression():
    with pytest.raises(ht.UnitsError, match="pint doesn't understand"):
        ht.add_unit_alias("bl", "blorp")


def test_aliases_reset_between_tests():
    assert "Ft" not in units._aliases


def test_define_unit_then_alias():
    ht.define_unit("test_rod = 3.0 * meter")
    ht.add_unit_alias("rods", "test_rod")
    assert (2.0 * parse_unit("rods")).to("meter").magnitude == pytest.approx(6.0)


def test_define_unit_rejects_bad_syntax():
    with pytest.raises(ht.UnitsError, match="Can't define unit"):
        ht.define_unit("= meter")


# --- Dimensions (P00 §4.3) -----------------------------------------------------


@pytest.mark.parametrize(
    ("text", "quantity"),
    [
        ("ft", "length"),
        ("kPa", "stress"),
        ("ksf", "stress"),
        ("pcf", "unit_weight"),
        ("pcf", "density"),
        ("Mg/m3", "density"),
        ("%", "percent"),
        ("%", "dimensionless"),
        ("deg", "angle"),
    ],
)
def test_units_of_the_right_dimension_pass(text, quantity):
    check_dimension(parse_unit(text), quantity)


@pytest.mark.parametrize(
    ("text", "quantity", "message"),
    [
        ("kPa", "length", 'a length, but its unit "kilopascal" is a stress unit'),
        ("Mg/m3", "unit_weight", "is a density unit"),
        ("m", "percent", "is a length unit"),
        ("m", "count", "is a length unit"),
        ("m/s**2", "length", r"\[length\] / \[time\] \*\* 2"),
    ],
)
def test_units_of_the_wrong_dimension_raise(text, quantity, message):
    with pytest.raises(ht.UnitsError, match=message):
        check_dimension(ureg.Unit(units._aliases.get(text, text)), quantity)


def test_display_override_with_the_wrong_dimension_raises():
    with pytest.raises(ht.HangtuError, match=r"display_overrides\['stress'\].*length"):
        ht.settings.display_overrides = {"stress": "ft"}


@pytest.mark.parametrize("kind", ["percent", "loudness"])
def test_display_override_for_a_kind_without_units_raises(kind):
    with pytest.raises(ht.HangtuError, match=f"can't set a unit for '{kind}'"):
        ht.settings.display_overrides = {kind: "ft"}


def test_every_display_unit_has_its_kinds_dimension():
    for (name, kind), system in itertools.product(
        _config.quantity_kinds().items(), ["US", "SI"]
    ):
        if kind[system]["unit"]:
            check_dimension(ureg.Unit(kind[system]["unit"]), name)
