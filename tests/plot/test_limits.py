import math

import matplotlib.pyplot as plt
import pytest
from hypothesis import given
from hypothesis import strategies as st

from ags_kit.plot.common import (
    apply_vertical_axis,
    log_limits,
    nice_limits,
    nice_step,
    set_log_axis,
)


@pytest.mark.parametrize(
    ("vmin", "vmax", "start_at_zero", "expected"),
    [
        (0.3, 7.8, True, (0, 8)),  # P00 §14
        (0.0, 100.0, True, (0, 100)),
        (12.3, 47.9, False, (10, 50)),  # padded to (10.52, 49.68), step 10
        (12.3, 47.9, True, (0, 50)),
        (-35.2, 12.4, False, (-40, 20)),  # elevations, step 10
        (-2.0, 5.0, True, (-4, 6)),  # negative values: no zero start
        (0.012, 0.087, True, (0, 0.1)),  # step 0.01 gives 10 ticks
        (7.3, 7.3, False, (6, 8.5)),  # single point: 6.3 to 8.3, step 0.5
        (0.0, 0.0, True, (0, 1)),
        (250.0, 250.0, True, (150, 350)),  # ± one step of 100
        (5e-324, 5e-324, False, (-1, 1)),  # subnormal: the step underflows
    ],
)
def test_nice_limits(vmin, vmax, start_at_zero, expected):
    assert nice_limits(vmin, vmax, start_at_zero=start_at_zero) == pytest.approx(
        expected
    )


def test_single_point_uses_the_typical_range():
    assert nice_limits(3e-5, 3e-5, start_at_zero=True, typical=(1e-9, 1e-2)) == (
        1e-9,
        1e-2,
    )
    assert nice_limits(5.0, 5.0, start_at_zero=True, typical=(0, 2)) == (0, 5.0)


@pytest.mark.parametrize("bad", [(2.0, 1.0), (math.nan, 1.0), (0.0, math.inf)])
def test_nice_limits_rejects_bad_ranges(bad):
    with pytest.raises(ValueError, match="finite vmin <= vmax"):
        nice_limits(*bad, start_at_zero=False)


values = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False)


@given(values, values, st.booleans())
def test_nice_limits_enclose_the_data_with_4_to_8_ticks(a, b, start_at_zero):
    vmin, vmax = sorted((a, b))
    if 0 < vmax - vmin < 1e-6 * max(abs(vmin), abs(vmax), 1):
        return  # ranges below float precision of the values are out of scope
    lo, hi = nice_limits(vmin, vmax, start_at_zero=start_at_zero)
    assert lo <= vmin and hi >= vmax
    ticks = round((hi - lo) / nice_step(lo, hi)) + 1
    assert 4 <= ticks <= 8


@pytest.mark.parametrize(
    ("vmin", "vmax", "expected"),
    [
        (2e-7, 3e-4, (1e-7, 1e-3)),  # P00 §14
        (5e-6, 8e-6, (1e-6, 1e-4)),  # P00 §14: one decade extended to two
        (1e-3, 1e-1, (1e-3, 1e-1)),  # exact decades are kept
        (1000.0, 1000.0, (1e3, 1e5)),
        (0.5, 300.0, (0.1, 1e3)),
    ],
)
def test_log_limits(vmin, vmax, expected):
    assert log_limits(vmin, vmax) == pytest.approx(expected)


@pytest.mark.parametrize("bad", [(0.0, 1.0), (-1.0, 1.0), (2.0, 1.0)])
def test_log_limits_reject_non_positive_values(bad):
    with pytest.raises(ValueError, match="0 < vmin <= vmax"):
        log_limits(*bad)


def test_log_axis_labels_decades_only():
    fig, ax = plt.subplots()
    ax.plot([2e-7, 3e-4], [0, 1])
    set_log_axis(ax, "x", log_limits(2e-7, 3e-4))
    fig.canvas.draw()
    assert ax.get_xscale() == "log"
    assert ax.get_xlim() == pytest.approx((1e-7, 1e-3))
    majors = [tick for tick in ax.xaxis.get_majorticklocs() if 1e-7 <= tick <= 1e-3]
    assert majors == pytest.approx([1e-7, 1e-6, 1e-5, 1e-4, 1e-3])
    assert all(not label.get_text() for label in ax.xaxis.get_minorticklabels())
    minors = [t for t in ax.xaxis.get_minorticklocs() if 1e-7 < t < 1e-6]
    assert minors == pytest.approx([k * 1e-7 for k in range(2, 10)])


def test_depth_axis_points_down_from_zero():
    _, ax = plt.subplots()
    assert apply_vertical_axis(ax, "depth", 1.5, 42.0) == (0, 50)
    assert ax.get_ylim() == (50, 0)
    ticks = [tick for tick in ax.yaxis.get_majorticklocs() if 0 <= tick <= 50]
    assert ticks == [0, 10, 20, 30, 40, 50]


def test_elevation_axis_points_up_with_padding():
    _, ax = plt.subplots()
    assert apply_vertical_axis(ax, "elevation", -35.2, 12.4) == (-40, 20)
    assert ax.get_ylim() == (-40, 20)


def test_vertical_axis_rejects_other_names():
    _, ax = plt.subplots()
    with pytest.raises(ValueError, match='"depth" or "elevation"'):
        apply_vertical_axis(ax, "height", 0, 1)
