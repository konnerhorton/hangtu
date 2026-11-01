"""Undrained strength rules Q (qc.md §4.13, M17 a).

Each checks one record. Plausible ranges for s_u are level 2. ``Q`` is for
``TRIG_TYPE``'s "quick undrained"; ``U`` (units) is taken.
"""

from hangtu.qc import _text
from hangtu.qc._data import Data
from hangtu.qc._registry import Finding, RuleResult, rule
from hangtu.qc._settings import RuleSettings
from hangtu.qc._tests import SLACK, _unflagged, _value, _where

#: Each group's peak and remolded headings (Q002).
_REMOLDED = {
    "IVAN": ("IVAN_IVAN", "IVAN_IVAR"),
    "LVAN": ("LVAN_VNPK", "LVAN_VNRM"),
    "LFCN": ("LFCN_FCPK", "LFCN_FCRM"),
}
#: Each group's strength heading (Q003).
_STRENGTH = {
    "LUCT": "LUCT_UCS",
    "LVAN": "LVAN_VNPK",
    "LPEN": "LPEN_PPEN",
    "LFCN": "LFCN_FCPK",
    "IVAN": "IVAN_IVAN",
    "IPEN": "IPEN_IPEN",
}
#: The heading that places a record: the specimen's depth, or the test's.
_DEPTH = {"IVAN": "IVAN_DPTH", "IPEN": "IPEN_DPTH"}


def _at(row: dict, data: Data, group: str) -> str:
    """``in BH1 at 1.20 m (3.94 ft)``, with the stage for a UU stage."""
    text = _where(row, data, group, _DEPTH.get(group, "SPEC_DPTH"))
    stage = row.get(f"{group}_TESN")
    if group == "TRIT" and stage not in (None, ""):
        text += f", stage {stage}"
    return text


@rule("Q001")
def reported_s_u_differs(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("TRIT", "TRIT_CU", "TRIT_DEVF"):
        return RuleResult()
    trit = data.table("TRIT")
    rows = trit[_unflagged(data, "TRIT", trit, "TRIT_CU", "TRIT_DEVF")]
    tolerance = settings.thresholds["undrained_strength_tolerance"]
    findings = []
    for row in rows.to_dict("records"):
        expected = row["TRIT_DEVF"] / 2
        difference = abs(row["TRIT_CU"] - expected)
        if difference <= tolerance.value + SLACK:
            continue
        computed = _text.values(data, "TRIT", "TRIT_CU", [expected])
        off = _text.values(data, "TRIT", "TRIT_CU", [difference])
        findings.append(
            Finding(
                "Q001",
                f"{_value(data, 'TRIT', 'TRIT_CU', row['TRIT_CU'])} "
                f"{_at(row, data, 'TRIT')}, differs from TRIT_DEVF / 2 = {computed} "
                f"by {off}, more than {_text.threshold(data, tolerance)}. "
                "p.undrained_strength() uses q_f / 2 and keeps the lab's value "
                "beside it as reported_undrained_shear_strength; check the two "
                "values on the lab's sheet.",
                group="TRIT",
                heading="TRIT_CU",
                line=row["_line"],
            )
        )
    return RuleResult(findings, len(rows))


@rule("Q002")
def remolded_above_peak(data: Data, settings: RuleSettings) -> RuleResult:
    findings, checked = [], 0
    for group, (peak, remolded) in _REMOLDED.items():
        if not data.has(group, peak, remolded):
            continue
        table = data.table(group)
        rows = table[_unflagged(data, group, table, peak, remolded)]
        checked += len(rows)
        findings += [
            Finding(
                "Q002",
                f"{_value(data, group, remolded, row[remolded])} "
                f"{_at(row, data, group)} "
                f"is above its peak, {_value(data, group, peak, row[peak])}. A "
                "remolded strength is the lower of the two; the values are usually "
                "swapped. The sensitivity from them is below 1.",
                group=group,
                heading=remolded,
                line=row["_line"],
            )
            for row in rows.to_dict("records")
            if row[remolded] > row[peak] + SLACK
        ]
    return RuleResult(findings, checked)


@rule("Q003")
def strength_not_positive(data: Data, settings: RuleSettings) -> RuleResult:
    findings, checked = [], 0
    for group, heading in _STRENGTH.items():
        if not data.has(group, heading):
            continue
        table = data.table(group)
        rows = table[_unflagged(data, group, table, heading)]
        checked += len(rows)
        findings += [
            Finding(
                "Q003",
                f"{_value(data, group, heading, row[heading])} "
                f"{_at(row, data, group)} is 0 or less, which can't be a strength: "
                "check the value and its sign. p.undrained_strength() leaves its "
                "s_u blank.",
                group=group,
                heading=heading,
                line=row["_line"],
            )
            for row in rows.to_dict("records")
            if row[heading] <= SLACK
        ]
    return RuleResult(findings, checked)
