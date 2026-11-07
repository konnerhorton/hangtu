"""The base every model set is built on (SPEC §5, "Model sets").

Spec: docs/work/m18f-mohr-coulomb-set.md, decisions 5-8. A model set is one
value per geology unit and parameter, each with where it came from: a
selection (``select()``), a rule with its citation, a judgment, or blank
with a reason. A set is a function that builds the records and a thin
subclass that names the model; this module knows no model. It gives the
views, the checks every set makes, and the reading of selections through
``select()``.
"""

import html
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from importlib.metadata import version
from typing import Any, Self

import numpy as np
import pandas as pd

from hangtu import _judgments
from hangtu.errors import HangtuError
from hangtu.stats import _select
from hangtu.stats._result import _cell, _plain, _Result, _table
from hangtu.stats._select import GEOLOGY, SelectionResult

#: The origins of a set's value (decision 5).
ORIGINS = ("selection", "rule", "judgment", "blank")


# --- Records (decision 5) -------------------------------------------------------------


def _record(
    geology_unit: str,
    parameter: str,
    origin: str,
    value: float = np.nan,
    unit: str | None = None,
    **fields: Any,
) -> dict[str, Any]:
    """One unit's value of one parameter, with every field the base records."""
    assert origin in ORIGINS
    has_value = bool(np.isfinite(value))
    return {
        "geology_unit": geology_unit,
        "parameter": parameter,
        "value": float(value) if has_value else np.nan,
        "unit": unit if has_value else None,
        "origin": origin,
        "selection": None,
        "rule": None,
        "judgment": None,
        "no_value_reason": None,
        "notes": (),
        **fields,
    }


def from_selection(
    result: SelectionResult, geology_unit: str, parameter: str
) -> dict[str, Any]:
    """Return a unit's record from ``select()``'s row for it."""
    row = next(r for r in result.rows if r["key"][GEOLOGY] == geology_unit)
    reason = row["no_value_reason"]
    if reason is None and row["selection_method"] == "none":
        reason = f"selected none ({row['selection_reason']})"
    return _record(
        geology_unit,
        parameter,
        "selection",
        row["value"],
        result.unit,
        selection={
            "parameter_source": row["parameter_source"],
            "selection_method": row["selection_method"],
            "selection_reason": row["selection_reason"],
        },
        no_value_reason=reason,
    )


def from_rule(
    geology_unit: str,
    parameter: str,
    value: float,
    unit: str | None,
    *,
    name: str,
    citation: str,
    inputs: Sequence[Mapping[str, Any]],
    no_value_reason: str | None = None,
    notes: Sequence[str] = (),
) -> dict[str, Any]:
    """Return a value a rule gives, with its citation and its inputs.

    Each input is ``{"name", "symbol", "value", "unit", "origin"}``, with
    ``"text"`` for a judgment as the file wrote it: the origin says where
    the rule's input came from (``"selected"``, ``"judgment"``), so the
    reader sees what the value rests on.
    """
    return _record(
        geology_unit,
        parameter,
        "rule",
        value,
        unit,
        rule={"name": name, "citation": citation, "inputs": [dict(i) for i in inputs]},
        no_value_reason=no_value_reason,
        notes=tuple(notes),
    )


def from_judgment(
    geology_unit: str,
    parameter: str,
    value: float,
    unit: str | None,
    *,
    name: str,
    key: str,
    source: str,
) -> dict[str, Any]:
    """Return a value taken as a judgment, with its name, key and source (SPEC §4)."""
    return _record(
        geology_unit,
        parameter,
        "judgment",
        value,
        unit,
        judgment={"name": name, "key": key, "source": source},
    )


def blank(geology_unit: str, parameter: str, reason: str) -> dict[str, Any]:
    """Return a parameter with no value in the unit, and why."""
    return _record(geology_unit, parameter, "blank", no_value_reason=reason)


# --- The checks every set makes, and the selections (decision 8) ---------------------


def read_selections(
    function: str,
    sources: Sequence[Any],
    parameters: Mapping[str, bool],
    *,
    selection: Mapping[str, Any] | None,
    include_assumed: bool,
    judgments: Any,
    units: Mapping[str, str] | None,
    display_units: str | None,
) -> tuple[dict[str, SelectionResult], "_judgments.Read | None"]:
    """Select each of the set's parameters with ``select()``, the file read once.

    ``parameters`` maps each parameter to whether it is required: a required
    one is always selected (``select()`` raising for no selection), an
    optional one only when ``selection=`` or the file has a selection of it.
    Each parameter's ``select()`` gets only the sources that carry it. A
    source that carries none of the parameters, and a selection that gives
    a line (``trend:``), are errors.
    """
    given = _check_selection(function, selection, parameters)
    carriers = _route(function, sources, parameters)
    read = _select._read_file(sources, judgments)
    results: dict[str, SelectionResult] = {}
    for parameter, required in parameters.items():
        in_file = read is not None and parameter in read.selections
        if not (required or parameter in given or in_file):
            continue
        result = _select.select_from(
            carriers[parameter],
            value=parameter,
            read=read,
            selection=given.get(parameter),
            include_assumed=include_assumed,
            judgments=judgments,
            units=units,
            display_units=display_units,
        )
        _check_constant(function, parameter, result)
        results[parameter] = result
    return results, read


def _check_selection(
    function: str, selection: Any, parameters: Mapping[str, bool]
) -> dict[str, Any]:
    if selection is None:
        return {}
    names = ", ".join(parameters)
    if not isinstance(selection, Mapping):
        raise HangtuError(
            f"{function} selection= maps each parameter to its selection, "
            "{parameter: {geology_unit: entry}}, e.g. {'effective_friction_angle': "
            "{'Terrace': {'method': 'value', 'value': '34 deg', 'reason': '...'}}}, "
            f"not {selection!r}. The parameters are {names}."
        )
    unknown = [str(p) for p in selection if p not in parameters]
    if unknown:
        raise HangtuError(
            f"{function} selection= has {', '.join(map(repr, unknown))}, which "
            f"isn't a parameter of the set. The parameters are {names}."
        )
    return dict(selection)


def carries(source: Any, parameter: str) -> bool:
    """Whether a source gives ``parameter``: a column, or a fit's value of it."""
    from hangtu.analysis import MohrCoulombFit, ShearBoxConversion  # imports stats

    if isinstance(source, pd.DataFrame):
        return parameter in source.columns
    if isinstance(source, MohrCoulombFit):
        return parameter in source._value_names()
    if isinstance(source, ShearBoxConversion):
        return parameter == "effective_friction_angle"
    return False


def _route(
    function: str, sources: Sequence[Any], parameters: Mapping[str, bool]
) -> dict[str, list[Any]]:
    """Give each parameter the sources that carry it; none carrying any is an error."""
    from hangtu.analysis import ShearBoxFit  # analysis imports stats

    carriers: dict[str, list[Any]] = {parameter: [] for parameter in parameters}
    for position, source in enumerate(sources, start=1):
        found = [p for p in parameters if carries(source, p)]
        if not found:
            what = (
                "a DataFrame"
                if isinstance(source, pd.DataFrame)
                else f"a {type(source).__name__}"
            )
            hint = (
                " Its φ′ is a direct shear one: convert it with "
                "ht.analysis.friction_angle_from_shear_box() and pass the conversion."
                if isinstance(source, ShearBoxFit)
                else ""
            )
            raise HangtuError(
                f"{function} source {position} ({what}) gives none of the set's "
                f"parameters, {', '.join(parameters)}.{hint} Pass only the sources "
                "that carry them."
            )
        for parameter in found:
            carriers[parameter].append(source)
    return carriers


def _check_constant(function: str, parameter: str, result: SelectionResult) -> None:
    """Raise for a line: a set holds constants only (decision 4)."""
    for row in result.rows:
        if row["vertical"] is not None:
            raise HangtuError(
                f"{function}: the selection of {parameter!r} in "
                f"{row['key'][GEOLOGY]!r} is a line with {row['vertical']} "
                "(trend:), and a model set holds constant values only. Select a "
                "constant for the set; select() still gives the line on its own."
            )


def unit_order(selections: Mapping[str, SelectionResult]) -> list[str]:
    """Return the set's units: the compared ones first, then value-only ones.

    The compared units come in the comparisons' order (so the geology map's);
    units only a ``value`` (or ``none``) entry names follow, in the order
    the selections list them.
    """
    compared: dict[str, None] = {}
    named: dict[str, None] = {}
    for result in selections.values():
        if result.comparison is not None:
            for row in result.comparison.rows:
                compared.setdefault(str(row["key"][GEOLOGY]), None)
        for row in result.rows:
            named.setdefault(str(row["key"][GEOLOGY]), None)
    return [*compared, *(name for name in named if name not in compared)]


def selected(
    selections: Mapping[str, SelectionResult], parameter: str, geology_unit: str
) -> bool:
    """Whether ``parameter``'s selection lists ``geology_unit``."""
    result = selections.get(parameter)
    return result is not None and any(
        row["key"][GEOLOGY] == geology_unit for row in result.rows
    )


def merged_judgments(selections: Mapping[str, SelectionResult]) -> dict[str, Any]:
    """Every selection's judgments, the ``selection`` record keyed by parameter."""
    merged: dict[str, Any] = {}
    chosen: dict[str, Any] = {}
    for parameter, result in selections.items():
        for name, record in result.judgments.items():
            if name == _judgments.SELECTION:
                chosen[parameter] = record
            else:
                merged[name] = record
    if chosen:
        merged[_judgments.SELECTION] = chosen
    return merged


# --- The result (decisions 5 and 7) --------------------------------------------------


def _symbol(parameter: str) -> str:
    """Return the label's symbol: ``"Effective cohesion, c′"`` -> ``"c′"``."""
    from hangtu import registry

    info = registry.column_info(parameter) or {}
    label = str(info.get("label", parameter))
    return label.rsplit(", ", 1)[-1] if ", " in label else parameter


def _inputs_text(rule: Mapping[str, Any]) -> str:
    """Return a rule's inputs in one line: ``φ′ 35.3 deg (selected), ...``."""
    parts = []
    for item in rule["inputs"]:
        given = item["value"]
        if item.get("text"):  # as the judgment wrote it, with its unit
            shown = str(item["text"])
        else:
            unit = f" {item['unit']}" if item.get("unit") else ""
            shown = (given if isinstance(given, str) else _cell(given)) + unit
        parts.append(f"{item['symbol']} {shown} ({item['origin']})")
    return ", ".join(parts)


def _joined(items: Sequence[str]) -> str:
    """Join names as prose: ``a``, ``a and b``, ``a, b and c``."""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"


@dataclass(frozen=True, repr=False)
class _ModelSet(_Result):
    """A model's parameter set: one value per geology unit and parameter.

    Use ``.to_frame()`` for the table a modeler is handed (one row per unit),
    ``.provenance()`` for where each value came from, and ``.selections``
    for the ``select()`` results behind it.
    """

    #: The model's name, e.g. ``"Mohr-Coulomb"``.
    model: str
    #: The model's published description, which the set follows.
    model_citation: str
    #: The model's parameters in order, by registry name.
    parameters: tuple[str, ...]
    #: The geology units in order.
    geology_units: tuple[str, ...]
    #: One record per unit and parameter (decision 5).
    records: tuple[dict[str, Any], ...]
    #: The system every source was converted to, or None.
    display_units: str | None
    #: The units a set fixes for its parameters whatever their values, such
    #: as degrees for an angle; the rest are their values' units.
    fixed_units: dict[str, str]
    #: ``select()``'s result for each parameter read by it.
    selections: dict[str, SelectionResult] = field(compare=False)

    @classmethod
    def create(
        cls,
        *,
        function: str,
        model: str,
        model_citation: str,
        parameters: Sequence[str],
        records: Sequence[dict[str, Any]],
        selections: Mapping[str, SelectionResult],
        geology_units: Sequence[str],
        judgments: Mapping[str, Any],
        display_units: str | None,
        notes: Sequence[str] = (),
        fixed_units: Mapping[str, str] | None = None,
        **fields: Any,
    ) -> Self:
        """Make a set: the base's fields, then a subclass's own ``fields``.

        The summary's notes are ``notes``, then each record's notes, named
        by its unit and parameter.
        """
        by_record = [
            f"{r['geology_unit']}, {_symbol(r['parameter'])}: {note}"
            for r in records
            for note in r["notes"]
        ]
        return cls(
            kind="parameter",
            function=function,
            value=None,
            unit=None,
            notes=(*notes, *by_record),
            judgments=dict(judgments),
            hangtu_version=version("hangtu"),
            model=model,
            model_citation=model_citation,
            parameters=tuple(parameters),
            geology_units=tuple(geology_units),
            records=tuple(records),
            display_units=display_units,
            fixed_units=dict(fixed_units or {}),
            selections=dict(selections),
            **fields,
        )

    def _units(self) -> dict[str, str]:
        units: dict[str, str] = {}
        for record in self.records:
            if record["unit"] and record["parameter"] not in units:
                units[record["parameter"]] = record["unit"]
        units |= self.fixed_units
        return {p: units[p] for p in self.parameters if p in units}

    def to_frame(self) -> pd.DataFrame:
        """Return one row per geology unit, one column per parameter: values only.

        ``attrs["units"]`` gives each parameter's unit. A blank is NaN;
        ``.provenance()`` says why.
        """
        values = {(r["geology_unit"], r["parameter"]): r["value"] for r in self.records}
        frame = pd.DataFrame(
            [
                {
                    GEOLOGY: unit,
                    **{p: values.get((unit, p), np.nan) for p in self.parameters},
                }
                for unit in self.geology_units
            ],
            columns=[GEOLOGY, *self.parameters],
        )
        frame[list(self.parameters)] = frame[list(self.parameters)].astype(float)
        frame.attrs["units"] = self._units()
        return frame

    def provenance(self) -> pd.DataFrame:
        """Return one row per unit and parameter: its value and where it came from.

        ``parameter_origin`` is ``selection``, ``rule``, ``judgment`` or
        ``blank``; ``reason`` is the selection's reason, or a rule's inputs
        in one line.
        """
        rows = []
        for record in self.records:
            chosen = record["selection"] or {}
            rule = record["rule"] or {}
            judgment = record["judgment"] or {}
            if chosen:
                reason = chosen["selection_reason"]
            elif rule:
                reason = _inputs_text(rule)
            elif judgment:
                reason = f"{judgment['name']} ({judgment['source']})"
            else:
                reason = None
            rows.append(
                {
                    GEOLOGY: record["geology_unit"],
                    "parameter": record["parameter"],
                    "value": record["value"],
                    "unit": record["unit"],
                    "parameter_origin": record["origin"],
                    "parameter_source": chosen.get("parameter_source"),
                    "selection_method": chosen.get("selection_method"),
                    "rule_name": rule.get("name"),
                    "rule_citation": rule.get("citation"),
                    "reason": reason,
                    "no_value_reason": record["no_value_reason"],
                }
            )
        columns = [
            GEOLOGY,
            "parameter",
            "value",
            "unit",
            "parameter_origin",
            "parameter_source",
            "selection_method",
            "rule_name",
            "rule_citation",
            "reason",
            "no_value_reason",
        ]
        frame = pd.DataFrame(rows, columns=columns)
        frame["value"] = frame["value"].astype(float)
        return frame

    def to_dict(self) -> dict[str, Any]:
        """Return every field, JSON-serializable (NaN as None).

        One record per unit and parameter, keyed by registry name, never a
        program's field name; each selection gives its own ``.to_dict()``.
        """
        return _plain(
            {
                "kind": self.kind,
                "function": self.function,
                "model": self.model,
                "model_citation": self.model_citation,
                "parameters": self.parameters,
                "geology_units": self.geology_units,
                "records": self.records,
                "selections": {
                    name: result.to_dict() for name, result in self.selections.items()
                },
                "notes": self.notes,
                "judgments": self.judgments,
                "display_units": self.display_units,
                "hangtu_version": self.hangtu_version,
            }
        )

    def _origin_line(self, record: Mapping[str, Any]) -> str | None:
        """Return what a record rests on, unless a plain selection with a value."""
        where = f"  {record['geology_unit']}, {_symbol(record['parameter'])}: "
        if record["origin"] == "selection":
            if record["no_value_reason"] is None:
                return None
            return f"{where}no value, {record['no_value_reason']}"
        if record["origin"] == "rule":
            rule = record["rule"]
            text = f"{where}{rule['name']} ({rule['citation']}): {_inputs_text(rule)}"
            if record["no_value_reason"] is not None:
                text += f"; no value, {record['no_value_reason']}"
            return text
        if record["origin"] == "judgment":
            judgment = record["judgment"]
            return (
                f"{where}judgment {judgment['name']}, {judgment['key']} "
                f"({judgment['source']})"
            )
        return f"{where}no value, {record['no_value_reason']}"

    def _blank_lines(self) -> list[str]:
        """One line per reason a parameter is blank, with the units it's blank in.

        Parameters blank for the same reason in the same units share a line.
        """
        units_of: dict[tuple[str, str], list[str]] = {}
        for record in self.records:
            if record["origin"] == "blank":
                key = (record["no_value_reason"], record["parameter"])
                units_of.setdefault(key, []).append(record["geology_unit"])
        grouped: dict[tuple[str, tuple[str, ...]], list[str]] = {}
        for (reason, parameter), units in units_of.items():
            grouped.setdefault((reason, tuple(units)), []).append(_symbol(parameter))
        lines = []
        for (reason, blank_in), symbols in grouped.items():
            where = (
                "Every unit"
                if len(blank_in) > 1 and len(blank_in) == len(self.geology_units)
                else _joined(blank_in)
            )
            lines.append(f"  {where}, {_joined(symbols)}: no value, {reason}")
        return lines

    def __str__(self) -> str:
        units = self._units()
        frame = self.to_frame()
        heading = [
            _symbol(p) + (f" ({units[p]})" if p in units else "")
            for p in self.parameters
        ]
        table = [["", *heading]]
        for _, row in frame.iterrows():
            table.append([str(row[GEOLOGY]), *(_cell(row[p]) for p in self.parameters)])
        lines = [f"{self.model} set ({self.model_citation}), by geology_unit"]
        lines += _table(table, indent="  ")
        origins = [
            line
            for r in self.records
            if r["origin"] != "blank" and (line := self._origin_line(r))
        ]
        origins += self._blank_lines()
        if origins:
            lines.append("Where the values come from")
            lines += origins
        return "\n".join([*lines, *self.notes])

    def __repr__(self) -> str:
        return str(self)

    def _repr_html_(self) -> str:
        return f"<pre>{html.escape(str(self))}</pre>"
