"""ht.analysis.spt_n1_60(): C_N and (N1)60 (docs/work/m13b1-spt-framework.md, AC 1)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht

KPA_TO_PSF = 1000 / 47.880259  # 1 kPa = 20.885 psf

# AC 1: σ′v (kPa) -> C_N, by hand from Youd et al. (2001) Eq. 9 and 10, capped at 1.7.
# L&W: (100 / σ′v)^0.5. Kayen: 2.2 / (1.2 + σ′v / 100).
STRESSES = [0.0, 25.0, 50.0, 100.0, 200.0, 300.0]
LIAO_WHITMAN = [1.7, 1.7, 1.4142, 1.0, 0.7071, 0.5774]
KAYEN = [1.7, 1.5172, 1.2941, 1.0, 0.6875, 0.5238]


def frame(n60, stress, unit="kPa", **columns):
    df = pd.DataFrame({"spt_n60": n60, "effective_vertical_stress": stress, **columns})
    return ht.set_units(df, {"effective_vertical_stress": unit})


@pytest.mark.parametrize(
    ("method", "expected"),
    [("liao_whitman_1986", LIAO_WHITMAN), ("kayen_1992", KAYEN)],
)
def test_overburden_correction_golden_values(method, expected):
    out = ht.analysis.spt_n1_60(frame([10.0] * 6, STRESSES), method=method)
    assert out["spt_overburden_correction"].tolist() == pytest.approx(
        expected, abs=1e-4
    )
    assert out["spt_n1_60"].tolist() == pytest.approx(
        [10 * c for c in expected], abs=1e-3
    )


def test_kayen_is_capped_at_the_surface():
    # Uncapped, 2.2 / 1.2 = 1.8333.
    out = ht.analysis.spt_n1_60(frame([10.0], [0.0]), method="kayen_1992")
    assert out["spt_overburden_correction"][0] == 1.7


@pytest.mark.parametrize("method", ["liao_whitman_1986", "kayen_1992"])
def test_us_units_give_the_same_result(method):
    si = ht.analysis.spt_n1_60(frame([10.0] * 6, STRESSES), method=method)
    psf = [s * KPA_TO_PSF for s in STRESSES]
    us = ht.analysis.spt_n1_60(frame([10.0] * 6, psf, unit="psf"), method=method)
    assert us["spt_n1_60"].tolist() == pytest.approx(si["spt_n1_60"].tolist(), rel=1e-3)


def test_above_300_kpa_is_blank_and_counted():
    df = frame([10.0, 10.0, 10.0], [300.0, 300.1, 450.0])
    with pytest.warns(UserWarning) as caught:
        out = ht.analysis.spt_n1_60(df, method="liao_whitman_1986")
    assert out["spt_n1_60"][0] == pytest.approx(5.7735, abs=1e-4)
    assert out[["spt_overburden_correction", "spt_n1_60"]][1:].isna().all().all()
    assert [str(w.message) for w in caught] == [
        "(N1)60 is blank for 2 rows: 2 with σ′v above 300 kPa, where Youd et al. "
        "(2001) say C_N should be estimated by other means."
    ]


def test_blank_inputs_give_blanks_counted_by_reason():
    df = frame([np.nan, 10.0, 10.0], [100.0, np.nan, 400.0])
    with pytest.warns(UserWarning) as caught:
        out = ht.analysis.spt_n1_60(df, method="kayen_1992")
    assert out["spt_n1_60"].isna().all()
    # A blank N60 still has a C_N from its σ′v.
    assert out["spt_overburden_correction"][0] == 1.0
    assert [str(w.message) for w in caught] == [
        "(N1)60 is blank for 3 rows: 2 with no N60 or σ′v; 1 with σ′v above 300 "
        "kPa, where Youd et al. (2001) say C_N should be estimated by other means."
    ]


def test_negative_stress_names_the_rows():
    with pytest.raises(ht.HangtuError, match=r"negative in rows 1\b"):
        ht.analysis.spt_n1_60(frame([10.0, 10.0], [50.0, -5.0]), method="kayen_1992")


def test_method_is_required():
    with pytest.raises(TypeError, match="method"):
        ht.analysis.spt_n1_60(frame([10.0], [50.0]))


def test_an_unknown_method_lists_the_methods():
    with pytest.raises(
        ht.HangtuError, match=r"'liao_whitman_1986', 'kayen_1992'.*Example"
    ):
        ht.analysis.spt_n1_60(frame([10.0], [50.0]), method="liao")


@pytest.mark.parametrize(
    ("column", "hint"),
    [
        ("spt_n60", r"ht\.analysis\.spt\(\) or p\.spt\(\)"),
        ("effective_vertical_stress", r"ht\.analysis\.vertical_stress\(\)"),
    ],
)
def test_a_missing_column_names_what_adds_it(column, hint):
    df = frame([10.0], [50.0]).drop(columns=column)
    with pytest.raises(ht.ColumnError, match=rf"'{column}' not found.*{hint}"):
        ht.analysis.spt_n1_60(df, method="kayen_1992")


def test_stress_without_units_is_an_error():
    df = pd.DataFrame({"spt_n60": [10.0], "effective_vertical_stress": [50.0]})
    with pytest.raises(ht.UnitsError, match="'effective_vertical_stress' has no units"):
        ht.analysis.spt_n1_60(df, method="kayen_1992")


def test_refusals_are_computed():
    df = frame([66.7], [100.0], spt_refusal=[True])
    out = ht.analysis.spt_n1_60(df, method="liao_whitman_1986")
    assert out["spt_n1_60"][0] == pytest.approx(66.7)


def test_no_row_is_dropped_or_reordered_and_the_input_is_unchanged():
    df = frame([5.0, 20.0, np.nan], [25.0, 50.0, 80.0], loca_id=["B", "A", "C"])
    df.index = [7, 3, 5]
    before = df.copy()
    with pytest.warns(UserWarning, match="no N60"):
        out = ht.analysis.spt_n1_60(df, method="liao_whitman_1986")
    assert out.index.tolist() == [7, 3, 5]
    assert out["loca_id"].tolist() == ["B", "A", "C"]
    pd.testing.assert_frame_equal(df, before)
    assert out.attrs["units"] == {"effective_vertical_stress": "kPa"}


def test_existing_columns_are_replaced_with_a_warning():
    df = frame([10.0], [100.0], spt_n1_60=[99.0])
    with pytest.warns(UserWarning, match="Replaced the existing columns 'spt_n1_60'"):
        out = ht.analysis.spt_n1_60(df, method="kayen_1992")
    assert out["spt_n1_60"][0] == 10.0


@pytest.mark.parametrize(
    ("method", "cited"),
    [
        ("liao_whitman_1986", "Liao & Whitman (1986)"),
        ("kayen_1992", "Kayen et al. (1992)"),
    ],
)
def test_the_method_is_recorded(method, cited):
    out = ht.analysis.spt_n1_60(frame([10.0], [100.0]), method=method)
    record = out.attrs["spt_n1_60"]
    assert record["method"] == method
    assert record["cap"] == 1.7
    assert record["pa"] == "100 kPa"
    assert record["source"].startswith(cited)
    assert "Youd et al. (2001)" in record["source"]
