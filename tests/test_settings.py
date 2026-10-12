import pytest

import hangtu as ht


def test_defaults():
    assert ht.settings.display_units == "US"
    assert ht.settings.display_overrides == {}
    assert ht.settings.vertical_datum is None
    assert ht.settings.palette == {}
    assert ht.settings.figure_sizes == {
        "default": (6.5, 4.5),
        "profile": (4.0, 6.5),
        "grid": (3.75, 2.75),
    }
    assert ht.settings.hints is True
    assert ht.settings.hammer_efficiency is None
    assert ht.settings.spt_cap == 100
    assert ht.settings.summary_min_count == 5


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("display_units", "SI"),
        ("display_overrides", {"stress": "ksf"}),
        ("vertical_datum", "NAVD88"),
        ("palette", {"Alluvium": "tan", "Till": "#808080"}),
        ("hints", False),
        ("hammer_efficiency", 80.0),
        ("spt_cap", 50),
        ("summary_min_count", 1),
    ],
)
def test_valid_values_are_stored(name, value):
    setattr(ht.settings, name, value)
    assert getattr(ht.settings, name) == value


def test_figure_sizes_are_stored_as_float_pairs():
    ht.settings.figure_sizes = {"default": [8, 5]}
    assert ht.settings.figure_sizes == {"default": (8.0, 5.0)}


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("display_units", "us", '"US" or "SI"'),
        ("display_overrides", ["stress"], "dict of {quantity kind: unit}"),
        ("vertical_datum", "", "datum name or None"),
        ("palette", {"Alluvium": "not a color"}, r"\['Alluvium'\]"),
        ("figure_sizes", {"profile": (4, 6)}, '"default"'),
        ("figure_sizes", {"default": (6.5, 0)}, r"figure_sizes\['default'\]"),
        ("figure_sizes", {"default": (6.5,)}, r"figure_sizes\['default'\]"),
        ("hints", 1, "True or False"),
        ("hammer_efficiency", 0, "greater than 0 and at most 100"),
        ("hammer_efficiency", 120, "greater than 0 and at most 100"),
        ("spt_cap", 100.0, "positive whole number"),
        ("spt_cap", True, "positive whole number"),
        ("spt_cap", 0, "positive whole number"),
        ("summary_min_count", 0, "at least 1"),
        ("summary_min_count", 2.5, "at least 1"),
        ("summary_min_count", True, "at least 1"),
    ],
)
def test_invalid_values_raise_and_keep_the_old_value(name, value, message):
    before = getattr(ht.settings, name)
    with pytest.raises(ht.HangtuError, match=message):
        setattr(ht.settings, name, value)
    assert getattr(ht.settings, name) == before


def test_unknown_setting_raises_naming_the_settings():
    with pytest.raises(
        ht.HangtuError, match=r"no setting 'display_unit'.*display_units"
    ):
        ht.settings.display_unit = "SI"
    with pytest.raises(AttributeError, match="no setting 'display_unit'"):
        _ = ht.settings.display_unit


def test_stored_dicts_are_copies():
    palette = {"Alluvium": "tan"}
    ht.settings.palette = palette
    palette["Till"] = "gray"
    assert ht.settings.palette == {"Alluvium": "tan"}


def test_override_restores_values_after_the_block():
    with ht.settings.override(display_units="SI", hints=False):
        assert ht.settings.display_units == "SI"
        assert ht.settings.hints is False
    assert ht.settings.display_units == "US"
    assert ht.settings.hints is True


def test_override_restores_values_when_the_block_raises():
    with pytest.raises(RuntimeError), ht.settings.override(display_units="SI"):
        raise RuntimeError
    assert ht.settings.display_units == "US"


def test_override_with_an_invalid_value_changes_nothing():
    with (
        pytest.raises(ht.HangtuError, match="spt_cap"),
        ht.settings.override(display_units="SI", spt_cap=-1),
    ):
        pass
    assert ht.settings.display_units == "US"


def test_reset_restores_defaults():
    ht.settings.display_units = "SI"
    ht.settings.palette = {"Alluvium": "tan"}
    ht.settings.reset()
    assert ht.settings.display_units == "US"
    assert ht.settings.palette == {}
