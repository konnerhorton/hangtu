"""P05 grain size curves, colors and counts (P05 §3, §7, §11, §12)."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError, HangtuHint


@pytest.fixture(autouse=True)
def _no_hints():
    """Most frames here have no geology_unit; its hint is tested on its own."""
    ht.settings.hints = False


CURVE_A = (
    [0.075, 0.15, 0.3, 0.6, 1.18, 2.36, 4.75],
    [4, 12, 30, 55, 75, 90, 100],
)


def curves(*specs, unit="mm", **columns):
    """One row per point; each spec is (specimen_id, sizes, passing)."""
    rows = []
    for specimen, sizes, passing in specs:
        for size, percent in zip(sizes, passing, strict=True):
            rows.append(
                {
                    "specimen_id": specimen,
                    "particle_size": size,
                    "percent_passing": percent,
                }
            )
    df = pd.DataFrame(rows)
    for column, values in columns.items():
        df[column] = values
    return ht.set_units(df, {"particle_size": unit})


def drawn(ax):
    return {
        line.get_label(): np.column_stack(line.get_data())
        for line in ax.lines
        if line.get_gid() == "curve"
    }


def legend_texts(ax):
    legend = ax.get_legend()
    return [t.get_text() for t in legend.get_texts()] if legend else []


# --- Curves (§12) ------------------------------------------------------------


def test_curve_is_drawn_through_its_points():
    _, ax = ht.plot.grain_size(curves(("A", *CURVE_A)))
    xy = drawn(ax)["A"]
    np.testing.assert_allclose(xy, np.column_stack(CURVE_A))


def test_shuffled_rows_are_drawn_in_size_order():
    df = curves(("A", *CURVE_A)).sample(frac=1, random_state=3)
    _, ax = ht.plot.grain_size(df)
    np.testing.assert_allclose(drawn(ax)["A"], np.column_stack(CURVE_A))


def test_curve_in_inches_lands_on_the_curve_in_mm():
    inches = [size / 25.4 for size in CURVE_A[0]]
    _, ax = ht.plot.grain_size(curves(("A", inches, CURVE_A[1]), unit="in"))
    np.testing.assert_allclose(drawn(ax)["A"], np.column_stack(CURVE_A))


def test_curves_are_told_apart_by_hole():
    df = curves(("1", *CURVE_A), ("1", *CURVE_A), loca_id=["B-1"] * 7 + ["B-2"] * 7)
    _, ax = ht.plot.grain_size(df)
    assert sorted(drawn(ax)) == ["B-1 1", "B-2 1"]


def test_x_limits_cover_the_data_in_whole_decades():
    _, ax = ht.plot.grain_size(curves(("A", [0.0005, 0.075, 150], [0, 50, 100])))
    np.testing.assert_allclose(ax.get_xlim(), (0.0001, 1000))
    # A point on a whole decade moves the limit out (P00 §8).
    _, ax = ht.plot.grain_size(curves(("A", [0.001, 100], [0, 100])))
    np.testing.assert_allclose(ax.get_xlim(), (0.0001, 1000))
    _, ax = ht.plot.grain_size(curves(("A", *CURVE_A)))
    np.testing.assert_allclose(ax.get_xlim(), (0.001, 100))


# --- Counts (§11) ------------------------------------------------------------


def test_short_curve_and_blank_points_are_counted():
    df = curves(
        ("A", *CURVE_A),
        ("B", [0.075], [10]),
        ("C", [0.075, 0.15, 0.3], [5, np.nan, 40]),
    )
    _, ax = ht.plot.grain_size(df)
    assert sorted(drawn(ax)) == ["A", "C"]
    assert ax.ags_notes == {"nan": 1, "short_curve": 1}
    footnote = ax.texts[-1].get_text()
    assert "1 curve with fewer than two points not shown" in footnote
    assert "1 blank value not shown" in footnote


def test_only_short_curves_give_no_data():
    _, ax = ht.plot.grain_size(curves(("B", [0.075], [10])))
    assert drawn(ax) == {}
    assert "No data" in [t.get_text() for t in ax.texts]


def test_non_monotonic_curve_is_drawn_as_given_with_a_warning():
    df = curves(("A", *CURVE_A), ("N", [0.075, 0.15, 0.3], [20, 10, 50]))
    with pytest.warns(UserWarning, match=r"toward finer sizes in N\. Drawn as"):
        _, ax = ht.plot.grain_size(df)
    np.testing.assert_allclose(drawn(ax)["N"][:, 1], [20, 10, 50])


def test_qualifiers_are_counted_and_drawn_at_their_value():
    df = curves(("A", *CURVE_A), qualifier=["<", "", "", "", "", "", ">"])
    _, ax = ht.plot.grain_size(df)
    assert ax.ags_notes == {"less_than": 1, "greater_than": 1}
    assert len(drawn(ax)["A"]) == 7


def test_xlim_draws_points_beyond_it_at_the_edge():
    _, ax = ht.plot.grain_size(curves(("A", *CURVE_A)), xlim=(0.1, 10))
    assert ax.ags_notes == {"beyond_limit": 1}
    (line,) = [line for line in ax.lines if line.get_gid() == "curve"]
    assert list(line.get_markevery()) == [False, True, True, True, True, True, True]


def test_note_is_added_to_the_footnote():
    _, ax = ht.plot.grain_size(curves(("A", *CURVE_A)), note="Lab: ABC")
    assert "Lab: ABC" in ax.texts[-1].get_text()


# --- Analysis errors pass through (§11) --------------------------------------


def _without_units(df):
    df.attrs = {}
    return df


@pytest.mark.parametrize(
    ("change", "match"),
    [
        (lambda df: df.drop(columns="percent_passing"), "'percent_passing' not found"),
        (lambda df: df.copy().pipe(_without_units), "particle_size"),
        (lambda df: df.assign(particle_size=0.0), "0 or less"),
        (lambda df: df.assign(percent_passing=120.0), "outside 0 to 100"),
        (lambda df: df.assign(particle_size=1.0), "same particle size"),
        (lambda df: df.assign(specimen_id=None), "blank specimen_id"),
    ],
)
def test_analysis_errors(change, match):
    df = change(curves(("A", *CURVE_A)))
    with pytest.raises(HangtuError, match=match):
        ht.plot.grain_size(df)


# --- Colors and legend (§7) --------------------------------------------------


def two_units():
    return curves(
        ("A", *CURVE_A),
        ("B", *CURVE_A),
        ("C", *CURVE_A),
        geology_unit=["Till"] * 7 + ["Alluvium"] * 14,
    )


def test_colored_by_unit_with_counts():
    _, ax = ht.plot.grain_size(two_units(), order=["Till", "Alluvium"])
    assert legend_texts(ax) == ["Till (n = 1 curve)", "Alluvium (n = 2 curves)"]
    lines = {
        line.get_label(): line.get_color()
        for line in ax.lines
        if line.get_gid() == "curve"
    }
    assert lines["B"] == lines["C"] != lines["A"]


def test_palette_colors_units():
    _, ax = ht.plot.grain_size(two_units(), palette={"Till": "tan"})
    colors = {
        line.get_label(): line.get_color()
        for line in ax.lines
        if line.get_gid() == "curve"
    }
    assert colors["A"] == "tan"


def test_one_color_without_color_by():
    _, ax = ht.plot.grain_size(two_units(), color_by=None)
    assert legend_texts(ax) == ["All curves (n = 3)"]


def test_hint_without_geology_unit():
    ht.settings.hints = True
    with pytest.warns(HangtuHint, match="all curves are drawn in one color"):
        _, ax = ht.plot.grain_size(curves(("A", *CURVE_A)))
    assert legend_texts(ax) == ["All curves (n = 1)"]


def test_color_by_specimen_leaves_the_session_palette_alone():
    ht.plot.reset_palette()
    _, ax = ht.plot.grain_size(two_units(), color_by="specimen_id")
    assert legend_texts(ax) == ["A", "B", "C"]
    colors = [line.get_color() for line in ax.lines if line.get_gid() == "curve"]
    assert len(set(colors)) == 3
    with pytest.raises(HangtuError, match="No geology units have colors"):
        ht.plot.legend_handles()


def test_more_than_20_curves_by_specimen_warns():
    df = curves(*((f"S{i:02}", *CURVE_A) for i in range(21)))
    with pytest.warns(
        UserWarning, match='colors repeat after 20. Use color_by="geology_unit"'
    ):
        ht.plot.grain_size(df, color_by="specimen_id")


def test_color_by_that_varies_within_a_curve_is_an_error():
    df = curves(("A", *CURVE_A), geology_unit=["Till"] * 6 + ["Alluvium"])
    with pytest.raises(ColumnError, match="changes within the curve A"):
        ht.plot.grain_size(df)


def test_color_by_that_is_not_a_column_is_an_error():
    with pytest.raises(ColumnError, match="color_by='soil' isn't a column"):
        ht.plot.grain_size(curves(("A", *CURVE_A)), color_by="soil")


# --- Units and contract ------------------------------------------------------


def test_us_and_si_draw_the_same_curves():
    df = two_units()
    _, us = ht.plot.grain_size(df, display_units="US")
    _, si = ht.plot.grain_size(df, display_units="SI")
    for label, xy in drawn(us).items():
        np.testing.assert_allclose(xy, drawn(si)[label])
    assert us.ags_notes == si.ags_notes


def test_on_a_sheet_and_no_global_state(assert_no_global_state):
    df = two_units()
    assert_no_global_state(ht.plot.grain_size, df)
    sheet = ht.Sheet("letter", layout=(1, 2))
    assert_no_global_state(ht.plot.grain_size, df, ax=sheet[1])
    plt.close(sheet.figure)


# --- Legend and footnote below the axes (§5) ---------------------------------


def test_legend_and_footnote_sit_below_the_x_label():
    df = curves(("A", *CURVE_A), ("S", [0.075], [10]))
    fig, ax = ht.plot.grain_size(df)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label = ax.xaxis.label.get_window_extent(renderer)
    legend = ax.get_legend().get_window_extent(renderer)
    footnote = ax.texts[-1].get_window_extent(renderer)
    assert legend.y1 <= label.y0
    assert footnote.y1 <= legend.y0
    # Nothing beside the axes on the right.
    assert legend.x1 <= ax.get_window_extent().x1
    assert footnote.x1 <= ax.get_window_extent().x1


def test_footnote_without_a_legend_sits_below_the_x_label():
    fig, ax = ht.plot.grain_size(pd.DataFrame(), note="No grading tests")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    assert ax.get_legend() is None
    footnote = ax.texts[-1].get_window_extent(renderer)
    assert footnote.y1 <= ax.xaxis.label.get_window_extent(renderer).y0
