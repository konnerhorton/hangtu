"""P32 Hoek-Brown envelope (docs/plots/P32-hoek-brown-envelope.md, AC 1, 4-8).

Golden values are the M17 (c) spec's (docs/work/m17c-hoek-brown-fit.md, AC 1, 2
and 7), hand-calculated there. Positions are read from the drawn artists.
"""

import math
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.colors import to_hex

import hangtu as ht
from hangtu.errors import HangtuError, UnitsError

REL = 1e-9
MINOR = "minor_principal_stress_at_failure"
MAJOR = "major_principal_stress_at_failure"
EFFECTIVE = [
    "effective_minor_principal_stress_at_failure",
    "effective_major_principal_stress_at_failure",
]
#: 1 MPa in psi: 1 psi = 0.45359237 × 9.80665 / 0.0254² Pa (exact).
PSI = 1e6 / (0.45359237 * 9.80665 / 0.0254**2)
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


def _table_1(unit="MPa", **kwargs):
    """Table 1 drawn; σ3 = 20 is beyond 0.5 σci, so the fit warns."""
    points = TABLE_1 if unit == "MPa" else [(x * PSI, y * PSI) for x, y in TABLE_1]
    with pytest.warns(UserWarning, match=BEYOND):
        return ht.plot.hoek_brown_envelope(_frame(points, unit), **kwargs)


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


def _box(ax):
    return next(text for text in ax.texts if text.get_gid() == "result_box").get_text()


def _footnote(ax):
    return "\n".join(text.get_text() for text in ax.texts)


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
    assert "σci fixed at 38.3 MPa (argument): mi = 15.0" in _box(ax)


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


def test_1_box():
    _, ax, _ = _table_1()
    box = _box(ax)
    assert "Free: σci = 37.4 MPa, mi = 15.5" in box
    assert "n = 5, R² = 0.997, σ3 0 to 20.0 MPa" in box
    assert "UCS: 1 test, mean 38.3 MPa" in box
    assert "σci fixed: no fit: no σci given" in box
    assert _lines(ax, "fixed_strength") == []
    assert "1 point at σ3 ≥ 0.5 σci (free fit)" in _footnote(ax)


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


# --- AC 5: groups ---------------------------------------------------------------------


def test_5_two_groups_two_colors_one_box():
    halved = [(x, x + (y - x) / 2) for x, y in TABLE_1]
    df = _frame([*TABLE_1, *halved], geology_unit=["Sandstone"] * 5 + ["Shale"] * 5)
    with pytest.warns(UserWarning):
        _, ax, fit = ht.plot.hoek_brown_envelope(df, group_by="geology_unit")
    solids = _lines(ax, "free")
    assert len(solids) == 2
    assert len({to_hex(line.get_color()) for line in solids}) == 2
    _on_the_curve(solids[0], A, B)
    shale = fit.groups[1]["fits"][0]
    _on_the_curve(solids[1], shale["line_intercept"], shale["line_slope"])
    box = _box(ax)
    assert "Sandstone" in box
    assert "Shale" in box
    assert len([t for t in ax.texts if t.get_gid() == "result_box"]) == 1
    assert {"Sandstone", "Shale"} <= set(_legend(ax))


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
    assert not any(text.get_gid() == "result_box" for text in ax.texts)


def test_6_draws_into_a_given_axes(assert_no_global_state):
    fig, ax = plt.subplots()
    figures = plt.get_fignums()
    out_fig, out_ax, _ = _table_1(ax=ax)
    assert (out_fig, out_ax) == (fig, ax)
    assert plt.get_fignums() == figures
    with pytest.warns(UserWarning, match=BEYOND):
        assert_no_global_state(ht.plot.hoek_brown_envelope, _frame(TABLE_1))


# --- AC 7: units ----------------------------------------------------------------------


def test_7_psi_gives_the_same_mi_and_sigma_ci_scaled():
    _, ax_mpa, fit_mpa = _table_1()
    _, ax_psi, fit_psi = _table_1("psi")
    free_mpa, free_psi = fit_mpa.groups[0]["fits"][0], fit_psi.groups[0]["fits"][0]
    assert free_psi["intact_hoek_brown_constant"] == pytest.approx(
        free_mpa["intact_hoek_brown_constant"], rel=REL
    )
    assert free_psi["intact_compressive_strength"] == pytest.approx(
        5423.52793, rel=1e-7
    )
    assert "mi = 15.5" in _box(ax_mpa)
    assert "mi = 15.5" in _box(ax_psi)
    assert ax_psi.get_xlabel() == "Minor principal stress at failure, σ3f (psi)"


def test_7_display_units_with_the_override():
    with ht.settings.override(display_overrides={"stress": "psi"}):
        _, ax, fit = _table_1(display_units="US")
    assert fit.unit == "psi"
    assert ax.get_ylabel() == "Major principal stress at failure, σ1f (psi)"
    assert fit.groups[0]["fits"][0]["intact_hoek_brown_constant"] == pytest.approx(
        15.5004012, rel=1e-7
    )
    _, ax, fit = _table_1(display_units="SI")
    assert fit.unit == "kPa"
    assert ax.get_xlabel() == "Minor principal stress at failure, σ3f (kPa)"


# --- AC 8: edge cases (§11) -----------------------------------------------------------


def test_8_no_principal_stress_columns_raise():
    df = _frame(TABLE_1).drop(columns=[MINOR, MAJOR, *EFFECTIVE])
    with pytest.raises(HangtuError, match=r'ht.template\("triaxial"\)'):
        _draw(df)


def test_8_modes_without_failure_modes_raise():
    df = _frame(TABLE_1, failure_mode=["Shear"] * 4 + ["Axial splitting"])
    with pytest.raises(HangtuError, match="failure_modes="):
        _draw(df)


def test_8_ucs_only_draws_points_on_the_axis_and_no_curve():
    df = _frame([(0, 50), (0, 55), (0, 60)])
    _, ax, _ = _draw(df, fixed_intact_compressive_strength="55 MPa")
    assert _points(ax, "point") == [(0, 50), (0, 55), (0, 60)]
    assert _lines(ax, "free") == _lines(ax, "fixed_strength") == []
    box = _box(ax)
    assert "Free: no fit: all points at the same minor principal stress" in box
    assert "no fit: all points at minor principal stress = 0" in box
    assert "UCS: 3 tests, mean 55.0 MPa" in box


def test_8_one_confined_point_besides_ucs_draws_with_the_note():
    df = _frame([(0, 50), (0, 55), (10, 120)])
    with pytest.warns(UserWarning, match=FEW):
        _, ax, _ = ht.plot.hoek_brown_envelope(df)
    assert len(_lines(ax, "free")) == 1
    assert "Fewer than 5 points in a fit" in _footnote(ax)


def test_8_a_fit_without_a_result_keeps_its_points_and_the_other():
    df = _frame([(0, 60), (10, 65), (20, 70)])
    _, ax, _ = _draw(df)
    assert len(_lines(ax, "point")) == 3
    assert _lines(ax, "free") == []
    assert "slope mi σci = -55 is 0 or below" in _box(ax)
    # σci² = -1325 free; fixed at 20, b = 142125/525 > 0, so that one is drawn.
    df = _frame([(5, 30), (10, 60), (20, 100)])
    with pytest.warns(UserWarning):  # 3 points, and σ3 ≥ 10 = 0.5 σci
        _, ax, _ = ht.plot.hoek_brown_envelope(
            df, fixed_intact_compressive_strength="20 MPa"
        )
    assert _lines(ax, "free") == []
    assert "intercept σci² = -1325 is 0 or below" in _box(ax)
    (fixed,) = _lines(ax, "fixed_strength")
    _on_the_curve(fixed, 400, 142125 / 525)
    assert "2 points at σ3 ≥ 0.5 σci (σci fixed)" in _footnote(ax)


def test_8_left_out_modes_drawn_open_with_their_count():
    df = _frame(
        [*TABLE_1, (0, 38.6), (10, 88.0)],
        failure_mode=["Shear"] * 5 + ["Axial splitting", "Along bedding"],
    )
    with pytest.warns(UserWarning, match=BEYOND):
        _, ax, _ = ht.plot.hoek_brown_envelope(df, failure_modes=["Shear"])
    assert _points(ax, "left_out_point") == [(0, 38.6), (10, 88.0)]
    # One marker per mode, in the modes' sorted order (P32 §7).
    assert [line.get_marker() for line in _lines(ax, "left_out_point")] == ["D", "^"]
    for line in _lines(ax, "left_out_point"):
        assert line.get_markerfacecolor() == "white"
    legend = _legend(ax)
    assert "Left out: Axial splitting (1)" in legend
    assert "Left out: Along bedding (1)" in legend
    handles = {
        handle.get_label().replace("\n", " "): handle.get_marker()
        for handle in ax.get_legend().legend_handles
    }
    assert handles["Left out: Along bedding (1)"] == "^"
    assert handles["Left out: Axial splitting (1)"] == "D"
    assert "Left out: 1 Axial splitting, 1 Along bedding" in _footnote(ax)


def test_8_a_blank_mode_takes_the_last_marker():
    df = _frame(
        [*TABLE_1, (0, 38.6), (10, 88.0)],
        failure_mode=["Shear"] * 5 + [None, "Along bedding"],
    )
    with pytest.warns(UserWarning, match=BEYOND):
        _, ax, _ = ht.plot.hoek_brown_envelope(df, failure_modes=["Shear"])
    # "Along bedding" sorts first; the blank mode comes last whatever its text.
    assert [line.get_marker() for line in _lines(ax, "left_out_point")] == ["D", "^"]


def test_8_negative_or_reversed_stresses_raise():
    with pytest.raises(HangtuError, match="tension"):
        _draw(_frame([(-1, 50), (5, 70)]))
    with pytest.raises(HangtuError, match="σ1 < σ3"):
        _draw(_frame([(10, 5), (5, 70)]))


def test_8_mixed_failure_criteria_raise_and_pool_draws_them():
    df = _frame(TABLE_1, failure_criterion=["Peak"] * 3 + ["Strain"] * 2)
    with pytest.raises(HangtuError, match="Strain"):
        _draw(df)
    with pytest.warns(UserWarning, match=BEYOND):
        _, ax, fit = ht.plot.hoek_brown_envelope(df, pool="failure_criterion")
    assert fit.pooled == ("failure_criterion",)
    assert len(_lines(ax, "free")) == 1


def test_8_color_by_with_group_by_raises():
    df = _frame(TABLE_1, geology_unit=["Sandstone"] * 5)
    with pytest.raises(HangtuError, match="color_by= can't be used with group_by="):
        _draw(df, group_by="geology_unit", color_by="geology_unit")


def test_8_missing_units_raise():
    df = _frame(TABLE_1)
    df.attrs = {}
    with pytest.raises(UnitsError, match="principal_stress_at_failure"):
        _draw(df)


def test_8_missing_optional_columns_give_one_hint():
    ht.settings.hints = True
    with pytest.warns(UserWarning) as caught:
        ht.plot.hoek_brown_envelope(_frame(TABLE_1))
    hints = [str(w.message) for w in caught if "σ3 ≥ 0.5 σci" not in str(w.message)]
    assert len(hints) == 1
    for column in ("failure_mode", "multistage_test", "failure_criterion"):
        assert column in hints[0]
    assert "geology_unit" in hints[0]


def test_8_multistage_drawn_as_squares():
    points = [*TABLE_1, (5, 66.0), (10, 85.0), (20, 120.0)]
    df = _frame(points, multistage_test=[False] * 5 + [True] * 3)
    with pytest.warns(UserWarning, match=BEYOND):
        _, ax, _ = ht.plot.hoek_brown_envelope(df)
    markers = sorted(line.get_marker() for line in _lines(ax, "point"))
    assert markers == ["o"] * 5 + ["s"] * 3
    assert "Multistage" in _legend(ax)
    assert "Single stage: σci = 37.4 MPa, mi = 15.5" in _box(ax)


def test_user_envelopes():
    _, ax, _ = _table_1(envelopes=[(40, 15, "Design")])
    (line,) = _lines(ax, "user_envelope")
    _on_the_curve(line, 1600, 600)
    assert line.get_label() == "Design"
    with pytest.raises(HangtuError, match="envelopes="):
        _draw(_frame(TABLE_1), envelopes=[(40, 15)])
    with pytest.raises(HangtuError, match="above 0"):
        _draw(_frame(TABLE_1), envelopes=[(40, 0, "zero")])


def test_not_a_frame_raises():
    with pytest.raises(HangtuError, match="pandas DataFrame"):
        ht.plot.hoek_brown_envelope([1, 2])
