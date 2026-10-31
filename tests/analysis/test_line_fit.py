"""The line-fit core (docs/work/m11b-envelope-fit.md, Decision 3; AC 1-3).

Golden values by hand. Golden 1's points (100, 300) and (200, 500) kPa are
s′ = 200, 350 and t = 100, 150.
"""

import json
import math

import numpy as np
import pytest

from hangtu.analysis._derived import _DerivedResult
from hangtu.analysis._line_fit import line_fit

S = np.array([200.0, 350.0])
T = np.array([100.0, 150.0])


def test_free_line_golden_1():
    # b = Sxy / Sxx = (-75·-25 + 75·25) / (2·75²) = 1/3; a = 125 - 275/3.
    line = line_fit(S, T)
    assert line.slope == pytest.approx(1 / 3, rel=1e-12)
    assert line.intercept == pytest.approx(33.333333333, rel=1e-9)
    assert line.r_squared == pytest.approx(1.0, rel=1e-12)
    assert line.count == 2
    assert not line.fixed_intercept
    assert line.no_fit_reason is None
    assert np.allclose(line.residuals, 0.0, atol=1e-9)


def test_line_through_origin_golden_1():
    # b = Σxy / Σx² = 72500 / 162500 = 29/65; R² = 1 - (10.769231² + 6.1538462²)/1250.
    line = line_fit(S, T, intercept=0)
    assert line.slope == pytest.approx(29 / 65, rel=1e-12)
    assert line.intercept == 0
    assert line.fixed_intercept
    assert line.r_squared == pytest.approx(57 / 65, rel=1e-9)
    assert line.residuals == pytest.approx((100 - 200 * 29 / 65, 150 - 350 * 29 / 65))


def test_golden_2_passes_through_origin_both_ways():
    # (100, 300) and (200, 600) kPa: s′ = 200, 400; t = 100, 200, so t = 0.5 s′.
    for intercept in (None, 0):
        line = line_fit(
            np.array([200.0, 400.0]), np.array([100.0, 200.0]), intercept=intercept
        )
        assert line.slope == pytest.approx(0.5, rel=1e-12)
        assert line.intercept == pytest.approx(0.0, abs=1e-12)


def test_one_point_with_a_fixed_intercept():
    line = line_fit(np.array([200.0]), np.array([100.0]), intercept=0)
    assert line.slope == pytest.approx(0.5, rel=1e-12)
    assert line.count == 1
    assert math.isnan(line.r_squared)


def test_all_y_equal_gives_nan_r_squared():
    line = line_fit(np.array([1.0, 2.0]), np.array([3.0, 3.0]))
    assert line.slope == 0
    assert line.intercept == 3
    assert math.isnan(line.r_squared)


def test_poor_line_through_origin_has_negative_r_squared():
    # b = (10 + 18) / 5 = 5.6; residuals 4.4 and -2.2; Σ(y - ȳ)² = 0.5;
    # R² = 1 - 24.2 / 0.5 = -47.4.
    line = line_fit(np.array([1.0, 2.0]), np.array([10.0, 9.0]), intercept=0)
    assert line.slope == pytest.approx(5.6, rel=1e-12)
    assert line.r_squared == pytest.approx(-47.4, rel=1e-12)


@pytest.mark.parametrize(
    ("x", "y", "intercept", "reason"),
    [
        ([200.0], [100.0], None, "1 point: a line needs at least 2"),
        ([], [], None, "0 points: a line needs at least 2"),
        ([200.0, 200.0], [100.0, 50.0], None, "all points at the same s′"),
        ([], [], 0, "no points"),
        ([0.0, 0.0], [1.0, 2.0], 0, "all points at s′ = 0"),
    ],
)
def test_cant_fit(x, y, intercept, reason):
    line = line_fit(np.array(x), np.array(y), intercept=intercept, x_name="s′")
    assert line.no_fit_reason == reason
    assert math.isnan(line.slope)
    assert math.isnan(line.intercept)
    assert math.isnan(line.r_squared)
    assert line.residuals == ()
    assert line.count == len(x)


def test_derived_result_base():
    from dataclasses import dataclass

    @dataclass(frozen=True, repr=False)
    class _Example(_DerivedResult):
        value: float

        def __str__(self):
            return f"value = {self.value}"

    result = _Example("example", "kPa", ("a note",), {}, "0.0.0", math.nan)
    assert result.kind == "derived"
    assert repr(result) == "value = nan"
    assert result._repr_html_() == "<pre>value = nan</pre>"
    record = result.to_dict()
    assert record["kind"] == "derived"
    assert record["value"] is None
    json.dumps(record)
