"""σ′p, OCR and K0 from SPT (docs/work/m13b2-spt-strength-history.md, AC 2, 3)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.analysis import correlations

NAN = np.nan
KPA_TO_PSF = 1000 / 47.880259

# AC 2, by hand with pa = 100 kPa: σ′p = 0.47 N pa; OCR = 0.58 N pa/σ′v0;
# K0 = 0.073 N pa/σ′v0. Ranges: 0.5 ≤ N ≤ 200; 1 ≤ N pa/σ′v0 ≤ 100 (OCR);
# 0 < N pa/σ′v0 ≤ 60 (K0).
# (N, σ′v0 kPa, σ′p kPa, OCR, K0)
GOLDEN = [
    (10, 100.0, 470.0, 5.80, 0.730),
    (10, 50.0, 470.0, 11.6, 1.460),
    (20, 50.0, 940.0, 23.2, 2.920),
    (30, 50.0, 1410.0, 34.8, 4.380),  # N pa/σ′v0 = 60, inside K0's range
    (31, 50.0, 1457.0, 35.96, NAN),  # 62: above K0's range
    (30, 20.0, 1410.0, NAN, NAN),  # 150: above both
]


def golden_frame(unit="kPa", factor=1.0):
    n, stress, *_ = zip(*GOLDEN, strict=True)
    df = pd.DataFrame(
        {"spt_n": n, "effective_vertical_stress": [s * factor for s in stress]}
    )
    return ht.set_units(df, {"effective_vertical_stress": unit})


def column(index):
    return [row[index] for row in GOLDEN]


def test_preconsolidation_stress_golden_values():
    out = correlations.preconsolidation_stress_mayne_kemper_1988(
        golden_frame(), display_units="SI"
    )
    assert out["preconsolidation_stress"].tolist() == pytest.approx(column(2))
    assert out.attrs["units"]["preconsolidation_stress"] == "kPa"


def test_preconsolidation_stress_in_us_units():
    out = correlations.preconsolidation_stress_mayne_kemper_1988(
        golden_frame(), display_units="US"
    )
    expected = [value * KPA_TO_PSF for value in column(2)]
    assert out["preconsolidation_stress"].tolist() == pytest.approx(expected)


def test_overconsolidation_ratio_golden_values():
    with pytest.warns(UserWarning, match=r"1 of 6 rows \(1 above range"):
        out = correlations.overconsolidation_ratio_mayne_kemper_1988(golden_frame())
    assert out["overconsolidation_ratio"].tolist() == pytest.approx(
        column(3), nan_ok=True
    )
    assert out["correlation_note"].tolist() == [None] * 5 + ["above range"]
    assert "overconsolidation_ratio" not in out.attrs["units"]


def test_k0_golden_values():
    with pytest.warns(UserWarning, match=r"2 of 6 rows \(2 above range"):
        out = correlations.at_rest_earth_pressure_coefficient_kulhawy_et_al_1989(
            golden_frame()
        )
    assert out["at_rest_earth_pressure_coefficient"].tolist() == pytest.approx(
        column(4), nan_ok=True
    )


def test_k0_warning_names_the_range_in_the_users_terms():
    with pytest.warns(UserWarning) as caught:
        correlations.at_rest_earth_pressure_coefficient_kulhawy_et_al_1989(
            golden_frame()
        )
    assert str(caught[0].message).endswith(
        "Its range is σ′v0 > 0 kPa; 0 < N pa/σ′v0 ≤ 60; outside it the estimate "
        "is blank, never extrapolated."
    )


@pytest.mark.parametrize(
    "name, target",
    [
        ("overconsolidation_ratio_mayne_kemper_1988", "overconsolidation_ratio"),
        (
            "at_rest_earth_pressure_coefficient_kulhawy_et_al_1989",
            "at_rest_earth_pressure_coefficient",
        ),
    ],
)
def test_stress_in_psf_gives_the_same_values(name, target):
    function = getattr(correlations, name)
    with pytest.warns(UserWarning):
        si = function(golden_frame())
    with pytest.warns(UserWarning):
        us = function(golden_frame("psf", KPA_TO_PSF))
    assert us[target].tolist() == pytest.approx(si[target].tolist(), nan_ok=True)


def test_preconsolidation_stress_range_is_the_charts_n_axis():
    df = pd.DataFrame({"spt_n": [0.4, 0.5, 200, 201]})
    with pytest.warns(UserWarning, match=r"2 of 4 rows \(1 below range, 1 above"):
        out = correlations.preconsolidation_stress_mayne_kemper_1988(df)
    assert out["correlation_note"].tolist() == [
        "below range",
        None,
        None,
        "above range",
    ]


def test_zero_stress_is_below_range_not_infinite():
    df = ht.set_units(
        pd.DataFrame({"spt_n": [10, 10], "effective_vertical_stress": [0.0, -5.0]}),
        {"effective_vertical_stress": "kPa"},
    )
    with pytest.warns(UserWarning, match=r"2 of 2 rows \(2 below range"):
        out = correlations.overconsolidation_ratio_mayne_kemper_1988(df)
    assert out["overconsolidation_ratio"].isna().all()


def test_ocr_below_one_normalized_is_below_range():
    df = ht.set_units(
        pd.DataFrame({"spt_n": [1], "effective_vertical_stress": [200.0]}),
        {"effective_vertical_stress": "kPa"},
    )
    with pytest.warns(UserWarning, match=r"below range"):
        out = correlations.overconsolidation_ratio_mayne_kemper_1988(df)
    assert out["correlation_note"].tolist() == ["below range"]


# --- AC 3: field N -------------------------------------------------------------------


FIELD_N = [
    "preconsolidation_stress_mayne_kemper_1988",
    "overconsolidation_ratio_mayne_kemper_1988",
    "at_rest_earth_pressure_coefficient_kulhawy_et_al_1989",
]


@pytest.mark.parametrize("name", FIELD_N)
def test_field_n_correlations_raise_without_spt_n(name):
    df = ht.set_units(
        pd.DataFrame({"spt_n60": [10.0], "effective_vertical_stress": [50.0]}),
        {"effective_vertical_stress": "kPa"},
    )
    with pytest.raises(ht.HangtuError, match=r"'spt_n'"):
        getattr(correlations, name)(df)


@pytest.mark.parametrize("name", FIELD_N[1:])
def test_ocr_and_k0_raise_without_stress_naming_vertical_stress(name):
    with pytest.raises(
        ht.HangtuError, match=r"effective_vertical_stress.*vertical_stress\(\)"
    ):
        getattr(correlations, name)(pd.DataFrame({"spt_n": [10.0]}))
