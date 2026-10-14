"""``p.permeability()``: lab and field hydraulic conductivity (datasets.md §6.4)."""

from os import PathLike

import pandas as pd

from hangtu.datasets import _joins
from hangtu.datasets._frame import Build
from hangtu.datasets._lab import specimens

COLUMNS = [
    "loca_id",
    "ground_level",
    "depth",
    "depth_top",
    "depth_base",
    "depth_basis",
    "elevation",
    "hydraulic_conductivity",
    "qualifier",
    "source",
    "test_type",
]
#: Field groups: (group, value, type, top, base). IPRG is 4.0.x only.
FIELD = [
    ("FGHG", "FGHG_IPRM", "FGHG_TYPE", "FGHG_TOP", "FGHG_BASE"),
    ("IPRG", "IPRG_IPRM", "IPRG_TYPE", "IPRG_TOP", "IPRG_BASE"),
]


def permeability(
    path: str | PathLike[str],
    *,
    display_units: str | None = None,
    include_incomplete: bool = False,
    **common,
) -> pd.DataFrame:
    """Build the permeability dataset; see ``Project.permeability``."""
    build = Build(
        path,
        noun=("permeability result", "permeability results"),
        display_units=display_units,
        include_incomplete=include_incomplete,
    )
    parts = []
    if build.has("PTST"):
        rows = build.rows("PTST")
        lab = specimens(build, "PTST", rows)
        lab["hydraulic_conductivity"] = build.numbers(rows, "PTST_K")
        lab["qualifier"] = build.qualifier("PTST", rows, "PTST_K")
        lab["source"] = "lab"
        lab["test_type"] = build.texts(rows, "PTST_TYPE")
        parts.append(lab)
    for group, value, kind, top_heading, base_heading in FIELD:
        if not build.has(group):
            continue
        rows = build.rows(group)
        top = build.numbers(rows, top_heading)
        base = build.numbers(rows, base_heading)
        depth, basis = _joins.zone_depth(top, base)
        parts.append(
            pd.DataFrame(
                {
                    "location_id": rows["location_id"],
                    "loca_id": build.texts(rows, "LOCA_ID"),
                    "depth": depth,
                    "depth_top": top,
                    "depth_base": base,
                    "depth_basis": basis,
                    "hydraulic_conductivity": build.numbers(rows, value),
                    "qualifier": build.qualifier(group, rows, value),
                    "source": "field",
                    "test_type": build.texts(rows, kind),
                    "_line": rows["_line"],
                }
            )
        )
    if not parts:
        return build.finish(
            pd.DataFrame(), COLUMNS, group="PTST, FGHG or IPRG", **common
        )
    frame = pd.concat(parts, ignore_index=True)
    return build.finish(frame, COLUMNS, **common)
