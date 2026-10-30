"""Rank-based tests SciPy doesn't give in the form hangtu reports them.

Spec: docs/work/m15d-compare.md, Decisions 4 and 6. ``brunner_munzel()``
carries its degrees of freedom, an interval for the probability of
superiority, and a permutation p-value for small groups.
"""

import math
from itertools import combinations
from typing import Any

import numpy as np
from scipy import stats as _stats

#: Below this many values in either group, the p-value is by permutation
#: (Karch 2021, p. 8).
PERMUTATION_BELOW = 10
#: The most splits enumerated exactly; beyond, this many random ones.
RESAMPLES = 9999
#: The seed of the random splits, so a result is reproducible.
SEED = 0


def _statistic(
    joint: np.ndarray, first: np.ndarray, second: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return p̂, its standard error and its degrees of freedom, along the last axis.

    ``joint`` holds the joint ranks, ``first`` and ``second`` the values, split
    the same way (Brunner & Munzel 2000, as SciPy's ``brunnermunzel``).
    """
    n1, n2 = first.shape[-1], second.shape[-1]
    joint_1, joint_2 = joint[..., :n1], joint[..., n1:]
    # Each value's placement: the values of the other group below it, ties half.
    placement_1 = joint_1 - _stats.rankdata(first, axis=-1)
    placement_2 = joint_2 - _stats.rankdata(second, axis=-1)
    p_hat = placement_1.mean(axis=-1) / n2
    variance_1 = placement_1.var(axis=-1, ddof=1)
    variance_2 = placement_2.var(axis=-1, ddof=1)
    spread = n1 * variance_1 + n2 * variance_2
    error = np.sqrt(spread) / (n1 * n2)
    with np.errstate(divide="ignore", invalid="ignore"):
        df = spread**2 / (
            (n1 * variance_1) ** 2 / (n1 - 1) + (n2 * variance_2) ** 2 / (n2 - 1)
        )
    return p_hat, error, df


def _signed(p_hat: np.ndarray, error: np.ndarray) -> np.ndarray:
    """Return (p̂ - 0.5) / its standard error: ±inf when the groups don't overlap."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return (p_hat - 0.5) / error


def brunner_munzel(
    first: np.ndarray, second: np.ndarray, alpha: float, labels: tuple[str, str]
) -> tuple[dict[str, Any], list[str]]:
    """Return the Brunner-Munzel test of first against second, and its notes.

    ``probability_of_superiority`` is P(first > second) + ½ P(equal) (Karch
    2021, p. 6, the groups' roles swapped). The statistic is positive when the
    first tends larger. Below 10 values in either group the p-value is by
    permutation of the same statistic, and there is no interval.
    """
    nan = float("nan")
    first, second = np.asarray(first, float), np.asarray(second, float)
    n1, n2 = first.size, second.size
    values = np.concatenate([first, second])
    joint = _stats.rankdata(values)
    p_hat, error, df = (float(x) for x in _statistic(joint, first, second))
    statistic = float(_signed(np.array(p_hat), np.array(error)))
    result = {
        "probability_of_superiority": p_hat,
        "probability_of_superiority_lower": nan,
        "probability_of_superiority_upper": nan,
        "brunner_munzel_statistic": statistic,
        "brunner_munzel_degrees_of_freedom": df if math.isfinite(df) else nan,
        "brunner_munzel_p_value": nan,
        "brunner_munzel_method": None,
    }
    notes = []
    one, two = labels
    if p_hat in (0.0, 1.0):
        above, below = (one, two) if p_hat == 1 else (two, one)
        notes.append(
            f"The groups don't overlap: every value of {above} is above every "
            f"value of {below}."
        )
    if math.isnan(statistic):
        notes.append("No Brunner-Munzel test: every value in both groups is the same.")
        return result, notes
    if min(n1, n2) < PERMUTATION_BELOW:
        p_value, method = _permutation(values, joint, n1, abs(statistic))
        result["brunner_munzel_p_value"] = p_value
        result["brunner_munzel_method"] = method
        notes.append(
            f"Brunner-Munzel p-value by permutation ({method.split(', ')[1]}), "
            f"as a group has fewer than {PERMUTATION_BELOW} values, where the t "
            "approximation is poor (Karch 2021); for the same reason the "
            "probability of superiority has no interval."
        )
        return result, notes
    result["brunner_munzel_method"] = "t"
    if math.isinf(statistic):
        notes.append(
            "No Brunner-Munzel p-value or interval: with no overlap its variance "
            "estimate is 0, which the t approximation can't work with."
        )
        return result, notes
    result["brunner_munzel_p_value"] = float(2 * _stats.t.sf(abs(statistic), df))
    half = float(_stats.t.ppf(1 - alpha / 2, df)) * error
    low, high = p_hat - half, p_hat + half
    if low < 0 or high > 1:
        notes.append(
            "The interval of the probability of superiority is clipped to 0-1."
        )
    result["probability_of_superiority_lower"] = max(low, 0.0)
    result["probability_of_superiority_upper"] = min(high, 1.0)
    return result, notes


def _permutation(
    values: np.ndarray, joint: np.ndarray, n1: int, observed: float
) -> tuple[float, str]:
    """Return the two-sided permutation p-value of |statistic|, and the method.

    Exact over every split when there are at most ``RESAMPLES``, else
    ``RESAMPLES`` random splits from a fixed seed, counting the observed one
    (Neubert & Brunner 2007). Splits whose groups don't overlap are the most
    extreme (|statistic| infinite).
    """
    n = values.size
    if math.comb(n, n1) <= RESAMPLES:
        chosen = np.array(list(combinations(range(n), n1)))
        method = "permutation, exact"
    else:
        rng = np.random.default_rng(SEED)
        chosen = np.array([rng.permutation(n)[:n1] for _ in range(RESAMPLES)])
        method = f"permutation, {RESAMPLES} resamples"
    mask = np.zeros((len(chosen), n), bool)
    mask[np.arange(len(chosen))[:, None], chosen] = True
    order = np.argsort(~mask, axis=1, kind="stable")
    split_values = values[order]
    split_joint = joint[order]
    p_hat, error, _ = _statistic(
        split_joint, split_values[:, :n1], split_values[:, n1:]
    )
    statistics = np.abs(_signed(p_hat, error))
    # A relative tolerance, so a split equal to the observed one counts.
    extreme = int((statistics >= observed * (1 - 1e-12)).sum())
    if method == "permutation, exact":
        return extreme / len(chosen), method
    return (extreme + 1) / (RESAMPLES + 1), method
