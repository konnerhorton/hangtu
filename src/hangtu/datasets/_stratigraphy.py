"""``p.stratigraphy()``: each hole's log, one row per GEOL layer (datasets.md §6.7)."""

from os import PathLike

import pandas as pd

from hangtu.datasets._frame import Build

COLUMNS = ["loca_id", "depth_top", "depth_base"]


def stratigraphy(
    path: str | PathLike[str],
    *,
    display_units: str | None = None,
    include_incomplete: bool = False,
    geology_fields=None,
    **common,
) -> pd.DataFrame:
    """Build the stratigraphy dataset; see ``Project.stratigraphy``."""
    build = Build(
        path,
        noun=("layer", "layers"),
        display_units=display_units,
        include_incomplete=include_incomplete,
    )
    if not build.has("GEOL"):
        return build.finish(
            pd.DataFrame(),
            COLUMNS,
            group="GEOL",
            geology_fields=geology_fields,
            **common,
        )
    rows = build.rows("GEOL")
    frame = pd.DataFrame(
        {
            "location_id": rows["location_id"],
            "loca_id": build.texts(rows, "LOCA_ID"),
            "depth_top": build.numbers(rows, "GEOL_TOP"),
            "depth_base": build.numbers(rows, "GEOL_BASE"),
            "_line": rows["_line"],
        }
    )
    # Layers are as written: overlaps and gaps are kept for QC to report.
    frame = frame.sort_values(["location_id", "depth_top"], kind="stable")
    return build.finish(
        frame, COLUMNS, layers=rows, geology_fields=geology_fields, **common
    )
