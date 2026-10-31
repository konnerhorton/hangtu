"""Triaxial rules X001 to X006 (qc.md §4.12; docs/work/m11a-triaxial-data.md AC 8)."""

import pytest

from hangtu.errors import HangtuError

from .conftest import found, make_files

group = make_files.group


@pytest.fixture(scope="module")
def report(projects):
    return projects["qc_defects"].qc()


def _message(report, rule_id, line):
    rows = report.findings.query("rule_id == @rule_id and source_line == @line")
    return rows["message"].iloc[0]


def test_triaxial_rules_at_their_lines(report):
    assert found(report, "X001") == [("BH1", "TRET_BVAL", 156)]
    assert found(report, "X002") == [("BH2", "TRET_PWPF", 158)]
    assert found(report, "X003") == [("BH2", "TRET_DEVF", 159)]
    assert found(report, "X004") == [("BH4", "TRET_PWPF", 160)]
    assert found(report, "X005") == [("BH4", "TREG_TYPE", 149), ("BH3", None, 169)]
    assert found(report, "X006") == [("BH1", "TRET_CONP", 157)]
    groups = report.findings.query("rule_id.str.startswith('X')")["group"]
    assert list(groups) == ["TRET", "TRET", "TRET", "TRET", "TREG", "TRIG", "TRET"]


def test_severities(report):
    severity = report.rules.set_index("rule_id")["severity"]
    assert severity["X003"] == "error"
    assert set(severity[["X001", "X002", "X004", "X005", "X006"]]) == {"warning"}


def test_x001_names_the_standards_and_the_lab_remarks(report):
    message = _message(report, "X001", 156)
    assert message.startswith("TRET_BVAL 0.90 in BH1 at 1.20 m (3.94 ft), stage 1")
    assert "is below 0.95" in message
    assert "ASTM D4767, ISO 17892-9; not yet checked" in message
    assert "read the lab's remarks" in message


def test_x001_accepts_exactly_the_threshold(report):
    # BH3-B1's B-value is 0.95 (line 163): not below 0.95.
    assert 163 not in [line for _, _, line in found(report, "X001")]


def test_x001_threshold_is_a_plain_number(projects):
    rules = {"X001": {"thresholds": {"lowest_pore_pressure_parameter_b": 0.96}}}
    report = projects["qc_defects"].qc(rules=rules)
    assert [line for _, _, line in found(report, "X001")] == [156, 163]
    with pytest.raises(HangtuError, match="is a ratio and takes a plain number"):
        projects["qc_defects"].qc(
            rules={
                "X001": {"thresholds": {"lowest_pore_pressure_parameter_b": "1 kPa"}}
            }
        )


def test_x002_says_phi_cant_be_fitted(report):
    message = _message(report, "X002", 158)
    assert "TRET_PWPF is blank in BH2 at 1.20 m" in message
    assert "undrained" in message and "φ′ can't be fitted" in message


def test_x003_x004_messages(report):
    assert "TRET_DEVF -20 kPa (-418 psf) in BH2" in _message(report, "X003", 159)
    x004 = _message(report, "X004", 160)
    assert "TRET_PWPF 410 kPa (8563 psf) in BH4 at 4.20 m" in x004
    assert "is above TRET_CELL 400 kPa (8354 psf)" in x004


def test_x006_golden(report):
    # 400 - 300 = 100 kPa expected; the file says 150, 50 kPa off.
    message = _message(report, "X006", 157)
    assert message.startswith("TRET_CONP 150 kPa (3133 psf) in BH1 at 1.30 m")
    assert "TRET_CELL - TRET_BACK = 100 kPa (2089 psf) by 50 kPa (1044 psf)" in message
    assert "more than 2 kPa (41.8 psf)" in message


def test_x006_skips_a_rounding_difference(report):
    # BH3-B1, line 163: TRET_CONP 101 with cell 400 and back 300, 1 kPa off.
    assert 163 not in [line for _, _, line in found(report, "X006")]


@pytest.mark.parametrize(
    ("tolerance", "lines"),
    # 50 kPa = 1044 psf = 1.044 ksf; 1 kPa = 20.9 psf.
    [
        ("1000 psf", [157]),
        ("1100 psf", []),
        ("1 ksf", [157]),
        ("1.1 ksf", []),
        ("10 psf", [157, 163]),
        ("0.5 kPa", [157, 163]),
    ],
)
def test_x006_tolerance_in_any_stress_unit(projects, tolerance, lines):
    rules = {"X006": {"thresholds": {"consolidation_stress_tolerance": tolerance}}}
    report = projects["qc_defects"].qc(rules=rules)
    assert [line for _, _, line in found(report, "X006")] == lines


def test_records_checked(report):
    checked = report.rules.set_index("rule_id")["records_checked"]
    # Eight TRET rows, all CU; one has no TRET_PWPF (X004); X006 checks each
    # specimen's first stage (7); X005 seven TREG and one TRIG.
    rules = ["X001", "X002", "X003", "X004", "X005", "X006"]
    assert checked[rules].tolist() == [8, 8, 8, 7, 8, 7]


# --- Cases built here ---------------------------------------------------------------

KEY = ["BH1", 1.50, "1", "U", "BH1-U1"]
SAMP = group(
    "SAMP",
    [
        ("LOCA_ID", "ID", ""),
        ("SAMP_TOP", "2DP", "m"),
        ("SAMP_REF", "X", ""),
        ("SAMP_TYPE", "PA", ""),
        ("SAMP_ID", "ID", ""),
    ],
    [KEY],
)
LOCA = group("LOCA", [("LOCA_ID", "ID", "")], [["BH1"]])


def _triaxial(build, tests, stages, effective=True):
    """A project with one test per ``(SPEC_REF, type)`` and ``stages`` as
    ``(SPEC_REF, TESN, DEVF)``."""
    test, stage = ("TREG", "TRET") if effective else ("TRIG", "TRIT")
    tests = group(
        test,
        [*make_files.SPECIMEN, (f"{test}_TYPE", "X", "")],
        [[*KEY, ref, 1.60, kind] for ref, kind in tests],
    )
    stages = group(
        stage,
        [
            *make_files.SPECIMEN,
            (f"{stage}_TESN", "X", ""),
            (f"{stage}_CELL", "0DP", "kPa"),
            (f"{stage}_DEVF", "0DP", "kPa"),
        ],
        [[*KEY, ref, 1.60, tesn, 100, devf] for ref, tesn, devf in stages],
    )
    return build(LOCA, SAMP, tests, stages)


def test_x005_multistage_type_with_one_stage(build):
    p = _triaxial(
        build,
        [("1", "CDM"), ("2", "CDM"), ("3", "XYZ")],
        [
            ("1", "1", 100),
            ("2", "1", 100),
            ("2", "2", 150),
            ("3", "1", 100),
            ("3", "2", 150),
        ],
    )
    rows = p.qc().findings.query("rule_id == 'X005'")
    # Specimen 1 has one stage; a type the dictionary doesn't list (XYZ) is
    # checked only for having stages.
    assert len(rows) == 1
    assert (
        "TREG_TYPE CDM in BH1 at 1.60 m is a multistage test" in rows["message"].iloc[0]
    )


def test_x003_skips_extension_and_checks_total_stress(build):
    p = _triaxial(build, [("1", "CIDE"), ("2", "CU")], [("1", "1", -50), ("2", "1", 0)])
    rows = p.qc().findings.query("rule_id == 'X003'")
    assert list(rows["source_line"]) == [p.table("TRET")["_line"].iloc[1]]
    p = _triaxial(build, [("1", "UU")], [("1", "1", 0)], effective=False)
    assert found(p.qc(), "X003")[0][1] == "TRIT_DEVF"
