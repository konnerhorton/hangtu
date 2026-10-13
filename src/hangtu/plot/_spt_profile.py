"""P02 SPT N profile (docs/plots/P02-spt-profile.md)."""

from typing import Any, Literal

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from hangtu import analysis
from hangtu._settings import settings
from hangtu.errors import HangtuError
from hangtu.plot import _values
from hangtu.plot._profile import _draw_profile

N_COLUMNS = ("spt_n", "spt_n60", "spt_n_capped")
REFUSAL_OPTIONS = ("cap", "exclude")
# A refusal drawn at the cap: a filled triangle pointing right (P02 §7).
REFUSAL = "refusal"
REFUSAL_FLAGS = {
    REFUSAL: _values.Flag(">", _values.CARET_SIZE, "refusal", "refusal"),
}


def _check_choice(name: str, value: Any, choices: tuple[str, ...]) -> None:
    if value not in choices:
        raise HangtuError(
            f"{name} must be one of {', '.join(map(repr, choices))}, not "
            f"{value!r}. Example: {name}={choices[-1]!r}"
        )


def spt_profile(
    df: pd.DataFrame,
    *,
    n: Literal["spt_n", "spt_n60", "spt_n_capped"] = "spt_n",
    vs: Literal["elevation", "depth"] | None = None,
    refusal: Literal["cap", "exclude"] = "cap",
    hammer_efficiency: float | None = None,
    cap: int | None = None,
    label: str | None = None,
    color_by: str | None = "geology_unit",
    marker_by: str | None = None,
    connect: bool = False,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    xaxis_position: Literal["top", "bottom"] = "bottom",
    secondary: Literal["depth"] | None = None,
    strata: pd.DataFrame | None = None,
    water_level: float | list[tuple[float, str]] | pd.DataFrame | None = None,
    ranges: pd.DataFrame | str | None = None,
    design_lines: pd.DataFrame | None = None,
    reference_lines: list[tuple[float, str]] | None = None,
    stats_box: bool | list[str] = False,
    stats_box_room: bool = True,
    note: str | None = None,
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes]:
    """Plot SPT N against depth or elevation (P02).

    The data first go through ``ht.analysis.spt()``, which finds refusals and
    computes N60 and capped N. Refusals are drawn at the cap as a filled
    triangle and counted. Everything else is as ``ht.plot.profile()``: points
    colored by geology unit, the same overlays, and nothing dropped silently.

    The vertical position is the ``depth`` (or ``elevation``) you give. Give
    the depth of the middle of the test drive when you know it: a test's top
    depth plots it up to 0.45 m (1.5 ft) high.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test, as ``ht.template("spt")``: ``spt_n`` plus
        ``depth`` or ``elevation``.
    n : {"spt_n", "spt_n60", "spt_n_capped"}
        The value plotted: N as reported, N60, or N capped for refusals. N and
        N60 are never mixed in one plot.
    vs : {"elevation", "depth"}, optional
        The vertical axis, as ``profile()``.
    refusal : {"cap", "exclude"}
        ``"cap"`` draws refusals at the cap; ``"exclude"`` leaves them out and
        counts them.
    hammer_efficiency : float, optional
        Energy ratio in percent for tests without ``energy_ratio``. Defaults
        to ``ht.settings.hammer_efficiency``.
    cap : int, optional
        Blow count refusals are drawn at. Defaults to ``ht.settings.spt_cap``.
    units : dict, optional
        ``{column: unit}``, overriding the units declared on ``df``.
        ``spt_penetration`` needs units only when refusals are found from it.
    **kwargs
        ``label``, ``color_by``, ``marker_by``, ``connect``, ``xlim``,
        ``ylim``, ``xaxis_position``, ``secondary``, the overlays (``strata``,
        ``water_level``, ``ranges``, ``design_lines``, ``reference_lines``,
        ``stats_box``, ``stats_box_room``, ``note``), ``palette``,
        ``display_units``, ``figsize``, ``ax`` and style overrides: as
        ``ht.plot.profile()``. Ranges and reference lines are in blows.

    Returns
    -------
    fig, ax

    Examples
    --------
    >>> spt = ht.read_csv("spt.csv", units={"depth": "ft", "ground_level": "ft",
    ...                                     "spt_penetration": "in"})
    >>> fig, ax = ht.plot.spt_profile(spt, connect=True)
    >>> fig, ax = ht.plot.spt_profile(spt, n="spt_n60", hammer_efficiency=80)
    """
    _check_choice("n", n, N_COLUMNS)
    _check_choice("refusal", refusal, REFUSAL_OPTIONS)
    if refusal == "exclude":
        raise NotImplementedError('refusal="exclude" is built in P02 build 2.')
    data = analysis.spt(df, hammer_efficiency=hammer_efficiency, cap=cap, units=units)
    cap = settings.spt_cap if cap is None else cap  # checked by the analysis
    refused = data["spt_refusal"].to_numpy(dtype=bool)
    data[n] = np.where(refused, float(cap), data[n].to_numpy(dtype=float))
    flags = np.where(refused, REFUSAL, "").astype(object)

    hints = {}
    if not {"spt_refusal", "spt_penetration"} & set(df.columns):
        hints["spt_refusal"] = (
            "refusals can't be found. Add it, or 'spt_penetration' with its units"
        )
    return _draw_profile(
        data,
        n,
        vs=vs,
        preset=n,
        label=label,
        color_by=color_by,
        marker_by=marker_by,
        connect=connect,
        intervals=False,
        xlim=xlim,
        ylim=ylim,
        xaxis_position=xaxis_position,
        secondary=secondary,
        strata=strata,
        water_level=water_level,
        ranges=ranges,
        design_lines=design_lines,
        reference_lines=reference_lines,
        stats_box=stats_box,
        stats_box_room=stats_box_room,
        note=note,
        palette=palette,
        units=units,
        display_units=display_units,
        figsize=figsize,
        ax=ax,
        flags=flags,
        flag_kinds=REFUSAL_FLAGS,
        extra_hints=hints,
        **style_overrides,
    )
