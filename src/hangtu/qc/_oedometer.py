"""Oedometer rules E (qc.md §4.15, M19 a and c1).

Each checks one specimen against itself: a record whose numbers can't all be
right. Plausible ranges for C_c or σ′p are level 2. A specimen's increments
are its ``CONS`` rows in file order, by ``specimen_id``.
"""

import math
import re
from collections.abc import Iterator
from decimal import Decimal
from itertools import pairwise

import pandas as pd

from hangtu import units as _units
from hangtu.qc import _text
from hangtu.qc._data import Data
from hangtu.qc._registry import Finding, RuleResult, rule
from hangtu.qc._settings import RuleSettings
from hangtu.qc._tests import SLACK, _where


def _at(row: dict, data: Data) -> str:
    """``in BH1 at 5.20 m, increment 3``: where an increment is."""
    text = _where(row, data, "CONS", "SPEC_DPTH")
    if row.get("CONS_INCN") not in (None, ""):
        text += f", increment {row['CONS_INCN']}"
    return text


def _number(data: Data, group: str, row: dict, heading: str) -> float | None:
    """Return the row's value of ``heading``, or None where blank or flagged."""
    value = row.get(heading)
    if value is None or pd.isna(value):
        return None
    if data.flag(group, row["_row"], heading) is not None:
        return None
    return float(value)


def _rounding(data: Data, group: str, heading: str) -> float:
    """Return half a unit in the last place of the heading's ``xDP`` TYPE, else 0."""
    places = _text._decimals(data.heading_info(group, heading)["file_type"])
    return 0.0 if places is None else 0.5 * 10.0**-places


def _tolerance(data: Data, settings: RuleSettings) -> float:
    """Return the chain tolerance, widened where the void ratios are coarser.

    AGS 4.0.4 types ``CONS_INCE`` 2DP and ``CONS_IVR`` 3DP, so a void ratio
    rounded to each can differ by their two roundings without either being
    wrong.
    """
    threshold = settings.thresholds["void_ratio_chain_tolerance"].value
    rounding = _rounding(data, "CONS", "CONS_IVR") + _rounding(
        data, "CONS", "CONS_INCE"
    )
    return max(threshold, rounding)


def _specimens(data: Data) -> Iterator[list[dict]]:
    """Yield each specimen's increments, in file order."""
    cons = data.table("CONS").dropna(subset=["specimen_id"])
    for _, rows in cons.groupby("specimen_id", sort=False):
        yield rows.sort_values("_line").to_dict("records")


def _void_ratio(data: Data, row: dict, heading: str) -> str:
    return f"{heading} {data.text_at('CONS', row['_line'], heading)}"


@rule("E001")
def void_ratios_dont_chain(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("CONS", "CONS_IVR", "CONS_INCE"):
        return RuleResult()
    tolerance = _tolerance(data, settings)
    findings, checked = [], 0
    for rows in _specimens(data):
        for previous, row in pairwise(rows):
            end = _number(data, "CONS", previous, "CONS_INCE")
            start = _number(data, "CONS", row, "CONS_IVR")
            if end is None or start is None:
                continue
            checked += 1
            if abs(start - end) <= tolerance + SLACK:
                continue
            findings.append(
                Finding(
                    "E001",
                    f"{_void_ratio(data, row, 'CONS_IVR')} {_at(row, data)} differs "
                    f"by {_text.number(abs(start - end), 3)} from the previous "
                    f"increment's {_void_ratio(data, previous, 'CONS_INCE')}. An "
                    "increment starts where the one before it ended, so one of them, "
                    "or the order of the rows, is wrong.",
                    group="CONS",
                    heading="CONS_IVR",
                    line=row["_line"],
                )
            )
    return RuleResult(findings, checked)


@rule("E002")
def void_ratio_rose_under_load(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("CONS", "CONS_INCF", "CONS_INCE"):
        return RuleResult()
    tolerance = _tolerance(data, settings)
    findings, checked = [], 0
    for rows in _specimens(data):
        for previous, row in pairwise(rows):
            stress = _number(data, "CONS", row, "CONS_INCF")
            before = _number(data, "CONS", previous, "CONS_INCF")
            end = _number(data, "CONS", row, "CONS_INCE")
            start = _number(data, "CONS", row, "CONS_IVR")
            if start is None:
                start = _number(data, "CONS", previous, "CONS_INCE")
            if None in (stress, before, end, start):
                continue
            assert stress is not None and before is not None  # checked above
            assert end is not None and start is not None
            if stress <= before + SLACK:
                continue
            checked += 1
            if end <= start + tolerance + SLACK:
                continue
            findings.append(
                Finding(
                    "E002",
                    f"The void ratio {_at(row, data)} rose by "
                    f"{_text.number(end - start, 3)} (to "
                    f"{_void_ratio(data, row, 'CONS_INCE')}) while the stress "
                    f"went up, to {_text.values(data, 'CONS', 'CONS_INCF', [stress])}"
                    ". A specimen compresses under a larger load unless it swells, "
                    "as some clays and rocks still do under a small increase: check "
                    "the void ratios, the stress and the order of the rows.",
                    group="CONS",
                    heading="CONS_INCE",
                    line=row["_line"],
                )
            )
    return RuleResult(findings, checked)


def _half_place(text: str) -> float:
    """Return half a unit in the last place written in ``text``: ``0.32`` -> 0.005."""
    exponent = Decimal(text.strip()).as_tuple().exponent
    assert isinstance(exponent, int)  # a number's text, read by _number already
    return 0.5 * 10.0**exponent


def _reported_interval(text: str) -> tuple[float, float]:
    """Return the reported m_v ± its rounding, never under 2 significant figures.

    BS 1377-5:1990, 3.7, item (i) reports m_v to two significant figures, so a
    value written to more is usually a conversion with its source's precision.
    """
    value = float(text)
    second_figure = math.floor(math.log10(abs(value))) - 1 if value else 0
    half = max(_half_place(text), 0.5 * 10.0**second_figure)
    return value - half, value + half


def _recomputed_interval(
    e1: float, h1: float, e2: float, h2: float, change: float
) -> tuple[float, float]:
    """Return the range of (e1 - e2) / ((1 + e1) Δσ′) over e1 ± h1, e2 ± h2."""
    corners = [
        (a - b) / ((1 + a) * change)
        for a in (e1 - h1, e1 + h1)
        for b in (e2 - h2, e2 + h2)
    ]
    return min(corners), max(corners)


@rule("E003")
def volume_compressibility_mismatch(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("CONS", "CONS_INMV", "CONS_INCF", "CONS_INCE"):
        return RuleResult()
    stress_unit = data.heading_info("CONS", "CONS_INCF")["file_unit"]
    mv_unit = data.heading_info("CONS", "CONS_INMV")["file_unit"]
    if not stress_unit or not mv_unit:
        return RuleResult()
    # 1 per (file stress unit), in the file's m_v unit.
    factor = float(
        (1 / _units.ureg.Quantity(1.0, _units.parse_unit(stress_unit)))
        .to(_units.parse_unit(mv_unit))
        .magnitude
    )
    rounding = {h: _rounding(data, "CONS", h) for h in ("CONS_IVR", "CONS_INCE")}
    findings, checked = [], 0
    for rows in _specimens(data):
        for previous, row in pairwise(rows):
            reported = _number(data, "CONS", row, "CONS_INMV")
            stress = _number(data, "CONS", row, "CONS_INCF")
            before = _number(data, "CONS", previous, "CONS_INCF")
            end = _number(data, "CONS", row, "CONS_INCE")
            start, start_heading = _number(data, "CONS", row, "CONS_IVR"), "CONS_IVR"
            if start is None:
                start = _number(data, "CONS", previous, "CONS_INCE")
                start_heading = "CONS_INCE"
            if None in (reported, stress, before, end, start):
                continue
            assert stress is not None and before is not None  # checked above
            assert end is not None and start is not None
            # The file's own text and unit, not the SI table.
            text = data.text_at("CONS", row["_line"], "CONS_INMV")
            stress_text = data.text_at("CONS", row["_line"], "CONS_INCF")
            before_text = data.text_at("CONS", previous["_line"], "CONS_INCF")
            assert text and stress_text and before_text  # not blank: read above
            change = float(stress_text) - float(before_text)
            if change <= 0:
                continue
            checked += 1
            low, high = _recomputed_interval(
                start, rounding[start_heading], end, rounding["CONS_INCE"], change
            )
            low, high = low * factor, high * factor
            reported_low, reported_high = _reported_interval(text)
            if low <= reported_high + SLACK and reported_low <= high + SLACK:
                continue
            unit = f" {mv_unit}"
            findings.append(
                Finding(
                    "E003",
                    f"CONS_INMV {text}{unit} {_at(row, data)} doesn't follow from "
                    "the increment's void ratios and stresses: "
                    "(e1 - e2) / ((1 + e1)(σ′2 - σ′1)), with e1 at the increment's "
                    "start (BS 1377-5:1990, 3.6.2.2.4), gives "
                    f"{_text.number(low)} to {_text.number(high)}{unit} within the "
                    "rounding of the values. A lab dividing by 1 + e0 of the "
                    "specimen instead gives values that grow apart at later "
                    "increments; check the m_v, the void ratios and the stresses.",
                    group="CONS",
                    heading="CONS_INMV",
                    line=row["_line"],
                )
            )
    return RuleResult(findings, checked)


def _increment_number(text: object) -> float | None:
    """Return ``CONS_INCN`` as a number (``"3"``, ``"3.5"``), else None."""
    if not isinstance(text, str) or not re.fullmatch(r"\s*\d+(\.\d+)?\s*", text):
        return None
    return float(text)


@rule("E004")
def increments_out_of_order(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("CONS", "CONS_INCN"):
        return RuleResult()
    findings, checked = [], 0
    raw = data.raw("CONS").set_index("_line")["CONS_INCN"]
    for rows in _specimens(data):
        largest: tuple[float, str] | None = None
        for row in rows:
            text = raw.get(row["_line"])
            number = _increment_number(text)
            if number is None:
                continue
            checked += 1
            if largest is not None and number <= largest[0]:
                findings.append(
                    Finding(
                        "E004",
                        f"CONS_INCN {text} {_where(row, data, 'CONS', 'SPEC_DPTH')} "
                        f"comes after increment {largest[1]} in the file. "
                        "p.oedometer() takes the increments in file order, so the "
                        "branches and the curve follow the rows: put them in test "
                        "order.",
                        group="CONS",
                        heading="CONS_INCN",
                        line=row["_line"],
                    )
                )
            if largest is None or number > largest[0]:
                largest = (number, str(text))
    return RuleResult(findings, checked)


@rule("E005")
def initial_void_ratio_mismatch(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("CONG", "CONG_IVR", "CONG_PDEN", "CONG_DDEN"):
        return RuleResult()
    tolerance = settings.thresholds["initial_void_ratio_tolerance"].value
    cong = data.table("CONG")
    findings, checked = [], 0
    for row in cong.to_dict("records"):
        void_ratio = _number(data, "CONG", row, "CONG_IVR")
        dry = _number(data, "CONG", row, "CONG_DDEN")
        particle = row.get("CONG_PDEN")
        flag = data.flag("CONG", row["_row"], "CONG_PDEN")
        assumed = flag is not None and flag.flag == "ASSUMED"
        if particle is None or pd.isna(particle) or (flag is not None and not assumed):
            continue
        if void_ratio is None or dry is None or dry <= 0:
            continue
        checked += 1
        expected = float(particle) / dry - 1
        if abs(void_ratio - expected) <= tolerance + SLACK:
            continue
        source = "an assumed particle density (#)" if assumed else "the file's values"
        particle_text = data.text_at("CONG", row["_line"], "CONG_PDEN")
        dry_text = data.text_at("CONG", row["_line"], "CONG_DDEN")
        dry_unit = data.heading_info("CONG", "CONG_DDEN")["file_unit"] or ""
        findings.append(
            Finding(
                "E005",
                f"CONG_IVR {data.text_at('CONG', row['_line'], 'CONG_IVR')} "
                f"{_where(row, data, 'CONG', 'SPEC_DPTH')} differs by "
                f"{_text.number(abs(void_ratio - expected), 3)} from "
                f"ρs / ρd - 1 = {_text.number(expected, 3)}, from CONG_PDEN "
                f"{particle_text} and CONG_DDEN {dry_text} {dry_unit}".rstrip()
                + f" ({source}). Check the densities and the void ratio: the "
                "lab's e0 is usually worked out from them.",
                group="CONG",
                heading="CONG_IVR",
                line=row["_line"],
            )
        )
    return RuleResult(findings, checked)
