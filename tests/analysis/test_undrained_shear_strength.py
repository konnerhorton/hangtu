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


def test_terzaghi_peck_no_estimate_for_blank_refusal_and_below_range():
    df = pd.DataFrame(
        {"spt_n": [NAN, 50, -1, 10], "spt_refusal": [None, True, False, False]}
    )
    with pytest.warns(UserWarning, match=r"no estimate for 3 of 4 rows") as caught:
        out = terzaghi_peck(df, display_units="SI")
    assert len(caught) == 1
    assert out["correlation_note"].tolist() == [
        "input blank",
        "refusal",
        "below range",
        None,
    ]
    assert out[LOWER].isna().tolist() == [True, True, True, False]
    assert out[UPPER].isna().tolist() == [True, True, True, False]


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
