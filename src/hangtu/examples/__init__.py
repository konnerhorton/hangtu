"""Example data files that ship with hangtu.

A synthetic site in US units: ``site.ags`` with its geology map
``strata.csv`` and its judgments file ``judgments.yaml`` (unit weights,
water levels, specific gravities and the sandstone's fixed σci), and the
same tests as CSV files (``spt.csv``, ``atterberg.csv``,
``permeability.csv``) laid out like ``ht.template()``.

``triaxial_readings.csv`` has readings during shearing for the site's six
triaxial stages, in psf, laid out like ``ht.template("triaxial_readings")``.
They are synthetic, made to end at each stage's failure values in
``site.ags``, for ``ht.plot.triaxial_shearing()``.

``rock_triaxial.csv`` has UCS and triaxial tests on the sandstone cored in
B-3, in MPa (depths in ft), laid out like ``ht.template("triaxial")`` with
``failure_mode`` filled, for ``ht.analysis.hoek_brown_fit()``. They aren't
in ``site.ags``.

Examples
--------
>>> p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
>>> spt = ht.read_csv(ht.examples.path("spt.csv"), units={"depth": "ft"})
>>> rock = ht.read_csv(
...     ht.examples.path("rock_triaxial.csv"),
...     units={
...         "depth": "ft",
...         "cell_pressure": "MPa",
...         "deviator_stress_at_failure": "MPa",
...         "back_pressure": "MPa",
...         "pore_pressure_at_failure": "MPa",
...         "reported_intact_compressive_strength": "MPa",
...     },
... )
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
