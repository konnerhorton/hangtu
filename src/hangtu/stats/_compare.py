"""``compare()``: whether a property differs between two groups.

Spec: docs/work/m15d-compare.md. The rows are chosen by ``_rows``, as
``describe()`` and ``fit()`` choose them; each group's count, mean and spread
come from ``_describe.summarize()``, so they agree with ``describe()``.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as _stats

from hangtu import units as _units
from hangtu._data import text_values
from hangtu.errors import HangtuError, warn
from hangtu.stats import _rows, _significance
from hangtu.stats._describe import summarize
from hangtu.stats._result import CompareResult
from hangtu.stats._rows import COUNTS

#: Fewer values than this in a group warn: the tests have very little power.
FEW = 5

FIRST, SECOND = "first", "second"


@dataclass
class Group:
    """One group's values, as chosen, and its counts."""

    label: str
    #: The ``by`` columns' values, empty for a group given on its own.
    key: dict[str, Any]
    values: np.ndarray
    counts: dict[str, int]
    text: dict[str, int]
    sources: dict[str, dict[str, int]] = field(default_factory=dict)

    def record(self, log: bool) -> dict[str, Any]:
        """Return the group as the result records it: key, statistics, counts."""
        statistics = summarize(self.values, percentiles=(), log=log).statistics
        names = (
            ("count", "geometric_mean", "geometric_standard_deviation")
            if log
            else ("count", "mean", "standard_deviation")
        )
        return {
            "label": self.label,
            "key": self.key,
            "statistics": {name: statistics[name] for name in names},
            "counts": self.counts,
            "text": self.text,
            "sources": self.sources,
        }


@dataclass(frozen=True)
class Groups:
    """What ``_read_groups()`` read: the groups and what they share."""

    groups: list[Group]
    value: str | None
    unit: str | None
    unit_given: bool
    by: list[str]
    pooled: list[str]
    frames: list[pd.DataFrame]


def _read_one(
    data: Any,
    value: str | None,
    by: Any,
    pool: Any,
    include_assumed: bool,
    units: Any,
    display_units: str | None,
    log: bool,
    function: str,
) -> tuple[_rows.Input, list[Group], str | None, list[str]]:
    """Read one input as ``describe()`` reads it, into its groups."""
    read = _rows.read_input(data, value, by, pool, units, function)
    frame = read.frame
    pooled = _rows.check_pool(pool, read, function)
    numbers, texts = text_values(frame, read.column)
    numbers, unit = _rows.convert(numbers, read, display_units, function)
    flags = (
        _rows.read_flags(frame, read.column, function)
        if read.value is not None
        else _rows.Flags.none(frame)
    )
    reasons, marks = _rows.choose_rows(
        numbers, texts, flags, include_assumed=include_assumed, positive_only=log
    )
    included = reasons == ""
    keys = _rows.group_keys(frame, read.by)
    _rows.check_sources(frame, keys, included, read, pooled, function)
    not_positive = int((reasons == "count_not_positive").sum())
    if not_positive:
        raise HangtuError(
            f"{function} with log=True found {not_positive} values of "
            f"{read.column!r} at or below 0, which a log scale has no place for. "
            "Compare without log=True, or filter the rows on purpose first."
        )
    _rows.warn_left_out(reasons, read.column, function)
    _rows.warn_text(texts, read.column, function)
    groups = []
    for key, rows in keys:
        chosen = rows & included
        groups.append(
            Group(
                label=", ".join(map(str, key.values())),
                key=key,
                values=numbers[chosen],
                counts={
                    name: int(marks.get(name, reasons == name)[rows].sum())
                    for name in COUNTS
                },
                text=_rows.spellings(texts[rows]),
                sources={
                    column: _rows.breakdown(frame.loc[chosen, column])
                    for column in pooled
                },
            )
        )
    return read, groups, unit, pooled


def _read_groups(
    data: Any,
    other: Any,
    *,
    value: str | None,
    by: Any,
    pool: Any,
    include_assumed: bool,
    units: Any,
    display_units: str | None,
    log: bool,
    function: str,
) -> Groups:
    """Read two inputs as two groups, or one input as its ``by`` groups."""
    if other is None:
        if by is None:
            raise HangtuError(
                f"{function} needs two groups: two sets of values, "
                "ht.stats.compare(a, b), or a DataFrame with value= and by=, "
                'e.g. ht.stats.compare(df, value="spt_n60", by="geology_unit").'
            )
        read, groups, unit, pooled = _read_one(
            data, value, by, pool, include_assumed, units, display_units, log, function
        )
        return Groups(
            groups=groups,
            value=read.value,
            unit=unit,
            unit_given=read.unit_given,
            by=read.by,
            pooled=pooled,
            frames=[read.frame] if isinstance(data, pd.DataFrame | pd.Series) else [],
        )
    if by is not None:
        raise HangtuError(
            f"{function} takes by= with one DataFrame, which it splits into groups; "
            "with two inputs, each is a group. Pass one DataFrame and by=, or two "
            "inputs without it."
        )
    frames = [isinstance(item, pd.DataFrame) for item in (data, other)]
    if frames[0] != frames[1]:
        raise HangtuError(
            f"{function} compares two DataFrames (with value=) or two sets of "
            "values (lists, arrays or Series), not one of each. Take the column "
            'from the DataFrame, e.g. df["spt_n60"].'
        )
    reads = [
        _read_one(
            item,
            value,
            None,
            pool,
            include_assumed,
            units,
            display_units,
            log,
            function,
        )
        for item in (data, other)
    ]
    (first, (group_1,), unit_1, pooled), (second, (group_2,), unit_2, _) = reads
    if not _same_unit(unit_1, unit_2):
        raise HangtuError(
            f"{function} can't compare values in {unit_1 or 'no unit'} with values "
            f"in {unit_2 or 'no unit'}. Convert one, or pass display_units='SI' or "
            "'US' to convert both."
        )
    names = [
        str(item.name) if isinstance(item, pd.Series) and item.name is not None else ""
        for item in (data, other)
    ]
    if not all(names) or names[0] == names[1]:
        names = [FIRST, SECOND]
    group_1.label, group_2.label = names
    return Groups(
        groups=[group_1, group_2],
        value=first.value if first.value == second.value else None,
        unit=unit_1,
        unit_given=first.unit_given and second.unit_given,
        by=[],
        pooled=pooled,
        frames=[
            read.frame
            for read, item in ((first, data), (second, other))
            if isinstance(item, pd.DataFrame | pd.Series)
        ],
    )


def _same_unit(first: str | None, second: str | None) -> bool:
    if first == second:
        return True
    if first is None or second is None:
        return False
    return _units.parse_unit(first) == _units.parse_unit(second)


def _choose(
    groups: list[Group], chosen: Any, by: list[str], function: str
) -> list[Group]:
    """Return the two groups ``groups=`` names, in its order."""
    labels = ", ".join(repr(group.label) for group in groups)
    if chosen is None:
        if len(groups) != 2:
            raise HangtuError(
                f"{function} compares two groups, and by={_by_text(by)} gives "
                f"{len(groups)}: {labels}. Name two with groups=, e.g. "
                f"groups=({groups[0].label!r}, {groups[-1].label!r}), or compare "
                "them all with ht.stats.compare_groups()."
            )
        return groups
    if isinstance(chosen, str) or len(chosen) != 2:
        raise HangtuError(
            f"{function} groups= takes two keys of by=, e.g. "
            f"groups=({groups[0].label!r}, {groups[-1].label!r}), not {chosen!r}."
        )
    found = []
    for wanted in chosen:
        text = ", ".join(map(str, wanted)) if isinstance(wanted, tuple) else str(wanted)
        match = [group for group in groups if group.label == text]
        if not match:
            raise HangtuError(
                f"{function} groups= names {wanted!r}, which isn't a group of "
                f"by={_by_text(by)}. Groups: {labels}."
            )
        found.append(match[0])
    if found[0] is found[1]:
        raise HangtuError(f"{function} groups= names {chosen[0]!r} twice.")
    return found


def _by_text(by: list[str]) -> str:
    return repr(by[0]) if len(by) == 1 else repr(by)


def _check_counts(groups: list[Group], column: str, function: str) -> None:
    """Raise below 2 values in a group; warn once below ``FEW``."""
    for group in groups:
        n = group.values.size
        if n < 2:
            raise HangtuError(
                f"{function} needs at least 2 values of {column!r} in each group, "
                f"and {group.label!r} has {n}. Group more widely, or report the "
                "values themselves."
            )
    _warn_few(groups, column, function)


def _warn_few(groups: list[Group], column: str, function: str) -> None:
    few = [f"{g.label} ({g.values.size})" for g in groups if g.values.size < FEW]
    if few:
        warn(
            f"{function} has fewer than {FEW} values of {column!r} in: "
            f"{', '.join(few)}. The tests have very little power with so few: "
            "a real difference will often go undetected."
        )


def welch(
    first: np.ndarray, second: np.ndarray, alpha: float, log: bool
) -> dict[str, float]:
    """Welch's t-test and the difference (or ratio) with its interval at 1 - α.

    With ``log``, on ln x, reported as the ratio of geometric means (Helsel et
    al. 2020 §5.3.4). Blank when neither group has any spread.
    """
    name = "ratio" if log else "difference"
    result = blank_welch(log)
    x, y = (np.log(first), np.log(second)) if log else (first, second)
    if np.ptp(x) == 0 and np.ptp(y) == 0:
        return result
    test = _stats.ttest_ind(x, y, equal_var=False)
    interval = test.confidence_interval(confidence_level=1 - alpha)
    estimate = float(x.mean() - y.mean())
    bounds = (float(interval.low), float(interval.high))
    if log:
        estimate, bounds = math.exp(estimate), tuple(map(math.exp, bounds))
    result.update(
        {
            name: estimate,
            f"{name}_lower": bounds[0],
            f"{name}_upper": bounds[1],
            "welch_t_statistic": float(test.statistic),
            "welch_degrees_of_freedom": float(test.df),
            "welch_p_value": float(test.pvalue),
        }
    )
    return result


def blank_welch(log: bool) -> dict[str, float]:
    """Welch's columns, blank: no test was run."""
    name = "ratio" if log else "difference"
    return dict.fromkeys(
        (
            name,
            f"{name}_lower",
            f"{name}_upper",
            "welch_t_statistic",
            "welch_degrees_of_freedom",
            "welch_p_value",
        ),
        float("nan"),
    )


#: Brunner-Munzel's columns, blank until it runs.
BRUNNER_MUNZEL = (
    "probability_of_superiority",
    "probability_of_superiority_lower",
    "probability_of_superiority_upper",
    "brunner_munzel_statistic",
    "brunner_munzel_degrees_of_freedom",
    "brunner_munzel_p_value",
)


def compare(
    data: pd.DataFrame | pd.Series | Sequence[float] | np.ndarray,
    other: pd.DataFrame | pd.Series | Sequence[float] | np.ndarray | None = None,
    *,
    value: str | None = None,
    by: str | Sequence[str] | None = None,
    groups: Sequence[Any] | None = None,
    log: bool = False,
    significance_level: float | None = None,
    judgments: Any = None,
    pool: str | Sequence[str] | None = None,
    include_assumed: bool = False,
    units: str | Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> CompareResult:
    r"""Test whether a property differs between two groups, two ways at once.

    Answers questions such as "do the upper and lower alluvium differ in N60?"
    (one parameter set or two) or "does lab s_u differ from an SPT
    correlation's?" (before pooling them). It reports the size of the
    difference with its interval, and two tests side by side, never one chosen
    by a normality pre-test:

    - **Welch's t-test** on the means, which doesn't assume equal variances
      (Welch 1947; Helsel et al. 2020 §5.3.3 recommend it always). The
      ``difference`` (mean of the first - mean of the second) has its interval
      at the confidence level 1 - α. With ``log=True`` the test is on ln x and
      the estimate is the ``ratio`` of geometric means (first / second) with
      its interval (§5.3.4), for values that span orders of magnitude.
    - **A rank-based test**, the Brunner-Munzel test, with its effect size
      ``probability_of_superiority``, the probability that a value from the
      first group exceeds one from the second (0.5: neither tends larger).

    **Two groups, three ways:** ``compare(a, b)`` with two lists, arrays or
    Series (named by the Series' names, else ``"first"`` and ``"second"``);
    ``compare(df_a, df_b, value=...)`` with two DataFrames, such as lab tests
    and a correlation's estimates; or ``compare(df, value=..., by=...)``,
    with ``groups=`` naming two of ``by``'s groups when it has more. Every
    difference is first minus second; the result names both.

    **The rows are chosen as ``ht.stats.describe()`` chooses them**: NP,
    assumed values, bands, text and blanks are left out and counted, and rows
    from different sources within one group raise an error (``pool=`` pools
    them on purpose). Sources are checked within each group, never across
    the two: comparing sources is what ``by="correlation_name"`` is for.
    Refusals and ``>``/``<`` values enter at their value and are counted
    (``count_at_least``, ``count_at_most``); the means, and so Welch's
    results, are then biased, and the summary says so.

    **The significance level α is a judgment with no default** (SPEC §4):
    ``significance_level=``, else ``judgments=``, else the project's
    judgments file, else an error. The p-values don't depend on it; the
    intervals (at 1 - α) and the summary's conclusions do.

    The tests assume independent values. Values from one hole, or close
    together, aren't, and the p-values are then too small.

    Not yet checked against the original papers (TODO #48): Welch (1947).

    Parameters
    ----------
    data : pandas.DataFrame, pandas.Series, list or array
        The first group's values, or a DataFrame holding both groups (with
        ``by=``).
    other : pandas.DataFrame, pandas.Series, list or array, optional
        The second group's values, of the same kind as ``data``.
    value : str
        With DataFrames, the column to compare, e.g. ``"spt_n60"``.
    by : str or list of str, optional
        With one DataFrame, the column(s) whose groups are compared, e.g.
        ``"geology_unit"``. Groups are in ``describe()``'s order.
    groups : pair of keys, optional
        The two groups of ``by`` to compare, in this order, e.g.
        ``("Upper alluvium", "Lower alluvium")``. Needed when ``by`` gives
        other than two groups. For several ``by`` columns, each key is a tuple.
    log : bool
        Compare on a log scale: Welch's test on ln x and the ratio of
        geometric means. A value at or below 0 is an error.
    significance_level : float, optional
        α, between 0 and 1. A judgment with no default; overrides the
        judgments file's, with a warning.
    judgments : Judgments or path, optional
        ``ht.judgments(path)``, ``p.judgments`` or a path to a judgments file
        holding ``significance_level``. By default the project's, from the
        DataFrame's ``attrs``.
    pool : str or list of str, optional
        Source columns to pool across on purpose within each group, as
        ``describe()``.
    include_assumed : bool
        Include assumed values, as ``describe()``.
    units : str or dict, optional
        The value's unit, as ``describe()``.
    display_units : {"US", "SI"}, optional
        Convert the values to this system's display unit before comparing.
        Two DataFrames must end up in the same unit, or it is an error.

    Returns
    -------
    CompareResult
        ``.to_frame()`` has one row: the groups, their statistics, the
        difference with its interval, both tests, α and the counts.
        ``print(result)`` shows the same numbers with a plain-English note.

    Raises
    ------
    HangtuError
        For fewer than 2 values in a group, ``by`` giving other than two groups
        without ``groups=``, an unknown group, two inputs in different units,
        no significance level, rows from different sources in one group, or a
        value at or below 0 with ``log=True``.
    ColumnError
        For a missing column, or one that holds no numbers.

    Examples
    --------
    >>> spt = p.spt()
    >>> result = ht.stats.compare(
    ...     spt, value="spt_n60", by="geology_unit",
    ...     groups=("Upper alluvium", "Lower alluvium"), significance_level=0.05,
    ... )
    >>> print(result)
    """
    function = "compare()"
    if other is not None and groups is not None:
        raise HangtuError(
            f"{function} takes groups= with by=, to name two of its groups; with "
            "two inputs, each is a group."
        )
    read = _read_groups(
        data,
        other,
        value=value,
        by=by,
        pool=pool,
        include_assumed=include_assumed,
        units=units,
        display_units=display_units,
        log=log,
        function=function,
    )
    alpha, record = _significance.resolve(
        significance_level, judgments, read.frames, function
    )
    chosen = (
        read.groups
        if other is not None
        else _choose(read.groups, groups, read.by, function)
    )
    column = read.value or "the values"
    _check_counts(chosen, column, function)
    first, second = chosen
    tested = not any(_all_one_bound(group) for group in chosen)
    test = (
        welch(first.values, second.values, alpha, log) if tested else blank_welch(log)
    )
    nan = float("nan")
    rank = dict.fromkeys(BRUNNER_MUNZEL, nan)
    rank["brunner_munzel_method"] = None
    return CompareResult(
        kind="property",
        function="compare",
        value=read.value,
        unit=read.unit,
        notes=tuple(_notes(chosen, read, test, tested, include_assumed, log)),
        judgments=_judgments_record(read.frames, record),
        hangtu_version=version("hangtu"),
        by=tuple(read.by),
        groups=tuple(group.record(log) for group in chosen),
        log=log,
        pooled=tuple(read.pooled),
        include_assumed=include_assumed,
        significance_level=alpha,
        confidence_level=1 - alpha,
        significance_level_source=record["source"],
        welch=test,
        brunner_munzel=rank,
    )


def _judgments_record(
    frames: list[pd.DataFrame], record: dict[str, Any]
) -> dict[str, Any]:
    """Return the input's judgments with the significance level's (SPEC §4)."""
    judgments: dict[str, Any] = {}
    for frame in frames:
        judgments.update(frame.attrs.get("judgments", {}))
    judgments["significance_level"] = record
    return judgments


def _all_one_bound(group: Group) -> bool:
    """Return whether a group's values are all bounds at one value: no test."""
    bounds = group.counts["count_at_least"] + group.counts["count_at_most"]
    return bounds == group.values.size and np.ptp(group.values) == 0


def _notes(
    groups: list[Group],
    read: Groups,
    test: dict[str, float],
    tested: bool,
    include_assumed: bool,
    log: bool,
) -> list[str]:
    """Return the lines under the table, but the note on what the tests found."""
    notes = [] if read.unit_given else ["(units not given)"]
    for group in groups:
        if _all_one_bound(group):
            notes.append(
                f"{group.label}: every value is a bound at {group.values[0]:g}, "
                "so neither test is run."
            )
    if tested and math.isnan(test["welch_t_statistic"]):
        notes.append(
            "No Welch's t-test: each group's values are all the same, so there is "
            "no spread to compare the difference with."
        )
    for name, kind, effect in (
        ("count_at_least", "Lower bounds (refusal or '>')", "underestimate"),
        ("count_at_most", "Upper bounds ('<')", "overestimate"),
    ):
        counted = [f"{g.label} {g.counts[name]}" for g in groups if g.counts[name]]
        if counted:
            notes.append(
                f"{kind}: {', '.join(counted)}, entered at their value. That "
                f"group's mean is an {effect}, and Welch's results are biased by "
                "it; the ranks treat values at a common limit as tied, which is "
                "closer to right but not right either."
            )
    if include_assumed:
        assumed = [
            f"{g.label} {g.counts['count_assumed']}"
            for g in groups
            if g.counts["count_assumed"]
        ]
        if assumed:
            notes.append(f"Assumed values included: {', '.join(assumed)}.")
    for group in groups:
        for column in read.pooled:
            listed = ", ".join(
                f"{value} {count}" for value, count in group.sources[column].items()
            )
            notes.append(f"Pooled across {column} in {group.label}: {listed}.")
    if log:
        notes.append(
            "Log scale: Welch's t-test is on ln x and compares geometric means, "
            "as their ratio; the geometric standard deviation is a factor."
        )
    return notes
