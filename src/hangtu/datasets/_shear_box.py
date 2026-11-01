"""``p.shear_box()``: one row per shear box stage (datasets.md §6.12; M17 a).

Spec: docs/work/m17a-strength-data.md, Decisions 11-13. Shear box and ring
shear, soil and rock joint tests alike; nothing labels which a test is, or
whether its stresses are effective.
"""

from os import PathLike

import pandas as pd

from hangtu import units
from hangtu.datasets._frame import Build
from hangtu.datasets._lab import SPECIMEN_COLUMNS, specimens
from hangtu.units import STANDARD_GRAVITY

G = STANDARD_GRAVITY

SHEAR_BOX_COLUMNS = [
    *SPECIMEN_COLUMNS,
    "test_type",
    "test_stage",
    "sample_condition",
    "encapsulation",
    "failure_criterion",
    "applied_normal_stress",
    "normal_stress_at_peak",
    "normal_stress_at_residual",
    "peak_shear_stress",
    "residual_shear_stress",
    "horizontal_displacement_at_peak",
    "horizontal_displacement_at_residual",
    "vertical_displacement_at_peak",
    "vertical_displacement_at_residual",
    "peak_displacement_rate",
    "residual_displacement_rate",
    "shear_traverses",
    "specimen_height",
    "specimen_diameter_along_shear",
    "specimen_diameter_across_shear",
    "water_content",
    "final_water_content",
    "bulk_unit_weight",
    "dry_unit_weight",
    "particle_density",
    "particle_density_assumed",
    "void_ratio",
    "reported_peak_cohesion",
    "reported_peak_friction_angle",
    "reported_residual_cohesion",
    "reported_residual_friction_angle",
    "test_remarks",
    "remarks",
]
#: SHBT numbers read as they are (in SI), by column.
STAGE_NUMBERS = {
    "applied_normal_stress": "SHBT_NORM",
    "normal_stress_at_peak": "SHBT_PVST",
    "normal_stress_at_residual": "SHBT_RVST",
    "peak_shear_stress": "SHBT_PEAK",
    "residual_shear_stress": "SHBT_RES",
    "horizontal_displacement_at_peak": "SHBT_PDIS",
    "horizontal_displacement_at_residual": "SHBT_RDIS",
    "vertical_displacement_at_peak": "SHBT_PDIN",
    "vertical_displacement_at_residual": "SHBT_RDIN",
    "shear_traverses": "SHBT_REVS",
    "specimen_height": "SHBT_HGT",
    "specimen_diameter_along_shear": "SHBT_DIA1",
    "specimen_diameter_across_shear": "SHBT_DIA2",
    "water_content": "SHBT_MCI",
    "final_water_content": "SHBT_MCF",
    "particle_density": "SHBT_PDEN",
    "void_ratio": "SHBT_IVR",
}
#: The displacement rates, converted from the unit ingest stored them in to
#: displacement_rate's mm/min (Decision 13), whatever kind ingest gave them.
RATES = {
    "peak_displacement_rate": "SHBT_DISP",
    "residual_displacement_rate": "SHBT_DISR",
}
#: SHBG values repeated on each of the test's stages, by column.
TEST_TEXTS = {
    "test_type": "SHBG_TYPE",
    "sample_condition": "SHBG_COND",
    "encapsulation": "SHBG_ENCA",
    "test_remarks": "SHBG_REM",
}
TEST_NUMBERS = {
    "reported_peak_cohesion": "SHBG_PCOH",
    "reported_peak_friction_angle": "SHBG_PHI",
    "reported_residual_cohesion": "SHBG_RCOH",
    "reported_residual_friction_angle": "SHBG_RPHI",
}
TEXT_COLUMNS = [*TEST_TEXTS, "test_stage", "failure_criterion", "remarks"]


def shear_box(
    path: str | PathLike[str],
    *,
    display_units: str | None = None,
    include_incomplete: bool = False,
    **common,
) -> pd.DataFrame:
    """Build the shear box dataset; see ``Project.shear_box``."""
    build = Build(
        path,
        noun=("shear box stage", "shear box stages"),
        display_units=display_units,
        include_incomplete=include_incomplete,
    )
    if not build.has("SHBT"):
        return build.finish(pd.DataFrame(), SHEAR_BOX_COLUMNS, group="SHBT", **common)
    rows = build.rows("SHBT")
    frame = specimens(build, "SHBT", rows)
    frame["_line"] = rows["_line"]
    frame["test_stage"] = build.texts(rows, "SHBT_TESN")
    frame["failure_criterion"] = build.texts(rows, "SHBT_CRIT")
    frame["remarks"] = build.texts(rows, "SHBT_REM")
    for column, heading in STAGE_NUMBERS.items():
        frame[column] = build.numbers(rows, heading)
    stored = build.data.table("SHBT").attrs.get("units", {})
    to_rate = units.ureg.Unit(units.quantity_kind("displacement_rate")["canonical"])
    for column, heading in RATES.items():
        values = build.numbers(rows, heading)
        if heading in stored:
            unit = units.parse_unit(stored[heading], heading)
            values = units.convert(
                values.to_numpy(float), unit, "displacement_rate", to_rate
            )
        frame[column] = values
    frame["bulk_unit_weight"] = build.numbers(rows, "SHBT_BDEN") * G
    frame["dry_unit_weight"] = build.numbers(rows, "SHBT_DDEN") * G
    frame["particle_density_assumed"] = build.flagged(
        "SHBT", rows, "SHBT_PDEN", "ASSUMED"
    )
    # A stage with no test row (a broken parent link) keeps blank test columns.
    specimen = rows["specimen_id"]
    tests = (
        build.data.table("SHBG").dropna(subset=["specimen_id"])
        if build.has("SHBG")
        else pd.DataFrame(columns=["specimen_id"])
    )
    tests = tests.drop_duplicates("specimen_id").set_index("specimen_id")
    for column, heading in TEST_TEXTS.items():
        frame[column] = specimen.map(build.texts(tests, heading))
    for column, heading in TEST_NUMBERS.items():
        frame[column] = specimen.map(build.numbers(tests, heading)).astype(float)
    for column in TEXT_COLUMNS:
        frame[column] = frame[column].astype(object).where(frame[column].notna(), None)
    return build.finish(frame, SHEAR_BOX_COLUMNS, **common)
