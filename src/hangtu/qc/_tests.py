"""Test result rules: SPT (S), Atterberg limits (A), qc.md §4.5 and §4.6.

Range checks skip blank and flagged values (qc.md §4, "General behavior").
"""

import re

import numpy as np
import pandas as pd

from hangtu.analysis._spt import n60
from hangtu.qc import _text
from hangtu.qc._data import Data
from hangtu.qc._registry import Finding, RuleResult, rule
from hangtu.qc._settings import RuleSettings

#: Slack on tolerance comparisons, as in the geology rules.
SLACK = 1e-9

_COMPLETE = re.compile(r"N\s*=\s*\d+")
_PAIRS = re.compile(r"\d+\s*/\s*\d+(\s+\d+\s*/\s*\d+)*")
_INCREMENTS = ("ISPT_INC3", "ISPT_INC4", "ISPT_INC5", "ISPT_INC6")


def _unflagged(data: Data, group: str, table: pd.DataFrame, *headings) -> pd.Series:
    """Return True for rows where each of ``headings`` is an unflagged number."""
    keep = table[list(headings)].notna().all(axis=1)
    for heading in headings:
        flagged = [data.flag(group, row, heading) is not None for row in table["_row"]]
        keep &= ~np.asarray(flagged, dtype=bool)
    return keep


def _where(row: dict, data: Data, group: str, heading: str | None) -> str:
    """``in BH1 at 3.00 m (9.84 ft)``: the record's hole and depth."""
    text = f"in {row['LOCA_ID']}" if "LOCA_ID" in row else ""
    if heading and not pd.isna(row.get(heading)):
        text += f" at {_text.values(data, group, heading, [row[heading]])}"
    return text


def _value(data: Data, group: str, heading: str, value: float) -> str:
    return f"{heading} {_text.values(data, group, heading, [value])}"


# --- SPT ---------------------------------------------------------------------------


@rule("S001")
def report_unreadable(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("ISPT", "ISPT_REP"):
        return RuleResult()
    ispt = data.table("ISPT")
    given = ispt[~data.blank("ISPT", "ISPT_REP")]
    findings = []
    for row in given.to_dict("records"):
        report = str(row["ISPT_REP"]).strip()
        if _COMPLETE.fullmatch(report) or _PAIRS.fullmatch(report):
            continue
        findings.append(
            Finding(
                "S001",
                f'ISPT_REP "{report}" {_where(row, data, "ISPT", "ISPT_TOP")} is '
                'neither a complete test ("N=12") nor blows/penetration pairs '
                '("25/75 50/75"), so whether the drive was completed can\'t be '
                "read from it. Check the report.",
                group="ISPT",
                heading="ISPT_REP",
                line=row["_line"],
            )
        )
    return RuleResult(findings, len(given))


@rule("S002")
def improbable_n(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("ISPT", "ISPT_NVAL"):
        return RuleResult()
    ispt = data.table("ISPT")
    rows = ispt[_unflagged(data, "ISPT", ispt, "ISPT_NVAL")]
    highest = settings.thresholds["highest_spt_n"]
    findings = [
        Finding(
            "S002",
            f"ISPT_NVAL {row['ISPT_NVAL']:g} {_where(row, data, 'ISPT', 'ISPT_TOP')} "
            f"is above {highest.text}, which is improbable for a completed test. "
            "Check the N value, or whether the test was a refusal.",
            group="ISPT",
            heading="ISPT_NVAL",
            line=row["_line"],
        )
        for row in rows.to_dict("records")
        if row["ISPT_NVAL"] > highest.value
    ]
    return RuleResult(findings, len(rows))


@rule("S003")
def no_energy_ratio(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("ISPT", "LOCA_ID", "ISPT_ERAT"):
        return RuleResult()
    ispt = data.table("ISPT").assign(_blank=data.blank("ISPT", "ISPT_ERAT"))
    findings = []
    for loca_id, tests in ispt.groupby("LOCA_ID", sort=False):
        blank = int(tests["_blank"].sum())
        if not blank:
            continue
        findings.append(
            Finding(
                "S003",
                f"{blank} of {len(tests)} SPTs in {loca_id} have no energy ratio "
                "(ISPT_ERAT), so N60 can't be computed for them. Add the hammer's "
                "energy ratio, or set ht.settings.hammer_efficiency for the analysis.",
                group="ISPT",
                heading="ISPT_ERAT",
                loca_id=loca_id,
            )
        )
    return RuleResult(findings, len(ispt))


@rule("S004")
def n_differs_from_blows(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("ISPT", "ISPT_NVAL"):
        return RuleResult()
    ispt = data.table("ISPT")
    rows = ispt[_unflagged(data, "ISPT", ispt, "ISPT_NVAL")]
    has_main = data.has("ISPT", "ISPT_MAIN")
    has_increments = data.has("ISPT", *_INCREMENTS)
    findings, checked = [], 0
    for row in rows.to_dict("records"):
        blows = []
        if has_main and not np.isnan(row["ISPT_MAIN"]):
            blows.append(("ISPT_MAIN", row["ISPT_MAIN"]))
        if has_increments and all(not np.isnan(row[h]) for h in _INCREMENTS):
            blows.append(("ISPT_INC3 to ISPT_INC6", sum(row[h] for h in _INCREMENTS)))
        if not blows:
            continue
        checked += 1
        for name, total in blows:
            if total == row["ISPT_NVAL"]:
                continue
            findings.append(
                Finding(
                    "S004",
                    f"ISPT_NVAL {row['ISPT_NVAL']:g} "
                    f"{_where(row, data, 'ISPT', 'ISPT_TOP')} doesn't match the "
                    f"blows of the test drive, {name} = {total:g}. Check the N value "
                    "and the blow counts.",
                    group="ISPT",
                    heading="ISPT_NVAL",
                    line=row["_line"],
                )
            )
            break
    return RuleResult(findings, checked)


@rule("S005")
def n60_differs(data: Data, settings: RuleSettings) -> RuleResult:
    headings = ("ISPT_NVAL", "ISPT_ERAT", "ISPT_N60")
    if not data.has("ISPT", *headings):
        return RuleResult()
    ispt = data.table("ISPT")
    rows = ispt[_unflagged(data, "ISPT", ispt, *headings)]
    tolerance = settings.thresholds["n60_tolerance"]
    findings = []
    for row in rows.to_dict("records"):
        computed = n60(row["ISPT_NVAL"], row["ISPT_ERAT"])
        if abs(row["ISPT_N60"] - computed) <= tolerance.value + SLACK:
            continue
        findings.append(
            Finding(
                "S005",
                f"ISPT_N60 {row['ISPT_N60']:g} {_where(row, data, 'ISPT', 'ISPT_TOP')} "
                f"differs from N * ER / 60 = {row['ISPT_NVAL']:g} * "
                f"{row['ISPT_ERAT']:g} / 60 = {_text.number(computed)} by more than "
                f"{tolerance.text}. Check N60, N and the energy ratio; "
                "ht.analysis.spt() uses the file's N60 where it is given.",
                group="ISPT",
                heading="ISPT_N60",
                line=row["_line"],
            )
        )
    return RuleResult(findings, len(rows))


# --- Atterberg limits --------------------------------------------------------------


def _llpl(data: Data, *headings: str) -> pd.DataFrame | None:
    if not data.has("LLPL", *headings):
        return None
    llpl = data.table("LLPL")
    return llpl[_unflagged(data, "LLPL", llpl, *headings)]


@rule("A001")
def liquid_below_plastic(data: Data, settings: RuleSettings) -> RuleResult:
    rows = _llpl(data, "LLPL_LL", "LLPL_PL")
    if rows is None:
        return RuleResult()
    findings = [
        Finding(
            "A001",
            f"{_value(data, 'LLPL', 'LLPL_LL', row['LLPL_LL'])} "
            f"{_where(row, data, 'LLPL', 'SPEC_DPTH')} is below "
            f"{_value(data, 'LLPL', 'LLPL_PL', row['LLPL_PL'])}. A liquid limit "
            "can't be below the plastic limit; check the two values.",
            group="LLPL",
            heading="LLPL_LL",
            line=row["_line"],
        )
        for row in rows.to_dict("records")
        if row["LLPL_LL"] < row["LLPL_PL"]
    ]
    return RuleResult(findings, len(rows))


@rule("A002")
def plasticity_index_differs(data: Data, settings: RuleSettings) -> RuleResult:
    rows = _llpl(data, "LLPL_LL", "LLPL_PL", "LLPL_PI")
    if rows is None:
        return RuleResult()
    tolerance = settings.thresholds["plasticity_index_tolerance"]
    findings = []
    for row in rows.to_dict("records"):
        difference = row["LLPL_LL"] - row["LLPL_PL"]
        if abs(row["LLPL_PI"] - difference) <= tolerance.value + SLACK:
            continue
        findings.append(
            Finding(
                "A002",
                f"LLPL_PI {row['LLPL_PI']:g} {_where(row, data, 'LLPL', 'SPEC_DPTH')} "
                f"differs from LL - PL = {row['LLPL_LL']:g} - {row['LLPL_PL']:g} = "
                f"{difference:g} by more than {tolerance.text}. Check the three "
                "values.",
                group="LLPL",
                heading="LLPL_PI",
                line=row["_line"],
            )
        )
    return RuleResult(findings, len(rows))


@rule("A003")
def improbable_liquid_limit(data: Data, settings: RuleSettings) -> RuleResult:
    rows = _llpl(data, "LLPL_LL")
    if rows is None:
        return RuleResult()
    lowest = settings.thresholds["lowest_liquid_limit"]
    highest = settings.thresholds["highest_liquid_limit"]
    findings = [
        Finding(
            "A003",
            f"{_value(data, 'LLPL', 'LLPL_LL', row['LLPL_LL'])} "
            f"{_where(row, data, 'LLPL', 'SPEC_DPTH')} is outside {lowest.text} to "
            f"{highest.text}, which is improbable. Check the value.",
            group="LLPL",
            heading="LLPL_LL",
            line=row["_line"],
        )
        for row in rows.to_dict("records")
        if not lowest.value <= row["LLPL_LL"] <= highest.value
    ]
    return RuleResult(findings, len(rows))


@rule("A004")
def non_plastic(data: Data, settings: RuleSettings) -> RuleResult:
    headings = [h for h in ("LLPL_LL", "LLPL_PL", "LLPL_PI") if data.has("LLPL", h)]
    if not headings:
        return RuleResult()
    llpl = data.table("LLPL")
    findings = []
    for row in llpl.to_dict("records"):
        flagged = [
            h
            for h in headings
            if (flag := data.flag("LLPL", row["_row"], h)) and flag.flag == "NP"
        ]
        if not flagged:
            continue
        findings.append(
            Finding(
                "A004",
                f"The specimen {_where(row, data, 'LLPL', 'SPEC_DPTH')} is non-plastic "
                f"({' and '.join(flagged)} NP). It has no plasticity index and plots "
                "on no plasticity chart; this is a result, not a defect.",
                group="LLPL",
                heading=flagged[0],
                line=row["_line"],
            )
        )
    return RuleResult(findings, len(llpl))
