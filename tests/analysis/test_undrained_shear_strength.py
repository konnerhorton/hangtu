"""s_u from SPT (docs/work/m13b2-spt-strength-history.md, AC 1, 3, 4)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.analysis import correlations

KPA_TO_PSF = 1000 / 47.880259
NAN = np.nan
LOWER, UPPER = "undrained_shear_strength_lower", "undrained_shear_strength_upper"

# AC 1, by hand: s_u/pa by N class (EPRI Table 4-10), pa = 100 kPa.
TERZAGHI_PECK = [
    (0, 0.0, 12.5),
    (2, 12.5, 25.0),
    (7, 25.0, 50.0),
    (8, 50.0, 100.0),
    (29, 100.0, 200.0),
    (30, 200.0, NAN),
]


def terzaghi_peck(df, **kwargs):
    return correlations.undrained_shear_strength_terzaghi_peck_1967(df, **kwargs)


# --- AC 1: Terzaghi & Peck ------------------------------------------------------


def test_terzaghi_peck_golden_bands():
    n, lower, upper = zip(*TERZAGHI_PECK, strict=True)
    out = terzaghi_peck(pd.DataFrame({"spt_n": n}), display_units="SI")
    assert out[LOWER].tolist() == pytest.approx(list(lower))
    assert out[UPPER].tolist() == pytest.approx(list(upper), nan_ok=True)
    # A band has no central value: nothing is interpolated (review 8).
    assert out["undrained_shear_strength"].isna().all()
    assert out["correlation_note"].isna().all()
    assert (
        out["correlation_name"] == "undrained_shear_strength_terzaghi_peck_1967"
    ).all()
    assert out.attrs["units"] == dict.fromkeys(
        ["undrained_shear_strength", LOWER, UPPER], "kPa"
    )


def test_terzaghi_peck_in_us_units():
    out = terzaghi_peck(pd.DataFrame({"spt_n": [7]}), display_units="US")
    assert out[LOWER].iloc[0] == pytest.approx(25.0 * KPA_TO_PSF)
    assert out[UPPER].iloc[0] == pytest.approx(50.0 * KPA_TO_PSF)
    assert out.attrs["units"][LOWER] == "psf"


def test_terzaghi_peck_no_estimate_for_blank_and_below_range_a_bound_at_refusal():
    df = pd.DataFrame(
        {"spt_n": [NAN, 50, -1, 10], "spt_refusal": [None, True, False, False]}
    )
    with pytest.warns(UserWarning) as caught:
        out = terzaghi_peck(df, display_units="SI")
    assert [str(w.message).split(" (")[0] for w in caught] == [
        "undrained_shear_strength_terzaghi_peck_1967 gave no estimate for 2 of 4 rows",
        "undrained_shear_strength_terzaghi_peck_1967 gave a bound, not an estimate, "
        "for 1 of 4 rows",
    ]
    assert out["correlation_note"].tolist() == [
        "input blank",
        "at least: refusal",
        "below range",
        None,
    ]
    # m18a spec: a refusal at N 50 is at least the band from 2.0 pa, open above.
    assert out["correlation_qualifier"].tolist() == [None, ">", None, None]
    assert out[LOWER].tolist() == pytest.approx([NAN, 200.0, NAN, 50.0], nan_ok=True)
    assert out[UPPER].tolist() == pytest.approx([NAN, NAN, NAN, 100.0], nan_ok=True)


def test_existing_band_columns_are_replaced_with_a_warning():
    df = pd.DataFrame({"spt_n": [10], LOWER: [1.0]})
    with pytest.warns(UserWarning, match=r"Replaced the existing columns '" + LOWER):
        out = terzaghi_peck(df, display_units="SI")
    assert out[LOWER].iloc[0] == 50.0


# --- AC 3: field N ---------------------------------------------------------------


def test_terzaghi_peck_without_spt_n_raises_naming_it():
    with pytest.raises(ht.HangtuError, match=r"spt_n"):
        terzaghi_peck(pd.DataFrame({"depth": [1.0]}))


def test_terzaghi_peck_does_not_read_n60_in_place_of_field_n():
    with pytest.raises(ht.HangtuError, match=r"'spt_n'"):
        terzaghi_peck(pd.DataFrame({"spt_n60": [10.0]}))


# --- AC 4: the bands and spt_class() agree ---------------------------------------


def test_the_bands_change_where_the_cohesive_classes_do():
    n = np.arange(0, 41, 0.5)
    df = pd.DataFrame({"spt_n": n})
    out = terzaghi_peck(df, display_units="SI")
    classes = ht.analysis.spt_class(df, table="cohesive").astype(str).to_numpy()
    band_changes = np.flatnonzero(np.diff(out[LOWER].to_numpy()) != 0)
    class_changes = np.flatnonzero(classes[1:] != classes[:-1])
    assert band_changes.tolist() == class_changes.tolist()


def test_terzaghi_peck_bands_draw_on_p01():
    df = pd.DataFrame(
        {
            "loca_id": ["B-1"] * 4,
            "ground_level": [10.0] * 4,
            "depth": [2.0, 4.0, 6.0, 8.0],
            "spt_n": [3, 12, 40, NAN],
        },
    )
    df = ht.set_units(df, {"depth": "m", "ground_level": "m"})
    with pytest.warns(UserWarning, match=r"no estimate for 1 of 4"):
        out = terzaghi_peck(df, display_units="SI")
    _, ax = ht.plot.profile(
        out, "undrained_shear_strength", color_by=None, display_units="SI"
    )
    assert ax.ags_notes == {"value_range": 3, "correlation_input_blank": 1}


# --- AC 1: Stroud ---------------------------------------------------------------------


def stroud(df, **kwargs):
    return correlations.undrained_shear_strength_stroud_1974(df, **kwargs)


def test_stroud_golden_values():
    # By hand, s_u = f1 N60 pa / 100 with pa = 100 kPa: 4.5 x 10 = 45.0;
    # 4.5 x 20 = 90.0; 15 <= PI < 30 gives 4.5 x 10 to 5.5 x 10 = 45.0 to 55.0.
    df = pd.DataFrame(
        {"spt_n60": [10, 20, 10, 10], "plasticity_index": [40, 30, 20, 12]}
    )
    with pytest.warns(
        UserWarning, match=r"no estimate for 1 of 4 rows \(1 below range"
    ):
        out = stroud(df, display_units="SI")
    assert out["undrained_shear_strength"].tolist() == pytest.approx(
        [45.0, 90.0, NAN, NAN], nan_ok=True
    )
    assert out[LOWER].tolist() == pytest.approx([NAN, NAN, 45.0, NAN], nan_ok=True)
    assert out[UPPER].tolist() == pytest.approx([NAN, NAN, 55.0, NAN], nan_ok=True)
    assert out["correlation_note"].tolist() == [None, None, None, "below range"]


@pytest.mark.filterwarnings("ignore:.*gave a bound")
def test_stroud_at_a_refusal_is_at_least_the_estimate_at_its_n60():
    # m18a spec: s_u >= 4.5 x 66.7 x 100 / 100 = 300.15 kPa.
    df = pd.DataFrame(
        {"spt_n60": [66.7], "plasticity_index": [35], "spt_refusal": [True]}
    )
    out = stroud(df, display_units="SI")
    assert out["undrained_shear_strength"].iloc[0] == pytest.approx(300.15, rel=1e-9)
    assert out["correlation_qualifier"].tolist() == [">"]
    assert out["correlation_note"].tolist() == ["at least: refusal"]


def test_stroud_us_twin():
    # 45.0 kPa = 45000 / 47.880259 = 939.85 psf.
    df = pd.DataFrame({"spt_n60": [10], "plasticity_index": [40]})
    out = stroud(df, display_units="US")
    assert out["undrained_shear_strength"].iloc[0] == pytest.approx(939.85, rel=1e-3)
    assert out.attrs["units"]["undrained_shear_strength"] == "psf"


def test_stroud_without_pi_raises_naming_add_judgment():
    with pytest.raises(ht.HangtuError, match=r"plasticity_index.*add_judgment"):
        stroud(pd.DataFrame({"spt_n60": [10]}))


def test_stroud_reads_n60_not_field_n():
    with pytest.raises(ht.HangtuError, match=r"'spt_n60'"):
        stroud(pd.DataFrame({"spt_n": [10], "plasticity_index": [40]}))


def test_stroud_after_add_judgment():
    df = pd.DataFrame({"spt_n60": [10, 8], "geology_unit": ["Alluvium", "Lacustrine"]})
    df = ht.analysis.add_judgment(
        df, "plasticity_index", value={"Alluvium": 32, "Lacustrine": 18}
    )
    out = stroud(df, display_units="SI")
    assert out["undrained_shear_strength"].tolist() == pytest.approx(
        [45.0, NAN], nan_ok=True
    )
    assert out[LOWER].tolist() == pytest.approx([NAN, 36.0], nan_ok=True)
    assert out[UPPER].tolist() == pytest.approx([NAN, 44.0], nan_ok=True)
    assert out.attrs["judgments"]["plasticity_index"]["source"] == "argument"
