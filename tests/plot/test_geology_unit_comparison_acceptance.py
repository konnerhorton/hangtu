"""P07 §12 acceptance criteria, against the test data in tests/data/.

Counts are by construction of the CSVs:
- comparison_index.csv (US): water contents A 60, B 80, C 40, D 90, E 50, F 70.
  Bulk unit weights B 12, C 2, D 15, E 8, F 10, none in A. Plasticity and
  consistency indices D 27, F 25, plus 3 NP specimens in D. Four consistency
  indices in F are below -0.6.
- comparison_vane.csv (SI): s_u D 14, F 25; one "<" value in F.
- comparison_perm.csv (cm/s): k in B, D and F, 8 each.
- comparison_baseline.csv (SI, declared with baseline_units): every unit for
  water content and unit weight, D and F for the rest, k in B, D and F with a
  central-only row in D.
"""

from pathlib import Path

import pytest

import hangtu as ht

DATA = Path(__file__).parents[1] / "data"
VALUES = [
    "water_content",
    "bulk_unit_weight",
    "plasticity_index",
    "consistency_index",
    "undrained_shear_strength",
    "hydraulic_conductivity",
]
BASELINE_UNITS = {
    "bulk_unit_weight": "kN/m3",
    "undrained_shear_strength": "kPa",
    "hydraulic_conductivity": "m/s",
}


def tables():
    index = ht.read_csv(
        DATA / "comparison_index.csv", units={"bulk_unit_weight": "pcf"}
    )
    vane = ht.read_csv(
        DATA / "comparison_vane.csv", units={"undrained_shear_strength": "kPa"}
    )
    perm = ht.read_csv(
        DATA / "comparison_perm.csv", units={"hydraulic_conductivity": "cm/s"}
    )
    return {
        "water_content": index,
        "bulk_unit_weight": index,
        "plasticity_index": index,
        "consistency_index": index,
        "undrained_shear_strength": vane,
        "hydraulic_conductivity": perm,
    }


def grid(**kwargs):
    return ht.plot.geology_unit_comparisons(
        tables(),
        VALUES,
        baseline=DATA / "comparison_baseline.csv",
        baseline_units=BASELINE_UNITS,
        baseline_label="GBR baseline p10-p90, p50",
        xlim={"consistency_index": (-0.6, 1.8)},
        **kwargs,
    )


def counts(ax):
    return {
        label.get_text().split(" (")[0]
        for label in ax.texts
        if label.get_text().startswith("n =")
    }


def count_texts(ax):
    return [text.get_text() for text in ax.texts if "n =" in text.get_text()]


def rows(ax):
    return [label.get_text() for label in ax.get_yticklabels()]


@pytest.fixture(name="panels", scope="module")
def _panels():
    _, axs = grid(display_units="SI")
    return dict(zip(VALUES, axs, strict=True))


def test_rows_and_counts_per_panel(panels):
    assert rows(panels["water_content"]) == list("ABCDEF")
    labels = [
        t.get_text() for t in panels["water_content"].texts if "n =" in t.get_text()
    ]
    assert labels == ["n = 60", "n = 80", "n = 40", "n = 90", "n = 50", "n = 70"]
    weight = [
        t.get_text() for t in panels["bulk_unit_weight"].texts if "n =" in t.get_text()
    ]
    assert weight == [
        "n = 0",
        "n = 12",
        "n = 2 (no summary)",
        "n = 15",
        "n = 8",
        "n = 10",
    ]
    assert rows(panels["plasticity_index"]) == ["D", "F"]
    assert counts(panels["plasticity_index"]) == {"n = 27", "n = 25"}
    assert rows(panels["undrained_shear_strength"]) == ["D", "F"]
    assert counts(panels["undrained_shear_strength"]) == {"n = 14", "n = 25"}
    assert rows(panels["hydraulic_conductivity"]) == ["B", "D", "F"]


def test_notes_per_panel(panels):
    assert panels["water_content"].ags_notes == {}
    assert panels["bulk_unit_weight"].ags_notes == {}
    assert panels["plasticity_index"].ags_notes == {"non_plastic": 3}
    assert panels["consistency_index"].ags_notes == {
        "non_plastic": 3,
        "beyond_limit": 4,
    }
    assert panels["undrained_shear_strength"].ags_notes == {"less_than": 1}
    assert panels["hydraulic_conductivity"].ags_notes == {}


def test_hydraulic_conductivity_is_on_a_log_axis_with_the_central_only_row(panels):
    ax = panels["hydraulic_conductivity"]
    assert ax.get_xscale() == "log"
    diamonds = {
        round(float(line.get_ydata()[0]) + 0.28): float(line.get_xdata()[0])
        for line in ax.lines
        if line.get_marker() == "D"
    }
    assert diamonds[1] == pytest.approx(1e-8)


def test_labels_carry_units(panels):
    assert panels["bulk_unit_weight"].get_xlabel() == "Bulk unit weight, γ (kN/m³)"
    assert panels["undrained_shear_strength"].get_xlabel().endswith("(kPa)")
    assert panels["hydraulic_conductivity"].get_xlabel().endswith("(m/s)")
    assert panels["consistency_index"].get_xlabel() == "Consistency index, Ic"


def test_us_and_si_give_the_same_rows_counts_and_notes():
    _, us = grid(display_units="US")
    _, si = grid(display_units="SI")
    for a, b in zip(us, si, strict=True):
        assert rows(a) == rows(b)
        assert counts(a) == counts(b)
        assert a.ags_notes == b.ags_notes


def test_us_labels_and_baseline_conversion():
    _, axs = grid(display_units="US")
    panels = dict(zip(VALUES, axs, strict=True))
    assert panels["bulk_unit_weight"].get_xlabel().endswith("(pcf)")
    assert panels["hydraulic_conductivity"].get_xlabel().endswith("(cm/s)")
    gray = [
        tuple(line.get_xdata())
        for line in panels["undrained_shear_strength"].lines
        if line.get_color() == "0.25" and len(line.get_xdata()) == 2
    ]
    assert pytest.approx(gray[0]) == (50 / 0.04788026, 150 / 0.04788026)


def test_box_summary_renders_for_every_panel():
    _, axs = grid(summary="box", display_units="SI")
    assert all(ax.patches for ax in axs[:2])
