"""E and Vs from SPT (docs/work/m13b3-spt-stiffness.md, AC 1 to 5)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.analysis import correlations

# By hand: 1 tsf = 2000 lbf/ft² = 2000 x 4.44822 N / 0.3048² m² = 95.7605 kPa,
# and 2 ksf; 1 ksf = 47.8803 kPa. pa = 100 kPa.
TSF = 95.7605

# --- AC 1: E golden values ------------------------------------------------------------

AASHTO = [
    # (soil row, (N1)60, E in kPa, E in ksf)
    ("clean_fine_to_medium_sands", 20.0, 13406.5, 280.0),
    ("silts", 10.0, 3830.4, 80.0),
    ("coarse_sands", 10.0, 9576.1, 200.0),
    ("gravels", 10.0, 11491.3, 240.0),
]
KULHAWY_MAYNE = [
    # (soil row, N60, E in kPa)
    ("clean_normally_consolidated_sands", 20.0, 20000.0),
    ("sands_with_fines", 10.0, 5000.0),
    ("clean_overconsolidated_sands", 10.0, 15000.0),
]


@pytest.mark.parametrize(("soil", "n1_60", "kpa", "ksf"), AASHTO)
def test_aashto_golden_values(soil, n1_60, kpa, ksf):
    df = pd.DataFrame({"spt_n1_60": [n1_60]})
    si = correlations.drained_youngs_modulus_aashto_2004(
        df, soil=soil, display_units="SI"
    )
    us = correlations.drained_youngs_modulus_aashto_2004(
        df, soil=soil, display_units="US"
    )
    assert si["drained_youngs_modulus"].iloc[0] == pytest.approx(kpa / 1000, rel=1e-4)
    assert us["drained_youngs_modulus"].iloc[0] == pytest.approx(ksf, rel=1e-4)
    assert si.attrs["units"]["drained_youngs_modulus"] == "MPa"
    assert us.attrs["units"]["drained_youngs_modulus"] == "ksf"
    assert si["correlation_soil"].iloc[0] == soil


def test_aashto_constants_are_tsf_not_ksf():
    # The unit trap: 7 x 20 = 140 tsf is 13 406 kPa; read as ksf it would be 6 703.
    out = correlations.drained_youngs_modulus_aashto_2004(
        pd.DataFrame({"spt_n1_60": [20.0]}),
        soil="clean_fine_to_medium_sands",
        display_units="SI",
    )
    assert out["drained_youngs_modulus"].iloc[0] == pytest.approx(140 * TSF / 1000)
    assert out["drained_youngs_modulus"].iloc[0] != pytest.approx(6.703, rel=0.01)


@pytest.mark.parametrize(("soil", "n60", "kpa"), KULHAWY_MAYNE)
def test_kulhawy_mayne_golden_values(soil, n60, kpa):
    out = correlations.drained_youngs_modulus_kulhawy_mayne_1990(
        pd.DataFrame({"spt_n60": [n60]}), soil=soil, display_units="SI"
    )
    assert out["drained_youngs_modulus"].iloc[0] == pytest.approx(kpa / 1000)


def test_kulhawy_mayne_in_us_units():
    # 20 000 kPa / 47.8803 = 417.7 ksf.
    out = correlations.drained_youngs_modulus_kulhawy_mayne_1990(
        pd.DataFrame({"spt_n60": [20.0]}),
        soil="clean_normally_consolidated_sands",
        display_units="US",
    )
    assert out["drained_youngs_modulus"].iloc[0] == pytest.approx(417.71, rel=1e-4)


@pytest.mark.parametrize(
    ("function", "column"),
    [
        (correlations.drained_youngs_modulus_aashto_2004, "spt_n1_60"),
        (correlations.drained_youngs_modulus_kulhawy_mayne_1990, "spt_n60"),
    ],
)
def test_e_gives_no_estimate_at_zero_n_or_a_refusal(function, column):
    df = pd.DataFrame(
        {column: [0.0, 15.0, np.nan], "spt_refusal": [False, True, False]}
    )
    soil = next(iter(correlations.describe(function.__name__)["rows"]))
    with pytest.warns(UserWarning, match=r"3 of 3 rows \(1 input blank, 1 refusal, 1"):
        out = function(df, soil=soil)
    assert out["correlation_note"].tolist() == ["below range", "refusal", "input blank"]
    assert out["drained_youngs_modulus"].isna().all()


# --- AC 3: the input ------------------------------------------------------------------


def test_aashto_given_n60_only_raises_naming_n1_60():
    with pytest.raises(ht.ColumnError, match=r"spt_n1_60.*spt_n1_60\(df"):
        correlations.drained_youngs_modulus_aashto_2004(
            pd.DataFrame({"spt_n60": [10.0]}), soil="silts"
        )


def test_kulhawy_mayne_without_n60_raises():
    with pytest.raises(ht.ColumnError, match=r"spt_n60"):
        correlations.drained_youngs_modulus_kulhawy_mayne_1990(
            pd.DataFrame({"spt_n": [10.0]}), soil="sands_with_fines"
        )


# --- AC 4 and 5: the soil row ---------------------------------------------------------


def test_e_without_soil_raises_listing_the_source_rows():
    with pytest.raises(ht.HangtuError, match=r"soil= is required.*'gravels' \(Sandy"):
        correlations.drained_youngs_modulus_aashto_2004(
            pd.DataFrame({"spt_n1_60": [10.0]})
        )


def test_by_geology_unit_with_the_uscs_check():
    df = pd.DataFrame(
        {
            "spt_n1_60": [10.0, 10.0, 10.0],
            "geology_unit": ["Terrace", "Terrace", "Gravel"],
            "uscs_symbol": ["SP", "GP", "GW"],
        }
    )
    soil = {"Terrace": "clean_fine_to_medium_sands", "Gravel": "gravels"}
    with pytest.warns(UserWarning, match=r"1 of 3 rows \(1 not for this soil"):
        out = correlations.drained_youngs_modulus_aashto_2004(
            df, soil=soil, uscs="proposed", display_units="SI"
        )
    assert out["correlation_note"].tolist() == [None, "not for this soil", None]
    assert out["drained_youngs_modulus"].tolist() == pytest.approx(
        [70 * TSF / 1000, np.nan, 120 * TSF / 1000], nan_ok=True
    )
    assert out["correlation_soil"].tolist() == [
        "clean_fine_to_medium_sands",
        "clean_fine_to_medium_sands",
        "gravels",
    ]


# --- AC 2: Vs golden values -----------------------------------------------------------

# By hand: 10^0.31 = 2.0417, 30^0.31 = 2.8702, 10^0.35 = 2.2387; 1 ft = 0.3048 m.
VS = [
    # (function, N60, Vs in m/s, Vs in ft/s)
    ("shear_wave_velocity_imai_tonouchi_1982", 10.0, 191.31, 627.66),
    ("shear_wave_velocity_imai_tonouchi_1982", 30.0, 268.93, 882.33),
    ("shear_wave_velocity_ohta_goto_1978", 10.0, 183.80, 603.02),
]


@pytest.mark.parametrize(("name", "n60", "si", "us"), VS)
def test_vs_golden_values(name, n60, si, us):
    function = getattr(correlations, name)
    df = pd.DataFrame({"spt_n60": [n60]})
    metric = function(df, display_units="SI")["shear_wave_velocity"].iloc[0]
    assert metric == pytest.approx(si, rel=1e-4)
    out = function(df, display_units="US")
    assert out["shear_wave_velocity"].iloc[0] == pytest.approx(us, rel=1e-4)
    assert out.attrs["units"]["shear_wave_velocity"] == "ft/s"


@pytest.mark.parametrize(
    ("name", "a", "b"),
    [
        ("shear_wave_velocity_imai_tonouchi_1982", 97.0, 0.31),
        ("shear_wave_velocity_ohta_goto_1978", 85.3, 0.35),
    ],
)
def test_vs_agrees_with_the_source_on_uncorrected_n(name, a, b):
    # Wair et al.'s 60 % form against the source's equation on N = N60 x 60/67.
    out = getattr(correlations, name)(
        pd.DataFrame({"spt_n60": [10.0]}), display_units="SI"
    )
    assert out["shear_wave_velocity"].iloc[0] == pytest.approx(
        a * (10.0 * 60 / 67) ** b, rel=1e-3
    )


@pytest.mark.parametrize(
    ("name", "n60", "notes"),
    [
        (
            "shear_wave_velocity_imai_tonouchi_1982",
            [0.0, 0.5, 447.0, 450.0],
            ["below range", None, None, "above range"],
        ),
        (
            "shear_wave_velocity_ohta_goto_1978",
            [2.0, 2.23, 223.0, 224.0],
            ["below range", None, None, "above range"],
        ),
    ],
)
def test_vs_range_is_the_sources_n_at_67_percent(name, n60, notes):
    with pytest.warns(UserWarning, match=r"Its range is .*N60 ≤ "):
        out = getattr(correlations, name)(pd.DataFrame({"spt_n60": n60}))
    assert out["correlation_note"].tolist() == notes


# --- AC 5: Vs and soil type -----------------------------------------------------------


def test_vs_has_no_proposed_groups_but_takes_a_list():
    df = pd.DataFrame({"spt_n60": [10.0, 10.0], "uscs_symbol": ["SP", "PT"]})
    with pytest.raises(ht.HangtuError, match=r"for all soils"):
        correlations.shear_wave_velocity_imai_tonouchi_1982(df, uscs="proposed")
    with pytest.warns(UserWarning, match=r"1 not for this soil"):
        out = correlations.shear_wave_velocity_imai_tonouchi_1982(df, uscs=["SP"])
    assert out["correlation_note"].tolist() == [None, "not for this soil"]
