"""The project's data as QC rules read it (qc.md §4, "General behavior").

Each table is read once per run through ``db.py`` and kept. Rules never write:
every read goes through a read-only connection.
"""

import re
from dataclasses import dataclass
from functools import cached_property
from os import PathLike
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import hangtu.db as database
from hangtu import units

#: Order in which a record's depth is chosen for a finding (qc.md §5.1).
_DEPTH_ORDER = ("_TOP", "_DPTH", "SPEC_DPTH", "SAMP_TOP")


@dataclass(frozen=True)
class Flag:
    """A cell's value flag, as stored at ingest (ingest.md §8)."""

    flag: str
    bound: float | None
    text: str


@dataclass(frozen=True)
class Row:
    """Where a DATA line is: its group, canonical row, hole and depth in m."""

    group: str
    row: int
    loca_id: str | None
    depth: float | None


class Data:
    """Canonical tables, value flags and record depths of one project."""

    def __init__(
        self,
        path: str | PathLike[str],
        min_fields: dict[str, dict[str, tuple[str, ...]]] | None = None,
    ) -> None:
        self.path = Path(path)
        #: The project's stored settings (display units, vertical datum, ...).
        self.project_settings = database.read_settings(self.path)
        self.display_units: str = self.project_settings["display_units"]
        #: Minimally useful fields per group, after overrides (qc.md §4.10).
        self.min_fields = min_fields or {}
        self._tables: dict[str, pd.DataFrame] = {}
        self._raw: dict[str, pd.DataFrame] = {}

    @cached_property
    def headings(self) -> pd.DataFrame:
        """``meta_heading``: one row per (group, heading), in file order."""
        return database.read_headings(self.path)

    @cached_property
    def groups(self) -> list[str]:
        """The AGS groups in the file, in file order."""
        return list(dict.fromkeys(self.headings["group"]))

    def has(self, group: str, *headings: str) -> bool:
        """Return True if ``group`` is in the file with every one of ``headings``."""
        if group not in self.groups:
            return False
        present = set(self.headings.loc[self.headings["group"] == group, "heading"])
        return set(headings) <= present

    def table(self, group: str) -> pd.DataFrame:
        """Return the canonical table of ``group``: typed, in SI, with ``_line``."""
        if group not in self._tables:
            self._tables[group] = database.read_table(self.path, group)
        return self._tables[group]

    def raw(self, group: str) -> pd.DataFrame:
        """Return the file's text of ``group``, with ``_line``."""
        if group not in self._raw:
            self._raw[group] = database.read_table(self.path, f"raw_{group}")
        return self._raw[group]

    @cached_property
    def _flags(self) -> dict[tuple[str, int, str], Flag]:
        flags = database.read_flags(self.path)
        return {
            (group, int(row), heading): Flag(
                flag, None if pd.isna(bound) else float(bound), text
            )
            for group, row, heading, flag, bound, text in flags.itertuples(index=False)
        }

    def flag(self, group: str, row: int, heading: str) -> Flag | None:
        """Return the value flag of one cell, or None if it has none."""
        return self._flags.get((group, int(row), heading))

    def record_depths(self, group: str) -> list[str]:
        """Return the group's own depth headings (qc.md §4, "Record depth").

        ``<GROUP>_TOP``, ``<GROUP>_BASE`` and ``<GROUP>_DPTH`` with a length
        unit, plus ``SPEC_DPTH`` in a specimen group. ``SAMP_TOP`` in a lab
        group is the sample's key, not the specimen's depth.
        """
        rows = self.headings[
            (self.headings["group"] == group) & (self.headings["quantity"] == "length")
        ]
        own = re.compile(rf"{re.escape(group)}_(TOP|BASE|DPTH)")
        return [
            heading
            for heading in rows["heading"]
            if own.fullmatch(heading) or heading == "SPEC_DPTH"
        ]

    def depth_heading(self, group: str) -> str | None:
        """Return the heading a finding's ``depth`` comes from (qc.md §5.1)."""
        lengths = set(
            self.headings.loc[
                (self.headings["group"] == group)
                & (self.headings["quantity"] == "length"),
                "heading",
            ]
        )
        for suffix in _DEPTH_ORDER:
            heading = f"{group}{suffix}" if suffix.startswith("_") else suffix
            if heading in lengths:
                return heading
        return None

    @cached_property
    def _rows(self) -> dict[int, Row]:
        rows: dict[int, Row] = {}
        for group in self.groups:
            table = self.table(group)
            depth = self.depth_heading(group)
            for record in table.to_dict("records"):
                loca_id = record.get("LOCA_ID")
                value = record.get(depth) if depth else None
                rows[int(record["_line"])] = Row(
                    group,
                    int(record["_row"]),
                    None if pd.isna(loca_id) else str(loca_id),
                    None if value is None or pd.isna(value) else float(value),
                )
        return rows

    def row_at(self, line: Any) -> Row | None:
        """Return the canonical row at a DATA line, or None for any other line."""
        if line is None or pd.isna(line):
            return None
        return self._rows.get(int(line))

    def text_at(self, group: str, line: Any, heading: str) -> str | None:
        """Return a cell's text exactly as in the file, or None if there isn't one."""
        if line is None or pd.isna(line) or group not in self.groups:
            return None
        raw = self.raw(group)
        if heading not in raw.columns:
            return None
        cells = raw.loc[raw["_line"] == int(line), heading]
        return None if cells.empty else str(cells.iloc[0])

    def to_display_length(self, values: Any) -> tuple[np.ndarray, str]:
        """Convert lengths in m to the project's display unit, ``ft`` or ``m``.

        Reads the quantity kind's table directly, so a session's
        ``display_overrides`` don't change a project's report.
        """
        target = units.quantity_kind("length")[self.display_units]
        converted = units.convert(
            values, units.ureg.Unit("meter"), "length", units.ureg.Unit(target["unit"])
        )
        return converted, target["text"]
