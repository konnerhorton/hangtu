"""ht.stats.mohr_coulomb_set() (docs/work/m18f-mohr-coulomb-set.md, decisions 9-19).

G1 is the example site's Terrace: its c′ and φ′ are select()'s for the same
sources and file (one calculation, many views). The other sets are given as
value selections, with no sources, so each value is the hand value.
"""

import json
import warnings

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError

C = "effective_cohesion"
PHI = "effective_friction_angle"
PSI = "dilatancy_angle"
E = "drained_youngs_modulus"
NU = "drained_poissons_ratio"
PAIR = r"c′ and φ′ of 'Sand' don't both come fitted from the same source"


def _value(value, reason="from the design report"):
    return {"method": "value", "value": value, "reason": reason}


def _map(**classes):
    """A geology map giving each unit its class."""
    return pd.DataFrame(
        {
            "code": list(classes),
            "geology_unit": list(classes),
            "soil_class": list(classes.values()),
            "order": range(1, len(classes) + 1),
            "color": None,
        }
    )


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


def _by_parameter(result, unit):
    return {r["parameter"]: r for r in result.records if r["geology_unit"] == unit}


# --- G1: the example site (AC 1, first half) ------------------------------------------


def example_sources(folder):
    """The selection guide's Terrace sources (docs/site/examples/selection.py)."""
    p = ht.Project.from_ags(ht.examples.path("site.ags"), db=folder / "site.sqlite")
    p.set_geology_map(ht.examples.path("strata.csv"))
    p.set_judgments(ht.examples.path("judgments.yaml"))
    holes = ["B-1", "B-2", "B-3", "B-5", "B-6"]
    spt = ht.analysis.vertical_stress(p.spt(holes=holes), stratigraphy=p.stratigraphy())
    spt = ht.analysis.spt_n1_60(spt, method="liao_whitman_1986")
    sand = spt[(spt["geology_unit"] == "Terrace") & (spt["spt_n60"] <= 40)]
    correlations = pd.concat(
        [
            ht.analysis.correlations.effective_friction_angle_hatanaka_uchida_1996(
                sand
            ),
            ht.analysis.correlations.effective_friction_angle_kulhawy_mayne_1990(sand),
        ],
        ignore_index=True,
    )
    triaxial = ht.analysis.mohr_coulomb_fit(
        p.triaxial(geology=["Terrace"]), group_by="geology_unit"
    )
    shear_box = ht.analysis.shear_box_fit(
        p.shear_box(geology=["Terrace"]), group_by="geology_unit"
    )
    converted = ht.analysis.friction_angle_from_shear_box(
        shear_box, soil="cohesionless"
    )
    return p, correlations, triaxial, converted


@pytest.fixture(scope="module")
def example(tmp_path_factory):
    """The selection guide's sources: SPT correlations, triaxial, converted."""
    return _quiet(example_sources, tmp_path_factory.mktemp("example"))


def test_g1_c_and_phi_equal_selects(example):
    _, correlations, triaxial, converted = example
    result = _quiet(ht.stats.mohr_coulomb_set, correlations, triaxial, converted)
    friction = ht.stats.select(
        correlations, triaxial, converted, value="effective_friction_angle"
    )
    cohesion = ht.stats.select(triaxial, value="effective_cohesion")
    frame = result.to_frame().set_index("geology_unit")
    assert frame.loc["Terrace", C] == cohesion.to_frame()["value"].iloc[0]
    assert frame.loc["Terrace", PHI] == friction.to_frame()["value"].iloc[0]
    assert frame.loc["Terrace", C] == pytest.approx(161.811, abs=0.001)
    assert frame.loc["Terrace", PHI] == pytest.approx(35.2902, abs=0.0001)
    assert frame.attrs["units"][C] == "psf"
    assert frame.attrs["units"][PHI] == "deg"
    assert result.geology_units == ("Terrace", "Alluvium")
    terrace = _by_parameter(result, "Terrace")
    for parameter in (E, NU):
        assert terrace[parameter]["origin"] == "blank"
        assert terrace[parameter]["no_value_reason"] == (
            "no selection; derived values come with wave 5 (M23)"
        )
    assert result.selections[PHI].to_frame().equals(friction.to_frame())
    assert result.soil_classes == {"Terrace": "coarse", "Alluvium": "fine"}
    assert result.judgments["soil_class"]["source"] == "the sources"


def test_the_example_routes_c_to_the_triaxial_fit_only(example):
    _, correlations, triaxial, converted = example
    result = _quiet(ht.stats.mohr_coulomb_set, correlations, triaxial, converted)
    assert len(result.selections[C].comparison.sources) == 1
    assert len(result.selections[PHI].comparison.sources) == 4


# --- The pair (decisions 11 and 12; AC 3 warning half, AC 10 first half) --------------


def test_g3_a_value_pair_warns_and_notes():
    selection = {C: {"Sand": _value("0 kPa")}, PHI: {"Sand": _value("38 deg")}}
    with pytest.warns(UserWarning, match=PAIR):
        result = ht.stats.mohr_coulomb_set(
            selection=selection, geology_map=_map(Sand="coarse")
        )
    assert (
        "Sand: c′ (value) and φ′ (value) don't come from one fit, so they aren't "
        "one envelope's pair."
    ) in result.notes
    assert "one envelope's pair" in str(result)


def test_both_none_isnt_warned():
    none = {"method": "none", "reason": "designed undrained"}
    result = _quiet(
        ht.stats.mohr_coulomb_set,
        selection={C: {"Clay": none}, PHI: {"Clay": none}},
        geology_map=_map(Clay="fine"),
    )
    assert np.isnan(result.to_frame()[PHI].iloc[0])
    assert result.notes == ()


@pytest.mark.parametrize(("listed", "missing"), [(C, PHI), (PHI, C)])
def test_a_unit_with_one_of_the_pair_is_an_error(listed, missing):
    def given(parameter, unit):
        return _value({C: "5 kPa", PHI: "26 deg"}[parameter], unit)

    selection = {
        listed: {"Clay": given(listed, "x"), "Sand": given(listed, "y")},
        missing: {"Clay": given(missing, "z")},
    }
    with pytest.raises(
        HangtuError,
        match=rf"'Sand' has a selection of '{listed}' and not of '{missing}'.*value: 0",
    ):
        ht.stats.mohr_coulomb_set(selection=selection)


def test_c_and_phi_are_required():
    with pytest.raises(HangtuError, match=r"has no selection of 'effective_cohesion'"):
        ht.stats.mohr_coulomb_set(selection={PHI: {"Sand": _value("38 deg")}})


# --- E′ and ν′ (decision 14) ----------------------------------------------------------


def test_e_and_nu_from_a_selection():
    selection = {
        C: {"Sand": _value("0 kPa")},
        PHI: {"Sand": _value("38 deg")},
        E: {"Sand": _value("40 MPa", "from the pressuremeter report")},
        NU: {"Sand": _value(0.3, "typical of a dense sand")},
    }
    with pytest.warns(UserWarning, match=PAIR):
        result = ht.stats.mohr_coulomb_set(
            selection=selection, geology_map=_map(Sand="coarse")
        )
    frame = result.to_frame()
    assert frame[E].iloc[0] == 40
    assert frame[NU].iloc[0] == 0.3
    assert frame.attrs["units"][E] == "MPa"
    records = _by_parameter(result, "Sand")
    assert records[E]["origin"] == "selection"
    assert records[NU]["selection"]["selection_reason"] == "typical of a dense sand"
    assert set(result.selections) == {C, PHI, E, NU}


# --- soil_class (decision 19, AC 8) ---------------------------------------------------


def _phi_frame(classes=None):
    frame = pd.DataFrame(
        {
            "geology_unit": ["Sand"] * 3,
            "depth": [1.0, 2.0, 3.0],
            "correlation_name": "A",
            PHI: [36.0, 37.0, 38.0],
        }
    )
    frame = ht.set_units(frame, {PHI: "deg", "depth": "m"})
    if classes is not None:
        frame.attrs["soil_classes"] = classes
    return frame


SAND_SELECTION = {
    C: {"Sand": _value("0 kPa")},
    PHI: {
        "Sand": {
            "source": "A",
            "method": "characteristic",
            "estimate": "mean",
            "side": "low",
            "distribution": "normal",
            "reason": "x",
        }
    },
}


def _set(*sources, **kwargs):
    with pytest.warns(UserWarning, match=PAIR):
        return ht.stats.mohr_coulomb_set(*sources, selection=SAND_SELECTION, **kwargs)


def test_soil_classes_from_the_sources():
    result = _set(_phi_frame({"Sand": "coarse", "Clay": "fine"}))
    assert result.soil_classes == {"Sand": "coarse"}
    assert result.judgments["soil_class"] == {
        "source": "the sources",
        "values": {"Sand": "coarse"},
    }


def test_soil_classes_from_geology_map_as_a_path(tmp_path):
    path = tmp_path / "strata.csv"
    _map(Sand="coarse").to_csv(path, index=False)
    result = _set(_phi_frame(), geology_map=path)
    assert result.soil_classes == {"Sand": "coarse"}
    assert result.judgments["soil_class"]["source"] == "geology_map="


def test_no_classes_anywhere_records_none():
    result = _set(_phi_frame())
    assert result.soil_classes == {}
    assert "soil_class" not in result.judgments


def test_sources_that_disagree_are_an_error():
    with pytest.raises(
        HangtuError, match=r"source 1 carries 'Sand' as 'coarse' and source 2 as 'fill'"
    ):
        ht.stats.mohr_coulomb_set(
            _phi_frame({"Sand": "coarse"}),
            _phi_frame({"Sand": "fill"}).assign(correlation_name="B"),
            selection=SAND_SELECTION,
        )


def test_an_argument_that_differs_warns_and_is_used():
    differ = r"geology_map= gives soil classes that differ"
    with pytest.warns(UserWarning, match=differ):
        result = _set(_phi_frame({"Sand": "fill"}), geology_map=_map(Sand="coarse"))
    assert result.soil_classes == {"Sand": "coarse"}


def test_a_projects_datasets_and_fit_carry_the_classes(example):
    _, correlations, triaxial, converted = example
    expected = {
        "Fill": "fill",
        "Alluvium": "fine",
        "Terrace": "coarse",
        "Sandstone": "rock",
    }
    assert correlations.attrs["soil_classes"] == expected
    assert triaxial.soil_classes == expected
    assert converted.soil_classes == expected


# --- The views (AC 12, the set's part) ------------------------------------------------


def test_views_agree(example):
    _, correlations, triaxial, converted = example
    result = _quiet(ht.stats.mohr_coulomb_set, correlations, triaxial, converted)
    frame = result.to_frame()
    provenance = result.provenance().set_index(["geology_unit", "parameter"])
    as_dict = result.to_dict()
    json.dumps(as_dict)
    records = {(r["geology_unit"], r["parameter"]): r for r in as_dict["records"]}
    for _, row in frame.iterrows():
        for parameter in (C, PHI):
            value = row[parameter]
            given = provenance.loc[(row["geology_unit"], parameter), "value"]
            recorded = records[(row["geology_unit"], parameter)]["value"]
            if np.isnan(value):
                assert np.isnan(given) and recorded is None
            else:
                assert given == value == recorded
    text = str(result)
    assert text.splitlines()[0] == (
        "Mohr-Coulomb set (Vermeer & de Borst (1984), Heron 29(3), p. 3), "
        "by geology_unit"
    )
    assert "  Terrace        162      35.3" in text
    assert "c′ (psf)  φ′ (deg)  ψ (deg)" in text
    assert "  Every unit, E′ and ν′: no value, no selection; derived values" in text
    assert as_dict["model"] == "Mohr-Coulomb"
    assert as_dict["parameters"] == [C, PHI, PSI, E, NU]
