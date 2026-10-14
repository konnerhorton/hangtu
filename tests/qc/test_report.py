import pandas as pd
import pytest

import hangtu as ht
from hangtu.qc._report import FINDING_COLUMNS, RULE_COLUMNS

from .conftest import DATA


@pytest.fixture(scope="module")
def defects(projects):
    return projects["defects"].qc()


def test_columns(defects):
    assert list(defects.findings.columns) == FINDING_COLUMNS
    assert list(defects.rules.columns) == RULE_COLUMNS


def test_ingest_findings_appear_with_their_lines(defects):
    found = defects.findings
    rows = set(zip(found["rule_id"], found["group"], found["source_line"], strict=True))
    assert ("U001", "LOCA", 54) in rows
    assert ("T001", "LNMC", 105) in rows
    assert ("V10c", "LLPL", 96) in rows
    assert ("V000", "TRAN", 11) in rows


def test_ingest_finding_gets_hole_depth_and_value_from_its_line(defects):
    wet = defects.findings.query("rule_id == 'T001'").iloc[0]
    assert wet["loca_id"] == "BH2"
    assert wet["depth"] == pytest.approx(2.00 / 0.3048)  # SPEC_DPTH 2.00 m, in ft
    assert wet["depth_unit"] == "ft"
    assert wet["heading"] == "LNMC_MC"
    assert wet["value"] == "wet"
    # A unit finding points at the UNIT line, which has no row.
    unit = defects.findings.query("rule_id == 'U001'").iloc[0]
    assert pd.isna(unit["loca_id"])
    assert pd.isna(unit["depth"])
    assert pd.isna(unit["depth_unit"])


def test_findings_sorted_by_severity_rule_and_line(defects):
    found = defects.findings
    order = {"error": 0, "warning": 1, "info": 2}
    assert list(found["severity"].map(order)) == sorted(found["severity"].map(order))
    errors = list(found.query("severity == 'error'")["rule_id"])
    assert errors == ["U001", "U004", "V7", "V9", "V9", "V10c", "V10c", "V18"]


def test_severity_override_changes_findings_and_summary(projects):
    report = projects["defects"].qc(rules={"U002": {"severity": "warning"}})
    assert set(report.findings.query("rule_id == 'U002'")["severity"]) == {"warning"}
    summary = report.summary().set_index("rule_id")
    assert summary.loc["U002", "severity"] == "warning"
    rule = report.rules.set_index("rule_id").loc["U002"]
    assert rule["severity"] == "warning"
    assert rule["overridden"] == "yes"


def test_disabled_rule_raises_nothing(projects):
    report = projects["defects"].qc(rules={"T001": {"enabled": False}})
    assert "T001" not in set(report.findings["rule_id"])
    rule = report.rules.set_index("rule_id").loc["T001"]
    assert not rule["enabled"]
    assert rule["findings"] == 0


def test_v_star_and_a_single_v_rule(projects):
    report = projects["defects"].qc(
        rules={"V*": {"severity": "warning"}, "V9": {"severity": "info"}}
    )
    severity = report.findings.groupby("rule_id")["severity"].agg(set)
    assert severity["V10c"] == {"warning"}
    assert severity["V9"] == {"info"}
    assert severity["V000"] == {"warning"}  # V000 starts with V too


def test_rules_table_lists_v_rules_found_after_v_star(defects):
    ids = list(defects.rules["rule_id"])
    assert ids[:5] == ["V*", "V7", "V9", "V10c", "V18"]
    rules = defects.rules.set_index("rule_id")
    assert rules.loc["V10c", "title"] == "python-ags4 rule 10c"
    assert rules.loc["V10c", "findings"] == 2
    assert rules.loc["V*", "severity"] == "as stored"
    assert pd.isna(rules.loc["U001", "records_checked"])  # ingest rule
    assert rules.loc["G002", "thresholds"] == "depth_tolerance = 0.01 m"


def test_threshold_shown_as_given(projects):
    report = projects["defects"].qc(
        rules={"G002": {"thresholds": {"depth_tolerance": "0.05 ft"}}}
    )
    rule = report.rules.set_index("rule_id").loc["G002"]
    assert rule["thresholds"] == "depth_tolerance = 0.05 ft"
    assert rule["overridden"] == "yes"


def test_summary_counts(defects):
    summary = defects.summary()
    assert list(summary.columns) == ["rule_id", "title", "severity", "count"]
    counts = dict(zip(summary["rule_id"], summary["count"], strict=True))
    assert counts["V9"] == 2
    assert counts["U001"] == 1
    assert summary["count"].sum() == len(defects.findings)


def test_source(defects, projects):
    source = defects.source
    assert source["file"] == "defects.ags"
    assert (
        source["sha256"]
        == projects["defects"].sql("select sha256 from meta_source").iloc[0, 0]
    )
    assert source["ags_version"] == "4.2"
    assert source["hangtu_version"]
    assert len(source["run_at"]) == len("2026-10-14T15:02:00+00:00")


def test_printed_summary(defects):
    text = repr(defects)
    lines = text.splitlines()
    assert lines[0].startswith("QC report: defects.ags (AGS 4.2), hangtu ")
    assert lines[1] == "  8 errors, 2 warnings, 2 info"
    assert lines[2].split() == [
        "error",
        "U001",
        "Unknown",
        "or",
        "ambiguous",
        "unit",
        "1",
    ]
    assert lines[-1].startswith("  findings: report.findings")
    # Counts line up in one column.
    assert len({line.rindex(" ") for line in lines[2:-1]}) == 1


def test_csv_round_trip(defects, tmp_path):
    path = tmp_path / "qc_report.csv"
    defects.to_csv(path)
    back = pd.read_csv(path)
    expected = defects.findings
    assert list(back.columns) == list(expected.columns)
    pd.testing.assert_frame_equal(
        back.astype(object).where(back.notna(), None),
        expected.astype(object).where(expected.notna(), None),
        check_dtype=False,
    )
    rules_path = tmp_path / "qc_report_rules.csv"
    lines = rules_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# file: defects.ags"
    assert any(line.startswith("# sha256: ") for line in lines)
    rules = pd.read_csv(rules_path, comment="#")
    assert list(rules["rule_id"]) == list(defects.rules["rule_id"])


def test_depth_in_si(tmp_path):
    project = ht.Project.from_ags(
        DATA / "defects.ags", db=tmp_path / "si.sqlite", display_units="SI"
    )
    wet = project.qc().findings.query("rule_id == 'T001'").iloc[0]
    assert wet["depth"] == pytest.approx(2.00)
    assert wet["depth_unit"] == "m"


def test_session_display_override_does_not_change_the_report(projects):
    ht.settings.display_overrides = {"length": "in"}
    wet = projects["defects"].qc().findings.query("rule_id == 'T001'").iloc[0]
    assert wet["depth_unit"] == "ft"


def test_min_fields_accepts_a_group_defined_in_the_file(projects):
    report = projects["site_si"].qc(min_fields={"XPPT": {"required": ["XPPT_RES"]}})
    assert report.findings is not None
