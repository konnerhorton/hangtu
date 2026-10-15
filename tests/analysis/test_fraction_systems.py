"""Size fractions and fraction systems (docs/drafts/analysis.md §3.5, §3.7)."""

import numpy as np
import pandas as pd
import pytest
import yaml

import hangtu as ht
from hangtu.analysis._fractions import builtin_systems, check_system, passing_at
from hangtu.errors import HangtuError

SIZES = [0.075, 0.15, 0.3, 0.6, 1.18, 2.36, 4.75]
PASSING = [4, 12, 30, 55, 75, 90, 100]
#: P(0.425) and P(2.0) on curve A, worked by hand (log-linear).
P_0425 = 30 + np.log10(0.425 / 0.3) / np.log10(2) * 25
P_2 = 75 + np.log10(2.0 / 1.18) / np.log10(2.36 / 1.18) * 15


def curve_a():
    df = pd.DataFrame(
        {"specimen_id": "A", "particle_size": SIZES, "percent_passing": PASSING}
    )
    return ht.set_units(df, {"particle_size": "mm"})


def fractions(system, **kwargs):
    row = ht.analysis.gradation(curve_a(), fractions=system, **kwargs).iloc[0]
    return {
        name.removesuffix("_content"): row[name]
        for name in row.index
        if name.endswith("_content")
    }, row["fraction_system"]


# --- Curve A golden values --------------------------------------------------------


def test_hand_worked_passing_values():
    assert pytest.approx(42.56, abs=5e-3) == P_0425
    assert pytest.approx(86.42, abs=5e-3) == P_2


def test_curve_a_astm_uscs():
    got, system = fractions("astm_uscs")
    assert system == "astm_uscs"
    assert got == pytest.approx(
        {"fines": 4.0, "sand": 96.0, "gravel": 0.0, "cobbles": 0.0, "boulders": 0.0}
    )


def test_curve_a_aashto():
    got, _ = fractions("aashto")
    assert got == pytest.approx(
        {
            "silt_clay": 4.0,
            "fine_sand": P_0425 - 4,
            "coarse_sand": P_2 - P_0425,
            "gravel": 100 - P_2,
            "boulders": 0.0,
        }
    )
    assert got["gravel"] == pytest.approx(13.58, abs=5e-3)


def test_curve_a_iso_leaves_what_it_cant_reach_blank():
    with pytest.warns(UserWarning, match="clay in 1 curve, silt in 1 curve, sand in 1"):
        got, _ = fractions("iso14688")
    assert np.isnan(got["clay"])
    assert np.isnan(got["silt"])
    assert np.isnan(got["sand"])
    assert got["gravel"] == pytest.approx(100 - P_2)
    assert got["cobbles"] == 0.0


@pytest.mark.parametrize("system", ["astm_uscs", "aashto"])
def test_fractions_sum_to_100(system):
    got, _ = fractions(system)
    assert sum(got.values()) == pytest.approx(100.0)


def test_default_system_is_astm_uscs():
    row = ht.analysis.gradation(curve_a()).iloc[0]
    assert row["fraction_system"] == "astm_uscs"
    assert row["fines_content"] == 4.0


# --- passing_at ----------------------------------------------------------------------


def test_passing_at_the_ends():
    sizes, passing = np.array([0.075, 0.3]), np.array([0.0, 90.0])
    assert passing_at(sizes, passing, 0) == 0.0
    assert passing_at(sizes, passing, None) == 100.0
    assert passing_at(sizes, passing, 0.01) == 0.0  # finest point passes 0 %
    assert np.isnan(passing_at(sizes, passing, 1.0))  # coarsest passes 90 %
    assert passing_at(sizes, passing, 0.3) == 90.0


# --- Built-in systems ----------------------------------------------------------------

#: The boundaries of §3.5, typed again here so a typo in the config (0.475 for
#: 0.425, 20 for 19) fails.
BOUNDARIES = {
    "astm_uscs": [0, 0.075, 4.75, 75, 300],
    "aashto": [0, 0.075, 0.425, 2.0, 75],
    "iso14688": [0, 0.002, 0.063, 2.0, 63, 200],
}
PARTS = {
    ("astm_uscs", "sand"): [0.425, 2.0, 4.75],
    ("astm_uscs", "gravel"): [19, 75],
    ("iso14688", "silt"): [0.0063, 0.02, 0.063],
    ("iso14688", "sand"): [0.2, 0.63, 2.0],
    ("iso14688", "gravel"): [6.3, 20, 63],
}


@pytest.mark.parametrize("name", list(BOUNDARIES))
def test_builtin_boundaries(name):
    system = builtin_systems()[name]
    check_system(name, system)
    assert system["source"]
    assert [fraction["lower"] for fraction in system["fractions"]] == BOUNDARIES[name]
    for fraction in system["fractions"]:
        parts = PARTS.get((name, fraction["name"]))
        if parts:
            assert [part["upper"] for part in fraction["parts"]] == parts
        else:
            assert not fraction.get("parts")


# --- A system of your own ----------------------------------------------------------

MINE = {
    "name": "two_bands",
    "fractions": [
        {"name": "fines", "lower": 0, "upper": 0.3},
        {"name": "coarse_material", "lower": 0.3, "upper": None},
    ],
}


def test_own_system_from_a_dict():
    got, system = fractions(MINE)
    assert system == "two_bands"
    assert got == {"fines": 30.0, "coarse_material": 70.0}


def test_own_system_from_a_file(tmp_path):
    path = tmp_path / "bands.yaml"
    path.write_text(yaml.safe_dump(MINE), encoding="utf-8")
    got, system = fractions(path)
    assert system == "two_bands"
    assert got["fines"] == 30.0


def _with(*changes):
    fractions_ = [dict(fraction) for fraction in MINE["fractions"]]
    for position, key, value in changes:
        fractions_[position][key] = value
    return {"name": "mine", "fractions": fractions_}


@pytest.mark.parametrize(
    ("system", "message"),
    [
        (_with((1, "lower", 0.2)), "'coarse_material' starts at 0.2 mm.*overlap"),
        (_with((1, "lower", 0.4)), "'coarse_material' starts at 0.4 mm.*gaps"),
        (
            _with((0, "lower", 0.001)),
            "'fines' starts at 0.001 mm.*start at 0",
        ),
        (_with((1, "upper", 10)), "must be open"),
        (_with((1, "name", "fines")), "'fines' is listed twice"),
        (_with((1, "name", "Coarse")), "lowercase words"),
        ({"name": "mine"}, "list of fractions"),
    ],
)
def test_malformed_systems_are_errors(system, message):
    with pytest.raises(HangtuError, match=message):
        fractions(system)


def test_name_clash_with_the_registry_is_an_error():
    # water_content is already the registry's water content.
    with pytest.raises(HangtuError, match="'water' would make the column"):
        fractions(_with((1, "name", "water")))
    # The built-in fraction names are allowed in a system of your own.
    got, _ = fractions(_with((1, "name", "gravel")))
    assert got["gravel"] == 70.0


def test_own_system_needs_a_name_other_than_a_builtin():
    with pytest.raises(HangtuError, match="needs a 'name'"):
        fractions({"fractions": MINE["fractions"]})
    with pytest.raises(HangtuError, match="'aashto' is a built-in fraction system"):
        fractions({**MINE, "name": "aashto"})


def test_unknown_system_lists_the_builtins():
    with pytest.raises(HangtuError, match="'astm_uscs', 'aashto', 'iso14688'"):
        fractions("uscs")
