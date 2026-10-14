"""Surrogate keys for locations, samples and specimens (docs/data/ingest.md §5).

Keys are numbered in file order from 1, so the same data always gets the same
keys. Parent rows are matched on their key headings' text exactly as written
(``"1.50"`` isn't ``"1.5"``), as AGS4 Rule 10 does. A row whose parent isn't
found keeps a NULL key; python-ags4 already reports it (Rule 10b/10c).
"""

from dataclasses import dataclass, field

from hangtu.ags._dictionary import FileDictionary
from hangtu.ags._read import AgsText

LOCATION, SAMPLE, SPECIMEN = "location_id", "sample_id", "specimen_id"
SPECIMEN_HEADINGS = ("SPEC_REF", "SPEC_DPTH")


@dataclass
class Keys:
    """Surrogate key columns by group, and the ``specimen`` table's rows.

    ``columns[group]`` maps ``location_id``/``sample_id``/``specimen_id`` to one
    value per DATA row, for the keys that apply to the group.
    """

    columns: dict[str, dict[str, list[int | None]]] = field(default_factory=dict)
    specimens: list[dict[str, object]] = field(default_factory=list)


def resolve(ags: AgsText, dictionary: FileDictionary) -> Keys:
    """Resolve the surrogate keys of every group in ``ags``."""
    keys = Keys()
    locations = _index(ags, "LOCA", ["LOCA_ID"])
    sample_headings = [
        h for h in dictionary.keys("SAMP") if h in ags.headings.get("SAMP", [])
    ]
    samples = _index(ags, "SAMP", sample_headings)
    specimens: dict[tuple, int] = {}

    for group, table in ags.tables.items():
        rows = table.to_dict("records")
        headings = ags.headings[group]
        chain = [group, *dictionary.ancestors(group)]
        defined = dictionary.group(group) is not None
        columns: dict[str, list[int | None]] = {}

        if "LOCA" in chain or (not defined and "LOCA_ID" in headings):
            columns[LOCATION] = _match(rows, ["LOCA_ID"], locations)
        if "SAMP" in chain and defined:
            shared = [h for h in sample_headings if h in headings]
            columns[SAMPLE] = _match(rows, shared, samples) if shared else _none(rows)
            if group != "SAMP" and any(h in headings for h in SPECIMEN_HEADINGS):
                columns[SPECIMEN] = _specimens(rows, columns[SAMPLE], specimens, keys)
        if columns:
            keys.columns[group] = columns
    return keys


def _index(ags: AgsText, group: str, headings: list[str]) -> dict[tuple, int]:
    """Index the rows of ``group`` by key text; the first of any duplicates wins."""
    if group not in ags.tables or not headings:
        return {}
    index: dict[tuple, int] = {}
    for i, row in enumerate(ags.tables[group].to_dict("records")):
        index.setdefault(tuple(row[h] for h in headings), i + 1)
    return index


def _match(rows: list[dict], headings: list[str], index: dict[tuple, int]) -> list:
    if rows and not all(h in rows[0] for h in headings):
        return _none(rows)
    return [index.get(tuple(row[h] for h in headings)) for row in rows]


def _none(rows: list[dict]) -> list[None]:
    return [None] * len(rows)


def _specimens(
    rows: list[dict], sample_ids: list, seen: dict[tuple, int], keys: Keys
) -> list[int | None]:
    """Give each distinct (sample, SPEC_REF, SPEC_DPTH) one ``specimen_id``."""
    ids: list[int | None] = []
    for row, sample_id in zip(rows, sample_ids, strict=True):
        if sample_id is None:
            ids.append(None)
            continue
        ref, depth = (row.get(h, "") for h in SPECIMEN_HEADINGS)
        combination = (sample_id, ref, depth)
        if combination not in seen:
            seen[combination] = len(seen) + 1
            keys.specimens.append(
                {
                    SPECIMEN: seen[combination],
                    SAMPLE: sample_id,
                    "SPEC_REF": ref,
                    "SPEC_DPTH": depth,
                }
            )
        ids.append(seen[combination])
    return ids
