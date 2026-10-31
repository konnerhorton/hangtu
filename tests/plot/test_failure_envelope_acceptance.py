"""P11 against the acceptance criteria of docs/plots/P11-failure-envelope.md §12.

AC 6 and 8 on the test files; the other criteria are in
test_failure_envelope.py. The fit's own values are the M11 (b) spec's
AC 4 and 5, hand-calculated there.
"""

import math
from pathlib import Path

import pytest

import hangtu as ht

AGS = Path(__file__).parents[1] / "data" / "ags"
#: 1 psf in kPa: 0.45359237 kg × 9.80665 m/s² / 0.3048² m² (exact).
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000
BACK_PRESSURE = r"drained triaxial stage had TRET_PWPF blank"


@pytest.fixture(autouse=True)
def _no_hints():
    ht.settings.hints = False


def _triaxial(name, system, tmp_path_factory):
    project = ht.Project.from_ags(
        AGS / f"{name}.ags",
        db=tmp_path_factory.mktemp(name) / f"{name}.sqlite",
        overwrite=True,
        display_units=system,
    )
    with pytest.warns(UserWarning, match=BACK_PRESSURE):
        return project.triaxial()


@pytest.fixture(scope="module")
def site_si(tmp_path_factory):
    return _triaxial("site_si", "SI", tmp_path_factory)


@pytest.fixture(scope="module")
def site_us(tmp_path_factory):
    return _triaxial("site_us", "US", tmp_path_factory)


def _lines(ax, gid):
    return [line for line in ax.lines if line.get_gid() == gid]


def _intercept_and_slope(line):
    (x0, x1), (y0, y1) = line.get_xdata(), line.get_ydata()
    slope = (y1 - y0) / (x1 - x0)
    return y0 - slope * x0, slope


def _box(ax):
    return next(text for text in ax.texts if text.get_gid() == "result_box")


def test_ac6_one_fit_and_the_fit_without_multistage(site_si):
    _, ax, fit = ht.plot.failure_envelope(site_si, display_units="SI")
    (solid,) = _lines(ax, "envelope")
    intercept, slope = _intercept_and_slope(solid)
    assert intercept == pytest.approx(25.430262, rel=1e-7)
    assert slope == pytest.approx(math.tan(math.radians(30.205634)), rel=1e-7)
    (dotted,) = _lines(ax, "envelope_other")
    assert dotted.get_linestyle() == ":"
    intercept, _ = _intercept_and_slope(dotted)
    assert intercept == pytest.approx(34.713036, rel=1e-7)
    assert dotted.get_label() == "Fit without multistage stages"
    text = _box(ax).get_text()
    assert "c′ = 25.4 kPa, φ′ = 30.2°, n = 6" in text
    assert "without multistage: c′ = 34.7 kPa, φ′ = 27.0°" in text
    assert "Lab: c′ = 5 kPa, φ′ = 27.0° (3 stages)" in text
    assert "Lab: c′ = 29 kPa, φ′ = 30.0° (3 stages)" in text
    footnote = [t.get_text() for t in ax.texts if "Left out" in t.get_text()]
    assert footnote == ["Left out: 3 without effective stresses"]
    assert fit.groups[0]["fits"][0]["count"] == 6


def test_ac6_two_groups_in_two_colors(site_si):
    _, ax, _ = ht.plot.failure_envelope(
        site_si, group_by="test_type", display_units="SI"
    )
    solid = _lines(ax, "envelope")
    assert len(solid) == 2
    assert solid[0].get_color() != solid[1].get_color()
    assert "UU: no fit: 0 points" in _box(ax).get_text()


def test_ac8_us_and_si_agree(site_si, site_us):
    _, si_ax, si = ht.plot.failure_envelope(site_si, display_units="SI")
    _, us_ax, us = ht.plot.failure_envelope(site_us, display_units="US")
    si_fit, us_fit = si.groups[0]["fits"][0], us.groups[0]["fits"][0]
    assert us_fit["friction_angle"] == pytest.approx(si_fit["friction_angle"], rel=1e-9)
    # The US file's stresses are to 6 decimals, which the intercept magnifies
    # to about 2e-9 (as in the fit's own twin test).
    assert us_fit["cohesion"] == pytest.approx(si_fit["cohesion"] / PSF, rel=1e-7)
    assert si_ax.get_xlabel().endswith("(kPa)")
    assert us_ax.get_xlabel().endswith("(psf)")
    assert "psf" in _box(us_ax).get_text()


def test_example_project_fits_each_geology_unit(tmp_path):
    p = ht.Project.from_ags(ht.examples.path("site.ags"), db=tmp_path / "site.sqlite")
    p.set_geology_map(ht.examples.path("strata.csv"))
    # The clay and the sand pooled give a negative intercept: fit each unit.
    with pytest.warns(UserWarning, match="negative"):
        _, ax, fit = ht.plot.failure_envelope(p.triaxial(), display_units="US")
    assert fit.by == ()
    _, ax, fit = ht.plot.failure_envelope(
        p.triaxial(), group_by="geology_unit", display_units="US"
    )
    assert [group["key"]["geology_unit"] for group in fit.groups] == [
        "Alluvium",
        "Terrace",
    ]
    assert len(_lines(ax, "envelope")) == 2
