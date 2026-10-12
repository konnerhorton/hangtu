"""P01 §12 acceptance criteria, against the test data in tests/data/.

Footnote counts are by hand from the CSVs:
- profile_perm.csv: 17 rows. B-2 at 36.0 ft is blank, B-2 at 22.0 ft is 0.0
  (≤ 0 on the log axis) and B-1 at 30.0 ft is "<". The other 15 are drawn,
  the "<" value as a caret.
- profile_su.csv: 10 rows in BH-1 (ground level 36.0 m), all drawn.
- profile_single.csv: one point.
"""

from functools import partial
from pathlib import Path

import matplotlib as mpl
import numpy as np
import pandas as pd
import pytest
from matplotlib.colors import to_rgba

import hangtu as ak

DATA = Path(__file__).parents[1] / "data"
FT = 0.3048
PSF_TO_KPA = 0.04788026


def perm():
    return ak.read_csv(
        DATA / "profile_perm.csv",
        units={
            "depth": "ft",
            "depth_top": "ft",
            "depth_base": "ft",
            "ground_level": "ft",
            "hydraulic_conductivity": "cm/s",
        },
    )


def su():
    return ak.read_csv(
        DATA / "profile_su.csv",
        units={
            "depth": "m",
            "ground_level": "m",
            "elevation": "m",
            "undrained_shear_strength": "kPa",
        },
    )


def single():
    return ak.read_csv(
        DATA / "profile_single.csv",
        units={"depth": "ft", "ground_level": "ft", "bulk_unit_weight": "pcf"},
    )


K = {"value": "hydraulic_conductivity", "preset": "hydraulic_conductivity"}
SU = {"value": "undrained_shear_strength", "preset": "undrained_shear_strength"}


def plot_k(**kwargs):
    return ak.plot.profile(perm(), **K, **kwargs)


def plot_su(**kwargs):
    return ak.plot.profile(su(), **SU, **kwargs)


def filled(ax):
    """{(x, y)} of every filled point drawn."""
    return {
        tuple(xy)
        for c in ax.collections
        if len(c.get_facecolor())
        for xy in c.get_offsets().tolist()
    }


def caret_tips(ax, marker_label):
    (collection,) = [c for c in ax.collections if c.get_label().endswith(marker_label)]
    vertices = collection.get_paths()[0].vertices
    return vertices[np.abs(vertices[:, 1]) < 1e-9, 0]


# --- golden values ---------------------------------------------------------------


def test_elevation_is_ground_level_minus_depth():
    # B-2: GL 120.0 ft, depth 15.0 ft -> 105.0 ft.
    _, ax = plot_k()
    assert (1.0e-3, 105.0) in filled(ax)


def test_interval_bounds_convert_the_same_way():
    # B-2: top 10.0 ft, base 20.0 ft, GL 120.0 ft -> 110.0 to 100.0 ft.
    _, ax = plot_k()
    bars = {
        (line.get_xdata()[i], line.get_ydata()[i], line.get_ydata()[i + 1])
        for line in ax.lines
        for i in range(0, len(line.get_xdata()), 3)
    }
    assert (1.0e-3, 110.0, 100.0) in bars
    assert len(bars) == 5


def test_k_in_cm_per_s_is_m_per_s_in_si():
    # k = 1.0e-5 m/s displays as 1.0e-3 cm/s; here the reverse.
    _, ax = plot_k(display_units="SI")
    assert any(
        x == pytest.approx(1.0e-5) and y == pytest.approx(105.0 * FT)
        for x, y in filled(ax)
    )


def test_ten_feet_is_3048_millimeters():
    # B-1 at 10.0 ft depth.
    _, ax = plot_k(vs="depth", display_units="SI")
    assert any(y == pytest.approx(3.048) for _, y in filled(ax))


def test_95_76_kpa_is_2000_psf():
    _, ax = plot_su(display_units="US")
    assert any(
        x == pytest.approx(2000.0, rel=1e-4) and y == pytest.approx(27.0 / FT)
        for x, y in filled(ax)
    )


# --- visual checks, automated ------------------------------------------------------


def test_depth_axis_starts_at_zero_at_the_top():
    _, ax = plot_k(vs="depth")
    assert ax.get_ylim() == (50.0, 0.0)


def test_elevation_increases_upward():
    _, ax = plot_k()
    low, high = ax.get_ylim()
    assert low < high
    assert low <= 120.0 - 44.0 and high >= 120.0


def test_log_axis_shows_whole_decades():
    _, ax = plot_k()
    low, high = ax.get_xlim()
    # 9.0e-8 to 1.0e-3 cm/s: 1.0e-3 is a whole decade, so it is the limit.
    assert (low, high) == pytest.approx((1e-8, 1e-3))
    labels = [ax.xaxis.get_major_formatter()(tick) for tick in (1e-8, 1e-5, 1e-3)]
    assert labels == [
        r"$\mathdefault{10^{-8}}$",
        r"$\mathdefault{10^{-5}}$",
        r"$\mathdefault{10^{-3}}$",
    ]


def test_x_axis_is_at_the_bottom():
    _, ax = plot_k()
    assert ax.xaxis.get_label_position() == "bottom"


def test_unit_colors_match_legend_handles():
    _, ax = plot_k()
    for handle in ak.plot.legend_handles(["Alluvium", "Fill", "Upper Clay"]):
        points = [c for c in ax.collections if c.get_label() == handle.get_label()]
        assert to_rgba(points[0].get_facecolor()[0]) == to_rgba(handle.get_facecolor())


def test_carets_point_the_right_way():
    df = perm()
    df.loc[0, "qualifier"] = ">"
    _, ax = ak.plot.profile(df, **K)
    assert caret_tips(ax, " <").max() < 0
    assert caret_tips(ax, " >").min() > 0


def test_footnote_counts():
    _, ax = plot_k()
    assert ax.ags_notes == {"nan": 1, "log_nonpositive": 1, "less_than": 1}
    assert ax.texts[-1].get_text().splitlines() == [
        "1 blank value not shown",
        "1 value ≤ 0 not shown on log axis",
        "1 value reported as less than (<)",
    ]
    assert len(filled(ax)) == 15
    legend = [text.get_text() for text in ax.get_legend().get_texts()]
    assert legend == ["Alluvium", "Fill", "Upper Clay", "less than (1)"]


# --- automated ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("data", "value"),
    [
        (perm, "hydraulic_conductivity"),
        (su, "undrained_shear_strength"),
        (single, "water_content"),
        (single, "bulk_unit_weight"),
    ],
)
@pytest.mark.parametrize("vs", ["depth", "elevation"])
def test_renders_for_every_preset_and_vs(data, value, vs):
    _, ax = ak.plot.profile(data(), value, preset=value, vs=vs)
    assert filled(ax)


def test_a_single_point_sits_inside_the_typical_range():
    _, ax = ak.plot.profile(single(), "bulk_unit_weight", preset="bulk_unit_weight")
    low, high = ax.get_xlim()
    assert low <= 89.1 and high >= 146.4  # 14-23 kN/m³ in pcf
    assert low < 118.0 < high


def test_labels_contain_units_and_the_datum():
    with ak.settings.override(vertical_datum="NAVD88"):
        _, us = plot_k()
        _, si = plot_su(display_units="SI")
    assert us.get_xlabel() == "Hydraulic conductivity, k (cm/s)"
    assert us.get_ylabel() == "Elevation (ft, NAVD88)"
    assert si.get_xlabel() == "Undrained shear strength, s_u (kPa)"
    assert si.get_ylabel() == "Elevation (m, NAVD88)"


def overlays():
    strata = ak.set_units(
        pd.DataFrame(
            {
                "geology_unit": ["Fill", "Alluvium", "Upper Clay"],
                "elevation_top": [120.0, 112.0, 96.0],
                "elevation_base": [112.0, 96.0, 75.0],
            }
        ),
        {"elevation_top": "ft", "elevation_base": "ft"},
    )
    ranges = ak.set_units(
        pd.DataFrame(
            {
                "low": [1e-5],
                "high": [1e-1],
                "label": ["silty sand"],
                "source": ["Freeze & Cherry 1979"],
            }
        ),
        {"low": "cm/s", "high": "cm/s"},
    )
    design = ak.set_units(
        pd.DataFrame(
            {"label": ["design"] * 2, "elevation": [120.0, 80.0], "value": [1e-4, 1e-6]}
        ),
        {"elevation": "ft", "value": "cm/s"},
    )
    return {
        "strata": strata,
        "water_level": [(112.5, "GWL (2026-03)")],
        "ranges": ranges,
        "design_lines": design,
        "reference_lines": [(1e-6, "limit")],
        "stats_box": True,
        "note": "Draft",
        "marker_by": "source",
        "connect": True,
    }


@pytest.mark.parametrize("overlay", list(overlays()))
def test_every_overlay_on_and_off(overlay):
    _, plain = plot_k()
    _, ax = plot_k(**{overlay: overlays()[overlay]})
    count = len(ax.patches) + len(ax.lines) + len(ax.texts) + len(ax.collections)
    plain_count = (
        len(plain.patches)
        + len(plain.lines)
        + len(plain.texts)
        + len(plain.collections)
    )
    assert count > plain_count
    assert ax.ags_notes == plain.ags_notes


def test_draws_into_a_sheet_panel_without_a_new_figure():
    sheet = ak.Sheet("letter", layout=(1, 2))
    figures = mpl.pyplot.get_fignums()
    fig, _ = plot_k(ax=sheet[0])
    assert fig is sheet.figure
    assert mpl.pyplot.get_fignums() == figures


@pytest.mark.parametrize(
    ("data", "kwargs", "quantity"),
    [
        (perm, {**K, "marker_by": "source", "connect": True}, "hydraulic_conductivity"),
        (perm, {**K, "vs": "depth"}, "hydraulic_conductivity"),
        (su, {**SU, "secondary": "depth"}, "stress"),
        (single, {"value": "water_content", "preset": "water_content"}, "percent"),
    ],
)
def test_us_and_si_put_points_in_the_same_place(
    data, kwargs, quantity, assert_us_si_equivalent
):
    plot = partial(ak.plot.profile, **kwargs)
    assert_us_si_equivalent(plot, data(), (quantity, "length"))


def test_out_of_range_counts():
    # Within 1e-7 to 1e-4 cm/s: 9.0e-8 is below; 3.2e-4, 2.1e-4, 1.5e-4,
    # 1.0e-3, 4.5e-4, 1.2e-4 and 3.5e-4 are above. The "<" value 4.0e-7 is
    # inside.
    _, ax = plot_k(xlim=(1e-7, 1e-4))
    assert ax.ags_notes == {
        "nan": 1,
        "log_nonpositive": 1,
        "beyond_limit": 8,
        "less_than": 1,
    }


def test_missing_columns_and_units_are_explained():
    with pytest.raises(ak.ColumnError, match="Column 'k' not found"):
        ak.plot.profile(perm(), "k")
    no_vertical = perm().drop(columns=["depth", "ground_level"])
    with pytest.raises(ak.ColumnError, match="'depth' or an 'elevation' column"):
        ak.plot.profile(no_vertical, **K)
    bare = pd.read_csv(DATA / "profile_perm.csv")
    with pytest.warns(UserWarning) as record:
        _, ax = ak.plot.profile(bare, **K)
    messages = [str(warning.message) for warning in record]
    assert any("'hydraulic_conductivity' has no units" in m for m in messages)
    assert ax.get_xlabel() == "Hydraulic conductivity, k (units unknown)"


def test_no_change_to_global_state(assert_no_global_state):
    assert_no_global_state(ak.plot.profile, perm(), **K, **overlays())
