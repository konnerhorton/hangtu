"""P01 log axes and fixed limits (P01 §6, §11; P00 §8, §9)."""

import math
from functools import partial

import numpy as np
import pytest

import hangtu as ht

K = [1e-5, 3e-6, 2e-4, 5e-7]  # cm/s
K_PRESET = {"preset": "hydraulic_conductivity"}


def test_log_axis_shows_whole_decades_labeled_ten_to_the_n(frame):
    df = frame("hydraulic_conductivity", K, "cm/s")
    _, ax = ht.plot.profile(df, "hydraulic_conductivity", **K_PRESET)
    lo, hi = ax.get_xlim()
    assert (lo, hi) == pytest.approx((1e-7, 1e-3))
    assert math.log10(lo).is_integer() and math.log10(hi).is_integer()
    assert "10^{-5}" in ax.xaxis.get_major_formatter()(1e-5)


def test_k_in_m_per_s_displays_in_cm_per_s(frame, points):
    # P01 §12: k = 1.0e-5 m/s displays as 1.0e-3 cm/s.
    df = frame("hydraulic_conductivity", [1.0e-5] * 4, "m/s")
    _, ax = ht.plot.profile(df, "hydraulic_conductivity", **K_PRESET)
    assert points(ax)[:, 0].tolist() == pytest.approx([1.0e-3] * 4)
    assert ax.get_xlabel() == "Hydraulic conductivity, k (cm/s)"


def test_log_without_a_preset(frame):
    df = frame("hydraulic_conductivity", [1e-5, 3e-6, 2e-4, 5e-7], "cm/s")
    _, ax = ht.plot.profile(df, "hydraulic_conductivity", log=True)
    assert ax.get_xscale() == "log"
    _, ax = ht.plot.profile(df, "hydraulic_conductivity", **K_PRESET, log=False)
    assert ax.get_xscale() == "linear"


def test_blank_and_nonpositive_values_on_log_are_counted(frame, points):
    df = frame("hydraulic_conductivity", [1e-5, np.nan, 0.0, -1e-6], "cm/s")
    _, ax = ht.plot.profile(df, "hydraulic_conductivity", **K_PRESET)
    assert ax.ags_notes == {"nan": 1, "log_nonpositive": 2}
    assert len(points(ax)) == 1
    footnote = ax.texts[-1].get_text()
    assert "1 blank value not shown" in footnote
    assert "2 values ≤ 0 not shown on log axis" in footnote


def test_values_beyond_xlim_and_ylim_are_drawn_at_the_edge_and_counted(frame):
    _, ax = ht.plot.profile(
        frame(), "undrained_shear_strength", vs="depth", xlim=(0, 1200), ylim=(0, 12)
    )
    # 1500 psf at 15 ft and 2000 psf at 20 ft are beyond both limits.
    assert ax.ags_notes == {"beyond_limit": 2}
    assert ax.get_xlim() == (0.0, 1200.0)
    assert ax.get_ylim() == (12.0, 0.0)
    edge = [c for c in ax.collections if len(c.get_facecolor()) == 0]
    assert np.concatenate([c.get_offsets() for c in edge]).tolist() == [
        [1200.0, 12.0],
        [1200.0, 12.0],
    ]


def test_edge_counts_on_a_log_axis(frame):
    df = frame("hydraulic_conductivity", K, "cm/s")
    _, ax = ht.plot.profile(df, "hydraulic_conductivity", **K_PRESET, xlim=(1e-6, 1e-4))
    assert ax.ags_notes == {"beyond_limit": 2}


@pytest.mark.parametrize(
    ("xlim", "message"),
    [((5, 5), "two different numbers"), ((0, "a"), "two different numbers")],
)
def test_bad_limits_are_an_error(xlim, message, frame):
    with pytest.raises(ht.HangtuError, match=message):
        ht.plot.profile(frame(), "undrained_shear_strength", xlim=xlim)


def test_log_limits_must_be_positive(frame):
    df = frame("hydraulic_conductivity", K, "cm/s")
    with pytest.raises(ht.HangtuError, match="greater than 0"):
        ht.plot.profile(df, "hydraulic_conductivity", log=True, xlim=(0, 1))


def test_a_single_log_point_uses_the_typical_decades(frame):
    df = frame("hydraulic_conductivity", [1e-5] * 4, "cm/s").iloc[:1]
    _, ax = ht.plot.profile(df, "hydraulic_conductivity", **K_PRESET)
    assert ax.get_xlim() == pytest.approx((1e-9, 1.0))


def test_us_and_si_count_the_same(assert_us_si_equivalent, frame):
    df = frame("hydraulic_conductivity", [1e-5, np.nan, 0.0, 2e-4], "cm/s")
    plot = partial(ht.plot.profile, value="hydraulic_conductivity", **K_PRESET)
    assert_us_si_equivalent(plot, df, ("hydraulic_conductivity", "length"))
