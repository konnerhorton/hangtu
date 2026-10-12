import pytest

import hangtu as ak


def test_defaults():
    assert ak.settings.display_units == "US"
    assert ak.settings.display_overrides == {}
    assert ak.settings.vertical_datum is None
    assert ak.settings.palette == {}
    assert ak.settings.figure_sizes == {"default": (6.5, 4.5), "profile": (4.0, 6.5)}
    assert ak.settings.hints is True
    assert ak.settings.hammer_efficiency is None
    assert ak.settings.spt_cap == 100


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
    ],
)
def test_valid_values_are_stored(name, value):
    setattr(ak.settings, name, value)
    assert getattr(ak.settings, name) == value


def test_figure_sizes_are_stored_as_float_pairs():
    ak.settings.figure_sizes = {"default": [8, 5]}
    assert ak.settings.figure_sizes == {"default": (8.0, 5.0)}


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
    ],
)
def test_invalid_values_raise_and_keep_the_old_value(name, value, message):
    before = getattr(ak.settings, name)
    with pytest.raises(ak.AgsKitError, match=message):
        setattr(ak.settings, name, value)
    assert getattr(ak.settings, name) == before


def test_unknown_setting_raises_naming_the_settings():
    with pytest.raises(
        ak.AgsKitError, match=r"no setting 'display_unit'.*display_units"
    ):
        ak.settings.display_unit = "SI"
    with pytest.raises(AttributeError, match="no setting 'display_unit'"):
        _ = ak.settings.display_unit


def test_stored_dicts_are_copies():
    palette = {"Alluvium": "tan"}
    ak.settings.palette = palette
    palette["Till"] = "gray"
    assert ak.settings.palette == {"Alluvium": "tan"}


def test_override_restores_values_after_the_block():
    with ak.settings.override(display_units="SI", hints=False):
        assert ak.settings.display_units == "SI"
        assert ak.settings.hints is False
    assert ak.settings.display_units == "US"
    assert ak.settings.hints is True


def test_override_restores_values_when_the_block_raises():
    with pytest.raises(RuntimeError), ak.settings.override(display_units="SI"):
        raise RuntimeError
    assert ak.settings.display_units == "US"


def test_override_with_an_invalid_value_changes_nothing():
    with (
        pytest.raises(ak.AgsKitError, match="spt_cap"),
        ak.settings.override(display_units="SI", spt_cap=-1),
    ):
        pass
    assert ak.settings.display_units == "US"


def test_reset_restores_defaults():
    ak.settings.display_units = "SI"
    ak.settings.palette = {"Alluvium": "tan"}
    ak.settings.reset()
    assert ak.settings.display_units == "US"
    assert ak.settings.palette == {}
