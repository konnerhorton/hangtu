"""Geology rules G001 to G004 (qc.md §4.3)."""

import numpy as np
import pandas as pd

import hangtu.db as database
from hangtu.qc import _text
from hangtu.qc._data import Data
from hangtu.qc._registry import Finding, RuleResult, rule
from hangtu.qc._settings import RuleSettings

#: Slack on tolerance comparisons, so a gap exactly at the tolerance isn't
#: reported because of rounding in the unit conversion.
SLACK = 1e-9


def _logs(data: Data) -> pd.DataFrame:
    """GEOL rows with a top and a base, sorted by hole, top and base."""
    geol = data.table("GEOL").dropna(subset=["GEOL_TOP", "GEOL_BASE"])
    return geol.sort_values(["LOCA_ID", "GEOL_TOP", "GEOL_BASE"], kind="stable")


@rule("G001")
def no_geology(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("LOCA", "LOCA_ID") or not data.has("GEOL", "LOCA_ID"):
        return RuleResult()
    logged = set(data.table("GEOL")["LOCA_ID"])
    others: dict[str, list[str]] = {}
    for group in data.groups:
        if group in ("LOCA", "GEOL") or not data.has(group, "LOCA_ID"):
            continue
        for loca_id in set(data.table(group)["LOCA_ID"].dropna()):
            others.setdefault(loca_id, []).append(group)
    loca = data.table("LOCA")
    with_records = loca[loca["LOCA_ID"].isin(others)]
    findings = [
        Finding(
            "G001",
            f"{row['LOCA_ID']} has records in {', '.join(others[row['LOCA_ID']])} "
            "but no geology (GEOL) rows, so its records can't be placed in a "
            "geology unit. Add its log to GEOL; for a CPT or probe hole with no "
            "log, this is expected.",
            group="LOCA",
            line=row["_line"],
        )
        for row in with_records.to_dict("records")
        if row["LOCA_ID"] not in logged
    ]
    return RuleResult(findings, len(with_records))


@rule("G002")
def geology_gap(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("GEOL", "LOCA_ID", "GEOL_TOP", "GEOL_BASE"):
        return RuleResult()
    tolerance = settings.thresholds["depth_tolerance"].value
    final = {}
    if data.has("LOCA", "LOCA_ID", "LOCA_FDEP"):
        loca = data.table("LOCA")
        final = dict(zip(loca["LOCA_ID"], loca["LOCA_FDEP"], strict=True))
    logs = _logs(data)
    findings = []

    def gap(row, top: float, base: float, where: str, heading: str) -> None:
        span = _text.values(data, "GEOL", "GEOL_TOP", [top, base])
        findings.append(
            Finding(
                "G002",
                f"Nothing is logged in {row['LOCA_ID']} from {span}, {where}. Check "
                "GEOL for a missing layer.",
                group="GEOL",
                heading=heading,
                line=row["_line"],
            )
        )

    for _, hole in logs.groupby("LOCA_ID", sort=False):
        rows = hole.to_dict("records")
        if rows[0]["GEOL_TOP"] > tolerance + SLACK:
            gap(rows[0], 0.0, rows[0]["GEOL_TOP"], "above the first layer", "GEOL_TOP")
        deepest = rows[0]["GEOL_BASE"]
        for row in rows[1:]:
            if row["GEOL_TOP"] - deepest > tolerance + SLACK:
                gap(row, deepest, row["GEOL_TOP"], "between two layers", "GEOL_TOP")
            deepest = max(deepest, row["GEOL_BASE"])
        bottom = final.get(rows[0]["LOCA_ID"], np.nan)
        if not np.isnan(bottom) and bottom - deepest > tolerance + SLACK:
            last = max(rows, key=lambda r: r["GEOL_BASE"])
            gap(
                last,
                deepest,
                bottom,
                "below the last layer and above the final depth (LOCA_FDEP)",
                "GEOL_BASE",
            )
    return RuleResult(findings, len(logs))


@rule("G003")
def geology_overlap(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("GEOL", "LOCA_ID", "GEOL_TOP", "GEOL_BASE"):
        return RuleResult()
    tolerance = settings.thresholds["depth_tolerance"].value
    logs = _logs(data)
    findings = []
    for _, hole in logs.groupby("LOCA_ID", sort=False):
        rows = hole.to_dict("records")
        above = rows[0]
        for row in rows[1:]:
            if above["GEOL_BASE"] - row["GEOL_TOP"] > tolerance + SLACK:
                span = _text.values(
                    data,
                    "GEOL",
                    "GEOL_TOP",
                    [row["GEOL_TOP"], min(above["GEOL_BASE"], row["GEOL_BASE"])],
                )
                findings.append(
                    Finding(
                        "G003",
                        f"Two geology layers in {row['LOCA_ID']} overlap from {span}, "
                        f"on lines {above['_line']} and {row['_line']}, so a record "
                        "there is in both. Check GEOL_TOP and GEOL_BASE.",
                        group="GEOL",
                        heading="GEOL_TOP",
                        line=row["_line"],
                    )
                )
            if row["GEOL_BASE"] > above["GEOL_BASE"]:
                above = row
    return RuleResult(findings, len(logs))


@rule("G004")
def unmapped_code(data: Data, settings: RuleSettings) -> RuleResult:
    key = data.project_settings.get("geology_key", "GEOL_GEOL")
    mapping = database.read_geology_map(data.path)
    if mapping.empty or not data.has("GEOL", key):
        return RuleResult()
    geol = data.table("GEOL")
    raw = data.raw("GEOL").set_index("_line")[key].reindex(geol["_line"])
    codes = pd.Series(raw.to_numpy(), index=geol.index).fillna("")
    known = set(mapping["code"])
    findings = []
    for code, rows in geol.groupby(codes, sort=False):
        if code == "" or code in known:
            continue
        first = rows.iloc[0]
        layers = f"{len(rows)} layer{'s' if len(rows) != 1 else ''}"
        findings.append(
            Finding(
                "G004",
                f"{key} {code!r} ({layers}, first in {first['LOCA_ID']}) isn't in the "
                "geology map, so its tests are kept under the code as their own "
                "geology unit. Add it to the map, or check the code.",
                group="GEOL",
                heading=key,
                line=first["_line"],
            )
        )
    return RuleResult(findings, len(geol))
