"""P07 sub-rows by a column, ``split_by=`` (P07 §4, §7, §11, §12; M18 (d))."""

import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.plot._geology_units import BASELINE_OFFSET, UNIT_RULE_COLOR

DOT = "\N{MIDDLE DOT}"
# Two units, Terrace split by three sources in this order of first appearance.
SOURCES = ["SPT B", "UU", "SPT B", "SPT A", "UU", "SPT A", "UU", "SPT B", "SPT A"]
TERRACE = [34.0, 30.0, 36.5, 31.2, 32.0, 34.8, 29.0, 39.2, 36.1]
ALLUVIUM = [30.0, 32.0, 29.0, 31.5, 28.0]


def frame():
    """Terrace with three sources (5 SPT B, 5 UU, 5 SPT A), Alluvium with one (5 UU)."""
    rows = {
        "geology_unit": ["Terrace"] * 15 + ["Alluvium"] * 5,
        "parameter_source": [*SOURCES, "UU", "SPT B", "SPT A", "SPT B", "SPT A", "UU"]
        + ["UU"] * 5,
        "effective_friction_angle": [
            *TERRACE,
            31.0,
            35.1,
            33.0,
            41.0,
            38.4,
            30.5,
            *ALLUVIUM,
        ],
    }
    return ht.set_units(pd.DataFrame(rows), {"effective_friction_angle": "deg"})


def plot(df=None, **kwargs):
    kwargs.setdefault("split_by", "parameter_source")
    kwargs.setdefault("order", ["Terrace", "Alluvium"])
    return ht.plot.geology_unit_comparison(
        frame() if df is None else df, "effective_friction_angle", **kwargs
    )


def tick_labels(ax):
    return [label.get_text() for label in ax.get_yticklabels()]


def count_labels(ax):
    return [text.get_text() for text in ax.texts if text.get_text().startswith("n =")]


def legend_texts(ax):
    legend = ax.get_legend()
    return [] if legend is None else [text.get_text() for text in legend.get_texts()]


def rules(ax):
    """The y of each thin rule between units."""
    return [
        float(line.get_ydata()[0])
        for line in ax.lines
        if line.get_color() == UNIT_RULE_COLOR
    ]


def bars(ax):
    """Summary bars as {row y: (x0, x1)}: horizontal two-point lines in a unit color."""
    found = {}
    for line in ax.lines:
        x, y = (np.asarray(a, dtype=float) for a in line.get_data())
        if (
            line.get_marker() in ("None", "none", "")
            and len(x) == 2
            and y[0] == y[1]
            and line.get_color() not in (UNIT_RULE_COLOR, "0.25")
        ):
            found[float(y[0])] = tuple(x)
    return found


def centrals(ax):
    return {
        float(line.get_ydata()[0]): float(line.get_xdata()[0])
        for line in ax.lines
        if line.get_marker() == "o"
    }


def points_by_row(ax):
    """{tick label: (n, 2) offsets} for the data point collections."""
    return {
        c.get_label().lstrip("_"): c.get_offsets().data
        for c in ax.collections
        if c.get_label().startswith("_")
    }


# --- rows ---------------------------------------------------------------------


def test_sub_rows_in_order_of_first_appearance_under_each_unit():
    _, ax = plot()
    assert tick_labels(ax) == [
        f"Terrace {DOT} SPT B",
        f"Terrace {DOT} UU",
        f"Terrace {DOT} SPT A",
        f"Alluvium {DOT} UU",
    ]


def test_without_split_by_each_unit_is_one_row():
    _, ax = plot(split_by=None)
    assert tick_labels(ax) == ["Terrace", "Alluvium"]
    assert rules(ax) == []
    assert count_labels(ax) == ["n = 15 (mixes sources)", "n = 5"]


def test_a_blank_split_value_is_a_blank_sub_row_last_in_its_unit():
    df = frame()
    df.loc[0, "parameter_source"] = None
    _, ax = plot(df)
    assert tick_labels(ax)[:4] == [
        f"Terrace {DOT} UU",
        f"Terrace {DOT} SPT B",
        f"Terrace {DOT} SPT A",
        f"Terrace {DOT} (blank)",
    ]


def test_units_keep_their_order_and_a_rule_separates_them():
    _, ax = plot(order=["Alluvium", "Terrace"])
    assert tick_labels(ax)[0] == f"Alluvium {DOT} UU"
    assert rules(ax) == [0.5]
    _, ax = plot()
    assert rules(ax) == [2.5]


def test_each_sub_row_points_sit_on_their_row():
    _, ax = plot()
    drawn = points_by_row(ax)
    assert {name: len(xy) for name, xy in drawn.items()} == {
        f"Terrace {DOT} SPT B": 5,
        f"Terrace {DOT} UU": 5,
        f"Terrace {DOT} SPT A": 5,
        f"Alluvium {DOT} UU": 5,
    }
    for row, name in enumerate(tick_labels(ax)):
        assert np.all(np.abs(drawn[name][:, 1] - row) <= 0.15)


# --- summaries and counts -----------------------------------------------------


def test_each_sub_row_is_summarized_as_describe_on_its_rows():
    df = frame()
    _, ax = plot(df)
    drawn = bars(ax)
    middle = centrals(ax)
    keys = [
        ("Terrace", "SPT B"),
        ("Terrace", "UU"),
        ("Terrace", "SPT A"),
        ("Alluvium", "UU"),
    ]
    for row, (unit, source) in enumerate(keys):
        these = df[(df["geology_unit"] == unit) & (df["parameter_source"] == source)]
        values = these["effective_friction_angle"].tolist()
        stats = ht.stats.describe(values, percentiles=(25, 75)).to_frame().iloc[0]
        assert drawn[row] == pytest.approx(
            (stats["percentile_25"], stats["percentile_75"])
        )
        assert middle[row] == pytest.approx(stats["median"])


def test_a_unit_split_by_a_source_column_never_mixes_sources():
    df = frame().rename(columns={"parameter_source": "test_type"})
    _, ax = plot(df, split_by=None)
    assert "n = 15 (mixes sources)" in count_labels(ax)
    _, ax = plot(df, split_by="test_type")
    assert count_labels(ax) == ["n = 5"] * 4
    assert len(bars(ax)) == 4


def test_a_sub_row_can_still_mix_sources_of_another_column():
    df = frame().assign(source=["lab", "field"] * 10)
    _, ax = plot(df)
    assert count_labels(ax)[0] == "n = 5 (mixes sources)"


# --- baseline -----------------------------------------------------------------


def baseline_rows(ax):
    """The y of each baseline bar."""
    return [
        float(line.get_ydata()[0])
        for line in ax.lines
        if line.get_color() == "0.25" and len(line.get_xdata()) == 2
    ]


def test_the_baseline_is_drawn_once_per_unit_on_its_first_sub_row():
    baseline = pd.DataFrame(
        {
            "geology_unit": ["Terrace", "Alluvium", "Till"],
            "low": [30.0, 26.0, 35.0],
            "central": [34.0, 29.0, 38.0],
            "high": [38.0, 32.0, 42.0],
        }
    )
    baseline = ht.set_units(baseline, {"low": "deg", "central": "deg", "high": "deg"})
    _, ax = plot(baseline=baseline)
    # Terrace on row 0 of 0-2, Alluvium on row 3, Till (no data) one row, 4.
    assert sorted(baseline_rows(ax)) == pytest.approx(
        [-BASELINE_OFFSET, 3 - BASELINE_OFFSET, 4 - BASELINE_OFFSET]
    )
    assert tick_labels(ax)[-1] == "Till"
    assert count_labels(ax)[-1] == "n = 0"
    assert rules(ax) == [2.5, 3.5]


# --- color --------------------------------------------------------------------


def test_color_by_the_split_column_colors_sub_rows_and_adds_a_legend():
    _, ax = plot(color_by="parameter_source", legend="bottom")
    drawn = {c.get_label().lstrip("_"): c for c in ax.collections}
    uu = [
        drawn[f"{unit} {DOT} UU"].get_facecolor()[0] for unit in ("Terrace", "Alluvium")
    ]
    assert mcolors.same_color(uu[0][:3], uu[1][:3])
    spt = drawn[f"Terrace {DOT} SPT A"].get_facecolor()[0]
    assert not mcolors.same_color(spt[:3], uu[0][:3])
    texts = legend_texts(ax)
    assert texts[-3:] == ["SPT B", "UU", "SPT A"]


def test_color_by_unit_adds_no_value_entries():
    _, ax = plot(legend="bottom")
    assert not {"SPT A", "SPT B", "UU"} & set(legend_texts(ax))
    drawn = {c.get_label().lstrip("_"): c for c in ax.collections}
    terrace = [drawn[f"Terrace {DOT} {s}"].get_facecolor()[0] for s in ("UU", "SPT A")]
    assert mcolors.same_color(terrace[0][:3], terrace[1][:3])


# --- errors -------------------------------------------------------------------


def test_a_missing_split_by_column_names_it_and_the_columns():
    with pytest.raises(
        ht.ColumnError, match=r"'test_type' not found.*parameter_source"
    ):
        plot(split_by="test_type")


def test_color_by_must_be_the_unit_the_split_column_or_none():
    with pytest.raises(ht.HangtuError, match="'parameter_source' \\(the split_by"):
        plot(color_by="loca_id")
    with pytest.raises(ht.HangtuError, match='"geology_unit" or None'):
        plot(split_by=None, color_by="parameter_source")


def test_split_by_geology_unit_is_an_error():
    with pytest.raises(ht.HangtuError, match="already geology units"):
        plot(split_by="geology_unit")


# --- grid ---------------------------------------------------------------------


def test_the_grid_splits_every_panel():
    df = frame().assign(water_content=np.linspace(10.0, 40.0, 20))
    _, axs = ht.plot.geology_unit_comparisons(
        df,
        ["effective_friction_angle", "water_content"],
        split_by="parameter_source",
        color_by="parameter_source",
        order=["Terrace", "Alluvium"],
    )
    for ax in axs:
        assert len(tick_labels(ax)) == 4
        assert rules(ax) == [2.5]
    legend = axs[0].figure.legends[0]
    texts = [text.get_text() for text in legend.get_texts()]
    assert [t for t in texts if t in ("SPT A", "SPT B", "UU")] == [
        "SPT B",
        "UU",
        "SPT A",
    ]
