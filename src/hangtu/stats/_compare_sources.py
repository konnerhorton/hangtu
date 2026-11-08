"""``compare_sources()``: one parameter's sources side by side, by geology unit.

Spec: docs/work/m18d-sources-compared.md, decisions 8-16. Each source is
summarized on its own through the calculation ``describe()`` uses, so a source
is never pooled with another; the comparison is descriptive and tests nothing
(decision 14).
"""

import html
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import text_values
from hangtu.errors import ColumnError, HangtuError, UnitsError
from hangtu.registry import statistics_roles
from hangtu.stats import _rows
from hangtu.stats._describe import (
    DEFAULT_PERCENTILES,
    PERCENTILE_METHOD,
    _flag_notes,
    _notes,
    check_percentiles,
    percentile_floor,
    summarize,
)
from hangtu.stats._result import _cell, _heading, _plain, _Result, _table
from hangtu.stats._rows import BLANK_GROUP, COUNTS

_FUNCTION = "compare_sources()"
#: A row whose source columns are all blank is a source of its own (decision 10).
NO_SOURCE = "(no source given)"
#: A ShearBoxConversion's label (decision 10).
CONVERTED = "shear box, converted (Kulhawy & Mayne 1990)"
#: The columns that place a value in the ground, in the comparison's length unit.
PLACE = ("depth", "depth_top", "depth_base", "elevation", "ground_level")
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
    #: Every row as ``.values()`` draws it, without ``parameter_source``.
    drawn: pd.DataFrame


@dataclass
class _Source:
    """One source of the comparison: its label, kind and where it came from."""

    label: str
    kind: str  # "rows" or "fit"
    position: int
    rows: _Rows | None = None
    #: The label the frame's rows carry, before a repeat's suffix.
    row_label: str | None = None
    #: A fit source's values: each unit's key -> one entry per fitted group.
    fits: dict[tuple[Any, ...], list[dict[str, Any]]] | None = None

    def mask(self, place: tuple[Any, ...]) -> np.ndarray:
        """Return a row source's rows in the unit ``place`` that carry its label."""
        data = self.rows
        assert data is not None  # a row source
        in_unit = data.units.get(place, np.zeros(len(data.numbers), bool))
        return in_unit & (data.labels == self.row_label)


@dataclass
class Compared:
    """A comparison and its sources as read, for ``select()`` (m18e, decision 13)."""

    comparison: "SourceComparison"
    sources: list[_Source]


@dataclass
class _Units:
    """The comparison's units: display_units, else the first source's (decision 8)."""

    display: str | None
    value: str | None = None
    stress: str | None = None
    depth: str | None = None

    def to(
        self, numbers: Any, unit: str | None, quantity: str, slot: str
    ) -> tuple[np.ndarray, str | None]:
        """Convert ``numbers`` in ``unit`` to the slot's unit, setting it if unset."""
        numbers = np.asarray(numbers, dtype=float)
        if unit is None:
            return numbers, None
        if self.display is not None:
            converted, shown = _units.to_display(numbers, unit, quantity, self.display)
            setattr(self, slot, getattr(self, slot) or shown)
            return converted, shown
        target = getattr(self, slot) or ("deg" if quantity == "angle" else unit)
        setattr(self, slot, target)
        return (
            _units.convert(
                numbers, _units.parse_unit(unit), quantity, _units.parse_unit(target)
            ),
            target,
        )


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
    two row sources (selection pools units on geology and plots; tests are a
    check).

    **Sources.** Each DataFrame gives its rows of ``value``, labeled by the
    non-blank values of the registry's source columns (``source``,
    ``test_type``, ``correlation_name``, ``conversion_name``, in registry
    order), joined by ", ". One frame can hold several sources, such as two
    correlations; a row with none of them is a source of its own,
    ``"(no source given)"``. A label already used by an earlier argument
    takes " (source <n>)", ``n`` the argument's position, so nothing merges
    silently.

    A ``MohrCoulombFit`` gives each group's main fit, for
    ``effective_friction_angle`` or ``effective_cohesion`` (``total_stress_…``
    for a total stress fit), labeled "Mohr-Coulomb fit (CD, CU)" by its points'
    test types. A ``ShearBoxConversion``, from
    ``ht.analysis.friction_angle_from_shear_box()``, gives its main line's
    converted ``effective_friction_angle`` only, labeled "shear box, converted
    (Kulhawy & Mayne 1990)". A ``ShearBoxFit`` isn't taken: a direct shear φ′
    isn't a triaxial φ′ until converted. A fit's groups must be
    keyed by every ``by`` column. One fit in a unit is one value, with
    ``count_points``, ``r_squared``, its normal stress range and its points'
    depths; fitted per sample (``group_by=["geology_unit",
    "sample_reference"]``), a unit's values are summarized like rows. A fit
    has no standard error here.

    **A fit's value is placed, never tested** (``.positions()``): below,
    within or above each row source's lowest to highest value in the unit,
    and, within it and from 4 values, its percentile rank, the inverse of
    Hyndman & Fan definition 7 (the middle of a run of ties).

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
    *sources : pandas.DataFrame, MohrCoulombFit or ShearBoxConversion
        The sources to compare, in the order the table lists them.
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
        ``.to_frame()`` has one row per unit and source; ``.positions()``
        places each fit among the row sources; ``print()`` shows the same
        numbers with their notes.

    Raises
    ------
    HangtuError
        For no sources, a source of another type (a ``ShearBoxFit``, naming
        the conversion; a ``HoekBrownFit``), a fit that doesn't give
        ``value`` or isn't grouped by every ``by`` column, or an argument out
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

    φ′ in each unit from an SPT correlation and a triaxial fit:

    >>> spt = ht.analysis.correlations.effective_friction_angle_hatanaka_uchida_1996(
    ...     p.spt()
    ... )
    >>> triaxial = ht.analysis.mohr_coulomb_fit(p.triaxial(), group_by="geology_unit")
    >>> compared = ht.stats.compare_sources(
    ...     spt, triaxial, value="effective_friction_angle"
    ... )
    >>> compared.positions()
    """
    return compare(
        sources, value, by, percentiles, include_assumed, units, display_units
    ).comparison


def compare(
    sources: Sequence[Any],
    value: str,
    by: str | Sequence[str] | None,
    percentiles: Sequence[float],
    include_assumed: bool,
    units: Mapping[str, str] | None,
    display_units: str | None,
) -> Compared:
    """Compute ``compare_sources()``, keeping each source as it was read."""
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
    state = _Units(display_units)
    listed: list[_Source] = []
    keys: list[pd.DataFrame] = []
    notes_left: list[str] = []
    for position, source in enumerate(sources, start=1):
        if isinstance(source, pd.DataFrame):
            rows = _read_rows(
                source, position, value, by_columns, units, include_assumed, state
            )
            state.value = state.value or rows.unit
            for label in dict.fromkeys(rows.labels):
                listed.append(_Source(label, "rows", position, rows, row_label=label))
            keys.append(source[by_columns])
            continue
        fit = _read_fit(source, position, value, by_columns, state, notes_left)
        listed.append(fit)
        assert fit.fits is not None  # a fit source
        keys.append(pd.DataFrame(list(fit.fits), columns=by_columns))
    unit = state.value
    _name_repeats(listed)
    interval, scale_known = _rows.scale(value)
    unit_keys = _union(keys, by_columns)
    records: list[dict[str, Any]] = []
    notes_by_reason: dict[int | str, dict[str, list[str]]] = {}
    placed: list[dict[str, Any]] = []
    for key in unit_keys:
        place = tuple(key.values())
        values: dict[str, np.ndarray] = {}
        for source in listed:
            summarize_one = _summarize_rows if source.kind == "rows" else _summarize_fit
            record, values[source.label] = summarize_one(
                source, place, percentiles, interval, notes_left
            )
            record["key"] = key
            records.append(record)
            label = f"{_label(key)} · {source.label}"
            for name, why in record["reasons"].items():
                notes_by_reason.setdefault(why, {}).setdefault(name, []).append(label)
        placed += _positions(key, listed, values)
    notes = _notes(notes_by_reason, unit_given=True, scale_known=scale_known, log=False)
    notes[-1:-1] = [
        *_flag_notes(records, by_columns, [], include_assumed),
        *notes_left,
        "Each source is summarized on its own, never pooled; nothing is tested. "
        "ht.stats.compare() tests two row sources; a fit's value is placed among "
        "a row source's values (.positions()), not tested against them.",
    ]
    comparison = SourceComparison(
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
        stress_unit=state.stress,
        depth_unit=state.depth,
        rows=tuple(records),
        placed=tuple(placed),
        _values_frame=_values(listed, value, by_columns),
    )
    return Compared(comparison, listed)


def _values(listed: list[_Source], value: str, by: list[str]) -> pd.DataFrame:
    """Build the long frame the figures draw: every row, one row per fit value."""
    parts = []
    done: set[int] = set()
    for source in listed:
        if source.rows is not None and source.position not in done:
            done.add(source.position)
            labels = {
                s.row_label: s.label for s in listed if s.position == source.position
            }
            drawn = source.rows.drawn.copy()
            drawn.insert(
                len(by),
                "parameter_source",
                [labels[label] for label in source.rows.labels],
            )
            parts.append(drawn)
        elif source.fits is not None:
            rows = []
            for place, entries in source.fits.items():
                keys: dict[str, Any] = {
                    column: None if key == BLANK_GROUP else key
                    for column, key in zip(by, place, strict=True)
                }
                for entry in entries:
                    top, base = _range(entry["depths"])
                    row: dict[str, Any] = {
                        **keys,
                        "parameter_source": source.label,
                        value: entry["value"],
                        "depth": (top + base) / 2,
                        "depth_top": top,
                        "depth_base": base,
                    }
                    for column in ("elevation", "ground_level"):
                        if column in entry:
                            row[column] = entry[column]
                    rows.append(row)
            parts.append(pd.DataFrame(rows))
    frame = pd.concat(parts, ignore_index=True)
    first = [*by, "parameter_source", value]
    frame = frame[first + [c for c in frame.columns if c not in first]]
    if value in frame.columns:
        cells = frame[value]
        numeric = pd.to_numeric(cells, errors="coerce")
        if numeric.notna().sum() == cells.notna().sum():
            frame[value] = numeric
    return frame


def _read_rows(
    frame: pd.DataFrame,
    position: int,
    value: str,
    by: list[str],
    units: Mapping[str, str] | None,
    include_assumed: bool,
    state: "_Units",
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
    numbers, unit = _in_unit(numbers, read, state.display, state.value, where)
    flags = _rows.read_flags(read.frame, read.column, _FUNCTION)
    reasons, marks = _rows.choose_rows(
        numbers, texts, flags, include_assumed=include_assumed, positive_only=False
    )
    _rows.warn_left_out(reasons, read.column, where)
    _rows.warn_text(texts, read.column, where)
    drawn = _drawn(read.frame, read, numbers, texts, unit, by, units, state, where)
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
        drawn=drawn,
    )


def _drawn(
    frame: pd.DataFrame,
    read: _rows.Input,
    numbers: np.ndarray,
    texts: np.ndarray,
    unit: str | None,
    by: list[str],
    units: Mapping[str, str] | None,
    state: "_Units",
    where: str,
) -> pd.DataFrame:
    """Every row of a frame as the figures draw it, in the comparison's units.

    A text cell (NP, refusal) is kept as text, so P01 counts it as the table
    does; bands and place columns are converted when their unit is declared.
    """
    value = read.column
    drawn = pd.DataFrame(index=frame.index)
    for column in by:
        drawn[column] = frame[column]
    cells = pd.Series(numbers, index=frame.index, dtype=object)
    cells[texts != ""] = texts[texts != ""]
    drawn[value] = cells
    if "loca_id" in frame.columns:
        drawn["loca_id"] = frame["loca_id"]
    declared = {**_units.units_of(frame), **(units or {})}
    for column in PLACE:
        if column not in frame.columns:
            continue
        given = declared.get(column)
        if given is None:
            continue  # a length is never guessed (SPEC §2.6)
        drawn[column], _ = state.to(
            pd.to_numeric(frame[column], errors="coerce"), given, "length", "depth"
        )
    for column, role in statistics_roles().items():
        if role["role"] == "source" or column not in frame.columns:
            continue
        if value in role.get("values", [value]):
            drawn[column] = frame[column]
    for column in (f"{value}_lower", f"{value}_upper"):
        if column in frame.columns and declared.get(column) and read.quantity:
            drawn[column], _ = state.to(
                pd.to_numeric(frame[column], errors="coerce"),
                declared[column],
                read.quantity,
                "value",
            )
    return drawn.reset_index(drop=True)


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
    notes: list[str],
) -> tuple[dict[str, Any], np.ndarray]:
    """One unit and row source: describe()'s statistics and counts (decision 12)."""
    data = source.rows
    assert data is not None  # a row source
    rows = source.mask(place)
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
    record = {
        "parameter_source": source.label,
        "source_kind": source.kind,
        "statistics": summary.statistics,
        "counts": counts,
        "reasons": summary.reasons if total else {},
        **dict.fromkeys(FIT_COLUMNS, np.nan),
        "stages": None,
        "line_kind": None,
        "no_value_reason": reason,
    }
    return record, data.numbers[included]


def _read_fit(
    source: Any,
    position: int,
    value: str,
    by: list[str],
    state: _Units,
    notes: list[str],
) -> _Source:
    """Read a fit result's main value per group (decisions 10 and 11)."""
    from hangtu.analysis import (  # analysis imports stats
        HoekBrownFit,
        MohrCoulombFit,
        ShearBoxConversion,
        ShearBoxFit,
    )

    where = f"{_FUNCTION} source {position}"
    if isinstance(source, ShearBoxFit):
        raise HangtuError(
            f"{where} is a ShearBoxFit. Its peak_friction_angle is a direct shear φ′, "
            "not a triaxial one, so the two aren't compared unconverted. "
            "Convert it with ht.analysis.friction_angle_from_shear_box(fit, soil=..., "
            "critical_state_friction_angle=...) and pass the conversion."
        )
    if isinstance(source, HoekBrownFit):
        raise HangtuError(
            f"{where} is a HoekBrownFit, which gives σci and mi of intact rock. "
            f"compare_sources() compares soil parameters' sources; it takes "
            "DataFrames, a MohrCoulombFit or a ShearBoxConversion."
        )
    if isinstance(source, MohrCoulombFit):
        cohesion, angle = source._value_names()
        if value not in (angle, cohesion):
            if value in ("effective_friction_angle", "effective_cohesion"):
                raise HangtuError(
                    f"{where} is a total stress MohrCoulombFit, which gives {angle} "
                    f"and {cohesion}, not {value!r}. Fit the effective stresses "
                    '(mohr_coulomb_fit(df, stress="effective")) to compare them.'
                )
            raise HangtuError(
                f"{where} is a MohrCoulombFit, which gives {angle} and {cohesion}, "
                f"not {value!r}."
            )
        _check_keys(source.by, by, where)
        types: list[str] = []
        fits: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
        for group in source.groups:
            main = group["fits"][0]
            types += [str(p["test_type"]) for p in main["points"] if p.get("test_type")]
            raw, unit, quantity = (
                (main["friction_angle"], "deg", "angle")
                if value == angle
                else (main["cohesion"], source.unit, "stress")
            )
            entry = _fit_entry(
                raw, unit, quantity, main, main["points"], source, state, notes
            )
            entry["stages"] = main["stages"]
            entry["reason"] = main["no_fit_reason"]
            fits.setdefault(_place(group["key"], by), []).append(entry)
        listed = ", ".join(dict.fromkeys(types))
        label = "Mohr-Coulomb fit" + (f" ({listed})" if listed else "")
        return _Source(label, "fit", position, fits=fits)
    if isinstance(source, ShearBoxConversion):
        if value != "effective_friction_angle":
            raise HangtuError(
                f"{where} is a ShearBoxConversion, which gives "
                f"effective_friction_angle only, not {value!r}: Kulhawy & Mayne (1990) "
                "give no conversion for the cohesion, so it isn't compared with a "
                "triaxial c′."
            )
        _check_keys(source.by, by, where)
        fits = {}
        for group in source.groups:
            line = group["lines"][0]
            entry = _fit_entry(
                line["effective_friction_angle"],
                "deg",
                "angle",
                line,
                group["points"],
                source,
                state,
                notes,
            )
            entry["line_kind"] = line["line_kind"]
            entry["reason"] = line["no_conversion_reason"]
            fits.setdefault(_place(group["key"], by), []).append(entry)
        return _Source(CONVERTED, "fit", position, fits=fits)
    raise HangtuError(
        f"{where} is a {type(source).__name__}; compare_sources() takes DataFrames of "
        "values, a MohrCoulombFit or a ShearBoxConversion."
    )


def _check_keys(fitted: Sequence[str], by: list[str], where: str) -> None:
    """Raise unless a fit's groups are keyed by every by column (decision 11)."""
    missing = [column for column in by if column not in fitted]
    if missing:
        grouped = f"group_by={list(fitted)!r}" if fitted else "no group_by"
        raise HangtuError(
            f"{where} was fitted with {grouped}, so its groups have no "
            f"{', '.join(missing)}. Fit again with group_by={by!r} (more columns, "
            "such as sample_reference, give several values per unit)."
        )


def _place(key: dict[str, Any], by: list[str]) -> tuple[Any, ...]:
    return tuple(key[column] for column in by)


def _fit_entry(
    raw: float,
    unit: str | None,
    quantity: str,
    line: dict[str, Any],
    points: list[dict[str, Any]],
    source: Any,
    state: _Units,
    notes: list[str],
) -> dict[str, Any]:
    """One fitted group's value, stresses and depths, in the comparison's units."""
    value, _ = state.to([raw], unit, quantity, "value")
    stresses, _ = state.to(
        [line["lowest_normal_stress"], line["highest_normal_stress"]],
        source.unit,
        "stress",
        "stress",
    )
    depths = np.array(
        [np.nan if p.get("depth") is None else p["depth"] for p in points], float
    )
    depth_unit = source.depth_units.get("depth")
    if depth_unit is None:
        if (~np.isnan(depths)).any():
            notes.append(
                f"{source.function}()'s points have depths with no unit, so they are "
                "left blank. Declare the depth's unit on the fit's input."
            )
        depths = np.full(len(points), np.nan)
    else:
        depths, _ = state.to(depths, depth_unit, "length", "depth")
    place: dict[str, float] = {}
    for column in ("elevation", "ground_level"):
        given = source.depth_units.get(column)
        found = [p.get(column) for p in points if p.get(column) is not None]
        if given is None or not found:
            continue
        converted, _ = state.to(found, given, "length", "depth")
        if column == "elevation":
            place[column] = float((converted.min() + converted.max()) / 2)
        elif np.ptp(converted) == 0:
            place[column] = float(converted[0])  # one ground level for the fit
    return {
        **place,
        "value": float(value[0]),
        "count_points": line["count"],
        "r_squared": line.get("r_squared", np.nan),
        "lowest_normal_stress": float(stresses[0]),
        "highest_normal_stress": float(stresses[1]),
        "depths": depths,
        "stages": None,
        "line_kind": None,
    }


def _summarize_fit(
    source: _Source,
    place: tuple[Any, ...],
    percentiles: tuple[float, ...],
    interval: bool,
    notes: list[str],
) -> tuple[dict[str, Any], np.ndarray]:
    """One unit and fit source: one value, or several summarized like rows."""
    assert source.fits is not None  # a fit source
    entries = source.fits.get(place, [])
    valued = [entry for entry in entries if not np.isnan(entry["value"])]
    numbers = np.array([entry["value"] for entry in valued], float)
    summary = summarize(numbers, percentiles=percentiles, interval=interval)
    depths = np.concatenate([e["depths"] for e in entries]) if entries else np.array([])
    shallowest, deepest = _range(depths)
    record: dict[str, Any] = {
        "parameter_source": source.label,
        "source_kind": source.kind,
        "statistics": summary.statistics,
        "counts": dict.fromkeys(COUNTS, 0),
        "reasons": summary.reasons if len(entries) > 1 else {},
        **dict.fromkeys(FIT_COLUMNS, np.nan),
        "count_points": sum(int(e["count_points"]) for e in entries),
        "shallowest_depth": shallowest,
        "deepest_depth": deepest,
        "stages": None,
        "line_kind": None,
        "no_value_reason": None,
    }
    reasons = list(
        dict.fromkeys(str(e["reason"]) for e in entries if np.isnan(e["value"]))
    )
    if len(entries) == 1:
        (entry,) = entries
        for name in ("r_squared", "lowest_normal_stress", "highest_normal_stress"):
            record[name] = entry[name]
        record["stages"], record["line_kind"] = entry["stages"], entry["line_kind"]
    if not entries:
        record["count_points"] = 0
        record["no_value_reason"] = "no rows in this unit"
    elif not valued:
        record["no_value_reason"] = "; ".join(reasons)
    elif reasons:
        notes.append(
            f"{', '.join(map(str, place)) or 'All'} · {source.label}: "
            f"{len(entries) - len(valued)} of {len(entries)} fits have no value "
            f"({'; '.join(reasons)})."
        )
    return record, numbers


def _range(values: np.ndarray) -> tuple[float, float]:
    finite = values[~np.isnan(values)]
    if not finite.size:
        return np.nan, np.nan
    return float(finite.min()), float(finite.max())


def _positions(
    key: dict[str, Any], listed: list[_Source], values: dict[str, np.ndarray]
) -> list[dict[str, Any]]:
    """Each one-value fit placed among each row source's values (decision 13)."""
    placed = []
    place = tuple(key.values())
    for fit in listed:
        if fit.kind != "fit" or len(values[fit.label]) != 1:
            continue
        assert fit.fits is not None  # a fit source
        if len(fit.fits.get(place, [])) != 1:
            continue
        value = float(values[fit.label][0])
        for rows in listed:
            if rows.kind != "rows" or not len(values[rows.label]):
                continue
            x = np.sort(values[rows.label])
            position = (
                "below" if value < x[0] else "above" if value > x[-1] else "within"
            )
            rank = (
                percentile_rank(x, value)
                if position == "within" and x.size >= percentile_floor(25)
                else np.nan
            )
            placed.append(
                {
                    "key": key,
                    "fit_source": fit.label,
                    "parameter_source": rows.label,
                    "fit_value": value,
                    "count": int(x.size),
                    "minimum": float(x[0]),
                    "maximum": float(x[-1]),
                    "position": position,
                    "percentile_rank": rank,
                }
            )
    return placed


def percentile_rank(values: np.ndarray, value: float) -> float:
    """Return the rank of ``value`` in percent: the inverse of H&F definition 7.

    For sorted values with x[i] <= v <= x[i+1] (0-based), h = i + (v - x[i]) /
    (x[i+1] - x[i]) and the rank is 100 h / (n - 1), so the H&F 7 quantile at
    the rank is ``value`` again. A value equal to a run of tied values takes
    the middle of the run (decision 13). ``value`` must lie within the values.
    """
    x = np.sort(np.asarray(values, dtype=float))
    equal = np.flatnonzero(x == value)
    if equal.size:
        h = (equal[0] + equal[-1]) / 2
    else:
        i = int(np.searchsorted(x, value)) - 1
        h = i + (value - x[i]) / (x[i + 1] - x[i])
    return float(100 * h / (x.size - 1))


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
    #: The unit of the fits' normal stresses, and of their depths, or None.
    stress_unit: str | None
    depth_unit: str | None
    #: One record per unit and source: ``key``, ``parameter_source``,
    #: ``source_kind``, ``statistics``, ``counts``, the fit columns,
    #: ``stages`` or ``line_kind`` (a unit's one fit) and ``no_value_reason``.
    rows: tuple[dict[str, Any], ...]
    #: One record per unit, fit and row source: the rows of ``.positions()``.
    placed: tuple[dict[str, Any], ...]
    #: The rows of ``.values()``; not in ``.to_dict()``.
    _values_frame: pd.DataFrame = field(repr=False, compare=False)

    def to_dict(self) -> dict[str, Any]:
        """Return every field but the values, JSON-serializable (NaN as None)."""
        return _plain(
            {f.name: getattr(self, f.name) for f in fields(self) if f.name[0] != "_"}
        )

    def values(self) -> pd.DataFrame:
        """Return the long frame the figures draw, one row per value.

        The ``by`` columns, ``parameter_source``, the value, and where the
        sources have them ``loca_id``, ``depth``, ``elevation``,
        ``ground_level``, the flag columns and the bands. Every row is kept,
        those left out of the statistics too, so a figure counts them as the
        table does. A fit's value is one row at the middle of its points'
        depths, with ``depth_top`` and ``depth_base`` at the shallowest and
        deepest, so P01 draws the range as an interval bar; a fit whose points
        have no depth has a blank one. ``attrs["units"]`` gives each unit.
        """
        frame = self._values_frame.copy()
        units: dict[str, str] = {}
        if self.unit is not None and self.value is not None:
            units |= dict.fromkeys(
                [self.value, f"{self.value}_lower", f"{self.value}_upper"], self.unit
            )
        if self.depth_unit is not None:
            units |= dict.fromkeys(PLACE, self.depth_unit)
        frame.attrs["units"] = {k: v for k, v in units.items() if k in frame.columns}
        return frame

    def profile(self, **kwargs: Any) -> Any:
        """Draw one unit's sources against depth or elevation: P01 of ``.values()``.

        Name the unit by its ``by`` column, e.g.
        ``.profile(geology_unit="Terrace")``; it is required when the
        comparison has more than one unit, because the stats box summarizes
        each source over what it draws and the table is per unit. Each source
        is colored by ``parameter_source``, a fit is a point with an interval
        bar over its points' depths, and the stats box has one line per source
        with the table's numbers. Other keyword arguments go to
        ``ht.plot.profile()`` and override these (``figsize`` 7 x 7 in and the
        legend below, room for long source names). Returns ``(fig, ax)``.
        """
        from hangtu.plot import profile  # plot imports stats

        assert self.value is not None  # compare_sources() always names it
        chosen = {column: kwargs.pop(column) for column in self.by if column in kwargs}
        values = self.values()
        keys = list(dict.fromkeys(tuple(r["key"].values()) for r in self.rows))
        if self.by and (len(keys) > 1 or chosen):
            missing = [column for column in self.by if column not in chosen]
            if missing:
                listed = "; ".join(", ".join(map(str, key)) for key in keys)
                raise HangtuError(
                    f"SourceComparison.profile() draws one unit, so its stats box "
                    f"matches the table: name it, e.g. .profile({missing[0]}="
                    f"{keys[0][self.by.index(missing[0])]!r}). Units: {listed}."
                )
            wanted = tuple(chosen[column] for column in self.by)
            if wanted not in keys:
                listed = "; ".join(", ".join(map(str, key)) for key in keys)
                raise HangtuError(
                    "SourceComparison.profile(): no unit "
                    f"{wanted if len(wanted) > 1 else wanted[0]!r}. Units: {listed}."
                )
            rows = np.ones(len(values), bool)
            for column, key in chosen.items():
                cells = values[column].astype(object)
                blank = cells.isna().to_numpy()
                rows &= (
                    blank if key == BLANK_GROUP else (cells == key).to_numpy() & ~blank
                )
            values = values[rows].reset_index(drop=True)
        options = {
            "color_by": "parameter_source",
            "stats_box": True,
            "intervals": "auto",
            "figsize": (7, 7),
            "legend": "bottom",
            **kwargs,
        }
        return profile(values, self.value, **options)

    def geology_unit_comparison(self, **kwargs: Any) -> Any:
        """Draw the sources geology unit by geology unit: P07 of ``.values()``.

        Each geology unit gets one sub-row per source, in the order passed,
        colored by ``parameter_source`` with one legend entry per source, so
        no sub-row "mixes sources". Each sub-row's percentile bar is that unit
        and source's, as in ``.to_frame()``: drawn wherever the table gives
        the percentiles, from 4 values for P25 and P75 (P07's
        ``summary_min_count`` is set to 1, so only the floors decide). A
        unit's one fit is a point with no bar. The comparison must be by
        ``geology_unit`` alone. P07 never summarizes assumed values, so with
        ``include_assumed=True`` it warns when there are any. Other keyword
        arguments go to ``ht.plot.geology_unit_comparison()`` and override
        these (the units in the table's order, the comparison's
        ``display_units``, the legend below, and ``figsize`` 9 in wide, room
        for the long source names). Returns ``(fig, ax)``.
        """
        from hangtu.plot import geology_unit_comparison  # plot imports stats

        assert self.value is not None  # compare_sources() always names it
        if self.by != ("geology_unit",):
            by = ", ".join(self.by) if self.by else "None"
            raise HangtuError(
                "SourceComparison.geology_unit_comparison() draws one row per "
                f"geology unit and source, but this comparison is by {by}. "
                'Compare with by="geology_unit", or draw .profile().'
            )
        values = self.values()
        if self.include_assumed and _rows.read_flags(values, self.value).assumed.any():
            warnings.warn(
                "SourceComparison.geology_unit_comparison(): P07 leaves assumed "
                "values out of each summary, but this comparison includes them "
                "(include_assumed=True), so the bars and .to_frame() differ.",
                UserWarning,
                stacklevel=2,
            )
        order = [
            r["key"]["geology_unit"]
            for r in self.rows
            if r["key"]["geology_unit"] != BLANK_GROUP
        ]
        drawn = values.dropna(subset=[self.value])
        rows = len(
            drawn.groupby(
                ["geology_unit", "parameter_source"], dropna=False, observed=True
            )
        )
        options = {
            "split_by": "parameter_source",
            "color_by": "parameter_source",
            # The table's floors decide, not P07's drawing threshold of 5.
            "summary_min_count": 1,
            "figsize": (9, max(4.0, 2.5 + 0.45 * rows)),
            "legend": "bottom",
            "order": list(dict.fromkeys(order)),
            **({"display_units": self.display_units} if self.display_units else {}),
            **kwargs,
        }
        return geology_unit_comparison(values, self.value, **options)

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
        units = (
            {}
            if self.unit is None
            else {n: self.unit for n in self._statistics() if n not in unitless}
        )
        if self.stress_unit:
            units |= dict.fromkeys(
                ["lowest_normal_stress", "highest_normal_stress"], self.stress_unit
            )
        if self.depth_unit:
            units |= dict.fromkeys(
                ["shallowest_depth", "deepest_depth"], self.depth_unit
            )
        frame.attrs["units"] = units
        return frame

    def positions(self) -> pd.DataFrame:
        """Return each fit's value placed among each row source's values, by unit.

        One row per unit, fit source with one value there, and row source with
        a counted value: ``position`` is ``"below"``, ``"within"`` or
        ``"above"`` the row source's ``minimum`` to ``maximum``, and
        ``percentile_rank`` the fit value's rank among them in percent (the
        inverse of Hyndman & Fan definition 7), given within that range from 4
        values. It places the value; it tests nothing.
        """
        columns = [
            *self.by,
            "fit_source",
            "parameter_source",
            "fit_value",
            "count",
            "minimum",
            "maximum",
            "position",
            "percentile_rank",
        ]
        rows = [
            {**r["key"], **{k: v for k, v in r.items() if k != "key"}}
            for r in self.placed
        ]
        frame = pd.DataFrame(rows, columns=columns)
        frame.attrs["units"] = (
            dict.fromkeys(["fit_value", "minimum", "maximum"], self.unit)
            if self.unit
            else {}
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
            for placed in self.placed:
                if tuple(placed["key"].items()) != key:
                    continue
                rank = placed["percentile_rank"]
                at = "" if np.isnan(rank) else f", at P{rank:.0f}"
                lines.append(
                    f"  {placed['fit_source']} {_cell(placed['fit_value'])} is "
                    f"{placed['position']} {placed['parameter_source']} "
                    f"({_cell(placed['minimum'])} to {_cell(placed['maximum'])}{at})"
                )
        return "\n".join([*lines, *self.notes])

    def __repr__(self) -> str:
        return str(self)

    def _repr_html_(self) -> str:
        return f"<pre>{html.escape(str(self))}</pre>"
