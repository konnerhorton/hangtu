"""undrained_shear_strength_from_tests() (docs/work/m17a-strength-data.md, D3, D6).

Hand values: s_u = q / 2 for a deviator stress or unconfined compressive
strength; a hand penetrometer reading as s_u or halved by its scale; a vane's
s_u as given, and S_t = s_u / s_u,r.
"""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.analysis import undrained_shear_strength_from_tests as from_tests
from hangtu.errors import HangtuError, UnitsError

KPA = {
    "deviator_stress_at_failure": "kPa",
    "unconfined_compressive_strength": "kPa",
    "hand_penetrometer_reading": "kPa",
    "undrained_shear_strength": "kPa",
    "remolded_undrained_shear_strength": "kPa",
}


def _frame(**columns):
    df = pd.DataFrame(columns)
    return ht.set_units(df, {c: KPA[c] for c in df.columns if c in KPA})


def _tests():
    # UU q_f 120; q_u 96; a field vane 42 / 14; a hand penetrometer 150.
    nan = np.nan
    return _frame(
        test_type=["UU", "unconfined compression", "BOREHOLE", "hand penetrometer"],
        deviator_stress_at_failure=[120.0, nan, nan, nan],
        unconfined_compressive_strength=[nan, 96.0, nan, nan],
        hand_penetrometer_reading=[nan, nan, nan, 150.0],
        undrained_shear_strength=[nan, nan, 42.0, nan],
        remolded_undrained_shear_strength=[nan, nan, 14.0, nan],
    )


@pytest.mark.parametrize(
    ("scale", "reading_su", "reading_basis"),
    [
        ("unconfined_compressive_strength", 75.0, "half_hand_penetrometer_reading"),
        ("undrained_shear_strength", 150.0, "hand_penetrometer_reading"),
    ],
)
def test_each_input_gives_its_s_u(scale, reading_su, reading_basis):
    result = from_tests(_tests(), hand_penetrometer_scale=scale)
    assert result["undrained_shear_strength"].tolist() == pytest.approx(
        [60.0, 48.0, 42.0, reading_su]
    )
    assert result["undrained_shear_strength_basis"].tolist() == [
        "half_deviator_stress",
        "half_unconfined_compressive_strength",
        "as_reported",
        reading_basis,
    ]
    sensitivity = result["strength_sensitivity"].tolist()
    assert sensitivity[2] == pytest.approx(3.0)
    assert np.isnan([sensitivity[i] for i in (0, 1, 3)]).all()
    assert result.attrs["units"]["undrained_shear_strength"] == "kPa"


def test_a_second_call_changes_nothing():
    once = from_tests(_tests(), hand_penetrometer_scale="undrained_shear_strength")
    twice = from_tests(once, hand_penetrometer_scale="undrained_shear_strength")
    pd.testing.assert_frame_equal(once, twice)


def test_the_input_is_not_changed():
    df = _tests()
    before = df.copy()
    from_tests(df, hand_penetrometer_scale="undrained_shear_strength")
    pd.testing.assert_frame_equal(df, before)


def test_a_bound_or_a_zero_remolded_value_gives_a_blank_sensitivity():
    # Peak >120 with remolded 30; 55 with remolded 0; 38 / 12 = 3.1666667.
    df = _frame(
        undrained_shear_strength=[120.0, 55.0, 38.0],
        qualifier=[">", None, None],
        remolded_undrained_shear_strength=[30.0, 0.0, 12.0],
    )
    with pytest.warns(UserWarning, match="left blank on 2 rows"):
        result = from_tests(df)
    sensitivity = result["strength_sensitivity"].to_numpy()
    assert np.isnan(sensitivity[:2]).all()
    assert sensitivity[2] == pytest.approx(38 / 12, rel=1e-9)
    assert result["remolded_undrained_shear_strength"].tolist() == [30.0, 0.0, 12.0]


def test_a_flagged_remolded_value_gives_a_blank_sensitivity():
    df = _frame(
        undrained_shear_strength=[40.0],
        remolded_undrained_shear_strength=[5.0],
        remolded_qualifier=["<"],
    )
    with pytest.warns(UserWarning, match="left blank on 1 row"):
        result = from_tests(df)
    assert np.isnan(result["strength_sensitivity"].iloc[0])


def test_s_u_comes_in_its_own_declared_unit():
    # q_f 2506.2522 psf / 2 = 1253.1261 psf = 60 kPa; s_u declared in kPa.
    df = pd.DataFrame(
        {
            "deviator_stress_at_failure": [2506.2522],
            "undrained_shear_strength": [np.nan],
        }
    )
    df = ht.set_units(
        df, {"deviator_stress_at_failure": "psf", "undrained_shear_strength": "kPa"}
    )
    result = from_tests(df)
    assert result["undrained_shear_strength"].iloc[0] == pytest.approx(60.0, rel=1e-6)
    assert result.attrs["units"]["undrained_shear_strength"] == "kPa"


def test_without_a_declared_unit_s_u_takes_the_inputs():
    df = ht.set_units(
        pd.DataFrame({"unconfined_compressive_strength": [2000.0]}),
        {"unconfined_compressive_strength": "psf"},
    )
    result = from_tests(df)
    assert result["undrained_shear_strength"].iloc[0] == pytest.approx(1000.0)
    assert result.attrs["units"]["undrained_shear_strength"] == "psf"


def test_two_inputs_on_a_row_raise():
    df = _frame(deviator_stress_at_failure=[120.0], undrained_shear_strength=[60.0])
    with pytest.raises(HangtuError, match="reported_undrained_shear_strength"):
        from_tests(df)


def test_a_deviator_stress_of_zero_raises():
    df = _frame(deviator_stress_at_failure=[120.0, 0.0])
    with pytest.raises(HangtuError, match="Rows 1 have a deviator_stress_at_failure"):
        from_tests(df)


def test_a_reading_without_its_scale_raises():
    df = _frame(hand_penetrometer_reading=[150.0])
    with pytest.raises(HangtuError, match="hand_penetrometer_scale"):
        from_tests(df)


def test_an_unknown_scale_raises():
    with pytest.raises(HangtuError, match="isn't one of"):
        from_tests(_tests(), hand_penetrometer_scale="kPa")


def test_a_strength_in_a_length_unit_raises():
    df = pd.DataFrame({"undrained_shear_strength": [40.0]})
    df.attrs["units"] = {"undrained_shear_strength": "m"}
    with pytest.raises(UnitsError, match="is a stress"):
        from_tests(df)


def test_a_strength_without_units_raises():
    with pytest.raises(UnitsError, match="has no units"):
        from_tests(pd.DataFrame({"undrained_shear_strength": [40.0]}))
