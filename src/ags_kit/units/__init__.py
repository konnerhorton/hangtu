"""Unit strings and quantity kinds (docs/plots/P00-framework.md §4).

One pint ``UnitRegistry`` serves the whole process. Plots only ever receive
plain magnitudes from here; pint objects never reach matplotlib.
"""

from typing import Any

import pint

from ags_kit import _config
from ags_kit.errors import UnitsError, warn

ureg = pint.UnitRegistry()

_aliases: dict[str, str] = {}


def _reset_aliases() -> None:
    """Restore the alias table to the shipped ``units/aliases.yaml``."""
    _aliases.clear()
    _aliases.update(_config.load("units/aliases.yaml"))


_reset_aliases()


def _pint_unit(expression: str) -> pint.Unit | None:
    """Return the pint unit for ``expression``, or None if pint can't read it."""
    try:
        return ureg.Unit(expression)
    except Exception:  # pint raises many error types for unreadable strings
        return None


def _lookup(text: str) -> tuple[pint.Unit | None, bool]:
    """Return ``(unit, from_alias)``; the unit is None when nothing matches."""
    if text in _aliases:
        return ureg.Unit(_aliases[text]), True
    return _pint_unit(text), False


def _where(column: str | None) -> str:
    return f" for column {column!r}" if column else ""


def parse_unit(text: str, column: str | None = None) -> pint.Unit:
    """Read a unit string, in the lookup order of P00 §4.2.

    1. The alias table (``units/aliases.yaml`` plus ``ak.add_unit_alias``).
    2. pint's own parser, with a warning saying what the string was read as.
    3. Otherwise ``UnitsError``.

    Lookups are case-sensitive: ``"ft"`` is a foot, ``"Ft"`` is unknown.
    """
    if not isinstance(text, str) or not text.strip():
        raise UnitsError(
            f'The unit{_where(column)} must be a unit string such as "ft", '
            f"not {text!r}."
        )
    unit, from_alias = _lookup(text)
    if unit is None:
        close = [alias for alias in _aliases if alias.lower() == text.lower()]
        suggestion = f' Did you mean "{close[0]}"?' if close else ""
        raise UnitsError(
            f'Unit "{text}"{_where(column)} isn\'t recognized, and unit strings are '
            f"case-sensitive.{suggestion} If it is a real unit, add it with "
            f'ak.add_unit_alias("{text}", "<pint unit>"), '
            f'e.g. ak.add_unit_alias("{text}", "foot").'
        )
    if not from_alias:
        warn(
            f'Unit "{text}"{_where(column)} was read as {unit}. Add it with '
            f'ak.add_unit_alias("{text}", "{unit}") to silence this.'
        )
    return unit


def add_unit_alias(text: str, pint_expr: str) -> None:
    """Add a unit string to the alias table for this session.

    Examples
    --------
    >>> ak.add_unit_alias("feet", "foot")
    >>> ak.add_unit_alias("kN/m^2", "kilonewton / meter**2")
    """
    if not isinstance(text, str) or not text.strip():
        raise UnitsError(f"The alias must be a non-empty string, not {text!r}.")
    if _pint_unit(pint_expr) is None:
        raise UnitsError(
            f'Can\'t add alias "{text}": pint doesn\'t understand "{pint_expr}". '
            'Use a pint unit expression such as "foot" or "kilonewton / meter**2", '
            "or define a new unit first with ak.define_unit(...)."
        )
    _aliases[text] = pint_expr


def define_unit(pint_definition: str) -> None:
    """Define a new unit in ags-kit's pint registry, using pint's definition syntax.

    Examples
    --------
    >>> ak.define_unit("smoot = 1.7018 * meter")
    >>> ak.add_unit_alias("smoots", "smoot")
    """
    try:
        ureg.define(pint_definition)
    except Exception as error:
        raise UnitsError(
            f"Can't define unit {pint_definition!r}: {error}. "
            'Use pint\'s syntax, e.g. ak.define_unit("smoot = 1.7018 * meter").'
        ) from None


def quantity_kind(name: str) -> dict[str, Any]:
    """Return the entry for quantity kind ``name`` from ``config/defaults.yaml``."""
    return _config.quantity_kinds()[name]


def _kind_of(unit: pint.Unit) -> str | None:
    """Name the first quantity kind whose canonical unit has ``unit``'s dimension."""
    for name, kind in _config.quantity_kinds().items():
        canonical = kind["canonical"]
        if canonical and ureg.Unit(canonical).dimensionality == unit.dimensionality:
            return name
    return None


def _is_force_per_volume(unit: pint.Unit) -> bool:
    return unit.dimensionality == ureg.Unit("newton / meter**3").dimensionality


def check_dimension(unit: pint.Unit, quantity: str, column: str | None = None) -> None:
    """Raise ``UnitsError`` if ``unit`` can't hold a value of kind ``quantity``.

    Kinds with no canonical unit (percent, dimensionless, count) are never
    converted, so they only accept units that don't change the number: percent
    takes ``%``; dimensionless and count take any dimensionless unit. A density
    column also takes a force per volume such as ``pcf`` (P00 §4.3 #1).
    """
    canonical = quantity_kind(quantity)["canonical"]
    if canonical is None:
        ok = (
            unit == ureg.Unit("percent")
            if quantity == "percent"
            else unit.dimensionless
        )
    else:
        ok = unit.dimensionality == ureg.Unit(canonical).dimensionality or (
            quantity == "density" and _is_force_per_volume(unit)
        )
    if ok:
        return
    actual = _kind_of(unit)
    actual = (
        f"a {actual.replace('_', ' ')} unit" if actual else f"[{unit.dimensionality}]"
    )
    expected = quantity.replace("_", " ")
    example = quantity_kind(quantity)["US"]["text"] or "%"
    subject = f"Column {column!r} is" if column else "The value is"
    raise UnitsError(
        f'{subject} a {expected}, but its unit "{unit}" is {actual}. '
        f'Declare a {expected} unit instead, e.g. "{example}".'
    )
