"""P08 distribution fit (docs/plots/P08-distribution-fit.md §12)."""

import numpy as np
import pandas as pd
import pytest
from matplotlib.text import Annotation

import hangtu as ht
from hangtu.errors import HangtuError, UnitsError
from hangtu.stats import _fit as fit_module
from hangtu.units import to_display

STRENGTH = [10.0, 12, 15, 20, 23]
N60 = [12, 18, 25, 31, 40]
#: Twelve values, so no small-sample warning.
TWELVE = [14.0, 18, 21, 25, 27, 30, 33, 38, 42, 47, 55, 68]


@pytest.fixture(autouse=True)
def _short_bootstrap(monkeypatch):
    """Draw few bootstrap samples: no test here checks a p-value's digits."""
    monkeypatch.setattr(fit_module, "BOOTSTRAP_SAMPLES", 19)


def _strength(values=TWELVE, unit="kPa", **columns):
    df = pd.DataFrame({"undrained_shear_strength": values, **columns})
    return ht.set_units(df, {"undrained_shear_strength": unit})


def _plot(df, **kwargs):
    kwargs.setdefault("value", "undrained_shear_strength")
    kwargs.setdefault("display_units", "SI")
    return ht.plot.distribution_fit(df, **kwargs)


def _curves(ax):
    return {
        line.get_label().split(" (")[0]: line
        for line in ax.lines
        if "(rank" in line.get_label()
    }


def _table(ax):
    texts = [t.get_text() for t in ax.texts if t.get_text().startswith("Rank")]
    return texts[0] if texts else None


def test_returns_two_panels_and_the_result():
    _, axs, result = _plot(_strength())
    assert axs.shape == (2,)
    assert result.function == "fit"
    assert axs[0].get_xlabel() == "Undrained shear strength, s_u (kPa)"
    assert axs[0].get_ylabel() == "Probability density (1/kPa)"
    assert axs[1].get_xlabel() == "Fitted quantile, lognormal (kPa)"


def test_bar_areas_are_the_share_uncensored_and_curves_are_the_pdfs():
    # AC 1
    df = pd.DataFrame(
        {"spt_n60": [*TWELVE, 100, 100], "spt_refusal": [False] * 12 + [True] * 2}
    )
    _, axs, result = ht.plot.distribution_fit(df, value="spt_n60")
    histogram = axs[0]
    area = sum(bar.get_width() * bar.get_height() for bar in histogram.patches)
    assert area == pytest.approx(12 / 14, rel=1e-9)
    curves = _curves(histogram)
    assert set(curves) == {"normal", "lognormal", "gamma", "weibull"}
    for name, line in curves.items():
        x, y = line.get_xydata().T
        np.testing.assert_allclose(y, result.distribution(name).pdf(x), rtol=1e-12)
    ranks = {fit["distribution"]: fit["rank"] for fit in result.groups[0]["fits"]}
    best = min(ranks, key=ranks.get)
    assert curves[best].get_linestyle() == "-"
    assert all(curves[name].get_linestyle() == "--" for name in curves if name != best)


def test_q_q_points_are_the_fitted_quantiles_at_hazens_positions():
    # AC 2, with the Spec's AC 5 values.
    with pytest.warns(UserWarning, match="fewer than 10"):
        _, axs, result = _plot(_strength(STRENGTH), qq="normal")
    points = next(line for line in axs[1].lines if line.get_marker() == "o")
    x, y = points.get_xydata().T
    expected = result.distribution("normal").ppf([0.1, 0.3, 0.5, 0.7, 0.9])
    np.testing.assert_allclose(x, expected, rtol=1e-12)
    assert y.tolist() == STRENGTH
    assert axs[1].get_xlim() == axs[1].get_ylim()
    assert axs[1].get_xlabel() == "Fitted quantile, normal (kPa)"


def test_refusals_are_open_triangles_with_a_count():
    # AC 3
    df = pd.DataFrame(
        {"spt_n60": [*N60, 100, 100], "spt_refusal": [False] * 5 + [True] * 2}
    )
    with pytest.warns(UserWarning, match="fewer than 10"):
        _, axs, _ = ht.plot.distribution_fit(df, value="spt_n60")
    triangles = [line for line in axs[0].lines if line.get_marker() == ">"]
    assert len(triangles) == 1
    assert triangles[0].get_xdata().tolist() == [100, 100]
    assert triangles[0].get_markerfacecolor() == "none"
    labels = [text.get_text() for text in axs[0].get_legend().get_texts()]
    assert "≥ 100: 2" in labels
    # The bars are the uncensored values; the refusals have their own entry.
    assert "Values (n = 5)" in labels
    table = _table(axs[1]).splitlines()
    assert all(row.rstrip().endswith("—") for row in table[1:])
    assert "No AD check: 2 censored" in _footnote(axs[0])


def _footnote(ax):
    return "\n".join(
        text.get_text()
        for text in ax.texts
        if isinstance(text, Annotation) and not text.get_text().startswith("Rank")
    )


def test_distributions_draws_only_those():
    # AC 4
    _, axs, result = _plot(_strength(), distributions=["normal", "lognormal"])
    assert set(_curves(axs[0])) == {"normal", "lognormal"}
    assert result.distributions == ("normal", "lognormal")
    assert len(_table(axs[1]).splitlines()) == 3


def test_qq_chooses_the_q_q_distribution():
    _, axs, _ = _plot(_strength(), qq="weibull")
    points = next(line for line in axs[1].lines if line.get_marker() == "o")
    assert points.get_color() == "#CC79A7"
    with pytest.raises(HangtuError, match="qq='beta' isn't among the fits"):
        _plot(_strength(), qq="beta")


def test_table_false_leaves_only_the_table_out():
    _, with_table, _ = _plot(_strength())
    _, without, _ = _plot(_strength(), table=False)
    assert _table(with_table[1]) is not None
    assert _table(without[1]) is None
    for a, b in zip(with_table[0].lines, without[0].lines, strict=True):
        np.testing.assert_array_equal(a.get_xydata(), b.get_xydata())


def test_log_spaces_the_bins_and_the_axes():
    _, axs, _ = _plot(_strength(), log=True)
    histogram, quantiles = axs
    assert histogram.get_xscale() == "log"
    assert quantiles.get_xscale() == quantiles.get_yscale() == "log"
    lefts = np.array([bar.get_x() for bar in histogram.patches])
    widths = np.array([bar.get_width() for bar in histogram.patches])
    ratios = (lefts + widths) / lefts
    np.testing.assert_allclose(ratios, ratios[0], rtol=1e-9)


def test_by_needs_a_group_listing_them():
    df = _strength([*TWELVE, *TWELVE], geology_unit=["A"] * 12 + ["B"] * 12)
    with pytest.raises(HangtuError, match="Name one with group=, from: 'A', 'B'"):
        _plot(df, by="geology_unit")
    with pytest.raises(HangtuError, match="no group 'C'"):
        _plot(df, by="geology_unit", group="C")
    _, _, result = _plot(df, by="geology_unit", group="B")
    assert [group["key"] for group in result.groups] == [{"geology_unit": "B"}]


def test_the_result_draws_the_same_figure():
    # AC 5
    df = _strength([*TWELVE, *TWELVE], geology_unit=["A"] * 12 + ["B"] * 12)
    _, drawn, _ = _plot(df, by="geology_unit", group="B")
    result = ht.stats.fit(
        df, value="undrained_shear_strength", by="geology_unit", display_units="SI"
    )
    _, again = result.plot(group="B")
    for a, b in zip(drawn, again, strict=True):
        assert len(a.lines) == len(b.lines)
        for line, other in zip(a.lines, b.lines, strict=True):
            np.testing.assert_allclose(line.get_xydata(), other.get_xydata())
        for bar, other in zip(a.patches, b.patches, strict=True):
            assert bar.get_bbox().bounds == pytest.approx(other.get_bbox().bounds)
        assert a.get_xlim() == b.get_xlim()


def test_us_and_si_differ_only_by_the_conversion():
    # AC 6
    c = to_display([1.0], "psf", "stress", "SI")[0][0]
    df = _strength([value / c for value in TWELVE], unit="psf")
    _, us, us_result = _plot(df, display_units="US")
    _, si, si_result = _plot(df, display_units="SI")
    assert (us_result.unit, si_result.unit) == ("psf", "kPa")
    us_points = next(line for line in us[1].lines if line.get_marker() == "o")
    si_points = next(line for line in si[1].lines if line.get_marker() == "o")
    np.testing.assert_allclose(
        us_points.get_xydata() * c, si_points.get_xydata(), rtol=1e-6
    )
    us_bars = [(b.get_x(), b.get_width(), b.get_height()) for b in us[0].patches]
    si_bars = [(b.get_x(), b.get_width(), b.get_height()) for b in si[0].patches]
    np.testing.assert_allclose(
        np.array(us_bars) * [c, c, 1 / c], np.array(si_bars), rtol=1e-9
    )
    for name, line in _curves(si[0]).items():
        x, y = line.get_xydata().T
        expected = us_result.distribution(name).pdf(x / c) / c
        np.testing.assert_allclose(y, expected, rtol=1e-5)
    assert us[0].get_xlabel().endswith("(psf)")


def test_too_few_values_draw_the_histogram_and_a_note():
    # distribution_fit() fits only the group drawn, so a small group is fit()'s
    # error; a result with several groups draws it with the note.
    df = _strength([*TWELVE, 10, 12, 15], geology_unit=["A"] * 12 + ["B"] * 3)
    with pytest.raises(HangtuError, match=r"no group has them: B \(3\)"):
        _plot(df, by="geology_unit", group="B")
    with pytest.warns(UserWarning, match="fewer than 4"):
        result = ht.stats.fit(df, value="undrained_shear_strength", by="geology_unit")
    _, axs = result.plot(group="B")
    assert len(axs[0].patches) > 0
    assert not _curves(axs[0])
    note = "too few values to fit (n = 3; 4 needed)"
    assert note in [text.get_text() for text in axs[0].texts]
    assert note in [text.get_text() for text in axs[1].texts]
    assert _table(axs[1]) is None


def test_a_group_of_three_alone_is_fits_error():
    df = _strength([10, 12, 15])
    with pytest.raises(HangtuError, match="needs at least 4 uncensored"):
        _plot(df)


def test_censored_both_ways_leaves_the_q_q_panel_empty():
    df = pd.DataFrame(
        {
            "hydraulic_conductivity": [0.1, *np.linspace(0.3, 3, 10), 9.0],
            "qualifier": ["<", *[None] * 10, ">"],
        }
    )
    df = ht.set_units(df, {"hydraulic_conductivity": "cm/s"})
    _, axs, _ = ht.plot.distribution_fit(
        df, value="hydraulic_conductivity", display_units="SI"
    )
    assert not [line for line in axs[1].lines if line.get_marker() == "o"]
    texts = [text.get_text() for text in axs[1].texts]
    assert "no plotting positions:\ncensored both ways" in texts
    assert "No plotting positions: censored both ways" in _footnote(axs[0])
    assert len(_curves(axs[0])) == 4


def test_values_at_zero_name_the_distributions_left_out():
    _, axs, _ = ht.plot.distribution_fit(
        pd.DataFrame({"spt_n60": [0, *TWELVE]}), value="spt_n60"
    )
    assert set(_curves(axs[0])) == {"normal"}
    assert "lognormal, gamma, weibull not fitted: 1 value at or below 0" in (
        _footnote(axs[0])
    )


def test_reference_lines_and_note():
    _, axs, _ = _plot(
        _strength(), reference_lines=[(30, "design")], note="Checked by hand."
    )
    assert any(line.get_xdata()[0] == 30 for line in axs[0].lines)
    assert "Checked by hand." in _footnote(axs[0])


def test_missing_units_are_fits_error():
    df = pd.DataFrame({"undrained_shear_strength": TWELVE})
    with pytest.raises(UnitsError, match="has no units"):
        ht.plot.distribution_fit(df, value="undrained_shear_strength")


def test_the_legend_stays_inside_the_histogram(tmp_path, monkeypatch):
    # With less headroom, the example project's Terrace leaves no corner clear.
    # A legend below the histogram would be wider than it and squeeze the Q-Q
    # panel, so it takes the least-covered corner instead.
    from hangtu.plot import _distribution_fit

    monkeypatch.setattr(_distribution_fit, "HEADROOM", 1.1)
    p = ht.Project.from_ags(ht.examples.path("site.ags"), db=tmp_path / "site.sqlite")
    p.set_geology_map(ht.examples.path("strata.csv"))
    spt = ht.analysis.spt(p.spt())
    _, axs, _ = ht.plot.distribution_fit(
        spt, value="spt_n60", by="geology_unit", group="Terrace"
    )
    legend = axs[0].get_legend()
    assert legend._loc in (1, 2, 3, 4)  # a corner, not "upper center" below
