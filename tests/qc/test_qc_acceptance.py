"""QC acceptance criteria (docs/data/qc.md §9), end to end."""

import hashlib
import warnings

import pandas as pd
import pytest

import hangtu as ht

from .conftest import DATA

GOOD = ("site_si", "site_us", "site_v404")

# Errors and warnings on qc_defects.ags, as (rule, line). Lines are in the
# test data README. A case that necessarily raises a second rule is marked.
EXPECTED = {
    ("L001", 21),  # BH5: LOCA_GL blank
    ("L002", 21),  # BH5: no coordinates
    ("L003", 21),  # BH5: LOCA_FDEP blank
    ("L004", 27),  # HORN_INCL 80
    ("L005", 20),  # BH4 8 m above its neighbors
    ("L007", None),  # BH1-BH3 NAVD88, BH4 NGVD29
    ("G001", 21),  # BH5 has ISPT and no GEOL
    ("G002", 34),  # BH1: 2.50 to 3.00 missing
    ("G002", 36),  # BH2: log stops 0.50 m short of LOCA_FDEP
    ("G003", 39),  # BH3: 3.50 to 4.00 in two layers
    ("D001", 48),  # SAMP base above top
    ("D002", 59),  # ISPT_TOP -0.50
    ("D003", 66),  # ISPT_TOP 1.00 m below LOCA_FDEP
    ("D004", 61),  # ISPT in BH1's gap
    ("D004", 59),  # cascade of D002: above the top of the log
    ("D004", 66),  # cascade of D003: below the bottom of the log
    ("D007", 85),  # SPEC_DPTH 0.30 m below its sample
    ("S001", 60),  # ISPT_REP "hard"
    ("S001", 70),  # ISPT_REP "50/76 ft": a unit that isn't accepted
    ("S002", 62),  # N 150
    ("S002", 71),  # N 126, a complete test ("41,81,57,75/113 N=126")
    ("S004", 63),  # N 20, blows 19
    ("S005", 64),  # N60 30, computed 25
    ("A001", 81),  # LL 30 < PL 35
    ("A002", 82),  # PI 25, LL - PL 30
    ("A003", 83),  # LL 8
    ("P001", 106),  # curve rises at 0.425 mm
    ("P002", 100),  # GRAT_PERP 104
    ("P003", 93),  # fractions sum to 94
    ("K001", 116),  # PTST_K 0
    ("K001", 122),  # FGHG_IPRM 5 m/s
    ("C001", 40),  # GEOL_DESC blank
    ("C001", 21),  # cascade of L001 and L003: BH5's required LOCA fields
    ("B001", 128),  # LDEN 2.00 / 1.20 = 1.667, not 1.80
    ("B002", 129),  # LDEN_DDEN 1.90 above LDEN_BDEN 1.80
    ("B003", 130),  # LDEN_BDEN 19.5: kN/m3 written as Mg/m3
    ("B003", 137),  # LPDN_PDEN 26.5
    ("X001", 156),  # TRET_BVAL 0.90
    ("X002", 158),  # CU stage with TRET_PWPF blank
    ("X003", 159),  # TRET_DEVF -20 in a CU stage
    ("X004", 160),  # TRET_PWPF 410 above TRET_CELL 400
    ("X005", 149),  # a CU test with two stages
    ("X005", 169),  # a TRIG with no TRIT rows
    ("X006", 157),  # TRET_CONP 150, cell 400 less back 300 is 100
}
# Info findings seeded on qc_defects.ags (C002 also lists absent headings).
EXPECTED_INFO = {
    ("L006", None),  # cascade of L007: holes name different datums
    ("D005", 52),
    ("D008", 84),  # SPEC_DPTH 0.05 m below its sample: rounding
    ("S003", None),
    ("A004", 84),
    ("P004", 108),
    ("B004", 138),  # LPDN_PDEN #2.65
}


def _pairs(findings):
    return {
        (rule_id, None if pd.isna(line) else int(line))
        for rule_id, line in zip(
            findings["rule_id"], findings["source_line"], strict=True
        )
    }


@pytest.fixture(scope="module")
def defects_report(projects):
    return projects["qc_defects"].qc()


# 1. One test per rule ---------------------------------------------------------------


def test_1_exact_errors_and_warnings(defects_report):
    found = defects_report.findings
    assert _pairs(found.query("severity != 'info'")) == EXPECTED


def test_1_info_findings(defects_report):
    info = defects_report.findings.query("severity == 'info'")
    assert _pairs(info.query("rule_id != 'C002'")) == EXPECTED_INFO
    assert ("LOCA", "LOCA_TYPE") in set(
        zip(info["group"], info["heading"], strict=True)
    )


def test_1_every_computed_rule_has_a_case(defects_report):
    raised = set(defects_report.findings["rule_id"])
    computed = {
        rule_id
        for rule_id in defects_report.rules["rule_id"]
        if rule_id[0] in "LGDSAPKBXC"
    }
    # G004 needs a geology map, so its case is joins.ags with strata.csv
    # (tests/qc/test_geology.py), not the defects file.
    assert computed - {"G004"} <= raised


def test_1_findings_carry_group_hole_and_heading(defects_report):
    found = defects_report.findings
    columns = ["rule_id", "source_line", "group", "loca_id", "heading"]
    rows = set(found[columns].itertuples(index=False, name=None))
    assert ("D003", 66, "ISPT", "BH3", "ISPT_TOP") in rows
    assert ("K001", 122, "FGHG", "BH4", "FGHG_IPRM") in rows
    assert ("G002", 36, "GEOL", "BH2", "GEOL_BASE") in rows


def _vlog_project(tmp_path):
    text = (DATA / "site_si.ags").read_text(encoding="utf-8")
    text = text.replace(
        '"HEADING","LOCA_ID","LOCA_TYPE"', '"HEADING","LOCA_ID","LOCA_ID"', 1
    )
    path = tmp_path / "duplicate.ags"
    path.write_text(text, encoding="utf-8", newline="")
    return ht.Project.from_ags(path, db=tmp_path / "duplicate.sqlite")


def test_1_ingest_rules_appear_in_the_report(projects, tmp_path):
    findings = pd.concat(
        [
            projects["defects"].qc().findings,
            projects["site_v404"].qc().findings,
            _vlog_project(tmp_path).qc().findings,
        ]
    )
    raised = set(findings["rule_id"])
    for rule_id in ("VLOG", "V000", "M001", "U001", "U002", "U003", "U004", "T001"):
        assert rule_id in raised, rule_id
    assert any(rule_id[0] == "V" and rule_id[1].isdigit() for rule_id in raised)
    # Filled from the line where it has a row: T001 is on an LNMC row.
    wet = findings.query("rule_id == 'T001'").iloc[0]
    assert wet["loca_id"] == "BH2"
    assert pd.notna(wet["depth"])
    # A unit finding is on the UNIT line, which has no row.
    assert findings.query("rule_id == 'U001'")["loca_id"].isna().all()


# 2. Good files ----------------------------------------------------------------------


@pytest.mark.parametrize("name", GOOD)
def test_2_good_files_have_no_errors_or_warnings(projects, name):
    found = projects[name].qc().findings
    assert found.query("severity != 'info'").empty
    # No L006 (LOCA_DATM names the datum), and no X or C001 (M11 a, AC 9): the
    # C002 is TRET_PWPF, blank on purpose in BH2-U2's stage 2.
    allowed = {"S003", "A004", "B004", "C002"}
    allowed |= {"site_v404": {"M001"}, "site_us": {"U002"}}.get(name, set())
    assert set(found["rule_id"]) <= allowed


# 3. Twin files ----------------------------------------------------------------------


def test_3_twins_give_the_same_findings(tmp_path):
    def findings(name):
        project = ht.Project.from_ags(
            DATA / f"{name}.ags", db=tmp_path / f"{name}.sqlite", display_units="SI"
        )
        found = project.qc().findings.query("rule_id != 'U002'")
        columns = ["rule_id", "severity", "group", "loca_id", "heading", "depth"]
        return found[columns].reset_index(drop=True)

    pd.testing.assert_frame_equal(
        findings("site_si"), findings("site_us"), check_exact=False, rtol=1e-9
    )


# 5. Thresholds and overrides --------------------------------------------------------


def test_5_feet_and_meters_give_the_same_findings(projects):
    p = projects["qc_defects"]
    in_feet = p.qc(rules={"G002": {"thresholds": {"depth_tolerance": "0.05 ft"}}})
    in_meters = p.qc(rules={"G002": {"thresholds": {"depth_tolerance": "0.01524 m"}}})
    columns = ["rule_id", "source_line", "message"]
    pd.testing.assert_frame_equal(
        in_feet.findings.query("rule_id == 'G002'")[columns],
        in_meters.findings.query("rule_id == 'G002'")[columns],
    )


def test_5_disabled_rule_and_severity_override(projects):
    report = projects["qc_defects"].qc(
        rules={"G003": {"enabled": False}, "L005": {"severity": "error"}}
    )
    assert "G003" not in set(report.findings["rule_id"])
    rules = report.rules.set_index("rule_id")
    assert not rules.loc["G003", "enabled"]
    assert pd.isna(rules.loc["G003", "records_checked"])
    assert set(report.findings.query("rule_id == 'L005'")["severity"]) == {"error"}
    summary = report.summary().set_index("rule_id")
    assert summary.loc["L005", "severity"] == "error"


def test_5_override_file_and_dict_give_the_same_report(projects, tmp_path):
    path = tmp_path / "site_x_qc.yaml"
    path.write_text(
        "rules:\n  G002:\n    thresholds:\n      depth_tolerance: 0.05 ft\n"
        "  A004:\n    enabled: false\n",
        encoding="utf-8",
    )
    as_dict = {
        "G002": {"thresholds": {"depth_tolerance": "0.05 ft"}},
        "A004": {"enabled": False},
    }
    p = projects["qc_defects"]
    from_file, from_dict = p.qc(rules=path), p.qc(rules=as_dict)
    pd.testing.assert_frame_equal(from_file.findings, from_dict.findings)
    pd.testing.assert_frame_equal(from_file.rules, from_dict.rules)


# 6. Rules table ---------------------------------------------------------------------


def test_6_rules_table(projects, defects_report):
    rules = defects_report.rules.set_index("rule_id")
    yaml_rules = set(ht.qc._settings.load().defaults)
    assert yaml_rules <= set(rules.index)
    assert (rules["overridden"] == "no").all()
    overridden = projects["qc_defects"].qc(
        rules={"L005": {"thresholds": {"neighbor_count": 3}}}
    )
    assert overridden.rules.set_index("rule_id").loc["L005", "overridden"] == "yes"
    # qc_defects.ags has no FGHS or IPRG; K001 checked its PTST and FGHG rows.
    assert rules.loc["K001", "records_checked"] == 2
    # site_si.ags has no HORN: L004 checked nothing.
    site = projects["site_si"].qc().rules.set_index("rule_id")
    assert site.loc["L004", "records_checked"] == 0


# 7. CSV ----------------------------------------------------------------------------


@pytest.mark.parametrize(("system", "unit"), [("US", "ft"), ("SI", "m")])
def test_7_csv(tmp_path, system, unit):
    project = ht.Project.from_ags(
        DATA / "qc_defects.ags", db=tmp_path / "p.sqlite", display_units=system
    )
    report = project.qc()
    report.to_csv(tmp_path / "qc_report.csv")
    back = pd.read_csv(tmp_path / "qc_report.csv")
    assert len(back) == len(report.findings)
    assert list(back.columns) == list(report.findings.columns)
    assert set(back["depth_unit"].dropna()) == {unit}
    d003 = back.query("rule_id == 'D003'").iloc[0]
    assert d003["depth"] == pytest.approx(7.0 / (0.3048 if unit == "ft" else 1))
    rules_file = tmp_path / "qc_report_rules.csv"
    first = rules_file.read_text(encoding="utf-8").splitlines()[0]
    assert first == "# file: qc_defects.ags"
    rules = pd.read_csv(rules_file, comment="#")
    assert list(rules["rule_id"]) == list(report.rules["rule_id"])


# 9. Read-only and quiet -------------------------------------------------------------


def test_9_read_only_and_quiet(tmp_path, capsys):
    db = tmp_path / "p.sqlite"
    project = ht.Project.from_ags(DATA / "qc_defects.ags", db=db)
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    capsys.readouterr()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        project.qc()
        project.qc(rules={"G002": {"thresholds": {"depth_tolerance": "0.05 ft"}}})
        project.diff("ISPT")
        project.diff("ISPT", changed_only=True)
    assert capsys.readouterr() == ("", "")
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before


def test_9_running_twice_gives_the_same_report(projects):
    first, second = projects["qc_defects"].qc(), projects["qc_defects"].qc()
    pd.testing.assert_frame_equal(first.findings, second.findings)
    pd.testing.assert_frame_equal(first.rules, second.rules)
