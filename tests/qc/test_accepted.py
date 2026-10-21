"""Accepted findings (qc.md §3.4; qc-review acceptance criteria)."""

import textwrap

import pandas as pd
import pytest

import hangtu as ht
from hangtu import qc
from hangtu.errors import HangtuError, UnitsError
from hangtu.qc._accepted import read_accepted
from hangtu.qc._settings import load

from .conftest import DATA

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


# Matching (AC 1) --------------------------------------------------------------------


def _accepted(report):
    """(rule_id, source line, reason) of each accepted finding."""
    rows = report.findings.query("accepted")
    return sorted(
        zip(
            rows["rule_id"],
            rows["source_line"].astype(object),
            rows["reason"],
            strict=True,
        )
    )


@pytest.fixture(scope="module")
def defects(projects):
    return projects["qc_defects"]


def test_rule_alone_accepts_the_rule_on_this_site(defects):
    report = defects.qc(accepted=[ENTRIES[0]])
    assert _accepted(report) == [("L005", 57, "Valley site.")]


@pytest.mark.parametrize("depth", ["4.75 m", "15.58 ft", "4.79 m", "4.71 m"])
def test_depth_matches_one_finding(defects, depth):
    entry = {"rule_id": "D007", "loca_id": "BH4", "depth": depth, "reason": "Ok."}
    assert _accepted(defects.qc(accepted=[entry])) == [("D007", 122, "Ok.")]


@pytest.mark.parametrize("depth", ["4.81 m", "4.69 m", "15.8 ft"])
def test_depth_beyond_the_tolerance_matches_nothing(defects, depth):
    entry = {"rule_id": "D007", "loca_id": "BH4", "depth": depth, "reason": "Ok."}
    report = defects.qc(accepted=[entry])
    assert _accepted(report) == []
    assert report.accepted["status"].tolist() == ["no match"]


def test_depth_matches_in_si_display_units(tmp_path):
    project = ht.Project.from_ags(
        DATA / "qc_defects.ags", db=tmp_path / "si.sqlite", display_units="SI"
    )
    entry = {"rule_id": "D007", "loca_id": "BH4", "depth": "15.58 ft", "reason": "Ok."}
    assert _accepted(project.qc(accepted=[entry])) == [("D007", 122, "Ok.")]


def test_group_limits_the_entry(defects):
    report = defects.qc(
        accepted=[
            {"rule_id": "D004", "group": "SAMP", "reason": "Not this group."},
            {"rule_id": "D004", "group": "ISPT", "reason": "SPT below the log."},
        ]
    )
    assert [line for _, line, _ in _accepted(report)] == [96, 98, 103]
    assert report.accepted["matches"].tolist() == [0, 3]


def test_hole_and_heading_must_equal(defects):
    report = defects.qc(
        accepted=[
            {"rule_id": "L005", "loca_id": "BH1", "reason": "Wrong hole."},
            {"rule_id": "L005", "loca_id": "bh4", "reason": "Case matters."},
            {"rule_id": "D007", "heading": "SPEC_DPTH", "reason": "Lab rounding."},
        ]
    )
    assert _accepted(report) == [("D007", 122, "Lab rounding.")]


# The report (AC 2, AC 3, AC 4) -------------------------------------------------------


def test_accepted_findings_keep_their_severity(defects):
    plain = defects.qc().findings
    report = defects.qc(accepted=ENTRIES)
    found = report.findings
    assert found["severity"].tolist() == plain["severity"].tolist()
    accepted = found.query("accepted")
    assert accepted["severity"].tolist() == ["warning", "warning"]
    assert accepted["reason"].tolist() == ["Checked.", "Valley site."]  # D007, L005
    assert found.query("not accepted")["reason"].isna().all()


def test_summary_counts_open_and_accepted(defects):
    summary = defects.qc(accepted=ENTRIES).summary().set_index("rule_id")
    assert (summary["open"] + summary["accepted"] == summary["count"]).all()
    assert summary.loc["L005", ["count", "open", "accepted"]].tolist() == [1, 0, 1]
    assert summary.loc["D007", ["count", "open", "accepted"]].tolist() == [1, 0, 1]
    assert summary.loc["D004", "accepted"] == 0


def test_report_accepted_table(defects):
    report = defects.qc(
        accepted=[*ENTRIES, {"rule_id": "G003", "loca_id": "BH1", "reason": "Old."}],
        rules={"S003": {"enabled": False}},
    )
    table = report.accepted
    assert list(table.columns) == [
        "rule_id",
        "loca_id",
        "group",
        "heading",
        "depth",
        "reason",
        "matches",
        "status",
    ]
    assert table["depth"].tolist()[1] == "4.75 m"
    assert table["matches"].tolist() == [1, 1, 0]
    assert table["status"].tolist() == ["matched", "matched", "no match"]
    assert report.source["accepted"] == "list"


def test_entry_for_a_disabled_rule(defects):
    report = defects.qc(accepted=[ENTRIES[0]], rules={"L005": {"enabled": False}})
    assert report.accepted["status"].tolist() == ["rule disabled"]
    assert report.accepted["matches"].tolist() == [0]


def test_broad_entry_behind_a_specific_one(defects):
    report = defects.qc(
        accepted=[
            {"rule_id": "L005", "loca_id": "BH4", "reason": "Specific."},
            {"rule_id": "L005", "reason": "Broad."},
        ]
    )
    assert _accepted(report) == [("L005", 57, "Specific.")]
    assert report.accepted["matches"].tolist() == [1, 1]
    assert report.accepted["status"].tolist() == ["matched", "matched"]


def test_file_and_list_give_the_same_report(defects, tmp_path):
    path = tmp_path / "accepted.yaml"
    path.write_text(YAML, encoding="utf-8")
    from_file = defects.qc(accepted=path)
    from_list = defects.qc(accepted=ENTRIES)
    pd.testing.assert_frame_equal(from_file.findings, from_list.findings)
    pd.testing.assert_frame_equal(from_file.accepted, from_list.accepted)
    assert from_file.source["accepted"] == str(path)


# Printed summary and CSV (AC 2, AC 3, AC 6) ------------------------------------------

REVIEW = [
    ENTRIES[0],
    {"rule_id": "D004", "loca_id": "BH1", "reason": "SPT in the log's gap."},
    {"rule_id": "G003", "loca_id": "BH1", "reason": "Fixed in revision B."},
]


def test_printed_summary_counts_open_and_accepted(defects):
    report = defects.qc(accepted=REVIEW)
    lines = repr(report).splitlines()
    open_ = report.findings.query("not accepted")["severity"].value_counts()
    assert lines[1] == (
        f"  open: {open_['error']} errors, {open_['warning']} warnings, "
        f"{open_['info']} info · accepted: 3"
    )
    by_rule = {line.split()[1]: line for line in lines[2:-2]}
    # D004 has three findings, two of them in BH1.
    assert by_rule["D004"].endswith("  1   (+2 accepted)")
    # A rule with only accepted findings is still listed.
    assert by_rule["L005"].endswith("  0   (+1 accepted)")
    assert by_rule["D007"].endswith("  1")
    assert lines[-2] == "  1 accepted entry matches no finding: report.accepted"
    assert lines[-1].startswith("  findings: report.findings")
    # Open counts line up in one column.
    counts = [line.split("(+")[0].rstrip() for line in by_rule.values()]
    assert len({line.rindex(" ") for line in counts}) == 1


def test_printed_summary_without_stale_entries(defects):
    lines = repr(defects.qc(accepted=ENTRIES)).splitlines()
    assert not any("match no finding" in line for line in lines)
    assert "entries match" not in repr(defects.qc(accepted=REVIEW))
    stale = [*REVIEW, {"rule_id": "G002", "loca_id": "BH9", "reason": "Old."}]
    assert "  2 accepted entries match no finding: report.accepted" in repr(
        defects.qc(accepted=stale)
    )


def test_csv_has_accepted_columns_and_header(defects, tmp_path):
    path = tmp_path / "qc_report.csv"
    review = tmp_path / "review.yaml"
    review.write_text(YAML, encoding="utf-8")
    report = defects.qc(accepted=[*REVIEW, *ENTRIES[1:]])
    report.to_csv(path)
    back = pd.read_csv(path)
    assert list(back.columns) == list(report.findings.columns)
    assert back["accepted"].tolist() == report.findings["accepted"].tolist()
    accepted = back.query("accepted")
    assert sorted(accepted["reason"]) == sorted(
        report.findings.query("accepted")["reason"]
    )
    rules_text = (tmp_path / "qc_report_rules.csv").read_text(encoding="utf-8")
    assert "# accepted: list, 4 entries, 1 match no finding\n" in rules_text
    defects.qc(accepted=review).to_csv(path)
    rules_text = (tmp_path / "qc_report_rules.csv").read_text(encoding="utf-8")
    assert f"# accepted: {review}, 2 entries, 0 match no finding\n" in rules_text
    assert len(pd.read_csv(tmp_path / "qc_report_rules.csv", comment="#"))


def test_csv_without_accepted_entries_has_no_accepted_line(defects, tmp_path):
    path = tmp_path / "qc_report.csv"
    defects.qc().to_csv(path)
    rules_text = (tmp_path / "qc_report_rules.csv").read_text(encoding="utf-8")
    assert "# accepted" not in rules_text
