"""Dunn's test and Holm's adjustment (m15d-compare, Decision 6, AC 5, 6 and 8)."""

import numpy as np
import pytest

from hangtu.stats._rank import dunn, dunn_z, holm, tie_term

A = np.array([12.0, 15, 18, 20, 22])
B = np.array([25.0, 28, 30, 35, 41, 44])
C = np.array([14.0, 16, 17, 21])

#: Helsel et al. (2020) Table 7.4: the ranks of fecal coliform counts.
SUMMER = np.array([6.0, 12, 15, 18, 21, 24])
FALL = np.array([5.0, 8.5, 11, 14, 19.5, 22])
WINTER = np.array([2.0, 4, 8.5, 13, 16, 19.5])
SPRING = np.array([1.0, 3, 7, 10, 17, 23])


def test_dunn_on_three_groups_without_ties():
    # AC 5: by hand from Decision 6's formula, N = 15, no ties.
    means, pairs = dunn([A, B, C])
    assert means == pytest.approx([5.2, 12.5, 4.75], rel=1e-12)
    z = {(i, j): value for i, j, value, _ in pairs}
    p = {(i, j): value for i, j, _, value in pairs}
    assert z[0, 1] == pytest.approx(-2.6957037, abs=5e-8)
    assert z[1, 2] == pytest.approx(2.6846788, abs=5e-8)
    assert z[0, 2] == pytest.approx(0.15, rel=1e-9)
    assert p[0, 1] == pytest.approx(0.00702401, abs=5e-9)
    assert p[1, 2] == pytest.approx(0.00725995, abs=5e-9)
    assert p[0, 2] == pytest.approx(0.88076462, abs=5e-9)
    assert [pair[:2] for pair in pairs] == [(0, 1), (0, 2), (1, 2)]


def test_holm_on_three_groups():
    # AC 5: 3 x 0.00702401, then max(2 x 0.00725995, 0.02107204), then 0.880...
    adjusted = holm([0.0070240126187334495, 0.8807646152595149, 0.0072599549881905605])
    assert adjusted == pytest.approx([0.02107204, 0.88076462, 0.02107204], abs=5e-9)


def test_dunn_and_holm_with_ties_on_helsel_table_7_4():
    # AC 6: two pairs of tied ranks (8.5, 19.5): Σ(t³ - t) = 12.
    groups = [SUMMER, FALL, WINTER, SPRING]
    assert tie_term(np.concatenate(groups)) == 12
    _, pairs = dunn(groups)
    z = {(i, j): value for i, j, value, _ in pairs}
    assert z[0, 3] == pytest.approx(1.4294907, abs=5e-8)  # Summer-Spring
    adjusted = holm([p for *_, p in pairs])
    for value in adjusted:
        assert value == 1 or value == pytest.approx(0.91717953, abs=5e-9)


def test_dunn_reproduces_dinno_example_1():
    # AC 8: from the printed rank sums and the tie term the printed χ² imply
    # (17.041 untied, 17.062 tied, N = 50): NE-N Cntrl z, Dinno's 2.698212.
    total = 50
    ties = (1 - 17.041 / 17.062) * (total**3 - total)
    z = dunn_z(376.5 / 9, 294.0 / 12, 9, 12, total, ties)
    assert z == pytest.approx(2.698212, abs=1e-4)


def test_holm_keeps_order_and_caps_at_one():
    adjusted = holm([0.04, 0.01, 0.03, 0.5])
    # Sorted: 0.01 x 4, 0.03 x 3, 0.04 x 2, 0.5 x 1, with the running maximum.
    assert adjusted == pytest.approx([0.09, 0.04, 0.09, 0.5])
    assert holm([0.6, 0.7]) == [1.0, 1.0]
