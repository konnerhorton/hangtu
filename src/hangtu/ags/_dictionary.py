"""Heading types, units, keys and parents from the AGS4 dictionaries (ingest.md §6).

Each group and heading is read through one dictionary, in this order:

1. the 4.2 standard dictionary;
2. the standard dictionary of the file's own version, for groups and headings
   that 4.2 removed (finding ``M001``);
3. the file's ``DICT`` group, for user-defined groups and headings.

The standard dictionaries are the ones python-ags4 ships; hangtu doesn't copy
them.
"""

import io
from dataclasses import dataclass
from functools import cache
from importlib.resources import files

import pandas as pd
from python_ags4 import AGS4

from hangtu.ags._findings import Finding
from hangtu.ags._read import REFERENCE_VERSION, AgsText, _Capture

DICT_SOURCE = "DICT"


@dataclass(frozen=True)
class Heading:
    """A heading's dictionary entry; ``source`` is a version or ``"DICT"``."""

    group: str
    heading: str
    status: str
    type: str
    unit: str
    source: str

    @property
    def is_key(self) -> bool:
        return "KEY" in self.status


@dataclass(frozen=True)
class Group:
    """A group's dictionary entry; ``parent`` is None for a top-level group."""

    group: str
    parent: str | None
    source: str


@dataclass(frozen=True)
class Dictionary:
    """Groups and headings, keyed by name and by ``(group, heading)``."""

    groups: dict[str, Group]
    headings: dict[tuple[str, str], Heading]

    def keys(self, group: str) -> list[str]:
        """Return the key headings of ``group``, in dictionary order."""
        return [
            h.heading for (g, _), h in self.headings.items() if g == group and h.is_key
        ]


@cache
def standard(version: str) -> Dictionary:
    """Load python-ags4's standard dictionary for ``version`` (e.g. ``"4.0.4"``)."""
    name = f"Standard_dictionary_v{version.replace('.', '_')}.ags"
    data = files("python_ags4").joinpath(name).read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:  # the 4.0.x dictionaries are Latin-1
        text = data.decode("latin-1")
    with _Capture():
        tables, _ = AGS4.AGS4_to_dataframe(io.StringIO(text, newline=""))
    rows = tables["DICT"]
    return _from_dict_rows(rows[rows["HEADING"] == "DATA"], version)


def _from_dict_rows(rows: pd.DataFrame, source: str) -> Dictionary:
    groups: dict[str, Group] = {}
    headings: dict[tuple[str, str], Heading] = {}
    for row in rows.to_dict("records"):
        kind, group = row["DICT_TYPE"].strip(), row["DICT_GRP"].strip()
        if kind == "GROUP":
            parent = row.get("DICT_PGRP", "").strip()
            groups[group] = Group(
                group, None if parent in ("", "-") else parent, source
            )
        elif kind == "HEADING":
            heading = row["DICT_HDNG"].strip()
            headings[group, heading] = Heading(
                group=group,
                heading=heading,
                status=row.get("DICT_STAT", "").strip(),
                type=row.get("DICT_DTYP", "").strip(),
                unit=row.get("DICT_UNIT", "").strip(),
                source=source,
            )
    return Dictionary(groups, headings)


@dataclass(frozen=True)
class FileDictionary:
    """The dictionary entries that apply to one file, in the order of §6."""

    version: str
    layers: tuple[Dictionary, ...]

    def group(self, group: str) -> Group | None:
        for layer in self.layers:
            if group in layer.groups:
                return layer.groups[group]
        return None

    def heading(self, group: str, heading: str) -> Heading | None:
        for layer in self.layers:
            if (group, heading) in layer.headings:
                return layer.headings[group, heading]
        return None

    def keys(self, group: str) -> list[str]:
        """Return the key headings of ``group``, from the layer that defines it."""
        entry = self.group(group)
        if entry is None:
            return []
        layer = next(layer for layer in self.layers if group in layer.groups)
        return layer.keys(group)

    def ancestors(self, group: str) -> list[str]:
        """Return the parent chain of ``group``, nearest first (GRAT: GRAG, SAMP, …)."""
        chain: list[str] = []
        entry = self.group(group)
        while entry is not None and entry.parent and entry.parent not in chain:
            chain.append(entry.parent)
            entry = self.group(entry.parent)
        return chain


def for_file(ags: AgsText) -> tuple[FileDictionary, list[Finding]]:
    """Return the dictionary for ``ags`` and an M001 per removed group or heading."""
    layers = [standard(REFERENCE_VERSION)]
    if ags.version != REFERENCE_VERSION:
        layers.append(standard(ags.version))
    if "DICT" in ags.tables:
        layers.append(_from_dict_rows(ags.tables["DICT"].fillna(""), DICT_SOURCE))
    dictionary = FileDictionary(ags.version, tuple(layers))
    return dictionary, _removed(ags, dictionary)


def _removed(ags: AgsText, dictionary: FileDictionary) -> list[Finding]:
    if ags.version == REFERENCE_VERSION:
        return []
    findings = []
    removal = (
        f"AGS {REFERENCE_VERSION} removed it, so it is kept under its own name "
        f"and read with the AGS {ags.version} dictionary."
    )
    for group, headings in ags.headings.items():
        entry = dictionary.group(group)
        if entry is not None and entry.source == ags.version:
            findings.append(
                Finding(
                    rule="M001",
                    severity="info",
                    group=group,
                    line=ags.group_lines.get(group),
                    message=f"Group {group} is from AGS {ags.version}; {removal}",
                )
            )
            continue  # its headings come with it
        for heading in headings:
            found = dictionary.heading(group, heading)
            if found is not None and found.source == ags.version:
                findings.append(
                    Finding(
                        rule="M001",
                        severity="info",
                        group=group,
                        heading=heading,
                        line=ags.heading_lines.get(group),
                        message=(
                            f"Heading {heading} in {group} is from AGS "
                            f"{ags.version}; {removal}"
                        ),
                    )
                )
    return findings
