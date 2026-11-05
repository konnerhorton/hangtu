"""What the envelope fits share (hangtu.analysis._fit_groups).

The lab's values converted keep their significant figures
(docs/plots/README.md, "Numbers in a box"; M17 (c) close-out review).
"""

import numpy as np
import pytest

from hangtu import units
from hangtu.analysis._fit_groups import _convert_reported, _significant_figures


@pytest.mark.parametrize(
    ("value", "figures"),
    [(64.0, 2), (12.4, 3), (0.05, 1), (1200.0, 2), (1205.0, 4), (60.83, 4), (7.0, 1)],
)
def test_significant_figures_of_a_value_as_read(value, figures):
    assert _significant_figures(value) == figures


def test_converted_lab_values_keep_their_figures():
    values = np.array([64.0, 61.5, np.nan, 0.0])
    converted = _convert_reported(
        values, units.parse_unit("MPa"), "stress", units.parse_unit("psi")
    )
    # 64 MPa = 9282.42 psi, 61.5 MPa = 8919.82 psi (1 MPa = 145.037738 psi).
    np.testing.assert_array_equal(converted[[0, 1, 3]], [9300.0, 8920.0, 0.0])
    assert np.isnan(converted[2])
