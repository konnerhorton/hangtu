"""ht.analysis.triaxial_failure_stresses() (docs/work/m11a-triaxial-data.md, AC 10).

Golden values are AC 1's CU stage and AC 2's CDM stages, by hand: σ3 is the
cell pressure, σ1 = σ3 + q_f, σ′3 = σ3 - u_f and σ′1 = σ′3 + q_f.
"""

import warnings

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError, UnitsError

#: 1 psf in kPa: 0.45359237 kg × 9.80665 m/s² / 0.3048² m² (exact).
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000
STRESSES = [
    "cell_pressure",
    "back_pressure",
    "deviator_stress_at_failure",
    "pore_pressure_at_failure",
]
PRINCIPAL = [
    "minor_principal_stress_at_failure",
    "major_principal_stress_at_failure",
    "effective_minor_principal_stress_at_failure",
    "effective_major_principal_stress_at_failure",
]


def _stages(unit="kPa", factor=1.0, **columns):
    """AC 1's CU stage and AC 2's three CDM stages, in ``unit`` (kPa × factor)."""
    data = {
        "test_type": ["CU", "CDM", "CDM", "CDM"],
        "test_stage": ["1", "1", "2", "3"],
        "cell_pressure": [400, 400, 500, 700],
        "back_pressure": [300, 300, 300, 300],
        "deviator_stress_at_failure": [180, 300, 520, 900],
        "pore_pressure_at_failure": [360, 300, np.nan, 300],
    }
    data.update(columns)
    df = pd.DataFrame(data)
    for column in STRESSES:
        if column in df:
            df[column] = df[column] * factor
    return ht.set_units(df, {c: unit for c in STRESSES if c in df})


def _quiet(function, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return function(*args, **kwargs)


def test_golden_values_and_basis():
    with pytest.warns(UserWarning, match=r"^1 drained stage had no pore_pressure"):
        result = ht.analysis.triaxial_failure_stresses(_stages())
    assert result["minor_principal_stress_at_failure"].tolist() == [400, 400, 500, 700]
    assert result["major_principal_stress_at_failure"].tolist() == [
        580,
        700,
        1020,
        1600,
    ]
    effective_minor = result["effective_minor_principal_stress_at_failure"]
    effective_major = result["effective_major_principal_stress_at_failure"]
    assert effective_minor.tolist() == [40, 100, 200, 400]
    assert effective_major.tolist() == [220, 400, 720, 1300]
    assert result["effective_stress_basis"].tolist() == [
        "pore_pressure_at_failure",
        "pore_pressure_at_failure",
        "back_pressure",
        "pore_pressure_at_failure",
    ]
    assert all(result.attrs["units"][column] == "kPa" for column in PRINCIPAL)


def test_returns_a_copy_in_the_same_order():
    df = _stages()
    result = _quiet(ht.analysis.triaxial_failure_stresses, df)
    assert list(result.columns) == [*df.columns, *PRINCIPAL, "effective_stress_basis"]
    assert result.index.equals(df.index)
    assert "minor_principal_stress_at_failure" not in df


def test_psf_comes_back_in_psf():
    result = _quiet(ht.analysis.triaxial_failure_stresses, _stages("psf", 1 / PSF))
    assert result.attrs["units"]["effective_minor_principal_stress_at_failure"] == "psf"
    expected = np.array([40, 100, 200, 400]) / PSF  # 835.4174 psf for 40 kPa
    assert result["effective_minor_principal_stress_at_failure"].to_numpy() == (
        pytest.approx(expected, rel=1e-9)
    )
    assert result["effective_minor_principal_stress_at_failure"].iloc[0] == (
        pytest.approx(835.4174, rel=1e-6)
    )


def test_mixed_stress_units_convert_to_the_cell_pressure_unit():
    df = _stages()
    df["pore_pressure_at_failure"] = df["pore_pressure_at_failure"] / PSF
    df.attrs["units"]["pore_pressure_at_failure"] = "psf"
    result = _quiet(ht.analysis.triaxial_failure_stresses, df)
    effective_minor = result["effective_minor_principal_stress_at_failure"]
    assert effective_minor.tolist() == pytest.approx([40, 100, 200, 400], rel=1e-9)


def test_units_argument_beats_attrs():
    df = _stages()
    df.attrs["units"] = {}
    result = _quiet(
        ht.analysis.triaxial_failure_stresses, df, units=dict.fromkeys(STRESSES, "kPa")
    )
    assert result["effective_minor_principal_stress_at_failure"].iloc[0] == 40


def test_without_pore_pressure_gives_total_stresses_only():
    # A UU set: cell 100, 200, 300 and q_f 120, 124, 118 kPa (AC 3).
    df = ht.set_units(
        pd.DataFrame(
            {
                "test_type": ["UU"] * 3,
                "cell_pressure": [100, 200, 300],
                "deviator_stress_at_failure": [120, 124, 118],
            }
        ),
        {"cell_pressure": "kPa", "deviator_stress_at_failure": "kPa"},
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = ht.analysis.triaxial_failure_stresses(df)
    assert result["major_principal_stress_at_failure"].tolist() == [220, 324, 418]
    assert result["effective_minor_principal_stress_at_failure"].isna().all()
    assert result["effective_stress_basis"].isna().all()


def test_undrained_without_pore_pressure_is_blank_not_back_pressure():
    df = _stages(pore_pressure_at_failure=[np.nan, 300, 300, 300])
    result = ht.analysis.triaxial_failure_stresses(df)
    assert np.isnan(result["effective_minor_principal_stress_at_failure"].iloc[0])
    assert result["effective_stress_basis"].iloc[0] is None
    assert result["minor_principal_stress_at_failure"].iloc[0] == 400


def test_extension_rows_are_blank_with_a_warning():
    df = _stages(
        test_type=["CU", "CIDE", "CDM", "CDM"],
        pore_pressure_at_failure=[360, 300, 300, 300],
    )
    with pytest.warns(UserWarning, match=r"Rows 1 are extension tests \(CIDE\)"):
        result = ht.analysis.triaxial_failure_stresses(df)
    assert result.loc[1, PRINCIPAL].isna().all()
    assert result["effective_stress_basis"].iloc[1] is None
    assert result["effective_minor_principal_stress_at_failure"].iloc[0] == 40


def test_deviator_stress_of_zero_names_the_rows():
    df = _stages(deviator_stress_at_failure=[0, 300, -5, 900])
    with pytest.raises(HangtuError, match=r"Rows 0, 2 have a deviator_stress"):
        ht.analysis.triaxial_failure_stresses(df)


def test_missing_cell_pressure_column():
    df = _stages().drop(columns="cell_pressure")
    with pytest.raises(ColumnError, match=r"no column 'cell_pressure'"):
        ht.analysis.triaxial_failure_stresses(df)


def test_pore_pressure_in_a_length_unit():
    df = _stages()
    df.attrs["units"]["pore_pressure_at_failure"] = "m"
    with pytest.raises(UnitsError, match=r"'pore_pressure_at_failure' is a stress"):
        ht.analysis.triaxial_failure_stresses(df)


def test_stress_without_units():
    df = _stages()
    del df.attrs["units"]["deviator_stress_at_failure"]
    with pytest.raises(UnitsError, match=r"'deviator_stress_at_failure' has no units"):
        ht.analysis.triaxial_failure_stresses(df)
