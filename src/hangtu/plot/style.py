"""The hangtu house style (docs/plots/P00-framework.md §6)."""

import difflib
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.resources import as_file, files
from typing import Any

import matplotlib as mpl
from matplotlib.axes import Axes

from hangtu.errors import HangtuError


def _rc_name(name: str) -> str:
    """Return the rcParams key for ``name``, given as ``font.size`` or ``font_size``."""
    if name in mpl.rcParams:
        return name
    by_underscore = {
        key.replace(".", "_").replace("-", "_"): key for key in mpl.rcParams
    }
    if name in by_underscore:
        return by_underscore[name]
    close = difflib.get_close_matches(name, [*mpl.rcParams, *by_underscore], n=1)
    suggestion = f" Did you mean {close[0]!r}?" if close else ""
    raise HangtuError(
        f"{name!r} isn't a matplotlib setting (rcParams), so it can't be used as a "
        f"style override.{suggestion} Write the name with dots as a dict, "
        '**{"font.size": 10}, or with underscores, font_size=10.'
    )


@contextmanager
def context(**style_overrides: Any) -> Iterator[None]:
    """Apply the house style, plus any overrides, inside a ``with`` block.

    Every rcParam is restored afterwards, even if the block raises.

    Parameters
    ----------
    **style_overrides
        matplotlib rcParams, named with dots (``**{"font.size": 10}``) or with
        underscores (``font_size=10``).

    Examples
    --------
    >>> with ht.plot.style.context(font_size=10):
    ...     fig, ax = plt.subplots()
    """
    rc = {_rc_name(name): value for name, value in style_overrides.items()}
    with (
        as_file(files("hangtu").joinpath("plot/hangtu.mplstyle")) as path,
        mpl.rc_context(fname=str(path), rc=rc),
    ):
        yield


def style_axes(ax: Axes) -> None:
    """Apply the axes-level style to an Axes created outside ``context()``.

    rcParams only affect axes created while they are set, so a ``Sheet`` panel
    or a user's own ``ax=`` would miss the house grid, ticks and spines. Call
    this inside ``context()``: it reads the current rcParams, so per-call
    overrides apply too.
    """
    rc = mpl.rcParams
    ax.set_axisbelow(rc["axes.axisbelow"])
    ax.grid(
        rc["axes.grid"],
        which=rc["axes.grid.which"],
        linewidth=rc["grid.linewidth"],
        color=rc["grid.color"],
    )
    for spine in ax.spines.values():
        spine.set_linewidth(rc["axes.linewidth"])
    for axis in ("x", "y"):
        for which in ("major", "minor"):
            ax.tick_params(
                axis=axis,
                which=which,
                direction=rc[f"{axis}tick.direction"],
                width=rc[f"{axis}tick.{which}.width"],
                labelsize=rc[f"{axis}tick.labelsize"],
            )
