"""The plain-English note on what the tests found (m15d-compare, Decision 9).

It never says two groups are the same: it says the data don't show a
difference at α, with the interval for scale. When the two tests disagree,
it says what usually causes it and points to the values.
"""

import math
from typing import Any

#: Always in the note: what the p-values rest on.
INDEPENDENCE = (
    "Both tests assume independent values. Values from one hole, or from close "
    "together, aren't, and the p-values are then too small; hangtu doesn't yet "
    "account for it."
)
LOOK = "Look at the values (P07)."


def _p(value: float) -> str:
    from hangtu.plot._overlays import format_number  # plot imports stats

    return format_number(value)


def _means(log: bool) -> str:
    return "geometric means" if log else "means"


def welch_finding(
    p: float, alpha: float, first: str, second: str, estimate: float, log: bool
) -> str:
    """Say what Welch's test found at α, in words."""
    means = _means(log)
    if p < alpha:
        higher = first if (estimate > 1 if log else estimate > 0) else second
        return (
            f"Welch's t-test finds the {means} differ, {higher}'s higher (p = {_p(p)})."
        )
    return f"Welch's t-test doesn't find that the {means} differ (p = {_p(p)})."


def rank_finding(
    p: float, alpha: float, first: str, second: str, p_hat: float, test: str
) -> str:
    """Say what a rank test found at α, in words."""
    if p < alpha:
        above, below = (first, second) if p_hat > 0.5 else (second, first)
        return (
            f"The {test} test finds that values in {above} tend to exceed those "
            f"in {below} (p = {_p(p)})."
        )
    return (
        f"The {test} test doesn't find that values in {first} tend to exceed "
        f"those in {second}, or the reverse (p = {_p(p)})."
    )


def agreement(
    welch_differs: bool,
    rank_differs: bool,
    first: str,
    second: str,
    welch: dict[str, float],
    p_hat: float,
    unit: str | None,
    log: bool,
    level: str,
) -> str:
    """Say whether the two tests agree, and what that does and doesn't mean."""
    name = "ratio" if log else "difference"
    unit_text = f" {unit}" if unit and not log else ""
    low, high = welch[f"{name}_lower"], welch[f"{name}_upper"]
    what = (
        f"ratio of geometric means, {first} / {second},"
        if log
        else f"difference in means, {first} - {second},"
    )
    if welch_differs and rank_differs:
        superiority = (
            ""
            if math.isnan(p_hat)
            else f"; a value in {first} exceeds one in {second} with probability "
            f"{_p(p_hat)}"
        )
        return (
            f"Both tests find a difference: the {what} is {_p(welch[name])}{unit_text} "
            f"({level} interval {_p(low)} to {_p(high)}{unit_text}){superiority}."
        )
    if not welch_differs and not rank_differs:
        return (
            "This doesn't show the groups are the same: the "
            f"{what} could be anywhere from {_p(low)} to {_p(high)}{unit_text} "
            f"({level} interval)."
        )
    if welch_differs:
        return (
            f"The two tests disagree: the {_means(log)} differ but neither group's "
            "values tend to exceed the other's. This is often one or two extreme "
            f"values moving a mean. {LOOK}"
        )
    above, below = (first, second) if p_hat > 0.5 else (second, first)
    hint = "" if log else " log=True compares geometric means, which they move less."
    return (
        f"The two tests disagree: values in {above} tend to exceed those in "
        f"{below} but the {_means(log)} don't clearly differ. This is often a "
        f"skewed group or an extreme value widening the spread.{hint} {LOOK}"
    )


def compare_note(
    first: str,
    second: str,
    welch: dict[str, float],
    rank: dict[str, Any],
    alpha: float,
    confidence: str,
    unit: str | None,
    log: bool,
) -> list[str]:
    """Return ``compare()``'s note: each finding, their agreement, independence."""
    lines = []
    name = "ratio" if log else "difference"
    welch_p = welch["welch_p_value"]
    rank_p = rank["brunner_munzel_p_value"]
    p_hat = rank["probability_of_superiority"]
    if not math.isnan(welch_p):
        lines.append(welch_finding(welch_p, alpha, first, second, welch[name], log))
    if not math.isnan(rank_p):
        lines.append(
            rank_finding(rank_p, alpha, first, second, p_hat, "Brunner-Munzel")
        )
    if not math.isnan(welch_p) and not math.isnan(rank_p):
        lines.append(
            agreement(
                welch_p < alpha,
                rank_p < alpha,
                first,
                second,
                welch,
                p_hat,
                unit,
                log,
                confidence,
            )
        )
    lines.append(INDEPENDENCE)
    return lines


def _overall(
    overall: dict[str, float], alpha: float, log: bool
) -> tuple[list[str], bool | None, bool | None]:
    """Say what the overall tests found; return whether each finds a difference."""
    lines = []
    means = _means(log)
    welch_p = overall["welch_p_value"]
    rank_p = overall["kruskal_wallis_p_value"]
    welch = rank = None
    if not math.isnan(welch_p):
        welch = welch_p < alpha
        lines.append(
            f"Welch's ANOVA finds the {means} differ among the groups "
            f"(p = {_p(welch_p)})."
            if welch
            else f"Welch's ANOVA doesn't find that the {means} differ among the "
            f"groups (p = {_p(welch_p)})."
        )
    if not math.isnan(rank_p):
        rank = rank_p < alpha
        lines.append(
            "The Kruskal-Wallis test finds that values in some group tend to be "
            f"higher or lower than in the others (p = {_p(rank_p)})."
            if rank
            else "The Kruskal-Wallis test doesn't find that values in any group "
            f"tend to be higher or lower than in the others (p = {_p(rank_p)})."
        )
    return lines, welch, rank


def groups_note(
    overall: dict[str, float],
    pairs: list[dict[str, Any]],
    alpha: float,
    confidence: str,
    log: bool,
) -> list[str]:
    """Return ``compare_groups()``'s note: overall tests, pairs that disagree."""
    lines, welch, rank = _overall(overall, alpha, log)
    means = _means(log)
    if welch is not None and rank is not None:
        if welch and not rank:
            lines.append(
                f"The two overall tests disagree: the {means} differ but no "
                "group's values tend to be higher or lower. This is often one or "
                f"two extreme values moving a mean. {LOOK}"
            )
        elif rank and not welch:
            hint = "" if log else " log=True compares geometric means."
            lines.append(
                "The two overall tests disagree: some group's values tend to be "
                f"higher or lower but the {means} don't clearly differ. This is "
                f"often a skewed group or an extreme value widening the spread."
                f"{hint} {LOOK}"
            )
        elif not welch and not rank:
            lines.append(
                "This doesn't show the groups are the same: each pair's "
                f"{'ratio' if log else 'difference'} and its {confidence} "
                "interval give the scale."
            )
    for pair in pairs:
        first, second = pair["group_1"], pair["group_2"]
        welch_p, dunn_p = pair["games_howell_p_value"], pair["dunn_p_value"]
        if math.isnan(welch_p) or (welch_p < alpha) == (dunn_p < alpha):
            continue
        if welch_p < alpha:
            lines.append(
                f"{first} and {second}: Games-Howell finds the {means} differ "
                f"(p = {_p(welch_p)}) but Dunn's test doesn't find that either "
                f"group's values tend to be higher (p = {_p(dunn_p)}). This is "
                f"often one or two extreme values moving a mean. {LOOK}"
            )
        else:
            above, below = (
                (first, second) if pair["dunn_z_statistic"] > 0 else (second, first)
            )
            hint = "" if log else " log=True compares geometric means."
            lines.append(
                f"{first} and {second}: Dunn's test finds values in {above} tend "
                f"to exceed those in {below} (p = {_p(dunn_p)}) but Games-Howell "
                f"doesn't find the {means} differ (p = {_p(welch_p)}). This is "
                "often a skewed group or an extreme value widening the spread."
                f"{hint} {LOOK}"
            )
    lines.append(INDEPENDENCE)
    return lines
