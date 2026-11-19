"""P13 consolidation curve (docs/plots/P13-consolidation-curve.md, AC 1-4, 6, 7, 9).

Golden values are the M19 (b) spec's (docs/work/m19b-compressibility.md, AC
1-11), hand-calculated there. Positions are read from the drawn artists.
"""

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.colors import to_hex

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError

AGS = Path(__file__).parents[1] / "data" / "ags"
REL = 1e-9

#: BH1-U3 (site_si.ags), in file order: loading, an unload-reload loop, a
#: last load and a second unload.
BH1_U3 = [
    (25, 0.795),
    (50, 0.788),
    (100, 0.776),
    (200, 0.748),
    (400, 0.690),
    (800, 0.612),
    (200, 0.625),
    (50, 0.638),
    (200, 0.630),
    (800, 0.608),
    (1600, 0.520),
    (400, 0.538),
]
#: The spec's AC 8: a straight e-log line, and an unload.
STRAIGHT = [
    *zip(
        [10 * 2**i for i in range(8)],
        [1.200, 1.125, 1.049, 0.974, 0.899, 0.824, 0.748, 0.673],
        strict=True,
    ),
    (320, 0.690),
]


@pytest.fixture(autouse=True)
def _no_hints():
    ht.settings.hints = False


@pytest.fixture(scope="module")
def site_si(tmp_path_factory):
    return ht.Project.from_ags(
        AGS / "site_si.ags",
        db=tmp_path_factory.mktemp("site_si") / "site_si.sqlite",
        overwrite=True,
        display_units="SI",
    ).oedometer()


def _frame(points, specimen="S1", **columns):
    """Increments ``(σ′v, e)`` of one specimen in kPa, in test order."""
    stress, void_ratio = (
        np.array(values, dtype=float) for values in zip(*points, strict=True)
    )
    df = pd.DataFrame(
        {
            "specimen_id": [specimen] * len(stress),
            "applied_vertical_stress": stress,
            "void_ratio_at_increment_end": void_ratio,
            **columns,
        }
    )
    df.attrs["units"] = {
        "applied_vertical_stress": "kPa",
        "effective_vertical_stress": "kPa",
    }
    return df


def _draw(df, **kwargs):
    kwargs.setdefault("display_units", "SI")
    return ht.plot.consolidation_curve(df, **kwargs)


def _lines(ax, gid):
    return [line for line in ax.lines if line.get_gid() == gid]


def _xy(line):
    return list(
        zip(
            (float(x) for x in line.get_xdata()),
            (float(y) for y in line.get_ydata()),
            strict=True,
        )
    )


def _log_line(line):
    """Return (e at σ′v = 1, slope per log cycle) of a two-point line."""
    (x0, y0), (x1, y1) = _xy(line)
    slope = (y1 - y0) / (math.log10(x1) - math.log10(x0))
    return y0 - slope * math.log10(x0), slope


def _box(ax):
    """Return the result box's text, its wrapped lines joined by single spaces."""
    box = next(text for text in ax.texts if text.get_gid() == "result_box")
    return " ".join(box.get_text().split())


def _footnote(ax):
    return "\n".join(
        text.get_text() for text in ax.texts if text.get_gid() != "result_box"
    )


@pytest.fixture
def bh1(site_si):
    yield _draw(site_si)
    plt.close("all")


def test_points_by_branch(bh1):
    """AC 1: 7 loading points (1600 kPa a diamond), 3 unloading, 2 reloading."""
    _, ax, _ = bh1
    (loading,) = _lines(ax, "loading_point")
    (after,) = _lines(ax, "loading_after_reload_point")
    (unloading,) = _lines(ax, "unloading_point")
    (reloading,) = _lines(ax, "reloading_point")
    assert _xy(loading) == [BH1_U3[i] for i in range(6)]
    assert _xy(after) == [(1600, 0.520)]
    assert _xy(unloading) == [(200, 0.625), (50, 0.638), (400, 0.538)]
    assert _xy(reloading) == [(200, 0.630), (800, 0.608)]
    assert loading.get_marker() == "o" and after.get_marker() == "D"
    assert unloading.get_markerfacecolor() == "white"
    assert reloading.get_marker() == "D"
    assert reloading.get_markerfacecolor() == "white"
    (curve,) = _lines(ax, "loading_curve")
    assert _xy(curve) == [*(BH1_U3[i] for i in range(6)), (1600, 0.520)]
    assert curve.get_marker() in ("None", None, "")


def test_index_lines(bh1):
    """AC 2: Cc through e = 1.42706111 at 1 kPa, slope -0.282363888, solid 400-1600."""
    _, ax, fit = bh1
    (solid,) = _lines(ax, "compression_index")
    intercept, slope = _log_line(solid)
    assert intercept == pytest.approx(1.42706111, rel=1e-8)
    assert slope == pytest.approx(-0.282363888, rel=1e-8)
    assert [x for x, _ in _xy(solid)] == [400, 1600]
    assert solid.get_linestyle() == "-"
    beyond = _lines(ax, "compression_index_beyond")
    assert [line.get_linestyle() for line in beyond] == ["--", "--"]
    assert [_xy(line)[0][0] for line in beyond] == [10, 1600]
    assert _xy(beyond[1])[1][0] == pytest.approx(ax.get_xlim()[1])
    for line in beyond:
        assert _log_line(line)[1] == pytest.approx(slope, rel=REL)
        assert line.get_linewidth() < solid.get_linewidth()
    (cr,) = _lines(ax, "recompression_index")
    assert [x for x, _ in _xy(cr)] == [25, 200]
    assert -_log_line(cr)[1] == pytest.approx(0.0508254999, rel=1e-8)
    (cs,) = _lines(ax, "swelling_index")
    assert [x for x, _ in _xy(cs)] == [50, 800]
    assert -_log_line(cs)[1] == pytest.approx(0.0215925326, rel=1e-8)
    assert fit.specimens[0]["compression_line"]["intercept"] == pytest.approx(
        intercept, rel=REL
    )
    # One specimen: the lines are black, the points the specimen's color.
    assert to_hex(solid.get_color()) == "#000000"


def test_preconsolidation_marks(bh1):
    """AC 3: the triangles on the loading curve at 264.401656 and 239.040472 kPa."""
    _, ax, _ = bh1
    (oikawa,) = _lines(ax, "preconsolidation_stress")
    (check,) = _lines(ax, "preconsolidation_stress_pacheco_silva")
    loading_x = np.log10([25, 50, 100, 200, 400, 800, 1600])
    loading_e = [0.795, 0.788, 0.776, 0.748, 0.690, 0.612, 0.520]
    for line, stress, filled in (
        (oikawa, 264.401656, True),
        (check, 239.040472, False),
    ):
        ((x, y),) = _xy(line)
        assert x == pytest.approx(stress, rel=1e-8)
        on_curve = np.interp(math.log10(x), loading_x, loading_e)
        assert y == pytest.approx(on_curve, rel=REL)
        assert line.get_marker() == "v"
        assert (line.get_markerfacecolor() == "white") is not filled
    assert not _lines(ax, "construction")


def test_construction(site_si):
    """AC 3: the steps through σA = 166.247579 kPa and e_B = 0.755466667."""
    _, ax, _ = _draw(site_si, construction=True)
    steps = [_xy(line) for line in _lines(ax, "construction")]
    assert len(steps) == 4
    (_, (a, e0)), ((a1, _), (_, b)), (_, (check, b1)), ((check1, _), (_, on)) = steps
    assert e0 == 0.800
    assert a == a1 == pytest.approx(166.247579, rel=1e-8)
    assert b == b1 == pytest.approx(0.755466667, rel=1e-8)
    assert check == check1 == pytest.approx(239.040472, rel=1e-8)
    ((_, mark),) = _xy(_lines(ax, "preconsolidation_stress_pacheco_silva")[0])
    assert on == pytest.approx(mark, rel=REL)
    plt.close("all")


def test_log_specific_volume(site_si):
    """AC 4: log y, Oikawa's two lines crossing at 264.401656 kPa, no Cs."""
    _, ax, _ = _draw(site_si, space="log_specific_volume")
    assert ax.get_yscale() == "log" and ax.get_xscale() == "log"
    assert ax.get_ylabel().startswith("Specific volume, 1 + e")
    (lower,) = _lines(ax, "oikawa_lower_line")
    (upper,) = _lines(ax, "oikawa_upper_line")

    def loglog(line):
        (x0, y0), (x1, y1) = _xy(line)
        b = (math.log10(y1) - math.log10(y0)) / (math.log10(x1) - math.log10(x0))
        return math.log10(y0) - b * math.log10(x0), b

    a1, b1 = loglog(lower)
    a2, b2 = loglog(upper)
    assert a1 == pytest.approx(0.272639634, rel=1e-8)
    assert b2 == pytest.approx(-0.0764759614, rel=1e-8)
    assert 10 ** ((a2 - a1) / (b1 - b2)) == pytest.approx(264.401656, rel=1e-8)
    assert [x for x, _ in _xy(lower)] == [25, 200]
    assert [x for x, _ in _xy(upper)] == [400, 1600]
    assert not _lines(ax, "swelling_index")
    assert not _lines(ax, "compression_index")
    (loading,) = _lines(ax, "loading_point")
    assert _xy(loading)[0] == (25, pytest.approx(1.795))
    ((_, y),) = _xy(_lines(ax, "preconsolidation_stress")[0])
    assert 1.7 < y < 1.75
    plt.close("all")


def test_no_clear_break():
    """AC 6: the spec's AC 8 frame: points and Cs, no Cc, Cr or σ′p, the reason."""
    _, ax, fit = _draw(_frame(STRAIGHT))
    assert len(_xy(_lines(ax, "loading_point")[0])) == 8
    assert -_log_line(_lines(ax, "swelling_index")[0])[1] == pytest.approx(
        0.0282363888, rel=1e-8
    )
    for gid in (
        "compression_index",
        "recompression_index",
        "preconsolidation_stress",
        "preconsolidation_stress_pacheco_silva",
    ):
        assert not _lines(ax, gid)
    box = _box(ax)
    assert "S1: σ′p not given: no clear break: the upper line is 1.17 times" in box
    assert "Cs = 0.0282" in box
    assert math.isnan(fit.specimens[0]["preconsolidation_stress"])
    plt.close("all")


def test_returns(site_si):
    """AC 7: the fit equals oedometer_fit() on the rows; fit=False; ax=."""
    fig, ax, fit = _draw(site_si)
    expected = ht.analysis.oedometer_fit(site_si, display_units="SI")
    pd.testing.assert_frame_equal(fit.to_frame(), expected.to_frame())
    assert fig is ax.figure
    plt.close("all")
    _, ax, fit = _draw(site_si, fit=False)
    assert fit is None
    for gid in ("compression_index", "swelling_index", "preconsolidation_stress"):
        assert not _lines(ax, gid)
    assert not [text for text in ax.texts if text.get_gid() == "result_box"]
    assert _lines(ax, "loading_point")
    plt.close("all")
    fig, given = plt.subplots()
    out_fig, out_ax, _ = _draw(site_si, ax=given)
    assert out_ax is given and out_fig is fig
    assert len(plt.get_fignums()) == 1
    plt.close("all")


def test_result_box_off(site_si):
    _, ax, _ = _draw(site_si, result_box=False)
    assert not [text for text in ax.texts if text.get_gid() == "result_box"]
    plt.close("all")


# --- AC 9: P13 §11, one hand-built frame per row -------------------------------


def test_missing_column_raises():
    df = _frame(BH1_U3).drop(columns="void_ratio_at_increment_end")
    with pytest.raises(ColumnError, match=r"void_ratio_at_increment_end.*template"):
        _draw(df)


def test_space_value_raises():
    with pytest.raises(HangtuError, match=r"void_ratio.*log_specific_volume"):
        _draw(_frame(BH1_U3), space="strain")


def test_no_unload():
    _, ax, _ = _draw(_frame(BH1_U3[:6]))
    assert not _lines(ax, "swelling_index")
    assert "Cs: no unloading" in _box(ax)
    plt.close("all")


def test_no_initial_void_ratio():
    _, ax, _ = _draw(_frame(BH1_U3))
    assert not _lines(ax, "initial_void_ratio")
    assert not _lines(ax, "preconsolidation_stress_pacheco_silva")
    box = _box(ax)
    assert "Pacheco Silva not given: no initial void ratio" in box
    assert "CR not given: no initial void ratio" in box
    plt.close("all")


def test_initial_void_ratio_tick():
    _, ax, _ = _draw(_frame(BH1_U3, void_ratio=0.800))
    (tick,) = _lines(ax, "initial_void_ratio")
    assert list(tick.get_ydata()) == [0.800, 0.800]
    assert tick.get_xdata()[0] == 0.0  # the left edge, in axes fraction
    plt.close("all")


def test_no_effective_vertical_stress_column():
    _, ax, _ = _draw(_frame(BH1_U3, void_ratio=0.800))
    assert not _lines(ax, "effective_vertical_stress")
    assert "OCR" not in _box(ax)
    assert "run ht.analysis.vertical_stress() on the rows" in _footnote(ax)
    plt.close("all")


def test_blank_effective_vertical_stress():
    df = _frame(BH1_U3, void_ratio=0.800, effective_vertical_stress=np.nan)
    _, ax, _ = _draw(df)
    assert not _lines(ax, "effective_vertical_stress")
    box = _box(ax)
    assert "OCR not given: no effective vertical stress at the specimen's depth" in box
    plt.close("all")


def test_ocr_below_one():
    df = _frame(BH1_U3, void_ratio=0.800, effective_vertical_stress=300.0)
    with pytest.warns(UserWarning, match="OCR below 1 in S1"):
        _, ax, _ = _draw(df)
    assert "OCR = 0.881 (< 1)" in _box(ax)
    ((x, _), _) = _xy(_lines(ax, "effective_vertical_stress")[0])
    assert x == 300.0
    plt.close("all")


def test_specimen_with_no_increments():
    df = pd.concat(
        [
            _frame(BH1_U3),
            _frame([(np.nan, np.nan)], specimen="SW1"),
        ],
        ignore_index=True,
    )
    df.attrs["units"] = {"applied_vertical_stress": "kPa"}
    _, ax, fit = _draw(df)
    assert "Not drawn, no increments to draw: SW1" in _footnote(ax)
    assert "SW1" not in _box(ax)
    assert len(fit.specimens) == 2
    plt.close("all")


def test_many_specimens():
    df = pd.concat(
        [_frame(BH1_U3, specimen="A"), _frame(STRAIGHT, specimen="B")],
        ignore_index=True,
    )
    df.attrs["units"] = {"applied_vertical_stress": "kPa"}
    _, ax, _ = _draw(df)
    first, second = _lines(ax, "loading_point")
    assert to_hex(first.get_color()) != to_hex(second.get_color())
    # Several specimens: the lines take the specimen's color.
    (cc,) = _lines(ax, "compression_index")
    assert to_hex(cc.get_color()) == to_hex(first.get_color())
    box = _box(ax)
    assert box.index("A: σ′p = 264 kPa") < box.index("B: σ′p not given")
    legend = [text.get_text() for text in ax.get_legend().get_texts()]
    assert legend[:2] == ["A", "B"]
    plt.close("all")


def test_construction_without_check():
    _, ax, _ = _draw(_frame(BH1_U3), construction=True)
    assert not _lines(ax, "construction")
    plt.close("all")


def test_left_out_footnote(bh1):
    _, ax, _ = bh1
    assert (
        "Left out of BH1-U3-OED1: 2 reloading, 1 unloading after the first run"
        in _footnote(ax)
    )
