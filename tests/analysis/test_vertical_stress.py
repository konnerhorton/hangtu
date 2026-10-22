"""ht.analysis.vertical_stress() (docs/work/m13a-judgments.md, Decisions 6 and 7)."""

import numpy as np
import pytest

from hangtu.analysis._vertical_stress import _integrate

# Criterion 1: BH01, Fill 0-2 m (18), Clay 2-6 m (19, saturated 20), Sand 6-10 m
# (19.5), water level 3.0 m, gamma_w 9.81 kN/m3. By hand:
#   z = 5:  sv = 18*2 + 19*1 + 20*2 = 95;  u = 9.81*2 = 19.62
#   z = 8:  sv = 36 + 19 + 20*3 + 19.5*2 = 154;  u = 9.81*5 = 49.05
#   z = 12: the Sand carried down, sv = 36 + 19 + 60 + 19.5*6 = 232; u = 88.29
GOLDEN = [
    (0.0, 0.0, 0.0, 0.0),
    (1.0, 18.0, 0.0, 18.0),
    (2.5, 45.5, 0.0, 45.5),
    (3.0, 55.0, 0.0, 55.0),
    (5.0, 95.0, 19.62, 75.38),
    (8.0, 154.0, 49.05, 104.95),
    (12.0, 232.0, 88.29, 143.71),
]


def test_integrate_alone_gives_the_golden_values():
    total, pore = _integrate(
        np.array([0.0, 2.0, 6.0]),
        np.array([2.0, 6.0, 12.0]),
        np.array([18.0, 19.0, 19.5]),
        np.array([np.nan, 20.0, np.nan]),
        3.0,
        9.81,
        np.array([row[0] for row in GOLDEN]),
    )
    assert total == pytest.approx([row[1] for row in GOLDEN], abs=1e-9)
    assert pore == pytest.approx([row[2] for row in GOLDEN], abs=1e-9)


def test_integrate_with_water_above_ground():
    # 1.0 m above ground, z = 5 m: sv = 9.81 + 18*2 + 20*3 = 105.81; u = 9.81*6.
    total, pore = _integrate(
        np.array([0.0, 2.0, 6.0]),
        np.array([2.0, 6.0, 10.0]),
        np.array([18.0, 19.0, 19.5]),
        np.array([np.nan, 20.0, np.nan]),
        -1.0,
        9.81,
        np.array([0.0, 5.0]),
    )
    assert total == pytest.approx([9.81, 105.81])
    assert pore == pytest.approx([9.81, 58.86])
