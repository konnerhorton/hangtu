"""``p.density()`` and ``p.particle_density()`` (datasets.md §6.8, §6.9; M14)."""

from os import PathLike

import pandas as pd

from hangtu.datasets._frame import Build
from hangtu.datasets._lab import SPECIMEN_COLUMNS, specimens

PARTICLE_DENSITY_COLUMNS = [
    *SPECIMEN_COLUMNS,
    "particle_density",
    "particle_density_assumed",
    "test_type",
]


def particle_density(
    path: str | PathLike[str],
    *,
    display_units: str | None = None,
    include_incomplete: bool = False,
    **common,
) -> pd.DataFrame:
    """Build the particle density dataset; see ``Project.particle_density``."""
    build = Build(
        path,
        noun=("particle density result", "particle density results"),
        display_units=display_units,
        include_incomplete=include_incomplete,
    )
    if not build.has("LPDN"):
        return build.finish(
            pd.DataFrame(), PARTICLE_DENSITY_COLUMNS, group="LPDN", **common
        )
    rows = build.rows("LPDN")
    frame = specimens(build, "LPDN", rows)
    frame["particle_density"] = build.numbers(rows, "LPDN_PDEN")
    frame["particle_density_assumed"] = build.flagged(
        "LPDN", rows, "LPDN_PDEN", "ASSUMED"
    )
    frame["test_type"] = build.texts(rows, "LPDN_TYPE")
    return build.finish(frame, PARTICLE_DENSITY_COLUMNS, **common)
