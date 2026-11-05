"""P32 Hoek-Brown envelope (docs/plots/P32-hoek-brown-envelope.md, AC 1, 4, 6).

Golden values are the M17 (c) spec's (docs/work/m17c-hoek-brown-fit.md, AC 1, 2
and 7), hand-calculated there. Positions are read from the drawn artists.
"""

import math
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError

REL = 1e-9
MINOR = "minor_principal_stress_at_failure"
MAJOR = "major_principal_stress_at_failure"
EFFECTIVE = [
    "effective_minor_principal_stress_at_failure",
    "effective_major_principal_stress_at_failure",
]
#: Hoek (2007), ch. 11, Table 1: one UCS test and four triaxial tests.
TABLE_1 = [(0, 38.3), (5, 72.4), (7.5, 80.5), (15, 115.6), (20, 134.3)]
#: Table 1's free line: a = σci², b = mi σci (spec AC 1).
A, B = 950847 / 680, 197071 / 340
BEYOND = r"points at σ3 ≥ 0\.5 σci of their fit"
FEW = r"fewer than 5 points"


@pytest.fixture(autouse=True)
def _no_hints():
    ht.settings.hints = False


def _frame(points, unit="MPa", **columns):
    """Rows at failure with the total pair ``(σ3, σ1)``, the effective pair blank."""
    minor, major = (np.array(v, dtype=float) for v in zip(*points, strict=True))
    df = pd.DataFrame(
        {MINOR: minor, MAJOR: major, **dict.fromkeys(EFFECTIVE, np.nan), **columns}
    )
    df.attrs["units"] = dict.fromkeys([MINOR, MAJOR, *EFFECTIVE], unit)
    return df


def _table_1(**kwargs):
    """Table 1 drawn; σ3 = 20 is beyond 0.5 σci, so the fit warns."""
    with pytest.warns(UserWarning, match=BEYOND):
        return ht.plot.hoek_brown_envelope(_frame(TABLE_1), **kwargs)


def _draw(df, **kwargs):
    """Draw, failing on any warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return ht.plot.hoek_brown_envelope(df, **kwargs)


def _lines(ax, gid):
    return [line for line in ax.lines if line.get_gid() == gid]


def _points(ax, gid):
    return sorted(
        (float(line.get_xdata()[0]), float(line.get_ydata()[0]))
        for line in _lines(ax, gid)
    )


def _legend(ax):
    return [t.get_text().replace("\n", " ") for t in ax.get_legend().get_texts()]


def _on_the_curve(line, a, b):
    """Every drawn point satisfies σ1 = σ3 + (a + b σ3)^0.5."""
    x, y = np.asarray(line.get_xdata()), np.asarray(line.get_ydata())
    np.testing.assert_allclose(y, x + np.sqrt(a + b * x), rtol=REL)


# --- AC 1: curves ---------------------------------------------------------------------


def test_1_free_curve_solid_over_the_points_and_dashed_beyond():
    _, ax, _ = _table_1()
    (solid,) = _lines(ax, "free")
    _on_the_curve(solid, A, B)
    assert solid.get_xdata()[0] == 0
    assert solid.get_ydata()[0] == pytest.approx(37.3939088, rel=1e-7)
    assert solid.get_xdata()[-1] == 20
    assert solid.get_linestyle() == "-"
    # At σ3 = 10: 10 + (a + 10 b)^0.5.
    at_10 = np.interp(10, solid.get_xdata(), solid.get_ydata())
    assert at_10 == pytest.approx(10 + math.sqrt(A + 10 * B), rel=1e-4)
    (beyond,) = _lines(ax, "free_beyond")  # Table 1 has a UCS point: none before 0
    _on_the_curve(beyond, A, B)
    assert beyond.get_xdata()[0] == 20
    assert beyond.get_xdata()[-1] == ax.get_xlim()[1]
    assert beyond.get_linestyle() == "--"


def test_1_fixed_curve_through_the_fixed_sigma_ci():
    _, ax, _ = _table_1(fixed_intact_compressive_strength="38.3 MPa")
    (fixed,) = _lines(ax, "fixed_strength")
    assert fixed.get_ydata()[0] == pytest.approx(38.3, rel=REL)
    x, y = fixed.get_xdata()[-1], fixed.get_ydata()[-1]
    constant = ((y - x) ** 2 - 38.3**2) / (38.3 * x)
    assert constant == pytest.approx(15.0132572, rel=1e-7)
    assert fixed.get_linestyle() == ":"
    assert fixed.get_alpha() == pytest.approx(0.6)
    assert fixed.get_xdata()[0] == 0
    assert fixed.get_xdata()[-1] == ax.get_xlim()[1]


def test_1_without_a_ucs_point_the_curve_is_dashed_back_to_zero():
    with pytest.warns(UserWarning, match=FEW):
        _, ax, _ = ht.plot.hoek_brown_envelope(_frame(TABLE_1[1:4]))
    before, after = sorted(
        _lines(ax, "free_beyond"), key=lambda line: line.get_xdata()[0]
    )
    assert (before.get_xdata()[0], before.get_xdata()[-1]) == (0, 5)
    assert _lines(ax, "free")[0].get_xdata()[0] == 5
    assert after.get_xdata()[0] == 15


def test_1_points_filled_circles_at_their_stresses():
    _, ax, _ = _table_1()
    assert _points(ax, "point") == TABLE_1
    for line in _lines(ax, "point"):
        assert line.get_marker() == "o"
        assert line.get_markerfacecolor() == line.get_color()


def test_1_left_out_modes_drawn_open_with_their_count():
    df = _frame(
        [*TABLE_1, (0, 38.6), (10, 88.0)],
        failure_mode=["Shear"] * 5 + ["Axial splitting", "Along bedding"],
    )
    with pytest.warns(UserWarning, match=BEYOND):
        _, ax, _ = ht.plot.hoek_brown_envelope(df, failure_modes=["Shear"])
    assert _points(ax, "left_out_point") == [(0, 38.6), (10, 88.0)]
    for line in _lines(ax, "left_out_point"):
        assert line.get_marker() == "o"
        assert line.get_markerfacecolor() == "white"
    legend = _legend(ax)
    assert "Left out: Axial splitting (1)" in legend
    assert "Left out: Along bedding (1)" in legend


def test_1_multistage_drawn_as_squares():
    points = [*TABLE_1, (5, 66.0), (10, 85.0), (20, 120.0)]
    df = _frame(points, multistage_test=[False] * 5 + [True] * 3)
    with pytest.warns(UserWarning, match=BEYOND):
        _, ax, _ = ht.plot.hoek_brown_envelope(df)
    markers = sorted(line.get_marker() for line in _lines(ax, "point"))
    assert markers == ["o"] * 5 + ["s"] * 3
    assert {"Single stage", "Multistage"} <= set(_legend(ax))


# --- AC 4: axes -----------------------------------------------------------------------


def test_4_labels_limits_and_aspect():
    _, ax, _ = _table_1()
    assert ax.get_xlabel() == "Minor principal stress at failure, σ3f (MPa)"
    assert ax.get_ylabel() == "Major principal stress at failure, σ1f (MPa)"
    assert ax.get_xlim() == (0, 25)
    right = 25 + math.sqrt(A + 25 * B)  # the free curve at the right edge
    assert ax.get_ylim()[0] == 0
    assert ax.get_ylim()[1] >= right
    assert ax.get_aspect() == "auto"


def test_4_effective_labels():
    df = _frame(TABLE_1)
    df[EFFECTIVE[0]], df[EFFECTIVE[1]] = df[MINOR], df[MAJOR]
    with pytest.warns(UserWarning, match=BEYOND):
        _, ax, _ = ht.plot.hoek_brown_envelope(df, stress="effective")
    assert ax.get_xlabel() == "Effective minor principal stress at failure, σ′3f (MPa)"
    assert ax.get_ylabel() == "Effective major principal stress at failure, σ′1f (MPa)"


# --- AC 6: returns --------------------------------------------------------------------


def test_6_returns_the_fit():
    fig, ax, fit = _table_1()
    assert fig is ax.figure
    with pytest.warns(UserWarning, match=BEYOND):
        expected = ht.analysis.hoek_brown_fit(_frame(TABLE_1))
    pd.testing.assert_frame_equal(fit.to_frame(), expected.to_frame())


def test_6_fit_false_draws_no_curve():
    _, ax, fit = _draw(_frame(TABLE_1), fit=False)
    assert fit is None
    assert _lines(ax, "free") == _lines(ax, "free_beyond") == []
    assert _lines(ax, "fixed_strength") == []
    assert len(_lines(ax, "point")) == 5


def test_6_draws_into_a_given_axes(assert_no_global_state):
    fig, ax = plt.subplots()
    figures = plt.get_fignums()
    out_fig, out_ax, _ = _table_1(ax=ax)
    assert (out_fig, out_ax) == (fig, ax)
    assert plt.get_fignums() == figures
    with pytest.warns(UserWarning, match=BEYOND):
        assert_no_global_state(ht.plot.hoek_brown_envelope, _frame(TABLE_1))


def test_not_a_frame_raises():
    with pytest.raises(HangtuError, match="pandas DataFrame"):
        ht.plot.hoek_brown_envelope([1, 2])
