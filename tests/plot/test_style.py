import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

import hangtu as ak
from hangtu.plot import style


def snapshot():
    return dict(mpl.rcParams)


def test_house_style_applies_inside_the_block():
    with style.context():
        assert mpl.rcParams["font.size"] == 9
        assert mpl.rcParams["xtick.labelsize"] == 8
        assert mpl.rcParams["axes.titlesize"] == 10
        assert mpl.rcParams["xtick.direction"] == "in"
        assert mpl.rcParams["axes.grid"] is True
        assert mpl.rcParams["grid.linewidth"] == 0.5
        assert mpl.rcParams["axes.linewidth"] == 0.6
        assert mpl.rcParams["savefig.dpi"] == 300
        assert mpl.rcParams["font.sans-serif"][:3] == [
            "Arial",
            "Helvetica",
            "DejaVu Sans",
        ]


def test_rcparams_are_unchanged_after_the_block():
    before = snapshot()
    with style.context(font_size=12):
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        fig.canvas.draw()
    assert snapshot() == before


def test_rcparams_are_unchanged_when_the_block_raises():
    before = snapshot()
    with pytest.raises(RuntimeError), style.context(**{"lines.linewidth": 3}):
        raise RuntimeError
    assert snapshot() == before


@pytest.mark.parametrize(
    "overrides",
    [{"font.size": 12}, {"font_size": 12}],
    ids=["dotted", "underscored"],
)
def test_overrides_apply_inside_the_block(overrides):
    with style.context(**overrides):
        assert mpl.rcParams["font.size"] == 12


def test_hyphenated_names_have_an_underscore_form():
    with style.context(font_sans_serif=["DejaVu Sans"]):
        assert mpl.rcParams["font.sans-serif"] == ["DejaVu Sans"]


def test_unknown_override_raises_with_a_suggestion():
    with (
        pytest.raises(ak.AgsKitError, match="Did you mean 'font_size'"),
        style.context(font_sise=12),
    ):
        pass


def test_style_axes_styles_axes_made_outside_the_context():
    _, ax = plt.subplots()  # global rcParams: no grid, ticks out
    with style.context(xtick_labelsize=6):
        style.style_axes(ax)
    gridline = ax.xaxis.get_gridlines()[0]
    assert gridline.get_visible()
    assert gridline.get_linewidth() == 0.5
    assert ax.spines["left"].get_linewidth() == 0.6
    tick = ax.xaxis.get_major_ticks()[0]
    assert tick._tickdir == "in"
    assert tick.label1.get_fontsize() == 6
