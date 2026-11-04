"""P09 representative value profile (docs/plots/P09-representative-profile.md)."""

import textwrap
import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text
from matplotlib.typing import LineStyleType

from hangtu._settings import settings
from hangtu.errors import HangtuError
from hangtu.plot import _layers, _values, style
from hangtu.plot._notes import Notes, figure_of
from hangtu.plot._overlays import ValueScale, draw_stats_box, format_number
from hangtu.plot._profile import Overlay, ProfileAxes, _draw_profile, room_below_data
from hangtu.plot._vertical import Vertical
from hangtu.registry import column_info
from hangtu.stats._representative import representative
from hangtu.stats._result import RepresentativeResult, _label

REPRESENTATIVE_WIDTH = 1.5  # points (P09 §7)
MEAN_WIDTH = 0.8  # points
BAND_ALPHA = 0.15
STYLE_COLOR = "0.4"  # the gray legend entries naming each mark
TABLE_WRAP = 40  # characters per line of the view in the table
#: A view's representative line, by the order it was drawn on the axes (values=False).
VIEW_STYLES: tuple[LineStyleType, ...] = ("-", "-.", ":")
#: The section of the profile's legend that holds the lines' entries.
OVERLAY_SECTION = 2


def representative_profile(
    df: pd.DataFrame,
    *,
    value: str,
    by: str | None = None,
    method: str | None = None,
    side: str | None = None,
    distribution: str | None = None,
    trend: str | None = None,
    estimate: str | None = None,
    coefficient_of_variation: float | None = None,
    scale_of_fluctuation: float | None = None,
    failure_length: float | None = None,
    sensitivity_index: float | None = None,
    percentile: float | None = None,
    standard_deviations: float | None = None,
    pool: str | list[str] | None = None,
    include_assumed: bool = False,
    spt_refusal_upper_limit: float | str | Mapping[str, float | str] | None = None,
    judgments: Any = None,
    mean: bool = True,
    band: bool = True,
    table: bool = True,
    values: bool = True,
    vs: Literal["elevation", "depth"] | None = None,
    preset: str | None = None,
    log: bool | None = None,
    label: str | None = None,
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
    reference_lines: list[tuple[float, str]] | None = None,
    note: str | None = None,
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    legend: Literal["auto", "inside", "bottom", "right"] | bool = "auto",
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes, RepresentativeResult]:
    """Plot a property's representative value per unit on its profile (P09).

    Computes the representative values with
    :func:`hangtu.stats.representative` and draws them over the values, as
    :func:`profile` draws them: each geology unit's representative value,
    constant or a line with depth, solid, beside the mean (the median, for a
    lognormal distribution) it came from, dashed, with the band between them
    shaded, all in the unit's color. The lines span only the depths of their
    unit's values. The plot computes nothing of its own: the lines are
    ``result.design_lines(mean=True)``.

    A table at the lower left names the view and its judgments, then gives
    each unit's n and value (or the line's value at the top and base of its
    values), or the reason it has none. The footnote counts the values the
    lines left out: censored values and values with no depth, which a trend
    can't use, and assumed values and ranges, which are drawn but not in
    the lines.

    Every judgment is passed to ``representative()`` unchanged and none has
    a default (SPEC §4), so its errors are this function's.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per value, as for :func:`hangtu.stats.representative` and
        :func:`profile`.
    value : str
        The column, e.g. ``"undrained_shear_strength"``.
    by : str, optional
        The column grouping the values, e.g. ``"geology_unit"``; it also
        colors them, so a line and its values share a color. One column:
        filter the rows or make one column to group by several. None is one
        group, drawn in one color.
    method, side, distribution, trend, estimate : str
        The view, as for ``representative()``.
    coefficient_of_variation, scale_of_fluctuation, failure_length : float, optional
        As for ``representative()``.
    sensitivity_index, percentile, standard_deviations : float, optional
        As for ``representative()``.
    pool : str or list of str, optional
        As for ``representative()``.
    include_assumed : bool
        As for ``representative()``. Assumed values are drawn either way.
    spt_refusal_upper_limit : float, "none" or dict, optional
        As for ``representative()``.
    judgments : Judgments or path, optional
        As for ``representative()``.
    mean : bool
        Draw each unit's mean (median) line.
    band : bool
        Shade between the mean (median) and the representative line, under
        the values.
    table : bool
        Draw the table of the view and each unit's value. It sits below the
        lowest data, deepening the vertical axis if needed, unless ``ylim=``
        is given.
    values : bool
        Draw the values. False draws only the lines, band and table, into
        ``ax=``, a profile drawn before by this function or
        :func:`profile`, in its coordinates: that is how a second view goes
        on the same figure. Its representative lines are dash-dot (a third
        view's dotted), its table rows join the table there, and its legend
        entries and footnote lines join the legend and footnote there.
        :func:`profile`'s drawing arguments aren't taken with it.
    vs : {"depth", "elevation"}, optional
        The vertical axis. A trend is drawn against its own column, the
        default; the other is an error. A constant defaults to the column
        ``result.vertical`` names; the other needs one ground level for all
        rows.
    preset, log, label, marker_by, connect, intervals : optional
        As for :func:`profile`.
    xlim, ylim : (low, high), optional
        As for :func:`profile`. A line beyond them is clipped at the axis
        and counted in the footnote.
    xaxis_position, secondary, strata, water_level, ranges : optional
        As for :func:`profile`.
    reference_lines, note, palette : optional
        As for :func:`profile`.
    units : dict, optional
        ``{column: unit}``, overriding the units declared on ``df``.
    display_units : {"US", "SI"}, optional
        Defaults to ``ht.settings.display_units``. The values, the lines
        and their statistics are in these units.
    legend : {"auto", "inside", "bottom", "right"} or bool
        As for :func:`profile`.
    figsize : (width, height), optional
        Inches; ignored with ``ax=``.
    ax : matplotlib Axes, optional
        Draw into this axes.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, ax, result
        ``result`` is the :class:`~hangtu.stats.RepresentativeResult` the
        lines were drawn from.

    Raises
    ------
    HangtuError
        For ``by=`` with several columns, a ``vs`` other than a trend's
        column, a constant drawn against the other column without one ground
        level, ``values=False`` without a profile's ``ax=`` or with
        ``profile()``'s drawing arguments, and as ``representative()`` and
        ``profile()``.

    Examples
    --------
    >>> fig, ax, result = ht.plot.representative_profile(
    ...     strength, value="undrained_shear_strength", by="geology_unit",
    ...     method="characteristic", estimate="mean", side="low",
    ...     distribution="normal", trend="depth")
    """
    _check_by(by)
    if not values:
        _profile_axes(ax, value)
    system = display_units or settings.display_units
    info = column_info(value) or {}
    result = representative(
        df,
        value=value,
        by=by,
        method=method,
        side=side,
        distribution=distribution,
        trend=trend,
        estimate=estimate,
        coefficient_of_variation=coefficient_of_variation,
        scale_of_fluctuation=scale_of_fluctuation,
        failure_length=failure_length,
        sensitivity_index=sensitivity_index,
        percentile=percentile,
        standard_deviations=standard_deviations,
        pool=pool,
        include_assumed=include_assumed,
        spt_refusal_upper_limit=spt_refusal_upper_limit,
        judgments=judgments,
        units=units,
        # An unregistered column has no kind of quantity to convert.
        display_units=system if "quantity" in info else display_units,
    )
    fig, ax = _draw(
        result,
        df,
        mean=mean,
        band=band,
        table=table,
        values=values,
        vs=vs,
        units=units,
        display_units=display_units,
        ax=ax,
        profile_arguments={
            "preset": preset,
            "log": log,
            "label": label,
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
            "reference_lines": reference_lines,
            "note": note,
            "palette": palette,
            "legend": legend,
            "figsize": figsize,
        },
        style_overrides=style_overrides,
    )
    return fig, ax, result


def draw(
    result: RepresentativeResult,
    df: pd.DataFrame,
    *,
    mean: bool = True,
    band: bool = True,
    table: bool = True,
    values: bool = True,
    vs: Literal["elevation", "depth"] | None = None,
    preset: str | None = None,
    log: bool | None = None,
    label: str | None = None,
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
    reference_lines: list[tuple[float, str]] | None = None,
    note: str | None = None,
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    legend: Literal["auto", "inside", "bottom", "right"] | bool = "auto",
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes]:
    """Draw P09 from an existing result (``RepresentativeResult.plot()``).

    ``df`` must be the rows the result was computed from: they are grouped
    and counted again, and a group that differs is an error.
    """
    if result.value is None:
        raise HangtuError(
            "The result was computed from a list of values, not a column, so "
            "there are no rows to draw. Compute it from a DataFrame with value=."
        )
    if len(result.by) > 1:
        _check_by(list(result.by))
    if display_units is not None and display_units != result.display_units:
        computed = (
            f'display_units="{result.display_units}"'
            if result.display_units
            else "the data's units"
        )
        raise HangtuError(
            f"The result was computed in {computed}, so it is drawn in them, not "
            f'display_units="{display_units}": the table gives the result\'s '
            "numbers. Leave display_units out, or compute the result with "
            f'display_units="{display_units}".'
        )
    if not values:
        _profile_axes(ax, result.value)
    _check_rows(result, df, units)
    shown: Any = result.display_units
    return _draw(
        result,
        df,
        mean=mean,
        band=band,
        table=table,
        values=values,
        vs=vs,
        units=units,
        display_units=shown,
        ax=ax,
        profile_arguments={
            "preset": preset,
            "log": log,
            "label": label,
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
            "reference_lines": reference_lines,
            "note": note,
            "palette": palette,
            "legend": legend,
            "figsize": figsize,
        },
        style_overrides=style_overrides,
    )


#: profile()'s drawing arguments and their defaults; values=False takes none.
_PROFILE_DEFAULTS: dict[str, Any] = {
    "preset": None,
    "log": None,
    "label": None,
    "marker_by": None,
    "connect": False,
    "intervals": "auto",
    "xlim": None,
    "ylim": None,
    "xaxis_position": "bottom",
    "secondary": None,
    "strata": None,
    "water_level": None,
    "ranges": None,
    "reference_lines": None,
    "note": None,
    "palette": None,
    "legend": "auto",
    "figsize": None,
}


@dataclass
class _Views:
    """The P09 views drawn on an axes, kept as ``ax.ags_representative``."""

    count: int = 0
    table: Text | None = None


def _draw(
    result: RepresentativeResult,
    df: pd.DataFrame,
    *,
    mean: bool,
    band: bool,
    table: bool,
    values: bool,
    vs: Literal["elevation", "depth"] | None,
    units: dict[str, str] | None,
    display_units: Literal["US", "SI"] | None,
    ax: Axes | None,
    profile_arguments: dict[str, Any],
    style_overrides: dict[str, Any],
) -> tuple[Figure, Axes]:
    """Draw ``result`` over ``df``'s profile, or into ``ax``'s with ``values=False``."""
    lines = result.design_lines(mean=True)
    vs = _choose_vs(result, vs)
    by = result.by[0] if result.by else None
    if values:
        given = profile_arguments
        fig, ax = _draw_profile(
            df,
            result.value or "",
            vs=vs,
            color_by=by,
            units=units,
            display_units=display_units,
            ax=ax,
            value_ranges=True,
            overlay=_overlay(
                result,
                lines,
                mean=mean,
                band=band,
                table=table,
                note=given["note"],
                xlim=given["xlim"],
                ylim=given["ylim"],
                room=given["ylim"] is None,
            ),
            cover_x=lines["value"].to_numpy(dtype=float),
            **given,
            **style_overrides,
        )
        return fig, ax
    taken = [
        name
        for name, default in _PROFILE_DEFAULTS.items()
        if (
            profile_arguments[name] is not None
            if default is None
            else profile_arguments[name] != default
        )
    ]
    if taken:
        raise HangtuError(
            f"values=False draws a view into the profile already in ax=, so it "
            f"takes none of profile()'s drawing arguments: "
            f"{', '.join(f'{name}=' for name in taken)}. Pass them to the call "
            "that drew the values."
        )
    state = _profile_axes(ax, result.value or "")
    assert ax is not None  # _profile_axes raised without one
    if vs != state.vertical.vs and result.trend is not None:
        raise HangtuError(
            f"The lines are a trend with {result.trend}, and the profile in ax= is "
            f"against {state.vertical.vs}. Draw the profile with "
            f"vs={result.trend!r}, or compute the trend with "
            f"trend={state.vertical.vs!r}."
        )
    with style.context(**style_overrides):
        # The profile set its limits, so a line beyond them is clipped: counted.
        overlay = _overlay(
            result,
            lines,
            mean=mean,
            band=band,
            table=table,
            note=None,
            xlim=ax.get_xlim(),
            ylim=ax.get_ylim(),
            room=state.room,
        )
        kept = state.legend
        handles = overlay(ax, state.vertical, state.scale, state.colors, kept.notes)
        shown = {handle.get_label() for handle in kept.sections[OVERLAY_SECTION]}
        kept.sections[OVERLAY_SECTION] += [
            handle for handle in handles if handle.get_label() not in shown
        ]
        kept.draw(ax)
    return figure_of(ax), ax


def _check_by(by: Any) -> None:
    if by is not None and not isinstance(by, str):
        raise HangtuError(
            f"representative_profile() colors each unit's line and values alike, so "
            f"by= is one column, not {by!r}. Filter the rows to one value of the "
            "others, or make one column that combines them."
        )


def _profile_axes(ax: Axes | None, value: str) -> ProfileAxes:
    """Return the profile drawn in ``ax``, for ``values=False``, else raise."""
    if ax is None:
        raise HangtuError(
            "values=False draws only the lines, band and table, into a profile "
            "already drawn, so it needs ax=: the axes of an earlier "
            "representative_profile() or profile() call."
        )
    state = getattr(ax, "ags_profile", None)
    if not isinstance(state, ProfileAxes):
        raise HangtuError(
            "values=False draws into a profile, and ax= wasn't drawn by "
            "representative_profile() or profile(). Draw the values there first."
        )
    if state.value != value:
        raise HangtuError(
            f"The profile in ax= draws {state.value!r}, not {value!r}: a view goes "
            "on a profile of its own parameter."
        )
    return state


def _check_rows(
    result: RepresentativeResult, df: pd.DataFrame, units: dict[str, str] | None
) -> None:
    """Raise unless ``df`` gives the result's groups with the same counts.

    The rows are grouped and counted again with the result's view. How many
    refusals are interval censored depends on the refusal limit, which
    isn't given again, so that count isn't compared; they are still counted
    as at least their value.
    """
    assert result.value is not None  # draw() raised without one
    intermediate = result.estimate == "intermediate"
    given = intermediate and result.scale_of_fluctuation is None
    with warnings.catch_warnings():
        # The result's own call gave them; the plot doesn't repeat them.
        warnings.simplefilter("ignore")
        again = representative(
            df,
            value=result.value,
            by=list(result.by) or None,
            method=result.method,
            side=result.side,
            distribution=result.distribution,
            trend=result.trend,
            estimate=result.estimate,
            coefficient_of_variation=result.coefficient_of_variation,
            scale_of_fluctuation=result.scale_of_fluctuation if intermediate else None,
            failure_length=result.failure_length if intermediate else None,
            sensitivity_index=result.sensitivity_index if given else None,
            percentile=result.percentile,
            standard_deviations=result.standard_deviations,
            pool=list(result.pooled) or None,
            include_assumed=result.include_assumed,
            units=units,
            display_units=result.display_units,
        )

    def counted(counts: Mapping[str, int]) -> dict[str, int]:
        return {
            name: int(n)
            for name, n in counts.items()
            if name != "count_interval_censored"
        }

    found = {_label(group["key"]): group for group in again.groups}
    for group in result.groups:
        name = _label(group["key"]) or "the values"
        other = found.pop(_label(group["key"]), None)
        if other is None:
            raise HangtuError(
                f"df has no rows for {name}, which the result has. Pass the rows "
                "the result was computed from."
            )
        mine, theirs = counted(group["counts"]), counted(other["counts"])
        differ = [n for n in mine if mine[n] != theirs.get(n, 0)]
        if differ:
            found_counts = ", ".join(
                f"{n} is {theirs.get(n, 0)}, not {mine[n]}" for n in differ
            )
            raise HangtuError(
                f"df's rows for {name} aren't the ones the result was computed "
                f"from: {found_counts}. "
                "Pass the same rows, or compute the result again from these."
            )
    if found:
        raise HangtuError(
            f"df has rows for {', '.join(found)}, which the result doesn't have. "
            "Pass the rows the result was computed from."
        )


def _choose_vs(
    result: RepresentativeResult, vs: Literal["elevation", "depth"] | None
) -> Literal["elevation", "depth"]:
    """Return the vertical axis: a trend's own column, or a constant's default."""
    own = result.trend or result.vertical
    # representative() records "depth" or "elevation"; design_lines() raised
    # without either.
    assert own == "depth" or own == "elevation"
    if result.trend is not None and vs is not None and vs != own:
        raise HangtuError(
            f"The lines are a trend with {own}, so they are drawn against {own}, "
            f"not vs={vs!r}. Leave vs out, or compute the trend with trend={vs!r}."
        )
    return vs or ("depth" if own == "depth" else "elevation")


def _short_name(result: RepresentativeResult) -> str:
    """Name the view in a legend entry: ``characteristic``, ``percentile 10``."""
    if result.method == "characteristic":
        return "characteristic"
    if result.method == "percentile":
        return f"percentile {result.percentile:g}"
    sign = "-" if result.side == "low" else "+"
    of = " of ln x" if result.distribution == "lognormal" else ""
    return f"mean {sign} {result.standard_deviations:g} std{of}"


def _overlay(
    result: RepresentativeResult,
    lines: pd.DataFrame,
    *,
    mean: bool,
    band: bool,
    table: bool,
    note: str | None,
    xlim: tuple[float, float] | None,
    ylim: tuple[float, float] | None,
    room: bool,
) -> Overlay:
    """Return the overlay that draws the lines, band, table and footnote lines.

    The views drawn on an axes are kept as ``ax.ags_representative``: a
    later view's representative line takes the next of ``VIEW_STYLES``, and
    its table rows join the table there. ``room`` lets the table deepen
    the vertical axis to sit below the data.
    """

    def draw(
        ax: Axes,
        vertical: Vertical,
        scale: ValueScale,
        colors: Mapping[Any, Any],
        notes: Notes,
    ) -> list[Artist]:
        views = getattr(ax, "ags_representative", None)
        if not isinstance(views, _Views):
            views = _Views()
            ax.ags_representative = views  # type: ignore[attr-defined]
        linestyle = VIEW_STYLES[views.count % len(VIEW_STYLES)]
        views.count += 1
        handles = _draw_lines(
            ax,
            result,
            lines,
            vertical,
            scale,
            colors,
            notes,
            mean,
            band,
            xlim,
            ylim,
            linestyle,
        )
        if table:
            rows = _table_rows(result, scale, colors)
            if views.table is None:
                views.table = draw_stats_box(ax, rows, note)
            else:
                joined = "\n".join(row[0] for row in rows)
                views.table.set_text(f"{views.table.get_text()}\n\n{joined}")
            lowest = ax.ags_profile.lowest  # type: ignore[attr-defined]
            if room and lowest is not None:
                room_below_data(ax, views.table, lowest)
        for line in _footnote(result, colors):
            if line not in notes.texts:  # a second view's may be the first's
                notes.add_text(line)
        return handles

    return draw


def _draw_lines(
    ax: Axes,
    result: RepresentativeResult,
    lines: pd.DataFrame,
    vertical: Vertical,
    scale: ValueScale,
    colors: Mapping[Any, Any],
    notes: Notes,
    mean: bool,
    band: bool,
    xlim: tuple[float, float] | None,
    ylim: tuple[float, float] | None,
    linestyle: LineStyleType,
) -> list[Artist]:
    """Draw the band, mean and representative line per unit; return legend entries."""
    assert result.vertical is not None  # design_lines() raised without one
    units = lines.attrs.get("units", {})
    positions = vertical.to_display(
        lines[result.vertical].to_numpy(dtype=float), units.get(result.vertical, "")
    )
    if result.vertical != vertical.vs:
        if vertical.ground_level is None:
            raise HangtuError(
                f"The lines are at the {result.vertical} of each unit's values, and "
                f"the plot is against {vertical.vs}, but the rows don't share one "
                f"ground level to convert them. Plot with vs={result.vertical!r}."
            )
        positions = vertical.ground_level - positions
    values = scale.to_display(lines["value"].to_numpy(dtype=float), units.get("value"))
    labels = lines["label"].to_numpy(dtype=object)
    center = "median" if result.distribution == "lognormal" else "mean"
    view = result._line_name()
    drawn = False
    for group in result.groups:
        name = _label(group["key"])
        these = labels == f"{name}: {view}"
        if not these.any():
            continue
        drawn = True
        key = group["key"].get(result.by[0]) if result.by else None
        color = colors.get(key, _values.NEUTRAL)
        y = positions[these]
        x = _cut(values[these], scale.log, notes, xlim, ylim, y)
        middle = _cut(
            values[labels == f"{name}: {center}"], scale.log, notes, xlim, ylim, y
        )
        if band:
            ax.fill_betweenx(
                y,
                x,
                middle,
                where=np.isfinite(x) & np.isfinite(middle),
                color=color,
                alpha=BAND_ALPHA,
                linewidth=0,
                zorder=_layers.REPRESENTATIVE_BAND,
            )
        if mean:
            ax.plot(
                middle,
                y,
                color=color,
                linewidth=MEAN_WIDTH,
                linestyle="--",
                zorder=_layers.REPRESENTATIVE_MEAN,
            )
        ax.plot(
            x,
            y,
            color=color,
            linewidth=REPRESENTATIVE_WIDTH,
            linestyle=linestyle,
            zorder=_layers.REPRESENTATIVE,
        )
    if not drawn:
        return []
    short = _short_name(result)
    handles: list[Artist] = [
        Line2D(
            [],
            [],
            color=STYLE_COLOR,
            linewidth=REPRESENTATIVE_WIDTH,
            linestyle=linestyle,
            label=short,
        )
    ]
    if mean:
        handles.append(
            Line2D(
                [],
                [],
                color=STYLE_COLOR,
                linewidth=MEAN_WIDTH,
                linestyle="--",
                label=center,
            )
        )
    if band:
        handles.append(
            Patch(
                facecolor=STYLE_COLOR,
                alpha=BAND_ALPHA,
                edgecolor="none",
                label=f"{center} to {short}",
            )
        )
    return handles


def _cut(
    x: np.ndarray,
    log: bool,
    notes: Notes,
    xlim: tuple[float, float] | None,
    ylim: tuple[float, float] | None,
    y: np.ndarray,
) -> np.ndarray:
    """Return a line's values with the part ≤ 0 on a log axis blank, counted.

    A line reaching beyond fixed limits is left for matplotlib to clip at
    the axis, and counted.
    """
    if log and (x <= 0).any():
        notes.add("line_log_nonpositive", 1)
        x = np.where(x > 0, x, np.nan)
    shown = np.isfinite(x)
    beyond = False
    if xlim is not None:
        low, high = sorted(xlim)
        beyond |= bool(((x[shown] < low) | (x[shown] > high)).any())
    if ylim is not None:
        low, high = sorted(ylim)
        beyond |= bool(((y[shown] < low) | (y[shown] > high)).any())
    if beyond:
        notes.add("line_beyond_limit", 1)
    return x


def _groups_in_order(
    result: RepresentativeResult, colors: Mapping[Any, Any]
) -> list[dict[str, Any]]:
    """Return the result's groups in the legend's order, then any others."""
    if not result.by:
        return list(result.groups)
    by = result.by[0]
    found = {group["key"][by]: group for group in result.groups}
    order = [found.pop(key) for key in colors if key in found]
    return order + list(found.values())


def _table_rows(
    result: RepresentativeResult, scale: ValueScale, colors: Mapping[Any, Any]
) -> list[list[str]]:
    """Return the table: the view, wrapped, then a line per unit (P09 §8).

    Each line is one cell, aligned here, so ``draw_stats_box`` writes the
    view's lines and the units' columns as given.
    """
    unit = f" {result.unit}" if result.unit else ""
    cells: list[tuple[str, str, str]] = []
    for group in _groups_in_order(result, colors):
        counts = group["counts"]
        n = f"n = {counts['count']}"
        if group["reason"]:
            shown = f"— {group['reason']}"
        elif result.trend is None:
            if counts["count_censored"]:
                n += f" ({counts['count_censored']} censored)"
            shown = format_number(_display(group["value"], scale, result)) + unit
        else:
            top, base = (
                format_number(_display(group["statistics"][end], scale, result))
                for end in ("value_top", "value_base")
            )
            shown = f"{top} → {base}{unit}"
        cells.append((_label(group["key"]), n, shown))
    names = max((len(name) for name, _, _ in cells), default=0)
    counts_width = max((len(n) for _, n, _ in cells), default=0)
    lines = textwrap.wrap(result._view(), TABLE_WRAP)
    lines += [
        f"{name.ljust(names)}  {n.ljust(counts_width)}  {shown}"
        for name, n, shown in cells
    ]
    return [[line] for line in lines]


def _display(value: float, scale: ValueScale, result: RepresentativeResult) -> float:
    """Return a value of the result in the plot's display units."""
    return float(scale.to_display([value], result.unit)[0])


def _footnote(result: RepresentativeResult, colors: Mapping[Any, Any]) -> list[str]:
    """Return the footnote lines on what the lines left out (P09 §8)."""
    groups = _groups_in_order(result, colors)
    lines = []
    if result.trend is not None:
        left_out = []
        for group in groups:
            counts = group["counts"]
            parts = []
            if counts["count_censored"]:
                parts.append(f"{counts['count_censored']} censored")
            blank = counts.get(f"count_blank_{result.trend}", 0)
            if blank:
                parts.append(f"{blank} with no {result.trend}")
            if parts:
                left_out.append(f"{_label(group['key'])} {', '.join(parts)}")
        if left_out:
            lines.append(f"Left out of the lines: {'; '.join(left_out)}.")
    assumed = 0 if result.include_assumed else _total(groups, "count_assumed")
    ranged = _total(groups, "count_range")
    kinds = [
        f"{count} {kind}"
        for count, kind in ((assumed, "assumed"), (ranged, "range"))
        if count
    ]
    if kinds:
        lines.append(f"Not in the lines: {', '.join(kinds)}.")
    no_line = [
        f"{_label(group['key'])} ({group['reason'] or f'no {result.vertical}'})"
        for group in groups
        if group["reason"] or group.get("vertical_range") is None
    ]
    if no_line:
        lines.append(f"No line: {'; '.join(no_line)}.")
    return lines


def _total(groups: list[dict[str, Any]], name: str) -> int:
    return sum(int(group["counts"].get(name, 0)) for group in groups)
