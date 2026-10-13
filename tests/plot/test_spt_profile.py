"""P02 SPT profile: columns, labels, overlays, units, hints and errors."""

import warnings

import matplotlib as mpl
import numpy as np
import pandas as pd
import pytest

import hangtu as ht


def spt_frame(**columns):
    """Two holes, two units, depths in ft, one ground level. No refusals."""
    data = {
        "loca_id": ["A", "A", "B", "B"],
        "depth": [5.0, 10.0, 15.0, 20.0],
        "ground_level": [120.0, 120.0, 120.0, 120.0],
        "geology_unit": ["Fill", "Fill", "Sand", "Sand"],
        "spt_n": [4.0, 9.0, 22.0, 35.0],
        "spt_refusal": [False, False, False, False],
        **columns,
    }
    return ht.set_units(pd.DataFrame(data), {"depth": "ft", "ground_level": "ft"})


def unit_points(ax, unit):
    (collection,) = [c for c in ax.collections if c.get_label() == unit]
    return collection.get_offsets().data.tolist()


# --- columns and labels ---------------------------------------------------------


def test_default_plots_n_against_elevation(points):
    fig, ax = ht.plot.spt_profile(spt_frame())
    assert isinstance(fig, mpl.figure.Figure)
    assert ax.get_xlabel() == "SPT N"
    assert ax.get_ylabel() == "Elevation (ft)"
    assert sorted(points(ax)[:, 0]) == [4.0, 9.0, 22.0, 35.0]
    assert sorted(points(ax)[:, 1]) == [100.0, 105.0, 110.0, 115.0]
    assert ax.get_xlim()[0] == 0
    assert ax.ags_notes == {}


def test_n60_and_capped_n_are_labeled_by_column(points):
    df = spt_frame(energy_ratio=[80, 80, 80, 80], spt_n=[30.0, 9.0, 120.0, 35.0])
    _, ax = ht.plot.spt_profile(df, n="spt_n60")
    assert ax.get_xlabel() == "SPT N60"
    # 30 * 80 / 60 = 40; 120 * 80 / 60 = 160, not capped.
    assert 40.0 in points(ax)[:, 0]
    assert 160.0 in points(ax)[:, 0]
    _, ax = ht.plot.spt_profile(df, n="spt_n_capped")
    assert ax.get_xlabel() == "SPT N (capped)"
    assert sorted(points(ax)[:, 0]) == [9.0, 30.0, 35.0, 100.0]


def test_label_overrides_the_column_label():
    _, ax = ht.plot.spt_profile(spt_frame(), label="Blow count, N")
    assert ax.get_xlabel() == "Blow count, N"


def test_against_depth():
    _, ax = ht.plot.spt_profile(spt_frame(), vs="depth")
    assert ax.get_ylabel() == "Depth (ft)"
    assert ax.yaxis_inverted()


def test_points_are_colored_by_unit():
    _, ax = ht.plot.spt_profile(spt_frame())
    assert unit_points(ax, "Fill") == [[4.0, 115.0], [9.0, 110.0]]
    assert unit_points(ax, "Sand") == [[22.0, 105.0], [35.0, 100.0]]


def test_connect_draws_a_line_per_hole():
    _, ax = ht.plot.spt_profile(spt_frame(), connect=True)
    assert len(ax.lines) == 2


def test_qualifier_column_is_not_read(points):
    _, ax = ht.plot.spt_profile(spt_frame(qualifier=["<", "", "", ">"]))
    assert ax.ags_notes == {}
    assert len(points(ax)) == 4


def test_a_refusal_is_drawn_at_the_cap_as_a_triangle():
    df = spt_frame(
        spt_n=[4.0, 9.0, 38.0, np.nan], spt_refusal=[False, False, True, True]
    )
    _, ax = ht.plot.spt_profile(df)
    sand = [c for c in ax.collections if c.get_label().startswith("_Sand")]
    (refusals,) = [c for c in sand if len(c.get_offsets())]
    assert refusals.get_offsets().data.tolist() == [[100.0, 105.0], [100.0, 100.0]]
    assert ax.ags_notes == {"refusal": 2}
    legend = [t.get_text() for t in ax.get_legend().get_texts()]
    assert "refusal (2)" in legend


# --- overlays pass through ------------------------------------------------------


def test_p01_overlays_pass_through():
    strata = ht.set_units(
        pd.DataFrame(
            {
                "geology_unit": ["Fill", "Sand"],
                "depth_top": [0, 12],
                "depth_base": [12, 25],
            }
        ),
        {"depth_top": "ft", "depth_base": "ft"},
    )
    ranges = pd.DataFrame({"low": [30], "high": [50], "label": ["Dense"]})
    design = ht.set_units(
        pd.DataFrame({"label": ["Design N"], "depth": [0.0], "value": [10.0]}),
        {"depth": "ft"},
    )
    _, ax = ht.plot.spt_profile(
        spt_frame(),
        strata=strata,
        water_level=108.0,
        ranges=ranges,
        design_lines=design,
        reference_lines=[(50, "Very dense")],
        stats_box=["count", "mean"],
        note="Draft",
    )
    texts = [t.get_text() for t in ax.texts]
    assert {"Fill", "Sand", "Dense", "Very dense", "Draft"} <= set(texts)
    assert any(line.get_linestyle() == "--" for line in ax.lines)  # water level
    assert len(ax.patches) >= 3  # two strata bands and a range


# --- units ------------------------------------------------------------------------


def test_us_and_si_put_points_in_the_same_place(assert_us_si_equivalent):
    df = spt_frame(spt_refusal=[False, False, False, True])
    assert_us_si_equivalent(ht.plot.spt_profile, df, ("count", "length"))


def test_n_is_never_converted(points):
    _, us = ht.plot.spt_profile(spt_frame(), display_units="US")
    _, si = ht.plot.spt_profile(spt_frame(), display_units="SI")
    assert points(us)[:, 0].tolist() == points(si)[:, 0].tolist()
    # 10.0 ft <-> 3.048 m, on the vertical axis only.
    np.testing.assert_allclose(points(si)[:, 1], points(us)[:, 1] * 0.3048)
    assert si.get_xlabel() == "SPT N"
    assert si.get_ylabel() == "Elevation (m)"


def test_penetration_units_reach_the_analysis():
    df = spt_frame(spt_refusal=[None] * 4, spt_penetration=[18.0, 18.0, 12.0, 18.0])
    _, ax = ht.plot.spt_profile(df, units={"spt_penetration": "in"})
    assert ax.ags_notes == {"refusal": 1}


def test_no_global_state(assert_no_global_state):
    assert_no_global_state(ht.plot.spt_profile, spt_frame())


def test_no_global_state_on_a_sheet_panel(assert_no_global_state):
    sheet = ht.Sheet("letter", layout=(1, 2))
    assert_no_global_state(ht.plot.spt_profile, spt_frame(), ax=sheet[0])


def test_empty_input_shows_no_data():
    df = spt_frame().iloc[0:0]
    _, ax = ht.plot.spt_profile(df)
    assert "No data" in [t.get_text() for t in ax.texts]


# --- hints ------------------------------------------------------------------------


def hints(df, **kwargs):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ht.plot.spt_profile(df, **kwargs)
    return [str(w.message) for w in caught if issubclass(w.category, ht.HangtuHint)]


def test_hint_when_neither_refusal_column_is_there():
    (hint,) = hints(spt_frame().drop(columns="spt_refusal"))
    assert "No 'spt_refusal' column: refusals can't be found" in hint
    assert "'spt_penetration'" in hint


def test_no_refusal_hint_with_either_column():
    assert hints(spt_frame()) == []
    df = spt_frame(spt_penetration=[450.0] * 4).drop(columns="spt_refusal")
    assert hints(df, units={"spt_penetration": "mm"}) == []


def test_refusal_hint_joins_the_p01_hint():
    df = spt_frame().drop(columns=["spt_refusal", "loca_id"])
    (hint,) = hints(df)
    assert hint.index("'loca_id'") < hint.index("'spt_refusal'")


# --- errors -----------------------------------------------------------------------


def test_missing_spt_n_lists_the_columns():
    with pytest.raises(ht.ColumnError, match=r"'spt_n'.*Available columns: loca_id"):
        ht.plot.spt_profile(spt_frame().drop(columns="spt_n"))


@pytest.mark.parametrize(
    ("argument", "value", "message"),
    [
        ("n", "N60", r"n must be one of 'spt_n', 'spt_n60', 'spt_n_capped', not 'N60'"),
        ("refusal", "drop", r"refusal must be one of 'cap', 'exclude', not 'drop'"),
    ],
)
def test_bad_choices_are_errors(argument, value, message):
    with pytest.raises(ht.HangtuError, match=message):
        ht.plot.spt_profile(spt_frame(), **{argument: value})
