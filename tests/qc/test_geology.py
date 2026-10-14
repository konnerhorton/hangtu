import pytest

from .conftest import found, geol, group, loca


@pytest.fixture(scope="module")
def report(projects):
    return projects["qc_defects"].qc()


def test_g001_hole_with_records_and_no_log(report):
    assert found(report, "G001") == [("BH5", None, 58)]
    message = report.findings.query("rule_id == 'G001'")["message"].iloc[0]
    assert "BH5 has records in ISPT but no geology (GEOL) rows" in message


def test_g002_gap_between_layers_and_at_the_bottom(report):
    assert found(report, "G002") == [("BH1", "GEOL_TOP", 71), ("BH2", "GEOL_BASE", 73)]
    messages = list(report.findings.query("rule_id == 'G002'")["message"])
    assert "from 2.50 to 3.00 m (8.20 to 9.84 ft), between two layers" in messages[0]
    assert "from 7.50 to 8.00 m (24.6 to 26.2 ft), below the last layer" in messages[1]


def test_g003_overlap(report):
    assert found(report, "G003") == [("BH3", "GEOL_TOP", 76)]
    message = report.findings.query("rule_id == 'G003'")["message"].iloc[0]
    assert (
        "overlap from 3.50 to 4.00 m (11.5 to 13.1 ft), on lines 75 and 76" in message
    )


def test_g002_gap_at_the_top(build):
    project = build(loca(["BH1", 0, 0, 10, 5]), geol(["BH1", 0.5, 5.0]))
    line = int(project.table("GEOL")["_line"].iloc[0])
    report = project.qc()
    assert found(report, "G002") == [("BH1", "GEOL_TOP", line)]
    message = report.findings.query("rule_id == 'G002'")["message"].iloc[0]
    assert "from 0.00 to 0.50 m, above the first layer" in message


def _gap_report(build, gap, **qc):
    layers = geol(["BH1", 0.0, 2.0], ["BH1", f"{2.0 + gap:.3f}", 5.0])
    return build(loca(["BH1", 0, 0, 10, 5]), layers).qc(**qc)


def test_g002_tolerance_edges(build):
    assert found(_gap_report(build, 0.01), "G002") == []
    assert len(found(_gap_report(build, 0.02), "G002")) == 1


def test_g002_tolerance_in_feet(build):
    # 0.05 ft is 0.01524 m: a 0.015 m gap is within it but beyond the default.
    in_feet = {"G002": {"thresholds": {"depth_tolerance": "0.05 ft"}}}
    in_meters = {"G002": {"thresholds": {"depth_tolerance": "0.01524 m"}}}
    assert len(found(_gap_report(build, 0.015), "G002")) == 1
    assert found(_gap_report(build, 0.015, rules=in_feet), "G002") == []
    assert found(_gap_report(build, 0.015, rules=in_meters), "G002") == []
    assert len(found(_gap_report(build, 0.02, rules=in_feet), "G002")) == 1
    assert len(found(_gap_report(build, 0.02, rules=in_meters), "G002")) == 1


def test_g003_tolerance_edges(build):
    def overlap(amount):
        layers = geol(["BH1", 0.0, 2.0], ["BH1", f"{2.0 - amount:.3f}", 5.0])
        return found(build(loca(["BH1", 0, 0, 10, 5]), layers).qc(), "G003")

    assert overlap(0.01) == []
    assert len(overlap(0.02)) == 1


def test_g001_skipped_without_geol(build):
    ispt = group(
        "ISPT",
        [("LOCA_ID", "ID", ""), ("ISPT_TOP", "2DP", "m"), ("ISPT_NVAL", "0DP", "")],
        [["BH1", 1.0, 10]],
    )
    report = build(loca(["BH1", 0, 0, 10, 5]), ispt).qc()
    assert found(report, "G001") == []
    assert report.rules.set_index("rule_id").loc["G001", "records_checked"] == 0
