"""The judgments file: a project's unit weights, water levels, PI, Gs and α (SPEC §4).

A judgment has no default. Analyses take it from an argument, then from
``judgments=``, then from the Project's file, else raise. The file format and
its checks are in ``docs/work/m13a-judgments.md``, Spec Decision 1.
"""

import hashlib
import math
from collections.abc import Mapping
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Any

from hangtu import _config, units
from hangtu.errors import HangtuError, warn

GUIDE = "the judgments guide in the hangtu docs"


@dataclass(frozen=True)
class Kind:
    """What one judgment's file entry holds."""

    keyed: str  # the section of keyed entries: values or by_hole
    fields: dict[str, str]  # field -> quantity kind
    required: tuple[str, ...]  # fields every entry needs
    one_of: tuple[str, ...]  # exactly one of these, when not empty
    by: str | None  # the column keys match, when fixed
    unitless: bool = False  # a pure number: no units block (m14b, Decision 4)
    project_only: bool = False  # one value for the project, no keys (m15d, Decision 8)


KINDS = {
    "unit_weight": Kind(
        keyed="values",
        fields={
            "bulk_unit_weight": "unit_weight",
            "saturated_unit_weight": "unit_weight",
        },
        required=("bulk_unit_weight",),
        one_of=(),
        by=None,
    ),
    "water_level": Kind(
        keyed="by_hole",
        fields={"depth": "length", "elevation": "length"},
        required=(),
        one_of=("depth", "elevation"),
        by="loca_id",
    ),
    # docs/work/m13b2-spt-strength-history.md, Decision 11.
    "plasticity_index": Kind(
        keyed="values",
        fields={"plasticity_index": "dimensionless"},
        required=("plasticity_index",),
        one_of=(),
        by=None,
    ),
    # docs/work/m14b-phase-relations.md, Decision 4.
    "specific_gravity": Kind(
        keyed="values",
        fields={"specific_gravity": "dimensionless"},
        required=("specific_gravity",),
        one_of=(),
        by=None,
        unitless=True,
    ),
    # docs/work/m15d-compare.md, Decision 8.
    "significance_level": Kind(
        keyed="values",
        fields={"significance_level": "dimensionless"},
        required=("significance_level",),
        one_of=(),
        by=None,
        unitless=True,
        project_only=True,
    ),
}

#: Fields that must be positive (a water level may be above ground).
POSITIVE = {"bulk_unit_weight", "saturated_unit_weight", "specific_gravity"}
#: Fields that may be zero but not negative.
NON_NEGATIVE = {"plasticity_index"}
#: Fields strictly between 0 and 1: a probability.
PROBABILITY = {"significance_level"}
#: Fields that warn outside a range, with what lies outside it: QC B003's
#: particle density range (docs/data/qc.md §4.11).
PLAUSIBLE = {
    "specific_gravity": (
        2.0,
        3.2,
        "peat and organic soils lie lower, ores and some rock higher",
    ),
    "significance_level": (
        0.001,
        0.2,
        "0.05 and 0.01 are the usual conventions; a level this far from them "
        "is rarely meant",
    ),
}

#: Units shown in examples, as they are written in the file.
EXAMPLE_UNITS = {"unit_weight": "kN/m3", "length": "m", "dimensionless": '"%"'}


@dataclass(frozen=True)
class Entry:
    """One value of a judgment: its fields and the reason given."""

    values: dict[str, float]
    reason: str | None

    def text(self, units_by_field: Mapping[str, str]) -> str:
        """``bulk_unit_weight 18.5 kN/m3 (median LDEN)``."""
        fields = ", ".join(
            f"{field} {quantity_text(value, units_by_field[field])}"
            for field, value in self.values.items()
        )
        return f"{fields} ({self.reason})" if self.reason else fields


@dataclass(frozen=True)
class Judgment:
    """One judgment from the file, checked."""

    name: str
    by: str | None
    units: dict[str, str]
    project: Entry | None
    values: dict[str, Entry]


@dataclass(frozen=True)
class Read:
    """The file as read once: its judgments and the SHA-256 of its bytes."""

    path: Path
    sha256: str
    judgments: dict[str, Judgment]


def quantity_text(value: float, unit: str) -> str:
    """``18.5 kN/m3``: a value with its unit, as recorded on results."""
    return f"{value:g} {unit}" if unit else f"{value:g}"


class Judgments:
    """A project's judgments file: unit weights, water levels, PI, Gs and α.

    Made by ``ht.judgments(path)`` or ``p.judgments``. It holds the path, not
    the values: each analysis re-reads the file, so an edit shows up in the next
    call, and records the SHA-256 of what it read on its result.

    Attributes
    ----------
    path
        The judgments file.

    Examples
    --------
    >>> j = ht.judgments("judgments.yaml")
    >>> j
    Judgments('judgments.yaml')
      unit_weight, by geology_unit:
        Fill: bulk_unit_weight 18.5 kN/m3 (median LDEN, n=12)
      ...
    >>> df = ht.analysis.vertical_stress(spt, stratigraphy=log, judgments=j)
    """

    __slots__ = ("path",)

    def __init__(self, path: str | PathLike[str]) -> None:
        self.path = Path(path)
        self.read()

    def read(self) -> Read:
        """Read and check the file now; raise ``HangtuError`` naming any problem."""
        data = _config.read_file(self.path, "judgments")
        parsed = _config.parse_yaml(data, self.path, "judgments", GUIDE)
        return Read(
            path=self.path,
            sha256=hashlib.sha256(data).hexdigest(),
            judgments=_check_file(parsed, self.path.name),
        )

    def __repr__(self) -> str:
        head = f"Judgments({str(self.path)!r})"
        try:
            judgments = self.read().judgments
        except (HangtuError, OSError) as error:
            return f"{head}\n  can't be read: {error}"
        if not judgments:
            return f"{head}\n  no judgments"
        lines = [head]
        for judgment in judgments.values():
            key = "hole" if judgment.by == "loca_id" else judgment.by
            lines.append(
                f"  {judgment.name}, by {key}:" if key else f"  {judgment.name}:"
            )
            for name, entry in judgment.values.items():
                lines.append(f"    {name}: {entry.text(judgment.units)}")
            if judgment.project is not None:
                lines.append(f"    project: {judgment.project.text(judgment.units)}")
        return "\n".join(lines)


def judgments(path: str | PathLike[str]) -> Judgments:
    """Open a judgments file: a project's unit weights, water levels, PI, Gs and α.

    Judgments have no defaults in hangtu (SPEC §4). They live in one YAML file
    with their units and reasons, and every analysis that needs one reads it
    from there unless the call gives the value directly. The file is checked
    now, so a mistake shows up where it is opened, and re-read by each analysis.

    Parameters
    ----------
    path
        The YAML file. Its top-level keys are judgment names:

        ```yaml
        unit_weight:
          by: geology_unit          # the stratigraphy column the keys match
          units: {bulk_unit_weight: kN/m3, saturated_unit_weight: kN/m3}
          project: {bulk_unit_weight: 19.0, reason: median LDEN of all units}
          values:
            Fill:     {bulk_unit_weight: 18.5, reason: median LDEN, n=12}
            Alluvium: {bulk_unit_weight: 19.0, saturated_unit_weight: 20.0}
        water_level:
          units: {depth: m}         # or {elevation: ft}
          project: {depth: 3.0, reason: highest standpipe reading}
          by_hole:
            BH01: {depth: 2.5, reason: standpipe reading 2026-09-14}
        plasticity_index:
          by: geology_unit
          units: {plasticity_index: "%"}
          values:
            Alluvium: {plasticity_index: 28, reason: "median of 9 tests"}
        specific_gravity:
          by: geology_unit          # no units: Gs is a pure number
          values:
            Alluvium: {specific_gravity: 2.68, reason: "median of 6 LPDN, measured"}
        significance_level:         # one value for the project, no keys
          project: {significance_level: 0.05, reason: "the usual convention"}
        ```

        - `unit_weight` entries take `bulk_unit_weight` (required) and
          `saturated_unit_weight` (used below the water level); `by:` names the
          stratigraphy column their keys match, such as `geology_unit` or
          `uscs_symbol`.
        - `water_level` entries take one of `depth` or `elevation`. A negative
          depth is water above ground; analyses warn about it.
        - `plasticity_index` entries take `plasticity_index`, 0 or more, keyed
          by a column of the rows it is put on (`by:`), and are put on them by
          `ht.analysis.add_judgment()`. `ht.stats.describe()` shows each
          unit's tested PI to inform it.
        - `specific_gravity` entries take `specific_gravity`, a positive
          number, which warns outside 2.0-3.2. `ht.analysis.phase_relations()`
          uses it only for rows with no particle density.
        - `significance_level` takes only a `project:` entry: α, between 0
          and 1, which warns outside 0.001-0.2. `ht.stats.compare()` and
          `ht.stats.compare_groups()` test at it and give intervals at
          1 - α.
        - `units:` gives a unit for every field used, except for
          `specific_gravity` and `significance_level`, which have none.
        - `project:` needs a `reason`. It is optional except for
          `significance_level`, and used, with a warning, for every unit or
          hole the keyed entries don't list.
        - Keys match exactly and case-sensitively. Quote keys YAML would read
          as something else (`"yes"`, `"1"`).

    Returns
    -------
    Judgments
        Pass it as `judgments=` to an analysis, or set it on a project with
        `p.set_judgments(path)`.

    Raises
    ------
    HangtuError
        Naming the file, the judgment and the entry for an unknown key or
        field, a missing `units`, `by` or `reason`, a wrong unit, a value that
        isn't a number (or isn't positive, for unit weights and Gs, or isn't
        between 0 and 1, for α), a `units` block for Gs or α, keys for α, or
        invalid YAML.
    FileNotFoundError
        If there is no file at `path`.

    Examples
    --------
    >>> j = ht.judgments("judgments.yaml")
    >>> df = ht.analysis.vertical_stress(
    ...     p.spt(), stratigraphy=p.stratigraphy(), judgments=j
    ... )
    """
    return Judgments(path)


#: The ``meta_project`` key holding a project's judgments file (Decision 5).
STORED_KEY = "judgments_path"


def to_store(db: Path, path: str | PathLike[str]) -> str:
    """Return the path to store: relative to the database's folder when inside it."""
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(db.resolve().parent).as_posix()
    except ValueError:
        return str(resolved)


def stored_path(db: Path, value: str) -> Path:
    """Return the file a stored path names, for the database at ``db``."""
    path = Path(value)
    return path if path.is_absolute() else db.resolve().parent / path


def as_judgments(value: Any) -> Judgments | None:
    """Read a ``judgments=`` argument: a ``Judgments``, a path, or None."""
    if value is None or isinstance(value, Judgments):
        return value
    if isinstance(value, str | PathLike):
        return Judgments(value)
    raise HangtuError(
        "judgments= takes ht.judgments(path), a path to a judgments file, or "
        f"None, not {type(value).__name__}. Example: judgments=p.judgments"
    )


# --- Checks (Spec Decision 1) -------------------------------------------------------


def _check_file(parsed: Any, name: str) -> dict[str, Judgment]:
    if parsed is None:
        return {}
    if not isinstance(parsed, Mapping):
        raise HangtuError(
            f"{name}: the file must map judgment names to their entries "
            f"({', '.join(KINDS)}), not hold a {type(parsed).__name__}."
        )
    checked = {}
    for key, body in parsed.items():
        if key not in KINDS:
            raise HangtuError(
                f"{name}: {key!r} isn't a judgment hangtu knows. "
                f"The judgments are {', '.join(KINDS)}."
            )
        checked[key] = _check_judgment(key, body, f"{name}, {key}")
    return checked


def _check_judgment(name: str, body: Any, where: str) -> Judgment:
    kind = KINDS[name]
    sections = ("by", "units", "project", kind.keyed)
    if kind.by is not None:
        sections = ("units", "project", kind.keyed)
    if kind.unitless:
        sections = tuple(section for section in sections if section != "units")
    if kind.project_only:
        sections = ("project",)
    if not isinstance(body, Mapping):
        raise HangtuError(
            f"{where}: must be a mapping of {', '.join(sections)}, not {body!r}."
        )
    for key in body:
        if key == "units" and kind.unitless:
            raise HangtuError(
                f"{where}: {name} is a pure number and takes no units. Remove "
                "the units: line; a % would be read as a ratio and change the "
                "value 100-fold."
            )
        if kind.project_only and key != "project":
            raise HangtuError(
                f"{where}: {name} takes only project:, one value for the whole "
                f"project with its reason, not {key}:. Example: project: "
                f'{{{name}: 0.05, reason: "the usual convention"}}'
            )
        if key not in sections:
            raise HangtuError(
                f"{where}: {key!r} isn't a section of {name}. "
                f"The sections are {', '.join(sections)}."
            )
    units_by_field = (
        dict.fromkeys(kind.fields, "")
        if kind.unitless
        else _check_units(kind, body.get("units"), where)
    )
    keyed = body.get(kind.keyed)
    by = kind.by
    if kind.by is None:
        by = body.get("by")
        if keyed is not None and by is None:
            raise HangtuError(
                f"{where}: 'by' is missing. It names the stratigraphy column the "
                f"keys of {kind.keyed} match, e.g. by: geology_unit."
            )
        if by is not None and (not isinstance(by, str) or not by.strip()):
            raise HangtuError(
                f"{where}, by: must be a column name such as geology_unit, not {by!r}."
            )
    project = body.get("project")
    if kind.project_only and project is None:
        raise HangtuError(
            f"{where}: 'project' is missing. Example: project: "
            f'{{{name}: 0.05, reason: "the usual convention"}}'
        )
    if project is not None:
        project = _check_entry(kind, project, units_by_field, f"{where}, project")
        if project.reason is None:
            why = (
                "It applies to every call in the project, so say why it was "
                'chosen, e.g. reason: "the usual convention"'
                if kind.project_only
                else "A project-wide value fills in for every key not listed, "
                "so say why it holds, e.g. reason: median of all tests"
            )
            raise HangtuError(f"{where}, project: 'reason' is missing. {why}.")
    values = {}
    if keyed is not None:
        if not isinstance(keyed, Mapping):
            raise HangtuError(
                f"{where}, {kind.keyed}: must map each key to its entry, not {keyed!r}."
            )
        for key, entry in keyed.items():
            if not isinstance(key, str):
                raise HangtuError(
                    f"{where}, {kind.keyed}: the key {key!r} isn't text. YAML "
                    "reads bare yes, no, on, off, null and numbers as other "
                    'types; put the key in quotes as written, e.g. "1": {...}.'
                )
            values[key] = _check_entry(
                kind, entry, units_by_field, f"{where}, {kind.keyed}.{key}"
            )
    return Judgment(
        name=name, by=by, units=units_by_field, project=project, values=values
    )


def _check_units(kind: Kind, given: Any, where: str) -> dict[str, str]:
    example = ", ".join(
        f"{field}: {EXAMPLE_UNITS[quantity]}" for field, quantity in kind.fields.items()
    )
    if given is None:
        raise HangtuError(
            f"{where}: 'units' is missing. Give a unit for each field used, "
            f"e.g. units: {{{example}}}."
        )
    if not isinstance(given, Mapping):
        raise HangtuError(
            f"{where}, units: must map fields to units, e.g. {{{example}}}, "
            f"not {given!r}."
        )
    checked = {}
    for field, unit in given.items():
        if field not in kind.fields:
            raise HangtuError(
                f"{where}, units: {field!r} isn't a field of this judgment. "
                f"The fields are {', '.join(kind.fields)}."
            )
        try:
            units.check_dimension(units.parse_unit(unit), kind.fields[field])
        except HangtuError as error:
            raise HangtuError(f"{where}, units.{field}: {error}") from None
        checked[field] = unit
    return checked


def _check_entry(
    kind: Kind, entry: Any, units_by_field: Mapping[str, str], where: str
) -> Entry:
    fields = (*kind.fields, "reason")
    if not isinstance(entry, Mapping):
        raise HangtuError(
            f"{where}: must be a mapping of {', '.join(fields)}, not {entry!r}."
        )
    for field in entry:
        if field not in fields:
            comma = (
                " If it is part of a reason, put the reason in quotes: a comma "
                'inside {...} starts a new field, e.g. reason: "median, n=12".'
                if entry[field] is None
                else ""
            )
            raise HangtuError(
                f"{where}: {field!r} isn't a field of this judgment. "
                f"The fields are {', '.join(fields)}.{comma}"
            )
    for field in kind.required:
        if field not in entry:
            raise HangtuError(f"{where}: {field!r} is missing.")
    if kind.one_of and sum(field in entry for field in kind.one_of) != 1:
        raise HangtuError(f"{where}: give exactly one of {' or '.join(kind.one_of)}.")
    values = {}
    for field in kind.fields:
        if field not in entry:
            continue
        value = entry[field]
        if (
            isinstance(value, bool)
            or not isinstance(value, int | float)
            or not math.isfinite(value)
            or (field in POSITIVE and value <= 0)
            or (field in NON_NEGATIVE and value < 0)
            or (field in PROBABILITY and not 0 < value < 1)
        ):
            sign = (
                "a number between 0 and 1, e.g. 0.05"
                if field in PROBABILITY
                else "a positive number"
                if field in POSITIVE
                else "a number of 0 or more"
                if field in NON_NEGATIVE
                else "a number"
            )
            raise HangtuError(f"{where}, {field}: must be {sign}, not {value!r}.")
        if field not in units_by_field:
            raise HangtuError(
                f"{where}, {field}: has no unit. Add it to the judgment's units, "
                f"e.g. units: {{{field}: {EXAMPLE_UNITS[kind.fields[field]]}}}."
            )
        if field in PLAUSIBLE:
            low, high, outside = PLAUSIBLE[field]
            if not low <= value <= high:
                warn(
                    f"{where}, {field}: {value:g} is outside {low:g}-{high:g}. "
                    f"Check the value: {outside}."
                )
        values[field] = float(value)
    reason = entry.get("reason")
    if reason is not None:
        reason = str(reason).strip() or None
    return Entry(values=values, reason=reason)
