"""ht.analysis.gradation(): D-values, Cu and Cc (docs/drafts/analysis.md §3.3, §3.7)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError, UnitsError

#: Curve A (§3.7).
SIZES = [0.075, 0.15, 0.3, 0.6, 1.18, 2.36, 4.75]
PASSING = [4, 12, 30, 55, 75, 90, 100]


def curve(sizes=SIZES, passing=PASSING, specimen="A", unit="mm", **columns):
    df = pd.DataFrame(
        {
            "specimen_id": specimen,
            "particle_size": sizes,
            "percent_passing": passing,
            **columns,
        }
    )
    return ht.set_units(df, {"particle_size": unit})


def one(df, **kwargs):
    out = ht.analysis.gradation(df, **kwargs)
    assert len(out) == 1
    return out.iloc[0]


# --- Golden values ---------------------------------------------------------------


def test_curve_a_golden_values():
    row = one(curve())
    # D10 between (0.075, 4) and (0.15, 12): 0.075 * 2 ** (6 / 8) = 0.12613.
    assert row["d10"] == pytest.approx(0.075 * 2**0.75)
    assert row["d10"] == pytest.approx(0.1261, abs=5e-5)
    # D30 is on a point.
    assert row["d30"] == pytest.approx(0.3)
    # D60 between (0.6, 55) and (1.18, 75): 0.6 * (1.18 / 0.6) ** (5 / 20).
    assert row["d60"] == pytest.approx(0.6 * (1.18 / 0.6) ** 0.25)
    assert row["d60"] == pytest.approx(0.7105, abs=5e-5)
    assert row["uniformity_coefficient"] == pytest.approx(5.633, abs=5e-4)
    assert row["curvature_coefficient"] == pytest.approx(1.004, abs=5e-4)


def test_d30_interpolated_when_its_point_is_removed():
    sizes = [s for s in SIZES if s != 0.3]
    passing = [p for p in PASSING if p != 30]
    # Between (0.15, 12) and (0.6, 55): 0.15 * 4 ** (18 / 43).
    assert one(curve(sizes, passing))["d30"] == pytest.approx(0.15 * 4 ** (18 / 43))


def test_shuffled_rows_give_the_same_answer():
    df = curve()
    shuffled = df.sample(frac=1, random_state=3)
    expected = one(df)[["d10", "d30", "d60"]].to_numpy(dtype=float)
    got = one(shuffled)[["d10", "d30", "d60"]].to_numpy(dtype=float)
    assert got == pytest.approx(expected)


def test_inches_are_converted_before_interpolating():
    inches = [size / 25.4 for size in SIZES]
    row = one(curve(inches, unit="in"))
    assert row["d10"] == pytest.approx(0.075 * 2**0.75)


def test_other_d_values():
    row = one(curve(), d_values=(15, 85))
    assert {"d15", "d85"} <= set(row.index)
    assert "d10" not in row.index
    # Cu and Cc still come from D10, D30 and D60.
    assert row["uniformity_coefficient"] == pytest.approx(5.633, abs=5e-4)
    # D85 between (1.18, 75) and (2.36, 90): 1.18 * 2 ** (10 / 15).
    assert row["d85"] == pytest.approx(1.18 * 2 ** (10 / 15))


# --- Never extrapolated -------------------------------------------------------------


def test_curve_starting_above_ten_percent_has_blank_d10():
    with (
        pytest.warns(UserWarning, match="D10 in 1 curve"),
        pytest.warns(UserWarning, match="Fractions left blank"),
    ):
        row = one(curve(SIZES[1:], PASSING[1:]))
    assert np.isnan(row["d10"])
    assert np.isnan(row["uniformity_coefficient"])
    assert row["d30"] == pytest.approx(0.3)


def test_curve_not_reaching_sixty_percent_has_blank_d60():
    with (
        pytest.warns(UserWarning, match="D60 in 1 curve"),
        pytest.warns(UserWarning, match="Fractions left blank"),
    ):
        row = one(curve(SIZES[:4], PASSING[:4]))
    assert np.isnan(row["d60"])


def test_finest_crossing_on_a_flat_run():
    row = one(curve([0.075, 0.15, 0.3, 0.6], [5, 10, 10, 100]))
    assert row["d10"] == pytest.approx(0.15)


# --- Non-monotonic curves --------------------------------------------------------


def test_small_dip_is_noise():
    # Passing falls from 12.0 to 11.6 toward coarser sizes: 0.4 points.
    row = one(curve([0.075, 0.15, 0.3, 0.6], [4, 12, 11.6, 100]))
    assert row["d10"] == pytest.approx(0.075 * 2**0.75)


def test_drop_beyond_the_qc_tolerance_blanks_the_curve():
    with pytest.warns(UserWarning, match="rises by more than 0.5 percentage points"):
        row = one(curve([0.075, 0.15, 0.3, 0.6], [4, 14, 12, 100]))
    assert np.isnan(row[["d10", "d30", "d60"]].to_numpy(dtype=float)).all()


# --- Curves and rows ----------------------------------------------------------------


def test_one_row_per_curve_with_constant_columns_carried():
    first = curve(specimen="S1", loca_id="BH1", depth=2.0, qualifier=None)
    second = curve(specimen="S1", loca_id="BH2", depth=4.0)
    second.loc[0, "qualifier"] = "<"
    df = pd.concat([second, first], ignore_index=True)
    df = ht.set_units(df, {"particle_size": "mm", "depth": "ft"})
    out = ht.analysis.gradation(df)
    assert out["loca_id"].tolist() == ["BH2", "BH1"]
    assert out["specimen_id"].tolist() == ["S1", "S1"]
    assert out["depth"].tolist() == [4.0, 2.0]
    assert "qualifier" not in out.columns
    assert "particle_size" not in out.columns
    assert out.attrs["units"] == {"depth": "ft", "d10": "mm", "d30": "mm", "d60": "mm"}


def test_curve_with_one_point_gets_blanks_and_a_warning():
    df = pd.concat([curve(), curve([0.3], [50], specimen="B")], ignore_index=True)
    df = ht.set_units(df, {"particle_size": "mm"})
    with pytest.warns(UserWarning, match="1 curve has fewer than two points"):
        out = ht.analysis.gradation(df)
    assert out["specimen_id"].tolist() == ["A", "B"]
    assert np.isnan(out.loc[1, "d30"])


def test_blank_points_are_left_out_and_counted():
    df = curve(passing=[4, 12, 30, None, 75, 90, 100])
    with pytest.warns(UserWarning, match="Left out 1 point"):
        row = one(df)
    assert row["d10"] == pytest.approx(0.075 * 2**0.75)


def test_input_is_not_modified():
    df = curve()
    before = df.copy()
    ht.analysis.gradation(df)
    pd.testing.assert_frame_equal(df, before)


# --- Errors -------------------------------------------------------------------------


def test_missing_column_lists_the_columns():
    df = curve().drop(columns="percent_passing")
    with pytest.raises(ColumnError, match="'percent_passing' not found"):
        ht.analysis.gradation(df)


def test_particle_size_without_units_is_an_error():
    df = curve()
    df.attrs = {}
    with pytest.raises(UnitsError, match="'particle_size' has no units"):
        ht.analysis.gradation(df)


@pytest.mark.parametrize(
    ("sizes", "passing", "message"),
    [
        ([0, 0.15], [4, 12], "sizes of 0 or less in rows 0"),
        ([0.075, 0.15], [4, 120], "outside 0 to 100 in rows 1"),
        ([0.075, 0.075, 0.15], [4, 5, 12], "Rows 0, 1 are two points at the same"),
    ],
)
def test_bad_points_are_errors(sizes, passing, message):
    with pytest.raises(HangtuError, match=message):
        ht.analysis.gradation(curve(sizes, passing))


def test_blank_specimen_id_is_an_error():
    df = curve()
    df.loc[2, "specimen_id"] = None
    with pytest.raises(HangtuError, match="Rows 2 have a blank specimen_id"):
        ht.analysis.gradation(df)


@pytest.mark.parametrize("bad", [0, 100, 10.5, True, "10"])
def test_bad_d_values_are_errors(bad):
    with pytest.raises(HangtuError, match="d_values must be whole-number"):
        ht.analysis.gradation(curve(), d_values=(10, bad))
