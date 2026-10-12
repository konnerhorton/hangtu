"""Unit strings, quantity kinds and display conversion (docs/plots/P00-framework.md §4).

One pint ``UnitRegistry`` serves the whole process. Plots only ever receive
plain magnitudes from here; pint objects never reach matplotlib.
"""

import re
from collections.abc import Iterable, Mapping
from os import PathLike
from typing import Any

import numpy as np
import pandas as pd
import pint

from hangtu import _config
from hangtu._settings import _display_units, settings
from hangtu.errors import ColumnError, UnitsError, warn
from hangtu.registry import column_info

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
    """Define a new unit in hangtu's pint registry, using pint's definition syntax.

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


def _display_target(quantity: str, system: str) -> tuple[pint.Unit | None, str | None]:
    override = settings.display_overrides.get(quantity)
    if override is not None:
        return parse_unit(override), _pretty(override)
    target = quantity_kind(quantity)[system]
    unit = ureg.Unit(target["unit"]) if target["unit"] else None
    return unit, target["text"]


def _pretty(text: str) -> str:
    """Write unit powers as superscripts: ``kN/m3`` -> ``kN/m³``."""
    return re.sub(r"(?<=[A-Za-z])([23])\b", lambda m: "²³"[int(m[1]) - 2], text)


def convert(values: Any, unit: pint.Unit, quantity: str, to: pint.Unit) -> np.ndarray:
    """Convert magnitudes from ``unit`` to ``to``, applying P00 §4.3 #1 for density."""
    factor = ureg.Quantity(1.0, unit)
    if quantity == "density" and _is_force_per_volume(unit):
        factor = factor / ureg.Quantity(1.0, "standard_gravity")
    return np.asarray(values, dtype=float) * factor.to(to).magnitude


def to_display(
    values: Iterable[float],
    unit: str | None,
    quantity: str | None,
    display_units: str | None = None,
) -> tuple[np.ndarray, str | None]:
    """Convert values to the display unit for their quantity kind.

    Parameters
    ----------
    values
        Magnitudes in ``unit``.
    unit
        The declared unit string, or None when it is unknown.
    quantity
        The quantity kind, or None for an unregistered column.
    display_units
        ``"US"`` or ``"SI"``; defaults to ``ak.settings.display_units``.

    Returns
    -------
    magnitudes, unit text
        The unit text is what the axis label shows, or None for no unit. Values
        are returned unchanged when the unit is unknown, when the column has no
        quantity kind (its unit is never guessed), and for kinds that are never
        converted (percent, dimensionless, count).
    """
    system = _display_units(display_units or settings.display_units)
    magnitudes = np.asarray(values, dtype=float)
    if quantity is None:
        return magnitudes, None if unit is None else _pretty(unit)
    kind = quantity_kind(quantity)
    if kind["canonical"] is None:
        return magnitudes, kind[system]["text"]
    if unit is None:
        return magnitudes, None
    target, text = _display_target(quantity, system)
    source, _ = _lookup(unit)
    if source is None:
        source = parse_unit(unit)
    return convert(magnitudes, source, quantity, target), text


# --- Units on DataFrames (P00 §4.4, SPEC §2.6) -------------------------------------


def _registered_kind(column: str) -> str | None:
    info = column_info(column)
    return None if info is None else info.get("quantity")


def _check_declared(column: str, text: str, quantity: str | None) -> None:
    info = column_info(column)
    if info is not None and info["type"] != "number":
        raise UnitsError(
            f"Column {column!r} holds {info['type']} values, so it has no unit. "
            f"Remove it from the units you declare."
        )
    unit = parse_unit(text, column)
    if quantity is not None:
        check_dimension(unit, quantity, column)


def set_units(df: pd.DataFrame, units: Mapping[str, str]) -> pd.DataFrame:
    """Declare the units of some columns, returning a new DataFrame.

    The units are checked and stored in ``df.attrs["units"]``, merged with any
    already declared. The input DataFrame is not changed.

    Parameters
    ----------
    df : pandas.DataFrame
        The data.
    units : dict
        ``{column: unit string}``, e.g. ``{"depth": "ft"}``.

    Examples
    --------
    >>> spt = ak.set_units(spt, {"depth": "ft", "ground_level": "ft"})
    """
    if not isinstance(units, Mapping):
        raise UnitsError(
            f"units must be a dict of {{column: unit}}, not {units!r}. "
            'Example: ak.set_units(df, {"depth": "ft"})'
        )
    missing = [column for column in units if column not in df.columns]
    if missing:
        raise ColumnError(
            f"Can't set units for {missing}: no such column. "
            f"Columns: {', '.join(map(str, df.columns))}."
        )
    for column, text in units.items():
        _check_declared(column, text, _registered_kind(column))
    result = df.copy(deep=False)
    result.attrs["units"] = {**units_of(df), **units}
    return result


def units_of(df: pd.DataFrame) -> dict[str, str]:
    """Return the declared units of ``df`` as ``{column: unit string}``.

    The result is empty when no units are declared. ``merge``, ``join`` and
    ``concat`` drop declared units; declare them again on the result.
    """
    return dict(df.attrs.get("units", {}))


def read_csv(
    path: str | PathLike[str],
    units: Mapping[str, str] | None = None,
    **pandas_kwargs: Any,
) -> pd.DataFrame:
    """Read a CSV file and declare the units of its columns.

    Parameters
    ----------
    path
        The CSV file. Headers are column names from ``ak.columns()``; there is
        no units row.
    units : dict, optional
        ``{column: unit string}``, e.g. ``{"depth": "ft"}``. Columns that are
        percentages, counts or dimensionless need no units.
    **pandas_kwargs
        Passed to ``pandas.read_csv``.

    Examples
    --------
    >>> spt = ak.read_csv("spt.csv", units={"depth": "ft", "ground_level": "ft"})
    """
    df = pd.read_csv(path, **pandas_kwargs)
    return set_units(df, units) if units else df


def needs_units(column: str, quantity: str | None = None) -> bool:
    """Return whether a column's values depend on a unit.

    ``quantity`` is the kind for an unregistered column (e.g. from a plot
    preset); registered columns use the registry's kind. A column with no known
    kind always needs a unit, because its unit is never guessed.
    """
    kind = _registered_kind(column) or quantity
    return kind is None or quantity_kind(kind)["canonical"] is not None


def resolve_units(
    df: pd.DataFrame,
    columns: Iterable[str],
    units: Mapping[str, str] | None = None,
    *,
    quantities: Mapping[str, str] | None = None,
    analysis: bool = False,
) -> dict[str, str | None]:
    """Find each column's unit, in the order of SPEC §2.6.

    1. ``units``, the explicit argument; 2. ``df.attrs["units"]``; 3. no unit
    needed (percent, dimensionless and count columns). Otherwise the unit is
    unknown: a plot gets None and a warning, an analysis gets ``UnitsError``.

    Returns
    -------
    dict
        ``{column: unit string or None}``. None means unknown, or not needed
        when ``needs_units`` is False.
    """
    units = units or {}
    quantities = quantities or {}
    declared = units_of(df)
    resolved: dict[str, str | None] = {}
    for column in columns:
        quantity = _registered_kind(column) or quantities.get(column)
        if column in units:
            _check_declared(column, units[column], quantity)
            resolved[column] = units[column]
        elif column in declared:
            resolved[column] = declared[column]
        else:
            resolved[column] = None
            if needs_units(column, quantity):
                _unknown_units(column, quantity, analysis)
    return resolved


def _unknown_units(column: str, quantity: str | None, analysis: bool) -> None:
    example = quantity_kind(quantity)["US"]["text"] if quantity else "<unit>"
    fix = (
        f'Declare them with ak.set_units(df, {{"{column}": "{example}"}}) '
        f'or ak.read_csv(..., units={{"{column}": "{example}"}}).'
    )
    if analysis:
        raise UnitsError(f"Column {column!r} has no units. {fix}")
    warn(
        f"Column {column!r} has no units, so its axis label says "
        f'"(units unknown)". {fix}'
    )


_QUANTITY_TEXT = re.compile(
    r"\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\s*(\S.*?)\s*"
)


def parse_quantity(text: str, quantity: str | None = None) -> tuple[float, str]:
    """Split a string such as ``"3 m"`` or ``"10 ft"`` into a value and a unit.

    The unit goes through the same alias table as column units (P00 §4.3 #4)
    and, when ``quantity`` is given, the same dimension check.

    Returns
    -------
    value, unit string
        Ready for ``to_display([value], unit, quantity)``.
    """
    match = _QUANTITY_TEXT.fullmatch(text) if isinstance(text, str) else None
    if match is None:
        raise UnitsError(
            f'{text!r} must be a number followed by a unit, e.g. "3 m" or "10 ft".'
        )
    unit = parse_unit(match[2])
    if quantity is not None:
        check_dimension(unit, quantity)
    return float(match[1]), match[2]
