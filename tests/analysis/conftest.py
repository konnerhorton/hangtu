"""Helpers shared by the analysis tests.

The golden triaxial readings (M11 c), at the end of the file, are shared by the
failure, stiffness and dilatancy tests.

Terzaghi's one-dimensional consolidation, for c_v golden readings (M19 c2).

Written from the series, not from hangtu, so readings generated here test
``consolidation_coefficient_from_readings()`` from outside it. The average
degree of consolidation of a layer drained at both faces, at time factor
T = c_v t / d², d the drainage path (half the specimen's height):

    U(T) = 1 - Σ_{m=0}^{∞} (2 / M²) exp(-M² T),   M = π (2m + 1) / 2

Checked in ``test_consolidation_coefficient_from_readings.py`` against
Abuel-Naga & Pender (2012), Table 1, p. 45, column i_cv = 0: T at U = 10 % to
90 %, to the table's three decimals.

The readings add an immediate compression and a secondary compression to the
primary one, as the c2 spec's golden increment was generated:

    y(t) = immediate + ρ U(T) + secondary × log10(1 + t / t1),   t > 0

with t1 the time at T = 1 and ρ the primary compression. y(0) = 0.
"""

import math
from pathlib import Path

import pandas as pd

#: Minutes in a year of 365.25 days.
MINUTES_PER_YEAR = 525960.0
#: The reading times of the c2 spec's golden increment, in minutes.
TIMES = (0, 0.1, 0.25, 0.5, 1, 2, 4, 8, 15, 30, 60, 120, 240, 480, 1440)


def degree(time_factor: float, terms: int = 200) -> float:
    """U(T), the average degree of consolidation (a fraction)."""
    if time_factor <= 0:
        return 0.0
    total = 0.0
    for m in range(terms):
        big_m = math.pi * (2 * m + 1) / 2
        total += 2 / big_m**2 * math.exp(-(big_m**2) * time_factor)
    return 1 - total


def time_factor(fraction: float) -> float:
    """T at which U(T) = ``fraction``, by bisection on the series."""
    low, high = 0.0, 10.0
    for _ in range(200):
        middle = (low + high) / 2
        if degree(middle) < fraction:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def readings(
    cv: float,
    average_height: float,
    primary: float,
    *,
    immediate: float = 0.0,
    secondary: float = 0.0,
    times=TIMES,
    rounding: int | None = None,
) -> list[float]:
    """y (mm, positive with the movement) at ``times`` (min).

    ``cv`` in m²/yr, ``average_height`` H̄ in mm (double drainage: d = H̄/2),
    ``primary`` ρ in mm, ``secondary`` in mm per log cycle of time.
    """
    rate = cv * 1.0e6 / MINUTES_PER_YEAR  # mm²/min
    drainage = average_height / 2
    t1 = drainage**2 / rate
    values = []
    for t in times:
        y = 0.0
        if t > 0:
            y = immediate + primary * degree(rate * t / drainage**2)
            y += secondary * math.log10(1 + t / t1)
        values.append(y if rounding is None else round(y, rounding))
    return values


#: The golden readings of the M11 (c) spec, in kPa and percent.
GOLDENS = Path(__file__).parents[1] / "data" / "triaxial_readings_goldens.csv"
STRESSES = ["cell_pressure", "back_pressure", "deviator_stress", "excess_pore_pressure"]


def triaxial_goldens(*stages, **columns):
    """The golden readings of ``stages`` (all when none), in kPa."""
    df = pd.read_csv(GOLDENS, dtype={"test_stage": str})
    if stages:
        df = df[df["specimen_id"].isin(stages)].reset_index(drop=True)
    for column, values in columns.items():
        df[column] = values
    df.attrs["units"] = dict.fromkeys(STRESSES, "kPa")
    return df


#: M23 (b)'s golden G1: a drained stage on PLAXIS's hyperbola, E50 = 20 000 kPa,
#: Rf = 0.9, q_f = 300 kPa at 8.25 %, one reading past failure (strain in %).
G1_Q = [
    (0, 0), (0.1, 32.79), (0.2, 59.70), (0.4, 101.27), (0.6, 131.87),
    (0.8, 155.34), (1.0, 173.91), (1.5, 206.90), (2, 228.57), (3, 255.32),
    (4, 271.19), (6, 289.16), (8.25, 300.00), (10, 295.00),
]  # fmt: skip
G1_EV = {0: 0, 1.0: 0.25, 2: 0.35, 4: 0.20, 6: -0.10, 7.0: -0.70, 8.25: -1.45}


def stage_frame(specimen, test_type, curve, *, volumetric=None, cell=300.0,
                back=100.0, excess=None, stage="1"):  # fmt: skip
    """One stage's readings in kPa and %, in strain order.

    ``curve`` is (strain, q) pairs; ``volumetric`` and ``excess`` map strain to
    εv and Δu, on the q reading at that strain or, where there is none, on a
    row of their own.
    """
    volumetric = volumetric or {}
    excess = excess or {}
    q = dict(curve)
    strains = sorted(set(q) | set(volumetric) | set(excess))
    df = pd.DataFrame(
        {
            "specimen_id": specimen,
            "test_stage": stage,
            "test_type": test_type,
            "cell_pressure": cell,
            "back_pressure": back,
            "axial_strain": [float(s) for s in strains],
            "deviator_stress": [q.get(s, math.nan) for s in strains],
            "excess_pore_pressure": [excess.get(s, math.nan) for s in strains],
            "volumetric_strain": [volumetric.get(s, math.nan) for s in strains],
        }
    )
    df.attrs["units"] = dict.fromkeys(STRESSES, "kPa")
    return df


def g1(offset=0.0, specimen="G1"):
    """G1, with ``offset`` kPa added to every q (G3: 50)."""
    curve = [(s, q + offset) for s, q in G1_Q]
    return stage_frame(specimen, "CD", curve, volumetric=G1_EV)


def stages_frame(*frames):
    df = pd.concat(frames, ignore_index=True)
    df.attrs["units"] = dict.fromkeys(STRESSES, "kPa")
    return df
