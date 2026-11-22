"""Terzaghi's one-dimensional consolidation, for c_v golden readings (M19 c2).

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
