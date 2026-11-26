"""Correlations on rows whose soil_class they aren't for.

docs/work/reliability-guards.md, AC 3, 4 and 8.
"""

import warnings

import numpy as np
import pandas as pd
import pytest

from hangtu.analysis import correlations

HATANAKA = correlations.effective_friction_angle_hatanaka_uchida_1996
AASHTO = correlations.drained_youngs_modulus_aashto_2004
NOTE = "soil class contradicts"


def rows(classes, units=None, n1_60=20.0):
    units = units or [f"U{i}" for i in range(len(classes))]
    return pd.DataFrame(
        {
            "spt_n1_60": [n1_60] * len(classes),
            "geology_unit": units,
            "soil_class": classes,
        }
    )


def quiet(function, df, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return function(df, **kwargs)


def test_fine_rows_warn_and_keep_their_estimates():
    df = rows(["fine", "fine", "coarse"], ["Alluvium", "Alluvium", "Terrace"])
    with pytest.warns(UserWarning, match=r"2 of 3 rows .*Alluvium \(fine\): 2"):
        result = HATANAKA(df)
    plain = quiet(HATANAKA, df.drop(columns="soil_class"))
    np.testing.assert_allclose(
        result["effective_friction_angle"], plain["effective_friction_angle"]
    )
    assert list(result["correlation_note"]) == [NOTE, NOTE, None]


def test_matching_unchecked_and_blank_classes_do_not_warn():
    df = rows(["coarse", "fill", "organic", None, "silty"])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = HATANAKA(df)
    assert result["correlation_note"].isna().all()


def test_rock_contradicts_a_soil_correlation():
    with pytest.warns(UserWarning, match=r"rock\): 1"):
        HATANAKA(rows(["rock"]))


def test_a_bound_keeps_its_own_note():
    df = rows(["fine"], n1_60=45.0)
    result = quiet(HATANAKA, df)
    assert result["correlation_note"].iloc[0].startswith("at least")


def test_a_blank_estimate_keeps_its_reason():
    df = rows(["fine"], n1_60=np.nan)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = HATANAKA(df)
    assert any("soil_class it doesn't apply to" in str(w.message) for w in caught)
    assert result["correlation_note"].iloc[0] == "input blank"


def test_classes_from_attrs_with_a_categorical_unit():
    df = rows(["fine", "coarse"], ["Alluvium", "Terrace"]).drop(columns="soil_class")
    df["geology_unit"] = pd.Categorical(
        df["geology_unit"], categories=["Terrace", "Alluvium", "Bedrock"]
    )
    df.attrs["soil_classes"] = {"Alluvium": "fine", "Terrace": "coarse"}
    with pytest.warns(UserWarning, match=r"1 of 2 rows .*Alluvium \(fine\): 1"):
        result = HATANAKA(df)
    assert list(result["correlation_note"]) == [NOTE, None]


def test_aashto_checks_each_soil_row():
    df = rows(["coarse", "fine"], ["Sand", "Silt"])
    with pytest.warns(UserWarning, match=r"Sand \(coarse\): 1"):
        AASHTO(df, soil={"Sand": "silts", "Silt": "silts"})
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        AASHTO(df, soil={"Sand": "coarse_sands", "Silt": "silts"})


def test_all_soils_correlation_is_not_checked():
    df = pd.DataFrame({"spt_n60": [10.0], "soil_class": ["rock"]})
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        correlations.shear_wave_velocity_imai_tonouchi_1982(df)


def test_describe_gives_the_classes():
    assert correlations.describe("undrained_shear_strength_stroud_1974")[
        "soil_classes"
    ] == ["fine"]


def test_profile_counts_the_noted_rows():
    import matplotlib.pyplot as plt

    import hangtu as ht

    df = rows(["fine", "fine", "coarse"], ["Alluvium", "Alluvium", "Terrace"])
    df["loca_id"] = "B1"
    df["ground_level"] = 50.0
    df["depth"] = [2.0, 4.0, 6.0]
    df = ht.set_units(df, {"depth": "m", "ground_level": "m"})
    result = quiet(HATANAKA, df)
    fig, ax = ht.plot.profile(result, "effective_friction_angle", vs="depth")
    texts = [t.get_text() for t in ax.texts]
    plt.close(fig)
    expected = "2 with a soil class the correlation isn't for, shown"
    assert any(expected in text for text in texts)
