"""SourceComparison's figures: docs/work/m18d-sources-compared.md, AC 10.

The data are G2's and G3's from test_compare_sources.py. A comparison's
``.profile()`` draws one unit (step 6, decided in the build), so its stats box
can equal the per-unit table.
"""

import warnings

import numpy as np
import pandas as pd
import pytest
from matplotlib.colors import to_rgba

import hangtu as ht
from hangtu.errors import HangtuError
from hangtu.plot._geology_units import UNIT_RULE_COLOR
from hangtu.plot._overlays import format_number
from hangtu.plot._values import group_text

from .test_compare_sources import (
    CONVERTED,
    HATANAKA,
    KULHAWY,
    PHI,
    PSF,
    STROUD,
    SU,
    _compare,
    _g2,
    _spt_phi,
    _stroud,
    _su,
    _triaxial_frame,
)

FIT = "Mohr-Coulomb fit (CD)"
DOT = "\N{MIDDLE DOT}"
#: P01's default stats box, as .to_frame() names each statistic.
BOX = ("count", "mean", "standard_deviation", "median", "minimum", "maximum")


def _profile(result, **kwargs):
    """Draw, failing on any warning; P01's ground-level hint is turned off."""
    with ht.settings.override(hints=False), warnings.catch_warnings():
        warnings.simplefilter("error")
        return result.profile(**kwargs)


def _box_lines(ax):
    (box,) = [text for text in ax.texts if text.get_bbox_patch() is not None]
    return box.get_text().splitlines()


def _bars(ax):
    """Each interval bar drawn, as (x, top, base, color)."""
    found = []
    for line in ax.lines:
        xs, ys = line.get_xdata(), line.get_ydata()
        for i in range(0, len(xs), 3):
            found.append((xs[i], ys[i], ys[i + 1], to_rgba(line.get_color())))
    return found


def _marker_color(ax, x, y):
    """The face color of the point drawn at (x, y)."""
    for collection in ax.collections:
        offsets = np.asarray(collection.get_offsets())
        hit = np.isclose(offsets[:, 0], x) & np.isclose(offsets[:, 1], y)
        if hit.any():
            colors = collection.get_facecolors()
            return tuple(colors[0 if len(colors) == 1 else int(np.argmax(hit))])
    raise AssertionError(f"no point at ({x}, {y})")


def _depthless_fit():
    """G2's triaxial stages in Terrace with no depth: φ′ 36°."""
    df = _triaxial_frame(
        [(50, 192.592), (100, 385.184), (200, 770.368)], geology_unit="Terrace"
    )
    with pytest.warns(UserWarning, match=r"intercept is negative"):
        return ht.analysis.mohr_coulomb_fit(df, group_by="geology_unit")


# --- .values() ------------------------------------------------------------------


def test_values_keep_every_row_and_one_per_fit():
    values = _g2().values()
    # 19 SPT rows (the band and the blank among them), 2 fit groups, 1 conversion.
    assert len(values) == 22
    counts = values.groupby(["geology_unit", "parameter_source"]).size().to_dict()
    assert counts == {
        ("Terrace", HATANAKA): 8,
        ("Terrace", KULHAWY): 8,
        ("Terrace", FIT): 1,
        ("Terrace", CONVERTED): 1,
        ("Alluvium", HATANAKA): 3,
        ("Alluvium", FIT): 1,
    }
    assert list(values.columns[:3]) == ["geology_unit", "parameter_source", PHI]
    band = values[values[f"{PHI}_lower"].notna()]
    assert band[[f"{PHI}_lower", f"{PHI}_upper"]].values.tolist() == [[33.0, 38.0]]
    assert values["correlation_qualifier"].tolist().count(">") == 1


def test_values_place_a_fit_at_the_middle_of_its_depths():
    values = _g2().values()
    fit = values[
        (values["geology_unit"] == "Terrace") & (values["parameter_source"] == FIT)
    ].iloc[0]
    assert fit[PHI] == pytest.approx(36.0, abs=1e-3)
    assert (fit["depth"], fit["depth_top"], fit["depth_base"]) == (6.5, 4.0, 9.0)
    assert pd.isna(fit["loca_id"])
    converted = values[values["parameter_source"] == CONVERTED].iloc[0]
    assert converted[PHI] == pytest.approx(30.5777, abs=1e-4)
    assert (converted["depth_top"], converted["depth_base"]) == (5.0, 5.0)
    # The fit with one stage in Alluvium has no value, but its row is kept.
    alluvium = values[
        (values["geology_unit"] == "Alluvium") & (values["parameter_source"] == FIT)
    ]
    assert alluvium[PHI].isna().all()
    assert values.attrs["units"] == {
        PHI: "deg",
        f"{PHI}_lower": "deg",
        f"{PHI}_upper": "deg",
        "depth": "m",
        "depth_top": "m",
        "depth_base": "m",
    }


def test_values_are_in_the_comparisons_units():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = ht.stats.compare_sources(_su(), _stroud(), value=SU)
    values = result.values()
    assert values.attrs["units"] == {SU: "kPa"}
    assert values["parameter_source"].iloc[-1] == STROUD
    converted = values[SU].iloc[-3:].to_numpy()
    np.testing.assert_allclose(converted, np.array([1200, 1500, 1350]) * PSF)
    assert len(values) == 10
    assert "depth" not in values


def test_a_fit_without_depths_has_a_blank_depth():
    spt = _spt_phi()
    spt = spt[spt["geology_unit"] == "Terrace"]
    with pytest.warns(UserWarning):
        result = ht.stats.compare_sources(spt, _depthless_fit(), value=PHI)
    fit = result.values().iloc[-1]
    assert fit["parameter_source"] == FIT
    assert fit[PHI] == pytest.approx(36.0, abs=1e-3)
    assert pd.isna(fit["depth"]) and pd.isna(fit["depth_top"])


# --- .profile() -----------------------------------------------------------------


def test_profile_stats_box_equals_the_table():
    result = _g2()
    _, ax = _profile(result, geology_unit="Terrace")
    lines = _box_lines(ax)
    frame = result.to_frame()
    terrace = frame[frame["geology_unit"] == "Terrace"]
    assert len(terrace) == 4
    for _, row in terrace.iterrows():
        (line,) = [s for s in lines if s.startswith(row["parameter_source"] + " ")]
        drawn = line.removeprefix(row["parameter_source"]).split()
        expected = [
            str(int(row["count"])),
            *(
                "—" if np.isnan(row[name]) else format_number(row[name])
                for name in BOX[1:]
            ),
        ]
        assert drawn == expected, row["parameter_source"]
    # The sources are never pooled into an "All" line.
    assert lines[-2].split()[:3] == ["All", "mixes", "sources"]


def test_profile_draws_each_fit_as_a_bar_in_its_color():
    _, ax = _profile(_g2(), geology_unit="Terrace", display_units="SI", vs="depth")
    bars = _bars(ax)
    fits = sorted((x, top, base) for x, top, base, _ in bars if x != 33.0)
    assert np.ravel(fits) == pytest.approx([30.577673, 5, 5, 36, 4, 9], abs=1e-3)
    for x, top, base, color in bars:
        if x == 33.0:
            continue  # the band, drawn from its lower bound
        assert _marker_color(ax, x, (top + base) / 2) == pytest.approx(color)
    # The band, the blank and the bound in the footnote, as the table counts them.
    assert ax.ags_notes == {"value_range": 1, "nan": 1, "greater_than": 1}


def test_profile_counts_a_fit_without_depth_in_the_footnote():
    spt = _spt_phi()
    spt = spt[spt["geology_unit"] == "Terrace"]
    with pytest.warns(UserWarning):
        result = ht.stats.compare_sources(spt, _depthless_fit(), value=PHI)
    _, ax = _profile(result)  # one unit: no need to name it
    assert ax.ags_notes["nan"] == 2  # the blank SPT row and the fit
    assert all(x == 33.0 for x, *_ in _bars(ax))


def test_profile_needs_the_unit_when_there_are_several():
    result = _g2()
    with pytest.raises(HangtuError, match=r"geology_unit='Alluvium'.*Terrace"):
        result.profile()
    with pytest.raises(HangtuError, match=r"no unit 'Sand'"):
        result.profile(geology_unit="Sand")


def test_profile_arguments_override_its_defaults():
    _, ax = _profile(_g2(), geology_unit="Terrace", figsize=(5, 6), legend="right")
    assert tuple(ax.figure.get_size_inches()) == (5, 6)


# --- .geology_unit_comparison() -------------------------------------------------


def _unit_comparison(result, **kwargs):
    """Draw P07, failing on any warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return result.geology_unit_comparison(**kwargs)


def _ticks(ax):
    return [label.get_text() for label in ax.get_yticklabels()]


def _counts(ax):
    return [text.get_text() for text in ax.texts if text.get_text().startswith("n =")]


def _summary_bars(ax):
    """Each sub-row's bar as {row: (low, high)}: a horizontal two-point line."""
    found = {}
    for line in ax.lines:
        x, y = (np.asarray(a, dtype=float) for a in line.get_data())
        if (
            len(x) == 2
            and y[0] == y[1]
            and line.get_marker() in ("None", "")
            and line.get_color() not in (UNIT_RULE_COLOR, "0.25")
        ):
            found[round(y[0])] = tuple(x)
    return found


def _centrals(ax):
    """Each sub-row's center marker as {row: x}."""
    return {
        round(line.get_ydata()[0]): float(line.get_xdata()[0])
        for line in ax.lines
        if line.get_marker() == "o"
    }


def _table_rows(result):
    """The .to_frame() rows that have a value, in the figure's row order."""
    frame = result.to_frame()
    return frame[frame["count"] > 0].reset_index(drop=True)


def _drawn_matches_the_table(result, ax):
    table = _table_rows(result)
    assert _ticks(ax) == [
        f"{unit} {DOT} {group_text(source)}"
        for unit, source in zip(
            table["geology_unit"], table["parameter_source"], strict=True
        )
    ]
    # P07 draws assumed values but leaves them out of the summary.
    drawn = table["count"] + (0 if result.include_assumed else table["count_assumed"])
    assert [int(c.split()[2]) for c in _counts(ax)] == drawn.tolist()
    bars, middles = _summary_bars(ax), _centrals(ax)
    for row, record in table.iterrows():
        if np.isnan(record["percentile_25"]):
            assert row not in bars and row not in middles
            continue
        assert bars[row] == pytest.approx(
            (record["percentile_25"], record["percentile_75"])
        )
        assert middles[row] == pytest.approx(record["median"])


def test_unit_comparison_one_sub_row_per_source_with_the_tables_percentiles():
    result = _g2(percentiles=(25, 75))
    _, ax = _unit_comparison(result)
    _drawn_matches_the_table(result, ax)
    # Terrace's A and B have bars; the fits, one value each, don't.
    assert len(_summary_bars(ax)) == 2
    assert not any("mixes sources" in c for c in _counts(ax))
    # The legend wraps long names.
    legend = [" ".join(t.get_text().split()) for t in ax.get_legend().get_texts()]
    for source in (HATANAKA, KULHAWY, FIT, CONVERTED):
        assert group_text(source) in legend


def test_unit_comparison_in_the_comparisons_units():
    for system in ("SI", "US"):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result = ht.stats.compare_sources(
                _su(), _stroud(), value=SU, percentiles=(25, 75), display_units=system
            )
        _, ax = _unit_comparison(result)
        _drawn_matches_the_table(result, ax)
        # UU has a bar; the vane and Stroud, 3 values each, don't.
        assert list(_summary_bars(ax)) == [0]
        assert ax.get_xlabel().endswith("(psf)" if system == "US" else "(kPa)")


def test_unit_comparison_takes_a_categorical_geology_unit():
    # A Project's datasets give geology_unit the geology map's categories,
    # some with no rows here: no pandas warning, one sub-row per source.
    su = _su()
    su["geology_unit"] = pd.Categorical(
        su["geology_unit"], categories=["Fill", "Alluvium", "Terrace"]
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = ht.stats.compare_sources(su, value=SU)
    _, ax = _unit_comparison(result)
    assert _ticks(ax) == [
        f"Alluvium {DOT} lab, UU",
        f"Alluvium {DOT} field, in situ vane",
    ]


def test_unit_comparison_needs_a_comparison_by_geology_unit():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = ht.stats.compare_sources(_su(), _stroud(), value=SU, by=None)
    with pytest.raises(HangtuError, match=r'by None.*by="geology_unit"'):
        result.geology_unit_comparison()


def test_unit_comparison_warns_when_the_table_includes_assumed_values():
    df = pd.DataFrame(
        {
            "geology_unit": "Terrace",
            "test_type": "particle density",
            "particle_density": [2.65, 2.68, 2.70, 2.66, 2.71],
            "particle_density_assumed": [True, False, False, False, False],
        }
    )
    df.attrs["units"] = {"particle_density": "Mg/m3"}
    value = "particle_density"
    result = _compare(df, value=value, include_assumed=True)
    with pytest.warns(UserWarning, match=r"include_assumed=True"):
        result.geology_unit_comparison()
    # Left out, as P07 leaves them out, the figure and the table agree.
    with pytest.warns(UserWarning, match=r"assumed"):
        result = ht.stats.compare_sources(df, value=value, percentiles=(25, 75))
    _, ax = _unit_comparison(result, display_units="SI")  # the table's Mg/m3
    _drawn_matches_the_table(result, ax)


def test_unit_comparison_arguments_override_its_defaults():
    _, ax = _unit_comparison(
        _g2(), figsize=(6, 5), order=["Terrace", "Alluvium"], color_by=None
    )
    assert tuple(ax.figure.get_size_inches()) == (6, 5)
    assert _ticks(ax)[0].startswith("Terrace")
