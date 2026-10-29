"""P07 grid: several properties, one panel each (P07 §5, §10)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht

VALUES = ["water_content", "bulk_unit_weight", "plasticity_index", "consistency_index"]


def index_frame():
    n = 15
    rng = np.random.default_rng(3)
    df = pd.DataFrame(
        {
            "geology_unit": ["A", "B", "C"] * (n // 3),
            "water_content": rng.uniform(10, 30, n),
            "bulk_unit_weight": rng.uniform(110, 130, n),
            "plasticity_index": rng.uniform(5, 25, n),
            "consistency_index": rng.uniform(-0.2, 1.2, n),
        }
    )
    return ht.set_units(df, {"bulk_unit_weight": "pcf"})


def baseline():
    return pd.DataFrame(
        {
            "property": ["water_content", "bulk_unit_weight", "plasticity_index"],
            "geology_unit": ["A", "A", "D"],
            "low": [12.0, 18.0, 5.0],
            "high": [25.0, 21.0, 15.0],
            "source": ["GBR"] * 3,
        }
    )


def rows(ax):
    return [label.get_text() for label in ax.get_yticklabels()]


@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_one_panel_per_value_in_order(n):
    fig, axs = ht.plot.geology_unit_comparisons(index_frame(), VALUES[:n])
    assert len(axs) == n
    assert len(fig.axes) == n
    assert [ax.get_xlabel().split(",")[0] for ax in axs] == [
        "Water content",
        "Bulk unit weight",
        "Plasticity index",
        "Consistency index",
    ][:n]


def test_an_odd_last_panel_leaves_its_cell_empty():
    fig, axs = ht.plot.geology_unit_comparisons(index_frame(), VALUES[:3])
    assert len(fig.axes) == 3
    top_right = axs[1].get_position()
    bottom_left = axs[2].get_position()
    assert bottom_left.y1 < top_right.y0


def test_default_size_is_the_grid_size_per_panel_plus_the_legend():
    fig, _ = ht.plot.geology_unit_comparisons(index_frame(), VALUES)
    assert tuple(fig.get_size_inches()) == pytest.approx((7.5, 6.1))
    fig, _ = ht.plot.geology_unit_comparisons(index_frame(), VALUES[:1])
    assert tuple(fig.get_size_inches()) == pytest.approx((3.75, 3.35))
    fig, _ = ht.plot.geology_unit_comparisons(index_frame(), VALUES, figsize=(8, 8))
    assert tuple(fig.get_size_inches()) == pytest.approx((8, 8))


def test_columns_sets_panels_per_row():
    _, axs = ht.plot.geology_unit_comparisons(index_frame(), VALUES, columns=4)
    tops = {round(ax.get_position().y1, 3) for ax in axs}
    assert len(tops) == 1


def test_per_panel_settings_reach_their_panel():
    _, axs = ht.plot.geology_unit_comparisons(
        index_frame(),
        VALUES[:2],
        xlim={"bulk_unit_weight": (100, 140)},
        log={"water_content": True},
        label={"water_content": "Moisture"},
    )
    assert axs[0].get_xscale() == "log"
    assert axs[0].get_xlabel() == "Moisture (%)"
    assert axs[1].get_xlim() == (100, 140)


def test_unknown_per_panel_key_is_an_error():
    with pytest.raises(ht.HangtuError, match="liquid_limit"):
        ht.plot.geology_unit_comparisons(
            index_frame(), VALUES[:2], xlim={"liquid_limit": (0, 50)}
        )


def test_per_panel_setting_must_be_a_dict():
    with pytest.raises(ht.HangtuError, match="dict of"):
        ht.plot.geology_unit_comparisons(index_frame(), VALUES[:2], xlim=(0, 50))


def test_a_dict_of_tables_keeps_each_tables_units():
    vane = ht.set_units(
        pd.DataFrame(
            {"geology_unit": ["A", "B"] * 3, "undrained_shear_strength": [50.0] * 6}
        ),
        {"undrained_shear_strength": "kPa"},
    )
    _, axs = ht.plot.geology_unit_comparisons(
        {"bulk_unit_weight": index_frame(), "undrained_shear_strength": vane},
        ["bulk_unit_weight", "undrained_shear_strength"],
        display_units="US",
    )
    assert axs[0].get_xlabel().endswith("(pcf)")
    su = axs[1].collections[0].get_offsets()[:, 0]
    assert np.allclose(su, 1044.27, atol=0.01)


def test_a_dict_of_tables_needs_one_per_value():
    with pytest.raises(ht.HangtuError, match="Missing: bulk_unit_weight"):
        ht.plot.geology_unit_comparisons({"water_content": index_frame()}, VALUES[:2])


def test_each_panel_shows_only_its_units():
    _, axs = ht.plot.geology_unit_comparisons(
        index_frame(),
        VALUES[:3],
        baseline=baseline(),
        baseline_units={"bulk_unit_weight": "kN/m3"},
    )
    assert rows(axs[0]) == ["A", "B", "C"]
    assert rows(axs[2]) == ["A", "B", "C", "D"]


def test_one_legend_for_the_figure_with_the_baseline_first():
    fig, axs = ht.plot.geology_unit_comparisons(
        index_frame(),
        VALUES[:3],
        baseline=baseline(),
        baseline_units={"bulk_unit_weight": "kN/m3"},
        baseline_label="GBR baseline",
    )
    assert all(ax.get_legend() is None for ax in axs)
    (legend,) = fig.legends
    texts = [text.get_text() for text in legend.get_texts()]
    assert texts == ["GBR baseline", "Data p25\N{EN DASH}p75, p50", "Data"]


def test_qualifier_counts_are_summed_over_the_panels():
    df = index_frame()
    df["qualifier"] = ["<"] + [""] * 14
    fig, axs = ht.plot.geology_unit_comparisons(df, VALUES[:2])
    texts = [text.get_text() for text in fig.legends[0].get_texts()]
    assert texts[-1] == "less than (2)"
    assert [ax.ags_notes for ax in axs] == [{"less_than": 1}] * 2


def test_footnote_names_the_panel_of_each_note():
    fig, axs = ht.plot.geology_unit_comparisons(
        index_frame(), VALUES, xlim={"consistency_index": (0, 1)}
    )
    (footnote,) = [text for text in fig.texts if "beyond" in text.get_text()]
    n = axs[3].ags_notes["beyond_limit"]
    assert footnote.get_text() == (
        f"Consistency index, Ic: {n} values beyond axis limit, shown at the edge"
    )
    assert axs[0].ags_notes == {}


def test_footnote_sits_below_the_legend():
    fig, _ = ht.plot.geology_unit_comparisons(
        index_frame(), VALUES, xlim={"consistency_index": (0, 1)}
    )
    fig.draw_without_rendering()
    renderer = fig.canvas.get_renderer()
    legend = fig.legends[0].get_window_extent(renderer)
    (footnote,) = fig.texts
    assert footnote.get_window_extent(renderer).y1 <= legend.y0


def test_a_multi_property_baseline_needs_a_property_column():
    frame = baseline().drop(columns="property")
    with pytest.raises(ht.ColumnError, match="'property' column"):
        ht.plot.geology_unit_comparisons(index_frame(), VALUES[:2], baseline=frame)


@pytest.mark.parametrize("values", ["water_content", [], ["water_content"] * 2])
def test_bad_values_are_an_error(values):
    with pytest.raises(ht.HangtuError, match="values must be a list"):
        ht.plot.geology_unit_comparisons(index_frame(), values)


def test_missing_value_column_is_an_error():
    with pytest.raises(ht.ColumnError, match="'liquid_limit' not found"):
        ht.plot.geology_unit_comparisons(index_frame(), ["liquid_limit"])


def test_no_global_state(assert_no_global_state):
    def grid(df, **kwargs):
        return ht.plot.geology_unit_comparisons(df, VALUES, **kwargs)

    assert_no_global_state(grid, index_frame())
