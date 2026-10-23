"""P01 value ranges: <value>_lower and <value>_upper (P01 §3, §7, §11, §12; M13 b2)."""

import numpy as np
import pytest

import hangtu as ht
from hangtu.errors import ColumnError

LOWER, UPPER = "undrained_shear_strength_lower", "undrained_shear_strength_upper"
NAN = np.nan


def ranged(frame, values, lower, upper, **columns):
    """Profile data with bounds; every s_u column in psf."""
    df = frame(values=values, **{LOWER: lower, UPPER: upper}, **columns)
    return ht.set_units(df, {LOWER: "psf", UPPER: "psf"})


def bars(ax):
    """Each range bar drawn, as (x0, x1, y), sorted."""
    found = []
    for line in ax.lines:
        if line.get_gid() != "value_range":
            continue
        xs, ys = line.get_xdata(), line.get_ydata()
        for i in range(0, len(xs), 3):
            found.append((float(xs[i]), float(xs[i + 1]), float(ys[i])))
    return sorted(found)


def carets(ax):
    """Each bound drawn alone, as (x, y), sorted."""
    found = []
    for collection in ax.collections:
        if collection.get_gid() != "value_range_bound":
            continue
        for x, y in collection.get_offsets():
            found.append((float(x), float(y)))
    return sorted(found)


def points(ax):
    """The value markers drawn, as (x, y), sorted."""
    found = []
    for collection in ax.collections:
        if collection.get_gid() is None and collection.get_label() in ("Fill", "Clay"):
            found += [(float(x), float(y)) for x, y in collection.get_offsets()]
    return sorted(found)


def legend(ax):
    return [t.get_text() for t in ax.get_legend().get_texts()]


def stats_lines(ax):
    (box,) = [text for text in ax.texts if text.get_bbox_patch() is not None]
    return box.get_text().splitlines()


# --- drawing ------------------------------------------------------------------------


def test_both_bounds_draw_a_bar_with_the_marker_at_the_value(frame):
    df = ranged(
        frame,
        values=[500.0, NAN, 1500.0, 2000.0],
        lower=[400.0, 800.0, NAN, NAN],
        upper=[600.0, 1200.0, NAN, NAN],
    )
    _, ax = ht.plot.profile(df, "undrained_shear_strength", vs="depth")
    assert bars(ax) == [(400.0, 600.0, 5.0), (800.0, 1200.0, 10.0)]
    # Depth 10 has no central value: the bar alone, no marker and no midpoint.
    assert points(ax) == [(500.0, 5.0), (1500.0, 15.0), (2000.0, 20.0)]
    assert ax.ags_notes == {"value_range": 2}
    assert "range" in legend(ax)


def test_one_bound_draws_a_caret_and_no_bar(frame):
    df = ranged(
        frame,
        values=[NAN, NAN, 1500.0, 2000.0],
        lower=[4000.0, NAN, NAN, NAN],
        upper=[NAN, 250.0, NAN, NAN],
    )
    _, ax = ht.plot.profile(df, "undrained_shear_strength", vs="depth")
    assert bars(ax) == []
    assert carets(ax) == [(250.0, 10.0), (4000.0, 5.0)]
    # ▷ at the lower bound alone, ◁ at the upper: the tips point opposite ways.
    tips = {
        float(c.get_offsets()[0][0]): c.get_paths()[0].vertices
        for c in ax.collections
        if c.get_gid() == "value_range_bound"
    }
    right = tips[4000.0][np.abs(tips[4000.0][:, 1]) < 1e-9, 0]
    left = tips[250.0][np.abs(tips[250.0][:, 1]) < 1e-9, 0]
    assert right.max() > 0 and left.min() < 0
    assert ax.ags_notes == {"value_range": 2}


def test_rows_with_bounds_and_no_value_are_not_counted_blank(frame):
    df = ranged(
        frame,
        values=[NAN, NAN, NAN, 2000.0],
        lower=[400.0, NAN, NAN, NAN],
        upper=[600.0, NAN, NAN, NAN],
    )
    _, ax = ht.plot.profile(df, "undrained_shear_strength", vs="depth")
    assert ax.ags_notes == {"value_range": 1, "nan": 2}


def test_the_x_limits_include_every_bound(frame):
    df = ranged(
        frame,
        values=[500.0, 1000.0, 1500.0, 2000.0],
        lower=[NAN, 100.0, NAN, NAN],
        upper=[NAN, 5200.0, NAN, NAN],
    )
    _, ax = ht.plot.profile(df, "undrained_shear_strength", vs="depth")
    low, high = ax.get_xlim()
    assert low <= 100.0 and high >= 5200.0


def test_a_bound_beyond_xlim_is_drawn_at_the_edge_and_the_row_counted_once(frame):
    df = ranged(
        frame,
        values=[500.0, NAN, 1500.0, 2000.0],
        lower=[400.0, NAN, -100.0, NAN],
        upper=[9000.0, 6000.0, 9500.0, NAN],
    )
    _, ax = ht.plot.profile(df, "undrained_shear_strength", vs="depth", xlim=(0, 3000))
    # Depth 5: the bar stops at the edge. Depth 15: both ends beyond, one row.
    assert bars(ax) == [(0.0, 3000.0, 15.0), (400.0, 3000.0, 5.0)]
    assert ax.ags_notes == {"value_range": 3, "beyond_limit": 3}


def test_a_lower_bound_of_zero_on_a_log_axis_is_drawn_at_the_edge(frame):
    df = ranged(
        frame,
        values=[NAN, 1000.0, 1500.0, 2000.0],
        lower=[0.0, NAN, NAN, NAN],
        upper=[250.0, NAN, NAN, NAN],
    )
    _, ax = ht.plot.profile(df, "undrained_shear_strength", vs="depth", log=True)
    ((x0, x1, y),) = bars(ax)
    assert x0 == pytest.approx(ax.get_xlim()[0]) and x1 == 250.0 and y == 5.0
    assert ax.ags_notes == {"value_range": 1, "beyond_limit": 1}


def test_us_and_si_draw_the_bars_at_the_same_positions(frame):
    df = ranged(
        frame,
        values=[500.0, NAN, 1500.0, 2000.0],
        lower=[400.0, 2000.0, NAN, NAN],
        upper=[600.0, NAN, NAN, NAN],
    )
    _, us = ht.plot.profile(df, "undrained_shear_strength", vs="depth")
    _, si = ht.plot.profile(
        df, "undrained_shear_strength", vs="depth", display_units="SI"
    )
    ((x0, x1, y),) = bars(si)
    # 400 psf = 19.152 kPa, 600 psf = 28.728 kPa; 5 ft = 1.524 m.
    assert (x0, x1, y) == pytest.approx((19.152, 28.728, 1.524), rel=1e-4)
    ((x, y),) = carets(si)
    assert (x, y) == pytest.approx((95.761, 3.048), rel=1e-4)
    assert us.ags_notes == si.ags_notes


def test_bounds_take_their_own_units(frame):
    df = frame(
        values=[500.0, NAN, 1500.0, 2000.0],
        **{LOWER: [NAN, 50.0, NAN, NAN], UPPER: [NAN, 100.0, NAN, NAN]},
    )
    df = ht.set_units(df, {LOWER: "kPa", UPPER: "kPa"})
    _, ax = ht.plot.profile(df, "undrained_shear_strength", vs="depth")
    ((x0, x1, _),) = bars(ax)
    assert (x0, x1) == pytest.approx((1044.27, 2088.54), rel=1e-4)


def test_a_value_with_no_bounds_draws_as_before(frame):
    _, plain = ht.plot.profile(frame(), "undrained_shear_strength", vs="depth")
    df = ranged(
        frame, values=[500.0, 1000.0, 1500.0, 2000.0], lower=[NAN] * 4, upper=[NAN] * 4
    )
    _, ax = ht.plot.profile(df, "undrained_shear_strength", vs="depth")
    assert points(ax) == points(plain)
    assert bars(ax) == [] and ax.ags_notes == {}
    assert "range" not in legend(ax)


# --- stats box ----------------------------------------------------------------------


def test_the_stats_box_leaves_ranges_out_and_says_how_many(frame):
    df = ranged(
        frame,
        values=[500.0, 1000.0, 1500.0, 2000.0],
        lower=[NAN, 800.0, NAN, 1800.0],
        upper=[NAN, 1200.0, NAN, NAN],
    )
    _, ax = ht.plot.profile(df, "undrained_shear_strength", stats_box=["count"])
    lines = stats_lines(ax)
    assert lines[1].split() == ["Clay", "1"]
    assert lines[2].split() == ["Fill", "1"]
    assert lines[-1] == "Ranges not included: 2"


# --- errors ---------------------------------------------------------------------------


def test_a_qualifier_on_a_row_with_a_bound_raises_naming_it(frame):
    df = ranged(
        frame,
        values=[500.0, 1000.0, 1500.0, 2000.0],
        lower=[NAN, 800.0, NAN, NAN],
        upper=[NAN, NAN, NAN, NAN],
        qualifier=["", ">", "<", ""],
    )
    with pytest.raises(ColumnError, match=r"Rows 1 have a qualifier and a bound"):
        ht.plot.profile(df, "undrained_shear_strength")


def test_lower_above_upper_raises_naming_the_rows(frame):
    df = ranged(
        frame,
        values=[500.0, 1000.0, 1500.0, 2000.0],
        lower=[NAN, 1300.0, NAN, NAN],
        upper=[NAN, 1200.0, NAN, NAN],
    )
    with pytest.raises(ColumnError, match=r"Rows 1 have .* above .*Swap"):
        ht.plot.profile(df, "undrained_shear_strength")
