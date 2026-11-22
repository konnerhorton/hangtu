"""The readings map: user-defined groups that hold readings → the readings datasets.

Read from a CSV or a DataFrame and checked against the project's file before
it's stored (datasets.md §6.15). Everything it's checked against was stored at
ingest (the file's ``DICT`` group, ``meta_heading``), so the AGS file isn't
read again. Group, heading and column names are matched exactly, as written.
"""

from contextlib import suppress
from dataclasses import dataclass
from os import PathLike
from pathlib import Path

import pandas as pd

import hangtu.db as database
from hangtu import units
from hangtu.ags import _dictionary
from hangtu.ags._read import REFERENCE_VERSION
from hangtu.errors import HangtuError, UnitsError
from hangtu.registry import column_info

COLUMNS = ("group", "dataset", "heading", "column")
_EXAMPLE = (
    "group,dataset,heading,column\n"
    "XTDS,triaxial_readings,XTDS_TESN,test_stage\n"
    "XTDS,triaxial_readings,XTDS_STRN,axial_strain\n"
    "XTDS,triaxial_readings,XTDS_DEVF,deviator_stress"
)


@dataclass(frozen=True)
class Readings:
    """What a readings dataset maps (datasets.md §6.15's second table).

    ``stages`` gives, for each parent group a curve group may have, the group
    whose rows are its stages.
    """

    mapped: tuple[str, ...]
    required: tuple[str, ...]
    one_of: tuple[str, ...]
    stages: dict[str, str]


DATASETS = {
    "triaxial_readings": Readings(
        mapped=(
            "test_stage",
            "axial_strain",
            "deviator_stress",
            "excess_pore_pressure",
            "volumetric_strain",
        ),
        required=("test_stage", "axial_strain"),
        one_of=("deviator_stress", "excess_pore_pressure", "volumetric_strain"),
        stages={"TREG": "TRET", "TRET": "TRET", "TRIG": "TRIT", "TRIT": "TRIT"},
    ),
    "shear_box_readings": Readings(
        mapped=(
            "test_stage",
            "horizontal_displacement",
            "shear_stress",
            "vertical_displacement",
        ),
        required=("test_stage", "horizontal_displacement"),
        one_of=("shear_stress", "vertical_displacement"),
        stages={"SHBG": "SHBT", "SHBT": "SHBT"},
    ),
    "oedometer_readings": Readings(
        mapped=("test_stage", "elapsed_time", "vertical_displacement"),
        required=("test_stage", "elapsed_time", "vertical_displacement"),
        one_of=(),
        stages={"CONG": "CONS", "CONS": "CONS"},
    ),
}

# meta_heading.status of a numeric heading ingest couldn't convert (ingest.md §7).
_NOT_CONVERTED = {
    "raw_only": "its unit couldn't be read or doesn't fit (finding U001, U003 or U004)",
    "file_unit": "hangtu doesn't know its unit, so it's kept as written (finding U005)",
    "not_numeric": "it isn't a number in the file",
}


def read(
    source: "str | PathLike[str] | pd.DataFrame", path: "str | PathLike[str]"
) -> pd.DataFrame:
    """Read a readings map and check it against the project database at ``path``.

    Return it with ``COLUMNS``, in map order. Raise ``HangtuError`` at the
    first problem, naming the map's line (a DataFrame's row) and what to do.
    """
    table, where, word = _table(source)
    _check_columns(table, where)
    table = table.loc[:, list(COLUMNS)]
    for column in COLUMNS:
        table[column] = table[column].map(_text)
    _check_cells(table, where, word)
    _check_names(table, where, word)
    _check_file(table, where, word, path)
    return table.reset_index(drop=True)


def _table(source) -> tuple[pd.DataFrame, str, str]:
    if isinstance(source, pd.DataFrame):
        table = source.copy()
        table.columns = [str(c) for c in table.columns]
        table.index = range(1, len(table) + 1)
        return table, "The readings map", "row"
    path = Path(source)
    if not path.is_file():
        raise HangtuError(
            f"No readings map at {str(path)!r}. Give the path to a CSV file with "
            f"the columns {', '.join(COLUMNS)}, for example:\n{_EXAMPLE}"
        )
    table = pd.read_csv(path, dtype=str, keep_default_na=False)
    table.index = range(2, len(table) + 2)  # line 1 is the header
    return table, f"The readings map {path.name}", "line"


def _text(value) -> str | None:
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    text = str(value)
    return None if text == "" else text


def _check_columns(table: pd.DataFrame, where: str) -> None:
    missing = [c for c in COLUMNS if c not in table.columns]
    unknown = [c for c in table.columns if c not in COLUMNS]
    if missing or unknown:
        problems = []
        if missing:
            problems.append(f"has no {' or '.join(missing)} column")
        if unknown:
            problems.append(f"has columns hangtu doesn't read: {', '.join(unknown)}")
        raise HangtuError(
            f"{where} {' and '.join(problems)}. Its columns are {', '.join(COLUMNS)}, "
            f"all required, one row per mapped heading, for example:\n{_EXAMPLE}"
        )
    if table.empty:
        raise HangtuError(
            f"{where} has no rows. Give one row per mapped heading, or remove the map "
            "with p.set_readings_map(None)."
        )


def _check_cells(table: pd.DataFrame, where: str, word: str) -> None:
    for column in COLUMNS:
        blank = table.index[table[column].isna()].tolist()
        if blank:
            raise HangtuError(
                f"{where} has a blank {column} on {_lines(word, blank)}. Every row "
                "names a group, its dataset, one of its headings and the column it "
                "gives."
            )
    for keys, what, fix in (
        (
            ["group", "heading"],
            "maps a heading more than once",
            "A heading gives one column, so keep one row for it.",
        ),
        (
            ["group", "column"],
            "maps a column more than once in one group",
            "Each column comes from one heading of a group, so keep one row for it.",
        ),
    ):
        repeated = table[table.duplicated(keys, keep=False)]
        if not repeated.empty:
            first = repeated.groupby(keys, sort=False).groups
            (group, name), lines = next(iter(first.items()))
            raise HangtuError(
                f"{where} {what}: {group} {name} on {_lines(word, list(lines))}. {fix}"
            )
    datasets = table.groupby("group", sort=False)["dataset"].unique()
    clashing = datasets[datasets.map(len) > 1]
    if not clashing.empty:
        group = clashing.index[0]
        raise HangtuError(
            f"{where} gives group {group} two datasets: "
            f"{', '.join(clashing.iloc[0])}. A group's readings go to one dataset, "
            "so give the same dataset on each of its rows."
        )


def _check_names(table: pd.DataFrame, where: str, word: str) -> None:
    for line, row in table.iterrows():
        if row["dataset"] not in DATASETS:
            raise HangtuError(
                f"{where} has dataset {row['dataset']!r} on {word} {line}. The "
                f"readings datasets are {', '.join(list(DATASETS)[:-1])} and "
                f"{list(DATASETS)[-1]}."
            )
        mapped = DATASETS[row["dataset"]].mapped
        if row["column"] not in mapped:
            raise HangtuError(
                f"{where} maps {row['heading']} to column {row['column']!r} on {word} "
                f"{line}, which {row['dataset']} doesn't read. Its columns are "
                f"{', '.join(mapped)}."
            )


def _check_file(table: pd.DataFrame, where: str, word: str, path) -> None:
    headings = database.read_headings(path)
    in_file = list(dict.fromkeys(headings["group"]))
    standard = _standard_groups(path)
    user_defined = [g for g in in_file if g not in standard]
    by_group = table.groupby("group", sort=False)

    for group, rows in by_group:
        line = rows.index[0]
        if group in standard:
            raise HangtuError(
                f"{where} names {group} on {word} {line}, a standard AGS group. The "
                "readings map reads user-defined groups only."
            )
        if group not in in_file:
            listed = ", ".join(sorted(user_defined)) or "none"
            raise HangtuError(
                f"{where} names group {group} on {word} {line}, which the file doesn't "
                f"have. Its user-defined groups are: {listed}. Group names are "
                "matched exactly, as the file writes them."
            )
        names = list(headings.loc[headings["group"] == group, "heading"])
        for heading_line, heading in rows["heading"].items():
            if heading not in names:
                raise HangtuError(
                    f"{where} maps heading {heading} on {word} {heading_line}, which "
                    f"group {group} doesn't have. Its headings are: {', '.join(names)}."
                )

    for group, rows in by_group:
        dataset = rows["dataset"].iloc[0]
        readings = DATASETS[dataset]
        given = set(rows["column"])
        missing = [c for c in readings.required if c not in given]
        none_of = bool(readings.one_of) and not given & set(readings.one_of)
        if missing or none_of:
            needs = [*missing] + ([" or ".join(readings.one_of)] if none_of else [])
            other = (
                f", and at least one of {', '.join(readings.one_of)}"
                if readings.one_of
                else ""
            )
            raise HangtuError(
                f"{where} doesn't map {', '.join(needs)} for group {group}. "
                f"{_article(dataset)} {dataset} group needs "
                f"{_listed(readings.required)}{other}."
            )

    parents = _parents(path)
    for group, rows in by_group:
        dataset = rows["dataset"].iloc[0]
        allowed = DATASETS[dataset].stages
        if group not in parents:
            raise HangtuError(
                f"{where} names group {group} on {word} {rows.index[0]}, which has no "
                "entry in the file's DICT group, so hangtu can't "
                f"tell which test its readings belong to. Add a DICT row for {group} "
                f"with DICT_PGRP one of {', '.join(allowed)}, and re-ingest the file."
            )
        parent = parents[group]
        if parent not in allowed:
            raise HangtuError(
                f"{where} sends group {group} to {dataset}, but the file's DICT gives "
                f"it the parent {parent or 'none'}. {_article(dataset)} {dataset} "
                "group is a child of "
                f"{', '.join(allowed)}. Check the dataset on "
                f"{_lines(word, list(rows.index))}."
            )

    known = headings.set_index(["group", "heading"])
    for line, row in table.iterrows():
        info = column_info(row["column"])
        assert info is not None  # every mapped column is registered (_check_names)
        quantity = info.get("quantity")
        if quantity is None:  # test_stage: text, read as written
            continue
        entry = known.loc[(row["group"], row["heading"])]
        _check_unit(row, entry, quantity, where, f"{word} {line}")


def _check_unit(
    row: pd.Series, entry: pd.Series, quantity: str, where: str, line: str
) -> None:
    file_unit = _text(entry["file_unit"])
    kind = quantity.replace("_", " ")
    problem = _NOT_CONVERTED.get(entry["status"])
    if problem is None:
        stored = _text(entry["unit"])
        try:
            if stored is None:  # a number with no unit, such as a count
                raise UnitsError("no unit")
            units.check_dimension(units.parse_unit(stored), quantity)
        except UnitsError:
            problem = f"its unit isn't a {kind}"
    if problem is not None:
        unit = f"unit {file_unit!r}" if file_unit else "no unit"
        raise HangtuError(
            f"{where} maps {row['group']} {row['heading']} ({unit}) to "
            f"{row['column']} on {line}, but {row['column']} is a {kind} and "
            f"{problem}. Map a heading whose unit is a {kind}, or correct the "
            "heading's unit in the file and re-ingest it."
        )


def _standard_groups(path) -> set[str]:
    groups = set(_dictionary.standard(REFERENCE_VERSION).groups)
    version = database.read_source(path)["ags_version"]
    # A version python-ags4 has no dictionary for (4.9): 4.2's groups only.
    with suppress(FileNotFoundError):
        groups |= set(_dictionary.standard(version).groups)
    return groups


def _parents(path) -> dict[str, str | None]:
    """Each group the file's ``DICT`` defines, with its parent (None if blank)."""
    if "raw_DICT" not in database.tables(path):
        return {}
    rows = database.read_table(path, "raw_DICT").fillna("")
    parents: dict[str, str | None] = {}
    for row in rows.to_dict("records"):
        if row.get("DICT_TYPE", "").strip() == "GROUP":
            parent = row.get("DICT_PGRP", "").strip()
            parents[row["DICT_GRP"].strip()] = None if parent in ("", "-") else parent
    return parents


def _article(word: str) -> str:
    return "An" if word[0] in "aeiou" else "A"


def _listed(names) -> str:
    """Join names as ``a``, ``a and b`` or ``a, b and c``."""
    names = list(names)
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def _lines(word: str, lines: list[int]) -> str:
    text = ", ".join(map(str, lines))
    return f"{word}{'s' if len(lines) > 1 else ''} {text}"
