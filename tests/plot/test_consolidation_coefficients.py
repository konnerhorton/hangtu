"""P14 consolidation coefficients (docs/plots/P14-consolidation-coefficients.md).

AC 1-4, 6, 8 and 9; AC 5 and 7 are in the acceptance file.

Golden values are the M19 (c1) spec's (docs/work/m19c-consolidation.md, AC
1-4), hand-calculated there. Positions are read from the drawn artists.
"""

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError

AGS = Path(__file__).parents[1] / "data" / "ags"
REL = 1e-9
BRANCHES = "'loading', 'unloading', 'reloading'"


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


@pytest.fixture(scope="module")
def bh1(site_si):
    ht.settings.hints = False  # a module fixture runs before the autouse one
    fig, axs = ht.plot.consolidation_coefficients(site_si, display_units="SI")
    yield fig, axs
    plt.close(fig)


def _with_in_situ(df, value):
    out = df.assign(effective_vertical_stress=value)
    out.attrs["units"] = {**df.attrs["units"], "effective_vertical_stress": "kPa"}
    return out


def _frame(stresses, void_ratios, specimen="S1", **columns):
    """Increments of one specimen in kPa, in test order."""
    df = pd.DataFrame(
        {
            "specimen_id": [specimen] * len(stresses),
            "applied_vertical_stress": np.array(stresses, dtype=float),
            "void_ratio_at_increment_end": np.array(void_ratios, dtype=float),
            **columns,
        }
    )
    df.attrs["units"] = {"applied_vertical_stress": "kPa"}
    return df


def _lines(ax, gid):
    return [line for line in ax.lines if line.get_gid() == gid]


def _segment(lines, low, high, value=None):
    """The one segment drawn from ``low`` to ``high`` (at ``value``, if given)."""
    found = [
        line
        for line in lines
        if math.isclose(line.get_xdata()[0], low, rel_tol=REL)
        and math.isclose(line.get_xdata()[-1], high, rel_tol=REL)
        and (value is None or math.isclose(line.get_ydata()[0], value, rel_tol=1e-8))
    ]
    assert len(found) == 1, (low, high, len(found))
    return found[0]


def _texts(ax):
    return "\n".join(text.get_text() for text in ax.texts)


def test_volume_segments(bh1):
    """AC 1: 6 solid and 5 dashed segments; increments 4 and 7."""
    _, (upper, _) = bh1
    loading = _lines(upper, "volume_loading")
    unload_reload = _lines(upper, "volume_unload_reload")
    assert len(loading) == 6
    assert len(unload_reload) == 5
    assert all(line.get_linestyle() == "-" for line in loading)
    assert all(line.get_linestyle() == "--" for line in unload_reload)
    fourth = _segment(loading, 100, 200)
    assert fourth.get_ydata()[0] == pytest.approx(0.157657658, rel=1e-8)
    assert fourth.get_ydata()[1] == fourth.get_ydata()[0]
    seventh = _segment(unload_reload, 200, 800, 0.0134408602)
    assert seventh.get_alpha() < 1
    assert seventh.get_linewidth() < fourth.get_linewidth()


def test_reported_marks(bh1):
    """AC 2: 6 × marks, increment 4's at (√(100 × 200), 0.16)."""
    _, (upper, _) = bh1
    marks = _lines(upper, "volume_reported")
    assert len(marks) == 6
    assert all(line.get_marker() == "x" for line in marks)
    fourth = [
        line
        for line in marks
        if math.isclose(line.get_xdata()[0], 141.421356, rel_tol=1e-8)
    ]
    assert len(fourth) == 1
    assert fourth[0].get_ydata()[0] == pytest.approx(0.16, rel=REL)


def test_no_reported_marks(site_si):
    _, (upper, _) = ht.plot.consolidation_coefficients(
        site_si, reported=False, display_units="SI"
    )
    assert not _lines(upper, "volume_reported")
    plt.close("all")


def test_consolidation_segments(bh1):
    """AC 3: increment 4's c_v, root time solid at 2.1, log time dotted at 1.8."""
    _, (_, lower) = bh1
    root = _segment(_lines(lower, "consolidation_root_time"), 100, 200)
    log = _segment(_lines(lower, "consolidation_log_time"), 100, 200)
    assert root.get_ydata()[0] == pytest.approx(2.1, rel=REL)
    assert log.get_ydata()[0] == pytest.approx(1.8, rel=REL)
    assert root.get_linestyle() == "-"
    assert log.get_linestyle() == ":"


@pytest.mark.parametrize(
    ("in_situ", "loading", "unload_reload"),
    [
        (80.0, (50, 100), (50, 200, 0.0533333333)),
        (150.0, (100, 200), (50, 200, 0.0533333333)),
    ],
)
def test_effective_vertical_stress(site_si, in_situ, loading, unload_reload):
    """AC 4: σ′v0's line in both panels and the increments spanning it thicker."""
    fig, (upper, lower) = ht.plot.consolidation_coefficients(
        _with_in_situ(site_si, in_situ), display_units="SI"
    )
    for ax in (upper, lower):
        (line,) = _lines(ax, "effective_vertical_stress")
        assert line.get_xdata()[0] == pytest.approx(in_situ, rel=REL)
        assert line.get_linestyle() == ":"
    solid = _lines(upper, "volume_loading")
    dashed = _lines(upper, "volume_unload_reload")
    thick = _segment(solid, *loading)
    widths = {line.get_linewidth() for line in solid if line is not thick}
    assert len(widths) == 1
    assert thick.get_linewidth() > widths.pop()
    thick = [line for line in dashed if line.get_linewidth() > 1.0]
    assert thick == [_segment(dashed, *unload_reload)]
    plt.close(fig)


def test_no_increment_spans(site_si):
    _, (_, lower) = ht.plot.consolidation_coefficients(
        _with_in_situ(site_si, 20.0), display_units="SI"
    )
    assert "No increment of BH1-U3-OED1 spans σ′v0" in _texts(lower)
    plt.close("all")


def test_branches(site_si):
    """AC 6: loading only draws 6 m_v segments and no dashed one."""
    _, (upper, _) = ht.plot.consolidation_coefficients(
        site_si, branches=("loading",), display_units="SI"
    )
    assert len(_lines(upper, "volume_loading")) == 6
    assert not _lines(upper, "volume_unload_reload")
    assert not any(line.get_linestyle() == "--" for line in upper.lines)
    assert "m_v, unloading" not in "".join(
        t.get_text() for t in upper.get_legend().get_texts()
    )
    plt.close("all")


def test_branches_as_a_string(site_si):
    _, (upper, _) = ht.plot.consolidation_coefficients(
        site_si, branches="unloading", display_units="SI"
    )
    assert len(_lines(upper, "volume_unload_reload")) == 3
    assert not _lines(upper, "volume_loading")
    plt.close("all")


@pytest.mark.parametrize("branches", [(), ("loading", "virgin")])
def test_branches_unknown(site_si, branches):
    """AC 9, §11: an empty or unknown branches= lists the three."""
    with pytest.raises(HangtuError, match=BRANCHES):
        ht.plot.consolidation_coefficients(site_si, branches=branches)


def test_returns(bh1):
    """AC 8: (fig, axs), two axes sharing a log x, log y on both."""
    fig, axs = bh1
    assert isinstance(axs, np.ndarray)
    assert axs.shape == (2,)
    upper, lower = axs
    assert upper.get_shared_x_axes().joined(upper, lower)
    for ax in axs:
        assert ax.get_xscale() == "log"
        assert ax.get_yscale() == "log"
    assert lower.get_xlabel() == "Effective vertical stress, σ′v (kPa)"
    assert " ".join(upper.get_ylabel().split()) == (
        "Coefficient of volume compressibility, m_v (m²/MN)"
    )
    assert " ".join(lower.get_ylabel().split()) == (
        "Coefficient of consolidation, c_v (m²/yr)"
    )
    assert upper.get_xlim() == pytest.approx((10, 10_000))
    assert tuple(fig.get_size_inches()) == pytest.approx(
        ht.settings.figure_sizes["stacked"]
    )


def test_missing_column():
    """AC 9, §11: a required column missing raises naming it and the template."""
    df = _frame([25, 50], [0.8, 0.79]).drop(columns="void_ratio_at_increment_end")
    with pytest.raises(ColumnError, match=r"void_ratio_at_increment_end.*template"):
        ht.plot.consolidation_coefficients(df)


def test_no_consolidation_reported():
    """§11: no c_v in either column leaves the lower panel with a note."""
    fig, (upper, lower) = ht.plot.consolidation_coefficients(
        _frame([25, 50, 100], [0.80, 0.79, 0.77]), display_units="SI"
    )
    assert len(_lines(upper, "volume_loading")) == 2
    assert "No c_v reported" in _texts(lower)
    assert not lower.lines
    plt.close(fig)


def test_no_in_situ_stress(bh1):
    """§11: no σ′v0, no line and no thick segment."""
    _, (upper, lower) = bh1
    assert not _lines(upper, "effective_vertical_stress")
    assert not _lines(lower, "effective_vertical_stress")
    assert len({line.get_linewidth() for line in _lines(upper, "volume_loading")}) == 1


def test_volume_not_positive():
    """§11: an m_v of 0 or less isn't drawn; the footnote names it."""
    fig, (upper, lower) = ht.plot.consolidation_coefficients(
        _frame([50, 100, 200], [0.788, 0.776, 0.781]), display_units="SI"
    )
    assert len(_lines(upper, "volume_loading")) == 1
    assert (
        "Not drawn for S1: increment 1 (start stress not given), "
        "increment 3 (m_v not positive)"
    ) in _texts(lower)
    plt.close(fig)


def test_constant_stress_and_first_consolidation():
    """A constant stress has no m_v (footnote); the first c_v is a × at its end."""
    df = _frame(
        [25, 50, 50],
        [0.80, 0.79, 0.785],
        reported_coefficient_of_consolidation_root_time=[3.0, 2.5, np.nan],
    )
    df.attrs["units"]["reported_coefficient_of_consolidation_root_time"] = "m2/yr"
    fig, (upper, lower) = ht.plot.consolidation_coefficients(df, display_units="SI")
    assert len(_lines(upper, "volume_loading")) == 1
    (point,) = _lines(lower, "consolidation_root_time_point")
    assert (point.get_xdata()[0], point.get_ydata()[0]) == (25, 3.0)
    assert point.get_marker() == "x"
    (segment,) = _lines(lower, "consolidation_root_time")
    assert list(segment.get_xdata()) == [25, 50]
    assert "increment 3 (no stress change)" in _texts(lower)
    plt.close(fig)


def test_specimen_without_increments():
    """§11: a specimen with no increments isn't drawn; the footnote names it."""
    df = pd.concat(
        [
            _frame([25, 50], [0.80, 0.79]),
            _frame([np.nan], [np.nan], specimen="SWELL"),
        ],
        ignore_index=True,
    )
    df.attrs["units"] = {"applied_vertical_stress": "kPa"}
    fig, (upper, lower) = ht.plot.consolidation_coefficients(df, display_units="SI")
    assert len(_lines(upper, "volume_loading")) == 1
    assert "Not drawn, no increments to draw: SWELL" in _texts(lower)
    plt.close(fig)


def test_two_specimens_two_colors():
    df = pd.concat(
        [
            _frame([25, 50, 100], [0.80, 0.79, 0.77]),
            _frame([25, 50, 100], [0.90, 0.88, 0.85], specimen="S2"),
        ],
        ignore_index=True,
    )
    df.attrs["units"] = {"applied_vertical_stress": "kPa"}
    fig, (upper, _) = ht.plot.consolidation_coefficients(df, display_units="SI")
    colors = {line.get_color() for line in _lines(upper, "volume_loading")}
    assert len(colors) == 2
    labels = [t.get_text() for t in upper.get_legend().get_texts()]
    assert labels[:2] == ["S1", "S2"]
    plt.close(fig)


def test_note(bh1, site_si):
    fig, (_, lower) = ht.plot.consolidation_coefficients(
        site_si, note="Lab: example", display_units="SI"
    )
    assert "Lab: example" in _texts(lower)
    plt.close(fig)


def test_reported_without_a_unit():
    df = _frame(
        [25, 50, 100],
        [0.80, 0.79, 0.77],
        reported_coefficient_of_volume_compressibility=[np.nan, 0.5, 0.4],
    )
    fig, (upper, lower) = ht.plot.consolidation_coefficients(df, display_units="SI")
    assert not _lines(upper, "volume_reported")
    assert (
        "reported_coefficient_of_volume_compressibility not drawn: its unit isn't "
        "given."
    ) in _texts(lower)
    plt.close(fig)


def test_hint_without_in_situ_stress(site_si):
    ht.settings.hints = True
    with pytest.warns(ht.HangtuHint, match="effective_vertical_stress"):
        ht.plot.consolidation_coefficients(site_si, display_units="SI")
    plt.close("all")
