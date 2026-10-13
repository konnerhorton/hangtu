import pytest

import hangtu as ht
from hangtu import units
from hangtu.plot._presets import preset, preset_names
from hangtu.registry import column_info

P01_PRESETS = [
    "hydraulic_conductivity",
    "undrained_shear_strength",
    "water_content",
    "bulk_unit_weight",
]
P02_PRESETS = ["spt_n", "spt_n60", "spt_n_capped"]


def test_the_p01_and_p02_presets_ship():
    assert preset_names() == P01_PRESETS + P02_PRESETS


@pytest.mark.parametrize("name", P01_PRESETS + P02_PRESETS)
def test_preset_matches_the_registry(name):
    entry = preset(name)
    info = column_info(entry.column)
    assert entry.column == name
    assert entry.quantity == info["quantity"]
    assert entry.label == info["label"]
    assert entry.typical[0] < entry.typical[1]


@pytest.mark.parametrize(
    ("name", "log", "start_at_zero"),
    [
        ("hydraulic_conductivity", True, False),
        ("undrained_shear_strength", False, True),
        ("water_content", False, True),
        ("bulk_unit_weight", False, False),
        ("spt_n", False, True),
        ("spt_n60", False, True),
        ("spt_n_capped", False, True),
    ],
)
def test_preset_scale_follows_p01(name, log, start_at_zero):
    assert (preset(name).log, preset(name).start_at_zero) == (log, start_at_zero)


@pytest.mark.parametrize(
    ("name", "system", "expected"),
    [
        ("hydraulic_conductivity", "SI", (1e-11, 1e-2)),
        ("hydraulic_conductivity", "US", (1e-9, 1.0)),
        ("undrained_shear_strength", "SI", (0.0, 300.0)),
        ("undrained_shear_strength", "US", (0.0, 6265.6)),
        ("water_content", "US", (0.0, 100.0)),
        ("bulk_unit_weight", "SI", (14.0, 23.0)),
        ("bulk_unit_weight", "US", (89.1, 146.4)),
    ],
)
def test_typical_range_is_in_the_canonical_unit(name, system, expected):
    # P01 §6 gives the US ranges rounded: 0-6,000 psf and 90-145 pcf.
    entry = preset(name)
    canonical = units.quantity_kind(entry.quantity)["canonical"]
    values, _ = units.to_display(entry.typical, canonical, entry.quantity, system)
    assert values == pytest.approx(expected, rel=1e-3)


def test_unknown_preset_lists_the_presets():
    with pytest.raises(ht.HangtuError, match=r"no preset named 'su'.*undrained_shear"):
        preset("su")
