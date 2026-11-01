"""``p.undrained_strength()``: one row per undrained strength result (§6.11).

Spec: docs/work/m17a-strength-data.md, Decisions 1-10.
"""

from os import PathLike

import numpy as np
import pandas as pd

from hangtu.analysis._undrained import SCALES, undrained_shear_strength_from_tests
from hangtu.datasets._frame import Build
from hangtu.datasets._lab import SPECIMEN_COLUMNS, specimens
from hangtu.datasets._triaxial import _stages
from hangtu.errors import HangtuError, warn
from hangtu.units import STANDARD_GRAVITY

G = STANDARD_GRAVITY

UNDRAINED_COLUMNS = [
    *SPECIMEN_COLUMNS,
    "source",
    "test_type",
    "test_stage",
    "multistage_test",
    "sample_condition",
    "undrained_shear_strength",
    "qualifier",
    "undrained_shear_strength_basis",
    "remolded_undrained_shear_strength",
    "remolded_qualifier",
    "strength_sensitivity",
    "reported_undrained_shear_strength",
    "cell_pressure",
    "deviator_stress_at_failure",
    "unconfined_compressive_strength",
    "hand_penetrometer_reading",
    "axial_strain_at_failure",
    "water_content",
    "bulk_unit_weight",
    "dry_unit_weight",
    "test_remarks",
    "remarks",
]
#: Every group read, in row order (Decision 1), for the missing-group warning.
GROUPS = ("TRIT", "LUCT", "LVAN", "LPEN", "LFCN", "IVAN", "IPEN")
#: The strength inputs, the ones the analysis reads (all in kPa here, SI).
STRENGTHS = [
    "undrained_shear_strength",
    "remolded_undrained_shear_strength",
    "deviator_stress_at_failure",
    "unconfined_compressive_strength",
    "hand_penetrometer_reading",
]
#: The lab groups read by specimen: (test type, its type heading or None,
#: the heading giving s_u's input and its column, the remolded heading, and
#: numbers and texts by column). A blank type code gives the name with
#: ", type not given" (Decision 2).
LAB = {
    "LUCT": (
        "unconfined compression",
        None,
        ("LUCT_UCS", "unconfined_compressive_strength"),
        None,
        {
            "axial_strain_at_failure": "LUCT_STRA",
            "water_content": "LUCT_IWC",
        },
        {"sample_condition": "LUCT_TYPE", "remarks": "LUCT_REM"},
    ),
    "LVAN": (
        "laboratory vane",
        "LVAN_TYPE",
        ("LVAN_VNPK", "undrained_shear_strength"),
        "LVAN_VNRM",
        {"water_content": "LVAN_MC"},
        {"remarks": "LVAN_REM"},
    ),
    "LPEN": (
        "hand penetrometer",
        None,
        ("LPEN_PPEN", "undrained_shear_strength"),
        None,
        {"water_content": "LPEN_MC"},
        {"remarks": "LPEN_REM"},
    ),
    "LFCN": (
        "fall cone",
        None,
        ("LFCN_FCPK", "undrained_shear_strength"),
        "LFCN_FCRM",
        {"water_content": "LFCN_WC"},
        {"remarks": "LFCN_REM"},
    ),
}
FIELD = {
    "IVAN": (
        "in situ vane",
        "IVAN_TYPE",
        ("IVAN_IVAN", "undrained_shear_strength"),
        "IVAN_IVAR",
    ),
    "IPEN": (
        "hand penetrometer",
        None,
        ("IPEN_IPEN", "hand_penetrometer_reading"),
        None,
    ),
}


def undrained_strength(
    path: str | PathLike[str],
    *,
    hand_penetrometer_scale: str | None = None,
    display_units: str | None = None,
    include_incomplete: bool = False,
    **common,
) -> pd.DataFrame:
    """Build the undrained strength dataset; see ``Project.undrained_strength``."""
    if hand_penetrometer_scale is not None and hand_penetrometer_scale not in SCALES:
        raise HangtuError(
            f"hand_penetrometer_scale={hand_penetrometer_scale!r} isn't one of "
            f"{', '.join(map(repr, SCALES))}. Say what the instrument read: check "
            "IPEN_METH and IPEN_REM."
        )
    build = Build(
        path,
        noun=("undrained strength result", "undrained strength results"),
        display_units=display_units,
        include_incomplete=include_incomplete,
    )
    parts = []
    if build.has("TRIT"):
        parts.append(_unconsolidated_undrained(build))
    for group in LAB:
        if build.has(group):
            parts.append(_lab(build, group))
    for group in FIELD:
        if build.has(group) and (group != "IPEN" or hand_penetrometer_scale):
            parts.append(_field(build, group))
    if build.has("IPEN") and not hand_penetrometer_scale:
        left_out = len(build.rows("IPEN"))
        warn(
            f"Left out {left_out} IPEN result{'s' if left_out > 1 else ''}: IPEN_IPEN "
            "doesn't say whether the instrument read s_u or q_u. Check IPEN_METH and "
            'IPEN_REM, then pass hand_penetrometer_scale="undrained_shear_strength" '
            'or "unconfined_compressive_strength".'
        )
    if not parts:
        group = f"{', '.join(GROUPS[:-1])} or {GROUPS[-1]}"
        return build.finish(pd.DataFrame(), UNDRAINED_COLUMNS, group=group, **common)
    frame = pd.concat(parts, ignore_index=True)
    for column in UNDRAINED_COLUMNS:
        if column not in frame.columns:
            frame[column] = np.nan
    for column in ("qualifier", "remolded_qualifier"):
        frame[column] = frame[column].fillna("")
    texts = [c for c in UNDRAINED_COLUMNS if c not in STRENGTHS and _text(c)]
    for column in texts:
        frame[column] = frame[column].astype(object).where(frame[column].notna(), None)
    frame["multistage_test"] = frame["multistage_test"].astype("boolean")
    frame = _strength(frame, hand_penetrometer_scale)
    return build.finish(frame, UNDRAINED_COLUMNS, **common)


def _text(column: str) -> bool:
    return column in {
        "loca_id",
        "specimen_id",
        "sample_reference",
        "specimen_reference",
        "depth_basis",
        "source",
        "test_type",
        "test_stage",
        "sample_condition",
        "test_remarks",
        "remarks",
    }


def _unconsolidated_undrained(build: Build) -> pd.DataFrame:
    """UU stages through ``p.triaxial()``'s build, so depths and stages agree."""
    frame = _stages(build, "TRIT")
    rows = build.data.table("TRIT").loc[frame.index]
    frame["reported_undrained_shear_strength"] = build.numbers(rows, "TRIT_CU")
    frame["qualifier"] = build.qualifier("TRIT", rows, "TRIT_DEVF")
    frame["_line"] = rows["_line"]
    types = frame["test_type"]
    frame["test_type"] = types.where(
        types.notna(), "total stress triaxial, type not given"
    )
    frame["source"] = "lab"
    keep = [
        *SPECIMEN_COLUMNS,
        "location_id",
        "_line",
        "source",
        "test_type",
        "test_stage",
        "multistage_test",
        "sample_condition",
        "qualifier",
        "reported_undrained_shear_strength",
        "cell_pressure",
        "deviator_stress_at_failure",
        "axial_strain_at_failure",
        "water_content",
        "bulk_unit_weight",
        "dry_unit_weight",
        "test_remarks",
        "remarks",
    ]
    return frame[[c for c in keep if c in frame.columns]]


def _lab(build: Build, group: str) -> pd.DataFrame:
    name, type_heading, (heading, column), remolded, numbers, texts = LAB[group]
    rows = build.rows(group)
    frame = specimens(build, group, rows)
    frame["_line"] = rows["_line"]
    frame["source"] = "lab"
    frame["test_type"] = _types(build, rows, name, type_heading)
    frame[column] = build.numbers(rows, heading)
    frame["qualifier"] = build.qualifier(group, rows, heading)
    if remolded:
        frame["remolded_undrained_shear_strength"] = build.numbers(rows, remolded)
        frame["remolded_qualifier"] = build.qualifier(group, rows, remolded)
    for target, source in numbers.items():
        frame[target] = build.numbers(rows, source)
    for target, source in texts.items():
        frame[target] = build.texts(rows, source)
    if group == "LUCT":
        frame["bulk_unit_weight"] = build.numbers(rows, "LUCT_BDEN") * G
        frame["dry_unit_weight"] = build.numbers(rows, "LUCT_DDEN") * G
    return frame


def _field(build: Build, group: str) -> pd.DataFrame:
    """In situ tests, at their test depth, as ``IDEN`` in ``p.density()``."""
    name, type_heading, (heading, column), remolded = FIELD[group]
    rows = build.rows(group)
    depth = build.numbers(rows, f"{group}_DPTH")
    basis = pd.Series("test_depth", index=rows.index, dtype=object)
    frame = pd.DataFrame(
        {
            "location_id": rows["location_id"],
            "loca_id": build.texts(rows, "LOCA_ID"),
            "depth": depth,
            "depth_basis": basis.where(depth.notna(), None),
            "source": "field",
            "test_type": _types(build, rows, name, type_heading),
            "test_stage": build.texts(rows, f"{group}_TESN"),
            column: build.numbers(rows, heading),
            "qualifier": build.qualifier(group, rows, heading),
            "remarks": build.texts(rows, f"{group}_REM"),
            "_line": rows["_line"],
        }
    )
    if remolded:
        frame["remolded_undrained_shear_strength"] = build.numbers(rows, remolded)
        frame["remolded_qualifier"] = build.qualifier(group, rows, remolded)
    return frame


def _types(build: Build, rows: pd.DataFrame, name: str, heading: str | None):
    """Return the file's type code, else the group's name (Decision 2)."""
    if heading is None:
        return pd.Series(name, index=rows.index, dtype=object)
    codes = build.texts(rows, heading)
    return codes.where(codes.notna(), f"{name}, type not given")


def _strength(frame: pd.DataFrame, scale: str | None) -> pd.DataFrame:
    """s_u and sensitivity with the analysis, after blanking inputs of 0 or less.

    A dataset doesn't stop on the file's data (§6.10), so a strength of 0 or
    less is blanked with one warning; p.qc() lists it (X003, Q003).
    """
    inputs = frame[STRENGTHS[2:] + STRENGTHS[:1]].to_numpy(dtype=float)
    not_positive = (inputs <= 0).any(axis=1)
    if not_positive.any():
        count = int(not_positive.sum())
        warn(
            f"{count} undrained strength result{'s' if count > 1 else ''} had a "
            "strength or deviator stress of 0 or less, so s_u is blank there. "
            "p.qc() lists them (X003, Q003)."
        )
        for column in [*STRENGTHS[2:], STRENGTHS[0]]:
            frame.loc[not_positive, column] = np.nan
    units = dict.fromkeys(STRENGTHS, "kPa")
    return undrained_shear_strength_from_tests(
        frame, hand_penetrometer_scale=scale, units=units
    )
