"""Heading units on ingest: what each column is converted from and to (ingest.md §7).

A column is converted only from the unit the file declares, read through the
dictionary (SPEC §2.2). Anything that can't be converted stays in the raw layer
with a ``U`` finding, and its canonical column is NULL. The exception is a
user-defined heading in a unit hangtu doesn't know but the file's UNIT group
defines: its numbers are kept as written, unconverted (``U005``).
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pint

from hangtu import _config, units
from hangtu.ags._dictionary import DICT_SOURCE, FileDictionary, Heading
from hangtu.ags._findings import Finding
from hangtu.ags._read import AgsText

ureg = units.ureg

# How a column's values are stored (ingest.md §7, the type table).
NUMBER, TEXT, DATE, TIME, YES_NO, DMS = (
    "number",
    "text",
    "date",
    "time",
    "yes_no",
    "dms",
)

# Column status in meta_heading.
CONVERTED, AS_IS, FILE_UNIT, RAW_ONLY, NOT_NUMERIC = (
    "converted",
    "as_is",
    "file_unit",
    "raw_only",
    "not_numeric",
)

#: Particle sizes: mm like a small length, but kept in mm in US output too, as
#: US practice does (datasets.md §10, P00 §4.1).
PARTICLE_SIZE_HEADINGS = frozenset({"GRAT_SIZE", "LLPL_SIZE", "PTST_SZUN"})

_NUMERIC_TYPE = re.compile(r"\d+(DP|SF|SCI)")
_TEXT_TYPES = {"ID", "PA", "PT", "PU", "RL", "RECORD LINK"}
_PERCENT = ureg.Unit("percent")
_DENSITY = ureg.Unit("megagram / meter**3").dimensionality
_FORCE = ureg.Unit("newton").dimensionality
# A bare "ton" or "t" depends on the file's unit system (SPEC §2.2).
_TON = {"ton", "t"}
_TONS = {
    ("US", False): "short_ton",
    ("SI", False): "metric_ton",
    ("US", True): "short_ton_force",
    ("SI", True): "metric_ton_force",
}


def value_kind(ags_type: str, has_unit: bool) -> str:
    """How values of AGS TYPE ``ags_type`` are stored (ingest.md §7).

    ``has_unit`` says whether the file or the dictionary gives the heading a
    unit; it decides whether an ``X`` heading holds numbers (``LNMC_MC``).
    """
    if _NUMERIC_TYPE.fullmatch(ags_type) or ags_type in ("MC", "U", "XN"):
        return NUMBER
    if ags_type == "X":
        return NUMBER if has_unit else TEXT
    return {"DT": DATE, "T": TIME, "YN": YES_NO, "DMS": DMS}.get(ags_type, TEXT)


@dataclass(frozen=True)
class HeadingUnit:
    """How one heading's values reach the canonical layer (``meta_heading``).

    ``unit`` is the canonical unit string, or None when values have no unit.
    ``format`` is the date or time format (``yyyy-mm-dd``, ``hh:mm:ss``) of a
    date or time heading: the file's UNIT row, else the dictionary's.
    ``quantity`` is the P00 quantity kind where one matches. ``standard`` says
    whether the heading is in the 4.2 dictionary.
    """

    group: str
    heading: str
    file_unit: str
    file_type: str
    kind: str
    unit: str | None
    quantity: str | None
    status: str
    standard: bool
    format: str | None = None
    source: pint.Unit | None = None
    target: pint.Unit | None = None

    def convert(self, values: np.ndarray) -> np.ndarray:
        """Convert magnitudes in the file's unit to the canonical unit."""
        values = np.asarray(values, dtype=float)
        if self.status != CONVERTED or self.source is None:
            return values
        return ureg.Quantity(values, self.source).to(self.target).magnitude


def resolve(
    ags: AgsText, dictionary: FileDictionary
) -> tuple[dict[tuple[str, str], HeadingUnit], list[Finding]]:
    """Resolve the unit of every heading in ``ags``, with its ``U`` findings."""
    system = file_system(ags)
    defined = file_units(ags)
    resolved, findings = {}, []
    for group, headings in ags.headings.items():
        for heading in headings:
            result, finding = resolve_heading(
                group,
                heading,
                ags.units[group].get(heading, "").strip(),
                ags.types[group].get(heading, "").strip(),
                dictionary.heading(group, heading),
                system,
                ags.unit_lines.get(group),
                defined,
            )
            resolved[group, heading] = result
            if finding is not None:
                findings.append(finding)
    return resolved, findings


def file_units(ags: AgsText) -> dict[str, str]:
    """Return the units the file's UNIT group defines, ``UNIT_UNIT`` to ``UNIT_DESC``.

    Matched exactly, as AGS Rule 15 lists them, after trimming spaces.
    """
    table = ags.tables.get("UNIT")
    if table is None or "UNIT_UNIT" not in table.columns:
        return {}
    descriptions = (
        table["UNIT_DESC"] if "UNIT_DESC" in table.columns else [""] * len(table)
    )
    return {
        unit.strip(): description.strip() if isinstance(description, str) else ""
        for unit, description in zip(table["UNIT_UNIT"], descriptions, strict=True)
        if isinstance(unit, str) and unit.strip()
    }


def file_system(ags: AgsText) -> str | None:
    """``"US"`` or ``"SI"`` from the length unit of ``LOCA_GL``, else ``GEOL_TOP``."""
    for group, heading in (("LOCA", "LOCA_GL"), ("GEOL", "GEOL_TOP")):
        text = ags.units.get(group, {}).get(heading, "").strip()
        unit, _ = units._lookup(text) if text else (None, False)
        if unit == ureg.Unit("foot"):
            return "US"
        if unit == ureg.Unit("meter"):
            return "SI"
    return None


def resolve_heading(
    group: str,
    heading: str,
    file_unit: str,
    file_type: str,
    entry: Heading | None,
    system: str | None,
    line: int | None = None,
    defined: Mapping[str, str] | None = None,
) -> tuple[HeadingUnit, Finding | None]:
    """Resolve one heading (ingest.md §7, Units, steps 1 to 5).

    ``defined`` holds the units the file's UNIT group defines, with their
    descriptions (``file_units``).
    """
    ags_type = file_type or (entry.type if entry else "") or "X"
    dictionary_unit = entry.unit if entry is not None else ""
    standard_entry = entry is not None and entry.source != DICT_SOURCE
    kind = value_kind(ags_type, bool(file_unit or dictionary_unit))
    base = {
        "group": group,
        "heading": heading,
        "file_unit": file_unit,
        "file_type": file_type,
        "kind": kind,
        "standard": entry is not None and entry.source == "4.2",
    }
    if kind in (DATE, TIME):
        base["format"] = file_unit or dictionary_unit or None
    if kind == TIME:
        return HeadingUnit(**base, unit="s", quantity=None, status=CONVERTED), None
    if kind == DMS:
        return HeadingUnit(**base, unit="deg", quantity=None, status=CONVERTED), None
    if kind != NUMBER:
        return HeadingUnit(**base, unit=None, quantity=None, status=NOT_NUMERIC), None

    def finding(rule: str, severity: str, message: str) -> Finding:
        return Finding(rule, severity, message, group, heading, line)

    def raw_only(rule: str, severity: str, message: str):
        note = (
            f" The column is kept as text in raw_{group} only; its canonical "
            "values are blank."
        )
        result = HeadingUnit(**base, unit=None, quantity=None, status=RAW_ONLY)
        return result, finding(rule, severity, message + note)

    where = f"{heading} ({group})"
    expected_text = dictionary_unit if standard_entry else ""
    expected = units._lookup(expected_text)[0] if expected_text else None

    if not file_unit:
        if dictionary_unit:
            return raw_only(
                "U003",
                "warning",
                f'{where} has no unit in the file, but the dictionary gives "'
                f"{dictionary_unit}\". hangtu doesn't guess units: add the unit to the "
                "UNIT row and ingest again.",
            )
        return HeadingUnit(**base, unit=None, quantity=None, status=AS_IS), None

    unit, note, by_convention = _parse(file_unit, expected, system)
    if unit is None:
        # pcf and a bare ton are ambiguous, not unknown: defining them in the
        # UNIT group doesn't say which unit they are.
        ambiguous = file_unit == "pcf" or file_unit in _TON
        description = None if ambiguous else (defined or {}).get(file_unit)
        if description is not None and not standard_entry:
            said = f' ("{description}")' if description else ""
            result = HeadingUnit(
                **base, unit=file_unit, quantity=None, status=FILE_UNIT
            )
            return result, finding(
                "U005",
                "info",
                f'{where}: the unit "{file_unit}" isn\'t one hangtu knows, but the '
                f"file's UNIT group defines it{said}. The values are kept as "
                "written, not converted.",
            )
        if description is not None:
            in_unit = f'in "{expected_text}"' if expected_text else "with no unit"
            said = f' as "{description}"' if description else ""
            note += (
                f" The file's UNIT group defines it{said}, but {heading} is a "
                f"standard heading {in_unit}."
            )
        return raw_only("U001", "error", f"{where}: {note}")

    if standard_entry:
        if expected is None:
            if unit.dimensionless and _factor(unit) == 1:
                return HeadingUnit(**base, unit=None, quantity=None, status=AS_IS), None
            return raw_only(
                "U004",
                "error",
                f'{where} has no unit in the AGS dictionary, but the file gives "'
                f'{file_unit}". Remove it from the UNIT row, or check the column.',
            )
        target, target_text = expected, expected_text
    elif unit.dimensionless:
        target, target_text = unit, file_unit
    else:
        target, target_text = _canonical(unit, file_unit)

    if unit.dimensionality != target.dimensionality:
        return raw_only(
            "U004",
            "error",
            f'{where} is {_describe(target)} in the AGS dictionary ("{target_text}"), '
            f'but the file\'s unit "{file_unit}" is {_describe(unit)}. Check the '
            "UNIT row.",
        )

    result = HeadingUnit(
        **base,
        unit=target_text,
        quantity=(
            "particle_size" if heading in PARTICLE_SIZE_HEADINGS else _quantity(target)
        ),
        status=CONVERTED,
        source=unit,
        target=target,
    )
    if by_convention:
        return result, finding("U002", "info", f"{where}: {note}")
    return result, None


def _parse(
    text: str, expected: pint.Unit | None, system: str | None
) -> tuple[pint.Unit | None, str, bool]:
    """Return ``(unit, note, by_convention)``; the unit is None if it can't be read.

    ``by_convention`` means the unit was read by a rule rather than as written
    (pcf, ton, or pint without an alias), and ``note`` says how (U002).
    """
    if text == "pcf":
        if expected is None:
            return (
                None,
                (
                    'the unit "pcf" can mean pounds (a density) or pounds-force '
                    "(a unit weight) per cubic foot, and nothing in the dictionary "
                    "says which. "
                    'Use a DICT entry with unit "Mg/m3" or "kN/m3" to say which.'
                ),
                False,
            )
        if expected.dimensionality == _DENSITY:
            return (
                ureg.Unit("pound / foot**3"),
                ('"pcf" read as pounds per cubic foot, since the column is a density.'),
                True,
            )
        return (
            units._lookup("pcf")[0],
            (
                '"pcf" read as pounds-force per cubic foot, since the column is a unit '
                "weight."
            ),
            True,
        )
    if text in _TON:
        force = expected is not None and expected.dimensionality == _FORCE
        if system is None:
            return (
                None,
                (
                    f'the unit "{text}" could be a short ton or a metric tonne, and '
                    "neither LOCA_GL nor GEOL_TOP gives the file's unit system. Use "
                    '"short_ton" or "metric_ton" in the UNIT row.'
                ),
                False,
            )
        name = _TONS[system, force]
        return (
            ureg.Unit(name),
            (
                f'"{text}" read as {name.replace("_", " ")}, since the file\'s lengths '
                f"are in {'feet' if system == 'US' else 'meters'}."
            ),
            True,
        )
    unit, from_alias = units._lookup(text)
    if unit is None:
        close = [alias for alias in units._aliases if alias.lower() == text.lower()]
        hint = f' Did you mean "{close[0]}"?' if close else ""
        return (
            None,
            (
                f'the unit "{text}" isn\'t recognized, and unit strings are '
                f"case-sensitive.{hint} Fix the UNIT row, or add the unit with "
                f'ht.add_unit_alias("{text}", "<pint unit>") and ingest again.'
            ),
            False,
        )
    if not from_alias:
        return (
            unit,
            (
                f'"{text}" read as {unit}. Add it with ht.add_unit_alias("{text}", '
                f'"{unit}") to confirm it.'
            ),
            True,
        )
    return unit, "", False


def _factor(unit: pint.Unit) -> float:
    return ureg.Quantity(1.0, unit).to_base_units().magnitude


def _canonical(unit: pint.Unit, text: str) -> tuple[pint.Unit, str]:
    """Return the P00 canonical unit of ``unit``'s dimension, else ``unit`` itself.

    A unit no P00 kind covers (``kN/mm``) is kept as the file writes it, so a
    plot labels it the way the file does (ingest.md §7, step 4).
    """
    kind = units._kind_of(unit)
    if kind is None:
        return unit, text
    target = ureg.Unit(_config.quantity_kinds()[kind]["canonical"])
    return target, _alias_for(target)


def _alias_for(unit: pint.Unit) -> str:
    """Return the alias-table string for ``unit``, so plots read it silently."""
    for text in units._aliases:
        if units._lookup(text)[0] == unit:
            return text
    return format(unit, "~")


def _quantity(unit: pint.Unit) -> str | None:
    if unit == _PERCENT:
        return "percent"
    for name, kind in _config.quantity_kinds().items():
        if kind["canonical"] and ureg.Unit(kind["canonical"]) == unit:
            return name
    return None


def _describe(unit: pint.Unit) -> str:
    kind = units._kind_of(unit)
    if kind is not None:
        return f"a {kind.replace('_', ' ')}"
    return f"[{unit.dimensionality}]"
