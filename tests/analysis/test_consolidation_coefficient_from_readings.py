"""ht.analysis.consolidation_coefficient_from_readings(), root time.

The c2 spec's acceptance criteria (docs/work/m19c2-cv-readings.md). The golden
increment is BH1-U3's increment 4 in site_si.ags: its readings, hand-calculated
there from the readings as rounded (BS 1377-5:1990, 3.6.3.3). The generated
curves come from Terzaghi's series in _terzaghi.py, written from the series and
checked against Abuel-Naga & Pender (2012), Table 1.
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError, UnitsError

from . import _terzaghi as terzaghi

DATA = Path(__file__).parents[1] / "data" / "ags"
MAP = DATA / "readings_map.csv"
#: The hand values are written to 9 significant figures, so they hold to 1e-8.
REL = 1e-8
FUNCTION = ht.analysis.consolidation_coefficient_from_readings
ROOT = "coefficient_of_consolidation_root_time"

#: AC 1's readings: (t min, δ_v mm).
INCREMENT_4 = [
    (0, 0.267), (0.1, 0.306), (0.25, 0.317), (0.5, 0.330), (1, 0.348),
    (2, 0.374), (4, 0.410), (8, 0.460), (15, 0.511), (30, 0.552),
    (60, 0.565), (120, 0.568), (240, 0.570), (480, 0.573), (1440, 0.578),
]  # fmt: skip
#: AC 1's hand calculation, root time.
ZERO = 0.286233001
AT_90 = 0.525696071
TIME_90 = 19.7847853
ROOT_TIME = 2.15039592
#: H̄ = (19.7333333 + 19.4222222) / 2 mm.
AVERAGE = 19.5777778
UNITS = {"elapsed_time": "min", "vertical_displacement": "mm", "specimen_height": "mm"}


def readings(points, *, stage="1", branch="loading", height=20.0, **values):
    """One increment's readings as a frame, in the template's shape."""
    frame = pd.DataFrame(
        {
            "specimen_id": "S1",
            "test_stage": stage,
            "load_branch": branch,
            "specimen_height": height,
            "void_ratio": 0.800,
            "void_ratio_at_increment_start": 0.776,
            "void_ratio_at_increment_end": 0.748,
            "elapsed_time": [t for t, _ in points],
            "vertical_displacement": [d for _, d in points],
            **values,
        }
    )
    return ht.set_units(frame, UNITS)


def quiet(*args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return FUNCTION(*args, **kwargs)


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    """BH1-U3's readings from site_si.ags and site_us.ags."""
    frames = {}
    for name in ("site_si", "site_us"):
        p = ht.Project.from_ags(
            DATA / f"{name}.ags",
            db=tmp_path_factory.mktemp(name) / "p.sqlite",
            display_units="SI",
            grag_fraction_system="astm_uscs",
        )
        p.set_readings_map(MAP)
        frames[name] = p.oedometer_readings()
    return frames


# --- The series the golden curves come from ----------------------------------------


def test_terzaghi_series_matches_abuel_naga_and_pender_table_1():
    # Table 1, p. 45, i_cv = 0: T at U = 10 % to 90 %. The series gives
    # T60 = 0.2863, which rounds to 0.286 against the table's 0.287, so each is
    # checked to within one unit of the table's last decimal.
    table = [0.008, 0.031, 0.071, 0.126, 0.197, 0.287, 0.403, 0.567, 0.848]
    for percent, expected in zip(range(10, 100, 10), table, strict=True):
        assert terzaghi.time_factor(percent / 100) == pytest.approx(expected, abs=1e-3)
    assert terzaghi.time_factor(0.5) == pytest.approx(0.197, abs=5e-4)
    assert terzaghi.time_factor(0.9) == pytest.approx(0.848, abs=5e-4)


def test_the_golden_readings_are_the_series_rounded():
    # AC 1's table: c_v 2.0 m²/yr, ρ from the void ratios, 0.020 mm immediate,
    # 0.010 mm per cycle, from a datum of 0.267 mm, rounded to 0.001 mm.
    times = [t for t, _ in INCREMENT_4]
    rho = 20 * (1.776 - 1.748) / 1.8 - 0.020
    rate = 2.0e6 / terzaghi.MINUTES_PER_YEAR
    rho -= 0.010 * np.log10(1 + 1440 / ((AVERAGE / 2) ** 2 / rate))
    y = terzaghi.readings(
        2.0, AVERAGE, rho, immediate=0.020, secondary=0.010, times=times
    )
    datum = 20 - 20 * 1.776 / 1.8  # H0 - H1
    assert [round(datum + v, 3) for v in y] == [d for _, d in INCREMENT_4]


# --- AC 1: the golden increment -----------------------------------------------------


def golden_row(frame):
    rows = quiet(frame)
    return rows[rows["test_stage"] == "4"].iloc[0], rows


def test_ac1_root_time(site):
    row, rows = golden_row(site["site_si"])
    assert row["average_specimen_height"] == pytest.approx(AVERAGE, rel=1e-8)
    assert row["corrected_zero_displacement_root_time"] == pytest.approx(ZERO, rel=REL)
    assert row["displacement_at_90_percent_consolidation"] == pytest.approx(
        AT_90, rel=REL
    )
    assert row["time_to_90_percent_consolidation"] == pytest.approx(TIME_90, rel=REL)
    assert row[ROOT] == pytest.approx(ROOT_TIME, rel=REL)
    assert row[f"{ROOT}_basis"] == "rule"
    assert row[f"{ROOT}_reason"] is None
    assert row["reported_coefficient_of_consolidation_root_time"] == 2.1
    assert (row["applied_vertical_stress"], row["load_branch"]) == (200, "loading")
    assert list(rows["test_stage"]) == ["2", "3", "4", "5", "6"]
    assert rows.attrs["units"][ROOT] == "m2/yr"
    assert rows.attrs["units"]["time_to_90_percent_consolidation"] == "min"
    assert rows.attrs["units"]["average_specimen_height"] == "mm"
    assert rows.attrs["consolidation_coefficient_from_readings"]["notes"] == []


def test_ac1_on_a_hand_built_frame():
    row = quiet(readings(INCREMENT_4)).iloc[0]
    assert row["time_to_90_percent_consolidation"] == pytest.approx(TIME_90, rel=REL)
    assert row[ROOT] == pytest.approx(ROOT_TIME, rel=REL)
    # The early line's intermediate values, as the spec writes them.
    from hangtu.analysis import _consolidation_readings as module

    frame = readings(INCREMENT_4)
    data = module.increment_readings(
        frame.index,
        np.arange(len(frame)),
        frame["elapsed_time"].to_numpy(float),
        frame["vertical_displacement"].to_numpy(float),
    )
    root = module.root_time(data)
    assert root.zero == pytest.approx(0.0192330013, rel=REL)
    assert root.slope == pytest.approx(0.0619114129, rel=REL)
    assert list(np.flatnonzero(root.fitted)) == [1, 2, 3, 4, 5, 6]  # 0.1 to 4 min
    assert np.sqrt(root.time) == pytest.approx(4.44800913, rel=REL)


# --- AC 3: recovery of the generating c_v -------------------------------------------


def generated(cv, immediate, secondary, primary=0.4):
    """Readings from the series with no rounding, H̄ 18 mm, the golden times."""
    times = terzaghi.TIMES
    y = terzaghi.readings(
        cv, 18.0, primary, immediate=immediate, secondary=secondary, times=times
    )
    return readings(
        list(zip(times, y, strict=True)),
        height=18.0,
        void_ratio_at_increment_start=0.800,
        void_ratio_at_increment_end=0.800,
    )


COMPRESSION = [(0.0, 0.0), (0.03, 0.02), (0.08, 0.05)]


@pytest.mark.parametrize("cv", [0.3, 1, 2, 5, 10])
@pytest.mark.parametrize(("immediate", "secondary"), COMPRESSION)
def test_ac3_root_time_recovers_the_generating_cv(cv, immediate, secondary):
    row = quiet(generated(cv, immediate, secondary)).iloc[0]
    assert row[ROOT] == pytest.approx(cv, rel=0.10)


@pytest.mark.parametrize(("immediate", "secondary"), COMPRESSION[:2])
def test_ac3_at_cv_20_the_times_cant_resolve_the_early_portion(immediate, secondary):
    row = quiet(generated(20, immediate, secondary)).iloc[0]
    assert np.isnan(row[ROOT])
    assert row[f"{ROOT}_reason"] == (
        "fewer than 3 readings in the first half of the increment's movement"
    )


def test_ac3_at_cv_20_a_large_immediate_compression_lengthens_the_early_portion():
    row = quiet(generated(20, *COMPRESSION[2])).iloc[0]
    assert row[ROOT] == pytest.approx(20, rel=0.10)


# --- AC 5: datum and sign -----------------------------------------------------------


@pytest.mark.parametrize(
    ("shift", "sign"), [(0.0, -1.0), (10.0, 1.0), (10.0, -1.0), (-3.0, -1.0)]
)
def test_ac5_datum_and_sign(shift, sign):
    moved = [(t, shift + sign * d) for t, d in INCREMENT_4]
    row = quiet(readings(moved)).iloc[0]
    assert row[ROOT] == pytest.approx(ROOT_TIME, rel=REL)
    assert row["time_to_90_percent_consolidation"] == pytest.approx(TIME_90, rel=REL)
    for column, value in (
        ("corrected_zero_displacement_root_time", ZERO),
        ("displacement_at_90_percent_consolidation", AT_90),
    ):
        assert row[column] == pytest.approx(shift + sign * value, rel=REL, abs=1e-12)


# --- AC 7: reasons ------------------------------------------------------------------


def reason(points, **kwargs):
    row = quiet(readings(points, **kwargs)).iloc[0]
    return row[ROOT], row[f"{ROOT}_reason"], row


@pytest.mark.parametrize(
    ("points", "kwargs", "expected"),
    [
        (INCREMENT_4, {"branch": "constant_stress"}, "constant stress increment"),
        (
            [(t, 0.5) for t, _ in INCREMENT_4],
            {},
            "no displacement over the increment",
        ),
        (
            [(0, 0.0), (1, 0.1), (4, 0.2)],
            {},
            "fewer than 3 readings after the load was applied",
        ),
        (
            [(0, 0.0), (1, 0.1), (4, 0.45), (9, 0.8), (16, 0.9), (25, 1.0)],
            {},
            "fewer than 3 readings in the first half of the increment's movement",
        ),
        (
            [(0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0), (4, 0.9), (9, 1.0)],
            {},
            "the early readings don't move with the increment",
        ),
        (
            [
                *[(0, 0.0), (1, 0.30), (4, 0.40), (9, 0.41), (16, 0.41)],
                *[(25, 0.9), (36, 1.0)],
            ],
            {},
            "the curve is below the 1.15 line in its early portion: no straight "
            "early line",
        ),
        (
            [(t, d) for t, d in INCREMENT_4 if t <= 8],
            {},
            "t90 after the last reading",
        ),
    ],
)
def test_ac7_reasons(points, kwargs, expected):
    value, why, row = reason(points, **kwargs)
    assert np.isnan(value)
    assert why == expected
    assert np.isnan(row["time_to_90_percent_consolidation"])


def test_ac7_no_specimen_height_gives_the_points_but_no_cv():
    value, why, row = reason(INCREMENT_4, height=np.nan)
    assert np.isnan(value) and why == "no specimen height or void ratio for H̄"
    assert np.isnan(row["average_specimen_height"])
    assert row["time_to_90_percent_consolidation"] == pytest.approx(TIME_90, rel=REL)
    assert row["corrected_zero_displacement_root_time"] == pytest.approx(ZERO, rel=REL)


def test_ac7_no_height_column_needs_no_unit():
    frame = readings(INCREMENT_4).drop(columns="specimen_height")
    value, why = quiet(frame).iloc[0][[ROOT, f"{ROOT}_reason"]]
    assert np.isnan(value) and why == "no specimen height or void ratio for H̄"


def test_unloading_increments_are_oriented_by_their_own_movement():
    swelling = [(t, 1.0 - (d - 0.267)) for t, d in INCREMENT_4]
    value, why, _ = reason(swelling, branch="unloading")
    assert why is None and value == pytest.approx(ROOT_TIME, rel=REL)


# --- AC 8: readings left out and sorting --------------------------------------------


def test_ac8_readings_left_out_are_counted_in_one_note_each():
    points = [*INCREMENT_4, (np.nan, 0.6), (np.nan, 0.61), (5000, np.nan), (-1, 0.2)]
    frame = readings(points)
    rows = quiet(frame)
    assert rows.iloc[0][ROOT] == pytest.approx(ROOT_TIME, rel=REL)
    assert rows.attrs["consolidation_coefficient_from_readings"]["notes"] == [
        "Left out 2 readings with a blank elapsed_time (rows 15, 16).",
        "Left out 1 reading with a blank vertical_displacement (rows 17).",
        "Left out 1 reading with a negative elapsed_time, before the load was "
        "applied (rows 18).",
    ]


def test_ac8_an_unsorted_increment_gives_the_sorted_increments_cv():
    order = np.random.default_rng(7).permutation(len(INCREMENT_4))
    shuffled = [INCREMENT_4[i] for i in order]
    row = quiet(readings(shuffled)).iloc[0]
    assert row[ROOT] == pytest.approx(ROOT_TIME, rel=REL)


def test_increments_in_order_of_first_appearance_and_their_start_void_ratio():
    first = readings(INCREMENT_4, stage="4")
    second = readings(
        INCREMENT_4,
        stage="3",
        void_ratio_at_increment_start=np.nan,
        void_ratio_at_increment_end=0.720,
    )
    rows = quiet(pd.concat([first, second], ignore_index=True))
    assert list(rows["test_stage"]) == ["4", "3"]
    # Increment "3" takes increment "4"'s end void ratio, the previous in the rows.
    assert rows.iloc[1]["average_specimen_height"] == pytest.approx(
        20 * (1.748 + 1.720) / 2 / 1.8, rel=REL
    )
    assert rows.attrs["consolidation_coefficient_from_readings"]["notes"] == [
        "S1 increment 3 has no void_ratio_at_increment_start: each takes the "
        "previous increment's void_ratio_at_increment_end."
    ]


def test_load_branch_is_added_from_the_stresses_with_a_note():
    first = readings(INCREMENT_4, stage="1", applied_vertical_stress=100)
    second = readings(INCREMENT_4, stage="2", applied_vertical_stress=100)
    frame = pd.concat([first, second], ignore_index=True).drop(columns="load_branch")
    frame = ht.set_units(frame, {**UNITS, "applied_vertical_stress": "kPa"})
    rows = quiet(frame)
    assert list(rows["load_branch"]) == ["loading", "constant_stress"]
    assert rows.iloc[1][f"{ROOT}_reason"] == "constant stress increment"
    notes = rows.attrs["consolidation_coefficient_from_readings"]["notes"]
    assert notes[0].startswith("load_branch added by ht.analysis.oedometer_load_branch")


# --- AC 11: units and twins ---------------------------------------------------------


def test_ac11_twins_give_the_same_cv(site):
    si = quiet(site["site_si"])
    us = quiet(site["site_us"])
    for column in (
        ROOT,
        "time_to_90_percent_consolidation",
        "average_specimen_height",
        "corrected_zero_displacement_root_time",
        "displacement_at_90_percent_consolidation",
    ):
        np.testing.assert_allclose(si[column], us[column], rtol=1e-9)


def test_ac11_display_units_us(site):
    rows = quiet(site["site_si"], display_units="US")
    row = rows[rows["test_stage"] == "4"].iloc[0]
    assert row[ROOT] == pytest.approx(23.1466690, rel=1e-6)
    assert row["average_specimen_height"] == pytest.approx(0.770778653, rel=1e-6)
    assert row["corrected_zero_displacement_root_time"] == pytest.approx(
        ZERO / 25.4, rel=1e-9
    )
    assert row["time_to_90_percent_consolidation"] == pytest.approx(TIME_90, rel=REL)
    assert row["reported_coefficient_of_consolidation_root_time"] == pytest.approx(
        2.1 * 10.7639104, rel=1e-6
    )
    assert row["specimen_height"] == pytest.approx(20 / 25.4, rel=1e-9)
    units = rows.attrs["units"]
    assert (units[ROOT], units["average_specimen_height"]) == ("ft²/yr", "in")
    assert units["time_to_90_percent_consolidation"] == "min"
    assert units["reported_coefficient_of_consolidation_root_time"] == "ft²/yr"


def test_inputs_in_other_units_convert_through_pint():
    frame = readings([(60 * t, d / 25.4) for t, d in INCREMENT_4], height=20 / 25.4)
    frame = ht.set_units(
        frame,
        {"elapsed_time": "s", "vertical_displacement": "in", "specimen_height": "in"},
    )
    row = quiet(frame).iloc[0]
    assert row[ROOT] == pytest.approx(ROOT_TIME, rel=REL)
    assert row["time_to_90_percent_consolidation"] == pytest.approx(TIME_90, rel=REL)


# --- Errors -------------------------------------------------------------------------


@pytest.mark.parametrize("column", ["specimen_id", "test_stage", "elapsed_time"])
def test_a_missing_column_names_it_and_the_template(column):
    with pytest.raises(ColumnError, match=rf"df has no column '{column}'.*template"):
        FUNCTION(readings(INCREMENT_4).drop(columns=column))


def test_a_missing_displacement_column():
    frame = readings(INCREMENT_4).drop(columns="vertical_displacement")
    with pytest.raises(
        ColumnError, match=r"'vertical_displacement'.*ht.template\(\"oedometer_readings"
    ):
        FUNCTION(frame)


def test_times_without_units():
    frame = readings(INCREMENT_4)
    frame.attrs["units"] = {"vertical_displacement": "mm"}
    with pytest.raises(UnitsError, match="'elapsed_time' has no units"):
        FUNCTION(frame)


def test_a_time_in_a_length_unit():
    with pytest.raises(HangtuError, match="elapsed_time"):
        FUNCTION(readings(INCREMENT_4), units={"elapsed_time": "mm"})


def test_a_blank_increment():
    frame = readings(INCREMENT_4)
    frame.loc[3, "test_stage"] = None
    with pytest.raises(HangtuError, match=r"Rows 3 have a blank specimen_id or test"):
        FUNCTION(frame)


def test_display_units_must_be_si_or_us():
    with pytest.raises(HangtuError, match=r'display_units must be "SI", "US"'):
        FUNCTION(readings(INCREMENT_4), display_units="metric")
