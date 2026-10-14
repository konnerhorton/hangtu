"""Depth and geology joins (SPEC §8, datasets.md §5.4 and §6).

Everything here is in SI (depths in m, penetrations in mm) and takes plain
Series and DataFrames, so the hand-calculated cases can test each rule alone.
"""

import numpy as np
import pandas as pd

#: Nominal SPT drives in mm, used when the increments aren't given (§6.1).
NOMINAL_SEATING = 150.0
NOMINAL_DEPTH = 300.0  # seating + half of a full 300 mm test drive


def spt_depth(
    top: pd.Series, total: pd.Series, penetrations: pd.DataFrame
) -> tuple[pd.Series, pd.Series]:
    """Return each SPT's mid-drive depth (m) and its ``depth_basis``.

    Parameters
    ----------
    top
        ``ISPT_TOP`` in m.
    total
        ``ISPT_NPEN``, seating plus test penetration, in mm.
    penetrations
        ``ISPT_PEN1`` to ``ISPT_PEN6`` in mm, in that order. Absent headings
        are absent columns.

    Notes
    -----
    - ``mid_drive`` where ``ISPT_PEN1`` is given: top + seating + test / 2,
      with seating = PEN1 + PEN2 and test = PEN3 + ... + PEN6; a blank
      increment after the last one counts as 0 (the drive stopped).
    - ``mid_drive_nominal`` otherwise: a 150 mm seating drive and the rest of
      ``total`` as the test drive; top + 300 mm with no total either.
    """
    pens = penetrations.reindex(columns=[f"ISPT_PEN{i}" for i in range(1, 7)]).set_axis(
        range(1, 7), axis=1
    )
    pens.index = top.index
    with_increments = pens[1].notna()
    seating = pens[[1, 2]].sum(axis=1, min_count=0)
    test = pens[[3, 4, 5, 6]].sum(axis=1, min_count=0)
    measured = seating + test / 2

    nominal_seating = total.clip(upper=NOMINAL_SEATING)
    nominal_test = (total - NOMINAL_SEATING).clip(lower=0)
    nominal = (nominal_seating + nominal_test / 2).fillna(NOMINAL_DEPTH)

    below_top = measured.where(with_increments, nominal)
    depth = top + below_top / 1000
    basis = pd.Series(
        np.where(with_increments, "mid_drive", "mid_drive_nominal"),
        index=top.index,
        dtype=object,
    )
    return depth, basis.where(top.notna(), None)


def lab_depth(
    specimen_depth: pd.Series, sample_top: pd.Series, sample_base: pd.Series
) -> tuple[pd.Series, pd.Series]:
    """Return each lab result's depth (m) and ``depth_basis`` (SPEC §8.2).

    Specimen depth (``spec_depth``), else the sample's midpoint
    (``sample_mid``), else the sample's top (``sample_top``).
    """
    middle = (sample_top + sample_base) / 2
    depth = specimen_depth.where(
        specimen_depth.notna(), middle.where(middle.notna(), sample_top)
    )
    basis = pd.Series(
        np.select(
            [specimen_depth.notna(), middle.notna(), sample_top.notna()],
            ["spec_depth", "sample_mid", "sample_top"],
            default=None,
        ),
        index=specimen_depth.index,
        dtype=object,
    )
    return depth, basis


def zone_depth(top: pd.Series, base: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Return the midpoint of a test zone (``zone_mid``); blank if an end is."""
    depth = (top + base) / 2
    basis = pd.Series("zone_mid", index=top.index, dtype=object)
    return depth, basis.where(depth.notna(), None)


def elevation(ground_level: pd.Series, depth: pd.Series) -> pd.Series:
    """``ground_level - depth`` (SPEC §8.1); blank where either is."""
    return ground_level - depth


def place_in_geology(
    tests: pd.DataFrame, layers: pd.DataFrame
) -> tuple[pd.Series, pd.Series]:
    """Find the geology layer each test is in (SPEC §8.3, datasets.md §5.4).

    Parameters
    ----------
    tests
        ``location_id`` and ``depth`` (m), one row per test.
    layers
        ``location_id``, ``top`` and ``base`` (m), one row per GEOL layer. The
        index identifies the layer in the result.

    Returns
    -------
    layer, overlapping
        The index of each test's layer (NA where it is in none), and True
        where the test is in more than one layer, so the deepest top was
        chosen.

    Notes
    -----
    A test is in a layer when ``top ≤ depth < base``, or when its depth equals
    the base of its hole's deepest layer. Where layers overlap, the one with
    the deepest top wins ("lowest top"); between equal tops, the later one.
    """
    layers = layers.dropna(subset=["location_id", "top", "base"])
    bottom = layers.groupby("location_id")["base"].transform("max")
    candidates = (
        tests[["location_id", "depth"]]
        .reset_index(drop=True)
        .reset_index(names="_test")
        .merge(
            layers.assign(_bottom=bottom).reset_index(names="_layer"),
            on="location_id",
        )
    )
    depth = candidates["depth"]
    inside = (candidates["top"] <= depth) & (
        (depth < candidates["base"])
        | (
            (depth == candidates["base"])
            & (candidates["base"] == candidates["_bottom"])
        )
    )
    hits = candidates[inside].sort_values(["_test", "top", "_layer"], kind="stable")
    counts = hits.groupby("_test").size()
    chosen = hits.groupby("_test")["_layer"].last()
    layer = chosen.reindex(range(len(tests))).set_axis(tests.index)
    overlapping = (counts.reindex(range(len(tests))).fillna(0) > 1).set_axis(
        tests.index
    )
    return layer.astype("Int64"), overlapping
