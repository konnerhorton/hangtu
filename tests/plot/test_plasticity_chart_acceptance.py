"""P04 against the acceptance criteria of docs/plots/P04-plasticity-chart.md §12.

Criteria tested in detail elsewhere are checked end to end here, and point to
the file with the cases (test_plasticity_chart.py, test_plasticity_regions.py).
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import hangtu as ht

AGS = Path(__file__).parents[1] / "data" / "ags"
GROUP = pd.DataFrame(
    {
        "label": ["Alluvium group"] * 5,
        "liquid_limit": [35.0, 50.0, 62.0, 55.0, 38.0],
        "plasticity_index": [12.0, 18.0, 30.0, 36.0, 22.0],
    }
)


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # HangtuHint is a warning too
        return call(*args, **kwargs)


def _xy(ax, gid):
    (line,) = [line for line in ax.lines if line.get_gid() == gid]
    return line.get_xydata()


def _filled(ax):
    return np.concatenate(
        [c.get_offsets() for c in ax.collections if len(c.get_facecolors())]
    )


@pytest.fixture(scope="module")
def example(tmp_path_factory):
    """The example project's Atterberg data (14 specimens, US units)."""
    folder = tmp_path_factory.mktemp("example")
    p = ht.Project.from_ags(ht.examples.path("site.ags"), db=folder / "site.sqlite")
    p.set_geology_map(ht.examples.path("strata.csv"))
    return p.atterberg()


# Geometry, USCS (test_plasticity_chart.py: test_uscs_*).
def test_uscs_geometry():
    _, ax = _quiet(ht.plot.plasticity_chart, pd.DataFrame())
    a = _xy(ax, "a_line")
    np.testing.assert_allclose(a[0], (25.479, 4), atol=1e-3)
    assert np.interp(50, a[:, 0], a[:, 1]) == pytest.approx(21.9)
    slope = (a[1, 1] - a[0, 1]) / (a[1, 0] - a[0, 0])
    assert a[0, 0] - a[0, 1] / slope == pytest.approx(20)
    u = _xy(ax, "u_line")
    np.testing.assert_allclose(u[:2], [(16, 0), (16, 7.2)])
    assert np.interp(50, u[1:, 0], u[1:, 1]) == pytest.approx(37.8)
    (hatch,) = [p for p in ax.patches if p.get_gid() == "cl_ml"]
    assert {tuple(np.round(v, 2)) for v in hatch.get_xy()} == {
        (16, 4),
        (25.48, 4),
        (29.59, 7),
        (16, 7),
    }
    np.testing.assert_allclose(_xy(ax, "divider"), [(50, 0), (50, 37.8)])


# Geometry, BS 5930 (test_plasticity_chart.py: test_bs5930_*).
def test_bs5930_geometry():
    _, ax = _quiet(ht.plot.plasticity_chart, pd.DataFrame(), system="bs5930")
    dividers = [line.get_xydata() for line in ax.lines if line.get_gid() == "divider"]
    assert sorted((d[0, 0], d[0, 1], d[-1, 1]) for d in dividers) == [
        (35, 0, 35),
        (50, 0, 50),
        (70, 0, 70),
        (90, 0, 90),
    ]
    np.testing.assert_allclose(_xy(ax, "a_line")[0], (20, 0))


# Agreement with the analysis: test_each_point_is_drawn_in_the_zone_of_its_class.


# Aspect, with default and user limits.
@pytest.mark.parametrize("kwargs", [{}, {"xlim": (10, 70), "ylim": (0, 30)}])
def test_aspect(example, kwargs):
    with pytest.warns(UserWarning, match="Rows 7"):
        fig, ax = ht.plot.plasticity_chart(example, **kwargs)
    fig.canvas.draw()
    (x0, y0), (x1, y1) = ax.transData.transform([(0, 0), (10, 10)])
    assert x1 - x0 == pytest.approx(y1 - y0, rel=1e-6)


# Limits.
def test_limits():
    def chart(liquid, index):
        df = pd.DataFrame({"liquid_limit": [liquid], "plasticity_index": [index]})
        return _quiet(ht.plot.plasticity_chart, df, color_by=None)[1]

    ax = chart(115.0, 60.0)
    assert (ax.get_xlim(), ax.get_ylim()) == ((0, 120), (0, 60))
    ax = chart(100.0, 50.0)
    assert ax.get_xlim() == (0, 100)
    ax = chart(90.0, 65.0)
    assert ax.ags_notes == {"beyond_limit": 1}
    (edge,) = [c for c in ax.collections if not len(c.get_facecolors())]
    np.testing.assert_allclose(edge.get_offsets(), [(90, 60)])


# Counts: NP, blank, and beyond xlim=.
def test_counts():
    df = pd.DataFrame(
        {
            "liquid_limit": [None, 25.0, 40.0, 55.0, 85.0],
            "plastic_limit": [None, None, 20.0, 25.0, 35.0],
            "non_plastic": [True, True, False, None, False],
        }
    )
    _, ax = _quiet(ht.plot.plasticity_chart, df, color_by=None, xlim=(0, 80))
    assert ax.ags_notes == {
        "non_plastic_excluded": 2,
        "beyond_limit": 1,
    }
    footnote = ax.texts[-1].get_text().splitlines()
    assert footnote == [
        "1 value beyond axis limit, shown at the edge",
        "2 non-plastic (NP) specimens not shown",
    ]
    df.loc[2, "liquid_limit"] = None
    _, ax = _quiet(ht.plot.plasticity_chart, df, color_by=None)
    assert ax.ags_notes == {"non_plastic_excluded": 2, "nan": 1}


# Regions (test_plasticity_regions.py).
def test_region_from_csv(tmp_path):
    path = tmp_path / "groups.csv"
    GROUP.to_csv(path, index=False)
    _, ax = _quiet(ht.plot.plasticity_chart, pd.DataFrame(), regions=path)
    (patch,) = [p for p in ax.patches if p.get_gid() == "region"]
    np.testing.assert_allclose(patch.get_xy()[0], patch.get_xy()[-1])
    assert len(patch.get_xy()) == 6


# Automated: both systems on the example project; a Sheet panel; rcParams; US = SI.
@pytest.mark.parametrize("system", ["uscs", "bs5930"])
def test_example_project_renders(example, system):
    # The example has one planted PI slip (QC A002), which plasticity() warns
    # about by name; nothing else warns.
    with pytest.warns(UserWarning, match="Rows 7 have a plasticity_index") as record:
        fig, ax = ht.plot.plasticity_chart(example, system=system)
    assert len(record) == 1
    assert len(_filled(ax)) == 14
    texts = [t.get_text() for t in ax.get_legend().get_texts()]
    assert texts == ["Fill (n = 2)", "Alluvium (n = 12)"]  # the map's order
    fig.canvas.draw()


def test_sheet_panel_and_global_state(example, assert_no_global_state):
    sheet = ht.Sheet("letter", layout=(1, 2))
    with pytest.warns(UserWarning, match="Rows 7"):
        assert_no_global_state(ht.plot.plasticity_chart, example, ax=sheet[1])
    assert sheet[1].get_xlabel() == "Liquid limit, LL (%)"


def test_us_and_si_are_the_same(example, assert_us_si_equivalent):
    with pytest.warns(UserWarning, match="Rows 7"):
        assert_us_si_equivalent(
            ht.plot.plasticity_chart, example, ("dimensionless", "dimensionless")
        )


# datasets.md §13 #14: p.atterberg() feeds the chart with no error, warning or hint.
@pytest.mark.parametrize("name", ["site_si", "site_us"])
def test_dataset_feeds_the_chart(tmp_path, name):
    p = ht.Project.from_ags(AGS / f"{name}.ags", db=tmp_path / f"{name}.sqlite")
    p.set_geology_map(AGS / "strata.csv")
    atterberg = _quiet(p.atterberg)
    _, ax = _quiet(ht.plot.plasticity_chart, atterberg)
    assert len(_filled(ax)) + sum(ax.ags_notes.values()) == len(atterberg)
