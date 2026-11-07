"""The model-set base (docs/work/m18f-mohr-coulomb-set.md, decisions 5-8).

A two-parameter set built here on the base: φ′ required and c′ optional, so
the base is tested apart from any model (AC 9, AC 10 second half, AC 12).
"""

import json
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError
from hangtu.stats import _model_set
from hangtu.stats._model_set import _ModelSet

from .test_select_fitted import G1, PHI, phi, sources

C = "effective_cohesion"
G1_VALUE = 34.868
GIVEN = {"method": "value", "value": "25 deg", "reason": "cautious"}


@dataclass(frozen=True, repr=False)
class PairSet(_ModelSet):
    """A test-only set: φ′ required, c′ optional."""


def pair_set(*sources, selection=None, judgments=None, display_units=None):
    parameters = {PHI: True, C: False}
    selections, _ = _model_set.read_selections(
        "pair_set()",
        sources,
        parameters,
        selection=selection,
        include_assumed=False,
        judgments=judgments,
        units=None,
        display_units=display_units,
    )
    units = _model_set.unit_order(selections)
    records = [
        _model_set.from_selection(selections[p], u, p)
        if _model_set.selected(selections, p, u)
        else _model_set.blank(u, p, "no selection")
        for u in units
        for p in parameters
    ]
    return PairSet.create(
        function="pair_set",
        model="Pair",
        model_citation="a test",
        parameters=list(parameters),
        records=records,
        selections=selections,
        geology_units=units,
        judgments=_model_set.merged_judgments(selections),
        display_units=display_units,
    )


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


def two_units():
    a, b = sources()
    clay = phi("A", [24.0, 25.0, 27.0, 28.0]).assign(geology_unit="Clay")
    a = ht.set_units(pd.concat([a, clay], ignore_index=True), a.attrs["units"])
    return a, b


# --- AC 9: constants only -------------------------------------------------------------


def test_a_trend_is_an_error_naming_the_unit_and_parameter():
    a, b = sources()
    entry = {**G1, "trend": "depth"}
    with pytest.raises(
        HangtuError,
        match=r"selection of 'effective_friction_angle' in 'Sand' is a line with "
        r"depth.*select\(\) still gives the line",
    ):
        pair_set(a, b, selection={PHI: {"Sand": entry}})


# --- AC 10, second half: routing ------------------------------------------------------


def test_a_source_that_carries_no_parameter_is_an_error():
    a, b = sources()
    other = pd.DataFrame({"geology_unit": ["Sand"], "water_content": [20.0]})
    with pytest.raises(
        HangtuError,
        match=r"source 3 \(a DataFrame\) gives none of the set's parameters, "
        r"effective_friction_angle, effective_cohesion",
    ):
        pair_set(a, b, other, selection={PHI: {"Sand": G1}})


def test_a_shear_box_fit_is_told_to_convert():
    a, _ = sources()
    df = pd.DataFrame(
        {
            "geology_unit": "Sand",
            "applied_normal_stress": [50.0, 100.0, 200.0],
            "peak_shear_stress": [30.0, 60.0, 115.0],
        }
    )
    df.attrs["units"] = {"applied_normal_stress": "kPa", "peak_shear_stress": "kPa"}
    box = ht.analysis.shear_box_fit(df, group_by="geology_unit")
    with pytest.raises(HangtuError, match=r"ShearBoxFit\) gives none.*convert it"):
        pair_set(a, box, selection={PHI: {"Sand": G1}})


def test_each_parameter_gets_only_its_sources():
    # A frame with c′ and not φ′: φ′'s select() would refuse it.
    a, b = sources()
    cohesion = pd.DataFrame(
        {"geology_unit": ["Sand"] * 3, "depth": [1.0, 2.0, 3.0], C: [2.0, 3.0, 4.0]}
    )
    cohesion = ht.set_units(cohesion, {C: "kPa", "depth": "m"})
    given_c = {"method": "value", "value": "0 kPa", "reason": "cohesionless"}
    result = _quiet(
        pair_set, a, b, cohesion, selection={PHI: {"Sand": G1}, C: {"Sand": given_c}}
    )
    labels = [s["parameter_source"] for s in result.selections[C].comparison.sources]
    assert len(labels) == 1
    assert len(result.selections[PHI].comparison.sources) == 2
    assert result.to_frame()[C].iloc[0] == 0


def test_an_optional_parameter_with_no_selection_is_blank():
    a, b = sources()
    result = _quiet(pair_set, a, b, selection={PHI: {"Sand": G1}})
    assert set(result.selections) == {PHI}
    (record,) = [r for r in result.records if r["parameter"] == C]
    assert record["origin"] == "blank"
    assert record["no_value_reason"] == "no selection"


def test_a_selection_of_another_parameter_is_an_error():
    a, b = sources()
    with pytest.raises(HangtuError, match=r"'undrained_shear_strength'.*isn't a param"):
        pair_set(a, b, selection={"undrained_shear_strength": {}})


# --- Unit order (decision 8) ----------------------------------------------------------


def test_units_in_the_comparisons_order_then_value_only_ones():
    a, b = two_units()
    selection = {
        PHI: {"Clay": GIVEN, "Sand": G1, "Gravel": {**GIVEN, "value": "38 deg"}},
        C: {"Rock": {"method": "value", "value": "50 kPa", "reason": "x"}},
    }
    result = _quiet(pair_set, a, b, selection=selection)
    # The comparison sorts plain text units; a Project's are the map's order.
    assert result.geology_units == ("Clay", "Sand", "Gravel", "Rock")


# --- AC 12, the base part: the views agree --------------------------------------------


def test_views_agree_on_a_projects_categorical_geology_unit():
    a, b = two_units()
    for frame in (a, b):
        frame["geology_unit"] = pd.Categorical(
            frame["geology_unit"], categories=["Fill", "Clay", "Sand"]
        )
    given_c = {"method": "value", "value": "5 kPa", "reason": "from the report"}
    selection = {PHI: {"Sand": G1, "Clay": GIVEN}, C: {"Clay": given_c}}
    result = _quiet(pair_set, a, b, selection=selection)
    frame = result.to_frame()
    assert frame["geology_unit"].tolist() == ["Clay", "Sand"]
    assert frame.attrs["units"] == {PHI: "deg", C: "kPa"}
    sand = frame.set_index("geology_unit").loc["Sand"]
    assert sand[PHI] == pytest.approx(G1_VALUE, abs=0.001)
    assert np.isnan(sand[C])

    provenance = result.provenance()
    assert len(provenance) == 4
    row = provenance.set_index(["geology_unit", "parameter"]).loc[("Sand", PHI)]
    assert row["value"] == sand[PHI]
    assert row["parameter_origin"] == "selection"
    assert row["selection_method"] == "characteristic"
    assert row["reason"] == G1["reason"]
    blank = provenance.set_index(["geology_unit", "parameter"]).loc[("Sand", C)]
    assert blank["parameter_origin"] == "blank"

    as_dict = result.to_dict()
    json.dumps(as_dict)
    assert as_dict["kind"] == "parameter"
    records = as_dict["records"]
    values = {(r["geology_unit"], r["parameter"]): r["value"] for r in records}
    assert values[("Sand", PHI)] == sand[PHI]
    assert values[("Sand", C)] is None
    assert as_dict["selections"][PHI] == result.selections[PHI].to_dict()

    text = str(result)
    assert text.splitlines()[0] == "Pair set (a test), by geology_unit"
    assert "φ′ (deg)" in text and "c′ (kPa)" in text
    assert "34.9" in text
    assert "Sand, c′: no value, no selection" in text
    assert result._repr_html_().startswith("<pre>")
    assert result.judgments["selection"][PHI]["source"] == "argument"


def test_a_selection_profile_is_drawn_from_the_set():
    a, b = sources()
    result = _quiet(pair_set, a, b, selection={PHI: {"Sand": G1}})
    with ht.settings.override(hints=False):
        fig, _ = result.selections[PHI].profile(geology_unit="Sand")
    assert fig is not None
