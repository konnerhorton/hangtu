"""The line every wave 2 fit is made of (docs/work/m11b-envelope-fit.md, Decision 3).

A criterion's public function transforms its failure points into x and y, fits
y = a + b x here, free or with a fixed, and back-transforms a and b into the
criterion's parameters. Mohr-Coulomb uses x = s′, y = t; M17's fits reuse it.
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Line:
    """A least-squares line y = a + b x and what it was fitted to."""

    #: The intercept a: fitted, or the value it was fixed at.
    intercept: float
    #: The slope b.
    slope: float
    #: Whether the intercept was fixed rather than fitted.
    fixed_intercept: bool
    #: The number of points.
    count: int
    #: The centered R², 1 - Σ(y - ŷ)² / Σ(y - ȳ)²; NaN for one point or all y equal.
    r_squared: float
    #: y - ŷ for each point, in the order given.
    residuals: tuple[float, ...]
    #: Why there is no line, or None. With a reason, intercept, slope and
    #: r_squared are NaN and residuals is empty.
    no_fit_reason: str | None


def line_fit(
    x: np.ndarray, y: np.ndarray, *, intercept: float | None = None, x_name: str = "x"
) -> Line:
    """Fit y = a + b x by ordinary least squares, free or through ``intercept``.

    Free: b = Sxy / Sxx and a = ȳ - b x̄, with Sxx = Σ(x - x̄)² and
    Sxy = Σ(x - x̄)(y - ȳ). With a fixed: b = Σx(y - a) / Σx², least squares
    with one unknown. R² is the centered definition in both cases, so a line
    with a fixed intercept can have a low or negative R² and is comparable with
    the free one. ``x`` and ``y`` hold no NaN; the caller counts the rows it
    leaves out. ``x_name`` names x in the reason a line can't be fitted.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    count = len(x)
    reason = _no_fit_reason(x, intercept, x_name)
    if reason is not None:
        return Line(np.nan, np.nan, intercept is not None, count, np.nan, (), reason)
    if intercept is None:
        dx = x - x.mean()
        slope = float(np.sum(dx * (y - y.mean())) / np.sum(dx**2))
        a = float(y.mean() - slope * x.mean())
    else:
        a = float(intercept)
        slope = float(np.sum(x * (y - a)) / np.sum(x**2))
    residuals = y - (a + slope * x)
    total = float(np.sum((y - y.mean()) ** 2))
    r_squared = (
        1 - float(np.sum(residuals**2)) / total if count > 1 and total > 0 else np.nan
    )
    return Line(
        a,
        slope,
        intercept is not None,
        count,
        r_squared,
        tuple(map(float, residuals)),
        None,
    )


def _no_fit_reason(x: np.ndarray, intercept: float | None, x_name: str) -> str | None:
    count = len(x)
    if intercept is None:
        if count < 2:
            return f"{count} point{'' if count == 1 else 's'}: a line needs at least 2"
        if np.sum((x - x.mean()) ** 2) == 0:
            return f"all points at the same {x_name}"
        return None
    if count == 0:
        return "no points"
    if np.sum(x**2) == 0:
        return f"all points at {x_name} = 0"
    return None
