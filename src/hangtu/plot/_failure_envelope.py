"""P11 failure envelope (docs/plots/P11-failure-envelope.md)."""

import math
from collections.abc import Sequence
from typing import Any, Literal

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Arc

from hangtu._settings import _display_units, settings
from hangtu.analysis._mohr_coulomb import MohrCoulombFit, mohr_coulomb_fit
from hangtu.analysis._triaxial import DRAINED
from hangtu.errors import HangtuError
from hangtu.plot import _envelope_drawing as envelope
from hangtu.plot import _layers, _values, style
from hangtu.plot._hints import hint_missing
from hangtu.plot._legend import add_legend
from hangtu.plot._notes import Notes
from hangtu.plot._palette import resolve_palette
from hangtu.plot._spt_profile import _check_choice

SPACES = ("mohr", "s_t", "p_q")
PATHS = ("idealized_drained",)
USER_ENVELOPE_COLOR = "0.55"
CIRCLE_WIDTH = 0.9
PATH_WIDTH = 0.7
MARKER_SIZE = 4.0


def failure_envelope(
    df: pd.DataFrame,
    *,
    space: Literal["mohr", "s_t", "p_q"] = "mohr",
    stress: Literal["effective", "total"] = "effective",
    group_by: str | list[str] | None = None,
    color_by: str | None = None,
    cohesion: float | None = None,
    multistage: bool = True,
    pool: str | list[str] | None = None,
    fit: bool = True,
    paths: Literal["idealized_drained"] | None = None,
    result_box: bool = True,
    envelopes: Sequence[tuple[float, float, str]] | None = None,
    note: str | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes, MohrCoulombFit | None]:
    r"""Plot triaxial failure states with the fitted Mohr-Coulomb envelope (P11).

    Draws the same failure points and the same fit in one of three spaces:
    Mohr circles in σ′-τ (``"mohr"``), points in s′-t (``"s_t"``), or points
    in p′-q (``"p_q"``). The fit is ``ht.analysis.mohr_coulomb_fit()``, made
    in s′-t; the other spaces draw it transformed, never refitted:

    $$
    \tau = c' + \sigma' \tan\phi', \quad t = c' \cos\phi' + s' \sin\phi',
    \quad q = \frac{6 c' \cos\phi'}{3 - \sin\phi'}
    + p' \frac{6 \sin\phi'}{3 - \sin\phi'}
    $$

    The p′-q line is for triaxial compression. The envelope is solid over
    the range of the tangent points and dashed beyond: c′ is an intercept,
    outside the stresses tested. A box gives each group's c′, φ′, n, R², the
    fitted range, and the lab's own values where the rows have them. Equal
    aspect in every space, so circles are circles and slopes read true.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per stage with the principal stresses at failure, as
        ``p.triaxial()`` or ``ht.analysis.triaxial_failure_stresses()``.
    space : {"mohr", "s_t", "p_q"}
        The space drawn.
    stress, group_by, cohesion, multistage, pool, units
        Passed to ``ht.analysis.mohr_coulomb_fit()``, which explains them.
    color_by : str, optional
        Colors circles and points when there is no ``group_by``. Defaults to
        ``geology_unit`` when the rows have it. An error with ``group_by``:
        each fit has one color.
    fit : bool
        False draws the points or circles only, and returns None for the fit.
    paths : {"idealized_drained"}, optional
        In ``s_t`` and ``p_q``, each stage's path as a drained compression test
        at constant cell pressure would have taken it, from (σ′3, 0): slope 1
        in s′-t, 3 in p′-q. Not the measured path, and labeled so. Only for
        drained tests (``CD``, ``CDM``, ``CIDC``, ``CADC``); a blank type is
        drawn as "assumed CD".
    result_box : bool
        Write the fit's numbers in the upper left.
    envelopes : list of (cohesion, friction_angle, label), optional
        Your own envelopes, cohesion in the display units and the angle in
        degrees, transformed into the space like the fit.
    note : str, optional
        Free text, added to the footnote.
    display_units : {"US", "SI"}, optional
        Stresses in psf (US) or kPa (SI); the fit is made in them. Defaults to
        ``ht.settings.display_units``.
    figsize : tuple, optional
        Figure size in inches. Defaults to ``ht.settings.figure_sizes["default"]``.
    ax : matplotlib.axes.Axes, optional
        Draw into this axes, e.g. a ``Sheet`` panel.
    **style_overrides
        matplotlib rcParams for this plot, e.g. ``font_size=10``.

    Returns
    -------
    fig, ax, fit
        ``fit`` is the ``MohrCoulombFit`` drawn, or None with ``fit=False``.

    Examples
    --------
    >>> stages = p.triaxial()
    >>> fig, ax, fit = ht.plot.failure_envelope(stages)
    >>> fig, ax, fit = ht.plot.failure_envelope(
    ...     stages, space="s_t", group_by="geology_unit"
    ... )
    >>> fig, ax, fit = ht.plot.failure_envelope(
    ...     stages, space="p_q", paths="idealized_drained"
    ... )
    """
    _check_choice("space", space, SPACES)
    if paths is not None:
        _check_choice("paths", paths, PATHS)
        if space == "mohr":
            raise HangtuError(
                'paths= draws stress paths in s′-t or p′-q: use space="s_t" or '
                'space="p_q", or leave paths=None for Mohr circles.'
            )
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if group_by is not None and color_by is not None:
        raise HangtuError(
            "color_by= can't be used with group_by=: each fit is drawn in its "
            "group's color. Use one or the other."
        )
    user_envelopes = envelope.check_envelopes(envelopes)
    system = _display_units(display_units or settings.display_units)
    if color_by is None and group_by is None and "geology_unit" in df.columns:
        color_by = "geology_unit"
    if color_by is not None and color_by not in df.columns:
        raise HangtuError(
            f"color_by={color_by!r}, but df has no such column. Available "
            f"columns: {', '.join(map(str, df.columns))}."
        )

    with style.context(**style_overrides):
        hint_missing(
            df,
            {
                "failure_criterion": "the fit can't check that the stages share one",
                "multistage_test": "multistage stages aren't fitted apart",
                **(
                    {"geology_unit": "the stages are drawn in one color"}
                    if group_by is None
                    else {}
                ),
            },
        )
        checked = ["failure_criterion"] + (["test_type"] if stress == "total" else [])
        result = mohr_coulomb_fit(
            df,
            stress=stress,
            group_by=group_by,
            cohesion=cohesion,
            multistage=multistage,
            pool=pool if fit else checked,
            units=units,
            display_units=system,
        )
        if paths is not None:
            _check_drained(df, result)
        if ax is None:
            fig, ax = plt.subplots(
                figsize=figsize or settings.figure_sizes["default"],
                layout="constrained",
            )
        else:
            fig = ax.figure
        style.style_axes(ax)
        notes = Notes()
        colors = _colors(df, result, color_by)
        xlim, ylim = envelope.limits(result, space)
        envelope.set_axes(ax, space, stress, result.unit, xlim, ylim)
        xlim = ax.get_xlim()
        handles = _draw_points(ax, df, result, space, color_by, colors)
        if paths is not None:
            handles += _draw_paths(ax, df, result, space, color_by, colors)
        for cohesion_value, angle, label in user_envelopes:
            intercept, slope = envelope.line(space, cohesion_value, math.radians(angle))
            handles += ax.plot(
                xlim,
                [intercept + slope * x for x in xlim],
                color=USER_ENVELOPE_COLOR,
                linewidth=envelope.LINE_WIDTH,
                label=label,
                gid="user_envelope",
                zorder=_layers.LINES,
            )
        if fit:
            handles += envelope.draw_fits(ax, result, space, colors, xlim)
            if result_box:
                envelope.draw_box(ax, result)
        envelope.footnote(result, notes)
        if note is not None:
            notes.add_text(str(note))
        if not any(group["fits"][0]["points"] for group in result.groups):
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
        placed = add_legend(ax, [handles], notes)
        notes.render(ax, where=placed.where, below=placed.legend)
    return fig, ax, result if fit else None


def _check_drained(df: pd.DataFrame, result: MohrCoulombFit) -> None:
    """Raise if a drawn stage isn't a drained test (P11 §11)."""
    if "test_type" not in df.columns:
        return
    types = df["test_type"]
    named = {
        str(value)
        for value in types.loc[_rows(result)].dropna()
        if str(value).strip() and str(value) not in DRAINED
    }
    if named:
        raise HangtuError(
            f"paths='idealized_drained' draws the path of a drained test at "
            f"constant cell pressure, but the stages include {sorted(named)}, "
            "whose paths differ: it would mislead. Draw only the drained stages "
            f"({', '.join(sorted(DRAINED))}), or leave paths=None."
        )


def _rows(result: MohrCoulombFit) -> list[Any]:
    """Return the index labels of every stage drawn (each group's "all" fit)."""
    return [
        point["row"]
        for group in result.groups
        for point in envelope.all_stages_fit(group)["points"]
    ]


def _colors(
    df: pd.DataFrame, result: MohrCoulombFit, color_by: str | None
) -> dict[Any, Any]:
    """Return ``{group or color_by value: color}``."""
    if result.by:
        labels = [
            _values.group_text(envelope.group_key(group)) for group in result.groups
        ]
        if len(labels) == 1:
            return {labels[0]: envelope.ENVELOPE_COLOR}
        return resolve_palette(labels, None, labels, df.attrs.get("palette"))
    _, colors = _values.color_groups(df, color_by, None)
    return colors


def _point_color(
    df: pd.DataFrame,
    group: dict[str, Any],
    row: Any,
    color_by: str | None,
    colors: dict[Any, Any],
) -> tuple[Any, Any]:
    """Return the legend label and color of one stage."""
    if group["key"]:
        label = _values.group_text(envelope.group_key(group))
        return label, colors[label]
    if color_by is None:
        return None, colors[None]
    value = df.at[row, color_by]
    label = _values.BLANK_GROUP if pd.isna(value) else value
    return label, colors[label]


def _draw_points(
    ax: Axes,
    df: pd.DataFrame,
    result: MohrCoulombFit,
    space: str,
    color_by: str | None,
    colors: dict[Any, Any],
) -> list[Line2D]:
    """Draw each stage: a circle and its top in ``mohr``, else a point."""
    seen: dict[Any, Line2D] = {}
    for group in result.groups:
        for point in envelope.all_stages_fit(group)["points"]:
            label, color = _point_color(df, group, point["row"], color_by, colors)
            x, y = envelope.coordinates(space, point)
            if space == "mohr":
                ax.add_patch(
                    Arc(
                        (point["mean_stress"], 0.0),
                        2 * point["radius"],
                        2 * point["radius"],
                        theta1=0.0,
                        theta2=180.0,
                        color=color,
                        linewidth=CIRCLE_WIDTH,
                        gid="mohr_circle",
                        zorder=_layers.MARKERS,
                    )
                )
            ax.plot(
                [x],
                [y],
                marker="o",
                markersize=MARKER_SIZE,
                color=color,
                linestyle="none",
                gid="failure_point",
                zorder=_layers.MARKERS,
            )
            if label is not None and label not in seen:
                seen[label] = _values.legend_marker(
                    "o", color, _values.group_text(label), MARKER_SIZE
                )
    return list(seen.values()) if len(seen) > 1 or result.by else []


def _draw_paths(
    ax: Axes,
    df: pd.DataFrame,
    result: MohrCoulombFit,
    space: str,
    color_by: str | None,
    colors: dict[Any, Any],
) -> list[Line2D]:
    """Draw each stage's idealized drained path from (σ′3, 0) (P11 §4)."""
    typed = "test_type" in df.columns
    assumed = False
    for group in result.groups:
        for point in envelope.all_stages_fit(group)["points"]:
            _, color = _point_color(df, group, point["row"], color_by, colors)
            if not typed or pd.isna(df.at[point["row"], "test_type"]):
                assumed = True
            x, y = envelope.coordinates(space, point)
            ax.plot(
                [point["minor_principal_stress"], x],
                [0.0, y],
                color=color,
                linewidth=PATH_WIDTH,
                linestyle="--",
                gid="idealized_path",
                zorder=_layers.CONNECT,
            )
    label = "Idealized drained path" + (" (assumed CD)" if assumed else "")
    return [Line2D([], [], color="0.3", linewidth=PATH_WIDTH, ls="--", label=label)]
