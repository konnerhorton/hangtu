"""P03 §12 acceptance criteria, against tests/data/spt.csv (P02's data).

The test splits the data on geology unit, as a user would: Fill and Alluvial
sand are cohesionless, Glacial till and Residual soil cohesive. Counts are by
hand from the CSV (refusals and blanks as in test_spt_profile_acceptance.py):
- Fill, 5 tests: N = 2 very loose; 8, 7, 8, 9 loose.
- Alluvial sand, 24 tests, one blank (BH-3 12.5 ft): 7 loose; 20 medium dense
  (10 to 29, N = 10 on BH-4 included); 34 and 31 dense. 23 classified.
- Glacial till, 33 tests, one blank (BH-2 42.5 ft): 29 very stiff; the other
  31, from 30 up, hard. 32 classified.
- Residual soil, 18 tests: 5 refusals (BH-1 92.5, BH-2 87.5, BH-3 77.5 and
  97.5, BH-4 97.5 ft); the other 13, from 42 up, hard.
- N60, energy ratio 82 % on BH-1 and BH-2 only. Fill: 8 -> 10.9 medium
  dense, 2 -> 2.7 very loose, 7 -> 9.6 loose. Sand: BH-1 14, 14, 13, 18, 18 medium
  dense, 26 -> 35.5 and 34 -> 46.5 dense; BH-2 7 -> 9.6 loose, 18, 20, 20, 11
  medium dense. Without an energy ratio: BH-3 Fill and 6 sand, BH-4 Fill and
  5 sand, 13 in all.
"""

from pathlib import Path

import pytest

import hangtu as ht

DATA = Path(__file__).parents[1] / "data"
DASH = "\N{EN DASH}"
COHESIONLESS = ["Fill", "Alluvial sand"]
COHESIVE = ["Glacial till", "Residual soil"]


def spt():
    return ht.read_csv(
        DATA / "spt.csv",
        units={"depth": "ft", "ground_level": "ft", "spt_penetration": "in"},
    )


def units_of(units):
    df = spt()
    return df[df["geology_unit"].isin(units)]


def heights(ax, unit):
    (bars,) = [c for c in ax.containers if c.get_label() == unit]
    return [round(p.get_height(), 1) for p in bars.patches]


def legend_texts(ax):
    return [t.get_text() for t in ax.get_legend().texts]


def footnote(ax):
    return "\n".join(t.get_text() for t in ax.texts)


def test_cohesionless_units():
    _, ax = ht.plot.spt_histogram(units_of(COHESIONLESS), order=COHESIONLESS)
    assert [c.get_label() for c in ax.containers] == COHESIONLESS
    # Fill: 1 and 4 of 5. Sand: 1, 20 and 2 of 23.
    assert heights(ax, "Fill") == [20.0, 80.0, 0.0, 0.0, 0.0, 0.0]
    assert heights(ax, "Alluvial sand") == [0.0, 4.3, 87.0, 8.7, 0.0, 0.0]
    assert legend_texts(ax) == ["Fill (n = 5)", "Alluvial sand (n = 23)"]
    assert ax.ags_notes == {"nan": 1}
    assert "1 blank value not shown" in footnote(ax)
    assert ax.get_xlabel() == "SPT N class (cohesionless)"
    assert ax.get_ylim() == (0.0, 100.0)


def test_cohesive_units_with_refusals():
    _, ax = ht.plot.spt_histogram(units_of(COHESIVE), table="cohesive")
    # Till: 1 and 31 of 32. Residual: 13 hard and 5 refusals of 18.
    assert heights(ax, "Glacial till") == [0.0, 0.0, 0.0, 0.0, 3.1, 96.9, 0.0]
    assert heights(ax, "Residual soil") == [0.0, 0.0, 0.0, 0.0, 0.0, 72.2, 27.8]
    assert legend_texts(ax) == [
        "Glacial till (n = 32)",
        "Residual soil (n = 18)",
        "refusal",
    ]
    assert ax.ags_notes == {"nan": 1}
    assert [t.get_text() for t in ax.get_xticklabels()][-2:] == [
        "Hard\n≥ 30",
        "Refusal",
    ]
    assert ax.get_xlabel() == "SPT N class (cohesive)"


def test_cohesive_units_without_refusals():
    _, ax = ht.plot.spt_histogram(
        units_of(COHESIVE), table="cohesive", refusal="exclude"
    )
    assert heights(ax, "Residual soil") == [0.0, 0.0, 0.0, 0.0, 0.0, 100.0]
    assert legend_texts(ax) == ["Glacial till (n = 32)", "Residual soil (n = 13)"]
    assert ax.ags_notes == {"nan": 1, "refusal_excluded": 5}
    assert "5 refusals not shown" in footnote(ax)


def test_cohesionless_n60():
    _, ax = ht.plot.spt_histogram(
        units_of(COHESIONLESS), n="spt_n60", order=COHESIONLESS
    )
    # Fill: 1, 1 and 1 of 3. Sand: 1, 9 and 2 of 12.
    assert heights(ax, "Fill") == [33.3, 33.3, 33.3, 0.0, 0.0, 0.0]
    assert heights(ax, "Alluvial sand") == [0.0, 8.3, 75.0, 16.7, 0.0, 0.0]
    assert legend_texts(ax) == ["Fill (n = 3)", "Alluvial sand (n = 12)"]
    assert ax.ags_notes == {"no_energy_ratio": 13, "nan": 1}
    assert ax.get_xlabel() == "SPT N60 class (cohesionless)"


def test_bar_labels_sum_to_n():
    _, ax = ht.plot.spt_histogram(units_of(COHESIVE), table="cohesive", bar_labels=True)
    counts = [int(t.get_text()) for t in ax.texts if t.get_text().isdigit()]
    assert sorted(counts) == [1, 5, 13, 31]
    assert sum(counts) == 32 + 18


def test_sheet_with_both_tables(assert_no_global_state):
    sheet = ht.Sheet("letter", layout=(1, 2))
    ht.plot.spt_histogram(units_of(COHESIONLESS), order=COHESIONLESS, ax=sheet[0])
    assert_no_global_state(
        ht.plot.spt_histogram, units_of(COHESIVE), table="cohesive", ax=sheet[1]
    )
    labels = [t.get_text() for t in sheet[1].get_xticklabels()]
    assert labels[3] == f"Stiff\n8{DASH}15"


@pytest.mark.parametrize("display_units", ["US", "SI"])
def test_display_units_change_nothing(display_units):
    _, ax = ht.plot.spt_histogram(
        units_of(COHESIONLESS), order=COHESIONLESS, display_units=display_units
    )
    assert heights(ax, "Alluvial sand") == [0.0, 4.3, 87.0, 8.7, 0.0, 0.0]
