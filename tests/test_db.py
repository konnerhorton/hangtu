"""The project database (SPEC §7, docs/data/ingest.md §4)."""

import csv
import io
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from hangtu import ags, db

DATA = Path(__file__).parent / "data" / "ags"
SETTINGS = {
    "display_units": "US",
    "vertical_datum": "NAVD88",
    "figure_sizes": {"default": [6.5, 4.5]},
}


@pytest.fixture(scope="module")
def site_db(tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "site.sqlite"
    db.write(path, ags.ingest(DATA / "site_si.ags"), SETTINGS, "0.0.test")
    return path


def _file_rows(path):
    """Each group's DATA rows as the file has them: (line, values)."""
    text = path.read_bytes().decode("utf-8")
    rows, group = {}, None
    for number, line in enumerate(csv.reader(io.StringIO(text, newline="")), start=1):
        if not line:
            continue
        if line[0] == "GROUP":
            group = line[1]
            rows[group] = []
        elif line[0] == "DATA":
            rows[group].append((number, line[1:]))
    return rows


def test_sqlite_is_new_enough_for_strict_tables():
    assert sqlite3.sqlite_version_info >= db.MINIMUM_SQLITE
    db.check_sqlite()


def test_every_table_is_strict(site_db):
    sql = db.read_sql(
        site_db, "SELECT name, sql FROM sqlite_master WHERE type = 'table'"
    )
    assert all(text.rstrip().endswith("STRICT") for text in sql["sql"]), sql


def test_raw_layer_is_the_file_text(site_db):
    # AC 2: every raw cell equals the file's text, and _line points at its DATA line.
    for group, rows in _file_rows(DATA / "site_si.ags").items():
        raw = db.read_table(site_db, f"raw_{group}")
        assert list(raw["_line"]) == [line for line, _ in rows], group
        assert raw.drop(columns="_line").values.tolist() == [
            values for _, values in rows
        ], group


def test_canonical_tables(site_db):
    loca = db.read_table(site_db, "LOCA")
    assert list(loca.columns[:4]) == ["_row", "_line", "location_id", "LOCA_ID"]
    assert list(loca["_row"]) == [1, 2, 3]
    assert list(loca["LOCA_GL"]) == [12.40, 11.85, 13.10]
    assert set(db.tables(site_db)) >= {
        "LOCA",
        "raw_LOCA",
        "XPPT",
        "specimen",
        "finding",
    }


def test_meta_tables(site_db):
    source = db.read_source(site_db)
    assert source["sha256"] == ags.ingest(DATA / "site_si.ags").ags.sha256
    assert (source["ags_version"], source["schema_version"]) == (
        "4.2",
        db.SCHEMA_VERSION,
    )
    assert source["hangtu_version"] == "0.0.test"
    assert db.read_settings(site_db) == SETTINGS
    heading = db.read_sql(
        site_db,
        'SELECT * FROM meta_heading WHERE "group" = ? AND heading = ?',
        ("PTST", "PTST_BDEN"),
    ).iloc[0]
    assert (
        heading["unit"],
        heading["quantity"],
        heading["status"],
        heading["standard"],
    ) == (
        "Mg/m3",
        "density",
        "converted",
        1,
    )
    flags = db.read_table(site_db, "value_flag")
    assert ("LLPL", 2, "LLPL_PL", "NP") in set(
        zip(flags["group"], flags["_row"], flags["heading"], flags["flag"], strict=True)
    )


def test_findings_are_stored(tmp_path):
    path = tmp_path / "defects.sqlite"
    db.write(path, ags.ingest(DATA / "defects.ags"), {}, "0.0.test")
    found = db.read_table(path, "finding")
    u001 = found[found["rule"] == "U001"].iloc[0]
    assert (u001["group"], u001["heading"], u001["severity"]) == (
        "LOCA",
        "LOCA_FDEP",
        "error",
    )
    assert u001["_line"] > 0


def test_reads_are_read_only(site_db):
    with pytest.raises(pd.errors.DatabaseError, match="readonly database"):
        db.read_sql(site_db, "DELETE FROM LOCA")


def test_a_failed_write_leaves_the_old_database(tmp_path, monkeypatch):
    path = tmp_path / "site.sqlite"
    result = ags.ingest(DATA / "site_si.ags")
    db.write(path, result, SETTINGS, "0.0.test")
    before = path.read_bytes()

    def fail(*args):
        raise RuntimeError("disk full")

    monkeypatch.setattr(db, "_write_all", fail)
    with pytest.raises(RuntimeError):
        db.write(path, result, SETTINGS, "0.0.test")
    assert path.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["site.sqlite"]


def test_write_replaces_an_existing_database(tmp_path):
    path = tmp_path / "site.sqlite"
    db.write(path, ags.ingest(DATA / "site_si.ags"), {}, "0.0.test")
    db.write(path, ags.ingest(DATA / "site_v404.ags"), {}, "0.0.test")
    assert db.read_source(path)["ags_version"] == "4.0.4"
    assert "FGHG" not in db.tables(path)


def test_settings_can_be_rewritten(tmp_path):
    path = tmp_path / "site.sqlite"
    db.write(
        path, ags.ingest(DATA / "site_si.ags"), {"display_units": "US"}, "0.0.test"
    )
    db.write_settings(path, {"display_units": "SI"})
    assert db.read_settings(path) == {"display_units": "SI"}


def test_quote():
    assert db.quote("group") == '"group"'
    assert db.quote('a"b') == '"a""b"'


def test_paths_with_spaces(tmp_path):
    path = tmp_path / "my project" / "site data.sqlite"
    path.parent.mkdir()
    db.write(path, ags.ingest(DATA / "site_si.ags"), {}, "0.0.test")
    assert len(db.read_table(path, "LOCA")) == 3
