"""P11 failure envelope (docs/plots/P11-failure-envelope.md, AC 1-5, 7 and 9).

Golden values are the M11 (b) spec's, hand-calculated there: golden 1 is
(σ′3, σ′1) = (100, 300) and (200, 500) kPa, golden 2 (100, 300) and
(200, 600) kPa. Positions are read from the drawn artists.
"""

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError, UnitsError

REL = 1e-9
STRESSES = [
    "minor_principal_stress_at_failure",
    "major_principal_stress_at_failure",
    "effective_minor_principal_stress_at_failure",
    "effective_major_principal_stress_at_failure",
]
GOLDEN_1 = [(100, 300), (200, 500)]
GOLDEN_2 = [(100, 300), (200, 600)]


@pytest.fixture(autouse=True)
def _no_hints():
    ht.settings.hints = False


def _points(points, unit="kPa", **columns):
    """Stages with effective points ``(σ′3, σ′1)`` and totals 300 kPa above."""
    minor, major = (np.array(pair, dtype=float) for pair in zip(*points, strict=True))
    df = pd.DataFrame(
        {
            STRESSES[0]: minor + 300,
            STRESSES[1]: major + 300,
            STRESSES[2]: minor,
            STRESSES[3]: major,
            **columns,
        }
    )
    df.attrs["units"] = dict.fromkeys(STRESSES, unit)
    return df


def _draw(df, **kwargs):
    kwargs.setdefault("display_units", "SI")
    fig, ax, fit = ht.plot.failure_envelope(df, **kwargs)
    return fig, ax, fit


def _lines(ax, gid):
    return [line for line in ax.lines if line.get_gid() == gid]


def _intercept_and_slope(line):
    (x0, x1), (y0, y1) = line.get_xdata(), line.get_ydata()
    slope = (y1 - y0) / (x1 - x0)
    return y0 - slope * x0, slope


def _box(ax):
    return next(text for text in ax.texts if text.get_gid() == "result_box")


# --- AC 1: Mohr circles and the envelope --------------------------------------------


def test_mohr_golden_1():
    _, ax, _ = _draw(_points(GOLDEN_1))
    circles = [patch for patch in ax.patches if patch.get_gid() == "mohr_circle"]
    centers = [circle.center for circle in circles]
    radii = [circle.width / 2 for circle in circles]
    assert centers == [(200.0, 0.0), (350.0, 0.0)]
    assert radii == pytest.approx([100.0, 150.0], rel=REL)
    (solid,) = _lines(ax, "envelope")
    intercept, slope = _intercept_and_slope(solid)
    assert intercept == pytest.approx(35.35534, rel=1e-6)
    assert slope == pytest.approx(0.3535534, rel=1e-6)
    for (center, _), radius in zip(centers, radii, strict=True):
        distance = (slope * center + intercept) / math.hypot(1, slope)
        assert distance == pytest.approx(radius, rel=REL)
    assert solid.get_xdata() == pytest.approx([166.6667, 300.0], rel=1e-6)
    assert solid.get_linestyle() == "-"
    beyond = _lines(ax, "envelope_beyond")
    assert [line.get_linestyle() for line in beyond] == ["--", "--"]
    assert beyond[0].get_xdata() == pytest.approx([0.0, 166.6667], rel=1e-6)
    assert beyond[1].get_xdata()[0] == pytest.approx(300.0, rel=REL)
    assert beyond[1].get_xdata()[1] == pytest.approx(ax.get_xlim()[1], rel=REL)
    for line in beyond:
        assert _intercept_and_slope(line) == pytest.approx((intercept, slope), rel=REL)


# --- AC 2: the intercept depends on the space ---------------------------------------


def test_s_t_draws_a_and_tan_alpha():
    _, ax, _ = _draw(_points(GOLDEN_1), space="s_t")
    (solid,) = _lines(ax, "envelope")
    assert _intercept_and_slope(solid) == pytest.approx((100 / 3, 1 / 3), rel=REL)
    points = [line.get_xydata()[0] for line in _lines(ax, "failure_point")]
    assert np.allclose(points, [(200, 100), (350, 150)])


def test_p_q_draws_q0_and_m():
    _, ax, _ = _draw(_points(GOLDEN_1), space="p_q")
    (solid,) = _lines(ax, "envelope")
    intercept, slope = _intercept_and_slope(solid)
    assert intercept == pytest.approx(75.0, rel=REL)
    assert slope == pytest.approx(0.75, rel=REL)
    for p, q in [(500 / 3, 200.0), (300.0, 300.0)]:
        assert intercept + slope * p == pytest.approx(q, rel=REL)
    points = [line.get_xydata()[0] for line in _lines(ax, "failure_point")]
    assert np.allclose(points, [(500 / 3, 200), (300, 300)])


# --- AC 3: through the origin -------------------------------------------------------


@pytest.mark.parametrize("cohesion", [None, 0])
@pytest.mark.parametrize(
    ("space", "slope"),
    [("mohr", math.tan(math.radians(30))), ("s_t", 0.5), ("p_q", 1.2)],
)
def test_golden_2_through_the_origin(cohesion, space, slope):
    _, ax, fit = _draw(_points(GOLDEN_2), space=space, cohesion=cohesion)
    (solid,) = _lines(ax, "envelope")
    intercept, drawn = _intercept_and_slope(solid)
    assert intercept == pytest.approx(0.0, abs=1e-9)
    assert drawn == pytest.approx(slope, rel=REL)
    assert fit.groups[0]["fits"][0]["friction_angle"] == pytest.approx(30.0, rel=REL)


# --- AC 4: idealized drained paths --------------------------------------------------


@pytest.mark.parametrize(
    ("space", "end"), [("s_t", (200.0, 100.0)), ("p_q", (500 / 3, 200.0))]
)
def test_idealized_path(space, end):
    df = _points([(100, 300)], test_type=["CD"])
    _, ax, _ = _draw(df, space=space, paths="idealized_drained", cohesion=0)
    (path,) = _lines(ax, "idealized_path")
    assert path.get_xydata() == pytest.approx(np.array([(100.0, 0.0), end]), rel=REL)
    labels = [t.get_text().replace("\n", " ") for t in ax.get_legend().get_texts()]
    assert "Idealized drained path" in labels


def test_path_of_an_undrained_test_raises():
    df = _points(GOLDEN_1, test_type=["CU", "CD"])
    with pytest.raises(HangtuError, match=r"\['CU'\]"):
        _draw(df, space="s_t", paths="idealized_drained")


@pytest.mark.parametrize("columns", [{}, {"test_type": [None, "CD"]}])
def test_path_without_a_type_is_assumed_drained(columns):
    _, ax, _ = _draw(
        _points(GOLDEN_1, **columns), space="s_t", paths="idealized_drained"
    )
    labels = [t.get_text().replace("\n", " ") for t in ax.get_legend().get_texts()]
    assert "Idealized drained path (assumed CD)" in labels


def test_paths_in_mohr_raise():
    with pytest.raises(HangtuError, match=r"s′-t or p′-q"):
        _draw(_points(GOLDEN_1), paths="idealized_drained")


# --- AC 5: equal aspect and limits --------------------------------------------------


@pytest.mark.parametrize("space", ["mohr", "s_t", "p_q"])
def test_equal_aspect_and_limits(space):
    _, ax, _ = _draw(_points(GOLDEN_1), space=space)
    assert ax.get_aspect() == 1
    largest_x = {"mohr": 500.0, "s_t": 350.0, "p_q": 300.0}[space]
    largest_y = {"mohr": 150.0, "s_t": 150.0, "p_q": 300.0}[space]
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    assert x0 == 0
    assert y0 == 0
    assert x1 > largest_x
    assert y1 > largest_y


def test_axis_labels():
    _, ax, _ = _draw(_points(GOLDEN_1))
    assert ax.get_xlabel() == "Effective normal stress, σ′ (kPa)"
    assert ax.get_ylabel() == "Shear stress, τ (kPa)"
    # The totals are 300 kPa above the effective points: a negative intercept.
    with pytest.warns(UserWarning, match="negative"):
        _, ax, _ = _draw(_points(GOLDEN_1), space="p_q", stress="total")
    assert ax.get_xlabel() == "Mean stress, p (kPa)"
    assert ax.get_ylabel() == "Deviator stress, q (kPa)"
    _, ax, _ = _draw(_points(GOLDEN_1), space="s_t")
    assert ax.get_xlabel() == "Mean effective stress, s′ (kPa)"
    assert ax.get_ylabel() == "Shear stress, t (kPa)"


# --- AC 7: returns ------------------------------------------------------------------


def test_returns_the_fit():
    df = _points(GOLDEN_1)
    fig, ax, fit = _draw(df)
    expected = ht.analysis.mohr_coulomb_fit(df, display_units="SI")
    pd.testing.assert_frame_equal(fit.to_frame(), expected.to_frame())
    assert ax.figure is fig


def test_fit_false_draws_no_line():
    _, ax, fit = _draw(_points(GOLDEN_1), fit=False)
    assert fit is None
    assert not _lines(ax, "envelope") and not _lines(ax, "envelope_beyond")
    assert not [text for text in ax.texts if text.get_gid() == "result_box"]
    assert len(_lines(ax, "failure_point")) == 2


def test_fit_false_draws_mixed_criteria():
    df = _points(GOLDEN_1, failure_criterion=["Maximum deviator stress", None])
    _, _, fit = _draw(df, fit=False)
    assert fit is None


def test_draws_into_a_given_axes(assert_no_global_state):
    _, given = plt.subplots()
    fig, ax, _ = _draw(_points(GOLDEN_1), ax=given)
    assert ax is given
    assert fig is given.figure
    assert_no_global_state(ht.plot.failure_envelope, _points(GOLDEN_1))


# --- AC 9: edge cases (§11) ---------------------------------------------------------


def test_no_principal_stresses_raises():
    with pytest.raises(ColumnError, match=r"triaxial_failure_stresses\(\)"):
        _draw(ht.template("triaxial"))


def test_reversed_stresses_raise():
    with pytest.raises(HangtuError, match=r"^Rows 1 have σ′1 < σ′3"):
        _draw(_points([(100, 300), (300, 200)]))


def test_negative_minor_stress_is_drawn_below_zero():
    with pytest.warns(UserWarning, match=r"tension"):
        _, ax, _ = _draw(_points([(-10, 200), (100, 400), (200, 600)]))
    assert ax.get_xlim()[0] < -10
    assert len(_lines(ax, "failure_point")) == 3


def test_one_point_draws_without_a_fit():
    _, ax, _ = _draw(_points([(100, 300)]))
    assert not _lines(ax, "envelope")
    assert "no fit: 1 point (2 needed, or cohesion=0)" in _box(ax).get_text()
    assert len(_lines(ax, "failure_point")) == 1


def test_a_group_without_a_fit_among_several():
    df = _points(
        [(100, 300), (200, 600), (150, 400)], geology_unit=["ALV", "ALV", "TRC"]
    )
    _, ax, _ = _draw(df, group_by="geology_unit")
    assert len(_lines(ax, "envelope")) == 1
    text = _box(ax).get_text()
    assert "ALV: c′ = 0" in text
    assert "TRC: no fit: 1 point" in text
    assert len(_lines(ax, "failure_point")) == 3


def test_slope_outside_its_range_draws_no_envelope():
    _, ax, _ = _draw(_points([(300, 500), (100, 900)]))
    assert not _lines(ax, "envelope")
    assert "slope tan α = 3.0" in _box(ax).get_text()


def test_negative_intercept_is_drawn_as_fitted():
    with pytest.warns(UserWarning, match=r"negative"):
        _, ax, _ = _draw(_points([(100, 250), (300, 1000)]))
    (solid,) = _lines(ax, "envelope")
    intercept, _ = _intercept_and_slope(solid)
    assert intercept == pytest.approx(-32.274861, rel=1e-7)
    assert "(c′ < 0)" in _box(ax).get_text()


def test_mixed_criteria_raise_and_pool_draws_one_fit():
    df = _points(
        [(100, 300), (200, 600), (300, 900)],
        failure_criterion=["Maximum deviator stress"] * 2 + ["Maximum stress ratio"],
    )
    with pytest.raises(HangtuError, match=r"'Maximum stress ratio' \(1 rows\)"):
        _draw(df)
    _, ax, fit = _draw(df, pool="failure_criterion")
    assert len(_lines(ax, "envelope")) == 1
    assert fit.pooled == ("failure_criterion",)


def test_missing_group_by_column_raises():
    with pytest.raises(ColumnError, match=r"can't group by 'geology_unit'"):
        _draw(_points(GOLDEN_1), group_by="geology_unit")


def test_color_by_with_group_by_raises():
    df = _points(GOLDEN_1, geology_unit=["ALV", "ALV"])
    with pytest.raises(HangtuError, match=r"color_by= can't be used with group_by="):
        _draw(df, group_by="geology_unit", color_by="geology_unit")


def test_missing_units_raise():
    df = _points(GOLDEN_1)
    df.attrs = {}
    with pytest.raises(UnitsError, match="minor_principal_stress_at_failure"):
        _draw(df)


def test_missing_optional_columns_give_one_hint():
    ht.settings.hints = True
    with pytest.warns(ht.HangtuHint) as caught:
        _draw(_points(GOLDEN_1))
    assert len(caught) == 1
    message = str(caught[0].message)
    for column in ("failure_criterion", "multistage_test", "geology_unit"):
        assert column in message


def test_user_envelopes_are_transformed():
    _, ax, _ = _draw(_points(GOLDEN_2), space="p_q", envelopes=[(0, 30, "Design")])
    (line,) = _lines(ax, "user_envelope")
    assert _intercept_and_slope(line) == pytest.approx((0.0, 1.2), abs=1e-9)
    assert line.get_label() == "Design"


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"space": "q_p"}, r"space must be one of"),
        ({"paths": "measured", "space": "s_t"}, r"paths must be one of"),
        ({"envelopes": [(0, 95, "Steep")]}, r"from 0 to below 90"),
        ({"envelopes": [(0, 30)]}, r"envelopes= takes a list"),
        ({"color_by": "geology_unit"}, r"df has no such column"),
    ],
)
def test_argument_errors(kwargs, match):
    with pytest.raises(HangtuError, match=match):
        _draw(_points(GOLDEN_1), **kwargs)
