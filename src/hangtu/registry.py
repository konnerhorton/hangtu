"""The column registry and CSV templates (docs/plots/P00-framework.md §5)."""

from typing import Any

import pandas as pd

from hangtu import _config
from hangtu.errors import ColumnError

_DTYPES = {"number": "float64", "text": "object", "bool": "bool"}


def _registry() -> dict[str, Any]:
    return _config.load("columns.yaml")


def column_info(name: str) -> dict[str, Any] | None:
    """Return the registry entry for column ``name``, or None if it isn't registered."""
    return _registry()["columns"].get(name)


def statistics_roles() -> dict[str, dict[str, Any]]:
    """Return the columns with a ``statistics:`` field, by name, and that field.

    The field says how ``ht.stats`` functions treat a flag or source column
    (the header of ``columns.yaml``).
    """
    return {
        name: entry["statistics"]
        for name, entry in _registry()["columns"].items()
        if "statistics" in entry
    }


def qualifier_for(column: str) -> str:
    """Return the qualifier column that holds ``<`` or ``>`` for ``column``.

    It is the qualifier that names ``column`` and replaces the generic one
    (``remolded_qualifier`` for ``remolded_undrained_shear_strength``), else the
    generic ``qualifier``. A qualifier that doesn't replace the generic one, such
    as ``correlation_qualifier``, which only hangtu writes, is never returned.
    """
    for name, field in statistics_roles().items():
        if (
            field["role"] == "qualifier"
            and "replaces" in field
            and column in field.get("values", ())
        ):
            return name
    return "qualifier"


def _entry(name: str) -> dict[str, Any]:
    """Return the entry for a template name: a column, or an overlay field."""
    registry = _registry()
    return registry["columns"].get(name) or registry["fields"][name]


def _template_columns(name: str) -> list[str]:
    templates = _registry()["templates"]
    if name not in templates:
        raise ColumnError(
            f"There is no template named {name!r}. "
            f"Templates: {', '.join(templates)}. Example: ht.template('spt')"
        )
    return templates[name]


def _column_row(name: str, entry: dict[str, Any]) -> dict[str, str]:
    quantity = entry.get("quantity")
    kind = _config.quantity_kinds().get(quantity, {}) if quantity else {}
    return {
        "name": name,
        "description": entry["description"],
        "quantity": entry.get("quantity", ""),
        "us_unit": (kind.get("US") or {}).get("text") or "",
        "si_unit": (kind.get("SI") or {}).get("text") or "",
        "used_by": ", ".join(entry.get("used_by", [])),
    }


def _frame_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Units read from attrs directly: hangtu.units imports this module.
    declared = df.attrs.get("units", {})
    rows = []
    for column in df.columns:
        name = str(column)
        entry = column_info(name)
        row = (
            _column_row(name, entry)
            if entry is not None
            else {
                "name": name,
                "description": "Not a registered column",
                "quantity": "",
                "us_unit": "",
                "si_unit": "",
                "used_by": "",
            }
        )
        row["declared_unit"] = declared.get(column, "")
        rows.append(row)
    return pd.DataFrame(rows)


def columns(template: str | pd.DataFrame | None = None) -> pd.DataFrame:
    """List the registered columns as a table, or the columns of a DataFrame.

    Parameters
    ----------
    template : str or pandas.DataFrame, optional
        A template name lists only that template's columns, in template order,
        e.g. ``"spt"``. Overlay templates such as ``"ranges"`` also list their
        overlay fields (``low``, ``high``), which take the plotted value's
        units. A DataFrame lists its own columns, in its order, with the unit
        declared on each, so you can check a file before declaring its units.

    Returns
    -------
    pandas.DataFrame
        One row per column: name, description, quantity kind, US and SI unit
        (blank when the column has no unit), and the plots that use it. The US
        and SI units are also what ``system="US"`` or ``"SI"`` declares. For a
        DataFrame, a ``declared_unit`` column holds the unit declared on it
        (blank if none), and a column the registry doesn't know is described as
        "Not a registered column".

    Examples
    --------
    >>> ht.columns("spt")

    Check a lab sheet's units before declaring them: compare ``us_unit`` with
    the units on the sheet, then declare the system and any exceptions.

    >>> lab = ht.read_csv("lab.csv")
    >>> ht.columns(lab)[["name", "us_unit", "declared_unit"]]
    >>> lab = ht.set_units(lab, system="US", units={"cell_pressure": "ksf"})
    """
    if isinstance(template, pd.DataFrame):
        return _frame_columns(template)
    names = (
        list(_registry()["columns"])
        if template is None
        else _template_columns(template)
    )
    return pd.DataFrame([_column_row(name, _entry(name)) for name in names])


def template(name: str) -> pd.DataFrame:
    """Return an empty DataFrame with the columns of template ``name``.

    Save it with ``.to_csv(path, index=False)`` to get a file to fill in. The
    file has one header row and no units row: declare units when you read it
    back with ``ht.read_csv(path, units={...})``.

    Examples
    --------
    >>> ht.template("spt").to_csv("spt.csv", index=False)
    """
    return pd.DataFrame(
        {
            column: pd.Series(dtype=_DTYPES[_entry(column)["type"]])
            for column in _template_columns(name)
        }
    )
