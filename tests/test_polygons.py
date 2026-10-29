"""Polygon tables and point-in-polygon (src/hangtu/_polygons.py)."""

import numpy as np
import pandas as pd
import pytest

from hangtu import _polygons
from hangtu.errors import HangtuError

# An L: the 2 x 2 square from the origin with its upper-right 1 x 1 cut out.
# Area 3, in two pieces: the bottom 2 x 1 (area 2, centroid (1, 0.5)) and the
# upper left 1 x 1 (area 1, centroid (0.5, 1.5)). Centroid:
# ((2 x 1 + 0.5) / 3, (2 x 0.5 + 1.5) / 3) = (2.5 / 3, 2.5 / 3).
L_SHAPE = np.array([(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2)], dtype=float)
KIND = _polygons.TableKind(
    argument="zones",
    item="Zone",
    axes=("x", "y"),
    numbers="",
    start="Start one with a template.",
)


def test_inside_and_outside_a_nonconvex_polygon():
    points = [(0.5, 0.5), (1.5, 0.5), (0.5, 1.5), (1.5, 1.5), (3, 3), (-1, 0.5)]
    np.testing.assert_array_equal(
        _polygons.contains(L_SHAPE, points),
        [True, True, True, False, False, False],
    )


def test_edges_and_vertices_are_inside():
    points = [(1, 0), (2, 0.5), (1.5, 1), (1, 1.5), (0, 2), (1, 1), (0, 0)]
    assert _polygons.contains(L_SHAPE, points).all()


def test_edge_tolerance():
    near, far = 1 + 0.5e-9, 1 + 1e-6
    assert _polygons.contains(L_SHAPE, [(1.5, near)])[0]
    assert not _polygons.contains(L_SHAPE, [(1.5, far)])[0]


def test_nan_points_are_outside():
    assert not _polygons.contains(L_SHAPE, [(np.nan, 0.5), (0.5, np.nan)]).any()


def test_centroid_of_an_l():
    polygon = _polygons.Polygon("L", L_SHAPE)
    np.testing.assert_allclose(polygon.centroid(), (2.5 / 3, 2.5 / 3))


def test_read_polygons_groups_by_label_in_table_order():
    table = pd.DataFrame(
        {
            "label": ["b"] * 3 + ["a"] * 3,
            "x": [0, 1, 0, 5, 6, 5],
            "y": [0, 0, 1, 5, 5, 6],
        }
    )
    polygons = _polygons.read_polygons(table, KIND)
    assert [p.label for p in polygons] == ["b", "a"]
    np.testing.assert_array_equal(polygons[1].vertices, [(5, 5), (6, 5), (5, 6)])


def test_messages_use_the_table_kind():
    table = pd.DataFrame({"label": ["high"] * 2, "x": [0, 1], "y": [0, 1]})
    with pytest.raises(HangtuError, match="Zone 'high' has 2 vertices"):
        _polygons.read_polygons(table, KIND)
    with pytest.raises(HangtuError, match="zones must be a DataFrame"):
        _polygons.read_polygons([(0, 0)], KIND)
