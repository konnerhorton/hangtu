"""``p.spt()``: one row per SPT, ready for P02 and P03 (datasets.md §6.1)."""

from os import PathLike

import numpy as np
import pandas as pd

from hangtu import analysis
from hangtu._settings import settings
from hangtu.datasets import _joins
from hangtu.datasets._frame import Build

COLUMNS = [
    "loca_id",
    "ground_level",
    "depth",
    "depth_basis",
    "elevation",
    "spt_n",
    "spt_n_capped",
    "spt_n60",
    "energy_ratio",
    "energy_source",
    "spt_refusal",
    "spt_penetration",
    "remarks",
]


def spt(
    path: str | PathLike[str],
    *,
    hammer_efficiency: float | None = None,
    cap: int | None = None,
    display_units: str | None = None,
    include_incomplete: bool = False,
    **common,
) -> pd.DataFrame:
    """Build the SPT dataset; see ``Project.spt``."""
    build = Build(
        path,
        noun=("SPT result", "SPT results"),
        display_units=display_units,
        include_incomplete=include_incomplete,
    )
    if not build.has("ISPT"):
        return build.finish(pd.DataFrame(), COLUMNS, group="ISPT", **common)
    rows = build.rows("ISPT")
    top = build.numbers(rows, "ISPT_TOP")
    total = build.numbers(rows, "ISPT_NPEN")
    penetrations = pd.DataFrame(
        {f"ISPT_PEN{i}": build.numbers(rows, f"ISPT_PEN{i}") for i in range(1, 7)}
    )
    depth, basis = _joins.spt_depth(top, total, penetrations)
    file_n60 = build.numbers(rows, "ISPT_N60")
    refusal = build.flagged("ISPT", rows, "ISPT_NVAL", "REFUSAL")
    frame = pd.DataFrame(
        {
            "location_id": rows["location_id"],
            "loca_id": build.texts(rows, "LOCA_ID"),
            "depth": depth,
            "depth_basis": basis,
            "spt_n": build.numbers(rows, "ISPT_NVAL"),
            "spt_n60": file_n60,
            "energy_ratio": build.numbers(rows, "ISPT_ERAT"),
            # A flagged refusal is True; the rest is left to ht.analysis.spt(),
            # which reads spt_penetration (analysis.md §1.3).
            "spt_refusal": pd.Series(refusal.where(refusal, None), dtype=object),
            "spt_penetration": total,
            "remarks": build.texts(rows, "ISPT_REM"),
            "_line": rows["_line"],
        }
    )
    frame = analysis.spt(
        frame,
        hammer_efficiency=hammer_efficiency,
        cap=cap,
        units={"spt_penetration": "mm"},
    )
    efficiency = settings.hammer_efficiency if hammer_efficiency is None else 1
    frame["energy_source"] = pd.Series(
        np.select(
            [
                file_n60.notna(),
                frame["spt_n60"].notna() & frame["energy_ratio"].notna(),
                frame["spt_n60"].notna() & (efficiency is not None),
            ],
            ["file_n60", "file_energy_ratio", "hammer_efficiency"],
            default=None,
        ),
        index=frame.index,
        dtype=object,
    )
    return build.finish(frame, COLUMNS, group="ISPT", **common)
