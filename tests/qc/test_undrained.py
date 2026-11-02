"""Undrained strength rules Q001 to Q003 (qc.md §4.13; m17a AC 13)."""

from .conftest import found, group, loca, make_files

SPECIMEN = make_files.SPECIMEN
KEY = ["BH1", 1.00, "1", "U", "BH1-U1", "1", 1.10]


def _samp():
    return group(
        "SAMP",
        [
            ("LOCA_ID", "ID", ""),
            ("SAMP_TOP", "2DP", "m"),
            ("SAMP_REF", "X", ""),
            ("SAMP_TYPE", "PA", ""),
            ("SAMP_ID", "ID", ""),
            ("SAMP_BASE", "2DP", "m"),
        ],
        [["BH1", 1.00, "1", "U", "BH1-U1", 1.45]],
    )


def _trit(*rows):
    return group(
        "TRIT",
        [
            *SPECIMEN,
            ("TRIT_TESN", "X", ""),
            ("TRIT_CELL", "0DP", "kPa"),
            ("TRIT_DEVF", "0DP", "kPa"),
            ("TRIT_CU", "0DP", "kPa"),
        ],
        [list(row) for row in rows],
    )


def test_q_rules_at_their_lines(projects):
    report = projects["qc_defects"].qc()
    assert found(report, "Q001") == [("BH2", "TRIT_CU", 176)]
    assert found(report, "Q002") == [("BH4", "LVAN_VNRM", 188)]
    assert found(report, "Q003") == [("BH4", "LUCT_UCS", 182)]
    severity = report.rules.set_index("rule_id")["severity"]
    assert severity["Q003"] == "error"
    assert set(severity[["Q001", "Q002"]]) == {"warning"}


def test_q001_gives_the_expected_value_and_the_difference(projects):
    report = projects["qc_defects"].qc()
    message = report.findings.query("rule_id == 'Q001'")["message"].iloc[0]
    assert message.startswith("TRIT_CU 70 kPa")
    assert "TRIT_DEVF / 2 = 60 kPa" in message
    assert "by 10 kPa" in message
    assert "reported_undrained_shear_strength" in message


def test_q001_clears_rounding(build):
    # TRIT_CU 61 with TRIT_DEVF 120 is 1 kPa off: within the tolerance.
    hole = loca(["BH1", 0, 0, 10, 10])
    project = build(hole, _samp(), _trit([*KEY, "1", 100, 120, 61]))
    assert found(project.qc(), "Q001") == []
    # 63 is 3 kPa off; a tolerance of 70 psf (3.35 kPa) clears it.
    project = build(hole, _samp(), _trit([*KEY, "1", 100, 120, 63]))
    assert len(found(project.qc(), "Q001")) == 1
    rules = {"Q001": {"thresholds": {"undrained_strength_tolerance": "70 psf"}}}
    assert found(project.qc(rules=rules), "Q001") == []
