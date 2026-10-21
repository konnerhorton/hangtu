"""Typing values and flagging recognized text (docs/data/ingest.md §7, §8)."""

import datetime as dt
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from typing import Any, Literal

from hangtu import _config
from hangtu.ags import _units as u
from hangtu.ags._findings import Finding


@dataclass(frozen=True)
class ValueFlag:
    """One flagged cell (the ``value_flag`` table); ``row`` is the group's ``_row``."""

    row: int
    heading: str
    flag: str
    bound: float | None
    text: str


def _flags() -> dict[str, Any]:
    return _config.load("ags/value_flags.yaml")


def type_column(
    heading: u.HeadingUnit, cells: Sequence[str], lines: Sequence[int]
) -> tuple[list[Any], list[ValueFlag], list[Finding]]:
    """Type one column, returning its canonical values, flags and T001 findings.

    ``cells`` are the raw texts in file order; row ``i`` gets ``_row`` ``i + 1``.
    A raw-only column (U001, U003, U004) is all blank, with no flags. A
    ``file_unit`` column (U005) is typed like any number column, unconverted.
    """
    if heading.status == u.RAW_ONLY:
        return [None] * len(cells), [], []
    parse = _PARSERS[heading.kind]
    values, flags, findings = [], [], []
    for i, (cell, line) in enumerate(zip(cells, lines, strict=True)):
        text = (cell or "").strip()
        if not text:
            values.append(None)
            continue
        value, flag, bound = parse(text, heading)
        if flag == "OTHER":
            findings.append(_t001(heading, text, line))
        if flag is not None:
            flags.append(ValueFlag(i + 1, heading.heading, flag, bound, text))
        values.append(value)
    if heading.kind == u.NUMBER:
        values = _convert(heading, values)
        flags = [
            f if f.bound is None else _with_bound(f, heading.convert([f.bound])[0])
            for f in flags
        ]
    return values, flags, findings


def refusal_flags(
    group: str, headings: Sequence[str], rows: Sequence[dict[str, str]]
) -> list[ValueFlag]:
    """Flag SPT N values whose report is an incomplete drive (``REFUSAL``).

    The N value may be blank. A row whose N value is itself a refusal ("50/75")
    was flagged when it was typed, so it isn't flagged again.
    """
    rule = _flags()["refusal"]
    if group != rule["group"] or rule["report"] not in headings:
        return []
    flags = []
    for i, row in enumerate(rows):
        report = (row.get(rule["report"]) or "").strip()
        value = (row.get(rule["value"]) or "").strip()
        if spt_report(report) == "incomplete" and not _refusal_value(value):
            flags.append(ValueFlag(i + 1, rule["value"], "REFUSAL", None, report))
    return flags


def spt_report(text: str) -> Literal["complete", "incomplete"] | None:
    """Read ``ISPT_REP`` as a complete test, an incomplete drive or neither.

    The forms are in ``value_flags.yaml`` (ingest.md §8). ``text`` is trimmed first.
    """
    complete, incomplete = _report_forms()
    text = text.strip()
    if complete.fullmatch(text):
        return "complete"
    if incomplete.fullmatch(text):
        return "incomplete"
    return None


@cache
def _report_forms() -> tuple[re.Pattern[str], re.Pattern[str]]:
    rule = _flags()["refusal"]
    unit = "(?:" + "|".join(re.escape(u) for u in rule["penetration_units"]) + ")"
    pair = rule["pair"].replace("{unit}", unit)
    separator = rule["separator"]

    def form(name: str) -> re.Pattern[str]:
        pattern = rule[name].replace("{pair}", pair).replace("{separator}", separator)
        return re.compile(pattern)

    return form("complete"), form("incomplete")


def _refusal_value(text: str) -> re.Match[str] | None:
    """Match an N value written as blows/penetration ("50/75")."""
    return re.fullmatch(_flags()["refusal"]["value_pattern"], text)


def _with_bound(flag: ValueFlag, bound: float) -> ValueFlag:
    return ValueFlag(flag.row, flag.heading, flag.flag, float(bound), flag.text)


def _convert(heading: u.HeadingUnit, values: list[Any]) -> list[float | None]:
    present = [i for i, v in enumerate(values) if v is not None]
    converted = heading.convert([values[i] for i in present])
    out: list[float | None] = [None] * len(values)
    for i, value in zip(present, converted, strict=True):
        out[i] = float(value)
    return out


def _t001(heading: u.HeadingUnit, text: str, line: int) -> Finding:
    what = {
        u.NUMBER: "a number",
        u.DATE: f"a date in the format {heading.format}",
        u.TIME: f"a time in the format {heading.format}",
        u.YES_NO: "Y or N",
        u.DMS: "degrees:minutes:seconds",
    }[heading.kind]
    return Finding(
        "T001",
        "info",
        f'"{text}" in {heading.heading} ({heading.group}) isn\'t {what} or text '
        "hangtu recognizes, so the value is blank; the text is kept with flag OTHER.",
        heading.group,
        heading.heading,
        int(line),
    )


Parsed = tuple[Any, str | None, float | None]  # value, flag, bound


def _number(text: str, heading: u.HeadingUnit) -> Parsed:
    value = _float(text)
    if value is not None:
        return value, None, None
    flags = _flags()
    if text in flags["blank"]:
        return None, flags["blank"][text], None
    prefix, rest = text[:1], text[1:].strip()
    if prefix in flags["prefix"] and (value := _float(rest)) is not None:
        flag = flags["prefix"][prefix]
        return value, flag, value if flag in ("LT", "GT") else None
    refusal = flags["refusal"]
    is_n = heading.heading == refusal["value"] and heading.group == refusal["group"]
    if is_n and (match := _refusal_value(text)):
        return float(match[1]), "REFUSAL", None
    return None, "OTHER", None


def _float(text: str) -> float | None:
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def _text(text: str, heading: u.HeadingUnit) -> Parsed:
    return text, None, None


def _yes_no(text: str, heading: u.HeadingUnit) -> Parsed:
    if text in ("Y", "N"):
        return int(text == "Y"), None, None
    return None, "OTHER", None


_DMS = re.compile(r"(-?)(\d+):(\d+):(\d+(?:\.\d*)?)\s*([NSEW]?)")


def _dms(text: str, heading: u.HeadingUnit) -> Parsed:
    match = _DMS.fullmatch(text)
    if match is None:
        return None, "OTHER", None
    sign, degrees, minutes, seconds, hemisphere = match.groups()
    value = int(degrees) + int(minutes) / 60 + float(seconds) / 3600
    if sign or hemisphere in ("S", "W"):
        value = -value
    return value, None, None


def _date(text: str, heading: u.HeadingUnit) -> Parsed:
    if not heading.format:  # no format in the file or the dictionary: ISO 8601 only
        try:
            return dt.datetime.fromisoformat(text).isoformat(), None, None
        except ValueError:
            return None, "OTHER", None
    code, has_date, has_time = _strptime_code(heading.format)
    try:
        parsed = dt.datetime.strptime(text, code)
    except ValueError:
        return None, "OTHER", None
    if has_date and has_time:
        return parsed.isoformat(), None, None
    return (parsed.date() if has_date else parsed.time()).isoformat(), None, None


def _strptime_code(ags_format: str) -> tuple[str, bool, bool]:
    """Turn ``yyyy-mm-ddThh:mm`` into ``%Y-%m-%dT%H:%M``; mm is a month before T.

    Also returns whether the format has a date part and a time part.
    """
    date_part, _, time_part = ags_format.partition("T")
    if not time_part and "hh" in date_part:
        date_part, time_part = "", date_part
    for token, code in (("yyyy", "%Y"), ("mm", "%m"), ("dd", "%d")):
        date_part = date_part.replace(token, code)
    for token, code in ((".sss", ".%f"), ("hh", "%H"), ("mm", "%M"), ("ss", "%S")):
        time_part = time_part.replace(token, code)
    code = "T".join(part for part in (date_part, time_part) if part)
    return code, bool(date_part), bool(time_part)


_TIME_UNITS = {"hh": 3600, "mm": 60, "ss": 1}


def _time(text: str, heading: u.HeadingUnit) -> Parsed:
    tokens = (heading.format or "").split(":")
    parts = text.split(":")
    if (
        not tokens
        or any(t not in _TIME_UNITS for t in tokens)
        or len(parts) != len(tokens)
    ):
        return None, "OTHER", None
    try:
        seconds = sum(
            _TIME_UNITS[t] * float(p) for t, p in zip(tokens, parts, strict=True)
        )
    except ValueError:
        return None, "OTHER", None
    return seconds, None, None


_PARSERS = {
    u.NUMBER: _number,
    u.TEXT: _text,
    u.DATE: _date,
    u.TIME: _time,
    u.YES_NO: _yes_no,
    u.DMS: _dms,
}
