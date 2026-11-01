"""P12 on the example readings (docs/plots/P12-triaxial-shearing.md, AC 10).

The readings are ``ht.examples``' ``triaxial_readings.csv``, in psf, made to end
at the example project's triaxial stages (M11 (c) spec decision 10).
"""

import warnings

import numpy as np
import pytest

import hangtu as ht

#: 1 psf in kPa: 0.45359237 kg × 9.80665 m/s² / 0.3048² m² (exact).
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000
STRESSES = [
    "effective_consolidation_stress",
    "back_pressure",
    "cell_pressure",
    "deviator_stress",
    "excess_pore_pressure",
]


@pytest.fixture(autouse=True)
def _no_hints():
    ht.settings.hints = False


def example_readings(unit="psf"):
    df = ht.read_csv(
        ht.examples.path("triaxial_readings.csv"),
        units=dict.fromkeys(STRESSES, "psf"),
        dtype={"specimen_id": str, "test_stage": str, "specimen_reference": str},
    )
    if unit == "kPa":
        for column in STRESSES:
            df[column] = df[column] * PSF
        df.attrs["units"] = dict.fromkeys(STRESSES, "kPa")
    return df


def fit_in(df, system):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _, ax, fit = ht.plot.triaxial_shearing(
            df, space="s_t", group_by="geology_unit", display_units=system
        )
    return ax, fit.to_frame()


def test_ac10_us_and_si_agree():
    us_ax, us = fit_in(example_readings("psf"), "US")
    si_ax, si = fit_in(example_readings("kPa"), "SI")
    np.testing.assert_allclose(
        us["effective_friction_angle"], si["effective_friction_angle"], rtol=1e-9
    )
    np.testing.assert_allclose(
        us["effective_cohesion"] * PSF, si["effective_cohesion"], rtol=1e-9
    )
    assert "(psf)" in us_ax.get_xlabel() and "(kPa)" in si_ax.get_xlabel()


def test_example_fits_match_the_lab_marks_and_p11(tmp_path):
    readings = example_readings()
    _, _, from_readings = ht.plot.triaxial_shearing(
        readings, space="s_t", group_by="geology_unit", display_units="US"
    )
    p = ht.Project.from_ags(
        ht.examples.path("site.ags"), db=tmp_path / "site.sqlite", display_units="US"
    )
    p.set_geology_map(ht.examples.path("strata.csv"))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        _, _, from_ags = ht.plot.failure_envelope(
            p.triaxial(), space="s_t", group_by="geology_unit", display_units="US"
        )
    columns = ["effective_cohesion", "effective_friction_angle"]
    np.testing.assert_allclose(
        from_readings.to_frame()[columns].to_numpy(dtype=float),
        from_ags.to_frame()[columns].to_numpy(dtype=float),
        rtol=1e-9,
    )
