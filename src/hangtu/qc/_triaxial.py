"""Triaxial rules X (qc.md §4.12, M11 a).

Each checks one stage, or one test against its own stages: a record that can't
give a valid failure state, or doesn't meet its test standard's own
requirement. Plausible ranges for strength are level 2. A stage's test type is
its test's (``TREG_TYPE`` or ``TRIG_TYPE``), joined by ``specimen_id``.
"""

import pandas as pd

from hangtu.analysis._triaxial import EXTENSION, LISTED, MULTISTAGE, UNDRAINED
from hangtu.qc import _text
from hangtu.qc._data import Data
from hangtu.qc._registry import Finding, RuleResult, rule
from hangtu.qc._settings import RuleSettings
from hangtu.qc._tests import SLACK, _unflagged, _value, _where

#: Each test group, its stage group and their headings for the test type and
#: the stage reference.
_TESTS = {"TREG": ("TRET", "TREG_TYPE"), "TRIG": ("TRIT", "TRIG_TYPE")}
_STAGES = {"TRET": ("TREG", "TRET_TESN"), "TRIT": ("TRIG", "TRIT_TESN")}


def _types(data: Data, stages: str) -> pd.Series:
    """Return the test type of each row of ``stages``, from its test, or None."""
    table = data.table(stages)
    test, _ = _STAGES[stages]
    heading = _TESTS[test][1]
    if not data.has(test, heading):
        return pd.Series(None, index=table.index, dtype=object)
    tests = data.table(test).dropna(subset=["specimen_id"])
    by_specimen = dict(zip(tests["specimen_id"], tests[heading], strict=True))
    types = table["specimen_id"].map(by_specimen).astype(object)
    return types.where(types.notna() & (types != ""), None)


def _stage(row: dict, data: Data, stages: str, test_type: str | None) -> str:
    """``in BH1 at 1.20 m, stage 1 of a CU test``: where a stage is."""
    _, tesn = _STAGES[stages]
    text = _where(row, data, stages, "SPEC_DPTH")
    if not pd.isna(row.get(tesn)) and row.get(tesn) != "":
        text += f", stage {row[tesn]}"
        text += f" of a {test_type} test" if test_type else ""
    elif test_type:
        text += f", a {test_type} test"
    return text


@rule("X001")
def saturation_below_standard(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("TRET", "TRET_BVAL"):
        return RuleResult()
    tret = data.table("TRET")
    rows = tret[_unflagged(data, "TRET", tret, "TRET_BVAL")]
    lowest = settings.thresholds["lowest_pore_pressure_parameter_b"]
    types = _types(data, "TRET")
    findings = [
        Finding(
            "X001",
            f"TRET_BVAL {data.text_at('TRET', row['_line'], 'TRET_BVAL')} "
            f"{_stage(row, data, 'TRET', types[i])}, is below {lowest.text}, the "
            "B-value commonly quoted for saturation before shearing (ASTM D4767, "
            "ISO 17892-9; not yet checked against the standards). Stiff soils may "
            "be accepted at a lower B-value where the standard allows it, so read "
            "the lab's remarks before accepting the finding.",
            group="TRET",
            heading="TRET_BVAL",
            line=row["_line"],
        )
        for i, row in zip(rows.index, rows.to_dict("records"), strict=True)
        if row["TRET_BVAL"] < lowest.value - SLACK
    ]
    return RuleResult(findings, len(rows))


@rule("X002")
def undrained_without_pore_pressure(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("TRET"):
        return RuleResult()
    tret = data.table("TRET")
    types = _types(data, "TRET")
    undrained = types.isin(UNDRAINED)
    blank = (
        data.blank("TRET", "TRET_PWPF")
        if data.has("TRET", "TRET_PWPF")
        else pd.Series(True, index=tret.index)
    )
    findings = [
        Finding(
            "X002",
            f"TRET_PWPF is blank {_stage(row, data, 'TRET', types[i])}. The test "
            "is undrained, so the stage has no effective stresses at failure and "
            "φ′ can't be fitted from it; p.triaxial() leaves them blank. Check the "
            "lab's sheet for the pore pressure at failure.",
            group="TRET",
            heading="TRET_PWPF",
            line=row["_line"],
        )
        for i, row in zip(tret.index, tret.to_dict("records"), strict=True)
        if undrained[i] and blank[i]
    ]
    return RuleResult(findings, int(undrained.sum()))


@rule("X003")
def deviator_stress_not_positive(data: Data, settings: RuleSettings) -> RuleResult:
    findings, checked = [], 0
    for stages in _STAGES:
        heading = f"{stages}_DEVF"
        if not data.has(stages, heading):
            continue
        table = data.table(stages)
        types = _types(data, stages)
        rows = table[_unflagged(data, stages, table, heading) & ~types.isin(EXTENSION)]
        checked += len(rows)
        findings += [
            Finding(
                "X003",
                f"{_value(data, stages, heading, row[heading])} "
                f"{_stage(row, data, stages, types[i])}, is 0 or less. A compression "
                "test can't fail at a deviator stress of 0 or less: check the value "
                "and its sign. p.triaxial() leaves the stage's principal stresses "
                "blank.",
                group=stages,
                heading=heading,
                line=row["_line"],
            )
            for i, row in zip(rows.index, rows.to_dict("records"), strict=True)
            if row[heading] <= SLACK
        ]
    return RuleResult(findings, checked)


@rule("X004")
def negative_effective_stress(data: Data, settings: RuleSettings) -> RuleResult:
    if not data.has("TRET", "TRET_PWPF", "TRET_CELL"):
        return RuleResult()
    tret = data.table("TRET")
    rows = tret[_unflagged(data, "TRET", tret, "TRET_PWPF", "TRET_CELL")]
    types = _types(data, "TRET")
    findings = [
        Finding(
            "X004",
            f"{_value(data, 'TRET', 'TRET_PWPF', row['TRET_PWPF'])} "
            f"{_stage(row, data, 'TRET', types[i])}, is above "
            f"{_value(data, 'TRET', 'TRET_CELL', row['TRET_CELL'])}, which gives a "
            "negative σ′3 at failure: not possible in an uncemented saturated "
            "specimen. The usual cause is one of the two written with the back "
            "pressure taken off and the other without; check both.",
            group="TRET",
            heading="TRET_PWPF",
            line=row["_line"],
        )
        for i, row in zip(rows.index, rows.to_dict("records"), strict=True)
        if row["TRET_PWPF"] > row["TRET_CELL"] + SLACK
    ]
    return RuleResult(findings, len(rows))


@rule("X005")
def stages_dont_match_test(data: Data, settings: RuleSettings) -> RuleResult:
    findings, checked = [], 0
    for test, (stages, heading) in _TESTS.items():
        if not data.has(test):
            continue
        tests = data.table(test)
        counts = (
            data.table(stages)["specimen_id"].value_counts()
            if data.has(stages)
            else pd.Series(dtype=int)
        )
        checked += len(tests)
        for row in tests.to_dict("records"):
            count = int(counts.get(row["specimen_id"], 0))
            test_type = row.get(heading)
            test_type = None if pd.isna(test_type) or test_type == "" else test_type
            where = _where(row, data, test, "SPEC_DPTH")
            named = f" ({test_type})" if test_type else ""
            if count == 0:
                message = (
                    f"{test}{named} {where} has no {stages} rows, so it gives no "
                    f"failure state. Check that the file has the test's stages."
                )
            elif test_type in MULTISTAGE and count == 1:
                message = (
                    f"{heading} {test_type} {where} is a multistage test, but it "
                    f"has one {stages} row. Check the test type and the stages."
                )
            elif test_type in LISTED - MULTISTAGE and count > 1:
                message = (
                    f"{heading} {test_type} {where} is a single-stage test, but it "
                    f"has {count} {stages} rows. Check the test type (a multistage "
                    "test has its own type) and the stages."
                )
            else:
                continue
            findings.append(
                Finding(
                    "X005",
                    message,
                    group=test,
                    heading=None if count == 0 else heading,
                    line=row["_line"],
                )
            )
    return RuleResult(findings, checked)


@rule("X006")
def consolidation_stress_differs(data: Data, settings: RuleSettings) -> RuleResult:
    headings = ("TRET_CONP", "TRET_CELL", "TRET_BACK")
    if not data.has("TRET", *headings):
        return RuleResult()
    tret = data.table("TRET")
    # Later stages change the cell pressure after consolidation, so only each
    # specimen's first stage (in file order) is checked.
    first = ~tret["specimen_id"].duplicated() | tret["specimen_id"].isna()
    rows = tret[first & _unflagged(data, "TRET", tret, *headings)]
    tolerance = settings.thresholds["consolidation_stress_tolerance"]
    types = _types(data, "TRET")
    findings = []
    for i, row in zip(rows.index, rows.to_dict("records"), strict=True):
        expected = row["TRET_CELL"] - row["TRET_BACK"]
        difference = abs(row["TRET_CONP"] - expected)
        if difference <= tolerance.value + SLACK:
            continue
        computed = _text.values(data, "TRET", "TRET_CONP", [expected])
        off = _text.values(data, "TRET", "TRET_CONP", [difference])
        findings.append(
            Finding(
                "X006",
                f"{_value(data, 'TRET', 'TRET_CONP', row['TRET_CONP'])} "
                f"{_stage(row, data, 'TRET', types[i])}, differs from TRET_CELL - "
                f"TRET_BACK = {computed} by {off}, more than "
                f"{_text.threshold(data, tolerance)}. The effective stress at the "
                "start of shearing is the cell pressure less the back pressure; "
                "check the three values.",
                group="TRET",
                heading="TRET_CONP",
                line=row["_line"],
            )
        )
    return RuleResult(findings, len(rows))
