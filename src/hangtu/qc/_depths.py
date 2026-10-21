"""Depth rules D001 to D008 (qc.md §4.4).

"Record depth" is each of a group's own depth headings (``Data.record_depths``).
D006 (duplicate) was dropped: python-ags4's Rule 10a already reports it.
"""

from collections.abc import Iterator

import numpy as np
import pandas as pd

from hangtu.qc import _text
from hangtu.qc._data import Data
from hangtu.qc._registry import Finding, RuleResult, rule
from hangtu.qc._settings import RuleSettings

#: Slack on tolerance comparisons, as in the geology rules.
SLACK = 1e-9


def _groups(data: Data) -> Iterator[tuple[str, pd.DataFrame, list[str]]]:
    """Each group with record depths and a LOCA_ID: (group, table, headings)."""
    for group in data.groups:
        depths = data.record_depths(group)
        if depths and data.has(group, "LOCA_ID"):
            yield group, data.table(group), depths


def _top(group: str, depths: list[str]) -> str:
    """Return the record's top depth: ``_TOP``, else ``_DPTH``, else ``SPEC_DPTH``."""
    for heading in (f"{group}_TOP", f"{group}_DPTH", "SPEC_DPTH"):
        if heading in depths:
            return heading
    return depths[0]


def _finding(
    rule_id: str, group: str, row: dict, heading: str, message: str
) -> Finding:
    return Finding(rule_id, message, group=group, heading=heading, line=row["_line"])


def _depth(data: Data, group: str, heading: str, value: float) -> str:
    return f"{heading} {_text.values(data, group, heading, [value])}"


@rule("D001")
def base_above_top(data: Data, settings: RuleSettings) -> RuleResult:
    findings, checked = [], 0
    for group, table, depths in _groups(data):
        top, base = f"{group}_TOP", f"{group}_BASE"
        if top not in depths or base not in depths:
            continue
        both = table.dropna(subset=[top, base])
        checked += len(both)
        for row in both[both[base] < both[top]].to_dict("records"):
            findings.append(
                _finding(
                    "D001",
                    group,
                    row,
                    base,
                    f"{_depth(data, group, base, row[base])} in {row['LOCA_ID']} "
                    f"is above {_depth(data, group, top, row[top])}. Check the two "
                    "depths; they may be swapped.",
                )
            )
    return RuleResult(findings, checked)


@rule("D002")
def negative_depth(data: Data, settings: RuleSettings) -> RuleResult:
    findings, checked = [], 0
    for group, table, depths in _groups(data):
        checked += int(table[depths].notna().any(axis=1).sum())
        for row in table.to_dict("records"):
            negative = [h for h in depths if row[h] < 0]
            if negative:
                heading = negative[0]
                findings.append(
                    _finding(
                        "D002",
                        group,
                        row,
                        heading,
                        f"{_depth(data, group, heading, row[heading])} in "
                        f"{row['LOCA_ID']} is negative, above ground level. Depths "
                        "are measured down from the ground; check the sign.",
                    )
                )
    return RuleResult(findings, checked)


def _final_depths(data: Data) -> dict[str, float]:
    if not data.has("LOCA", "LOCA_ID", "LOCA_FDEP"):
        return {}
    loca = data.table("LOCA").dropna(subset=["LOCA_FDEP"])
    return dict(zip(loca["LOCA_ID"], loca["LOCA_FDEP"], strict=True))


@rule("D003")
def below_final_depth(data: Data, settings: RuleSettings) -> RuleResult:
    final = _final_depths(data)
    tolerance = settings.thresholds["final_depth_tolerance"].value
    findings, checked = [], 0
    for group, table, depths in _groups(data):
        for row in table[table["LOCA_ID"].isin(final)].to_dict("records"):
            bottom = final[row["LOCA_ID"]]
            if all(np.isnan(row[h]) for h in depths):
                continue
            checked += 1
            below = [h for h in depths if row[h] > bottom + tolerance + SLACK]
            if not below:
                continue
            heading = below[0]
            findings.append(
                _finding(
                    "D003",
                    group,
                    row,
                    heading,
                    f"{_depth(data, group, heading, row[heading])} in "
                    f"{row['LOCA_ID']} is below the final depth of the hole, "
                    f"{_depth(data, 'LOCA', 'LOCA_FDEP', bottom)}. Check the "
                    "record's depth or the final depth.",
                )
            )
    return RuleResult(findings, checked)


def _geology(data: Data) -> dict[str, pd.DataFrame]:
    """GEOL intervals with a top and a base, by hole, sorted by top."""
    if not data.has("GEOL", "LOCA_ID", "GEOL_TOP", "GEOL_BASE"):
        return {}
    geol = data.table("GEOL").dropna(subset=["GEOL_TOP", "GEOL_BASE"])
    geol = geol.sort_values(["LOCA_ID", "GEOL_TOP"], kind="stable")
    return {loca_id: log for loca_id, log in geol.groupby("LOCA_ID", sort=False)}


def _in_geology(depth: float, log: pd.DataFrame) -> bool:
    """``top <= d < base`` for some interval, or ``d`` at the bottom of the log."""
    top, base = log["GEOL_TOP"].to_numpy(), log["GEOL_BASE"].to_numpy()
    return bool(((top <= depth) & (depth < base)).any() or depth == base.max())


@rule("D004")
def outside_geology(data: Data, settings: RuleSettings) -> RuleResult:
    logs = _geology(data)
    findings, checked = [], 0
    for group, table, depths in _groups(data):
        if group == "GEOL":
            continue
        heading = _top(group, depths)
        rows = table[table["LOCA_ID"].isin(logs)].dropna(subset=[heading])
        checked += len(rows)
        for row in rows.to_dict("records"):
            log = logs[row["LOCA_ID"]]
            if _in_geology(row[heading], log):
                continue
            span = _text.values(
                data,
                "GEOL",
                "GEOL_TOP",
                [log["GEOL_TOP"].min(), log["GEOL_BASE"].max()],
            )
            findings.append(
                _finding(
                    "D004",
                    group,
                    row,
                    heading,
                    f"{_depth(data, group, heading, row[heading])} in "
                    f"{row['LOCA_ID']} isn't in any geology layer, so it can't be "
                    f"given a geology unit. GEOL there is logged from {span}, and "
                    "any gaps in it are reported as G002. Check the depth or the log.",
                )
            )
    return RuleResult(findings, checked)


@rule("D005")
def crosses_boundary(data: Data, settings: RuleSettings) -> RuleResult:
    logs = _geology(data)
    findings, checked = [], 0
    for group, table, depths in _groups(data):
        top, base = f"{group}_TOP", f"{group}_BASE"
        if group == "GEOL" or top not in depths or base not in depths:
            continue
        rows = table[table["LOCA_ID"].isin(logs)].dropna(subset=[top, base])
        checked += len(rows)
        for row in rows.to_dict("records"):
            log = logs[row["LOCA_ID"]]
            bounds = np.unique(log[["GEOL_TOP", "GEOL_BASE"]].to_numpy())
            inside = bounds[(bounds > row[top]) & (bounds < row[base])]
            if not inside.size:
                continue
            span = _text.values(data, group, top, [row[top], row[base]])
            at = _text.values(data, "GEOL", "GEOL_TOP", [inside[0]])
            findings.append(
                _finding(
                    "D005",
                    group,
                    row,
                    top,
                    f"{group} from {span} in {row['LOCA_ID']} crosses the geology "
                    f"boundary at {at}, so it spans two layers. It is assigned by "
                    "its top depth; check that this is the layer it represents.",
                )
            )
    return RuleResult(findings, checked)


def _specimen_offsets(
    data: Data, depth_tolerance: float
) -> tuple[list[tuple[str, dict, str, float]], int]:
    """Specimens outside their sample by more than ``depth_tolerance``.

    One check per specimen, at its first row, though several tests may share
    it. Returns ``(group, row, sample text, offset in m)`` for each, and the
    number of specimens checked.
    """
    if not data.has("SAMP", "SAMP_TOP"):
        return [], 0
    samples = data.table("SAMP").set_index("sample_id")
    has_base = "SAMP_BASE" in samples
    outside, checked, seen = [], 0, set()
    for group in data.groups:
        if not data.has(group, "SPEC_DPTH", "LOCA_ID") or group == "SAMP":
            continue
        table = data.table(group)
        if "specimen_id" not in table or "sample_id" not in table:
            continue
        for row in table.dropna(subset=["SPEC_DPTH"]).to_dict("records"):
            if row["specimen_id"] in seen or row["sample_id"] not in samples.index:
                continue
            seen.add(row["specimen_id"])  # one check per specimen, not per test
            sample = samples.loc[row["sample_id"]]
            top = sample["SAMP_TOP"]
            base = sample["SAMP_BASE"] if has_base else np.nan
            if np.isnan(top):
                continue
            checked += 1
            depth = row["SPEC_DPTH"]
            offset = max(top - depth, 0.0 if np.isnan(base) else depth - base)
            if offset <= depth_tolerance + SLACK:
                continue
            if np.isnan(base):
                sample_text = f"which starts at {_depth(data, 'SAMP', 'SAMP_TOP', top)}"
            else:
                span = _text.values(data, "SAMP", "SAMP_TOP", [top, base])
                sample_text = f"from {span}"
            outside.append((group, row, sample_text, offset))
    return outside, checked


@rule("D007")
def specimen_outside_sample(data: Data, settings: RuleSettings) -> RuleResult:
    thresholds = settings.thresholds
    outside, checked = _specimen_offsets(data, thresholds["depth_tolerance"].value)
    rounding = thresholds["rounding_tolerance"].value
    findings = [
        _finding(
            "D007",
            group,
            row,
            "SPEC_DPTH",
            f"{_depth(data, group, 'SPEC_DPTH', row['SPEC_DPTH'])} in "
            f"{row['LOCA_ID']} is outside its sample {row['SAMP_ID']}, "
            f"{sample_text}. Check the specimen depth or the sample's depths in SAMP.",
        )
        for group, row, sample_text, offset in outside
        if offset > rounding + SLACK
    ]
    return RuleResult(findings, checked)


@rule("D008")
def specimen_just_outside_sample(data: Data, settings: RuleSettings) -> RuleResult:
    # D007's thresholds (THRESHOLDS_FROM): D008 is the lower band of its check.
    thresholds = settings.thresholds
    outside, checked = _specimen_offsets(data, thresholds["depth_tolerance"].value)
    rounding = thresholds["rounding_tolerance"]
    findings = [
        _finding(
            "D008",
            group,
            row,
            "SPEC_DPTH",
            f"{_depth(data, group, 'SPEC_DPTH', row['SPEC_DPTH'])} in "
            f"{row['LOCA_ID']} is "
            f"{_text.values(data, group, 'SPEC_DPTH', [offset])} outside its "
            f"sample {row['SAMP_ID']}, {sample_text}, within the rounding "
            f"tolerance of {_text.threshold(data, rounding)}. Likely unit "
            "rounding; check the specimen depth if it matters.",
        )
        for group, row, sample_text, offset in outside
        if offset <= rounding.value + SLACK
    ]
    return RuleResult(findings, checked)
