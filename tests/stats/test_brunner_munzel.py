"""The Brunner-Munzel test in compare() (m15d-compare, Decision 4, AC 3 and 13)."""

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import hangtu as ht

KPA_PER_PSF = 0.04788026


def _compare(first, second, **kwargs):
    return ht.stats.compare(first, second, significance_level=0.05, **kwargs)


def _row(result):
    return result.to_frame().iloc[0]


def test_helsel_by_the_t_approximation(helsel):
    # AC 3: 76.5 of the 100 pairs favor industrial (ties half), counted from
    # Example 5.1's ranks; the statistic and p are SciPy's with the groups
    # swapped, positive when the first tends larger.
    industrial, residential = helsel
    row = _row(_compare(industrial, residential))
    assert row["probability_of_superiority"] == pytest.approx(0.765, rel=1e-12)
    assert row["brunner_munzel_statistic"] == pytest.approx(2.2392145, abs=5e-8)
    assert row["brunner_munzel_p_value"] == pytest.approx(0.0403155, abs=5e-8)
    scipy = stats.brunnermunzel(residential, industrial)
    assert row["brunner_munzel_statistic"] == pytest.approx(scipy.statistic, rel=1e-9)
    assert row["brunner_munzel_p_value"] == pytest.approx(scipy.pvalue, rel=1e-9)
    assert row["brunner_munzel_method"] == "t"
    # The degrees of freedom reproduce the p-value.
    df = row["brunner_munzel_degrees_of_freedom"]
    assert 2 * stats.t.sf(row["brunner_munzel_statistic"], df) == pytest.approx(
        scipy.pvalue, rel=1e-9
    )


def test_helsel_interval_is_clipped(helsel):
    # AC 3: p̂ ± t * (p̂ - 0.5) / statistic, clipped to [0, 1].
    result = _compare(*helsel)
    row = _row(result)
    error = (0.765 - 0.5) / row["brunner_munzel_statistic"]
    half = stats.t.ppf(0.975, row["brunner_munzel_degrees_of_freedom"]) * error
    assert row["probability_of_superiority_lower"] == pytest.approx(0.765 - half)
    assert 0.765 + half > 1
    assert row["probability_of_superiority_upper"] == 1
    assert "The interval of the probability of superiority is clipped to 0-1." in (
        result.notes
    )


def test_small_groups_by_exact_permutation():
    # AC 3: 5 against 4, 126 splits; 96 at least as extreme.
    with pytest.warns(UserWarning, match="fewer than 5"):
        result = _compare([12, 15, 18, 20, 22], [14, 16, 17, 21])
    row = _row(result)
    assert row["probability_of_superiority"] == pytest.approx(0.55, rel=1e-12)
    assert row["brunner_munzel_statistic"] == pytest.approx(0.2245444, abs=5e-8)
    assert row["brunner_munzel_p_value"] == pytest.approx(96 / 126, rel=1e-12)
    assert row["brunner_munzel_method"] == "permutation, exact"
    assert np.isnan(row["probability_of_superiority_lower"])
    assert any("by permutation (exact)" in note for note in result.notes)
    assert any("has no interval" in note for note in result.notes)


def test_groups_that_dont_overlap_by_permutation():
    # AC 3: p̂ 0, statistic -inf, p 2/20; no warning reaches the user (the
    # suite turns warnings into errors).
    with pytest.warns(UserWarning, match="fewer than 5"):
        result = _compare([1, 2, 3], [4, 5, 6])
    row = _row(result)
    assert row["probability_of_superiority"] == 0
    assert row["brunner_munzel_statistic"] == -np.inf
    assert row["brunner_munzel_p_value"] == pytest.approx(0.1, rel=1e-12)
    assert (
        "The groups don't overlap: every value of second is above every value of "
        "first." in result.notes
    )


def test_twelve_against_twelve_that_dont_overlap():
    # AC 3: the p-value is blank, with the note.
    result = _compare(np.arange(12.0) + 20, np.arange(12.0))
    row = _row(result)
    assert row["probability_of_superiority"] == 1
    assert row["brunner_munzel_statistic"] == np.inf
    assert np.isnan(row["brunner_munzel_p_value"])
    assert np.isnan(row["probability_of_superiority_lower"])
    assert any("No Brunner-Munzel p-value or interval" in n for n in result.notes)
    assert "every value of first is above every value of second" in str(result)


def test_many_splits_are_sampled_from_a_fixed_seed():
    first, second = np.arange(9.0), np.arange(30.0) + 3.5
    one, two = _row(_compare(first, second)), _row(_compare(first, second))
    assert one["brunner_munzel_method"] == "permutation, 9999 resamples"
    assert one["brunner_munzel_p_value"] == two["brunner_munzel_p_value"]
    assert one["brunner_munzel_p_value"] == pytest.approx(1 / 10000)


def test_reversing_the_groups_gives_one_minus_p_hat(three_groups):
    # AC 10: groups=("C", "A") gives 1 - p̂.
    def run(groups):
        with pytest.warns(UserWarning, match="fewer than 5"):
            return _row(
                ht.stats.compare(
                    three_groups,
                    value="undrained_shear_strength",
                    by="geology_unit",
                    groups=groups,
                    significance_level=0.05,
                )
            )

    forward, backward = run(("A", "C")), run(("C", "A"))
    assert forward["probability_of_superiority"] == pytest.approx(0.55)
    assert backward["probability_of_superiority"] == pytest.approx(0.45)
    assert backward["brunner_munzel_statistic"] == pytest.approx(
        -forward["brunner_munzel_statistic"]
    )
    assert backward["brunner_munzel_p_value"] == pytest.approx(
        forward["brunner_munzel_p_value"]
    )


def test_units_and_log_leave_the_rank_test_unchanged(helsel):
    # AC 13: p̂ and the statistic don't change with units; ranks don't change
    # on a log scale.
    def frame(values, unit):
        return ht.set_units(
            pd.DataFrame({"undrained_shear_strength": values}),
            {"undrained_shear_strength": unit},
        )

    frames = [frame(values, "psf") for values in helsel]
    psf = _row(_compare(*frames, value="undrained_shear_strength"))
    kpa = _row(_compare(*frames, value="undrained_shear_strength", display_units="SI"))
    logged = _row(_compare(*helsel, log=True))
    names = [
        "probability_of_superiority",
        "probability_of_superiority_lower",
        "brunner_munzel_statistic",
        "brunner_munzel_degrees_of_freedom",
        "brunner_munzel_p_value",
    ]
    for name in names:
        assert kpa[name] == pytest.approx(psf[name], rel=1e-9)
        assert logged[name] == pytest.approx(psf[name], rel=1e-9)
