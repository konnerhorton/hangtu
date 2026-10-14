"""AGS4 ingest: read a file into the tables of a project database.

Specified in docs/data/ingest.md. ``ingest()`` runs the pipeline of §3 in
memory; ``hangtu.db`` writes the result.
"""

from dataclasses import dataclass
from os import PathLike
from typing import Any

from hangtu.ags import _dictionary, _keys, _read, _units, _values
from hangtu.ags._findings import Finding
from hangtu.ags._read import AgsText
from hangtu.ags._units import HeadingUnit
from hangtu.ags._values import ValueFlag

# SQLite column type for each kind of value (ingest.md §7).
SQL_TYPES = {
    _units.NUMBER: "REAL",
    _units.TIME: "REAL",
    _units.DMS: "REAL",
    _units.YES_NO: "INTEGER",
    _units.DATE: "TEXT",
    _units.TEXT: "TEXT",
}


@dataclass
class Ingest:
    """Everything ingest found in one file, ready for ``hangtu.db`` to write.

    ``canonical[group]`` maps each column (surrogate keys, then headings) to its
    values in file order; ``sql_types`` gives each column's SQLite type.
    """

    ags: AgsText
    headings: dict[tuple[str, str], HeadingUnit]
    canonical: dict[str, dict[str, list[Any]]]
    sql_types: dict[str, dict[str, str]]
    flags: list[tuple[str, ValueFlag]]
    specimens: list[dict[str, Any]]
    findings: list[Finding]


def ingest(path: str | PathLike[str]) -> Ingest:
    """Read, type, convert, flag and key the AGS4 file at ``path``."""
    ags = _read.read(path)
    dictionary, removed = _dictionary.for_file(ags)
    headings, unit_findings = _units.resolve(ags, dictionary)
    keys = _keys.resolve(ags, dictionary)

    canonical: dict[str, dict[str, list[Any]]] = {}
    sql_types: dict[str, dict[str, str]] = {}
    flags: list[tuple[str, ValueFlag]] = []
    type_findings: list[Finding] = []
    for group, table in ags.tables.items():
        lines = list(table["_line"])
        columns = dict(keys.columns.get(group, {}))
        types = dict.fromkeys(columns, "INTEGER")
        for name in ags.headings[group]:
            heading = headings[group, name]
            values, cell_flags, found = _values.type_column(
                heading, list(table[name]), lines
            )
            columns[name] = values
            types[name] = SQL_TYPES[heading.kind]
            flags += [(group, flag) for flag in cell_flags]
            type_findings += found
        rows = table.to_dict("records")
        refusals = _values.refusal_flags(group, ags.headings[group], rows)
        flags += [(group, flag) for flag in refusals]
        canonical[group] = columns
        sql_types[group] = types

    return Ingest(
        ags=ags,
        headings=headings,
        canonical=canonical,
        sql_types=sql_types,
        flags=flags,
        specimens=_specimen_rows(keys, canonical),
        findings=[*ags.findings, *removed, *unit_findings, *type_findings],
    )


def _specimen_rows(
    keys: _keys.Keys, canonical: dict[str, dict[str, list[Any]]]
) -> list[dict[str, Any]]:
    """Build the ``specimen`` table, with ``SPEC_DPTH`` in canonical units.

    The depth comes from the first row that names the specimen, so the SI and
    US twins give the same table.
    """
    depths: dict[int, Any] = {}
    for columns in canonical.values():
        ids = columns.get(_keys.SPECIMEN)
        if ids is None:
            continue
        values = columns.get("SPEC_DPTH", [None] * len(ids))
        for specimen_id, depth in zip(ids, values, strict=True):
            if specimen_id is not None:
                depths.setdefault(specimen_id, depth)
    return [
        {**row, "SPEC_DPTH": depths.get(row[_keys.SPECIMEN])} for row in keys.specimens
    ]
