"""compare()'s plain-English note (m15d-compare, Decision 9, AC 2)."""

import numpy as np
import pytest

import hangtu as ht
from hangtu.stats._note import INDEPENDENCE

LOW = list(np.arange(10.0, 20.0))
HIGH = list(np.arange(15.0, 25.0))
STEADY = [9.5, 9.6, 9.7, 9.8, 9.9, 10.1, 10.2, 10.3, 10.4, 10.5]
SPLIT = [9.0, 9.2, 9.4, 9.6, 9.8, 20, 20.5, 21, 21.5, 22]


def _notes(first, second, **kwargs):
    kwargs.setdefault("significance_level", 0.05)
    return ht.stats.compare(first, second, units="kPa", **kwargs).notes


def test_helsel_disagrees_rank_only(helsel):
    # AC 2: Welch p 0.977, Brunner-Munzel p 0.0403 at α = 0.05.
    notes = _notes(*helsel)
    assert notes[0] == "Welch's t-test doesn't find that the means differ (p = 0.977)."
    assert notes[1] == (
        "The Brunner-Munzel test finds that values in first tend to exceed those "
        "in second (p = 0.0403)."
    )
    assert notes[2].startswith(
        "The two tests disagree: values in first tend to exceed those in second "
        "but the means don't clearly differ."
    )
    assert "log=True compares geometric means" in notes[2]
    assert notes[2].endswith("Look at the values (P07).")
    assert notes[3] == INDEPENDENCE


def test_on_a_log_scale_the_note_doesnt_suggest_it(helsel):
    notes = _notes(*helsel, log=True)
    assert "geometric means don't clearly differ" in notes[2]
    assert "log=True" not in notes[2]


def test_both_find_a_difference():
    notes = _notes(LOW, HIGH)
    assert (
        notes[0]
        == "Welch's t-test finds the means differ, second's higher (p = 1.67e-03)."
    )
    assert notes[1].startswith(
        "The Brunner-Munzel test finds that values in second tend to exceed "
        "those in first"
    )
    assert notes[2].startswith(
        "Both tests find a difference: the difference in means, first - second, "
        "is -5.00 kPa (95 % interval"
    )
    assert "a value in first exceeds one in second with probability 0.125" in notes[2]


def test_neither_finds_a_difference_and_says_what_that_doesnt_mean():
    notes = _notes(list(np.arange(1.0, 11.0)), list(np.arange(1.5, 11.5)))
    assert notes[0].startswith("Welch's t-test doesn't find")
    assert notes[1].startswith(
        "The Brunner-Munzel test doesn't find that values in first tend to "
        "exceed those in second, or the reverse"
    )
    assert notes[2].startswith(
        "This doesn't show the groups are the same: the difference in means, "
        "first - second, could be anywhere from -3."
    )
    assert notes[2].endswith("kPa (95 % interval).")
    assert not any("are the same" in n and "doesn't" not in n for n in notes)


def test_welch_only_points_to_extreme_values():
    notes = _notes(STEADY, SPLIT)
    assert notes[0].startswith("Welch's t-test finds the means differ, second's higher")
    assert notes[1].startswith("The Brunner-Munzel test doesn't find")
    assert notes[2] == (
        "The two tests disagree: the means differ but neither group's values tend "
        "to exceed the other's. This is often one or two extreme values moving a "
        "mean. Look at the values (P07)."
    )


def test_the_conclusions_follow_the_significance_level(helsel):
    # α changes the note's conclusion, not the p-values.
    notes = _notes(*helsel, significance_level=0.01)
    assert notes[1].startswith("The Brunner-Munzel test doesn't find")
    assert notes[2].startswith("This doesn't show the groups are the same")
    assert "(99 % interval)" in notes[2]


@pytest.mark.parametrize(
    ("first", "second"),
    [([2.0] * 5, [3.0] * 5), (LOW, HIGH), ([1, 2, 3, 4, 5], [4, 5, 6, 7, 8])],
)
def test_the_independence_line_is_always_there(first, second):
    assert INDEPENDENCE in _notes(first, second)


def test_the_note_comes_first_in_the_text(helsel):
    text = str(ht.stats.compare(*helsel, significance_level=0.05))
    lines = text.splitlines()
    start = lines.index(
        "Welch's t-test doesn't find that the means differ (p = 0.977)."
    )
    assert lines[start - 1] == "Significance level 0.05 (argument)"
