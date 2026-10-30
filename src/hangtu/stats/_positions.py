"""Plotting positions for P08's Q-Q panel (docs/work/m15c-fit.md, Decision 8)."""

import numpy as np
from scipy import stats as _stats


def plotting_positions(
    exact: np.ndarray, left: np.ndarray, right: np.ndarray
) -> tuple[np.ndarray, np.ndarray] | None:
    """Return the uncensored values in order and the probability of each.

    Without censoring, Hazen's (i - 0.5)/n (Hazen 1914, p. 1549): each value
    sits in the middle of its strip. With right-censored values, the middle
    of each value's step in the Kaplan-Meier estimate of the CDF
    (``scipy.stats.ecdf``), which reduces to Hazen's without censoring;
    tied values split their step equally. With left-censored values, the
    same on -x. Censored both ways: None, since there is no estimator for
    that here.
    """
    if left.size and right.size:
        return None
    if left.size:
        values, positions = plotting_positions(-exact, np.empty(0), -left)
        return -values[::-1], 1 - positions[::-1]
    x = np.sort(np.asarray(exact, float))
    if not right.size:
        return x, (np.arange(1, x.size + 1) - 0.5) / x.size
    estimate = _stats.ecdf(_stats.CensoredData(uncensored=x, right=right)).cdf
    after = estimate.probabilities
    before = np.concatenate([[0.0], after[:-1]])
    positions = np.empty(x.size)
    for value, low, high in zip(estimate.quantiles, before, after, strict=True):
        tied = x == value
        count = tied.sum()
        positions[tied] = low + (np.arange(1, count + 1) - 0.5) / count * (high - low)
    return x, positions
