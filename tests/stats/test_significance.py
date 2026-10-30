"""The significance level as a judgment (docs/work/m15d-compare.md, Decision 8)."""

import textwrap

import pandas as pd
import pytest

import hangtu as ht
from hangtu.stats._significance import resolve

ALPHA = """\
significance_level:
  project: {significance_level: 0.05, reason: "the usual convention"}
"""


def write(tmp_path, text=ALPHA):
    path = tmp_path / "judgments.yaml"
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def test_the_argument_is_used_and_recorded():
    alpha, record = resolve(0.1, None, [], "compare()")
    assert alpha == 0.1
    assert record == {"significance_level": 0.1, "source": "argument"}


def test_judgments_gives_the_file_value_with_its_source_and_reason(tmp_path):
    # Criterion 9: the result records 0.05 and its source.
    path = write(tmp_path)
    alpha, record = resolve(None, ht.judgments(path), [], "compare()")
    assert alpha == 0.05
    assert record["source"] == str(path)
    assert record["reason"] == "the usual convention"
    assert len(record["sha256"]) == 64


def test_a_frame_carries_the_project_file(tmp_path):
    path = write(tmp_path)
    frame = pd.DataFrame({"x": [1.0]})
    frame.attrs["judgments_file"] = str(path)
    alpha, record = resolve(None, None, [pd.DataFrame(), frame], "compare()")
    assert alpha == 0.05
    assert record["source"] == str(path)


def test_the_argument_over_a_file_value_warns(tmp_path):
    # Criterion 9: the argument wins, with a warning.
    with pytest.warns(UserWarning, match="significance_level= replaces the one in"):
        alpha, record = resolve(0.1, ht.judgments(write(tmp_path)), [], "compare()")
    assert alpha == 0.1
    assert record["source"] == "argument"


def test_missing_everywhere_is_an_error_showing_the_entry():
    # Criterion 9.
    with pytest.raises(ht.HangtuError) as error:
        resolve(None, None, [], "compare()")
    text = str(error.value)
    assert "compare() tests at the significance level" in text
    assert "no default (SPEC §4)" in text
    assert "significance_level:\n  project: {significance_level: 0.05" in text
    assert "merge and concat" not in text


def test_missing_with_a_frame_hints_at_dropped_attrs():
    with pytest.raises(ht.HangtuError, match=r"merge and concat drop df\.attrs"):
        resolve(None, None, [pd.DataFrame()], "compare()")


def test_a_file_without_it_is_named(tmp_path):
    path = write(
        tmp_path,
        "specific_gravity:\n  by: geology_unit\n"
        "  values:\n    Fill: {specific_gravity: 2.65}\n",
    )
    with pytest.raises(ht.HangtuError, match=r"judgments\.yaml' has no significance"):
        resolve(None, ht.judgments(path), [], "compare_groups()")


@pytest.mark.parametrize("value", [0, 1, -0.1, 1.5, float("nan"), True, "0.05"])
def test_an_argument_outside_0_to_1_is_an_error(value):
    # Criterion 9: 0 or 1 is an error.
    with pytest.raises(ht.HangtuError, match="between 0 and 1"):
        resolve(value, None, [], "compare()")


def test_an_argument_outside_the_plausible_range_warns():
    # Criterion 9: 0.3 warns.
    with pytest.warns(UserWarning, match=r"0\.3 is outside 0\.001-0\.2"):
        assert resolve(0.3, None, [], "compare()")[0] == 0.3
