"""P09 representative value profile (docs/plots/P09-representative-profile.md §12)."""

import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import PolyCollection
from matplotlib.colors import to_rgb

import hangtu as ht
from hangtu.errors import HangtuError
from hangtu.plot import _layers

from .conftest import assert_no_global_state

FT = 0.3048
KPA_PER_PSF = 0.047880258980335843

VIEW = {"method": "characteristic", "estimate": "mean", "side": "low"}


def strength(**columns):
    """Two clay units in m and kPa: Upper rises with depth, Lower is scattered."""
    data = {
        "loca_id": ["A", "A", "A", "B", "B", "B", "A", "A", "B", "B"],
        "depth": [1.5, 3.0, 4.5, 2.0, 3.5, 5.5, 8.0, 10.0, 9.0, 12.0],
        "ground_level": [100.0] * 10,
        "geology_unit": ["Upper"] * 6 + ["Lower"] * 4,
        "undrained_shear_strength": [
            22.0,
            35.0,
            41.0,
            30.0,
            33.0,
            58.0,
            80.0,
            120.0,
            95.0,
            70.0,
        ],
        **columns,
    }
    units = {"depth": "m", "ground_level": "m", "undrained_shear_strength": "kPa"}
    return ht.set_units(pd.DataFrame(data), units)


def draw(df=None, **kwargs):
    arguments = {
        "value": "undrained_shear_strength",
        "by": "geology_unit",
        "distribution": "normal",
        "display_units": "SI",
        **VIEW,
        **kwargs,
    }
    return ht.plot.representative_profile(strength() if df is None else df, **arguments)


def lines_at(ax, zorder):
    return [line for line in ax.lines if line.get_zorder() == zorder]


def bands(ax):
    return [
        c
        for c in ax.collections
        if isinstance(c, PolyCollection)
        and c.get_zorder() == _layers.REPRESENTATIVE_BAND
    ]


def legend_texts(ax):
    return [text.get_text() for text in ax.get_legend().get_texts()]


def units_of(result):
    return [group["key"]["geology_unit"] for group in result.groups]


def expected(result, label, vs="depth"):
    frame = result.design_lines(mean=True)
    rows = frame[frame["label"] == label]
    return rows["value"].to_numpy(), rows[vs].to_numpy()


# --- criterion 1: lines from the result -------------------------------------------


@pytest.mark.parametrize("trend", [None, "depth"])
@pytest.mark.parametrize("distribution", ["normal", "lognormal"])
def test_lines_are_the_results_design_lines(trend, distribution):
    _, ax, result = draw(trend=trend, distribution=distribution)
    center = "median" if distribution == "lognormal" else "mean"
    representative = lines_at(ax, _layers.REPRESENTATIVE)
    middle = lines_at(ax, _layers.REPRESENTATIVE_MEAN)
    assert len(representative) == len(middle) == 2
    for unit, line, mean_line in zip(
        units_of(result), representative, middle, strict=True
    ):
        x, y = expected(result, f"{unit}: characteristic, mean, low")
        np.testing.assert_allclose(line.get_xdata(), x, rtol=1e-12)
        np.testing.assert_allclose(line.get_ydata(), y, rtol=1e-12)
        x, y = expected(result, f"{unit}: {center}")
        np.testing.assert_allclose(mean_line.get_xdata(), x, rtol=1e-12)
        np.testing.assert_allclose(mean_line.get_ydata(), y, rtol=1e-12)
    assert len(representative[0].get_xdata()) == (50 if trend else 2)


def test_lines_are_in_the_units_colors():
    _, ax, result = draw()
    colors = {
        c.get_label(): to_rgb(c.get_facecolor()[0])
        for c in ax.collections
        if c.get_label() in ("Upper", "Lower")
    }
    lines = lines_at(ax, _layers.REPRESENTATIVE) + lines_at(
        ax, _layers.REPRESENTATIVE_MEAN
    )
    assert [to_rgb(line.get_color()) for line in lines] == [
        colors[unit] for unit in units_of(result)
    ] * 2
    representative = lines_at(ax, _layers.REPRESENTATIVE)[0]
    assert representative.get_linewidth() == 1.5
    assert representative.get_linestyle() == "-"
    assert lines_at(ax, _layers.REPRESENTATIVE_MEAN)[0].get_linestyle() == "--"


def test_constant_drawn_against_elevation_through_one_ground_level():
    _, ax, result = draw(vs="elevation")
    x, depth = expected(result, f"{units_of(result)[0]}: characteristic, mean, low")
    line = lines_at(ax, _layers.REPRESENTATIVE)[0]
    np.testing.assert_allclose(line.get_ydata(), 100.0 - depth, rtol=1e-12)
    np.testing.assert_allclose(line.get_xdata(), x, rtol=1e-12)


def test_constant_against_elevation_without_one_ground_level_raises():
    df = strength()
    df["ground_level"] = [100.0] * 6 + [90.0] * 4
    with pytest.raises(HangtuError, match="don't share one ground level"):
        draw(df, vs="elevation")


# --- criterion 2: band ------------------------------------------------------------


@pytest.mark.parametrize("trend", [None, "depth"])
def test_one_band_per_unit_between_the_two_lines(trend):
    _, ax, result = draw(trend=trend)
    found = bands(ax)
    assert len(found) == 2
    for unit, band in zip(units_of(result), found, strict=True):
        x, y = expected(result, f"{unit}: characteristic, mean, low")
        middle, _ = expected(result, f"{unit}: mean")
        vertices = band.get_paths()[0].vertices
        assert np.isclose(vertices[:, 0].min(), min(x.min(), middle.min()))
        assert np.isclose(vertices[:, 0].max(), max(x.max(), middle.max()))
        assert np.isclose(vertices[:, 1].min(), y.min())
        assert np.isclose(vertices[:, 1].max(), y.max())
        assert band.get_alpha() == 0.15
    # Under the values.
    assert _layers.REPRESENTATIVE_BAND < _layers.MARKERS


def test_band_false_draws_no_band():
    _, ax, _ = draw(band=False)
    assert bands(ax) == []
    assert len(lines_at(ax, _layers.REPRESENTATIVE_MEAN)) == 2
    assert "mean to characteristic" not in legend_texts(ax)


# --- legend -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("view", "distribution", "names"),
    [
        (VIEW, "normal", ["characteristic", "mean", "mean to characteristic"]),
        (
            {"method": "percentile", "percentile": 10, "side": "low"},
            "lognormal",
            ["percentile 10", "median", "median to percentile 10"],
        ),
        (
            {
                "method": "standard_deviations",
                "standard_deviations": 1.5,
                "side": "low",
            },
            "normal",
            ["mean - 1.5 std", "mean", "mean to mean - 1.5 std"],
        ),
    ],
)
def test_legend_names_the_view(view, distribution, names):
    df = strength()
    _, ax, _ = ht.plot.representative_profile(
        df,
        value="undrained_shear_strength",
        by="geology_unit",
        distribution=distribution,
        display_units="SI",
        **view,
    )
    assert legend_texts(ax) == ["Lower", "Upper", *names]


# --- criterion 6: judgments -------------------------------------------------------


def test_missing_judgment_raises_representatives_error_unchanged():
    with pytest.raises(HangtuError) as from_stats:
        ht.stats.representative(
            strength(),
            value="undrained_shear_strength",
            by="geology_unit",
            method="characteristic",
            estimate="mean",
            distribution="normal",
        )
    with pytest.raises(HangtuError) as from_plot:
        draw(side=None)
    assert str(from_plot.value) == str(from_stats.value)


# --- criterion 7: arguments -------------------------------------------------------


def test_mean_false_removes_only_the_mean_lines():
    _, ax, _ = draw(mean=False)
    assert lines_at(ax, _layers.REPRESENTATIVE_MEAN) == []
    assert len(lines_at(ax, _layers.REPRESENTATIVE)) == 2
    assert len(bands(ax)) == 2
    assert legend_texts(ax) == [
        "Lower",
        "Upper",
        "characteristic",
        "mean to characteristic",
    ]


def test_by_with_several_columns_raises():
    with pytest.raises(HangtuError, match="by= is one column"):
        draw(by=["geology_unit", "loca_id"])


def test_vs_other_than_the_trends_column_raises():
    with pytest.raises(HangtuError, match="drawn against depth, not vs='elevation'"):
        draw(trend="depth", vs="elevation")


def test_by_none_draws_one_group_in_one_color():
    _, ax, result = draw(by=None)
    (line,) = lines_at(ax, _layers.REPRESENTATIVE)
    x, _ = expected(result, "All: characteristic, mean, low")
    np.testing.assert_allclose(line.get_xdata(), x, rtol=1e-12)
    assert legend_texts(ax) == ["characteristic", "mean", "mean to characteristic"]


# --- criterion 9: contract --------------------------------------------------------


def test_returns_figure_axes_and_result_and_draws_into_ax():
    import matplotlib.pyplot as plt

    fig, given = plt.subplots()
    out_fig, ax, result = draw(ax=given)
    assert out_fig is fig and ax is given
    assert isinstance(result, ht.stats.RepresentativeResult)


def test_no_global_state():
    def plot(df, **kwargs):
        return draw(df, **kwargs)[:2]

    assert_no_global_state(plot, strength())
    assert_no_global_state(plot, strength(), trend="depth")


# --- criterion 10: units ----------------------------------------------------------


@pytest.mark.parametrize("trend", [None, "depth"])
def test_us_and_si_differ_only_by_the_conversion(trend):
    _, us, _ = draw(trend=trend, display_units="US")
    _, si, _ = draw(trend=trend, display_units="SI")
    for zorder in (_layers.REPRESENTATIVE, _layers.REPRESENTATIVE_MEAN):
        for us_line, si_line in zip(
            lines_at(us, zorder), lines_at(si, zorder), strict=True
        ):
            np.testing.assert_allclose(
                us_line.get_xdata() * KPA_PER_PSF, si_line.get_xdata(), rtol=1e-9
            )
            np.testing.assert_allclose(
                us_line.get_ydata() * FT, si_line.get_ydata(), rtol=1e-9
            )
    assert us.ags_notes == si.ags_notes
    assert "psf" in us.get_xlabel() and "kPa" in si.get_xlabel()


# --- §11 edge cases ---------------------------------------------------------------


def test_line_at_or_below_zero_on_a_log_axis_is_cut_and_counted():
    # Upper's spread takes its fractile (Type B) below 0: k_n s > mean.
    df = strength()
    df.loc[df["geology_unit"] == "Upper", "undrained_shear_strength"] = [
        2.0,
        60.0,
        3.0,
        70.0,
        4.0,
        80.0,
    ]
    with pytest.warns(UserWarning, match="at or below 0"):
        _, ax, result = draw(df, log=True, estimate="fractile")
    upper = result.to_frame().set_index("geology_unit").loc["Upper", "value"]
    assert upper <= 0
    assert ax.ags_notes["line_log_nonpositive"] == 1
    line = lines_at(ax, _layers.REPRESENTATIVE)[units_of(result).index("Upper")]
    assert np.isnan(line.get_xdata()).all()


def test_line_beyond_xlim_is_clipped_and_counted():
    _, ax, _ = draw(xlim=(30.0, 200.0))
    # Upper's characteristic value is below 30 kPa; its mean is not.
    assert ax.ags_notes["line_beyond_limit"] == 1
    assert ax.get_xlim() == (30.0, 200.0)


def test_automatic_limits_cover_the_lines():
    _, ax, result = draw(trend="depth")
    low, high = ax.get_xlim()
    values = result.design_lines(mean=True)["value"]
    assert low <= values.min() and values.max() <= high
    assert "line_beyond_limit" not in ax.ags_notes


def test_no_unit_with_a_line_draws_values_without_line_entries():
    df = strength().iloc[[0, 6]]  # one value per unit: no line
    _, ax, result = draw(df)
    assert all(group["reason"] for group in result.groups)
    assert lines_at(ax, _layers.REPRESENTATIVE) == []
    assert bands(ax) == []
    assert legend_texts(ax) == ["Lower", "Upper"]
