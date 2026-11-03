"""Every SPT correlation rises with its N input (docs/work/m18a-refusals.md, AC 9).

A bound at the range's end, or at a refusal's N, is a bound of the estimate at
the row's true N only because the estimate is non-decreasing in N with the
other inputs fixed. This checks that for each correlation, across its range and
beyond it, where ``bound()`` holds N at the range's end.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import hangtu as ht
from hangtu.analysis import correlations
from hangtu.analysis.correlations import _framework

STRESS = {"effective_vertical_stress": "kPa"}
BAND = ("undrained_shear_strength_lower", "undrained_shear_strength_upper")


def _frame(column, n, **others):
    df = pd.DataFrame({column: n, **{key: [v] * len(n) for key, v in others.items()}})
    return ht.set_units(df, STRESS) if "effective_vertical_stress" in others else df


# name: (N column, other inputs fixed, call kwargs, columns compared)
CASES = {
    "effective_friction_angle_hatanaka_uchida_1996": (
        "spt_n1_60",
        {},
        {},
        ("effective_friction_angle",),
    ),
    "effective_friction_angle_kulhawy_mayne_1990": (
        "spt_n60",
        {"effective_vertical_stress": 120.0},
        {},
        ("effective_friction_angle",),
    ),
    "undrained_shear_strength_terzaghi_peck_1967": ("spt_n", {}, {}, BAND),
    "undrained_shear_strength_stroud_1974": (
        "spt_n60",
        {"plasticity_index": 20.0},
        {},
        BAND,
    ),
    "preconsolidation_stress_mayne_kemper_1988": (
        "spt_n",
        {},
        {},
        ("preconsolidation_stress",),
    ),
    "overconsolidation_ratio_mayne_kemper_1988": (
        "spt_n",
        {"effective_vertical_stress": 60.0},
        {},
        ("overconsolidation_ratio",),
    ),
    "at_rest_earth_pressure_coefficient_kulhawy_et_al_1989": (
        "spt_n",
        {"effective_vertical_stress": 60.0},
        {},
        ("at_rest_earth_pressure_coefficient",),
    ),
    "drained_youngs_modulus_aashto_2004": (
        "spt_n1_60",
        {},
        {"soil": "silts"},
        ("drained_youngs_modulus",),
    ),
    "drained_youngs_modulus_kulhawy_mayne_1990": (
        "spt_n60",
        {},
        {"soil": "sands_with_fines"},
        ("drained_youngs_modulus",),
    ),
    "shear_wave_velocity_imai_tonouchi_1982": (
        "spt_n60",
        {},
        {},
        ("shear_wave_velocity",),
    ),
    "shear_wave_velocity_ohta_goto_1978": (
        "spt_n60",
        {},
        {},
        ("shear_wave_velocity",),
    ),
}


def test_every_spt_correlation_is_checked():
    assert set(CASES) == set(_framework.catalog())
    for name, (column, *_) in CASES.items():
        bound_by = _framework.entry(name)["bound_by"]
        assert bound_by in (column, "normalized_n"), name
        assert "spt_n" in column


@pytest.mark.filterwarnings("ignore:.*gave (a bound|no estimate)")
@pytest.mark.parametrize("name", list(CASES))
@settings(max_examples=60, deadline=None)
@given(
    low=st.floats(0.01, 1000.0),
    step=st.floats(0.0, 1000.0),
    refusal=st.booleans(),
)
def test_the_estimate_is_non_decreasing_in_n(name, low, step, refusal):
    column, others, kwargs, targets = CASES[name]
    df = _frame(column, [low, low + step], **others)
    df["spt_refusal"] = [refusal, refusal]
    out = getattr(correlations, name)(df, display_units="SI", **kwargs)
    for target in targets:
        lower_n, higher_n = out[target].to_numpy(dtype=float)
        if np.isnan(lower_n) or np.isnan(higher_n):
            continue
        assert lower_n <= higher_n * (1 + 1e-12), (target, low, low + step)
