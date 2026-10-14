"""Load the QC rule settings and check overrides (qc.md §3).

Defaults come from ``qc/rules.yaml`` and ``qc/min_fields.yaml``. Overrides
come from ``p.qc(rules=..., min_fields=...)`` as a path to a YAML file or a
dict of the same shape, holding only what changes. Every override is checked
here, before any rule runs, and thresholds are converted to their canonical
unit once (m, deg, m/s; percent and counts as given).
"""

import difflib
from collections.abc import Mapping
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Any

import yaml

from hangtu import _config, units
from hangtu.ags._dictionary import standard
from hangtu.errors import HangtuError, UnitsError
from hangtu.qc._registry import INGEST_RULES, THRESHOLDS

SEVERITIES = ("error", "warning", "info")
RULE_KEYS = ("enabled", "severity", "thresholds")
FIELD_KINDS = ("required", "recommended")

#: Dictionaries a ``min_fields`` group or heading is looked up in: 4.2 first,
#: then the older versions ingest reads (``IPRG`` is 4.0.x only).
DICTIONARY_VERSIONS = ("4.2", "4.1.1", "4.1", "4.0.4", "4.0.3")

Override = str | PathLike[str] | Mapping[str, Any] | None


@dataclass(frozen=True)
class Threshold:
    """One threshold: the text as given, and its value in the canonical unit."""

    text: str
    value: float
    kind: str


@dataclass(frozen=True)
class RuleSettings:
    """The settings one rule runs with, after overrides.

    ``severity`` is None for an ingest rule that keeps the stored severity.
    """

    rule_id: str
    title: str
    severity: str | None
    enabled: bool
    thresholds: dict[str, Threshold]
    overridden: bool

    @property
    def is_ingest(self) -> bool:
        return is_ingest_rule(self.rule_id)


def is_ingest_rule(rule_id: str) -> bool:
    """Return True for a rule whose findings are stored at ingest (§4.1)."""
    return rule_id in INGEST_RULES or _is_v_rule(rule_id)


def _is_v_rule(rule_id: str) -> bool:
    """Return True for ``V*`` or a single python-ags4 rule such as ``V10a``."""
    return rule_id == "V*" or (
        len(rule_id) > 1 and rule_id[0] == "V" and rule_id[1:].isalnum()
    )


@dataclass(frozen=True)
class Settings:
    """The rule settings and minimally useful fields for one QC run."""

    defaults: dict[str, dict[str, Any]]
    overrides: dict[str, dict[str, Any]]
    min_fields: dict[str, dict[str, tuple[str, ...]]]

    @property
    def rule_ids(self) -> list[str]:
        """Every rule in ``rules.yaml``, then V rules named only in overrides."""
        extra = [rule_id for rule_id in self.overrides if rule_id not in self.defaults]
        return [*self.defaults, *extra]

    def rule(self, rule_id: str) -> RuleSettings:
        """Return the settings for ``rule_id``; a V rule not listed follows ``V*``.

        For a V rule, a key given for that rule wins over one given for ``V*``,
        which wins over the defaults (§3.3).
        """
        if rule_id in self.defaults:
            default = self.defaults[rule_id]
        elif _is_v_rule(rule_id):
            default = {**self.defaults["V*"], "title": "python-ags4 format rule"}
        else:
            raise KeyError(rule_id)
        layers = [self.overrides.get(rule_id, {})]
        if _is_v_rule(rule_id) and rule_id != "V*":
            layers.insert(0, self.overrides.get("V*", {}))
        merged = {**default, "thresholds": dict(default.get("thresholds") or {})}
        for layer in layers:
            for key, value in layer.items():
                if key == "thresholds":
                    merged["thresholds"].update(value)
                else:
                    merged[key] = value
        thresholds = {
            name: _threshold(rule_id, name, text)
            for name, text in merged["thresholds"].items()
        }
        defaults = {
            name: _threshold(rule_id, name, text)
            for name, text in (default.get("thresholds") or {}).items()
        }
        enabled = merged.get("enabled", True)
        overridden = (
            merged.get("severity") != default.get("severity")
            or enabled != default.get("enabled", True)
            or any(thresholds[name].value != defaults[name].value for name in defaults)
        )
        return RuleSettings(
            rule_id=rule_id,
            title=merged["title"],
            severity=merged.get("severity"),
            enabled=enabled,
            thresholds=thresholds,
            overridden=overridden,
        )


def load(rules: Override = None, min_fields: Override = None) -> Settings:
    """Return the default settings merged with ``rules`` and ``min_fields``.

    Raises
    ------
    FileNotFoundError
        An override file isn't there.
    HangtuError
        An override file isn't YAML, or names an unknown rule, key, threshold,
        severity, group or heading.
    UnitsError
        A threshold is of the wrong kind.
    """
    defaults = _config.load("qc/rules.yaml")["rules"]
    overrides = _read(rules, "rules")
    _check_rules(overrides, defaults)
    settings = Settings(
        defaults=defaults,
        overrides=overrides,
        min_fields=_merge_min_fields(_read(min_fields, "min_fields")),
    )
    for rule_id in overrides:
        settings.rule(rule_id)  # converts each threshold, raising if one is wrong
    return settings


def _read(source: Override, top_key: str) -> dict[str, Any]:
    """Read an override from a path or a dict; ``top_key`` may wrap it."""
    if source is None:
        return {}
    if isinstance(source, str | PathLike):
        path = Path(source)
        if not path.is_file():
            raise FileNotFoundError(
                f"No QC {top_key} file at {str(path)!r}. Check the path; it is "
                f"relative to {str(Path.cwd())!r} unless it starts from a drive or /."
            )
        try:
            source = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            where = getattr(error, "problem_mark", None)
            line = f" at line {where.line + 1}" if where else ""
            raise HangtuError(
                f"The QC {top_key} file {str(path)!r} isn't valid YAML{line}. "
                f"Check its indentation and colons against docs/data/qc.md §3."
            ) from None
        if source is None:
            return {}
    if not isinstance(source, Mapping):
        raise HangtuError(
            f"QC {top_key} overrides must be a dict or a path to a YAML file, "
            f"not {type(source).__name__}. See docs/data/qc.md §3.3."
        )
    if set(source) == {top_key}:
        source = source[top_key] or {}
    return {str(key): value for key, value in source.items()}


def _check_rules(overrides: dict[str, Any], defaults: dict[str, Any]) -> None:
    for rule_id, override in overrides.items():
        if rule_id not in defaults and not _is_v_rule(rule_id):
            raise HangtuError(
                f"QC rule {rule_id!r} doesn't exist. The rules are "
                f"{', '.join(defaults)}, and V<rule> for one python-ags4 rule."
            )
        if not isinstance(override, Mapping):
            raise HangtuError(
                f"The override for QC rule {rule_id} must be a dict of "
                f"{', '.join(RULE_KEYS)}, not {override!r}."
            )
        for key, value in override.items():
            if key not in RULE_KEYS:
                raise HangtuError(
                    f"QC rule {rule_id} has no setting {key!r}. "
                    f"The settings are {', '.join(RULE_KEYS)}."
                )
            if key == "severity" and value not in SEVERITIES:
                raise HangtuError(
                    f"QC rule {rule_id} can't have severity {value!r}. "
                    f"Use one of {', '.join(SEVERITIES)}."
                )
            if key == "enabled" and not isinstance(value, bool):
                raise HangtuError(
                    f"QC rule {rule_id}: enabled must be true or false, not {value!r}."
                )
            if key == "thresholds":
                _check_threshold_names(rule_id, value)


def _check_threshold_names(rule_id: str, thresholds: Any) -> None:
    known = THRESHOLDS.get(rule_id, {})
    if is_ingest_rule(rule_id):
        raise HangtuError(
            f"QC rule {rule_id} is raised at ingest and has no thresholds; "
            f"it takes severity and enabled only."
        )
    if not isinstance(thresholds, Mapping):
        raise HangtuError(
            f"The thresholds of QC rule {rule_id} must be a dict of name: value, "
            f"not {thresholds!r}."
        )
    for name in thresholds:
        if name not in known:
            names = (
                f"Its thresholds are {', '.join(known)}."
                if known
                else "It has no thresholds."
            )
            raise HangtuError(f"QC rule {rule_id} has no threshold {name!r}. {names}")


def _threshold(rule_id: str, name: str, given: Any) -> Threshold:
    """Check one threshold against its kind and convert it to the canonical unit."""
    kind = THRESHOLDS[rule_id][name]
    where = f"QC rule {rule_id}, threshold {name}"
    if kind == "count":
        number = _plain_number(given)
        if number is None:
            raise UnitsError(
                f"{where} is a count and takes a plain number with no unit, "
                f"e.g. {name}: 5, not {given!r}."
            )
        return Threshold(str(given), number, kind)
    example = _config.load("qc/rules.yaml")["rules"][rule_id]["thresholds"][name]
    if _plain_number(given) is not None:
        raise UnitsError(
            f"{where} needs a unit: write it as a number and a unit, "
            f'e.g. {name}: "{example}". Units are never guessed.'
        )
    text = str(given).strip()
    try:
        value, unit_text = units.parse_quantity(text, kind)
    except UnitsError as error:
        raise UnitsError(f"{where}: {error}") from None
    unit = units.parse_unit(unit_text)
    # pint reads % and a bare number as dimensionless, like degrees, so
    # check_dimension lets them through as angles.
    if kind == "angle" and unit in (units.ureg.Unit("percent"), units.ureg.Unit("")):
        raise UnitsError(
            f'{where} is an angle, but its unit "{unit_text}" isn\'t an angle '
            f'unit. Use degrees, e.g. {name}: "{example}".'
        )
    canonical = units.quantity_kind(kind)["canonical"]
    if canonical is not None:
        value = float(units.convert([value], unit, kind, units.ureg.Unit(canonical))[0])
    return Threshold(text, value, kind)


def _plain_number(given: Any) -> float | None:
    """Return ``given`` as a float if it is a number with no unit, else None."""
    if isinstance(given, bool):
        return None
    if isinstance(given, int | float):
        return float(given)
    try:
        return float(str(given))
    except ValueError:
        return None


def _merge_min_fields(
    overrides: dict[str, Any],
) -> dict[str, dict[str, tuple[str, ...]]]:
    merged = {
        group: {kind: _flatten(lists.get(kind) or []) for kind in FIELD_KINDS}
        for group, lists in _config.load("qc/min_fields.yaml")["min_fields"].items()
    }
    for group, lists in overrides.items():
        _check_group(group)
        if not isinstance(lists, Mapping):
            raise HangtuError(
                f"min_fields for {group} must be a dict of "
                f"{' and/or '.join(FIELD_KINDS)} lists, not {lists!r}."
            )
        entry = merged.setdefault(group, {kind: () for kind in FIELD_KINDS})
        for kind, headings in lists.items():
            if kind not in FIELD_KINDS:
                raise HangtuError(
                    f"min_fields for {group} has no list {kind!r}. "
                    f"The lists are {', '.join(FIELD_KINDS)}."
                )
            headings = _flatten(headings or [])
            for heading in headings:
                _check_heading(group, heading)
            entry[kind] = headings
    return merged


def _flatten(headings: Any) -> tuple[str, ...]:
    """Flatten one level, so ``[*spec_key, LLPL_LL]`` reads as a plain list."""
    if isinstance(headings, str):
        return (headings,)
    flat: list[str] = []
    for item in headings:
        flat.extend(item if isinstance(item, list | tuple) else [item])
    return tuple(str(item) for item in flat)


def _check_group(group: str) -> None:
    if any(group in standard(version).groups for version in DICTIONARY_VERSIONS):
        return
    known = sorted({g for v in DICTIONARY_VERSIONS for g in standard(v).groups})
    close = difflib.get_close_matches(group, known, n=3)
    hint = f" Did you mean {', '.join(close)}?" if close else ""
    raise HangtuError(
        f"min_fields names group {group!r}, which isn't in the AGS 4 "
        f"dictionaries.{hint} The groups are {', '.join(known)}."
    )


def _check_heading(group: str, heading: str) -> None:
    for version in DICTIONARY_VERSIONS:
        if (group, heading) in standard(version).headings:
            return
    known = list(
        dict.fromkeys(
            h
            for v in DICTIONARY_VERSIONS
            for (g, h) in standard(v).headings
            if g == group
        )
    )
    raise HangtuError(
        f"min_fields names heading {heading!r} in {group}, which isn't in the "
        f"AGS 4 dictionaries. The headings of {group} are {', '.join(known)}."
    )
