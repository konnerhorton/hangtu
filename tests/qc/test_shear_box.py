"""Shear box rules H001 to H003 (qc.md §4.14; m17a AC 13)."""

from .conftest import found


def test_h_rules_at_their_lines(projects):
    report = projects["qc_defects"].qc()
    assert found(report, "H001") == [("BH1", "SHBT_RES", 200)]
    assert found(report, "H002") == [("BH1", None, 201)]
    assert found(report, "H003") == [("BH1", "SHBT_NORM", 202)]
    severity = report.rules.set_index("rule_id")["severity"]
    assert set(severity[["H001", "H003"]]) == {"error"}
    assert severity["H002"] == "warning"


def test_h001_names_both_values(projects):
    report = projects["qc_defects"].qc()
    message = report.findings.query("rule_id == 'H001'")["message"].iloc[0]
    assert message.startswith("SHBT_RES 60 kPa")
    assert "stage 1" in message
    assert "SHBT_PEAK 50 kPa" in message


def test_records_checked(projects):
    checked = projects["qc_defects"].qc().rules.set_index("rule_id")["records_checked"]
    # Three stages; H001 checks the two with both stresses, H003 all three.
    assert checked[["H001", "H002", "H003"]].tolist() == [2, 3, 3]


def test_good_files_raise_no_h_finding(projects):
    for name in ("site_si", "site_us", "site_v404"):
        rules = set(projects[name].qc().findings["rule_id"])
        assert not {"H001", "H002", "H003"} & rules, name
