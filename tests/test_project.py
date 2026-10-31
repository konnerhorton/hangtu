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
    assert project.groups[:3] == ["PROJ", "TRAN", "DICT"]
    last = ["IDEN", "TREG", "TRET", "TRIG", "TRIT", "UNIT", "TYPE", "ABBR"]
    assert project.groups[-8:] == last


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
    with ht.settings.override(hints=False):
        p = ht.Project.from_ags(site, display_units="SI")
    assert p.settings.display_units == "SI"
    assert p.settings.hints is False  # from ht.settings at ingest
    p.settings.display_units = "US"
    with pytest.raises(ht.HangtuError, match='display_units must be "US" or "SI"'):
        p.settings.display_units = "XX"
    assert ht.Project.open(p.path).settings.display_units == "US"
    assert "figure_sizes" in repr(p.settings)


def test_a_datum_not_in_the_table_hints_once_when_set(project):
    with pytest.warns(ht.HangtuHint, match='"Site datum" isn\'t in the datum table'):
        project.settings.vertical_datum = "Site datum"
    assert project.settings.vertical_datum == "Site datum"  # read back quietly


def _source(p):
    return db.read_settings(p.path)["vertical_datum_source"]


def test_vertical_datum_comes_from_loca_datm(project):
    # AC 1: NAVD88 in every hole of site_si.ags, no setting.
    assert project.settings.vertical_datum == "NAVD88"
    assert _source(project) == "LOCA_DATM"
    assert "vertical_datum='NAVD88',  # from LOCA_DATM" in repr(project.settings)
    assert "vertical_datum_source" not in repr(project.settings)


def test_vertical_datum_argument_wins_over_the_file(site):
    # AC 4.
    p = ht.Project.from_ags(site, vertical_datum="NGVD29")
    assert (p.settings.vertical_datum, _source(p)) == ("NGVD29", "setting")
    assert "vertical_datum='NGVD29',  # set" in repr(p.settings)


def test_vertical_datum_argument_none_wins_over_the_file(site):
    p = ht.Project.from_ags(site, vertical_datum=None)
    assert (p.settings.vertical_datum, _source(p)) == (None, None)


def test_the_file_wins_over_the_session_setting(site):
    # AC 4.
    with ht.settings.override(vertical_datum="NGVD29"):
        p = ht.Project.from_ags(site)
    assert (p.settings.vertical_datum, _source(p)) == ("NAVD88", "LOCA_DATM")


def test_the_session_setting_applies_when_the_file_has_no_datum(tmp_path):
    path = tmp_path / "plain.ags"
    path.write_text(
        (DATA / "site_si.ags").read_text(encoding="utf-8").replace("NAVD88", ""),
        encoding="utf-8",
    )
    with ht.settings.override(vertical_datum="NGVD29"):
        p = ht.Project.from_ags(path)
    assert (p.settings.vertical_datum, _source(p)) == ("NGVD29", "setting")


def test_setting_the_datum_later_changes_its_source(project):
    # AC 4.
    project.settings.vertical_datum = "NGVD 29"
    assert (project.settings.vertical_datum, _source(project)) == ("NGVD29", "setting")
    project.settings.vertical_datum = None
    assert _source(project) is None


def test_a_datum_not_in_the_table_is_read_once_added(tmp_path):
    # AC 2.
    path = tmp_path / "anytown.ags"
    path.write_text(
        (DATA / "site_si.ags")
        .read_text(encoding="utf-8")
        .replace("NAVD88", "Anytown datum"),
        encoding="utf-8",
    )
    p = ht.Project.from_ags(path)
    assert p.settings.vertical_datum is None
    ht.add_vertical_datum("ATD", name="Anytown datum")
    p = ht.Project.from_ags(path, overwrite=True)
    assert (p.settings.vertical_datum, _source(p)) == ("ATD", "LOCA_DATM")


def test_geology_key_is_a_project_setting(site):
    with ht.settings.override(geology_key="GEOL_LEG"):
        p = ht.Project.from_ags(site, geology_key="GEOL_FORM")
    assert p.settings.geology_key == "GEOL_FORM"
    p.settings.geology_key = "GEOL_GEOL"
    assert ht.Project.open(p.path).settings.geology_key == "GEOL_GEOL"
    with pytest.raises(ht.HangtuError, match="must be one of GEOL_GEOL"):
        p.settings.geology_key = "GEOL_DESC"


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


# --- The judgments file (docs/work/m13a-judgments.md, Decision 5) -----------------

JUDGMENTS = """\
water_level:
  units: {depth: m}
  project: {depth: 3.0, reason: assumed}
"""


def _write_judgments(path, text=JUDGMENTS):
    path.write_text(text, encoding="utf-8")
    return path


def test_set_judgments_reads_back_and_removes(project, tmp_path):
    assert project.judgments is None
    path = _write_judgments(tmp_path / "judgments.yaml")
    project.set_judgments(path)
    assert project.judgments.path == path.resolve()
    assert db.read_settings(project.path)["judgments_path"] == "judgments.yaml"
    project.set_judgments(None)
    assert project.judgments is None


def test_judgments_path_isnt_a_setting(project, tmp_path):
    project.set_judgments(_write_judgments(tmp_path / "judgments.yaml"))
    assert "judgments_path" not in repr(project.settings)


def test_a_relative_path_survives_moving_the_folder(tmp_path):
    # Criterion 8.
    folder = tmp_path / "job"
    folder.mkdir()
    shutil.copy(DATA / "site_si.ags", folder / "site.ags")
    (folder / "inputs").mkdir()
    _write_judgments(folder / "inputs" / "judgments.yaml")
    p = ht.Project.from_ags(folder / "site.ags")
    p.set_judgments(folder / "inputs" / "judgments.yaml")
    moved = tmp_path / "archive" / "job"
    moved.parent.mkdir()
    shutil.move(folder, moved)
    p = ht.Project.open(moved / "site.sqlite")
    assert p.judgments.path == (moved / "inputs" / "judgments.yaml").resolve()


def test_a_path_outside_the_folder_is_stored_absolute(project, tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    sub = project.path.parent / "db"
    sub.mkdir()
    moved = sub / "site.sqlite"
    shutil.copy(project.path, moved)
    p = ht.Project.open(moved)
    path = _write_judgments(elsewhere / "judgments.yaml")
    p.set_judgments(path)
    assert db.read_settings(moved)["judgments_path"] == str(path.resolve())


def test_a_bad_file_errors_on_set_and_nothing_is_stored(project, tmp_path):
    path = _write_judgments(tmp_path / "judgments.yaml", "unitweight: {}")
    with pytest.raises(ht.HangtuError, match="'unitweight' isn't a judgment"):
        project.set_judgments(path)
    assert project.judgments is None


def test_a_missing_file_errors_naming_set_judgments(project, tmp_path):
    path = _write_judgments(tmp_path / "judgments.yaml")
    project.set_judgments(path)
    path.unlink()
    with pytest.raises(ht.HangtuError, match=r"isn't there.*p.set_judgments"):
        project.judgments  # noqa: B018


def test_every_dataset_carries_the_judgments_file(project, tmp_path):
    assert "judgments_file" not in project.spt().attrs
    path = _write_judgments(tmp_path / "judgments.yaml")
    project.set_judgments(path)
    expected = str(path.resolve())
    project.set_geology_map(DATA / "strata.csv")
    for name in (
        "spt",
        "atterberg",
        "grain_size",
        "grain_size_summary",
        "index_properties",
        "permeability",
        "stratigraphy",
    ):
        assert getattr(project, name)().attrs["judgments_file"] == expected, name
    assert project.locations.attrs["judgments_file"] == expected


def test_a_rebuild_starts_without_judgments(project, site, tmp_path):
    project.set_judgments(_write_judgments(tmp_path / "judgments.yaml"))
    p = ht.Project.from_ags(site, db=project.path, overwrite=True)
    assert p.judgments is None
