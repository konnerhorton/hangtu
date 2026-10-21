"""The QC rules in code: threshold kinds and rule functions (qc.md §3.1).

``rules.yaml`` holds each rule's default settings; this module holds what code
decides. ``THRESHOLDS`` declares the quantity kind of every threshold, so
override checks work before any rule function exists. The kinds aren't
inferred from the YAML defaults, because pint reads ``deg`` and ``%`` as both
dimensionless and ``"2 %"`` would pass as an angle.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

#: Rules whose findings are stored at ingest (qc.md §4.1). They take
#: ``severity`` and ``enabled`` only. ``V*`` stands for every python-ags4 rule.
INGEST_RULES = (
    "V*",
    "VLOG",
    "V000",
    "M001",
    "U001",
    "U002",
    "U003",
    "U004",
    "U005",
    "T001",
)

#: Quantity kind of each threshold, by rule (P00 quantity kinds).
THRESHOLDS: dict[str, dict[str, str]] = {
    "L004": {"inclination_tolerance": "angle"},
    "L005": {
        "ground_level_difference": "length",
        "neighbor_count": "count",
        "fewest_neighbors": "count",
        "search_radius": "length",
    },
    "G002": {"depth_tolerance": "length"},
    "G003": {"depth_tolerance": "length"},
    "D003": {"final_depth_tolerance": "length"},
    "D007": {"depth_tolerance": "length"},
    "S002": {"highest_spt_n": "count"},
    "S005": {"n60_tolerance": "count"},
    "A002": {"plasticity_index_tolerance": "percent"},
    "A003": {"lowest_liquid_limit": "percent", "highest_liquid_limit": "percent"},
    "P001": {"percent_passing_tolerance": "percent"},
    "P003": {"fraction_sum_tolerance": "percent"},
    "P004": {"fewest_points": "count"},
    "K001": {
        "lowest_hydraulic_conductivity": "hydraulic_conductivity",
        "highest_hydraulic_conductivity": "hydraulic_conductivity",
    },
}


@dataclass(frozen=True)
class Finding:
    """One QC finding, before its severity is applied (qc.md §5.1).

    ``line`` is the DATA line the finding is about. ``loca_id``, ``depth`` (in
    m) and ``value`` are filled from that line when not given.
    """

    rule_id: str
    message: str
    group: str | None = None
    heading: str | None = None
    line: int | None = None
    loca_id: str | None = None
    depth: float | None = None
    value: str | None = None


@dataclass
class RuleResult:
    """What a rule returns: its findings and how many records it looked at."""

    findings: list[Finding] = field(default_factory=list)
    records_checked: int = 0


#: Rule functions by rule ID, in the order they were registered.
RULES: dict[str, Callable[..., RuleResult]] = {}


def rule(
    rule_id: str,
) -> Callable[[Callable[..., RuleResult]], Callable[..., RuleResult]]:
    """Register ``(data, settings) -> RuleResult`` as the check for ``rule_id``."""

    def register(function: Callable[..., RuleResult]) -> Callable[..., RuleResult]:
        if rule_id in RULES:
            raise ValueError(f"QC rule {rule_id} is registered twice.")
        RULES[rule_id] = function
        return function

    return register
