"""``select()``: each geology unit's selected value of one parameter (SPEC §5).

Spec: docs/work/m18e-selection.md, decisions 10-17. The selection is a
judgment: the judgments file (or ``selection=``) names, per geology unit, a
source and a method. ``select()`` runs ``compare_sources()`` once, then each
unit's method on that source's rows, and records what was chosen, from what.
"""

import html
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd

from hangtu import _judgments
from hangtu import units as _units
from hangtu.errors import HangtuError, warn
from hangtu.stats import _compare_sources, _representative
from hangtu.stats._compare_sources import PLACE, SourceComparison, percentile_rank
from hangtu.stats._describe import DEFAULT_PERCENTILES, percentile_floor
from hangtu.stats._result import (
    RepresentativeResult,
    _cell,
    _heading,
    _plain,
    _Result,
    _table,
)
from hangtu.stats._rows import BLANK_GROUP

FUNCTION = "select()"
#: A selection is by geology unit only (decision 9).
GEOLOGY = "geology_unit"
#: The comparison's reason for a unit a source has no rows in.
NO_ROWS = "no rows in this unit"
#: The columns of a line, as ``RepresentativeResult.to_frame()`` names them.
LINE = ("line_intercept", "line_slope", "value_top", "value_base")


def select(
    *sources: Any,
    value: str,
    selection: Mapping[str, Any] | None = None,
    include_assumed: bool = False,
    judgments: Any = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> "SelectionResult":
    r"""Select one parameter's value in each geology unit, as the judgments say.

    The selection is a judgment: for each geology unit, the
    judgments file's ``selection`` names the source and the method that give
    the value, or gives the value with its reason. ``select()`` computes it,
    and records what was chosen, from what, and what the other sources gave.
    Engineers choose, hangtu reports: no source, method or side is picked
    for them, and hangtu stops at the selected value, with no partial
    factors.

    **The sources** are ``compare_sources()``'s, compared by
    ``geology_unit`` (``.comparison``): DataFrames of values, labeled by
    their source columns, a ``MohrCoulombFit`` and a
    ``ShearBoxConversion``. A ``source`` in the selection is a
    ``parameter_source`` label of that comparison.

    **The methods**, each entry's ``method``:

    - ``characteristic``, ``percentile`` or ``standard_deviations``:
      :func:`representative` on that source's rows in the unit, the frame as
      passed, with the entry's fields as its arguments (``side``,
      ``distribution``, ``trend``, ``estimate``, ...) and ``judgments=``
      passed through, so ``spt_refusal_upper_limit`` reaches it. A fit
      fitted per sample (several values in the unit) gives its values;
    - ``fitted``: a fit's one value in the unit, as fitted. Select both
      ``effective_cohesion`` and ``effective_friction_angle`` as ``fitted``
      from one ``MohrCoulombFit`` to keep the pair on one line: c′ and φ′
      selected by views of their own aren't a joint fractile;
    - ``value``: the engineer's value, converted to the comparison's unit;
    - ``none``: no value, on purpose, with the reason.

    **Every unit the sources have needs an entry**, ``none`` included; a
    unit no source has may have a ``value`` (or ``none``). A unit whose
    method gives no value (fewer than 2 values, every row left out) is
    listed with ``no_value_reason`` and a warning, and is never filled from
    another source.

    **The other sources** (``.positions()``): a selected constant is placed
    among each other source's values in the unit, below, within or above
    them, with its percentile rank within them from 4 values, as
    :func:`compare_sources` places a fit; against a fit's one value, the
    difference is given instead. It places the value; it tests nothing.

    **Units**: every value is in the comparison's unit (``display_units``,
    else its first source's; angles in degrees). A source in another unit is
    converted, with its depths, before its method is computed.

    **No source**: a parameter nothing measures yet (a dilatancy angle, a
    Poisson's ratio) can be selected with no sources when every entry is
    ``value`` or ``none``. There is nothing to compare or place:
    ``.comparison`` is None, ``.positions()`` is empty, and there is no line
    to draw. The unit is ``display_units``' for the quantity, else the first
    ``value`` entry's, and the other entries are converted to it.

    Parameters
    ----------
    *sources : pandas.DataFrame, MohrCoulombFit or ShearBoxConversion
        As for :func:`compare_sources`; none when every entry is ``value``
        or ``none``.
    value : str
        The parameter, a numeric registry column such as
        ``"effective_friction_angle"`` or ``"undrained_shear_strength"``.
    selection : dict, optional
        ``{geology_unit: entry}``, the whole selection of ``value`` in the
        file's shape, with a value as a quantity: ``{"Clay": {"method":
        "value", "value": "500 psf", "reason": "..."}}``. It replaces the
        file's selection of ``value``, with a warning when there is one.
        None reads it from ``judgments=``, then from the Project's file the
        sources carry.
    include_assumed : bool
        Include assumed values, as for :func:`compare_sources`.
    judgments : Judgments or path, optional
        The judgments file: its ``selection``, and the judgments a method
        reads (``spt_refusal_upper_limit``). By default the Project's.
    units : dict, optional
        ``{column: unit}``, applied to every DataFrame.
    display_units : {"US", "SI"}, optional
        Convert every source to this system's unit.

    Returns
    -------
    SelectionResult
        ``.to_frame()`` has one row per geology unit, with the selected
        value (or line), its method, source and reason; ``.positions()``
        places it among the other sources.

    Raises
    ------
    HangtuError
        For no selection of ``value`` anywhere; a geology unit the sources
        have and the selection doesn't list; a ``source`` that isn't in the
        comparison; ``fitted`` on a row source or a fit with several values
        in the unit, or a view on a fit's one value; a computed method for
        a unit no source has, or with no sources at all; a
        ``selection=`` entry that breaks the file's rules; and the errors of
        :func:`compare_sources` and :func:`representative`.

    Examples
    --------
    >>> uu = p.undrained_strength()
    >>> selected = ht.stats.select(
    ...     uu, value="undrained_shear_strength", judgments=p.judgments
    ... )
    >>> selected.to_frame()
    """
    return select_from(
        sources,
        value=value,
        read=_read_file(sources, judgments),
        selection=selection,
        include_assumed=include_assumed,
        judgments=judgments,
        units=units,
        display_units=display_units,
    )


def select_from(
    sources: Sequence[Any],
    *,
    value: str,
    read: "_judgments.Read | None",
    selection: Mapping[str, Any] | None = None,
    include_assumed: bool = False,
    judgments: Any = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> "SelectionResult":
    """``select()`` with the judgments file already read (``read``).

    A model set reads the file once for every parameter it selects
    (docs/work/m18f-mohr-coulomb-set.md, decision 8); ``judgments`` still
    reaches each method, for the judgments it reads.
    """
    quantity = _judgments.selected_quantity(value, f"{FUNCTION} value=")
    compared: _compare_sources.Compared | None = None
    comparison: SourceComparison | None = None
    if sources:
        compared = _compare_sources.compare(
            sources,
            value,
            GEOLOGY,
            DEFAULT_PERCENTILES,
            include_assumed,
            units,
            display_units,
        )
        comparison = compared.comparison
    chosen, record = _resolve(value, quantity, selection, read, comparison)
    if comparison is None:
        _check_no_source(value, chosen)
        unit = _no_source_unit(chosen, quantity, display_units)
    else:
        unit = comparison.unit
    geologies = [] if comparison is None else _geologies(comparison)
    _check_listed(value, geologies, chosen, comparison)
    context = _Context(
        sources=sources,
        compared=compared,
        value=value,
        quantity=quantity,
        unit=unit,
        include_assumed=include_assumed,
        judgments=judgments,
        units=units,
        display_units=display_units,
    )
    rows, results, placed = [], {}, []
    for name in [*map(str, geologies), *(g for g in chosen if g not in geologies)]:
        place = _place(name, geologies)
        row, result = _select_one(context, name, place, chosen[name])
        rows.append(row)
        if result is not None:
            results[name] = result
        if place is not None:
            placed += _positions(context, row, place)
    _warn_no_value(rows, value)
    if comparison is None:
        later = [
            f"No source carries {value}, so the selection has nothing to compare "
            "or draw."
        ]
        merged: dict[str, Any] = {}
    else:
        _value_depths(rows, comparison, geologies)
        later = _line_notes(rows, results)
        merged = dict(comparison.judgments)
    for result in results.values():
        merged |= result.judgments
    merged[_judgments.SELECTION] = record
    return SelectionResult(
        kind="parameter",
        function="select",
        value=value,
        unit=unit,
        notes=(*_notes(rows, unit), *later),
        judgments=merged,
        hangtu_version=version("hangtu"),
        by=(GEOLOGY,),
        include_assumed=include_assumed,
        display_units=display_units,
        rows=tuple(rows),
        placed=tuple(placed),
        comparison=comparison,
        representatives=results,
    )


@dataclass
class _Context:
    """What every unit's method reads: the sources, the comparison, the call."""

    sources: Sequence[Any]
    #: None with no sources (a ``value`` or ``none`` selection only).
    compared: _compare_sources.Compared | None
    value: str
    quantity: str
    #: The selection's unit: the comparison's, or with no sources decision 20's.
    unit: str | None
    include_assumed: bool
    judgments: Any
    units: Mapping[str, str] | None
    display_units: str | None

    def with_sources(self) -> _compare_sources.Compared:
        """Return the comparison, for a method that reads a source."""
        # Only value and none reach a selection with no sources (decision 20).
        assert self.compared is not None
        return self.compared


def _read_file(sources: Sequence[Any], judgments: Any) -> "_judgments.Read | None":
    """Read ``judgments=``, else the Project's file the first source carries."""
    from hangtu.analysis._judgment_values import read_judgments_file  # imports stats

    for position, source in enumerate(sources, start=1):
        attached = (
            source.attrs.get("judgments_file")
            if isinstance(source, pd.DataFrame)
            else getattr(source, "judgments_file", None)
        )
        if attached is not None:
            return read_judgments_file(judgments, str(attached), f"source {position}")
    return read_judgments_file(judgments, None, "the sources")


def _resolve(
    value: str,
    quantity: str,
    selection: Any,
    read: "_judgments.Read | None",
    comparison: SourceComparison | None,
) -> tuple[dict[str, "_judgments.SelectionEntry"], dict[str, Any]]:
    """Resolve the selection: selection=, then the file (decision 12)."""
    in_file = None if read is None else read.selections.get(value)
    if selection is not None:
        if read is not None and in_file is not None:
            warn(
                f"{FUNCTION} selection= replaces the selection of {value!r} in "
                f"{str(read.path)!r}, for every geology unit; the file's isn't used."
            )
        chosen = _from_argument(selection, quantity)
        return chosen, _record(chosen, "argument")
    if read is not None and in_file is not None:
        return dict(in_file.values), _record(
            in_file.values, str(read.path), read.sha256
        )
    raise HangtuError(_missing(value, read, comparison))


def _from_argument(
    selection: Any, quantity: str
) -> dict[str, "_judgments.SelectionEntry"]:
    """Check ``selection=`` by the file's rules, a value given as a quantity."""
    where = f"{FUNCTION} selection="
    if not isinstance(selection, Mapping):
        raise HangtuError(
            f"{where} maps each geology unit to its entry, e.g. {{'Clay': "
            "{'method': 'value', 'value': '500 psf', 'reason': '...'}}, not "
            f"{selection!r}."
        )
    chosen = {}
    for geology, entry in selection.items():
        here = f"{where}, {geology}"
        unit = None
        if isinstance(entry, Mapping) and entry.get("method") == "value":
            entry, unit = _quantity(entry, quantity, here)
        chosen[str(geology)] = _judgments.check_selection_entry(
            entry, quantity, unit, here
        )
    return chosen


def _quantity(
    entry: Mapping[str, Any], quantity: str, where: str
) -> tuple[dict[str, Any], str | None]:
    """Split a ``value`` entry's quantity, ``"500 psf"``, into a number and unit."""
    given = entry.get("value")
    if not isinstance(given, str):
        if quantity in _judgments.PURE_NUMBERS or given is None:
            return dict(entry), None
        example = _judgments.example_unit(quantity)
        raise HangtuError(
            f"{where}, value: give the value with its unit as text, e.g. "
            f'"26 {example}", not {given!r}.'
        )
    try:
        number, unit = _units.parse_quantity(given, quantity)
    except HangtuError as error:
        raise HangtuError(f"{where}, value: {error}") from None
    return {**entry, "value": number}, unit


def _record(
    chosen: Mapping[str, "_judgments.SelectionEntry"],
    source: str,
    sha256: str | None = None,
) -> dict[str, Any]:
    """Return the selection as ``judgments`` records it: its source and entries."""
    record: dict[str, Any] = {"source": source}
    if sha256 is not None:
        record["sha256"] = sha256
    record["by"] = GEOLOGY
    record["values"] = {
        geology: {
            "method": entry.method,
            **({"source": entry.source} if entry.source else {}),
            **entry.inputs,
            **(
                {}
                if entry.value is None
                else {"value": _judgments.quantity_text(entry.value, entry.unit or "")}
            ),
            "reason": entry.reason,
        }
        for geology, entry in chosen.items()
    }
    return record


def _missing(
    value: str, read: "_judgments.Read | None", comparison: SourceComparison | None
) -> str:
    """Name the parameter and show an entry to add (decision 12)."""
    where = (
        f"{str(read.path)!r} has no selection of it"
        if read is not None
        else "no judgments file was given, and the sources carry none"
    )
    start = (
        f"{FUNCTION} has no selection of {value!r}: {where}. The selection is a "
        "judgment, with no default. Add it to the judgments file and "
        "pass judgments=ht.judgments(path), or give selection=. Example:\n"
        "selection:\n"
        f"  {value}:\n"
        "    values:\n"
    )
    if comparison is None:
        quantity = _judgments.selected_quantity(value, FUNCTION)
        given = (
            "1"
            if quantity in _judgments.PURE_NUMBERS
            else f'"1 {_judgments.example_unit(quantity)}"'
        )
        return (
            f"{start}"
            "      Terrace:\n"
            "        method: value\n"
            f"        value: {given}\n"
            '        reason: "from the design report"'
        )
    labels = [s["parameter_source"] for s in comparison.sources]
    geology = next(
        (
            str(r["key"][GEOLOGY])
            for r in comparison.rows
            if r["no_value_reason"] is None
        ),
        "Terrace",
    )
    return (
        f"{start}"
        f"      {geology}:\n"
        f'        source: "{labels[0]}"\n'
        "        method: characteristic\n"
        "        estimate: mean\n"
        "        side: low\n"
        "        distribution: normal\n"
        '        reason: "a mean over a long slip surface"'
    )


def _check_no_source(
    value: str, chosen: Mapping[str, "_judgments.SelectionEntry"]
) -> None:
    """With no sources, only ``value`` and ``none`` (decision 20)."""
    computed = [
        f"{geology} ({entry.method})"
        for geology, entry in chosen.items()
        if entry.method not in ("value", "none")
    ]
    if computed:
        raise HangtuError(
            f"{FUNCTION}: no source carries {value!r}, so the selection can't "
            f"compute {', '.join(computed)}. With no sources, give each unit "
            "method: value with its value and reason, or method: none; or pass "
            "the sources that carry it."
        )


def _no_source_unit(
    chosen: Mapping[str, "_judgments.SelectionEntry"],
    quantity: str,
    display_units: str | None,
) -> str | None:
    """Return the unit with no sources: display_units', else the first value's."""
    given = [e for e in chosen.values() if e.method == "value"]
    if not given:
        return None
    first = given[0]
    if display_units is None:
        return first.unit
    _, unit = _units.to_display([0.0], first.unit, quantity, display_units)
    return unit


def _geologies(comparison: SourceComparison) -> list[Any]:
    """Every geology unit any source has, in the comparison's order."""
    return list(dict.fromkeys(r["key"][GEOLOGY] for r in comparison.rows))


def _place(name: str, geologies: list[Any]) -> tuple[Any, ...] | None:
    """Return the comparison's key of unit ``name``; None if no source has it."""
    return next(((g,) for g in geologies if str(g) == name), None)


def _check_listed(
    value: str,
    geologies: list[Any],
    chosen: Mapping[str, "_judgments.SelectionEntry"],
    comparison: SourceComparison | None,
) -> None:
    """Raise for a unit not listed, or computed with no source (decision 10)."""
    missing = [str(g) for g in geologies if str(g) not in chosen]
    if missing:
        raise HangtuError(
            f"{FUNCTION}: the selection of {value!r} doesn't list "
            f"{', '.join(map(repr, missing))}, which the sources have. Add an entry "
            "for each, or method: none with a reason to give no value on purpose, "
            f'e.g. {missing[0]}: {{method: none, reason: "not used in design"}}.'
        )
    names = {str(g) for g in geologies}
    for geology, entry in chosen.items():
        if geology in names or entry.method in ("value", "none"):
            continue
        raise HangtuError(
            f"{FUNCTION}: the selection of {value!r} computes {geology!r} by "
            f"{entry.method} from {entry.source!r}, but no source has a geology unit "
            f"{geology!r}. The units are {', '.join(map(repr, sorted(names)))}. "
            "Correct the name, or give a value with method: value."
        )


def _row(
    geology: str,
    entry: "_judgments.SelectionEntry",
    **values: Any,
) -> dict[str, Any]:
    """One unit's row: its method, source and reason, and what it gave."""
    return {
        "key": {GEOLOGY: geology},
        "parameter_source": entry.source,
        "selection_method": entry.method,
        "value": np.nan,
        **dict.fromkeys(LINE, np.nan),
        "vertical": None,
        "vertical_top": np.nan,
        "vertical_base": np.nan,
        "count": np.nan,
        "selection_reason": entry.reason,
        "no_value_reason": None,
        "entry": entry,
        #: A fitted value's points' shallowest and deepest depth.
        "depths": (np.nan, np.nan),
        **values,
    }


def _positions(
    context: _Context, row: dict[str, Any], place: tuple[Any, ...]
) -> list[dict[str, Any]]:
    """Place the selected value among each other source's values (decision 14).

    A row source's values (or a fit's per-sample values) give a position and,
    within their range and from 4 values, a percentile rank; a fit's one value
    gives the difference instead. A line has no single value to place.
    """
    selected = row["value"]
    line = row["vertical"]
    if line is None and not np.isfinite(selected):
        return []
    placed = []
    for source in context.with_sources().sources:
        if source.label == row["parameter_source"]:
            continue  # the selected source isn't placed against itself
        if source.kind == "rows":
            data = source.rows
            assert data is not None  # a row source
            values = data.numbers[source.mask(place) & (data.reasons == "")]
        else:
            assert source.fits is not None  # a fit source
            values = np.array(
                [e["value"] for e in source.fits.get(place, [])], dtype=float
            )
            values = values[np.isfinite(values)]
        if not values.size:
            continue
        record: dict[str, Any] = {
            "key": row["key"],
            "selected_source": row["parameter_source"],
            "parameter_source": source.label,
            "source_kind": source.kind,
            "selected_value": selected,
            "fit_value": np.nan,
            "difference": np.nan,
            "count": int(values.size),
            "minimum": float(values.min()),
            "maximum": float(values.max()),
            "position": None,
            "percentile_rank": np.nan,
            "no_position_reason": None,
        }
        placed.append(record)
        if line is not None:
            record["no_position_reason"] = f"a line with {line}"
        elif source.kind == "fit" and values.size == 1:
            record["fit_value"] = float(values[0])
            record["difference"] = float(selected - values[0])
            record["minimum"] = record["maximum"] = np.nan
        else:
            x = np.sort(values)
            record["position"] = (
                "below"
                if selected < x[0]
                else "above"
                if selected > x[-1]
                else "within"
            )
            if record["position"] == "within" and x.size >= percentile_floor(25):
                record["percentile_rank"] = percentile_rank(x, selected)
    return placed


def _select_one(
    context: _Context,
    geology: str,
    place: tuple[Any, ...] | None,
    entry: "_judgments.SelectionEntry",
) -> tuple[dict[str, Any], RepresentativeResult | None]:
    """Apply one unit's method."""
    if entry.method == "none":
        return _row(geology, entry), None
    if entry.method == "value":
        return _row(geology, entry, value=_given_value(context, entry)), None
    assert place is not None  # checked: a computed method needs a source
    source = _source(context, geology, place, entry)
    if source.kind == "fit":
        return _from_fit(context, geology, place, entry, source)
    return _from_rows(context, geology, place, entry, source)


def _from_fit(
    context: _Context,
    geology: str,
    place: tuple[Any, ...],
    entry: "_judgments.SelectionEntry",
    source: _compare_sources._Source,
) -> tuple[dict[str, Any], RepresentativeResult | None]:
    """Take a fit's one value as fitted, or its per-sample values to a view."""
    assert source.fits is not None  # a fit source
    fitted = source.fits.get(place, [])
    computed = ", ".join(_representative.METHODS)
    if not fitted:
        return _row(geology, entry, no_value_reason=NO_ROWS), None
    if entry.method == "fitted":
        if len(fitted) > 1:
            raise HangtuError(
                f"{FUNCTION}: {geology!r} selects fitted from {source.label!r}, "
                f"which has {len(fitted)} values in this unit (fitted per sample), "
                f"so there is no one fitted value. Choose {computed}, which compute "
                "a value from them."
            )
        (one,) = fitted
        no_value = None if np.isfinite(one["value"]) else str(one["reason"])
        top, base = _compare_sources._range(one["depths"])
        return (
            _row(
                geology,
                entry,
                value=one["value"] if no_value is None else np.nan,
                count=int(one["count_points"]),
                no_value_reason=no_value,
                depths=(top, base),
            ),
            None,
        )
    if len(fitted) == 1:
        raise HangtuError(
            f"{FUNCTION}: {geology!r} selects {entry.method} from {source.label!r}, "
            "which has one fitted value in this unit, not values to compute a "
            "representative value from. Choose fitted to take it as fitted."
        )
    values = _fit_values(context, geology, place, source.label)
    result = _representative.representative(
        values,
        value=context.value,
        by=GEOLOGY,
        method=entry.method,
        include_assumed=context.include_assumed,
        judgments=context.judgments,
        units=None,
        display_units=None,  # .values() is in the comparison's units already
        **entry.inputs,
    )
    return _from_result(geology, entry, result), result


def _fit_values(
    context: _Context, geology: str, place: tuple[Any, ...], label: str
) -> pd.DataFrame:
    """Return a per-sample fit's values in the unit, as ``.values()`` draws them."""
    values = context.with_sources().comparison.values()
    cells = values[GEOLOGY].astype(object)
    in_unit = (
        cells.isna() if place[0] == BLANK_GROUP else (cells == place[0]) & cells.notna()
    )
    rows = values[in_unit & (values["parameter_source"] == label)].copy()
    rows[GEOLOGY] = geology
    rows.attrs = dict(values.attrs)
    return rows


def _given_value(context: _Context, entry: "_judgments.SelectionEntry") -> float:
    """Return a ``value`` entry in the selection's unit (decisions 13, 20)."""
    assert entry.value is not None  # a value entry has one
    if entry.unit is None or context.unit is None:
        return float(entry.value)
    if context.display_units is not None:
        converted, _ = _units.to_display(
            [entry.value], entry.unit, context.quantity, context.display_units
        )
    else:
        converted = _units.convert(
            [entry.value],
            _units.parse_unit(entry.unit),
            context.quantity,
            _units.parse_unit(context.unit),
        )
    return float(converted[0])


def _source(
    context: _Context,
    geology: str,
    place: tuple[Any, ...],
    entry: "_judgments.SelectionEntry",
) -> _compare_sources._Source:
    """Find the entry's source in the comparison, else list those in the unit."""
    for source in context.with_sources().sources:
        if source.label == entry.source:
            return source
    comparison = context.with_sources().comparison
    there = [
        r["parameter_source"]
        for r in comparison.rows
        if tuple(r["key"].values()) == place and r["no_value_reason"] != NO_ROWS
    ]
    raise HangtuError(
        f"{FUNCTION}: {geology!r} selects from {entry.source!r}, which isn't a "
        "source of the comparison. The sources with rows in this unit are "
        f"{', '.join(map(repr, there)) or 'none'}; write the label as "
        "compare_sources() gives it in parameter_source."
    )


def _from_rows(
    context: _Context,
    geology: str,
    place: tuple[Any, ...],
    entry: "_judgments.SelectionEntry",
    source: _compare_sources._Source,
) -> tuple[dict[str, Any], RepresentativeResult | None]:
    """Compute a representative() method on a row source's rows in the unit."""
    if entry.method not in _representative.METHODS:
        raise HangtuError(
            f"{FUNCTION}: {geology!r} selects {entry.method} from "
            f"{source.label!r}, a source of rows, which has no single fitted value. "
            f"Choose {', '.join(_representative.METHODS)}, which compute a value "
            "from its rows."
        )
    summary = _comparison_row(context, place, source.label)
    if summary["statistics"]["count"] == 0:
        return _row(geology, entry, no_value_reason=summary["no_value_reason"]), None
    frame = context.sources[source.position - 1]
    rows = _rows_in_units(frame, source.mask(place), context)
    result = _representative.representative(
        rows,
        value=context.value,
        by=GEOLOGY,
        method=entry.method,
        include_assumed=context.include_assumed,
        judgments=context.judgments,
        units=None,
        display_units=context.display_units,
        **entry.inputs,
    )
    return _from_result(geology, entry, result), result


def _comparison_row(
    context: _Context, place: tuple[Any, ...], label: str
) -> dict[str, Any]:
    """Return the comparison's record of one unit and source."""
    return next(
        r
        for r in context.with_sources().comparison.rows
        if tuple(r["key"].values()) == place and r["parameter_source"] == label
    )


def _rows_in_units(
    frame: pd.DataFrame, mask: np.ndarray, context: _Context
) -> pd.DataFrame:
    """Return the unit's rows of ``frame``, in the comparison's units.

    Numbers in the value column, its bands and the place columns are
    converted to the comparison's units; text cells (NP, refusal) are kept,
    so the rows reach representative() as they would reach fit(). With
    display_units, representative() converts them itself.
    """
    rows = frame.loc[mask].copy()
    declared = {**_units.units_of(frame), **(context.units or {})}
    if GEOLOGY in rows.columns:
        # One unit's rows: a categorical's other categories would be groups.
        rows[GEOLOGY] = rows[GEOLOGY].astype(object)
    comparison = context.with_sources().comparison
    if context.display_units is None:
        value = context.value
        targets = {
            column: (comparison.unit, context.quantity)
            for column in (value, f"{value}_lower", f"{value}_upper")
        } | {column: (comparison.depth_unit, "length") for column in PLACE}
        for column, (target, quantity) in targets.items():
            given = declared.get(column)
            if column not in rows.columns or given is None or target is None:
                continue
            if _units.quantity_kind(quantity)["canonical"] is None:
                continue  # a pure number or a percent isn't converted
            rows[column] = _convert(rows[column], given, quantity, target)
            declared[column] = target
    rows.attrs = {**frame.attrs, "units": declared}
    return rows


def _convert(cells: pd.Series, given: str, quantity: str, target: str) -> pd.Series:
    """Convert a column's numbers, keeping its text cells as written."""
    numbers = pd.to_numeric(cells, errors="coerce")
    converted = pd.Series(
        _units.convert(
            numbers.to_numpy(dtype=float),
            _units.parse_unit(given),
            quantity,
            _units.parse_unit(target),
        ),
        index=cells.index,
    )
    if numbers.notna().sum() == cells.notna().sum():
        return converted
    kept = cells.astype(object).copy()
    kept[numbers.notna()] = converted[numbers.notna()]
    return kept


def _from_result(
    geology: str, entry: "_judgments.SelectionEntry", result: RepresentativeResult
) -> dict[str, Any]:
    """One unit's row from its representative() result (one group)."""
    (group,) = result.groups
    frame = result.to_frame()
    found: dict[str, Any] = {
        "count": group["counts"]["count"],
        "no_value_reason": group["reason"],
    }
    if result.trend is None:
        found["value"] = group["value"]
    elif group["reason"] is None:
        found |= {name: frame[name].iloc[0] for name in LINE}
        found["vertical"] = result.trend
        found["vertical_top"] = frame[f"{result.trend}_top"].iloc[0]
        found["vertical_base"] = frame[f"{result.trend}_base"].iloc[0]
    return _row(geology, entry, **found)


def _value_depths(
    rows: list[dict[str, Any]], comparison: SourceComparison, geologies: list[Any]
) -> None:
    """Give each ``value`` unit the depths of every source's rows in it.

    A given value is drawn as a constant over them (decision 15); a unit no
    source has, or whose rows have no depth, has none.
    """
    values = comparison.values()
    ends = [name for name in ("depth", "depth_top", "depth_base") if name in values]
    if not ends:
        return
    cells = values[GEOLOGY].astype(object)
    for row in rows:
        place = _place(row["key"][GEOLOGY], geologies)
        if row["selection_method"] != "value" or place is None:
            continue
        in_unit = (
            cells.isna()
            if place[0] == BLANK_GROUP
            else (cells == place[0]) & cells.notna()
        )
        depths = values.loc[in_unit, ends].to_numpy(dtype=float).ravel()
        row["depths"] = _compare_sources._range(depths)


def _line_notes(
    rows: list[dict[str, Any]], results: Mapping[str, RepresentativeResult]
) -> list[str]:
    """Name each unit with a value that ``.design_lines()`` can't draw."""
    notes = []
    for row in rows:
        geology = row["key"][GEOLOGY]
        if not _has_value(row):
            continue
        if geology in results:
            drawable = results[geology].vertical is not None
        else:
            drawable = bool(np.isfinite(row["depths"]).all())
        if not drawable:
            notes.append(
                f"{geology}: no source has rows with a depth in this unit, so "
                ".design_lines() has no line for its selected value."
            )
    return notes


def _has_value(row: Mapping[str, Any]) -> bool:
    """Whether a unit's row has a selected value or line."""
    return row["vertical"] is not None or bool(np.isfinite(row["value"]))


def _warn_no_value(rows: list[dict[str, Any]], value: str) -> None:
    """Warn about units whose method gave no value (decision 13)."""
    listed = [
        f"{r['key'][GEOLOGY]} ({r['no_value_reason']})"
        for r in rows
        if r["no_value_reason"] is not None
    ]
    if listed:
        warn(
            f"{FUNCTION} gives no value of {value!r} in {', '.join(listed)}: the "
            "method gave none. They are listed with no_value_reason and aren't "
            "filled from another source; choose another method or source, or "
            "method: none."
        )


def _notes(rows: list[dict[str, Any]], unit: str | None) -> list[str]:
    """One line per unit: what was chosen, from what, and why (decision 16)."""
    notes = []
    for row in rows:
        entry = row["entry"]
        chosen = ", ".join(
            part for part in (row["parameter_source"], entry.method) if part
        )
        if row["no_value_reason"] is not None:
            what = f"no value, {row['no_value_reason']}"
        elif entry.method == "none":
            what = "no value"
        elif row["vertical"] is not None:
            what = (
                f"a line with {row['vertical']}, {_cell(row['value_top'])} to "
                f"{_cell(row['value_base'])}{f' {unit}' if unit else ''}"
            )
        else:
            what = _judgments.quantity_text(row["value"], unit or "")
        notes.append(f"{row['key'][GEOLOGY]}: {chosen}: {what} ({entry.reason}).")
    return notes


def _text(value: Any) -> str:
    """Show a cell of the summary: text as written, a number as ``_cell`` does."""
    if isinstance(value, str):
        return value
    return _cell(None if pd.isna(value) else value)


def _placed_text(placed: Mapping[str, Any]) -> str:
    """One line of the summary's positions: the selected value against a source."""
    other = placed["parameter_source"]
    if placed["no_position_reason"] is not None:
        return f"{other}: no position ({placed['no_position_reason']})"
    if placed["position"] is None:
        difference = placed["difference"]
        side = "above" if difference > 0 else "below" if difference < 0 else ""
        by = f" {_cell(abs(difference))} {side}" if side else " equal to"
        return (
            f"{_cell(placed['selected_value'])} is{by} {other}, "
            f"{_cell(placed['fit_value'])}"
        )
    rank = placed["percentile_rank"]
    at = "" if np.isnan(rank) else f", at P{rank:.0f}"
    return (
        f"{_cell(placed['selected_value'])} is {placed['position']} {other} "
        f"({_cell(placed['minimum'])} to {_cell(placed['maximum'])}{at})"
    )


@dataclass(frozen=True, repr=False)
class SelectionResult(_Result):
    """The selection ``ht.stats.select()`` returns: one value per geology unit.

    Use ``.to_frame()`` for a table with one row per unit, ``.comparison``
    for the sources side by side, and ``.representative(geology_unit)`` for
    the statistics behind a computed value.
    """

    #: The column selected by: always ``("geology_unit",)``.
    by: tuple[str, ...]
    include_assumed: bool
    #: The system every source was converted to, or None.
    display_units: str | None
    #: One record per unit: its key, method, source, value or line, count,
    #: reason and ``no_value_reason``.
    rows: tuple[dict[str, Any], ...]
    #: One record per unit and other source: the rows of ``.positions()``.
    placed: tuple[dict[str, Any], ...]
    #: The sources side by side, as ``compare_sources()`` gives them; None
    #: for a selection with no sources (every entry ``value`` or ``none``).
    comparison: SourceComparison | None = field(compare=False)
    #: Each computed unit's ``representative()`` result, by unit.
    representatives: dict[str, RepresentativeResult] = field(compare=False)

    def representative(self, geology_unit: str) -> RepresentativeResult:
        """Return the ``representative()`` result behind one unit's value."""
        if geology_unit in self.representatives:
            return self.representatives[geology_unit]
        for row in self.rows:
            if row["key"][GEOLOGY] == geology_unit:
                raise HangtuError(
                    f"SelectionResult.representative(): {geology_unit!r} is "
                    f"selected by {row['selection_method']}, not by "
                    "representative(), so it has no representative result."
                    + (
                        f" Its method gave no value: {row['no_value_reason']}."
                        if row["no_value_reason"]
                        else ""
                    )
                )
        units = ", ".join(repr(row["key"][GEOLOGY]) for row in self.rows)
        raise HangtuError(
            f"SelectionResult.representative(): no geology unit {geology_unit!r}. "
            f"Units: {units}."
        )

    def positions(self) -> pd.DataFrame:
        """Return each unit's selected value placed among its other sources.

        One row per unit with a value and each other source with a counted
        value there. Against a row source (or a fit's per-sample values),
        ``position`` is ``"below"``, ``"within"`` or ``"above"`` its
        ``minimum`` to ``maximum``, and ``percentile_rank`` the selected
        value's rank among them in percent (the inverse of Hyndman & Fan
        definition 7), within that range and from 4 values. Against a fit's
        one value, ``fit_value`` and ``difference`` (selected - fit) instead.
        A selected line has no single value, so ``position`` is blank, with
        ``no_position_reason``. It places the value; it tests nothing.
        """
        columns = [
            GEOLOGY,
            "selected_source",
            "parameter_source",
            "source_kind",
            "selected_value",
            "fit_value",
            "difference",
            "count",
            "minimum",
            "maximum",
            "position",
            "percentile_rank",
            "no_position_reason",
        ]
        rows = [
            {**r["key"], **{k: v for k, v in r.items() if k != "key"}}
            for r in self.placed
        ]
        frame = pd.DataFrame(rows, columns=columns)
        with_unit = ["selected_value", "fit_value", "difference", "minimum", "maximum"]
        frame.attrs["units"] = dict.fromkeys(with_unit, self.unit) if self.unit else {}
        return frame

    def design_lines(self) -> pd.DataFrame:
        """Return the selected lines P01 draws, as ``ht.template("design_lines")``.

        One line per geology unit with a value, labeled
        ``"<unit>: selected, <method>"``. A ``representative()`` method gives
        that result's line (``RepresentativeResult.design_lines()``); a
        ``fitted`` value is a constant over its points' depths; a ``value`` a
        constant over the depths of every source's rows in the unit. A unit
        with no depths to draw at has no line, and a note says so.
        ``attrs["units"]`` gives the depth's (elevation's) unit and the
        value's. Pass it to ``ht.plot.profile(..., design_lines=)``, or draw
        ``.profile()``.

        Raises
        ------
        HangtuError
            When one unit's line is by depth and another's by elevation, so
            the lines can't share a table; and for a selection with no
            sources, which has no depths to draw at.
        """
        self._check_drawable("design_lines")
        return self._lines(self.rows)

    def _check_drawable(self, view: str) -> None:
        if self.comparison is None:
            raise HangtuError(
                f"SelectionResult.{view}(): no source carries {self.value}, so "
                "the selection has nothing to draw: each value was given, with no "
                "rows or depths. Pass the sources to select() to draw them."
            )

    def _lines(self, rows: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        units: dict[str, str] = {}
        for row in rows:
            geology = row["key"][GEOLOGY]
            if not _has_value(row):
                continue
            label = f"{geology}: selected, {row['selection_method']}"
            result = self.representatives.get(geology)
            if result is not None:
                if result.vertical is None:
                    continue
                lines = result.design_lines()
                units |= lines.attrs["units"]
                frames.append(lines.assign(label=label))
                continue
            top, base = row["depths"]
            if not (np.isfinite(top) and np.isfinite(base)):
                continue
            assert self.comparison is not None  # depths come from a source
            if self.comparison.depth_unit is not None:
                units["depth"] = self.comparison.depth_unit
            frames.append(
                pd.DataFrame(
                    {"label": label, "depth": [top, base], "value": row["value"]}
                )
            )
        verticals = {
            name for frame in frames for name in frame.columns if name != "label"
        } - {"value"}
        if len(verticals) > 1:
            raise HangtuError(
                "SelectionResult.design_lines(): some units' lines are by depth and "
                "others by elevation, so they can't share one table. Select every "
                "unit's trend with depth, or draw each unit with .profile()."
            )
        vertical = verticals.pop() if verticals else "depth"
        if frames:
            frame = pd.concat(frames, ignore_index=True)[["label", vertical, "value"]]
        else:
            frame = pd.DataFrame(columns=["label", vertical, "value"])
        frame[[vertical, "value"]] = frame[[vertical, "value"]].astype(float)
        if self.unit is not None:
            units["value"] = self.unit
        frame.attrs["units"] = {
            name: units[name] for name in (vertical, "value") if name in units
        }
        return frame

    def profile(self, geology_unit: str | None = None, **kwargs: Any) -> Any:
        """Draw one unit's sources with the line selected from them (P01).

        The comparison's ``.profile()`` of that unit, with
        ``design_lines=`` its selected line, so the figure shows the sources
        and the value chosen from them, against depth (elevation for a trend
        with elevation). ``geology_unit`` is required when the comparison has
        more than one unit. Other keyword arguments go to
        ``SourceComparison.profile()`` and ``ht.plot.profile()``, a
        ``design_lines=`` of your own replacing the selected line. Returns
        ``(fig, ax)``. A selection with no sources has nothing to draw, and
        raises.
        """
        self._check_drawable("profile")
        assert self.comparison is not None  # checked
        if geology_unit is None:
            rows: Sequence[Mapping[str, Any]] = self.rows
            chosen: dict[str, Any] = {}
        else:
            rows = [r for r in self.rows if r["key"][GEOLOGY] == str(geology_unit)]
            chosen = {GEOLOGY: geology_unit}
        lines = self._lines(rows)
        options: dict[str, Any] = {}
        if len(lines):
            # Against the lines' own vertical: depth lines can't be drawn
            # against elevation when the holes' ground levels differ.
            vertical = next(n for n in lines.columns if n not in ("label", "value"))
            options = {"design_lines": lines, "vs": vertical}
        options |= kwargs
        return self.comparison.profile(**chosen, **options)

    def _vertical_columns(self) -> list[str]:
        verticals = list(
            dict.fromkeys(r["vertical"] for r in self.rows if r["vertical"])
        )
        return [
            f"{v}_{end}" for v in (verticals or ["depth"]) for end in ("top", "base")
        ]

    def to_frame(self) -> pd.DataFrame:
        """Return one row per geology unit: the selected value or line, and why.

        Units in the comparison's order, then those no source has.
        ``attrs["units"]`` gives the unit of each column that has one.
        """
        verticals = self._vertical_columns()
        columns = [
            GEOLOGY,
            "parameter_source",
            "selection_method",
            "value",
            "line_intercept",
            "line_slope",
            *verticals,
            "value_top",
            "value_base",
            "count",
            "selection_reason",
            "no_value_reason",
        ]
        rows = []
        for row in self.rows:
            ends = {name: np.nan for name in verticals}
            if row["vertical"] is not None:
                ends[f"{row['vertical']}_top"] = row["vertical_top"]
                ends[f"{row['vertical']}_base"] = row["vertical_base"]
            rows.append(
                {
                    **row["key"],
                    **{n: row[n] for n in columns if n in row and n != GEOLOGY},
                    **ends,
                }
            )
        frame = pd.DataFrame(rows, columns=columns)
        frame["count"] = frame["count"].astype("Int64")
        units: dict[str, str] = {}
        if self.unit is not None:
            units |= dict.fromkeys(["value", "value_top", "value_base"], self.unit)
        if self.comparison is not None and self.comparison.depth_unit is not None:
            units |= dict.fromkeys(verticals, self.comparison.depth_unit)
        frame.attrs["units"] = units
        return frame

    def to_dict(self) -> dict[str, Any]:
        """Return every field, JSON-serializable (NaN as None).

        The comparison and each ``representative()`` result give their own
        ``.to_dict()``.
        """
        rows = [
            {
                **{k: v for k, v in row.items() if k != "entry"},
                "entry": _record({"": row["entry"]}, "")["values"][""],
            }
            for row in self.rows
        ]
        return _plain(
            {
                "kind": self.kind,
                "function": self.function,
                "value": self.value,
                "unit": self.unit,
                "notes": self.notes,
                "judgments": self.judgments,
                "hangtu_version": self.hangtu_version,
                "by": self.by,
                "include_assumed": self.include_assumed,
                "display_units": self.display_units,
                "rows": rows,
                "positions": self.placed,
                "comparison": (
                    None if self.comparison is None else self.comparison.to_dict()
                ),
                "representatives": {
                    name: result.to_dict()
                    for name, result in self.representatives.items()
                },
            }
        )

    def __str__(self) -> str:
        frame = self.to_frame()
        shown = [
            name
            for name in frame.columns
            if name not in (GEOLOGY, "selection_reason", "no_value_reason")
            and frame[name].notna().any()
        ]
        title = f"{self.value}" + (f" ({self.unit})" if self.unit else "")
        lines = [f"{title}, selected by geology_unit"]
        table = [["", *(_heading(name) for name in shown)]]
        for _, row in frame.iterrows():
            table.append([str(row[GEOLOGY]), *(_text(row[name]) for name in shown)])
        lines += _table(table, indent="  ")
        if self.placed:
            lines.append("Against the other sources")
        for placed in self.placed:
            lines.append(f"  {placed['key'][GEOLOGY]}: {_placed_text(placed)}")
        return "\n".join([*lines, *self.notes])

    def __repr__(self) -> str:
        return str(self)

    def _repr_html_(self) -> str:
        return f"<pre>{html.escape(str(self))}</pre>"
