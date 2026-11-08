"""``mohr_coulomb_set()``: each geology unit's Mohr-Coulomb parameters (SPEC §5).

Spec: docs/analysis/statistics.md §7. c′ and φ′ come
from ``select()``; ψ from a selection, else by rule from the unit's
``soil_class``; E′ and ν′ from a selection, else blank until wave 5 (M23).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from hangtu import _judgments
from hangtu.errors import HangtuError, warn
from hangtu.stats import _model_set
from hangtu.stats._model_set import _ModelSet
from hangtu.stats._select import SelectionResult

FUNCTION = "mohr_coulomb_set()"
COHESION = "effective_cohesion"
FRICTION = "effective_friction_angle"
DILATANCY = "dilatancy_angle"
MODULUS = "drained_youngs_modulus"
POISSON = "drained_poissons_ratio"
#: The model's parameters, in order, and whether select() must give each.
PARAMETERS = {
    COHESION: True,
    FRICTION: True,
    DILATANCY: False,
    MODULUS: False,
    POISSON: False,
}
MODEL = "Mohr-Coulomb"
#: The model's published description, which names exactly these five.
MODEL_CITATION = "Vermeer & de Borst (1984), Heron 29(3), p. 3"
#: φ′ and ψ are in degrees whatever their values (decision 15).
FIXED_UNITS = {FRICTION: "deg", DILATANCY: "deg"}
#: Why E′ and ν′ are blank without a selection (decision 14).
NO_STIFFNESS = "no selection; derived values aren't built yet"
#: The judgment record of the classes the set read (decision 16).
SOIL_CLASS = "soil_class"
#: φ′cv, the judgment Bolton's relation reads (M18 d).
CRITICAL = "critical_state_friction_angle"
#: Bolton's relation as Kulhawy & Mayne (1990) give it: φ′tc = φ′cv + 0.8 ψ.
BOLTON = "Bolton's relation, ψ = (φ′ - φ′cv) / 0.8"
BOLTON_CITATION = "Kulhawy & Mayne (1990), Eq. 4-16, p. 4-20, after Bolton (1986)"
BOLTON_FACTOR = 0.8
#: φ′ - φ′cv = 3 I_R (triaxial), I_R limited to 4: the relation's range, deg.
LIMIT = 12.0
LIMIT_CITATION = "Kulhawy & Mayne 1990, p. 4-10"
FINE = "ψ = 0 for a fine-grained unit"
FINE_CITATION = "Vermeer & de Borst (1984), p. 13"
FINE_NOTE = (
    "ψ is 0, as for a normally consolidated clay; an overconsolidated clay may "
    "dilate (Obrzud & Truty 2018, p. 107), and ψ is then given as a selection."
)
#: The classes a rule reads (decision 18); others are named, read by nothing.
NAMED_CLASSES = ("fill", "rock", "organic")


def mohr_coulomb_set(
    *sources: Any,
    selection: Mapping[str, Any] | None = None,
    critical_state_friction_angle: Any = None,
    geology_map: Any = None,
    include_assumed: bool = False,
    judgments: Any = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> "MohrCoulombSet":
    r"""Give each geology unit's Mohr-Coulomb parameters, each with its origin.

    The Mohr-Coulomb model (Vermeer & de Borst 1984, p. 3) is perfectly
    plastic with non-associated flow, and has five parameters: the
    effective cohesion c′, the effective friction angle φ′, the dilatancy
    angle ψ, the drained Young's modulus E′ and the drained Poisson's ratio
    ν′. The set gives one constant of each per geology unit and records
    where each came from. Engineers choose, hangtu reports: the set stops
    there, with no partial factors, design values or program input files.

    **c′ and φ′** are :func:`select`'s, one call each, from the sources that
    carry them, with the judgments file's (or ``selection=``'s) selection.
    Both are required for every unit in the set. When a unit's c′ and φ′
    aren't both ``fitted`` from the same source, they aren't one envelope's
    pair, so the set warns and notes it.

    **ψ**, in this order:

    1. a selection of ``dilatancy_angle`` that lists the unit (``value`` or
       ``none``), for a unit the rule doesn't fit;
    2. blank, when the unit has no φ′ value;
    3. by the unit's ``soil_class``, from the geology map (never USCS or the
       data):

       - ``coarse``: Bolton's relation, as Kulhawy & Mayne (1990, Eq. 4-16,
         p. 4-20) give it for triaxial compression,
         $\phi'_{tc} = \phi'_{cv} + 0.8\,\psi$, so

         $$\psi = \frac{\phi' - \phi'_{cv}}{0.8}$$

         with $\phi'$ the set's selected φ′ and $\phi'_{cv}$ the
         ``critical_state_friction_angle`` judgment. The relation is for a
         peak φ′: with a cautious selected φ′ it gives a smaller ψ, and the
         record shows the φ′ it used. A φ′ below φ′cv gives ψ = 0, with a
         note. Above φ′ - φ′cv = 12° (3 I_R with I_R limited to 4, Kulhawy &
         Mayne 1990, Eq. 4-6 and p. 4-10) the relation is beyond its data,
         so ψ is blank with the reason and a warning, never clipped; at
         exactly 12° it gives 15°;
       - ``fine``: 0, as for a normally consolidated clay (Vermeer & de
         Borst 1984, p. 13); an overconsolidated clay may dilate (Obrzud &
         Truty 2018, p. 107), and ψ is then given as a selection;
       - ``fill``, ``rock``, ``organic``, blank or any other class: an
         error, saying to give ψ as a ``value`` selection. Rock belongs in
         the generalized Hoek-Brown set, planned but not built yet.

    **E′ and ν′** are a selection's when it lists the unit, else blank:
    derived values aren't built yet.

    **A set holds constants**: a selection that gives a line with depth
    (``trend:``) is an error; :func:`select` gives the line on its own.

    Parameters
    ----------
    *sources : pandas.DataFrame, MohrCoulombFit or ShearBoxConversion
        As for :func:`select`. Each parameter's ``select()`` gets only the
        sources that carry it; a source that carries none of the five is an
        error.
    selection : dict, optional
        ``{parameter: {geology_unit: entry}}``, as for :func:`select`'s
        ``selection=``, replacing the file's selection of each parameter it
        names.
    critical_state_friction_angle : float or dict, optional
        φ′cv in degrees for Bolton's relation: a number when one unit needs
        it, else ``{geology_unit: number}``. It replaces the judgments
        file's, with a warning. By default the file's.
    geology_map : path or pandas.DataFrame, optional
        The geology map (a CSV path, or ``p.geology_map``), for each unit's
        ``soil_class``. By default the classes the sources carry from the
        Project's map.
    include_assumed : bool
        Include assumed values, as for :func:`select`.
    judgments : Judgments or path, optional
        The judgments file. By default the Project's.
    units : dict, optional
        ``{column: unit}``, applied to every DataFrame.
    display_units : {"US", "SI"}, optional
        Convert every source to this system's unit.

    Returns
    -------
    MohrCoulombSet
        ``.to_frame()`` has one row per geology unit and one column per
        parameter; ``.provenance()`` says where each value came from.

    Raises
    ------
    HangtuError
        For a unit with c′ selected and not φ′ (or the reverse); a selection
        with a line; a source that carries none of the parameters; sources
        that carry different soil classes for a unit; a unit ψ's rule needs
        a class for with none, or a class the rule can't read; a coarse
        unit without φ′cv; and the errors of :func:`select`.

    Examples
    --------
    >>> mc = ht.stats.mohr_coulomb_set(correlations, triaxial, converted)
    >>> mc.to_frame()
    """
    selections, read = _model_set.read_selections(
        FUNCTION,
        sources,
        PARAMETERS,
        selection=selection,
        include_assumed=include_assumed,
        judgments=judgments,
        units=units,
        display_units=display_units,
    )
    geology_units = _model_set.unit_order(selections)
    _check_pairs(selections, geology_units)
    classes, class_source = _soil_classes(geology_map, sources)
    ruled = [u for u in geology_units if _by_rule(selections, u)]
    _check_classes(ruled, classes, class_source)
    coarse = [u for u in ruled if classes[u] == "coarse"]
    critical, critical_record = _critical_state(
        critical_state_friction_angle, read, coarse
    )
    records: list[dict[str, Any]] = []
    for unit in geology_units:
        records += [
            _model_set.from_selection(selections[COHESION], unit, COHESION),
            _model_set.from_selection(selections[FRICTION], unit, FRICTION),
            _dilatancy(selections, unit, classes.get(unit), critical.get(unit)),
            _optional(selections, unit, MODULUS),
            _optional(selections, unit, POISSON),
        ]
    _warn_beyond_limit(records)
    recorded = _model_set.merged_judgments(selections)
    if critical_record is not None:
        recorded[CRITICAL] = critical_record
    in_set = {u: classes[u] for u in geology_units if u in classes}
    if in_set:
        recorded[SOIL_CLASS] = {"source": class_source, "values": in_set}
    return MohrCoulombSet.create(
        function="mohr_coulomb_set",
        model=MODEL,
        model_citation=MODEL_CITATION,
        parameters=list(PARAMETERS),
        records=records,
        selections=selections,
        geology_units=geology_units,
        judgments=recorded,
        display_units=display_units,
        notes=_pair_notes(selections, geology_units),
        fixed_units=FIXED_UNITS,
        soil_classes=in_set,
    )


# --- c′ and φ′ (decisions 11 and 12) --------------------------------------------------


def _check_pairs(
    selections: Mapping[str, SelectionResult], geology_units: Sequence[str]
) -> None:
    """Raise for a unit with one of c′ and φ′ selected and not the other."""
    for unit in geology_units:
        missing = [
            p
            for p in (COHESION, FRICTION)
            if not _model_set.selected(selections, p, unit)
        ]
        if not missing:
            continue
        listed = [p for p in (COHESION, FRICTION) if p not in missing]
        has = (
            f"has a selection of {listed[0]!r} and not of {missing[0]!r}"
            if listed
            else f"has neither {COHESION!r} nor {FRICTION!r} selected"
        )
        raise HangtuError(
            f"{FUNCTION}: {unit!r} {has}, and a Mohr-Coulomb set needs both. Add "
            f"an entry for {' and '.join(map(repr, missing))} in {unit!r}: a value "
            "with its reason (value: 0 with a reason for a c′ of zero), or method: "
            "none with a reason."
        )


def _pair(
    selections: Mapping[str, SelectionResult], unit: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = []
    for parameter in (COHESION, FRICTION):
        result = selections[parameter]
        rows.append(next(r for r in result.rows if r["key"]["geology_unit"] == unit))
    return rows[0], rows[1]


def _unpaired(selections: Mapping[str, SelectionResult], unit: str) -> bool:
    """Whether c′ and φ′ aren't one fit's pair; two ``none`` are no pair at all."""
    cohesion, friction = _pair(selections, unit)
    methods = {cohesion["selection_method"], friction["selection_method"]}
    if methods == {"none"}:
        return False
    return not (
        methods == {"fitted"}
        and cohesion["parameter_source"] == friction["parameter_source"]
    )


def _how(row: Mapping[str, Any]) -> str:
    return ", ".join(p for p in (row["parameter_source"], row["selection_method"]) if p)


def _pair_notes(
    selections: Mapping[str, SelectionResult], geology_units: Sequence[str]
) -> list[str]:
    """Warn once, and note per unit, where c′ and φ′ aren't one fit's pair."""
    units = [u for u in geology_units if _unpaired(selections, u)]
    if units:
        warn(
            f"{FUNCTION}: c′ and φ′ of {', '.join(map(repr, units))} don't both come "
            "fitted from the same source, so they aren't one envelope's pair (c′ and "
            "φ′ selected apart aren't a joint fractile). Select both as fitted from "
            "one MohrCoulombFit to keep them on one line, or keep them with the note."
        )
    notes = []
    for unit in units:
        cohesion, friction = _pair(selections, unit)
        notes.append(
            f"{unit}: c′ ({_how(cohesion)}) and φ′ ({_how(friction)}) don't come "
            "from one fit, so they aren't one envelope's pair."
        )
    return notes


# --- ψ (decision 13), E′ and ν′ (decision 14) -----------------------------------------


def _phi_row(selections: Mapping[str, SelectionResult], unit: str) -> dict[str, Any]:
    result = selections[FRICTION]
    return next(r for r in result.rows if r["key"]["geology_unit"] == unit)


def _by_rule(selections: Mapping[str, SelectionResult], unit: str) -> bool:
    """Whether ψ comes by rule: no ψ selection lists the unit, and it has a φ′."""
    if _model_set.selected(selections, DILATANCY, unit):
        return False
    return bool(np.isfinite(_phi_row(selections, unit)["value"]))


def _dilatancy(
    selections: Mapping[str, SelectionResult],
    unit: str,
    soil_class: str | None,
    critical: dict[str, Any] | None,
) -> dict[str, Any]:
    """ψ in decision 13's order: a selection, blank with no φ′, else by class."""
    if _model_set.selected(selections, DILATANCY, unit):
        return _model_set.from_selection(selections[DILATANCY], unit, DILATANCY)
    row = _phi_row(selections, unit)
    if not np.isfinite(row["value"]):
        return _model_set.blank(unit, DILATANCY, "no φ′ selected")
    if soil_class == "fine":
        return _model_set.from_rule(
            unit,
            DILATANCY,
            0.0,
            "deg",
            name=FINE,
            citation=FINE_CITATION,
            inputs=[_class_input("fine")],
            notes=[FINE_NOTE],
        )
    assert soil_class == "coarse" and critical is not None  # checked
    return _bolton(unit, row, critical)


def _class_input(soil_class: str) -> dict[str, Any]:
    return {
        "name": SOIL_CLASS,
        "symbol": "soil_class",
        "value": soil_class,
        "unit": None,
        "origin": "geology map",
    }


def _bolton(
    unit: str, row: Mapping[str, Any], critical: Mapping[str, Any]
) -> dict[str, Any]:
    """ψ = (φ′ - φ′cv) / 0.8, floored at 0 and blank beyond its range."""
    phi, phi_cv = float(row["value"]), float(critical["value"])
    inputs = [
        {
            "name": FRICTION,
            "symbol": "φ′",
            "value": phi,
            "unit": "deg",
            "origin": "selected",
            "parameter_source": row["parameter_source"],
            "selection_method": row["selection_method"],
        },
        {
            "name": CRITICAL,
            "symbol": "φ′cv",
            "value": phi_cv,
            "unit": "deg",
            "origin": "judgment",
            "source": critical["source_text"],
            "text": critical["text"][CRITICAL],
        },
    ]
    rule: dict[str, Any] = {
        "name": BOLTON,
        "citation": BOLTON_CITATION,
        "inputs": inputs,
    }
    difference = phi - phi_cv
    if difference > LIMIT:
        return _model_set.from_rule(
            unit,
            DILATANCY,
            np.nan,
            "deg",
            **rule,
            no_value_reason=(
                f"φ′ - φ′cv = {difference:.1f} deg, above the {LIMIT:g} deg of "
                f"I_R = 4 ({LIMIT_CITATION}); give ψ as a value selection"
            ),
        )
    psi = difference / BOLTON_FACTOR
    if psi >= 0:
        return _model_set.from_rule(unit, DILATANCY, psi, "deg", **rule)
    return _model_set.from_rule(
        unit,
        DILATANCY,
        0.0,
        "deg",
        **rule,
        notes=[
            f"φ′ {phi:.1f} deg is below φ′cv {phi_cv:.1f} deg, so ψ is 0 (the "
            f"relation gives {psi:.1f} deg)."
        ],
    )


def _warn_beyond_limit(records: Sequence[Mapping[str, Any]]) -> None:
    beyond = [
        r["geology_unit"]
        for r in records
        if r["parameter"] == DILATANCY
        and r["origin"] == "rule"
        and r["no_value_reason"] is not None
    ]
    if beyond:
        warn(
            f"{FUNCTION}: φ′ - φ′cv is above {LIMIT:g} deg in "
            f"{', '.join(map(repr, beyond))}, beyond the data Bolton's relation was "
            f"drawn from (I_R = 4, {LIMIT_CITATION}), so ψ is blank there, not "
            "clipped. Give ψ as a value selection with its reason."
        )


def _check_classes(
    ruled: Sequence[str], classes: Mapping[str, str], source: str | None
) -> None:
    """Raise for a unit ψ's rule needs a class for and can't read (decision 13)."""
    for unit in ruled:
        soil_class = classes.get(unit)
        if soil_class in ("coarse", "fine"):
            continue
        fix = (
            f"give ψ as a selection: dilatancy_angle: {{values: {{{unit}: {{method: "
            'value, value: "0 deg", reason: "..."}}}}}} in the judgments file\'s '
            "selection, or selection="
        )
        if soil_class is None:
            where = (
                "no geology map was given and the sources carry none"
                if source is None
                else f"{source} give none for it"
                if source == "the sources"
                else "geology_map= gives none for it"
            )
            raise HangtuError(
                f"{FUNCTION}: ψ's rule reads {unit!r}'s soil_class, coarse or fine, "
                f"and {where}. Pass geology_map= (the map's soil_class column), or "
                f"{fix}."
            )
        rock = (
            " Rock belongs in the generalized Hoek-Brown set (planned, not built yet), "
            "not Mohr-Coulomb."
            if soil_class == "rock"
            else ""
        )
        known = "" if soil_class in NAMED_CLASSES else ", a class hangtu doesn't know"
        raise HangtuError(
            f"{FUNCTION}: {unit!r} has soil_class {soil_class!r}{known}, and ψ's "
            "rule reads only coarse (Bolton's relation) or fine (0). Guessing would "
            f"put a rule where only the engineer can judge: {fix}.{rock}"
        )


# --- φ′cv (decision 13) ---------------------------------------------------------------


def _angle(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise HangtuError(
            f"{FUNCTION} {where} takes φ′cv in degrees as a number, e.g. 32, not "
            f"{value!r}."
        )
    if not 0 < value < 90:
        raise HangtuError(
            f"{FUNCTION} {where} must be between 0° and 90°, not {value!r}: φ′cv is "
            "a friction angle in degrees."
        )
    return float(value)


def _how_to_set(units: Sequence[str]) -> str:
    unit = units[0] if units else "Terrace"
    return (
        f"Pass {CRITICAL}= in degrees ({{{unit!r}: 32}}), or add it to the "
        f"judgments file: {CRITICAL}: {{by: geology_unit, units: {{{CRITICAL}: deg}}, "
        f'values: {{{unit}: {{{CRITICAL}: 32, reason: "ring shear, BH02"}}}}}}. Or '
        "give ψ as a value selection."
    )


def _critical_state(
    argument: Any, read: "_judgments.Read | None", needed: Sequence[str]
) -> tuple[dict[str, dict[str, Any]], dict[str, Any] | None]:
    """φ′cv of each coarse unit Bolton's relation reads, and the record.

    Argument, then the judgments file, then an error naming the units.
    """
    from hangtu.analysis._judgment_values import from_file  # analysis imports stats

    in_file = read is not None and CRITICAL in read.judgments
    if not needed:
        return {}, None
    if argument is not None:
        if in_file:
            assert read is not None  # in_file
            warn(f"{FUNCTION} {CRITICAL}= replaces the {CRITICAL} in {read.path.name}.")
        return _from_argument(argument, needed)
    if not in_file:
        where = (
            f"the judgments file {read.path.name} has no {CRITICAL}"
            if read is not None
            else "no judgments file was given, and the sources carry none"
        )
        raise HangtuError(
            f"{FUNCTION}: Bolton's relation needs {CRITICAL}, φ′cv, for "
            f"{', '.join(map(repr, needed))}: {where}. " + _how_to_set(needed)
        )
    assert read is not None  # in_file
    values = from_file(read.judgments[CRITICAL], read)
    found: dict[str, dict[str, Any]] = {}
    for unit in needed:
        if unit in values.entries:
            value, text = values.entries[unit], values.texts[unit]
        elif values.project is not None and values.project_text is not None:
            value, text = values.project, values.project_text
        else:
            continue
        found[unit] = {
            "value": value[CRITICAL],
            "source_text": read.path.name,
            "text": dict(text),
        }
    missing = [u for u in needed if u not in found]
    if missing:
        raise HangtuError(
            f"{FUNCTION}: the judgments file {read.path.name} has no {CRITICAL}, "
            f"φ′cv, for {', '.join(map(repr, missing))}, which Bolton's relation "
            "needs. " + _how_to_set(missing)
        )
    record = {
        "source": str(read.path),
        "sha256": read.sha256,
        "by": "geology_unit",
        "values": {unit: found[unit]["text"] for unit in needed},
    }
    return found, record


def _from_argument(
    argument: Any, needed: Sequence[str]
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if not isinstance(argument, Mapping):
        value = _angle(argument, f"{CRITICAL}=")
        if len(needed) != 1:
            raise HangtuError(
                f"{FUNCTION} {CRITICAL}= is one number, but Bolton's relation needs "
                f"φ′cv for {len(needed)} units ({', '.join(map(repr, needed))}). "
                "Give a mapping by geology_unit, e.g. {'Terrace': 32}: one φ′cv for "
                "every unit would be coarser than the judgment allows."
            )
        given = {needed[0]: value}
    else:
        given = {
            str(k): _angle(v, f"{CRITICAL}={{{k!r}: ...}}") for k, v in argument.items()
        }
    missing = [u for u in needed if u not in given]
    if missing:
        raise HangtuError(
            f"{FUNCTION} {CRITICAL}= has no φ′cv for {', '.join(map(repr, missing))}, "
            "which Bolton's relation needs. " + _how_to_set(missing)
        )
    found = {
        unit: {
            "value": given[unit],
            "source_text": "argument",
            "text": {CRITICAL: _judgments.quantity_text(given[unit], "deg")},
        }
        for unit in needed
    }
    record = {
        "source": "argument",
        "by": "geology_unit",
        "values": {unit: found[unit]["text"] for unit in needed},
    }
    return found, record


def _optional(
    selections: Mapping[str, SelectionResult], unit: str, parameter: str
) -> dict[str, Any]:
    if _model_set.selected(selections, parameter, unit):
        return _model_set.from_selection(selections[parameter], unit, parameter)
    return _model_set.blank(unit, parameter, NO_STIFFNESS)


# --- soil_class (decision 19) ---------------------------------------------------------


def _carried(source: Any) -> Mapping[str, str]:
    if isinstance(source, pd.DataFrame):
        return dict(source.attrs.get("soil_classes", {}))
    return dict(getattr(source, "soil_classes", {}) or {})


def _soil_classes(
    geology_map: Any, sources: Sequence[Any]
) -> tuple[dict[str, str], str | None]:
    """Each unit's class: ``geology_map=``, else what the sources carry.

    The rows' own ``soil_class`` column isn't read: a fit has no rows, and a
    CSV's column is the user's text (SPEC §8.3).
    """
    from hangtu.datasets import _geology_map  # datasets imports stats

    carried: dict[str, tuple[str, int]] = {}
    for position, source in enumerate(sources, start=1):
        for unit, soil_class in _carried(source).items():
            unit, soil_class = str(unit), str(soil_class)
            if unit in carried and carried[unit][0] != soil_class:
                first, at = carried[unit]
                raise HangtuError(
                    f"{FUNCTION}: source {at} carries {unit!r} as {first!r} and "
                    f"source {position} as {soil_class!r}, from different geology "
                    "maps. Make the sources from one Project, or pass the map with "
                    "geology_map=."
                )
            carried.setdefault(unit, (soil_class, position))
    if geology_map is None:
        if not carried:
            return {}, None
        return {u: c for u, (c, _) in carried.items()}, "the sources"
    table = _geology_map.read(geology_map)
    given = {
        str(u): str(c) for u, c in _geology_map.unit_values(table, "soil_class").items()
    }
    differs = [u for u, c in given.items() if u in carried and carried[u][0] != c]
    if differs:
        listed = ", ".join(f"{u} ({given[u]}, not {carried[u][0]})" for u in differs)
        warn(
            f"{FUNCTION}: geology_map= gives soil classes that differ from the ones "
            f"the sources carry from the Project's map: {listed}. geology_map= is "
            "used."
        )
    return given, "geology_map="


@dataclass(frozen=True, repr=False)
class MohrCoulombSet(_ModelSet):
    """The set ``ht.stats.mohr_coulomb_set()`` returns: c′, φ′, ψ, E′, ν′.

    Use ``.to_frame()`` for the table a modeler is handed (one row per
    geology unit, one column per parameter, by registry name),
    ``.provenance()`` for where each value came from, ``.selections`` for
    the ``select()`` result behind each selected parameter, and
    ``.to_dict()`` for a report.
    """

    #: Each unit's ``soil_class`` as the set read it.
    soil_classes: dict[str, str]
