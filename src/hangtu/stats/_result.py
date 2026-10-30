"""The results of the statistics functions (docs/work/m15a-describe.md, Decision 2)."""

import html
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from hangtu.errors import HangtuError


def _plain(value: Any) -> Any:
    """Make ``value`` JSON-serializable: NaN as None, NumPy scalars as Python."""
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(item) for item in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


@dataclass(frozen=True)
class _Result:
    """What every statistics result records: what it summarized, and from what."""

    #: ``"property"`` for test values, ``"parameter"`` for selected values (SPEC §5).
    kind: str
    #: The function that made the result, e.g. ``"describe"``.
    function: str
    #: The column summarized, or None for a list or array.
    value: str | None
    #: The unit of the statistics that have one, or None.
    unit: str | None
    #: The lines of the summary under the table.
    notes: tuple[str, ...]
    #: ``attrs["judgments"]`` of the input, when it carries them.
    judgments: dict[str, Any]
    hangtu_version: str

    def to_dict(self) -> dict[str, Any]:
        """Return every field, JSON-serializable (NaN as None)."""
        return _plain(asdict(self))


@dataclass(frozen=True, repr=False)
class DescribeResult(_Result):
    """The summary ``ht.stats.describe()`` returns.

    Use ``.to_frame()`` for a table with one row per group, ``.to_dict()``
    for a report, or ``print(result)`` to read it. The text is a view of the
    same numbers.
    """

    #: The columns grouped by, in order.
    by: tuple[str, ...]
    log: bool
    #: The source columns pooled on purpose (``pool=``).
    pooled: tuple[str, ...]
    include_assumed: bool
    #: The percentiles asked for.
    percentiles: tuple[float, ...]
    percentile_method: str
    #: One record per group: its key, statistics, counts and source breakdown.
    groups: tuple[dict[str, Any], ...]

    def to_frame(self) -> pd.DataFrame:
        """Return one row per group: the ``by`` columns, the statistics, the counts.

        ``attrs["units"]`` gives the unit of each statistic that has one.
        """
        rows = [
            {**group["key"], **group["statistics"], **group["counts"]}
            for group in self.groups
        ]
        frame = pd.DataFrame(rows, columns=[*self.by, *self._columns()])
        frame.attrs["units"] = (
            {}
            if self.unit is None
            else dict.fromkeys(self._statistics_with_unit(), self.unit)
        )
        return frame

    def _statistics(self) -> list[str]:
        return list(self.groups[0]["statistics"]) if self.groups else []

    def _counts(self) -> list[str]:
        return list(self.groups[0]["counts"]) if self.groups else []

    def _columns(self) -> list[str]:
        return [*self._statistics(), *self._counts()]

    def _statistics_with_unit(self) -> list[str]:
        unitless = {"count", "coefficient_of_variation", "geometric_standard_deviation"}
        return [name for name in self._statistics() if name not in unitless]

    def __str__(self) -> str:
        from hangtu.plot._overlays import format_number  # plot imports stats

        frame = self.to_frame()
        counts = [name for name in self._counts() if frame[name].any()]
        shown = [*self._statistics(), *counts]
        heading = ["", *(_heading(name) for name in shown)]
        rows = [heading]
        for _, row in frame.iterrows():
            label = ", ".join(str(row[column]) for column in self.by) or "All"
            rows.append(
                [
                    label,
                    *(
                        "—"
                        if pd.isna(row[name])
                        else str(int(row[name]))
                        if name == "count" or name.startswith("count_")
                        else format_number(float(row[name]))
                        for name in shown
                    ),
                ]
            )
        widths = [max(len(row[i]) for row in rows) for i in range(len(heading))]
        lines = [
            "  ".join(
                cell.ljust(width) if i == 0 else cell.rjust(width)
                for i, (cell, width) in enumerate(zip(row, widths, strict=True))
            ).rstrip()
            for row in rows
        ]
        title = self.value or "Values"
        title += f" ({self.unit})" if self.unit else ""
        return "\n".join([title, *lines, *self.notes])

    def __repr__(self) -> str:
        return str(self)

    def _repr_html_(self) -> str:
        return f"<pre>{html.escape(str(self))}</pre>"


@dataclass(frozen=True, repr=False)
class FitResult(_Result):
    """The fits ``ht.stats.fit()`` returns.

    Use ``.to_frame()`` for a table with one row per group and distribution,
    ``.distribution(name)`` for a fitted SciPy distribution, ``.to_dict()``
    for a report, or ``print(result)`` to read it. The text is a view of the
    same numbers.
    """

    #: The columns grouped by, in order.
    by: tuple[str, ...]
    #: The source columns pooled on purpose (``pool=``).
    pooled: tuple[str, ...]
    include_assumed: bool
    #: ``(low, high)`` in the result's unit, None for no bound.
    bounds: tuple[float | None, float | None]
    #: The system the values were converted to before fitting, None if not.
    display_units: str | None
    #: The distributions asked for, in the order that breaks a tie.
    distributions: tuple[str, ...]
    #: One record per group: its key, counts, fits (ranked), the
    #: distributions left out and why, the reason it has no fits, the values
    #: fitted (``exact``, and censored ``left`` and ``right``) and the
    #: plotting positions of the exact ones.
    groups: tuple[dict[str, Any], ...]

    def to_frame(self) -> pd.DataFrame:
        """Return one row per group and distribution, ranked within each group.

        A group with no fits has one row, with ``distribution`` blank and its
        counts. ``attrs["units"]`` gives the unit of each column that has one.
        """
        rows = []
        for group in self.groups:
            counts = group["counts"]
            head = {
                "count": counts["count"],
                "count_censored": counts["count_censored"],
            }
            tail = {name: counts[name] for name in _FIT_COUNTS}
            if not group["fits"]:
                rows.append({**group["key"], "distribution": None, **head, **tail})
            for fit in group["fits"]:
                rows.append(
                    {
                        **group["key"],
                        "distribution": fit["distribution"],
                        "rank": fit["rank"],
                        **head,
                        **{name: fit[name] for name in _FIT_STATISTICS},
                        "parameters": _parameter_text(fit, self.unit),
                        **{name: fit[name] for name in _FIT_COLUMNS},
                        **tail,
                    }
                )
        columns = [
            *self.by,
            "distribution",
            "rank",
            "count",
            "count_censored",
            *_FIT_STATISTICS,
            "parameters",
            *_FIT_COLUMNS,
            *_FIT_COUNTS,
        ]
        frame = pd.DataFrame(rows, columns=columns)
        frame["rank"] = frame["rank"].astype("Int64")
        frame.attrs["units"] = (
            {} if self.unit is None else dict.fromkeys(_FIT_STATISTICS, self.unit)
        )
        return frame

    def distribution(self, name: str, group: Any = None) -> Any:
        """Return the fitted SciPy frozen distribution ``name`` of one group.

        ``group`` is the group's key: its value for one ``by`` column, a tuple
        for several. It is needed when the result has more than one group.
        Use it downstream, e.g. ``.ppf(0.05)`` for a 5 % fractile.
        """
        from hangtu.stats._fit import frozen  # _fit imports this module

        chosen = self._group(group)
        for fit in chosen["fits"]:
            if fit["distribution"] == name:
                return frozen(name, fit["parameters"])
        label = _label(chosen["key"])
        why = chosen["reason"] or chosen["left_out"].get(name)
        if why is None:
            why = f"it wasn't asked for; fitted: {', '.join(self.distributions)}"
        raise HangtuError(f"{label} has no {name} fit: {why}.")

    def _group(self, group: Any) -> dict[str, Any]:
        """Return the record of the group whose key is ``group``."""
        if group is None:
            if len(self.groups) == 1:
                return self.groups[0]
            raise HangtuError(
                f"The result has {len(self.groups)} groups; name one with group=, "
                f"from: {', '.join(_label(g['key']) for g in self.groups)}."
            )
        wanted = group if isinstance(group, tuple) else (group,)
        for record in self.groups:
            if tuple(map(str, record["key"].values())) == tuple(map(str, wanted)):
                return record
        raise HangtuError(
            f"The result has no group {group!r}. Groups: "
            f"{', '.join(_label(g['key']) for g in self.groups)}."
        )

    def plot(self, group: Any = None, **kwargs: Any) -> Any:
        """Draw P08 for one group of this result, without refitting.

        ``group`` is needed when the result has more than one. The keyword
        arguments are ``ht.plot.distribution_fit()``'s drawing ones:
        ``distributions``, ``qq``, ``bins``, ``log``, ``table``,
        ``reference_lines``, ``note``, ``figsize`` and style overrides.
        Returns ``(fig, axs)``.
        """
        from hangtu.plot._distribution_fit import draw  # plot imports stats

        return draw(self, group=group, **kwargs)

    def __str__(self) -> str:
        from hangtu.plot._overlays import format_number  # plot imports stats

        frame = self.to_frame()
        columns = [
            name
            for name in ("rank", *_FIT_STATISTICS, *_FIT_COLUMNS)
            if frame[name].notna().any()
        ]
        headings = {
            **_FIT_HEADINGS,
            "probability_below_lower_bound": f"P(< {_number(self.bounds[0])})",
            "probability_above_upper_bound": f"P(> {_number(self.bounds[1])})",
        }
        title = self.value or "Values"
        lines = [title + (f" ({self.unit})" if self.unit else "")]
        for group in self.groups:
            counts = group["counts"]
            parts = [f"{counts['count']} values"]
            parts += [
                f"{counts[name]} {_heading(name)}"
                for name in ("count_censored", *_FIT_COUNTS)
                if counts[name] and name not in ("count_at_least", "count_at_most")
            ]
            heading = ", ".join(parts)
            lines.append(f"{_label(group['key'])}: {heading}" if self.by else heading)
            if not group["fits"]:
                lines.append(f"  not fitted: {group['reason']}")
                continue
            rows = [["", *(headings.get(name, name) for name in columns)]]
            for fit in group["fits"]:
                rows.append(
                    [
                        fit["distribution"],
                        *(
                            "—"
                            if not math.isfinite(fit[name])
                            else str(fit[name])
                            if name == "rank"
                            else format_number(float(fit[name]))
                            for name in columns
                        ),
                    ]
                )
            widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
            for row in rows:
                lines.append(
                    "  "
                    + "  ".join(
                        cell.ljust(width) if i == 0 else cell.rjust(width)
                        for i, (cell, width) in enumerate(zip(row, widths, strict=True))
                    ).rstrip()
                )
            for fit in group["fits"]:
                lines.append(
                    f"  {fit['distribution']}: {_parameter_text(fit, self.unit)}"
                )
        return "\n".join([*lines, *self.notes])

    def __repr__(self) -> str:
        return str(self)

    def _repr_html_(self) -> str:
        return f"<pre>{html.escape(str(self))}</pre>"


#: The fitted distribution's statistics, in the value's unit.
_FIT_STATISTICS = (
    "mean",
    "standard_deviation",
    "median",
    "percentile_5",
    "percentile_95",
)
_FIT_COLUMNS = (
    "log_likelihood",
    "aicc",
    "delta_aicc",
    "akaike_weight",
    "anderson_darling_statistic",
    "anderson_darling_p_value",
    "probability_below_lower_bound",
    "probability_above_upper_bound",
)
_FIT_COUNTS = (
    "count_at_least",
    "count_at_most",
    "count_non_plastic",
    "count_assumed",
    "count_range",
    "count_text",
    "count_blank",
)
_FIT_HEADINGS = {
    "standard_deviation": "std",
    "percentile_5": "P5",
    "percentile_95": "P95",
    "log_likelihood": "ln L",
    "aicc": "AICc",
    "delta_aicc": "ΔAICc",
    "akaike_weight": "weight",
    "anderson_darling_statistic": "A²",
    "anderson_darling_p_value": "AD p",
}
#: How each distribution's parameters read: (SciPy name, label, has the unit).
_PARAMETERS = {
    "normal": (("loc", "mean", True), ("scale", "standard deviation", True)),
    "lognormal": (("scale", "median", True), ("s", "σ of ln x", False)),
    "gamma": (("a", "shape", False), ("scale", "scale", True)),
    "weibull": (("c", "shape", False), ("scale", "scale", True)),
    "beta": (("a", "α", False), ("b", "β", False)),
}


def _parameter_text(fit: dict[str, Any], unit: str | None) -> str:
    """Write a fit's parameters: ``shape = 3.08, scale = 23.3 kPa``."""
    from hangtu.plot._overlays import format_number  # plot imports stats

    return ", ".join(
        f"{label} = {format_number(fit['parameters'][name])}"
        + (f" {unit}" if has_unit and unit else "")
        for name, label, has_unit in _PARAMETERS[fit["distribution"]]
    )


def _label(key: dict[str, Any]) -> str:
    return ", ".join(map(str, key.values())) or "All"


def _number(value: float | None) -> str:
    return "None" if value is None else f"{value:g}"


#: Short table headings for the statistics (the frame keeps the full names).
_HEADINGS = {
    "count": "n",
    "standard_deviation": "std",
    "coefficient_of_variation": "CoV",
    "minimum": "min",
    "maximum": "max",
    "geometric_mean": "geo mean",
    "geometric_standard_deviation": "geo std",
    "count_at_least": "at least",
    "count_at_most": "at most",
    "count_non_plastic": "NP",
    "count_assumed": "assumed",
    "count_range": "range",
    "count_blank": "blank",
    "count_text": "text",
    "count_not_positive": "≤ 0",
    "count_censored": "censored",
}


def _heading(name: str) -> str:
    """Return the table heading of a statistic: ``percentile_2_5`` -> ``P2.5``."""
    if name.startswith("percentile_"):
        return "P" + name.removeprefix("percentile_").replace("_", ".")
    return _HEADINGS.get(name, name)


def _table(rows: list[list[str]], indent: str = "") -> list[str]:
    """Lay out rows of cells: the first column left-aligned, the rest right."""
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    return [
        indent
        + "  ".join(
            cell.ljust(width) if i == 0 else cell.rjust(width)
            for i, (cell, width) in enumerate(zip(row, widths, strict=True))
        ).rstrip()
        for row in rows
    ]


def _cell(value: Any) -> str:
    from hangtu.plot._overlays import format_number  # plot imports stats

    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    if isinstance(value, int | np.integer):
        return str(int(value))
    return format_number(float(value))


def _percent(level: float) -> str:
    return f"{level * 100:g} %"


@dataclass(frozen=True, repr=False)
class CompareResult(_Result):
    """The comparison ``ht.stats.compare()`` returns.

    Use ``.to_frame()`` for one row with both groups, the difference and both
    tests, ``.to_dict()`` for a report, or ``print(result)`` to read it with
    its note. The text is a view of the same numbers.
    """

    #: The columns grouped by, empty for two inputs.
    by: tuple[str, ...]
    #: The two groups, first then second: label, key, statistics and counts.
    groups: tuple[dict[str, Any], ...]
    log: bool
    #: The source columns pooled on purpose (``pool=``), within each group.
    pooled: tuple[str, ...]
    include_assumed: bool
    #: α, a judgment (SPEC §4).
    significance_level: float
    #: 1 - α, the level of every interval.
    confidence_level: float
    #: Where α came from: ``"argument"`` or the judgments file's path.
    significance_level_source: str
    #: Welch's t-test and the difference (or ratio) with its interval.
    welch: dict[str, float]
    #: The Brunner-Munzel test and the probability of superiority.
    brunner_munzel: dict[str, Any]

    def to_frame(self) -> pd.DataFrame:
        """Return one row: the groups, their statistics, both tests, α, the counts.

        Columns ending ``_1`` are the first group's, ``_2`` the second's.
        ``attrs["units"]`` gives the unit of each column that has one.
        """
        first, second = self.groups
        row: dict[str, Any] = {"group_1": first["label"], "group_2": second["label"]}
        for name in first["statistics"]:
            for i, group in enumerate(self.groups, start=1):
                row[f"{name}_{i}"] = group["statistics"][name]
        row.update(self.welch)
        row.update(self.brunner_munzel)
        row["significance_level"] = self.significance_level
        row["confidence_level"] = self.confidence_level
        for name in first["counts"]:
            for i, group in enumerate(self.groups, start=1):
                row[f"{name}_{i}"] = group["counts"][name]
        frame = pd.DataFrame([row])
        frame.attrs["units"] = (
            {}
            if self.unit is None
            else dict.fromkeys(
                (name for name in row if name in self._with_unit()), self.unit
            )
        )
        return frame

    def _with_unit(self) -> set[str]:
        if self.log:
            return {"geometric_mean_1", "geometric_mean_2"}
        return {
            "mean_1",
            "mean_2",
            "standard_deviation_1",
            "standard_deviation_2",
            "difference",
            "difference_lower",
            "difference_upper",
        }

    def __str__(self) -> str:
        first, second = (group["label"] for group in self.groups)
        title = self.value or "Values"
        title += f" ({self.unit})" if self.unit else ""
        lines = [title, *self._groups_table()]
        level = _percent(self.confidence_level)
        unit = f" {self.unit}" if self.unit and not self.log else ""
        name = "ratio" if self.log else "difference"
        welch = self.welch
        what = (
            f"Ratio of geometric means, {first} / {second}"
            if self.log
            else f"Difference in means, {first} - {second}"
        )
        lines.append(
            f"{what}: {_cell(welch[name])}{unit}; {level} interval "
            f"{_cell(welch[f'{name}_lower'])} to {_cell(welch[f'{name}_upper'])}{unit}"
        )
        lines.append(
            f"Welch's t-test: t = {_cell(welch['welch_t_statistic'])}, "
            f"df = {_cell(welch['welch_degrees_of_freedom'])}, "
            f"p = {_cell(welch['welch_p_value'])}"
        )
        rank = self.brunner_munzel
        lines.append(
            f"P({first} > {second}): {_cell(rank['probability_of_superiority'])}; "
            f"{level} interval {_cell(rank['probability_of_superiority_lower'])} to "
            f"{_cell(rank['probability_of_superiority_upper'])}"
        )
        method = rank["brunner_munzel_method"]
        lines.append(
            f"Brunner-Munzel test: statistic = "
            f"{_cell(rank['brunner_munzel_statistic'])}, "
            f"df = {_cell(rank['brunner_munzel_degrees_of_freedom'])}, "
            f"p = {_cell(rank['brunner_munzel_p_value'])}"
            + (f" ({method})" if method else "")
        )
        source = self.significance_level_source
        lines.append(
            f"Significance level {self.significance_level:g} "
            f"({'argument' if source == 'argument' else Path(source).name})"
        )
        return "\n".join([*lines, *self.notes])

    def _groups_table(self) -> list[str]:
        statistics = list(self.groups[0]["statistics"])
        counts = [
            name
            for name in self.groups[0]["counts"]
            if any(group["counts"][name] for group in self.groups)
        ]
        rows = [["", *(_heading(name) for name in (*statistics, *counts))]]
        for group in self.groups:
            rows.append(
                [
                    group["label"],
                    *(_cell(group["statistics"][name]) for name in statistics),
                    *(str(group["counts"][name]) for name in counts),
                ]
            )
        return _table(rows)

    def __repr__(self) -> str:
        return str(self)

    def _repr_html_(self) -> str:
        return f"<pre>{html.escape(str(self))}</pre>"


@dataclass(frozen=True, repr=False)
class CompareGroupsResult(_Result):
    """The comparison ``ht.stats.compare_groups()`` returns.

    Use ``.to_frame()`` for one row per pair, ``.overall()`` for the overall
    tests, ``.groups_frame()`` for each group's statistics and counts,
    ``.to_dict()`` for a report, or ``print(result)`` to read them with the
    note. The text is a view of the same numbers.
    """

    #: The columns grouped by.
    by: tuple[str, ...]
    #: Every group, in order: label, key, statistics, counts, and the reason it
    #: was left out of the tests (None if tested).
    groups: tuple[dict[str, Any], ...]
    log: bool
    #: The source columns pooled on purpose (``pool=``), within each group.
    pooled: tuple[str, ...]
    include_assumed: bool
    #: α, a judgment (SPEC §4).
    significance_level: float
    #: 1 - α, the level of every interval.
    confidence_level: float
    #: Where α came from: ``"argument"`` or the judgments file's path.
    significance_level_source: str
    #: Welch's ANOVA and Kruskal-Wallis (``.overall()`` as a frame).
    overall_tests: dict[str, Any]
    #: One record per pair of tested groups, first in group order.
    pairs: tuple[dict[str, Any], ...]

    def to_frame(self) -> pd.DataFrame:
        """Return one row per pair: the groups, their statistics, both pair tests.

        Columns ending ``_1`` are the pair's first group's, ``_2`` the
        second's. ``attrs["units"]`` gives the unit of each column that has one.
        """
        by_label = {group["label"]: group for group in self.groups}
        statistics = list(self.groups[0]["statistics"])
        name = "ratio" if self.log else "difference"
        columns = [
            "group_1",
            "group_2",
            *(f"{s}_{i}" for s in statistics for i in (1, 2)),
            name,
            f"{name}_lower",
            f"{name}_upper",
            "games_howell_p_value",
            "dunn_z_statistic",
            "dunn_p_value",
            "significance_level",
            "confidence_level",
        ]
        rows = []
        for pair in self.pairs:
            row = dict(pair)
            for s in statistics:
                for i in (1, 2):
                    row[f"{s}_{i}"] = by_label[pair[f"group_{i}"]]["statistics"][s]
            row["significance_level"] = self.significance_level
            row["confidence_level"] = self.confidence_level
            rows.append(row)
        frame = pd.DataFrame(rows, columns=columns)
        frame.attrs["units"] = self._units(columns)
        return frame

    def overall(self) -> pd.DataFrame:
        """Return one row: Welch's ANOVA, Kruskal-Wallis and α."""
        return pd.DataFrame(
            [
                {
                    **self.overall_tests,
                    "significance_level": self.significance_level,
                    "confidence_level": self.confidence_level,
                }
            ]
        )

    def groups_frame(self) -> pd.DataFrame:
        """Return one row per group: the ``by`` columns, statistics, counts, reason.

        ``reason_not_tested`` is blank for a group in the tests.
        """
        rows = [
            {
                **group["key"],
                **group["statistics"],
                **group["counts"],
                "reason_not_tested": group["reason"],
            }
            for group in self.groups
        ]
        frame = pd.DataFrame(rows)
        frame.attrs["units"] = self._units(frame.columns)
        return frame

    def _units(self, columns: Any) -> dict[str, str]:
        if self.unit is None:
            return {}
        stems = (
            ("geometric_mean",)
            if self.log
            else ("mean", "standard_deviation", "difference")
        )
        return {
            column: self.unit
            for column in columns
            if any(column == stem or column.startswith(f"{stem}_") for stem in stems)
        }

    def __str__(self) -> str:
        title = self.value or "Values"
        title += f" ({self.unit})" if self.unit else ""
        statistics = list(self.groups[0]["statistics"])
        counts = [
            name
            for name in self.groups[0]["counts"]
            if any(group["counts"][name] for group in self.groups)
        ]
        rows = [["", *(_heading(name) for name in (*statistics, *counts))]]
        for group in self.groups:
            rows.append(
                [
                    group["label"],
                    *(_cell(group["statistics"][name]) for name in statistics),
                    *(str(group["counts"][name]) for name in counts),
                ]
            )
        lines = [title, *_table(rows)]
        overall = self.overall_tests
        lines.append(
            f"Welch's ANOVA: F = {_cell(overall['welch_f_statistic'])}, df = "
            f"{_cell(overall['welch_degrees_of_freedom_numerator'])} and "
            f"{_cell(overall['welch_degrees_of_freedom_denominator'])}, "
            f"p = {_cell(overall['welch_p_value'])}"
        )
        lines.append(
            f"Kruskal-Wallis: H = {_cell(overall['kruskal_wallis_statistic'])}, "
            f"df = {_cell(overall['kruskal_wallis_degrees_of_freedom'])}, "
            f"p = {_cell(overall['kruskal_wallis_p_value'])}"
        )
        name = "ratio" if self.log else "difference"
        unit = f" ({self.unit})" if self.unit and not self.log else ""
        lines.append(
            f"Pairs, {_percent(self.confidence_level)} intervals, family-wise "
            f"p-values{unit}:"
        )
        pair_rows = [
            ["", name, "lower", "upper", "Games-Howell p", "Dunn z", "Dunn p (Holm)"]
        ]
        joiner = " / " if self.log else " - "
        for pair in self.pairs:
            pair_rows.append(
                [
                    f"{pair['group_1']}{joiner}{pair['group_2']}",
                    *(
                        _cell(pair[column])
                        for column in (
                            name,
                            f"{name}_lower",
                            f"{name}_upper",
                            "games_howell_p_value",
                            "dunn_z_statistic",
                            "dunn_p_value",
                        )
                    ),
                ]
            )
        lines.extend(_table(pair_rows, indent="  "))
        source = self.significance_level_source
        lines.append(
            f"Significance level {self.significance_level:g} "
            f"({'argument' if source == 'argument' else Path(source).name})"
        )
        return "\n".join([*lines, *self.notes])

    def __repr__(self) -> str:
        return str(self)

    def _repr_html_(self) -> str:
        return f"<pre>{html.escape(str(self))}</pre>"


#: The label of the totals row and column of a ``CrosstabResult``.
TOTAL = "(total)"
#: The mismatches ``print(result)`` shows; ``.mismatches`` has them all.
MISMATCHES_SHOWN = 20


def _listed(value: Any) -> str:
    return value if isinstance(value, str) else _cell(value)


@dataclass(frozen=True, repr=False)
class CrosstabResult(_Result):
    """The table ``ht.stats.crosstab()`` returns.

    Use ``.to_frame()`` for the counts with totals, ``.mismatches`` for the
    rows whose classes disagree, ``.to_dict()`` for a report, or
    ``print(result)`` to read it. The text is a view of the same numbers.
    """

    #: The column whose classes are the rows.
    rows: str
    #: The column whose classes are the columns.
    columns: str
    #: ``"same"``, the mapping (each value a list of text), or None.
    agree: str | dict[str, list[str]] | None
    #: The classes of ``rows`` present, in order, without ``"(blank)"``.
    row_values: tuple[str, ...]
    #: The classes of ``columns`` present, in order, without ``"(blank)"``.
    column_values: tuple[str, ...]
    #: Row class -> column class -> rows, ``"(blank)"`` last where present.
    counts: dict[str, dict[str, int]]
    #: Rows with both values; the agreement fields are None without ``agree=``.
    count_compared: int | None
    count_agreeing: int | None
    count_disagreeing: int | None
    #: Rows blank in ``rows`` only.
    count_blank_in_rows: int | None
    #: Rows blank in ``columns`` only.
    count_blank_in_columns: int | None
    count_blank_in_both: int | None
    #: ``count_agreeing / count_compared``, NaN when nothing is compared.
    proportion_agreeing: float | None
    #: The mismatch listing's columns, its rows' index labels and values.
    mismatch_columns: tuple[str, ...]
    mismatch_index: tuple[Any, ...]
    mismatch_values: tuple[tuple[Any, ...], ...]

    def to_frame(self) -> pd.DataFrame:
        """Return the counts, with ``"(total)"`` last on each side.

        One row per ``rows`` class and one column per ``columns`` class.
        """
        frame = pd.DataFrame.from_dict(self.counts, orient="index")
        column_labels = next(iter(self.counts.values()), {}).keys()
        frame = frame.reindex(columns=list(column_labels)).astype("int64")
        frame[TOTAL] = frame.sum(axis=1)
        frame.loc[TOTAL] = frame.sum(axis=0)
        frame = frame.astype("int64")
        frame.index.name = self.rows
        frame.columns.name = self.columns
        return frame

    @property
    def mismatches(self) -> pd.DataFrame:
        """The rows whose classes disagree, indexed as in the input.

        ``df.loc[result.mismatches.index]`` gives their full rows. Empty
        without ``agree=``.
        """
        return pd.DataFrame(
            [list(values) for values in self.mismatch_values],
            index=pd.Index(list(self.mismatch_index)),
            columns=list(self.mismatch_columns),
        )

    def __str__(self) -> str:
        frame = self.to_frame()
        rows = [[self.rows, *map(str, frame.columns)]]
        rows += [
            [str(label), *(str(int(count)) for count in counts)]
            for label, counts in zip(frame.index, frame.to_numpy(), strict=True)
        ]
        lines = [f"{self.rows} × {self.columns}", *_table(rows), *self.notes]
        return "\n".join([*lines, *self._listing()])

    def _listing(self) -> list[str]:
        """Return the first mismatches as a table (Decision 9)."""
        n = len(self.mismatch_values)
        if not n:
            return []
        verb = "row disagrees" if n == 1 else "rows disagree"
        shown = self.mismatch_values[:MISMATCHES_SHOWN]
        cells = [
            [str(label), *(_listed(value) for value in values)]
            for label, values in zip(self.mismatch_index, shown, strict=False)
        ]
        header = ["", *self.mismatch_columns]
        lines = [f"{n} {verb}:", *_table([header, *cells], "  ")]
        if n > MISMATCHES_SHOWN:
            lines.append(
                f"… and {n - MISMATCHES_SHOWN} more: result.mismatches lists them all."
            )
        return lines

    def __repr__(self) -> str:
        return str(self)

    def _repr_html_(self) -> str:
        return f"<pre>{html.escape(str(self))}</pre>"
