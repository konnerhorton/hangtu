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

from .test_select_fitted import FITTED, g3_fit

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
            "no selection; derived values aren't built yet"
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
            selection=selection,
            geology_map=_map(Sand="coarse"),
            critical_state_friction_angle=32,
        )
    # G3: ψ = (38 - 32) / 0.8 = 7.5 deg.
    assert result.to_frame()[PSI].iloc[0] == pytest.approx(7.5, abs=1e-12)
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
            selection=selection,
            geology_map=_map(Sand="coarse"),
            critical_state_friction_angle=32,
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
    kwargs.setdefault("critical_state_friction_angle", 32)
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


def test_no_class_for_the_rule_is_an_error_saying_pass_geology_map():
    with pytest.raises(
        HangtuError,
        match=r"ψ's rule reads 'Sand''s soil_class, coarse or fine, and no "
        r"geology map was given and the sources carry none\. Pass geology_map=",
    ):
        ht.stats.mohr_coulomb_set(_phi_frame(), selection=SAND_SELECTION)


def test_no_class_is_needed_when_psi_is_selected():
    selection = {**SAND_SELECTION, PSI: {"Sand": _value("2 deg")}}
    with pytest.warns(UserWarning, match=PAIR):
        result = ht.stats.mohr_coulomb_set(_phi_frame(), selection=selection)
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
    assert "  Terrace        162      35.3     4.11" in text
    assert "c′ (psf)  φ′ (deg)  ψ (deg)" in text
    assert "  Every unit, E′ and ν′: no value, no selection; derived values" in text
    assert as_dict["model"] == "Mohr-Coulomb"
    assert as_dict["parameters"] == [C, PHI, PSI, E, NU]


# --- ψ (decision 13; G1-G6, AC 1-7) ---------------------------------------------------


def test_g1_terrace_psi_by_boltons_relation(example):
    _, correlations, triaxial, converted = example
    result = _quiet(ht.stats.mohr_coulomb_set, correlations, triaxial, converted)
    frame = result.to_frame().set_index("geology_unit")
    phi = frame.loc["Terrace", PHI]
    # ψ = (35.2902 - 32) / 0.8 = 4.1128 deg.
    assert frame.loc["Terrace", PSI] == pytest.approx(4.1128, abs=0.0005)
    assert frame.loc["Terrace", PSI] == pytest.approx((phi - 32) / 0.8, rel=1e-12)
    assert frame.attrs["units"][PSI] == "deg"
    terrace = _by_parameter(result, "Terrace")[PSI]
    assert terrace["origin"] == "rule"
    assert terrace["rule"]["citation"] == (
        "Kulhawy & Mayne (1990), Eq. 4-16, p. 4-20, after Bolton (1986)"
    )
    phi_input, critical_input = terrace["rule"]["inputs"]
    assert phi_input["value"] == phi
    assert phi_input["parameter_source"] == "Mohr-Coulomb fit (CDM, CD)"
    assert phi_input["selection_method"] == "fitted"
    assert critical_input["value"] == 32
    assert critical_input["source"] == "judgments.yaml"
    recorded = result.judgments["critical_state_friction_angle"]
    assert recorded["values"] == {
        "Terrace": {
            "critical_state_friction_angle": "32 deg",
            "reason": (
                "assumed for subangular quartz sand with gravel; no ring shear or "
                "angle of repose test yet"
            ),
        }
    }
    assert recorded["sha256"]
    # The Alluvium is designed undrained: φ′ none, so ψ is blank, not 0.
    alluvium = _by_parameter(result, "Alluvium")[PSI]
    assert alluvium["origin"] == "blank"
    assert alluvium["no_value_reason"] == "no φ′ selected"
    provenance = result.provenance().set_index(["geology_unit", "parameter"])
    assert provenance.loc[("Terrace", PSI), "reason"] == (
        "φ′ 35.3 deg (selected), φ′cv 32 deg (judgment)"
    )
    assert provenance.loc[("Terrace", PSI), "rule_name"] == (
        "Bolton's relation, ψ = (φ′ - φ′cv) / 0.8"
    )


def test_g2_the_floor():
    selection = {C: {"Sand": FITTED}, PHI: {"Sand": FITTED}}
    result = _quiet(
        ht.stats.mohr_coulomb_set,
        g3_fit(),
        selection=selection,
        geology_map=_map(Sand="coarse"),
        critical_state_friction_angle=32,
    )
    assert result.to_frame()[PSI].iloc[0] == 0
    assert (
        "Sand, ψ: φ′ 30.0 deg is below φ′cv 32.0 deg, so ψ is 0 (the relation "
        "gives -2.5 deg)."
    ) in result.notes


def _sand_set(phi, **kwargs):
    """``Sand`` (coarse) with c′ 0 kPa and φ′ as values; φ′cv 32 by default."""
    selection = {C: {"Sand": _value("0 kPa")}, PHI: {"Sand": _value(f"{phi} deg")}}
    selection |= kwargs.pop("selection", {})
    kwargs.setdefault("critical_state_friction_angle", 32)
    return ht.stats.mohr_coulomb_set(
        selection=selection, geology_map=_map(Sand="coarse"), **kwargs
    )


def _sand(phi, **kwargs):
    """As ``_sand_set()``, expecting the pair warning (two values, no one fit)."""
    with pytest.warns(UserWarning, match=PAIR):
        return _sand_set(phi, **kwargs)


def test_g4_at_the_limit():
    # 44 - 32 = 12 deg, the limit itself: 12 / 0.8 = 15.0 deg.
    assert _sand(44).to_frame()[PSI].iloc[0] == pytest.approx(15.0, abs=1e-12)


def test_g4_beyond_the_limit_is_blank_never_clipped():
    with pytest.warns(UserWarning, match=r"φ′ - φ′cv is above 12 deg in 'Sand'"):
        result = _sand(45)
    assert np.isnan(result.to_frame()[PSI].iloc[0])
    record = _by_parameter(result, "Sand")[PSI]
    assert record["origin"] == "rule"
    assert record["no_value_reason"] == (
        "φ′ - φ′cv = 13.0 deg, above the 12 deg of I_R = 4 (Kulhawy & Mayne 1990, "
        "p. 4-10); give ψ as a value selection"
    )


def test_g5_fine():
    selection = {C: {"Clay": _value("5 kPa")}, PHI: {"Clay": _value("26 deg")}}
    with pytest.warns(UserWarning, match=r"c′ and φ′ of 'Clay'"):
        result = ht.stats.mohr_coulomb_set(
            selection=selection, geology_map=_map(Clay="fine")
        )
    assert result.to_frame()[PSI].iloc[0] == 0
    record = _by_parameter(result, "Clay")[PSI]
    assert record["origin"] == "rule"
    assert record["rule"]["citation"] == "Vermeer & de Borst (1984), p. 13"
    assert any("Obrzud & Truty 2018, p. 107" in note for note in result.notes)
    assert "critical_state_friction_angle" not in result.judgments


def test_g6_psi_selected():
    given = {"method": "value", "value": "2 deg", "reason": "a loose sand"}
    result = _sand(38, selection={PSI: {"Sand": given}})
    assert result.to_frame()[PSI].iloc[0] == 2
    record = _by_parameter(result, "Sand")[PSI]
    assert record["origin"] == "selection"
    assert record["selection"]["selection_reason"] == "a loose sand"
    assert "critical_state_friction_angle" not in result.judgments
    assert set(result.selections) == {C, PHI, PSI}


@pytest.mark.parametrize("soil_class", ["fill", "rock", "organic", "silty"])
def test_a_class_the_rule_cant_read_is_an_error(soil_class):
    selection = {C: {"Unit": _value("0 kPa")}, PHI: {"Unit": _value("30 deg")}}
    match = rf"'Unit' has soil_class '{soil_class}'.*give ψ as a selection"
    if soil_class == "rock":
        match += r".*generalized Hoek-Brown set \(planned, not built yet\)"
    if soil_class == "silty":
        match = r"'Unit' has soil_class 'silty', a class hangtu doesn't know"
    with pytest.raises(HangtuError, match=match):
        ht.stats.mohr_coulomb_set(
            selection=selection, geology_map=_map(Unit=soil_class)
        )


def test_a_blank_class_is_an_error():
    selection = {C: {"Unit": _value("0 kPa")}, PHI: {"Unit": _value("30 deg")}}
    with pytest.raises(HangtuError, match=r"'Unit''s soil_class.*geology_map= gives"):
        ht.stats.mohr_coulomb_set(selection=selection, geology_map=_map(Unit=None))


@pytest.mark.parametrize("soil_class", ["fill", "rock", None])
def test_no_phi_gives_a_blank_psi_and_no_error(soil_class):
    none = {"method": "none", "reason": "not used"}
    result = _quiet(
        ht.stats.mohr_coulomb_set,
        selection={C: {"Unit": none}, PHI: {"Unit": none}},
        geology_map=_map(Unit=soil_class),
    )
    assert _by_parameter(result, "Unit")[PSI]["no_value_reason"] == "no φ′ selected"


def test_a_coarse_unit_without_phi_cv_is_an_error():
    with pytest.raises(
        HangtuError,
        match=r"Bolton's relation needs critical_state_friction_angle, φ′cv, for "
        r"'Sand': no judgments file was given",
    ):
        _sand_set(38, critical_state_friction_angle=None)


def test_a_file_without_phi_cv_for_the_unit_is_an_error(tmp_path):
    path = tmp_path / "judgments.yaml"
    path.write_text(
        "critical_state_friction_angle:\n"
        "  by: geology_unit\n"
        "  units: {critical_state_friction_angle: deg}\n"
        "  values:\n"
        "    Gravel: {critical_state_friction_angle: 34, reason: x}\n",
        encoding="utf-8",
    )
    missing = r"has no critical_state_friction_angle.*'Sand'"
    with pytest.raises(HangtuError, match=missing):
        _sand_set(38, critical_state_friction_angle=None, judgments=path)


def test_an_argument_overrides_the_file(tmp_path):
    path = tmp_path / "judgments.yaml"
    path.write_text(
        "critical_state_friction_angle:\n"
        "  by: geology_unit\n"
        "  units: {critical_state_friction_angle: deg}\n"
        "  values:\n"
        "    Sand: {critical_state_friction_angle: 30, reason: x}\n",
        encoding="utf-8",
    )
    from_file = _sand(38, critical_state_friction_angle=None, judgments=path)
    assert from_file.to_frame()[PSI].iloc[0] == pytest.approx(10.0, abs=1e-12)
    with pytest.warns(UserWarning, match=r"critical_state_friction_angle= replaces"):
        argued = _sand(38, critical_state_friction_angle={"Sand": 34}, judgments=path)
    assert argued.to_frame()[PSI].iloc[0] == pytest.approx(5.0, abs=1e-12)
    assert argued.judgments["critical_state_friction_angle"]["source"] == "argument"


def test_one_number_for_two_coarse_units_is_an_error():
    selection = {
        C: {"Sand": _value("0 kPa"), "Gravel": _value("0 kPa")},
        PHI: {"Sand": _value("36 deg"), "Gravel": _value("38 deg")},
    }
    with pytest.raises(HangtuError, match=r"is one number.*for 2 units"):
        ht.stats.mohr_coulomb_set(
            selection=selection,
            geology_map=_map(Sand="coarse", Gravel="coarse"),
            critical_state_friction_angle=32,
        )


def test_views_agree_with_psi_by_rule(example):
    _, correlations, triaxial, converted = example
    result = _quiet(ht.stats.mohr_coulomb_set, correlations, triaxial, converted)
    psi = result.to_frame().set_index("geology_unit").loc["Terrace", PSI]
    provenance = result.provenance().set_index(["geology_unit", "parameter"])
    assert provenance.loc[("Terrace", PSI), "value"] == psi
    assert provenance.loc[("Terrace", PSI), "parameter_origin"] == "rule"
    records = {
        (r["geology_unit"], r["parameter"]): r for r in result.to_dict()["records"]
    }
    assert records[("Terrace", PSI)]["value"] == psi
    text = str(result)
    assert "  Terrace        162      35.3     4.11" in text
    assert (
        "  Terrace, ψ: Bolton's relation, ψ = (φ′ - φ′cv) / 0.8 (Kulhawy & Mayne "
        "(1990), Eq. 4-16, p. 4-20, after Bolton (1986)): φ′ 35.3 deg (selected), "
        "φ′cv 32 deg (judgment)"
    ) in text
