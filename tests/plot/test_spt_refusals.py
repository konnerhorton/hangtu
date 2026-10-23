"""P02 refusals at the cap, N60 and their counts (P02 §6, §7, §11, §12)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht


def spt_frame(**columns):
    """One hole, one unit, depths in ft at 120 ft ground level."""
    n = len(next(iter(columns.values()))) if columns else 4
    data = {
        "loca_id": ["A"] * n,
        "depth": [5.0 * (i + 1) for i in range(n)],
        "ground_level": [120.0] * n,
        "geology_unit": ["Sand"] * n,
        **columns,
    }
    return ht.set_units(pd.DataFrame(data), {"depth": "ft", "ground_level": "ft"})


def refusal_points(ax):
    """(x, y) of every point drawn with the refusal triangle."""
    found = [
        c.get_offsets().data
        for c in ax.collections
        if len(c.get_offsets()) and c.get_label().endswith(" >")
    ]
    return np.concatenate(found).tolist() if found else []


def footnote(ax):
    (text,) = [t for t in ax.texts if t.get_text().startswith(tuple("0123456789"))]
    return text.get_text().splitlines()


def legend(ax):
    return [t.get_text() for t in ax.get_legend().get_texts()]


# --- refusals at the cap ----------------------------------------------------------


def test_refusals_at_the_cap_golden_values(points):
    df = spt_frame(
        spt_n=[20.0, 38.0, np.nan, 150.0, 150.0],
        spt_refusal=[False, True, True, True, False],
    )
    _, ax = ht.plot.spt_profile(df)
    # N = 38, blank and 150 refusals at 100; a non-refusal N = 150 at 150.
    assert refusal_points(ax) == [[100.0, 110.0], [100.0, 105.0], [100.0, 100.0]]
    assert sorted(points(ax)[:, 0]) == [20.0, 100.0, 100.0, 100.0, 150.0]
    assert ax.ags_notes == {"refusal": 3}
    assert "refusal (3)" in legend(ax)
    assert footnote(ax) == ["3 refusals, shown at N = 100"]


def test_refusal_markers_are_in_the_unit_color():
    df = spt_frame(spt_n=[20.0, 38.0], spt_refusal=[False, True])
    _, ax = ht.plot.spt_profile(df, palette={"Sand": "#aa3377"})
    (triangles,) = [c for c in ax.collections if c.get_label().endswith(" >")]
    assert tuple(triangles.get_facecolor()[0][:3]) == pytest.approx(
        (0xAA / 255, 0x33 / 255, 0x77 / 255)
    )


@pytest.mark.parametrize("how", ["argument", "setting"])
def test_cap_from_the_argument_and_the_setting(how):
    df = spt_frame(spt_n=[20.0, 38.0], spt_refusal=[False, True])
    if how == "setting":
        ht.settings.spt_cap = 50
        _, ax = ht.plot.spt_profile(df)
    else:
        _, ax = ht.plot.spt_profile(df, cap=50)
    assert refusal_points(ax) == [[50.0, 110.0]]
    assert footnote(ax) == ["1 refusal, shown at N = 50"]
    # 1.05 * 50 = 52.5 -> 60.
    assert ax.get_xlim() == (0.0, 60.0)


def test_the_x_axis_clears_the_cap_when_there_are_refusals():
    df = spt_frame(spt_n=[20.0, 38.0], spt_refusal=[False, True])
    _, ax = ht.plot.spt_profile(df)
    # 1.05 * 100 = 105 -> 120, so the triangles aren't on the frame.
    assert ax.get_xlim() == (0.0, 120.0)


def test_without_refusals_the_limits_are_p01s():
    df = spt_frame(spt_n=[20.0, 38.0], spt_refusal=[False, False])
    _, ax = ht.plot.spt_profile(df)
    assert ax.get_xlim() == (0.0, 40.0)


def test_xlim_below_the_cap_puts_refusals_at_the_edge():
    df = spt_frame(spt_n=[20.0, 38.0], spt_refusal=[False, True])
    _, ax = ht.plot.spt_profile(df, xlim=(0, 60))
    assert ax.get_xlim() == (0.0, 60.0)
    assert ax.ags_notes == {"refusal": 1, "beyond_limit": 1}


def test_refusal_exclude_leaves_them_out_and_counts_them(points):
    df = spt_frame(spt_n=[20.0, 38.0, np.nan], spt_refusal=[False, True, True])
    _, ax = ht.plot.spt_profile(df, refusal="exclude")
    assert points(ax)[:, 0].tolist() == [20.0]
    assert refusal_points(ax) == []
    assert ax.ags_notes == {"refusal_excluded": 2}
    assert footnote(ax) == ["2 refusals not shown"]
    assert ax.get_xlim() == (0.0, 50.0)  # one point: the typical range


# --- N60 ----------------------------------------------------------------------------


def test_n60_golden_values(points):
    df = spt_frame(spt_n=[30.0, 90.0], energy_ratio=[80, 80], spt_refusal=[False] * 2)
    _, ax = ht.plot.spt_profile(df, n="spt_n60")
    # 30 * 80 / 60 = 40.0; 90 * 80 / 60 = 120.0, drawn at its value.
    assert points(ax)[:, 0].tolist() == [40.0, 120.0]


def test_n60_refusal_footnote_names_n60():
    df = spt_frame(spt_n=[30.0, 38.0], spt_refusal=[False, True])
    with pytest.warns(UserWarning, match="Energy ratio 80 %"):
        _, ax = ht.plot.spt_profile(df, n="spt_n60", hammer_efficiency=80)
    assert refusal_points(ax) == [[100.0, 110.0]]
    assert footnote(ax) == ["1 refusal, shown at N60 = 100"]


def test_n60_tests_without_an_energy_ratio_are_counted(points):
    df = spt_frame(
        spt_n=[30.0, 12.0, np.nan, 38.0],
        energy_ratio=[80, np.nan, np.nan, np.nan],
        spt_refusal=[False, False, False, True],
    )
    _, ax = ht.plot.spt_profile(df, n="spt_n60")
    assert points(ax)[:, 0].tolist() == [40.0, 100.0]
    assert ax.ags_notes == {"no_energy_ratio": 1, "nan": 1, "refusal": 1}
    assert footnote(ax) == [
        "1 blank value not shown",
        "1 refusal, shown at N60 = 100",
        "1 test without an energy ratio not shown",
    ]


def test_n60_with_no_energy_ratio_anywhere_is_an_error():
    df = spt_frame(spt_n=[30.0, 12.0], spt_refusal=[False, False])
    with pytest.raises(
        ht.HangtuError,
        match=r"No test has N60.*hammer_efficiency = 80.*'energy_ratio'.*spt_n",
    ):
        ht.plot.spt_profile(df, n="spt_n60")


def test_n60_with_no_n_at_all_shows_no_data():
    df = spt_frame(spt_n=[np.nan, np.nan], spt_refusal=[False, False])
    _, ax = ht.plot.spt_profile(df, n="spt_n60")
    assert "No data" in [t.get_text() for t in ax.texts]


# --- stats box ----------------------------------------------------------------------


def test_stats_include_refusals_at_the_cap_and_say_so():
    df = spt_frame(spt_n=[20.0, 38.0], spt_refusal=[False, True])
    _, ax = ht.plot.spt_profile(df, stats_box=["count", "mean"])
    assert footnote(ax) == [
        "1 refusal, shown at N = 100",
        "Statistics include refusals at N = 100",
    ]
    box = [t.get_text() for t in ax.texts if "mean" in t.get_text()]
    assert box and "60" in box[0]  # (20 + 100) / 2


def test_no_statistics_line_without_a_stats_box_or_refusals():
    df = spt_frame(spt_n=[20.0, 38.0], spt_refusal=[False, True])
    _, ax = ht.plot.spt_profile(df)
    assert "Statistics include" not in "\n".join(footnote(ax))
    df = spt_frame(spt_n=[20.0, 38.0], spt_refusal=[False, False])
    _, ax = ht.plot.spt_profile(df, stats_box=True)
    assert not [t for t in ax.texts if "Statistics include" in t.get_text()]
