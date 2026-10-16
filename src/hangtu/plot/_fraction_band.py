"""The grain size plot's fraction band, dividers and sieve labels (P05 §8).

The band and the dividers read the same fraction system as
``ht.analysis.gradation(fractions=)``, so they can't disagree with it.
"""

import math
from numbers import Real
from typing import Any

from matplotlib.axes import Axes
from matplotlib.markers import TICKDOWN
from mpl_toolkits.axes_grid1 import make_axes_locatable

from hangtu import _config
from hangtu.errors import HangtuError
from hangtu.plot import _layers

HEADER_HEIGHT = 0.45  # inches
MIN_NAME_DECADES = 0.25  # a name narrower than this in view is left out
NAME_SIZE = 7
PART_SIZE = 6.5
BAND_COLOR = "0.2"  # the band's cell borders
BAND_WIDTH = 0.6
FRACTION_DIVIDER = {"color": "0.55", "linewidth": 0.6}
PART_DIVIDER = {"color": "0.75", "linewidth": 0.4, "linestyle": "--"}
SIEVE_SIZE = 6.5
SIEVE_TICK = 4.0  # points
SIEVE_COLOR = "0.3"

Fraction = dict[str, Any]


def add_header(ax: Axes) -> Axes:
    """Carve the band's axes from the top of ``ax``, sharing its x axis."""
    header = make_axes_locatable(ax).append_axes(
        "top", size=HEADER_HEIGHT, pad=0, sharex=ax
    )
    header.set_ylim(0, 1)
    header.set_yticks([])
    header.grid(False, which="both")
    header.tick_params(
        axis="x",
        which="both",
        bottom=False,
        top=False,
        labelbottom=False,
        labeltop=False,
    )
    for spine in header.spines.values():
        spine.set_linewidth(BAND_WIDTH)
    return header


def fraction_label(name: str) -> str:
    """Return a fraction or part name as text: ``silt_clay`` -> ``Silt clay``."""
    text = name.replace("_", " ")
    return text[:1].upper() + text[1:]


def boundaries(fractions: list[Fraction]) -> tuple[list[float], list[float]]:
    """Return the fraction boundaries and the part boundaries inside them, in mm."""
    between = [float(f["lower"]) for f in fractions if f["lower"] > 0]
    parts = [
        float(part["upper"])
        for fraction in fractions
        for part in (fraction.get("parts") or [])[:-1]
    ]
    return between, parts


def _visible(
    lower: float, upper: float | None, limits: tuple[float, float]
) -> tuple[float, float] | None:
    """Return the part of ``lower`` to ``upper`` inside ``limits``, or None."""
    lo = max(lower, limits[0])
    hi = min(math.inf if upper is None else upper, limits[1])
    return (lo, hi) if hi > lo else None


def _name(header: Axes, span: tuple[float, float], y: float, text: str, **kw) -> None:
    lo, hi = span
    if math.log10(hi / lo) < MIN_NAME_DECADES:
        return
    header.text(
        math.sqrt(lo * hi), y, text, ha="center", va="center", clip_on=True, **kw
    )


def draw_band(
    header: Axes, ax: Axes, fractions: list[Fraction], limits: tuple[float, float]
) -> None:
    """Name the fractions and their parts, and draw the dividers (P05 §8).

    Fraction names fill the upper row and parts the lower one; a fraction
    without parts spans both, and a system without parts has one row.
    """
    limits = (min(limits), max(limits))
    two_rows = any(fraction.get("parts") for fraction in fractions)
    for fraction in fractions:
        span = _visible(fraction["lower"], fraction["upper"], limits)
        if span is None:
            continue
        parts = fraction.get("parts") or []
        y = 0.75 if parts else 0.5
        _name(
            header,
            span,
            y,
            fraction_label(fraction["name"]),
            fontsize=NAME_SIZE,
            gid="fraction_name",
        )
        if not parts:
            continue
        header.plot(
            span,
            [0.5, 0.5],
            color=BAND_COLOR,
            linewidth=BAND_WIDTH,
            gid="band_rule",
        )
        previous = fraction["lower"]
        for part in parts:
            part_span = _visible(previous, part["upper"], limits)
            previous = part["upper"]
            if part_span is not None:
                _name(
                    header,
                    part_span,
                    0.25,
                    fraction_label(part["name"]),
                    fontsize=PART_SIZE,
                    gid="part_name",
                )
    between, parts = boundaries(fractions)
    for size in between:
        if limits[0] < size < limits[1]:
            header.axvline(size, color=BAND_COLOR, linewidth=BAND_WIDTH, gid="band")
            ax.axvline(
                size,
                gid="fraction_divider",
                zorder=_layers.DIVIDERS,
                **FRACTION_DIVIDER,
            )
    for size in parts:
        if limits[0] < size < limits[1]:
            header.axvline(
                size,
                ymax=0.5 if two_rows else 1.0,
                color=BAND_COLOR,
                linewidth=BAND_WIDTH,
                gid="band",
            )
            ax.axvline(
                size, gid="part_divider", zorder=_layers.DIVIDERS, **PART_DIVIDER
            )


def _bad_sieves(sieves: Any) -> HangtuError:
    return HangtuError(
        f'sieves must be "auto", "us", "iso", None or a list of (size in mm, '
        f'label) pairs, not {sieves!r}. Example: sieves=[(4.75, "#4"), '
        '(0.075, "#200")]'
    )


def sieve_list(sieves: Any, display_units: str) -> list[tuple[float, str]]:
    """Resolve ``sieves=`` to ``(size in mm, label)`` pairs."""
    if sieves is None:
        return []
    builtin = _config.load("config/sieves.yaml")
    if isinstance(sieves, str):
        if sieves == "auto":
            sieves = "us" if display_units == "US" else "iso"
        if sieves not in builtin:
            raise _bad_sieves(sieves)
        return [(float(size), str(label)) for size, label in builtin[sieves]["sieves"]]
    if not isinstance(sieves, list | tuple):
        raise _bad_sieves(sieves)
    result = []
    for pair in sieves:
        if (
            not isinstance(pair, list | tuple)
            or len(pair) != 2
            or not isinstance(pair[0], Real)
            or isinstance(pair[0], bool)
            or not pair[0] > 0
            or not isinstance(pair[1], str)
        ):
            raise _bad_sieves(sieves)
        result.append((float(pair[0]), pair[1]))
    return result


def draw_sieves(
    ax: Axes, sieves: list[tuple[float, str]], limits: tuple[float, float]
) -> None:
    """Write each sieve's label just inside the top of ``ax``, under a short tick."""
    lo, hi = min(limits), max(limits)
    for size, label in sieves:
        if not lo < size < hi:
            continue
        ax.plot(
            [size],
            [1.0],
            marker=TICKDOWN,
            markersize=SIEVE_TICK,
            markeredgewidth=0.6,
            color=SIEVE_COLOR,
            transform=ax.get_xaxis_transform(),
            clip_on=False,
            gid="sieve_tick",
            zorder=_layers.ANNOTATIONS,
        )
        ax.annotate(
            label,
            xy=(size, 1.0),
            xycoords=("data", "axes fraction"),
            xytext=(0, -SIEVE_TICK - 1),
            textcoords="offset points",
            rotation=90,
            ha="center",
            va="top",
            fontsize=SIEVE_SIZE,
            color=SIEVE_COLOR,
            gid="sieve_label",
            zorder=_layers.ANNOTATIONS,
        )
