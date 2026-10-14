import pytest

from .conftest import found, group, loca


@pytest.fixture(scope="module")
def report(projects):
    return projects["qc_defects"].qc()


def test_c001_blank_required_field(report):
    # GEOL_DESC on line 77 is the case; BH5's blank LOCA_GL and LOCA_FDEP
    # (L001, L003) are a cascade, in one finding for the record.
    assert found(report, "C001") == [("BH5", "LOCA_GL", 58), ("BH4", "GEOL_DESC", 77)]
    messages = list(report.findings.query("rule_id == 'C001'")["message"])
    assert messages[0].startswith("Required LOCA_GL and LOCA_FDEP are blank in the ")


def test_c002_absent_heading_once(report):
    rows = report.findings.query("rule_id == 'C002' and heading == 'LOCA_TYPE'")
    assert len(rows) == 1
    assert rows["source_line"].isna().all()
    assert rows["message"].iloc[0].startswith("LOCA has no LOCA_TYPE heading")


def test_c002_counts_blanks(report):
    rows = report.findings.query("rule_id == 'C002' and heading == 'ISPT_ERAT'")
    assert rows["message"].iloc[0].startswith("ISPT_ERAT is blank in 2 of 11 ISPT")


def _llpl(*rows):
    headings = [
        ("LOCA_ID", "ID", ""),
        ("SAMP_TOP", "2DP", "m"),
        ("SAMP_REF", "X", ""),
        ("SAMP_TYPE", "PA", ""),
        ("SAMP_ID", "ID", ""),
        ("SPEC_REF", "X", ""),
        ("SPEC_DPTH", "2DP", "m"),
        ("LLPL_LL", "0DP", "%"),
        ("LLPL_PL", "XN", "%"),
    ]
    specimen = ["BH1", 1.0, "1", "U", "BH1-U1"]
    return group(
        "LLPL",
        headings,
        [[*specimen, str(i), 1.0, *row] for i, row in enumerate(rows, 1)],
    )


def test_flagged_value_is_not_missing(build):
    project = build(loca(["BH1", 0, 0, 10, 5]), _llpl([30, "NP"], [30, None]))
    report = project.qc()
    lines = list(project.table("LLPL")["_line"])
    assert found(report, "C001") == [("BH1", "LLPL_PL", lines[1])]


def test_absent_required_heading_is_one_finding(build):
    lnmc = group(
        "LNMC",
        [("LOCA_ID", "ID", ""), ("SAMP_TOP", "2DP", "m"), ("LNMC_MC", "0DP", "%")],
        [["BH1", 1.0, 20], ["BH1", 2.0, 25]],
    )
    report = build(loca(["BH1", 0, 0, 10, 5]), lnmc).qc()
    absent = report.findings.query("rule_id == 'C001' and group == 'LNMC'")
    assert set(absent["heading"]) == {
        "SAMP_REF",
        "SAMP_TYPE",
        "SAMP_ID",
    }
    assert absent["source_line"].isna().all()


def test_group_not_in_the_file_is_not_checked(build):
    report = build(loca(["BH1", 0, 0, 10, 5])).qc()
    assert set(report.findings.query("rule_id in ['C001', 'C002']")["group"]) == {
        "LOCA"
    }


def test_min_fields_override(build):
    project = build(loca(["BH1", 0, 0, 10, 5]))
    report = project.qc(
        min_fields={"LOCA": {"required": ["LOCA_ID"], "recommended": ["LOCA_TYPE"]}}
    )
    assert found(report, "C001") == []
    assert found(report, "C002") == [(None, "LOCA_TYPE", None)]
