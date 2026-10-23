"""Vertical stress through each hole's log (docs/work/m13a-judgments.md, Decision 6).

Unit weights and water levels are judgments (SPEC §4): each comes from an
argument, else from a judgments file, else the call raises. Everything is
computed in m, kN/m³ and kPa and converted for display at the end.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from numbers import Real
from typing import Any

import numpy as np
import pandas as pd

from hangtu import _judgments
from hangtu import units as _units
from hangtu._data import numeric_column
from hangtu._settings import _display_units, settings
from hangtu.analysis._judgment_values import (
    ALL,
    Values,
    from_file,
    read_judgments,
    take,
    warn_unused,
)
from hangtu.errors import ColumnError, HangtuError, UnitsError, warn

#: Gaps and overlaps up to this are rounding (m), as QC G002/G003's default.
TOLERANCE = 0.01
STRESS_COLUMNS = (
    "total_vertical_stress",
    "pore_pressure",
    "effective_vertical_stress",
)
_METER = _units.ureg.meter
_UNIT_WEIGHT = _units.ureg.Unit("kilonewton / meter**3")
_UNIT_WEIGHT_FIELDS = ("bulk_unit_weight", "saturated_unit_weight")


@dataclass
class Log:
    """One hole's layers, checked and trimmed to its deepest test (m)."""

    tops: np.ndarray
    bases: np.ndarray
    keys: list[str | None]


def vertical_stress(
    df: pd.DataFrame,
    *,
    stratigraphy: pd.DataFrame,
    judgments: Any = None,
    unit_weight: str | Mapping[str, Any] | None = None,
    water_level: Any = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Add total, pore and effective vertical stress at each test's depth.

    The stress is integrated through each hole's log, from the ground surface
    down to the test:

    $$
    \sigma_{v0} = \sum_i \gamma_i \,\Delta z_i, \qquad
    u_0 = \gamma_w \max(0,\ z - z_w), \qquad
    \sigma'_{v0} = \sigma_{v0} - u_0
    $$

    where $\gamma_i$ is the unit weight of layer $i$ over its thickness
    $\Delta z_i$ above depth $z$ (the saturated unit weight below the water
    level, where one is given, else the bulk unit weight), $z_w$ the depth of
    the water level and $\gamma_w$ the unit weight of water,
    ``ht.settings.water_unit_weight`` (9.81 kN/m³ by default, converted as
    needed). Source: Loehr et al. (2016), FHWA NHI-16-072, eqs. 11.26 to 11.29.

    **Water above ground** ($z_w < 0$, a flooded load case): the water's
    weight $\gamma_w |z_w|$ is added to $\sigma_{v0}$, with a warning, so
    $\sigma'_{v0}$ is what it would be with the water at ground level.

    **Judgments taken** (SPEC §4); none has a default. Each resolves from its
    argument, else ``judgments=``, else the project's judgments file carried in
    ``df.attrs["judgments_file"]``, else an error naming it.

    - Unit weights, keyed by a stratigraphy column (``geology_unit`` for the
      argument; the file's ``by:``).
    - Water levels, keyed by hole (``loca_id``).

    **Assumptions:** level ground with laterally uniform layers within each
    hole; geostatic stress only (no surcharge, structures or arching);
    hydrostatic pore pressure from one water level per hole, so artesian or
    under-drained conditions need measured pore pressures instead. A
    $\sigma'_{v0}$ that is too high isn't conservative in a fixed direction:
    it lowers (N1)60, on the safe side for strength, and lowers OCR, on the
    unsafe side for settlement.

    **The log** must run from 0 down to each hole's deepest test with no gap
    or overlap (more than 0.01 m; QC G002, G003): otherwise the call raises,
    listing every hole and depth range. A test below the base of the log takes
    the last layer down to it, with a warning.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per test, with ``loca_id`` and ``depth`` (and ``ground_level``
        when a water level is given as an elevation), such as ``p.spt()``.
    stratigraphy : pandas.DataFrame
        Each hole's log, as ``ht.template("stratigraphy")`` or
        ``p.stratigraphy()``: ``loca_id``, ``depth_top``, ``depth_base`` and
        the column the unit weights are keyed by, with its own units declared.
        It is always passed explicitly: it's data you may have edited.
    judgments : Judgments or path, optional
        ``ht.judgments(path)``, ``p.judgments`` or a path to a judgments file.
        By default the project's, from ``df.attrs["judgments_file"]``.
    unit_weight : str or dict, optional
        Replaces the judgments file's unit weights. One unit weight for every
        layer (``"19 kN/m3"``), or a dict keyed by ``geology_unit``:
        ``{"Fill": "18 kN/m3", "Clay": {"bulk_unit_weight": "19 kN/m3",
        "saturated_unit_weight": "20 kN/m3"}}``.
    water_level : number, str, dict or pandas.DataFrame, optional
        Replaces the judgments file's water levels: a depth for every hole (a
        number in ``df``'s depth units, or ``"3 m"``); a dict
        ``{loca_id: depth}`` listing every hole; or a table of ``loca_id`` and
        ``depth`` or ``elevation``, with its own units (P01's format).
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.
    display_units : {"US", "SI"}, optional
        The units of the stresses; by default ``ht.settings.display_units``.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``total_vertical_stress``, ``pore_pressure``
        and ``effective_vertical_stress``. No row is dropped or reordered; a
        row with no ``depth`` or ``loca_id`` gets blank stresses, with a
        warning. ``df.attrs["judgments"]`` records each judgment's source (the
        argument, or the file's path and SHA-256) and the values used;
        ``df.attrs["vertical_stress"]`` records the pore pressure method and
        $\gamma_w$.

    Raises
    ------
    HangtuError
        For a missing judgment or a unit or hole without a value, a log that
        can't be integrated, or missing units.

    Examples
    --------
    >>> p.set_judgments("judgments.yaml")
    >>> spt = ht.analysis.vertical_stress(p.spt(), stratigraphy=p.stratigraphy())
    >>> spt[["loca_id", "depth", "effective_vertical_stress"]]

    With values given directly:

    >>> ht.analysis.vertical_stress(
    ...     spt, stratigraphy=log, unit_weight="19 kN/m3", water_level="3 m"
    ... )
    """
    _check_frame(df, "df", ["loca_id", "depth"])
    _check_frame(stratigraphy, "stratigraphy", ["loca_id", "depth_top", "depth_base"])
    system = _display_units(display_units or settings.display_units)
    depth_unit = _units.resolve_units(df, ["depth"], units, analysis=True)["depth"]
    depths = _to_meters(numeric_column(df, "depth"), depth_unit, "depth")
    holes = _hole_ids(df["loca_id"])
    valid = ~np.isnan(depths) & (holes != "")
    tested = list(dict.fromkeys(holes[valid]))
    deepest = {hole: float(depths[valid & (holes == hole)].max()) for hole in tested}

    read = read_judgments(judgments, df)
    weights = _resolve("unit_weight", unit_weight, read, df, depth_unit)
    levels = _resolve("water_level", water_level, read, df, depth_unit)
    log, log_unit = _read_log(stratigraphy, weights.by)
    logs, extended = _check_log(log, deepest, weights.by, log_unit)

    keys = [key for hole in tested for key in logs[hole].keys]
    noun = "geology unit" if weights.by in (None, "geology_unit") else weights.by
    gamma = take(weights, keys, noun)
    warn_unused(
        weights,
        log["key"] if weights.by else [],
        f"the stratigraphy's {weights.by}",
    )
    water = _water_depths(take(levels, tested, "hole"), df, units)
    warn_unused(levels, log["loca_id"], "the stratigraphy's loca_id")
    gamma_w = _water_unit_weight()

    total = np.full(len(df), np.nan)
    pore = np.full(len(df), np.nan)
    for hole in tested:
        rows = valid & (holes == hole)
        hole_log = logs[hole]
        bulk = np.array([gamma[key]["bulk_unit_weight"] for key in hole_log.keys])
        saturated = np.array(
            [gamma[key].get("saturated_unit_weight", np.nan) for key in hole_log.keys]
        )
        total[rows], pore[rows] = _integrate(
            hole_log.tops,
            hole_log.bases,
            bulk,
            saturated,
            water[hole],
            gamma_w,
            depths[rows],
        )

    _warn_extended(extended, log_unit)
    standing = {hole: -z for hole, z in water.items() if z < 0}
    _warn_standing(standing, depth_unit)
    blank = int((~valid).sum())
    if blank:
        warn(
            f"{blank} row{'s have' if blank != 1 else ' has'} no depth or loca_id, "
            "so the stresses there are blank."
        )
    replaced = [column for column in STRESS_COLUMNS if column in df.columns]
    if replaced:
        warn(f"Replaced the existing columns {', '.join(map(repr, replaced))}.")

    result = df.copy()
    stress_unit = None
    for column, values in zip(STRESS_COLUMNS, (total, pore, total - pore), strict=True):
        result[column], text = _units.to_display(values, "kPa", "stress", system)
        stress_unit = text
    result.attrs["units"] = {
        **_units.units_of(df),
        **(units or {}),
        **dict.fromkeys(STRESS_COLUMNS, stress_unit),
    }
    result.attrs["judgments"] = {
        **df.attrs.get("judgments", {}),
        weights.name: weights.record(),
        levels.name: levels.record(),
    }
    method: dict[str, Any] = {
        "pore_pressure": "hydrostatic",
        "water_unit_weight": settings.water_unit_weight,
    }
    if standing:
        method["water_above_ground"] = {
            hole: _length_text(height, depth_unit) for hole, height in standing.items()
        }
    result.attrs["vertical_stress"] = method
    return result


# --- The calculation ----------------------------------------------------------------


def _integrate(
    tops: np.ndarray,
    bases: np.ndarray,
    bulk: np.ndarray,
    saturated: np.ndarray,
    water_depth: float,
    water_unit_weight: float,
    depths: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return total stress and pore pressure (kPa) at ``depths`` (m).

    Layers are ``tops`` to ``bases`` (m) with unit weights in kN/m³; a NaN
    saturated unit weight takes the bulk one below the water level.
    """
    z = np.asarray(depths, dtype=float)[:, None]
    reached = np.minimum(bases[None, :], z)
    above = np.clip(np.minimum(reached, water_depth) - tops, 0, None)
    below = np.clip(reached - np.maximum(tops, water_depth), 0, None)
    wet = np.where(np.isnan(saturated), bulk, saturated)
    total = above @ bulk + below @ wet
    if water_depth < 0:
        total = total + water_unit_weight * -water_depth
    pore = water_unit_weight * np.clip(z[:, 0] - water_depth, 0, None)
    return total, pore


def _water_unit_weight() -> float:
    value, unit = _units.parse_quantity(settings.water_unit_weight, "unit_weight")
    return float(
        _units.convert([value], _units.parse_unit(unit), "unit_weight", _UNIT_WEIGHT)[0]
    )


# --- Inputs -------------------------------------------------------------------------


def _check_frame(frame: Any, name: str, columns: list[str]) -> None:
    if not isinstance(frame, pd.DataFrame):
        raise HangtuError(
            f"{name} must be a pandas DataFrame, not {type(frame).__name__}."
        )
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        start = ' Start from ht.template("stratigraphy").' if name != "df" else ""
        raise ColumnError(
            f"{name} has no column {', '.join(map(repr, missing))}. Available "
            f"columns: {', '.join(map(str, frame.columns)) or 'none'}.{start}"
        )


def _hole_ids(values: pd.Series) -> np.ndarray:
    """Hole IDs as text, ``""`` for blank."""
    return np.array(
        ["" if pd.isna(value) else str(value).strip() for value in values],
        dtype=object,
    )


def _to_meters(values: np.ndarray, unit: str, column: str) -> np.ndarray:
    return _units.convert(values, _units.parse_unit(unit, column), "length", _METER)


def _length_text(meters: float, unit: str) -> str:
    """Write a length in m in ``unit``: ``"1.2 m"``, ``"3.9 ft"``."""
    value = _units.convert([meters], _METER, "length", _units.parse_unit(unit))[0]
    return f"{round(float(value), 3):g} {unit}"


def _read_log(stratigraphy: pd.DataFrame, by: str | None) -> tuple[pd.DataFrame, str]:
    """Return the log in m, each layer's key as text, and its depth unit."""
    if by is not None and by not in stratigraphy.columns:
        raise ColumnError(
            f"The unit weights are keyed by {by!r}, and stratigraphy has no such "
            f"column. Columns: {', '.join(map(str, stratigraphy.columns))}."
        )
    try:
        found = _units.resolve_units(
            stratigraphy, ["depth_top", "depth_base"], analysis=True
        )
    except UnitsError as error:
        raise UnitsError(f"stratigraphy: {error}") from None
    if found["depth_top"] != found["depth_base"]:
        raise UnitsError(
            "stratigraphy: 'depth_top' and 'depth_base' have different units "
            f"({found['depth_top']}, {found['depth_base']}). Declare one unit for both."
        )
    unit = found["depth_top"]
    keys = (
        [None] * len(stratigraphy)
        if by is None
        else [None if pd.isna(key) else str(key) for key in stratigraphy[by]]
    )
    log = pd.DataFrame(
        {
            "loca_id": _hole_ids(stratigraphy["loca_id"]),
            "top": _to_meters(
                numeric_column(stratigraphy, "depth_top"), unit, "depth_top"
            ),
            "base": _to_meters(
                numeric_column(stratigraphy, "depth_base"), unit, "depth_base"
            ),
            "key": pd.Series(keys, dtype=object).to_numpy(),
        }
    )
    return log, unit


def _check_log(
    log: pd.DataFrame, deepest: Mapping[str, float], by: str | None, unit: str
) -> tuple[dict[str, Log], list[tuple[str, float, float]]]:
    """Check each tested hole's log down to its deepest test (Decision 7).

    Returns the layers per hole, trimmed to the deepest test, with the last one
    carried down to it where needed, and those holes as (hole, base, deepest).
    """
    logs: dict[str, Log] = {}
    extended = []
    problems: list[str] = []
    gaps = False

    def at(meters: float) -> str:
        return _length_text(meters, unit)

    for hole, bottom in deepest.items():
        rows = log[log["loca_id"] == hole]
        if rows.empty:
            problems.append(f"{hole}: no layers")
            continue
        if rows[["top", "base"]].isna().any().any():
            problems.append(f"{hole}: a layer with a blank depth_top or depth_base")
            continue
        rows = rows.sort_values("top", kind="stable")
        tops = rows["top"].to_numpy(dtype=float)
        bases = rows["base"].to_numpy(dtype=float)
        keys = list(rows["key"])
        before = len(problems)
        for top, base in zip(tops, bases, strict=True):
            if base < top:
                problems.append(
                    f"{hole}: a layer with its base ({at(base)}) above its top "
                    f"({at(top)})"
                )
        if len(problems) > before:
            continue
        if tops[0] > TOLERANCE:
            problems.append(f"{hole}: the log starts at {at(tops[0])}, not at 0")
        tops[0] = 0.0
        last = len(tops) - 1
        for i in range(1, len(tops)):
            if bases[i - 1] >= bottom:
                last = i - 1
                break
            step = tops[i] - bases[i - 1]
            if step > TOLERANCE:
                problems.append(
                    f"{hole}: a gap from {at(bases[i - 1])} to {at(tops[i])}"
                )
                gaps = True
            elif step < -TOLERANCE:
                problems.append(
                    f"{hole}: an overlap from {at(tops[i])} to {at(bases[i - 1])}"
                )
                gaps = True
            tops[i] = bases[i - 1]
        tops, bases, keys = tops[: last + 1], bases[: last + 1].copy(), keys[: last + 1]
        if by is not None:
            blank = [i for i, key in enumerate(keys) if key is None or key == ""]
            for i in blank:
                problems.append(
                    f"{hole}: the layer from {at(tops[i])} to {at(bases[i])} "
                    f"has no {by}"
                )
        if bases[-1] < bottom:
            extended.append((hole, float(bases[-1]), bottom))
            bases[-1] = bottom
        logs[hole] = Log(tops=tops, bases=bases, keys=[str(key) for key in keys])
    if problems:
        listed = "\n".join(f"  {problem}" for problem in problems)
        qc = (
            " p.qc() lists the gaps and overlaps in a project's file (G002, G003)."
            if gaps
            else ""
        )
        raise HangtuError(
            "The stratigraphy can't be integrated down to the deepest test in "
            f"{'this hole' if len(problems) == 1 else 'these holes'}:\n{listed}\n"
            "Each hole's log must run from 0 down to its deepest test, with no gap "
            f"or overlap of more than {at(TOLERANCE)}.{qc} Fix the layers in the "
            "stratigraphy table and call again."
        )
    return logs, extended


# --- Judgments ----------------------------------------------------------------------


def _resolve(
    name: str,
    argument: Any,
    read: "_judgments.Read | None",
    df: pd.DataFrame,
    depth_unit: str,
) -> Values:
    """One judgment: its argument, else the judgments file, else an error."""
    in_file = None if read is None else read.judgments.get(name)
    if argument is not None:
        if in_file is not None:
            warn(f"{name}= replaces the {name} in {read.path.name}.")
        if name == "unit_weight":
            return _unit_weight_argument(argument)
        return _water_level_argument(argument, depth_unit)
    if in_file is not None:
        return from_file(in_file, read)
    raise HangtuError(_missing(name, read, "judgments_file" in df.attrs))


def _missing(name: str, read: "_judgments.Read | None", attached: bool) -> str:
    if name == "unit_weight":
        what = "unit weights, keyed by geology unit"
        example = 'unit_weight={"Fill": "18 kN/m3", "Clay": "19 kN/m3"}'
    else:
        what = "water levels, keyed by hole"
        example = 'water_level={"BH1": "3 m", "BH2": "2.5 m"}'
    if read is not None:
        return (
            f"The judgments file {str(read.path)!r} has no {name}, and "
            f"vertical_stress() needs {what}, a judgment with no default (SPEC §4). "
            f"Add {name}: to the file, or give them in the call, {example}."
        )
    hint = (
        ""
        if attached
        else " If df came from a Project dataset, merge and concat drop df.attrs: "
        "pass judgments=p.judgments."
    )
    return (
        f"vertical_stress() needs {what}, a judgment with no default (SPEC §4). "
        f"Give them in the call, {example}, or in a judgments file under "
        f"{name}: and pass judgments=ht.judgments(path), or set it on the project "
        f"with p.set_judgments(path).{hint}"
    )


def _quantity(value: Any, quantity: str, where: str, example: str) -> tuple[float, str]:
    """Read a quantity string; a unit weight must be positive."""
    try:
        number, unit = _units.parse_quantity(value, quantity)
    except HangtuError as error:
        raise HangtuError(f"{where}: {error} Example: {example}") from None
    if quantity == "unit_weight" and number <= 0:
        raise HangtuError(f"{where} must be positive, not {value!r}.")
    return number, unit


def _unit_weight_argument(argument: Any) -> Values:
    example = 'unit_weight="19 kN/m3" or unit_weight={"Fill": "18 kN/m3"}'

    def entry(value: Any, where: str) -> tuple[dict[str, float], dict[str, str]]:
        given = value if isinstance(value, Mapping) else {"bulk_unit_weight": value}
        unknown = [name for name in given if name not in _UNIT_WEIGHT_FIELDS]
        if unknown or "bulk_unit_weight" not in given:
            raise HangtuError(
                f'{where} must be a unit weight such as "18 kN/m3", or a dict '
                f"with bulk_unit_weight and, optionally, saturated_unit_weight, "
                f"not {value!r}."
            )
        values, texts = {}, {}
        for name, text in given.items():
            number, unit = _quantity(text, "unit_weight", f"{where} {name}", example)
            values[name] = float(
                _units.convert(
                    [number], _units.parse_unit(unit), "unit_weight", _UNIT_WEIGHT
                )[0]
            )
            texts[name] = text.strip()
        return values, texts

    if isinstance(argument, str):
        values, texts = entry(argument, "unit_weight")
        return Values("unit_weight", "argument", None, {ALL: values}, {ALL: texts})
    if not isinstance(argument, Mapping):
        raise HangtuError(
            "unit_weight must be a unit weight with its unit or a dict keyed by "
            f"geology unit, not {argument!r}. Example: {example}"
        )
    entries, texts = {}, {}
    for key, value in argument.items():
        entries[str(key)], texts[str(key)] = entry(value, f"unit_weight[{key!r}]")
    return Values("unit_weight", "argument", "geology_unit", entries, texts)


def _water_level_argument(argument: Any, depth_unit: str) -> Values:
    example = 'water_level="3 m" or water_level={"BH1": "3 m", "BH2": 2.5}'

    def entry(value: Any, where: str) -> tuple[dict[str, float], dict[str, str]]:
        if isinstance(value, Real) and not isinstance(value, bool):
            number, unit, text = float(value), depth_unit, f"{value:g} {depth_unit}"
        elif isinstance(value, str):
            number, unit = _quantity(value, "length", where, example)
            text = value.strip()
        else:
            raise HangtuError(
                f"{where} must be a depth: a number in df's depth units or a "
                f'string such as "3 m", not {value!r}. Example: {example}'
            )
        meters = float(_to_meters(np.array([number]), unit, "water_level")[0])
        return {"depth": meters}, {"depth": text}

    if isinstance(argument, pd.DataFrame):
        return _water_level_table(argument, depth_unit)
    if isinstance(argument, Mapping):
        entries, texts = {}, {}
        for key, value in argument.items():
            entries[str(key)], texts[str(key)] = entry(value, f"water_level[{key!r}]")
        return Values("water_level", "argument", "loca_id", entries, texts)
    values, texts = entry(argument, "water_level")
    return Values("water_level", "argument", None, {ALL: values}, {ALL: texts})


def _water_level_table(table: pd.DataFrame, depth_unit: str) -> Values:
    """P01's per-hole table: ``loca_id`` and one of ``depth`` or ``elevation``."""
    if "loca_id" not in table.columns:
        raise ColumnError("The water_level table has no column 'loca_id'.")
    given = [vs for vs in ("depth", "elevation") if vs in table.columns]
    if len(given) != 1:
        problem = "both" if given else "neither"
        raise ColumnError(
            f"The water_level table has {problem} of 'depth' and 'elevation'. "
            "Give one column with each hole's water level."
        )
    vs = given[0]
    unit = _units.units_of(table).get(vs)
    if unit is None:
        unit = depth_unit
        warn(
            f"The water_level table's {vs!r} has no units, so it takes df's depth "
            f'units ({unit}). Declare them with ht.set_units(table, {{"{vs}": "ft"}}).'
        )
    values = _to_meters(numeric_column(table, vs), unit, vs)
    entries, texts = {}, {}
    for hole, value in zip(_hole_ids(table["loca_id"]), values, strict=True):
        if hole == "" or np.isnan(value):
            continue
        if hole in entries:
            raise HangtuError(
                f"The water_level table has more than one level for {hole}. Give one."
            )
        entries[hole] = {vs: float(value)}
        texts[hole] = {vs: _length_text(float(value), unit)}
    return Values("water_level", "argument", "loca_id", entries, texts)


def _water_depths(
    entries: Mapping[str, dict[str, float]],
    df: pd.DataFrame,
    units: Mapping[str, str] | None,
) -> dict[str, float]:
    """Each hole's water level as a depth (m), from ``ground_level`` if needed."""
    need = [hole for hole, entry in entries.items() if "elevation" in entry]
    ground: dict[str, float] = {}
    if need:
        if "ground_level" not in df.columns:
            raise ColumnError(
                f"The water levels for {', '.join(need)} are elevations, and df "
                "has no ground_level to turn them into depths. Add ground_level, "
                "or give the water levels as depths."
            )
        unit = _units.resolve_units(df, ["ground_level"], units, analysis=True)
        levels = _units.convert(
            numeric_column(df, "ground_level"),
            _units.parse_unit(unit["ground_level"], "ground_level"),
            "length",
            _METER,
        )
        holes = _hole_ids(df["loca_id"])
        bad = []
        for hole in need:
            found = pd.unique(levels[(holes == hole) & ~np.isnan(levels)])
            if len(found) != 1:
                bad.append(hole)
            else:
                ground[hole] = float(found[0])
        if bad:
            raise HangtuError(
                f"The water levels for {', '.join(bad)} are elevations, and df "
                "doesn't have exactly one ground_level for "
                f"{'that hole' if len(bad) == 1 else 'each of those holes'}. "
                "Fill in one ground level per hole, or give the water levels as depths."
            )
    return {
        hole: entry["depth"] if "depth" in entry else ground[hole] - entry["elevation"]
        for hole, entry in entries.items()
    }


# --- Warnings -----------------------------------------------------------------------


def _warn_extended(extended: list[tuple[str, float, float]], unit: str) -> None:
    if not extended:
        return
    listed = "; ".join(
        f"{hole} ({_length_text(base, unit)} to {_length_text(bottom, unit)})"
        for hole, base, bottom in extended
    )
    warn(f"Tests below the base of the log take its last layer down to them: {listed}.")


def _warn_standing(standing: Mapping[str, float], unit: str) -> None:
    if not standing:
        return
    listed = "; ".join(
        f"{hole}: water level {_length_text(height, unit)} above ground"
        for hole, height in standing.items()
    )
    warn(f"{listed}. The water's weight is added to the total vertical stress.")
