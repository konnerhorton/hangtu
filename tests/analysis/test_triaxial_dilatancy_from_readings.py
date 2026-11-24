"""ht.analysis.triaxial_dilatancy_from_readings() (docs/analysis/strength.md §9).

Golden values are the M23 (b) spec's hand calculations: on G1 the εv readings
at 6.0, 7.0 and 8.25 % lie on a line of slope -0.6, so r = 0.6 and
ψ = asin(0.6 / 2.6) = 13.34°; on the example's B-1-U5 specimen 1, the readings
at 3.5, 4.5 and 5.1 % give r = 0.0235 and ψ = 0.66°.
"""

import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError, UnitsError

from .conftest import G1_Q, g1, stage_frame, stages_frame, triaxial_goldens

DATA = Path(ht.examples.path("site.ags")).parent
ANGLE = "dilatancy_angle"
RATE = "dilation_rate"
REASON = "dilatancy_angle_reason"
MAX_Q = "max_deviator_stress"


def dilatancy(df, **kwargs):
    """The analysis, failing on any warning."""
    kwargs.setdefault("failure_criterion", MAX_Q)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return ht.analysis.triaxial_dilatancy_from_readings(df, **kwargs)


def assert_angle_or_reason(rows):
    assert (rows[ANGLE].notna() ^ rows[REASON].notna()).all(), rows[[ANGLE, REASON]]


# --- AC 4: G1 and G2 ------------------------------------------------------------------


@pytest.mark.parametrize("offset", [0.0, 50.0])
def test_g1(offset):
    row = dilatancy(g1(offset)).iloc[0]
    assert row[RATE] == pytest.approx(0.600, abs=5e-4)
    assert row[ANGLE] == pytest.approx(13.34, abs=0.01)
    assert row[ANGLE] == pytest.approx(math.degrees(math.asin(0.6 / 2.6)), rel=1e-6)
    assert row[REASON] is None


def test_g2_from_the_example_project(tmp_path):
    p = ht.Project.from_ags(
        DATA / "site.ags", db=tmp_path / "site.sqlite", display_units="US"
    )
    p.set_readings_map(ht.examples.path("readings_map.csv"))
    with pytest.warns(UserWarning, match="interpolated in strain"):
        rows = ht.analysis.triaxial_dilatancy_from_readings(
            p.triaxial_readings(), failure_criterion=MAX_Q
        )
    row = rows[rows["sample_reference"].eq("B-1-U5")].iloc[0]
    assert row[ANGLE] == pytest.approx(0.66, abs=0.01)
    assert row[RATE] == pytest.approx(0.0235, abs=1e-4)
    assert_angle_or_reason(rows)
    assert rows.attrs["units"][ANGLE] == "deg"


# --- AC 6: ψ's limits -----------------------------------------------------------------


@pytest.mark.parametrize("test_type", ["CU", "UU", "CIUC", "UUM"])
def test_undrained_stages_have_no_volume_change(test_type):
    df = g1()
    df["test_type"] = test_type
    df["excess_pore_pressure"] = 0.0
    row = dilatancy(df).iloc[0]
    assert np.isnan(row[ANGLE]) and np.isnan(row[RATE])
    assert row[REASON] == "undrained: no volume change"


def test_a_blank_test_type_has_unknown_drainage():
    df = g1()
    df["test_type"] = None
    assert dilatancy(df).iloc[0][REASON] == "test_type blank: drainage unknown"


def test_a_drained_extension_stage_is_named():
    df = g1()
    df["test_type"] = "CIDE"
    assert "isn't a drained compression stage" in dilatancy(df).iloc[0][REASON]


def test_a_drained_stage_without_volumetric_strain():
    row = dilatancy(stage_frame("S", "CD", G1_Q)).iloc[0]
    assert np.isnan(row[ANGLE])
    assert row[REASON] == "no volumetric strain readings"


def test_one_reading_in_the_window():
    volumetric = {0: 0, 2: 0.35, 4: 0.20, 8.25: -1.45}
    row = dilatancy(stage_frame("S", "CD", G1_Q, volumetric=volumetric)).iloc[0]
    assert np.isnan(row[ANGLE])
    assert row[REASON].startswith(
        "1 volumetric strain reading between 6 % and 8.25 % axial strain"
    )


def test_contracting_faster_than_axial_strain_has_no_angle():
    volumetric = {0: 0, 6: 0.0, 7.0: 1.2, 8.25: 2.7}  # slope 1.2: r = -1.2
    row = dilatancy(stage_frame("S", "CD", G1_Q, volumetric=volumetric)).iloc[0]
    assert np.isnan(row[ANGLE])
    assert row[RATE] == pytest.approx(-1.2, rel=1e-9)
    assert "-1.2" in row[REASON]


def test_a_stage_contracting_at_failure_keeps_its_negative_angle():
    volumetric = {0: 0, 6: 1.0, 7.0: 1.3, 8.25: 1.675}  # slope 0.3: r = -0.3
    row = dilatancy(stage_frame("S", "CD", G1_Q, volumetric=volumetric)).iloc[0]
    assert row[RATE] == pytest.approx(-0.3, rel=1e-9)
    assert row[ANGLE] == pytest.approx(math.degrees(math.asin(-0.3 / 1.7)), rel=1e-9)
    assert row[ANGLE] < 0 and row[REASON] is None


def test_every_row_has_an_angle_or_a_reason():
    rows = dilatancy(
        stages_frame(
            g1(),
            stage_frame("A", "CD", G1_Q),
            stage_frame("B", "CU", G1_Q, excess={0: 0, 8.25: 10}),
        )
    )
    assert_angle_or_reason(rows)
    assert_angle_or_reason(dilatancy(triaxial_goldens()))


# --- AC 8: the failure rows -----------------------------------------------------------


@pytest.mark.parametrize("criterion", ["max_deviator_stress", "max_stress_ratio"])
def test_the_failure_rows_are_unchanged(criterion):
    df = stages_frame(g1(), triaxial_goldens("A", "B", "C"))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        failure = ht.analysis.triaxial_failure_from_readings(
            df, failure_criterion=criterion
        )
    rows = dilatancy(df, failure_criterion=criterion)
    assert list(rows.columns) == [*failure.columns, ANGLE, RATE, REASON]
    pd.testing.assert_frame_equal(rows[failure.columns], failure)


def test_the_window_ends_at_the_failure_reading():
    # An εv reading past the failure reading (8.25 %) is outside the window.
    by_q = dilatancy(g1()).iloc[0]
    later = g1()
    later.loc[later["axial_strain"] == 10, "volumetric_strain"] = -5.0
    assert dilatancy(later).iloc[0][RATE] == pytest.approx(by_q[RATE], rel=1e-12)


# --- AC 10: attrs and arguments -------------------------------------------------------


def test_dilatancy_from_in_attrs_and_the_window_moves():
    assert dilatancy(g1()).attrs["dilatancy_from"] == 0.95
    rows = dilatancy(g1(), dilatancy_from=0.85)
    assert rows.attrs["dilatancy_from"] == 0.85
    # 0.85 × 300 = 255 first reached at 3 %: εv at 4, 6, 7 and 8.25 %.
    x = np.array([4, 6, 7.0, 8.25])
    y = np.array([0.20, -0.10, -0.70, -1.45])
    assert rows.iloc[0][RATE] == pytest.approx(-np.polyfit(x, y, 1)[0], rel=1e-9)


@pytest.mark.parametrize("bad", [0, 1.2, -0.5, "0.95", None, True, math.nan])
def test_a_bad_dilatancy_from_raises(bad):
    with pytest.raises(HangtuError, match="dilatancy_from"):
        ht.analysis.triaxial_dilatancy_from_readings(
            g1(), failure_criterion=MAX_Q, dilatancy_from=bad
        )


def test_a_volumetric_strain_in_another_unit_raises():
    df = g1()
    df.attrs["units"] = {**df.attrs["units"], "volumetric_strain": "mm"}
    with pytest.raises(UnitsError, match="volumetric_strain"):
        ht.analysis.triaxial_dilatancy_from_readings(df, failure_criterion=MAX_Q)
