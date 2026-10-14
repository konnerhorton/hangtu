"""QC level 1: rules, report and diff (docs/data/qc.md)."""

from os import PathLike

# The rule modules register their rules with @rule when imported.
from hangtu.qc import _depths, _geology, _locations, _tests  # noqa: F401
from hangtu.qc._data import Data
from hangtu.qc._registry import RULES, RuleResult
from hangtu.qc._report import Report, build
from hangtu.qc._settings import Override, load

__all__ = ["Report", "run"]


def run(
    path: str | PathLike[str],
    rules: Override = None,
    min_fields: Override = None,
) -> Report:
    """Check the project database at ``path`` and return the report (qc.md §2).

    Every override is checked before any rule runs. The database is only read.
    """
    data = Data(path)
    file_headings = zip(data.headings["group"], data.headings["heading"], strict=True)
    settings = load(rules, min_fields, file_headings)
    data.min_fields = settings.min_fields
    results: dict[str, RuleResult | None] = {}
    for rule_id in settings.defaults:
        if rule_id not in RULES:
            continue
        rule = settings.rule(rule_id)
        results[rule_id] = RULES[rule_id](data, rule) if rule.enabled else None
    return build(data, settings, results)
