"""Convert a shear box φ′ to a triaxial one (docs/work/m18d-sources-compared.md).

Kulhawy & Mayne (1990), Eq. 4-10 with the ratios of Tables 4-2 and 4-5, and
the critical state friction angle as a judgment (decisions 1-7).
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd

from hangtu import _judgments
from hangtu.analysis._derived import _DerivedResult
from hangtu.analysis._fit_groups import _label
from hangtu.analysis._judgment_values import from_file, read_judgments_file
from hangtu.analysis._shear_box_fit import ShearBoxFit
from hangtu.errors import HangtuError, warn

_FUNCTION = "friction_angle_from_shear_box()"
_JUDGMENT = "critical_state_friction_angle"
_KEY = "geology_unit"
#: The name a converted value carries, as a correlation's estimate carries its
#: correlation_name (decision 7).
CONVERSION_NAME = "friction_angle_from_shear_box_kulhawy_mayne_1990"
#: soil= -> (φ′psc / φ′tc, where Kulhawy & Mayne 1990 give it) (decision 1).
_SOILS = {
    "cohesionless": (1.12, "Table 4-2, p. 4-14"),
    "normally_consolidated_cohesive": (1.10, "Table 4-5, p. 4-25"),
}
_SOIL_TEXT = {
    "cohesionless": "cohesionless",
    "normally_consolidated_cohesive": "normally consolidated cohesive",
}
_HOW_TO_SET = (
    f"Pass {_JUDGMENT}= in degrees (a number for a fit with one group, else "
    f"{{'Terrace': 32, ...}} by {_KEY}), or add it to the judgments file: "
    f"{_JUDGMENT}: {{by: {_KEY}, units: {{{_JUDGMENT}: deg}}, values: {{Terrace: "
    f'{{{_JUDGMENT}: 32, reason: "ring shear, BH02"}}}}}}, and pass judgments= or '
    "set it on the project with p.set_judgments()."
)
_ASSUMED = (
    "Converting treats the shear box stresses as effective and the test as drained "
    "(ASTM D3080); shear_box_fit() assumes neither. Check that the tests were "
    "drained before using effective_friction_angle."
)
_SPECULATIVE = (
    "normally_consolidated_cohesive: Kulhawy & Mayne (1990), Table 4-5, footnote 2 "
    'on the direct shear row: "Speculative, based on results from sand".'
)
_RESIDUAL = (
    "Residual angles aren't converted: φr is independent of test type (Kulhawy & "
    "Mayne 1990, p. 4-10). residual_friction_angle is kept as fitted."
)
_COHESION = (
    "peak_cohesion is kept as fitted, not converted: Kulhawy & Mayne (1990) give no "
    "conversion for the intercept."
)


def friction_angle_from_shear_box(
    fit: ShearBoxFit,
    *,
    soil: str | Mapping[str, str] | None = None,
    critical_state_friction_angle: float | Mapping[str, float] | None = None,
    judgments: Any = None,
) -> "ShearBoxConversion":
    r"""Convert a shear box peak φ′ to a triaxial compression φ′ (Kulhawy & Mayne 1990).

    A direct shear test shears the soil in plane strain on a plane it doesn't
    choose, so its peak angle $\phi'_{ds}$ isn't a triaxial compression angle
    $\phi'_{tc}$ (SPEC §5 keeps them apart by name). Kulhawy & Mayne (1990,
    Eq. 4-10, p. 4-12) relate direct shear to plane strain compression:

    $$
    \tan\phi'_{ds} = \tan\phi'_{psc}\,\cos\phi'_{cv}
    \quad\Rightarrow\quad
    \phi'_{psc} = \tan^{-1}\!\left(\frac{\tan\phi'_{ds}}{\cos\phi'_{cv}}\right)
    $$

    and plane strain to triaxial compression by a ratio for the soil type:

    $$
    \phi'_{tc} = \phi'_{psc} / r
    $$

    with $r = 1.12$ for cohesionless soils (Table 4-2, p. 4-14) and
    $r = 1.10$ for normally consolidated cohesive soils (Table 4-5, p. 4-25,
    where TC means CIUC, CK0UC or CAUC). $\phi'_{cv}$ is the critical state
    (constant volume) friction angle, which is unique and independent of test
    type (p. 4-10). For typical $\phi'_{cv}$, the source says, $\phi'_{psc}$
    is "some 2 to 7 degrees higher than the direct shear values" (p. 4-12).

    **What is converted:** the peak friction angle of both lines,
    ``"free"`` and ``"through_origin"``, main line first, as the fit ordered
    them. The converted value is ``effective_friction_angle``, with
    ``conversion_name`` saying it was converted, so a frame with triaxial and
    converted rows keeps them apart as two sources (SPEC §5).
    ``plane_strain_friction_angle`` is the step between. **Not converted:**
    residual angles, because $\phi_r$ is independent of test type (p. 4-10),
    and ``peak_cohesion``, for which the source gives no conversion; both are
    kept as fitted in ``.groups``.

    **Valid for:** the soils of Tables 4-2 and 4-5 only (``soil=``).
    Overconsolidated cohesive soils, rock and rock joints aren't covered: compare
    their ``peak_friction_angle`` unconverted. **Out of range:** a fitted
    $\phi'_{ds} < \tan^{-1}(\sin\phi'_{cv})$ gives $\phi'_{psc} < \phi'_{cv}$,
    a peak below critical state, which Eq. 4-10 doesn't describe; it is still
    converted, flagged in ``below_critical_state`` and warned about. A line
    the fit couldn't fit, or one with $\phi'_{ds} \le 0$, gets no value and a
    ``no_conversion_reason``. **Scatter:** the source states none.

    **Assumptions:** the shear box stresses are effective and the test was
    drained (ASTM D3080), which ``shear_box_fit()`` doesn't assume; the
    result says so in its notes. For normally consolidated cohesive soils,
    the source marks the direct shear relation "Speculative, based on results
    from sand" (Table 4-5, footnote 2), and the notes quote it.

    **Judgments taken:** ``critical_state_friction_angle``, $\phi'_{cv}$ in
    degrees, keyed by ``geology_unit`` with no project-wide value, because
    mineralogy and grading set it. It resolves from the argument, then
    ``judgments=``, then the Project's judgments file that the fit's input
    carried (``fit.judgments_file``), else an error naming it (SPEC §4). The
    soil type is an argument too, never inferred from a soil class or a USCS
    symbol.

    Parameters
    ----------
    fit : ShearBoxFit
        From ``ht.analysis.shear_box_fit()``. A mapping of ``soil`` or
        $\phi'_{cv}$ needs it grouped by ``geology_unit``.
    soil : {"cohesionless", "normally_consolidated_cohesive"} or dict
        The soil type, which picks the ratio $r$; or ``{geology_unit: soil}``.
        Required.
    critical_state_friction_angle : float or dict, optional
        $\phi'_{cv}$ in degrees, strictly between 0 and 90: one number for a
        fit with one group, else ``{geology_unit: degrees}``. It replaces the
        judgments file's, with a warning.
    judgments : str, path or Judgments, optional
        The judgments file; by default the Project's, from the fit.

    Returns
    -------
    ShearBoxConversion
        ``.to_frame()`` has one row per group and line kind; ``.groups``
        keeps the fit's peak points with their depths, the residual angle and
        the peak cohesion; ``.judgments`` records the $\phi'_{cv}$ used.

    Raises
    ------
    HangtuError
        For a ``fit`` that isn't a ``ShearBoxFit``, ``soil`` missing or not
        one of the two, a mapping without a group's ``geology_unit`` or on a
        fit not grouped by it, $\phi'_{cv}$ missing for a group, one number
        for a fit with several groups, or a value outside 0-90°.

    Examples
    --------
    >>> df = pd.DataFrame({
    ...     "geology_unit": "Terrace",
    ...     "applied_normal_stress": [50.0, 100.0, 200.0],
    ...     "peak_shear_stress": [34.0, 61.0, 120.0],
    ... })
    >>> df.attrs["units"] = {"applied_normal_stress": "kPa", "peak_shear_stress": "kPa"}
    >>> fit = ht.analysis.shear_box_fit(df, group_by="geology_unit")
    >>> converted = ht.analysis.friction_angle_from_shear_box(
    ...     fit, soil="cohesionless", critical_state_friction_angle={"Terrace": 32}
    ... )
    >>> converted.to_frame()[["line_kind", "effective_friction_angle"]]

    References
    ----------
    Kulhawy, F.H. & Mayne, P.W. (1990). *Manual on Estimating Soil Properties
    for Foundation Design*. EPRI EL-6800, Electric Power Research Institute,
    Palo Alto. Eq. 4-10 (p. 4-12), Table 4-2 (p. 4-14), Table 4-5 (p. 4-25),
    p. 4-10.
    """
    if not isinstance(fit, ShearBoxFit):
        raise HangtuError(
            f"{_FUNCTION} takes the ShearBoxFit that ht.analysis.shear_box_fit() "
            f"returns, not {type(fit).__name__}."
        )
    convertible = [_convertible(group) for group in fit.groups]
    soils = _soils(soil, fit, convertible)
    angles, record = _critical_state(
        critical_state_friction_angle, judgments, fit, convertible
    )
    groups = []
    below = []
    for group, soil_name, angle in zip(fit.groups, soils, angles, strict=True):
        peak = group["strengths"]["peak"]
        residual = group["strengths"]["residual"]
        lines = [
            _convert(line, residual_line, soil_name, angle)
            for line, residual_line in zip(
                peak["lines"], residual["lines"], strict=True
            )
        ]
        below += [
            f"{_label(group['key'])} ({_kind_text(line['line_kind'])})"
            for line in lines
            if line["below_critical_state"]
        ]
        groups.append(
            {
                "key": group["key"],
                "count_rows": group["count_rows"],
                "conversion_soil": soil_name,
                "critical_state_friction_angle": (
                    angle["value"] if angle is not None else np.nan
                ),
                "critical_state_friction_angle_source": (
                    angle["source_text"] if angle is not None else None
                ),
                "critical_state_friction_angle_reason": (
                    angle["reason"] if angle is not None else None
                ),
                "lines": lines,
                "points": peak["points"],
            }
        )
    if below:
        warn(
            f"{_FUNCTION}: φ′ds < tan⁻¹(sin φ′cv) in {', '.join(below)}, so φ′psc < "
            "φ′cv: a peak below critical state, which Kulhawy & Mayne (1990) Eq. "
            "4-10 doesn't describe. It is converted and flagged "
            "(below_critical_state); check φ′cv and the tests."
        )
    assert soil is not None  # _soils() raised for None
    notes = [_ASSUMED, _RESIDUAL, _COHESION]
    if "normally_consolidated_cohesive" in soils:
        notes.append(_SPECULATIVE)
    if below:
        notes.append(
            f"Below critical state (below_critical_state): {', '.join(below)}."
        )
    return ShearBoxConversion(
        function="friction_angle_from_shear_box",
        unit=fit.unit,
        notes=tuple(notes),
        judgments={**fit.judgments, **({_JUDGMENT: record} if record else {})},
        hangtu_version=version("hangtu"),
        judgments_file=fit.judgments_file,
        by=fit.by,
        soil=soil if isinstance(soil, str) else dict(soil),
        depth_units=dict(fit.depth_units),
        groups=tuple(groups),
    )


def _convertible(group: dict[str, Any]) -> bool:
    """Whether a group has a peak line with a friction angle to convert."""
    return any(
        line["no_fit_reason"] is None and line["friction_angle"] > 0
        for line in group["strengths"]["peak"]["lines"]
    )


def _unit_of(key: dict[str, Any]) -> str | None:
    value = key.get(_KEY)
    return None if value is None or pd.isna(value) else str(value)


def _check_soil(value: Any, where: str) -> str:
    if isinstance(value, str) and value in _SOILS:
        return value
    raise HangtuError(
        f"{_FUNCTION} {where} must be "
        f'"cohesionless" (Kulhawy & Mayne 1990, Table 4-2) or '
        f'"normally_consolidated_cohesive" (Table 4-5), not {value!r}. Those tables '
        "give the ratio of plane strain to triaxial φ′ for those two soils only; "
        "overconsolidated cohesive soils, rock and rock joints aren't covered. To "
        "compare such a φ′, compare peak_friction_angle unconverted."
    )


def _soils(soil: Any, fit: ShearBoxFit, convertible: list[bool]) -> list[str | None]:
    """Each group's soil type, from one value or a mapping by geology unit."""
    if soil is None:
        raise HangtuError(
            f'{_FUNCTION} needs soil=: "cohesionless" (Kulhawy & Mayne 1990, Table '
            '4-2, φ′psc = 1.12 φ′tc) or "normally_consolidated_cohesive" (Table '
            "4-5, φ′psc = 1.10 φ′tc), or a mapping {geology_unit: soil}. It is "
            "never inferred from a soil class (SPEC §4)."
        )
    if not isinstance(soil, Mapping):
        one = _check_soil(soil, "soil=")
        return [one] * len(fit.groups)
    given = {
        key: _check_soil(value, f"soil={{{key!r}: ...}}") for key, value in soil.items()
    }
    _keyed_by_unit(fit, "soil=")
    soils: list[str | None] = []
    missing = []
    for group, needed in zip(fit.groups, convertible, strict=True):
        unit = _unit_of(group["key"])
        if unit in given:
            soils.append(given[unit])
            continue
        soils.append(None)
        if needed:
            missing.append(unit)
    if missing:
        raise HangtuError(
            f"{_FUNCTION} soil= has no soil type for the geology_unit "
            f"{', '.join(_unit_text(unit) for unit in missing)}. Add "
            f"{'it' if len(missing) == 1 else 'them'} to the mapping."
        )
    return soils


def _unit_text(unit: str | None) -> str:
    return "(blank)" if unit is None else repr(unit)


def _keyed_by_unit(fit: ShearBoxFit, what: str) -> None:
    if _KEY not in fit.by:
        grouped = f"group_by={list(fit.by)!r}" if fit.by else "no group_by"
        raise HangtuError(
            f"{_FUNCTION} {what} is keyed by {_KEY}, but the fit has {grouped}. Fit "
            f"again with group_by={_KEY!r}."
        )


def _angle(value: Any, where: str) -> float:
    """Check one φ′cv given as an argument, in degrees."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise HangtuError(
            f"{_FUNCTION} {where} takes φ′cv in degrees as a number, e.g. 32, not "
            f"{value!r}."
        )
    if not 0 < value < 90:
        raise HangtuError(
            f"{_FUNCTION} {where} must be between 0° and 90°, not {value!r}: φ′cv is "
            "a friction angle in degrees."
        )
    return float(value)


def _critical_state(
    argument: Any, judgments: Any, fit: ShearBoxFit, needed: list[bool]
) -> tuple[list[dict[str, Any] | None], dict[str, Any] | None]:
    """Each group's φ′cv in degrees, with its source, and the record (decision 5)."""
    read = read_judgments_file(judgments, fit.judgments_file, "the fit")
    in_file = read is not None and _JUDGMENT in read.judgments
    if argument is not None:
        if in_file:
            assert read is not None  # in_file
            warn(f"{_JUDGMENT}= replaces the {_JUDGMENT} in {read.path.name}.")
        return _from_argument(argument, fit, needed)
    if not in_file:
        if not any(needed):
            return [None] * len(fit.groups), None
        where = (
            f"the judgments file {read.path.name} has no {_JUDGMENT}"
            if read is not None
            else "no judgments file was given, and the fit's input carried none"
        )
        raise HangtuError(
            f"{_FUNCTION} needs {_JUDGMENT}, φ′cv, keyed by {_KEY}: {where}. "
            + _HOW_TO_SET
        )
    assert read is not None  # in_file
    return _from_file(read.judgments[_JUDGMENT], read, fit, needed)


def _from_argument(
    argument: Any, fit: ShearBoxFit, needed: list[bool]
) -> tuple[list[dict[str, Any] | None], dict[str, Any]]:
    def entry(value: float) -> dict[str, Any]:
        return {
            "value": value,
            "text": f"{value:g} deg",
            "reason": None,
            "source": "argument",
            "source_text": "argument",
        }

    if not isinstance(argument, Mapping):
        value = _angle(argument, f"{_JUDGMENT}=")
        if len(fit.groups) != 1:
            groups = "; ".join(_label(group["key"]) for group in fit.groups)
            raise HangtuError(
                f"{_FUNCTION} {_JUDGMENT}= is one number, but the fit has "
                f"{len(fit.groups)} groups ({groups}). Give a mapping by {_KEY}, "
                f"e.g. {{'Terrace': 32}}: one φ′cv for every unit would be coarser "
                "than the judgment allows (SPEC §4)."
            )
        one = entry(value)
        return [one], {"source": "argument", "by": None, "values": {"all": one["text"]}}
    given = {
        str(key): entry(_angle(value, f"{_JUDGMENT}={{{key!r}: ...}}"))
        for key, value in argument.items()
    }
    _keyed_by_unit(fit, f"{_JUDGMENT}=")
    angles, used = _match(given, fit, needed, f"{_JUDGMENT}=")
    unmatched = [key for key in given if key not in used]
    if unmatched:
        warn(
            f"{_FUNCTION} {_JUDGMENT}= has values for "
            f"{', '.join(map(repr, unmatched))}, which match no group's {_KEY}. Check "
            "the spelling: keys match exactly, by case too."
        )
    return angles, {"source": "argument", "by": _KEY, "values": used}


def _from_file(
    judgment: "_judgments.Judgment",
    read: "_judgments.Read",
    fit: ShearBoxFit,
    needed: list[bool],
) -> tuple[list[dict[str, Any] | None], dict[str, Any]]:
    values = from_file(judgment, read)
    given = {
        key: {
            "value": values.entries[key][_JUDGMENT],
            "text": values.texts[key][_JUDGMENT],
            "reason": values.texts[key].get("reason"),
            "source": "judgments file",
            "source_text": read.path.name,
        }
        for key in values.entries
    }
    if any(needed):
        _keyed_by_unit(fit, f"the judgments file's {_JUDGMENT}")
    angles, used = _match(given, fit, needed, f"The judgments file's {_JUDGMENT}")
    record = {
        "source": str(read.path),
        "sha256": read.sha256,
        "by": _KEY,
        "values": {key: dict(values.texts[key]) for key in used},
    }
    return angles, record


def _match(
    given: dict[str, dict[str, Any]], fit: ShearBoxFit, needed: list[bool], where: str
) -> tuple[list[dict[str, Any] | None], dict[str, Any]]:
    """Each group's φ′cv by its geology unit; an error for a needed one missing."""
    angles: list[dict[str, Any] | None] = []
    used: dict[str, Any] = {}
    missing = []
    for group, need in zip(fit.groups, needed, strict=True):
        unit = _unit_of(group["key"]) if _KEY in fit.by else None
        if unit is not None and unit in given:
            angles.append(given[unit])
            used[unit] = given[unit]["text"]
            continue
        angles.append(None)
        if need:
            missing.append(unit)
    if missing:
        listed = ", ".join(_unit_text(unit) for unit in dict.fromkeys(missing))
        raise HangtuError(
            f"{_FUNCTION}: {where} has no {_JUDGMENT}, φ′cv, for the {_KEY} {listed}. "
            + _HOW_TO_SET
        )
    return angles, used


def _convert(
    line: dict[str, Any],
    residual: dict[str, Any],
    soil: str | None,
    angle: dict[str, Any] | None,
) -> dict[str, Any]:
    """Convert one peak line's φ′ds: Eq. 4-10, then the soil's ratio (decision 1)."""
    friction = line["friction_angle"]
    record: dict[str, Any] = {
        "line_kind": line["line_kind"],
        "peak_friction_angle": friction,
        "peak_cohesion": line["cohesion"],
        "residual_friction_angle": residual["friction_angle"],
        "count": line["count"],
        "lowest_normal_stress": line["lowest_normal_stress"],
        "highest_normal_stress": line["highest_normal_stress"],
        "plane_strain_friction_angle": np.nan,
        "effective_friction_angle": np.nan,
        "below_critical_state": None,
        "no_conversion_reason": None,
    }
    if line["no_fit_reason"] is not None:
        record["no_conversion_reason"] = line["no_fit_reason"]
        return record
    if not friction > 0:
        record["no_conversion_reason"] = (
            f"φ′ds is {friction:g}°: Eq. 4-10 converts a friction angle above 0°"
        )
        return record
    assert angle is not None and soil is not None  # needed, so resolved or raised
    critical = math.radians(angle["value"])
    plane_strain = math.degrees(
        math.atan(math.tan(math.radians(friction)) / math.cos(critical))
    )
    ratio, _ = _SOILS[soil]
    record["plane_strain_friction_angle"] = plane_strain
    record["effective_friction_angle"] = plane_strain / ratio
    record["below_critical_state"] = bool(
        friction < math.degrees(math.atan(math.sin(critical)))
    )
    return record


def _kind_text(kind: str) -> str:
    return "free" if kind == "free" else "through the origin"


@dataclass(frozen=True, repr=False)
class ShearBoxConversion(_DerivedResult):
    """The conversion ``ht.analysis.friction_angle_from_shear_box()`` returns.

    Use ``.to_frame()`` for a table with one row per group and line kind,
    ``.to_dict()`` for a report, or ``print(conversion)`` to read it.
    ``.groups`` holds each group's soil type, φ′cv and converted lines, with
    the fit's peak points and their depths. Pass it to
    ``ht.stats.compare_sources()`` to compare the converted φ′ with other
    sources.
    """

    #: The columns the fit grouped by, in order.
    by: tuple[str, ...]
    #: ``soil=`` as given: one soil type, or ``{geology_unit: soil}``.
    soil: str | dict[str, str]
    #: ``{column: unit}`` of the points' depths, from the fit.
    depth_units: dict[str, str]
    #: One record per group: its key, ``count_rows``, ``conversion_soil``,
    #: ``critical_state_friction_angle`` (degrees) with its source and reason,
    #: ``lines`` (the main one first; each with the values of ``.to_frame()``,
    #: ``peak_cohesion`` and ``residual_friction_angle`` kept as fitted) and the
    #: fit's peak ``points``.
    groups: tuple[dict[str, Any], ...]

    def _columns(self) -> list[str]:
        return [
            *self.by,
            "line_kind",
            "peak_friction_angle",
            "critical_state_friction_angle",
            "conversion_soil",
            "plane_strain_friction_angle",
            "effective_friction_angle",
            "conversion_name",
            "below_critical_state",
            "count",
            "lowest_normal_stress",
            "highest_normal_stress",
            "no_conversion_reason",
        ]

    def to_frame(self) -> pd.DataFrame:
        """Return one row per group and line kind, the main line of each group first.

        ``effective_friction_angle`` is the converted φ′tc and
        ``conversion_name`` says how it was converted; ``count`` and the normal
        stress range are the fitted line's. ``attrs["units"]`` gives the unit
        of each column that has one; angles are in degrees.
        """
        rows = []
        for group in self.groups:
            for line in group["lines"]:
                rows.append(
                    {
                        **group["key"],
                        "line_kind": line["line_kind"],
                        "peak_friction_angle": line["peak_friction_angle"],
                        "critical_state_friction_angle": group[
                            "critical_state_friction_angle"
                        ],
                        "conversion_soil": group["conversion_soil"],
                        "plane_strain_friction_angle": line[
                            "plane_strain_friction_angle"
                        ],
                        "effective_friction_angle": line["effective_friction_angle"],
                        "conversion_name": CONVERSION_NAME,
                        "below_critical_state": line["below_critical_state"],
                        "count": line["count"],
                        "lowest_normal_stress": line["lowest_normal_stress"],
                        "highest_normal_stress": line["highest_normal_stress"],
                        "no_conversion_reason": line["no_conversion_reason"],
                    }
                )
        frame = pd.DataFrame(rows, columns=self._columns())
        angles = [
            "peak_friction_angle",
            "critical_state_friction_angle",
            "plane_strain_friction_angle",
            "effective_friction_angle",
        ]
        stresses = ["lowest_normal_stress", "highest_normal_stress"]
        frame.attrs["units"] = {
            **dict.fromkeys(angles, "deg"),
            **(dict.fromkeys(stresses, self.unit) if self.unit else {}),
        }
        return frame

    def __str__(self) -> str:
        from hangtu.plot._overlays import format_number  # plot imports analysis

        unit = f" {self.unit}" if self.unit else ""
        lines = [
            "Shear box φ′ converted to triaxial compression (Kulhawy & Mayne 1990, "
            "Eq. 4-10)"
        ]
        for group in self.groups:
            head = f"{_label(group['key'])}: " if self.by else ""
            soil = group["conversion_soil"]
            if soil is None:
                lines.append(f"{head}not converted")
            else:
                ratio, table = _SOILS[soil]
                source = group["critical_state_friction_angle_source"]
                reason = group["critical_state_friction_angle_reason"]
                cv = (
                    f"φ′cv = {format_number(group['critical_state_friction_angle'])}° "
                    f"({source}{': ' + reason if reason else ''})"
                    if source is not None
                    else "no φ′cv"
                )
                lines.append(
                    f"{head}{_SOIL_TEXT[soil]}, φ′psc = {ratio:g} φ′tc ({table}), {cv}"
                )
            for line in group["lines"]:
                kind = f"  {_kind_text(line['line_kind'])}: "
                if line["no_conversion_reason"]:
                    lines.append(f"{kind}not converted: {line['no_conversion_reason']}")
                    continue
                flag = ", below critical state" if line["below_critical_state"] else ""
                lines.append(
                    f"{kind}φ′ds {format_number(line['peak_friction_angle'])}° → "
                    f"φ′psc {format_number(line['plane_strain_friction_angle'])}° → "
                    f"φ′tc {format_number(line['effective_friction_angle'])}°, "
                    f"{line['count']} point{'s' if line['count'] != 1 else ''}, σn "
                    f"{format_number(line['lowest_normal_stress'])} to "
                    f"{format_number(line['highest_normal_stress'])}{unit}{flag}"
                )
        return "\n".join([*lines, *self.notes])
