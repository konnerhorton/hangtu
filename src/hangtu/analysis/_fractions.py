"""Size-fraction systems and the passing at a size (docs/drafts/analysis.md §3.5)."""

import re
from os import PathLike
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from hangtu import _config
from hangtu.errors import HangtuError
from hangtu.registry import column_info

_NAME = re.compile(r"[a-z][a-z0-9]*(_[a-z0-9]+)*")


def builtin_systems() -> dict[str, dict[str, Any]]:
    """Return the built-in systems from ``config/fraction_systems.yaml``."""
    return _config.load("config/fraction_systems.yaml")


def _builtin_fraction_names() -> set[str]:
    return {
        fraction["name"]
        for system in builtin_systems().values()
        for fraction in system["fractions"]
    }


def content_column(name: str) -> str:
    """Return the column holding a fraction's percentage: ``<name>_content``."""
    return f"{name}_content"


def _bad(system: str, problem: str) -> HangtuError:
    return HangtuError(
        f"Fraction system {system!r}: {problem} See the built-in systems in "
        "config/fraction_systems.yaml for the structure."
    )


def _size(system: str, where: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise _bad(system, f"{where} must be a size in mm, not {value!r}.")
    return float(value)


def _check_parts(system: str, fraction: dict[str, Any], lower: float) -> None:
    parts = fraction.get("parts") or []
    if not isinstance(parts, list):
        raise _bad(system, f"the parts of {fraction['name']!r} must be a list.")
    names: set[str] = set()
    previous = lower
    for part in parts:
        if not isinstance(part, dict) or "name" not in part or "upper" not in part:
            raise _bad(
                system,
                f"each part of {fraction['name']!r} needs a name and an upper size.",
            )
        upper = _size(system, f"the upper size of part {part['name']!r}", part["upper"])
        if part["name"] in names or upper <= previous:
            raise _bad(
                system,
                f"the parts of {fraction['name']!r} must have different names and "
                "increasing upper sizes.",
            )
        names.add(part["name"])
        previous = upper
    if parts and previous != fraction["upper"]:
        raise _bad(
            system,
            f"the last part of {fraction['name']!r} must end at the fraction's "
            f"upper size, {fraction['upper']:g} mm.",
        )


def check_system(name: str, system: Any) -> list[dict[str, Any]]:
    """Check a fraction system's structure and return its fractions (§3.5)."""
    if not isinstance(system, dict) or not isinstance(system.get("fractions"), list):
        raise _bad(name, "it must hold a list of fractions under 'fractions'.")
    fractions = system["fractions"]
    if not fractions:
        raise _bad(name, "it has no fractions.")
    allowed = _builtin_fraction_names()
    names: set[str] = set()
    previous = 0.0
    for position, fraction in enumerate(fractions):
        if not isinstance(fraction, dict) or not {"name", "lower", "upper"} <= set(
            fraction
        ):
            raise _bad(name, "each fraction needs a name, a lower and an upper size.")
        label = fraction["name"]
        if not isinstance(label, str) or not _NAME.fullmatch(label):
            raise _bad(
                name,
                f"fraction name {label!r} must be lowercase words joined by "
                "underscores, e.g. coarse_sand.",
            )
        if label in names:
            raise _bad(name, f"fraction {label!r} is listed twice.")
        if label not in allowed and column_info(content_column(label)) is not None:
            raise _bad(
                name,
                f"fraction {label!r} would make the column "
                f"{content_column(label)!r}, which the registry already uses for "
                "something else. Rename the fraction.",
            )
        names.add(label)
        lower = _size(name, f"the lower size of {label!r}", fraction["lower"])
        last = position == len(fractions) - 1
        if lower != previous:
            where = "start at 0" if position == 0 else "start where the one before ends"
            raise _bad(
                name,
                f"fraction {label!r} starts at {lower:g} mm, but it must {where} "
                f"({previous:g} mm): fractions can't overlap or leave gaps.",
            )
        if fraction["upper"] is None:
            if not last:
                raise _bad(name, f"only the last fraction can be open, not {label!r}.")
            continue
        upper = _size(name, f"the upper size of {label!r}", fraction["upper"])
        if upper <= lower:
            raise _bad(name, f"fraction {label!r} must end above where it starts.")
        if last:
            raise _bad(
                name,
                f"the last fraction, {label!r}, must be open (upper: null), so every "
                "size is in a fraction.",
            )
        _check_parts(name, fraction, lower)
        previous = upper
    return fractions


def fraction_system(fractions: Any) -> tuple[str, list[dict[str, Any]]]:
    """Resolve ``fractions=``: a built-in name, a dict, or a YAML file's path."""
    systems = builtin_systems()
    if isinstance(fractions, str) and fractions in systems:
        return fractions, check_system(fractions, systems[fractions])
    if isinstance(fractions, str | PathLike) and Path(fractions).suffix in {
        ".yaml",
        ".yml",
    }:
        path = Path(fractions)
        if not path.is_file():
            raise HangtuError(f"Fraction system file {str(path)!r} not found.")
        fractions = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(fractions, dict):
        name = fractions.get("name")
        if not isinstance(name, str) or not name.strip():
            raise HangtuError(
                "A fraction system of your own needs a 'name', which goes in the "
                "fraction_system column. Example: {'name': 'project_bands', "
                "'fractions': [...]}"
            )
        if name in systems:
            raise HangtuError(
                f"{name!r} is a built-in fraction system. Give yours another name, "
                'or use the built-in one with fractions="' + name + '".'
            )
        return name, check_system(name, fractions)
    raise HangtuError(
        f"There is no fraction system {fractions!r}. Built-in systems: "
        f"{', '.join(map(repr, systems))}; or pass your own as a dict or the path "
        'to a YAML file. Example: fractions="iso14688"'
    )


def passing_at(sizes: np.ndarray, passing: np.ndarray, size: float | None) -> float:
    """Return the % passing at ``size`` (mm), or NaN where the curve can't say.

    ``sizes`` are sorted from the finest up and distinct. Log-linear between
    points and exact at a point (§3.5). P(0) = 0 and P(open upper) = 100. Above
    the coarsest point it is 100 only if that point passes 100 %; below the
    finest point it is 0 only if that point passes 0 %.
    """
    if size is None:
        return 100.0
    if size == 0:
        return 0.0
    if size > sizes[-1]:
        return 100.0 if passing[-1] == 100 else np.nan
    if size < sizes[0]:
        return 0.0 if passing[0] == 0 else np.nan
    i = int(np.searchsorted(sizes, size, side="left"))
    if sizes[i] == size:
        return float(passing[i])
    low, high = np.log10(sizes[i - 1]), np.log10(sizes[i])
    share = (np.log10(size) - low) / (high - low)
    return float(passing[i - 1] + share * (passing[i] - passing[i - 1]))
