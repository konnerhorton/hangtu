"""fit(): censored values, and the rows describe() would choose (m15c-fit.md, D3-5)."""

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import hangtu as ht
from hangtu.analysis import correlations
from hangtu.errors import HangtuError
from hangtu.stats import _fit as fit_module

N60 = [12, 18, 25, 31, 40]
#: Counts of rows left out; with ``count`` they add up to the group's rows.
LEFT_OUT = ["count_non_plastic", "count_range", "count_text", "count_blank"]


@pytest.fixture(autouse=True)
def _short_bootstrap(monkeypatch):
    """Draw few bootstrap samples: no test here checks a p-value."""
    monkeypatch.setattr(fit_module, "BOOTSTRAP_SAMPLES", 19)


def _fits(result, group=0):
    return {fit["distribution"]: fit for fit in result.groups[group]["fits"]}


def _adds_up(result, rows, *, assumed_left_out=True):
    left_out = [*LEFT_OUT, *(["count_assumed"] if assumed_left_out else [])]
    for group, expected in zip(result.groups, rows, strict=True):
        counts = group["counts"]
        assert counts["count"] + sum(counts[name] for name in left_out) == expected


@pytest.fixture(scope="module")
def refusals():
    df = pd.DataFrame(
        {"spt_n60": [*N60, 100, 100], "spt_refusal": [False] * 5 + [True] * 2}
    )
    with (
        pytest.MonkeyPatch.context() as patch,
        pytest.warns(UserWarning, match="fewer than 10"),
    ):
        patch.setattr(fit_module, "BOOTSTRAP_SAMPLES", 19)
        return ht.stats.fit(df, value="spt_n60")


SCIPY_FITS = {
    "normal": lambda data: dict(
        zip(["loc", "scale"], stats.norm.fit(data), strict=True)
    ),
    "lognormal": lambda data: dict(
        zip(["s", "loc", "scale"], stats.lognorm.fit(data, floc=0), strict=True)
    ),
    "gamma": lambda data: dict(
        zip(["a", "loc", "scale"], stats.gamma.fit(data, floc=0), strict=True)
    ),
    "weibull": lambda data: dict(
        zip(["c", "loc", "scale"], stats.weibull_min.fit(data, floc=0), strict=True)
    ),
}


def test_refusals_are_right_censored(refusals):
    # AC 4
    counts = refusals.groups[0]["counts"]
    assert (counts["count"], counts["count_censored"]) == (7, 2)
    assert counts["count_at_least"] == 2
    data = stats.CensoredData(uncensored=N60, right=[100, 100])
    for name, fit in _fits(refusals).items():
        expected = SCIPY_FITS[name](data)
        expected.pop("loc", None)
        for key, value in expected.items():
            assert fit["parameters"][key] == pytest.approx(value, rel=1e-6), name
        distribution = refusals.distribution(name)
        log_likelihood = distribution.logpdf(N60).sum() + 2 * distribution.logsf(100)
        assert fit["log_likelihood"] == pytest.approx(log_likelihood, rel=1e-12)
        assert fit["aicc"] == pytest.approx(
            4 - 2 * log_likelihood + 12 / (7 - 3), rel=1e-12
        )


def test_censored_values_have_no_anderson_darling_check(refusals):
    for fit in _fits(refusals).values():
        assert np.isnan(fit["anderson_darling_statistic"])
        assert np.isnan(fit["anderson_darling_p_value"])
    assert (
        "All: no Anderson-Darling check: 2 values are censored; judge the fit on "
        "the Q-Q plot."
    ) in refusals.notes
    assert any("2 of 7 values censored (29%" in note for note in refusals.notes)
    assert not any("evidence against" in note for note in refusals.notes)


def test_censored_values_have_kaplan_meier_positions(refusals):
    positions = refusals.groups[0]["positions"]
    assert positions["values"] == N60
    assert positions["probabilities"] == pytest.approx(
        [1 / 14, 3 / 14, 5 / 14, 7 / 14, 9 / 14], rel=1e-12
    )


def _conductivity(values, qualifiers):
    df = pd.DataFrame({"hydraulic_conductivity": values, "qualifier": qualifiers})
    return ht.set_units(df, {"hydraulic_conductivity": "cm/s"})


def test_a_less_than_is_left_censored():
    values = [0.1, 0.3, 0.5, 0.8, 1.2, 2.0]
    df = _conductivity(values, ["<", *[None] * 5])
    with pytest.warns(UserWarning, match="fewer than 10"):
        result = ht.stats.fit(df, value="hydraulic_conductivity")
    counts = result.groups[0]["counts"]
    assert (counts["count_at_most"], counts["count_censored"]) == (1, 1)
    data = stats.CensoredData(uncensored=values[1:], left=[0.1])
    location, scale = stats.norm.fit(data)
    normal = _fits(result)["normal"]
    assert normal["parameters"]["loc"] == pytest.approx(location, rel=1e-6)
    assert normal["parameters"]["scale"] == pytest.approx(scale, rel=1e-6)
    distribution = result.distribution("normal")
    assert normal["log_likelihood"] == pytest.approx(
        distribution.logpdf(values[1:]).sum() + distribution.logcdf(0.1), rel=1e-12
    )


def test_censored_both_ways_has_no_positions():
    df = _conductivity([0.1, 0.3, 0.5, 0.8, 1.2, 2.0, 9.0], ["<", *[None] * 5, ">"])
    with pytest.warns(UserWarning, match="fewer than 10"):
        result = ht.stats.fit(df, value="hydraulic_conductivity")
    assert result.groups[0]["positions"] is None
    assert any("no plotting positions" in note for note in result.notes)
    assert len(result.groups[0]["fits"]) == 4


def test_the_minimum_counts_uncensored_values(fresh):
    # site_si: ALV has three N and a refusal; TRC one N.
    spt = fresh("site_si").spt()
    with pytest.raises(HangtuError, match=r"no group has them: ALV \(3\), TRC \(1\)"):
        ht.stats.fit(spt, value="spt_n_capped", by="geology_unit")


def test_a_refusal_with_a_blank_n_is_a_blank():
    df = pd.DataFrame({"spt_n": [*N60, np.nan], "spt_refusal": [False] * 5 + [True]})
    with pytest.warns(UserWarning, match="fewer than 10"):
        counts = ht.stats.fit(df, value="spt_n").groups[0]["counts"]
    assert (counts["count"], counts["count_blank"], counts["count_at_least"]) == (
        5,
        1,
        0,
    )


# AC 9: describe()'s acceptance criteria 6-11 hold for fit().


def test_non_plastic_rows_are_left_out():
    df = pd.DataFrame(
        {
            "plasticity_index": [20, "NP", 30, 25, 18, 22],
            "non_plastic": [False, False, False, False, False, True],
        }
    )
    with pytest.warns(UserWarning, match="fewer than 10"):
        result = ht.stats.fit(df, value="plasticity_index")
    counts = result.groups[0]["counts"]
    assert (counts["count"], counts["count_non_plastic"]) == (4, 2)
    _adds_up(result, [6])


def test_assumed_values_are_left_out_by_default(fresh):
    density = fresh("site_si").particle_density()
    density = pd.concat([density] * 4, ignore_index=True)
    measured = density["particle_density_assumed"] != True  # noqa: E712
    density.loc[measured, "particle_density"] = [2.66, 2.68, 2.70, 2.72]
    with pytest.warns(UserWarning) as record:
        result = ht.stats.fit(density, value="particle_density")
    messages = [str(warning.message) for warning in record]
    assert any("fit() left out 4 assumed values" in m for m in messages)
    counts = result.groups[0]["counts"]
    assert (counts["count"], counts["count_assumed"]) == (4, 4)
    _adds_up(result, [8])
    with pytest.warns(UserWarning, match="fewer than 10"):
        included = ht.stats.fit(density, value="particle_density", include_assumed=True)
    assert included.groups[0]["counts"]["count"] == 8
    assert "Assumed values included: 4." in included.notes
    _adds_up(included, [8], assumed_left_out=False)


def test_band_only_rows_are_left_out():
    df = pd.DataFrame(
        {
            "spt_n60": [10, 20, 30, 40, 50, 10, 12],
            "plasticity_index": [40, 35, 31, 45, 50, 20, 25],
        }
    )
    estimates = correlations.undrained_shear_strength_stroud_1974(
        df, display_units="SI"
    )
    with pytest.warns(UserWarning) as record:
        result = ht.stats.fit(estimates, value="undrained_shear_strength")
    assert any("fit() left out 2 rows" in str(w.message) for w in record)
    counts = result.groups[0]["counts"]
    assert (counts["count"], counts["count_range"], counts["count_censored"]) == (
        5,
        2,
        0,
    )
    _adds_up(result, [7])


def test_sources_arent_pooled_unawares():
    df = pd.DataFrame(
        {
            "undrained_shear_strength": np.arange(10.0, 20.0),
            "correlation_name": ["a"] * 5 + ["b"] * 5,
        }
    )
    df = ht.set_units(df, {"undrained_shear_strength": "kPa"})
    with pytest.raises(HangtuError, match=r"fit\(\) can't pool rows"):
        ht.stats.fit(df, value="undrained_shear_strength")
    result = ht.stats.fit(
        df, value="undrained_shear_strength", pool=["correlation_name"]
    )
    assert result.pooled == ("correlation_name",)
    assert "Pooled across correlation_name: a 5, b 5." in result.notes


def test_pool_needs_a_source_column():
    with pytest.raises(HangtuError, match=r"fit\(\) pools only across source"):
        ht.stats.fit(
            pd.DataFrame({"spt_n60": N60, "geology_unit": ["A"] * 5}),
            value="spt_n60",
            pool="geology_unit",
        )


def test_equal_values_have_no_spread_to_fit():
    df = pd.DataFrame(
        {"spt_n60": [*N60, 7, 7, 7, 7], "geology_unit": ["A"] * 5 + ["B"] * 4}
    )
    with pytest.warns(UserWarning, match="fewer than 10"):
        result = ht.stats.fit(df, value="spt_n60", by="geology_unit")
    assert result.groups[1]["fits"] == []
    assert "B: not fitted, all 4 values are 7, so there is no spread to fit." in (
        result.notes
    )
    with pytest.raises(HangtuError, match=r"could fit no group .* all 4 values"):
        ht.stats.fit(df[df["geology_unit"] == "B"], value="spt_n60")
