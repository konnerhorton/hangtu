"""``mohr_coulomb_set()``: each geology unit's Mohr-Coulomb parameters (SPEC §5).

Spec: docs/work/m18f-mohr-coulomb-set.md, decisions 9-19. c′ and φ′ come
from ``select()``; ψ from a selection, else by rule from the unit's
``soil_class``; E′ and ν′ from a selection, else blank until wave 5 (M23).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import pandas as pd

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
NO_STIFFNESS = "no selection; derived values come with wave 5 (M23)"
#: The judgment record of the classes the set read (decision 16).
SOIL_CLASS = "soil_class"


def mohr_coulomb_set(
    *sources: Any,
    selection: Mapping[str, Any] | None = None,
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

    **E′ and ν′** are a selection's when it lists the unit, else blank:
    derived values come with wave 5 (M23).

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
        that carry different soil classes for a unit; and the errors of
        :func:`select`.

    Examples
    --------
    >>> mc = ht.stats.mohr_coulomb_set(correlations, triaxial, converted)
    >>> mc.to_frame()
    """
    selections, _ = _model_set.read_selections(
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
    records: list[dict[str, Any]] = []
    for unit in geology_units:
        records += [
            _model_set.from_selection(selections[COHESION], unit, COHESION),
            _model_set.from_selection(selections[FRICTION], unit, FRICTION),
            _dilatancy(selections, unit),
            _optional(selections, unit, MODULUS),
            _optional(selections, unit, POISSON),
        ]
    recorded = _model_set.merged_judgments(selections)
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


def _dilatancy(selections: Mapping[str, SelectionResult], unit: str) -> dict[str, Any]:
    """ψ: a selection when it lists the unit; the rule comes in the next step."""
    if _model_set.selected(selections, DILATANCY, unit):
        return _model_set.from_selection(selections[DILATANCY], unit, DILATANCY)
    return _model_set.blank(unit, DILATANCY, "no rule for ψ yet")


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
