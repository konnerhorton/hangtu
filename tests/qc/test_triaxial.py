"""Triaxial rules X001 to X008 (qc.md §4.12).

X001 to X006 are docs/work/m11a-triaxial-data.md AC 8; X007 and X008 are
docs/work/m23a-triaxial-moduli.md AC 5 to 8, with the hand calculations there.
"""

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
    assert found(report, "X007") == [("BH4", "TRET_E50", 161)]
    assert found(report, "X008") == [("BH4", "TRET_EP50", 162)]
    groups = report.findings.query("rule_id.str.startswith('X')")["group"]
    assert list(groups) == ["TRET"] * 4 + ["TREG", "TRIG"] + ["TRET"] * 3


def test_severities(report):
    severity = report.rules.set_index("rule_id")["severity"]
    assert severity["X003"] == "error"
    warnings = ["X001", "X002", "X004", "X005", "X006", "X007", "X008"]
    assert set(severity[warnings]) == {"warning"}


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
    # Eight TRET rows, all CU, and one TRIT row (X003, M17 a's Q001 case); one
    # TRET has no TRET_PWPF (X004); X006 checks each specimen's first stage
    # (7); X005 seven TREG and two TRIG. X007 compares BH4-U1's stage 1, the
    # one with all three values, and X008 its two stages with TRET_EP50.
    rules = ["X001", "X002", "X003", "X004", "X005", "X006", "X007", "X008"]
    assert checked[rules].tolist() == [8, 8, 9, 7, 9, 7, 1, 2]


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


# --- X007 and X008: the lab's E50 (M23 a) -------------------------------------------

MAXIMUM = "Maximum deviator stress"


def _e50(build, stages, criterion=MAXIMUM, test_type="CU"):
    """One test per stage, each ``(DEVF, STRN, EP50, E50)`` as written."""
    tests = group(
        "TREG",
        [*make_files.SPECIMEN, ("TREG_TYPE", "X", ""), ("TREG_FCR", "X", "")],
        [[*KEY, str(i), 1.60, test_type, criterion] for i in range(len(stages))],
    )
    rows = group(
        "TRET",
        [
            *make_files.SPECIMEN,
            ("TRET_TESN", "X", ""),
            ("TRET_CELL", "0DP", "kPa"),
            ("TRET_DEVF", "0DP", "kPa"),
            ("TRET_STRN", "1DP", "%"),
            ("TRET_EP50", "2DP", "%"),
            ("TRET_E50", "2DP", "MPa"),
        ],
        [[*KEY, str(i), 1.60, "1", 400, *stage] for i, stage in enumerate(stages)],
    )
    return build(LOCA, SAMP, tests, rows).qc()


def test_x007_dictionary_example_message(build):
    # AC 5: (359.5 / 2) / 0.03225 to (360.5 / 2) / 0.03215 kPa is 5.574 to
    # 5.607 MPa, far from 75.495 to 75.505 MPa.
    report = _e50(build, [(360, 8.0, "3.22", "75.50")])
    assert len(found(report, "X007")) == 1
    message = report.findings.query("rule_id == 'X007'")["message"].iloc[0]
    assert message.startswith("TRET_E50 75.50 MPa in BH1 at 1.60 m")
    assert "TRET_DEVF 360 kPa and TRET_EP50 3.22 %" in message
    assert "gives 5.59 MPa (from 5.57 to 5.61" in message
    assert "kPa written as MPa" in message and "a fraction" in message


@pytest.mark.parametrize(
    ("strain", "modulus", "count"),
    [
        # AC 6: q_f 180, ε50 0.60 % gives 14.835 to 15.168 MPa.
        ("0.60", "15.16", 0),  # 15.155 to 15.165: inside
        ("0.60", "15.20", 1),  # 15.195 to 15.205: above 15.168
        ("0.60", "15000", 1),  # kPa written as MPa
        ("0.006", "15.00", 1),  # ε50 as a fraction: about 1 500 MPa
    ],
)
def test_x007_at_the_edges(build, strain, modulus, count):
    report = _e50(build, [(180, 8.5, strain, modulus)])
    assert len(found(report, "X007")) == count


@pytest.mark.parametrize(
    ("strain", "e50", "x007", "x008"),
    [
        ("9.00", None, 0, 1),  # AC 7: above the strain at failure, 8.5 %
        ("8.50", None, 0, 1),  # equal
        ("0.006", None, 0, 0),  # a fraction with E50 blank: the accepted gap
    ],
)
def test_x008(build, strain, e50, x007, x008):
    report = _e50(build, [(180, 8.5, strain, e50)])
    assert (len(found(report, "X007")), len(found(report, "X008"))) == (x007, x008)
    if x008:
        message = report.findings.query("rule_id == 'X008'")["message"].iloc[0]
        assert f"TRET_EP50 {strain} % in BH1 at 1.60 m" in message
        assert "is at or above TRET_STRN 8.5 %" in message


@pytest.mark.parametrize(
    ("criterion", "test_type", "stage"),
    [
        ("Maximum stress ratio", "CU", (360, 3.0, "3.22", "75.50")),
        (None, "CU", (360, 3.0, "3.22", "75.50")),
        (MAXIMUM, "CIDE", (360, 3.0, "3.22", "75.50")),
        (MAXIMUM, "CU", (360, 3.0, None, "75.50")),
        (MAXIMUM, "CU", (">360", 3.0, "3.22", "75.50")),
    ],
)
def test_x007_x008_skips(build, criterion, test_type, stage):
    # AC 8; TRET_STRN 3.0 is below ε50 3.22, so a stage that were checked would
    # raise X008 too.
    report = _e50(build, [stage], criterion=criterion, test_type=test_type)
    assert found(report, "X007") == found(report, "X008") == []
    checked = report.rules.set_index("rule_id")["records_checked"]
    assert checked[["X007", "X008"]].tolist() == [0, 0]


@pytest.mark.parametrize(
    "criterion", ["  MAXIMUM deviator STRESS ", "Peak deviator stress"]
)
def test_x007_peak_spellings(build, criterion):
    report = _e50(build, [(360, 8.0, "3.22", "75.50")], criterion=criterion)
    assert len(found(report, "X007")) == 1


@pytest.mark.parametrize("name", ["site_si", "site_us"])
def test_x007_x008_clean_on_the_good_files(projects, name):
    # AC 9: BH1-U3 specimen 1 and BH2-U2 specimen 3 stage 1 are checked, and
    # agree (the US twin's 10SF values included); site_v404.ags has neither.
    report = projects[name].qc()
    assert found(report, "X007") == found(report, "X008") == []
    checked = report.rules.set_index("rule_id")["records_checked"]
    assert checked[["X007", "X008"]].tolist() == [2, 2]
