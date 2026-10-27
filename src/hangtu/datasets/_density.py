"""``p.density()`` and ``p.particle_density()`` (datasets.md §6.8, §6.9; M14)."""

from os import PathLike

import numpy as np
import pandas as pd

from hangtu.datasets._frame import Build
from hangtu.datasets._index import _nearest, _sample_keys
from hangtu.datasets._lab import SPECIMEN_COLUMNS, specimens
from hangtu.errors import warn

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
    "particle_density_specimen_id",
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
        lab["_sample"] = _sample_keys(build, rows)
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
    frame = _join_particle_density(build, frame)
    result = build.finish(frame, [*DENSITY_COLUMNS, "_chosen"], **common)
    _warn_chosen(result.pop("_chosen"), result)
    return result


def _join_particle_density(build: Build, frame: pd.DataFrame) -> pd.DataFrame:
    """Give each lab row its sample's particle density (§6.8, decision 4).

    The ``LPDN`` specimen of the same sample nearest the density specimen's
    depth, by ``p.index_properties()``'s rule (§6.6). Field rows, and samples
    with no ``LPDN``, stay blank: ``particle_density_assumed`` is NA, never
    False, which would say "measured". ``_chosen`` marks a row whose sample
    had several specimens to choose from.
    """
    frame["particle_density"] = np.nan
    frame["particle_density_assumed"] = pd.array([pd.NA] * len(frame), "boolean")
    frame["particle_density_specimen_id"] = None
    frame["_chosen"] = False
    found = _particle_densities(build)
    if found is None:
        return frame
    by_sample = {
        key: [row for _, row in group.iterrows()]
        for key, group in found.groupby("_sample", sort=False)
    }
    for i in frame.index[frame["source"] == "lab"]:
        candidates = by_sample.get(frame.at[i, "_sample"])
        if not candidates:
            continue
        chosen = _nearest(candidates, frame.at[i, "depth"], None)
        frame.at[i, "particle_density"] = chosen["particle_density"]
        frame.at[i, "particle_density_assumed"] = bool(chosen["assumed"])
        frame.at[i, "particle_density_specimen_id"] = chosen["specimen_id"]
        frame.at[i, "_chosen"] = len(candidates) > 1
    return frame


def _particle_densities(build: Build) -> pd.DataFrame | None:
    """Return the ``LPDN`` results with a value, as specimens, or None.

    Read from the table, not ``build.rows()``: a record with no value can't
    be joined, and isn't one of ``p.density()``'s own records to report as
    left out (§7).
    """
    if not build.has("LPDN"):
        return None
    rows = build.data.table("LPDN")
    found = specimens(build, "LPDN", rows)
    found["particle_density"] = build.numbers(rows, "LPDN_PDEN")
    found["assumed"] = build.flagged("LPDN", rows, "LPDN_PDEN", "ASSUMED")
    found["_sample"] = _sample_keys(build, rows)
    found["_specimen"] = found.index  # one row per specimen and value
    found = found[found["particle_density"].notna()]
    return None if found.empty else found


def _warn_chosen(chosen: pd.Series, result: pd.DataFrame) -> None:
    """Count the samples, among those returned, where a specimen was chosen."""
    samples = result.loc[chosen.to_numpy(dtype=bool), ["loca_id", "sample_reference"]]
    count = len(samples.drop_duplicates())
    if count:
        warn(
            f"{count} sample{'s' if count > 1 else ''} had more than one particle "
            "density specimen; the one nearest in depth was used. "
            "particle_density_specimen_id says which."
        )


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
