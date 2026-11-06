"""SourceComparison's figures by depth: docs/work/m18d-sources-compared.md, AC 10.

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
from hangtu.plot._overlays import format_number

from .test_compare_sources import (
    CONVERTED,
    HATANAKA,
    KULHAWY,
    PHI,
    PSF,
    STROUD,
    SU,
    _g2,
    _spt_phi,
    _stroud,
    _su,
    _triaxial_frame,
)

FIT = "Mohr-Coulomb fit (CD)"
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
