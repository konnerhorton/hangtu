"""Numbers in QC messages: file unit first, then the display unit (qc.md §4.9).

A value is written as ``6.00 m (19.7 ft)``: in the file's unit, so the supplier
sees the number they wrote, then in the project's display unit when it differs,
so the engineer sees it in theirs. File values keep the file's decimal places
where its TYPE gives them (``2DP``); everything else has 3 significant figures.
"""

import math
import re
from collections.abc import Sequence

import numpy as np

from hangtu import units
from hangtu.qc._data import Data
from hangtu.qc._settings import Threshold


def number(value: float, decimals: int | None = None) -> str:
    """Write ``value`` with ``decimals`` places, else to 3 significant figures."""
    if decimals is None:
        magnitude = math.floor(math.log10(abs(value))) if value else 0
        decimals = max(0, 2 - magnitude)
    return f"{value:.{decimals}f}"


def _decimals(file_type: str | None) -> int | None:
    match = re.fullmatch(r"(\d+)DP", file_type or "")
    return int(match[1]) if match else None


def _unit(text: str):
    unit, _ = units._lookup(text)  # no warning: ingest already reported it (U002)
    return unit


def values(data: Data, group: str, heading: str, si: Sequence[float]) -> str:
    """Write SI values of one heading as ``2.50 to 3.00 m (8.20 to 9.84 ft)``.

    One value gives ``2.50 m (8.20 ft)``; two give a range.
    """
    info = data.heading_info(group, heading)
    kind, file_unit = info["quantity"], info["file_unit"]
    joined = " to ".join
    si = np.asarray(si, dtype=float)
    if kind is None or file_unit is None:
        return joined(number(v) for v in si)
    canonical = units.quantity_kind(kind)["canonical"]
    source = _unit(file_unit)
    if canonical is None or source is None:
        return f"{joined(number(v) for v in si)} {file_unit}"
    canonical = units.ureg.Unit(canonical)
    in_file = units.convert(si, canonical, kind, source)
    text = f"{joined(number(v, _decimals(info['file_type'])) for v in in_file)}"
    text += f" {file_unit}"
    target = units.quantity_kind(kind)[data.display_units]
    target_unit = units.ureg.Unit(target["unit"])
    if units.convert([1.0], source, kind, target_unit)[0] == 1.0:
        return text
    shown = units.convert(si, canonical, kind, target_unit)
    return f"{text} ({joined(number(v) for v in shown)} {target['text']})"


def threshold(data: Data, given: Threshold) -> str:
    """Write a threshold as given, then in the display unit if that differs."""
    kind = given.kind
    canonical = units.quantity_kind(kind)["canonical"]
    if canonical is None:
        return given.text
    source = _unit(units._QUANTITY_TEXT.fullmatch(given.text)[2])
    target = units.quantity_kind(kind)[data.display_units]
    target_unit = units.ureg.Unit(target["unit"])
    if source is None or units.convert([1.0], source, kind, target_unit)[0] == 1.0:
        return given.text
    shown = units.convert([given.value], units.ureg.Unit(canonical), kind, target_unit)
    return f"{given.text} ({number(shown[0])} {target['text']})"
