"""Minimally useful fields C001 and C002 (qc.md §4.10).

Missing means the heading isn't in the group, or the cell is blank. A flagged
value (``NP``, ``Dry``, ``<x``) is a result, not a missing one. The fields come
from ``qc/min_fields.yaml`` and ``p.qc(min_fields=...)``; groups not in the
file aren't checked.
"""

import pandas as pd

from hangtu.qc._data import Data
from hangtu.qc._registry import Finding, RuleResult, rule
from hangtu.qc._settings import RuleSettings


def _absent(group: str, heading: str, rule_id: str, why: str) -> Finding:
    return Finding(
        rule_id,
        f"{group} has no {heading} heading, {why}. Ask for it, or change the "
        "minimally useful fields with p.qc(min_fields=...).",
        group=group,
        heading=heading,
    )


def blank_required(data: Data, group: str, required: tuple[str, ...]) -> pd.DataFrame:
    """Return True where a required field of a ``group`` record is missing.

    One bool column per required heading, indexed like ``data.table(group)``.
    An absent heading is missing on every record. A record with any True is
    incomplete: C001 reports it, and the datasets leave it out by default
    (datasets.md §7).
    """
    table = data.table(group)
    return pd.DataFrame(
        {heading: data.blank(group, heading) for heading in required},
        index=table.index,
        dtype=bool,
    )


@rule("C001")
def required_missing(data: Data, settings: RuleSettings) -> RuleResult:
    findings, checked = [], 0
    for group, fields in data.min_fields.items():
        if group not in data.groups or not fields["required"]:
            continue
        table = data.table(group)
        checked += len(table)
        present = [h for h in fields["required"] if data.has(group, h)]
        for heading in fields["required"]:
            if heading not in present:
                findings.append(
                    _absent(
                        group,
                        heading,
                        "C001",
                        "which is required, so none of its records are complete",
                    )
                )
        blank = blank_required(data, group, tuple(present))
        for i, row in zip(table.index, table.to_dict("records"), strict=True):
            missing = [heading for heading in present if blank.at[i, heading]]
            if not missing:
                continue
            where = f" for {row['LOCA_ID']}" if "LOCA_ID" in row else ""
            verb, them = ("is", "it") if len(missing) == 1 else ("are", "them")
            findings.append(
                Finding(
                    "C001",
                    f"Required {' and '.join(missing)} {verb} blank in the {group} "
                    f"record{where}, so the record is incomplete. Add {them}, or "
                    "check whether the record should be there.",
                    group=group,
                    heading=missing[0],
                    line=row["_line"],
                )
            )
    return RuleResult(findings, checked)


@rule("C002")
def recommended_missing(data: Data, settings: RuleSettings) -> RuleResult:
    findings, checked = [], 0
    for group, fields in data.min_fields.items():
        if group not in data.groups or not fields["recommended"]:
            continue
        table = data.table(group)
        checked += len(table)
        for heading in fields["recommended"]:
            if not data.has(group, heading):
                findings.append(_absent(group, heading, "C002", "which is recommended"))
                continue
            blank = int(data.blank(group, heading).sum())
            if blank:
                findings.append(
                    Finding(
                        "C002",
                        f"{heading} is blank in {blank} of {len(table)} {group} "
                        "records. It is recommended; add it where it is known.",
                        group=group,
                        heading=heading,
                    )
                )
    return RuleResult(findings, checked)
