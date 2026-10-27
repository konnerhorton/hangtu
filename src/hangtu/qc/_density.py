"""Density rules B (qc.md §4.11, M14).

Each checks one record against itself, or against a wide range that catches a
value in the wrong unit. Checks across tests (saturation, particle against dry
density) are phase relations, M14 (b).
"""

import pandas as pd

from hangtu.qc import _text
from hangtu.qc._data import Data
from hangtu.qc._registry import Finding, RuleResult, rule
from hangtu.qc._settings import RuleSettings
from hangtu.qc._tests import SLACK, _unflagged, _value, _where

#: The bulk densities B003 checks, by group, and the particle density.
_BULK = {"LDEN": "LDEN_BDEN", "IDEN": "IDEN_IDEN"}
_PARTICLE = {"LPDN": "LPDN_PDEN"}
#: Where the material, not the unit, can explain a value outside the range.
_OUTSIDE = {
    "bulk": "peat and organic soils lie below it, and some rock above",
    "particle": "peat and organic soils lie below it, and ores and some rock above",
}


def _lden(data: Data, *headings: str) -> pd.DataFrame | None:
    if not data.has("LDEN", *headings):
        return None
    lden = data.table("LDEN")
    return lden[_unflagged(data, "LDEN", lden, *headings)]


@rule("B001")
def dry_density_differs(data: Data, settings: RuleSettings) -> RuleResult:
    rows = _lden(data, "LDEN_BDEN", "LDEN_DDEN", "LDEN_MC")
    if rows is None:
        return RuleResult()
    tolerance = settings.thresholds["dry_density_tolerance"]
    findings = []
    for row in rows.to_dict("records"):
        expected = row["LDEN_BDEN"] / (1 + row["LDEN_MC"] / 100)
        difference = abs(row["LDEN_DDEN"] - expected)
        if difference <= tolerance.value + SLACK:
            continue
        computed = _text.values(data, "LDEN", "LDEN_DDEN", [expected], computed=True)
        off = _text.values(data, "LDEN", "LDEN_DDEN", [difference], computed=True)
        findings.append(
            Finding(
                "B001",
                f"{_value(data, 'LDEN', 'LDEN_DDEN', row['LDEN_DDEN'])} "
                f"{_where(row, data, 'LDEN', 'SPEC_DPTH')} differs from LDEN_BDEN / "
                f"(1 + LDEN_MC / 100) = {computed} by {off}, more than "
                f"{_text.threshold(data, tolerance)}. Check the three values, which "
                "should come from one specimen.",
                group="LDEN",
                heading="LDEN_DDEN",
                line=row["_line"],
            )
        )
    return RuleResult(findings, len(rows))


@rule("B002")
def dry_above_bulk(data: Data, settings: RuleSettings) -> RuleResult:
    rows = _lden(data, "LDEN_BDEN", "LDEN_DDEN")
    if rows is None:
        return RuleResult()
    findings = [
        Finding(
            "B002",
            f"{_value(data, 'LDEN', 'LDEN_DDEN', row['LDEN_DDEN'])} "
            f"{_where(row, data, 'LDEN', 'SPEC_DPTH')} is above "
            f"{_value(data, 'LDEN', 'LDEN_BDEN', row['LDEN_BDEN'])}. A dry density "
            "can't exceed the bulk density; check the two values.",
            group="LDEN",
            heading="LDEN_DDEN",
            line=row["_line"],
        )
        for row in rows.to_dict("records")
        if row["LDEN_DDEN"] > row["LDEN_BDEN"] + SLACK
    ]
    return RuleResult(findings, len(rows))


@rule("B003")
def improbable_density(data: Data, settings: RuleSettings) -> RuleResult:
    findings, checked = [], 0
    for kind, headings in (("bulk", _BULK), ("particle", _PARTICLE)):
        lowest = settings.thresholds[f"lowest_{kind}_density"]
        highest = settings.thresholds[f"highest_{kind}_density"]
        for group, heading in headings.items():
            if not data.has(group, heading):
                continue
            table = data.table(group).dropna(subset=[heading])
            for row in table.to_dict("records"):
                flag = data.flag(group, row["_row"], heading)
                if flag is not None and flag.flag != "ASSUMED":
                    continue  # an assumed value is checked like a measured one
                checked += 1
                if lowest.value <= row[heading] <= highest.value:
                    continue
                where = _where(row, data, group, data.depth_heading(group))
                findings.append(
                    Finding(
                        "B003",
                        f"{_value(data, group, heading, row[heading])} {where} is "
                        f"outside the {kind} density range "
                        f"{_text.threshold(data, lowest)} to "
                        f"{_text.threshold(data, highest)}; {_OUTSIDE[kind]}. "
                        "Check the value's unit (kg/m3 and pcf read as Mg/m3 fall "
                        "far outside), then the material.",
                        group=group,
                        heading=heading,
                        line=row["_line"],
                    )
                )
    return RuleResult(findings, checked)


@rule("B004")
def assumed_particle_density(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("LPDN", "LPDN_PDEN"):
        return RuleResult()
    lpdn = data.table("LPDN")
    findings = []
    for row in lpdn.to_dict("records"):
        flag = data.flag("LPDN", row["_row"], "LPDN_PDEN")
        if flag is None or flag.flag != "ASSUMED":
            continue
        findings.append(
            Finding(
                "B004",
                f"{_value(data, 'LPDN', 'LPDN_PDEN', row['LPDN_PDEN'])} "
                f"{_where(row, data, 'LPDN', 'SPEC_DPTH')} is assumed (#), not "
                "measured. It's kept and flagged in p.particle_density(); this is "
                "a note, not a defect.",
                group="LPDN",
                heading="LPDN_PDEN",
                line=row["_line"],
            )
        )
    return RuleResult(findings, len(lpdn))
