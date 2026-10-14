"""The project database: the only module that talks to SQLite (SPEC §7).

The layout is in docs/data/ingest.md §4. A database is built in one go into a
temporary file next to it and moved into place at the end, so a failed ingest
never leaves a half-built database. Reads use a read-only connection.
"""

import datetime as dt
import json
import os
import secrets
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from hangtu.errors import HangtuError

if TYPE_CHECKING:
    from hangtu.ags import Ingest

# Raise whenever the layout changes; open() compares it for equality.
SCHEMA_VERSION = 1
# STRICT tables need SQLite 3.37 (2021).
MINIMUM_SQLITE = (3, 37, 0)

_META_TABLES = {
    "specimen": [
        ("specimen_id", "INTEGER PRIMARY KEY"),
        ("sample_id", "INTEGER"),
        ("SPEC_REF", "TEXT"),
        ("SPEC_DPTH", "REAL"),
    ],
    "value_flag": [
        ("group", "TEXT"),
        ("_row", "INTEGER"),
        ("heading", "TEXT"),
        ("flag", "TEXT"),
        ("bound", "REAL"),
        ("text", "TEXT"),
    ],
    "finding": [
        ("rule", "TEXT"),
        ("severity", "TEXT"),
        ("group", "TEXT"),
        ("heading", "TEXT"),
        ("_line", "INTEGER"),
        ("message", "TEXT"),
    ],
    "meta_project": [("key", "TEXT PRIMARY KEY"), ("value", "TEXT")],
    "meta_source": [
        ("path", "TEXT"),
        ("sha256", "TEXT"),
        ("size", "INTEGER"),
        ("ags_version", "TEXT"),
        ("ags_version_source", "TEXT"),
        ("ingested_at", "TEXT"),
        ("hangtu_version", "TEXT"),
        ("schema_version", "INTEGER"),
    ],
    "meta_heading": [
        ("group", "TEXT"),
        ("heading", "TEXT"),
        ("file_unit", "TEXT"),
        ("file_type", "TEXT"),
        ("unit", "TEXT"),
        ("quantity", "TEXT"),
        ("status", "TEXT"),
        ("standard", "INTEGER"),
    ],
}


def quote(name: str) -> str:
    """Quote an SQL identifier: ``group`` is a keyword, and headings vary."""
    return '"' + name.replace('"', '""') + '"'


def check_sqlite() -> None:
    """Raise if the SQLite in this Python is too old for STRICT tables."""
    if sqlite3.sqlite_version_info < MINIMUM_SQLITE:
        raise HangtuError(
            f"hangtu needs SQLite {'.'.join(map(str, MINIMUM_SQLITE))} or newer, but "
            f"this Python has {sqlite3.sqlite_version}. Install a newer Python."
        )


# --- Writing ---------------------------------------------------------------------


def write(
    path: str | os.PathLike[str],
    result: "Ingest",
    settings: Mapping[str, Any],
    hangtu_version: str,
) -> None:
    """Build the database for ``result`` at ``path``, replacing any file there."""
    check_sqlite()
    path = Path(path)
    temporary = path.with_name(f"{path.name}.tmp-{secrets.token_hex(4)}")
    try:
        with closing(sqlite3.connect(temporary)) as connection, connection:
            _write_all(connection, result, settings, hangtu_version)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_all(connection, result, settings, hangtu_version) -> None:
    ags = result.ags
    for group, table in ags.tables.items():
        raw = [("_line", "INTEGER"), *((h, "TEXT") for h in ags.headings[group])]
        _create(connection, f"raw_{group}", raw)
        _insert(
            connection,
            f"raw_{group}",
            [c for c, _ in raw],
            table.itertuples(index=False),
        )

        types = result.sql_types[group]
        columns = [
            ("_row", "INTEGER PRIMARY KEY"),
            ("_line", "INTEGER"),
            *types.items(),
        ]
        _create(connection, group, columns)
        names = ["_row", "_line", *types]
        values = result.canonical[group]
        rows = zip(
            range(1, len(table) + 1),
            (int(line) for line in table["_line"]),
            *(values[name] for name in types),
            strict=True,
        )
        _insert(connection, group, names, rows)

    for name, columns in _META_TABLES.items():
        _create(connection, name, columns)
    _insert_dicts(connection, "specimen", result.specimens)
    _insert(
        connection,
        "value_flag",
        [c for c, _ in _META_TABLES["value_flag"]],
        ((g, f.row, f.heading, f.flag, f.bound, f.text) for g, f in result.flags),
    )
    _insert(
        connection,
        "finding",
        [c for c, _ in _META_TABLES["finding"]],
        (
            (f.rule, f.severity, f.group, f.heading, f.line, f.message)
            for f in result.findings
        ),
    )
    _write_settings(connection, settings)
    _insert(
        connection,
        "meta_source",
        [c for c, _ in _META_TABLES["meta_source"]],
        [
            (
                str(ags.path),
                ags.sha256,
                ags.size,
                ags.version,
                ags.version_source,
                dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                hangtu_version,
                SCHEMA_VERSION,
            )
        ],
    )
    _insert(
        connection,
        "meta_heading",
        [c for c, _ in _META_TABLES["meta_heading"]],
        (
            (
                h.group,
                h.heading,
                h.file_unit,
                h.file_type,
                h.unit,
                h.quantity,
                h.status,
                int(h.standard),
            )
            for h in result.headings.values()
        ),
    )


def _create(connection, table: str, columns: Iterable[tuple[str, str]]) -> None:
    body = ", ".join(f"{quote(name)} {sql_type}" for name, sql_type in columns)
    connection.execute(f"CREATE TABLE {quote(table)} ({body}) STRICT")


def _insert(
    connection, table: str, names: Sequence[str], rows: Iterable[Sequence]
) -> None:
    marks = ", ".join("?" * len(names))
    columns = ", ".join(map(quote, names))
    connection.executemany(
        f"INSERT INTO {quote(table)} ({columns}) VALUES ({marks})", rows
    )


def _insert_dicts(connection, table: str, rows: list[dict[str, Any]]) -> None:
    names = [c for c, _ in _META_TABLES[table]]
    _insert(connection, table, names, ([row[n] for n in names] for row in rows))


def _write_settings(connection, settings: Mapping[str, Any]) -> None:
    connection.executemany(
        "INSERT OR REPLACE INTO meta_project (key, value) VALUES (?, ?)",
        [(key, json.dumps(value)) for key, value in settings.items()],
    )


def write_settings(path: str | os.PathLike[str], settings: Mapping[str, Any]) -> None:
    """Store project settings in ``meta_project``."""
    with closing(sqlite3.connect(path)) as connection, connection:
        _write_settings(connection, settings)


# --- Reading ---------------------------------------------------------------------


def connect_read_only(path: str | os.PathLike[str]) -> sqlite3.Connection:
    """Open ``path`` read-only; a URI, so Windows paths and spaces work."""
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)


def read_sql(
    path: str | os.PathLike[str], sql: str, params: Sequence = ()
) -> pd.DataFrame:
    """Run a query on a read-only connection; a write raises ``sqlite3.Error``."""
    with closing(connect_read_only(path)) as connection:
        return pd.read_sql_query(sql, connection, params=params)


def read_table(path: str | os.PathLike[str], table: str) -> pd.DataFrame:
    """Return a whole table, in row order."""
    return read_sql(path, f"SELECT * FROM {quote(table)} ORDER BY rowid")


def tables(path: str | os.PathLike[str]) -> list[str]:
    """Return the names of every table in the database."""
    found = read_sql(path, "SELECT name FROM sqlite_master WHERE type = 'table'")
    return list(found["name"])


def read_source(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Return the ``meta_source`` row."""
    return read_table(path, "meta_source").iloc[0].to_dict()


def read_settings(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Return the stored project settings."""
    rows = read_table(path, "meta_project")
    return {
        key: json.loads(value)
        for key, value in zip(rows["key"], rows["value"], strict=True)
    }


def read_findings(path: str | os.PathLike[str]) -> pd.DataFrame:
    """Return the findings stored at ingest, in the order they were raised."""
    return read_table(path, "finding")


def read_flags(path: str | os.PathLike[str]) -> pd.DataFrame:
    """Return the value flags (``NP``, ``LT``, ``REFUSAL``, ...) of every cell."""
    return read_table(path, "value_flag")


def read_headings(path: str | os.PathLike[str]) -> pd.DataFrame:
    """Return ``meta_heading``: each heading's file unit, type, unit and kind."""
    return read_table(path, "meta_heading")
