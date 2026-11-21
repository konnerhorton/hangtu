"""Oedometer rules E001-E005 (qc.md §4.15; m19a AC 10, 11; m19c Spec AC 8, 9).

The cases are qc_defects.ags's specimens on BH2-U1; built cases put a value
exactly at each tolerance, which raises nothing.
"""

import pytest

import hangtu as ht

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
    assert found(report, "E003") == [
        ("BH2", "CONS_INMV", 222),
        ("BH2", "CONS_INMV", 235),
    ]
    assert found(report, "E004") == [("BH2", "CONS_INCN", 224)]
    assert found(report, "E005") == [("BH2", "CONG_IVR", 211)]
    severity = report.rules.set_index("rule_id")["severity"]
    assert set(severity[["E001", "E002", "E003", "E004", "E005"]]) == {"warning"}


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
    # E001 the 16 pairs of increments (E5's 12 increments give 11); E002 the
    # 13 whose stress went up; E003 the 7 of those with a CONS_INMV (E4's
    # increment 2, E5's 2-6 and 11); E004 all 20 numbered increments; E005 the
    # one specimen with both densities.
    checked = rules.loc[["E001", "E002", "E003", "E004", "E005"], "records_checked"]
    assert checked.tolist() == [16, 13, 7, 20, 1]


def test_e003_messages(projects):
    report = projects["qc_defects"].qc()
    first, later = _messages(report, "E003")
    assert first.startswith("CONS_INMV 0.32 m2/MN in BH2 at 1.30 m")
    assert "increment 2 " in first
    assert "gives 0.134 to 0.178 m2/MN" in first
    assert "BS 1377-5:1990, 3.6.2.2.4" in first
    assert "1 + e0" in first
    assert later.startswith("CONS_INMV 0.061 m2/MN in BH2 at 1.40 m")
    assert "increment 11 " in later
    assert "gives 0.0677 to 0.0692 m2/MN" in later


MV_HEADINGS = [*CONS_HEADINGS, ("CONS_INMV", "2SF", "m2/MN")]


def _e003(build, *increments, headings=MV_HEADINGS):
    project = build(LOCA, SAMP, _cong(), _cons(*increments, headings=headings))
    return found(project.qc(), "E003")


def test_e003_interval_ends(build):
    # 100 to 200 kPa, e 0.776 to 0.748 at 3DP: 0.0275 / (1.7765 × 100) =
    # 0.154799 to 0.0285 / (1.7755 × 100) = 0.160518 m2/MN. A reported 0.15
    # spans 0.145 to 0.155 and overlaps; 0.14 (0.135 to 0.145) doesn't; 0.17
    # (0.165 to 0.175) doesn't.
    first = ["1", 0.800, 100, 0.776, None]
    assert _e003(build, first, ["2", 0.776, 200, 0.748, 0.15]) == []
    assert len(_e003(build, first, ["2", 0.776, 200, 0.748, 0.14])) == 1
    assert len(_e003(build, first, ["2", 0.776, 200, 0.748, 0.17])) == 1


def test_e003_two_significant_figure_floor(build):
    # 0.1499 written to 10SF, as a converted file writes it, would be
    # ± 5e-11, below 0.154799; at the 2SF floor it is 0.1449 to 0.1549 and
    # overlaps.
    headings = [*CONS_HEADINGS, ("CONS_INMV", "10SF", "m2/MN")]
    increments = (["1", 0.800, 100, 0.776, None], ["2", 0.776, 200, 0.748, 0.1499])
    assert _e003(build, *increments, headings=headings) == []


def test_e003_reads_the_start_from_the_previous_end(build):
    # No CONS_IVR on increment 2: e1 is the previous CONS_INCE, 0.776.
    increments = (["1", 0.800, 100, 0.776, None], ["2", None, 200, 0.748, 0.14])
    assert len(_e003(build, *increments)) == 1


def test_e003_skips_unloads_and_equal_stresses(build):
    increments = (
        ["1", 0.800, 200, 0.748, None],
        ["2", 0.748, 100, 0.760, 9.9],  # an unload
        ["3", 0.760, 100, 0.759, 9.9],  # no stress change
    )
    assert _e003(build, *increments) == []


def test_e003_in_us_units(build):
    # The interval end test above in psf and ft2/kip: 0.154799 to 0.160518 m2/MN
    # is 0.0074117 to 0.0076855 ft2/kip; 0.0075 overlaps, 0.0071 doesn't.
    headings = [
        *SPECIMEN,
        ("CONS_INCN", "X", ""),
        ("CONS_IVR", "3DP", ""),
        ("CONS_INCF", "10SF", "psf"),
        ("CONS_INCE", "3DP", ""),
        ("CONS_INMV", "2SF", "ft2/kip"),
    ]
    psf = 1000 * 0.3048**2 / 4.4482216152605  # psf per kPa
    first = ["1", 0.800, 100 * psf, 0.776, None]
    for reported, findings in ((0.0075, 0), (0.0071, 1)):
        second = ["2", 0.776, 200 * psf, 0.748, reported]
        assert len(_e003(build, first, second, headings=headings)) == findings


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


def test_e003_example_project_is_clean(tmp_path):
    # Its two specimens' m_v are 2SF ft2/kip written from their void ratios.
    project = ht.Project.from_ags(
        ht.examples.path("site.ags"), db=tmp_path / "site.sqlite"
    )
    report = project.qc()
    assert report.rules.set_index("rule_id").loc["E003", "records_checked"] > 0
    assert found(report, "E003") == []
