"""select() with no source (docs/work/m18f-mohr-coulomb-set.md, decision 20, AC 11).

A parameter nothing measures yet is selected by value or none: nothing is
compared, placed or drawn.
"""

import warnings

import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError

#: 1 psf in kPa: 0.45359237 kg × 9.80665 m/s² / 0.3048² m² (exact).
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000
GIVEN = {"method": "value", "value": "32 deg", "reason": "from the design report"}
NONE = {"method": "none", "reason": "designed undrained"}


def _select(**kwargs):
    """Select with no sources, failing on any warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return ht.stats.select(**kwargs)


def test_value_and_none_are_accepted():
    result = _select(
        value="effective_friction_angle",
        selection={"Terrace": GIVEN, "Alluvium": NONE},
    )
    frame = result.to_frame()
    assert list(frame["geology_unit"]) == ["Terrace", "Alluvium"]
    assert frame["value"].iloc[0] == 32
    assert pd.isna(frame["value"].iloc[1])
    assert list(frame["selection_method"]) == ["value", "none"]
    assert result.unit == "deg"
    assert frame.attrs["units"]["value"] == "deg"


def test_a_value_is_converted_to_display_units():
    result = _select(
        value="undrained_shear_strength",
        selection={
            "Clay": {"method": "value", "value": "50 kPa", "reason": "x"},
            "Silt": {"method": "value", "value": "1000 psf", "reason": "y"},
        },
        display_units="US",
    )
    assert result.unit == "psf"
    values = result.to_frame()["value"]
    assert values.iloc[0] == pytest.approx(50 / PSF, rel=1e-9)
    assert values.iloc[1] == pytest.approx(1000, rel=1e-9)


def test_other_entries_take_the_first_values_unit():
    result = _select(
        value="undrained_shear_strength",
        selection={
            "Clay": {"method": "value", "value": "50 kPa", "reason": "x"},
            "Silt": {"method": "value", "value": "1000 psf", "reason": "y"},
        },
    )
    assert result.unit == "kPa"
    assert result.to_frame()["value"].iloc[1] == pytest.approx(1000 * PSF, rel=1e-9)


@pytest.mark.parametrize("method", ["characteristic", "fitted"])
def test_another_method_is_refused(method):
    entry = {"method": method, "source": "triaxial", "reason": "x"}
    if method == "characteristic":
        entry |= {"estimate": "mean", "side": "low", "distribution": "normal"}
    with pytest.raises(HangtuError, match=r"no source carries 'effective_frict"):
        _select(value="effective_friction_angle", selection={"Terrace": entry})


def test_views_with_no_comparison():
    result = _select(
        value="effective_friction_angle",
        selection={"Terrace": GIVEN, "Alluvium": NONE},
    )
    assert result.comparison is None
    assert result.positions().empty
    with pytest.raises(HangtuError, match=r"design_lines\(\): no source carries"):
        result.design_lines()
    with pytest.raises(HangtuError, match=r"profile\(\): no source carries"):
        result.profile("Terrace")
    as_dict = result.to_dict()
    assert as_dict["comparison"] is None
    assert as_dict["rows"][0]["value"] == 32
    text = str(result)
    assert "Terrace" in text
    assert "nothing to compare" in text
    assert result.judgments["selection"]["source"] == "argument"


def test_read_from_the_judgments_file(tmp_path):
    path = tmp_path / "judgments.yaml"
    path.write_text(
        "selection:\n"
        "  effective_friction_angle:\n"
        "    units: {value: deg}\n"
        "    values:\n"
        "      Terrace: {method: value, value: 34, reason: from the report}\n",
        encoding="utf-8",
    )
    result = _select(value="effective_friction_angle", judgments=path)
    assert result.to_frame()["value"].iloc[0] == 34
    assert result.judgments["selection"]["source"] == str(path)


def test_no_selection_shows_a_value_entry():
    with pytest.raises(HangtuError, match=r"method: value\n\s+value: \"1 deg\""):
        _select(value="effective_friction_angle")
