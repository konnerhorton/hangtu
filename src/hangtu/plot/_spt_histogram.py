"""P03 SPT class histogram (docs/plots/P03-spt-histogram.md)."""

from collections.abc import Mapping
from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FixedLocator, NullLocator

from hangtu import analysis
from hangtu._settings import _display_units, settings
from hangtu.analysis._spt import REFUSAL_CLASS, class_table
from hangtu.errors import ColumnError, HangtuError
from hangtu.plot import _layers, _values, style
from hangtu.plot._hints import hint_missing
from hangtu.plot._legend import add_legend
from hangtu.plot._limits import nice_limits, set_linear_axis
from hangtu.plot._notes import Notes
from hangtu.plot._spt_profile import _check_choice
from hangtu.registry import column_info

N_COLUMNS = ("spt_n", "spt_n60")
REFUSAL_OPTIONS = ("separate", "exclude")
GROUP_WIDTH = 0.8  # of a class slot, split evenly between the units (P03 §7)
REFUSAL_HATCH = "////"
REFUSAL_FILL_ALPHA = 0.25  # the refusal bar's fill, so the hatch shows
BAR_LABEL_SIZE = 7
BAR_LABEL_GAP = 1.5  # points above the bar
BAR_LABEL_ROOM = 1.1  # the y limit clears the tallest bar's label


def _range_text(lowers: np.ndarray, i: int) -> str:
    """Return class ``i``'s range from the lower bounds, e.g. "< 4" or "≥ 50"."""
    if i == 0:
        return f"< {lowers[1]:g}"
    if i == len(lowers) - 1:
        return f"≥ {lowers[i]:g}"
    return f"{lowers[i]:g}\N{EN DASH}{lowers[i + 1]:g}"


def _hatch(bar: Rectangle, color: Any, outlined: bool) -> None:
    """Hatch a refusal bar in its unit color, over a light fill of that color."""
    bar.set_facecolor((*bar.get_facecolor()[:3], REFUSAL_FILL_ALPHA))
    bar.set_edgecolor(color)  # the hatch follows an explicit edge color
    bar.set_linewidth(0.8 if outlined else 0.0)
    bar.set_hatch(REFUSAL_HATCH)


def _label_bars(ax: Axes, bars: list[Rectangle], counts: np.ndarray) -> None:
    """Write each non-zero bar's count just above it."""
    for bar, count in zip(bars, counts, strict=True):
        if count:
            ax.annotate(
                str(int(count)),
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, BAR_LABEL_GAP),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=BAR_LABEL_SIZE,
                zorder=_layers.ANNOTATIONS,
            )


def _set_class_axis(ax: Axes, slots: list[str], title: str) -> None:
    ax.set_xlim(-0.5, len(slots) - 0.5)
    ax.xaxis.set_major_locator(FixedLocator(range(len(slots))))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticklabels(slots)
    ax.tick_params(axis="x", which="major", length=0)
    ax.xaxis.grid(False)
    ax.set_xlabel(title)


def _set_percent_axis(ax: Axes, tallest: float) -> None:
    hi = nice_limits(0.0, tallest, start_at_zero=True)[1] if tallest > 0 else 100.0
    set_linear_axis(ax, "y", (0.0, min(hi, 100.0)))
    ax.yaxis.grid(True, which="major")
    ax.set_ylabel("Tests in unit (%)")


def spt_histogram(
    df: pd.DataFrame,
    *,
    n: Literal["spt_n", "spt_n60"] = "spt_n",
    table: Literal["cohesionless", "cohesive"] = "cohesionless",
    refusal: Literal["separate", "exclude"] = "separate",
    color_by: str | None = "geology_unit",
    order: list[str] | None = None,
    hammer_efficiency: float | Mapping[str, float] | None = None,
    bar_labels: bool = False,
    note: str | None = None,
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes]:
    """Plot the share of SPT tests in each density or consistency class (P03).

    Each geology unit gets one bar per class: the percent of its classified
    tests in that class. Classes come from ``ht.analysis.spt_class()``, so a
    class runs from its lower bound up to, not including, the next one, and a
    refusal is "Refusal" whatever its N.

    Which table applies is your call: pick ``table`` and pass the rows it
    applies to. For both, draw two histograms on a ``Sheet``.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test, as ``ht.template("spt")``. Only ``spt_n`` is
        required.
    n : {"spt_n", "spt_n60"}
        The value classified. Tests without N60 are left out and counted.
    table : {"cohesionless", "cohesive"}
        Relative density (very loose to very dense) or consistency (very soft
        to hard), from ``config/spt_classes.yaml``.
    refusal : {"separate", "exclude"}
        ``"separate"`` gives refusals their own hatched class, last;
        ``"exclude"`` leaves them out and counts them.
    color_by : str or None
        The column bars are grouped and colored by; None for one group.
    order : list of str, optional
        Geology units in stratigraphic order. Units not in it follow, by name.
    hammer_efficiency : float or dict, optional
        Energy ratio in percent for tests without ``energy_ratio``, for N60:
        one number, or ``{loca_id: ER}`` by hole. Defaults to
        ``ht.settings.hammer_efficiency``. A warning names the tests it's used
        for, as ``ht.analysis.spt()``.
    bar_labels : bool
        Write the number of tests above each bar that has any.
    note : str, optional
        Free text, added to the footnote.
    palette : dict, optional
        ``{unit: color}``, overriding the session's colors.
    units : dict, optional
        ``{column: unit}``. ``spt_penetration`` needs units only when refusals
        are found from it.
    display_units : {"US", "SI"}, optional
        Accepted for the plot contract. Nothing converts, so it changes
        nothing.
    figsize : tuple, optional
        Figure size in inches. Defaults to ``ht.settings.figure_sizes["default"]``.
    ax : matplotlib.axes.Axes, optional
        Draw into this axes, e.g. a ``Sheet`` panel.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, ax

    Examples
    --------
    >>> sand = spt[spt["geology_unit"].isin(["Fill", "Alluvial sand"])]
    >>> fig, ax = ht.plot.spt_histogram(sand, order=["Fill", "Alluvial sand"])
    >>> fig, ax = ht.plot.spt_histogram(clay, table="cohesive")
    """
    _check_choice("n", n, N_COLUMNS)
    _check_choice("refusal", refusal, REFUSAL_OPTIONS)
    names, lowers = class_table(table)
    _display_units(display_units or settings.display_units)
    if color_by is not None and color_by != "geology_unit" and color_by not in df:
        raise ColumnError(
            f"color_by={color_by!r} isn't a column. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}. Or use color_by=None."
        )

    with style.context(**style_overrides):
        optional = {}
        if color_by == "geology_unit":
            optional["geology_unit"] = "all tests are drawn as one group"
        extra = {}
        if not {"spt_refusal", "spt_penetration"} & set(df.columns):
            extra["spt_refusal"] = (
                "refusals can't be found. Add it, or 'spt_penetration' with its units"
            )
        hint_missing(df, optional, extra)

        data = analysis.spt(df, hammer_efficiency=hammer_efficiency, units=units)
        values = data[n].to_numpy(dtype=float)
        refused = data["spt_refusal"].to_numpy(dtype=bool)
        notes = Notes()
        if n == "spt_n60":
            reported = data["spt_n"].to_numpy(dtype=float)
            if np.isfinite(reported).any() and not np.isfinite(values).any():
                raise HangtuError(
                    "No test has N60, because no energy ratio is known. Set "
                    "ht.settings.hammer_efficiency = 80, pass hammer_efficiency=80, "
                    "or fill in 'energy_ratio'. Or classify N with n=\"spt_n\"."
                )
            no_ratio = np.isnan(values) & np.isfinite(reported) & ~refused
            notes.count(no_ratio, "no_energy_ratio")
            notes.count(np.isnan(values) & ~no_ratio & ~refused, "nan")
        else:
            notes.count(np.isnan(values) & ~refused, "nan")

        codes = analysis.spt_class(data, n=n, table=table).cat.codes.to_numpy()
        # One word per line, then the range, so the labels fit narrow panels.
        slots = [
            "\n".join([*name.split(), _range_text(lowers, i)])
            for i, name in enumerate(names)
        ]
        separate = refusal == "separate"
        if separate:
            slots.append(REFUSAL_CLASS)
        else:
            notes.count(refused, "refusal_excluded")
            codes = np.where(refused, -1, codes)
        groups, colors = _values.color_groups(data, color_by, palette, order)

        counts = {}
        for unit in colors:
            these = codes[groups == unit] if unit is not None else codes
            these = these[these >= 0]
            counts[unit] = np.bincount(these, minlength=len(slots))
        drawn = {unit: c for unit, c in counts.items() if c.sum() > 0}
        listed = [] if color_by is None or color_by not in data else (order or [])
        missing = [u for u in listed if u not in counts]
        missing += [u for u in counts if u not in drawn]
        if missing:
            notes.add_text(f"No classified tests: {', '.join(map(str, missing))}")
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

        handles = []
        tallest = 0.0
        width = GROUP_WIDTH / max(len(drawn), 1)
        for j, (unit, unit_counts) in enumerate(drawn.items()):
            total = int(unit_counts.sum())
            percent = unit_counts / total * 100
            tallest = max(tallest, float(percent.max()))
            x = np.arange(len(slots)) - GROUP_WIDTH / 2 + (j + 0.5) * width
            color = colors[unit]
            bars = ax.bar(
                x,
                percent,
                width=width,
                color=color,
                linewidth=0,
                label=str(unit),
                zorder=_layers.MARKERS,
            )
            if separate:
                _hatch(bars.patches[-1], color, bool(unit_counts[-1]))
            if bar_labels:
                _label_bars(ax, bars.patches, unit_counts)
            text = "All tests" if unit is None else str(unit)
            handles.append(
                Patch(facecolor=color, edgecolor="none", label=f"{text} (n = {total})")
            )

        if separate and refused.any() and drawn:
            handles.append(
                Patch(
                    facecolor="white",
                    edgecolor=_values.NEUTRAL,
                    linewidth=0.8,
                    hatch=REFUSAL_HATCH,
                    label="refusal",
                )
            )
        _set_class_axis(ax, slots, f"{column_info(n)['label']} class ({table})")
        _set_percent_axis(ax, tallest * BAR_LABEL_ROOM if bar_labels else tallest)
        if not drawn:
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
        add_legend(ax, [handles], notes)
        notes.render(ax)
    return fig, ax
