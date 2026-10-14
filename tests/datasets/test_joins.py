"""Depth and geology joins, against hand-calculated values (datasets.md §5.4, §6)."""

import numpy as np
import pandas as pd
import pytest

from hangtu.datasets import _joins

NA = np.nan


def _pens(*rows):
    return pd.DataFrame(rows, columns=[f"ISPT_PEN{i}" for i in range(1, 7)])


def test_mid_drive_from_increments():
    top = pd.Series([3.00, 6.00, 3.00])
    total = pd.Series([450.0, 275.0, 50.0])
    pens = _pens(
        [75, 75, 75, 75, 75, 75],  # 3.00 + 0.150 + 0.300 / 2 = 3.300
        [75, 75, 75, 50, NA, NA],  # 6.00 + 0.150 + 0.125 / 2 = 6.2125
        [50, NA, NA, NA, NA, NA],  # seating refusal: 3.00 + 0.050 = 3.050
    )
    depth, basis = _joins.spt_depth(top, total, pens)
    assert list(depth) == pytest.approx([3.300, 6.2125, 3.050])
    assert list(basis) == ["mid_drive"] * 3


@pytest.mark.parametrize(
    ("total", "expected"),
    [
        (450.0, 1.300),  # 1.00 + 0.150 + 0.300 / 2
        (300.0, 1.225),  # 1.00 + 0.150 + 0.150 / 2
        (200.0, 1.175),  # 1.00 + 0.150 + 0.050 / 2 (SPEC's old rule gave 1.050)
        (100.0, 1.100),  # seating only: 1.00 + 0.100
        (NA, 1.300),  # no total: 1.00 + 0.300
    ],
)
def test_nominal_mid_drive(total, expected):
    depth, basis = _joins.spt_depth(
        pd.Series([1.00]), pd.Series([total]), pd.DataFrame(index=[0])
    )
    assert depth.iloc[0] == pytest.approx(expected)
    assert basis.iloc[0] == "mid_drive_nominal"


def test_spt_with_no_top_has_no_depth():
    depth, basis = _joins.spt_depth(
        pd.Series([NA]), pd.Series([450.0]), pd.DataFrame(index=[0])
    )
    assert depth.isna().all() and basis.isna().all()


def test_lab_depth_fallbacks():
    depth, basis = _joins.lab_depth(
        pd.Series([1.10, NA, NA, NA]),
        pd.Series([1.00, 1.00, 3.00, NA]),
        pd.Series([1.50, 1.50, NA, NA]),
    )
    assert list(depth[:3]) == pytest.approx([1.10, 1.25, 3.00])
    assert np.isnan(depth.iloc[3])
    assert list(basis) == ["spec_depth", "sample_mid", "sample_top", None]


def test_zone_midpoint_and_a_missing_end():
    depth, basis = _joins.zone_depth(pd.Series([3.00, 3.00]), pd.Series([4.00, NA]))
    assert depth.iloc[0] == pytest.approx(3.50)
    assert np.isnan(depth.iloc[1])
    assert list(basis) == ["zone_mid", None]


def test_elevation():
    assert list(_joins.elevation(pd.Series([12.40, NA]), pd.Series([3.30, 1.0]))) == (
        pytest.approx([9.10, NA], nan_ok=True)
    )


# J1 in joins.ags: FILL 0-2, ALV 2-5, TRC 4.5-8 (overlap), gap 8-9, BED 9-10.
LAYERS = pd.DataFrame(
    {
        "location_id": [1, 1, 1, 1, 2],
        "top": [0.0, 2.0, 4.5, 9.0, 0.0],
        "base": [2.0, 5.0, 8.0, 10.0, 5.0],
    },
    index=[10, 11, 12, 13, 14],
)


@pytest.mark.parametrize(
    ("hole", "depth", "layer", "overlapping"),
    [
        (1, 1.99, 10, False),
        (1, 2.00, 11, False),  # top <= d: the boundary belongs to the lower layer
        (1, 4.80, 12, True),  # in ALV and TRC: the deepest top (4.50) wins
        (1, 5.00, 12, False),  # ALV's base, TRC only
        (1, 8.20, None, False),  # in the gap
        (1, 10.00, 13, False),  # the base of the deepest layer
        (1, 10.01, None, False),  # below the log
        (2, 5.00, 14, False),
        (3, 1.00, None, False),  # a hole with no geology
        (1, NA, None, False),  # no depth
    ],
)
def test_place_in_geology(hole, depth, layer, overlapping):
    tests = pd.DataFrame({"location_id": [hole], "depth": [depth]}, index=[7])
    found, overlap = _joins.place_in_geology(tests, LAYERS)
    assert (None if pd.isna(found.loc[7]) else found.loc[7]) == layer
    assert bool(overlap.loc[7]) is overlapping


def test_place_in_geology_keeps_the_test_index_and_order():
    tests = pd.DataFrame(
        {"location_id": [1, 2, 1], "depth": [9.5, 1.0, 0.5]}, index=[5, 3, 9]
    )
    found, _ = _joins.place_in_geology(tests, LAYERS)
    assert list(found.index) == [5, 3, 9]
    assert list(found) == [13, 14, 10]
