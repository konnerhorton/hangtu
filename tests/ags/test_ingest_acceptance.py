"""Ingest acceptance criteria, end to end through ht.Project (ingest.md §12).

AC 2 (raw fidelity) is in tests/test_db.py; AC 4 (keys) in tests/ags/test_keys.py;
AC 6 (flags) in tests/ags/test_values.py; AC 8, 9 and 10 (open, atomic, read-only
SQL) in tests/test_project.py.
"""

import importlib.util
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
        ("U001", "XUND", "XUND_BLOW"),
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


def test_ac5_a_unit_the_file_defines_is_kept_as_written_with_u005(projects):
    defects = projects["defects"]
    xund = defects.table("XUND")
    assert xund["XUND_SWEL"].tolist() == [1.25]
    assert xund.attrs["units"]["XUND_SWEL"] == "%/log cycle"
    heading = defects.sql(
        "SELECT unit, quantity, status FROM meta_heading WHERE heading = 'XUND_SWEL'"
    )
    assert heading.values.tolist() == [["%/log cycle", None, "file_unit"]]
    found = defects.sql(
        "SELECT rule, severity, message FROM finding WHERE heading = 'XUND_SWEL'"
    )
    assert found[["rule", "severity"]].values.tolist() == [["U005", "info"]]
    assert '("percent strain per log cycle of stress")' in found["message"].iloc[0]


def test_ac5_a_standard_heading_says_the_unit_group_defines_its_unit(projects):
    found = projects["defects"].sql(
        "SELECT message FROM finding WHERE heading = 'LOCA_FDEP'"
    )
    assert (
        'The file\'s UNIT group defines it as "foot (wrong case)", but LOCA_FDEP '
        'is a standard heading in "m".'
    ) in found["message"].iloc[0]


def test_ac5_kn_per_mm_keeps_its_unit_and_um_converts_to_m(projects):
    defects = projects["defects"]
    xund = defects.table("XUND")
    assert xund["XUND_STIF"].tolist() == [35.5]
    assert xund["XUND_SIZE"].tolist() == pytest.approx([75.0e-6], rel=1e-9)
    assert xund.attrs["units"]["XUND_STIF"] == "kN/mm"
    assert xund.attrs["units"]["XUND_SIZE"] == "m"
    found = defects.sql(
        "SELECT rule FROM finding WHERE heading IN ('XUND_STIF', 'XUND_SIZE')"
    )
    assert found.empty


def test_ac5_rucs_4_2_headings_are_typed_and_converted(tmp_path):
    script = DATA / "_make_files.py"
    spec = importlib.util.spec_from_file_location("_make_files", script)
    files = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(files)
    rucs = files.group(
        "RUCS",
        [
            *files.SPECIMEN,
            ("RUCS_UCS", "3SF", "MPa"),
            ("RUCS_ESEC", "3SF", "GPa"),
            ("RUCS_ETAN", "3SF", "GPa"),
            ("RUCS_MUS", "3SF", ""),
            ("RUCS_MUT", "3SF", ""),
        ],
        [[*files.BH1_U1, 1.20, 0.250, 0.310, 0.280, 0.300]],
    )
    path = tmp_path / "rucs.ags"
    files.write_file(path, "4.2", [files.LOCA, files.SAMP, rucs])
    p = ht.Project.from_ags(path, db=tmp_path / "rucs.sqlite")
    table = p.table("RUCS")
    columns = ["RUCS_ESEC", "RUCS_ETAN", "RUCS_MUS", "RUCS_MUT"]
    assert table[columns].iloc[0].tolist() == pytest.approx([0.25, 0.31, 0.28, 0.30])
    assert table.attrs["units"]["RUCS_ESEC"] == "GPa"
    assert table.attrs["units"]["RUCS_ETAN"] == "GPa"
    status = p.sql(
        "SELECT heading, status FROM meta_heading WHERE \"group\" = 'RUCS'"
    ).set_index("heading")["status"]
    assert status[["RUCS_ESEC", "RUCS_ETAN"]].tolist() == ["converted", "converted"]
    assert status[["RUCS_MUS", "RUCS_MUT"]].tolist() == ["as_is", "as_is"]
    found = p.sql("SELECT rule FROM finding WHERE rule = 'M001' OR rule LIKE 'U%'")
    assert found.empty


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
        ("U005", "defects", True),
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
