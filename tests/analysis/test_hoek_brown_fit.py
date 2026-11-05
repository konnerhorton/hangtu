"""ht.analysis.hoek_brown_fit() (docs/work/m17c-hoek-brown-fit.md, AC 1-9).

Golden values are the spec's, hand-calculated from its Derivation with the
sums written out and the arithmetic done in fractions: x = σ3, y = (σ1 - σ3)²,
free b = Sxy / Sxx and a = ȳ - b x̄, σci fixed b = Σx(y - σci²) / Σx², then
σci = √a and mi = b / σci. Points are (σ3, σ1) in MPa.
"""

import hashlib
import json
import math
import warnings

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError, UnitsError

REL = 1e-7
#: 1 MPa in psi: 1 psi = 0.45359237 × 9.80665 / 0.0254² Pa (exact).
PSI = 1e6 / (0.45359237 * 9.80665 / 0.0254**2)
MINOR = "minor_principal_stress_at_failure"
MAJOR = "major_principal_stress_at_failure"
EFFECTIVE = [
    "effective_minor_principal_stress_at_failure",
    "effective_major_principal_stress_at_failure",
]
#: Hoek (2007), ch. 11, Table 1: one UCS test and four triaxial tests.
TABLE_1 = [(0, 38.3), (5, 72.4), (7.5, 80.5), (15, 115.6), (20, 134.3)]
BEYOND = r"points at σ3 ≥ 0\.5 σci of their fit"
FEW = r"fewer than 5 points"
COUNTS = [
    "count_no_principal_stresses",
    "count_no_effective_stresses",
    "count_other_failure_mode",
    "count_multistage_left_out",
]


def _frame(points, unit="MPa", **columns):
    """Rows at failure with the total pair ``(σ3, σ1)``, the effective pair blank."""
    minor, major = (
        np.array(values, dtype=float) for values in zip(*points, strict=True)
    )
    df = pd.DataFrame(
        {
            MINOR: minor,
            MAJOR: major,
            **dict.fromkeys(EFFECTIVE, np.nan),
            **columns,
        }
    )
    df.attrs["units"] = dict.fromkeys([MINOR, MAJOR, *EFFECTIVE], unit)
    return df


def _fit(df, **kwargs):
    """Fit, failing on any warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return ht.analysis.hoek_brown_fit(df, **kwargs)


def _get(result, kind="free", stages="all", group=0):
    fits = result.groups[group]["fits"]
    return next(f for f in fits if f["line_kind"] == kind and f["stages"] == stages)


def _counts_add_up(result):
    """AC 9: count plus the four count_... is each group's rows, in every fit."""
    for group in result.groups:
        for fit in group["fits"]:
            assert (
                fit["count"] + sum(fit[name] for name in COUNTS)
                == (group["count_rows"])
            ), fit


def _table_1(**kwargs):
    with pytest.warns(UserWarning, match=BEYOND) as caught:
        result = ht.analysis.hoek_brown_fit(_frame(TABLE_1), **kwargs)
    assert len(caught) == 1, [str(w.message) for w in caught]
    return result


# --- AC 1, 2: Hoek (2007) Table 1, free and with σci fixed ---------------------------


def test_1_table_1_free():
    result = _table_1()
    free = _get(result)
    # b = 197071/340, a = 950847/680.
    assert free["line_slope"] == pytest.approx(197071 / 340, rel=1e-12)
    assert free["line_intercept"] == pytest.approx(950847 / 680, rel=1e-12)
    assert free["intact_compressive_strength"] == pytest.approx(37.3939088, rel=REL)
    assert free["intact_hoek_brown_constant"] == pytest.approx(15.5004012, rel=REL)
    assert free["r_squared"] == pytest.approx(0.997147827, rel=REL)
    assert free["count"] == 5
    assert (
        free["lowest_minor_principal_stress"],
        free["highest_minor_principal_stress"],
    ) == (0, 20)
    # 0.5 σci = 18.70, so σ3 = 20 is beyond.
    assert free["count_beyond_confining_range"] == 1
    assert (free["uniaxial_count"], free["uniaxial_mean"]) == (1, 38.3)
    assert free["intact_compressive_strength_source"] == "fitted"
    back = [p["back_calculated_hoek_brown_constant"] for p in free["points"]]
    assert math.isnan(back[0])
    assert back[1:] == pytest.approx(
        [16.8180096, 14.0154577, 15.5498687, 15.5990454], rel=REL
    )
    _counts_add_up(result)


def test_1_without_sigma_ci_the_fixed_fit_has_its_reason():
    fixed = _get(_table_1(), "fixed_strength")
    assert fixed["no_fit_reason"] == (
        "no σci given: pass fixed_intact_compressive_strength= or add it to the "
        "judgments file"
    )
    assert math.isnan(fixed["intact_compressive_strength"])
    assert math.isnan(fixed["intact_hoek_brown_constant"])
    assert fixed["intact_compressive_strength_source"] is None
    assert fixed["count"] == 5


def test_2_table_1_with_sigma_ci_fixed():
    result = _table_1(fixed_intact_compressive_strength="38.3 MPa")
    fixed = _get(result, "fixed_strength")
    # Σx(y - a) = 406099.225 over Σx² = 706.25.
    assert fixed["line_slope"] == pytest.approx(406099.225 / 706.25, rel=1e-12)
    assert fixed["line_slope"] == pytest.approx(575.007752, rel=REL)
    assert fixed["intact_compressive_strength"] == 38.3
    assert fixed["intact_hoek_brown_constant"] == pytest.approx(15.0132572, rel=REL)
    assert fixed["r_squared"] == pytest.approx(0.997048983, rel=REL)
    assert fixed["intact_compressive_strength_source"] == "argument"
    back = [p["back_calculated_hoek_brown_constant"] for p in fixed["points"]]
    assert back[1:] == pytest.approx(
        [16.0619843, 13.4451175, 15.0626110, 15.1404700], rel=REL
    )
    # 0.5 × 38.3 = 19.15: σ3 = 20 is beyond.
    assert fixed["count_beyond_confining_range"] == 1
    _counts_add_up(result)


def test_2_through_triaxial_failure_stresses():
    # Table 1 typed into the template's columns, σ1 - σ3 as the deviator.
    df = pd.DataFrame(
        {
            "test_type": ["UCS", *["Triaxial"] * 4],
            "cell_pressure": [x for x, _ in TABLE_1],
            "deviator_stress_at_failure": [y - x for x, y in TABLE_1],
        }
    )
    df = ht.set_units(df, {"cell_pressure": "MPa", "deviator_stress_at_failure": "MPa"})
    df = ht.analysis.triaxial_failure_stresses(df)
    with pytest.warns(UserWarning, match=BEYOND):
        result = ht.analysis.hoek_brown_fit(
            df, fixed_intact_compressive_strength="38.3 MPa"
        )
    assert _get(result)["intact_hoek_brown_constant"] == pytest.approx(
        15.5004012, rel=REL
    )
    assert result.unit == "MPa"


# --- AC 4: units ---------------------------------------------------------------------


def test_4_psi_twin_gives_the_same_mi():
    df = _frame([(x * PSI, y * PSI) for x, y in TABLE_1], unit="psi")
    with pytest.warns(UserWarning, match=BEYOND):
        result = ht.analysis.hoek_brown_fit(
            df, fixed_intact_compressive_strength=f"{38.3 * PSI} psi"
        )
    mpa = _table_1(fixed_intact_compressive_strength="38.3 MPa")
    assert result.unit == "psi"
    assert _get(result)["intact_compressive_strength"] == pytest.approx(
        5423.52793, rel=REL
    )
    for kind in ["free", "fixed_strength"]:
        assert _get(result, kind)["intact_hoek_brown_constant"] == pytest.approx(
            _get(mpa, kind)["intact_hoek_brown_constant"], rel=1e-9
        )


def test_4_display_units_converts_before_fitting():
    with pytest.warns(UserWarning, match=BEYOND):
        result = ht.analysis.hoek_brown_fit(_frame(TABLE_1), display_units="SI")
    free = _get(result)
    assert result.unit == "kPa"
    assert free["intact_compressive_strength"] == pytest.approx(37393.9088, rel=REL)
    assert free["intact_hoek_brown_constant"] == pytest.approx(15.5004012, rel=REL)
    assert result.to_frame().attrs["units"]["intact_compressive_strength"] == "kPa"


def test_4_fixed_value_in_another_unit_converts():
    # 38.3 MPa × 145.037738 = 5554.95 psi.
    result = _table_1(fixed_intact_compressive_strength=f"{38.3 * PSI:.10f} psi")
    fixed = _get(result, "fixed_strength")
    assert fixed["intact_compressive_strength"] == pytest.approx(38.3, rel=1e-9)
    assert fixed["intact_hoek_brown_constant"] == pytest.approx(15.0132572, rel=REL)


@pytest.mark.parametrize("value", [61, 61.0])
def test_4_bare_number_asks_for_the_unit(value):
    with pytest.raises(HangtuError, match=r'needs its unit: .*"61 MPa"'):
        ht.analysis.hoek_brown_fit(
            _frame(TABLE_1), fixed_intact_compressive_strength=value
        )


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("61 kN/m3", r"fixed_intact_compressive_strength="),
        ("sixty MPa", r"must be a number followed by a unit"),
        ("0 MPa", r"must be positive, not '0 MPa'"),
    ],
)
def test_4_fixed_value_errors(value, message):
    with pytest.raises(HangtuError, match=message):
        ht.analysis.hoek_brown_fit(
            _frame(TABLE_1), fixed_intact_compressive_strength=value
        )


def test_4_frame_without_units_raises_naming_the_column():
    df = _frame(TABLE_1)
    df.attrs = {}
    with pytest.raises(UnitsError, match=MINOR):
        ht.analysis.hoek_brown_fit(df)


def test_4_units_argument_overrides_attrs():
    df = _frame([(x * 1000, y * 1000) for x, y in TABLE_1])
    with pytest.warns(UserWarning, match=BEYOND):
        result = ht.analysis.hoek_brown_fit(
            df, units=dict.fromkeys([MINOR, MAJOR], "kPa")
        )
    assert result.unit == "kPa"
    assert _get(result)["intact_hoek_brown_constant"] == pytest.approx(
        15.5004012, rel=REL
    )


def test_4_frame_without_the_principal_stresses_raises():
    df = pd.DataFrame({"cell_pressure": [0, 5], "deviator_stress_at_failure": [40, 60]})
    with pytest.raises(
        ht.ColumnError,
        match=r"triaxial_failure_stresses\(\).*ht\.template\(\"triaxial\"\)",
    ):
        ht.analysis.hoek_brown_fit(df)


# --- AC 5: failure modes -------------------------------------------------------------

#: The example's modes: 13 shear points, one splitting UCS, one along bedding.
MODES = ["Shear"] * 5 + ["Axial splitting", "Along bedding"]
MODE_POINTS = [*TABLE_1, (0, 38.6), (10, 88.0)]


def _modes(modes=MODES):
    return _frame(MODE_POINTS, failure_mode=modes)


def test_5_modes_required_when_the_column_has_values():
    with pytest.raises(
        HangtuError,
        match=r"needs failure_modes=.*'Shear' \(5 rows\), 'Axial splitting' \(1 row\), "
        r"'Along bedding' \(1 row\).*failure_modes=\['Shear'\]",
    ):
        ht.analysis.hoek_brown_fit(_modes())


def test_5_a_mode_no_row_has_raises():
    with pytest.raises(
        HangtuError, match=r"names 'shear', which no row has.*'Shear' \(5 rows\)"
    ):
        ht.analysis.hoek_brown_fit(_modes(), failure_modes=["shear"])


def test_5_rows_of_other_modes_are_left_out_and_counted():
    with pytest.warns(UserWarning, match=BEYOND):
        result = ht.analysis.hoek_brown_fit(_modes(), failure_modes=["Shear"])
    free = _get(result)
    assert free["count"] == 5
    assert free["count_other_failure_mode"] == 2
    assert free["intact_hoek_brown_constant"] == pytest.approx(15.5004012, rel=REL)
    group = result.groups[0]
    assert group["count_by_failure_mode"] == {"Axial splitting": 1, "Along bedding": 1}
    assert [row["reason"] for row in group["left_out"]] == [
        "count_other_failure_mode"
    ] * 2
    assert [row["failure_mode"] for row in group["left_out"]] == [
        "Axial splitting",
        "Along bedding",
    ]
    assert result.failure_modes == ("Shear",)
    assert "left out: 2 other failure mode (Axial splitting 1, Along bedding 1)" in (
        str(result)
    )
    _counts_add_up(result)


def test_5_two_modes_named_fit_both():
    with pytest.warns(UserWarning, match=BEYOND):
        result = ht.analysis.hoek_brown_fit(
            _modes(), failure_modes=["Shear", "Along bedding"]
        )
    assert _get(result)["count"] == 6
    assert _get(result)["count_other_failure_mode"] == 1


def test_5_without_the_column_every_row_is_fitted_with_a_note():
    with pytest.warns(UserWarning, match=BEYOND):
        result = ht.analysis.hoek_brown_fit(_frame(MODE_POINTS))
    assert _get(result)["count"] == 7
    assert result.failure_modes is None
    assert any(note.startswith("failure_mode not given") for note in result.notes)


@pytest.mark.parametrize("modes", [None, [None] * 7])
def test_5_failure_modes_on_a_frame_without_modes_raises(modes):
    df = _frame(MODE_POINTS) if modes is None else _modes(modes)
    state = "missing" if modes is None else "blank throughout"
    with pytest.raises(HangtuError, match=rf"failure_mode column is {state}"):
        ht.analysis.hoek_brown_fit(df, failure_modes=["Shear"])


def test_5_a_blank_mode_is_left_out_unless_none_is_named():
    modes = [*MODES[:4], None, *MODES[5:]]
    with pytest.warns(UserWarning):
        result = ht.analysis.hoek_brown_fit(_modes(modes), failure_modes=["Shear"])
    assert _get(result)["count"] == 4
    assert result.groups[0]["count_by_failure_mode"] == {
        "blank": 1,
        "Axial splitting": 1,
        "Along bedding": 1,
    }
    with pytest.warns(UserWarning, match=BEYOND):
        result = ht.analysis.hoek_brown_fit(
            _modes(modes), failure_modes=["Shear", None]
        )
    assert _get(result)["count"] == 5


def test_5_without_modes_named_the_error_lists_blank():
    modes = [*MODES[:4], None, *MODES[5:]]
    with pytest.raises(HangtuError, match=r"blank \(1 row\)"):
        ht.analysis.hoek_brown_fit(_modes(modes))


# --- AC 7: validity (hand-built) -----------------------------------------------------


def test_7_ucs_only():
    result = _fit(
        _frame([(0, 50), (0, 55), (0, 60)]),
        fixed_intact_compressive_strength="55 MPa",
    )
    free, fixed = _get(result), _get(result, "fixed_strength")
    assert free["no_fit_reason"] == "all points at the same minor principal stress"
    assert fixed["no_fit_reason"] == "all points at minor principal stress = 0"
    assert fixed["intact_compressive_strength"] == 55
    assert free["uniaxial_mean"] == 55
    assert free["uniaxial_count"] == 3
    _counts_add_up(result)


def test_7_one_minor_principal_stress():
    with pytest.warns(UserWarning, match=FEW) as caught:
        result = ht.analysis.hoek_brown_fit(
            _frame([(10, 120), (10, 125)]),
            fixed_intact_compressive_strength="50 MPa",
        )
    assert len(caught) == 1
    assert _get(result)["no_fit_reason"] == (
        "all points at the same minor principal stress"
    )
    fixed = _get(result, "fixed_strength")
    # y = 12100, 13225; b = 203250 / 200 = 1016.25, mi = 1016.25 / 50.
    assert fixed["line_slope"] == pytest.approx(1016.25, rel=1e-12)
    assert fixed["intact_hoek_brown_constant"] == pytest.approx(20.325, rel=1e-12)
    assert any("2 points" in note for note in fixed["notes"])


def test_7_negative_intercept_has_no_free_fit():
    # Sxx = 350/3, Sxy = 45000, a = -1325.
    with pytest.warns(UserWarning, match=FEW):
        result = ht.analysis.hoek_brown_fit(
            _frame([(5, 30), (10, 60), (20, 100)]),
            fixed_intact_compressive_strength="50 MPa",
        )
    free = _get(result)
    assert free["no_fit_reason"] == "intercept σci² = -1325 is 0 or below: no σci"
    assert math.isnan(free["intact_compressive_strength"])
    assert all(
        math.isnan(p["back_calculated_hoek_brown_constant"]) for p in free["points"]
    )
    assert _get(result, "fixed_strength")["no_fit_reason"] is None


def test_7_negative_slope_has_no_fit():
    result = _fit(_frame([(0, 60), (10, 65), (20, 70)]))
    assert _get(result)["no_fit_reason"] == (
        "slope mi σci = -55 is 0 or below: mi must be positive"
    )
    # No fit has a result, so no warning about the number of points.
    assert math.isnan(_get(result)["intact_hoek_brown_constant"])


def test_7_point_beyond_half_sigma_ci():
    with pytest.warns(UserWarning, match=BEYOND) as caught:
        result = ht.analysis.hoek_brown_fit(
            _frame([(0, 50), (5, 85), (10, 105), (20, 140), (40, 190)])
        )
    assert len(caught) == 1
    assert "All: 1 (free)" in str(caught[0].message)
    free = _get(result)
    assert free["line_intercept"] == pytest.approx(3646.875, rel=1e-12)
    assert free["line_slope"] == pytest.approx(487.875, rel=1e-12)
    assert free["intact_compressive_strength"] == pytest.approx(60.3893616, rel=REL)
    assert free["intact_hoek_brown_constant"] == pytest.approx(8.07882360, rel=REL)
    assert free["r_squared"] == pytest.approx(0.987174208, rel=REL)
    # σ3 = 40 ≥ 0.5 × 60.39 = 30.19.
    assert free["count_beyond_confining_range"] == 1


def test_7_low_r_squared_is_a_note_not_a_warning():
    # A scattered set: R² = 0.556 by the same sums.
    points = [(0, 40), (0, 70), (5, 60), (5, 95), (10, 80), (10, 105)]
    result = _fit(_frame(points))
    free = _get(result)
    assert free["r_squared"] < 0.9
    assert any(note.startswith("R² = ") for note in free["notes"])
    assert "is below 0.9" in str(result)


@pytest.mark.parametrize(
    ("points", "message"),
    [
        ([(0, 50), (-1, 60), (5, 90)], r"Rows 1 have σ3 < 0 \(tension\)"),
        ([(0, 50), (10, 8), (5, 90)], r"Rows 1 have σ1 < σ3"),
    ],
)
def test_7_tension_or_reversed_stresses_raise(points, message):
    with pytest.raises(HangtuError, match=message):
        ht.analysis.hoek_brown_fit(_frame(points))


# --- AC 8 (stresses), multistage, rows left out --------------------------------------


def test_8_effective_leaves_out_rows_without_effective_stresses():
    df = _frame(TABLE_1)
    df.loc[[3, 4], EFFECTIVE[0]] = [10, 15]
    df.loc[[3, 4], EFFECTIVE[1]] = [110.6, 129.3]
    df.loc[2, MAJOR] = np.nan
    with pytest.warns(UserWarning, match=FEW):
        result = ht.analysis.hoek_brown_fit(df, stress="effective")
    free = _get(result)
    assert free["count"] == 2
    assert free["count_no_principal_stresses"] == 1
    assert free["count_no_effective_stresses"] == 2
    assert result.stress == "effective"
    _counts_add_up(result)


@pytest.mark.parametrize(
    ("argument", "message"),
    [
        ({"stress": "mean"}, r"stress must be 'total' or 'effective', not 'mean'"),
        ({"multistage": "yes"}, r"multistage must be True or False"),
        ({"display_units": "metric"}, r"display_units must be"),
        ({"group_by": "geology_unit"}, r"can't group by 'geology_unit'"),
    ],
)
def test_arguments_out_of_range_raise(argument, message):
    with pytest.raises(HangtuError, match=message):
        ht.analysis.hoek_brown_fit(_frame(TABLE_1), **argument)


def test_not_a_frame_raises():
    with pytest.raises(HangtuError, match="must be a pandas DataFrame"):
        ht.analysis.hoek_brown_fit(TABLE_1)


#: Table 1 plus a multistage specimen of three stages, biased low.
MULTISTAGE_POINTS = [*TABLE_1, (5, 66.0), (10, 85.0), (20, 120.0)]
MULTISTAGE = [False] * 5 + [True] * 3


def test_multistage_stages_give_two_stage_sets():
    df = _frame(MULTISTAGE_POINTS, multistage_test=MULTISTAGE)
    with pytest.warns(UserWarning, match=BEYOND):
        result = ht.analysis.hoek_brown_fit(df)
    fits = result.groups[0]["fits"]
    assert [(f["stages"], f["line_kind"]) for f in fits] == [
        ("all", "free"),
        ("all", "fixed_strength"),
        ("single_stage", "free"),
        ("single_stage", "fixed_strength"),
    ]
    single = _get(result, stages="single_stage")
    assert single["count"] == 5
    assert single["count_multistage_left_out"] == 3
    assert single["intact_hoek_brown_constant"] == pytest.approx(15.5004012, rel=REL)
    assert _get(result)["count"] == 8
    assert _get(result)["count_multistage_left_out"] == 0
    assert [p["multistage_test"] for p in _get(result)["points"]] == MULTISTAGE
    assert "all stages, free:" in str(result)
    assert "single stage, free:" in str(result)
    _counts_add_up(result)


def test_multistage_false_puts_the_single_stage_fits_first():
    df = _frame(MULTISTAGE_POINTS, multistage_test=MULTISTAGE)
    with pytest.warns(UserWarning, match=BEYOND):
        result = ht.analysis.hoek_brown_fit(df, multistage=False)
    frame = result.to_frame()
    assert frame["stages"].tolist() == ["single_stage"] * 2 + ["all"] * 2
    assert frame["intact_hoek_brown_constant"].iloc[0] == pytest.approx(
        15.5004012, rel=REL
    )


def test_every_stage_multistage_has_no_single_stage_fit():
    df = _frame(MULTISTAGE_POINTS[5:], multistage_test=[True] * 3)
    with pytest.warns(UserWarning) as caught:
        result = ht.analysis.hoek_brown_fit(df)
    messages = [str(w.message) for w in caught]
    assert len(messages) == 2
    assert "fewer than 5 points in All (3 points)" in messages[0]
    single = _get(result, stages="single_stage")
    assert single["no_fit_reason"] == "every stage is multistage"
    _counts_add_up(result)


def test_without_multistage_test_a_note_says_so():
    result = _table_1()
    assert "multistage_test not given: multistage stages weren't told apart." in (
        result.notes
    )
    assert len(result.groups[0]["fits"]) == 2


def test_rows_without_principal_stresses_are_counted():
    df = _frame([*TABLE_1, (np.nan, np.nan), (5, np.nan)])
    with pytest.warns(UserWarning, match=BEYOND):
        result = ht.analysis.hoek_brown_fit(df)
    free = _get(result)
    assert free["count"] == 5
    assert free["count_no_principal_stresses"] == 2
    assert [row["row"] for row in result.groups[0]["left_out"]] == [5, 6]
    _counts_add_up(result)


def test_the_lab_pair_is_listed_not_compared():
    df = _frame(
        TABLE_1,
        reported_intact_compressive_strength=[37.4] * 5,
        reported_intact_hoek_brown_constant=[15.5] * 5,
    )
    df.attrs["units"]["reported_intact_compressive_strength"] = "MPa"
    with pytest.warns(UserWarning, match=BEYOND):
        result = ht.analysis.hoek_brown_fit(df, display_units="SI")
    free = _get(result)
    assert free["reported_pairs"] == [
        {
            "intact_compressive_strength": pytest.approx(37400),
            "intact_hoek_brown_constant": 15.5,
            "count": 5,
        }
    ]
    row = result.to_frame().iloc[0]
    assert row["reported_intact_compressive_strength"] == pytest.approx(37400)
    assert row["reported_intact_hoek_brown_constant"] == 15.5
    assert row["count_reported_pairs"] == 1
    assert "lab: σci = 37400 kPa, mi = 15.5 (5 rows)" in str(result)


# --- AC 9: views ---------------------------------------------------------------------

COLUMNS = [
    "stages",
    "line_kind",
    "intact_compressive_strength",
    "intact_hoek_brown_constant",
    "r_squared",
    "count",
    "lowest_minor_principal_stress",
    "highest_minor_principal_stress",
    "count_beyond_confining_range",
    "uniaxial_count",
    "uniaxial_mean",
    "intact_compressive_strength_source",
    "reported_intact_compressive_strength",
    "reported_intact_hoek_brown_constant",
    "count_reported_pairs",
    *COUNTS,
    "no_fit_reason",
]


def test_9_views():
    result = _table_1(fixed_intact_compressive_strength="38.3 MPa")
    frame = result.to_frame()
    assert list(frame.columns) == COLUMNS
    assert frame["line_kind"].tolist() == ["free", "fixed_strength"]
    assert frame["intact_compressive_strength"].tolist() == pytest.approx(
        [37.3939088, 38.3], rel=REL
    )
    assert frame.attrs["units"] == dict.fromkeys(
        [
            "intact_compressive_strength",
            "lowest_minor_principal_stress",
            "highest_minor_principal_stress",
            "uniaxial_mean",
            "reported_intact_compressive_strength",
        ],
        "MPa",
    )
    assert result.kind == "derived"
    json.dumps(result.to_dict())
    text = str(result)
    assert text.splitlines()[:3] == [
        "Hoek-Brown fit of intact rock, total stresses",
        "free: σci = 37.4 MPa, mi = 15.5, R² = 0.997, 5 points, σ3 0 to 20.0 MPa",
        "  σci fixed at 38.3 MPa (argument): mi = 15.0, R² = 0.997",
    ]
    assert "UCS (σ3 = 0): 1 test, mean 38.3 MPa" in text
    assert repr(result) == text


def test_9_views_without_a_fit():
    result = _fit(_frame([(0, 50), (0, 55), (0, 60)]))
    frame = result.to_frame()
    assert frame["no_fit_reason"].iloc[0] == (
        "all points at the same minor principal stress"
    )
    json.dumps(result.to_dict())
    assert "free: not fitted: all points at the same minor principal stress" in (
        str(result)
    )
    assert "σci fixed: not fitted: no σci given" in str(result)


# --- AC 6: the fixed σci's sources ---------------------------------------------------

#: Two units of Table 1's points: Sandstone as given, Shale with σ1 halved.
UNITS = ["Sandstone"] * 5 + ["Shale"] * 5
TWO_UNITS = [*TABLE_1, *[(x, x + (y - x) / 2) for x, y in TABLE_1]]
FILE = """\
fixed_intact_compressive_strength:
  by: geology_unit
  units: {intact_compressive_strength: MPa}
  values:
    Sandstone: {intact_compressive_strength: 38.3, reason: "the UCS test"}
"""


def _two_units(**columns):
    return _frame(TWO_UNITS, geology_unit=UNITS, **columns)


def _judgments(tmp_path, text=FILE):
    path = tmp_path / "judgments.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def _messages(call, *args, **kwargs):
    with pytest.warns(UserWarning) as caught:
        result = call(*args, **kwargs)
    return result, [str(w.message) for w in caught]


def test_6_from_the_judgments_file(tmp_path):
    path = _judgments(tmp_path)
    df = _two_units()
    df.attrs["judgments_file"] = str(path)
    result, _ = _messages(ht.analysis.hoek_brown_fit, df, group_by="geology_unit")
    fixed = _get(result, "fixed_strength")
    assert fixed["intact_compressive_strength"] == 38.3
    assert fixed["intact_hoek_brown_constant"] == pytest.approx(15.0132572, rel=REL)
    assert fixed["intact_compressive_strength_source"] == "judgments file"
    assert fixed["fixed_strength"]["sha256"] == (
        hashlib.sha256(path.read_bytes()).hexdigest()
    )
    assert fixed["fixed_strength"]["reason"] == "the UCS test"
    assert "σci fixed at 38.3 MPa (judgments.yaml): mi = 15.0" in str(result)
    record = result.judgments["fixed_intact_compressive_strength"]
    assert record["source"] == str(path)
    assert record["values"] == {"Sandstone": "38.3 MPa"}
    shale = _get(result, "fixed_strength", group=1)
    assert shale["no_fit_reason"] == (
        "the judgments file's fixed_intact_compressive_strength has no value for "
        "geology_unit 'Shale': add it, or a project: entry with its reason"
    )
    _counts_add_up(result)


def test_6_judgments_argument_reads_the_file(tmp_path):
    result, _ = _messages(
        ht.analysis.hoek_brown_fit,
        _two_units(),
        group_by="geology_unit",
        judgments=_judgments(tmp_path),
    )
    assert _get(result, "fixed_strength")["intact_compressive_strength"] == 38.3


def test_6_the_argument_beside_the_file_warns_and_wins(tmp_path):
    result, messages = _messages(
        ht.analysis.hoek_brown_fit,
        _two_units(),
        group_by="geology_unit",
        judgments=_judgments(tmp_path),
        fixed_intact_compressive_strength="40 MPa",
    )
    assert (
        "fixed_intact_compressive_strength= replaces the "
        "fixed_intact_compressive_strength in judgments.yaml." in messages
    )
    assert _get(result, "fixed_strength")["intact_compressive_strength"] == 40
    assert _get(result, "fixed_strength", group=1)["intact_compressive_strength"] == 40
    assert result.judgments["fixed_intact_compressive_strength"]["source"] == (
        "argument"
    )


def test_6_a_mapping_by_group():
    result, messages = _messages(
        ht.analysis.hoek_brown_fit,
        _frame(TABLE_1, geology_unit=["Sandstone"] * 5),
        group_by="geology_unit",
        fixed_intact_compressive_strength={"Sandstone": "38.3 MPa", "Shale": "20 MPa"},
    )
    assert _get(result, "fixed_strength")["intact_hoek_brown_constant"] == (
        pytest.approx(15.0132572, rel=REL)
    )
    unused = [m for m in messages if "match no group" in m]
    assert unused == [
        "hoek_brown_fit() fixed_intact_compressive_strength= has values for "
        "'Shale', which match no group (group_by=['geology_unit']: 'Sandstone'). "
        "Check the spelling: keys match exactly, by case too."
    ]


def test_6_a_group_the_mapping_doesnt_list_has_a_reason():
    result, _ = _messages(
        ht.analysis.hoek_brown_fit,
        _two_units(),
        group_by="geology_unit",
        fixed_intact_compressive_strength={"Sandstone": "38.3 MPa"},
    )
    assert _get(result, "fixed_strength", group=1)["no_fit_reason"] == (
        "no σci for this group in fixed_intact_compressive_strength=: add 'Shale' "
        "to the mapping"
    )


def test_6_a_mapping_by_two_columns_takes_tuples():
    result, _ = _messages(
        ht.analysis.hoek_brown_fit,
        _two_units(loca_id=["B-3"] * 10),
        group_by=["geology_unit", "loca_id"],
        fixed_intact_compressive_strength={("Sandstone", "B-3"): "38.3 MPa"},
    )
    assert _get(result, "fixed_strength")["intact_compressive_strength"] == 38.3


def test_6_a_bare_number_in_a_mapping_asks_for_the_unit():
    with pytest.raises(HangtuError, match=r"\{'Sandstone': \.\.\.\} needs its unit"):
        ht.analysis.hoek_brown_fit(
            _two_units(),
            group_by="geology_unit",
            fixed_intact_compressive_strength={"Sandstone": 38.3},
        )


def test_6_no_argument_and_no_file_entry(tmp_path):
    text = "specific_gravity:\n  by: geology_unit\n  values:\n"
    text += '    Sandstone: {specific_gravity: 2.65, reason: "x"}\n'
    result, _ = _messages(
        ht.analysis.hoek_brown_fit,
        _two_units(),
        group_by="geology_unit",
        judgments=_judgments(tmp_path, text),
    )
    assert _get(result, "fixed_strength")["no_fit_reason"].startswith("no σci given")
    assert "fixed_intact_compressive_strength" not in result.judgments


def test_6_a_file_keyed_by_another_column(tmp_path):
    text = FILE.replace("by: geology_unit", "by: specimen_id")
    result, _ = _messages(
        ht.analysis.hoek_brown_fit,
        _two_units(),
        group_by="geology_unit",
        judgments=_judgments(tmp_path, text),
    )
    for group in (0, 1):
        assert _get(result, "fixed_strength", group=group)["no_fit_reason"] == (
            "the judgments file's fixed_intact_compressive_strength is keyed by "
            "'specimen_id': group by it (group_by='specimen_id') to use it"
        )


def test_6_the_project_value_fills_an_unlisted_group_with_a_warning(tmp_path):
    text = FILE.replace(
        "  values:",
        '  project: {intact_compressive_strength: 19, reason: "half of it"}\n  values:',
    )
    result, messages = _messages(
        ht.analysis.hoek_brown_fit,
        _two_units(),
        group_by="geology_unit",
        judgments=_judgments(tmp_path, text),
    )
    assert (
        "fixed_intact_compressive_strength: the project value 19 MPa is used for "
        "Shale (half of it)." in messages
    )
    shale = _get(result, "fixed_strength", group=1)
    assert shale["intact_compressive_strength"] == 19
    assert shale["no_fit_reason"] is None
    record = result.judgments["fixed_intact_compressive_strength"]
    assert record["values"]["project"] == {"value": "19 MPa", "used_for": "Shale"}


def test_6_a_file_value_in_another_unit_converts(tmp_path):
    text = FILE.replace("MPa}", "psi}").replace("38.3,", f"{38.3 * PSI},")
    result, _ = _messages(
        ht.analysis.hoek_brown_fit,
        _two_units(),
        group_by="geology_unit",
        judgments=_judgments(tmp_path, text),
    )
    fixed = _get(result, "fixed_strength")
    assert fixed["intact_compressive_strength"] == pytest.approx(38.3, rel=1e-9)


# --- AC 8: pooling -------------------------------------------------------------------


def test_8_two_failure_criteria_raise():
    df = _frame(TABLE_1, failure_criterion=["Peak"] * 3 + ["Maximum stress"] * 2)
    with pytest.raises(
        HangtuError,
        match=r"failure_criterion: 'Peak' \(3 rows\),\s+'Maximum stress' \(2 rows\)",
    ):
        ht.analysis.hoek_brown_fit(df)


def test_8_pool_fits_them_on_purpose():
    df = _frame(TABLE_1, failure_criterion=["Peak"] * 3 + ["Maximum stress"] * 2)
    with pytest.warns(UserWarning, match=BEYOND):
        result = ht.analysis.hoek_brown_fit(df, pool="failure_criterion")
    assert result.pooled == ("failure_criterion",)
    assert "Pooled on purpose: failure_criterion." in result.notes


def test_8_pool_takes_only_failure_criterion():
    with pytest.raises(HangtuError, match=r"can't pool 'test_type'.*'failure_crit"):
        ht.analysis.hoek_brown_fit(_frame(TABLE_1), pool="test_type")


def test_8_ucs_and_triaxial_types_fit_together():
    df = _frame(
        TABLE_1,
        test_type=["UCS", *["Triaxial"] * 4],
        failure_criterion=["Peak"] * 5,
    )
    with pytest.warns(UserWarning, match=BEYOND):
        result = ht.analysis.hoek_brown_fit(df)
    assert _get(result)["count"] == 5
    assert not any("failure_criterion not given" in note for note in result.notes)


def test_8_without_failure_criterion_a_note_says_so():
    assert (
        "failure_criterion not given: the fit couldn't check that the rows share one."
        in _table_1().notes
    )


def test_group_by_gives_one_set_of_fits_per_group():
    result, _ = _messages(
        ht.analysis.hoek_brown_fit, _two_units(), group_by="geology_unit"
    )
    frame = result.to_frame()
    assert frame["geology_unit"].tolist() == ["Sandstone"] * 2 + ["Shale"] * 2
    assert list(frame.columns[:3]) == ["geology_unit", "stages", "line_kind"]
    # Shale's deviator stresses are half Sandstone's, so y = (σ1 - σ3)² is a
    # quarter: a and b are a quarter, σci = √a halves and mi = b / σci halves.
    sandstone, shale = frame["intact_compressive_strength"].iloc[[0, 2]]
    assert shale == pytest.approx(sandstone / 2, rel=1e-12)
    mi = frame["intact_hoek_brown_constant"].iloc[[0, 2]].tolist()
    assert mi[0] == pytest.approx(15.5004012, rel=REL)
    assert mi[1] == pytest.approx(15.5004012 / 2, rel=REL)
    text = str(result)
    assert "Sandstone: 5 rows" in text and "Shale: 5 rows" in text
    _counts_add_up(result)
