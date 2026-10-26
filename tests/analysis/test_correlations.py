"""ht.analysis.correlations (docs/work/m13b1-spt-framework.md, AC 2, 3, 5 and 6)."""

import inspect
import re

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu import _config
from hangtu.analysis import correlations

# AC 2, by hand: φ′ = (15.4 (N1)60)^0.5 + 20. (N1)60 by Liao & Whitman, then by Kayen.
HATANAKA_UCHIDA = [
    (28.284, 40.87),
    (10.000, 32.41),
    (21.213, 38.07),
    (8.500, 31.44),
    (25.882, 39.96),
    (20.625, 37.82),
    (7.586, 30.81),
]
# AC 2, by hand: φ′ = arctan{[N60 / (12.2 + 20.3 σ′v / 100)]^0.34}, σ′v in kPa.
KULHAWY_MAYNE = [
    (20, 50.0, 43.92),
    (10, 100.0, 33.82),
    (30, 200.0, 39.53),
    (5, 25.0, 33.27),
]
KPA_TO_PSF = 1000 / 47.880259
FUNCTIONS = {
    name: getattr(correlations, name)
    for name in (
        "effective_friction_angle_hatanaka_uchida_1996",
        "effective_friction_angle_kulhawy_mayne_1990",
        "undrained_shear_strength_stroud_1974",
        "undrained_shear_strength_terzaghi_peck_1967",
        "preconsolidation_stress_mayne_kemper_1988",
        "overconsolidation_ratio_mayne_kemper_1988",
        "at_rest_earth_pressure_coefficient_kulhawy_et_al_1989",
        "drained_youngs_modulus_aashto_2004",
        "drained_youngs_modulus_kulhawy_mayne_1990",
        "shear_wave_velocity_imai_tonouchi_1982",
        "shear_wave_velocity_ohta_goto_1978",
    )
}


def frame(**columns):
    return pd.DataFrame(columns)


def stresses(n60, stress, unit="kPa", **columns):
    df = frame(spt_n60=n60, effective_vertical_stress=stress, **columns)
    return ht.set_units(df, {"effective_vertical_stress": unit})


def test_hatanaka_uchida_golden_values():
    n1_60, expected = zip(*HATANAKA_UCHIDA, strict=True)
    out = correlations.effective_friction_angle_hatanaka_uchida_1996(
        frame(spt_n1_60=list(n1_60))
    )
    assert out["effective_friction_angle"].tolist() == pytest.approx(
        list(expected), abs=0.005
    )
    assert (
        out["correlation_name"] == "effective_friction_angle_hatanaka_uchida_1996"
    ).all()
    assert out["correlation_note"].isna().all()
    assert out.attrs["units"] == {"effective_friction_angle": "°"}


def test_hatanaka_uchida_range_ends_are_inside():
    out = correlations.effective_friction_angle_hatanaka_uchida_1996(
        frame(spt_n1_60=[4.55, 39.0])
    )
    assert out["effective_friction_angle"].notna().all()


def test_no_estimate_gives_nan_with_the_reason_and_one_warning():
    df = frame(
        spt_n1_60=[4.0, 40.0, np.nan, 20.0, 20.0, np.nan],
        spt_refusal=[False, False, False, True, False, True],
    )
    with pytest.warns(UserWarning) as caught:
        out = correlations.effective_friction_angle_hatanaka_uchida_1996(df)
    # A blank input comes before a refusal.
    assert out["correlation_note"].tolist() == [
        "below range",
        "above range",
        "input blank",
        "refusal",
        None,
        "input blank",
    ]
    assert out["effective_friction_angle"].isna().tolist() == [
        True, True, True, True, False, True,
    ]  # fmt: skip
    assert [str(w.message) for w in caught] == [
        "effective_friction_angle_hatanaka_uchida_1996 gave no estimate for 5 of 6 "
        "rows (2 input blank, 1 refusal, 1 below range, 1 above range; see "
        "'correlation_note'). Its range is 4.55 ≤ (N1)60 ≤ 39; outside it the "
        "estimate is blank, never extrapolated."
    ]


def test_no_row_is_dropped_or_reordered_and_the_input_is_unchanged():
    df = frame(loca_id=["B", "A", "C"], spt_n1_60=[10.0, 2.0, 20.0])
    df.index = [7, 3, 5]
    before = df.copy()
    with pytest.warns(UserWarning, match="1 below range"):
        out = correlations.effective_friction_angle_hatanaka_uchida_1996(df)
    assert out.index.tolist() == [7, 3, 5]
    assert out["loca_id"].tolist() == ["B", "A", "C"]
    pd.testing.assert_frame_equal(df, before)


def test_existing_output_columns_are_replaced_with_a_warning():
    df = frame(spt_n1_60=[10.0], effective_friction_angle=[30.0])
    with pytest.warns(UserWarning, match="Replaced the existing columns"):
        out = correlations.effective_friction_angle_hatanaka_uchida_1996(df)
    assert out["effective_friction_angle"][0] == pytest.approx(32.41, abs=0.005)


def test_kulhawy_mayne_golden_values():
    n60, stress, expected = zip(*KULHAWY_MAYNE, strict=True)
    out = correlations.effective_friction_angle_kulhawy_mayne_1990(
        stresses(list(n60), list(stress))
    )
    assert out["effective_friction_angle"].tolist() == pytest.approx(
        list(expected), abs=0.005
    )
    assert (
        out["correlation_name"] == "effective_friction_angle_kulhawy_mayne_1990"
    ).all()


def test_kulhawy_mayne_in_psf_gives_the_same_angle():
    n60, stress, expected = zip(*KULHAWY_MAYNE, strict=True)
    psf = [value * KPA_TO_PSF for value in stress]
    out = correlations.effective_friction_angle_kulhawy_mayne_1990(
        stresses(list(n60), psf, unit="psf")
    )
    assert out["effective_friction_angle"].tolist() == pytest.approx(
        list(expected), abs=0.005
    )


def test_kulhawy_mayne_out_of_range():
    df = stresses(
        [60, 61, 20, 20, 20, np.nan, 20],
        [300.0, 100.0, 301.0, 0.0, np.nan, 100.0, 100.0],
        spt_refusal=[False] * 6 + [True],
    )
    with pytest.warns(UserWarning) as caught:
        out = correlations.effective_friction_angle_kulhawy_mayne_1990(df)
    assert out["correlation_note"].tolist() == [
        None,
        "above range",
        "above range",
        "below range",
        "input blank",
        "input blank",
        "refusal",
    ]
    assert out["effective_friction_angle"].notna().tolist() == [True] + [False] * 6
    assert str(caught[0].message).endswith(
        "Its range is N60 ≤ 60; 0 < σ′v ≤ 300 kPa; outside it the estimate is "
        "blank, never extrapolated."
    )


def test_kulhawy_mayne_needs_the_stress_units():
    df = frame(spt_n60=[10.0], effective_vertical_stress=[100.0])
    with pytest.raises(ht.UnitsError, match="'effective_vertical_stress' has no units"):
        correlations.effective_friction_angle_kulhawy_mayne_1990(df)


def test_kulhawy_mayne_without_n60_names_what_adds_it():
    df = ht.set_units(
        frame(spt_n1_60=[10.0], effective_vertical_stress=[100.0]),
        {"effective_vertical_stress": "kPa"},
    )
    with pytest.raises(
        ht.ColumnError, match=r"'spt_n60' not found.*ht\.analysis\.spt\(\)"
    ):
        correlations.effective_friction_angle_kulhawy_mayne_1990(df)


# --- AC 7: comparison on a profile ----------------------------------------------------


def test_both_concatenate_and_draw_on_a_profile():
    df = ht.set_units(
        frame(
            loca_id=["B-1"] * 4,
            ground_level=[50.0] * 4,
            depth=[2.0, 4.0, 6.0, 8.0],
            spt_n60=[10.0, 20.0, 30.0, 70.0],
            effective_vertical_stress=[30.0, 60.0, 90.0, 120.0],
            spt_refusal=[False, False, True, False],
        ),
        {"depth": "m", "ground_level": "m", "effective_vertical_stress": "kPa"},
    )
    # (N1)60 = 17.0, 25.8, 31.6 and 63.9: the last above H&U's 39; N60 70 above
    # K&M's 60. The test at 6 m is a refusal.
    df = ht.analysis.spt_n1_60(df, method="liao_whitman_1986")
    with pytest.warns(UserWarning, match="gave no estimate") as caught:
        est = pd.concat(
            [
                correlations.effective_friction_angle_hatanaka_uchida_1996(df),
                correlations.effective_friction_angle_kulhawy_mayne_1990(df),
            ],
            ignore_index=True,
        )
    assert ["1 refusal, 1 above range" in str(w.message) for w in caught] == [True] * 2
    assert est.attrs["units"]["depth"] == "m"
    _, ax = ht.plot.profile(
        est, value="effective_friction_angle", vs="depth", color_by="correlation_name"
    )
    legend = [text.get_text() for text in ax.get_legend().get_texts()]
    assert legend == [
        "effective_friction_angle_hatanaka_uchida_1996",
        "effective_friction_angle_kulhawy_mayne_1990",
    ]
    # The refusal and the out-of-range row of each, counted by correlation_note.
    assert ax.ags_notes == {"correlation_refusal": 2, "correlation_above_range": 2}
    footnote = [text.get_text() for text in ax.texts if "estimate" in text.get_text()]
    assert footnote == ["2 refusals, no estimate\n2 above range, no estimate"]
    assert len(ax.collections[0].get_offsets()) == 2


def test_the_footnote_counts_other_blanks_as_blank():
    df = ht.set_units(
        frame(
            depth=[2.0, 4.0, np.nan, 8.0],
            effective_friction_angle=[np.nan, 35.0, 30.0, 33.0],
            correlation_name=["a"] * 4,
            correlation_note=["input blank", None, None, None],
        ),
        {"depth": "m", "effective_friction_angle": "deg"},
    )
    with pytest.warns(UserWarning, match="ground_level|loca_id"):
        _, ax = ht.plot.profile(df, "effective_friction_angle", vs="depth")
    # A blank depth is P01's blank value, whatever the note.
    assert ax.ags_notes == {"nan": 1, "correlation_input_blank": 1}


# --- AC 3: the wrong variant is an error ----------------------------------------------


def test_n60_without_n1_60_is_an_error_naming_what_adds_it():
    df = frame(spt_n=[10.0], spt_n60=[12.0])
    with pytest.raises(
        ht.ColumnError, match=r"'spt_n1_60' not found.*ht\.analysis\.spt_n1_60\("
    ):
        correlations.effective_friction_angle_hatanaka_uchida_1996(df)


@pytest.mark.parametrize("name", list(FUNCTIONS))
def test_no_argument_chooses_the_input_column(name):
    parameters = set(inspect.signature(FUNCTIONS[name]).parameters)
    # uscs= selects rows by soil (M13 b2, Decision 10), and soil= names the
    # source's soil row (M13 b3, Decision 3); neither chooses an input column.
    expected = {"df", "uscs", "units", "display_units"}
    if correlations.describe(name).get("rows"):
        expected.add("soil")
    assert parameters == expected


# --- AC 5: what's recorded ------------------------------------------------------------


def test_attrs_hold_every_entry_and_describe_returns_the_same():
    out = correlations.effective_friction_angle_hatanaka_uchida_1996(
        frame(spt_n1_60=[10.0])
    )
    recorded = out.attrs["correlations"]
    assert set(recorded) == set(_config.load("config/correlations.yaml"))
    assert recorded[
        "effective_friction_angle_hatanaka_uchida_1996"
    ] == correlations.describe("effective_friction_angle_hatanaka_uchida_1996")
    entry = recorded["effective_friction_angle_hatanaka_uchida_1996"]
    assert entry["inputs"] == {
        "spt_n1_60": {"variant": "(N1)60, N60 corrected for overburden", "unit": None}
    }
    assert entry["range"] == {"spt_n1_60": {"at_least": 4.55, "at_most": 39.0}}


def test_describe_returns_a_copy():
    correlations.describe("effective_friction_angle_hatanaka_uchida_1996")[
        "range"
    ].clear()
    assert correlations.describe("effective_friction_angle_hatanaka_uchida_1996")[
        "range"
    ]


def test_describe_an_unknown_name_lists_the_correlations():
    with pytest.raises(ht.HangtuError, match=r"no correlation named 'wolff_1989'.*"):
        correlations.describe("wolff_1989")


def test_outputs_from_one_input_concatenate_with_their_attrs():
    df = ht.set_units(frame(depth=[3.0], spt_n1_60=[10.0]), {"depth": "m"})
    first = correlations.effective_friction_angle_hatanaka_uchida_1996(df)
    second = correlations.effective_friction_angle_hatanaka_uchida_1996(df)
    both = pd.concat([first, second], ignore_index=True)
    assert both.attrs["units"] == {"depth": "m", "effective_friction_angle": "°"}
    assert both.attrs["correlations"] == first.attrs["correlations"]


# --- AC 6: the config and the docstrings agree ----------------------------------------


def _drift(name, docstring):
    """Return what the entry states and the docstring doesn't."""
    text = " ".join(docstring.split())
    entry = correlations.describe(name)
    expected = []
    for source in entry["sources"]:
        expected += [source["cite"], *source["locators"]]
    for bounds in entry["range"].values():
        expected += [f"{bound:g}" for bound in bounds.values()]
    expected += entry.get("uscs") or []
    for name, row in (entry.get("rows") or {}).items():
        expected += [name, row["wording"], f"{row['coefficient']:g}", *row["uscs"]]
    expected += list((entry.get("labels") or {}).values())
    for band in entry.get("bands", []):
        expected += [f"{bound:g}" for bound in band.values() if bound is not None]
    return [item for item in expected if item not in text]


def test_every_entry_has_a_function():
    assert set(_config.load("config/correlations.yaml")) == set(FUNCTIONS)
    assert set(correlations.__all__) == {*FUNCTIONS, "describe"}


@pytest.mark.parametrize("name", list(FUNCTIONS))
def test_the_docstring_names_the_sources_locators_and_range(name):
    assert _drift(name, FUNCTIONS[name].__doc__) == []


def test_the_drift_test_fails_when_a_docstring_changes():
    docstring = correlations.effective_friction_angle_hatanaka_uchida_1996.__doc__
    changed = re.sub(r"4\.55", "4.5", docstring)
    changed = changed.replace("Eq. 7.23", "Eq. 7.32")
    assert _drift("effective_friction_angle_hatanaka_uchida_1996", changed) == [
        "Eq. 7.23, p. 7-55",
        "4.55",
    ]


# --- Chaining (docs/work/m13b2-spt-strength-history.md, AC 5) ---------------------


@pytest.fixture
def chain_entry(monkeypatch):
    """A correlation made for the test, reading effective_friction_angle."""
    from hangtu.analysis.correlations import _framework

    entries = {
        **_framework.catalog(),
        "test_chain": {
            "target": {"column": "undrained_shear_strength", "unit": "kPa"},
            "equation": "s_u = φ′ kPa",
            "inputs": {"effective_friction_angle": {"variant": "φ′", "unit": None}},
            "range": {},
            "sources": [],
        },
    }
    monkeypatch.setattr(_framework, "catalog", lambda: entries)

    def run(df):
        item = _framework.entry("test_chain")
        values = _framework.inputs(df, item, None)
        note = _framework.notes(df, item, values)
        return _framework.estimate(
            df, "test_chain", values["effective_friction_angle"], note, "SI"
        )

    return run


def test_reading_an_estimate_warns_once_and_records_the_upstream(chain_entry):
    upstream = correlations.effective_friction_angle_hatanaka_uchida_1996(
        frame(spt_n1_60=[10.0, 20.0])
    )
    with pytest.warns(UserWarning) as caught:
        out = chain_entry(upstream)
    chain = [str(w.message) for w in caught if "Chaining" in str(w.message)]
    assert chain == [
        "'effective_friction_angle' on 2 rows is an estimate from "
        "'effective_friction_angle_hatanaka_uchida_1996'. Chaining correlations "
        "compounds their errors, and the result reads as more certain than it "
        "is: prefer an input from test data. The upstream correlation is in "
        "'correlation_input'."
    ]
    assert (
        out["correlation_input"].tolist()
        == ["effective_friction_angle_hatanaka_uchida_1996"] * 2
    )
    assert (out["correlation_name"] == "test_chain").all()


def test_measured_input_is_not_chained(chain_entry):
    out = chain_entry(frame(effective_friction_angle=[32.0]))
    assert out["correlation_input"].isna().all()


def test_data_columns_on_another_correlations_frame_are_not_chained():
    first = correlations.undrained_shear_strength_terzaghi_peck_1967(
        frame(spt_n=[10.0]), display_units="SI"
    )
    with pytest.warns(UserWarning) as caught:
        out = correlations.undrained_shear_strength_terzaghi_peck_1967(
            first, display_units="SI"
        )
    assert not [w for w in caught if "Chaining" in str(w.message)]
    assert out["correlation_input"].isna().all()


# --- The opt-in USCS map (docs/work/m13b2-spt-strength-history.md, AC 6) ----------


def clays(**columns):
    return frame(spt_n=[10.0, 10.0, 10.0, 10.0, 10.0], **columns)


USCS = ["CL", "SP", None, " ch ", "CL-ML"]


def test_proposed_groups_give_no_estimate_outside_them():
    with pytest.warns(UserWarning, match=r"3 of 5 rows \(2 not for this soil, 1 soil"):
        out = correlations.undrained_shear_strength_terzaghi_peck_1967(
            clays(uscs_symbol=USCS), uscs="proposed", display_units="SI"
        )
    assert out["correlation_note"].tolist() == [
        None,
        "not for this soil",
        "soil type unknown",
        None,
        "not for this soil",
    ]
    assert out["undrained_shear_strength_lower"].isna().tolist() == [
        False, True, True, False, True,
    ]  # fmt: skip
    assert out.attrs["correlation_uscs"] == "proposed"


def test_blanks_for_soil_alone_leave_the_range_out_of_the_warning():
    # TODO #41: the range doesn't explain rows left out for their soil.
    df = clays(uscs_symbol=["SP"] * 5)
    with pytest.warns(UserWarning) as caught:
        correlations.undrained_shear_strength_terzaghi_peck_1967(df, uscs="proposed")
    assert [str(w.message) for w in caught] == [
        "undrained_shear_strength_terzaghi_peck_1967 gave no estimate for 5 of 5 "
        "rows (5 not for this soil; see 'correlation_note')."
    ]


def test_a_list_of_groups_replaces_the_proposed_ones():
    with pytest.warns(UserWarning, match=r"3 of 5 rows"):
        out = correlations.undrained_shear_strength_terzaghi_peck_1967(
            clays(uscs_symbol=USCS), uscs=["CL", "CL-ML"], display_units="SI"
        )
    assert out["correlation_note"].tolist() == [
        None,
        "not for this soil",
        "soil type unknown",
        "not for this soil",
        None,
    ]
    assert out.attrs["correlation_uscs"] == ["CL", "CL-ML"]


def test_the_soil_reason_comes_before_the_input_reasons():
    df = frame(spt_n=[np.nan], uscs_symbol=["SP"])
    with pytest.warns(UserWarning):
        out = correlations.undrained_shear_strength_terzaghi_peck_1967(
            df, uscs="proposed"
        )
    assert out["correlation_note"].tolist() == ["not for this soil"]


def test_uscs_without_a_uscs_symbol_column_raises_saying_it_is_not_derived():
    with pytest.raises(ht.ColumnError, match=r"'uscs_symbol'.*doesn't derive"):
        correlations.undrained_shear_strength_terzaghi_peck_1967(
            clays(), uscs="proposed"
        )


def test_by_default_no_soil_type_is_read():
    out = correlations.undrained_shear_strength_terzaghi_peck_1967(
        clays(uscs_symbol=USCS), display_units="SI"
    )
    assert out["correlation_note"].isna().all()
    assert out.attrs["correlation_uscs"] is None


@pytest.mark.parametrize("bad", ["proposd", [], ["CL", 3], 5])
def test_a_wrong_uscs_argument_raises_with_examples(bad):
    with pytest.raises(ht.HangtuError, match=r'uscs= takes "proposed" or a list'):
        correlations.effective_friction_angle_hatanaka_uchida_1996(
            frame(spt_n1_60=[10.0], uscs_symbol=["SP"]), uscs=bad
        )


def test_p01_counts_the_soil_reasons():
    df = ht.set_units(
        clays(depth=[1.0, 2.0, 3.0, 4.0, 5.0], uscs_symbol=USCS), {"depth": "m"}
    )
    with pytest.warns(UserWarning):
        out = correlations.undrained_shear_strength_terzaghi_peck_1967(
            df, uscs="proposed", display_units="SI"
        )
    with pytest.warns(ht.HangtuHint):
        _, ax = ht.plot.profile(
            out, "undrained_shear_strength", vs="depth", color_by=None
        )
    assert ax.ags_notes == {
        "value_range": 2,
        "correlation_not_for_this_soil": 2,
        "correlation_soil_type_unknown": 1,
    }


def test_a_value_on_an_inclusive_bound_stays_inside_after_conversion():
    # 300 kPa through psf is 300.00000000000006 kPa; still at most 300.
    psf = ht.units.convert(
        [300.0], ht.units.parse_unit("kPa"), "stress", ht.units.parse_unit("psf")
    )
    df = stresses([20], list(psf), unit="psf")
    out = correlations.effective_friction_angle_kulhawy_mayne_1990(df)
    assert out["correlation_note"].isna().all()


# --- The soil row (docs/work/m13b3-spt-stiffness.md, AC 4 and 5) -------------------


@pytest.fixture
def rows_entry(monkeypatch):
    """A correlation made for the test, with a coefficient by soil row."""
    from hangtu.analysis.correlations import _framework

    entries = {
        **_framework.catalog(),
        "test_rows": {
            "target": {"column": "drained_youngs_modulus", "unit": "kPa"},
            "equation": "E = C N60 kPa",
            "inputs": {"spt_n60": {"variant": "N60", "unit": None}},
            "range": {},
            "rows": {
                "silts": {"wording": "Silts", "coefficient": 4, "uscs": ["ML"]},
                "sands": {"wording": "Sands", "coefficient": 7, "uscs": ["SP"]},
            },
            "uscs": None,
            "sources": [],
        },
    }
    monkeypatch.setattr(_framework, "catalog", lambda: entries)

    def run(df, soil=None, uscs=None):
        item = _framework.entry("test_rows")
        values = _framework.inputs(df, item, None)
        rows = _framework.soil_rows(df, item, soil)
        coefficient = np.array([item["rows"][row]["coefficient"] for row in rows])
        note = _framework.notes(df, item, values, uscs, rows)
        return _framework.estimate(
            df,
            "test_rows",
            coefficient * values["spt_n60"],
            note,
            "SI",
            uscs=uscs,
            rows=rows,
        )

    return run


def test_soil_is_required_and_the_error_lists_the_rows(rows_entry):
    with pytest.raises(ht.HangtuError, match=r"soil= is required.*'silts' \(Silts\)"):
        rows_entry(frame(spt_n60=[10]))


def test_an_unknown_row_name_raises_listing_the_rows(rows_entry):
    with pytest.raises(ht.HangtuError, match=r"'clays', which isn't one.*'sands'"):
        rows_entry(frame(spt_n60=[10]), soil="clays")


def test_one_row_name_applies_to_every_row(rows_entry):
    out = rows_entry(frame(spt_n60=[10, 20]), soil="sands")
    # kPa in the entry, MPa on display (modulus).
    assert out["drained_youngs_modulus"].tolist() == pytest.approx([0.07, 0.14])
    assert out["correlation_soil"].tolist() == ["sands", "sands"]


def test_a_mapping_gives_each_geology_unit_its_row(rows_entry):
    df = frame(spt_n60=[10, 10, 10], geology_unit=["Alluvium", "Terrace", "Alluvium"])
    soil = {"Alluvium": "silts", "Terrace": "sands"}
    out = rows_entry(df, soil=soil)
    assert out["drained_youngs_modulus"].tolist() == pytest.approx([0.04, 0.07, 0.04])
    assert out["correlation_soil"].tolist() == ["silts", "sands", "silts"]


def test_a_mapping_raises_naming_an_unmapped_unit(rows_entry):
    df = frame(spt_n60=[10, 10], geology_unit=["Alluvium", "Glacial till"])
    with pytest.raises(ht.HangtuError, match=r"no row for the geology units 'Glacial"):
        rows_entry(df, soil={"Alluvium": "silts"})


def test_a_mapping_raises_on_a_blank_geology_unit(rows_entry):
    df = frame(spt_n60=[10, 10], geology_unit=["Alluvium", None])
    with pytest.raises(ht.HangtuError, match=r"1 rows have no 'geology_unit'"):
        rows_entry(df, soil={"Alluvium": "silts"})


def test_a_mapping_without_geology_unit_raises(rows_entry):
    with pytest.raises(ht.ColumnError, match=r"no 'geology_unit' column"):
        rows_entry(frame(spt_n60=[10]), soil={"Alluvium": "silts"})


def test_uscs_checks_each_row_against_its_own_soil_row(rows_entry):
    df = frame(
        spt_n60=[10, 10, 10, 10],
        geology_unit=["Alluvium", "Alluvium", "Terrace", "Terrace"],
        uscs_symbol=["ML", "SP", "SP", None],
    )
    with pytest.warns(UserWarning, match=r"2 of 4 rows \(1 not for this soil, 1 soil"):
        out = rows_entry(
            df, soil={"Alluvium": "silts", "Terrace": "sands"}, uscs="proposed"
        )
    assert out["correlation_note"].tolist() == [
        None,
        "not for this soil",
        None,
        "soil type unknown",
    ]


def test_uscs_never_chooses_the_row(rows_entry):
    # An SP row under soil="silts" is checked, not moved to "sands".
    with pytest.warns(UserWarning, match=r"not for this soil"):
        out = rows_entry(
            frame(spt_n60=[10], uscs_symbol=["SP"]), soil="silts", uscs="proposed"
        )
    assert out["correlation_soil"].tolist() == ["silts"]
    assert out["drained_youngs_modulus"].isna().all()


def test_correlations_without_rows_leave_correlation_soil_blank():
    out = correlations.undrained_shear_strength_terzaghi_peck_1967(
        clays(), display_units="SI"
    )
    assert out["correlation_soil"].isna().all()


def test_proposed_raises_on_a_correlation_for_all_soils():
    from hangtu.analysis.correlations import _framework

    item = {"range": {}, "uscs": None}
    with pytest.raises(ht.HangtuError, match=r"for all soils.*uscs=\["):
        _framework.uscs_groups(item, "proposed")
