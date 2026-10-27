"""``p.density()`` and ``p.particle_density()`` (datasets.md §6.8, §6.9; M14)."""

from os import PathLike

import numpy as np
import pandas as pd

from hangtu.datasets._frame import Build
from hangtu.datasets._lab import SPECIMEN_COLUMNS, specimens

#: Standard gravity (m/s², exact by definition). A density in Mg/m³ times g is
#: a unit weight in kN/m³ (datasets.md §6.8).
G = 9.80665

DENSITY_COLUMNS = [
    *SPECIMEN_COLUMNS,
    "bulk_unit_weight",
    "dry_unit_weight",
    "water_content",
    "particle_density",
    "particle_density_assumed",
    "sample_condition",
    "stabilizer_content",
    "source",
    "test_type",
]
#: Text columns only one of the two groups fills.
TEXT_COLUMNS = [
    "specimen_id",
    "sample_reference",
    "specimen_reference",
    "sample_condition",
]
PARTICLE_DENSITY_COLUMNS = [
    *SPECIMEN_COLUMNS,
    "particle_density",
    "particle_density_assumed",
    "test_type",
]


def density(
    path: str | PathLike[str],
    *,
    display_units: str | None = None,
    include_incomplete: bool = False,
    **common,
) -> pd.DataFrame:
    """Build the density dataset; see ``Project.density``."""
    build = Build(
        path,
        noun=("density result", "density results"),
        display_units=display_units,
        include_incomplete=include_incomplete,
    )
    parts = []
    if build.has("LDEN"):
        rows = build.rows("LDEN")
        lab = specimens(build, "LDEN", rows)
        lab["bulk_unit_weight"] = build.numbers(rows, "LDEN_BDEN") * G
        lab["dry_unit_weight"] = build.numbers(rows, "LDEN_DDEN") * G
        lab["water_content"] = build.numbers(rows, "LDEN_MC")
        lab["sample_condition"] = build.texts(rows, "LDEN_COND")
        lab["source"] = "lab"
        lab["test_type"] = build.texts(rows, "LDEN_TYPE")
        parts.append(lab)
    if build.has("IDEN"):
        rows = build.rows("IDEN")
        depth = build.numbers(rows, "IDEN_DPTH")
        basis = pd.Series("test_depth", index=rows.index, dtype=object)
        parts.append(
            pd.DataFrame(
                {
                    "location_id": rows["location_id"],
                    "loca_id": build.texts(rows, "LOCA_ID"),
                    "depth": depth,
                    "depth_basis": basis.where(depth.notna(), None),
                    "bulk_unit_weight": build.numbers(rows, "IDEN_IDEN") * G,
                    "water_content": build.numbers(rows, "IDEN_MC"),
                    "stabilizer_content": build.numbers(rows, "IDEN_STAB"),
                    "source": "field",
                    "test_type": build.texts(rows, "IDEN_TYPE"),
                    "_line": rows["_line"],
                }
            )
        )
    if not parts:
        return build.finish(
            pd.DataFrame(), DENSITY_COLUMNS, group="LDEN or IDEN", **common
        )
    frame = pd.concat(parts, ignore_index=True)
    # Field rows have no sample or specimen: blank (None), as texts() gives.
    for column in TEXT_COLUMNS:
        frame[column] = frame[column].astype(object).where(frame[column].notna(), None)
    # Blank until the particle density join; never False, which would say
    # "measured".
    frame["particle_density"] = np.nan
    frame["particle_density_assumed"] = pd.array([pd.NA] * len(frame), "boolean")
    return build.finish(frame, DENSITY_COLUMNS, **common)


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
