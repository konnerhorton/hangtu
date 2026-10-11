"""A dummy plot and the shared test helpers for plots (P00 §14)."""

import copy

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest

from ags_kit import units
from ags_kit._settings import settings
from ags_kit.plot import style
from ags_kit.plot.common import (
    Notes,
    add_legend,
    apply_vertical_axis,
    axis_label,
    edge_markers,
    hint_missing,
    nice_limits,
    resolve_palette,
    set_linear_axis,
)
from ags_kit.registry import column_info


def dummy_plot(
    df,
    value,
    *,
    vs="depth",
    xlim=None,
    palette=None,
    units_=None,
    display_units=None,
    figsize=None,
    ax=None,
    **style_overrides,
):
    """A minimal plot that follows the contract and uses every P00 helper.

    ``units_`` stands in for the contract's ``units=`` argument, which would
    shadow the ``units`` module here.
    """
    optional = {"geology_unit": "points are not colored by geology"}
    with style.context(**style_overrides):
        hint_missing(df, optional)
        resolved = units.resolve_units(df, [value, vs], units_)
        quantity = column_info(value)["quantity"]
        notes = Notes()
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize or settings.figure_sizes["profile"])
        else:
            fig = ax.figure
        style.style_axes(ax)

        blank = (df[value].isna() | df[vs].isna()).to_numpy()
        notes.count(blank, "nan")
        x, x_text = units.to_display(
            df[value][~blank], resolved[value], quantity, display_units
        )
        y, y_text = units.to_display(
            df[vs][~blank], resolved[vs], "length", display_units
        )
        apply_vertical_axis(ax, vs, y.min(), y.max())
        limits = xlim or nice_limits(x.min(), x.max(), start_at_zero=True)
        set_linear_axis(ax, "x", limits)

        geology = (
            df["geology_unit"][~blank].to_numpy()
            if "geology_unit" in df
            else np.full(len(x), None)
        )
        colors = resolve_palette(geology, palette)
        edge = np.zeros(len(x), dtype=bool)
        handles = []
        for unit in [*colors, None] if None in geology else colors:
            rows = geology == unit
            color = colors.get(unit, "0.3")
            if xlim:
                edge[rows] = edge_markers(ax, x[rows], y[rows], {"x": xlim}, color)
            inside = rows & ~edge
            handle = ax.scatter(x[inside], y[inside], color=color, label=str(unit))
            if unit is not None:
                handles.append(handle)
        notes.count(edge, "beyond_limit")

        datum = settings.vertical_datum if vs == "elevation" else None
        ax.set_xlabel(
            axis_label(
                column_info(value)["label"],
                x_text,
                unknown=resolved[value] is None and units.needs_units(value),
            )
        )
        ax.set_ylabel(
            axis_label(vs.capitalize(), y_text, datum, unknown=resolved[vs] is None)
        )
        add_legend(ax, [handles], notes)
        notes.render(ax)
    return fig, ax


def _point_positions(ax):
    return [c.get_offsets().data.copy() for c in ax.collections]


def assert_no_global_state(plot_fn, df, **kwargs):
    """The plot leaves rcParams, the figure list and its input frame unchanged."""
    rc_before = dict(mpl.rcParams)
    figures_before = plt.get_fignums()
    frame_before = df.copy(deep=True)
    attrs_before = copy.deepcopy(df.attrs)
    plot_fn(df, **kwargs)
    assert dict(mpl.rcParams) == rc_before
    added = len(plt.get_fignums()) - len(figures_before)
    assert added == (0 if kwargs.get("ax") is not None else 1)
    assert df.equals(frame_before)
    assert df.attrs == attrs_before


def assert_us_si_equivalent(plot_fn, df, quantities, **kwargs):
    """US and SI versions of a plot put every point in the same place.

    ``quantities`` is ``(x quantity, y quantity)``. Positions drawn in US are
    converted to SI and compared; the notes must match too. Only labels and
    ticks may differ.
    """
    _, us = plot_fn(df, display_units="US", **kwargs)
    _, si = plot_fn(df, display_units="SI", **kwargs)
    to_si = []
    for quantity in quantities:
        kind = units.quantity_kind(quantity)
        if kind["canonical"] is None:
            to_si.append(1.0)
        else:
            source = units.ureg.Unit(kind["US"]["unit"])
            target = units.ureg.Unit(kind["SI"]["unit"])
            to_si.append(units.convert([1.0], source, quantity, target)[0])
    us_points = _point_positions(us)
    si_points = _point_positions(si)
    assert len(us_points) == len(si_points)
    for us_xy, si_xy in zip(us_points, si_points, strict=True):
        np.testing.assert_allclose(us_xy * to_si, si_xy, rtol=1e-9)
    assert us.ags_notes == si.ags_notes


@pytest.fixture(name="dummy_plot")
def _dummy_plot():
    return dummy_plot


@pytest.fixture(name="assert_no_global_state")
def _assert_no_global_state():
    return assert_no_global_state


@pytest.fixture(name="assert_us_si_equivalent")
def _assert_us_si_equivalent():
    return assert_us_si_equivalent
