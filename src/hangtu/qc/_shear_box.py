"""Shear box rules H (qc.md §4.14, M17 a).

Each checks one stage. ``S`` (SPT) is taken. ``SHBT_PVST`` or ``SHBT_RVST``
far from ``SHBT_NORM`` isn't a rule: they differ where the lab corrects for
the contact area, and no source gives a threshold.
"""

from hangtu.qc._data import Data
from hangtu.qc._registry import Finding, RuleResult, rule
from hangtu.qc._settings import RuleSettings
from hangtu.qc._tests import SLACK, _unflagged, _value, _where


def _at(row: dict, data: Data) -> str:
    """``in BH1 at 1.10 m (3.61 ft), stage 2``: where a stage is."""
    text = _where(row, data, "SHBT", "SPEC_DPTH")
    if row.get("SHBT_TESN") not in (None, ""):
        text += f", stage {row['SHBT_TESN']}"
    return text


@rule("H001")
def residual_above_peak(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("SHBT", "SHBT_PEAK", "SHBT_RES"):
        return RuleResult()
    shbt = data.table("SHBT")
    rows = shbt[_unflagged(data, "SHBT", shbt, "SHBT_PEAK", "SHBT_RES")]
    findings = [
        Finding(
            "H001",
            f"{_value(data, 'SHBT', 'SHBT_RES', row['SHBT_RES'])} {_at(row, data)} "
            f"is above the peak, {_value(data, 'SHBT', 'SHBT_PEAK', row['SHBT_PEAK'])}"
            ". The peak is the largest shear stress of the stage, so the two are "
            "usually swapped: check the lab's sheet.",
            group="SHBT",
            heading="SHBT_RES",
            line=row["_line"],
        )
        for row in rows.to_dict("records")
        if row["SHBT_RES"] > row["SHBT_PEAK"] + SLACK
    ]
    return RuleResult(findings, len(rows))


@rule("H002")
def no_shear_stress(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("SHBT"):
        return RuleResult()
    shbt = data.table("SHBT")
    blank = data.blank("SHBT", "SHBT_PEAK") if data.has("SHBT", "SHBT_PEAK") else None
    blank_residual = (
        data.blank("SHBT", "SHBT_RES") if data.has("SHBT", "SHBT_RES") else None
    )
    findings = []
    for i, row in zip(shbt.index, shbt.to_dict("records"), strict=True):
        no_peak = blank is None or blank[i]
        no_residual = blank_residual is None or blank_residual[i]
        if no_peak and no_residual:
            findings.append(
                Finding(
                    "H002",
                    f"The shear box stage {_at(row, data)} has neither SHBT_PEAK nor "
                    "SHBT_RES, so it gives no point for a peak or a residual fit. "
                    "Check that the file has the stage's results.",
                    group="SHBT",
                    heading=None,
                    line=row["_line"],
                )
            )
    return RuleResult(findings, len(shbt))


@rule("H003")
def normal_stress_not_positive(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("SHBT", "SHBT_NORM"):
        return RuleResult()
    shbt = data.table("SHBT")
    rows = shbt[_unflagged(data, "SHBT", shbt, "SHBT_NORM")]
    findings = [
        Finding(
            "H003",
            f"{_value(data, 'SHBT', 'SHBT_NORM', row['SHBT_NORM'])} {_at(row, data)} "
            "is 0 or less. A shear box stage is sheared under a compressive normal "
            "stress: check the value and its sign.",
            group="SHBT",
            heading="SHBT_NORM",
            line=row["_line"],
        )
        for row in rows.to_dict("records")
        if row["SHBT_NORM"] <= SLACK
    ]
    return RuleResult(findings, len(rows))
