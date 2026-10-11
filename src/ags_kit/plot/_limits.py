"""Axis limits and ticks (docs/plots/P00-framework.md §8)."""

import math
from typing import Literal

from matplotlib.axes import Axes
from matplotlib.ticker import (
    LogFormatterSciNotation,
    LogLocator,
    MultipleLocator,
    NullFormatter,
)

MAX_TICKS = 8
PADDING = 0.05
_MULTIPLIERS = (1, 2, 5)


def _snap(value: float) -> float:
    """Remove floating-point noise, e.g. 0.30000000000000004 -> 0.3."""
    return float(f"{value:.12g}")


def _span_in_steps(lo: float, hi: float, step: float) -> tuple[int, int]:
    # The tolerance keeps a value that is a whole number of steps from rounding
    # out to the next step.
    return math.floor(lo / step + 1e-9), math.ceil(hi / step - 1e-9)


def nice_step(lo: float, hi: float) -> float:
    """Return the smallest step of 1, 2 or 5 x 10ⁿ that gives at most 8 ticks.

    The ticks run from ``lo`` rounded down to ``hi`` rounded up, in that step.
    This gives 4 to 8 major ticks for any range.
    """
    if not hi > lo:
        raise ValueError(f"hi ({hi}) must be greater than lo ({lo}).")
    exponent = math.floor(math.log10((hi - lo) / MAX_TICKS))
    while True:
        for multiplier in _MULTIPLIERS:
            step = _snap(multiplier * 10.0**exponent)
            first, last = _span_in_steps(lo, hi, step)
            if last - first + 1 <= MAX_TICKS:
                return step
        exponent += 1


def nice_limits(
    vmin: float,
    vmax: float,
    *,
    start_at_zero: bool,
    typical: tuple[float, float] | None = None,
) -> tuple[float, float]:
    """Return axis limits on "nice" values that enclose ``vmin`` to ``vmax``.

    Parameters
    ----------
    vmin, vmax
        The data range.
    start_at_zero
        For ratio-scale quantities: when all values are ≥ 0, the lower limit
        is 0. Otherwise both ends are padded by 5%.
    typical
        A preset's typical range, used when all values are equal, widened if
        needed to include the value.
    """
    if not (math.isfinite(vmin) and math.isfinite(vmax)) or vmin > vmax:
        raise ValueError(f"Need finite vmin <= vmax, got ({vmin}, {vmax}).")
    zero = start_at_zero and vmin >= 0
    if vmin == vmax:
        if typical is not None:
            return min(typical[0], vmin), max(typical[1], vmax)
        step = 10.0 ** math.floor(math.log10(abs(vmin))) if vmin else 1.0
        lo, hi = vmin - step, vmax + step
        if zero:
            lo = max(lo, 0.0)
    elif zero:
        lo, hi = 0.0, vmax
    else:
        padding = PADDING * (vmax - vmin)
        lo, hi = vmin - padding, vmax + padding
    step = nice_step(lo, hi)
    first, last = _span_in_steps(lo, hi, step)
    return _snap(first * step), _snap(last * step)


def _decade(value: float, rounding: Literal["floor", "ceil"]) -> int:
    exponent = math.log10(value)
    if abs(exponent - round(exponent)) < 1e-9:
        return round(exponent)
    return math.floor(exponent) if rounding == "floor" else math.ceil(exponent)


def log_limits(vmin: float, vmax: float, min_decades: int = 2) -> tuple[float, float]:
    """Return whole-decade limits enclosing positive data, at least ``min_decades``.

    The upper end is extended when the data span fewer decades. Values ≤ 0
    can't be drawn on a log axis: count and remove them first.
    """
    if not vmin > 0 or vmin > vmax:
        raise ValueError(f"Need 0 < vmin <= vmax for a log axis, got ({vmin}, {vmax}).")
    lo, hi = _decade(vmin, "floor"), _decade(vmax, "ceil")
    hi = max(hi, lo + min_decades)
    return 10.0**lo, 10.0**hi


def set_linear_axis(
    ax: Axes, axis: Literal["x", "y"], limits: tuple[float, float]
) -> None:
    """Set linear limits and major ticks every ``nice_step``.

    Pass ``limits`` reversed, as ``(high, low)``, for an inverted axis.
    """
    lo, hi = sorted(limits)
    getattr(ax, f"set_{axis}lim")(*limits)
    getattr(ax, f"{axis}axis").set_major_locator(MultipleLocator(nice_step(lo, hi)))


def set_log_axis(
    ax: Axes, axis: Literal["x", "y"], limits: tuple[float, float]
) -> None:
    """Make an axis logarithmic with labeled decades and unlabeled minor ticks 2 to 9.

    Minor gridlines are drawn on log axes only (P00 §6).
    """
    getattr(ax, f"set_{axis}scale")("log")
    getattr(ax, f"set_{axis}lim")(*limits)
    target = getattr(ax, f"{axis}axis")
    target.set_major_locator(LogLocator(base=10, numticks=99))
    target.set_major_formatter(LogFormatterSciNotation(base=10))
    target.set_minor_locator(LogLocator(base=10, subs=range(2, 10), numticks=99))
    target.set_minor_formatter(NullFormatter())
    ax.grid(True, which="minor", axis=axis, linewidth=0.3)


def apply_vertical_axis(
    ax: Axes, vs: Literal["depth", "elevation"], vmin: float, vmax: float
) -> tuple[float, float]:
    """Set up the y axis for depth or elevation and return its limits.

    Depth runs downward from 0 at the top to the nice ceiling of the deepest
    value. Elevation runs upward with padded nice limits.
    """
    if vs == "depth":
        lo, hi = nice_limits(min(vmin, 0.0), vmax, start_at_zero=True)
        set_linear_axis(ax, "y", (hi, lo))
    elif vs == "elevation":
        lo, hi = nice_limits(vmin, vmax, start_at_zero=False)
        set_linear_axis(ax, "y", (lo, hi))
    else:
        raise ValueError(f'vs must be "depth" or "elevation", not {vs!r}.')
    return lo, hi
