"""Ingest acceptance criteria, end to end through ht.Project (ingest.md §12).

AC 2 (raw fidelity) is in tests/test_db.py; AC 4 (keys) in tests/ags/test_keys.py;
AC 6 (flags) in tests/ags/test_values.py; AC 8, 9 and 10 (open, atomic, read-only
SQL) in tests/test_project.py.
"""

import warnings
from pathlib import Path

import pandas as pd
import pytest

import hangtu as ht

DATA = Path(__file__).parents[1] / "data" / "ags"
# Groups that describe the file rather than the data: they differ between twins.
FILE_GROUPS = {"UNIT", "TYPE", "DICT"}


@pytest.fixture(scope="module")
def projects(tmp_path_factory):
    folder = tmp_path_factory.mktemp("acceptance")
    return {
        name: ht.Project.from_ags(DATA / f"{name}.ags", db=folder / f"{name}.sqlite")
        for name in ("site_si", "site_us", "site_v404", "defects")
    }


def assert_same_table(a, b, where):
    """Equal keys and text; numbers to 1e-9 relative."""
    assert list(a.columns) == list(b.columns), where
    for column in a.columns:
        if pd.api.types.is_float_dtype(a[column]):
            pd.testing.assert_series_equal(
                a[column], b[column], rtol=1e-9, atol=0, obj=f"{where}.{column}"
            )
        else:
            assert a[column].tolist() == b[column].tolist(), f"{where}.{column}"


def flags(project):
    return project.sql(
        'SELECT "group", _row, heading, flag, bound FROM value_flag '
        'ORDER BY "group", _row, heading'
    )


def test_ac1_twin_files_give_identical_canonical_tables(projects):
    si, us = projects["site_si"], projects["site_us"]
    assert si.groups == us.groups
    for group in si.groups:
        if group not in FILE_GROUPS:
            # _line is provenance: the twins' UNIT groups differ in length.
            a, b = (p.table(group).drop(columns="_line") for p in (si, us))
            assert_same_table(a, b, group)
    assert_same_table(flags(si), flags(us), "value_flag")
    assert_same_table(
        si.sql("SELECT * FROM specimen"), us.sql("SELECT * FROM specimen"), "specimen"
    )


def test_ac1_twin_files_declare_the_same_canonical_units(projects):
    query = (
        'SELECT "group", heading, unit, status FROM meta_heading '
        "WHERE \"group\" NOT IN ('UNIT', 'TYPE', 'DICT')"
    )
    assert projects["site_si"].sql(query).equals(projects["site_us"].sql(query))


def test_ac3_older_version_gives_the_same_tables_for_shared_groups(projects):
    si, old = projects["site_si"], projects["site_v404"]
    shared = [
        g for g in old.groups if g in si.groups and g not in FILE_GROUPS | {"TRAN"}
    ]
    assert shared == [
        "PROJ",
        "ABBR",
        "LOCA",
        "GEOL",
        "SAMP",
        "ISPT",
        "LLPL",
        "LNMC",
        "GRAG",
        "GRAT",
        "PTST",
        "XPPT",
    ]
    for group in shared:
        a, b = si.table(group), old.table(group)
        columns = [c for c in b.columns if c in a.columns and c != "_line"]
        assert_same_table(a[columns], b[columns], group)


def test_ac3_removed_groups_and_headings_are_kept_typed_and_in_si(projects):
    old = projects["site_v404"]
    iprg = old.table("IPRG")
    assert list(iprg["IPRG_IPRM"]) == [4.0e-6, 4.4e-6]
    assert iprg.attrs["units"]["IPRG_IPRM"] == "m/s"
    assert list(iprg["location_id"]) == [3, 3]
    assert list(old.table("IPRT")["IPRT_TIME"]) == [0.0, 300.0, 4800.0]
    rucs = old.table("RUCS")
    assert list(rucs["RUCS_E"]) == [0.25]
    assert rucs.attrs["units"]["RUCS_E"] == "GPa"
    assert rucs.loc[0, "RUCS_DURN"] == 330.0  # mm:ss
    m001 = old.sql("SELECT \"group\", heading FROM finding WHERE rule = 'M001'")
    assert set(map(tuple, m001.fillna("").values)) == {
        ("IPRG", ""),
        ("IPRT", ""),
        ("RUCS", "RUCS_E"),
    }


def test_ac3_old_unit_spellings_convert_without_findings(projects):
    old = projects["site_v404"]
    assert set(old.sql("SELECT rule FROM finding")["rule"]) == {"M001"}
    assert list(old.table("LNMC")["LNMC_TEMP"]) == [105.0, 105.0, 105.0]
    assert old.table("SAMP").attrs["units"]["SAMP_BAR"] == "bar"


def test_ac5_pcf_by_heading(projects):
    si, us = projects["site_si"], projects["site_us"]
    assert list(us.table("PTST")["PTST_BDEN"]) == pytest.approx(
        [1.85, 1.78], rel=1e-9
    )  # density
    assert list(us.table("CPTP")["CPTP_SUW1"]) == pytest.approx(
        [18.5, 19.2], rel=1e-9
    )  # unit weight
    assert si.table("PTST").attrs["units"]["PTST_BDEN"] == "Mg/m3"
    assert si.table("CPTP").attrs["units"]["CPTP_SUW1"] == "kN/m3"


@pytest.mark.parametrize(
    ("rule", "group", "heading"),
    [
        ("U001", "LOCA", "LOCA_FDEP"),
        ("U003", "ISPT", "ISPT_CAS"),
        ("U004", "LOCA", "LOCA_NATE"),
    ],
)
def test_ac5_unconvertible_columns_are_blank_with_the_raw_text_kept(
    projects, rule, group, heading
):
    defects = projects["defects"]
    assert defects.table(group)[heading].isna().all()
    raw = defects.table(group, raw=True)[heading]
    assert (raw != "").any()
    status = defects.sql(
        'SELECT status FROM meta_heading WHERE "group" = ? AND heading = ?',
        (group, heading),
    )
    assert status["status"].tolist() == ["raw_only"]
    found = defects.sql("SELECT rule FROM finding WHERE heading = ?", (heading,))
    assert found["rule"].tolist() == [rule]


def test_ac5_a_unit_only_pint_knows_is_converted_with_u002(projects):
    defects = projects["defects"]
    assert defects.table("SAMP")["SAMP_BASE"].iloc[0] == pytest.approx(1.95 * 0.3048)
    found = defects.sql(
        "SELECT rule, severity FROM finding WHERE heading = 'SAMP_BASE'"
    )
    assert found.values.tolist() == [["U002", "info"]]


@pytest.mark.parametrize(
    ("rule", "project", "needs_heading"),
    [
        ("V000", "defects", True),
        ("V9", "defects", False),
        ("V10c", "defects", False),
        ("U001", "defects", True),
        ("U002", "defects", True),
        ("U003", "defects", True),
        ("U004", "defects", True),
        ("T001", "defects", True),
        ("M001", "site_v404", False),  # group-level for IPRG/IPRT
    ],
)
def test_ac7_each_ingest_rule_is_raised_with_group_heading_and_line(
    projects, rule, project, needs_heading
):
    found = projects[project].sql(
        "SELECT * FROM finding WHERE rule = ? AND _line IS NOT NULL", (rule,)
    )
    assert len(found), rule
    assert found["group"].notna().all()
    if needs_heading:
        assert found["heading"].notna().all()


def test_ac7_t001_names_the_cell(projects):
    found = projects["defects"].sql("SELECT * FROM finding WHERE rule = 'T001'").iloc[0]
    assert (found["group"], found["heading"]) == ("LNMC", "LNMC_MC")
    raw = projects["defects"].table("LNMC", raw=True)
    assert raw.loc[raw["_line"] == found["_line"], "LNMC_MC"].tolist() == ["wet"]


@pytest.mark.parametrize("name", ["site_si", "site_us", "site_v404"])
def test_ac11_ingesting_a_good_file_is_quiet(tmp_path, capsys, name):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        p = ht.Project.from_ags(DATA / f"{name}.ags", db=tmp_path / "p.sqlite")
        ht.Project.open(p.path)
    assert caught == []
    assert capsys.readouterr() == ("", "")
