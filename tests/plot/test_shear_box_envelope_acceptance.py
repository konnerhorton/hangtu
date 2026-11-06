"""P31 against the acceptance criteria of docs/plots/P31-shear-box-envelope.md §12.

AC 5 on the example project and AC 8 on the twin files and the example's
Sandstone joints; the other criteria are in test_shear_box_envelope.py. The
fit's values are the M17 (b) spec's AC 1, 2, 5 and 6, hand-calculated there.
"""

import math
from pathlib import Path

import pytest
from matplotlib.colors import to_hex

import hangtu as ht

AGS = Path(__file__).parents[1] / "data" / "ags"
#: 1 psf in kPa: 0.45359237 kg × 9.80665 m/s² / 0.3048² m² (exact).
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000
REL = 1e-9


@pytest.fixture(autouse=True)
def _no_hints():
    ht.settings.hints = False


def _shear_box(path, system, tmp_path):
    return ht.Project.from_ags(
        path, db=tmp_path / "data.sqlite", overwrite=True, display_units=system
    ).shear_box()


@pytest.fixture(scope="module")
def example(tmp_path_factory):
    p = ht.Project.from_ags(
        ht.examples.path("site.ags"),
        db=tmp_path_factory.mktemp("example") / "site.sqlite",
        display_units="US",
    )
    p.set_geology_map(ht.examples.path("strata.csv"))
    df = p.shear_box()
    # The Terrace samples added for M18 (d) are left out, so the hand fits of
    # M17 (b) stay the goldens.
    return df[~df["sample_reference"].isin(["B-2-D5", "B-5-D5", "B-6-D5"])]


def _lines(ax, gid):
    return [line for line in ax.lines if line.get_gid() == gid]


def _intercept_and_slope(line):
    (x0, x1), (y0, y1) = line.get_xdata(), line.get_ydata()
    slope = (y1 - y0) / (x1 - x0)
    return y0 - slope * x0, slope


def _box(ax):
    return next(text for text in ax.texts if text.get_gid() == "result_box").get_text()


# --- AC 5: groups -------------------------------------------------------------------


def test_soil_sets_by_geology_unit(example):
    soil = example[example["geology_unit"].isin(["Alluvium", "Terrace"])]
    _, ax, fit = ht.plot.shear_box_envelope(
        soil, group_by="geology_unit", display_units="US"
    )
    solid = _lines(ax, "peak_free")
    assert len(solid) == 2
    # The example's strata.csv colors.
    assert [to_hex(line.get_color()) for line in solid] == ["#5b8db8", "#e0b040"]
    expected = [(170, 699 / 1400), (71.0169492, 3933 / 5900)]
    for line, (c, b) in zip(solid, expected, strict=True):
        assert _intercept_and_slope(line) == pytest.approx((c, b), rel=1e-7)
    box = _box(ax)
    assert box.index("Alluvium") < box.index("Terrace")
    assert box.count("Lab:") == 6  # two pairs per strength for the Alluvium
    assert "Lab: c = 145 psf, φ = 27.4° (3 stages)" in box
    assert "Lab: c = 195 psf, φ = 25.6° (3 stages)" in box
    # The lab's values as it wrote them, not padded to 3 significant figures.
    assert "Lab: c = 5 psf, φ = 21.7° (3 stages)" in box
    assert [group["key"] for group in fit.groups] == [
        {"geology_unit": "Alluvium"},
        {"geology_unit": "Terrace"},
    ]
    legend = [text.get_text() for text in ax.get_legend().get_texts()]
    assert legend[:4] == ["Alluvium", "Terrace", "Peak", "Residual"]


# --- AC 8: units --------------------------------------------------------------------


def test_twin_files_agree(tmp_path):
    drawn = {}
    for name, system in (("site_si", "SI"), ("site_us", "US")):
        (tmp_path / name).mkdir()
        rows = _shear_box(AGS / f"{name}.ags", system, tmp_path / name)
        for display in ("SI", "US"):
            _, ax, _ = ht.plot.shear_box_envelope(rows, display_units=display)
            unit = "kPa" if display == "SI" else "psf"
            assert ax.get_xlabel() == f"Normal stress, σn ({unit})"
            assert ax.get_ylabel() == f"Shear stress, τ ({unit})"
            drawn[name, display] = {
                gid: _intercept_and_slope(_lines(ax, gid)[0])
                for gid in (
                    "peak_free",
                    "peak_through_origin",
                    "residual_free",
                    "residual_through_origin",
                )
            }
    reference = drawn["site_si", "SI"]
    assert reference["peak_free"] == pytest.approx((8, 0.6), rel=REL)
    for (_, display), lines in drawn.items():
        scale = 1 if display == "SI" else 1 / PSF
        for gid, (c, slope) in lines.items():
            assert slope == pytest.approx(reference[gid][1], rel=REL)
            # c is a difference of large numbers, so site_us.ags's 10
            # significant figures come back to about 5e-9 (the fit's AC 3).
            assert c == pytest.approx(reference[gid][0] * scale, rel=1e-7, abs=1e-9)


def test_sandstone_joints_in_mpa(example):
    joints = example[example["geology_unit"] == "Sandstone"]
    with ht.settings.override(display_overrides={"stress": "MPa"}):
        _, ax, fit = ht.plot.shear_box_envelope(joints, display_units="SI")
    assert fit.unit == "MPa"
    assert ax.get_xlabel() == "Normal stress, σn (MPa)"
    assert ax.get_ylabel() == "Shear stress, τ (MPa)"
    (solid,) = _lines(ax, "peak_free")
    c, slope = _intercept_and_slope(solid)
    assert c == pytest.approx(0.1, rel=1e-7)
    assert math.degrees(math.atan(slope)) == pytest.approx(38.106583, rel=1e-7)
    assert "Lab: c = 0.095 MPa, φ = 38.7° (3 stages)" in _box(ax)
