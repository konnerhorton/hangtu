"""The QC report: findings, the rules used, and where they came from (qc.md §5)."""

import datetime as dt
from importlib.metadata import version
from os import PathLike
from pathlib import Path
from typing import Any

import pandas as pd

import hangtu.db as database
from hangtu.qc._accepted import Accepted, apply
from hangtu.qc._data import Data
from hangtu.qc._registry import THRESHOLDS_FROM, Finding, RuleResult
from hangtu.qc._settings import (
    RuleSettings,
    Settings,
    is_ingest_rule,
    rule_sort_key,
)

SEVERITIES = ("error", "warning", "info")
FINDING_COLUMNS = [
    "rule_id",
    "severity",
    "accepted",
    "reason",
    "group",
    "loca_id",
    "depth",
    "depth_unit",
    "heading",
    "value",
    "message",
    "source_line",
]
RULE_COLUMNS = [
    "rule_id",
    "title",
    "enabled",
    "severity",
    "thresholds",
    "overridden",
    "records_checked",
    "findings",
]
#: Shown in ``report.rules`` for an ingest rule that keeps each stored severity.
AS_STORED = "as stored"


class Report:
    """The result of ``p.qc()``.

    Attributes
    ----------
    findings : DataFrame
        One row per finding, sorted by severity, rule and line (qc.md §5.1).
    rules : DataFrame
        The settings this run used, one row per rule (qc.md §5.2).
    accepted : DataFrame
        One row per accepted entry, in the order given, with how many findings
        it matched and its ``status``: ``matched``, ``no match`` or ``rule
        disabled`` (qc.md §5.4). An entry's depth matches a finding's within
        0.05 m. Empty when ``accepted=`` isn't given.
    source : dict
        The file checked, its SHA-256 and AGS version, hangtu's version, the
        time of the run, and the accepted-findings file (its path, ``list``,
        or blank).

    Examples
    --------
    >>> report = p.qc()
    >>> report                       # counts by severity and by rule
    >>> report.findings.query("severity == 'error' and not accepted")
    >>> report.to_csv("qc_report.csv")
    """

    def __init__(
        self,
        findings: pd.DataFrame,
        rules: pd.DataFrame,
        source: dict[str, Any],
        accepted: pd.DataFrame,
    ) -> None:
        self.findings = findings
        self.rules = rules
        self.source = source
        self.accepted = accepted

    def summary(self) -> pd.DataFrame:
        """Count findings by rule.

        Columns ``rule_id``, ``title``, ``severity``, ``count``, and ``open``
        and ``accepted``, which add up to ``count``.
        """
        titles = dict(zip(self.rules["rule_id"], self.rules["title"], strict=True))
        counts = (
            self.findings.groupby(["severity", "rule_id"], sort=False)
            .agg(count=("accepted", "size"), accepted=("accepted", "sum"))
            .reset_index()
        )
        counts["accepted"] = counts["accepted"].astype("int64")
        counts["open"] = counts["count"] - counts["accepted"]
        counts["title"] = [
            titles.get(rule_id) or titles.get("V*") for rule_id in counts["rule_id"]
        ]
        columns = ["rule_id", "title", "severity", "count", "open", "accepted"]
        return counts[columns].reset_index(drop=True)

    def __repr__(self) -> str:
        """Summarize the run: counts by severity, then by rule (qc.md §5.3)."""
        source = self.source
        when = source["run_at"][:16].replace("T", " ")
        lines = [
            f"QC report: {source['file']} (AGS {source['ags_version']}), "
            f"hangtu {source['hangtu_version']}, {when}"
        ]
        reviewed = bool(source["accepted"])
        open_findings = self.findings.loc[~self.findings["accepted"]]
        by_severity = open_findings["severity"].value_counts()
        counts = ", ".join(
            _count(int(by_severity.get(severity, 0)), severity)
            for severity in SEVERITIES
        )
        if reviewed:
            n_accepted = int(self.findings["accepted"].sum())
            counts = f"open: {counts} · accepted: {n_accepted}"
        lines.append(f"  {counts}")
        summary = self.summary()
        width = max((len(title) for title in summary["title"]), default=0)
        count_width = max((len(str(n)) for n in summary["open"]), default=0)
        for row in summary.itertuples(index=False):
            line = (
                f"  {row.severity:<8} {row.rule_id:<5} {row.title:<{width}}  {row.open}"
            )
            if row.accepted:
                line += f"{'':<{count_width - len(str(row.open))}}  "
                line += f"(+{row.accepted} accepted)"
            lines.append(line)
        stale = self._stale()
        if stale:
            entries = "entry matches" if stale == 1 else "entries match"
            lines.append(f"  {stale} accepted {entries} no finding: report.accepted")
        lines.append(
            "  findings: report.findings · rules used: report.rules · "
            'save: report.to_csv("qc_report.csv")'
        )
        return "\n".join(lines)

    def _stale(self) -> int:
        """Count the accepted entries that match no finding."""
        return int((self.accepted["status"] == "no match").sum())

    def to_csv(self, path: str | PathLike[str]) -> None:
        """Write the findings to ``path`` and the rules to ``<stem>_rules.csv``.

        The rules file starts with ``#`` lines naming the file checked and,
        when accepted findings were given, where from and how many matched
        nothing, so a report sent on its own says what it checked. Read it
        back with ``pd.read_csv(path, comment="#")``. Both files are
        overwritten.
        """
        path = Path(path)
        self.findings.to_csv(path, index=False, encoding="utf-8")
        rules_path = path.with_name(f"{path.stem}_rules.csv")
        header = "".join(
            f"# {key}: {value}\n"
            for key, value in self.source.items()
            if key != "accepted"
        )
        if self.source["accepted"]:
            n = len(self.accepted)
            entries = "entry" if n == 1 else "entries"
            header += (
                f"# accepted: {self.source['accepted']}, {n} {entries}, "
                f"{self._stale()} match no finding\n"
            )
        with rules_path.open("w", encoding="utf-8", newline="") as file:
            file.write(header)
            self.rules.to_csv(file, index=False)


def _count(n: int, severity: str) -> str:
    plural = "s" if n != 1 and severity != "info" else ""
    return f"{n} {severity}{plural}"


def build(
    data: Data,
    settings: Settings,
    results: dict[str, RuleResult | None],
    accepted: Accepted,
) -> Report:
    """Assemble the report from stored and computed findings.

    ``results`` holds each computed rule's result, or None for a disabled rule.
    Severity and ``enabled`` are applied here, to ingest and computed findings
    alike, and the accepted entries are matched while depths are still in m.
    """
    rows: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    stored = database.read_findings(data.path)
    for record in stored.to_dict("records"):
        rule = settings.rule(record["rule"])
        if not rule.enabled:
            continue
        finding = Finding(
            rule_id=record["rule"],
            message=record["message"],
            group=record["group"],
            heading=record["heading"],
            line=None if pd.isna(record["_line"]) else int(record["_line"]),
        )
        rows.append(_row(data, finding, rule.severity or record["severity"]))
        counts[record["rule"]] = counts.get(record["rule"], 0) + 1
    for rule_id, result in results.items():
        if result is None:
            continue
        severity = settings.rule(rule_id).severity
        for finding in result.findings:
            rows.append(_row(data, finding, severity))
        counts[rule_id] = len(result.findings)

    accepted_frame = apply(rows, accepted, settings)
    findings = _findings_frame(data, rows)
    found_v = {rule_id for rule_id in stored["rule"] if is_ingest_rule(rule_id)}
    rules = _rules_frame(settings, results, counts, found_v)
    return Report(findings, rules, _source(data, accepted), accepted_frame)


def _row(data: Data, finding: Finding, severity: str) -> dict[str, Any]:
    """Fill a finding's hole, depth and value from its line (qc.md §5.1)."""
    at = data.row_at(finding.line)
    group = finding.group or (at.group if at else None)
    value = finding.value
    if value is None and finding.heading and group:
        value = data.text_at(group, finding.line, finding.heading)
    return {
        "rule_id": finding.rule_id,
        "severity": severity,
        "group": group,
        "loca_id": finding.loca_id or (at.loca_id if at else None),
        "depth": finding.depth
        if finding.depth is not None
        else (at.depth if at else None),
        "heading": finding.heading,
        "value": value,
        "message": finding.message,
        "source_line": finding.line,
    }


def _findings_frame(data: Data, rows: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=[c for c in FINDING_COLUMNS if c != "depth_unit"])
    depth = pd.to_numeric(df["depth"], errors="coerce").astype(float)
    converted, unit = data.to_display_length(depth.to_numpy())
    df["depth"] = converted
    df.insert(
        FINDING_COLUMNS.index("depth_unit"),
        "depth_unit",
        [unit if pd.notna(d) else None for d in depth],
    )
    df["source_line"] = df["source_line"].astype("Int64")
    df["accepted"] = df["accepted"].astype(bool)
    order = {severity: i for i, severity in enumerate(SEVERITIES)}
    df["_severity"] = df["severity"].map(order)
    ranks = {r: i for i, r in enumerate(sorted(set(df["rule_id"]), key=rule_sort_key))}
    df["_rule"] = df["rule_id"].map(ranks)
    df = df.sort_values(
        ["_severity", "_rule", "source_line"], kind="stable", na_position="first"
    )
    df = df.drop(columns=["_severity", "_rule"]).reset_index(drop=True)
    df.attrs["units"] = {"depth": unit}
    return df


def _rules_frame(
    settings: Settings,
    results: dict[str, RuleResult | None],
    counts: dict[str, int],
    found_v: set[str],
) -> pd.DataFrame:
    """One row per rule, in ``rules.yaml`` order; V rules follow ``V*``."""
    listed = list(settings.defaults)
    extra = sorted(
        {
            rule_id
            for rule_id in {*found_v, *settings.overrides}
            if rule_id not in settings.defaults
        },
        key=rule_sort_key,
    )
    at = listed.index("V*") + 1
    order = [*listed[:at], *extra, *listed[at:]]
    rows = []
    for rule_id in order:
        rule = settings.rule(rule_id)
        result = results.get(rule_id)
        rows.append(
            {
                "rule_id": rule_id,
                "title": rule.title,
                "enabled": rule.enabled,
                "severity": rule.severity or AS_STORED,
                "thresholds": _thresholds_text(rule),
                "overridden": "yes" if rule.overridden else "no",
                "records_checked": None if result is None else result.records_checked,
                "findings": counts.get(rule_id, 0),
            }
        )
    rules = pd.DataFrame(rows, columns=RULE_COLUMNS)
    rules["records_checked"] = rules["records_checked"].astype("Int64")
    return rules


def _thresholds_text(rule: RuleSettings) -> str:
    """``name = value; ...``, prefixed by the rule they come from if not its own."""
    text = "; ".join(
        f"{name} = {threshold.text}" for name, threshold in rule.thresholds.items()
    )
    if rule.rule_id in THRESHOLDS_FROM:
        return f"from {THRESHOLDS_FROM[rule.rule_id]}: {text}"
    return text


def _source(data: Data, accepted: Accepted) -> dict[str, Any]:
    source = database.read_source(data.path)
    return {
        "file": Path(source["path"]).name,
        "path": source["path"],
        "sha256": source["sha256"],
        "ags_version": source["ags_version"],
        "hangtu_version": version("hangtu"),
        "run_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "accepted": accepted.source,
    }
