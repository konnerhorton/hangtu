"""Judgments as an analysis uses them: looked up by key and recorded (SPEC §4).

Shared by ``vertical_stress()`` and ``add_judgment()``. A judgment comes from
an argument or the judgments file; ``take()`` gives each key its value,
filling with the project value where allowed, and records what was used for
``df.attrs["judgments"]``.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from hangtu import _judgments
from hangtu import units as _units
from hangtu.errors import HangtuError, warn

#: The key of a judgment given as one value for every layer or hole.
ALL = "all"

#: The unit each quantity is worked in. Kinds with no canonical unit (percent,
#: dimensionless) are used as given.
WORKING_UNITS = {
    "unit_weight": _units.ureg.Unit("kilonewton / meter**3"),
    "length": _units.ureg.meter,
}


@dataclass
class Values:
    """One judgment as this call uses it, in m and kN/m³, with its record."""

    name: str
    source: str  # "argument", or the judgments file's path
    by: str | None  # the column its keys match; None for one value for all
    entries: dict[str, dict[str, float]]
    texts: dict[str, dict[str, str]]  # as given, with units, for the record
    project: dict[str, float] | None = None
    project_text: dict[str, str] | None = None
    sha256: str | None = None
    #: A file's project value with no keyed values: used for every key, warned.
    project_only: bool = False
    used: dict[str, dict[str, str]] = field(default_factory=dict)

    def record(self) -> dict[str, Any]:
        """``df.attrs["judgments"][name]``: the source and the keys used."""
        record: dict[str, Any] = {"source": self.source}
        if self.sha256 is not None:
            record["sha256"] = self.sha256
        record["by"] = self.by
        record["values"] = self.used
        return record


def read_judgments(judgments: Any, df: pd.DataFrame) -> "_judgments.Read | None":
    """Read the judgments file for this call: ``judgments=``, else df's project's."""
    given = _judgments.as_judgments(judgments)
    attached = df.attrs.get("judgments_file")
    if given is None:
        if attached is None:
            return None
        given = _judgments.Judgments(attached)
    elif attached is not None and given.path.resolve() != Path(attached).resolve():
        warn(
            f"judgments= is {str(given.path)!r}, not the project's judgments file "
            f"{attached!r} that df carries; judgments= is used."
        )
    return given.read()


def _to_working_unit(value: float, unit: str, quantity: str) -> float:
    if quantity not in WORKING_UNITS:
        return float(value)
    return float(
        _units.convert(
            [value], _units.parse_unit(unit), quantity, WORKING_UNITS[quantity]
        )[0]
    )


def from_file(judgment: "_judgments.Judgment", read: "_judgments.Read") -> Values:
    """Convert a judgment from the file to working units, with texts for the record."""
    kinds = _judgments.KINDS[judgment.name].fields

    def convert(entry: "_judgments.Entry") -> tuple[dict[str, float], dict[str, str]]:
        values, texts = {}, {}
        for name, value in entry.values.items():
            unit = judgment.units[name]
            values[name] = _to_working_unit(value, unit, kinds[name])
            texts[name] = _judgments.quantity_text(value, unit)
        if entry.reason is not None:
            texts["reason"] = entry.reason
        return values, texts

    entries, texts = {}, {}
    for key, entry in judgment.values.items():
        entries[key], texts[key] = convert(entry)
    project = project_text = None
    if judgment.project is not None:
        project, project_text = convert(judgment.project)
    values = Values(
        judgment.name,
        str(read.path),
        judgment.by,
        entries,
        texts,
        project=project,
        project_text=project_text,
        sha256=read.sha256,
    )
    if not judgment.values and judgment.project is not None and judgment.by is None:
        values.entries, values.texts = {ALL: project}, {ALL: project_text}
        values.project_only = True
    return values


def take(values: Values, keys: Iterable[str], noun: str) -> dict[str, dict[str, float]]:
    """Each key's entry, the project value filling in; record the ones used."""
    keys = list(dict.fromkeys(keys))
    if values.project_only:
        warn_project(values, "every " + noun, values.texts[ALL])
        values.used["project"] = values.texts[ALL]
        return dict.fromkeys(keys, values.entries[ALL])
    if values.by is None:
        values.used[ALL] = values.texts[ALL]
        return dict.fromkeys(keys, values.entries[ALL])
    found = {}
    missing = []
    for key in keys:
        if key in values.entries:
            found[key] = values.entries[key]
            values.used[key] = values.texts[key]
        else:
            missing.append(key)
    if not missing:
        return found
    listed = ", ".join(map(repr, missing))
    plural = noun + ("s" if len(missing) != 1 else "")
    if values.project is None:
        where = (
            f"{values.name}="
            if values.source == "argument"
            else f"The judgments file's {values.name}"
        )
        raise HangtuError(
            f"{where} has no value for the {plural} {listed}. Add "
            f"{'it' if len(missing) == 1 else 'them'}"
            + (
                ", or a project: entry with its reason to use for every one not listed."
                if values.source != "argument"
                else "."
            )
        )
    warn_project(values, f"the {plural} {listed} not listed", values.project_text)
    for key in missing:
        found[key] = values.project
    values.used["project"] = {
        **(values.project_text or {}),
        "used_for": ", ".join(missing),
    }
    return found


def warn_project(values: Values, used_for: str, text: Mapping[str, str]) -> None:
    shown = dict(text)
    reason = shown.pop("reason", None)
    warn(
        f"{values.name}: the project value {', '.join(shown.values())} is used for "
        f"{used_for}" + (f" ({reason})." if reason else ".")
    )


def warn_unused(values: Values, present: Iterable[Any], where: str) -> None:
    """Warn about keyed entries for a key that isn't in the data.

    ``where`` names the data, such as "the stratigraphy's geology_unit".
    """
    if values.by is None:
        return
    present = {str(key) for key in present if key is not None and key == key}
    unused = [key for key in values.entries if key not in present]
    if unused:
        warn(
            f"{values.name} has values for {', '.join(map(repr, unused))}, which "
            f"{'is' if len(unused) == 1 else 'are'} not in {where}. Check the "
            "spelling: keys match exactly, by case too."
        )
