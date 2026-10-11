import numpy as np
import pytest

import ags_kit as ak
from ags_kit.units import to_display


# P00 §14 golden values, hand-calculated:
# 1 ft = 0.3048 m; 1 psf = 0.45359237 kg x 9.80665 m/s² / 0.3048² m² = 47.880 Pa;
# 1 lbf/ft³ = 4.4482 N / 0.028317 m³ = 157.09 N/m³; 1 lb/ft³ = 16.018 kg/m³;
# 1 in = 25.4 mm.
@pytest.mark.parametrize(
    ("value", "unit", "quantity", "expected", "text"),
    [
        (10.0, "ft", "length", 3.048, "m"),
        (2000.0, "psf", "stress", 95.76, "kPa"),
        (120.0, "pcf", "unit_weight", 18.85, "kN/m³"),
        (120.0, "pcf", "density", 1.922, "Mg/m³"),
        (6.0, "in", "small_length", 152.4, "mm"),
    ],
)
def test_golden_values_us_to_si(value, unit, quantity, expected, text):
    magnitudes, label = to_display([value], unit, quantity, "SI")
    assert magnitudes[0] == pytest.approx(expected, rel=5e-4)
    assert label == text


def test_golden_value_hydraulic_conductivity_si_to_us():
    magnitudes, label = to_display([1.0e-5], "m/s", "hydraulic_conductivity", "US")
    assert magnitudes[0] == pytest.approx(1.0e-3)
    assert label == "cm/s"


@pytest.mark.parametrize(
    ("value", "unit", "quantity"),
    [
        (10.0, "ft", "length"),
        (2000.0, "psf", "stress"),
        (120.0, "pcf", "unit_weight"),
        (6.0, "in", "small_length"),
        (2.5e-4, "cm/s", "hydraulic_conductivity"),
    ],
)
def test_us_value_shown_in_si_converts_back_by_hand(value, unit, quantity):
    by_hand = {"ft": 0.3048, "psf": 0.047880259, "pcf": 0.15708746, "in": 25.4}
    by_hand["cm/s"] = 0.01
    si, _ = to_display([value], unit, quantity, "SI")
    assert si[0] / by_hand[unit] == pytest.approx(value, rel=1e-6)


def test_display_units_default_to_the_setting():
    assert to_display([10.0], "m", "length")[1] == "ft"
    with ak.settings.override(display_units="SI"):
        assert to_display([10.0], "ft", "length")[1] == "m"


def test_display_override_changes_the_unit():
    ak.settings.display_overrides = {"stress": "ksf"}
    magnitudes, label = to_display([95.76], "kPa", "stress", "US")
    assert magnitudes[0] == pytest.approx(2.0, rel=5e-4)
    assert label == "ksf"


def test_override_text_uses_superscripts():
    ak.settings.display_overrides = {"unit_weight": "kN/m3"}
    assert to_display([1.0], "pcf", "unit_weight", "US")[1] == "kN/m³"


@pytest.mark.parametrize(
    ("quantity", "text"), [("percent", "%"), ("dimensionless", None), ("count", None)]
)
def test_unconverted_kinds_pass_values_through(quantity, text):
    magnitudes, label = to_display([12.0, 30.0], None, quantity, "SI")
    np.testing.assert_array_equal(magnitudes, [12.0, 30.0])
    assert label == text


def test_unknown_unit_passes_values_through_without_a_label():
    magnitudes, label = to_display([4.0], None, "length", "SI")
    assert magnitudes[0] == 4.0
    assert label is None


def test_unregistered_column_stays_in_its_declared_unit():
    magnitudes, label = to_display([4.0], "kN/m3", None, "US")
    assert magnitudes[0] == 4.0
    assert label == "kN/m³"


def test_invalid_display_units_argument_raises():
    with pytest.raises(ak.AgsKitError, match='"US" or "SI"'):
        to_display([1.0], "ft", "length", "metric")
