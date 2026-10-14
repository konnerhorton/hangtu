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


def _on(limit: float, value: float, step: float) -> bool:
    return abs(limit - value) <= 1e-9 * step


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
    clear: bool = True,
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
    clear
        Keep the data off the limits (P00 §8): a limit that ``vmin`` or
        ``vmax`` would sit on moves out one step, and the limits are snapped
        again. A lower limit of 0 stays at 0. False when ``vmin`` to ``vmax``
        isn't data, such as a typical range drawn with no data.
    """
    if not (math.isfinite(vmin) and math.isfinite(vmax)) or vmin > vmax:
        raise ValueError(f"Need finite vmin <= vmax, got ({vmin}, {vmax}).")
    zero = start_at_zero and vmin >= 0
    if vmin == vmax:
        if typical is not None:
            lo, hi = min(typical[0], vmin), max(typical[1], vmax)
            return _clear(lo, hi, vmin, vmax) if clear else (lo, hi)
        step = 10.0 ** math.floor(math.log10(abs(vmin))) if vmin else 1.0
        lo, hi = vmin - step, vmax + step
        if not hi > lo:  # step underflows for subnormal values such as 5e-324
            lo, hi = vmin - 1.0, vmax + 1.0
        if zero:
            lo = max(lo, 0.0)
    elif zero:
        lo, hi = 0.0, vmax
    else:
        padding = PADDING * (vmax - vmin)
        lo, hi = vmin - padding, vmax + padding
    lo, hi = _nice(lo, hi)
    return _clear(lo, hi, vmin, vmax) if clear else (lo, hi)


def _nice(lo: float, hi: float) -> tuple[float, float]:
    step = nice_step(lo, hi)
    first, last = _span_in_steps(lo, hi, step)
    return _snap(first * step), _snap(last * step)


def _clear(lo: float, hi: float, vmin: float, vmax: float) -> tuple[float, float]:
    """Move a limit that sits on ``vmin`` or ``vmax`` out one step (P00 §8)."""
    step = nice_step(lo, hi)
    low = lo != 0 and _on(lo, vmin, step)
    high = _on(hi, vmax, step)
    if not (low or high):
        return lo, hi
    # The wider range can take a larger step, so snap again to its ticks.
    return _nice(lo - step if low else lo, hi + step if high else hi)


def _decade(value: float, rounding: Literal["floor", "ceil"]) -> int:
    exponent = math.log10(value)
    if abs(exponent - round(exponent)) < 1e-9:
        return round(exponent)
    return math.floor(exponent) if rounding == "floor" else math.ceil(exponent)


def log_limits(
    vmin: float, vmax: float, min_decades: int = 2, *, clear: bool = True
) -> tuple[float, float]:
    """Return whole-decade limits enclosing positive data, at least ``min_decades``.

    The upper end is extended when the data span fewer decades. Values ≤ 0
    can't be drawn on a log axis: count and remove them first. ``clear`` is
    as in ``nice_limits``: a value on a whole decade gets one more decade
    beyond it.
    """
    if not vmin > 0 or vmin > vmax:
        raise ValueError(f"Need 0 < vmin <= vmax for a log axis, got ({vmin}, {vmax}).")
    lo, hi = _decade(vmin, "floor"), _decade(vmax, "ceil")
    if clear:
        lo -= _on(math.log10(vmin), lo, 1.0)
        hi += _on(math.log10(vmax), hi, 1.0)
    hi = max(hi, lo + min_decades)
    return 10.0**lo, 10.0**hi


def clear_of_data(
    limits: tuple[float, float], vmin: float, vmax: float, *, log: bool
) -> tuple[float, float]:
    """Move ``limits`` off the data ``vmin`` to ``vmax`` (P00 §8).

    For limits worked out from a wider range than the data, such as a
    preset's typical range around a single value.
    """
    lo, hi = limits
    if log:
        lo /= 10.0 ** _on(math.log10(vmin), math.log10(lo), 1.0)
        hi *= 10.0 ** _on(math.log10(vmax), math.log10(hi), 1.0)
        return lo, hi
    return _clear(lo, hi, vmin, vmax)


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
    ax: Axes,
    vs: Literal["depth", "elevation"],
    vmin: float,
    vmax: float,
    *,
    clear: bool = True,
) -> tuple[float, float]:
    """Set up the y axis for depth or elevation and return its limits.

    Depth runs downward from 0 at the top to the nice ceiling of the deepest
    value. Elevation runs upward with padded nice limits. ``clear`` is as in
    ``nice_limits``.
    """
    if vs == "depth":
        lo, hi = nice_limits(min(vmin, 0.0), vmax, start_at_zero=True, clear=clear)
        set_linear_axis(ax, "y", (hi, lo))
    elif vs == "elevation":
        lo, hi = nice_limits(vmin, vmax, start_at_zero=False, clear=clear)
        set_linear_axis(ax, "y", (lo, hi))
    else:
        raise ValueError(f'vs must be "depth" or "elevation", not {vs!r}.')
    return lo, hi
