"""P01 property profile (docs/plots/P01-property-profile.md)."""

from collections.abc import Mapping
from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ags_kit import units as _units
from ags_kit._settings import _display_units, settings
from ags_kit.errors import AgsKitError, ColumnError
from ags_kit.plot import _layers, _presets, style
from ags_kit.plot._data import numeric_column
from ags_kit.plot._hints import hint_missing
from ags_kit.plot._labels import axis_label
from ags_kit.plot._legend import add_legend
from ags_kit.plot._limits import apply_vertical_axis, nice_limits, set_linear_axis
from ags_kit.plot._notes import Notes
from ags_kit.plot._palette import resolve_palette
from ags_kit.plot._presets import Preset
from ags_kit.plot._vertical import choose_vs, length_columns, vertical_values
from ags_kit.registry import column_info

LEGEND_WIDTH = 1.5  # inches added to the settings size for the outside legend
NEUTRAL = "0.3"  # points not colored by a group
MARKER_SIZE = 5.0  # points
BLANK_GROUP = "(blank)"


def _not_yet(argument: str) -> NotImplementedError:
    return NotImplementedError(f"profile({argument}) isn't available yet.")


def _check_not_yet_built(df: pd.DataFrame, arguments: Mapping[str, Any]) -> None:
    for name, value in arguments.items():
        if value is not None and value is not False:
            raise _not_yet(f"{name}=...")
    if "qualifier" in df.columns and df["qualifier"].fillna("").astype(str).any():
        raise _not_yet("data with a 'qualifier' column")


def _quantity(value: str, preset: Preset | None) -> str | None:
    info = column_info(value)
    registered = info.get("quantity") if info else None
    if preset is None:
        return registered
    if registered is not None and registered != preset.quantity:
        raise AgsKitError(
            f"preset={preset.name!r} is for a {preset.quantity.replace('_', ' ')}, "
            f"but column {value!r} is a {registered.replace('_', ' ')}. "
            f"Use preset={value!r} if it exists, or leave preset out."
        )
    return preset.quantity


def _x_text(value: str, label: str | None, preset: Preset | None) -> str:
    if label is not None:
        return label
    if preset is not None:
        return preset.label
    info = column_info(value)
    return info["label"] if info and "label" in info else value


def _start_at_zero(value: str, preset: Preset | None) -> bool:
    if preset is not None:
        return preset.start_at_zero
    info = column_info(value)
    return bool(info) and info.get("scale") == "ratio"


def _typical(
    preset: Preset | None, x_unit: str | None, system: str
) -> tuple[float, float] | None:
    """Return the preset's typical range in display units, if it can be converted."""
    if preset is None:
        return None
    kind = _units.quantity_kind(preset.quantity)
    if kind["canonical"] is not None and x_unit is None:
        return None
    low, high = _units.to_display(
        preset.typical, kind["canonical"], preset.quantity, system
    )[0]
    return float(low), float(high)


def _x_limits(
    x: np.ndarray, *, start_at_zero: bool, typical: tuple[float, float] | None
) -> tuple[float, float]:
    if not x.size:
        if typical is not None:
            return nice_limits(*typical, start_at_zero=start_at_zero)
        return (0.0, 1.0)
    vmin, vmax = float(x.min()), float(x.max())
    if vmin == vmax and typical is not None:
        # A single value: the typical range, widened to include it (P01 §11).
        vmin, vmax = min(typical[0], vmin), max(typical[1], vmax)
    return nice_limits(vmin, vmax, start_at_zero=start_at_zero)


def _set_vertical_axis(
    ax: Axes, vs: Literal["depth", "elevation"], y: np.ndarray
) -> None:
    if y.size:
        apply_vertical_axis(ax, vs, float(y.min()), float(y.max()))
    else:
        apply_vertical_axis(ax, vs, 0.0, 1.0)


def _color_groups(
    df: pd.DataFrame, color_by: str | None, palette: Mapping[Any, Any] | None
) -> tuple[np.ndarray, dict[Any, Any]]:
    """Return each row's group, and ``{group: color}`` in legend order.

    Rows with a blank group are grouped as ``BLANK_GROUP`` in a neutral color.
    """
    if color_by is None or color_by not in df.columns:
        return np.full(len(df), None, dtype=object), {None: NEUTRAL}
    groups = df[color_by].to_numpy(dtype=object)
    blank = pd.isna(groups)
    colors = resolve_palette(groups[~blank], palette)
    groups = np.where(blank, BLANK_GROUP, groups)
    if blank.any():
        colors[BLANK_GROUP] = NEUTRAL
    return groups, colors


def _new_axes(figsize: tuple[float, float] | None) -> tuple[Figure, Axes]:
    if figsize is None:
        width, height = settings.figure_sizes["profile"]
        figsize = (width + LEGEND_WIDTH, height)
    return plt.subplots(figsize=figsize, layout="constrained")


def profile(
    df: pd.DataFrame,
    value: str,
    *,
    vs: Literal["elevation", "depth"] | None = None,
    preset: str | None = None,
    log: bool | None = None,
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
    note: str | None = None,
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes]:
    """Plot a property against depth or elevation (P01).

    Points are colored by geology unit. Nothing is dropped silently: blanks,
    values ≤ 0 on a log axis and values beyond fixed limits are counted in a
    footnote, and the counts are in ``ax.ags_notes``.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per observation: the ``value`` column, plus ``depth`` or
        ``elevation`` (or ``depth`` and ``ground_level``). See
        ``ak.template("profile")``.
    value : str
        The column to plot.
    vs : {"elevation", "depth"}, optional
        The vertical axis. By default elevation when it is available (an
        ``elevation`` column, or ``depth`` plus ``ground_level``), else depth.
    preset : str, optional
        ``"hydraulic_conductivity"``, ``"undrained_shear_strength"``,
        ``"water_content"`` or ``"bulk_unit_weight"``: the label, units, log or
        linear scale and default limits for that property.
    log : bool, optional
        Use a log x-axis. By default from the preset, else linear.
    label : str, optional
        The x-axis text; units are added automatically.
    color_by : str or None
        Column that colors the points; None for one neutral color.
    xlim, ylim : (low, high), optional
        Fixed limits in display units. Values beyond them are drawn at the
        edge with an arrow, and counted.
    xaxis_position : {"bottom", "top"}
        ``"top"`` puts the value axis at the top, as on a borehole log.
    palette : dict, optional
        ``{geology unit: color}`` for this plot.
    units : dict, optional
        ``{column: unit}``, overriding the units declared on ``df``.
    display_units : {"US", "SI"}, optional
        Defaults to ``ak.settings.display_units``.
    figsize : (width, height), optional
        Inches; by default the settings ``profile`` size plus room for the
        legend. Ignored with ``ax=``.
    ax : matplotlib Axes, optional
        Draw into this axes, e.g. a ``Sheet`` panel.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, ax

    Examples
    --------
    >>> k = ak.read_csv("perm.csv", units={"depth": "ft", "ground_level": "ft",
    ...                                    "hydraulic_conductivity": "cm/s"})
    >>> fig, ax = ak.plot.profile(k, "hydraulic_conductivity",
    ...                           preset="hydraulic_conductivity")
    """
    if value not in df.columns:
        raise ColumnError(
            f"Column {value!r} not found. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}."
        )
    if color_by is not None and color_by != "geology_unit" and color_by not in df:
        raise ColumnError(
            f"color_by={color_by!r} isn't a column. Available columns: "
            f"{', '.join(map(str, df.columns))}."
        )
    if xaxis_position not in ("top", "bottom"):
        raise AgsKitError(
            f'xaxis_position must be "top" or "bottom", not {xaxis_position!r}.'
        )
    _check_not_yet_built(
        df,
        {
            "marker_by": marker_by,
            "connect": connect or None,
            "secondary": secondary,
            "xlim": xlim,
            "ylim": ylim,
            "strata": strata,
            "water_level": water_level,
            "ranges": ranges,
            "design_lines": design_lines,
            "reference_lines": reference_lines,
            "stats_box": stats_box or None,
            "note": note,
        },
    )
    if intervals is True or (
        intervals == "auto" and {"depth_top", "depth_base"} <= set(df.columns)
    ):
        raise _not_yet("intervals=...")

    system = _display_units(display_units or settings.display_units)
    chosen = _presets.preset(preset) if preset is not None else None
    quantity = _quantity(value, chosen)
    log = chosen.log if log is None and chosen is not None else bool(log)
    if log:
        raise _not_yet("log=True, or a log preset")
    vs = choose_vs(df, vs)

    with style.context(**style_overrides):
        optional = {
            "loca_id": "connect= and per-hole water levels are unavailable",
        }
        if color_by == "geology_unit":
            optional = {"geology_unit": "points are not colored by geology", **optional}
        if vs == "depth":
            optional["ground_level"] = "elevations can't be computed"
        hint_missing(df, optional)

        resolved = _units.resolve_units(
            df,
            [value, *length_columns(df)],
            units,
            quantities={value: quantity} if quantity else None,
        )
        raw = numeric_column(df, value)
        x, x_unit_text = _units.to_display(raw, resolved[value], quantity, system)
        y, vertical = vertical_values(df, vs, resolved, system)

        notes = Notes()
        blank = np.isnan(x) | np.isnan(y)
        notes.count(blank, "nan")
        drawn = ~blank

        if ax is None:
            fig, ax = _new_axes(figsize)
        else:
            fig = ax.figure
        style.style_axes(ax)

        limits = _x_limits(
            x[drawn],
            start_at_zero=_start_at_zero(value, chosen),
            typical=_typical(chosen, resolved[value], system),
        )
        set_linear_axis(ax, "x", limits)
        _set_vertical_axis(ax, vs, y[drawn])
        if xaxis_position == "top":
            ax.xaxis.tick_top()
            ax.xaxis.set_label_position("top")

        groups, colors = _color_groups(df, color_by, palette)
        handles = []
        for group, color in colors.items():
            rows = drawn & (groups == group) if group is not None else drawn
            handle = ax.scatter(
                x[rows],
                y[rows],
                s=MARKER_SIZE**2,
                color=color,
                edgecolors="white",
                linewidths=0.4,
                label=str(group),
                zorder=_layers.MARKERS,
            )
            if group is not None and rows.any():
                handles.append(handle)

        if not drawn.any():
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
                _x_text(value, label, chosen),
                x_unit_text,
                unknown=resolved[value] is None and _units.needs_units(value, quantity),
            )
        )
        ax.set_ylabel(vertical.label())
        add_legend(ax, [handles], notes)
        notes.render(ax)
    return fig, ax
