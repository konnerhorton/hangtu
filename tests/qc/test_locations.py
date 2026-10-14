import pytest

from .conftest import found, group, loca


@pytest.fixture(scope="module")
def report(projects):
    return projects["qc_defects"].qc()


def test_l001_l002_l003_on_bh5(report):
    assert found(report, "L001") == [("BH5", "LOCA_GL", 58)]
    assert found(report, "L002") == [("BH5", None, 58)]
    assert found(report, "L003") == [("BH5", "LOCA_FDEP", 58)]
    message = report.findings.query("rule_id == 'L001'")["message"].iloc[0]
    assert message.startswith("LOCA_GL is blank for BH5")


def test_l004_on_the_horn_row(report):
    assert found(report, "L004") == [("BH2", "HORN_INCL", 64)]
    row = report.findings.query("rule_id == 'L004'").iloc[0]
    assert row["value"] == "80"
    assert "10.0° from vertical" in row["message"]


def test_l005_golden_median_and_difference(report):
    assert found(report, "L005") == [("BH4", "LOCA_GL", 57)]
    message = report.findings.query("rule_id == 'L005'")["message"].iloc[0]
    # Neighbors BH1, BH2, BH3 at 10.00, 10.50, 9.50 m: median 10.00 m.
    # BH4 is at 18.00 m: 8.00 m above. In ft: 8 / 0.3048 = 26.2, 10 / 0.3048 = 32.8.
    assert "LOCA_GL 18.00 m (59.1 ft) in BH4" in message
    assert "is 8.00 m (26.2 ft) above the median of the 3 nearest holes" in message
    assert "10.00 m (32.8 ft) (BH2, BH3, BH1)" in message
    assert "more than 3 m (9.84 ft)" in message


def test_l006_once_per_project(report):
    rows = report.findings.query("rule_id == 'L006'")
    assert len(rows) == 1
    assert rows["group"].isna().all()
    assert rows["source_line"].isna().all()
    assert 'p.settings.vertical_datum = "NAVD88"' in rows["message"].iloc[0]


def test_l006_not_raised_with_a_datum(build):
    project = build(loca(["BH1", 0, 0, 10, 5]), vertical_datum="NAVD88")
    assert found(project.qc(), "L006") == []


def _horn(*inclinations):
    return group(
        "HORN",
        [
            ("LOCA_ID", "ID", ""),
            ("HORN_TOP", "2DP", "m"),
            ("HORN_BASE", "2DP", "m"),
            ("HORN_INCL", "1DP", "deg"),
        ],
        [["BH1", float(i), float(i + 1), incl] for i, incl in enumerate(inclinations)],
    )


def test_l004_tolerance_edges(build):
    project = build(loca(["BH1", 0, 0, 10, 5]), _horn("88", "87.9", "92", "92.1"))
    report = project.qc()
    assert set(report.findings.query("rule_id == 'L004'")["value"]) == {"87.9", "92.1"}


def test_l004_hole_without_horn_is_vertical(build):
    project = build(loca(["BH1", 0, 0, 10, 5]))
    report = project.qc()
    assert found(report, "L004") == []
    rule = report.rules.set_index("rule_id").loc["L004"]
    assert rule["records_checked"] == 0


def test_l005_needs_enough_neighbors(build):
    holes = [["BH1", 0, 0, 10, 5], ["BH2", 50, 0, 10, 5], ["BH3", 500, 0, 30, 5]]
    report = build(loca(*holes)).qc()
    # BH3 has no neighbor within 200 m; BH1 and BH2 have only one each.
    assert found(report, "L005") == []
    assert report.rules.set_index("rule_id").loc["L005", "records_checked"] == 0


def test_l005_threshold_override(build):
    holes = [
        ["BH1", 0, 0, 10.0, 5],
        ["BH2", 50, 0, 10.0, 5],
        ["BH3", 0, 50, 10.0, 5],
        ["BH4", 50, 50, 12.0, 5],
    ]
    project = build(loca(*holes))
    assert found(project.qc(), "L005") == []
    report = project.qc(
        rules={"L005": {"thresholds": {"ground_level_difference": "5 ft"}}}
    )
    assert [f[0] for f in found(report, "L005")] == ["BH4"]
