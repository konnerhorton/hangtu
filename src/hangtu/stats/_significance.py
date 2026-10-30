"""The significance level α: a judgment with no default (SPEC §4).

Spec: docs/work/m15d-compare.md, Decision 8. ``compare()`` and
``compare_groups()`` resolve it here: the argument, then ``judgments=``, then
the Project's file a DataFrame input carries, else an error naming it.
"""

import math
from collections.abc import Sequence
from numbers import Real
from typing import Any

import pandas as pd

from hangtu import _judgments
from hangtu.analysis._judgment_values import read_judgments
from hangtu.errors import HangtuError, warn

NAME = "significance_level"
ENTRY = (
    "significance_level:\n"
    '  project: {significance_level: 0.05, reason: "the usual convention"}'
)


def resolve(
    argument: Any, judgments: Any, frames: Sequence[pd.DataFrame], function: str
) -> tuple[float, dict[str, Any]]:
    """Return α and its record: the value, its source and, from a file, its reason."""
    carrier = next(
        (frame for frame in frames if "judgments_file" in frame.attrs), pd.DataFrame()
    )
    read = read_judgments(judgments, carrier)
    in_file = read is not None and NAME in read.judgments
    if argument is not None:
        alpha = _check(argument)
        if in_file:
            warn(f"significance_level= replaces the one in {read.path.name}.")
        return alpha, {NAME: alpha, "source": "argument"}
    if not in_file:
        raise HangtuError(_missing(read, bool(frames), function))
    entry = read.judgments[NAME].project
    alpha = entry.values[NAME]
    return alpha, {
        NAME: alpha,
        "source": str(read.path),
        "sha256": read.sha256,
        "reason": entry.reason,
    }


def _check(argument: Any) -> float:
    if (
        isinstance(argument, bool)
        or not isinstance(argument, Real)
        or not math.isfinite(argument)
        or not 0 < argument < 1
    ):
        raise HangtuError(
            "significance_level= must be a number between 0 and 1, e.g. 0.05, "
            f"not {argument!r}."
        )
    low, high, outside = _judgments.PLAUSIBLE[NAME]
    if not low <= argument <= high:
        warn(
            f"significance_level= {argument:g} is outside {low:g}-{high:g}. "
            f"Check the value: {outside}."
        )
    return float(argument)


def _missing(read: Any, frames: bool, function: str) -> str:
    why = (
        f"{function} tests at the significance level, a judgment with no default "
        "(SPEC §4): 0.05 is a convention, not a law, so set it on purpose."
    )
    if read is not None:
        return (
            f"{why} The judgments file {str(read.path)!r} has no significance_level. "
            f"Add it:\n{ENTRY}\nor give it in the call, significance_level=0.05."
        )
    hint = (
        "\nIf the data came from a Project dataset, merge and concat drop "
        "df.attrs: pass judgments=p.judgments."
        if frames
        else ""
    )
    return (
        f"{why} Give it in the call, significance_level=0.05, or in a judgments "
        f"file:\n{ENTRY}\nand pass judgments=ht.judgments(path), or set it on the "
        f"project with p.set_judgments(path).{hint}"
    )
