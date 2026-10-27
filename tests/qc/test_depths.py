import pytest

from .conftest import found, geol, group, loca


@pytest.fixture(scope="module")
def report(projects):
    return projects["qc_defects"].qc()


def test_each_rule_at_its_line(report):
    assert found(report, "D001") == [("BH1", "SAMP_BASE", 48)]
    assert found(report, "D002") == [("BH1", "ISPT_TOP", 59)]
    assert found(report, "D003") == [("BH3", "ISPT_TOP", 66)]
    # 98 is the case (in BH1's 2.50 to 3.00 gap); 96 and 103 are cascades of
    # D002 (above the log) and D003 (below it).
    assert found(report, "D004") == [
        ("BH1", "ISPT_TOP", 59),
        ("BH1", "ISPT_TOP", 61),
        ("BH3", "ISPT_TOP", 66),
    ]
    assert found(report, "D005") == [("BH4", "SAMP_TOP", 52)]
    assert found(report, "D007") == [("BH4", "SPEC_DPTH", 85)]
    assert found(report, "D008") == [("BH3", "SPEC_DPTH", 84)]


def test_messages(report):
    message = dict(
        zip(report.findings["rule_id"], report.findings["message"], strict=True)
    )
    assert message["D003"] == (
        "ISPT_TOP 7.00 m (23.0 ft) in BH3 is below the final depth of the hole, "
        "LOCA_FDEP 6.00 m (19.7 ft). Check the record's depth or the final depth."
    )
    assert "crosses the geology boundary at 2.50 m (8.20 ft)" in message["D005"]
    assert "outside its sample BH4-U2, from 4.00 to 4.45 m" in message["D007"]
    assert message["D008"] == (
        "SPEC_DPTH 1.55 m (5.09 ft) in BH3 is 0.05 m (0.164 ft) outside its sample "
        "BH3-B1, from 1.00 to 1.50 m (3.28 to 4.92 ft), within the rounding "
        "tolerance of 0.1 m (0.328 ft). Likely unit rounding; check the specimen "
        "depth if it matters."
    )


def _ispt(*depths):
    return group(
        "ISPT",
        [("LOCA_ID", "ID", ""), ("ISPT_TOP", "2DP", "m"), ("ISPT_NVAL", "0DP", "")],
        [["BH1", depth, 10] for depth in depths],
    )


def test_d003_tolerance_edge(build):
    # LOCA_FDEP 5.00 m and the 0.1 m tolerance: 5.10 is within it, 5.11 isn't.
    project = build(loca(["BH1", 0, 0, 10, 5.0]), _ispt("5.10", "5.11"))
    assert [f[2] for f in found(project.qc(), "D003")] == [
        int(project.table("ISPT")["_line"].iloc[1])
    ]


def test_d003_skipped_without_final_depth(build):
    project = build(loca(["BH1", 0, 0, 10, None]), _ispt(50.0))
    assert found(project.qc(), "D003") == []


def test_d004_interval_rule(build):
    # Layers 0-2 and 2-5: 2.00 is in the second; 5.00, the bottom of the log,
    # belongs to the last layer (SPEC §8.3); 5.01 is outside.
    layers = geol(["BH1", 0.0, 2.0], ["BH1", 2.0, 5.0])
    project = build(loca(["BH1", 0, 0, 10, 6]), layers, _ispt(0.0, 2.0, 5.0, 5.01))
    lines = list(project.table("ISPT")["_line"])
    assert [f[2] for f in found(project.qc(), "D004")] == [lines[3]]


def test_d004_skipped_for_a_hole_without_geology(build):
    project = build(loca(["BH1", 0, 0, 10, 6]), geol(), _ispt(1.0))
    assert found(project.qc(), "D004") == []


def test_sample_top_in_a_lab_group_is_checked_once(build):
    samp = group(
        "SAMP",
        [
            ("LOCA_ID", "ID", ""),
            ("SAMP_TOP", "2DP", "m"),
            ("SAMP_REF", "X", ""),
            ("SAMP_TYPE", "PA", ""),
            ("SAMP_ID", "ID", ""),
            ("SAMP_BASE", "2DP", "m"),
        ],
        [["BH1", -1.0, "1", "U", "BH1-U1", 0.5]],
    )
    lnmc = group(
        "LNMC",
        [
            ("LOCA_ID", "ID", ""),
            ("SAMP_TOP", "2DP", "m"),
            ("SAMP_REF", "X", ""),
            ("SAMP_TYPE", "PA", ""),
            ("SAMP_ID", "ID", ""),
            ("SPEC_REF", "X", ""),
            ("SPEC_DPTH", "2DP", "m"),
            ("LNMC_MC", "0DP", "%"),
        ],
        [["BH1", -1.0, "1", "U", "BH1-U1", "1", 0.2, 20]],
    )
    report = build(loca(["BH1", 0, 0, 10, 6]), samp, lnmc).qc()
    assert [(f[1]) for f in found(report, "D002")] == ["SAMP_TOP"]


def test_d007_specimen_in_two_tests_is_checked_once(projects):
    report = projects["qc_defects"].qc()
    rule = report.rules.set_index("rule_id").loc["D007"]
    # Eight specimens, though LLPL, GRAG, GRAT, PTST, LDEN and LPDN hold 27 rows
    # of them: LDEN uses four of the six, and LPDN adds two.
    assert rule["records_checked"] == 8
    assert report.rules.set_index("rule_id").loc["D008", "records_checked"] == 8


def _severities(report, *rule_ids):
    rows = report.findings.query("rule_id in @rule_ids")
    return sorted(
        zip(rows["rule_id"], rows["source_line"], rows["severity"], strict=True)
    )


def test_d008_is_the_rounding_band_of_d007(projects):
    report = projects["qc_defects"].qc()
    assert _severities(report, "D007", "D008") == [
        ("D007", 85, "warning"),
        ("D008", 84, "info"),
    ]


def test_wider_rounding_tolerance_turns_d007_into_d008(projects):
    report = projects["qc_defects"].qc(
        rules={"D007": {"thresholds": {"rounding_tolerance": "0.5 m"}}}
    )
    assert _severities(report, "D007", "D008") == [
        ("D008", 84, "info"),
        ("D008", 85, "info"),
    ]


def test_disabling_d008_leaves_the_rounding_case_unreported(projects):
    report = projects["qc_defects"].qc(rules={"D008": {"enabled": False}})
    assert _severities(report, "D007", "D008") == [("D007", 85, "warning")]


def test_disabling_d007_keeps_d008s_band(projects):
    report = projects["qc_defects"].qc(rules={"D007": {"enabled": False}})
    assert _severities(report, "D007", "D008") == [("D008", 84, "info")]


def test_d008_thresholds_cell(projects):
    rules = projects["qc_defects"].qc().rules.set_index("rule_id")
    assert rules.loc["D008", "thresholds"] == (
        "from D007: depth_tolerance = 0.01 m; rounding_tolerance = 0.1 m"
    )
    assert rules.loc["D008", "overridden"] == "no"
