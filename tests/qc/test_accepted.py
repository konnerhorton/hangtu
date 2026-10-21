"""Accepted findings (qc.md §3.4; qc-review acceptance criteria)."""

import textwrap

import pytest

from hangtu import qc
from hangtu.errors import HangtuError, UnitsError
from hangtu.qc._accepted import read_accepted
from hangtu.qc._settings import load

ENTRIES = [
    {"rule_id": "L005", "reason": "Valley site."},
    {"rule_id": "D007", "loca_id": "BH4", "depth": "4.75 m", "reason": "Checked."},
]
YAML = """\
- rule_id: L005
  reason: Valley site.
- rule_id: D007
  loca_id: BH4
  depth: 4.75 m
  reason: Checked.
"""


def _read(source):
    return read_accepted(source, load())


# Reading ----------------------------------------------------------------------------


def test_file_list_and_top_key_read_the_same(tmp_path):
    bare = tmp_path / "bare.yaml"
    bare.write_text(YAML, encoding="utf-8")
    keyed = tmp_path / "keyed.yaml"
    keyed.write_text("accepted:\n" + textwrap.indent(YAML, "  "), encoding="utf-8")
    from_list = _read(ENTRIES)
    assert _read(bare).entries == from_list.entries
    assert _read(keyed).entries == from_list.entries
    assert _read({"accepted": ENTRIES}).entries == from_list.entries
    assert _read(bare).source == str(bare)
    assert from_list.source == "list"


def test_entry_fields():
    entry = _read(ENTRIES).entries[1]
    assert (entry.position, entry.rule_id, entry.loca_id, entry.depth) == (
        2,
        "D007",
        "BH4",
        "4.75 m",
    )
    assert entry.group is None and entry.heading is None
    assert entry.depth_m == pytest.approx(4.75)


def test_depth_in_feet_is_read_in_meters():
    entry = _read([{**ENTRIES[1], "depth": "41.5 ft"}]).entries[0]
    assert entry.depth == "41.5 ft"
    assert entry.depth_m == pytest.approx(12.6492)


def test_nothing_given(tmp_path):
    empty = tmp_path / "empty.yaml"
    empty.write_text("", encoding="utf-8")
    assert _read(None).entries == ()
    assert _read(None).source == ""
    assert _read(empty).entries == ()
    assert _read([]).entries == ()


def test_single_v_rule_is_accepted():
    assert _read([{"rule_id": "V10a", "reason": "Known."}]).entries[0].rule_id == "V10a"


# Errors (Decision 6) ----------------------------------------------------------------


def test_missing_file(tmp_path):
    with pytest.raises(
        FileNotFoundError, match=r"No QC accepted findings file at .*nope\.yaml"
    ):
        _read(tmp_path / "nope.yaml")


def test_bad_yaml(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("- rule_id: [\n", encoding="utf-8")
    with pytest.raises(HangtuError, match=r"isn't valid YAML at line"):
        _read(path)


@pytest.mark.parametrize("given", [{"rule_id": "L005"}, 5])
def test_not_a_list(given):
    with pytest.raises(HangtuError, match=r"must be a list of entries"):
        _read(given)


def test_entry_not_a_mapping():
    with pytest.raises(HangtuError, match=r"accepted entry 2 must be a mapping"):
        _read([ENTRIES[0], "L005"])


@pytest.mark.parametrize("reason", [None, "", "  "])
def test_missing_reason(reason):
    entry = {"rule_id": "L005"}
    if reason is not None:
        entry["reason"] = reason
    with pytest.raises(HangtuError, match=r"accepted entry 2 \(L005\) needs a reason"):
        _read([ENTRIES[0], entry])


def test_missing_rule_id():
    with pytest.raises(
        HangtuError, match=r"accepted entry 1 \(no rule_id\) needs a rule_id"
    ):
        _read([{"reason": "Checked."}])


def test_unknown_key():
    with pytest.raises(
        HangtuError,
        match=r"accepted entry 1 \(L005\) has an unknown key 'line'\. The keys are "
        r"rule_id, loca_id, group, heading, depth, reason\.",
    ):
        _read([{"rule_id": "L005", "line": 57, "reason": "Checked."}])


def test_unknown_rule():
    with pytest.raises(
        HangtuError,
        match=r"accepted entry 1 \(G009\): QC rule 'G009' doesn't exist\. "
        r"The rules are .*G002",
    ):
        _read([{"rule_id": "G009", "reason": "Checked."}])


def test_v_star_is_not_accepted():
    with pytest.raises(
        HangtuError, match=r"accepted entry 1 \(V\*\): V\* can't be accepted"
    ):
        _read([{"rule_id": "V*", "reason": "Checked."}])


def test_depth_without_hole():
    with pytest.raises(
        HangtuError, match=r"accepted entry 1 \(D007\) gives a depth without a loca_id"
    ):
        _read([{"rule_id": "D007", "depth": "4.75 m", "reason": "Checked."}])


@pytest.mark.parametrize("depth", [4.75, "4.75"])
def test_depth_without_unit(depth):
    with pytest.raises(
        UnitsError, match=r"accepted entry 1 \(D007\): depth .* needs a unit"
    ):
        _read([{**ENTRIES[1], "depth": depth}])


def test_depth_not_a_length():
    with pytest.raises(
        UnitsError, match=r"accepted entry 1 \(D007\): depth '4.75 kPa' isn't a length"
    ):
        _read([{**ENTRIES[1], "depth": "4.75 kPa"}])


def test_errors_are_raised_before_any_rule_runs(projects, monkeypatch):
    def fail(*args):
        raise AssertionError("a rule ran")

    monkeypatch.setitem(qc.RULES, "L001", fail)
    with pytest.raises(HangtuError, match=r"accepted entry 1"):
        qc.run(projects["qc_defects"]._path, accepted=[{"rule_id": "L005"}])
