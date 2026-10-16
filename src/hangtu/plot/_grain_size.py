"""P05 grain size distribution (docs/plots/P05-grain-size.md)."""

import os
from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MultipleLocator

from hangtu._settings import _display_units, settings
from hangtu.analysis._fractions import fraction_system
from hangtu.errors import HangtuError
from hangtu.plot import _fraction_band, _layers, _values, style
from hangtu.plot._legend import add_legend
from hangtu.plot._limits import clear_of_data, log_limits, set_log_axis
from hangtu.plot._notes import Notes

MIN_LIMITS = (0.001, 100.0)  # mm; the x axis covers at least these (§6)
MIN_DECADES = 5
Y_LIMITS = (0.0, 100.0)
Y_STEP = 10.0


def _decade_label(value: float, _position: Any) -> str:
    """Write a decade in plain numbers: 0.001, 0.01, ..., 100."""
    return np.format_float_positional(value, trim="-")


def x_limits(xlim: Any, sizes: np.ndarray) -> tuple[float, float]:
    """Return ``xlim`` as given, else whole decades over the data and 0.001-100 mm.

    A point on a whole decade moves that limit out one decade (P00 §8).
    """
    if xlim is not None:
        return _values.check_limits("xlim", xlim, log=True)
    if not sizes.size:
        return MIN_LIMITS
    finest, coarsest = float(sizes.min()), float(sizes.max())
    limits = log_limits(
        min(finest, MIN_LIMITS[0]),
        max(coarsest, MIN_LIMITS[1]),
        MIN_DECADES,
        clear=False,
    )
    return clear_of_data(limits, finest, coarsest, log=True)


def _set_axes(ax: Axes, limits: tuple[float, float], reverse: bool) -> None:
    set_log_axis(ax, "x", limits[::-1] if reverse else limits)
    ax.xaxis.set_major_formatter(FuncFormatter(_decade_label))
    ax.set_ylim(*Y_LIMITS)
    ax.yaxis.set_major_locator(MultipleLocator(Y_STEP))
    ax.grid(True, which="major")
    ax.set_xlabel("Particle size (mm)")
    ax.set_ylabel("Percent passing (%)")


def grain_size(
    df: pd.DataFrame,
    *,
    fractions: str | dict | os.PathLike | None = "astm_uscs",
    sieves: Literal["auto", "us", "iso"] | list[tuple[float, str]] | None = "auto",
    d_values: bool | list[int] = False,
    envelopes: pd.DataFrame | str | None = None,
    envelope_colors: dict[str, str] | None = None,
    color_by: str | None = "geology_unit",
    order: list[str] | None = None,
    reverse: bool = False,
    xlim: tuple[float, float] | None = None,
    note: str | None = None,
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes]:
    """Plot grading curves on a log size axis with the soil fractions above (P05).

    Not finished: only the axes, the band and the sieve labels are drawn.
    """
    system = _display_units(display_units or settings.display_units)
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if len(df) or d_values or envelopes is not None or envelope_colors:
        raise NotImplementedError("Curves, D-values and envelopes come next (P05).")
    system_fractions = fraction_system(fractions)[1] if fractions is not None else []
    sieve_list = _fraction_band.sieve_list(sieves, system)
    limits = x_limits(xlim, np.empty(0))

    with style.context(**style_overrides):
        notes = Notes()
        if note is not None:
            notes.add_text(str(note))
        if ax is None:
            fig, ax = plt.subplots(
                figsize=figsize or settings.figure_sizes["default"],
                layout="constrained",
            )
        else:
            fig = ax.figure
        style.style_axes(ax)
        _set_axes(ax, limits, reverse)
        ax.grain_size_header = None
        if fractions is not None:
            ax.grain_size_header = _fraction_band.add_header(ax)
            _fraction_band.draw_band(ax.grain_size_header, ax, system_fractions, limits)
        _fraction_band.draw_sieves(ax, sieve_list, limits)
        ax.text(
            0.5,
            0.5,
            "No data",
            transform=ax.transAxes,
            ha="center",
            va="center",
            color="0.4",
            zorder=_layers.ANNOTATIONS,
        )
        add_legend(ax, [], notes)
        notes.render(ax)
    return fig, ax
