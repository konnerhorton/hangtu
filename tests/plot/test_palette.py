import numpy as np
import pytest
from matplotlib.colors import to_rgba

import ags_kit as ak
from ags_kit.plot._palette import AUTOMATIC
from ags_kit.plot.common import resolve_palette


def test_automatic_colors_use_dark_tab20_shades_first():
    assert AUTOMATIC[0] == pytest.approx(to_rgba("tab:blue")[:3])
    assert AUTOMATIC[1] == pytest.approx(to_rgba("tab:orange")[:3])
    assert len(AUTOMATIC) == 20 == len(set(AUTOMATIC))


def test_units_are_colored_by_name_without_an_order():
    colors = resolve_palette(["Till", "Alluvium", np.nan, "Till"])
    assert list(colors) == ["Alluvium", "Till"]
    assert colors == {"Alluvium": AUTOMATIC[0], "Till": AUTOMATIC[1]}


def test_stratigraphic_order_is_respected():
    colors = resolve_palette(
        ["Alluvium", "Bedrock", "Till", "Fill"], order=["Fill", "Alluvium", "Till"]
    )
    assert list(colors) == ["Fill", "Alluvium", "Till", "Bedrock"]
    assert colors["Fill"] == AUTOMATIC[0]
    assert colors["Bedrock"] == AUTOMATIC[3]


def test_a_unit_keeps_its_color_in_a_later_plot():
    first = resolve_palette(["Till", "Alluvium"])
    second = resolve_palette(["Fill", "Till"])
    assert second["Till"] == first["Till"]
    assert second["Fill"] == AUTOMATIC[2]


def test_reset_palette_forgets_assignments():
    resolve_palette(["Till", "Alluvium"])
    ak.plot.reset_palette()
    assert resolve_palette(["Till"]) == {"Till": AUTOMATIC[0]}


def test_argument_beats_settings_beats_automatic():
    ak.settings.palette = {"Till": "gray", "Fill": "black"}
    colors = resolve_palette(["Till", "Fill", "Alluvium"], palette={"Till": "tan"})
    assert colors == {"Alluvium": AUTOMATIC[0], "Fill": "black", "Till": "tan"}


def test_invalid_palette_argument_raises():
    with pytest.raises(ak.AgsKitError, match=r"\['Till'\]"):
        resolve_palette(["Till"], palette={"Till": "not a color"})


def test_more_than_20_units_repeat_colors_with_a_warning():
    units = [f"Unit {i:02d}" for i in range(21)]
    with pytest.warns(UserWarning, match="More than 20 geology units") as record:
        colors = resolve_palette(units)
    assert len(record) == 1
    assert colors["Unit 20"] == colors["Unit 00"]


def test_palette_cmap_follows_the_given_order():
    cmap = ak.plot.palette_cmap(["Till", "Alluvium"])
    assert cmap.N == 2
    assert [tuple(c) for c in cmap.colors] == [AUTOMATIC[0], AUTOMATIC[1]]


def test_palette_cmap_without_units_uses_every_colored_unit():
    ak.settings.palette = {"Fill": "black"}
    resolve_palette(["Till"])
    assert list(ak.plot.palette_cmap().colors) == ["black", AUTOMATIC[0]]


def test_legend_handles():
    handles = ak.plot.legend_handles(["Till", "Fill"])
    assert [h.get_label() for h in handles] == ["Till", "Fill"]
    assert handles[0].get_facecolor() == to_rgba(AUTOMATIC[0])


@pytest.mark.parametrize("call", [ak.plot.palette_cmap, ak.plot.legend_handles])
def test_nothing_colored_yet_raises(call):
    with pytest.raises(ak.AgsKitError, match="No geology units have colors yet"):
        call()
