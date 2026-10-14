import pytest

from .conftest import found, group, loca


@pytest.fixture(scope="module")
def report(projects):
    return projects["qc_defects"].qc()


def _message(report, rule_id):
    return report.findings.query("rule_id == @rule_id")["message"].iloc[0]


# --- SPT ---------------------------------------------------------------------------


def test_spt_rules_at_their_lines(report):
    assert found(report, "S001") == [("BH1", "ISPT_REP", 97)]
    assert found(report, "S002") == [("BH1", "ISPT_NVAL", 99)]
    assert found(report, "S004") == [("BH2", "ISPT_NVAL", 100)]
    assert found(report, "S005") == [("BH2", "ISPT_N60", 101)]


def test_s003_one_per_hole_with_the_count(report):
    assert found(report, "S003") == [("BH4", "ISPT_ERAT", None)]
    assert _message(report, "S003").startswith("2 of 2 SPTs in BH4 have no energy")


def test_s004_golden(report):
    # INC3 to INC6: 4 + 5 + 5 + 5 = 19, not N = 20.
    assert "ISPT_INC3 to ISPT_INC6 = 19" in _message(report, "S004")


def test_s005_golden(report):
    # N60 = 20 * 75 / 60 = 25, and the file says 30.
    assert "N * ER / 60 = 20 * 75 / 60 = 25.0" in _message(report, "S005")
    assert "ISPT_N60 30 in BH2 at 5.00 m (16.4 ft)" in _message(report, "S005")


def _ispt(headings, *rows):
    base = [("LOCA_ID", "ID", ""), ("ISPT_TOP", "2DP", "m")]
    return group(
        "ISPT", base + headings, [["BH1", float(i), *r] for i, r in enumerate(rows)]
    )


def test_s001_reads_complete_tests_and_pairs(build):
    reports = ["N=12", "N = 12", "25/75 50/75", "50/30", "refusal"]
    ispt = _ispt(
        [("ISPT_NVAL", "0DP", ""), ("ISPT_REP", "X", "")],
        *([10, text] for text in reports),
    )
    report = build(loca(["BH1", 0, 0, 10, 9]), ispt).qc()
    assert list(report.findings.query("rule_id == 'S001'")["value"]) == ["refusal"]


def test_s004_skips_refusals_and_checks_main(build):
    headings = [
        ("ISPT_MAIN", "0DP", ""),
        ("ISPT_NVAL", "0DP", ""),
        ("ISPT_REP", "X", ""),
    ]
    ispt = _ispt(
        headings,
        [30, 50, "25/75 50/75"],  # refusal: N is flagged, not compared
        [12, 12, "N=12"],
        [12, 13, "N=13"],
    )
    project = build(loca(["BH1", 0, 0, 10, 9]), ispt)
    lines = list(project.table("ISPT")["_line"])
    report = project.qc()
    assert [f[2] for f in found(report, "S004")] == [lines[2]]
    assert "ISPT_MAIN = 12" in _message(report, "S004")


def test_s002_skips_a_refusal(build):
    ispt = _ispt(
        [("ISPT_NVAL", "0DP", ""), ("ISPT_REP", "X", "")],
        [150, "50/25"],
        [150, "N=150"],
    )
    project = build(loca(["BH1", 0, 0, 10, 9]), ispt)
    assert [f[2] for f in found(project.qc(), "S002")] == [
        int(project.table("ISPT")["_line"].iloc[1])
    ]


# --- Atterberg limits --------------------------------------------------------------


def test_atterberg_rules_at_their_lines(report):
    assert found(report, "A001") == [("BH1", "LLPL_LL", 112)]
    assert found(report, "A002") == [("BH2", "LLPL_PI", 113)]
    assert found(report, "A003") == [("BH2", "LLPL_LL", 114)]
    assert found(report, "A004") == [("BH3", "LLPL_PL", 115)]


def test_a002_golden(report):
    # LL 50 - PL 20 = 30, and the file's PI is 25.
    assert "LL - PL = 50 - 20 = 30 by more than 1 %" in _message(report, "A002")


def test_a001_and_a003_messages(report):
    assert _message(report, "A001").startswith(
        "LLPL_LL 30 % in BH1 at 1.10 m (3.61 ft) is below LLPL_PL 35 %."
    )
    assert "LLPL_LL 8 % in BH2" in _message(report, "A003")
    assert "outside 10 % to 150 %" in _message(report, "A003")


def test_np_is_not_compared(report):
    # BH3's PL is NP: A004 says so, and A001 doesn't compare it.
    assert [f[0] for f in found(report, "A001")] == ["BH1"]
