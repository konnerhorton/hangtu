"""The geology map: codes in the file → the units an engineer reports on.

Read from a CSV or a DataFrame and checked before it's stored (datasets.md §5.2).
Codes are matched exactly and case-sensitively (SPEC §8.3), so they're read as
text with nothing trimmed or turned into NaN.
"""

from os import PathLike
from pathlib import Path

import pandas as pd
from matplotlib.colors import is_color_like

from hangtu.errors import HangtuError

COLUMNS = ("code", "geology_unit", "soil_class", "order", "color")
REQUIRED = ("code", "geology_unit")
_EXAMPLE = (
    "code,geology_unit,soil_class,order,color\n"
    "ALV,Alluvium,fine,1,tan\n"
    "TRC,Terrace,coarse,2,#d9b26f"
)


def read(source: "str | PathLike[str] | pd.DataFrame") -> pd.DataFrame:
    """Read and check a geology map; return it with ``COLUMNS``, in map order.

    Blank optional cells are None. ``order`` is a float or None.
    """
    if isinstance(source, pd.DataFrame):
        table, where = source.copy(), "The geology map"
        table.columns = [str(c) for c in table.columns]
        lines = list(range(1, len(table) + 1))
        line_word = "row"
    else:
        path = Path(source)
        if not path.is_file():
            raise HangtuError(
                f"No geology map at {str(path)!r}. Give the path to a CSV file with "
                f"the columns {', '.join(COLUMNS)}, for example:\n{_EXAMPLE}"
            )
        table = pd.read_csv(path, dtype=str, keep_default_na=False)
        where = f"The geology map {path.name}"
        lines = list(range(2, len(table) + 2))  # line 1 is the header
        line_word = "line"
    _check_columns(table, where)
    table = table.reindex(columns=list(COLUMNS))
    table.index = lines
    for column in COLUMNS:
        table[column] = table[column].map(_blank_to_none)
    _check_rows(table, where, line_word)
    table["order"] = _orders(table, where, line_word)
    _check_units(table, where)
    return table.reset_index(drop=True)


def _blank_to_none(value):
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    if isinstance(value, str) and value == "":
        return None
    return value


def _check_columns(table: pd.DataFrame, where: str) -> None:
    missing = [c for c in REQUIRED if c not in table.columns]
    unknown = [c for c in table.columns if c not in COLUMNS]
    if missing or unknown:
        problems = []
        if missing:
            problems.append(f"has no {' or '.join(missing)} column")
        if unknown:
            problems.append(f"has columns hangtu doesn't read: {', '.join(unknown)}")
        raise HangtuError(
            f"{where} {' and '.join(problems)}. Its columns are {', '.join(COLUMNS)} "
            f"(the first two required), for example:\n{_EXAMPLE}"
        )


def _check_rows(table: pd.DataFrame, where: str, line_word: str) -> None:
    for column in REQUIRED:
        blank = table.index[table[column].isna()].tolist()
        if blank:
            raise HangtuError(
                f"{where} has a blank {column} on {_lines(line_word, blank)}. Every "
                "row needs a code and the geology unit it belongs to."
            )
    codes = table["code"].astype(str)
    repeated = codes[codes.duplicated(keep=False)]
    if not repeated.empty:
        detail = "; ".join(
            f"{code!r} on {_lines(line_word, rows.index.tolist())}"
            for code, rows in repeated.groupby(repeated, sort=False)
        )
        raise HangtuError(
            f"{where} lists a code more than once: {detail}. Each code belongs to "
            "one geology unit, so keep one row per code."
        )
    bad = [
        (line, color)
        for line, color in table["color"].items()
        if color is not None and not is_color_like(color)
    ]
    if bad:
        detail = ", ".join(f"{color!r} ({line_word} {line})" for line, color in bad)
        raise HangtuError(
            f"{where} has colors matplotlib doesn't recognize: {detail}. Use a color "
            'name ("tan"), a hex string ("#d2b48c") or leave it blank.'
        )


def _orders(table: pd.DataFrame, where: str, line_word: str) -> pd.Series:
    def number(line, value):
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            raise HangtuError(
                f"{where} has order {value!r} on {line_word} {line}, which isn't a "
                "number. Give a number that sets the units' order, or leave it blank."
            ) from None

    return pd.Series(
        [number(line, value) for line, value in table["order"].items()],
        index=table.index,
        dtype=object,
    )


def _check_units(table: pd.DataFrame, where: str) -> None:
    for column, what in (
        ("color", "colors"),
        ("soil_class", "soil classes"),
        ("order", "orders"),
    ):
        given = table.dropna(subset=[column])
        values = given.groupby("geology_unit", sort=False)[column].unique()
        clashing = values[values.map(len) > 1]
        if not clashing.empty:
            detail = "; ".join(
                f"{unit!r}: {', '.join(map(repr, found))}"
                for unit, found in clashing.items()
            )
            raise HangtuError(
                f"{where} gives one geology unit two {what}: {detail}. Every code of "
                f"a unit must give the same {column.replace('_', ' ')}, or leave it "
                "blank on all but one."
            )


def _lines(word: str, lines: list[int]) -> str:
    text = ", ".join(map(str, lines))
    return f"{word}{'s' if len(lines) > 1 else ''} {text}"


def unit_order(table: pd.DataFrame) -> list[str]:
    """Return the map's geology units in order (datasets.md §5.2).

    By ``order`` where given; units without one follow, in order of first
    appearance.
    """
    first = {}
    for position, row in enumerate(table.itertuples(index=False)):
        unit = row.geology_unit
        number = None if pd.isna(row.order) else float(row.order)
        if unit not in first:
            first[unit] = [number, position]
        elif first[unit][0] is None and number is not None:
            first[unit][0] = number
    return sorted(
        first,
        key=lambda u: (first[u][0] is None, first[u][0] or 0.0, first[u][1]),
    )


def unit_values(table: pd.DataFrame, column: str) -> dict[str, str]:
    """Return ``{geology unit: value}`` of ``soil_class`` or ``color``."""
    given = table.dropna(subset=[column])
    return dict(zip(given["geology_unit"], given[column], strict=True))
