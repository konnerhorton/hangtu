"""P02 §12 acceptance criteria, against tests/data/spt.csv.

Counts are by hand from the CSV: 4 holes (BH-1 to BH-4) with 20 tests each,
every 5 ft from 2.5 to 97.5 ft. Energy ratio 82 % on BH-1 and BH-2 only.
- Refusals, 5: BH-1 92.5 ft and BH-2 87.5 ft (flagged; BH-2's N is blank);
  BH-3 77.5 and 97.5 ft and BH-4 97.5 ft (spt_refusal blank, penetration
  11, 6 and 16 in, under 18 in). BH-4 92.5 ft has 18 in: not a refusal.
- Blank N, not refusals, 2: BH-2 42.5 ft and BH-3 12.5 ft.
- N60: BH-3 has 20 - 2 refusals - 1 blank = 17 tests without an energy ratio,
  BH-4 has 20 - 1 = 19: 36 in all.
"""

from pathlib import Path

import numpy as np
import pytest

import hangtu as ht

DATA = Path(__file__).parents[1] / "data"
FT = 0.3048


def spt():
    return ht.read_csv(
        DATA / "spt.csv",
        units={"depth": "ft", "ground_level": "ft", "spt_penetration": "in"},
    )


def triangles(ax):
    found = [
        c.get_offsets().data
        for c in ax.collections
        if len(c.get_offsets()) and c.get_label().endswith(" >")
    ]
    return np.concatenate(found) if found else np.empty((0, 2))


def footnote(ax):
    (text,) = [t for t in ax.texts if t.get_text()[:1].isdigit()]
    return text.get_text().splitlines()


def test_n_counts_refusals_and_blanks(points):
    _, ax = ht.plot.spt_profile(spt())
    assert ax.ags_notes == {"nan": 2, "refusal": 5}
    assert len(points(ax)) == 78
    assert triangles(ax)[:, 0].tolist() == [100.0] * 5
    assert footnote(ax) == ["2 blank values not shown", "5 refusals, shown at N = 100"]
    assert ax.get_xlim() == (0.0, 120.0)
    assert ax.get_xlabel() == "SPT N"


def test_refusal_elevations():
    _, ax = ht.plot.spt_profile(spt())
    # Ground level minus depth: BH-1 112.4 - 92.5, BH-2 110.8 - 87.5,
    # BH-3 113.1 - 77.5 and - 97.5, BH-4 109.6 - 97.5.
    assert sorted(triangles(ax)[:, 1]) == pytest.approx(
        sorted([19.9, 23.3, 35.6, 15.6, 12.1])
    )


def test_n60_counts_tests_without_an_energy_ratio(points):
    _, ax = ht.plot.spt_profile(spt(), n="spt_n60")
    assert ax.ags_notes == {"nan": 2, "refusal": 5, "no_energy_ratio": 36}
    assert len(points(ax)) == 42
    assert footnote(ax) == [
        "2 blank values not shown",
        "5 refusals, shown at N60 = 100",
        "36 tests without an energy ratio not shown",
    ]
    # BH-1 at 2.5 ft: N = 8, ER = 82 -> 10.933 at elevation 109.9 ft.
    x, y = np.asarray(points(ax)).T
    assert x[np.isclose(y, 109.9)].tolist() == pytest.approx([8 * 82 / 60])


def test_n60_with_a_hammer_efficiency_for_the_rest(points):
    with pytest.warns(UserWarning, match="Energy ratio 60 %"):
        _, ax = ht.plot.spt_profile(spt(), n="spt_n60", hammer_efficiency=60)
    assert ax.ags_notes == {"nan": 2, "refusal": 5}
    assert len(points(ax)) == 78


def test_exclude_counts_refusals_not_shown(points):
    _, ax = ht.plot.spt_profile(spt(), refusal="exclude")
    assert ax.ags_notes == {"nan": 2, "refusal_excluded": 5}
    assert len(points(ax)) == 73
    assert len(triangles(ax)) == 0
    assert ax.get_xlim()[1] < 100


def test_units_in_the_legend_with_their_colors():
    _, ax = ht.plot.spt_profile(spt())
    legend = [t.get_text() for t in ax.get_legend().get_texts()]
    for unit in ["Fill", "Alluvial sand", "Glacial till", "Residual soil"]:
        assert unit in legend
    assert "refusal (5)" in legend


def test_us_and_si_agree(assert_us_si_equivalent):
    assert_us_si_equivalent(ht.plot.spt_profile, spt(), ("count", "length"))


def test_si_labels_and_depth():
    _, ax = ht.plot.spt_profile(spt(), vs="depth", display_units="SI")
    assert ax.get_ylabel() == "Depth (m)"
    assert ax.get_ylim()[1] == 0
    assert ax.get_ylim()[0] >= 97.5 * FT
