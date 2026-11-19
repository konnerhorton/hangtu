"""``p.triaxial_readings()`` and ``p.shear_box_readings()`` (M16).

The readings of the user-defined groups the readings map names (datasets.md
§6.15 to §6.17).

One row per reading, never merged: each keeps only the values its group gives,
with its stage's values from ``TRET``, ``TRIT`` or ``SHBT`` on each. Readings
stay in file order, so an unload at the end of a stage stays at the end
(docs/analysis/strength.md §2).
"""

from dataclasses import dataclass, field
from os import PathLike

import pandas as pd

import hangtu.db as database
from hangtu import units
from hangtu.datasets._frame import GEOLOGY_COLUMNS, Build
from hangtu.datasets._lab import specimens
from hangtu.datasets._readings_map import DATASETS, _parents
from hangtu.errors import warn
from hangtu.registry import _template_columns, column_info


@dataclass(frozen=True)
class Stages:
    """How one stage group gives a readings dataset its stage values."""

    test: str  # the test group, by specimen
    texts: dict[str, str] = field(default_factory=dict)  # from the test group
    numbers: dict[str, str] = field(default_factory=dict)  # from the stage group


STAGES = {
    "TRET": Stages(
        "TREG",
        {"test_type": "TREG_TYPE", "failure_criterion": "TREG_FCR"},
        {
            "effective_consolidation_stress": "TRET_CONP",
            "back_pressure": "TRET_BACK",
            "cell_pressure": "TRET_CELL",
        },
    ),
    "TRIT": Stages("TRIG", {"test_type": "TRIG_TYPE"}, {"cell_pressure": "TRIT_CELL"}),
    "SHBT": Stages(
        "SHBG", {"test_type": "SHBG_TYPE"}, {"applied_normal_stress": "SHBT_NORM"}
    ),
}
#: Each dataset's stage groups, in the order its stages come (its stage
#: dataset's order), and its name in messages.
ORDER = {
    "triaxial_readings": (("TRET", "TRIT"), "triaxial readings"),
    "shear_box_readings": (("SHBT",), "shear box readings"),
}


def triaxial_readings(path: str | PathLike[str], **arguments) -> pd.DataFrame:
    """Build the triaxial readings dataset; see ``Project.triaxial_readings``."""
    return _readings(path, "triaxial_readings", **arguments)


def shear_box_readings(path: str | PathLike[str], **arguments) -> pd.DataFrame:
    """Build the shear box readings dataset; see ``Project.shear_box_readings``."""
    return _readings(path, "shear_box_readings", **arguments)


def _readings(
    path: str | PathLike[str],
    dataset: str,
    *,
    display_units: str | None = None,
    include_incomplete: bool = False,
    **common,
) -> pd.DataFrame:
    stage_groups, noun = ORDER[dataset]
    build = Build(
        path,
        noun=(noun[:-1], noun),
        display_units=display_units,
        include_incomplete=include_incomplete,
    )
    template = _template_columns(dataset)
    columns = [c for c in template if c not in GEOLOGY_COLUMNS]
    mapping = database.read_readings_map(path)
    if mapping.empty:
        warn(
            f"No readings map for this project, so there are no {noun}. Set one "
            "with p.set_readings_map(path)."
        )
        return build._empty([*template, "source_line"])
    mapping = mapping[mapping["dataset"] == dataset]
    if mapping.empty:
        warn(f"The readings map names no {dataset} group.")
        return build._empty([*template, "source_line"])

    stages = pd.concat(
        [_stage_rows(build, group) for group in stage_groups if build.has(group)]
        or [pd.DataFrame(columns=["_stage", "_specimen", "_position"])],
        ignore_index=True,
    )
    stages["_position"] = range(len(stages))
    parents = _parents(path)
    left_out: dict[str, list[str]] = {"stage": [], "flagged": [], "incomplete": []}
    parts = []
    for position, (group, rows) in enumerate(mapping.groupby("group", sort=False)):
        parent = parents[group]
        assert parent is not None  # set_readings_map() checked it
        stage_group = DATASETS[dataset].stages[parent]
        part = _group_readings(
            build, group, dict(zip(rows["column"], rows["heading"], strict=True))
        )
        part["_group"] = position
        part, gone = _join(part, stages[stages["_stage"] == stage_group])
        _count(left_out, "stage", gone, f"with no stage in {stage_group}")
        parts.append(part)
    frame = pd.concat(parts, ignore_index=True)

    flagged = frame.pop("_flagged")
    _count(left_out, "flagged", frame[flagged], "")
    frame = frame[~flagged]
    incomplete = _incomplete(frame, DATASETS[dataset])
    if not include_incomplete:
        _count(left_out, "incomplete", frame[incomplete], "")
        frame = frame[~incomplete]
    _warn(left_out, noun)

    frame = frame.sort_values(
        ["_position", "_group", "_line"], na_position="last", kind="stable"
    )
    if "reported_failure_reading" in columns:
        frame["reported_failure_reading"] = pd.Series(
            pd.NA, index=frame.index, dtype="boolean"
        )
    for column in ("test_type", "test_stage", "failure_criterion"):
        if column in frame:
            values = frame[column].astype(object)
            frame[column] = values.where(values.notna(), None)
    return build.finish(frame.reset_index(drop=True), columns, **common)


def _stage_rows(build: Build, group: str) -> pd.DataFrame:
    """Return every row of a stage group, with its stage values in SI.

    Incomplete rows too: a stage left out of the stage dataset still gives its
    readings their values.
    """
    rows = build.data.table(group)
    spec = STAGES[group]
    frame = pd.DataFrame(
        {
            "_stage": group,
            "_specimen": rows["specimen_id"],
            "test_stage": build.texts(rows, f"{group}_TESN"),
        },
        index=rows.index,
    )
    for column, heading in spec.numbers.items():
        frame[column] = build.numbers(rows, heading)
    tests = (
        build.data.table(spec.test).dropna(subset=["specimen_id"])
        if build.has(spec.test)
        else pd.DataFrame(columns=["specimen_id"])
    )
    tests = tests.drop_duplicates("specimen_id").set_index("specimen_id")
    for column, heading in spec.texts.items():
        frame[column] = rows["specimen_id"].map(build.texts(tests, heading))
    return frame.dropna(subset=["_specimen"])


def _group_readings(build: Build, group: str, headings: dict[str, str]):
    """Return a curve group's rows: the specimen, the mapped values in SI."""
    rows = build.data.table(group)
    frame = specimens(build, group, rows)
    frame["_specimen"] = rows["specimen_id"]
    frame["test_stage"] = build.texts(rows, headings["test_stage"])
    known = build.data.headings
    stored = dict(
        zip(
            known.loc[known["group"] == group, "heading"],
            known.loc[known["group"] == group, "unit"],
            strict=True,
        )
    )
    for column, heading in headings.items():
        if column == "test_stage":
            continue
        values = build.numbers(rows, heading)
        info = column_info(column)
        assert info is not None  # the map holds registered columns only
        kind = info["quantity"]
        canonical = units.quantity_kind(kind)["canonical"]
        if canonical is not None and isinstance(stored.get(heading), str):
            # Ingest's canonical unit for the heading's dimension (m for a
            # user-defined mm heading) to the column's (mm): datasets.md §6.15.
            values = pd.Series(
                units.convert(
                    values.to_numpy(float),
                    units.parse_unit(stored[heading], heading),
                    kind,
                    units.ureg.Unit(canonical),
                ),
                index=rows.index,
            )
        frame[column] = values
    flags = build._flags
    flagged_rows = flags.loc[
        (flags["group"] == group) & flags["heading"].isin(list(headings.values())),
        "_row",
    ]
    frame["_flagged"] = rows["_row"].isin(set(flagged_rows))
    frame["_group_name"] = group
    return frame


def _join(part: pd.DataFrame, stages: pd.DataFrame):
    """Give each reading its stage's values; return them and those with no stage.

    A reading with a blank ``test_stage`` stays, to be counted as incomplete.
    """
    values = stages.drop(columns=["_stage", "test_stage"]).assign(
        _key=list(zip(stages["_specimen"], stages["test_stage"], strict=True))
    )
    values = values.drop_duplicates("_key").drop(columns="_specimen")
    part = part.assign(
        _key=list(zip(part["_specimen"], part["test_stage"], strict=True))
    )
    joined = part.merge(values, on="_key", how="left").set_axis(part.index)
    found = joined["_position"].notna()
    keep = found | joined["test_stage"].isna()
    return joined[keep].drop(columns=["_key", "_specimen"]), joined[~keep]


def _incomplete(frame: pd.DataFrame, readings) -> pd.Series:
    blank = frame["test_stage"].isna() | frame[readings.required[1]].isna()
    others = [c for c in readings.one_of if c in frame]
    return blank | frame[others].isna().all(axis=1)


def _count(left_out, kind, rows: pd.DataFrame, why: str) -> None:
    for name, these in rows.groupby("_group_name", sort=False):
        lines = [int(line) for line in these["_line"]]
        left_out[kind].append((name, lines, why))


def _warn(left_out, noun: str) -> None:
    texts = {
        "stage": (
            "{n} {readings} of {group} {why} ({lines})",
            ": their specimen and stage must match a row of that group. "
            "Without its stage a reading has nothing to be read against, so "
            "include_incomplete=True doesn't keep it.",
        ),
        "flagged": (
            "{n} {readings} of {group} with a flagged value ({lines})",
            ": a bound (<x, >x) or text can't sit on a curve, so "
            "include_incomplete=True doesn't keep them. p.diff() shows the text.",
        ),
        "incomplete": (
            "{n} {readings} of {group} with a blank stage or strain, or no other "
            "value ({lines})",
            ". Keep them with include_incomplete=True.",
        ),
    }
    for kind, found in left_out.items():
        if not found:
            continue
        part, end = texts[kind]
        parts = [
            part.format(
                n=len(lines),
                readings="reading" if len(lines) == 1 else "readings",
                group=group,
                why=why,
                lines=_lines(lines),
            )
            for group, lines, why in found
        ]
        warn(f"Left out {'; '.join(parts)} from the {noun}{end}")


def _lines(lines: list[int], most: int = 5) -> str:
    """Write ``lines 2041-2052, 2060`` (an en dash) from the first runs of lines."""
    runs: list[list[int]] = []
    for line in sorted(lines):
        if runs and line == runs[-1][-1] + 1:
            runs[-1].append(line)
        else:
            runs.append([line])
    dash = "\u2013"
    shown = [
        str(run[0]) if len(run) == 1 else f"{run[0]}{dash}{run[-1]}"
        for run in runs[:most]
    ]
    more = ", …" if len(runs) > most else ""
    word = "line" if len(lines) == 1 else "lines"
    return f"{word} {', '.join(shown)}{more}"
