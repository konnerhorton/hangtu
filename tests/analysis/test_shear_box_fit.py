"""ht.analysis.shear_box_fit() (docs/work/m17b-shear-box-fit.md, AC 1-13).

Golden values are the spec's, hand-calculated from its Derivation: the
least-squares line τ = a + b σn, free (b = Sxy / Sxx, a = ȳ - b x̄) and through
the origin (b = Σσnτ / Σσn²), then c = a and φ = arctan b. Points are (σn, τ).
"""

import json
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError, UnitsError

DATA = Path(__file__).parents[1] / "data" / "ags"
#: 1 psf in kPa: 0.45359237 kg × 9.80665 m/s² / 0.3048² m² (exact).
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000
REL = 1e-7
STRESS_UNITS = {
    "applied_normal_stress": "kPa",
    "peak_shear_stress": "kPa",
    "residual_shear_stress": "kPa",
}


def _frame(peak, residual=None, unit="kPa", **columns):
    """Stages with peak points ``(σn, τ)`` and, if given, residual ``τ`` per stage."""
    normal, shear = (
        np.array(values, dtype=float) for values in zip(*peak, strict=True)
    )
    df = pd.DataFrame(
        {
            "applied_normal_stress": normal,
            "peak_shear_stress": shear,
            "residual_shear_stress": (
                np.full(len(normal), np.nan) if residual is None else residual
            ),
            **columns,
        }
    )
    df.attrs["units"] = dict.fromkeys(STRESS_UNITS, unit)
    return df


def _fit(df, **kwargs):
    """Fit, failing on any warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return ht.analysis.shear_box_fit(df, **kwargs)


def _line(result, strength="peak", kind="free", group=0):
    record = result.groups[group]["strengths"][strength]
    return next(line for line in record["lines"] if line["line_kind"] == kind)


def _strength(result, strength="peak", group=0):
    return result.groups[group]["strengths"][strength]


def _project(name, system, tmp_path_factory):
    return ht.Project.from_ags(
        DATA / f"{name}.ags",
        db=tmp_path_factory.mktemp(name) / f"{name}.sqlite",
        overwrite=True,
        display_units=system,
    )


@pytest.fixture(scope="module")
def site_si(tmp_path_factory):
    return _project("site_si", "SI", tmp_path_factory).shear_box()


@pytest.fixture(scope="module")
def site_us(tmp_path_factory):
    return _project("site_us", "US", tmp_path_factory).shear_box()


@pytest.fixture(scope="module")
def joins(tmp_path_factory):
    return _project("joins", "SI", tmp_path_factory).shear_box()


def _counts_add_up(result):
    """AC 11: each strength's count plus its rows left out is the group's rows."""
    for group in result.groups:
        for strength, record in group["strengths"].items():
            left_out = (
                record[f"count_no_{strength}_shear_stress"]
                + record[f"count_no_{strength}_normal_stress"]
            )
            for line in record["lines"]:
                assert line["count"] + left_out == group["count_rows"]


# AC 1-2: BH2-D1, peak and residual, free and through the origin.


def test_bh2_d1_peak(site_si):
    result = _fit(site_si)
    assert result.unit == "kPa"
    free = _line(result)
    assert free["cohesion"] == pytest.approx(8, rel=REL)
    assert free["friction_angle"] == pytest.approx(30.963757, rel=REL)
    assert free["r_squared"] == pytest.approx(1, rel=REL)
    assert free["count"] == 3
    origin = _line(result, kind="through_origin")
    assert origin["cohesion"] == 0
    assert origin["line_slope"] == pytest.approx(49 / 75, rel=REL)
    assert origin["friction_angle"] == pytest.approx(33.157924, rel=REL)
    assert origin["r_squared"] == pytest.approx(0.98984127, rel=REL)
    for line in (free, origin):
        assert (line["lowest_normal_stress"], line["highest_normal_stress"]) == (
            50,
            200,
        )
    record = _strength(result)
    assert record["reported_pairs"] == [
        {"cohesion": 8.0, "friction_angle": 31.0, "count": 3}
    ]
    assert record["normal_stress_basis"] == "at_peak"
    points = record["points"]
    assert [point["normal_stress_basis"] for point in points] == ["at_peak"] * 3
    assert [point["secant_friction_angle"] for point in points] == pytest.approx(
        [37.234834, 34.215702, 32.619243], rel=REL
    )
    _counts_add_up(result)


def test_bh2_d1_residual(site_si):
    result = _fit(site_si)
    free = _line(result, "residual")
    assert free["line_slope"] == pytest.approx(191 / 350, rel=REL)
    assert free["cohesion"] == pytest.approx(3, rel=REL)
    assert free["friction_angle"] == pytest.approx(28.621928, rel=REL)
    assert free["r_squared"] == pytest.approx(0.999917772, rel=REL)
    origin = _line(result, "residual", "through_origin")
    assert origin["line_slope"] == pytest.approx(99 / 175, rel=REL)
    assert origin["friction_angle"] == pytest.approx(29.497461, rel=REL)
    assert origin["r_squared"] == pytest.approx(0.998190988, rel=REL)
    record = _strength(result, "residual")
    assert record["reported_pairs"] == [
        {"cohesion": 2.0, "friction_angle": 28.5, "count": 3}
    ]
    assert record["normal_stress_basis"] == "at_residual"


# AC 3: the US twin.


def test_us_twin(site_si, site_us):
    si, us = _fit(site_si), _fit(site_us)
    assert us.unit == "psf"
    for strength in ("peak", "residual"):
        for kind in ("free", "through_origin"):
            assert _line(us, strength, kind)["friction_angle"] == pytest.approx(
                _line(si, strength, kind)["friction_angle"], rel=1e-9
            )
    assert _line(us)["cohesion"] == pytest.approx(167.083474, rel=REL)
    assert _line(us, "residual")["cohesion"] == pytest.approx(62.6563027, rel=REL)
    shown = _fit(site_us, display_units="SI")
    assert shown.unit == "kPa"
    assert _line(shown)["cohesion"] == pytest.approx(8, rel=REL)
    assert _line(shown, "residual")["cohesion"] == pytest.approx(3, rel=REL)
    assert _strength(shown)["reported_pairs"][0]["cohesion"] == pytest.approx(
        8, rel=1e-3
    )


# AC 4: the normal stress of each point.


def test_applied_normal_stress(site_si):
    result = _fit(site_si, normal_stress="applied")
    assert result.normal_stress == "applied"
    assert _line(result)["friction_angle"] == pytest.approx(30.963757, rel=REL)
    assert _line(result, "residual")["cohesion"] == pytest.approx(3, rel=REL)
    for strength in ("peak", "residual"):
        assert _strength(result, strength)["normal_stress_basis"] == "applied"


def test_mixed_bases():
    df = _frame(
        [(50, 38), (100, 68), (200, 128)], normal_stress_at_peak=[52, np.nan, 205]
    )
    df.attrs["units"]["normal_stress_at_peak"] = "kPa"
    result = _fit(df)
    record = _strength(result)
    assert [point["normal_stress"] for point in record["points"]] == [52, 100, 205]
    assert [point["normal_stress_basis"] for point in record["points"]] == [
        "at_peak",
        "applied",
        "at_peak",
    ]
    assert record["normal_stress_basis"] == "mixed"
    assert record["notes"] == [
        "σn from more than one basis: applied (1 point), at_peak (2 points)."
    ]
    assert "σn from more than one basis" in str(result)
    assert "mixed" in result.to_frame()["peak_normal_stress_basis"].tolist()
    applied = _fit(df, normal_stress="applied")
    points = _strength(applied)["points"]
    assert [point["normal_stress"] for point in points] == [50, 100, 200]
    assert _strength(applied)["notes"] == []


# AC 8: validity.


def test_negative_slope_has_no_free_line():
    result = _fit(_frame([(100, 80), (200, 60)]))
    free = _line(result)
    assert free["no_fit_reason"] == "slope tan φ = -0.2 is below 0: no friction angle"
    assert math.isnan(free["friction_angle"])
    assert math.isnan(free["cohesion"])
    origin = _line(result, kind="through_origin")
    assert origin["line_slope"] == pytest.approx(0.4, rel=REL)
    assert origin["r_squared"] == pytest.approx(-9, rel=REL)


def test_negative_intercept_is_kept_with_a_warning():
    df = _frame([(100, 20), (200, 80), (300, 140)])
    with pytest.warns(UserWarning, match=r"negative in All \(peak\).*through_origin"):
        result = ht.analysis.shear_box_fit(df)
    free = _line(result)
    assert free["cohesion"] == pytest.approx(-40, rel=REL)
    assert free["line_slope"] == pytest.approx(0.6, rel=REL)
    origin = _line(result, kind="through_origin")
    assert origin["line_slope"] == pytest.approx(3 / 7, rel=REL)
    assert origin["friction_angle"] == pytest.approx(23.198591, rel=REL)
    assert origin["r_squared"] == pytest.approx(0.904761905, rel=REL)


def test_same_normal_stress_has_no_free_line():
    result = _fit(_frame([(100, 60), (100, 70)]))
    assert _line(result)["no_fit_reason"] == "all points at the same normal stress"
    assert _line(result, kind="through_origin")["line_slope"] == pytest.approx(0.65)


def test_zero_normal_stress_is_fitted_without_a_secant_angle():
    result = _fit(_frame([(0, 5), (100, 65), (200, 125)]))
    points = _strength(result)["points"]
    assert math.isnan(points[0]["secant_friction_angle"])
    assert _line(result)["count"] == 3
    assert _line(result)["cohesion"] == pytest.approx(5, rel=REL)


def test_all_at_zero_normal_stress_has_no_line_through_the_origin():
    result = _fit(_frame([(0, 5)]))
    assert (
        _line(result, kind="through_origin")["no_fit_reason"]
        == "all points at normal stress = 0"
    )
    assert _line(result)["no_fit_reason"] == "1 point: a line needs at least 2"


@pytest.mark.parametrize(
    "peak", [[(100, 60), (200, -5)], [(-100, 60), (200, 120)]], ids=["shear", "normal"]
)
def test_negative_stress_raises(peak):
    with pytest.raises(HangtuError, match=r"Rows [01] have a negative.*Check the sign"):
        ht.analysis.shear_box_fit(_frame(peak))


def test_negative_stress_on_a_row_left_out_is_not_checked():
    df = _frame([(100, 60), (200, 120)], residual=[np.nan, np.nan])
    df.loc[2] = [-50.0, np.nan, np.nan]
    result = _fit(df)
    assert _line(result)["count"] == 2


def test_two_points():
    result = _fit(_frame([(100, 60), (200, 120)]))
    free = _line(result)
    assert free["notes"] == ["2 points: the line passes through both, so R² = 1."]
    assert free["r_squared"] == pytest.approx(1)
    assert "passes through both" in str(result)
    assert _line(result, kind="through_origin")["notes"] == []


def test_one_point_through_the_origin_has_no_r_squared():
    result = _fit(_frame([(100, 60)]))
    origin = _line(result, kind="through_origin")
    assert origin["line_slope"] == pytest.approx(0.6)
    assert math.isnan(origin["r_squared"])


def test_rows_left_out_are_counted():
    df = _frame(
        [(100, 60), (200, 120), (300, np.nan), (np.nan, 50)],
        residual=[60, np.nan, 160, np.nan],
    )
    result = _fit(df)
    peak = _strength(result)
    assert (
        peak["count_no_peak_shear_stress"],
        peak["count_no_peak_normal_stress"],
    ) == (
        1,
        1,
    )
    assert _line(result)["count"] == 2
    residual = _strength(result, "residual")
    assert residual["count_no_residual_shear_stress"] == 2
    assert residual["count_no_residual_normal_stress"] == 0
    assert _line(result, "residual")["count"] == 2
    assert "left out: 1 no peak shear stress, 1 no peak normal stress" in str(result)
    _counts_add_up(result)


# AC 10: lines, order and views.


def test_cohesion_zero_puts_the_line_through_the_origin_first(site_si):
    result = _fit(site_si, cohesion=0)
    frame = result.to_frame()
    assert frame["line_kind"].tolist() == ["through_origin", "free"]
    assert frame["peak_friction_angle"].tolist() == pytest.approx(
        [33.157924, 30.963757], rel=REL
    )
    assert frame["residual_cohesion"].tolist() == pytest.approx([0, 3], rel=REL)
    text = str(result).splitlines()
    assert text[1].startswith("peak, through the origin: φ = 33.2°, R² = 0.990")
    assert text[2].startswith("  free: c = 8.00 kPa, φ = 31.0°")


def test_cohesion_other_than_none_or_zero_raises():
    with pytest.raises(HangtuError, match=r"cohesion must be None.*or 0"):
        ht.analysis.shear_box_fit(_frame([(100, 60), (200, 120)]), cohesion=5)


def test_to_frame(site_si):
    result = _fit(site_si)
    frame = result.to_frame()
    columns = ["line_kind"]
    for s in ("peak", "residual"):
        columns += [
            f"{s}_cohesion",
            f"{s}_friction_angle",
            f"{s}_r_squared",
            f"{s}_count",
            f"{s}_lowest_normal_stress",
            f"{s}_highest_normal_stress",
            f"{s}_normal_stress_basis",
            f"reported_{s}_cohesion",
            f"reported_{s}_friction_angle",
            f"count_reported_{s}_pairs",
            f"count_no_{s}_shear_stress",
            f"count_no_{s}_normal_stress",
            f"{s}_no_fit_reason",
        ]
    assert frame.columns.tolist() == columns
    assert frame["line_kind"].tolist() == ["free", "through_origin"]
    assert frame["peak_cohesion"].tolist() == pytest.approx([8, 0], rel=REL)
    assert frame["reported_peak_cohesion"].tolist() == [8, 8]
    assert frame["count_reported_peak_pairs"].tolist() == [1, 1]
    units = frame.attrs["units"]
    assert units["peak_cohesion"] == units["residual_highest_normal_stress"] == "kPa"
    assert units["reported_residual_cohesion"] == "kPa"
    assert (
        units["peak_friction_angle"] == units["reported_peak_friction_angle"] == "deg"
    )
    assert "peak_count" not in units


def test_to_dict_kind_and_summary(site_si):
    result = _fit(site_si)
    assert result.kind == "derived"
    assert result.function == "shear_box_fit"
    record = json.loads(json.dumps(result.to_dict()))
    assert record["groups"][0]["strengths"]["peak"]["lines"][0]["cohesion"] == 8
    assert str(result).splitlines()[:7] == [
        "Shear box fit",
        "peak, free: c = 8.00 kPa, φ = 31.0°, R² = 1.000, 3 points, σn 50.0 to 200 kPa",
        "  through the origin: φ = 33.2°, R² = 0.990",
        "  lab: c = 8 kPa, φ = 31° (3 stages)",
        "residual, free: c = 3.00 kPa, φ = 28.6°, R² = 1.000, 3 points, "
        "σn 50.0 to 200 kPa",
        "  through the origin: φ = 29.5°, R² = 0.998",
        "  lab: c = 2 kPa, φ = 28.5° (3 stages)",
    ]
    assert str(result).splitlines()[-1].startswith("c is an intercept at σn = 0")
    assert repr(result) == str(result)


def test_no_line_in_the_views():
    result = _fit(_frame([(100, 60)]))
    frame = result.to_frame()
    assert frame["peak_no_fit_reason"].tolist() == [
        "1 point: a line needs at least 2",
        None,
    ]
    assert math.isnan(frame["peak_cohesion"][0])
    assert frame["count_reported_peak_pairs"].tolist() == [0, 0]
    assert "peak, free: not fitted: 1 point: a line needs at least 2" in str(result)
    assert "residual, free: not fitted: 0 points" in str(result)


# AC 12: units and columns.


def test_without_units_raises():
    df = _frame([(100, 60), (200, 120)])
    df.attrs = {}
    with pytest.raises(UnitsError, match="peak_shear_stress"):
        ht.analysis.shear_box_fit(df)


def test_units_argument_overrides_attrs():
    df = _frame([(100, 60), (200, 120)], unit="psf")
    result = _fit(df, units=STRESS_UNITS)
    assert result.unit == "kPa"


def test_shear_stress_in_a_length_unit_raises():
    df = _frame([(100, 60), (200, 120)])
    df.attrs["units"]["peak_shear_stress"] = "mm"
    with pytest.raises(UnitsError, match="peak_shear_stress"):
        ht.analysis.shear_box_fit(df)


def test_template_with_blank_columns_fits_on_the_applied_stress():
    df = ht.template("shear_box").reindex(range(3))
    df["applied_normal_stress"] = [50.0, 100.0, 200.0]
    df["peak_shear_stress"] = [38.0, 68.0, 128.0]
    result = _fit(
        df, units={"applied_normal_stress": "kPa", "peak_shear_stress": "kPa"}
    )
    assert _line(result)["cohesion"] == pytest.approx(8, rel=REL)
    assert _strength(result)["normal_stress_basis"] == "applied"
    assert _strength(result, "residual")["count_no_residual_shear_stress"] == 3


def test_frame_without_a_shear_stress_raises():
    df = pd.DataFrame({"applied_normal_stress": [100.0]})
    with pytest.raises(HangtuError, match=r'neither.*ht\.template\("shear_box"\)'):
        ht.analysis.shear_box_fit(df)


def test_frame_without_a_normal_stress_raises():
    df = pd.DataFrame({"peak_shear_stress": [60.0], "normal_stress_at_peak": [100.0]})
    with pytest.raises(HangtuError, match=r"needs a normal stress.*applied_normal"):
        ht.analysis.shear_box_fit(df, normal_stress="applied")


@pytest.mark.parametrize(
    ("argument", "message"),
    [
        ({"normal_stress": "peak"}, "normal_stress must be 'at_peak_or_residual' or"),
        ({"display_units": "MPa"}, 'display_units must be "SI", "US" or None'),
    ],
)
def test_arguments_out_of_range_raise(argument, message):
    with pytest.raises(HangtuError, match=message):
        ht.analysis.shear_box_fit(_frame([(100, 60), (200, 120)]), **argument)


def test_not_a_frame_raises():
    with pytest.raises(HangtuError, match="must be a pandas DataFrame"):
        ht.analysis.shear_box_fit([1, 2])


def test_mpa_input():
    df = _frame(
        [(0.5, 0.52), (1, 0.86), (2, 1.71), (0.5, 0.45), (1, 0.93), (2, 1.62)],
        unit="MPa",
    )
    result = _fit(df)
    assert result.unit == "MPa"
    assert _line(result)["cohesion"] == pytest.approx(0.1, rel=REL)
    assert _line(result)["line_slope"] == pytest.approx(549 / 700, rel=REL)
    assert _line(result)["friction_angle"] == pytest.approx(38.106583, rel=REL)
    shown = _fit(df, display_units="SI")
    assert shown.unit == "kPa"
    assert _line(shown)["cohesion"] == pytest.approx(100, rel=REL)
    assert _line(shown)["friction_angle"] == pytest.approx(38.106583, rel=REL)


def test_joint_stored_in_mpa(joins):
    joint = joins[joins["sample_reference"] == "J1-U3"]
    result = _fit(joint)
    origin = _line(result, kind="through_origin")
    assert origin["line_slope"] == pytest.approx(0.84, rel=REL)
    assert origin["friction_angle"] == pytest.approx(40.030259, rel=REL)
    _counts_add_up(result)
