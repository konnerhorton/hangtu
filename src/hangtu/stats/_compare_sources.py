"""``compare_sources()``: one parameter's sources side by side, by geology unit.

Spec: docs/work/m18d-sources-compared.md, decisions 8-16. Each source is
summarized on its own through the calculation ``describe()`` uses, so a source
is never pooled with another; the comparison is descriptive and tests nothing
(decision 14).
"""

import html
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import text_values
from hangtu.errors import ColumnError, HangtuError, UnitsError
from hangtu.stats import _rows
from hangtu.stats._describe import (
    DEFAULT_PERCENTILES,
    PERCENTILE_METHOD,
    _flag_notes,
    _notes,
    check_percentiles,
    summarize,
)
from hangtu.stats._result import _cell, _heading, _Result, _table
from hangtu.stats._rows import BLANK_GROUP, COUNTS

_FUNCTION = "compare_sources()"
#: A row whose source columns are all blank is a source of its own (decision 10).
NO_SOURCE = "(no source given)"
#: The columns a fit source fills, blank for a row source (decision 16).
FIT_COLUMNS = (
    "count_points",
    "r_squared",
    "lowest_normal_stress",
    "highest_normal_stress",
    "shallowest_depth",
    "deepest_depth",
)


@dataclass
class _Rows:
    """One DataFrame source's rows, read once for every label it holds."""

    position: int
    numbers: np.ndarray
    reasons: np.ndarray
    marks: dict[str, np.ndarray]
    labels: np.ndarray
    #: Each unit's key, as a tuple of the ``by`` values, -> its rows.
    units: dict[tuple[Any, ...], np.ndarray]
    unit: str | None


@dataclass
class _Source:
    """One source of the comparison: its label, kind and where it came from."""

    label: str
    kind: str  # "rows" or "fit"
    position: int
    rows: _Rows | None = None
    #: The label the frame's rows carry, before a repeat's suffix.
    row_label: str | None = None


def compare_sources(
    *sources: Any,
    value: str,
    by: str | Sequence[str] | None = "geology_unit",
    percentiles: Sequence[float] = DEFAULT_PERCENTILES,
    include_assumed: bool = False,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> "SourceComparison":
    r"""Put every source of one parameter side by side, geology unit by geology unit.

    Before choosing a value, see whether its sources agree: SPT correlations,
    triaxial and converted shear box fits of φ′, or UU, vane and correlated
    s_u. Each source is summarized on its own, per unit, and **never pooled**:
    grouping by source is the point, so there is no ``pool=``. The comparison
    is descriptive and tests nothing; ``ht.stats.compare()`` is the check for
    two row sources (SPEC §5: selection pools units "on geology and plots;
    tests are a check").

    **Sources.** Each DataFrame gives its rows of ``value``, labeled by the
    non-blank values of the registry's source columns (``source``,
    ``test_type``, ``correlation_name``, ``conversion_name``, in registry
    order), joined by ", ". One frame can hold several sources, such as two
    correlations; a row with none of them is a source of its own,
    ``"(no source given)"``. A label already used by an earlier argument
    takes " (source <n>)", ``n`` the argument's position, so nothing merges
    silently.

    **The statistics** of each unit and source are ``describe()``'s, from the
    same rows by the same rules: flags from the registry; bands, non-plastic
    values, text and blanks left out and counted; assumed values only with
    ``include_assumed=True``; refusals and ``>``/``<`` values at their value,
    counted as bounds; ``count`` and the counts left out add up to the
    source's rows in the unit; percentiles by Hyndman & Fan (1996)
    definition 7, each reported only with one value beyond it on each side.

    **Nothing is dropped.** Every unit of every source is listed for every
    source; a pair with no value has ``count`` 0 and a ``no_value_reason``
    ("no rows in this unit", or "all n rows left out", with the counts
    giving why).

    Parameters
    ----------
    *sources : pandas.DataFrame
        The frames to compare, in the order the table lists them.
    value : str
        The parameter, a registry column such as
        ``"effective_friction_angle"`` or ``"undrained_shear_strength"``.
    by : str or list of str, optional
        The column(s) to compare by, ``"geology_unit"`` by default, in
        ``describe()``'s order (categorical, else by name, blank last).
        None compares all rows together.
    percentiles : sequence of float
        As for ``describe()``; the median is always given.
    include_assumed : bool
        Summarize assumed values with the rest, still counted.
    units : dict, optional
        ``{column: unit}``, applied to every DataFrame, overriding its
        ``attrs["units"]``.
    display_units : {"US", "SI"}, optional
        Convert every source to this system's unit. None converts each to the
        unit of the first source that has one; angles are always in degrees.

    Returns
    -------
    SourceComparison
        ``.to_frame()`` has one row per unit and source; ``print()`` shows
        the same numbers with their notes.

    Raises
    ------
    HangtuError
        For no sources, a source that isn't a DataFrame, or an argument out
        of its range.
    ColumnError
        For a frame without ``value`` or a ``by`` column, naming the frame's
        position among the sources.
    UnitsError
        For a frame whose ``value`` has no unit, naming its position.

    Examples
    --------
    >>> uu = p.undrained_strength()
    >>> stroud = ht.analysis.correlations.undrained_shear_strength_stroud_1974(
    ...     p.spt(), plasticity_index=25
    ... )
    >>> ht.stats.compare_sources(uu, stroud, value="undrained_shear_strength")
    """
    if not sources:
        raise HangtuError(
            f"{_FUNCTION} needs at least one source: DataFrames of values, e.g. "
            'ht.stats.compare_sources(triaxial, spt, value="effective_friction_angle").'
        )
    by_columns = [] if by is None else [by] if isinstance(by, str) else list(by)
    percentiles = check_percentiles(percentiles, _FUNCTION)
    if display_units not in (None, "US", "SI"):
        raise HangtuError(
            f'{_FUNCTION} display_units must be "US", "SI" or None, not '
            f"{display_units!r}."
        )
    unit: str | None = None
    listed: list[_Source] = []
    keys: list[pd.DataFrame] = []
    for position, source in enumerate(sources, start=1):
        if isinstance(source, pd.DataFrame):
            rows = _read_rows(
                source,
                position,
                value,
                by_columns,
                units,
                include_assumed,
                display_units,
                unit,
            )
            unit = unit or rows.unit
            for label in dict.fromkeys(rows.labels):
                listed.append(_Source(label, "rows", position, rows, row_label=label))
            keys.append(source[by_columns])
            continue
        raise HangtuError(
            f"{_FUNCTION} source {position} is a {type(source).__name__}; it takes "
            "DataFrames of values."
        )
    _name_repeats(listed)
    interval, scale_known = _rows.scale(value)
    unit_keys = _union(keys, by_columns)
    records: list[dict[str, Any]] = []
    notes_by_reason: dict[int | str, dict[str, list[str]]] = {}
    for key in unit_keys:
        place = tuple(key.values())
        for source in listed:
            record = _summarize_rows(source, place, percentiles, interval)
            record["key"] = key
            records.append(record)
            label = f"{_label(key)} · {source.label}"
            for name, why in record["reasons"].items():
                notes_by_reason.setdefault(why, {}).setdefault(name, []).append(label)
    notes = _notes(notes_by_reason, unit_given=True, scale_known=scale_known, log=False)
    notes[-1:-1] = [
        *_flag_notes(records, by_columns, [], include_assumed),
        "Each source is summarized on its own, never pooled; nothing is tested. "
        "ht.stats.compare() tests two row sources.",
    ]
    return SourceComparison(
        kind="property",
        function="compare_sources",
        value=value,
        unit=unit,
        notes=tuple(notes),
        judgments=_judgments(sources),
        hangtu_version=version("hangtu"),
        by=tuple(by_columns),
        sources=tuple(
            {"parameter_source": s.label, "source_kind": s.kind, "position": s.position}
            for s in listed
        ),
        include_assumed=include_assumed,
        percentiles=percentiles,
        percentile_method=PERCENTILE_METHOD,
        display_units=display_units,
        rows=tuple(records),
    )


def _read_rows(
    frame: pd.DataFrame,
    position: int,
    value: str,
    by: list[str],
    units: Mapping[str, str] | None,
    include_assumed: bool,
    display_units: str | None,
    reference: str | None,
) -> _Rows:
    """Read one frame as describe() does, in the comparison's unit (decision 8)."""
    where = f"{_FUNCTION} source {position} (a DataFrame)"
    if units is not None and not isinstance(units, Mapping):
        raise HangtuError(
            f"{_FUNCTION} units must be a dict {{column: unit}}, applied to every "
            f"DataFrame, not {units!r}."
        )
    try:
        read = _rows.read_input(frame, value, by, None, units, _FUNCTION)
    except (ColumnError, UnitsError) as error:
        message = str(error).removeprefix(f"{_FUNCTION} ")
        raise type(error)(f"{where}: {message}") from None
    numbers, texts = text_values(read.frame, read.column)
    numbers, unit = _in_unit(numbers, read, display_units, reference, where)
    flags = _rows.read_flags(read.frame, read.column, _FUNCTION)
    reasons, marks = _rows.choose_rows(
        numbers, texts, flags, include_assumed=include_assumed, positive_only=False
    )
    _rows.warn_left_out(reasons, read.column, where)
    _rows.warn_text(texts, read.column, where)
    return _Rows(
        position=position,
        numbers=numbers,
        reasons=reasons,
        marks=marks,
        labels=_labels(read.frame),
        units={
            tuple(key.values()): rows for key, rows in _rows.group_keys(read.frame, by)
        },
        unit=unit,
    )


def _in_unit(
    numbers: np.ndarray,
    read: _rows.Input,
    display_units: str | None,
    reference: str | None,
    where: str,
) -> tuple[np.ndarray, str | None]:
    """Convert to display_units, else to the first source's unit; angles in degrees."""
    if display_units is not None or read.unit is None:
        return _rows.convert(numbers, read, display_units, _FUNCTION)
    target = reference or ("deg" if read.quantity == "angle" else read.unit)
    source, to = _units.parse_unit(read.unit), _units.parse_unit(target)
    if read.quantity is None:
        if source != to:
            raise UnitsError(
                f"{where}: {read.column!r} is in {read.unit}, not {target} as the "
                "first source, and isn't a registered column, so it can't be "
                "converted. Convert it yourself, or pass units=."
            )
        return numbers, target
    return _units.convert(numbers, source, read.quantity, to), target


def _labels(frame: pd.DataFrame) -> np.ndarray:
    """Each row's source: its non-blank source columns, joined (decision 10)."""
    columns = [c for c in _rows._source_columns() if c in frame.columns]
    parts = []
    for column in columns:
        text = frame[column].astype("string").str.strip()
        parts.append(text.where(text != "").to_numpy(dtype=object, na_value=None))
    labels = np.empty(len(frame), dtype=object)
    for i in range(len(frame)):
        found = [str(part[i]) for part in parts if part[i] is not None]
        labels[i] = ", ".join(found) or NO_SOURCE
    return labels


def _name_repeats(listed: list[_Source]) -> None:
    """Give a label already taken by an earlier argument its position (decision 10)."""
    taken: set[str] = set()
    for source in listed:
        if source.label in taken:
            source.label = f"{source.label} (source {source.position})"
        taken.add(source.label)


def _union(keys: list[pd.DataFrame], by: list[str]) -> list[dict[str, Any]]:
    """Every unit any source has, in describe()'s order (decision 15)."""
    if not by:
        return [{}]
    frame = pd.concat(keys, ignore_index=True) if keys else pd.DataFrame(columns=by)
    frame = frame.replace({BLANK_GROUP: None})
    return [key for key, _ in _rows.group_keys(frame, by)]


def _summarize_rows(
    source: _Source,
    place: tuple[Any, ...],
    percentiles: tuple[float, ...],
    interval: bool,
) -> dict[str, Any]:
    """One unit and row source: describe()'s statistics and counts (decision 12)."""
    data = source.rows
    assert data is not None  # a row source
    in_unit = data.units.get(place, np.zeros(len(data.numbers), bool))
    rows = in_unit & (data.labels == source.row_label)
    included = rows & (data.reasons == "")
    summary = summarize(
        data.numbers[included], percentiles=percentiles, interval=interval
    )
    counts = {
        name: int(data.marks.get(name, data.reasons == name)[rows].sum())
        for name in COUNTS
    }
    total = int(rows.sum())
    reason = None
    if total == 0:
        reason = "no rows in this unit"
    elif summary.statistics["count"] == 0:
        reason = f"all {total} rows left out"
    return {
        "parameter_source": source.label,
        "source_kind": source.kind,
        "statistics": summary.statistics,
        "counts": counts,
        "reasons": summary.reasons if total else {},
        **dict.fromkeys(FIT_COLUMNS, np.nan),
        "no_value_reason": reason,
    }


def _judgments(sources: Sequence[Any]) -> dict[str, Any]:
    """Merge the judgments the sources record, in the order passed."""
    merged: dict[str, Any] = {}
    for source in sources:
        if isinstance(source, pd.DataFrame):
            merged |= source.attrs.get("judgments", {})
        else:
            merged |= getattr(source, "judgments", {})
    return merged


def _label(key: dict[str, Any]) -> str:
    return ", ".join(map(str, key.values())) or "All"


@dataclass(frozen=True, repr=False)
class SourceComparison(_Result):
    """The comparison ``ht.stats.compare_sources()`` returns.

    Use ``.to_frame()`` for a table with one row per unit and source,
    ``.to_dict()`` for a report, or ``print(comparison)`` to read it. The
    text is a view of the same numbers.
    """

    #: The columns compared by, in order.
    by: tuple[str, ...]
    #: Each source in the order listed: ``parameter_source``, ``source_kind``
    #: (``"rows"`` or ``"fit"``) and its ``position`` among the arguments.
    sources: tuple[dict[str, Any], ...]
    include_assumed: bool
    #: The percentiles asked for.
    percentiles: tuple[float, ...]
    percentile_method: str
    #: The system every source was converted to, or None.
    display_units: str | None
    #: One record per unit and source: ``key``, ``parameter_source``,
    #: ``source_kind``, ``statistics``, ``counts``, the fit columns and
    #: ``no_value_reason``.
    rows: tuple[dict[str, Any], ...]

    def _statistics(self) -> list[str]:
        return list(self.rows[0]["statistics"]) if self.rows else []

    def _columns(self) -> list[str]:
        return [
            *self.by,
            "parameter_source",
            "source_kind",
            *self._statistics(),
            *COUNTS,
            *FIT_COLUMNS,
            "no_value_reason",
        ]

    def to_frame(self) -> pd.DataFrame:
        """Return one row per unit and source: units in order, sources as passed.

        ``attrs["units"]`` gives the unit of each column that has one.
        """
        rows = [
            {
                **record["key"],
                "parameter_source": record["parameter_source"],
                "source_kind": record["source_kind"],
                **record["statistics"],
                **record["counts"],
                **{name: record[name] for name in FIT_COLUMNS},
                "no_value_reason": record["no_value_reason"],
            }
            for record in self.rows
        ]
        frame = pd.DataFrame(rows, columns=self._columns())
        unitless = {"count", "coefficient_of_variation"}
        frame.attrs["units"] = (
            {}
            if self.unit is None
            else {
                name: self.unit for name in self._statistics() if name not in unitless
            }
        )
        return frame

    def __str__(self) -> str:
        frame = self.to_frame()
        counts = [name for name in COUNTS if frame[name].any()]
        shown = [*self._statistics(), *counts]
        title = f"{self.value}" + (f" ({self.unit})" if self.unit else "")
        title += ", sources compared" + (f" by {', '.join(self.by)}" if self.by else "")
        lines = [title]
        for key in dict.fromkeys(tuple(r["key"].items()) for r in self.rows):
            lines.append(_label(dict(key)))
            table = [["", *(_heading(name) for name in shown), ""]]
            for record in self.rows:
                if tuple(record["key"].items()) != key:
                    continue
                values = {**record["statistics"], **record["counts"]}
                table.append(
                    [
                        record["parameter_source"],
                        *(_cell(values[name]) for name in shown),
                        record["no_value_reason"] or "",
                    ]
                )
            lines.extend(_table(table, indent="  "))
        return "\n".join([*lines, *self.notes])

    def __repr__(self) -> str:
        return str(self)

    def _repr_html_(self) -> str:
        return f"<pre>{html.escape(str(self))}</pre>"
