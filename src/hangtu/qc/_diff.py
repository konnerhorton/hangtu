"""``p.diff(group)``: what ingest did to each cell (qc.md §7)."""

from collections.abc import Sequence
from os import PathLike

import numpy as np
import pandas as pd

import hangtu.db as database
from hangtu import units
from hangtu.errors import HangtuError

COLUMNS = [
    "_line",
    "loca_id",
    "heading",
    "text",
    "file_unit",
    "value",
    "unit",
    "display_value",
    "display_unit",
    "flag",
    "bound",
    "change",
]
CHANGED = ("flagged", "not_converted", "converted", "reformatted")
#: TYPEs ingest always rewrites: elapsed time, angle, yes/no.
_REWRITTEN = ("T", "DMS", "YN")


def diff(
    path: str | PathLike[str],
    group: str,
    heading: str | Sequence[str] | None = None,
    changed_only: bool = False,
) -> pd.DataFrame:
    """Return one row per cell of ``group``: the file's text and what ingest stored.

    See ``Project.diff`` for the columns.
    """
    meta = database.read_headings(path)
    groups = list(dict.fromkeys(meta["group"]))
    if group not in groups:
        raise HangtuError(
            f"This project has no group {group!r}. Groups: {', '.join(groups)}."
        )
    meta = meta[meta["group"] == group].set_index("heading")
    headings = _headings(group, list(meta.index), heading)
    system = database.read_settings(path)["display_units"]

    raw = database.read_table(path, f"raw_{group}").set_index("_line")
    canonical = database.read_table(path, group).set_index("_line")
    flags = database.read_flags(path)
    flags = flags[flags["group"] == group].set_index(["_row", "heading"])
    flag_of = {key: (row.flag, row.bound) for key, row in flags.iterrows()}

    rows = []
    for line in raw.index:
        stored = canonical.loc[line]
        loca_id = stored.get("LOCA_ID")
        for name in headings:
            info = meta.loc[name]
            text = raw.at[line, name]
            value = stored.get(name)
            flag, bound = flag_of.get((int(stored["_row"]), name), (None, None))
            shown, shown_unit = _display(value, info, system)
            rows.append(
                {
                    "_line": int(line),
                    "loca_id": loca_id,
                    "heading": name,
                    "text": text,
                    "file_unit": info["file_unit"] or None,
                    "value": value,
                    "unit": info["unit"],
                    "display_value": shown,
                    "display_unit": shown_unit,
                    "flag": flag,
                    "bound": bound,
                    "change": _change(text, value, flag, info),
                }
            )
    df = pd.DataFrame(rows, columns=COLUMNS)
    if changed_only:
        df = df[df["change"].isin(CHANGED)].reset_index(drop=True)
    return df


def _headings(group: str, known: list[str], heading) -> list[str]:
    if heading is None:
        return known
    wanted = [heading] if isinstance(heading, str) else list(heading)
    unknown = [h for h in wanted if h not in known]
    if unknown:
        raise HangtuError(
            f"{group} has no heading {', '.join(map(repr, unknown))}. "
            f"Headings: {', '.join(known)}."
        )
    return wanted


def _unit(text) -> object:
    if not isinstance(text, str) or not text:
        return None
    unit, _ = units._lookup(text)  # no warning: ingest reported any (U002)
    return unit


def _change(text, value, flag, info) -> str:
    if text is None or str(text).strip() == "":
        return "blank"
    if flag is not None:
        return "flagged"
    if info["status"] == "raw_only":
        return "not_converted"
    if info["file_type"] in _REWRITTEN:
        return "reformatted"
    if info["file_type"] == "DT":
        return "unchanged" if text == value else "reformatted"
    if info["status"] == "converted":
        source, target = _unit(info["file_unit"]), _unit(info["unit"])
        if source is not None and target is not None and source != target:
            return "converted"
    return "unchanged"


def _display(value, info, system: str) -> tuple[object, str | None]:
    """Return the value in the display unit; as stored when it has no kind."""
    kind, unit = info["quantity"], info["unit"]
    if kind is None or value is None or pd.isna(value):
        return value, unit
    target = units.quantity_kind(kind)[system]
    if target["unit"] is None:
        return value, target["text"] or unit
    source = _unit(unit)
    if source is None:
        return value, unit
    shown = units.convert([value], source, kind, units.ureg.Unit(target["unit"]))
    return float(np.asarray(shown)[0]), target["text"]
