"""P05 D-values (P05 §7, §11, §12)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError

CURVE_A = (
    [0.075, 0.15, 0.3, 0.6, 1.18, 2.36, 4.75],
    [4, 12, 30, 55, 75, 90, 100],
)
#: Curve A's D-values, worked by hand (docs/drafts/analysis.md §3.7).
GOLDEN = {10: 0.1261, 30: 0.300, 60: 0.7105}


@pytest.fixture(autouse=True)
def _no_hints():
    ht.settings.hints = False


def curves(*specs, unit="mm"):
    rows = [
        {"specimen_id": name, "particle_size": size, "percent_passing": percent}
        for name, sizes, passing in specs
        for size, percent in zip(sizes, passing, strict=True)
    ]
    return ht.set_units(pd.DataFrame(rows), {"particle_size": unit})


def d_lines(ax):
    return [line for line in ax.lines if line.get_gid() == "d_value"]


def d_labels(ax):
    return [t.get_text() for t in ax.texts if t.get_gid() == "d_value_label"]


# --- D-values (§7, §12) ------------------------------------------------------


def test_d_values_of_curve_a():
    _, ax = ht.plot.grain_size(curves(("A", *CURVE_A)), d_values=True)
    lines = d_lines(ax)
    assert len(lines) == 3
    left = ax.get_xlim()[0]
    for line, (percent, size) in zip(lines, GOLDEN.items(), strict=True):
        x, y = line.get_data()
        np.testing.assert_allclose(x[:2], size, rtol=1e-3)
        assert x[2] == left
        np.testing.assert_allclose(y, [0, percent, percent])
        assert line.get_linestyle() == "--"
    assert d_labels(ax) == ["D10 = 0.126 mm", "D30 = 0.300 mm", "D60 = 0.711 mm"]


def test_reversed_leaders_go_to_the_left_edge():
    _, ax = ht.plot.grain_size(curves(("A", *CURVE_A)), d_values=[60], reverse=True)
    (line,) = d_lines(ax)
    assert line.get_xdata()[2] == ax.get_xlim()[0] == 100


def test_several_curves_get_ticks_without_labels():
    df = curves(("A", *CURVE_A), ("B", *CURVE_A))
    _, ax = ht.plot.grain_size(df, d_values=[10, 60])
    lines = d_lines(ax)
    assert len(lines) == 4
    assert {line.get_marker() for line in lines} == {"|"}
    assert d_labels(ax) == []
    sizes = sorted(round(line.get_xdata()[0], 4) for line in lines)
    assert sizes == [0.1261, 0.1261, 0.7105, 0.7105]


def test_unreached_d_values_are_counted_per_percentage():
    fill = ([0.075, 0.425, 4.75, 75], [24, 40, 77, 100])
    df = curves(("A", *CURVE_A), ("F", *fill), ("G", *fill))
    _, ax = ht.plot.grain_size(df, d_values=True)
    assert ax.ags_notes == {"d_value_unreached": 2}
    assert "2 D-values not reached (D10 by 2 curves)" in ax.texts[-1].get_text()
    assert len(d_lines(ax)) == 7


def test_non_monotonic_curve_gets_no_d_values():
    df = curves(("A", *CURVE_A), ("N", [0.075, 0.15, 0.3, 1], [20, 10, 50, 100]))
    with pytest.warns(UserWarning, match="without D-values"):
        _, ax = ht.plot.grain_size(df, d_values=[30])
    assert len(d_lines(ax)) == 1
    assert ax.ags_notes == {}


def test_d_values_off_by_default_and_empty_list():
    df = curves(("A", *CURVE_A))
    assert d_lines(ht.plot.grain_size(df)[1]) == []
    assert d_lines(ht.plot.grain_size(df, d_values=[])[1]) == []


@pytest.mark.parametrize("d_values", [[0], [100], [12.5], "D10"])
def test_bad_d_values_is_an_error(d_values):
    with pytest.raises(HangtuError, match="d_values must be"):
        ht.plot.grain_size(curves(("A", *CURVE_A)), d_values=d_values)
