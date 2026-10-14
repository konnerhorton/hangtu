"""Example data files that ship with hangtu.

A synthetic site in US units: ``site.ags`` with its geology map
``strata.csv``, and the same tests as CSV files (``spt.csv``,
``atterberg.csv``, ``permeability.csv``) laid out like ``ht.template()``.

Examples
--------
>>> p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
>>> spt = ht.read_csv(ht.examples.path("spt.csv"), units={"depth": "ft"})
"""

from importlib.resources import files
from pathlib import Path

from hangtu.errors import HangtuError

__all__ = ["names", "path"]


def names() -> list[str]:
    """List the example files."""
    data = files(__name__).joinpath("data")
    return sorted(entry.name for entry in data.iterdir() if entry.is_file())


def path(name: str) -> Path:
    """Return the path of example file ``name``, e.g. ``"site.ags"``.

    The files are read-only: write databases and outputs somewhere else.
    """
    available = names()
    if name not in available:
        raise HangtuError(f"No example file {name!r}. Files: {', '.join(available)}.")
    return Path(str(files(__name__).joinpath("data", name)))
