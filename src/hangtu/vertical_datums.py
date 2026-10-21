"""The vertical datum table (docs/data/ingest.md §7, "Datum table").

Datums are stored by their short name as EPSG abbreviates it (``NAVD88``), so
a label reads the same whatever spelling a file or a setting used.
"""

import re
from collections.abc import Iterable
from typing import Any

from hangtu import _config
from hangtu.errors import HangtuError

_datums: dict[str, dict[str, Any]] = {}


def _reset() -> None:
    """Restore the table to the shipped ``vertical_datums.yaml``."""
    _datums.clear()
    _datums.update(_config.load("vertical_datums.yaml"))


_reset()


def _normalize(text: str) -> str:
    """Casefold ``text`` and drop spaces, ``-`` and ``_``."""
    return re.sub(r"[\s\-_]", "", text).casefold()


def _names(short_name: str, entry: dict[str, Any]) -> list[str]:
    return [short_name, entry["name"], *entry.get("spellings", ())]


def match(text: str) -> str | None:
    """Return the short name of the datum ``text`` names, or None if none does.

    ``"NAVD 88"``, ``"navd-88"`` and ``"North American Vertical Datum 1988"``
    all give ``"NAVD88"``. Only names in the table match.
    """
    wanted = _normalize(text)
    for short_name, entry in _datums.items():
        if any(_normalize(name) == wanted for name in _names(short_name, entry)):
            return short_name
    return None


def add_vertical_datum(
    short_name: str,
    *,
    name: str,
    epsg: int | None = None,
    spellings: Iterable[str] = (),
) -> None:
    """Add a vertical datum to the datum table for this session.

    A file's ``LOCA_DATM`` is read only when it names a datum in the table, so
    add a local or less common datum before ingesting the file.

    Parameters
    ----------
    short_name
        The name to store and show on elevation labels, e.g. ``"ATD"``.
    name
        The datum's full name, e.g. ``"Anytown datum"``.
    epsg
        The EPSG datum code, if it has one.
    spellings
        Other ways files write it. Matching ignores case, spaces, ``-`` and ``_``.

    Examples
    --------
    >>> ht.add_vertical_datum("ATD", name="Anytown datum", spellings=["Anytown"])
    """
    for text in (short_name, name):
        if not isinstance(text, str) or not text.strip():
            raise HangtuError(
                f"A vertical datum's short name and name must be non-empty strings, "
                f"not {text!r}. Example: "
                'ht.add_vertical_datum("ATD", name="Anytown datum")'
            )
    spellings = list(spellings)
    for text in (short_name, name, *spellings):
        existing = match(text)
        if existing is not None:
            raise HangtuError(
                f'"{text}" already names the vertical datum {existing} '
                f"({_datums[existing]['name']}). Use {existing}, or choose another "
                "name."
            )
    _datums[short_name] = {"name": name, "epsg": epsg, "spellings": spellings}
