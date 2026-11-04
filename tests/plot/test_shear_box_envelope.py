"""P31 shear box envelope (docs/plots/P31-shear-box-envelope.md, AC 1-4 and 7).

Golden values are the M17 (b) spec's (docs/work/m17b-shear-box-fit.md, AC 1-8),
hand-calculated there. Positions are read from the drawn artists.
"""

import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError

AGS = Path(__file__).parents[1] / "data" / "ags"
REL = 1e-9
STRESSES = ["applied_normal_stress", "peak_shear_stress", "residual_shear_stress"]


@pytest.fixture(autouse=True)
def _no_hints():
    ht.settings.hints = False


def _project(name, tmp_path_factory):
    return ht.Project.from_ags(
        AGS / f"{name}.ags",
        db=tmp_path_factory.mktemp(name) / f"{name}.sqlite",
        overwrite=True,
        display_units="SI",
    ).shear_box()


@pytest.fixture(scope="module")
def site_si(tmp_path_factory):
    return _project("site_si", tmp_path_factory)


def _frame(peak, residual=None, **columns):
    """Stages with peak points ``(σn, τ)`` and, if given, residual ``τ``, in kPa."""
    normal, shear = (np.array(v, dtype=float) for v in zip(*peak, strict=True))
    df = pd.DataFrame(
        {
            STRESSES[0]: normal,
            STRESSES[1]: shear,
            STRESSES[2]: np.full(len(normal), np.nan) if residual is None else residual,
            **columns,
        }
    )
    df.attrs["units"] = dict.fromkeys(STRESSES, "kPa")
    return df


def _draw(df, **kwargs):
    kwargs.setdefault("display_units", "SI")
    return ht.plot.shear_box_envelope(df, **kwargs)


def _lines(ax, gid):
    return [line for line in ax.lines if line.get_gid() == gid]


def _intercept_and_slope(line):
    (x0, x1), (y0, y1) = line.get_xdata(), line.get_ydata()
    slope = (y1 - y0) / (x1 - x0)
    return y0 - slope * x0, slope


def _points(ax, gid):
    return sorted(
        (float(line.get_xdata()[0]), float(line.get_ydata()[0]))
        for line in _lines(ax, gid)
    )


# --- AC 1-2: lines and points -------------------------------------------------------


def test_bh2_d1_lines(site_si):
    _, ax, _ = _draw(site_si)
    (solid,) = _lines(ax, "peak_free")
    assert solid.get_linestyle() == "-"
    assert list(solid.get_xdata()) == pytest.approx([50, 200], rel=REL)
    assert _intercept_and_slope(solid) == pytest.approx((8, 0.6), rel=REL)
    beyond = _lines(ax, "peak_free_beyond")
    assert [line.get_linestyle() for line in beyond] == ["--", "--"]
    assert beyond[0].get_xdata()[0] == 0
    assert beyond[0].get_xdata()[1] == pytest.approx(50, rel=REL)
    assert beyond[1].get_xdata()[0] == pytest.approx(200, rel=REL)
    assert beyond[1].get_xdata()[1] == pytest.approx(ax.get_xlim()[1], rel=REL)
    for line in beyond:
        assert _intercept_and_slope(line) == pytest.approx((8, 0.6), rel=REL)
    (origin,) = _lines(ax, "peak_through_origin")
    assert origin.get_linestyle() == ":"
    assert origin.get_alpha() == pytest.approx(0.6)
    assert _intercept_and_slope(origin) == pytest.approx((0, 49 / 75), abs=1e-9)
    (residual,) = _lines(ax, "residual_free")
    assert _intercept_and_slope(residual) == pytest.approx((3, 191 / 350), rel=REL)
    (residual_origin,) = _lines(ax, "residual_through_origin")
    assert _intercept_and_slope(residual_origin)[1] == pytest.approx(99 / 175, rel=REL)


def test_bh2_d1_points(site_si):
    _, ax, _ = _draw(site_si)
    assert _points(ax, "peak_point") == pytest.approx(
        [(50, 38), (100, 68), (200, 128)], rel=REL
    )
    assert _points(ax, "residual_point") == pytest.approx(
        [(50, 30), (100, 58), (200, 112)], rel=REL
    )
    peak = _lines(ax, "peak_point")[0]
    residual = _lines(ax, "residual_point")[0]
    assert peak.get_markerfacecolor() == peak.get_markeredgecolor()
    assert residual.get_markerfacecolor() != residual.get_markeredgecolor()


def test_points_at_their_basis():
    df = _frame(
        [(50, 38), (100, 68), (200, 128)],
        normal_stress_at_peak=[52, np.nan, 205],
    )
    df.attrs["units"]["normal_stress_at_peak"] = "kPa"
    _, ax, _ = _draw(df)
    assert [x for x, _ in _points(ax, "peak_point")] == pytest.approx([52, 100, 205])


# --- AC 3: cohesion=0 ---------------------------------------------------------------


def test_cohesion_zero_swaps_the_styles(site_si):
    _, ax, fit = _draw(site_si, cohesion=0)
    (solid,) = _lines(ax, "peak_through_origin")
    assert solid.get_linestyle() == "-"
    assert _intercept_and_slope(solid) == pytest.approx((0, 49 / 75), abs=1e-9)
    assert len(_lines(ax, "peak_through_origin_beyond")) == 2
    (dotted,) = _lines(ax, "peak_free")
    assert dotted.get_linestyle() == ":"
    assert _intercept_and_slope(dotted) == pytest.approx((8, 0.6), rel=REL)
    free = next(
        line
        for line in fit.groups[0]["strengths"]["peak"]["lines"]
        if line["line_kind"] == "free"
    )
    assert free["cohesion"] == pytest.approx(8, rel=REL)


# --- AC 4: equal aspect and limits --------------------------------------------------


def test_equal_aspect_and_limits(site_si):
    _, ax, _ = _draw(site_si)
    assert ax.get_aspect() == 1
    assert ax.get_xlim()[0] == 0
    assert ax.get_ylim()[0] == 0
    assert ax.get_xlim()[1] > 200
    assert ax.get_ylim()[1] > 128


def test_negative_intercept_goes_below_zero():
    with pytest.warns(UserWarning, match="intercept is negative"):
        _, ax, _ = _draw(_frame([(100, 20), (200, 80), (300, 140)]))
    assert ax.get_ylim()[0] < -40
    (solid,) = _lines(ax, "peak_free")
    assert _intercept_and_slope(solid) == pytest.approx((-40, 0.6), rel=REL)


# --- AC 7: returns ------------------------------------------------------------------


def test_returns_the_fit(site_si):
    fig, ax, fit = _draw(site_si)
    assert fig is ax.figure
    expected = ht.analysis.shear_box_fit(site_si, display_units="SI")
    pd.testing.assert_frame_equal(fit.to_frame(), expected.to_frame())


def test_fit_false_draws_no_line(site_si):
    _, ax, fit = _draw(site_si, fit=False)
    assert fit is None
    assert not [line for line in ax.lines if "free" in str(line.get_gid())]
    assert not [line for line in ax.lines if "origin" in str(line.get_gid())]
    assert len(_lines(ax, "peak_point")) == 3


def test_fit_false_draws_mixed_types_and_a_negative_intercept():
    df = _frame(
        [(100, 20), (200, 80), (300, 140)],
        test_type=["SMALL SBOX", "SMALL SBOX", "SMALL RSHEAR"],
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _, ax, fit = _draw(df, fit=False)
    assert fit is None
    assert len(_lines(ax, "peak_point")) == 3


def test_draws_into_a_given_axes(site_si, assert_no_global_state):
    fig, ax = plt.subplots()
    figures = plt.get_fignums()
    out_fig, out_ax, _ = _draw(site_si, ax=ax)
    assert (out_fig, out_ax) == (fig, ax)
    assert plt.get_fignums() == figures
    assert_no_global_state(ht.plot.shear_box_envelope, site_si)


def test_axis_labels(site_si):
    _, ax, _ = _draw(site_si)
    assert ax.get_xlabel() == "Normal stress, σn (kPa)"
    assert ax.get_ylabel() == "Shear stress, τ (kPa)"


# --- Arguments ---------------------------------------------------------------------


def test_not_a_frame_raises():
    with pytest.raises(HangtuError, match="pandas DataFrame"):
        ht.plot.shear_box_envelope([1, 2])
