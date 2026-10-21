import pytest

import hangtu as ht

from .conftest import found, group, loca, loca_datum


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


def _message(report, rule_id):
    rows = report.findings.query(f"rule_id == '{rule_id}'")
    assert len(rows) == 1, rows
    return rows["message"].iloc[0]


def test_l006_and_l007_on_holes_with_different_datums(report):
    # AC 5. BH5 has no LOCA_GL, so its blank LOCA_DATM doesn't count.
    assert "holes name different datums (L007)" in _message(report, "L006")
    row = report.findings.query("rule_id == 'L007'").iloc[0]
    assert (row["group"], row["heading"], row["severity"]) == (
        "LOCA",
        "LOCA_DATM",
        "warning",
    )
    assert "NAVD88 in 3 holes (BH1, BH2, BH3); NGVD29 in 1 hole (BH4)" in row["message"]


def test_l006_names_holes_with_a_blank_datum(build):
    # AC 3.
    report = build(
        loca_datum(["BH1", 10, "NAVD88", None], ["BH2", 11, None, None])
    ).qc()
    assert "it is blank for BH2, so that hole could be on" in _message(report, "L006")
    assert found(report, "L007") == []


def test_l006_names_at_most_ten_blank_holes(build):
    rows = [["BH0", 10, "NAVD88", None]]
    rows += [[f"BH{i}", 10, None, None] for i in range(1, 13)]
    message = _message(build(loca_datum(*rows)).qc(), "L006")
    assert "blank for BH1, BH2, BH3, BH4, BH5, BH6, BH7, BH8, BH9, BH10 and 2 more" in (
        message
    )


def test_l006_names_holes_with_a_local_level(build):
    # AC 3, AC 5: no L007, since BH2's LOCA_DATM may be a local datum.
    report = build(
        loca_datum(["BH1", 10, "NAVD88", None], ["BH2", 11, "Site datum", 2.5])
    ).qc()
    assert "BH2 has a LOCA_LOCZ" in _message(report, "L006")
    assert found(report, "L007") == []


def test_l006_shows_how_to_add_an_unknown_datum(build):
    # AC 2.
    report = build(loca_datum(["BH1", 10, "Anytown datum", None])).qc()
    message = _message(report, "L006")
    assert '"Anytown datum" isn\'t in the datum table' in message
    assert 'ht.add_vertical_datum("<short name>", name="Anytown datum")' in message
    assert found(report, "L007") == []


def test_l007_when_the_set_datum_differs_from_the_file(build):
    # AC 4.
    report = build(
        loca_datum(["BH1", 10, "NAVD88", None]), vertical_datum="NGVD29"
    ).qc()
    message = _message(report, "L007")
    assert "set to NGVD29, but LOCA_DATM names NAVD88 for BH1" in message
    assert found(report, "L006") == []


def test_no_l007_when_the_file_wins_over_the_session_setting(build):
    # AC 4.
    ht.settings.vertical_datum = "NGVD29"
    report = build(loca_datum(["BH1", 10, "NAVD88", None])).qc()
    assert found(report, "L007") == [] and found(report, "L006") == []


def test_no_l007_for_another_spelling_of_the_set_datum(build):
    report = build(
        loca_datum(["BH1", 10, "NAVD 88", None]), vertical_datum="NAVD88"
    ).qc()
    assert found(report, "L007") == []


def test_no_l007_for_a_local_level_on_another_datum(build):
    # AC 5.
    report = build(
        loca_datum(["BH1", 10, "NAVD88", None], ["BH2", 11, "NGVD29", 3.0]),
        vertical_datum="NAVD88",
    ).qc()
    assert found(report, "L007") == []


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
