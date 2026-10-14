"""ht.Project (docs/data/ingest.md §2, §10; AC 8, 9, 10)."""

import shutil
import sqlite3
from pathlib import Path

import pytest

import hangtu as ht
from hangtu import db

DATA = Path(__file__).parent / "data" / "ags"


@pytest.fixture
def site(tmp_path):
    """A copy of site_si.ags in tmp_path, so tests can change or move it."""
    path = tmp_path / "site.ags"
    shutil.copy(DATA / "site_si.ags", path)
    return path


@pytest.fixture
def project(site):
    return ht.Project.from_ags(site, db=site.with_name("site.sqlite"))


def test_from_ags_puts_the_database_next_to_the_file_by_default(site):
    p = ht.Project.from_ags(site)
    assert p.path == site.with_suffix(".sqlite") and p.path.is_file()


def test_groups_in_file_order(project):
    assert project.groups[:6] == ["PROJ", "TRAN", "UNIT", "TYPE", "ABBR", "DICT"]
    assert project.groups[-3:] == ["FGHG", "FGHS", "XPPT"]


def test_canonical_table(project):
    spt = project.table("ISPT")
    assert list(spt["ISPT_TOP"]) == [3.0, 6.0, 2.0, 5.0, 1.5]
    assert str(spt["location_id"].dtype) == "Int64"
    assert spt.attrs["units"]["ISPT_TOP"] == "m"
    assert "ISPT_NVAL" not in spt.attrs["units"]  # a count has no unit
    assert ht.units_of(spt)["ISPT_NPEN"] == "mm"
    assert str(project.table("GRAG")["GRAG_SUFF"].dtype) == "Int64"


def test_raw_table(project):
    raw = project.table("ISPT", raw=True)
    assert list(raw["ISPT_TOP"])[:2] == ["3.00", "6.00"]
    assert "_line" in raw and "location_id" not in raw


def test_unknown_group_lists_the_groups(project):
    with pytest.raises(ht.HangtuError, match=r"no group 'NOPE'\. Groups: PROJ, TRAN"):
        project.table("NOPE")


def test_sql(project):
    found = project.sql(
        "SELECT LOCA_ID, ISPT_NVAL FROM ISPT WHERE ISPT_NVAL > ?", (20,)
    )
    assert found.values.tolist() == [["BH1", 50.0], ["BH2", 30.0]]


def test_sql_is_read_only(project):
    # AC 10
    with pytest.raises(ht.HangtuError, match="read-only"):
        project.sql("DELETE FROM ISPT")
    assert len(project.table("ISPT")) == 5


def test_a_bad_query_says_why(project):
    with pytest.raises(ht.HangtuError, match=r"query failed: .*no such table: NOPE"):
        project.sql("SELECT * FROM NOPE")


def test_settings_are_stored_and_checked(site):
    with ht.settings.override(vertical_datum="NAVD88"):
        p = ht.Project.from_ags(site, display_units="SI")
    assert p.settings.display_units == "SI"
    assert p.settings.vertical_datum == "NAVD88"  # from ht.settings at ingest
    p.settings.display_units = "US"
    with pytest.raises(ht.HangtuError, match='display_units must be "US" or "SI"'):
        p.settings.display_units = "XX"
    assert ht.Project.open(p.path).settings.display_units == "US"
    assert "figure_sizes" in repr(p.settings)


def test_unknown_setting(site):
    with pytest.raises(ht.HangtuError, match="no setting 'colour'"):
        ht.Project.from_ags(site, colour="red")
    assert not site.with_suffix(".sqlite").exists()


def test_from_ags_on_an_existing_database(project, site):
    # AC 8
    with pytest.raises(
        ht.HangtuError,
        match=r"already exists\. Open it with ht\.Project\.open.*overwrite=True",
    ):
        ht.Project.from_ags(site, db=project.path)
    rebuilt = ht.Project.from_ags(site, db=project.path, overwrite=True)
    assert len(rebuilt.table("LOCA")) == 3


def test_open_reads_back_the_same_tables(project):
    # AC 8
    again = ht.Project.open(project.path)
    for group in project.groups:
        assert again.table(group).equals(project.table(group)), group


def test_open_works_without_the_ags_file(project, site):
    site.unlink()
    assert len(ht.Project.open(project.path).table("LOCA")) == 3  # no warning


def test_open_warns_when_the_ags_file_changed(project, site):
    site.write_bytes(site.read_bytes().replace(b"10.00", b"11.00", 1))
    with pytest.warns(
        UserWarning, match=r"has changed since .* out of date.*overwrite=True"
    ):
        ht.Project.open(project.path)


def test_open_a_database_from_another_schema(project):
    with sqlite3.connect(project.path) as connection:
        connection.execute("UPDATE meta_source SET schema_version = 0")
    connection.close()
    with pytest.raises(
        ht.HangtuError, match=r"can't read it\. Rebuild it .*overwrite=True"
    ):
        ht.Project.open(project.path)


def test_open_errors(tmp_path):
    with pytest.raises(FileNotFoundError, match="No project database"):
        ht.Project.open(tmp_path / "nope.sqlite")
    other = tmp_path / "other.sqlite"
    other.write_text("not a database")
    with pytest.raises(ht.HangtuError, match="isn't a hangtu project database"):
        ht.Project.open(other)


def test_a_parse_failure_writes_nothing(tmp_path, project):
    # AC 9
    bad = tmp_path / "bad.ags"
    text = (
        (DATA / "site_si.ags")
        .read_bytes()
        .replace(b'"DATA","BH1","CP"', b'"DATA","BH1"', 1)
    )
    bad.write_bytes(text)
    with pytest.raises(
        ht.AgsFileError, match="does not have the same number of entries"
    ):
        ht.Project.from_ags(bad)
    assert not bad.with_suffix(".sqlite").exists()
    before = project.path.read_bytes()
    with pytest.raises(ht.AgsFileError):
        ht.Project.from_ags(bad, db=project.path, overwrite=True)
    assert project.path.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "bad.ags",
        "site.ags",
        "site.sqlite",
    ]


def test_repr(project):
    text = repr(project)
    assert "site.ags (AGS 4.2)" in text
    assert "LOCA, GEOL" in text
    assert "findings: none" in text


def test_repr_counts_findings(tmp_path):
    p = ht.Project.from_ags(DATA / "defects.ags", db=tmp_path / "d.sqlite")
    assert "errors" in repr(p) and "info" in repr(p)


def test_database_matches_the_db_layer(project):
    assert db.read_source(project.path)["schema_version"] == db.SCHEMA_VERSION
