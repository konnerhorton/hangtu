"""ht.stats.fit(): distributions, ranking, bounds, inputs (docs/work/m15c-fit.md)."""

import math

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError
from hangtu.units import to_display

STRENGTH = [10, 12, 15, 20, 23]
FEW = "fewer than 10"


def _strength(values=STRENGTH, unit="kPa", **columns):
    df = pd.DataFrame({"undrained_shear_strength": values, **columns})
    return ht.set_units(df, {"undrained_shear_strength": unit})


def _fit(data, **kwargs):
    """Fit fewer than 10 values, which warns."""
    with pytest.warns(UserWarning, match=FEW):
        return ht.stats.fit(data, **kwargs)


def _fits(result, group=0):
    return {fit["distribution"]: fit for fit in result.groups[group]["fits"]}


def _aicc(log_likelihood, n, k=2):
    return 2 * k - 2 * log_likelihood + 2 * k * (k + 1) / (n - k - 1)


# AC 1: normal and lognormal in closed form, hand-calculated in the spec.


def test_normal_closed_form():
    fit = _fits(_fit(_strength(), value="undrained_shear_strength"))["normal"]
    assert fit["parameters"]["loc"] == pytest.approx(16, rel=1e-9)
    assert fit["parameters"]["scale"] == pytest.approx(4.8579831, rel=1e-8)
    assert fit["log_likelihood"] == pytest.approx(-14.99780945, rel=1e-9)
    assert fit["aicc"] == pytest.approx(39.99561889, rel=1e-9)
    assert fit["probability_below_lower_bound"] == pytest.approx(4.946575e-4, rel=1e-6)


def test_lognormal_closed_form():
    fit = _fits(_fit(_strength(), value="undrained_shear_strength"))["lognormal"]
    assert math.log(fit["parameters"]["scale"]) == pytest.approx(2.72535369, rel=1e-8)
    assert fit["parameters"]["s"] == pytest.approx(0.30924660, rel=1e-8)
    assert fit["median"] == pytest.approx(15.2618109, rel=1e-8)
    assert fit["log_likelihood"] == pytest.approx(-14.85337983, rel=1e-9)
    assert fit["aicc"] == pytest.approx(39.70675966, rel=1e-9)


def test_ranking_of_normal_and_lognormal():
    result = _fit(
        _strength(),
        value="undrained_shear_strength",
        distributions=["normal", "lognormal"],
    )
    lognormal, normal = result.groups[0]["fits"]
    assert (lognormal["distribution"], lognormal["rank"]) == ("lognormal", 1)
    assert (normal["distribution"], normal["rank"]) == ("normal", 2)
    assert lognormal["delta_aicc"] == 0
    assert normal["delta_aicc"] == pytest.approx(0.28885923, rel=1e-7)
    assert lognormal["akaike_weight"] == pytest.approx(0.53604477, rel=1e-7)
    assert normal["akaike_weight"] == pytest.approx(0.46395523, rel=1e-7)


def test_the_notes_give_the_rough_guide():
    result = _fit(_strength(), value="undrained_shear_strength")
    assert any("Burnham & Anderson 2004" in note for note in result.notes)


def test_a_tie_keeps_the_table_order():
    # Every positive fit of identical scale-free data ties only by construction
    # of the sort; check the sort is stable on an exact tie.
    from hangtu.stats._fit import _rank

    fits = [{"distribution": name, "aicc": 1.0} for name in ("normal", "gamma")]
    _rank(fits)
    assert [fit["distribution"] for fit in fits] == ["normal", "gamma"]
    assert [fit["akaike_weight"] for fit in fits] == [0.5, 0.5]


# AC 2: gamma and Weibull by SciPy's fit.


def test_gamma_equals_scipy():
    x = np.array(STRENGTH, float)
    fit = _fits(_fit(_strength(), value="undrained_shear_strength"))["gamma"]
    shape, _, scale = stats.gamma.fit(x, floc=0)
    assert fit["parameters"]["a"] == pytest.approx(shape, rel=1e-6)
    assert fit["parameters"]["scale"] == pytest.approx(scale, rel=1e-6)
    log_likelihood = stats.gamma.logpdf(x, shape, scale=scale).sum()
    assert fit["log_likelihood"] == pytest.approx(log_likelihood, rel=1e-6)
    assert fit["aicc"] == pytest.approx(_aicc(log_likelihood, 5), rel=1e-6)


@pytest.mark.parametrize(
    "values",
    [STRENGTH, np.random.default_rng(1).weibull(1.5, 30) * 20],
    ids=["five", "thirty"],
)
def test_weibull_through_gumbel_is_the_maximum_likelihood_fit(values):
    # weibull_min.fit(floc=0) stops about 1e-6 short of the maximum in scale;
    # the Gumbel route solves the likelihood equation exactly, so it is checked
    # against the equation and against SciPy at 1e-5 (the spec's AC 2 note).
    x = np.asarray(values, float)
    result = _fit(x) if x.size < 10 else ht.stats.fit(x)
    fit = _fits(result)["weibull"]
    shape, scale = fit["parameters"]["c"], fit["parameters"]["scale"]
    logs = np.log(x)
    profile = 1 / shape + logs.mean() - (x**shape * logs).sum() / (x**shape).sum()
    assert profile == pytest.approx(0, abs=1e-9)
    assert scale == pytest.approx(np.mean(x**shape) ** (1 / shape), rel=1e-9)
    scipy_shape, _, scipy_scale = stats.weibull_min.fit(x, floc=0)
    assert shape == pytest.approx(scipy_shape, rel=1e-5)
    assert scale == pytest.approx(scipy_scale, rel=1e-5)
    scipy_log_likelihood = stats.weibull_min.logpdf(
        x, scipy_shape, scale=scipy_scale
    ).sum()
    assert fit["log_likelihood"] >= scipy_log_likelihood - 1e-12
    assert fit["log_likelihood"] == pytest.approx(
        stats.weibull_min.logpdf(x, shape, scale=scale).sum(), rel=1e-12
    )


# AC 6: bounds.


def test_auto_bounds_on_a_ratio_scale():
    result = _fit(_strength(), value="undrained_shear_strength")
    assert result.bounds == (0.0, None)
    assert "beta" not in result.distributions
    frame = result.to_frame()
    assert frame["probability_above_upper_bound"].isna().all()
    positive = frame[frame["distribution"] != "normal"]
    assert (positive["probability_below_lower_bound"] == 0).all()


def test_auto_bounds_on_an_interval_scale():
    df = ht.set_units(
        pd.DataFrame({"elevation": [-3.0, 1, 4, 6, 9]}), {"elevation": "m"}
    )
    result = _fit(df, value="elevation")
    assert result.bounds == (None, None)
    frame = result.to_frame()
    assert frame["probability_below_lower_bound"].isna().all()
    assert frame["probability_above_upper_bound"].isna().all()
    # Values below 0 leave only the normal.
    assert list(frame["distribution"]) == ["normal"]


def test_auto_bounds_for_a_list_are_none():
    assert _fit(STRENGTH).bounds == (None, None)


FINES = [2.0, 8, 15, 22, 35, 41, 50, 63, 70, 88]


def _fines(values=FINES):
    return pd.DataFrame({"fines_content": values})


def test_two_bounds_add_beta():
    result = ht.stats.fit(_fines(), value="fines_content", bounds=(0, 100))
    assert result.distributions == ("normal", "lognormal", "gamma", "weibull", "beta")
    fit = _fits(result)["beta"]
    a, b, _, _ = stats.beta.fit(np.array(FINES), floc=0, fscale=100)
    assert fit["parameters"]["a"] == pytest.approx(a, rel=1e-6)
    assert fit["parameters"]["b"] == pytest.approx(b, rel=1e-6)
    assert fit["probability_below_lower_bound"] == 0
    assert fit["probability_above_upper_bound"] == 0
    normal = _fits(result)["normal"]
    assert normal["probability_above_upper_bound"] == pytest.approx(
        stats.norm.sf(100, normal["parameters"]["loc"], normal["parameters"]["scale"])
    )


def test_a_value_outside_the_bounds_is_an_error():
    with pytest.raises(HangtuError, match=r"1 values of 'fines_content' outside"):
        ht.stats.fit(_fines([*FINES, 105]), value="fines_content", bounds=(0, 100))


def test_beta_needs_two_bounds():
    with pytest.raises(HangtuError, match=r"bounds=\(low, high\)"):
        ht.stats.fit(_fines(), value="fines_content", distributions=["beta"])


@pytest.mark.parametrize("bounds", [(5, 1), (None,), "x", (0, math.inf), 3])
def test_bounds_must_be_low_and_high(bounds):
    with pytest.raises(HangtuError, match="bounds must be"):
        ht.stats.fit(_fines(), value="fines_content", bounds=bounds)


def test_an_unknown_distribution_lists_the_names():
    with pytest.raises(HangtuError, match="Choose from: normal, lognormal"):
        ht.stats.fit(_fines(), value="fines_content", distributions=["cauchy"])


def test_beta_on_a_value_at_a_bound_is_left_out_with_a_note():
    result = ht.stats.fit(_fines([0.0, *FINES]), value="fines_content", bounds=(0, 100))
    assert "beta" not in _fits(result)
    assert result.groups[0]["left_out"]["beta"].startswith("1 value on the bounds")


def test_a_normal_far_below_zero_gets_a_note():
    df = ht.set_units(
        pd.DataFrame(
            {"undrained_shear_strength": [1.0, 2, 3, 5, 40, 2, 1.5, 3, 4, 2.5]}
        ),
        {"undrained_shear_strength": "kPa"},
    )
    result = ht.stats.fit(df, value="undrained_shear_strength")
    assert any("the normal fit puts" in note for note in result.notes)


# AC 7: values at or below 0.


def test_a_zero_fits_the_normal_only():
    df = pd.DataFrame({"spt_n60": [0.0, 12, 18, 25, 31, 40]})
    result = _fit(df, value="spt_n60")
    assert list(_fits(result)) == ["normal"]
    assert set(result.groups[0]["left_out"]) == {"lognormal", "gamma", "weibull"}
    assert (
        "All: lognormal, gamma, weibull not fitted: 1 value at or below 0, outside "
        "the distribution's range."
    ) in result.notes
    assert result.groups[0]["counts"]["count"] == 6


# AC 8: minimum n.


def _units(values_a, values_b):
    return _strength(
        [*values_a, *values_b],
        geology_unit=["A"] * len(values_a) + ["B"] * len(values_b),
    )


def test_a_group_of_three_has_no_fits_and_warns():
    df = _units([10, 12, 15], list(range(20, 32)))
    with pytest.warns(UserWarning, match=r"fewer than 4 .* A \(3\)"):
        result = ht.stats.fit(df, value="undrained_shear_strength", by="geology_unit")
    frame = result.to_frame()
    row = frame[frame["geology_unit"] == "A"].iloc[0]
    assert row["count"] == 3
    assert pd.isna(row["distribution"])
    assert pd.isna(row["rank"])
    assert result.groups[0]["reason"].startswith("fewer than 4 uncensored values")
    assert (frame["geology_unit"] == "B").sum() == 4


def test_groups_of_three_and_six_warn_once_each():
    df = _units([10, 12, 15], [20, 21, 25, 28, 30, 33])
    with pytest.warns(UserWarning) as caught:
        ht.stats.fit(df, value="undrained_shear_strength", by="geology_unit")
    messages = [str(warning.message) for warning in caught]
    assert len(messages) == 2
    assert "fewer than 4" in messages[0] and "A (3)" in messages[0]
    assert "fewer than 10" in messages[1] and "B (6)" in messages[1]


def test_no_group_of_four_is_an_error():
    df = _units([10, 12, 15], [20, 21])
    with pytest.raises(HangtuError, match="no group has them: A \\(3\\), B \\(2\\)"):
        ht.stats.fit(df, value="undrained_shear_strength", by="geology_unit")


# AC 10: units.


def test_a_psf_frame_fits_in_psf_and_si_in_kpa():
    c = to_display([1.0], "psf", "stress", "SI")[0][0]
    psf = _fit(_strength(unit="psf"), value="undrained_shear_strength")
    kpa = _fit(
        _strength(unit="psf"), value="undrained_shear_strength", display_units="SI"
    )
    assert (psf.unit, kpa.unit) == ("psf", "kPa")
    fits_psf, fits_kpa = _fits(psf), _fits(kpa)
    normal_psf, normal_kpa = fits_psf["normal"], fits_kpa["normal"]
    assert normal_kpa["parameters"]["loc"] == pytest.approx(
        c * normal_psf["parameters"]["loc"], rel=1e-9
    )
    assert normal_kpa["parameters"]["scale"] == pytest.approx(
        c * normal_psf["parameters"]["scale"], rel=1e-9
    )
    assert fits_kpa["lognormal"]["parameters"]["scale"] == pytest.approx(
        c * fits_psf["lognormal"]["parameters"]["scale"], rel=1e-9
    )
    assert fits_kpa["lognormal"]["parameters"]["s"] == pytest.approx(
        fits_psf["lognormal"]["parameters"]["s"], rel=1e-9
    )
    m = len(STRENGTH)
    for name in ("normal", "lognormal"):
        assert fits_kpa[name]["log_likelihood"] == pytest.approx(
            fits_psf[name]["log_likelihood"] - m * math.log(c), rel=1e-9
        )
        assert fits_kpa[name]["aicc"] == pytest.approx(
            fits_psf[name]["aicc"] + 2 * m * math.log(c), rel=1e-9
        )
    for name in fits_psf:
        # The numerical fits (gamma, Weibull) are scale-equivariant to their
        # optimizer's tolerance.
        assert fits_kpa[name]["delta_aicc"] == pytest.approx(
            fits_psf[name]["delta_aicc"], rel=1e-6, abs=1e-9
        )
        assert fits_kpa[name]["akaike_weight"] == pytest.approx(
            fits_psf[name]["akaike_weight"], rel=1e-6
        )
        assert fits_kpa[name]["rank"] == fits_psf[name]["rank"]


def test_bounds_are_in_display_units():
    # 100 psf is 4.79 kPa: inside in kPa, so no error; 4.79 psf would be outside.
    df = _strength(unit="psf")
    _fit(df, value="undrained_shear_strength", display_units="SI", bounds=(0, 1.2))
    with pytest.raises(HangtuError, match="outside"):
        ht.stats.fit(df, value="undrained_shear_strength", bounds=(0, 1.2))


def test_a_list_without_units_says_so():
    assert "(units not given)" in _fit(STRENGTH).notes


# AC 9: the three input forms.


def test_a_series_and_an_array_give_the_same_fits():
    expected = _fit(_strength(), value="undrained_shear_strength").to_frame()
    expected = expected.drop(columns="parameters")
    series = _strength()["undrained_shear_strength"]
    series.attrs = {"units": {"undrained_shear_strength": "kPa"}}
    for data in (series, np.array(STRENGTH), STRENGTH, pd.Series(STRENGTH)):
        frame = _fit(data, bounds=(0, None)).to_frame().drop(columns="parameters")
        pd.testing.assert_frame_equal(frame, expected)


def test_a_dataframe_needs_value():
    with pytest.raises(HangtuError, match=r"fit\(\) needs value="):
        ht.stats.fit(_strength())


def test_a_missing_column_names_fit():
    with pytest.raises(ColumnError, match=r"fit\(\) needs the column"):
        ht.stats.fit(_strength(), value="plasticity_index")


def test_blanks_and_text_are_counted():
    df = _strength([*STRENGTH, None, "wet"])
    with pytest.warns(UserWarning) as caught:
        result = ht.stats.fit(df, value="undrained_shear_strength")
    assert any("'wet'" in str(warning.message) for warning in caught)
    counts = result.groups[0]["counts"]
    assert (counts["count"], counts["count_blank"], counts["count_text"]) == (5, 1, 1)


# AC 12: no log=.


def test_no_log_argument():
    with pytest.raises(TypeError):
        ht.stats.fit(STRENGTH, log=True)
    assert "has no ``log=``" in ht.stats.fit.__doc__


def test_the_input_is_unchanged():
    df = _strength(geology_unit=["A"] * 5)
    before = df.copy()
    _fit(df, value="undrained_shear_strength", by="geology_unit")
    pd.testing.assert_frame_equal(df, before)
