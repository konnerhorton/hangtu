"""P15 against docs/plots/P15-consolidation-time-curves.md §12, on hand-built frames.

The drawn values are the M19 (c2) spec's AC 1, 2 and 4, hand-calculated
there from BH1-U3's increment 4 readings. AC 1, 2 and 6 on the twin files and
the example project are in test_consolidation_time_curves_acceptance.py.
"""

import math
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError

#: AC 1's readings: (t min, δ_v mm).
INCREMENT_4 = [
    (0, 0.267), (0.1, 0.306), (0.25, 0.317), (0.5, 0.330), (1, 0.348),
    (2, 0.374), (4, 0.410), (8, 0.460), (15, 0.511), (30, 0.552),
    (60, 0.565), (120, 0.568), (240, 0.570), (480, 0.573), (1440, 0.578),
]  # fmt: skip
#: The spec's AC 1 (root time) and AC 2 (log time), hand-calculated there.
ZERO = 0.286233001
SLOPE = 0.0619114129
AT_90 = 0.525696071
TIME_90 = 19.7847853
LOG_ZERO = 0.286666667
AT_100 = 0.560523057
TIME_100 = 29.0882465
AT_50 = 0.423594862
TIME_50 = 4.82957834
REL = 1e-8
UNITS = {
    "elapsed_time": "min",
    "vertical_displacement": "mm",
    "specimen_height": "mm",
    "applied_vertical_stress": "kPa",
    "reported_coefficient_of_consolidation_root_time": "m2/yr",
    "reported_coefficient_of_consolidation_log_time": "m2/yr",
}
PLOT = ht.plot.consolidation_time_curves


@pytest.fixture(autouse=True)
def _no_hints():
    ht.settings.hints = False


@pytest.fixture(autouse=True)
def _close():
    yield
    plt.close("all")


def increment(points, *, specimen="S1", stage="4", stress=200.0, **values):
    """One increment's readings in the template's shape, BH1-U3's values."""
    columns = {
        "specimen_id": specimen,
        "sample_reference": "BH1-U3",
        "specimen_reference": "OED1",
        "test_stage": stage,
        "load_branch": "loading",
        "applied_vertical_stress": stress,
        "specimen_height": 20.0,
        "void_ratio": 0.800,
        "void_ratio_at_increment_start": 0.776,
        "void_ratio_at_increment_end": 0.748,
        "reported_coefficient_of_consolidation_root_time": 2.1,
        "reported_coefficient_of_consolidation_log_time": 1.8,
        "elapsed_time": [t for t, _ in points],
        "vertical_displacement": [d for _, d in points],
    }
    columns.update(values)
    return pd.DataFrame(columns)


def frame(*parts):
    return ht.set_units(pd.concat(parts, ignore_index=True), UNITS)


def golden(**values):
    """Increments 3 and 4: 3 gives increment 4 its start stress."""
    return frame(
        increment(INCREMENT_4, stage="3", stress=100.0, **values),
        increment(INCREMENT_4, **values),
    )


def draw(df, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return PLOT(df, display_units=kwargs.pop("display_units", "SI"), **kwargs)


def lines(ax, gid):
    return [line for line in ax.lines if line.get_gid() == gid]


def line(ax, gid):
    found = lines(ax, gid)
    assert len(found) == 1, gid
    return found[0]


def texts(ax, gid):
    return [t.get_text() for t in ax.texts if t.get_gid() == gid]


def points(ax, gid):
    found = lines(ax, gid)
    if not found:
        return np.array([]), np.array([])
    return np.asarray(found[0].get_xdata(), float), np.asarray(
        found[0].get_ydata(), float
    )


def edge_points(ax):
    """The readings drawn at the x axis' edge, as open markers (P00 §9)."""
    return sum(len(c.get_offsets()) for c in ax.collections)


# --- AC 1: the root time panel ---------------------------------------------------


def test_ac1_root_time_panel():
    _, axs = draw(golden(), increments=["4"])
    ax = axs[0, 0]
    x, y = points(ax, "readings_used")
    times = [t for t, _ in INCREMENT_4]
    np.testing.assert_allclose(x, np.sqrt(times[1:7]), rtol=1e-12)  # 0.1-4 min
    np.testing.assert_allclose(y, [d for _, d in INCREMENT_4[1:7]], rtol=1e-12)
    others, _ = points(ax, "readings")
    # 15 readings: 6 filled, the others open, those past the x limit at its edge.
    assert len(x) + len(others) + edge_points(ax) == 15
    assert edge_points(ax) == 3  # 240, 480 and 1440 min
    early = line(ax, "early_line")
    ex, ey = early.get_xdata(), early.get_ydata()
    assert ex[0] == 0 and ey[0] == pytest.approx(ZERO, rel=REL)
    assert (ey[1] - ey[0]) / (ex[1] - ex[0]) == pytest.approx(SLOPE, rel=REL)
    assert early.get_linestyle() == "-"
    ratio = line(ax, "ratio_line")
    rx, ry = ratio.get_xdata(), ratio.get_ydata()
    assert (ry[1] - ry[0]) / (rx[1] - rx[0]) == pytest.approx(SLOPE / 1.15, rel=REL)
    assert ratio.get_linestyle() == "--"
    t90 = line(ax, "time_t90")
    assert t90.get_xdata()[0] == pytest.approx(math.sqrt(TIME_90), rel=REL)
    assert t90.get_ydata()[0] == pytest.approx(AT_90, rel=REL)
    assert line(ax, "level_d90").get_ydata()[0] == pytest.approx(AT_90, rel=REL)
    assert line(ax, "level_d0").get_ydata()[0] == pytest.approx(ZERO, rel=REL)
    assert texts(ax, "result") == ["c_v 2.15 m²/yr (lab 2.1)"]
    assert texts(ax, "label_d0") == ["d0"] and texts(ax, "label_t90") == ["t90"]
    assert axs[0, 0].get_title(loc="left") == "Increment 4: 100 → 200 kPa"


def test_the_time_labels_sit_left_of_their_lines():
    # P15 §7: the construction lines run down to the right past t90 and t50.
    _, axs = draw(golden(), increments=["4"])
    for ax, name in ((axs[0, 0], "label_t90"), (axs[0, 1], "label_t50")):
        (label,) = [t for t in ax.texts if t.get_gid() == name]
        assert label.get_horizontalalignment() == "right"
        assert label.get_bbox_patch().get_facecolor()[:3] == (1.0, 1.0, 1.0)


def test_ac1_the_x_axis_stops_past_t90():
    # P15 §6: from 0 to past 2.5 √t90, not to the last reading.
    _, axs = draw(golden(), increments=["4"])
    low, high = axs[0, 0].get_xlim()
    assert low == 0
    assert 2.5 * math.sqrt(TIME_90) <= high < math.sqrt(240)
    assert axs[0, 0].ags_notes == {"beyond_limit": 3}  # 240, 480 and 1440 min


# --- AC 2: the log time panel ----------------------------------------------------


def test_ac2_log_time_panel():
    _, axs = draw(golden(), increments=["4"])
    ax = axs[0, 1]
    x, _ = points(ax, "readings_used")
    np.testing.assert_allclose(x, [0.5, 1, 2, 4, 8, 15, 240, 480, 1440])
    others, _ = points(ax, "readings")
    assert len(x) + len(others) == 14  # no t = 0 on a log axis
    tangent, secondary = line(ax, "tangent"), line(ax, "secondary_line")
    assert tangent.get_xdata()[-1] == pytest.approx(TIME_100, rel=REL)
    assert tangent.get_ydata()[-1] == pytest.approx(AT_100, rel=REL)
    assert secondary.get_xdata()[0] == pytest.approx(TIME_100, rel=REL)
    assert secondary.get_ydata()[0] == pytest.approx(AT_100, rel=REL)
    for gid, value in (
        ("level_d0", LOG_ZERO),
        ("level_d50", AT_50),
        ("level_d100", AT_100),
    ):
        assert line(ax, gid).get_ydata()[0] == pytest.approx(value, rel=REL)
    t50 = line(ax, "time_t50")
    assert t50.get_xdata()[0] == pytest.approx(TIME_50, rel=REL)
    assert t50.get_ydata()[0] == pytest.approx(AT_50, rel=REL)
    assert texts(ax, "result") == ["c_v 2.06 m²/yr (lab 1.8)"]
    assert ax.get_xscale() == "log"
    assert ax.get_xlim()[0] == pytest.approx(0.1)  # the decade at the first reading


# --- AC 3: orientation -----------------------------------------------------------


def test_ac3_rising_readings_point_down():
    _, axs = draw(golden(), increments=["4"])
    assert all(ax.yaxis_inverted() for ax in axs[0])


def test_ac3_falling_readings_are_not_inverted_and_draw_the_same_lines():
    df = golden()
    df["vertical_displacement"] = -df["vertical_displacement"]
    _, axs = draw(df, increments=["4"])
    assert not any(ax.yaxis_inverted() for ax in axs[0])
    root, log = axs[0]
    assert line(root, "early_line").get_ydata()[0] == pytest.approx(-ZERO, rel=REL)
    assert line(root, "level_d90").get_ydata()[0] == pytest.approx(-AT_90, rel=REL)
    assert line(log, "level_d50").get_ydata()[0] == pytest.approx(-AT_50, rel=REL)
    assert line(log, "tangent").get_ydata()[-1] == pytest.approx(-AT_100, rel=REL)


# --- AC 4: an override -----------------------------------------------------------


def test_ac4_an_override_is_dash_dotted_and_named():
    overrides = ht.set_units(
        pd.DataFrame(
            {
                "specimen_id": ["S1"],
                "test_stage": ["4"],
                "consolidation_method": ["root_time"],
                "curve_portion": ["early"],
                "elapsed_time_start": [0.25],
                "elapsed_time_end": [4.0],
                "override_reason": ["0.1 min read before the load"],
            }
        ),
        {"elapsed_time_start": "min", "elapsed_time_end": "min"},
    )
    fig, axs = draw(golden(), increments=["4"], overrides=overrides)
    root, log = axs[0]
    x, _ = points(root, "readings_used")
    np.testing.assert_allclose(x, np.sqrt([0.25, 0.5, 1, 2, 4]))
    assert line(root, "early_line").get_linestyle() == "-."
    assert texts(root, "result") == ["c_v 2.16 m²/yr (lab 2.1) (override)"]
    assert texts(log, "result") == ["c_v 2.06 m²/yr (lab 1.8)"]
    labels = [t.get_text() for t in fig.legends[0].get_texts()]
    assert "Line over an override range" in labels


# --- AC 5: a reason --------------------------------------------------------------


def test_ac5_a_construction_that_stops_draws_its_readings_and_reason():
    stopped = [(t, d) for t, d in INCREMENT_4 if t <= 8]
    df = frame(increment(stopped))
    rows = ht.analysis.consolidation_coefficient_from_readings(df)
    _, axs = draw(df)
    root, log = axs[0]
    assert texts(root, "reason") == ["t90 after the last reading"]
    assert texts(root, "result") == []
    assert not lines(root, "time_t90")
    x, _ = points(root, "readings_used")
    others, _ = points(root, "readings")
    assert len(x) + len(others) == len(stopped)
    expected = rows["coefficient_of_consolidation_log_time_reason"].iloc[0]
    assert expected is not None
    assert [t.replace("\n", " ") for t in texts(log, "reason")] == [expected]


# --- AC 6: units -----------------------------------------------------------------


def test_ac6_us_units():
    _, axs = draw(golden(), increments=["4"], display_units="US")
    root, log = axs[0]
    assert line(root, "level_d0").get_ydata()[0] == pytest.approx(
        0.0112690158, rel=1e-8
    )
    assert texts(root, "result") == ["c_v 23.1 ft²/yr (lab 23)"]
    assert texts(log, "result") == ["c_v 22.2 ft²/yr (lab 19)"]
    assert line(log, "time_t50").get_xdata()[0] == pytest.approx(TIME_50, rel=REL)
    assert root.get_ylabel().replace("\n", " ") == "Vertical displacement, δ_v (in)"
    assert log.get_xlabel() == "Time, t (min)"
    assert root.get_xlabel() == "Square root of time, √t (√min)"


# --- AC 7 and 8: layout and returns ----------------------------------------------


def test_ac7_one_method_gives_one_column():
    _, axs = draw(golden(), methods=("log_time",))
    assert axs.shape == (2, 1)
    assert axs[0, 0].get_xscale() == "log"


def test_ac7_increments_give_rows_in_their_order():
    fig, axs = draw(golden(), increments=["4", "3"])
    assert axs.shape == (2, 2)
    assert [ax.get_title(loc="left") for ax in axs[:, 0]] == [
        "Increment 4: 100 → 200 kPa",
        "Increment 3: to 100 kPa",
    ]
    assert isinstance(fig, plt.Figure)


def test_ac7_seven_increments_raise_naming_increments():
    df = frame(*(increment(INCREMENT_4, stage=str(n)) for n in range(1, 8)))
    with pytest.raises(HangtuError, match=r"7 increments.*increments="):
        PLOT(df)


def test_ac7_two_specimens_need_specimen():
    df = frame(increment(INCREMENT_4), increment(INCREMENT_4, specimen="S2"))
    df.loc[df["specimen_id"] == "S2", "sample_reference"] = "BH2-U1"
    with pytest.raises(HangtuError, match=r"2 specimens \(BH1-U3-OED1, BH2-U1-OED1\)"):
        PLOT(df)
    _, axs = draw(df, specimen="BH2-U1-OED1")
    assert axs.shape == (1, 2)
    _, axs = draw(df, specimen="S1")
    assert axs.shape == (1, 2)


def test_ac8_returns_fig_and_a_rows_by_columns_array():
    fig, axs = draw(golden())
    assert isinstance(axs, np.ndarray) and axs.shape == (2, 2)
    assert all(ax.figure is fig for ax in axs.flat)
    assert fig._suptitle.get_text() == "BH1-U3-OED1"


# --- AC 9: edge cases (P15 §11) --------------------------------------------------


def test_ac9_a_missing_column_is_the_analysis_error():
    df = golden().drop(columns="elapsed_time")
    with pytest.raises(ColumnError, match=r"elapsed_time.*oedometer_readings"):
        PLOT(df)


def test_ac9_unknown_specimen_and_increment():
    with pytest.raises(HangtuError, match=r"No specimen 'BH9'.*BH1-U3-OED1"):
        PLOT(golden(), specimen="BH9")
    with pytest.raises(HangtuError, match=r"increments= has '9'.*increments 3, 4"):
        PLOT(golden(), increments=["9"])


@pytest.mark.parametrize("methods", [(), ("root",), ("log_time", "log_time")])
def test_ac9_methods_must_be_the_two(methods):
    with pytest.raises(HangtuError, match="methods="):
        PLOT(golden(), methods=methods)


def test_ac9_no_average_height_draws_the_construction_without_cv():
    df = golden(specimen_height=np.nan)
    _, axs = draw(df, increments=["4"])
    root, log = axs[0]
    expected = "c_v not computed: no specimen height or void ratio for H̄"
    assert texts(root, "result") == [expected]
    assert texts(log, "result") == [expected]
    assert line(root, "time_t90").get_xdata()[0] == pytest.approx(
        math.sqrt(TIME_90), rel=REL
    )


def test_ac9_a_constant_stress_increment_is_named_in_the_footnote():
    df = frame(
        increment(INCREMENT_4),
        increment(INCREMENT_4, stage="5", load_branch="constant_stress"),
    )
    fig, axs = draw(df)
    assert axs.shape == (1, 2)
    footnote = [t.get_text() for t in fig.texts if "Not drawn" in t.get_text()]
    assert footnote and "Not drawn: increment 5 (constant stress)" in footnote[0]


def test_ac9_readings_left_out_are_counted_in_the_footnote():
    df = golden()
    df.loc[3, "elapsed_time"] = np.nan
    fig, _ = draw(df)
    footnote = "\n".join(t.get_text() for t in fig.texts)
    assert "Left out 1 reading with a blank elapsed_time" in footnote
    assert "2 t = 0 readings on the root time panels only" in footnote


def test_ac9_a_lab_value_left_blank_is_a_dash():
    df = golden(reported_coefficient_of_consolidation_root_time=np.nan)
    _, axs = draw(df, increments=["4"])
    assert texts(axs[0, 0], "result") == ["c_v 2.15 m²/yr (lab —)"]
    _, axs = draw(df, increments=["4"], reported=False)
    assert texts(axs[0, 1], "result") == ["c_v 2.06 m²/yr"]


def test_df_must_be_a_frame():
    with pytest.raises(HangtuError, match="DataFrame"):
        PLOT([1, 2])


def test_global_matplotlib_state_is_unchanged():
    before = dict(plt.rcParams)
    draw(golden())
    assert dict(plt.rcParams) == before
