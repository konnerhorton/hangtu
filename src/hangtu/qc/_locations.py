"""Location rules L001 to L006 (qc.md §4.2)."""

import numpy as np

from hangtu.qc import _text
from hangtu.qc._data import Data
from hangtu.qc._registry import Finding, RuleResult, rule
from hangtu.qc._settings import RuleSettings

COORDINATES = ("LOCA_NATE", "LOCA_NATN", "LOCA_LAT", "LOCA_LON")


def _blank_rule(data: Data, rule_id: str, heading: str, why: str) -> RuleResult:
    if not data.has("LOCA", heading):
        return RuleResult()
    loca = data.table("LOCA")
    blank = data.blank("LOCA", heading)
    findings = [
        Finding(
            rule_id,
            f"{heading} is blank for {row['LOCA_ID']}, {why} Add it to LOCA.",
            group="LOCA",
            heading=heading,
            line=row["_line"],
        )
        for row in loca[blank].to_dict("records")
    ]
    return RuleResult(findings, len(loca))


@rule("L001")
def ground_level_blank(data: Data, settings: RuleSettings) -> RuleResult:
    return _blank_rule(
        data, "L001", "LOCA_GL", "so its depths can't be given as elevations."
    )


@rule("L002")
def no_coordinates(data: Data, settings: RuleSettings) -> RuleResult:
    present = [h for h in COORDINATES if data.has("LOCA", h)]
    if not present:
        return RuleResult()
    loca = data.table("LOCA")
    grid = data.blank("LOCA", "LOCA_NATE") | data.blank("LOCA", "LOCA_NATN")
    latitude = data.blank("LOCA", "LOCA_LAT") | data.blank("LOCA", "LOCA_LON")
    findings = [
        Finding(
            "L002",
            f"{row['LOCA_ID']} has no coordinates: LOCA_NATE/LOCA_NATN and "
            "LOCA_LAT/LOCA_LON are blank, so it can't be placed on a plan or "
            "compared with nearby holes. Add its coordinates to LOCA.",
            group="LOCA",
            line=row["_line"],
        )
        for row in loca[grid & latitude].to_dict("records")
    ]
    return RuleResult(findings, len(loca))


@rule("L003")
def final_depth_blank(data: Data, settings: RuleSettings) -> RuleResult:
    return _blank_rule(
        data,
        "L003",
        "LOCA_FDEP",
        "so record depths in it can't be checked against the bottom of the hole.",
    )


@rule("L004")
def not_vertical(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("HORN", "LOCA_ID", "HORN_INCL"):
        return RuleResult()
    horn = data.table("HORN")
    tolerance = settings.thresholds["inclination_tolerance"]
    off = (horn["HORN_INCL"] - 90).abs()
    # A small slack keeps a value exactly at the tolerance from being reported
    # because of rounding in the unit conversion.
    tilted = horn[off > tolerance.value + 1e-9]
    findings = []
    for row in tilted.to_dict("records"):
        section = ""
        if data.has("HORN", "HORN_TOP", "HORN_BASE"):
            section = " from " + _text.values(
                data, "HORN", "HORN_TOP", [row["HORN_TOP"], row["HORN_BASE"]]
            )
        findings.append(
            Finding(
                "L004",
                f"HORN_INCL in {row['LOCA_ID']}{section} is "
                f"{_text.values(data, 'HORN', 'HORN_INCL', [row['HORN_INCL']])}, "
                f"{_text.number(abs(row['HORN_INCL'] - 90))}° from vertical, more than "
                f"the tolerance of {tolerance.text}. Depths in this section are "
                "along the hole, not vertical; take that into account when using "
                "them, or check the inclination.",
                group="HORN",
                heading="HORN_INCL",
                line=row["_line"],
            )
        )
    return RuleResult(findings, int(horn["HORN_INCL"].notna().sum()))


@rule("L005")
def ground_level_outlier(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("LOCA", "LOCA_ID", "LOCA_NATE", "LOCA_NATN", "LOCA_GL"):
        return RuleResult()
    loca = data.table("LOCA")
    placed = loca.dropna(subset=["LOCA_NATE", "LOCA_NATN", "LOCA_GL"])
    thresholds = settings.thresholds
    count = int(thresholds["neighbor_count"].value)
    fewest = int(thresholds["fewest_neighbors"].value)
    radius = thresholds["search_radius"].value
    difference = thresholds["ground_level_difference"]
    east, north = placed["LOCA_NATE"].to_numpy(), placed["LOCA_NATN"].to_numpy()
    level = placed["LOCA_GL"].to_numpy()
    findings, checked = [], 0
    for i, row in enumerate(placed.to_dict("records")):
        distance = np.hypot(east - east[i], north - north[i])
        distance[i] = np.inf
        near = [j for j in np.argsort(distance, kind="stable") if distance[j] <= radius]
        near = near[:count]
        if len(near) < fewest:
            continue
        checked += 1
        median = float(np.median(level[near]))
        off = level[i] - median
        if abs(off) <= difference.value + 1e-9:
            continue
        names = ", ".join(str(placed["LOCA_ID"].iloc[j]) for j in near)
        where = "above" if off > 0 else "below"
        findings.append(
            Finding(
                "L005",
                f"LOCA_GL {_text.values(data, 'LOCA', 'LOCA_GL', [level[i]])} in "
                f"{row['LOCA_ID']} is "
                f"{_text.values(data, 'LOCA', 'LOCA_GL', [abs(off)])} {where} the "
                f"median of the {len(near)} nearest holes, "
                f"{_text.values(data, 'LOCA', 'LOCA_GL', [median])} ({names}), more "
                f"than {_text.threshold(data, difference)}. Check the ground level "
                "and the coordinates.",
                group="LOCA",
                heading="LOCA_GL",
                line=row["_line"],
            )
        )
    return RuleResult(findings, checked)


@rule("L006")
def no_vertical_datum(data: Data, settings: RuleSettings) -> RuleResult:
    if data.project_settings.get("vertical_datum"):
        return RuleResult([], 1)
    finding = Finding(
        "L006",
        "The project's vertical datum isn't set, so elevations don't say what "
        'they are measured from. Set it with p.settings.vertical_datum = "NAVD88" '
        "(or the datum of LOCA_GL).",
    )
    return RuleResult([finding], 1)
