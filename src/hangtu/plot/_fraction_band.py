"""The grain size plot's fraction band, dividers and sieve strip (P05 §8).

The band and the dividers read the same fraction system as
``ht.analysis.gradation(fractions=)``, so they can't disagree with it.
"""

import math
from itertools import pairwise
from numbers import Real
from typing import Any

from matplotlib.axes import Axes
from matplotlib.markers import TICKUP
from matplotlib.transforms import blended_transform_factory
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.axes_grid1.axes_divider import AxesDivider

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
SIEVE_TICK = 3.0  # points, up from the frame
SIEVE_PAD = 0.05  # inches between the frame and the first row of labels
SIEVE_ROW = 0.12  # inches per row of labels
CROWDED_DECADES = 0.25  # neighbors closer than this put the labels on two rows
SIEVE_COLOR = "0.3"

Fraction = dict[str, Any]


def _divider(ax: Axes) -> AxesDivider:
    """Return ``ax``'s divider, made once, so the strip and the band stack."""
    divider = getattr(ax, "_grain_size_divider", None)
    if divider is None:
        divider = ax._grain_size_divider = make_axes_locatable(ax)
    return divider


def add_header(ax: Axes) -> Axes:
    """Carve the band's axes from the top of ``ax``, sharing its x axis."""
    header = _divider(ax).append_axes("top", size=HEADER_HEIGHT, pad=0, sharex=ax)
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


def sieve_rows(sizes: list[float]) -> list[int]:
    """Return each sieve's label row: 0, or alternating 0 and 1 when crowded.

    Labels alternate between two rows, in size order, when any two neighbors
    are closer than ``CROWDED_DECADES``, so horizontal labels don't overlap.
    """
    order = sorted(range(len(sizes)), key=sizes.__getitem__)
    gaps = [math.log10(sizes[b] / sizes[a]) for a, b in pairwise(order)]
    rows = [0] * len(sizes)
    if any(gap < CROWDED_DECADES for gap in gaps):
        for position, i in enumerate(order):
            rows[i] = position % 2
    return rows


def add_sieve_strip(
    ax: Axes, sieves: list[tuple[float, str]], limits: tuple[float, float]
) -> Axes | None:
    """Label the sieves in a strip carved from the top of ``ax`` (P05 §8).

    Each sieve gets a short tick up from the frame and a horizontal label
    above it. Returns the strip, or None when no sieve is inside ``limits``.
    Call before ``add_header``, so the strip sits between the frame and the
    band.
    """
    lo, hi = min(limits), max(limits)
    inside = [(size, label) for size, label in sieves if lo < size < hi]
    if not inside:
        return None
    rows = sieve_rows([size for size, _ in inside])
    height = SIEVE_PAD + (max(rows) + 1) * SIEVE_ROW
    strip = _divider(ax).append_axes("top", size=height, pad=0, sharex=ax)
    strip.set_axis_off()
    strip.set_ylim(0, 1)
    on_strip = blended_transform_factory(strip.transData, strip.transAxes)
    for (size, label), row in zip(inside, rows, strict=True):
        ax.plot(
            [size],
            [1.0],
            marker=TICKUP,
            markersize=SIEVE_TICK,
            markeredgewidth=0.6,
            color=SIEVE_COLOR,
            transform=ax.get_xaxis_transform(),
            clip_on=False,
            gid="sieve_tick",
            zorder=_layers.ANNOTATIONS,
        )
        strip.text(
            size,
            (SIEVE_PAD + (row + 0.5) * SIEVE_ROW) / height,
            label,
            transform=on_strip,
            ha="center",
            va="center",
            fontsize=SIEVE_SIZE,
            color=SIEVE_COLOR,
            gid="sieve_label",
        )
    return strip
