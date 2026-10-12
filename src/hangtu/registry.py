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


def _entry(name: str) -> dict[str, Any]:
    """Return the entry for a template name: a column, or an overlay field."""
    registry = _registry()
    return registry["columns"].get(name) or registry["fields"][name]


def _template_columns(name: str) -> list[str]:
    templates = _registry()["templates"]
    if name not in templates:
        raise ColumnError(
            f"There is no template named {name!r}. "
            f"Templates: {', '.join(templates)}. Example: ak.template('spt')"
        )
    return templates[name]


def columns(template: str | None = None) -> pd.DataFrame:
    """List the registered columns as a table.

    Parameters
    ----------
    template : str, optional
        Only list the columns of this template, in template order, e.g. ``"spt"``.
        Overlay templates such as ``"ranges"`` also list their overlay fields
        (``low``, ``high``), which take the plotted value's units.

    Returns
    -------
    pandas.DataFrame
        One row per column: name, description, quantity kind, US and SI display
        unit (blank when the column has no unit), and the plots that use it.

    Examples
    --------
    >>> ak.columns("spt")
    """
    names = (
        list(_registry()["columns"])
        if template is None
        else _template_columns(template)
    )
    kinds = _config.quantity_kinds()
    rows = []
    for name in names:
        entry = _entry(name)
        kind = kinds.get(entry.get("quantity"), {})
        rows.append(
            {
                "name": name,
                "description": entry["description"],
                "quantity": entry.get("quantity", ""),
                "us_unit": (kind.get("US") or {}).get("text") or "",
                "si_unit": (kind.get("SI") or {}).get("text") or "",
                "used_by": ", ".join(entry.get("used_by", [])),
            }
        )
    return pd.DataFrame(rows)


def template(name: str) -> pd.DataFrame:
    """Return an empty DataFrame with the columns of template ``name``.

    Save it with ``.to_csv(path, index=False)`` to get a file to fill in. The
    file has one header row and no units row: declare units when you read it
    back with ``ak.read_csv(path, units={...})``.

    Examples
    --------
    >>> ak.template("spt").to_csv("spt.csv", index=False)
    """
    return pd.DataFrame(
        {
            column: pd.Series(dtype=_DTYPES[_entry(column)["type"]])
            for column in _template_columns(name)
        }
    )
