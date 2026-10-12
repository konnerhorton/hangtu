"""P07 property by geology unit (docs/plots/P07-geology-unit-comparison.md)."""

from dataclasses import dataclass, field
from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import NullLocator

from hangtu import units as _units
from hangtu._settings import _display_units, settings
from hangtu.errors import ColumnError, HangtuError
from hangtu.plot import _layers, _presets, _values, style
from hangtu.plot._data import numeric_column
from hangtu.plot._labels import axis_label
from hangtu.plot._legend import add_legend
from hangtu.plot._limits import set_linear_axis, set_log_axis
from hangtu.plot._notes import Notes
from hangtu.plot._palette import resolve_palette
from hangtu.plot._presets import Preset

POINT_SIZE = 3.0  # points
POINT_ALPHA = 0.4
JITTER = 0.15  # row heights either side of the center line (P07 §7)
JITTER_SEED = 0  # the same data always gives the same figure (plan decision 4)


@dataclass
class _Panel:
    """What one panel drew, for the legend and footnote around it."""

    handles: list[Artist] = field(default_factory=list)
    notes: Notes = field(default_factory=Notes)


def _choose_preset(value: str, preset: str | None) -> Preset | None:
    """Return the preset given, else the one named after the value column (P07 §6)."""
    if preset is not None:
        return _presets.preset(preset)
    if value in _presets.preset_names():
        return _presets.preset(value)
    return None


def _check_columns(df: pd.DataFrame, value: str, color_by: str | None) -> None:
    available = ", ".join(map(str, df.columns)) or "none"
    for column in (value, "geology_unit"):
        if column not in df.columns:
            raise ColumnError(
                f"Column {column!r} not found. Available columns: {available}. "
                + (
                    "This plot groups values by geology unit, so it needs a "
                    "'geology_unit' column."
                    if column == "geology_unit"
                    else ""
                )
            )
    if color_by not in ("geology_unit", None):
        raise HangtuError(
            f'color_by must be "geology_unit" or None, not {color_by!r}. Rows are '
            "always geology units; color_by=None draws them in one neutral color."
        )


def _not_built(**arguments: Any) -> None:
    """Refuse arguments whose behavior isn't built yet, instead of ignoring them."""
    given = [name for name, used in arguments.items() if used]
    if given:
        raise NotImplementedError(f"{', '.join(given)} isn't built yet (P07 plan).")


def _rows(
    df: pd.DataFrame, order: list[str] | None, palette: dict[str, str] | None
) -> tuple[np.ndarray, dict[Any, Any]]:
    """Return each row's geology unit, and ``{unit: color}`` in row order.

    Units in ``order`` come first, then the rest by name, then "(blank)".
    """
    groups = df["geology_unit"].to_numpy(dtype=object)
    blank = pd.isna(groups)
    colors = resolve_palette(groups[~blank], palette, order)
    if blank.any():
        groups = np.where(blank, _values.BLANK_GROUP, groups)
        colors[_values.BLANK_GROUP] = _values.NEUTRAL
    return groups, colors


def _set_unit_axis(ax: Axes, names: list[Any]) -> None:
    """One row per unit, first at the top, with no gridlines between them."""
    n = max(len(names), 1)
    ax.set_yticks(range(len(names)), [str(name) for name in names])
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_ylim(n - 0.5, -0.5)
    ax.grid(False, axis="y", which="both")


def _draw_panel(
    ax: Axes,
    df: pd.DataFrame,
    value: str,
    *,
    preset: str | None,
    log: bool | None,
    label: str | None,
    xlim: tuple[float, float] | None,
    order: list[str] | None,
    color_by: str | None,
    points: bool,
    palette: dict[str, str] | None,
    units: dict[str, str] | None,
    system: str,
) -> _Panel:
    """Draw one property by geology unit into ``ax``."""
    panel = _Panel()
    chosen = _choose_preset(value, preset)
    quantity = _values.quantity_of(value, chosen)
    log = chosen.log if log is None and chosen is not None else bool(log)
    xlim = _values.check_limits("xlim", xlim, log) if xlim is not None else None

    resolved = _units.resolve_units(
        df, [value], units, quantities={value: quantity} if quantity else None
    )
    x, x_unit_text = _units.to_display(
        numeric_column(df, value), resolved[value], quantity, system
    )
    # Blank values are tests not done, so they are skipped, not counted (P07 §14).
    drawn = ~np.isnan(x)
    if log:
        nonpositive = drawn & (x <= 0)
        panel.notes.count(nonpositive, "log_nonpositive")
        drawn &= ~nonpositive
    groups, colors = _rows(df[drawn], order, palette)
    rows = list(colors)
    unit_of = np.full(len(df), None, dtype=object)
    unit_of[drawn] = groups
    row_of = {unit: i for i, unit in enumerate(rows)}
    jitter = np.random.default_rng(JITTER_SEED).uniform(-JITTER, JITTER, len(df))

    style.style_axes(ax)
    limits = _values.value_limits(
        x[drawn],
        log=log,
        xlim=xlim,
        start_at_zero=_values.start_at_zero(value, chosen),
        typical=_values.typical_range(chosen, resolved[value], system),
    )
    if log:
        set_log_axis(ax, "x", limits)
    else:
        set_linear_axis(ax, "x", limits)
    _set_unit_axis(ax, rows)

    for unit, color in colors.items():
        these = drawn & (unit_of == unit)
        if points and these.any():
            ax.scatter(
                x[these],
                row_of[unit] + jitter[these],
                s=POINT_SIZE**2,
                color=_values.NEUTRAL if color_by is None else color,
                alpha=POINT_ALPHA,
                linewidths=0,
                label=f"_{unit}",
                zorder=_layers.MARKERS,
            )
    if points and drawn.any():
        panel.handles.append(
            _values.legend_marker("o", _values.NEUTRAL, "Data", POINT_SIZE)
        )

    if not rows:
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
    ax.set_xlabel(
        axis_label(
            _values.axis_text(value, label, chosen),
            x_unit_text,
            unknown=resolved[value] is None and _units.needs_units(value, quantity),
        )
    )
    return panel


def _new_axes(figsize: tuple[float, float] | None) -> tuple[Figure, Axes]:
    return plt.subplots(
        figsize=figsize or settings.figure_sizes["default"], layout="constrained"
    )


def geology_unit_comparison(
    df: pd.DataFrame,
    value: str,
    *,
    baseline: pd.DataFrame | str | None = None,
    baseline_label: str | None = None,
    baseline_units: dict[str, str] | None = None,
    summary: Literal["percentiles", "box"] | None = "percentiles",
    percentiles: tuple[float, float, float] = (10, 50, 90),
    percentile_method: str = "linear",
    summary_min_count: int | None = None,
    points: bool = True,
    preset: str | None = None,
    log: bool | None = None,
    label: str | None = None,
    xlim: tuple[float, float] | None = None,
    order: list[str] | None = None,
    color_by: Literal["geology_unit"] | None = "geology_unit",
    reference_lines: list[tuple[float, str]] | None = None,
    note: str | None = None,
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes]:
    """Compare a property's values by geology unit with a report's ranges (P07).

    Each geology unit is a row: its values as jittered points, a summary bar,
    and the report's baseline range above it. Nothing is dropped silently:
    values ≤ 0 on a log axis, values beyond fixed limits and flagged values
    are counted in a footnote, and the counts are in ``ax.ags_notes``.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per observation, with the ``value`` column and
        ``geology_unit``.
    value : str
        The column to compare.
    points : bool
        Draw every value as a point.
    preset : str, optional
        By default the preset named after ``value``, if there is one.
    log : bool, optional
        Use a log value axis. By default from the preset, else linear.
    label : str, optional
        The value axis text; units are added automatically.
    xlim : (low, high), optional
        Fixed value axis limits in display units.
    order : list of str, optional
        Geology units in stratigraphic order, top first. Other units follow,
        sorted by name.
    color_by : {"geology_unit", None}
        None draws every unit in one neutral color.
    palette : dict, optional
        ``{geology unit: color}`` for this plot.
    units : dict, optional
        ``{column: unit}``, overriding the units declared on ``df``.
    display_units : {"US", "SI"}, optional
        Defaults to ``ht.settings.display_units``.
    figsize : (width, height), optional
        Inches; by default the settings ``default`` size. Ignored with ``ax=``.
    ax : matplotlib Axes, optional
        Draw into this axes, e.g. a ``Sheet`` panel.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, ax

    Examples
    --------
    >>> index = ht.read_csv("index.csv", units={"bulk_unit_weight": "pcf"})
    >>> fig, ax = ht.plot.geology_unit_comparison(
    ...     index, "bulk_unit_weight", order=["Fill", "Alluvium", "Till"])
    """
    _check_columns(df, value, color_by)
    _not_built(
        baseline=baseline is not None,
        baseline_label=baseline_label is not None,
        baseline_units=baseline_units is not None,
        summary=summary is not None,
        percentiles=tuple(percentiles) != (10, 50, 90),
        percentile_method=percentile_method != "linear",
        summary_min_count=summary_min_count is not None,
        xlim=xlim is not None,
        reference_lines=reference_lines is not None,
        note=note is not None,
        qualifier="qualifier" in df.columns,
        non_plastic="non_plastic" in df.columns,
    )
    system = _display_units(display_units or settings.display_units)

    with style.context(**style_overrides):
        if ax is None:
            fig, ax = _new_axes(figsize)
        else:
            fig = ax.figure
        panel = _draw_panel(
            ax,
            df,
            value,
            preset=preset,
            log=log,
            label=label,
            xlim=xlim,
            order=order,
            color_by=color_by,
            points=points,
            palette=palette,
            units=units,
            system=system,
        )
        add_legend(ax, [panel.handles], panel.notes)
        panel.notes.render(ax)
    return fig, ax
