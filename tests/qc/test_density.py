"""Density rules B001 to B004 (qc.md §4.11; docs/work/m14a-density-data.md AC 7)."""

import pytest

from .conftest import found


@pytest.fixture(scope="module")
def report(projects):
    return projects["qc_defects"].qc()


def _message(report, rule_id, line):
    rows = report.findings.query("rule_id == @rule_id and source_line == @line")
    return rows["message"].iloc[0]


def test_density_rules_at_their_lines(report):
    assert found(report, "B001") == [("BH1", "LDEN_DDEN", 128)]
    assert found(report, "B002") == [("BH2", "LDEN_DDEN", 129)]
    assert found(report, "B003") == [
        ("BH2", "LDEN_BDEN", 130),
        ("BH1", "LPDN_PDEN", 137),
    ]
    assert found(report, "B004") == [("BH2", "LPDN_PDEN", 138)]


def test_b001_golden(report):
    # 2.00 / (1 + 20 / 100) = 1.667, and the file says 1.80: 0.133 apart.
    message = _message(report, "B001", 128)
    assert "LDEN_DDEN 1.80 Mg/m3 (112 pcf) in BH1 at 1.10 m (3.61 ft)" in message
    assert "= 1.67 Mg/m3 (104 pcf) by 0.133 Mg/m3 (8.32 pcf)" in message
    assert "more than 0.03 Mg/m3 (1.87 pcf)" in message


def test_b001_skips_the_dictionary_example_and_a_blank_water_content(report):
    # BH4-U1, line 131: 1.66 / 1.57 = 1.057 against 1.06, 0.003 apart. Line 129
    # has no LDEN_MC, so only B002 checks it.
    lines = [line for _, _, line in found(report, "B001")]
    assert 131 not in lines and 129 not in lines


@pytest.mark.parametrize(
    ("tolerance", "raised"),
    # 0.133 Mg/m3 apart; 1 pcf = 0.0160185 Mg/m3, so 8.0 pcf = 0.128 and
    # 8.6 pcf = 0.138 Mg/m3.
    [
        ("0.128 Mg/m3", True),
        ("8.0 pcf", True),
        ("0.138 Mg/m3", False),
        ("8.6 pcf", False),
    ],
)
def test_b001_tolerance_in_either_unit(projects, tolerance, raised):
    rules = {"B001": {"thresholds": {"dry_density_tolerance": tolerance}}}
    report = projects["qc_defects"].qc(rules=rules)
    assert bool(found(report, "B001")) is raised


def test_b002_message(report):
    assert "is above LDEN_BDEN 1.80 Mg/m3" in _message(report, "B002", 129)


def test_b003_names_the_unit_and_the_material(report):
    bulk = _message(report, "B003", 130)
    assert bulk.startswith("LDEN_BDEN 19.50 Mg/m3 (1217 pcf) in BH2 at 4.10 m")
    assert "outside the bulk density range 1.0 Mg/m3 (62.4 pcf) to 2.8 Mg/m3" in bulk
    assert "kg/m3 and pcf read as Mg/m3" in bulk
    particle = _message(report, "B003", 137)
    assert "particle density range 2.0 Mg/m3 (125 pcf) to 3.2 Mg/m3" in particle
    assert "ores and some rock above" in particle


def test_b003_ranges_in_pcf(projects):
    # 1250 pcf = 20.02 Mg/m3, so 19.50 is inside; 26.5 is still outside 3.2.
    rules = {"B003": {"thresholds": {"highest_bulk_density": "1250 pcf"}}}
    report = projects["qc_defects"].qc(rules=rules)
    assert found(report, "B003") == [("BH1", "LPDN_PDEN", 137)]


def test_b004_is_a_note(report):
    rows = report.findings.query("rule_id == 'B004'")
    assert list(rows["severity"]) == ["info"]
    assert "2.65 Mg/m3 (165 pcf) in BH2 at 1.20 m" in rows["message"].iloc[0]
    assert "is assumed (#), not measured" in rows["message"].iloc[0]


def test_records_checked(report):
    checked = report.rules.set_index("rule_id")["records_checked"]
    # B001 needs all three (3 of 4 LDEN rows); B002 two (4); B003 four LDEN
    # and two LPDN; B004 every LPDN row.
    assert checked[["B001", "B002", "B003", "B004"]].tolist() == [3, 4, 6, 2]


def test_good_files_have_only_the_assumed_note(projects):
    for name in ("site_si", "site_us", "site_v404"):
        findings = projects[name].qc().findings
        density = findings[findings["rule_id"].str.startswith("B")]
        assert list(density["rule_id"]) == ["B004"], name
