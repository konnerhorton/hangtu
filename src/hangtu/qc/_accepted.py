"""Accepted findings: what a reviewer checked and accepts, with a reason (qc.md §3.4).

Entries come from ``p.qc(accepted=...)`` as a path to a YAML file or a list of
dicts. Each is checked here, before any rule runs. An entry matches findings
on content (rule, hole, group, heading, depth), never on file lines, since
lines move between revisions of a file.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from os import PathLike
from typing import Any

import pandas as pd

from hangtu import units
from hangtu.errors import HangtuError, UnitsError
from hangtu.qc._settings import Settings, _is_v_rule, _plain_number, read_yaml

#: How far apart, in m, an entry's depth and a finding's may be and still match.
#: Fixed, because practitioners write depths with inconsistent precision.
DEPTH_TOLERANCE = 0.05
KEYS = ("rule_id", "loca_id", "group", "heading", "depth", "reason")
#: Keys an entry may leave out; each one left out matches anything.
OPTIONAL = ("loca_id", "group", "heading", "depth")

AcceptedSource = str | PathLike[str] | Sequence[Mapping[str, Any]] | None


@dataclass(frozen=True)
class Entry:
    """One accepted entry. ``depth`` is as written; ``depth_m`` is in m."""

    position: int
    rule_id: str
    reason: str
    loca_id: str | None = None
    group: str | None = None
    heading: str | None = None
    depth: str | None = None
    depth_m: float | None = None


@dataclass(frozen=True)
class Accepted:
    """The entries of one run and where they came from.

    ``source`` is the path as given, ``"list"``, or ``""`` with no entries given.
    """

    entries: tuple[Entry, ...] = ()
    source: str = ""


def read_accepted(source: AcceptedSource, settings: Settings) -> Accepted:
    """Read and check the accepted entries (qc.md §2, §3.4).

    Raises
    ------
    FileNotFoundError
        The file isn't there.
    HangtuError
        The file isn't YAML or isn't a list of entries, or an entry is
        missing its rule or reason, has an unknown key or rule, or gives a
        depth without a hole.
    UnitsError
        An entry's depth has no unit or isn't a length.
    """
    if source is None:
        return Accepted()
    if isinstance(source, str | PathLike):
        label = str(source)
        items = read_yaml(source, "accepted findings")
    else:
        label = "list"
        items = source
    if isinstance(items, Mapping) and set(items) == {"accepted"}:
        items = items["accepted"]
    if items is None:
        items = []
    if isinstance(items, str | bytes | Mapping) or not isinstance(items, Sequence):
        raise HangtuError(
            "Accepted findings must be a list of entries, each with a rule_id and "
            f"a reason, not {type(items).__name__}. See docs/data/qc.md §3.4."
        )
    entries = tuple(
        _entry(position, item, settings) for position, item in enumerate(items, start=1)
    )
    return Accepted(entries, label)


def _entry(position: int, item: Any, settings: Settings) -> Entry:
    if not isinstance(item, Mapping):
        raise HangtuError(
            f"accepted entry {position} must be a mapping of "
            f"{', '.join(KEYS)}, not {item!r}."
        )
    rule_id = _given(item.get("rule_id"))
    where = f"accepted entry {position} ({rule_id or 'no rule_id'})"
    for key in item:
        if key not in KEYS:
            raise HangtuError(
                f"{where} has an unknown key {key!r}. The keys are {', '.join(KEYS)}."
            )
    if rule_id is None:
        raise HangtuError(f"{where} needs a rule_id, e.g. rule_id: L005.")
    reason = _given(item.get("reason"))
    if reason is None:
        raise HangtuError(
            f"{where} needs a reason: say why the finding is accepted, e.g. "
            "reason: Valley site; ground levels follow the topography."
        )
    if rule_id == "V*":
        raise HangtuError(
            f"{where}: V* can't be accepted, since it covers every python-ags4 "
            "rule at once. Accept single V rules, e.g. rule_id: V10a."
        )
    if rule_id not in settings.defaults and not _is_v_rule(rule_id):
        known = [r for r in settings.defaults if r != "V*"]
        raise HangtuError(
            f"{where}: QC rule {rule_id!r} doesn't exist. The rules are "
            f"{', '.join(known)}, and V<rule> for one python-ags4 rule."
        )
    given = {key: _given(item.get(key)) for key in OPTIONAL}
    depth_m = None
    if given["depth"] is not None:
        if given["loca_id"] is None:
            raise HangtuError(
                f"{where} gives a depth without a loca_id. A depth means nothing "
                "without its hole: add loca_id, or leave out depth."
            )
        depth_m = _depth(where, item["depth"])
    return Entry(position, rule_id, reason, **given, depth_m=depth_m)


def _given(value: Any) -> str | None:
    """Return a key's value as text, or None when it is absent or blank."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _depth(where: str, given: Any) -> float:
    """Read a depth such as ``"41.5 ft"`` and return it in m."""
    example = 'depth: "12.5 ft"'
    if (
        not isinstance(given, str)
        or _plain_number(given) is not None
        or units._QUANTITY_TEXT.fullmatch(given) is None
    ):
        raise UnitsError(
            f"{where}: depth {given!r} needs a unit, written as a number and a "
            f"unit, e.g. {example}. Units are never guessed."
        )
    try:
        value, unit_text = units.parse_quantity(given.strip(), "length")
    except UnitsError as error:
        raise UnitsError(f"{where}: depth {given!r} isn't a length. {error}") from None
    meter = units.ureg.Unit("meter")
    unit = units.parse_unit(unit_text)
    return float(units.convert([value], unit, "length", meter)[0])


#: Columns of ``report.accepted`` (qc.md §5.4).
ACCEPTED_COLUMNS = [
    "rule_id",
    "loca_id",
    "group",
    "heading",
    "depth",
    "reason",
    "matches",
    "status",
]


def apply(
    rows: list[dict[str, Any]], accepted: Accepted, settings: Settings
) -> pd.DataFrame:
    """Mark the finding rows the entries match, and return ``report.accepted``.

    ``rows`` are finding rows with ``depth`` in m. Each gets ``accepted`` and
    ``reason``, the reason of the first entry that matches it. Every entry
    counts all the findings it matches, so a broad entry behind a specific one
    isn't shown as matching nothing.
    """
    matches = [0] * len(accepted.entries)
    for row in rows:
        row["accepted"], row["reason"] = False, None
        for i, entry in enumerate(accepted.entries):
            if not _matches(entry, row):
                continue
            matches[i] += 1
            if not row["accepted"]:
                row["accepted"], row["reason"] = True, entry.reason
    records = [
        {
            "rule_id": entry.rule_id,
            "loca_id": entry.loca_id,
            "group": entry.group,
            "heading": entry.heading,
            "depth": entry.depth,
            "reason": entry.reason,
            "matches": count,
            "status": _status(entry, count, settings),
        }
        for entry, count in zip(accepted.entries, matches, strict=True)
    ]
    frame = pd.DataFrame(records, columns=ACCEPTED_COLUMNS)
    frame["matches"] = frame["matches"].astype("int64")
    return frame


def _matches(entry: Entry, row: Mapping[str, Any]) -> bool:
    """Every key the entry gives equals the row's; a depth within the tolerance."""
    for key in ("rule_id", "loca_id", "group", "heading"):
        given = getattr(entry, key)
        if given is not None and row.get(key) != given:
            return False
    if entry.depth_m is None:
        return True
    depth = row.get("depth")
    if depth is None or pd.isna(depth):
        return False
    return abs(float(depth) - entry.depth_m) <= DEPTH_TOLERANCE + 1e-9


def _status(entry: Entry, matches: int, settings: Settings) -> str:
    if not settings.rule(entry.rule_id).enabled:
        return "rule disabled"
    return "matched" if matches else "no match"
