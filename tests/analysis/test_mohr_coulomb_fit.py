"""ht.analysis.mohr_coulomb_fit() (docs/work/m11b-envelope-fit.md, AC 1-12).

Golden values are the spec's, hand-calculated from its Derivations: s′ and t
from each point (σ′3, σ′1), the least-squares line t = a + s′ tan α, then
φ′ = arcsin(tan α) and c′ = a / cos φ′. Points are (σ′3, σ′1) in kPa.
"""

import json
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError, UnitsError

DATA = Path(__file__).parents[1] / "data" / "ags"
#: 1 psf in kPa: 0.45359237 kg × 9.80665 m/s² / 0.3048² m² (exact).
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000
STRESSES = [
    "minor_principal_stress_at_failure",
    "major_principal_stress_at_failure",
    "effective_minor_principal_stress_at_failure",
    "effective_major_principal_stress_at_failure",
]
BACK_PRESSURE = r"drained triaxial stage had TRET_PWPF blank"
REL = 1e-7


def _points(points, unit="kPa", **columns):
    """Stages with effective points ``(σ′3, σ′1)`` and totals 300 kPa above them."""
    minor, major = (
        np.array(values, dtype=float) for values in zip(*points, strict=True)
    )
    df = pd.DataFrame(
        {
            STRESSES[0]: minor + 300,
            STRESSES[1]: major + 300,
            STRESSES[2]: minor,
            STRESSES[3]: major,
            **columns,
        }
    )
    df.attrs["units"] = dict.fromkeys(STRESSES, unit)
    return df


def _fit(df, **kwargs):
    """Fit, failing on any warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return ht.analysis.mohr_coulomb_fit(df, **kwargs)


def _main(result, group=0):
    return result.groups[group]["fits"][0]


@pytest.fixture(scope="module")
def site_si(tmp_path_factory):
    return _triaxial("site_si", "SI", tmp_path_factory)


@pytest.fixture(scope="module")
def site_us(tmp_path_factory):
    return _triaxial("site_us", "US", tmp_path_factory)


def _triaxial(name, system, tmp_path_factory):
    project = ht.Project.from_ags(
        DATA / f"{name}.ags",
        db=tmp_path_factory.mktemp(name) / f"{name}.sqlite",
        overwrite=True,
        display_units=system,
    )
    with pytest.warns(UserWarning, match=BACK_PRESSURE):
        return project.triaxial()


# --- AC 1-3: golden values ----------------------------------------------------------


def test_golden_1_free():
    result = _fit(_points([(100, 300), (200, 500)]))
    fit = _main(result)
    assert fit["line_slope"] == pytest.approx(1 / 3, rel=REL)
    assert fit["line_intercept"] == pytest.approx(33.333333, rel=REL)
    assert fit["friction_angle"] == pytest.approx(19.471221, rel=REL)
    assert fit["cohesion"] == pytest.approx(25 * math.sqrt(2), rel=REL)
    assert fit["cohesion"] == pytest.approx(35.355339, rel=REL)
    assert fit["r_squared"] == pytest.approx(1.0, rel=REL)
    normal = [point["normal_stress"] for point in fit["points"]]
    assert normal == pytest.approx([166.66667, 300.0], rel=REL)
    assert fit["lowest_normal_stress"] == pytest.approx(166.66667, rel=REL)
    assert fit["highest_normal_stress"] == pytest.approx(300.0, rel=REL)
    assert any("passes through both" in note for note in fit["notes"])
    assert "passes through both" in str(result)


def test_golden_1_through_the_origin():
    result = _fit(_points([(100, 300), (200, 500)]), cohesion=0)
    fit = _main(result)
    assert fit["line_slope"] == pytest.approx(29 / 65, rel=REL)
    assert fit["friction_angle"] == pytest.approx(26.497185, rel=REL)
    assert fit["cohesion"] == 0
    assert fit["r_squared"] == pytest.approx(57 / 65, rel=REL)
    assert result.cohesion == 0
    assert "c′ = 0 fixed" in str(result)


@pytest.mark.parametrize("cohesion", [None, 0])
def test_golden_2(cohesion):
    fit = _main(_fit(_points([(100, 300), (200, 600)]), cohesion=cohesion))
    assert fit["line_slope"] == pytest.approx(0.5, rel=REL)
    assert fit["friction_angle"] == pytest.approx(30.0, rel=REL)
    assert fit["cohesion"] == pytest.approx(0.0, abs=1e-12)


def test_one_point():
    fixed = _main(_fit(_points([(100, 300)]), cohesion=0))
    assert fixed["friction_angle"] == pytest.approx(30.0, rel=REL)
    assert math.isnan(fixed["r_squared"])
    free = _main(_fit(_points([(100, 300)])))
    assert free["no_fit_reason"].startswith("1 point")
    assert math.isnan(free["cohesion"])
    assert math.isnan(free["friction_angle"])


# --- AC 4, 5, 9, 10: site_si.ags ----------------------------------------------------


def test_cu_set(site_si):
    cu = site_si[site_si["sample_reference"] == "BH1-U3"]
    result = _fit(cu)
    fit = _main(result)
    assert fit["line_slope"] == pytest.approx(0.454233427, rel=REL)
    assert fit["line_intercept"] == pytest.approx(30.9252437, rel=REL)
    assert fit["friction_angle"] == pytest.approx(27.015622, rel=REL)
    assert fit["cohesion"] == pytest.approx(34.713036, rel=REL)
    assert fit["r_squared"] == pytest.approx(0.999999682, rel=REL)
    assert fit["lowest_normal_stress"] == pytest.approx(89.1301, rel=1e-6)
    assert fit["highest_normal_stress"] == pytest.approx(292.7069, rel=1e-6)
    assert fit["reported_pairs"] == [
        {"cohesion": 5.0, "friction_angle": 27.0, "count": 3}
    ]
    assert [stage["stages"] for stage in result.groups[0]["fits"]] == ["all"]
    assert result.unit == "kPa"


def test_pooled_effective(site_si):
    result = _fit(site_si)
    fits = result.groups[0]["fits"]
    assert [fit["stages"] for fit in fits] == ["all", "single_stage"]
    pooled = fits[0]
    assert pooled["line_slope"] == pytest.approx(0.503104935, rel=REL)
    assert pooled["line_intercept"] == pytest.approx(21.9774766, rel=REL)
    assert pooled["friction_angle"] == pytest.approx(30.205634, rel=REL)
    assert pooled["cohesion"] == pytest.approx(25.430262, rel=REL)
    assert pooled["r_squared"] == pytest.approx(0.998125121, rel=REL)
    assert pooled["count"] == 6
    assert pooled["count_no_effective_stresses"] == 3
    assert pooled["reported_pairs"] == [
        {"cohesion": 5.0, "friction_angle": 27.0, "count": 3},
        {"cohesion": 29.0, "friction_angle": 30.0, "count": 3},
    ]
    single = fits[1]
    assert single["cohesion"] == pytest.approx(34.713036, rel=REL)
    assert single["count"] == 3
    frame = result.to_frame()
    assert frame.loc[0, "count_reported_pairs"] == 2
    assert math.isnan(frame.loc[0, "reported_effective_cohesion"])
    assert frame.loc[1, "reported_effective_cohesion"] == 5.0


def test_multistage_false(site_si):
    result = _fit(site_si, multistage=False)
    fits = result.groups[0]["fits"]
    assert [fit["stages"] for fit in fits] == ["single_stage", "all"]
    assert fits[0]["cohesion"] == pytest.approx(34.713036, rel=REL)
    assert fits[0]["count_multistage_left_out"] == 3
    assert fits[1]["cohesion"] == pytest.approx(25.430262, rel=REL)
    assert not result.multistage
    only = _fit(site_si[site_si["sample_reference"] == "BH2-U2"], multistage=False)
    main = _main(only)
    assert main["stages"] == "single_stage"
    assert main["no_fit_reason"] == "every stage is multistage"
    assert math.isnan(main["cohesion"])


def test_groups_and_counts(site_si):
    result = _fit(site_si, group_by="test_type")
    assert [group["key"] for group in result.groups] == [
        {"test_type": "CDM"},
        {"test_type": "CU"},
        {"test_type": "UU"},
    ]
    uu = _main(result, 2)
    assert uu["no_fit_reason"] is not None
    for group in result.groups:
        for fit in group["fits"]:
            left_out = sum(
                fit[name]
                for name in (
                    "count_no_principal_stresses",
                    "count_no_effective_stresses",
                    "count_multistage_left_out",
                )
            )
            assert fit["count"] + left_out == group["count_rows"]
    frame = result.to_frame()
    assert list(frame.columns) == [
        "test_type",
        "stages",
        "effective_cohesion",
        "effective_friction_angle",
        "line_intercept",
        "line_slope",
        "r_squared",
        "count",
        "lowest_normal_stress",
        "highest_normal_stress",
        "reported_effective_cohesion",
        "reported_effective_friction_angle",
        "count_reported_pairs",
        "count_no_principal_stresses",
        "count_no_effective_stresses",
        "count_multistage_left_out",
        "no_fit_reason",
    ]
    assert list(frame["stages"]) == ["all", "single_stage", "all", "all"]
    assert frame.attrs["units"]["effective_cohesion"] == "kPa"
    assert frame.attrs["units"]["effective_friction_angle"] == "deg"
    record = result.to_dict()
    assert record["kind"] == "derived"
    json.dumps(record)
    assert "UU: 3 rows" in str(result)


def test_groups_in_sorted_order_with_blank_last():
    df = _points(
        [(100, 300), (200, 600), (100, 300), (200, 600), (100, 300), (200, 600)],
        geology_unit=["TRC", "TRC", None, None, "ALV", "ALV"],
    )
    result = _fit(df, group_by="geology_unit")
    keys = [group["key"]["geology_unit"] for group in result.groups]
    assert keys == ["ALV", "TRC", "(blank)"]


# --- AC 6: total stress -------------------------------------------------------------


def test_total_stress(site_si):
    cu = site_si[site_si["sample_reference"] == "BH1-U3"]
    with pytest.warns(UserWarning, match=r"negative in BH1-U3.*cohesion=0") as caught:
        result = ht.analysis.mohr_coulomb_fit(
            cu, stress="total", group_by="sample_reference"
        )
    assert len(caught) == 1
    fit = _main(result)
    assert fit["line_slope"] == pytest.approx(0.278759064, rel=REL)
    assert fit["line_intercept"] == pytest.approx(-45.7744608, rel=REL)
    assert fit["friction_angle"] == pytest.approx(16.186156, rel=REL)
    assert fit["cohesion"] == pytest.approx(-47.663803, rel=REL)
    assert fit["reported_pairs"] is None
    frame = result.to_frame()
    assert "total_stress_cohesion" in frame.columns
    assert "reported_effective_cohesion" not in frame.columns
    assert "count_no_effective_stresses" not in frame.columns


def test_total_stress_refuses_mixed_sources(site_si):
    with pytest.raises(HangtuError) as error:
        _fit(site_si, stress="total")
    message = str(error.value)
    for text in (
        "test_type: 'CU' (3 rows)",
        "'CDM' (3 rows)",
        "'UU' (3 rows)",
        "failure_criterion: 'Maximum deviator stress' (6 rows)",
        "'(blank)' (3 rows)",
        "pool=",
    ):
        assert text in message
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = ht.analysis.mohr_coulomb_fit(
            site_si, stress="total", pool=["test_type", "failure_criterion"]
        )
    assert result.pooled == ("test_type", "failure_criterion")
    assert _main(result)["count"] == 9


def test_uu_alone_has_no_fit(site_si):
    uu = site_si[site_si["test_type"] == "UU"]
    fit = _main(_fit(uu, stress="total"))
    assert fit["line_slope"] == pytest.approx(-0.00481368, rel=1e-6)
    assert fit["no_fit_reason"].startswith("slope tan α = -0.004814 is outside")
    assert math.isnan(fit["cohesion"])


# --- AC 7: validity -----------------------------------------------------------------


def test_slope_of_one_or_more_has_no_fit():
    fit = _main(_fit(_points([(300, 500), (100, 900)])))
    assert fit["no_fit_reason"] == (
        "slope tan α = 3.0 is outside 0 ≤ tan α < 1: no friction angle fits"
    )


def test_negative_intercept_is_kept_with_a_warning():
    with pytest.warns(UserWarning, match=r"negative in All") as caught:
        result = ht.analysis.mohr_coulomb_fit(_points([(100, 250), (300, 1000)]))
    assert len(caught) == 1
    fit = _main(result)
    assert fit["line_slope"] == pytest.approx(0.578947368, rel=REL)
    assert fit["line_intercept"] == pytest.approx(-26.3157895, rel=REL)
    assert fit["friction_angle"] == pytest.approx(35.376540, rel=REL)
    assert fit["cohesion"] == pytest.approx(-32.274861, rel=REL)


def test_same_mean_stress_has_no_fit():
    fit = _main(_fit(_points([(100, 300), (150, 250)])))
    assert fit["no_fit_reason"] == "all points at the same mean stress"


def test_reversed_principal_stresses_raise():
    with pytest.raises(HangtuError, match=r"^Rows 1 have σ′1 < σ′3"):
        _fit(_points([(100, 300), (300, 200)]))


def test_tension_is_fitted_with_a_warning():
    with pytest.warns(UserWarning, match=r"rows 0 have σ′3 < 0 \(tension\)") as caught:
        result = ht.analysis.mohr_coulomb_fit(
            _points([(-10, 200), (100, 400), (200, 600)])
        )
    assert len(caught) == 1
    assert _main(result)["count"] == 3


def test_one_warning_per_kind_naming_every_group():
    df = _points(
        [(100, 250), (300, 1000), (100, 250), (300, 1000)],
        geology_unit=["ALV", "ALV", "TRC", "TRC"],
    )
    with pytest.warns(UserWarning, match=r"negative in ALV, TRC") as caught:
        ht.analysis.mohr_coulomb_fit(df, group_by="geology_unit")
    assert len(caught) == 1


# --- AC 8: pooling ------------------------------------------------------------------


def test_two_failure_criteria_raise():
    df = _points(
        [(100, 300), (200, 600), (300, 900)],
        failure_criterion=["Maximum deviator stress"] * 2 + ["Maximum stress ratio"],
    )
    with pytest.raises(HangtuError) as error:
        _fit(df)
    message = str(error.value)
    assert "'Maximum deviator stress' (2 rows)" in message
    assert "'Maximum stress ratio' (1 rows)" in message
    result = _fit(df, pool="failure_criterion")
    assert result.pooled == ("failure_criterion",)
    assert "Pooled on purpose: failure_criterion." in str(result)


def test_a_blank_beside_a_criterion_is_mixed():
    df = _points(
        [(100, 300), (200, 600)], failure_criterion=["Maximum deviator stress", None]
    )
    with pytest.raises(HangtuError, match=r"'\(blank\)' \(1 rows\)"):
        _fit(df)


def test_without_the_column_it_fits_with_a_note():
    result = _fit(_points([(100, 300), (200, 600)]))
    assert "failure_criterion not given" in str(result)
    assert any("multistage_test not given" in note for note in result.notes)


def test_cu_and_cd_pool_in_effective_stress():
    df = _points([(100, 300), (200, 600)], test_type=["CU", "CD"])
    assert _main(_fit(df))["count"] == 2


# --- AC 11: units -------------------------------------------------------------------


def test_twin_files_agree(site_si, site_us):
    si = _main(_fit(site_si))
    us = _main(_fit(site_us, display_units="US"))
    assert us["friction_angle"] == pytest.approx(si["friction_angle"], rel=1e-9)
    # The file's stresses are to 6 decimals, which the intercept magnifies to
    # about 2e-9: c′ takes the spec's default tolerance.
    assert us["cohesion"] == pytest.approx(si["cohesion"] / PSF, rel=REL)
    assert us["reported_pairs"][0]["cohesion"] == pytest.approx(5 / PSF, rel=1e-9)


def test_psf_frame_fitted_in_si():
    df = _points([(100 / PSF, 300 / PSF), (200 / PSF, 500 / PSF)], unit="psf")
    result = _fit(df, display_units="SI")
    assert result.unit == "kPa"
    assert _main(result)["cohesion"] == pytest.approx(35.355339, rel=REL)
    plain = _fit(df)
    assert plain.unit == "psf"
    assert _main(plain)["cohesion"] == pytest.approx(35.355339 / PSF, rel=REL)


def test_frame_without_units_raises():
    df = _points([(100, 300), (200, 600)])
    df.attrs = {}
    with pytest.raises(UnitsError, match="minor_principal_stress_at_failure"):
        _fit(df)


def test_stresses_in_a_length_unit_raise():
    with pytest.raises(UnitsError):
        _fit(_points([(100, 300), (200, 600)], unit="ft"))


# --- AC 12: errors ------------------------------------------------------------------


def test_template_without_principal_stresses_raises():
    with pytest.raises(ColumnError, match=r"triaxial_failure_stresses\(\)"):
        _fit(ht.template("triaxial"))


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"cohesion": 5}, r"cohesion must be None \(fitted\) or 0"),
        ({"stress": "drained"}, r'stress must be "effective" or "total"'),
        ({"group_by": "geology_unit"}, r"can't group by 'geology_unit'"),
        ({"pool": "test_type"}, r"can't pool 'test_type'"),
        ({"display_units": "metric"}, r"display_units must be"),
    ],
)
def test_argument_errors(kwargs, match):
    with pytest.raises(HangtuError, match=match):
        _fit(_points([(100, 300), (200, 600)]), **kwargs)


def test_input_is_unchanged():
    df = _points([(100, 300), (200, 600)])
    before = df.copy()
    _fit(df)
    pd.testing.assert_frame_equal(df, before)
