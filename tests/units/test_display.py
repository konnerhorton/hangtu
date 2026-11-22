import numpy as np
import pytest

import hangtu as ht
from hangtu import units
from hangtu.units import to_display


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
    with ht.settings.override(display_units="SI"):
        assert to_display([10.0], "ft", "length")[1] == "m"


def test_display_override_changes_the_unit():
    ht.settings.display_overrides = {"stress": "ksf"}
    magnitudes, label = to_display([95.76], "kPa", "stress", "US")
    assert magnitudes[0] == pytest.approx(2.0, rel=5e-4)
    assert label == "ksf"


def test_override_text_uses_superscripts():
    ht.settings.display_overrides = {"unit_weight": "kN/m3"}
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
    with pytest.raises(ht.HangtuError, match='"US" or "SI"'):
        to_display([1.0], "ft", "length", "metric")


# --- Modulus and velocity (docs/work/m13b3-spt-stiffness.md, Decision 6, AC 6) --------


@pytest.mark.parametrize(
    ("system", "expected", "text"),
    [("SI", 13.406, "MPa"), ("US", 280.0, "ksf")],
)
def test_a_modulus_displays_in_mpa_or_ksf(system, expected, text):
    # 140 tsf by hand: 140 x 95.7605 kPa = 13 406 kPa, and 140 x 2 = 280 ksf.
    magnitudes, label = to_display([13406.47], "kPa", "modulus", system)
    assert magnitudes[0] == pytest.approx(expected, rel=1e-4)
    assert label == text


@pytest.mark.parametrize(
    ("system", "expected", "text"),
    [("SI", 191.31, "m/s"), ("US", 627.66, "ft/s")],
)
def test_a_velocity_displays_in_m_per_s_or_ft_per_s(system, expected, text):
    magnitudes, label = to_display([191.31], "m/s", "velocity", system)
    assert magnitudes[0] == pytest.approx(expected, rel=1e-4)
    assert label == text


@pytest.mark.parametrize(
    ("unit", "kind"),
    [
        ("kPa", "stress"),
        ("m/s", "hydraulic_conductivity"),
        ("m2/MN", "volume_compressibility"),
        ("m2/yr", "consolidation_coefficient"),
    ],
)
def test_new_kinds_leave_the_first_match_of_a_unit_unchanged(unit, kind):
    # AGS ingest canonicalizes a heading by its unit's first kind (_kind_of).
    assert units._kind_of(units.parse_unit(unit)) == kind


# M19 (a): 1 m²/MN = 10.7639104 ft² / 224.808943 kip = 0.04788026 ft²/kip;
# 1 m²/yr = 10.7639104 ft²/yr.
_FT2_PER_KIP = 10.7639104 / 224.808943


@pytest.mark.parametrize(
    ("value", "unit", "quantity", "expected", "text"),
    [
        (0.16, "m2/MN", "volume_compressibility", 0.16 * _FT2_PER_KIP, "ft²/kip"),
        (2.1, "m2/yr", "consolidation_coefficient", 22.60421, "ft²/yr"),
    ],
)
def test_golden_values_oedometer_kinds_si_to_us(value, unit, quantity, expected, text):
    magnitudes, label = to_display([value], unit, quantity, "US")
    assert magnitudes[0] == pytest.approx(expected, rel=1e-6)
    assert label == text


@pytest.mark.parametrize("system", ["US", "SI"])
def test_a_time_displays_in_minutes_in_both_systems(system):
    # M19 (c2): no other kind has time's dimension, and both systems read minutes.
    assert units._kind_of(units.parse_unit("s")) == "time"
    magnitudes, label = to_display([90.0], "s", "time", system)
    assert magnitudes[0] == pytest.approx(1.5, rel=1e-12)
    assert label == "min"
