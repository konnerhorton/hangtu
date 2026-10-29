"""Clay clogging potential (docs/plots/P17-clogging-diagram.md §4)."""

from dataclasses import dataclass
from os import PathLike
from typing import Any, Literal

import numpy as np
import pandas as pd

from hangtu import _config, _polygons
from hangtu._data import flag_column, numeric_column
from hangtu.analysis._plasticity import _NOT_PLASTIC_HINT, plasticity
from hangtu.errors import ColumnError, HangtuError, warn

METHODS = ("thewes_burger_2004",)
KIND = _polygons.TableKind(
    argument="zones",
    item="Zone",
    axes=("plasticity_index", "consistency_index"),
    numbers=" (PI in percent, Ic dimensionless)",
    start='Start one with ht.template("clogging_zones").',
)

#: Why a row has no zone, in the order they are checked.
REASONS = (
    "non-plastic",
    "no liquid or plastic limit",
    "a plasticity index of 0",
    "no water content",
    "outside the diagram",
)


@dataclass(frozen=True)
class Zone:
    """One zone: its name, its (PI, Ic) vertices, and where its label goes."""

    name: str
    vertices: np.ndarray
    label_at: np.ndarray | None = None


@dataclass(frozen=True)
class Diagram:
    """A method's zones, lowest potential first, and the box it draws."""

    zones: tuple[Zone, ...]
    box: tuple[float, float, float, float] | None  # PI low, high; Ic low, high
    source: str | None


def method_config(method: str) -> dict[str, Any]:
    """Return a method from ``config/clogging_methods.yaml``."""
    methods = _config.load("config/clogging_methods.yaml")
    if method not in methods:
        raise HangtuError(
            f"There is no clogging method named {method!r}. Methods: "
            f'{", ".join(map(repr, methods))}. Example: method="thewes_burger_2004"'
        )
    return methods[method]


def diagram(
    method: str = "thewes_burger_2004",
    zones: pd.DataFrame | str | PathLike[str] | None = None,
) -> Diagram:
    """Return the zones to place specimens in: ``zones`` if given, else the method's.

    User zones have no box: a specimen is in one of them or in none.
    """
    if zones is not None:
        polygons = _polygons.read_polygons(zones, KIND)
        return Diagram(tuple(Zone(p.label, p.vertices) for p in polygons), None, None)
    config = method_config(method)
    axes = config["axes"]
    box = (*axes["plasticity_index"], *axes["consistency_index"])
    built = tuple(
        Zone(
            zone["name"],
            np.array(zone["vertices"], dtype=float),
            None if "label_at" not in zone else np.array(zone["label_at"], float),
        )
        for zone in config["zones"]
    )
    return Diagram(built, tuple(map(float, box)), config["source"])


def _check(df: Any) -> None:
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    if "water_content" not in df.columns and "consistency_index" not in df.columns:
        raise ColumnError(
            "df has no 'water_content' column. Ic needs the in situ water "
            "content; p.atterberg() joins it from LNMC, or give a "
            "consistency_index column. Available columns: "
            f"{', '.join(map(str, df.columns)) or 'none'}."
        )


def _place(
    df: pd.DataFrame, figure: Diagram
) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """Add PI, Ic and ``clogging_potential``; return them and the blank rows by reason.

    Each reason's mask holds only rows not already blank for an earlier one.
    """
    given = (
        numeric_column(df, "consistency_index")
        if "consistency_index" in df.columns
        else np.full(len(df), np.nan)
    )
    result = plasticity(df)
    non_plastic = np.array(
        [flag is True for flag in flag_column(df, "non_plastic", _NOT_PLASTIC_HINT)],
        dtype=bool,
    )
    index = result["plasticity_index"].to_numpy(dtype=float)
    computed = result["consistency_index"].to_numpy(dtype=float)
    usable = ~non_plastic & (index > 0)
    consistency = np.where(usable & ~np.isnan(given), given, computed)
    result["consistency_index"] = consistency

    points = np.column_stack([index, consistency])
    placed = np.isfinite(points).all(axis=1)
    if figure.box is not None:
        x0, x1, y0, y1 = figure.box
        slack = _polygons.SLACK
        placed &= (
            (index >= x0 - slack)
            & (index <= x1 + slack)
            & (consistency >= y0 - slack)
            & (consistency <= y1 + slack)
        )
    names = np.full(len(df), None, dtype=object)
    open_ = placed.copy()
    for zone in reversed(figure.zones):  # highest first: it wins a boundary
        inside = open_ & _polygons.contains(zone.vertices, points)
        names[inside] = zone.name
        open_ &= ~inside
    result["clogging_potential"] = names

    masks = {
        "non-plastic": non_plastic,
        "no liquid or plastic limit": np.isnan(index),
        "a plasticity index of 0": index == 0,
        "no water content": np.isnan(consistency),
        "outside the diagram": pd.isna(names),
    }
    blank = np.zeros(len(df), dtype=bool)
    reasons = {}
    for reason in REASONS:
        reasons[reason] = masks[reason] & ~blank
        blank |= masks[reason]
    return result, reasons


def clogging_potential(
    df: pd.DataFrame,
    *,
    method: Literal["thewes_burger_2004"] = "thewes_burger_2004",
    zones: pd.DataFrame | str | PathLike[str] | None = None,
) -> pd.DataFrame:
    r"""Add each specimen's clay clogging potential for TBM drives, from PI and Ic.

    The consistency index at in situ water content is

    $$
    I_c = \frac{LL - w}{LL - PL}
    $$

    where $LL$ and $PL$ are the liquid and plastic limits and $w$ the water
    content (all %), as ``ht.analysis.plasticity()`` gives it. The specimen
    is then placed by plasticity index $PI = LL - PL$ (%) and $I_c$ on the
    chart of Thewes & Burger (2004), which is drawn over PI 0 to 70 and $I_c$
    0.3 to 1.5:

    | Zone | PI (%) | $I_c$ |
    |---|---|---|
    | high | 20 to 70 | 0.75 to 1.3 |
    | medium-high | 20 to 70 | 1.3 to 1.5 |
    | medium | 10 to 70 | 0.6 to 1.5, around high and medium-high |
    | low | 0 to 70 | 0.3 to 1.5, the rest |

    A point on a boundary between two zones takes the higher potential, so a
    borderline specimen is never reported as the safer one; a point on the
    diagram's edge is in it. Source: Thewes, M. & Burger, W. (2004), Clogging
    risks for TBM drives in clay, *Tunnels & Tunnelling International* 36(6),
    28-31.

    **Validity:** a screen on index properties only. Mineralogy, the machine,
    the cutterhead design and conditioning are outside it. A specimen beyond
    the drawn axes (Ic below 0.3, often below 0 in soft clays; Ic above 1.5;
    PI above 70) is outside the diagram, not given the nearest zone, since
    the source doesn't show what lies there.

    **Blank ``clogging_potential``, with one warning counting the rows by
    reason:** non-plastic, no liquid or plastic limit, a PI of 0 (Ic is
    undefined), no water content, and outside the diagram.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per specimen, as ``p.atterberg()`` or
        ``ht.template("atterberg")``: ``liquid_limit``, ``plastic_limit`` or
        ``plasticity_index``, and ``water_content``, in percent. A
        ``consistency_index`` given is kept where it isn't blank, so a table
        with Ic but no water content works too. ``non_plastic`` marks NP
        specimens.
    method : {"thewes_burger_2004"}
        The diagram, from ``config/clogging_methods.yaml``.
    zones : DataFrame or str, optional
        Your own zones instead of the method's, e.g. a variant from another
        source: a table or CSV path with one row per vertex, in order around
        each polygon (``ht.template("clogging_zones")``), zones listed from
        the lowest potential to the highest. With ``zones``, there are no
        axes: a specimen in none of the zones is outside the diagram.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``plasticity_index``, ``consistency_index`` and
        the other columns of ``plasticity()``, and ``clogging_potential``:
        the zone's name, or blank. No row is dropped or reordered.

    Raises
    ------
    HangtuError
        For an unknown method, a bad ``zones`` table, no ``water_content``
        (or ``consistency_index``) column, or the errors of ``plasticity()``.

    Examples
    --------
    >>> limits = p.atterberg()
    >>> table = ht.analysis.clogging_potential(limits)
    >>> table.groupby("geology_unit")["clogging_potential"].value_counts()
    """
    _check(df)
    if method not in METHODS:
        method_config(method)  # raises, listing the methods
    result, reasons = _place(df, diagram(method, zones))
    counted = [
        f"{int(mask.sum())} {reason}" for reason, mask in reasons.items() if mask.any()
    ]
    if counted:
        warn(
            f"clogging_potential is blank for rows: {'; '.join(counted)}. A zone "
            "needs a plastic specimen with LL, PL and water content, inside the "
            "diagram."
        )
    return result
