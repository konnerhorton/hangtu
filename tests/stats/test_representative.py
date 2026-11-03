"""representative(): the characteristic value (docs/work/m18b-representative-values.md).

Golden values are the spec's (G1-G4), hand-calculated from the JRC report's
formulas with NumPy and SciPy, not from the implementation; 1e-6 relative.
"""

import math

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import hangtu as ht
from hangtu.errors import HangtuError

#: G1, JRC Annex I (Coca), Table 33: c' in kPa.
COHESION = [27.0, 45.0, 47.0, 46.0, 4.5, 9.5]
#: G2, Annex I: tan φ'.
FRICTION = [0.61, 0.63, 0.47, 0.55, 0.51, 0.53]
#: G3, Annex IV (Puurs), Table 48: k_v by falling head, m/s.
CLAY = [x * 1e-10 for x in (1.2, 1.7, 3.8, 3.2, 2.8, 5.7, 3.3, 2.2, 9.8, 110, 2.9)]
PEAT = [5.2e-10, 12e-10, 12e-10]
REL = 1e-6


def cohesion():
    frame = pd.DataFrame({"effective_cohesion": COHESION})
    return ht.set_units(frame, {"effective_cohesion": "kPa"})


def characteristic(data, **kwargs):
    kwargs.setdefault("side", "low")
    kwargs.setdefault("distribution", "normal")
    return ht.stats.representative(data, method="characteristic", **kwargs)


def value(result, group=0):
    return result.groups[group]["value"]


# --- Criterion 1: required inputs, and no input of another method ---------------


@pytest.mark.parametrize("missing", ["method", "side", "distribution"])
def test_the_view_has_no_defaults(missing):
    kwargs = {"method": "characteristic", "side": "low", "distribution": "normal"}
    kwargs.pop(missing)
    with pytest.raises(HangtuError, match=rf"needs {missing}=.*Example: method="):
        ht.stats.representative(COHESION, estimate="mean", **kwargs)


def test_the_estimate_is_required():
    with pytest.raises(HangtuError, match=r"needs estimate=.*Example: "):
        characteristic(COHESION)


@pytest.mark.parametrize(
    ("given", "message"),
    [
        ({"method": "median"}, "doesn't know method='median'"),
        ({"side": "lower"}, "doesn't know side='lower'"),
        ({"distribution": "gamma"}, "doesn't know distribution='gamma'"),
        ({"estimate": "type_a"}, "doesn't know estimate='type_a'"),
        ({"trend": "time"}, "doesn't know trend='time'"),
    ],
)
def test_unknown_choices_are_errors(given, message):
    kwargs = {
        "method": "characteristic",
        "side": "low",
        "distribution": "normal",
        "estimate": "mean",
        **given,
    }
    with pytest.raises(HangtuError, match=message):
        ht.stats.representative(COHESION, **kwargs)


@pytest.mark.parametrize(
    "given",
    [
        {"scale_of_fluctuation": 1.0, "failure_length": 10.0},
        {"sensitivity_index": 0.3},
    ],
)
def test_type_c_inputs_only_with_the_intermediate_estimate(given):
    with pytest.raises(HangtuError, match='only with estimate="intermediate"'):
        characteristic(COHESION, estimate="fractile", **given)


@pytest.mark.parametrize(
    ("given", "message"),
    [
        ({}, "needs scale_of_fluctuation= and failure_length="),
        ({"scale_of_fluctuation": 1.0}, "needs failure_length="),
        (
            {"sensitivity_index": 0.3, "failure_length": 10.0},
            "either as sensitivity_index= or",
        ),
        ({"sensitivity_index": 1.5}, "from 0 to 1, not 1.5"),
        ({"scale_of_fluctuation": 0, "failure_length": 10.0}, "above 0"),
        ({"scale_of_fluctuation": True, "failure_length": 10.0}, "is a number"),
    ],
)
def test_type_c_inputs_are_checked(given, message):
    with pytest.raises(HangtuError, match=message):
        characteristic(COHESION, estimate="intermediate", **given)


def test_an_assumed_coefficient_of_variation_is_above_zero():
    with pytest.raises(HangtuError, match="above 0"):
        characteristic(COHESION, estimate="mean", coefficient_of_variation=-0.1)


@pytest.mark.parametrize(
    ("given", "message"),
    [
        ({"estimate": "mean", "coefficient_of_variation": 0.4}, "not with coeff"),
        (
            {"estimate": "intermediate", "sensitivity_index": 0.3},
            "beyond its scope",
        ),
    ],
)
def test_a_trend_takes_neither_an_assumed_v_x_nor_type_c(given, message):
    with pytest.raises(HangtuError, match=message):
        characteristic(cohesion(), value="effective_cohesion", trend="depth", **given)


# --- Criterion 2: Type A against the JRC's Annexes I and IV ---------------------


def test_g1_type_a_cohesion_assumed_and_computed():
    assumed = characteristic(
        cohesion(),
        value="effective_cohesion",
        estimate="mean",
        coefficient_of_variation=0.40,
    )
    computed = characteristic(cohesion(), value="effective_cohesion", estimate="mean")
    assert value(assumed) == pytest.approx(21.819996403556402, rel=REL)
    assert value(computed) == pytest.approx(14.01238734909873, rel=REL)
    # The JRC's Table 35 prints 21.82 and 14.01.
    assert round(value(assumed), 2) == 21.82
    assert round(value(computed), 2) == 14.01
    statistics = computed.groups[0]["statistics"]
    assert statistics["mean"] == pytest.approx(29.833333333333332, rel=REL)
    assert statistics["standard_deviation"] == pytest.approx(19.23191791441162, rel=REL)
    assert statistics["quantile_factor"] == pytest.approx(stats.t.ppf(0.95, 5))
    assert statistics["sensitivity_index"] == 0
    assert assumed.groups[0]["statistics"]["quantile_factor"] == pytest.approx(
        1.6448536269514722
    )
    assert (
        assumed.coefficient_of_variation_case,
        computed.coefficient_of_variation_case,
    ) == (3, 2)


def test_g2_type_a_friction():
    computed = characteristic(FRICTION, estimate="mean")
    assumed = characteristic(FRICTION, estimate="mean", coefficient_of_variation=0.10)
    assert value(computed) == pytest.approx(0.5000961835051846, rel=REL)
    assert math.degrees(math.atan(value(computed))) == pytest.approx(26.57, abs=0.01)
    # The hand value, not the JRC's 26.86°: their table doesn't follow from
    # their own inputs (spec, G2).
    assert value(assumed) == pytest.approx(0.5130670225303576, rel=REL)


@pytest.mark.parametrize(
    ("values", "expected", "deviation", "coefficient"),
    [
        (CLAY, 2.2090643679673639e-10, 1.213204685400131, 0.5464775901338715),
        (
            CLAY[:9] + CLAY[10:],
            2.2009187278261962e-10,
            0.5903091933730302,
            0.5796812075504562,
        ),
        (PEAT, 4.023745764342306e-10, 0.4828080218815194, 1.6858544608470483),
    ],
    ids=["clay", "clay without test 21", "peat"],
)
def test_g3_type_a_lognormal_permeability(values, expected, deviation, coefficient):
    result = characteristic(values, estimate="mean", distribution="lognormal")
    assert value(result) == pytest.approx(expected, rel=REL)
    statistics = result.groups[0]["statistics"]
    assert math.log(statistics["geometric_standard_deviation"]) == pytest.approx(
        deviation, rel=REL
    )
    assert statistics["statistical_coefficient"] == pytest.approx(coefficient, rel=REL)


def test_hydraulic_conductivity_with_a_normal_distribution_warns():
    frame = ht.set_units(
        pd.DataFrame({"hydraulic_conductivity": CLAY}),
        {"hydraulic_conductivity": "m/s"},
    )
    with (
        pytest.warns(UserWarning, match="Table A.1, note 2"),
        pytest.warns(UserWarning, match="may be lognormal"),
    ):
        characteristic(frame, value="hydraulic_conductivity", estimate="mean")


# --- Criterion 3: Types B and C, both sides -------------------------------------


def test_g4_type_b_computed_below_zero_warns():
    with pytest.warns(UserWarning, match=r"at or below 0.*may be lognormal"):
        result = characteristic(COHESION, estimate="fractile")
    assert value(result) == pytest.approx(-12.02495524673743, rel=REL)


def test_g4_type_b_assumed():
    result = characteristic(COHESION, estimate="fractile", coefficient_of_variation=0.4)
    assert value(result) == pytest.approx(8.632036645373717, rel=REL)


def test_g4_type_c_computed_and_assumed():
    computed = characteristic(COHESION, estimate="intermediate", sensitivity_index=0.3)
    assumed = characteristic(
        COHESION,
        estimate="intermediate",
        scale_of_fluctuation=3.0,
        failure_length=10.0,
        coefficient_of_variation=0.4,
    )
    assert value(computed) == pytest.approx(3.3598271594055404, rel=REL)
    assert value(assumed) == pytest.approx(16.424455956746026, rel=REL)
    assert assumed.sensitivity_index == pytest.approx(0.3)
    assert (assumed.scale_of_fluctuation, assumed.failure_length) == (3.0, 10.0)


def test_theta_over_l_above_one_is_capped_at_the_fractile():
    capped = characteristic(
        COHESION,
        estimate="intermediate",
        scale_of_fluctuation=20.0,
        failure_length=10.0,
        coefficient_of_variation=0.4,
    )
    assert capped.sensitivity_index == 1
    assert value(capped) == pytest.approx(8.632036645373717, rel=REL)
    assert any("θ/L = 2 is above 1, so Γ² = 1" in note for note in capped.notes)


def test_the_high_side_adds():
    result = characteristic(COHESION, estimate="fractile", side="high")
    assert value(result) == pytest.approx(71.69162191340409, rel=REL)


def test_lognormal_type_b_on_both_sides():
    logs = np.log(COHESION)
    k_n = stats.t.ppf(0.95, 5) * math.sqrt(1 + 1 / 6)
    low = characteristic(COHESION, estimate="fractile", distribution="lognormal")
    high = characteristic(
        COHESION, estimate="fractile", distribution="lognormal", side="high"
    )
    assert value(low) == pytest.approx(2.547884302310994, rel=REL)
    assert value(high) == pytest.approx(
        math.exp(logs.mean() + k_n * logs.std(ddof=1)), rel=REL
    )


def test_lognormal_with_v_x_assumed_takes_s_ln_from_it():
    result = characteristic(
        COHESION,
        estimate="mean",
        distribution="lognormal",
        coefficient_of_variation=0.4,
    )
    s_ln = math.sqrt(math.log(1 + 0.4**2))
    expected = math.exp(
        np.log(COHESION).mean() - stats.norm.ppf(0.95) * math.sqrt(1 / 6) * s_ln
    )
    assert value(result) == pytest.approx(expected, rel=REL)


def test_lognormal_leaves_out_values_at_or_below_zero_and_counts_them():
    with pytest.warns(UserWarning, match="left out 1 values .* at or below 0"):
        result = characteristic(
            [0.0, *COHESION], estimate="mean", distribution="lognormal"
        )
    assert result.groups[0]["counts"]["count_not_positive"] == 1
    assert result.groups[0]["counts"]["count"] == 6


# --- Criterion 6, constant: censored values through the ML fit -------------------


def terrace(refusals=True):
    """Five measured N60 and two refusals at 66.7 (field N 50), as in m18a."""
    return pd.DataFrame(
        {
            "geology_unit": ["Terrace"] * 7,
            "spt_n": [9.0, 13.5, 18.75, 23.25, 30.0, 50.0, 50.0],
            "spt_n60": [12.0, 18.0, 25.0, 31.0, 40.0, 66.7, 66.7],
            "spt_refusal": [False] * 5 + [refusals] * 2,
        }
    )


def test_refusals_enter_through_the_censored_ml_fit_and_are_noted():
    result = characteristic(
        terrace(), value="spt_n60", by="geology_unit", estimate="mean"
    )
    values = stats.CensoredData(
        uncensored=[12.0, 18.0, 25.0, 31.0, 40.0], right=[66.7, 66.7]
    )
    location, scale = stats.norm.fit(values)
    k_n = stats.t.ppf(0.95, 6) * math.sqrt(1 / 7)
    assert value(result) == pytest.approx(location - k_n * scale, rel=1e-4)
    counts = result.groups[0]["counts"]
    assert (counts["count"], counts["count_censored"]) == (7, 2)
    assert any(
        "2 of 7 values censored" in note and "assume complete data" in note
        for note in result.notes
    )


def test_refusals_under_their_upper_limit_are_interval_censored():
    result = characteristic(
        terrace(),
        value="spt_n60",
        by="geology_unit",
        estimate="mean",
        spt_refusal_upper_limit=120,
    )
    limit = 120 * 66.7 / 50
    values = stats.CensoredData(
        uncensored=[12.0, 18.0, 25.0, 31.0, 40.0],
        interval=[[66.7, limit], [66.7, limit]],
    )
    location, scale = stats.norm.fit(values)
    k_n = stats.t.ppf(0.95, 6) * math.sqrt(1 / 7)
    assert value(result) == pytest.approx(location - k_n * scale, rel=1e-4)
    assert result.groups[0]["counts"]["count_interval_censored"] == 2
    assert "spt_refusal_upper_limit" in result.judgments


def test_without_censoring_the_sample_statistics_are_used():
    result = characteristic(
        terrace(refusals=False),
        value="spt_n60",
        estimate="mean",
    )
    values = np.array([12.0, 18.0, 25.0, 31.0, 40.0, 66.7, 66.7])
    k_n = stats.t.ppf(0.95, 6) * math.sqrt(1 / 7)
    assert value(result) == pytest.approx(
        values.mean() - k_n * values.std(ddof=1), rel=REL
    )
    assert not any("censored" in note for note in result.notes)


def test_counts_add_up_to_the_groups_rows():
    frame = pd.DataFrame(
        {
            "geology_unit": ["Clay"] * 6 + ["Sand"] * 4,
            "plasticity_index": [20.0, 25.0, None, "NP", 30.0, 22.0, 5, 6, 7, 8],
        }
    )
    result = characteristic(
        frame, value="plasticity_index", by="geology_unit", estimate="mean"
    )
    table = result.to_frame()
    counted = table[
        ["count", "count_non_plastic", "count_text", "count_blank", "count_range"]
    ].sum(axis=1)
    assert counted.tolist() == [6, 4]


def test_a_group_with_one_value_has_no_value_with_the_reason():
    frame = pd.DataFrame(
        {
            "geology_unit": ["Clay", "Clay", "Clay", "Sand"],
            "plasticity_index": [20, 25, 30, 9],
        }
    )
    result = characteristic(
        frame, value="plasticity_index", by="geology_unit", estimate="mean"
    )
    sand = result.to_frame().set_index("geology_unit").loc["Sand"]
    assert math.isnan(sand["value"])
    assert sand["reason"] == "fewer than 2 values (1)"
    assert "Sand: no value, fewer than 2 values (1)." in result.notes
