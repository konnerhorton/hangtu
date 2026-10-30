"""P08 distribution fit (docs/plots/P08-distribution-fit.md)."""

from collections.abc import Sequence
from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from hangtu._settings import figure_size, settings
from hangtu.errors import HangtuError
from hangtu.plot import _layers, style
from hangtu.plot._labels import axis_label
from hangtu.plot._legend import add_legend
from hangtu.plot._limits import log_limits, nice_limits, set_linear_axis, set_log_axis
from hangtu.plot._notes import Notes, below_x_label
from hangtu.plot._overlays import (
    TEXT_SIZE,
    ValueScale,
    draw_reference_lines,
    format_number,
)
from hangtu.registry import column_info
from hangtu.stats import _fit, _rows
from hangtu.stats._result import FitResult

#: One color per distribution, the same in every figure (Okabe & Ito).
COLORS = {
    "normal": "#0072B2",
    "lognormal": "#D55E00",
    "gamma": "#009E73",
    "weibull": "#CC79A7",
    "beta": "#E69F00",
}
HISTOGRAM_FILL = "0.85"
HISTOGRAM_EDGE = "0.55"
CENSORED_COLOR = "0.25"
BEST_WIDTH = 1.8  # points, the rank-1 fit
OTHER_WIDTH = 1.0
CURVE_POINTS = 400
#: The y axis clears the tallest bar and the rank-1 curve by this factor,
#: leaving the top corners for the legend; other curves may run off the top.
HEADROOM = 1.4
QQ_MARKER_SIZE = 4.0
PANEL_RATIO = (3, 2)
TOO_FEW = "too few values to fit (n = {n}; 4 needed)"


def distribution_fit(
    df: pd.DataFrame,
    *,
    value: str,
    by: str | list[str] | None = None,
    group: Any = None,
    distributions: list[str] | None = None,
    bounds: tuple[float | None, float | None] | Literal["auto"] = "auto",
    pool: str | list[str] | None = None,
    include_assumed: bool = False,
    qq: str | None = None,
    bins: int | str = "auto",
    log: bool = False,
    table: bool = True,
    reference_lines: list[tuple[float | str, str]] | None = None,
    note: str | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    **style_overrides: Any,
) -> tuple[Figure, np.ndarray, FitResult]:
    """Plot the distributions fitted to one property's values in one group (P08).

    Fits with :func:`hangtu.stats.fit` and draws its result for one group:
    on the left, a histogram of the values with each fitted probability
    density; on the right, a Q-Q plot of the values against one fit's
    quantiles. A good fit puts the Q-Q points on the 1:1 line; the tails
    are where fits differ. Use it to check the AICc ranking by eye before
    a distribution is used.

    The histogram's bars are scaled so their area is the share of values
    not censored, so they and the densities (each of area 1) are on one
    scale. Censored values (refusals, ``>x``, ``<x``) are open triangles at
    their limit, pointing the way the true value lies. The fit table (rank,
    ΔAICc, Anderson-Darling p) sits under the Q-Q panel.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per value, as for :func:`hangtu.stats.fit`.
    value : str
        The column fitted, e.g. ``"spt_n60"``.
    by : str or list of str, optional
        The columns grouping the rows, e.g. ``"geology_unit"``.
    group : str or tuple, optional
        The group drawn: its value of ``by``, or a tuple for several
        columns. Needed when ``by`` gives more than one group.
    distributions : list of str, optional
        The distributions fitted and drawn, as for ``fit()``.
    bounds : "auto" or (low, high)
        As for ``fit()``.
    pool : str or list of str, optional
        As for ``fit()``.
    include_assumed : bool
        As for ``fit()``.
    qq : str, optional
        The distribution on the Q-Q panel. Defaults to the rank-1 fit.
    bins : int or str
        Histogram bins, as ``numpy.histogram_bin_edges``: ``"auto"`` (the
        larger of Sturges's and Freedman-Diaconis's counts) or a number.
    log : bool
        Log axes, with log-spaced bins. An axis setting only: ``fit()``
        fits lognormal for values on a log scale.
    table : bool
        Draw the fit table.
    reference_lines : list of (value, label), optional
        Vertical lines on the histogram, e.g. ``[(30, "design")]``. A number
        is in the plot's units; a string such as ``"2000 psf"`` carries its
        own unit.
    note : str, optional
        Free text, added to the footnote.
    units : dict, optional
        ``{column: unit}``, as for ``fit()``.
    display_units : {"US", "SI"}, optional
        Defaults to ``ht.settings.display_units``. The fit is made in these
        units, so the axes and the table are in them.
    figsize : tuple, optional
        Figure size in inches. Defaults to ``ht.settings.figure_sizes["default"]``.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, axs, result
        ``axs`` is the histogram and the Q-Q axes; ``result`` the
        ``FitResult``, for its table (``result.to_frame()``).

    Raises
    ------
    HangtuError
        For a missing or unknown ``group`` with ``by``, and as ``fit()``.

    Examples
    --------
    >>> fig, axs, result = ht.plot.distribution_fit(
    ...     p.spt(), value="spt_n60", by="geology_unit", group="Alluvium"
    ... )
    """
    system = display_units or settings.display_units
    info = column_info(value) or {}
    if by is not None:
        df = df[_chosen(df, value, by, group)]
    result = _fit.fit(
        df,
        value=value,
        by=by,
        distributions=distributions,
        bounds=bounds,
        pool=pool,
        include_assumed=include_assumed,
        units=units,
        # An unregistered column has no kind of quantity to convert.
        display_units=system if "quantity" in info else display_units,
    )
    fig, axs = draw(
        result,
        group=group,
        qq=qq,
        bins=bins,
        log=log,
        table=table,
        reference_lines=reference_lines,
        note=note,
        figsize=figsize,
        **style_overrides,
    )
    return fig, axs, result


def _chosen(df: pd.DataFrame, value: str, by: Any, group: Any) -> np.ndarray:
    """Return the rows of the group drawn, or raise listing the groups."""
    columns = [by] if isinstance(by, str) else list(by)
    missing = [column for column in columns if column not in df.columns]
    if missing or value not in df.columns:
        return np.ones(len(df), bool)  # fit() names what is missing
    keys = _rows.group_keys(df, columns)
    labels = ", ".join(repr(_key(key)) for key, _ in keys)
    if group is None:
        if len(keys) == 1:
            return keys[0][1]
        raise HangtuError(
            f"distribution_fit() draws one group, and by={by!r} gives "
            f"{len(keys)}. Name one with group=, from: {labels}."
        )
    wanted = tuple(map(str, group if isinstance(group, tuple) else (group,)))
    for key, rows in keys:
        if tuple(map(str, key.values())) == wanted:
            return rows
    raise HangtuError(
        f"distribution_fit() found no group {group!r} in by={by!r}. Groups: {labels}."
    )


def _key(key: dict[str, Any]) -> Any:
    values = tuple(key.values())
    return values[0] if len(values) == 1 else values


def draw(
    result: FitResult,
    *,
    group: Any = None,
    distributions: Sequence[str] | None = None,
    qq: str | None = None,
    bins: int | str = "auto",
    log: bool = False,
    table: bool = True,
    reference_lines: list[tuple[float | str, str]] | None = None,
    note: str | None = None,
    figsize: tuple[float, float] | None = None,
    **style_overrides: Any,
) -> tuple[Figure, np.ndarray]:
    """Draw P08 for one group of ``result`` (``FitResult.plot()``)."""
    record = result._group(group)
    fits = [
        fit
        for fit in record["fits"]
        if distributions is None or fit["distribution"] in distributions
    ]
    if distributions is not None:
        unknown = [name for name in distributions if name not in result.distributions]
        if unknown:
            raise HangtuError(
                f"distributions= names {', '.join(map(repr, unknown))}, which the "
                f"result didn't fit. Fitted: {', '.join(result.distributions)}."
            )
    fitted = [fit["distribution"] for fit in fits]
    if qq is not None and qq not in fitted:
        raise HangtuError(
            f"qq={qq!r} isn't among the fits drawn: {', '.join(fitted) or 'none'}."
        )
    qq = qq or (fitted[0] if fitted else None)
    exact = np.asarray(record["values"]["exact"], float)
    left = np.asarray(record["values"]["left"], float)
    right = np.asarray(record["values"]["right"], float)
    notes = Notes()
    if log:
        notes.count(exact <= 0, "log_nonpositive")
        notes.count(left <= 0, "log_nonpositive")
        notes.count(right <= 0, "log_nonpositive")
        exact, left, right = exact[exact > 0], left[left > 0], right[right > 0]
    _footnote(notes, record, note)

    info = column_info(result.value) if result.value else None
    text = info["label"] if info and "label" in info else (result.value or "Value")
    x_label = axis_label(text, result.unit)
    ratio = result.bounds[0] == 0

    with style.context(**style_overrides):
        fig, axs = plt.subplots(
            1,
            2,
            figsize=figsize or figure_size("default"),
            layout="constrained",
            gridspec_kw={"width_ratios": PANEL_RATIO},
        )
        histogram, quantiles = axs
        for ax in axs:
            style.style_axes(ax)
        limits = _value_limits(np.concatenate([exact, left, right]), log, ratio)
        handles = _draw_histogram(
            histogram, result, record, fits, exact, left, right, limits, bins, log
        )
        histogram.set_xlabel(x_label)
        density = f"1/{result.unit}" if result.unit else None
        histogram.set_ylabel(axis_label("Probability density", density))
        if reference_lines:
            scale = ValueScale(
                result.unit if result.display_units else None,
                info.get("quantity") if info else None,
                result.display_units or settings.display_units,
                log,
            )
            draw_reference_lines(histogram, reference_lines, scale)
        _draw_quantiles(quantiles, result, record, qq, limits, log, x_label)
        # Inside always: a legend below would be wider than the histogram and
        # squeeze the Q-Q panel.
        placed = add_legend(histogram, [handles], notes, where="inside")
        if table and fits:
            _draw_table(quantiles, _table_text(fits))
        notes.render(histogram, where=placed.where, below=placed.legend)
    return fig, axs


def _footnote(notes: Notes, record: dict[str, Any], note: str | None) -> None:
    counts = record["counts"]
    left_out = {
        "count_non_plastic": "non-plastic (NP)",
        "count_assumed": "assumed",
        "count_range": "range only",
        "count_text": "text",
        "count_blank": "blank",
    }
    listed = [
        f"{counts[name]} {text}" for name, text in left_out.items() if counts[name]
    ]
    if listed:
        notes.add_text(f"Not fitted: {', '.join(listed)}")
    censored = counts["count_censored"]
    if censored and record["fits"]:
        notes.add_text(f"No AD check: {censored} censored")
    if record["positions"] is None and record["fits"]:
        notes.add_text("No plotting positions: censored both ways")
    by_reason: dict[str, list[str]] = {}
    for name, why in record["left_out"].items():
        by_reason.setdefault(why, []).append(name)
    for why, names in by_reason.items():
        notes.add_text(f"{', '.join(names)} not fitted: {why}")
    if note is not None:
        notes.add_text(str(note))


def _value_limits(values: np.ndarray, log: bool, ratio: bool) -> tuple[float, float]:
    if not values.size:
        return (1.0, 100.0) if log else (0.0, 1.0)
    if log:
        return log_limits(float(values.min()), float(values.max()), min_decades=1)
    return nice_limits(float(values.min()), float(values.max()), start_at_zero=ratio)


def _draw_histogram(
    ax: Axes,
    result: FitResult,
    record: dict[str, Any],
    fits: list[dict[str, Any]],
    exact: np.ndarray,
    left: np.ndarray,
    right: np.ndarray,
    limits: tuple[float, float],
    bins: int | str,
    log: bool,
) -> list[Any]:
    """Draw the bars, the censored markers and the densities; return the handles."""
    count = record["counts"]["count"]
    handles = []
    tallest = 0.0
    if exact.size:
        source = np.log10(exact) if log else exact
        edges = np.histogram_bin_edges(source, bins)
        edges = 10.0**edges if log else edges
        counts, _ = np.histogram(exact, edges)
        # Area = the share uncensored, so the bars and the densities share a scale.
        heights = counts / (count * np.diff(edges))
        ax.bar(
            edges[:-1],
            heights,
            width=np.diff(edges),
            align="edge",
            color=HISTOGRAM_FILL,
            edgecolor=HISTOGRAM_EDGE,
            linewidth=0.5,
            zorder=_layers.INTERVALS,
        )
        tallest = float(heights.max())
        handles.append(
            Patch(
                facecolor=HISTOGRAM_FILL,
                edgecolor=HISTOGRAM_EDGE,
                linewidth=0.5,
                label=f"Values (n = {exact.size})",
            )
        )
    for values, marker, sign in ((right, ">", "≥"), (left, "<", "<")):
        if not values.size:
            continue
        ax.plot(
            values,
            np.zeros(values.size),
            linestyle="none",
            marker=marker,
            markersize=7,
            markeredgewidth=1.2,
            markerfacecolor="none",
            markeredgecolor=CENSORED_COLOR,
            clip_on=False,
            zorder=_layers.QUALIFIERS,
        )
        bound = (
            f"{format_number(values[0])}"
            if np.all(values == values[0])
            else f"{format_number(values.min())} to {format_number(values.max())}"
        )
        handles.append(
            Line2D(
                [],
                [],
                linestyle="none",
                marker=marker,
                markerfacecolor="none",
                markeredgecolor=CENSORED_COLOR,
                label=f"{sign} {bound}: {values.size}",
            )
        )
    xs = (
        np.geomspace(*limits, CURVE_POINTS)
        if log
        else np.linspace(*limits, CURVE_POINTS)
    )
    group = _key(record["key"]) if result.by else None
    for i, fit in enumerate(fits):
        name = fit["distribution"]
        # Gamma and Weibull with a shape below 1 are infinite at 0.
        with np.errstate(divide="ignore", invalid="ignore"):
            density = result.distribution(name, group).pdf(xs)
        if i == 0:
            tallest = max(tallest, float(np.nanmax(density[np.isfinite(density)])))
        (line,) = ax.plot(
            xs,
            density,
            color=COLORS[name],
            linewidth=BEST_WIDTH if fit["rank"] == 1 else OTHER_WIDTH,
            linestyle="-" if fit["rank"] == 1 else "--",
            label=f"{name} (rank {fit['rank']})",
            zorder=_layers.CONNECT,
        )
        handles.append(line)
    if not record["fits"]:
        ax.text(
            0.5,
            0.5,
            _not_fitted(record),
            transform=ax.transAxes,
            ha="center",
            va="center",
            color="0.4",
            zorder=_layers.ANNOTATIONS,
        )
    if log:
        set_log_axis(ax, "x", limits)
    else:
        set_linear_axis(ax, "x", limits)
    top = nice_limits(0.0, tallest * HEADROOM, start_at_zero=True)[1] if tallest else 1
    set_linear_axis(ax, "y", (0.0, top))
    return handles


def _not_fitted(record: dict[str, Any]) -> str:
    if record["reason"] and record["reason"].startswith("fewer than"):
        return TOO_FEW.format(n=len(record["values"]["exact"]))
    return f"not fitted: {record['reason']}"


def _draw_quantiles(
    ax: Axes,
    result: FitResult,
    record: dict[str, Any],
    qq: str | None,
    limits: tuple[float, float],
    log: bool,
    y_label: str,
) -> None:
    """Draw the values against the fitted quantiles at their plotting positions."""
    positions = record["positions"]
    message = None
    if qq is None:
        message = _not_fitted(record)
    elif positions is None:
        message = "no plotting positions:\ncensored both ways"
    if message is None:
        values = np.asarray(positions["values"], float)
        group = _key(record["key"]) if result.by else None
        fitted = result.distribution(qq, group).ppf(positions["probabilities"])
        if log:
            keep = (values > 0) & (fitted > 0)
            values, fitted = values[keep], fitted[keep]
        both = np.concatenate([values, fitted])
        both = both[np.isfinite(both)]
        lo, hi = (
            log_limits(both.min(), both.max(), min_decades=1)
            if log
            else nice_limits(both.min(), both.max(), start_at_zero=limits[0] == 0)
        )
        ax.plot([lo, hi], [lo, hi], color="black", linewidth=0.6, zorder=_layers.LINES)
        ax.plot(
            fitted,
            values,
            linestyle="none",
            marker="o",
            markersize=QQ_MARKER_SIZE,
            color=COLORS[qq],
            zorder=_layers.MARKERS,
        )
        limits = (lo, hi)
    else:
        ax.text(
            0.5,
            0.5,
            message,
            transform=ax.transAxes,
            ha="center",
            va="center",
            color="0.4",
            zorder=_layers.ANNOTATIONS,
        )
    for axis in ("x", "y"):
        if log:
            set_log_axis(ax, axis, limits)
        else:
            set_linear_axis(ax, axis, limits)
    ax.set_aspect("equal", adjustable="box")
    unit = result.unit
    ax.set_xlabel(
        axis_label(f"Fitted quantile, {qq}" if qq else "Fitted quantile", unit)
    )
    ax.set_ylabel(y_label)


def _table_text(fits: list[dict[str, Any]]) -> str:
    rows = [["Rank", "Distribution", "ΔAICc", "AD p"]]
    for fit in fits:
        p_value = fit["anderson_darling_p_value"]
        rows.append(
            [
                str(fit["rank"]),
                fit["distribution"],
                format_number(fit["delta_aicc"]),
                "—" if not np.isfinite(p_value) else format_number(p_value),
            ]
        )
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    return "\n".join(
        "  ".join(
            cell.ljust(width) if i == 1 else cell.rjust(width)
            for i, (cell, width) in enumerate(zip(row, widths, strict=True))
        )
        for row in rows
    )


def _draw_table(ax: Axes, text: str) -> None:
    """Write the fit table under the Q-Q panel's x label.

    The panel's equal aspect leaves room there, so the table never covers
    data, the legend or the curves.
    """
    ax.annotate(
        text,
        xy=(0.5, 0.0),
        xycoords="axes fraction",
        xytext=(0.0, -below_x_label(ax)),
        textcoords="offset points",
        ha="center",
        va="top",
        fontsize=TEXT_SIZE,
        family="monospace",
        color="0.15",
        annotation_clip=False,
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": "white",
            "edgecolor": "0.7",
            "linewidth": 0.5,
        },
        zorder=_layers.ANNOTATIONS,
    )
