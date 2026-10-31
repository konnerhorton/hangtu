"""ht.analysis.mohr_coulomb_fit() (docs/work/m11b-envelope-fit.md, AC 1-12).

Golden values are the spec's, hand-calculated from its Derivations: s′ and t
from each point (σ′3, σ′1), the least-squares line t = a + s′ tan α, then
φ′ = arcsin(tan α) and c′ = a / cos φ′. Points are (σ′3, σ′1) in kPa.
"""

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


# --- AC 4: site_si.ags ------------------------------------------------------------


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
    assert [stage["stages"] for stage in result.groups[0]["fits"]] == ["all"]
    assert result.unit == "kPa"


# --- AC 6: total stress -------------------------------------------------------------


def test_total_stress(site_si):
    cu = site_si[site_si["sample_reference"] == "BH1-U3"]
    with pytest.warns(UserWarning, match=r"negative.*cohesion=0") as caught:
        result = ht.analysis.mohr_coulomb_fit(cu, stress="total")
    assert len(caught) == 1
    fit = _main(result)
    assert fit["line_slope"] == pytest.approx(0.278759064, rel=REL)
    assert fit["line_intercept"] == pytest.approx(-45.7744608, rel=REL)
    assert fit["friction_angle"] == pytest.approx(16.186156, rel=REL)
    assert fit["cohesion"] == pytest.approx(-47.663803, rel=REL)
    assert "no effective stresses" not in str(result)


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
    with pytest.warns(UserWarning, match=r"intercept is negative") as caught:
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


# --- AC 11: units -------------------------------------------------------------------


def test_twin_files_agree(site_si, site_us):
    si = _main(_fit(site_si[site_si["sample_reference"] == "BH1-U3"]))
    us = _main(
        _fit(site_us[site_us["sample_reference"] == "BH1-U3"], display_units="US")
    )
    assert us["friction_angle"] == pytest.approx(si["friction_angle"], rel=1e-9)
    # The file's stresses are to 6 decimals, which the intercept magnifies to
    # about 2e-9: c′ takes the spec's default tolerance.
    assert us["cohesion"] == pytest.approx(si["cohesion"] / PSF, rel=REL)


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
