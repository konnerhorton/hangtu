"""fit(): Anderson-Darling statistic and bootstrap p-value (m15c-fit.md, Decision 7)."""

import numpy as np
import pytest
from scipy import stats

import hangtu as ht

STRENGTH = [10, 12, 15, 20, 23]
NORMAL_30 = np.random.default_rng(7).normal(30, 5, 30)
EXPONENTIAL_30 = np.random.default_rng(7).exponential(10, 30)


def _fits(result):
    return {fit["distribution"]: fit for fit in result.groups[0]["fits"]}


@pytest.fixture(scope="module")
def strength():
    with pytest.warns(UserWarning, match="fewer than 10"):
        return _fits(ht.stats.fit(STRENGTH))


@pytest.fixture(scope="module")
def normal_30():
    return ht.stats.fit(NORMAL_30, distributions=["normal"])


def test_statistic_of_five_values(strength):
    # AC 1, hand-calculated in the spec.
    assert strength["normal"]["anderson_darling_statistic"] == pytest.approx(
        0.26640897, rel=1e-6
    )
    assert strength["lognormal"]["anderson_darling_statistic"] == pytest.approx(
        0.23962352, rel=1e-6
    )


def test_every_fit_has_a_p_value(strength):
    for fit in strength.values():
        assert 0 < fit["anderson_darling_p_value"] <= 1
        # (1 + count) / 1000 is a multiple of 1/1000.
        assert fit["anderson_darling_p_value"] * 1000 == pytest.approx(
            round(fit["anderson_darling_p_value"] * 1000)
        )


def test_p_value_agrees_with_scipy(normal_30):
    # AC 3: within 0.03 of goodness_of_fit at 9999 samples. SciPy refits the
    # normal with the n - 1 standard deviation, so the statistics differ a little.
    fit = _fits(normal_30)["normal"]
    scipy = stats.goodness_of_fit(
        stats.norm,
        NORMAL_30,
        statistic="ad",
        n_mc_samples=9999,
        random_state=np.random.default_rng(1),
    )
    assert fit["anderson_darling_p_value"] == pytest.approx(scipy.pvalue, abs=0.03)


def test_an_exponential_sample_rejects_the_normal():
    result = ht.stats.fit(EXPONENTIAL_30, distributions=["normal"])
    assert _fits(result)["normal"]["anderson_darling_p_value"] < 0.05


def test_the_same_data_give_the_same_p_value(normal_30):
    again = ht.stats.fit(NORMAL_30, distributions=["normal"])
    assert (
        _fits(again)["normal"]["anderson_darling_p_value"]
        == _fits(normal_30)["normal"]["anderson_darling_p_value"]
    )


def test_the_notes_say_what_a_p_value_means(normal_30):
    assert any("evidence against" in note for note in normal_30.notes)
