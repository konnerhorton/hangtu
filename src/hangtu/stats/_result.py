"""The results of the statistics functions (docs/work/m15a-describe.md, Decision 2)."""

import html
import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd


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
}


def _heading(name: str) -> str:
    """Return the table heading of a statistic: ``percentile_2_5`` -> ``P2.5``."""
    if name.startswith("percentile_"):
        return "P" + name.removeprefix("percentile_").replace("_", ".")
    return _HEADINGS.get(name, name)
