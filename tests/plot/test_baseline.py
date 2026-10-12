"""P07 baseline table: format, units and drawing (P07 §8, §9, §11)."""

import re

import matplotlib as mpl
import numpy as np
import pandas as pd
import pytest

import hangtu as ht

GRAY = mpl.colors.to_rgb("0.25")


def table(**columns):
    data = {
        "geology_unit": ["Clay", "Fill", "Sand"],
        "low": [1000.0, 400.0, 600.0],
        "central": [1500.0, 800.0, 900.0],
        "high": [2000.0, 1200.0, 1300.0],
        **columns,
    }
    return pd.DataFrame(data)


def psf(frame):
    return ht.set_units(frame, {"low": "psf", "central": "psf", "high": "psf"})


def baseline_bars(ax):
    """{row: (low, high)} for the gray baseline bars."""
    found = {}
    for line in ax.lines:
        x, y = (np.asarray(a, dtype=float) for a in line.get_data())
        gray = mpl.colors.same_color(line.get_color(), GRAY)
        if gray and line.get_marker() in ("None", "") and len(x) == 2:
            found[round(y[0] + 0.28, 6)] = tuple(x)
    return found


def diamonds(ax):
    """{row: central} for the baseline diamonds."""
    return {
        round(float(line.get_ydata()[0]) + 0.28, 6): float(line.get_xdata()[0])
        for line in ax.lines
        if line.get_marker() == "D"
    }


def legend_texts(ax):
    return [text.get_text() for text in ax.get_legend().get_texts()]


def count_labels(ax):
    return [text.get_text() for text in ax.texts if text.get_text().startswith("n =")]


@pytest.fixture(name="plot")
def _plot(comparison):
    def plot(baseline, **kwargs):
        kwargs.setdefault("summary", None)
        return ht.plot.geology_unit_comparison(
            comparison(), "undrained_shear_strength", baseline=baseline, **kwargs
        )

    return plot


# --- drawing ------------------------------------------------------------------


def test_bars_sit_above_each_row_with_a_diamond_at_central(plot):
    _, ax = plot(psf(table()))
    assert baseline_bars(ax) == {
        0.0: (1000.0, 2000.0),
        1.0: (400.0, 1200.0),
        2.0: (600.0, 1300.0),
    }
    assert diamonds(ax) == {0.0: 1500.0, 1.0: 800.0, 2.0: 900.0}


def test_baseline_comes_first_in_the_legend(plot):
    _, ax = plot(psf(table()), baseline_label="GBR baseline p10-p90, p50")
    assert legend_texts(ax) == ["GBR baseline p10-p90, p50", "Data"]


@pytest.mark.parametrize(
    ("sources", "text"),
    [
        (["GBR Table 4-2"] * 3, "GBR Table 4-2"),
        (["GBR Table 4-2", "GBR Table 4-2", None], "GBR Table 4-2"),
        (["GBR", "GIR", "GBR"], "Baseline"),
        (None, "Baseline"),
    ],
)
def test_legend_falls_back_to_the_one_source(plot, sources, text):
    frame = table() if sources is None else table(source=sources)
    _, ax = plot(psf(frame))
    assert legend_texts(ax)[0] == text


def test_a_unit_only_in_the_baseline_gets_a_row_with_n_0(plot):
    frame = table(
        geology_unit=["Clay", "Fill", "Till"],
    )
    _, ax = plot(psf(frame), order=["Fill", "Till"])
    rows = [label.get_text() for label in ax.get_yticklabels()]
    assert rows == ["Fill", "Till", "Clay", "Sand"]
    assert count_labels(ax) == ["n = 2", "n = 0", "n = 2", "n = 2"]
    assert 1.0 in baseline_bars(ax)


def test_a_central_only_row_draws_just_the_diamond(plot):
    frame = table(low=[1000.0, np.nan, 600.0], high=[2000.0, np.nan, 1300.0])
    _, ax = plot(psf(frame))
    assert set(baseline_bars(ax)) == {0.0, 2.0}
    assert diamonds(ax)[1.0] == 800.0


def test_default_limits_cover_a_baseline_wider_than_the_data(plot):
    frame = table(high=[2000.0, 1200.0, 4800.0])
    _, ax = plot(psf(frame))
    assert ax.get_xlim()[1] >= 4800.0


def test_rows_for_other_properties_are_ignored(plot):
    frame = pd.concat(
        [
            table(property=["undrained_shear_strength"] * 3),
            table(property=["water_content"] * 3, low=[1.0] * 3, high=[2.0] * 3),
        ],
        ignore_index=True,
    )
    _, ax = plot(psf(frame))
    assert len(baseline_bars(ax)) == 3


def test_baseline_can_be_a_csv_path(plot, tmp_path):
    path = tmp_path / "baseline.csv"
    table().to_csv(path, index=False)
    with pytest.warns(UserWarning, match="no units"):
        _, ax = plot(str(path))
    assert len(baseline_bars(ax)) == 3


def test_a_low_at_or_below_zero_starts_at_the_edge_of_a_log_axis(comparison):
    df = comparison(
        "hydraulic_conductivity", (1e-5, 3e-6, 2e-4, 5e-7, 1e-6, 4e-5), "cm/s"
    )
    frame = pd.DataFrame(
        {"geology_unit": ["Clay"], "low": [0.0], "central": [1e-6], "high": [1e-5]}
    )
    frame = ht.set_units(frame, {"low": "cm/s", "central": "cm/s", "high": "cm/s"})
    _, ax = ht.plot.geology_unit_comparison(
        df, "hydraulic_conductivity", baseline=frame, summary=None
    )
    (bar,) = baseline_bars(ax).values()
    assert bar == pytest.approx((ax.get_xlim()[0], 1e-5))


# --- units --------------------------------------------------------------------


def test_baseline_in_psf_is_drawn_in_kpa(plot):
    _, ax = plot(psf(table()), display_units="SI")
    assert baseline_bars(ax)[0.0] == pytest.approx((47.88, 95.76), abs=0.01)


def test_baseline_units_win_over_declared_units(plot):
    frame = table(low=[50.0, 20.0, 30.0], central=[70.0] * 3, high=[95.76, 60.0, 65.0])
    _, ax = plot(psf(frame), baseline_units={"undrained_shear_strength": "kPa"})
    assert baseline_bars(ax)[0.0][1] == pytest.approx(2000.0, abs=0.1)


def test_undeclared_units_are_the_datas_with_a_warning(plot):
    expected = re.escape('baseline_units={"undrained_shear_strength": "psf"}')
    with pytest.warns(UserWarning, match=expected):
        _, ax = plot(table())
    assert baseline_bars(ax)[0.0] == (1000.0, 2000.0)


def test_no_warning_for_a_quantity_without_units(comparison):
    df = comparison("water_content", (10.0, 12.0, 20.0, 22.0, 30.0, 31.0), None)
    frame = pd.DataFrame({"geology_unit": ["Clay"], "low": [15.0], "high": [25.0]})
    ht.plot.geology_unit_comparison(df, "water_content", baseline=frame)


def test_unknown_baseline_units_key_is_an_error(plot):
    with pytest.raises(ht.HangtuError, match="undrained_shear_strenght"):
        plot(table(), baseline_units={"undrained_shear_strenght": "kPa"})


def test_baseline_unit_of_the_wrong_kind_is_an_error(plot):
    with pytest.raises(ht.UnitsError, match="stress"):
        plot(table(), baseline_units={"undrained_shear_strength": "ft"})


def test_us_and_si_put_the_baseline_in_the_same_place(plot):
    _, us = plot(psf(table()), display_units="US")
    _, si = plot(psf(table()), display_units="SI")
    for row, (low, high) in baseline_bars(us).items():
        assert np.array(baseline_bars(si)[row]) == pytest.approx(
            np.array([low, high]) * 0.04788026
        )


# --- rows that can't be drawn -------------------------------------------------


@pytest.mark.parametrize(
    ("columns", "message", "drawn"),
    [
        ({"geology_unit": ["Clay", None, "Sand"]}, "no geology_unit", {0.0, 2.0}),
        ({"low": [3000.0, 400.0, 600.0]}, "low above high", {1.0, 2.0}),
        ({"high": [2000.0, np.nan, 1300.0]}, "only one end", {0.0, 2.0}),
    ],
)
def test_rows_that_cant_be_drawn_warn(plot, columns, message, drawn):
    with pytest.warns(UserWarning, match=message):
        _, ax = plot(psf(table(**columns)))
    assert set(baseline_bars(ax)) == drawn


def test_a_row_with_nothing_to_draw_warns(plot):
    frame = table(low=[1000.0, np.nan, 600.0], central=[1500.0, np.nan, 900.0])
    frame["high"] = [2000.0, np.nan, 1300.0]
    with pytest.warns(UserWarning, match="no range or central value"):
        plot(psf(frame))


def test_two_rows_for_one_unit_are_an_error(plot):
    frame = table(geology_unit=["Clay", "Clay", "Sand"])
    with pytest.raises(ht.HangtuError, match=r"more than one row .* Clay"):
        plot(psf(frame))


def test_missing_fields_are_an_error(plot):
    with pytest.raises(ht.ColumnError, match=re.escape('ht.template("baseline")')):
        plot(table().drop(columns=["low", "central"]))


def test_baseline_of_the_wrong_type_is_an_error(plot):
    with pytest.raises(ht.HangtuError, match="DataFrame or the path"):
        plot([1, 2, 3])
