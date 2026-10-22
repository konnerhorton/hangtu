"""P06 water content profile (docs/plots/P06-water-content-profile.md)."""

from collections.abc import Mapping
from typing import Any, Literal

import numpy as np
import pandas as pd
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.path import Path

from hangtu import units as _units
from hangtu._data import flag_column, rows_text, text_values
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.plot import _layers, _text_values, _values
from hangtu.plot._notes import Notes, edge_markers
from hangtu.plot._profile import Companion, _draw_profile

VALUE = "water_content"
LIMITS = ("plastic_limit", "liquid_limit")
LABEL = "Water content, w, and Atterberg limits"
FIXED = ("value", "preset", "log")  # profile() arguments P06 sets itself
BAR_WIDTH = 1.2  # points
TICK_SIZE = 4.0  # points
TICK = "|"
# The legend's "PL to LL": a bar with an end tick at each end.
BAR_MARKER = Path(
    [(-1.0, 0.0), (1.0, 0.0), (-1.0, -0.3), (-1.0, 0.3), (1.0, -0.3), (1.0, 0.3)],
    [Path.MOVETO, Path.LINETO] * 3,
)
BAR_LEGEND_SIZE = 14.0  # points
# A non-plastic specimen with a water content: open, in P01's NP text shape (P06 §7).
NON_PLASTIC = "non_plastic"
FLAGS = {
    **_values.QUALIFIERS,
    NON_PLASTIC: _values.Flag(
        _text_values.SHAPES[0],
        _text_values.SIZE,
        "non-plastic",
        "non_plastic_drawn",
        filled=False,
    ),
}
NP_HINT = "True marks a non-plastic (NP) specimen, drawn with no limits bar."


def _check_input(df: pd.DataFrame) -> None:
    present = [column for column in (VALUE, *LIMITS) if column in df.columns]
    if VALUE not in present and len(present) < len(LIMITS):
        raise ColumnError(
            "water_content_profile() needs a 'water_content' column, or both "
            "'plastic_limit' and 'liquid_limit'. Found "
            f"{', '.join(map(repr, present)) or 'neither'}. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}."
        )


def _limit_values(
    df: pd.DataFrame,
    units: Mapping[str, str] | None,
    display_units: str | None,
) -> dict[str, np.ndarray]:
    """Return PL and LL in display units, NaN where blank or the column is missing."""
    present = [column for column in LIMITS if column in df.columns]
    resolved = _units.resolve_units(df, present, units)
    values = {}
    for column in LIMITS:
        if column not in present:
            values[column] = np.full(len(df), np.nan)
            continue
        raw, texts = text_values(df, column)
        text = texts != ""
        if text.any():
            found = ", ".join(map(repr, dict.fromkeys(texts[text])))
            raise ColumnError(
                f"Column {column!r} has text in rows {rows_text(df.index[text])} "
                f"({found}). A limit must be a number or blank. For a non-plastic "
                "specimen, leave the limits blank and set 'non_plastic' to True."
            )
        values[column] = _units.to_display(
            raw, resolved[column], "percent", display_units
        )[0]
    return values


def _non_plastic_flags(data: pd.DataFrame, non_plastic: np.ndarray) -> np.ndarray:
    """Return each row's flag key, with NP rows that have a water content flagged.

    An NP row with a blank water content gets the text ``NP`` in ``data`` (a
    copy), so it is drawn at the left edge and counted as P01's text NP is.
    """
    flags = _values.qualifiers(data)
    qualified = non_plastic & (flags != "")
    if qualified.any():
        raise ColumnError(
            f"Rows {rows_text(data.index[qualified])} are marked non-plastic and "
            "have a qualifier. A non-plastic specimen is drawn at its water "
            "content: clear 'qualifier' on those rows, or set 'non_plastic' to "
            "False."
        )
    w, texts = text_values(data, VALUE)
    blank = non_plastic & np.isnan(w) & (texts == "")
    if blank.any():
        data[VALUE] = data[VALUE].astype(object)
        data.loc[blank, VALUE] = "NP"
    return np.where(non_plastic & np.isfinite(w), NON_PLASTIC, flags).astype(object)


def _warn_one_limit(df: pd.DataFrame, one: np.ndarray, pl: np.ndarray) -> None:
    if not one.any():
        return
    message = (
        f"Rows {rows_text(df.index[one])} have only one Atterberg limit, so "
        "they are drawn as a single tick."
    )
    if "plasticity_index" in df.columns:
        index = pd.to_numeric(df["plasticity_index"], errors="coerce").to_numpy()
        if (one & np.isnan(pl) & np.isfinite(index)).any():
            message += (
                " The plastic limit isn't computed from LL - PI: fill in "
                "'plastic_limit' on those rows, or remove them."
            )
    warn(message)


def _outside(values: np.ndarray, limits: tuple[float, float] | None) -> np.ndarray:
    if limits is None:
        return np.zeros(values.shape, dtype=bool)
    return (values < limits[0]) | (values > limits[1])


def _draw_ticks(
    ax: Axes,
    x: np.ndarray,
    y: np.ndarray,
    color: Any,
    xlim: tuple[float, float] | None,
) -> np.ndarray:
    """Draw end ticks; those beyond ``xlim`` at the edge. Returns that mask."""
    edge = np.zeros(x.size, dtype=bool)
    if xlim is not None:
        edge = edge_markers(ax, x, y, {"x": xlim}, color, TICK)
    ax.scatter(
        x[~edge],
        y[~edge],
        s=TICK_SIZE**2,
        marker=TICK,
        color=color,
        linewidths=BAR_WIDTH,
        zorder=_layers.LIMITS_BARS,
        gid="limits_tick",
    )
    return edge


def _limits_bars(
    pl: np.ndarray,
    ll: np.ndarray,
    bar: np.ndarray,
    one: np.ndarray,
    xlim: tuple[float, float] | None,
    ylim: tuple[float, float] | None,
) -> Companion:
    """Return the PL to LL bars and single ticks to draw in the profile (P06 §7)."""
    rows = bar | one

    def draw(
        ax: Axes,
        y: np.ndarray,
        groups: np.ndarray,
        colors: Mapping[Any, Any],
        notes: Notes,
    ) -> list[Artist]:
        shown = rows & np.isfinite(y)
        beyond = shown & _outside(y, ylim)
        shown &= ~beyond
        for group, color in colors.items():
            these = shown & (groups == group) if group is not None else shown
            bars = np.flatnonzero(these & bar)
            if bars.size:
                low, high = pl[bars], ll[bars]
                if xlim is not None:
                    low, high = np.clip(low, *xlim), np.clip(high, *xlim)
                gaps = np.full(bars.size, np.nan)
                ax.plot(
                    np.column_stack([low, high, gaps]).ravel(),
                    np.column_stack([y[bars], y[bars], gaps]).ravel(),
                    color=color,
                    linewidth=BAR_WIDTH,
                    solid_capstyle="butt",
                    zorder=_layers.LIMITS_BARS,
                    gid="limits_bar",
                )
            ends = np.concatenate([bars, bars, np.flatnonzero(these & one)])
            if not ends.size:
                continue
            singles = np.flatnonzero(these & one)
            x = np.concatenate([pl[bars], ll[bars], np.fmax(pl[singles], ll[singles])])
            edge = _draw_ticks(ax, x, y[ends], color, xlim)
            beyond[ends[edge]] = True
        notes.count(beyond, "beyond_limit")
        if not (shown & bar).any():
            return []
        return [
            Line2D(
                [],
                [],
                marker=BAR_MARKER,
                markersize=BAR_LEGEND_SIZE,
                markeredgewidth=BAR_WIDTH,
                color=_values.NEUTRAL,
                linestyle="none",
                label="PL to LL",
            )
        ]

    x = np.concatenate([pl[rows], ll[rows]])
    return Companion(rows=rows, x=x[np.isfinite(x)], draw=draw)


def water_content_profile(
    df: pd.DataFrame,
    *,
    limits: bool = True,
    vs: Literal["elevation", "depth"] | None = None,
    label: str | None = None,
    color_by: str | None = "geology_unit",
    marker_by: str | None = None,
    connect: bool = False,
    intervals: bool | Literal["auto"] = "auto",
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
    """Plot water content against depth or elevation, with the Atterberg limits (P06).

    Each specimen's water content is a point, and its plastic limit (PL) and
    liquid limit (LL) are a bar from PL to LL at the same depth, so you see
    where w sits in the plastic range. A row with only the limits draws the
    bar alone.

    A non-plastic specimen (``non_plastic`` True) has no bar, even with a
    liquid limit: it is drawn as an open diamond at its water content, or,
    without one, at the left edge as the text ``NP`` is, and counted.

    Limits are read as given. A row with one limit is drawn as a single tick
    and counted, and PL is never computed from LL - PI: fill in the missing
    limit, or remove the row. A row with PL above LL has no bar and is
    counted, with a warning naming it.

    Everything else is as ``ht.plot.profile()`` with the ``water_content``
    preset: points colored by geology unit, text values such as ``NP`` at the
    left edge, the same overlays, and nothing dropped silently. The arguments
    not listed below (``vs``, ``color_by``, ``marker_by``, ``connect``,
    ``intervals``, ``xlim``, ``ylim``, ``xaxis_position``, ``secondary``, the
    overlays ``strata``, ``water_level``, ``ranges``, ``design_lines``,
    ``reference_lines``, ``stats_box``, ``stats_box_room`` and ``note``,
    ``palette``, ``display_units``, ``figsize``, ``ax`` and style overrides)
    are as ``ht.plot.profile()``. ``stats_box`` summarizes water content only.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per specimen (``p.atterberg()``) or sample
        (``p.index_properties()``): ``water_content``, or ``plastic_limit``
        and ``liquid_limit``, or all three, plus ``depth`` or ``elevation``.
        See ``ht.template("atterberg")``.
    limits : bool
        Draw the PL to LL bars. False draws ``ht.plot.profile(df,
        "water_content", preset="water_content")``.
    label : str, optional
        The x-axis text; by default "Water content, w, and Atterberg limits".
        Units are added automatically.
    xlim : (low, high), optional
        Fixed limits in percent. By default from 0 to a nice value above the
        largest w, PL and LL. A bar beyond them is cut at the edge, with an
        arrow, and counted.
    units : dict, optional
        ``{column: unit}``, overriding the units declared on ``df``.

    Returns
    -------
    fig, ax

    Examples
    --------
    >>> fig, ax = ht.plot.water_content_profile(p.index_properties(), vs="elevation")
    >>> fig, ax = ht.plot.water_content_profile(
    ...     p.atterberg(geology=["Upper Clay"]), strata=strata
    ... )
    """
    fixed = [name for name in FIXED if name in style_overrides]
    if fixed:
        raise HangtuError(
            f"water_content_profile() always plots 'water_content' with the "
            f"water_content preset on a linear axis, so it doesn't take "
            f"{', '.join(fixed)}=. To plot another column, use ht.plot.profile()."
        )
    profile_arguments = {
        "vs": vs,
        "preset": VALUE,
        "color_by": color_by,
        "marker_by": marker_by,
        "connect": connect,
        "intervals": intervals,
        "xlim": xlim,
        "ylim": ylim,
        "xaxis_position": xaxis_position,
        "secondary": secondary,
        "strata": strata,
        "water_level": water_level,
        "ranges": ranges,
        "design_lines": design_lines,
        "reference_lines": reference_lines,
        "stats_box": stats_box,
        "stats_box_room": stats_box_room,
        "note": note,
        "palette": palette,
        "units": units,
        "display_units": display_units,
        "figsize": figsize,
        "ax": ax,
        **style_overrides,
    }
    if not limits:
        return _draw_profile(df, VALUE, label=label, **profile_arguments)

    _check_input(df)
    xlim = _values.check_limits("xlim", xlim) if xlim is not None else None
    ylim = _values.check_limits("ylim", ylim) if ylim is not None else None
    non_plastic = np.array(
        [flag is True for flag in flag_column(df, "non_plastic", NP_HINT)], dtype=bool
    )
    data = df.copy()
    if VALUE not in data.columns:
        data[VALUE] = np.nan
    flags = _non_plastic_flags(data, non_plastic)
    values = _limit_values(df, units, display_units)
    pl, ll = values["plastic_limit"], values["liquid_limit"]
    # NP is reported when PL can't be found, often with an LL: that's normal.
    with_pl = non_plastic & np.isfinite(pl)
    if with_pl.any():
        warn(
            f"Rows {rows_text(df.index[with_pl])} are marked non-plastic but have "
            "a plastic limit, so their limits aren't drawn. Check those rows."
        )
    pl = np.where(non_plastic, np.nan, pl)
    ll = np.where(non_plastic, np.nan, ll)
    both = np.isfinite(pl) & np.isfinite(ll)
    inverted = both & (pl > ll)
    bar = both & ~inverted
    one = np.isfinite(pl) != np.isfinite(ll)
    _warn_one_limit(df, one, pl)
    notes = Notes()
    notes.count(one, "one_limit")
    if inverted.any():
        warn(
            f"Rows {rows_text(df.index[inverted])} have a plastic limit above the "
            "liquid limit, which is impossible, so their limits aren't drawn. "
            "Check those rows."
        )
        notes.count(inverted, "limits_inverted")
    hints = {
        column: "the limits bars aren't drawn"
        for column in LIMITS
        if column not in df.columns
    }
    return _draw_profile(
        data,
        VALUE,
        label=LABEL if label is None else label,
        extra_hints=hints,
        notes=notes,
        flags=flags,
        flag_kinds=FLAGS,
        companion=_limits_bars(pl, ll, bar, one, xlim, ylim),
        **profile_arguments,
    )
