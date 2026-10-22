"""Vertical stress through each hole's log (docs/work/m13a-judgments.md, Decision 6).

Unit weights and water levels are judgments (SPEC §4): each comes from an
argument, else from a judgments file, else the call raises. Everything is
computed in m, kN/m³ and kPa and converted for display at the end.
"""

import numpy as np

from hangtu import units as _units
from hangtu._settings import settings

_UNIT_WEIGHT = _units.ureg.Unit("kilonewton / meter**3")


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
