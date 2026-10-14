"""P03 SPT class histogram: classes, bars, units, notes, hints and errors."""

import warnings

import numpy as np
import pandas as pd
import pytest

import hangtu as ht

DASH = "\N{EN DASH}"
GOLDEN_N = [0.0, 4.0, 10.0, 29.0, 30.0, 50.0, 51.0]
COHESIONLESS = [
    "Very loose\n< 4",
    f"Loose\n4{DASH}10",
    f"Medium dense\n10{DASH}30",
    f"Dense\n30{DASH}50",
    "Very dense\n≥ 50",
    "Refusal",
]


def spt_frame(n=GOLDEN_N, unit="A", **columns):
    """SPT tests in one unit, no refusals, unless ``columns`` say otherwise."""
    data = {
        "spt_n": list(n),
        "spt_refusal": [False] * len(n),
        "geology_unit": [unit] * len(n),
        **columns,
    }
    return pd.DataFrame(data)


def two_units():
    """Unit B (3 tests) listed before unit A (4 tests), so order isn't by row."""
    return spt_frame(
        n=[5.0, 12.0, 35.0, 2.0, 8.0, 15.0, 40.0],
        geology_unit=["B", "B", "B", "A", "A", "A", "A"],
    )


def heights(ax, unit):
    """Bar heights for ``unit``, one per class slot, rounded to 0.1 %."""
    (bars,) = [c for c in ax.containers if c.get_label() == unit]
    return [round(p.get_height(), 1) for p in bars.patches]


def tick_labels(ax):
    return [t.get_text() for t in ax.get_xticklabels()]


def legend_texts(ax):
    return [t.get_text() for t in ax.get_legend().texts]


# --- classes and bars -------------------------------------------------------------


def test_golden_heights_lower_bound_inclusive():
    # Very loose 0; loose 4; medium dense 10, 29; dense 30; very dense 50, 51.
    _, ax = ht.plot.spt_histogram(spt_frame())
    assert heights(ax, "A") == [14.3, 14.3, 28.6, 14.3, 28.6, 0.0]
    assert legend_texts(ax) == ["A (n = 7)"]
    assert ax.ags_notes == {}


def test_cohesionless_axis():
    _, ax = ht.plot.spt_histogram(spt_frame())
    assert tick_labels(ax) == COHESIONLESS
    assert ax.get_xlabel() == "SPT N class (cohesionless)"
    assert ax.get_ylabel() == "Tests in unit (%)"
    assert ax.get_ylim() == (0.0, 30.0)


def test_cohesive_table():
    # Very soft 0, 1; soft 2; medium stiff 4; stiff 8, 14; very stiff 15; hard 30.
    df = spt_frame(n=[0.0, 1.0, 2.0, 4.0, 8.0, 14.0, 15.0, 30.0])
    _, ax = ht.plot.spt_histogram(df, table="cohesive")
    assert tick_labels(ax) == [
        "Very soft\n< 2",
        f"Soft\n2{DASH}4",
        f"Medium stiff\n4{DASH}8",
        f"Stiff\n8{DASH}15",
        f"Very stiff\n15{DASH}30",
        "Hard\n≥ 30",
        "Refusal",
    ]
    assert ax.get_xlabel() == "SPT N class (cohesive)"
    assert heights(ax, "A") == [25.0, 12.5, 12.5, 25.0, 12.5, 12.5, 0.0]


def test_every_test_is_in_exactly_one_bar():
    rng = np.random.default_rng(1)
    df = spt_frame(n=rng.integers(0, 80, 40).astype(float))
    _, ax = ht.plot.spt_histogram(df)
    assert sum(heights(ax, "A")) == pytest.approx(100.0, abs=0.5)
    (bars,) = ax.containers
    counts = [round(p.get_height() * 40 / 100) for p in bars.patches]
    assert sum(counts) == 40


def test_percent_is_per_unit():
    _, ax = ht.plot.spt_histogram(two_units())
    # A: 2 very loose, 8 loose, 15 medium dense, 40 dense; 4 tests.
    assert heights(ax, "A") == [25.0, 25.0, 25.0, 25.0, 0.0, 0.0]
    # B: 5 loose, 12 medium dense, 35 dense; 3 tests.
    assert heights(ax, "B") == [0.0, 33.3, 33.3, 33.3, 0.0, 0.0]
    assert legend_texts(ax) == ["A (n = 4)", "B (n = 3)"]


def test_bars_are_grouped_side_by_side():
    _, ax = ht.plot.spt_histogram(two_units())
    a, b = ax.containers
    assert a.patches[0].get_width() == pytest.approx(0.4)
    assert a.patches[0].get_x() == pytest.approx(-0.4)
    assert b.patches[0].get_x() == pytest.approx(0.0)
    assert b.patches[2].get_x() == pytest.approx(2.0)


def test_order_puts_listed_units_first():
    _, ax = ht.plot.spt_histogram(two_units(), order=["B"])
    assert [c.get_label() for c in ax.containers] == ["B", "A"]
    assert legend_texts(ax) == ["B (n = 3)", "A (n = 4)"]


def test_blank_unit_is_last_in_gray():
    df = spt_frame(n=[5.0, 12.0, 35.0], geology_unit=["B", None, "A"])
    _, ax = ht.plot.spt_histogram(df)
    assert [c.get_label() for c in ax.containers] == ["A", "B", "(blank)"]
    (blank,) = [c for c in ax.containers if c.get_label() == "(blank)"]
    assert blank.patches[0].get_facecolor()[:3] == pytest.approx((0.3, 0.3, 0.3))


def test_color_by_none_draws_one_group():
    _, ax = ht.plot.spt_histogram(two_units(), color_by=None)
    assert len(ax.containers) == 1
    assert legend_texts(ax) == ["All tests (n = 7)"]


def test_palette_colors_the_bars():
    _, ax = ht.plot.spt_histogram(spt_frame(), palette={"A": "tan"})
    assert ax.containers[0].patches[0].get_facecolor()[:3] == pytest.approx(
        (210 / 255, 180 / 255, 140 / 255)
    )


def test_unknown_color_by_column_is_an_error():
    with pytest.raises(ht.ColumnError, match="color_by='soil' isn't a column"):
        ht.plot.spt_histogram(spt_frame(), color_by="soil")


# --- blank values and N60 ---------------------------------------------------------


def test_blank_n_is_counted_not_classified():
    df = spt_frame(n=[5.0, np.nan, 12.0, np.nan])
    _, ax = ht.plot.spt_histogram(df)
    assert legend_texts(ax) == ["A (n = 2)"]
    assert heights(ax, "A")[1:3] == [50.0, 50.0]
    assert ax.ags_notes == {"nan": 2}


def test_n60_is_classified_and_labeled():
    # 30 * 80 / 60 = 40, dense; 9 * 80 / 60 = 12, medium dense.
    df = spt_frame(n=[30.0, 9.0], energy_ratio=[80, 80])
    _, ax = ht.plot.spt_histogram(df, n="spt_n60")
    assert ax.get_xlabel() == "SPT N60 class (cohesionless)"
    assert heights(ax, "A") == [0.0, 0.0, 50.0, 50.0, 0.0, 0.0]


def test_n60_hammer_efficiency_is_passed_to_the_analysis():
    df = spt_frame(n=[30.0, 9.0])
    _, ax = ht.plot.spt_histogram(df, n="spt_n60", hammer_efficiency=80)
    assert heights(ax, "A") == [0.0, 0.0, 50.0, 50.0, 0.0, 0.0]


def test_tests_without_n60_are_counted():
    df = spt_frame(n=[30.0, 9.0, 20.0, np.nan], energy_ratio=[80, 80, None, 80])
    _, ax = ht.plot.spt_histogram(df, n="spt_n60")
    assert legend_texts(ax) == ["A (n = 2)"]
    assert ax.ags_notes == {"no_energy_ratio": 1, "nan": 1}


def test_no_n60_anywhere_is_an_error():
    with pytest.raises(ht.HangtuError, match="No test has N60") as caught:
        ht.plot.spt_histogram(spt_frame(), n="spt_n60")
    assert "hammer_efficiency=80" in str(caught.value)
    assert 'n="spt_n"' in str(caught.value)


# --- errors, hints and the contract -----------------------------------------------


@pytest.mark.parametrize(
    ("argument", "value", "message"),
    [
        ("n", "spt_n_capped", "n must be one of 'spt_n', 'spt_n60'"),
        ("table", "granular", "There is no SPT class table named 'granular'"),
        ("refusal", "cap", "refusal must be one of 'separate', 'exclude'"),
    ],
)
def test_unknown_choices_are_errors(argument, value, message):
    with pytest.raises(ht.HangtuError, match=message):
        ht.plot.spt_histogram(spt_frame(), **{argument: value})


def test_missing_spt_n_is_the_analysis_error():
    with pytest.raises(ht.ColumnError, match="Column 'spt_n'"):
        ht.plot.spt_histogram(spt_frame().drop(columns="spt_n"))


def hints(df, **kwargs):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ht.plot.spt_histogram(df, **kwargs)
    return [str(w.message) for w in caught if issubclass(w.category, ht.HangtuHint)]


def test_hint_without_geology_unit_draws_one_group():
    df = spt_frame().drop(columns="geology_unit")
    with pytest.warns(ht.HangtuHint, match="No 'geology_unit' column: all tests"):
        _, ax = ht.plot.spt_histogram(df)
    assert legend_texts(ax) == ["All tests (n = 7)"]


def test_hint_without_refusal_columns():
    (hint,) = hints(spt_frame().drop(columns="spt_refusal"))
    assert "No 'spt_refusal' column: refusals can't be found" in hint


def test_no_hint_with_the_columns():
    assert hints(spt_frame()) == []
    assert hints(spt_frame().drop(columns="geology_unit"), color_by=None) == []


def test_display_units_change_nothing():
    _, us = ht.plot.spt_histogram(two_units(), display_units="US")
    _, si = ht.plot.spt_histogram(two_units(), display_units="SI")
    for unit in ("A", "B"):
        assert heights(us, unit) == heights(si, unit)
    assert tick_labels(us) == tick_labels(si)
    assert us.get_xlabel() == si.get_xlabel()


def test_no_global_state(assert_no_global_state):
    assert_no_global_state(ht.plot.spt_histogram, two_units())


def test_no_global_state_on_a_sheet_panel(assert_no_global_state):
    sheet = ht.Sheet("letter", layout=(1, 2))
    assert_no_global_state(ht.plot.spt_histogram, two_units(), ax=sheet[1])


def test_empty_input_shows_no_data():
    _, ax = ht.plot.spt_histogram(spt_frame().iloc[0:0])
    assert "No data" in [t.get_text() for t in ax.texts]
    assert ax.get_ylim() == (0.0, 100.0)


# --- refusals ---------------------------------------------------------------------


def with_refusal():
    """The golden N plus a refusal at N = 12: 8 tests."""
    return spt_frame(
        n=[*GOLDEN_N, 12.0], spt_refusal=[False] * 7 + [True], geology_unit=["A"] * 8
    )


def test_refusal_is_in_its_own_class_only():
    _, ax = ht.plot.spt_histogram(with_refusal())
    # 1, 1, 2, 1, 2 and 1 refusal of 8; N = 12 doesn't add to medium dense.
    assert heights(ax, "A") == [12.5, 12.5, 25.0, 12.5, 25.0, 12.5]
    assert legend_texts(ax) == ["A (n = 8)", "refusal"]
    assert ax.ags_notes == {}


def test_refusal_bar_is_hatched_in_the_unit_color():
    _, ax = ht.plot.spt_histogram(with_refusal(), palette={"A": "tan"})
    (bars,) = ax.containers
    tan = (210 / 255, 180 / 255, 140 / 255)
    assert bars.patches[-1].get_hatch() == "////"
    assert bars.patches[-1].get_edgecolor()[:3] == pytest.approx(tan)
    assert bars.patches[-1].get_facecolor()[:3] == pytest.approx(tan)
    assert all(p.get_hatch() is None for p in bars.patches[:-1])


def test_one_shared_refusal_legend_entry():
    df = pd.concat([with_refusal(), with_refusal().assign(geology_unit="B")])
    _, ax = ht.plot.spt_histogram(df.reset_index(drop=True))
    assert legend_texts(ax) == ["A (n = 8)", "B (n = 8)", "refusal"]
    (entry,) = [h for h in ax.get_legend().get_patches() if h.get_hatch()]
    assert entry.get_label() == "refusal"


def test_no_refusal_legend_entry_without_refusals():
    _, ax = ht.plot.spt_histogram(spt_frame())
    assert legend_texts(ax) == ["A (n = 7)"]


def test_refusal_with_blank_n_is_a_refusal():
    df = spt_frame(n=[5.0, np.nan], spt_refusal=[False, True])
    _, ax = ht.plot.spt_histogram(df)
    assert heights(ax, "A") == [0.0, 50.0, 0.0, 0.0, 0.0, 50.0]
    assert ax.ags_notes == {}


def test_exclude_leaves_refusals_out_and_counts_them():
    _, ax = ht.plot.spt_histogram(with_refusal(), refusal="exclude")
    assert tick_labels(ax) == COHESIONLESS[:-1]
    assert heights(ax, "A") == [14.3, 14.3, 28.6, 14.3, 28.6]
    assert legend_texts(ax) == ["A (n = 7)"]
    assert ax.ags_notes == {"refusal_excluded": 1}
    assert "1 refusal not shown" in footnote(ax)


def test_refusals_are_counted_with_n60():
    # The refusal has no energy ratio, but it is still a refusal.
    df = spt_frame(
        n=[30.0, 9.0, 60.0], energy_ratio=[80, 80, None], spt_refusal=[0, 0, 1]
    )
    _, ax = ht.plot.spt_histogram(df, n="spt_n60")
    assert legend_texts(ax) == ["A (n = 3)", "refusal"]
    assert ax.ags_notes == {}


# --- bar labels and notes ---------------------------------------------------------


def footnote(ax):
    return "\n".join(t.get_text() for t in ax.texts)


def test_bar_labels_on_non_zero_bars_only():
    _, ax = ht.plot.spt_histogram(with_refusal(), bar_labels=True)
    labels = [t for t in ax.texts if t.get_text().isdigit()]
    assert [t.get_text() for t in labels] == ["1", "1", "2", "1", "2", "1"]
    (bars,) = ax.containers
    assert [t.xy for t in labels] == pytest.approx(
        [(p.get_x() + p.get_width() / 2, p.get_height()) for p in bars.patches]
    )
    assert ax.get_ylim()[1] > 25.0


def test_no_bar_labels_by_default():
    _, ax = ht.plot.spt_histogram(spt_frame())
    assert not [t for t in ax.texts if t.get_text().isdigit()]


def test_note_is_in_the_footnote():
    _, ax = ht.plot.spt_histogram(spt_frame(), note="Sands only")
    assert "Sands only" in footnote(ax)


def test_unit_in_order_with_no_tests_is_noted():
    _, ax = ht.plot.spt_histogram(two_units(), order=["C", "B", "A"])
    assert [c.get_label() for c in ax.containers] == ["B", "A"]
    assert "No classified tests: C" in footnote(ax)


def test_unit_with_only_blank_n_is_noted():
    df = spt_frame(n=[5.0, np.nan, np.nan], geology_unit=["A", "B", "B"])
    _, ax = ht.plot.spt_histogram(df)
    assert [c.get_label() for c in ax.containers] == ["A"]
    assert legend_texts(ax) == ["A (n = 1)"]
    assert "No classified tests: B" in footnote(ax)
    assert ax.ags_notes == {"nan": 2}


def test_no_note_when_every_unit_has_tests():
    _, ax = ht.plot.spt_histogram(two_units(), order=["B", "A"])
    assert "No classified tests" not in footnote(ax)
