"""P06 against the acceptance criteria of docs/plots/P06-water-content-profile.md §12.

The geometry, one-limit, NP and limits criteria are tested case by case in
test_water_content_profile.py. Here: the example project (``site.ags``, US
units) and atterberg.csv end to end, and the automated criteria.

Counts by hand from the example data: 20 index samples, 14 with w, PL and
LL (2 Fill, 12 Alluvium) and 6 Terrace samples with grading only, which are
blank here. No NP specimen. The highest LL is 59 (B-2 at 18 ft).
"""

import warnings

import matplotlib as mpl
import numpy as np
import pandas as pd
import pytest

import hangtu as ht

LENGTHS = dict.fromkeys(
    ["ground_level", "depth", "elevation", "depth_top", "depth_base"], "ft"
)


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # HangtuHint is a warning too
        return call(*args, **kwargs)


@pytest.fixture(name="project", scope="module")
def _project(tmp_path_factory):
    db = tmp_path_factory.mktemp("p06") / "site.sqlite"
    p = ht.Project.from_ags(ht.examples.path("site.ags"), db=db)
    p.set_geology_map(ht.examples.path("strata.csv"))
    return p


def index_properties(project, system="US"):
    # The dataset warns about unreached D10s in its gradation; that's not P06's.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return project.index_properties(display_units=system)


def atterberg_csv():
    return ht.read_csv(ht.examples.path("atterberg.csv"), units=LENGTHS)


def bars(ax):
    return [line for line in ax.lines if line.get_gid() == "limits_bar"]


def bar_count(ax):
    return sum(len(line.get_xydata()) // 3 for line in bars(ax))


def strata():
    return ht.set_units(
        pd.DataFrame(
            {
                "geology_unit": ["Fill", "Alluvium", "Terrace"],
                "elevation_top": [36.5, 32.0, 14.5],
                "elevation_base": [32.0, 14.5, -15.0],
            }
        ),
        {"elevation_top": "ft", "elevation_base": "ft"},
    )


# --- datasets --------------------------------------------------------------------


@pytest.mark.parametrize("system", ["US", "SI"])
def test_index_properties_draw_with_no_warning(project, system):
    df = index_properties(project, system)
    _, ax = _quiet(ht.plot.water_content_profile, df, display_units=system)
    assert bar_count(ax) == 14
    assert ax.ags_notes == {"nan": 6}
    assert ax.get_xlim() == (0.0, 60.0)
    legend = [t.get_text() for t in ax.get_legend().get_texts()]
    assert legend == ["Fill", "Alluvium", "PL to LL"]


def test_atterberg_draws_with_no_warning(project):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = project.atterberg()
    _, ax = _quiet(ht.plot.water_content_profile, df)
    assert bar_count(ax) == 14
    assert ax.ags_notes == {}


def test_atterberg_csv_draws_with_no_warning():
    _, ax = _quiet(ht.plot.water_content_profile, atterberg_csv())
    assert bar_count(ax) == 14
    assert ax.ags_notes == {}


# --- automated -------------------------------------------------------------------


@pytest.mark.parametrize("vs", ["depth", "elevation"])
def test_renders_against_depth_and_elevation(vs):
    _, ax = _quiet(ht.plot.water_content_profile, atterberg_csv(), vs=vs)
    assert ax.get_ylabel().startswith(vs.capitalize())
    assert ax.yaxis_inverted() == (vs == "depth")
    # B-1 at 13 ft: elevation 23.5, PL 20, LL 51, w 41.
    y = 13.0 if vs == "depth" else 23.5
    segments = np.concatenate([line.get_xydata() for line in bars(ax)])
    assert [20.0, y] in segments.tolist()
    assert [51.0, y] in segments.tolist()


def test_draws_into_a_sheet_panel_without_a_new_figure():
    sheet = ht.Sheet("letter", layout=(1, 2))
    figures = mpl.pyplot.get_fignums()
    fig, _ = _quiet(ht.plot.water_content_profile, atterberg_csv(), ax=sheet[0])
    assert fig is sheet.figure
    assert mpl.pyplot.get_fignums() == figures


def test_no_change_to_global_state(assert_no_global_state):
    df = atterberg_csv().assign(non_plastic=[True] + [False] * 13)
    with pytest.warns(UserWarning, match="marked non-plastic but have a plastic limit"):
        assert_no_global_state(ht.plot.water_content_profile, df, strata=strata())


def test_us_and_si_differ_only_in_the_vertical_axis(assert_us_si_equivalent):
    assert_us_si_equivalent(
        ht.plot.water_content_profile, atterberg_csv(), ("percent", "length")
    )
    _, us = _quiet(ht.plot.water_content_profile, atterberg_csv(), display_units="US")
    _, si = _quiet(ht.plot.water_content_profile, atterberg_csv(), display_units="SI")
    assert us.get_xlabel() == si.get_xlabel()
    assert us.get_xlim() == si.get_xlim()
    for us_bar, si_bar in zip(bars(us), bars(si), strict=True):
        np.testing.assert_allclose(
            us_bar.get_xydata() * [1.0, 0.3048], si_bar.get_xydata(), rtol=1e-9
        )


# --- P01 passes through ----------------------------------------------------------


@pytest.mark.parametrize(
    "overlay",
    [
        {"strata": strata()},
        {"water_level": [(25.0, "GWL")]},
        {"note": "Draft"},
        {"connect": True},
    ],
    ids=lambda overlay: next(iter(overlay)),
)
def test_overlays_pass_through(overlay):
    df = atterberg_csv()
    _, plain = _quiet(ht.plot.water_content_profile, df)
    _, ax = _quiet(ht.plot.water_content_profile, df, **overlay)
    _, p01 = _quiet(
        ht.plot.profile, df, "water_content", preset="water_content", **overlay
    )
    _, p01_plain = _quiet(ht.plot.profile, df, "water_content", preset="water_content")

    def artists(axes):
        return len(axes.patches) + len(axes.lines) + len(axes.texts)

    assert artists(ax) - artists(plain) == artists(p01) - artists(p01_plain) > 0
    assert ax.ags_notes == plain.ags_notes


def test_stats_box_summarizes_water_content_only():
    df = atterberg_csv()
    _, ax = _quiet(ht.plot.water_content_profile, df, stats_box=True)
    _, p01 = _quiet(
        ht.plot.profile, df, "water_content", preset="water_content", stats_box=True
    )
    texts = {t.get_text() for t in ax.texts}
    (box,) = [t.get_text() for t in p01.texts if "mean" in t.get_text()]
    assert box in texts


def test_limits_false_gives_p01s_figure():
    df = atterberg_csv()
    _, ours = _quiet(ht.plot.water_content_profile, df, limits=False)
    _, p01 = _quiet(ht.plot.profile, df, "water_content", preset="water_content")
    assert bars(ours) == []
    assert ours.get_xlabel() == p01.get_xlabel()
    assert ours.get_xlim() == p01.get_xlim()
    assert ours.get_ylim() == p01.get_ylim()
    assert [c.get_offsets().data.tolist() for c in ours.collections] == [
        c.get_offsets().data.tolist() for c in p01.collections
    ]
