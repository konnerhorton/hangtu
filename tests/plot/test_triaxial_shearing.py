"""P12 triaxial shearing (docs/plots/P12-triaxial-shearing.md, AC 1-9 and 12).

The readings are the M11 (c) spec's golden readings in
``tests/data/triaxial_readings_goldens.csv`` (kPa, percent): R1 is stages A
and B (CU), R3 stage C (CD, Δu blank), R4 stage D (UU). Expected positions
are the spec's hand calculations. Positions are read from the drawn artists.
"""

import math
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError, UnitsError

GOLDENS = Path(__file__).parents[1] / "data" / "triaxial_readings_goldens.csv"
STRESSES = ["cell_pressure", "back_pressure", "deviator_stress", "excess_pore_pressure"]
BACK_PRESSURE = r"1 drained stage had no pore_pressure_at_failure"
REL = 1e-9


@pytest.fixture(autouse=True)
def _no_hints():
    ht.settings.hints = False


def readings(*stages, **columns):
    df = pd.read_csv(GOLDENS, dtype={"test_stage": str})
    if stages:
        df = df[df["specimen_id"].isin(stages)].reset_index(drop=True)
    for column, values in columns.items():
        df[column] = values
    df.attrs["units"] = dict.fromkeys(STRESSES, "kPa")
    return df


def draw(df, **kwargs):
    """Draw in SI, failing on any warning."""
    kwargs.setdefault("display_units", "SI")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return ht.plot.triaxial_shearing(df, **kwargs)


def lines(ax, gid):
    return [line for line in ax.lines if line.get_gid() == gid]


def dots(ax):
    return [
        (float(line.get_xdata()[0]), float(line.get_ydata()[0]))
        for line in lines(ax, "failure_point")
    ]


def footnote(ax):
    return " ".join(t.get_text() for t in ax.texts if "Left out" in t.get_text())


def twin_of(ax):
    (twin,) = [a for a in ax.get_shared_x_axes().get_siblings(ax) if a is not ax]
    return twin


# --- AC 1-2: failure readings and the fit -------------------------------------------


def test_ac1_max_deviator_stress_fit_is_p11_golden_1():
    _, ax, fit = draw(
        readings("A", "B"), space="s_t", failure_criterion="max_deviator_stress"
    )
    row = fit.to_frame().iloc[0]
    assert row["effective_cohesion"] == pytest.approx(25 * math.sqrt(2), rel=1e-7)
    assert row["effective_friction_angle"] == pytest.approx(19.471221, rel=1e-7)
    assert dots(ax) == pytest.approx([(200, 100), (350, 150)], rel=REL)


def test_ac2_max_stress_ratio():
    _, ax, fit = draw(
        readings("A", "B"), space="s_t", failure_criterion="max_stress_ratio"
    )
    row = fit.to_frame().iloc[0]
    assert row["effective_cohesion"] == pytest.approx(37.123106, rel=1e-7)
    assert row["effective_friction_angle"] == pytest.approx(19.471221, rel=1e-7)
    # (σ′3, σ′1) = (90, 285) and (185, 475): s′ = 187.5, 330; t = 97.5, 145.
    assert dots(ax) == pytest.approx([(187.5, 97.5), (330, 145)], rel=REL)


# --- AC 4: paths --------------------------------------------------------------------


def test_ac4_r1_paths():
    _, ax, _ = draw(readings("A"), space="s_t", failure_criterion="max_deviator_stress")
    (path,) = lines(ax, "stress_path")
    xy = np.column_stack([path.get_xdata(), path.get_ydata()])
    assert xy[0] == pytest.approx([200, 0])
    assert xy[2] == pytest.approx([200, 90])  # 4 %: σ′3 110, σ′1 290
    _, ax, _ = draw(readings("A"), space="p_q", failure_criterion="max_deviator_stress")
    (path,) = lines(ax, "stress_path")
    assert [path.get_xdata()[2], path.get_ydata()[2]] == pytest.approx([170, 180])
    assert [path.get_xdata()[0], path.get_ydata()[0]] == pytest.approx([200, 0])


def test_ac4_r3_drained_path_has_slope_1_and_3():
    with pytest.warns(UserWarning, match=BACK_PRESSURE):
        _, ax, _ = ht.plot.triaxial_shearing(
            readings("C"),
            space="s_t",
            failure_criterion="max_deviator_stress",
            display_units="SI",
        )
    (path,) = lines(ax, "stress_path")
    x, y = path.get_xdata(), path.get_ydata()
    assert [x[3], y[3]] == pytest.approx([225, 125])
    assert np.diff(y) / np.diff(x) == pytest.approx(np.ones(4))
    with pytest.warns(UserWarning, match=BACK_PRESSURE):
        _, ax, _ = ht.plot.triaxial_shearing(
            readings("C"),
            space="p_q",
            failure_criterion="max_deviator_stress",
            display_units="SI",
        )
    (path,) = lines(ax, "stress_path")
    x, y = path.get_xdata(), path.get_ydata()
    assert [x[3], y[3]] == pytest.approx([100 + 250 / 3, 250])
    assert np.diff(y) / np.diff(x) == pytest.approx(np.full(4, 3.0))


# --- AC 5-6: the same reading in every view; aspect --------------------------------


@pytest.mark.parametrize("criterion", ["max_deviator_stress", "max_stress_ratio"])
def test_ac5_the_same_reading_in_every_view(criterion):
    df = readings("A", "B")
    _, ax, _ = draw(df, failure_criterion=criterion)
    strains = [x for x, _ in dots(ax)]
    rows = ht.analysis.triaxial_failure_from_readings(df, failure_criterion=criterion)
    assert strains == list(rows["axial_strain_at_failure"])
    stresses = ht.analysis.triaxial_failure_stresses(rows)
    minor = stresses["effective_minor_principal_stress_at_failure"].to_numpy()
    major = stresses["effective_major_principal_stress_at_failure"].to_numpy()
    _, ax, _ = draw(df, space="s_t", failure_criterion=criterion)
    assert dots(ax) == pytest.approx(
        list(zip((major + minor) / 2, (major - minor) / 2, strict=True))
    )
    _, ax, _ = draw(df, space="p_q", failure_criterion=criterion)
    assert dots(ax) == pytest.approx(
        list(zip((major + 2 * minor) / 3, major - minor, strict=True))
    )
    _, p11, _ = ht.plot.failure_envelope(stresses, space="s_t", display_units="SI")
    assert dots(p11) == pytest.approx(
        list(zip((major + minor) / 2, (major - minor) / 2, strict=True))
    )


def test_ac6_equal_aspect_in_stress_spaces_only():
    df = readings("A", "B")
    for space in ("s_t", "p_q"):
        _, ax, _ = draw(df, space=space, failure_criterion="max_deviator_stress")
        assert ax.get_aspect() == 1
    _, ax, _ = draw(df, failure_criterion="max_deviator_stress")
    assert ax.get_aspect() == "auto"
    assert ax.get_xlim()[0] == 0 and ax.get_ylim()[0] == 0
    assert ax.get_xlim()[1] > 15 and ax.get_ylim()[1] > 300


# --- AC 7: the second axis ----------------------------------------------------------


def test_ac7_excess_pore_pressure_on_a_twin_axis():
    _, ax, _ = draw(
        readings("A", "B"),
        failure_criterion="max_deviator_stress",
        second_axis="excess_pore_pressure",
    )
    twin = twin_of(ax)
    drawn = [line for line in twin.lines if line.get_gid() == "second_axis_line"]
    assert [list(line.get_ydata()) for line in drawn] == [
        [0, 50, 90, 100, 110, 112],
        [0, 40, 80, 100, 115, 120],
    ]
    assert all(line.get_linestyle() == "--" for line in drawn)
    assert twin.get_ylabel() == "Excess pore pressure, Δu (kPa)"


def test_ac7_volumetric_strain_shows_dilation():
    with pytest.warns(UserWarning, match=BACK_PRESSURE):
        _, ax, _ = ht.plot.triaxial_shearing(
            readings("C"),
            failure_criterion="max_deviator_stress",
            second_axis="volumetric_strain",
            display_units="SI",
        )
    twin = twin_of(ax)
    (line,) = [line for line in twin.lines if line.get_gid() == "second_axis_line"]
    assert list(line.get_ydata()) == [0, 0.3, 0.2, -0.4, -0.8]
    assert twin.get_ylim()[0] < -0.8


# --- AC 8: left out and counted -----------------------------------------------------


def test_ac8_uu_is_left_out_of_effective_paths():
    _, ax, _ = draw(
        readings("A", "B", "D"),
        space="s_t",
        failure_criterion="max_deviator_stress",
        fit=False,
    )
    assert len(lines(ax, "stress_path")) == 2
    assert "1 without effective stresses" in footnote(ax)


def test_ac8_uu_total_path():
    _, ax, fit = draw(
        readings("D"),
        space="s_t",
        stress="total",
        failure_criterion="max_deviator_stress",
    )
    (path,) = lines(ax, "stress_path")
    assert [path.get_xdata()[0], path.get_ydata()[0]] == pytest.approx([200, 0])
    assert [path.get_xdata()[2], path.get_ydata()[2]] == pytest.approx([260, 60])
    assert dots(ax) == pytest.approx([(260, 60)])
    assert fit.groups[0]["fits"][0]["no_fit_reason"] is not None


# --- AC 9: returns ------------------------------------------------------------------


def test_ac9_returns():
    df = readings("A", "B")
    fig, ax, fit = draw(df, space="s_t", failure_criterion="max_deviator_stress")
    rows = ht.analysis.triaxial_failure_stresses(
        ht.analysis.triaxial_failure_from_readings(
            df, failure_criterion="max_deviator_stress"
        )
    )
    expected = ht.analysis.mohr_coulomb_fit(rows, display_units="SI")
    pd.testing.assert_frame_equal(fit.to_frame(), expected.to_frame())
    assert ax.figure is fig
    assert draw(df, failure_criterion="max_deviator_stress")[2] is None
    _, ax, fit = draw(
        df, space="s_t", failure_criterion="max_deviator_stress", fit=False
    )
    assert fit is None and not lines(ax, "envelope")
    fig, given = plt.subplots()
    _, ax, _ = draw(df, failure_criterion="max_deviator_stress", ax=given)
    assert ax is given


# --- AC 12: edge cases (P12 §11) ----------------------------------------------------


def test_no_failure_reading_raises():
    with pytest.raises(HangtuError, match=r"No failure reading.*failure_criterion="):
        draw(readings("A"))


def test_ratio_on_uu_raises():
    with pytest.raises(HangtuError, match="needs effective stresses"):
        draw(readings("D"), failure_criterion="max_stress_ratio")


def test_decreasing_strain_raises():
    with pytest.raises(HangtuError, match="axial_strain decreases"):
        draw(
            readings("E", axial_strain=[0, 4, 2, 6]),
            failure_criterion="max_deviator_stress",
        )


def test_second_axis_outside_stress_strain_raises():
    with pytest.raises(HangtuError, match='needs space="stress_strain"'):
        draw(readings("A"), space="s_t", second_axis="excess_pore_pressure")


@pytest.mark.parametrize(
    "argument",
    [{"cohesion": 0}, {"multistage": False}, {"fit": False}, {"envelopes": []}],
)
def test_fit_arguments_in_stress_strain_raise(argument):
    with pytest.raises(HangtuError, match='drawn in space="s_t" or "p_q"'):
        draw(readings("A"), failure_criterion="max_deviator_stress", **argument)


def test_color_by_with_group_by_raises():
    with pytest.raises(HangtuError, match="color_by= can't be used with group_by="):
        draw(readings("A"), group_by="test_type", color_by="test_type")


def test_drained_stage_has_no_excess_line():
    with pytest.warns(UserWarning, match=BACK_PRESSURE):
        _, ax, _ = ht.plot.triaxial_shearing(
            readings("A", "C"),
            failure_criterion="max_deviator_stress",
            second_axis="excess_pore_pressure",
            display_units="SI",
        )
    texts = " ".join(t.get_text() for t in ax.texts)
    assert "No Δu line: 1 stage without excess_pore_pressure" in texts
    assert (
        len(
            [line for line in twin_of(ax).lines if line.get_gid() == "second_axis_line"]
        )
        == 1
    )


def test_blank_readings_are_counted():
    df = readings("A", deviator_stress=[0, 100, 180, None, 195, 190])
    _, ax, _ = draw(df, failure_criterion="max_deviator_stress")
    (curve,) = lines(ax, "reading_curve")
    assert len(curve.get_xdata()) == 5
    assert "1 reading without axial strain or deviator stress" in footnote(ax)


def test_negative_deviator_stress_is_drawn():
    df = readings("A", deviator_stress=[-5, 100, 180, 200, 195, 190])
    _, ax, _ = draw(df, failure_criterion="max_deviator_stress")
    (curve,) = lines(ax, "reading_curve")
    assert curve.get_ydata()[0] == -5
    assert ax.get_ylim()[0] < -5


def test_extension_is_counted_in_paths():
    df = readings("A", "B", test_type=["CU"] * 6 + ["CAUE"] * 6)
    with pytest.warns(UserWarning, match="extension"):
        _, ax, _ = ht.plot.triaxial_shearing(
            df,
            space="s_t",
            failure_criterion="max_deviator_stress",
            fit=False,
            display_units="SI",
        )
    assert len(lines(ax, "stress_path")) == 1
    assert "1 extension stage" in footnote(ax)


def test_missing_units_raise():
    df = readings("A")
    df.attrs["units"] = {}
    with pytest.raises(UnitsError, match="cell_pressure"):
        draw(df, failure_criterion="max_deviator_stress")


def test_group_by_colors_and_fits_per_group():
    df = readings("A", "B")
    df["geology_unit"] = ["ALV"] * 6 + ["TRC"] * 6
    _, ax, fit = draw(
        df,
        space="s_t",
        failure_criterion="max_deviator_stress",
        group_by="geology_unit",
    )
    colors = {line.get_color() for line in lines(ax, "stress_path")}
    assert len(colors) == 2
    assert len(fit.groups) == 2


@pytest.mark.parametrize(
    ("criterion", "text"),
    [
        ("max_deviator_stress", "Failure: maximum deviator stress"),
        ("max_stress_ratio", "Failure: maximum principal stress ratio"),
        (None, "Failure: lab's reading"),
    ],
)
@pytest.mark.parametrize("space", ["stress_strain", "s_t"])
def test_the_legend_says_the_dot_is_the_failure_reading(criterion, text, space):
    df = readings("A", "B")
    df["reported_failure_reading"] = df["axial_strain"] == 8
    if criterion is not None:
        df = df.drop(columns="reported_failure_reading")
    _, ax, _ = draw(df, space=space, failure_criterion=criterion)
    labels = [t.get_text().replace("\n", " ") for t in ax.get_legend().get_texts()]
    assert text in labels
