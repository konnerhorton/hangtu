"""``p.triaxial()``: one row per triaxial stage at failure (datasets.md §6.10)."""

import warnings
from os import PathLike

import numpy as np
import pandas as pd

from hangtu import units
from hangtu.analysis._triaxial import (
    EXTENSION,
    MULTISTAGE,
    STRESS_COLUMNS,
    triaxial_failure_stresses,
)
from hangtu.datasets._frame import Build
from hangtu.datasets._lab import SPECIMEN_COLUMNS, specimen_names, specimens
from hangtu.errors import warn
from hangtu.units import STANDARD_GRAVITY

G = STANDARD_GRAVITY

TRIAXIAL_COLUMNS = [
    *SPECIMEN_COLUMNS,
    "test_type",
    "test_stage",
    "multistage_test",
    "sample_condition",
    "failure_criterion",
    "water_content",
    "bulk_unit_weight",
    "dry_unit_weight",
    "void_ratio",
    "effective_consolidation_stress",
    "back_pressure",
    "pore_pressure_parameter_b",
    "cell_pressure",
    "deviator_stress_at_failure",
    "pore_pressure_at_failure",
    "axial_strain_at_failure",
    "volumetric_strain_at_failure",
    *STRESS_COLUMNS,
    "effective_stress_basis",
    "reported_effective_friction_angle",
    "reported_effective_cohesion",
    "test_remarks",
    "remarks",
]
#: Text columns that one of the two groups, or a stage with no test row, leaves
#: blank: None, as ``texts()`` gives.
TEXT_COLUMNS = [
    "test_type",
    "test_stage",
    "sample_condition",
    "failure_criterion",
    "test_remarks",
    "remarks",
]
#: Each stage group: its test group, and the headings read from each, by column.
GROUPS = {
    "TRET": (
        "TREG",
        {
            "test_type": "TREG_TYPE",
            "sample_condition": "TREG_COND",
            "failure_criterion": "TREG_FCR",
            "test_remarks": "TREG_REM",
        },
        {
            "reported_effective_friction_angle": "TREG_PHI",
            "reported_effective_cohesion": "TREG_COH",
        },
    ),
    "TRIT": (
        "TRIG",
        {
            "test_type": "TRIG_TYPE",
            "sample_condition": "TRIG_COND",
            "test_remarks": "TRIG_REM",
        },
        {},
    ),
}
#: Numeric headings of each stage group, by column (the unit weights apart).
STAGE_NUMBERS = {
    "water_content": "_IMC",
    "void_ratio": "_IVR",
    "effective_consolidation_stress": "_CONP",
    "back_pressure": "_BACK",
    "pore_pressure_parameter_b": "_BVAL",
    "cell_pressure": "_CELL",
    "deviator_stress_at_failure": "_DEVF",
    "pore_pressure_at_failure": "_PWPF",
    "axial_strain_at_failure": "_STRN",
    "volumetric_strain_at_failure": "_STV",
}
#: The stresses ``triaxial_failure_stresses()`` reads, in kPa here (SI).
INPUT_STRESSES = [
    "cell_pressure",
    "deviator_stress_at_failure",
    "pore_pressure_at_failure",
    "back_pressure",
]


def triaxial(
    path: str | PathLike[str],
    *,
    display_units: str | None = None,
    include_incomplete: bool = False,
    **common,
) -> pd.DataFrame:
    """Build the triaxial dataset; see ``Project.triaxial``."""
    build = Build(
        path,
        noun=("triaxial stage", "triaxial stages"),
        display_units=display_units,
        include_incomplete=include_incomplete,
    )
    parts = [_stages(build, stage) for stage in GROUPS if build.has(stage)]
    if not parts:
        return build.finish(
            pd.DataFrame(), TRIAXIAL_COLUMNS, group="TRET or TRIT", **common
        )
    frame = pd.concat(parts, ignore_index=True)
    for column in TEXT_COLUMNS:
        values = frame.get(column, pd.Series(None, index=frame.index))
        frame[column] = values.astype(object).where(values.notna(), None)
    frame["multistage_test"] = frame["multistage_test"].astype("boolean")
    frame = _failure_stresses(frame)
    marks = ["_extension", "_not_positive"]
    result = build.finish(frame, [*TRIAXIAL_COLUMNS, *marks], **common)
    _warn(result, *(result.pop(mark).to_numpy(dtype=bool) for mark in marks))
    return result


def _stages(build: Build, stage: str) -> pd.DataFrame:
    """Return the rows of one stage group, with its test's columns, in SI."""
    rows = build.rows(stage)
    frame = specimens(build, stage, rows)
    test, texts, numbers = GROUPS[stage]
    frame["test_stage"] = build.texts(rows, f"{stage}_TESN")
    for column, suffix in STAGE_NUMBERS.items():
        frame[column] = build.numbers(rows, f"{stage}{suffix}")
    frame["bulk_unit_weight"] = build.numbers(rows, f"{stage}_BDEN") * G
    frame["dry_unit_weight"] = build.numbers(rows, f"{stage}_DDEN") * G
    frame["remarks"] = build.texts(rows, f"{stage}_REM")
    specimen = rows["specimen_id"]
    # A stage with no test row (a broken parent link) keeps blank test columns.
    tests = (
        build.data.table(test).dropna(subset=["specimen_id"])
        if build.has(test)
        else pd.DataFrame(columns=["specimen_id"])
    )
    tests = tests.drop_duplicates("specimen_id").set_index("specimen_id")
    for column, heading in texts.items():
        frame[column] = specimen.map(build.texts(tests, heading))
    for column, heading in numbers.items():
        frame[column] = specimen.map(build.numbers(tests, heading)).astype(float)
    # Every stage in the file counts, so a stage left out as incomplete (§7)
    # doesn't make its test look single-stage.
    count = specimen.map(build.data.table(stage)["specimen_id"].value_counts())
    frame["multistage_test"] = frame["test_type"].isin(MULTISTAGE) | (count > 1)
    return frame


def _failure_stresses(frame: pd.DataFrame) -> pd.DataFrame:
    """Add the principal stresses with ``triaxial_failure_stresses()`` (§6.10).

    The rows a dataset doesn't stop on (extension, and a deviator stress of 0
    or less in compression, which the analysis raises on) are left out of the
    call, with blank stresses, and marked for the warnings.
    """
    extension = frame["test_type"].isin(EXTENSION)
    not_positive = ~extension & (frame["deviator_stress_at_failure"] <= 0)
    frame["_extension"] = extension
    frame["_not_positive"] = not_positive
    for column in STRESS_COLUMNS:
        frame[column] = np.nan
    frame["effective_stress_basis"] = None
    computed = ~extension & ~not_positive
    if not computed.any():
        return frame
    stages = units.set_units(
        frame.loc[computed, ["test_type", *INPUT_STRESSES]],
        dict.fromkeys(INPUT_STRESSES, "kPa"),
    )
    with warnings.catch_warnings():
        # The back pressure count is given on the rows returned (_warn).
        warnings.simplefilter("ignore", UserWarning)
        stresses = triaxial_failure_stresses(stages)
    for column in [*STRESS_COLUMNS, "effective_stress_basis"]:
        frame.loc[computed, column] = stresses[column].to_numpy()
    return frame


def _warn(result: pd.DataFrame, extension: np.ndarray, not_positive: np.ndarray):
    """Give the §6.10 warnings, counted on the rows returned."""
    names = (
        result["loca_id"].astype(str)
        + " "
        + specimen_names(result)
        + " stage "
        + result["test_stage"].fillna("").astype(str)
    )
    used = int((result["effective_stress_basis"] == "back_pressure").sum())
    if used:
        warn(
            f"{used} drained triaxial stage{'s' if used > 1 else ''} had TRET_PWPF "
            "blank, so the back pressure was used as the pore pressure at failure: "
            "a drained test holds the pore pressure at the back pressure. "
            "effective_stress_basis says which was used."
        )
    if extension.any():
        types = ", ".join(dict.fromkeys(result.loc[extension, "test_type"]))
        warn(
            f"Extension stages {', '.join(names[extension])} ({types}) have blank "
            "principal stresses: the deviator stress has no agreed sign in "
            "extension, where the axial stress is the minor one."
        )
    if not_positive.any():
        warn(
            f"Stages {', '.join(names[not_positive])} have a deviator stress at "
            "failure of 0 or less, so their principal stresses are blank. p.qc() "
            "lists them (X003)."
        )
