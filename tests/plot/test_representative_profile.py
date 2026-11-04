"""P09 representative value profile (docs/plots/P09-representative-profile.md §12)."""

import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import PathCollection, PolyCollection
from matplotlib.colors import to_rgb

import hangtu as ht
from hangtu.errors import HangtuError
from hangtu.plot import _layers
from hangtu.plot._overlays import format_number

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


# --- criterion 3: table -----------------------------------------------------------


def table_lines(ax):
    """The table's lines, trailing spaces removed; [] when there is none."""
    boxes = [text for text in ax.texts if text.get_bbox_patch() is not None]
    if not boxes:
        return []
    (box,) = boxes
    return [line.rstrip() for line in box.get_text().split("\n")]


def footnote(ax):
    return "\n".join(
        text.get_text() for text in ax.texts if text.get_bbox_patch() is None
    )


def test_table_names_the_view_and_gives_each_units_value():
    _, ax, result = draw()
    lines = table_lines(ax)
    view = " ".join(lines[:-2])
    assert view == result._view()
    values = result.to_frame().set_index("geology_unit")["value"]
    counts = result.to_frame().set_index("geology_unit")["count"]
    # Legend order: Lower, then Upper.
    for line, unit in zip(lines[-2:], ["Lower", "Upper"], strict=True):
        assert line.split() == [
            unit,
            "n",
            "=",
            str(counts[unit]),
            format_number(values[unit]),
            "kPa",
        ]


def test_table_gives_a_trends_top_and_base():
    _, ax, result = draw(trend="depth")
    frame = result.to_frame().set_index("geology_unit")
    for line, unit in zip(table_lines(ax)[-2:], ["Lower", "Upper"], strict=True):
        top = format_number(frame.loc[unit, "value_top"])
        base = format_number(frame.loc[unit, "value_base"])
        assert line.split() == [
            unit,
            "n",
            "=",
            str(frame.loc[unit, "count"]),
            top,
            "→",
            base,
            "kPa",
        ]


def test_table_gives_a_unit_with_no_line_its_reason():
    df = strength().drop(index=[7, 8, 9])  # Lower keeps one value
    _, ax, result = draw(df)
    reason = result.to_frame().set_index("geology_unit").loc["Lower", "reason"]
    lower = [line for line in table_lines(ax) if line.startswith("Lower")]
    assert lower == [f"Lower  n = 1  — {reason}"]
    assert f"No line: Lower ({reason})." in footnote(ax)


def test_table_counts_a_constants_censored_values():
    df = strength(qualifier=[""] * 4 + [">", ">"] + [""] * 4)
    _, ax, _ = draw(df)
    (upper,) = [line for line in table_lines(ax) if line.startswith("Upper")]
    assert "n = 6 (2 censored)" in upper


def test_table_false_draws_no_table():
    _, ax, _ = draw(table=False)
    assert table_lines(ax) == []
    assert len(lines_at(ax, _layers.REPRESENTATIVE)) == 2


def test_table_sits_below_the_lowest_data():
    _, ax, _ = draw(trend="depth")
    bottom, _ = ax.get_ylim()
    assert bottom > 12.0  # deepened past the deepest value, 12 m


# --- criterion 4: a trend's censored values ---------------------------------------


def test_trend_footnote_counts_censored_values_and_values_with_no_depth():
    df = strength(qualifier=[""] * 4 + [">", ">"] + [""] * 4)
    df.loc[2, "depth"] = np.nan
    with pytest.warns(UserWarning, match="out of the trend"):
        _, ax, result = draw(df, trend="depth")
    counts = result.to_frame().set_index("geology_unit").loc["Upper"]
    assert counts["count_censored"] == 2
    assert counts["count_blank_depth"] == 1
    assert "Left out of the lines: Upper 2 censored, 1 with no depth." in footnote(ax)
    # P01 draws the two at their limits and counts the one it can't place.
    assert ax.ags_notes == {"greater_than": 2, "nan": 1}


def test_constant_has_no_left_out_line():
    df = strength(qualifier=[""] * 4 + [">", ">"] + [""] * 4)
    _, ax, _ = draw(df)
    assert "Left out of the lines" not in footnote(ax)


# --- criterion 5: values left out by both -----------------------------------------


def density_frame():
    """Particle density with two assumed values."""
    df = pd.DataFrame(
        {
            "loca_id": ["A"] * 6,
            "depth": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "ground_level": [100.0] * 6,
            "geology_unit": ["Clay"] * 6,
            "particle_density": [2.65, 2.70, 2.68, 2.72, 2.66, 2.71],
            "particle_density_assumed": [False, True, False, False, True, False],
        }
    )
    units = {"depth": "m", "ground_level": "m", "particle_density": "Mg/m3"}
    return ht.set_units(df, units)


DENSITY = {
    "value": "particle_density",
    "by": "geology_unit",
    "distribution": "normal",
    "display_units": "SI",
    **VIEW,
}


def test_assumed_values_are_drawn_and_counted_not_in_the_lines():
    with pytest.warns(UserWarning, match="assumed"):
        _, ax, result = ht.plot.representative_profile(density_frame(), **DENSITY)
    points = [c for c in ax.collections if isinstance(c, PathCollection)]
    assert sum(len(c.get_offsets()) for c in points) == 6
    assert result.groups[0]["counts"]["count"] == 4
    assert "Not in the lines: 2 assumed." in footnote(ax)


def test_include_assumed_puts_them_in_the_lines():
    _, ax, result = ht.plot.representative_profile(
        density_frame(), include_assumed=True, **DENSITY
    )
    alone = ht.stats.representative(density_frame(), include_assumed=True, **DENSITY)
    assert result.groups[0]["counts"]["count"] == 6
    (line,) = lines_at(ax, _layers.REPRESENTATIVE)
    np.testing.assert_allclose(line.get_xdata(), alone.groups[0]["value"], rtol=1e-12)
    assert "Not in the lines" not in footnote(ax)
