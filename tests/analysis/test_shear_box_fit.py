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


# group_by=.


def test_group_by_gives_one_set_of_lines_per_group():
    df = _frame(
        [(100, 60), (200, 120), (100, 50), (200, 90), (100, 70)],
        group=["B", "B", "A", "A", None],
    )
    result = _fit(df, group_by="group")
    keys = [group["key"]["group"] for group in result.groups]
    assert keys[:2] == ["A", "B"]
    assert len(keys) == 3
    assert result.by == ("group",)
    assert _line(result, group=0)["line_slope"] == pytest.approx(0.4, rel=REL)
    assert _line(result, group=1)["line_slope"] == pytest.approx(0.6, rel=REL)
    assert _line(result, group=2)["count"] == 1
    frame = result.to_frame()
    assert frame.columns[:2].tolist() == ["group", "line_kind"]
    assert len(frame) == 6
    assert "A: 2 rows" in str(result)
    _counts_add_up(result)


def test_group_by_a_missing_column_raises():
    with pytest.raises(HangtuError, match=r"can't group by 'geology_unit'.*Available"):
        ht.analysis.shear_box_fit(
            _frame([(100, 60), (200, 120)]), group_by="geology_unit"
        )


# AC 7: ring shear and a rock joint, joins.ags.


def test_ring_shear_residual_only(joins):
    ring = joins[joins["sample_reference"] == "J1-D2"]
    result = _fit(ring)
    assert _line(result, "residual")["no_fit_reason"] == (
        "1 point: a line needs at least 2"
    )
    origin = _line(result, "residual", "through_origin")
    assert origin["line_slope"] == pytest.approx(0.21, rel=REL)
    assert origin["friction_angle"] == pytest.approx(11.859779, rel=REL)
    assert math.isnan(origin["r_squared"])
    assert _line(result)["no_fit_reason"] == "0 points: a line needs at least 2"
    assert _line(result, kind="through_origin")["no_fit_reason"] == "no points"
    assert _strength(result)["count_no_peak_shear_stress"] == 1


def test_joins_in_one_group_pool_nothing(joins):
    result = _fit(joins)
    assert _line(result, kind="through_origin")["friction_angle"] == pytest.approx(
        40.030259, rel=REL
    )
    assert _line(result, "residual", "through_origin")["friction_angle"] == (
        pytest.approx(11.859779, rel=REL)
    )
    assert result.groups[0]["count_rows"] == 2
    _counts_add_up(result)


# AC 9: pooling.


@pytest.fixture
def with_ring_shear(site_si):
    ring = pd.DataFrame(
        {
            "test_type": ["SMALL RSHEAR"],
            "failure_criterion": ["Maximum shear stress"],
            "applied_normal_stress": [150.0],
            "residual_shear_stress": [80.0],
        },
        index=[3],
    )
    df = pd.concat([site_si, ring])
    df.attrs = site_si.attrs
    return df


def test_mixed_test_types_raise(with_ring_shear):
    with pytest.raises(HangtuError) as error:
        ht.analysis.shear_box_fit(with_ring_shear)
    message = str(error.value)
    assert "can't fit residual rows from different sources" in message
    assert "test_type: 'SMALL SBOX' (3 rows)," in message
    assert "'SMALL RSHEAR' (1 rows)" in message
    assert "pool=['test_type']" in message


def test_mixed_failure_criteria_raise(site_si):
    df = site_si.copy()
    df.loc[2, "failure_criterion"] = None
    with pytest.raises(HangtuError, match=r"(?s)peak rows.*'\(blank\)' \(1 rows\)"):
        ht.analysis.shear_box_fit(df)


def test_pool_fits_them_on_purpose(with_ring_shear):
    df = with_ring_shear.copy()
    df.loc[2, "failure_criterion"] = None
    result = _fit(df, pool=["test_type", "failure_criterion"])
    assert result.pooled == ("test_type", "failure_criterion")
    assert _line(result, "residual")["count"] == 4
    assert _line(result)["count"] == 3
    assert "Pooled on purpose: test_type, failure_criterion." in str(result)
    _counts_add_up(result)


def test_pool_takes_only_the_checked_columns():
    with pytest.raises(HangtuError, match="pool= takes 'test_type' and 'failure_"):
        ht.analysis.shear_box_fit(_frame([(100, 60), (200, 120)]), pool="geology_unit")


def test_without_the_checked_columns_notes_say_so():
    result = _fit(_frame([(100, 60), (200, 120)]))
    assert result.notes[:2] == (
        "test_type not given: the fit couldn't check that a line's rows share one.",
        "failure_criterion not given: the fit couldn't check that a line's rows "
        "share one.",
    )


def test_site_si_has_no_pooling_notes(site_si):
    assert not any("not given" in note for note in _fit(site_si).notes)


# AC 13: multistage_test isn't read.


def test_multistage_test_changes_nothing(site_si):
    df = site_si.copy()
    df["multistage_test"] = [True, True, False]
    assert _fit(df).to_frame().equals(_fit(site_si).to_frame())


# AC 5-6: the example project's shear box tests (site.ags, stored in psf).
#: Terrace samples added for M18 (d) (docs/work/m18d-sources-compared.md,
#: decision 20), left out so the hand fits below stay this unit's.
SOURCES_COMPARED = ["B-2-D5", "B-5-D5", "B-6-D5"]


@pytest.fixture(scope="module")
def example(tmp_path_factory):
    p = ht.Project.from_ags(
        ht.examples.path("site.ags"),
        db=tmp_path_factory.mktemp("example") / "site.sqlite",
        display_units="US",
    )
    p.set_geology_map(ht.examples.path("strata.csv"))
    df = p.shear_box()
    return df[~df["sample_reference"].isin(SOURCES_COMPARED)]


def _unit(result, name):
    return next(g for g in result.groups if g["key"] == {"geology_unit": name})


def _unit_line(result, name, strength="peak", kind="free"):
    record = _unit(result, name)["strengths"][strength]
    return next(line for line in record["lines"] if line["line_kind"] == kind)


def _sandstone(example):
    return example[example["geology_unit"] == "Sandstone"]


def _check_sandstone(result, scale):
    """AC 5's lines, with c in MPa × ``scale``; φ to 1e-9 in every unit."""
    expected = {
        ("peak", "free"): (0.1, 549 / 700, 38.106583, 0.993557064),
        ("peak", "through_origin"): (0, 1787 / 2100, 40.396201, 0.98432697),
        ("residual", "free"): (0.025, 0.57, 29.683140, 0.994099135),
        ("residual", "through_origin"): (0, 44 / 75, 30.398728, 0.993006382),
    }
    for (strength, kind), (c, b, phi, r2) in expected.items():
        line = _line(result, strength, kind)
        assert line["cohesion"] == pytest.approx(c * scale, rel=REL, abs=1e-12)
        assert line["line_slope"] == pytest.approx(b, rel=1e-9)
        assert line["friction_angle"] == pytest.approx(phi, rel=REL)
        assert math.tan(math.radians(line["friction_angle"])) == pytest.approx(
            b, rel=1e-9
        )
        assert line["r_squared"] == pytest.approx(r2, rel=REL)
        assert line["count"] == 6
    _counts_add_up(result)


def test_sandstone_joints_in_mpa(example):
    with ht.settings.override(display_overrides={"stress": "MPa"}):
        result = _fit(_sandstone(example), display_units="SI")
    assert result.unit == "MPa"
    _check_sandstone(result, 1)
    free = _line(result)
    assert free["lowest_normal_stress"] == pytest.approx(0.5, rel=1e-9)
    assert free["highest_normal_stress"] == pytest.approx(2, rel=1e-9)
    pairs = _strength(result)["reported_pairs"]
    assert [pair["cohesion"] for pair in pairs] == pytest.approx(
        [0.095, 0.105], rel=1e-9
    )
    assert [pair["friction_angle"] for pair in pairs] == [38.7, 37.5]


@pytest.mark.parametrize(("system", "scale"), [("SI", 1000), ("US", 1e6 / PSF / 1e3)])
def test_sandstone_joints_in_kpa_and_psf(example, system, scale):
    result = _fit(_sandstone(example), display_units=system)
    _check_sandstone(result, scale)


def test_sandstone_joints_in_psf_values(example):
    result = _fit(_sandstone(example))
    assert result.unit == "psf"
    assert _line(result)["cohesion"] == pytest.approx(2088.54342, rel=REL)
    assert _line(result, "residual")["cohesion"] == pytest.approx(522.135856, rel=REL)


def test_sandstone_per_specimen(example):
    with ht.settings.override(display_overrides={"stress": "MPa"}):
        result = _fit(
            _sandstone(example), group_by="specimen_reference", display_units="SI"
        )
    assert [group["key"] for group in result.groups] == [
        {"specimen_reference": "1"},
        {"specimen_reference": "2"},
    ]
    first = _line(result)
    assert first["line_slope"] == pytest.approx(561 / 700, rel=1e-9)
    assert first["cohesion"] == pytest.approx(0.095, rel=REL)
    assert first["friction_angle"] == pytest.approx(38.709683, rel=REL)
    assert first["count"] == 3
    _counts_add_up(result)


def test_example_by_geology_unit(example):
    result = _fit(example, group_by="geology_unit")
    assert result.unit == "psf"
    assert [group["key"] for group in result.groups] == [
        {"geology_unit": "Alluvium"},
        {"geology_unit": "Terrace"},
        {"geology_unit": "Sandstone"},
    ]
    expected = {
        "Alluvium": {
            ("peak", "free"): (170, 699 / 1400, 26.532301, 0.989167965),
            ("peak", "through_origin"): (0, 467 / 840, 29.071975, 0.97278579),
            ("residual", "free"): (27.5, 0.3825, 20.931853, 0.992243133),
            ("residual", "through_origin"): (0, 47 / 120, 21.388623, 0.991510439),
        },
        "Terrace": {
            ("peak", "free"): (71.0169492, 3933 / 5900, 33.687826, 0.998350334),
            ("peak", "through_origin"): (0, 973 / 1425, 34.325536, 0.997555186),
            ("residual", "free"): (3.05084746, 3539 / 5900, 30.956615, 0.999722222),
            ("residual", "through_origin"): (
                0,
                1141 / 1900,
                30.985925,
                0.999720407,
            ),
        },
    }
    for name, lines in expected.items():
        for (strength, kind), (c, b, phi, r2) in lines.items():
            line = _unit_line(result, name, strength, kind)
            assert line["cohesion"] == pytest.approx(c, rel=REL)
            assert line["line_slope"] == pytest.approx(b, rel=REL)
            assert line["friction_angle"] == pytest.approx(phi, rel=REL)
            assert line["r_squared"] == pytest.approx(r2, rel=REL)
    assert _unit_line(result, "Alluvium")["count"] == 6
    assert _unit_line(result, "Terrace")["count"] == 4
    assert _unit_line(result, "Sandstone")["count"] == 6
    _counts_add_up(result)


def test_example_alluvium_has_two_lab_pairs(example):
    result = _fit(example, group_by="geology_unit")
    for strength, pairs in {
        "peak": [(145, 27.4), (195, 25.6)],
        "residual": [(5, 21.7), (50, 20.2)],
    }.items():
        record = _unit(result, "Alluvium")["strengths"][strength]
        reported = record["reported_pairs"]
        assert [pair["cohesion"] for pair in reported] == pytest.approx(
            [c for c, _ in pairs], rel=1e-9
        )
        assert [pair["friction_angle"] for pair in reported] == [
            phi for _, phi in pairs
        ]
        assert [pair["count"] for pair in reported] == [3, 3]
    row = result.to_frame().iloc[0]
    assert row["geology_unit"] == "Alluvium"
    assert row["count_reported_peak_pairs"] == 2
    assert math.isnan(row["reported_peak_cohesion"])
    assert math.isnan(row["reported_peak_friction_angle"])


def test_example_alluvium_in_si(example):
    result = _fit(example, group_by="geology_unit", display_units="SI")
    assert result.unit == "kPa"
    assert _unit_line(result, "Alluvium")["cohesion"] == pytest.approx(
        8.13964403, rel=REL
    )
    assert _unit_line(result, "Alluvium", "residual")["cohesion"] == pytest.approx(
        1.31670712, rel=REL
    )


# --- M18 (d), AC 12: depths and the judgments file kept on the fit -------------------


def test_points_keep_their_depth_elevation_and_ground_level():
    df = _frame(
        [(50, 30), (100, 58), (200, 115)],
        depth=[4.0, 4.0, 4.0],
        elevation=[96.0, 96.0, 96.0],
        ground_level=[100.0, 100.0, 100.0],
    )
    df.attrs["units"] |= {"depth": "ft", "elevation": "ft", "ground_level": "ft"}
    result = _fit(df)
    points = _strength(result)["points"]
    assert [p["depth"] for p in points] == [4.0] * 3
    assert [p["elevation"] for p in points] == [96.0] * 3
    assert [p["ground_level"] for p in points] == [100.0] * 3
    assert result.depth_units == {
        "depth": "ft",
        "elevation": "ft",
        "ground_level": "ft",
    }
    assert result.judgments_file is None
    record = json.loads(json.dumps(result.to_dict()))
    assert record["groups"][0]["strengths"]["peak"]["points"][0]["depth"] == 4.0
    plain = _fit(_frame([(50, 30), (100, 58), (200, 115)]))
    assert _line(result)["friction_angle"] == _line(plain)["friction_angle"]
    assert "depth" not in _strength(plain)["points"][0]
    assert plain.depth_units == {}


def test_judgments_file_from_a_projects_frame(tmp_path):
    project = ht.Project.from_ags(
        DATA / "site_si.ags",
        db=tmp_path / "site.sqlite",
        overwrite=True,
        display_units="SI",
    )
    path = ht.examples.path("judgments.yaml")
    project.set_judgments(path)
    result = ht.analysis.shear_box_fit(project.shear_box())
    assert result.judgments_file == str(path)
    points = _strength(result)["points"]
    assert all(p["depth"] is not None for p in points)
    assert result.depth_units["depth"] == "m"
    json.dumps(result.to_dict())
