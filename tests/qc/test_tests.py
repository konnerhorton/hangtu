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


# --- Particle size -----------------------------------------------------------------


def test_particle_size_rules_at_their_lines(report):
    assert found(report, "P001") == [("BH2", "GRAT_PERP", 137)]
    assert found(report, "P002") == [("BH1", "GRAT_PERP", 131)]
    assert found(report, "P003") == [("BH3", None, 124)]
    assert found(report, "P004") == [("BH4", None, 139)]


def test_p001_names_the_two_points(report):
    message = _message(report, "P001")
    assert "rises at GRAT_SIZE 0.425 mm" in message
    assert "GRAT_PERP 85 % passing, more than the 80 % passing" in message


def test_p003_golden(report):
    # 10.0 + 60.0 + 24.0 = 94, 6 from 100.
    assert "add up to 94 %, more than 2 % from 100 %" in _message(report, "P003")


def _specimen_group(name, headings, rows):
    key = [
        ("LOCA_ID", "ID", ""),
        ("SAMP_TOP", "2DP", "m"),
        ("SAMP_REF", "X", ""),
        ("SAMP_TYPE", "PA", ""),
        ("SAMP_ID", "ID", ""),
        ("SPEC_REF", "X", ""),
        ("SPEC_DPTH", "2DP", "m"),
    ]
    specimen = ["BH1", 1.0, "1", "B", "BH1-B1", "1", 1.0]
    return group(name, key + headings, [specimen + row for row in rows])


def test_p003_uses_silt_and_clay_without_fines(build):
    headings = [
        ("GRAG_VCRE", "1DP", "%"),
        ("GRAG_GRAV", "1DP", "%"),
        ("GRAG_SAND", "1DP", "%"),
        ("GRAG_SILT", "1DP", "%"),
        ("GRAG_CLAY", "1DP", "%"),
    ]
    # 0 (blank cobbles) + 20 + 40 + 25 + 10 = 95.
    grag = _specimen_group("GRAG", headings, [[None, 20.0, 40.0, 25.0, 10.0]])
    report = build(loca(["BH1", 0, 0, 10, 5]), grag).qc()
    assert "add up to 95 %" in _message(report, "P003")


def test_p001_tolerance(build):
    headings = [("GRAT_SIZE", "3SF", "mm"), ("GRAT_PERP", "1DP", "%")]
    rows = [[2.0, "80.0"], [0.425, "80.5"], [0.063, "50.0"]]
    report = build(loca(["BH1", 0, 0, 10, 5]), _specimen_group("GRAT", headings, rows))
    assert found(report.qc(), "P001") == []


# --- Permeability ------------------------------------------------------------------


def test_k001_at_its_lines(report):
    assert found(report, "K001") == [
        ("BH2", "PTST_K", 147),
        ("BH4", "FGHG_IPRM", 153),
    ]
    assert "isn't greater than zero" in _message(report, "K001")


def test_k001_lt_value_is_checked_at_its_bound(build):
    headings = [("PTST_TESN", "X", ""), ("PTST_K", "XN", "m/s")]
    rows = [["1", "<1E-13"], ["2", "<1E-9"], ["3", ">2"], ["4", "OTHER"]]
    project = build(loca(["BH1", 0, 0, 10, 5]), _specimen_group("PTST", headings, rows))
    report = project.qc()
    assert list(report.findings.query("rule_id == 'K001'")["value"]) == ["<1E-13", ">2"]
    assert report.rules.set_index("rule_id").loc["K001", "records_checked"] == 3
