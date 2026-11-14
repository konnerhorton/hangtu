"""``p.oedometer()``: one row per oedometer increment (datasets.md §6.14; M19 a).

Spec: docs/data/datasets.md §6.14. Every ``CONG_TYPE`` is read, the swelling
tests too; a ``CONG`` row with no ``CONS`` rows is one row with blank
increment columns, so a swelling pressure on its own isn't dropped.
"""

from os import PathLike

import pandas as pd

from hangtu.analysis._oedometer import oedometer_load_branch
from hangtu.datasets._frame import Build
from hangtu.datasets._lab import SPECIMEN_COLUMNS, specimens
from hangtu.units import STANDARD_GRAVITY

G = STANDARD_GRAVITY

OEDOMETER_COLUMNS = [
    *SPECIMEN_COLUMNS,
    "test_type",
    "sample_condition",
    "test_stage",
    "load_branch",
    "applied_vertical_stress",
    "void_ratio_at_increment_start",
    "void_ratio_at_increment_end",
    "reported_coefficient_of_volume_compressibility",
    "reported_coefficient_of_consolidation_root_time",
    "reported_coefficient_of_consolidation_log_time",
    "specimen_height",
    "specimen_diameter",
    "water_content",
    "final_water_content",
    "bulk_unit_weight",
    "dry_unit_weight",
    "particle_density",
    "particle_density_assumed",
    "degree_of_saturation",
    "void_ratio",
    "swelling_pressure",
    "height_change_on_saturation",
    "equipment_deformation_corrected",
    "test_remarks",
    "remarks",
]
#: CONS numbers, by column (in SI, as stored).
INCREMENT_NUMBERS = {
    "applied_vertical_stress": "CONS_INCF",
    "void_ratio_at_increment_start": "CONS_IVR",
    "void_ratio_at_increment_end": "CONS_INCE",
    "reported_coefficient_of_volume_compressibility": "CONS_INMV",
    "reported_coefficient_of_consolidation_root_time": "CONS_CVRT",
    "reported_coefficient_of_consolidation_log_time": "CONS_CVLG",
}
#: CONG values repeated on each of the specimen's increments, by column.
SPECIMEN_TEXTS = {
    "test_type": "CONG_TYPE",
    "sample_condition": "CONG_COND",
    "test_remarks": "CONG_REM",
}
SPECIMEN_NUMBERS = {
    "specimen_height": "CONG_HIGT",
    "specimen_diameter": "CONG_SDIA",
    "water_content": "CONG_MCI",
    "final_water_content": "CONG_MCF",
    "particle_density": "CONG_PDEN",
    "degree_of_saturation": "CONG_SATR",
    "void_ratio": "CONG_IVR",
    "swelling_pressure": "CONG_SPRS",
    "height_change_on_saturation": "CONG_SATH",
}
#: Densities that become unit weights (× g), by column.
SPECIMEN_DENSITIES = {
    "bulk_unit_weight": "CONG_BDEN",
    "dry_unit_weight": "CONG_DDEN",
}
TEXT_COLUMNS = [*SPECIMEN_TEXTS, "test_stage", "remarks"]


def oedometer(
    path: str | PathLike[str],
    *,
    display_units: str | None = None,
    include_incomplete: bool = False,
    **common,
) -> pd.DataFrame:
    """Build the oedometer dataset; see ``Project.oedometer``."""
    build = Build(
        path,
        noun=("oedometer test", "oedometer tests"),
        display_units=display_units,
        include_incomplete=include_incomplete,
    )
    if not build.has("CONG") and not build.has("CONS"):
        return build.finish(pd.DataFrame(), OEDOMETER_COLUMNS, group="CONG", **common)
    tests = _specimen_values(build)
    increments = build.rows("CONS") if build.has("CONS") else None
    parts = []
    if increments is not None:
        frame = specimens(build, "CONS", increments)
        frame["test_stage"] = build.texts(increments, "CONS_INCN")
        frame["remarks"] = build.texts(increments, "CONS_REM")
        for column, heading in INCREMENT_NUMBERS.items():
            frame[column] = build.numbers(increments, heading)
        # An increment with no CONG row (a broken parent link) keeps blank
        # specimen columns.
        key = increments["specimen_id"]
        for column in tests.columns:
            frame[column] = key.map(tests[column])
        parts.append(frame)
    if build.has("CONG"):
        # Every CONS row in the file counts, so a specimen whose increments
        # were all left out as incomplete (§7) isn't shown as one with none.
        stored = (
            build.data.table("CONS")["specimen_id"]
            if build.has("CONS")
            else pd.Series(dtype=float)
        )
        cong = build.rows("CONG")
        alone = cong[~cong["specimen_id"].isin(set(stored.dropna()))]
        if not alone.empty:
            frame = specimens(build, "CONG", alone)
            for column in tests.columns:
                frame[column] = alone["specimen_id"].map(tests[column])
            parts.append(frame)
    frame = pd.concat(parts).sort_values("_line", kind="stable")
    frame = frame.reset_index(drop=True)
    for column in INCREMENT_NUMBERS:
        if column not in frame:
            frame[column] = float("nan")
    for column in TEXT_COLUMNS:
        values = frame.get(column, pd.Series(None, index=frame.index))
        frame[column] = values.astype(object).where(values.notna(), None)
    for column in ("particle_density_assumed", "equipment_deformation_corrected"):
        frame[column] = frame[column].astype("boolean")
    frame = oedometer_load_branch(frame)
    return build.finish(frame, OEDOMETER_COLUMNS, **common)


def _specimen_values(build: Build) -> pd.DataFrame:
    """Each CONG specimen's columns, by ``specimen_id``, in SI."""
    columns = [
        *SPECIMEN_TEXTS,
        *SPECIMEN_NUMBERS,
        *SPECIMEN_DENSITIES,
        "particle_density_assumed",
        "equipment_deformation_corrected",
    ]
    if not build.has("CONG"):
        return pd.DataFrame(columns=columns)
    cong = build.data.table("CONG").dropna(subset=["specimen_id"])
    values = pd.DataFrame(index=cong.index)
    for column, heading in SPECIMEN_TEXTS.items():
        values[column] = build.texts(cong, heading)
    for column, heading in SPECIMEN_NUMBERS.items():
        values[column] = build.numbers(cong, heading)
    for column, heading in SPECIMEN_DENSITIES.items():
        values[column] = build.numbers(cong, heading) * G
    values["particle_density_assumed"] = build.flagged(
        "CONG", cong, "CONG_PDEN", "ASSUMED"
    )
    values["equipment_deformation_corrected"] = _yes_no(cong, "CONG_CORR")
    values.index = cong["specimen_id"]
    return values[~values.index.duplicated()]


def _yes_no(table: pd.DataFrame, heading: str) -> pd.Series:
    """Return a ``YN`` heading as True, False or blank."""
    if heading not in table:
        return pd.Series(pd.NA, index=table.index, dtype="boolean")
    return table[heading].map({1: True, 0: False}).astype("boolean")
