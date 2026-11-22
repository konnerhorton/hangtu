"""ht.analysis.consolidation_coefficient_from_readings(), root time and log time.

The c2 spec's acceptance criteria (docs/work/m19c2-cv-readings.md). The golden
increment is BH1-U3's increment 4 in site_si.ags: its readings, hand-calculated
there from the readings as rounded (BS 1377-5:1990, 3.6.3.2 and 3.6.3.3). The generated
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

from . import conftest as terzaghi

DATA = Path(__file__).parents[1] / "data" / "ags"
MAP = DATA / "readings_map.csv"
#: The hand values are written to 9 significant figures, so they hold to 1e-8.
REL = 1e-8
FUNCTION = ht.analysis.consolidation_coefficient_from_readings
ROOT = "coefficient_of_consolidation_root_time"
LOG = "coefficient_of_consolidation_log_time"

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
#: AC 2's hand calculation, log time.
LOG_ZERO = 0.286666667
AT_100 = 0.560523057
AT_50 = 0.423594862
TIME_50 = 4.82957834
LOG_TIME = 2.06343562
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


# --- AC 2: the golden increment, log time ------------------------------------------


def test_ac2_log_time(site):
    row, rows = golden_row(site["site_si"])
    assert row["corrected_zero_displacement_log_time"] == pytest.approx(
        LOG_ZERO, rel=REL
    )
    assert row["displacement_at_100_percent_primary_consolidation"] == pytest.approx(
        AT_100, rel=REL
    )
    assert row["displacement_at_50_percent_consolidation"] == pytest.approx(
        AT_50, rel=REL
    )
    assert row["time_to_50_percent_consolidation"] == pytest.approx(TIME_50, rel=REL)
    assert row[LOG] == pytest.approx(LOG_TIME, rel=REL)
    assert row[f"{LOG}_basis"] == "rule"
    assert row[f"{LOG}_reason"] is None
    assert rows.attrs["units"][LOG] == "m2/yr"
    assert rows.attrs["units"]["time_to_50_percent_consolidation"] == "min"
    assert rows.attrs["units"]["displacement_at_50_percent_consolidation"] == "mm"


def test_ac2_intermediate_values():
    from hangtu.analysis import _consolidation_readings as module

    frame = readings(INCREMENT_4)
    data = module.increment_readings(
        frame.index,
        np.arange(len(frame)),
        frame["elapsed_time"].to_numpy(float),
        frame["vertical_displacement"].to_numpy(float),
    )
    log = module.log_time(data)
    assert log.reason is None
    # The secondary line over 240, 480 and 1440 min.
    assert list(np.flatnonzero(log.secondary.fitted)) == [12, 13, 14]
    assert log.secondary.intercept == pytest.approx(0.278448445, rel=REL)
    assert log.secondary.slope == pytest.approx(0.0102988527, rel=REL)
    # The tangent over 4, 8 and 15 min, 17.1 times as steep.
    assert list(np.flatnonzero(log.tangent.fitted)) == [6, 7, 8]
    assert log.tangent.intercept == pytest.approx(0.0362299771, rel=REL)
    assert log.tangent.slope == pytest.approx(0.175780553, rel=REL)
    assert log.tangent.slope / log.secondary.slope == pytest.approx(17.1, abs=0.05)
    # The pairs (0.5, 2), (1, 4), (2, 8); d0 their mean.
    assert list(data.times[log.pairs]) == [0.5, 1, 2]
    assert log.zero == pytest.approx(0.0196666667, rel=REL)
    assert np.log10(log.time_100) == pytest.approx(1.46371754, rel=REL)
    assert log.time_100 == pytest.approx(29.0882465, rel=REL)
    assert log.movement_100 == pytest.approx(0.293523057, rel=REL)
    assert log.movement_50 == pytest.approx(0.156594862, rel=REL)
    assert np.log10(log.time) == pytest.approx(0.683909216, rel=REL)


def test_ac2_on_a_hand_built_frame():
    row = quiet(readings(INCREMENT_4)).iloc[0]
    assert row["time_to_50_percent_consolidation"] == pytest.approx(TIME_50, rel=REL)
    assert row[LOG] == pytest.approx(LOG_TIME, rel=REL)


def test_the_result_columns_in_order():
    rows = quiet(readings(INCREMENT_4))
    new = list(rows.columns[list(rows.columns).index("average_specimen_height") :])
    assert new == [
        "average_specimen_height",
        "corrected_zero_displacement_root_time",
        "displacement_at_90_percent_consolidation",
        "time_to_90_percent_consolidation",
        ROOT,
        f"{ROOT}_basis",
        f"{ROOT}_reason",
        "corrected_zero_displacement_log_time",
        "displacement_at_100_percent_primary_consolidation",
        "displacement_at_50_percent_consolidation",
        "time_to_50_percent_consolidation",
        LOG,
        f"{LOG}_basis",
        f"{LOG}_reason",
    ]


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


@pytest.mark.parametrize("cv", [0.3, 1, 2, 5, 10])
@pytest.mark.parametrize(("immediate", "secondary"), COMPRESSION)
def test_ac3_log_time_recovers_the_generating_cv(cv, immediate, secondary):
    row = quiet(generated(cv, immediate, secondary)).iloc[0]
    assert row[LOG] == pytest.approx(cv, rel=0.10)


@pytest.mark.parametrize(("immediate", "secondary"), COMPRESSION)
def test_ac3_at_cv_20_log_time_has_too_few_pairs(immediate, secondary):
    row = quiet(generated(20, immediate, secondary)).iloc[0]
    assert np.isnan(row[LOG])
    assert row[f"{LOG}_reason"] == (
        "fewer than 3 pairs of times in the ratio 1:4 before the inflexion"
    )


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
    assert row[LOG] == pytest.approx(LOG_TIME, rel=REL)
    assert row["time_to_50_percent_consolidation"] == pytest.approx(TIME_50, rel=REL)
    for column, value in (
        ("corrected_zero_displacement_root_time", ZERO),
        ("displacement_at_90_percent_consolidation", AT_90),
        ("corrected_zero_displacement_log_time", LOG_ZERO),
        ("displacement_at_100_percent_primary_consolidation", AT_100),
        ("displacement_at_50_percent_consolidation", AT_50),
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


@pytest.mark.parametrize(
    "points",
    [
        INCREMENT_4,
        [(t, 0.5) for t, _ in INCREMENT_4],
        [(0, 0.0), (1, 0.1), (4, 0.2)],
    ],
)
def test_ac7_the_increment_reasons_apply_to_both_methods(points):
    for kwargs in ({"branch": "constant_stress"}, {}):
        if points is INCREMENT_4 and not kwargs:
            continue
        rows = quiet(readings(points, **kwargs))
        assert rows.iloc[0][f"{ROOT}_reason"] == rows.iloc[0][f"{LOG}_reason"]
        assert np.isnan(rows.iloc[0][LOG])


#: A first reading far past the rest, as a misread gauge gives: d0 from the
#: pairs (0.1, 0.4), (0.25, 1), (0.5, 2) is 0.622, d100 1.163, so d50 0.892 is
#: below the first reading's 1.0.
SPIKE = [
    *[(0, 0.0), (0.1, 1.0), (0.25, 0.30), (0.5, 0.35), (1, 0.45), (2, 0.65)],
    *[(4, 0.95), (8, 1.10), (15, 1.15), (30, 1.17), (60, 1.18), (120, 1.19)],
    *[(240, 1.20), (480, 1.21), (1440, 1.22)],
]
#: Two steps: the tangent over 1, 2 and 4 min is above the secondary line at
#: its middle reading, 2 min, so the lines cross before it.
TWO_STEPS = [
    *[(0, 0.0), (0.1, 0.02), (0.25, 0.03), (0.5, 0.05), (1, 0.10), (2, 0.50)],
    *[(4, 0.90), (8, 1.0), (15, 1.0), (30, 1.0), (60, 1.0), (120, 1.0)],
    *[(240, 1.05), (480, 1.15), (1440, 1.30)],
]

#: Readings that dip after 1 min, as a reset gauge gives: the pairs (0.25, 1),
#: (0.5, 2), (1, 4) give d0 = (0.9 + 1.6 + 1.3) / 3 = 1.267, d100 0.967, so
#: d50 1.117 is above every reading.
DIP = [
    *[(0, 0.0), (0.1, 0.85), (0.25, 0.9), (0.5, 0.9), (1, 0.9), (2, 0.2)],
    *[(4, 0.5), (8, 0.85), (15, 0.95), (30, 0.97), (60, 0.98), (120, 0.99)],
    *[(240, 1.0), (480, 1.01), (1440, 1.02)],
]


@pytest.mark.parametrize(
    ("points", "expected"),
    [
        # Stop at 10 min: only 2 and 10 min in the last cycle.
        (
            [(0, 0.0), (0.1, 0.1), (0.5, 0.2), (2, 0.3), (10, 0.4)],
            "fewer than 3 readings in the last log cycle of time",
        ),
        (
            [(0, 0.0), (100, 0.1), (200, 0.2), (400, 0.3), (1000, 0.4)],
            "no three readings before the last log cycle",
        ),
        # A straight line in log t: the tangent is as steep as the last cycle.
        (
            [(0, 0.0), *[(t, 1 + np.log10(t)) for t, _ in INCREMENT_4[1:]]],
            "no clear secondary portion: the tangent is less than twice as steep "
            "as the last log cycle",
        ),
        # Stopped at 15 min, the curve is still steep in its last cycle.
        (
            [(t, d) for t, d in INCREMENT_4 if t <= 15],
            "no clear secondary portion: the tangent is less than twice as steep "
            "as the last log cycle",
        ),
        (TWO_STEPS, "d100 outside the readings"),
        (SPIKE, "t50 before the first reading"),
        (DIP, "t50 after the last reading"),
    ],
)
def test_ac7_log_time_reasons(points, expected):
    row = quiet(readings(points)).iloc[0]
    assert np.isnan(row[LOG])
    assert row[f"{LOG}_reason"] == expected
    for column in (
        "time_to_50_percent_consolidation",
        "corrected_zero_displacement_log_time",
        "displacement_at_100_percent_primary_consolidation",
        "displacement_at_50_percent_consolidation",
    ):
        assert np.isnan(row[column])


def test_ac7_no_specimen_height_gives_the_points_but_no_cv():
    value, why, row = reason(INCREMENT_4, height=np.nan)
    assert np.isnan(value) and why == "no specimen height or void ratio for H̄"
    assert np.isnan(row["average_specimen_height"])
    assert row["time_to_90_percent_consolidation"] == pytest.approx(TIME_90, rel=REL)
    assert row["corrected_zero_displacement_root_time"] == pytest.approx(ZERO, rel=REL)
    assert np.isnan(row[LOG])
    assert row[f"{LOG}_reason"] == "no specimen height or void ratio for H̄"
    assert row["time_to_50_percent_consolidation"] == pytest.approx(TIME_50, rel=REL)
    assert row["corrected_zero_displacement_log_time"] == pytest.approx(
        LOG_ZERO, rel=REL
    )


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
    # site_us.ags writes the displacements to 10 significant figures in inches;
    # t50 interpolates between differences of them, which carries that rounding
    # to 1.5e-9, so log time holds to 1e-8.
    for column in (
        LOG,
        "time_to_50_percent_consolidation",
        "corrected_zero_displacement_log_time",
        "displacement_at_100_percent_primary_consolidation",
        "displacement_at_50_percent_consolidation",
    ):
        np.testing.assert_allclose(si[column], us[column], rtol=1e-8)


def test_ac11_display_units_us(site):
    rows = quiet(site["site_si"], display_units="US")
    row = rows[rows["test_stage"] == "4"].iloc[0]
    assert row[ROOT] == pytest.approx(23.1466690, rel=1e-6)
    assert row["average_specimen_height"] == pytest.approx(0.770778653, rel=1e-6)
    assert row["corrected_zero_displacement_root_time"] == pytest.approx(
        ZERO / 25.4, rel=1e-9
    )
    assert row["time_to_90_percent_consolidation"] == pytest.approx(TIME_90, rel=REL)
    assert row[LOG] == pytest.approx(LOG_TIME * 10.7639104, rel=1e-6)
    assert row["displacement_at_50_percent_consolidation"] == pytest.approx(
        AT_50 / 25.4, rel=1e-9
    )
    assert row["reported_coefficient_of_consolidation_root_time"] == pytest.approx(
        2.1 * 10.7639104, rel=1e-6
    )
    assert row["specimen_height"] == pytest.approx(20 / 25.4, rel=1e-9)
    units = rows.attrs["units"]
    assert (units[ROOT], units["average_specimen_height"]) == ("ft²/yr", "in")
    assert (units[LOG], units["time_to_50_percent_consolidation"]) == ("ft²/yr", "min")
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
    # Times from seconds still pair: 4 x 6 s against 24 s, within rounding.
    assert row[LOG] == pytest.approx(LOG_TIME, rel=REL)
    assert row["time_to_50_percent_consolidation"] == pytest.approx(TIME_50, rel=REL)


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


# --- AC 4: overrides ----------------------------------------------------------------

MINUTES = {"elapsed_time_start": "min", "elapsed_time_end": "min"}


def overrides(*rows, units=MINUTES):
    """Overrides for S1 increment 1, in the template's shape."""
    columns = list(ht.template("consolidation_overrides").columns)
    frame = pd.DataFrame(
        [("S1", "1", *row) for row in rows], columns=columns, dtype=object
    )
    for column in ("elapsed_time_start", "elapsed_time_end"):
        frame[column] = pd.to_numeric(frame[column])
    return ht.set_units(frame, units) if units else frame


EARLY_OVERRIDE = ("root_time", "early", 0.25, 4, "0.1 min read before the load")
SECONDARY_OVERRIDE = ("log_time", "secondary", 120, 1440, "secondary from 2 hours")


def test_the_overrides_template():
    assert list(ht.template("consolidation_overrides").columns) == [
        "specimen_id",
        "test_stage",
        "consolidation_method",
        "curve_portion",
        "elapsed_time_start",
        "elapsed_time_end",
        "override_reason",
    ]


def test_ac4_root_time_early_override():
    from hangtu.analysis import _consolidation_readings as module

    rows = quiet(readings(INCREMENT_4), overrides=overrides(EARLY_OVERRIDE))
    row = rows.iloc[0]
    assert row["time_to_90_percent_consolidation"] == pytest.approx(19.7049019, rel=REL)
    assert row[ROOT] == pytest.approx(2.15911359, rel=REL)
    assert row[f"{ROOT}_basis"] == "override"
    assert row[f"{LOG}_basis"] == "rule"
    assert row[LOG] == pytest.approx(LOG_TIME, rel=REL)
    frame = readings(INCREMENT_4)
    data = module.increment_readings(
        frame.index,
        np.arange(len(frame)),
        frame["elapsed_time"].to_numpy(float),
        frame["vertical_displacement"].to_numpy(float),
    )
    root = module.root_time(data, (0.25, 4))
    assert root.zero == pytest.approx(0.0190752377, rel=REL)
    assert root.slope == pytest.approx(0.0620181363, rel=REL)


def test_ac4_log_time_secondary_override():
    rows = quiet(readings(INCREMENT_4), overrides=overrides(SECONDARY_OVERRIDE))
    row = rows.iloc[0]
    assert row["corrected_zero_displacement_log_time"] == pytest.approx(
        LOG_ZERO, rel=REL
    )
    assert row["time_to_50_percent_consolidation"] == pytest.approx(4.87474524, rel=REL)
    assert row[LOG] == pytest.approx(2.04431687, rel=REL)
    assert (row[f"{LOG}_basis"], row[f"{ROOT}_basis"]) == ("override", "rule")
    assert row[ROOT] == pytest.approx(ROOT_TIME, rel=REL)
    from hangtu.analysis import _consolidation_readings as module

    frame = readings(INCREMENT_4)
    data = module.increment_readings(
        frame.index,
        np.arange(len(frame)),
        frame["elapsed_time"].to_numpy(float),
        frame["vertical_displacement"].to_numpy(float),
    )
    log = module.log_time(data, {"secondary": (120, 1440)})
    assert log.secondary.intercept == pytest.approx(0.281019115, rel=REL)
    assert log.secondary.slope == pytest.approx(0.00941096958, rel=REL)
    assert log.time_100 == pytest.approx(29.6044854, rel=REL)


def test_ac4_both_overrides_are_recorded():
    given = overrides(EARLY_OVERRIDE, SECONDARY_OVERRIDE)
    rows = quiet(readings(INCREMENT_4), overrides=given)
    assert list(rows.iloc[0][[f"{ROOT}_basis", f"{LOG}_basis"]]) == [
        "override",
        "override",
    ]
    recorded = rows.attrs["consolidation_coefficient_from_readings"]["overrides"]
    assert [r["override_reason"] for r in recorded] == [
        "0.1 min read before the load",
        "secondary from 2 hours",
    ]
    assert recorded[1]["elapsed_time_start"] == 120


def test_without_overrides_none_are_recorded():
    rows = quiet(readings(INCREMENT_4))
    assert rows.attrs["consolidation_coefficient_from_readings"]["overrides"] == []


def test_override_times_in_seconds_convert_to_minutes():
    given = overrides(
        ("root_time", "early", 15, 240, "in seconds"),
        units={"elapsed_time_start": "s", "elapsed_time_end": "s"},
    )
    row = quiet(readings(INCREMENT_4), overrides=given).iloc[0]
    assert row[ROOT] == pytest.approx(2.15911359, rel=REL)


def test_log_time_early_override_takes_every_pair_in_the_range():
    # 0.25 to 4 min holds the pairs (0.25, 1), (0.5, 2) and (1, 4):
    # d0 = (2 x 0.050 - 0.081 + 2 x 0.063 - 0.107 + 2 x 0.081 - 0.143) / 3.
    given = overrides(("log_time", "early", 0.25, 4, "the later pairs"))
    row = quiet(readings(INCREMENT_4), overrides=given).iloc[0]
    assert row["corrected_zero_displacement_log_time"] == pytest.approx(
        0.267 + (0.019 + 0.019 + 0.019) / 3, rel=REL
    )
    assert row[f"{LOG}_basis"] == "override"


def test_log_time_inflexion_override_fits_the_tangent_to_the_range():
    # 8 to 30 min: the next-steepest three, slope 0.159859434 (AC 2). Its
    # middle reading, 15 min, lets the pair (2, 8) in, as 4 x 4 = 16 > 15
    # keeps (4, 16) out: the pairs are the same three.
    from hangtu.analysis import _consolidation_readings as module

    frame = readings(INCREMENT_4)
    data = module.increment_readings(
        frame.index,
        np.arange(len(frame)),
        frame["elapsed_time"].to_numpy(float),
        frame["vertical_displacement"].to_numpy(float),
    )
    log = module.log_time(data, {"inflexion": (8, 30)})
    assert log.tangent.slope == pytest.approx(0.159859434, rel=REL)
    assert list(data.times[log.pairs]) == [0.5, 1, 2]
    given = overrides(("log_time", "inflexion", 8, 30, "the later three"))
    row = quiet(frame, overrides=given).iloc[0]
    assert row[f"{LOG}_basis"] == "override"
    assert row["time_to_50_percent_consolidation"] == pytest.approx(log.time)


@pytest.mark.parametrize(
    ("row", "column", "expected"),
    [
        (
            ("root_time", "early", 3, 5, "one reading"),
            ROOT,
            "the override for early holds 1 reading",
        ),
        (
            ("log_time", "secondary", 1000, 1500, "one reading"),
            LOG,
            "the override for secondary holds 1 reading",
        ),
        (
            ("log_time", "inflexion", 9, 10, "none"),
            LOG,
            "the override for inflexion holds 0 readings",
        ),
        (
            ("log_time", "early", 1, 3, "no 1:4 pair"),
            LOG,
            "the override for early holds no pair of times in the ratio 1:4",
        ),
    ],
)
def test_ac4_a_range_too_short_gives_a_reason(row, column, expected):
    result = quiet(readings(INCREMENT_4), overrides=overrides(row)).iloc[0]
    assert np.isnan(result[column])
    assert result[f"{column}_reason"] == expected
    assert result[f"{column}_basis"] == "override"


# --- AC 9: the overrides' errors ----------------------------------------------------


def run_overrides(given):
    return FUNCTION(readings(INCREMENT_4), overrides=given)


@pytest.mark.parametrize(
    ("rows", "match"),
    [
        (
            [("root_time", "early", 0.25, 4, "ok"), ("root_time", "early", 1, 4, "x")],
            r"Override row 3 \(the header is row 1\) repeats row 2",
        ),
        (
            [("taylor", "early", 0.25, 4, "x")],
            r"Override row 2 .* consolidation_method 'taylor'\. Use 'root_time' or "
            r"'log_time'",
        ),
        (
            [("log_time", "middle", 0.25, 4, "x")],
            r"Override row 2 .* curve_portion 'middle'\. Use 'early', 'inflexion', "
            r"'secondary'",
        ),
        (
            [("root_time", "secondary", 120, 1440, "x")],
            r"Override row 2 .* secondary line for root_time, which has only an "
            r"early line",
        ),
        (
            [("root_time", "inflexion", 4, 15, "x")],
            r"Override row 2 .* inflexion line for root_time",
        ),
        (
            [("root_time", "early", 4, 0.25, "x")],
            r"Override row 2 .* elapsed_time_start 4 after elapsed_time_end 0\.25",
        ),
        (
            [("root_time", "early", 0.25, 4, "  ")],
            r"Override row 2 .* blank override_r",
        ),
        (
            [("root_time", "early", 0.25, 4, None)],
            r"Override row 2 .* blank override_r",
        ),
        (
            [("root_time", "early", np.nan, 4, "x")],
            r"Override row 2 .* blank elapsed_time_start or elapsed_time_end",
        ),
    ],
)
def test_ac9_override_errors_name_the_row(rows, match):
    with pytest.raises(HangtuError, match=match):
        run_overrides(overrides(*rows))


def test_ac9_an_override_for_an_increment_the_readings_dont_have():
    given = overrides(EARLY_OVERRIDE)
    given.loc[0, "test_stage"] = "7"
    with pytest.raises(
        HangtuError, match=r"Override row 2 .* specimen 'S1' increment '7', which"
    ):
        run_overrides(given)


def test_ac9_override_times_without_units():
    with pytest.raises(UnitsError, match="'elapsed_time_start' has no units"):
        run_overrides(overrides(EARLY_OVERRIDE, units=None))


def test_ac9_override_times_in_a_length_unit():
    given = overrides(EARLY_OVERRIDE)
    given.attrs["units"] = {**MINUTES, "elapsed_time_start": "mm"}
    with pytest.raises(HangtuError, match="elapsed_time_start"):
        run_overrides(given)


def test_ac9_an_overrides_column_missing():
    given = overrides(EARLY_OVERRIDE).drop(columns="override_reason")
    with pytest.raises(
        ColumnError,
        match=r"overrides has no column 'override_reason'.*consolidation_overrides",
    ):
        run_overrides(given)


def test_ac9_overrides_must_be_a_frame():
    with pytest.raises(HangtuError, match="overrides must be a pandas DataFrame"):
        run_overrides([EARLY_OVERRIDE])
