"""Phase relations of one specimen (docs/work/m14b-phase-relations.md, Decisions 1-6).

Void ratio, porosity and degree of saturation from a specimen's bulk unit
weight, water content and specific gravity. Gs comes from the row's particle
density where it has one, else from the ``specific_gravity`` judgment (SPEC §4).
Everything is computed in kN/m³ and Mg/m³ and converted for display at the end.
"""

import math
from collections.abc import Mapping
from numbers import Real
from typing import Any

import numpy as np
import pandas as pd

from hangtu import _config
from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu._settings import _display_units, settings
from hangtu.analysis._judgment_values import (
    ALL,
    Values,
    from_file,
    read_judgments,
    take,
    warn_unused,
)
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.units import STANDARD_GRAVITY as G

OUTPUT_COLUMNS = (
    "specific_gravity",
    "specific_gravity_source",
    "void_ratio",
    "porosity",
    "degree_of_saturation",
    "saturated_unit_weight",
    "oversaturated",
)
_UNIT_WEIGHT = _units.ureg.Unit("kilonewton / meter**3")
_DENSITY = _units.ureg.Unit("megagram / meter**3")
#: Rounding slack on the dry unit weight check (kN/m³), as QC's SLACK.
_SLACK = 1e-9


def phase_relations(
    df: pd.DataFrame,
    *,
    specific_gravity: float | Mapping[str, float] | None = None,
    judgments: Any = None,
    saturation_tolerance: float = 5,
    units: dict[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Add void ratio, porosity and degree of saturation from γ, w and Gs.

    Each row is one specimen, with its own bulk unit weight $\gamma$ and water
    content $w$ (as ``p.density()`` gives them). With $w$ as a decimal:

    $$
    e = \frac{G_s\,\gamma_w\,(1 + w)}{\gamma} - 1, \qquad
    n = \frac{e}{1 + e}, \qquad
    S = \frac{w\,G_s}{e},
    $$
    $$
    \gamma_{sat} = \gamma_w\,\frac{G_s + e}{1 + e}, \qquad
    \gamma_d = \frac{\gamma}{1 + w}
    $$

    where $e$ is the void ratio, $n$ the porosity, $S$ the degree of
    saturation, $\gamma_{sat}$ the unit weight at the same void ratio fully
    saturated, $\gamma_d$ the dry unit weight and $\gamma_w$ the unit weight
    of water, ``ht.settings.water_unit_weight`` (9.81 kN/m³ by default).
    These are identities from the definitions of the phases, valid for any
    soil. Sources: Loehr et al. (2016), Geotechnical Site Characterization,
    FHWA NHI-16-072, §4.7, eqs. 4.9-4.10, p. 4-8; Kulhawy & Mayne (1990),
    EPRI EL-6800, eq. 2-9, p. 2-17.

    **Specific gravity.** Gs = $\rho_s / \rho_w$, with the particle density
    $\rho_s$ of the row and $\rho_w = \gamma_w / g$ ($g$ = 9.80665 m/s²). The
    same water is used in Gs and in $e$, so for a row with a particle density
    $e = \rho_s (1 + w) / \rho - 1$ exactly, whatever $\gamma_w$ is set to.
    ``specific_gravity_source`` says where each row's Gs came from:

    1. ``measured``: the row's particle density;
    2. ``assumed``: the row's particle density, marked as assumed in the file
       (``#``), with a warning counting the rows. It is the value the lab
       used, and a judgment never replaces it;
    3. ``judgment``: the ``specific_gravity`` judgment, for rows with no
       particle density.

    **Judgment taken** (SPEC §4); it has no default. Gs for rows with no
    particle density, keyed by geology unit (the file's ``by:``): from
    ``specific_gravity=``, else ``judgments=``, else the project's judgments
    file carried in ``df.attrs["judgments_file"]``, else an error naming it.
    It is read only when a row needs it. A row whose key is blank gets a blank
    Gs, counted. To inform it, summarize the measured particle densities by
    unit, leaving out the assumed ones, which are never pooled with measured
    values::

        pd_rows = p.particle_density()
        measured = pd_rows[~pd_rows["particle_density_assumed"]]
        ht.analysis.summary_by(measured, "particle_density")

    **Checks**, which flag and never correct:

    - ``oversaturated`` is True where $S$ is above 100 % by more than
      ``saturation_tolerance`` percentage points, with a warning naming the
      rows. $S$ over 100 % is impossible above or below the water table: a
      wrong Gs, an under-measured $\gamma$ or a $w$ from another specimen is
      likely. $S$ well under 100 % isn't flagged: above the water table, or
      with gas or swelling, it is real.
    - A ``dry_unit_weight`` on the row that differs from $\gamma / (1 + w)$ by
      more than QC B001's ``dry_density_tolerance`` (0.03 Mg/m³, so
      0.294 kN/m³) warns, naming the rows. It is kept, and not used.

    **Assumptions:** $\gamma$, $w$ and $\rho_s$ belong to one specimen, or for
    $\rho_s$ to its sample (``p.density()`` pairs them so); mixing one unit's
    mean $\gamma$ with another sample's $w$ adds scatter. A recompacted
    specimen's $e$ is the specimen's, not the ground's (``sample_condition``
    says which). A pycnometer Gs is for the fraction finer than 4.75 mm; a
    coarser fraction needs its own Gs and a weighted mean, which isn't
    computed here.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per specimen, as ``p.density()`` or ``ht.template("density")``:
        ``bulk_unit_weight`` and ``water_content`` (%), and optionally
        ``particle_density`` with ``particle_density_assumed``, and
        ``dry_unit_weight``. Rows that take the judgment need its key column,
        usually ``geology_unit``.
    specific_gravity : float or dict, optional
        Gs for the rows with no particle density, replacing the judgments
        file's: one number for every such row, or ``{geology_unit: number}``.
    judgments : Judgments or path, optional
        ``ht.judgments(path)``, ``p.judgments`` or a path to a judgments file.
        By default the project's, from ``df.attrs["judgments_file"]``.
    saturation_tolerance : float, default 5
        Percentage points above 100 % before a row is flagged
        ``oversaturated``. A reporting threshold, not a design input.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.
    display_units : {"US", "SI"}, optional
        The units of the unit weights; by default ``ht.settings.display_units``.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``specific_gravity``, ``specific_gravity_source``,
        ``void_ratio``, ``porosity`` (%), ``degree_of_saturation`` (%),
        ``saturated_unit_weight`` and ``oversaturated``, and
        ``dry_unit_weight`` filled where it was blank. No row is dropped or
        reordered; a row without $\gamma$, $w$ or Gs gets blanks, counted by
        reason. ``df.attrs["phase_relations"]`` records $\gamma_w$, $g$ and the
        tolerance; ``df.attrs["judgments"]`` the judgment's source and the
        values used, when a row took it.

    Raises
    ------
    HangtuError
        For a missing column, a ``particle_density`` without
        ``particle_density_assumed``, missing units, or a missing judgment or
        a geology unit without a value.

    Examples
    --------
    >>> rows = ht.analysis.phase_relations(p.density())
    >>> rows[["loca_id", "depth", "void_ratio", "degree_of_saturation"]]

    With Gs given for the rows that have no particle density:

    >>> ht.analysis.phase_relations(p.density(), specific_gravity={"Fill": 2.68})
    """
    _check_columns(df)
    system = _display_units(display_units or settings.display_units)
    gamma = _unit_weight(df, "bulk_unit_weight", units)
    water = numeric_column(df, "water_content") / 100
    gamma_w = _water_unit_weight()
    rho_w = gamma_w / G

    gravity, source = _gravity_from_particle_density(df, units, rho_w)
    judged = _judged(df, np.isnan(gravity), specific_gravity, judgments)
    if judged is not None:
        values, gravity_judged, no_key = judged
        taken = ~np.isnan(gravity_judged)
        gravity[taken] = gravity_judged[taken]
        source[taken] = "judgment"
    _warn_assumed(source)

    reasons = {
        "no bulk unit weight": np.isnan(gamma),
        "a bulk unit weight of 0 or less": gamma <= 0,
        "no water content": np.isnan(water),
        "a negative water content": water < 0,
        "no specific gravity": np.isnan(gravity) & ~no_key
        if judged is not None
        else np.isnan(gravity),
    }
    if judged is not None and no_key.any():
        reasons[f"a blank {values.by} to key the specific gravity by"] = no_key
    blank = np.zeros(len(df), bool)
    for mask in reasons.values():
        blank |= mask
    _warn_blank(reasons)

    with np.errstate(divide="ignore", invalid="ignore"):
        void_ratio = np.where(
            blank, np.nan, gravity * gamma_w * (1 + water) / gamma - 1
        )
        porosity = 100 * void_ratio / (1 + void_ratio)
        saturation = 100 * water * gravity / void_ratio
        saturated = gamma_w * (gravity + void_ratio) / (1 + void_ratio)
        dry_expected = np.where(gamma > 0, gamma / (1 + water), np.nan)

    dry = (
        _unit_weight(df, "dry_unit_weight", units)
        if "dry_unit_weight" in df.columns
        else np.full(len(df), np.nan)
    )
    _check_dry(df, dry, dry_expected)
    dry = np.where(np.isnan(dry), dry_expected, dry)

    oversaturated = pd.array(
        np.where(np.isnan(saturation), pd.NA, saturation > 100 + saturation_tolerance),
        dtype="boolean",
    )
    _warn_oversaturated(df, oversaturated, saturation, saturation_tolerance)

    replaced = [column for column in OUTPUT_COLUMNS if column in df.columns]
    if replaced:
        warn(f"Replaced the existing columns {', '.join(map(repr, replaced))}.")

    result = df.copy()
    result["dry_unit_weight"], weight_unit = _units.to_display(
        dry, "kN/m3", "unit_weight", system
    )
    result["specific_gravity"] = gravity
    result["specific_gravity_source"] = source
    result["void_ratio"] = void_ratio
    result["porosity"] = porosity
    result["degree_of_saturation"] = saturation
    result["saturated_unit_weight"], _ = _units.to_display(
        saturated, "kN/m3", "unit_weight", system
    )
    result["oversaturated"] = oversaturated
    result.attrs["units"] = {
        **_units.units_of(df),
        **(units or {}),
        "dry_unit_weight": weight_unit,
        "saturated_unit_weight": weight_unit,
        "porosity": "%",
        "degree_of_saturation": "%",
    }
    if judged is not None:
        result.attrs["judgments"] = {
            **df.attrs.get("judgments", {}),
            values.name: values.record(),
        }
    result.attrs["phase_relations"] = {
        "water_unit_weight": settings.water_unit_weight,
        "gravity": f"{G} m/s2",
        "saturation_tolerance": saturation_tolerance,
    }
    return result


# --- Inputs -------------------------------------------------------------------------


def _check_columns(df: Any) -> None:
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    missing = [c for c in ("bulk_unit_weight", "water_content") if c not in df.columns]
    if missing:
        raise ColumnError(
            f"df has no column {', '.join(map(repr, missing))}. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}. Start from "
            'ht.template("density") or p.density().'
        )
    if "particle_density" in df.columns and "particle_density_assumed" not in df:
        raise ColumnError(
            "df has particle_density but no particle_density_assumed, so hangtu "
            "can't tell measured values from assumed ones. Add the column: True "
            "where the value was assumed (# in an AGS file), False where measured."
        )


def _unit_weight(
    df: pd.DataFrame, column: str, units: dict[str, str] | None
) -> np.ndarray:
    unit = _units.resolve_units(df, [column], units, analysis=True)[column]
    return _units.convert(
        numeric_column(df, column),
        _units.parse_unit(unit, column),
        "unit_weight",
        _UNIT_WEIGHT,
    )


def _water_unit_weight() -> float:
    value, unit = _units.parse_quantity(settings.water_unit_weight, "unit_weight")
    return float(
        _units.convert([value], _units.parse_unit(unit), "unit_weight", _UNIT_WEIGHT)[0]
    )


def _gravity_from_particle_density(
    df: pd.DataFrame, units: dict[str, str] | None, rho_w: float
) -> tuple[np.ndarray, np.ndarray]:
    """Gs and its source from the row's particle density; blank where it has none."""
    gravity = np.full(len(df), np.nan)
    source = np.full(len(df), None, dtype=object)
    if "particle_density" not in df.columns:
        return gravity, source
    unit = _units.resolve_units(df, ["particle_density"], units, analysis=True)[
        "particle_density"
    ]
    rho_s = _units.convert(
        numeric_column(df, "particle_density"),
        _units.parse_unit(unit, "particle_density"),
        "density",
        _DENSITY,
    )
    # A blank flag is read as measured: p.density() writes True or False on
    # every row with a particle density, so a blank only comes from a hand-made
    # CSV (Decision 3).
    assumed = (
        df["particle_density_assumed"].astype("boolean").fillna(False).to_numpy(bool)
    )
    has = ~np.isnan(rho_s)
    gravity[has] = rho_s[has] / rho_w
    source[has & ~assumed] = "measured"
    source[has & assumed] = "assumed"
    return gravity, source


def _warn_assumed(source: np.ndarray) -> None:
    count = int((source == "assumed").sum())
    if count:
        warn(
            f"{count} row{'s use' if count != 1 else ' uses'} a particle density "
            "the file marks as assumed (#); specific_gravity_source says which. "
            "It is the value the lab used, so a judgment doesn't replace it."
        )


def _judged(
    df: pd.DataFrame, needs: np.ndarray, argument: Any, judgments: Any
) -> tuple[Values, np.ndarray, np.ndarray] | None:
    """Gs from the judgment for the rows that need it, and the rows with no key."""
    if not needs.any():
        if argument is not None:
            warn(
                "specific_gravity= isn't used: every row has a particle density, "
                "which a judgment never replaces."
            )
        return None
    read = None
    if argument is not None:
        read = read_judgments(judgments, df)
        if read is not None and "specific_gravity" in read.judgments:
            warn(
                f"specific_gravity= replaces the specific_gravity in {read.path.name}."
            )
        values = _argument(argument)
    else:
        read = read_judgments(judgments, df)
        if read is None or "specific_gravity" not in read.judgments:
            raise HangtuError(_missing(read, int(needs.sum()), df))
        values = from_file(read.judgments["specific_gravity"], read)
    out = np.full(len(df), np.nan)
    no_key = np.zeros(len(df), bool)
    if values.by is None:
        out[needs] = take(values, [ALL], "row")[ALL]["specific_gravity"]
        return values, out, no_key
    if values.by not in df.columns:
        raise ColumnError(
            f"The specific_gravity values are keyed by {values.by!r}, and df has "
            f"no {values.by!r} column. Add it to the rows; p.density() has "
            "geology_unit when the project has a geology map."
        )
    keys = df[values.by].to_numpy(dtype=object)
    no_key = needs & pd.isna(keys)
    rows = needs & ~no_key
    keys = np.array(["" if pd.isna(k) else str(k) for k in keys], dtype=object)
    noun = "geology unit" if values.by == "geology_unit" else values.by
    found = take(values, keys[rows], noun)
    warn_unused(values, keys, f"df's {values.by}")
    out[rows] = [found[key]["specific_gravity"] for key in keys[rows]]
    return values, out, no_key


def _argument(argument: Any) -> Values:
    example = 'specific_gravity=2.70 or specific_gravity={"Alluvium": 2.68}'

    def number(value: Any, where: str) -> float:
        if (
            isinstance(value, bool)
            or not isinstance(value, Real)
            or not math.isfinite(value)
            or value <= 0
        ):
            raise HangtuError(
                f"{where} must be a positive number, not {value!r}. Example: {example}"
            )
        return float(value)

    if isinstance(argument, Mapping):
        if not argument:
            raise HangtuError(f"specific_gravity= is empty. Example: {example}")
        entries = {
            str(key): {"specific_gravity": number(value, f"specific_gravity[{key!r}]")}
            for key, value in argument.items()
        }
        texts = {
            key: {"specific_gravity": f"{entry['specific_gravity']:g}"}
            for key, entry in entries.items()
        }
        return Values("specific_gravity", "argument", "geology_unit", entries, texts)
    value = number(argument, "specific_gravity=")
    return Values(
        "specific_gravity",
        "argument",
        None,
        {ALL: {"specific_gravity": value}},
        {ALL: {"specific_gravity": f"{value:g}"}},
    )


def _missing(read: Any, count: int, df: pd.DataFrame) -> str:
    rows = f"{count} row{'s have' if count != 1 else ' has'} no particle density"
    example = 'specific_gravity={"Alluvium": 2.68}'
    if read is not None:
        return (
            f"{rows}, and the judgments file {str(read.path)!r} has no "
            "specific_gravity, a judgment with no default (SPEC §4). Add "
            "specific_gravity: to the file, keyed by geology unit, or give it in "
            f"the call, {example}."
        )
    hint = (
        ""
        if "judgments_file" in df.attrs
        else " If df came from a Project dataset, merge and concat drop df.attrs: "
        "pass judgments=p.judgments."
    )
    return (
        f"{rows}, so their Gs is the specific_gravity judgment, which has no "
        f"default (SPEC §4). Give it in the call, {example}, or in a judgments "
        "file under specific_gravity: and pass judgments=ht.judgments(path), or "
        f"set it on the project with p.set_judgments(path).{hint}"
    )


# --- Checks -------------------------------------------------------------------------


def _warn_blank(reasons: dict[str, np.ndarray]) -> None:
    counted = []
    seen = np.zeros(len(next(iter(reasons.values()))), bool)
    for reason, mask in reasons.items():
        new = mask & ~seen
        seen |= mask
        if new.any():
            counted.append(f"{int(new.sum())} with {reason}")
    if counted:
        warn(
            "The phase relations are blank for rows "
            + "; ".join(counted)
            + ". Give each row a bulk unit weight, a water content and a "
            "particle density or a specific_gravity judgment."
        )


def _dry_tolerance() -> float:
    """QC B001's default tolerance, as a unit weight (kN/m³)."""
    text = _config.load("qc/rules.yaml")["rules"]["B001"]["thresholds"][
        "dry_density_tolerance"
    ]
    value, unit = _units.parse_quantity(text, "density")
    density = _units.convert([value], _units.parse_unit(unit), "density", _DENSITY)[0]
    return float(density) * G


def _check_dry(df: pd.DataFrame, dry: np.ndarray, expected: np.ndarray) -> None:
    tolerance = _dry_tolerance()
    with np.errstate(invalid="ignore"):
        off = np.abs(dry - expected) > tolerance + _SLACK
    if off.any():
        warn(
            f"dry_unit_weight differs from bulk_unit_weight / (1 + w) by more than "
            f"{tolerance:.3f} kN/m3 (QC B001's tolerance) in {_rows(df, off)}. The "
            "given value is kept and not used; check the three values, which "
            "should come from one specimen. On AGS data, p.qc() reports these as "
            "B001."
        )


def _warn_oversaturated(
    df: pd.DataFrame,
    oversaturated: pd.arrays.BooleanArray,
    saturation: np.ndarray,
    tolerance: float,
) -> None:
    flagged = oversaturated.fillna(False).to_numpy(bool)
    if not flagged.any():
        return
    warn(
        f"Degree of saturation above {100 + tolerance:g} % in {_rows(df, flagged)} "
        f"(highest {np.nanmax(saturation[flagged]):.1f} %), flagged in "
        "oversaturated. Above 100 % is impossible: check Gs, the bulk unit "
        "weight, and that the water content is the same specimen's."
    )


def _rows(df: pd.DataFrame, mask: np.ndarray) -> str:
    """Name rows by hole and depth where df has them, else by index label."""
    if not {"loca_id", "depth"} <= set(df.columns):
        return "rows " + rows_text(df.index[mask])
    unit = _units.units_of(df).get("depth", "")
    named = [
        f"{loca} at {depth:g} {unit}".rstrip()
        for loca, depth in zip(
            df["loca_id"][mask], pd.to_numeric(df["depth"][mask]), strict=True
        )
    ]
    more = f" and {len(named) - 5} more" if len(named) > 5 else ""
    return ", ".join(named[:5]) + more
