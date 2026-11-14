"""Oedometer rules E001, E002, E004 and E005 (qc.md §4.15; m19a AC 10, 11).

The cases are qc_defects.ags's four specimens on BH2-U1; built cases put a
value exactly at each tolerance, which raises nothing.
"""

import pytest

from .conftest import found, group, make_files

SPECIMEN = make_files.SPECIMEN
KEY = ["BH1", 1.00, "1", "U", "BH1-U1"]
LOCA = group(
    "LOCA",
    [("LOCA_ID", "ID", ""), ("LOCA_GL", "2DP", "m"), ("LOCA_FDEP", "2DP", "m")],
    [["BH1", 10.00, 10.00]],
)
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
CONS_HEADINGS = [
    *SPECIMEN,
    ("CONS_INCN", "X", ""),
    ("CONS_IVR", "3DP", ""),
    ("CONS_INCF", "0DP", "kPa"),
    ("CONS_INCE", "3DP", ""),
]


def _cong(dry=None, particle=None, void_ratio=0.800):
    return group(
        "CONG",
        [
            *SPECIMEN,
            ("CONG_DDEN", "2DP", "Mg/m3"),
            ("CONG_PDEN", "XN", "Mg/m3"),
            ("CONG_IVR", "3DP", ""),
        ],
        [[*KEY, "O1", 1.10, dry, particle, void_ratio]],
    )


def _cons(*increments, headings=CONS_HEADINGS):
    return group(
        "CONS", headings, [[*KEY, "O1", 1.10, *values] for values in increments]
    )


def _messages(report, rule_id):
    return report.findings.query("rule_id == @rule_id")["message"].tolist()


def test_ac10_each_rule_at_its_case(projects):
    report = projects["qc_defects"].qc()
    assert found(report, "E001") == [("BH2", "CONS_IVR", 218)]
    assert found(report, "E002") == [("BH2", "CONS_INCE", 220)]
    assert found(report, "E004") == [("BH2", "CONS_INCN", 224)]
    assert found(report, "E005") == [("BH2", "CONG_IVR", 211)]
    severity = report.rules.set_index("rule_id")["severity"]
    assert set(severity[["E001", "E002", "E004", "E005"]]) == {"warning"}


def test_ac10_messages_give_the_differences(projects):
    report = projects["qc_defects"].qc()
    [e001] = _messages(report, "E001")
    assert e001.startswith("CONS_IVR 0.690 in BH2 at 1.10 m")
    assert "increment 2 differs by 0.010" in e001
    assert "CONS_INCE 0.700" in e001
    [e002] = _messages(report, "E002")
    assert "increment 2 rose by 0.005 (to CONS_INCE 0.781)" in e002
    assert "200 kPa" in e002 and "swells" in e002
    [e004] = _messages(report, "E004")
    assert e004.startswith("CONS_INCN 3 in BH2 at 1.30 m")
    assert "after increment 4" in e004
    [e005] = _messages(report, "E005")
    assert e005.startswith("CONG_IVR 0.650 in BH2 at 1.40 m")
    assert "differs by 0.150 from ρs / ρd - 1 = 0.800" in e005
    assert "(the file's values)" in e005


def test_records_checked(projects):
    rules = projects["qc_defects"].qc().rules.set_index("rule_id")
    # Five pairs of increments; E002 the five whose stress went up; E004 all
    # eight numbered increments; E005 the one specimen with both densities.
    assert rules.loc[["E001", "E002", "E004", "E005"], "records_checked"].tolist() == [
        5,
        5,
        8,
        1,
    ]


@pytest.mark.parametrize("name", ["site_si", "site_us", "site_v404"])
def test_ac11_good_files_raise_no_e_finding(projects, name):
    findings = projects[name].qc().findings
    assert not findings["rule_id"].str.startswith("E").any()
    oedometer = findings[findings["group"].isin(["CONG", "CONS"])]
    assert "C001" not in set(oedometer["rule_id"])
    assert "C002" not in set(oedometer["rule_id"])


def test_e001_e002_at_the_tolerance_raise_nothing(build):
    # 0.700 to 0.702 is exactly 0.002 (E001); 0.702 to 0.704 under a larger
    # load is exactly 0.002 up (E002).
    project = build(
        LOCA,
        SAMP,
        _cong(),
        _cons(["1", 0.720, 50, 0.700], ["2", 0.702, 100, 0.704]),
    )
    report = project.qc()
    assert found(report, "E001") == []
    assert found(report, "E002") == []


def test_e001_e002_just_past_the_tolerance(build):
    project = build(
        LOCA,
        SAMP,
        _cong(),
        _cons(["1", 0.720, 50, 0.700], ["2", 0.703, 100, 0.706]),
    )
    report = project.qc()
    assert len(found(report, "E001")) == 1
    assert len(found(report, "E002")) == 1


def test_e001_tolerance_widens_with_coarser_void_ratios(build):
    # 4.0.4 types: CONS_INCE 2DP and CONS_IVR 3DP, so 0.005 + 0.0005 apart is
    # rounding (0.78 is 0.776 to 2DP).
    headings = [(h, "2DP" if h == "CONS_INCE" else t, u) for h, t, u in CONS_HEADINGS]
    project = build(
        LOCA,
        SAMP,
        _cong(),
        _cons(["1", 0.788, 50, 0.78], ["2", 0.776, 100, 0.75], headings=headings),
    )
    assert found(project.qc(), "E001") == []


def test_e002_unloading_and_equal_stress_arent_checked(build):
    project = build(
        LOCA,
        SAMP,
        _cong(),
        _cons(
            ["1", 0.720, 200, 0.700],
            ["2", 0.700, 100, 0.710],  # unloading swells
            ["3", 0.710, 100, 0.720],  # flooded at one stress
        ),
    )
    report = project.qc()
    assert found(report, "E002") == []
    assert report.rules.set_index("rule_id").loc["E002", "records_checked"] == 0


def test_e004_skips_text_and_names_the_largest(build):
    project = build(
        LOCA,
        SAMP,
        _cong(),
        _cons(
            ["1", 0.800, 25, 0.795],
            ["Flood", 0.795, 25, 0.790],
            ["3", 0.790, 50, 0.785],
            ["2", 0.785, 100, 0.780],
            ["2a", 0.780, 200, 0.770],
            ["4", 0.770, 400, 0.750],
        ),
    )
    report = project.qc()
    [message] = _messages(report, "E004")
    assert message.startswith("CONS_INCN 2 in BH1")
    assert "after increment 3" in message
    # Five numbered increments; "Flood" and "2a" aren't numbers.
    assert report.rules.set_index("rule_id").loc["E004", "records_checked"] == 4


def test_e005_at_the_tolerance_and_assumed(build):
    # 2.70 / 1.50 - 1 = 0.800: 0.820 is exactly 0.02 off; 0.821 is past it.
    assert found(build(LOCA, SAMP, _cong(1.50, "2.70", 0.820)).qc(), "E005") == []
    report = build(LOCA, SAMP, _cong(1.50, "#2.70", 0.821)).qc()
    [message] = _messages(report, "E005")
    assert "differs by 0.021" in message
    assert "an assumed particle density (#)" in message


def test_e005_needs_all_three(build):
    report = build(LOCA, SAMP, _cong(None, "2.70", 0.650)).qc()
    assert found(report, "E005") == []
    assert report.rules.set_index("rule_id").loc["E005", "records_checked"] == 0
