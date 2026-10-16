"""User regions on the plasticity chart (P04 §8)."""

import numpy as np
import pandas as pd
import pytest
from matplotlib.colors import to_rgba

import hangtu as ht
from hangtu.errors import HangtuError

EMPTY = pd.DataFrame()

# A non-rectangular five-vertex region (a "house"): a 20 x 10 box from
# (30, 10) with a roof peak at (40, 30). Area 200 + 100 = 300. Centroid y:
# (200 x 15 + 100 x (20 + 10/3)) / 300 = 17.78; x is 40 by symmetry.
HOUSE = pd.DataFrame(
    {
        "label": ["Group 1"] * 5,
        "liquid_limit": [30.0, 50.0, 50.0, 40.0, 30.0],
        "plasticity_index": [10.0, 10.0, 20.0, 30.0, 20.0],
    }
)
HOUSE_CENTROID = (40.0, (200 * 15 + 100 * (20 + 10 / 3)) / 300)
TRIANGLE = pd.DataFrame(
    {
        "label": ["Group 2"] * 3,
        "liquid_limit": [60.0, 80.0, 70.0],
        "plasticity_index": [20.0, 20.0, 35.0],
    }
)


def region_patches(ax):
    return [p for p in ax.patches if p.get_gid() == "region"]


def region_labels(ax):
    return {
        t.get_text(): t.get_position()
        for t in ax.texts
        if t.get_gid() == "region_label"
    }


def test_template_columns():
    assert list(ht.template("plasticity_regions").columns) == [
        "label",
        "liquid_limit",
        "plasticity_index",
    ]


def test_five_vertex_region_drawn_closed_with_label_at_centroid():
    _, ax = ht.plot.plasticity_chart(EMPTY, regions=HOUSE)
    (patch,) = region_patches(ax)
    xy = patch.get_xy()
    np.testing.assert_allclose(xy[0], xy[-1])  # closed
    np.testing.assert_allclose(xy[:-1], HOUSE[["liquid_limit", "plasticity_index"]])
    np.testing.assert_allclose(region_labels(ax)["Group 1"], HOUSE_CENTROID)
    assert patch.get_facecolor() == pytest.approx(to_rgba("0.5", 0.12))
    assert patch.get_edgecolor() == pytest.approx(to_rgba("0.5"))
    assert patch.get_linewidth() == 1.0


def test_region_from_a_csv_path(tmp_path):
    path = tmp_path / "groups.csv"
    HOUSE.to_csv(path, index=False)
    for given in (path, str(path)):
        _, ax = ht.plot.plasticity_chart(EMPTY, regions=given)
        assert len(region_patches(ax)) == 1
        np.testing.assert_allclose(region_labels(ax)["Group 1"], HOUSE_CENTROID)


def test_two_regions_and_a_color():
    regions = pd.concat([HOUSE, TRIANGLE], ignore_index=True)
    _, ax = ht.plot.plasticity_chart(
        EMPTY, regions=regions, region_colors={"Group 2": "tan"}
    )
    first, second = region_patches(ax)
    assert first.get_edgecolor() == pytest.approx(to_rgba("0.5"))
    assert second.get_edgecolor() == pytest.approx(to_rgba("tan"))
    np.testing.assert_allclose(region_labels(ax)["Group 2"], (70, 25))


def test_regions_sit_below_the_chart_lines():
    _, ax = ht.plot.plasticity_chart(EMPTY, regions=HOUSE)
    (patch,) = region_patches(ax)
    assert patch.get_zorder() < min(line.get_zorder() for line in ax.lines)


def test_too_few_vertices_is_an_error():
    with pytest.raises(HangtuError, match="'Group 1' has 2 vertices"):
        ht.plot.plasticity_chart(EMPTY, regions=HOUSE.iloc[:2])


def test_blank_label_is_an_error():
    regions = HOUSE.copy()
    regions.loc[3, "label"] = None
    with pytest.raises(HangtuError, match=r"Rows 3 .* no label"):
        ht.plot.plasticity_chart(EMPTY, regions=regions)


def test_missing_label_column_is_an_error():
    with pytest.raises(ht.ColumnError, match="no 'label' column"):
        ht.plot.plasticity_chart(EMPTY, regions=HOUSE.drop(columns="label"))


@pytest.mark.parametrize("value", [None, "high"])
def test_blank_or_text_vertex_is_an_error(value):
    regions = HOUSE.astype({"plasticity_index": object})
    regions.loc[2, "plasticity_index"] = value
    with pytest.raises(HangtuError, match="'Group 1' has a blank or non-numeric"):
        ht.plot.plasticity_chart(EMPTY, regions=regions)


def test_regions_of_the_wrong_type_is_an_error():
    with pytest.raises(HangtuError, match="regions must be a DataFrame"):
        ht.plot.plasticity_chart(EMPTY, regions=[(30, 10), (50, 10), (40, 30)])


def test_unknown_region_color_warns():
    with pytest.warns(UserWarning, match="'Group 9', which is not in"):
        ht.plot.plasticity_chart(EMPTY, regions=HOUSE, region_colors={"Group 9": "red"})


def test_bad_region_color_is_an_error():
    with pytest.raises(HangtuError, match="doesn't recognize"):
        ht.plot.plasticity_chart(
            EMPTY, regions=HOUSE, region_colors={"Group 1": "not a color"}
        )
