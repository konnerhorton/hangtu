"""Plotting positions for the Q-Q panel (docs/work/m15c-fit.md, Decision 8)."""

from itertools import pairwise

import numpy as np
import pytest

from hangtu.stats._positions import plotting_positions

STRENGTH = np.array([10.0, 12, 15, 20, 23])
NONE = np.empty(0)


def test_hazen_without_censoring():
    # AC 5: (i - 0.5) / n.
    values, positions = plotting_positions(STRENGTH[::-1], NONE, NONE)
    assert values.tolist() == STRENGTH.tolist()
    assert positions == pytest.approx([0.1, 0.3, 0.5, 0.7, 0.9], rel=1e-12)


def test_right_censored_above_every_value():
    # AC 5: Kaplan-Meier steps of 1/7, midpoints (2i - 1) / 14.
    _, positions = plotting_positions(STRENGTH, NONE, np.array([30.0, 30.0]))
    assert positions == pytest.approx(np.arange(1, 10, 2) / 14, rel=1e-12)


def test_right_censored_among_the_values():
    # Censored at 13 of 7: F = 1/7, 2/7, then 1 - (5/7)(3/4) = 13/28 at 15,
    # 1 - (5/7)(2/4) = 9/14 at 20, 1 - (5/7)(1/4) = 23/28 at 23.
    _, positions = plotting_positions(STRENGTH, NONE, np.array([13.0, 30.0]))
    steps = [0, 1 / 7, 2 / 7, 13 / 28, 9 / 14, 23 / 28]
    midpoints = [(a + b) / 2 for a, b in pairwise(steps)]
    assert positions == pytest.approx(midpoints, rel=1e-12)


def test_left_censored_mirrors_right():
    _, positions = plotting_positions(STRENGTH, np.array([5.0, 5.0]), NONE)
    assert positions == pytest.approx(np.arange(5, 14, 2) / 14, rel=1e-12)


def test_ties_split_their_step():
    _, positions = plotting_positions(np.array([10.0, 12, 12, 20]), NONE, NONE)
    assert positions == pytest.approx([0.125, 0.375, 0.625, 0.875], rel=1e-12)
    _, positions = plotting_positions(
        np.array([10.0, 12, 12, 20]), NONE, np.array([30.0])
    )
    assert positions == pytest.approx(np.arange(1, 8, 2) / 10, rel=1e-12)


def test_censored_both_ways_has_none():
    assert plotting_positions(STRENGTH, np.array([5.0]), np.array([30.0])) is None
