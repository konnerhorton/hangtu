"""Location rules L001 to L007 (qc.md §4.2)."""

import numpy as np

from hangtu import vertical_datums
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


def _holes(holes: tuple[str, ...], limit: int) -> str:
    """Name up to ``limit`` holes, then count the rest."""
    named = ", ".join(holes[:limit])
    rest = len(holes) - limit
    return f"{named} and {rest} more" if rest > 0 else named


def _file_datum(data: Data) -> vertical_datums.FileDatum:
    if "LOCA" not in data.groups:
        return vertical_datums.FileDatum()
    return vertical_datums.from_locations(data.table("LOCA"))


def _why_not_from_the_file(found: vertical_datums.FileDatum) -> str:
    """Why LOCA_DATM didn't set the datum (ingest.md §7), or "" if it says none."""
    count = len(found.holes)
    holes = _holes(found.holes, 10)
    if found.reason == "blank":
        return (
            f" LOCA_DATM wasn't used: it is blank for {holes}, so "
            f"{'that hole' if count == 1 else 'those holes'} could be on another "
            "datum. Fill it in and ingest again."
        )
    if found.reason == "local_level":
        return (
            f" LOCA_DATM wasn't used: {holes} {'has' if count == 1 else 'have'} a "
            "LOCA_LOCZ, so LOCA_DATM may be the datum of that local level rather "
            "than LOCA_GL's."
        )
    if found.reason == "different":
        return (
            " LOCA_DATM wasn't used: holes name different datums (L007), so their "
            "elevations can't be compared."
        )
    if found.reason == "unknown":
        (name,) = found.names
        return (
            f" LOCA_DATM wasn't used: \"{name}\" isn't in the datum table. If it is "
            f'a datum, add it with ht.add_vertical_datum("<short name>", '
            f'name="{name}") and ingest again.'
        )
    return ""


@rule("L006")
def no_vertical_datum(data: Data, settings: RuleSettings) -> RuleResult:
    if data.project_settings.get("vertical_datum"):
        return RuleResult([], 1)
    finding = Finding(
        "L006",
        "No vertical datum is known for the project, so elevations don't say "
        'what they are measured from. Set it with p.settings.vertical_datum = "NAVD88" '
        "(or the datum of LOCA_GL)." + _why_not_from_the_file(_file_datum(data)),
    )
    return RuleResult([finding], 1)


@rule("L007")
def vertical_datums_disagree(data: Data, settings: RuleSettings) -> RuleResult:
    found = _file_datum(data)
    if not found.names:
        return RuleResult()
    where = {"group": "LOCA", "heading": "LOCA_DATM"}
    if len(found.names) > 1:
        listed = "; ".join(
            f"{name} in {len(holes)} hole{'s' if len(holes) > 1 else ''} "
            f"({_holes(holes, 5)})"
            for name, holes in found.names.items()
        )
        message = (
            f"Holes name different vertical datums in LOCA_DATM: {listed}. Their "
            "elevations (LOCA_GL) can't be compared. Check LOCA_DATM, and convert "
            "the ground levels to one datum before using elevations."
        )
        return RuleResult([Finding("L007", message, **where)], 1)
    datum = data.project_settings.get("vertical_datum")
    source = data.project_settings.get("vertical_datum_source", "setting")
    ((name, holes),) = found.names.items()
    if datum and source == "setting" and not vertical_datums.same(name, datum):
        message = (
            f"The project's vertical datum is set to {datum}, but LOCA_DATM names "
            f"{name} for {_holes(holes, 5)}. Elevations are LOCA_GL as written, so "
            "check which datum the ground levels are on, and set "
            "p.settings.vertical_datum to it."
        )
        return RuleResult([Finding("L007", message, **where)], 1)
    return RuleResult([], 1)
