"""The results of the statistics functions (docs/work/m15a-describe.md, Decision 2)."""

import html
import math
from dataclasses import asdict, dataclass
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
    #: The distributions asked for, in the order that breaks a tie.
    distributions: tuple[str, ...]
    #: One record per group: its key, counts, fits (ranked), the
    #: distributions left out and why, and the reason it has no fits.
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
        """Draw P08 for one group of this result, without refitting."""
        raise NotImplementedError("FitResult.plot() arrives with P08.")

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
