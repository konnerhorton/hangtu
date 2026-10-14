"""Test result rules S, A, P and K (qc.md §4.5 to §4.8).

Range checks skip blank and flagged values (qc.md §4, "General behavior").
"""

import itertools
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


# --- Particle size -----------------------------------------------------------------

_PERCENTAGES = {
    "GRAT": ("GRAT_PERP",),
    "GRAG": (
        "GRAG_VCRE",
        "GRAG_GRAV",
        "GRAG_SAND",
        "GRAG_SILT",
        "GRAG_CLAY",
        "GRAG_FINE",
    ),
}


def _curves(data: Data) -> list[pd.DataFrame] | None:
    """Each specimen's grading points, coarsest first; None without GRAT."""
    if not data.has("GRAT", "GRAT_SIZE", "GRAT_PERP"):
        return None
    grat = data.table("GRAT")
    if "specimen_id" not in grat:  # a surrogate key, so not in meta_heading
        return None
    return [
        points.sort_values("GRAT_SIZE", ascending=False, kind="stable")
        for _, points in grat.groupby("specimen_id", sort=False)
    ]


@rule("P001")
def curve_rises(data: Data, settings: RuleSettings) -> RuleResult:
    curves = _curves(data)
    if curves is None:
        return RuleResult()
    tolerance = settings.thresholds["percent_passing_tolerance"]
    findings = []
    for points in curves:
        points = points[_unflagged(data, "GRAT", points, "GRAT_SIZE", "GRAT_PERP")]
        rows = points.to_dict("records")
        for coarser, row in itertools.pairwise(rows):
            if row["GRAT_PERP"] <= coarser["GRAT_PERP"] + tolerance.value + SLACK:
                continue
            findings.append(
                Finding(
                    "P001",
                    f"The grading curve {_where(row, data, 'GRAT', 'SPEC_DPTH')} "
                    f"rises at {_value(data, 'GRAT', 'GRAT_SIZE', row['GRAT_SIZE'])}: "
                    f"{_value(data, 'GRAT', 'GRAT_PERP', row['GRAT_PERP'])} passing, "
                    f"more than the {coarser['GRAT_PERP']:g} % passing the coarser "
                    f"sieve ({coarser['GRAT_SIZE']:g} mm). Percent passing can't "
                    "increase as the size decreases; check the two points.",
                    group="GRAT",
                    heading="GRAT_PERP",
                    line=row["_line"],
                )
            )
            break  # one finding per specimen, at the first point that rises
    return RuleResult(findings, len(curves))


@rule("P002")
def percentage_out_of_range(data: Data, settings: RuleSettings) -> RuleResult:
    findings, checked = [], 0
    for group, candidates in _PERCENTAGES.items():
        headings = [h for h in candidates if data.has(group, h)]
        if not headings:
            continue
        table = data.table(group)
        for row in table.to_dict("records"):
            values = [
                h
                for h in headings
                if not np.isnan(row[h]) and data.flag(group, row["_row"], h) is None
            ]
            if not values:
                continue
            checked += 1
            outside = [h for h in values if not 0 <= row[h] <= 100]
            if not outside:
                continue
            heading = outside[0]
            findings.append(
                Finding(
                    "P002",
                    f"{_value(data, group, heading, row[heading])} "
                    f"{_where(row, data, group, 'SPEC_DPTH')} is outside 0 to 100 %. "
                    "Check the value.",
                    group=group,
                    heading=heading,
                    line=row["_line"],
                )
            )
    return RuleResult(findings, checked)


@rule("P003")
def fractions_dont_add_up(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("GRAG", "GRAG_GRAV", "GRAG_SAND"):
        return RuleResult()
    grag = data.table("GRAG")

    def column(heading: str) -> pd.Series:
        if heading not in grag:
            return pd.Series(np.nan, index=grag.index)
        return grag[heading]

    fines = column("GRAG_FINE").fillna(column("GRAG_SILT") + column("GRAG_CLAY"))
    total = (
        column("GRAG_VCRE").fillna(0) + grag["GRAG_GRAV"] + grag["GRAG_SAND"] + fines
    )
    checked = total.notna()
    tolerance = settings.thresholds["fraction_sum_tolerance"]
    findings = [
        Finding(
            "P003",
            f"The grading fractions {_where(row, data, 'GRAG', 'SPEC_DPTH')} add up "
            f"to {total[i]:g} %, more than {tolerance.text} from 100 %. Check "
            "GRAG_VCRE, GRAG_GRAV, GRAG_SAND and the fines (GRAG_FINE, or "
            "GRAG_SILT and GRAG_CLAY).",
            group="GRAG",
            line=row["_line"],
        )
        for i, row in zip(grag.index, grag.to_dict("records"), strict=True)
        if checked[i] and abs(total[i] - 100) > tolerance.value + SLACK
    ]
    return RuleResult(findings, int(checked.sum()))


@rule("P004")
def too_few_points(data: Data, settings: RuleSettings) -> RuleResult:
    curves = _curves(data)
    if curves is None:
        return RuleResult()
    fewest = settings.thresholds["fewest_points"]
    findings = [
        Finding(
            "P004",
            f"The grading curve {_where(row, data, 'GRAT', 'SPEC_DPTH')} has "
            f"{len(points)} point{'s' if len(points) != 1 else ''}, fewer than "
            f"{fewest.text}, so D10, D30 and D60 may not be readable from it.",
            group="GRAT",
            line=row["_line"],
        )
        for points in curves
        if len(points) < fewest.value
        for row in points.head(1).to_dict("records")
    ]
    return RuleResult(findings, len(curves))


# --- Permeability ------------------------------------------------------------------

#: Hydraulic conductivity headings (IPRG is 4.0.x).
_CONDUCTIVITY = {
    "PTST": "PTST_K",
    "FGHG": "FGHG_IPRM",
    "FGHS": "FGHS_IPRM",
    "IPRG": "IPRG_IPRM",
}


@rule("K001")
def conductivity_out_of_range(data: Data, settings: RuleSettings) -> RuleResult:
    lowest = settings.thresholds["lowest_hydraulic_conductivity"]
    highest = settings.thresholds["highest_hydraulic_conductivity"]
    findings, checked = [], 0
    for group, heading in _CONDUCTIVITY.items():
        if not data.has(group, heading):
            continue
        table = data.table(group).dropna(subset=[heading])
        for row in table.to_dict("records"):
            flag = data.flag(group, row["_row"], heading)
            if flag is not None and flag.flag not in ("LT", "GT"):
                continue  # an LT/GT value is checked at its bound
            checked += 1
            value = row[heading]
            if lowest.value <= value <= highest.value:
                continue
            where = _where(row, data, group, data.depth_heading(group))
            if value <= 0:
                why = "isn't greater than zero"
            else:
                why = (
                    f"is outside {_text.threshold(data, lowest)} to "
                    f"{_text.threshold(data, highest)}"
                )
            findings.append(
                Finding(
                    "K001",
                    f"{_value(data, group, heading, value)} {where} {why}. Check the "
                    "value and its unit.",
                    group=group,
                    heading=heading,
                    line=row["_line"],
                )
            )
    return RuleResult(findings, checked)
