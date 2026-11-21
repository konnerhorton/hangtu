"""ht.analysis.oedometer_increments() (docs/work/m19c-consolidation.md, Spec AC 1-11).

Golden values are the spec's, hand-calculated on BH1-U3 (site_si.ags):
m_v = 1000 Δe / ((1 + e1) Δσ′) m²/MN with e1 at the increment's start
(BS 1377-5:1990, 3.6.2.2.4), E = 1/m_v in kPa.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError

DATA = Path(__file__).parents[1] / "data" / "ags"
REL = 1e-9
#: 1 m²/MN in ft²/kip, and 1 kPa in psf, from 1 ft = 0.3048 m and
#: 1 lbf = 4.4482216152605 N (exact).
FT2_PER_KIP = 0.3048**2 / (1000 * 4.4482216152605) * 1e6
PSF = 4.4482216152605 / 0.3048**2 / 1000

FIRST = "first increment: its start stress isn't given"

#: BH1-U3, AC table: (branch, σ′1, m_v m²/MN, Eoed kPa, Eur,oed kPa).
TABLE = [
    ("loading", np.nan, np.nan, np.nan, np.nan),
    ("loading", 25, 0.155988858, 6410.71429, np.nan),
    ("loading", 50, 0.134228188, 7450, np.nan),
    ("loading", 100, 0.157657658, 6342.85714, np.nan),
    ("loading", 200, 0.165903890, 6027.58621, np.nan),
    ("loading", 400, 0.115384615, 8666.66667, np.nan),
    ("unloading", 800, 0.0134408602, np.nan, 74400),
    ("unloading", 200, 0.0533333333, np.nan, 18750),
    ("reloading", 50, 0.0325600326, np.nan, 30712.5),
    ("reloading", 200, 0.0224948875, np.nan, 44454.5455),
    ("loading", 800, 0.0684079602, 14618.1818, np.nan),
    ("unloading", 1600, 0.00986842105, np.nan, 101333.333),
]
#: The table's values are written to 9 significant figures.
TABLE_REL = 1e-8


def _project(name, system, tmp_path_factory):
    return ht.Project.from_ags(
        DATA / f"{name}.ags",
        db=tmp_path_factory.mktemp(name) / f"{name}.sqlite",
        overwrite=True,
        display_units=system,
    )


@pytest.fixture(scope="module")
def site_si(tmp_path_factory):
    return _project("site_si", "SI", tmp_path_factory).oedometer()


@pytest.fixture(scope="module")
def site_us(tmp_path_factory):
    return _project("site_us", "US", tmp_path_factory).oedometer()


@pytest.fixture(scope="module")
def bh1_u3(site_si):
    return ht.analysis.oedometer_increments(site_si)


def _frame(stresses, void_ratios, specimen="S1", start=None):
    df = pd.DataFrame(
        {
            "specimen_id": [specimen] * len(stresses),
            "applied_vertical_stress": np.array(stresses, dtype=float),
            "void_ratio_at_increment_end": np.array(void_ratios, dtype=float),
        }
    )
    if start is not None:
        df["void_ratio_at_increment_start"] = np.array(start, dtype=float)
    df.attrs["units"] = {"applied_vertical_stress": "kPa"}
    return df


def _with_in_situ(df, value, unit="kPa"):
    out = df.copy()
    out["effective_vertical_stress"] = value
    out.attrs["units"] = {**df.attrs["units"], "effective_vertical_stress": unit}
    return out


def _notes(df):
    return df.attrs["oedometer_increments"]["notes"]


# --- AC 1: increments ---------------------------------------------------------


def test_ac1_stress_at_start(bh1_u3):
    expected = [row[1] for row in TABLE]
    np.testing.assert_allclose(
        bh1_u3["applied_vertical_stress_at_increment_start"], expected, rtol=REL
    )
    assert bh1_u3.attrs["units"]["applied_vertical_stress_at_increment_start"] == "kPa"


def test_ac1_volume_compressibility(bh1_u3):
    expected = [row[2] for row in TABLE]
    np.testing.assert_allclose(
        bh1_u3["coefficient_of_volume_compressibility"], expected, rtol=TABLE_REL
    )
    assert bh1_u3.attrs["units"]["coefficient_of_volume_compressibility"] == "m2/MN"
    # Increment 2 exactly: 0.007 / (1.795 × 25) × 1000.
    assert bh1_u3["coefficient_of_volume_compressibility"].iloc[1] == pytest.approx(
        7 / (1.795 * 25), rel=REL
    )


def test_ac1_moduli_on_their_branches(bh1_u3):
    assert list(bh1_u3["load_branch"]) == [row[0] for row in TABLE]
    np.testing.assert_allclose(
        bh1_u3["constrained_modulus"], [row[3] for row in TABLE], rtol=TABLE_REL
    )
    np.testing.assert_allclose(
        bh1_u3["unload_reload_constrained_modulus"],
        [row[4] for row in TABLE],
        rtol=TABLE_REL,
    )
    assert bh1_u3["constrained_modulus"].iloc[2] == pytest.approx(7450, rel=REL)
    assert bh1_u3["unload_reload_constrained_modulus"].iloc[7] == pytest.approx(
        18750, rel=REL
    )
    assert bh1_u3.attrs["units"]["constrained_modulus"] == "kPa"


def test_ac1_reasons(bh1_u3):
    reasons = bh1_u3["coefficient_of_volume_compressibility_reason"]
    assert reasons.iloc[0] == FIRST
    assert reasons.iloc[1:].isna().all()
    modulus = bh1_u3["constrained_modulus_reason"]
    assert modulus.iloc[0] == FIRST
    assert modulus.iloc[1:].isna().all()


def test_ac1_keeps_rows_and_columns(site_si, bh1_u3):
    assert list(bh1_u3.columns[: len(site_si.columns)]) == list(site_si.columns)
    assert bh1_u3.index.equals(site_si.index)
    assert "coefficient_of_volume_compressibility" not in site_si.columns


# --- AC 3: US display ---------------------------------------------------------


def test_ac3_us_display(site_si):
    us = ht.analysis.oedometer_increments(site_si, display_units="US")
    row = us.iloc[3]
    assert row["coefficient_of_volume_compressibility"] == pytest.approx(
        0.00754868948, rel=1e-6
    )
    assert row["constrained_modulus"] == pytest.approx(132.473326, rel=1e-6)
    assert row["applied_vertical_stress_at_increment_start"] == pytest.approx(
        2088.54342, rel=1e-6
    )
    assert row["applied_vertical_stress"] == pytest.approx(200 / PSF, rel=REL)
    units = us.attrs["units"]
    assert units["coefficient_of_volume_compressibility"] == "ft²/kip"
    assert units["constrained_modulus"] == "ksf"
    assert units["applied_vertical_stress"] == "psf"
    assert units["applied_vertical_stress_at_increment_start"] == "psf"


def test_ac3_si_display_writes_moduli_in_mpa(site_si):
    si = ht.analysis.oedometer_increments(site_si, display_units="SI")
    assert si["constrained_modulus"].iloc[2] == pytest.approx(7.45, rel=REL)
    assert si.attrs["units"]["constrained_modulus"] == "MPa"


# --- AC 4: σ′v0 ---------------------------------------------------------------


@pytest.mark.parametrize(("in_situ", "rows"), [(80.0, [2, 7]), (150.0, [3, 7])])
def test_ac4_increments_spanning_in_situ(site_si, in_situ, rows):
    result = ht.analysis.oedometer_increments(_with_in_situ(site_si, in_situ))
    spans = result["spans_effective_vertical_stress"]
    assert str(spans.dtype) == "boolean"
    assert list(np.flatnonzero(spans.to_numpy(dtype=bool))) == rows
    assert not any("spans the" in note for note in _notes(result))


def test_ac4_in_situ_below_every_increment(site_si):
    result = ht.analysis.oedometer_increments(_with_in_situ(site_si, 20.0))
    assert not result["spans_effective_vertical_stress"].any()
    assert result["spans_effective_vertical_stress"].notna().all()
    (note,) = [n for n in _notes(result) if "spans the" in n]
    assert "BH1-U3" in note
    assert "nothing is extrapolated" in note


def test_ac4_without_in_situ(bh1_u3):
    assert bh1_u3["spans_effective_vertical_stress"].isna().all()
    assert any("ht.analysis.vertical_stress()" in note for note in _notes(bh1_u3))


def test_ac4_in_situ_in_another_unit(site_si):
    result = ht.analysis.oedometer_increments(
        _with_in_situ(site_si, 80.0 / PSF, unit="psf")
    )
    flags = result["spans_effective_vertical_stress"].to_numpy(dtype=bool)
    assert list(np.flatnonzero(flags)) == [2, 7]


# --- AC 5: start void ratio ---------------------------------------------------


def test_ac5_start_void_ratio_from_previous_end(site_si):
    df = site_si.copy()
    df.loc[df.index[3], "void_ratio_at_increment_start"] = np.nan
    result = ht.analysis.oedometer_increments(df)
    assert result["coefficient_of_volume_compressibility"].iloc[3] == pytest.approx(
        0.157657658, rel=TABLE_REL
    )
    (note,) = [n for n in _notes(result) if "void_ratio_at_increment_start" in n]
    assert f"Rows {df.index[3]} " in note


def test_ac5_frame_without_start_column():
    result = ht.analysis.oedometer_increments(_frame([100, 200], [0.776, 0.748]))
    assert result["coefficient_of_volume_compressibility"].iloc[1] == pytest.approx(
        28 / 177.6, rel=REL
    )


# --- AC 6: blank and odd rows -------------------------------------------------


def test_ac6_constant_stress():
    result = ht.analysis.oedometer_increments(_frame([100, 100], [0.776, 0.770]))
    assert result["load_branch"].iloc[1] == "constant_stress"
    assert np.isnan(result["coefficient_of_volume_compressibility"].iloc[1])
    assert result["coefficient_of_volume_compressibility_reason"].iloc[1] == (
        "no stress change"
    )
    assert result["constrained_modulus_reason"].iloc[1] == "no stress change"
    assert any("oedometer_load_branch()" in note for note in _notes(result))


def test_ac6_negative_volume_compressibility_kept():
    result = ht.analysis.oedometer_increments(_frame([100, 200], [0.776, 0.781]))
    assert result["coefficient_of_volume_compressibility"].iloc[1] == pytest.approx(
        -0.0281531532, rel=TABLE_REL
    )
    assert result["coefficient_of_volume_compressibility_reason"].isna().iloc[1]
    assert np.isnan(result["constrained_modulus"].iloc[1])
    assert result["constrained_modulus_reason"].iloc[1] == "m_v is not positive"


def test_ac6_blank_stress():
    df = _frame([50, np.nan, 200], [0.788, 0.776, 0.748])
    result = ht.analysis.oedometer_increments(df)
    reasons = result["coefficient_of_volume_compressibility_reason"]
    assert list(reasons.iloc[1:]) == [
        "no stress",
        "the previous increment has no stress",
    ]
    assert result["coefficient_of_volume_compressibility"].iloc[1:].isna().all()


def test_ac6_blank_void_ratio():
    df = _frame([50, 100, 200], [0.788, np.nan, 0.748])
    result = ht.analysis.oedometer_increments(df)
    reasons = result["coefficient_of_volume_compressibility_reason"]
    assert reasons.iloc[1] == "no void ratio at the increment's end"
    assert reasons.iloc[2] == "no void ratio at the increment's start"


def test_ac6_two_specimens_start_blank():
    df = pd.concat(
        [_frame([25, 50], [0.795, 0.788], "A"), _frame([25, 50], [0.795, 0.788], "B")],
        ignore_index=True,
    )
    df.attrs["units"] = {"applied_vertical_stress": "kPa"}
    result = ht.analysis.oedometer_increments(df)
    start = result["applied_vertical_stress_at_increment_start"]
    assert list(np.isnan(start)) == [True, False, True, False]
    reasons = result["coefficient_of_volume_compressibility_reason"]
    assert list(reasons.iloc[[0, 2]]) == [FIRST, FIRST]


def test_ac6_categorical_specimen_order():
    df = _frame([25, 50], [0.795, 0.788])
    df["specimen_id"] = pd.Categorical(df["specimen_id"])
    result = ht.analysis.oedometer_increments(df)
    assert result["coefficient_of_volume_compressibility"].notna().sum() == 1


# --- AC 7: errors -------------------------------------------------------------


def test_ac7_missing_end_void_ratio():
    df = _frame([25, 50], [0.795, 0.788]).drop(columns="void_ratio_at_increment_end")
    with pytest.raises(ColumnError, match="void_ratio_at_increment_end") as error:
        ht.analysis.oedometer_increments(df)
    assert 'ht.template("oedometer")' in str(error.value)


def test_ac7_two_in_situ_stresses():
    df = _with_in_situ(_frame([25, 50], [0.795, 0.788]), [80.0, 90.0])
    with pytest.raises(HangtuError, match="more than one effective_vertical_stress"):
        ht.analysis.oedometer_increments(df)


def test_ac7_blank_specimen_and_display_units():
    df = _frame([25, 50], [0.795, 0.788])
    with pytest.raises(HangtuError, match="display_units"):
        ht.analysis.oedometer_increments(df, display_units="metric")
    df.loc[0, "specimen_id"] = None
    with pytest.raises(HangtuError, match="no specimen_id"):
        ht.analysis.oedometer_increments(df)


# --- AC 10: twins -------------------------------------------------------------

_TWIN_COLUMNS = [
    "applied_vertical_stress",
    "applied_vertical_stress_at_increment_start",
    "coefficient_of_volume_compressibility",
    "constrained_modulus",
    "unload_reload_constrained_modulus",
]


@pytest.mark.parametrize("system", ["SI", "US"])
def test_ac10_twins_agree(site_si, site_us, system):
    si = ht.analysis.oedometer_increments(site_si, display_units=system)
    us = ht.analysis.oedometer_increments(site_us, display_units=system)
    for column in _TWIN_COLUMNS:
        np.testing.assert_allclose(si[column], us[column], rtol=REL, err_msg=column)
        assert si.attrs["units"][column] == us.attrs["units"][column]
    for column in (
        "coefficient_of_volume_compressibility_reason",
        "constrained_modulus_reason",
    ):
        assert si[column].equals(us[column])


# --- AC 11: docstring ---------------------------------------------------------


def test_ac11_docstring():
    doc = ht.analysis.oedometer_increments.__doc__
    assert "BS 1377-5:1990, 3.6.2.2.4" in doc
    for reason in (
        FIRST,
        "no stress change",
        "the previous increment has no stress",
        "m_v is not positive",
        "no void ratio at the increment's start",
    ):
        assert reason in doc.replace("\n    ", " ")
