"""P12 triaxial shearing (docs/plots/P12-triaxial-shearing.md)."""

import math
from collections.abc import Sequence
from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from hangtu import units as _units
from hangtu._settings import _display_units, settings
from hangtu.analysis._mohr_coulomb import MohrCoulombFit, mohr_coulomb_fit
from hangtu.analysis._triaxial import EXTENSION, triaxial_failure_stresses
from hangtu.analysis._triaxial_readings import Reduced, reduce_readings
from hangtu.errors import HangtuError
from hangtu.plot import _envelope_drawing as envelope
from hangtu.plot import _layers, _values, style
from hangtu.plot._labels import axis_label
from hangtu.plot._legend import add_legend
from hangtu.plot._limits import nice_limits
from hangtu.plot._notes import Notes
from hangtu.plot._palette import resolve_palette
from hangtu.plot._spt_profile import _check_choice
from hangtu.registry import _entry

SPACES = ("stress_strain", "s_t", "p_q")
STRESSES = ("effective", "total")
SECOND_AXES = ("excess_pore_pressure", "volumetric_strain")
USER_ENVELOPE_COLOR = "0.55"
CURVE_WIDTH = 1.0
MARKER_SIZE = 4.5
STAGE_COLORS = plt.get_cmap("tab10").colors


def triaxial_shearing(
    df: pd.DataFrame,
    *,
    space: Literal["stress_strain", "s_t", "p_q"] = "stress_strain",
    stress: Literal["effective", "total"] = "effective",
    failure_criterion: Literal["max_deviator_stress", "max_stress_ratio"] | None = None,
    second_axis: Literal["excess_pore_pressure", "volumetric_strain"] | None = None,
    group_by: str | list[str] | None = None,
    color_by: str | None = None,
    cohesion: float | None = None,
    multistage: bool = True,
    pool: str | list[str] | None = None,
    fit: bool = True,
    result_box: bool = True,
    envelopes: Sequence[tuple[float, float, str]] | None = None,
    note: str | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides: Any,
) -> tuple[Figure, Axes, MohrCoulombFit | None]:
    r"""Plot triaxial readings during shearing: curves or stress paths (P12).

    Draws each stage's readings, one row per strain step as
    ``ht.template("triaxial_readings")`` lays them out, in one of three
    spaces: deviator stress against axial strain (``"stress_strain"``), or
    the measured stress path in s′-t (``"s_t"``) or p′-q (``"p_q"``) with the
    Mohr-Coulomb envelope P11 fits to the same stages. Each stage's failure
    reading is marked with a dot, the same reading in every view and in the
    fit: it is picked by ``ht.analysis.triaxial_failure_from_readings()``,
    whose rows go through ``triaxial_failure_stresses()`` to
    ``mohr_coulomb_fit()``, as ``ht.plot.failure_envelope()`` draws them.

    At each reading, with $\sigma_c$ the cell pressure, $u_b$ the back
    pressure, $q$ the deviator stress and $\Delta u$ the excess pore pressure
    (0 in a drained stage where it is blank):

    $$
    \sigma'_3 = \sigma_c - (u_b + \Delta u), \quad
    \sigma'_1 = \sigma'_3 + q, \quad
    s' = \frac{\sigma'_1 + \sigma'_3}{2}, \quad
    t = \frac{q}{2}, \quad
    p' = \frac{\sigma'_1 + 2\sigma'_3}{3}
    $$

    These are definitions, used without a coefficient. ``stress="total"``
    draws $\sigma_3 = \sigma_c$ and $\sigma_1 = \sigma_c + q$ instead, as for
    ``UU`` tests. The envelope is the s′-t fit, transformed into p′-q, never
    refitted.

    **Valid for:** triaxial compression with constant cell pressure. Extension
    stages are drawn in ``"stress_strain"`` only, and counted in the others.
    **Judgments taken:** none; the failure criterion is the caller's or the
    lab's.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per reading, as for ``triaxial_failure_from_readings()``:
        ``specimen_id`` (and ``test_stage``), ``test_type``, ``cell_pressure``,
        ``axial_strain`` and ``deviator_stress``; ``back_pressure`` and
        ``excess_pore_pressure`` for effective stresses; ``volumetric_strain``
        and ``reported_failure_reading`` where known.
    space : {"stress_strain", "s_t", "p_q"}
        The view.
    stress : {"effective", "total"}
        The stresses of the paths and the fit (``"s_t"`` and ``"p_q"``).
    failure_criterion : {"max_deviator_stress", "max_stress_ratio"}, optional
        How each stage's failure reading is picked. Without it, the lab's
        ``reported_failure_reading`` is used; there is no default.
    second_axis : {"excess_pore_pressure", "volumetric_strain"}, optional
        In ``"stress_strain"``, draw this column dashed on a second y axis.
        The returned ``ax`` is the deviator stress axis; the second one is
        ``ax.get_shared_x_axes().get_siblings(ax)``'s other member.
    group_by : str or list of str, optional
        One color and, in ``"s_t"``/``"p_q"``, one fit per group.
    color_by : str, optional
        Color the stages by this stage column; default one color per stage.
        Can't be used with ``group_by``.
    cohesion, multistage, pool, fit, result_box, envelopes
        As ``ht.plot.failure_envelope()``, in ``"s_t"`` and ``"p_q"`` only.
    note : str, optional
        A line added to the footnote.
    units : dict, optional
        ``{column: unit}`` for ``df``, overriding ``df.attrs["units"]``.
    display_units : {"US", "SI"}, optional
        Units to draw in; default ``ht.settings.display_units``.
    figsize : (float, float), optional
        Figure size in inches. Defaults to ``ht.settings.figure_sizes["default"]``.
    ax : matplotlib.axes.Axes, optional
        Draw into these axes, such as a panel of an ``ht.Sheet``.
    **style_overrides
        Matplotlib rcParams for this plot only.

    Returns
    -------
    fig, ax, fit
        The figure, the axes, and the ``MohrCoulombFit`` drawn: None in
        ``"stress_strain"`` and with ``fit=False``.

    Raises
    ------
    HangtuError
        For the problems ``triaxial_failure_from_readings()`` raises on, an
        argument the space doesn't take, or ``color_by`` with ``group_by``.

    Examples
    --------
    >>> readings = ht.read_csv("readings.csv", units={...})
    >>> fig, ax, _ = ht.plot.triaxial_shearing(
    ...     readings, failure_criterion="max_deviator_stress",
    ...     second_axis="excess_pore_pressure",
    ... )
    >>> fig, ax, fit = ht.plot.triaxial_shearing(
    ...     readings, space="s_t", failure_criterion="max_stress_ratio"
    ... )
    """
    _check_choice("space", space, SPACES)
    _check_choice("stress", stress, STRESSES)
    if second_axis is not None:
        _check_choice("second_axis", second_axis, SECOND_AXES)
    _check_space_arguments(
        space,
        second_axis=second_axis,
        cohesion=cohesion,
        multistage=multistage,
        pool=pool,
        fit=fit,
        result_box=result_box,
        envelopes=envelopes,
    )
    if group_by is not None and color_by is not None:
        raise HangtuError(
            "color_by= can't be used with group_by=: each group is drawn in its "
            "own color. Use one or the other."
        )
    if isinstance(df, pd.DataFrame):
        if second_axis is not None and second_axis not in df.columns:
            raise HangtuError(
                f"second_axis={second_axis!r}, but df has no such column. Add it, "
                "or leave second_axis=None."
            )
        if color_by is not None and color_by not in df.columns:
            raise HangtuError(
                f"color_by={color_by!r}, but df has no such column. Available "
                f"columns: {', '.join(map(str, df.columns))}."
            )
    user_envelopes = envelope.check_envelopes(envelopes)
    system = _display_units(display_units or settings.display_units)
    reduced = reduce_readings(df, failure_criterion, units)
    stages = triaxial_failure_stresses(reduced.rows)

    with style.context(**style_overrides):
        if ax is None:
            fig, ax = plt.subplots(
                figsize=figsize or settings.figure_sizes["default"],
                layout="constrained",
            )
        else:
            fig = ax.figure
        style.style_axes(ax)
        notes = Notes()
        labels, colors = _stage_colors(reduced, group_by, color_by)
        stress_unit = _display_stress_unit(reduced, system)
        if space == "stress_strain":
            handles = _draw_curves(ax, reduced, labels, colors, system, notes)
            if second_axis is not None:
                handles += _draw_second_axis(
                    ax, reduced, second_axis, labels, colors, system, notes
                )
            result = None
        else:
            result = None
            if fit:
                result = mohr_coulomb_fit(
                    stages,
                    stress=stress,
                    group_by=group_by,
                    cohesion=cohesion,
                    multistage=multistage,
                    pool=pool,
                    display_units=system,
                )
            handles = _draw_paths(
                ax, reduced, space, stress, labels, colors, system, stress_unit, notes
            )
            xlim = ax.get_xlim()
            for cohesion_value, angle, label in user_envelopes:
                intercept, slope = envelope.line(
                    space, cohesion_value, math.radians(angle)
                )
                handles += ax.plot(
                    xlim,
                    [intercept + slope * x for x in xlim],
                    color=USER_ENVELOPE_COLOR,
                    linewidth=envelope.LINE_WIDTH,
                    label=label,
                    gid="user_envelope",
                    zorder=_layers.LINES,
                )
            if result is not None:
                handles += envelope.draw_fits(ax, result, space, colors, xlim)
                if result_box:
                    envelope.draw_box(ax, result)
                _fit_footnote(result, notes)
        if note is not None:
            notes.add_text(str(note))
        placed = add_legend(ax, [handles], notes)
        notes.render(ax, where=placed.where, below=placed.legend)
    return fig, ax, result


def _check_space_arguments(space: str, **given: Any) -> None:
    """Raise for an argument the space doesn't take (P12 §11)."""
    defaults = {
        "cohesion": None,
        "multistage": True,
        "pool": None,
        "fit": True,
        "result_box": True,
        "envelopes": None,
    }
    if space != "stress_strain" and given["second_axis"] is not None:
        raise HangtuError(
            f"second_axis= draws on the strain axis, so it needs "
            f'space="stress_strain", not {space!r}.'
        )
    if space == "stress_strain":
        changed = [
            name
            for name, default in defaults.items()
            if given[name] is not default and given[name] != default
        ]
        if changed:
            raise HangtuError(
                f"{', '.join(f'{name}=' for name in changed)} set the failure "
                'envelope, which is drawn in space="s_t" or "p_q", not in '
                '"stress_strain". Change the space, or leave them out.'
            )


def _stage_label(reduced: Reduced, key: tuple) -> str:
    specimen, stage = key
    rows = reduced.rows
    multistage = False
    if "multistage_test" in rows.columns:
        same = rows["specimen_id"].astype(object) == specimen
        multistage = bool(rows.loc[same, "multistage_test"].any())
    if multistage and stage is not None:
        return f"{specimen}, stage {stage}"
    return str(specimen)


def _stage_colors(
    reduced: Reduced, group_by: str | list[str] | None, color_by: str | None
) -> tuple[dict[tuple, str], dict[str, Any]]:
    """Return each stage's legend label and ``{label: color}``."""
    df = reduced.readings.df
    first = {key: rows[0] for key, rows in reduced.stages.items()}
    if group_by is not None:
        columns = [group_by] if isinstance(group_by, str) else list(group_by)
        missing = [column for column in columns if column not in df.columns]
        if missing:
            raise HangtuError(
                f"group_by= names {', '.join(map(repr, missing))}, but df has no "
                "such column."
            )
        labels = {}
        for key, row in first.items():
            values = tuple(df.iloc[row][column] for column in columns)
            value = values[0] if len(values) == 1 else values
            labels[key] = _values.group_text(
                _values.BLANK_GROUP if _blank(value) else value
            )
        names = list(dict.fromkeys(labels.values()))
        if len(names) == 1:
            return labels, {names[0]: envelope.ENVELOPE_COLOR}
        return labels, resolve_palette(names, None, names, df.attrs.get("palette"))
    if color_by is not None:
        frame = df.iloc[list(first.values())]
        groups, colors = _values.color_groups(frame, color_by, None)
        labels = {
            key: str(group) if group is not None else None
            for key, group in zip(first, groups, strict=True)
        }
        return labels, {str(k) if k is not None else None: v for k, v in colors.items()}
    labels = {key: _stage_label(reduced, key) for key in first}
    names = list(dict.fromkeys(labels.values()))
    colors = {name: STAGE_COLORS[i % len(STAGE_COLORS)] for i, name in enumerate(names)}
    return labels, colors


def _blank(value: Any) -> bool:
    return not isinstance(value, tuple) and pd.isna(value)


def _display_stress_unit(reduced: Reduced, system: str) -> str | None:
    return _units.to_display([0.0], reduced.readings.stress_unit, "stress", system)[1]


def _display(values: np.ndarray, reduced: Reduced, system: str) -> np.ndarray:
    return _units.to_display(values, reduced.readings.stress_unit, "stress", system)[0]


def _legend_entries(
    labels: dict[tuple, str], colors: dict[str, Any], drawn: set[tuple]
) -> list[Line2D]:
    names = list(dict.fromkeys(labels[key] for key in labels if key in drawn))
    if len(names) < 2 and None in names:
        return []
    return [
        Line2D([], [], color=colors[name], linewidth=CURVE_WIDTH, label=str(name))
        for name in names
        if name is not None
    ]


def _draw_curves(
    ax: Axes,
    reduced: Reduced,
    labels: dict[tuple, str],
    colors: dict[str, Any],
    system: str,
    notes: Notes,
) -> list[Line2D]:
    """Draw q against axial strain per stage, with its failure reading (§7)."""
    readings = reduced.readings
    strain = readings.strain
    deviator = _display(readings.deviator, reduced, system)
    blank = np.isnan(strain) | np.isnan(deviator)
    drawn = set()
    for key, rows in reduced.stages.items():
        shown = rows[~blank[rows]]
        if not len(shown):
            continue
        drawn.add(key)
        color = colors[labels[key]]
        ax.plot(
            strain[shown],
            deviator[shown],
            color=color,
            linewidth=CURVE_WIDTH,
            gid="reading_curve",
            zorder=_layers.LINES,
        )
        pick = reduced.picks[key]
        ax.plot(
            [strain[pick]],
            [deviator[pick]],
            marker="o",
            markersize=MARKER_SIZE,
            color=color,
            linestyle="none",
            gid="failure_point",
            zorder=_layers.MARKERS,
        )
    if blank.any():
        notes.add_text(
            f"Left out: {int(blank.sum())} reading{'s' if blank.sum() > 1 else ''} "
            "without axial strain or deviator stress"
        )
    unit = _display_stress_unit(reduced, system)
    ax.set_xlabel(axis_label(_entry("axial_strain")["label"], "%"))
    ax.set_ylabel(axis_label(_entry("deviator_stress")["label"], unit))
    finite = ~blank
    if finite.any():
        ax.set_xlim(*nice_limits(0.0, float(strain[finite].max()), start_at_zero=True))
        ax.set_ylim(
            *nice_limits(
                min(0.0, float(deviator[finite].min())),
                float(deviator[finite].max()),
                start_at_zero=True,
            )
        )
    ax.grid(True, which="major")
    return _legend_entries(labels, colors, drawn)


def _draw_second_axis(
    ax: Axes,
    reduced: Reduced,
    column: str,
    labels: dict[tuple, str],
    colors: dict[str, Any],
    system: str,
    notes: Notes,
) -> list[Line2D]:
    """Draw Δu or ε_v dashed on a twin y axis (P12 §8)."""
    readings = reduced.readings
    if column == "excess_pore_pressure":
        values = _display(readings.excess, reduced, system)
        unit = _display_stress_unit(reduced, system)
        short = "Δu"
    else:
        values = readings.volumetric
        unit = "%"
        short = "ε_v"
    twin = ax.twinx()
    style.style_axes(twin)
    missing = 0
    shown_any = np.zeros(len(values), dtype=bool)
    for key, rows in reduced.stages.items():
        shown = rows[~np.isnan(values[rows]) & ~np.isnan(readings.strain[rows])]
        if not len(shown):
            missing += 1
            continue
        shown_any[shown] = True
        color = colors[labels[key]]
        twin.plot(
            readings.strain[shown],
            values[shown],
            color=color,
            linewidth=CURVE_WIDTH,
            linestyle="--",
            gid="second_axis_line",
            zorder=_layers.CONNECT,
        )
    if missing:
        notes.add_text(
            f"No {short} line: {missing} stage{'s' if missing > 1 else ''} without "
            f"{column}"
        )
    twin.set_ylabel(axis_label(_entry(column)["label"], unit))
    if shown_any.any():
        twin.set_ylim(
            *nice_limits(
                min(0.0, float(values[shown_any].min())),
                float(values[shown_any].max()),
                start_at_zero=True,
            )
        )
    return [
        Line2D(
            [],
            [],
            color="0.3",
            linewidth=CURVE_WIDTH,
            ls="--",
            label=f"{short} (dashed)",
        )
    ]


def _draw_paths(
    ax: Axes,
    reduced: Reduced,
    space: str,
    stress: str,
    labels: dict[tuple, str],
    colors: dict[str, Any],
    system: str,
    unit: str | None,
    notes: Notes,
) -> list[Line2D]:
    """Draw each stage's measured path and its failure reading (P12 §4)."""
    readings = reduced.readings
    if stress == "effective":
        minor = _display(readings.effective_minor, reduced, system)
        major = _display(readings.effective_major, reduced, system)
    else:
        minor = _display(readings.cell, reduced, system)
        major = minor + _display(readings.deviator, reduced, system)
    if space == "s_t":
        x, y = (major + minor) / 2, (major - minor) / 2
    else:
        x, y = (major + 2 * minor) / 3, major - minor
    usable = ~np.isnan(x) & ~np.isnan(y) & ~np.isnan(readings.strain)
    extension = readings.types.isin(EXTENSION).to_numpy()
    counts = {"extension": 0, "no_stress": 0}
    drawn = set()
    xs, ys = [], []
    for key, rows in reduced.stages.items():
        if extension[rows].any():
            counts["extension"] += 1
            continue
        shown = rows[usable[rows]]
        if not len(shown):
            counts["no_stress"] += 1
            continue
        drawn.add(key)
        color = colors[labels[key]]
        ax.plot(
            x[shown],
            y[shown],
            color=color,
            linewidth=CURVE_WIDTH,
            gid="stress_path",
            zorder=_layers.LINES,
        )
        xs.extend(x[shown])
        ys.extend(y[shown])
        pick = reduced.picks[key]
        if usable[pick]:
            ax.plot(
                [x[pick]],
                [y[pick]],
                marker="o",
                markersize=MARKER_SIZE,
                color=color,
                linestyle="none",
                gid="failure_point",
                zorder=_layers.MARKERS,
            )
    parts = []
    if counts["no_stress"]:
        kind = "effective" if stress == "effective" else "total"
        parts.append(f"{counts['no_stress']} without {kind} stresses")
    if counts["extension"]:
        n = counts["extension"]
        parts.append(f"{n} extension stage{'s' if n > 1 else ''}")
    if parts:
        notes.add_text("Left out of the paths: " + ", ".join(parts))
    if xs:
        x_low = min(0.0, min(xs))
        xlim = nice_limits(x_low, max(xs), start_at_zero=True)
        ylim = nice_limits(0.0, max(max(ys), 0.0), start_at_zero=True)
    else:
        xlim, ylim = (0.0, 1.0), (0.0, 1.0)
    envelope.set_axes(ax, space, stress, unit, xlim, ylim)
    return _legend_entries(labels, colors, drawn)


def _fit_footnote(result: MohrCoulombFit, notes: Notes) -> None:
    """Count the multistage stages the main fit leaves out; P12 counts the rest."""
    left_out = sum(
        group["fits"][0]["count_multistage_left_out"] for group in result.groups
    )
    if left_out:
        notes.add_text(f"Left out of the fit: {left_out} multistage stages")
