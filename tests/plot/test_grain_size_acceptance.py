"""P05 against the acceptance criteria of docs/plots/P05-grain-size.md §12.

Criteria tested in detail elsewhere are checked end to end here, and point to
the file with the cases (test_grain_size.py, test_grain_size_band.py,
test_grain_size_d_values.py, test_grain_size_envelopes.py).
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import hangtu as ht

AGS = Path(__file__).parents[1] / "data" / "ags"
CURVE_A = (
    [0.075, 0.15, 0.3, 0.6, 1.18, 2.36, 4.75],
    [4, 12, 30, 55, 75, 90, 100],
)
FILTER = pd.DataFrame(
    {
        "label": ["Filter"] * 3,
        "particle_size": [0.075, 0.425, 4.75],
        "low": [0, 20, 80],
        "high": [5, 45, 100],
    }
)
USER_SYSTEM = {
    "name": "project_bands",
    "fractions": [
        {"name": "fines", "lower": 0, "upper": 0.075},
        {"name": "sand", "lower": 0.075, "upper": 2.0},
        {"name": "coarse", "lower": 2.0, "upper": None},
    ],
}


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # HangtuHint is a warning too
        return call(*args, **kwargs)


def _curves(*specs, unit="mm", geology_unit=None):
    rows = [
        {"specimen_id": name, "particle_size": size, "percent_passing": percent}
        for name, sizes, passing in specs
        for size, percent in zip(sizes, passing, strict=True)
    ]
    df = pd.DataFrame(rows)
    df["geology_unit"] = geology_unit or "Alluvium"
    return ht.set_units(df, {"particle_size": unit})


def _drawn(ax):
    return {
        line.get_label(): line.get_xydata()
        for line in ax.lines
        if line.get_gid() == "curve"
    }


def _dividers(ax):
    return sorted(
        line.get_xdata()[0]
        for line in ax.lines
        if line.get_gid() in ("fraction_divider", "part_divider")
    )


def _sieves(ax):
    texts = ax.grain_size_sieves.texts
    return {t.get_text(): t.get_position()[0] for t in texts}


@pytest.fixture(scope="module")
def example(tmp_path_factory):
    """The example project's grading curves (14 curves, US units)."""
    folder = tmp_path_factory.mktemp("example")
    p = ht.Project.from_ags(ht.examples.path("site.ags"), db=folder / "site.sqlite")
    p.set_geology_map(ht.examples.path("strata.csv"))
    return p.grain_size()


# Band (test_grain_size_band.py: test_*_boundaries).
def test_band_boundaries():
    _, ax = _quiet(ht.plot.grain_size, pd.DataFrame())
    assert _dividers(ax) == [0.075, 0.425, 2.0, 4.75, 19, 75]
    _, ax = _quiet(ht.plot.grain_size, pd.DataFrame(), fractions="iso14688")
    assert _dividers(ax) == [0.002, 0.0063, 0.02, 0.063, 0.2, 0.63, 2.0, 6.3, 20, 63]


# Sieve labels (test_grain_size_band.py: test_*_sieve_labels).
def test_sieve_labels():
    _, ax = _quiet(ht.plot.grain_size, pd.DataFrame(), display_units="US")
    assert ax.grain_size_sieves is None  # off by default
    _, ax = _quiet(
        ht.plot.grain_size, pd.DataFrame(), display_units="US", sieves="auto"
    )
    assert _sieves(ax)["#200"] == 0.075
    assert _sieves(ax)["#4"] == 4.75
    _, ax = _quiet(
        ht.plot.grain_size, pd.DataFrame(), display_units="SI", sieves="auto"
    )
    assert _sieves(ax)["0.063"] == 0.063


# Curves (test_grain_size.py: test_shuffled_*, test_curve_in_inches_*).
def test_curves_in_size_order_and_units():
    expected = np.column_stack(CURVE_A)
    shuffled = _curves(("A", *CURVE_A)).sample(frac=1, random_state=7)
    _, ax = _quiet(ht.plot.grain_size, shuffled)
    np.testing.assert_allclose(_drawn(ax)["A"], expected)
    inches = [size / 25.4 for size in CURVE_A[0]]
    _, ax = _quiet(ht.plot.grain_size, _curves(("A", inches, CURVE_A[1]), unit="in"))
    np.testing.assert_allclose(_drawn(ax)["A"], expected)


# D-values (test_grain_size_d_values.py).
def test_d_values_of_curve_a():
    _, ax = _quiet(ht.plot.grain_size, _curves(("A", *CURVE_A)), d_values=True)
    sizes = [line.get_xdata()[0] for line in ax.lines if line.get_gid() == "d_value"]
    np.testing.assert_allclose(sizes, [0.1261, 0.300, 0.7105], atol=5e-5)


# Envelopes (test_grain_size_envelopes.py).
def test_envelope_edges():
    table = ht.set_units(FILTER, {"particle_size": "mm"})
    _, ax = _quiet(ht.plot.grain_size, pd.DataFrame(), envelopes=table)
    (band,) = [c for c in ax.collections if c.get_gid() == "envelope"]
    vertices = {tuple(np.round(v, 6)) for v in band.get_paths()[0].vertices}
    for _, row in FILTER.iterrows():
        assert (row["particle_size"], row["low"]) in vertices
        assert (row["particle_size"], row["high"]) in vertices


# Direction (test_grain_size_band.py: test_reverse_*).
def test_reverse():
    _, ax = _quiet(ht.plot.grain_size, _curves(("A", *CURVE_A)), reverse=True)
    to_screen = ax.transData.transform
    assert to_screen((100, 0))[0] < to_screen((0.1, 0))[0]


# Counts (test_grain_size.py: test_short_curve_*; d_values: test_unreached_*).
def test_counts():
    df = _curves(
        ("A", *CURVE_A),
        ("S", [0.075], [10]),
        ("B", [0.075, 0.15, 4.75], [20, np.nan, 100]),
    )
    _, ax = _quiet(ht.plot.grain_size, df, d_values=True)
    assert ax.ags_notes == {"nan": 1, "short_curve": 1, "d_value_unreached": 1}
    footnote = ax.texts[-1].get_text()
    assert "1 curve with fewer than two points not shown" in footnote
    assert "1 D-value not reached (D10 by 1 curve)" in footnote


# Non-monotonic curves are drawn as given, with one warning.
def test_non_monotonic():
    df = _curves(("A", *CURVE_A), ("N", [0.075, 0.15, 0.3], [20, 10, 50]))
    with pytest.warns(UserWarning, match="toward finer sizes in N") as record:
        _, ax = ht.plot.grain_size(df)
    assert len(record) == 1
    np.testing.assert_allclose(_drawn(ax)["N"][:, 1], [20, 10, 50])


# Automated: each system renders, and a user's; fractions=None hides the band.
@pytest.mark.parametrize("fractions", ["astm_uscs", "aashto", "iso14688", USER_SYSTEM])
def test_renders_with_each_system(fractions):
    fig, ax = _quiet(ht.plot.grain_size, _curves(("A", *CURVE_A)), fractions=fractions)
    assert ax.grain_size_header.texts
    fig.canvas.draw()


def test_fractions_none_hides_the_band():
    _, ax = _quiet(ht.plot.grain_size, _curves(("A", *CURVE_A)), fractions=None)
    assert ax.grain_size_header is None
    assert _dividers(ax) == []


def test_example_project_renders(example):
    fig, ax = _quiet(ht.plot.grain_size, example)
    curves = _drawn(ax)
    assert len(curves) == 14
    texts = [t.get_text() for t in ax.get_legend().get_texts()]
    assert texts == [  # the map's order
        "Fill (n = 2 curves)",
        "Alluvium (n = 6 curves)",
        "Terrace (n = 6 curves)",
    ]
    # The fill and alluvium curves continue below the #200 sieve (hydrometer).
    assert sum(xy[:, 0].min() < 0.075 for xy in curves.values()) == 8
    np.testing.assert_allclose(ax.get_xlim(), (0.001, 100))
    assert ax.ags_notes == {}
    assert not [line for line in ax.lines if line.get_gid() == "d_value"]
    fig.canvas.draw()


def test_example_project_d_values(example):
    _, ax = _quiet(ht.plot.grain_size, example, d_values=True)
    # The alluvium's finest hydrometer points pass more than 10 %.
    assert ax.ags_notes == {"d_value_unreached": 6}


def test_sheet_panel_and_global_state(example, assert_no_global_state):
    sheet = ht.Sheet("letter", layout=(2, 1))
    _quiet(assert_no_global_state, ht.plot.grain_size, example, ax=sheet[0])
    header = sheet[0].grain_size_header
    assert header in sheet.figure.axes
    sheet.figure.canvas.draw()
    assert header.get_window_extent().y1 <= sheet.figure.bbox.y1


@pytest.mark.parametrize("sieves", [None, "auto"])
def test_us_and_si_differ_only_in_sieve_labels(example, sieves):
    _, us = _quiet(ht.plot.grain_size, example, display_units="US", sieves=sieves)
    _, si = _quiet(ht.plot.grain_size, example, display_units="SI", sieves=sieves)
    for label, xy in _drawn(us).items():
        np.testing.assert_allclose(xy, _drawn(si)[label])
    assert _dividers(us) == _dividers(si)
    assert us.ags_notes == si.ags_notes
    assert us.get_xlim() == si.get_xlim()
    if sieves is None:  # the same figure
        assert us.grain_size_sieves is None and si.grain_size_sieves is None
    else:
        assert set(_sieves(us)) != set(_sieves(si))
    others = [
        sorted(t.get_text() for t in ax.texts if t.get_gid() != "sieve_label")
        for ax in (us, si)
    ]
    assert others[0] == others[1]


# datasets.md §13 #14: p.grain_size() feeds the plot with no error, warning or hint.
@pytest.mark.parametrize("name", ["site_si", "site_us"])
def test_dataset_feeds_the_plot(tmp_path, name):
    p = ht.Project.from_ags(AGS / f"{name}.ags", db=tmp_path / f"{name}.sqlite")
    p.set_geology_map(AGS / "strata.csv")
    curves = _quiet(p.grain_size)
    _, ax = _quiet(ht.plot.grain_size, curves)
    names = curves.groupby(["loca_id", "specimen_id"]).ngroups
    assert len(_drawn(ax)) + ax.ags_notes.get("short_curve", 0) == names
