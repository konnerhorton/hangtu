"""P12 triaxial shearing (docs/plots/P12-triaxial-shearing.md, AC 1-9 and 12).

This commit covers the stress-strain view (AC 6, 7, 9 and 12 in part).

The readings are the M11 (c) spec's golden readings in
``tests/data/triaxial_readings_goldens.csv`` (kPa, percent): R1 is stages A
and B (CU), R3 stage C (CD, Δu blank), R4 stage D (UU). Expected positions
are the spec's hand calculations. Positions are read from the drawn artists.
"""

import warnings
from pathlib import Path

import matplotlib.pyplot as plt
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


def test_missing_units_raise():
    df = readings("A")
    df.attrs["units"] = {}
    with pytest.raises(UnitsError, match="cell_pressure"):
        draw(df, failure_criterion="max_deviator_stress")


def test_stress_strain_axes_and_return():
    df = readings("A", "B")
    fig, ax, fit = draw(df, failure_criterion="max_deviator_stress")
    assert fit is None and ax.figure is fig
    assert ax.get_aspect() == "auto"
    assert ax.get_xlim()[0] == 0 and ax.get_ylim()[0] == 0
    assert ax.get_xlim()[1] > 15 and ax.get_ylim()[1] > 300
    assert [x for x, _ in dots(ax)] == [8, 8]
    fig, given = plt.subplots()
    assert draw(df, failure_criterion="max_deviator_stress", ax=given)[1] is given
