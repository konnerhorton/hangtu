"""P13 against the acceptance criteria of docs/plots/P13-consolidation-curve.md §12.

AC 5 and 8 on the twin files and the example project; the other criteria are
in test_consolidation_curve.py. The fit's values are the M19 (b) spec's AC 1-6
and its Example data, hand-calculated there.
"""

import math
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

import hangtu as ht

AGS = Path(__file__).parents[1] / "data" / "ags"
#: 1 psf in kPa: 0.45359237 kg × 9.80665 m/s² / 0.3048² m² (exact).
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000
REL = 1e-9


@pytest.fixture(autouse=True)
def _no_hints():
    ht.settings.hints = False


def _oedometer(name, system, tmp_path_factory):
    return ht.Project.from_ags(
        AGS / f"{name}.ags",
        db=tmp_path_factory.mktemp(name) / f"{name}.sqlite",
        overwrite=True,
        display_units=system,
    ).oedometer()


@pytest.fixture(scope="module")
def site_si(tmp_path_factory):
    return _oedometer("site_si", "SI", tmp_path_factory)


@pytest.fixture(scope="module")
def site_us(tmp_path_factory):
    return _oedometer("site_us", "US", tmp_path_factory)


@pytest.fixture(scope="module")
def example(tmp_path_factory):
    p = ht.Project.from_ags(
        ht.examples.path("site.ags"),
        db=tmp_path_factory.mktemp("example") / "site.sqlite",
        display_units="US",
    )
    p.set_geology_map(ht.examples.path("strata.csv"))
    p.set_judgments(ht.examples.path("judgments.yaml"))
    return p


def _lines(ax, gid):
    return [line for line in ax.lines if line.get_gid() == gid]


def _box(ax):
    box = next(text for text in ax.texts if text.get_gid() == "result_box")
    return " ".join(box.get_text().split())


def _footnote(ax):
    return " ".join(
        " ".join(text.get_text().split())
        for text in ax.texts
        if text.get_gid() != "result_box"
    )


def _log_line(line):
    (x0, x1), (y0, y1) = line.get_xdata(), line.get_ydata()
    slope = (y1 - y0) / (math.log10(x1) - math.log10(x0))
    return y0 - slope * math.log10(x0), slope


def test_effective_vertical_stress_and_box(site_si):
    """AC 5: σ′v0 = 80 kPa, the dotted line, the box's class and its row."""
    df = site_si.assign(effective_vertical_stress=80.0)
    df.attrs["units"] = {**site_si.attrs["units"], "effective_vertical_stress": "kPa"}
    _, ax, fit = ht.plot.consolidation_curve(df, display_units="SI")
    (line,) = _lines(ax, "effective_vertical_stress")
    assert list(line.get_xdata()) == [80.0, 80.0]
    assert line.get_linestyle() == ":"
    assert "OCR = 3.31, Δe/e0 = 0.0252: very good to excellent (OCR 2-4 row)" in _box(
        ax
    )
    assert "The Δe/e0 class uses this test's OCR" in _footnote(ax)
    assert fit.specimens[0]["overconsolidation_ratio"] == pytest.approx(
        3.30502070, rel=1e-8
    )
    plt.close("all")


def test_no_caveat_without_a_class(site_si):
    _, ax, _ = ht.plot.consolidation_curve(site_si, display_units="SI")
    assert "class uses this test's OCR" not in _footnote(ax)
    plt.close("all")


@pytest.mark.parametrize("system", ["SI", "US"])
def test_units_on_the_twin_files(site_si, site_us, system):
    """AC 8: the same lines in e on both files, σ′p scaled, labels in kPa or psf."""
    _, ax_si, fit_si = ht.plot.consolidation_curve(site_si, display_units=system)
    _, ax_us, fit_us = ht.plot.consolidation_curve(site_us, display_units=system)
    unit = "kPa" if system == "SI" else "psf"
    scale = 1.0 if system == "SI" else 1 / PSF
    for ax in (ax_si, ax_us):
        assert ax.get_xlabel() == f"Effective vertical stress, σ′v ({unit})"
        (cc,) = _lines(ax, "compression_index")
        assert _log_line(cc)[1] == pytest.approx(-0.282363888, rel=1e-8)
        ((stress,), _) = _lines(ax, "preconsolidation_stress")[0].get_data()
        assert stress == pytest.approx(264.401656 * scale, rel=1e-8)
        # 264.401656 kPa is 5522.15 psf; the box gives 3 significant figures.
        expected = "264 kPa" if system == "SI" else "5,520 psf"
        assert f"σ′p = {expected} (Oikawa)" in _box(ax)
    e_si = _lines(ax_si, "loading_point")[0].get_ydata()
    e_us = _lines(ax_us, "loading_point")[0].get_ydata()
    assert list(e_si) == list(e_us)
    assert fit_si.unit == fit_us.unit == unit
    plt.close("all")


def test_example_project(example):
    """The example's two specimens, the Example data's values in the box."""
    _, ax, fit = ht.plot.consolidation_curve(example.oedometer(), display_units="US")
    box = _box(ax)
    assert "B-4-U1-C1, 13.0 ft: σ′p = 1,620 psf (Oikawa) Pacheco Silva: 1,620" in box
    assert "Cc = 0.388, Cr = 0.0382, Cs = 0.0590, CR = 0.186" in box
    assert "B-5-U2-C1, 18.0 ft: σ′p = 4,230 psf (Oikawa) Pacheco Silva: 3,940" in box
    assert "Cc = 0.254, Cr = 0.0326, Cs = 0.0399, CR = 0.137" in box
    assert "Not drawn, no increments to draw: B-1-U2-SW1" in _footnote(ax)
    assert len(_lines(ax, "loading_point")) == 2
    # In specimen_id order (80, 81, 82).
    assert [s["label"] for s in fit.specimens] == [
        "B-4-U1-C1",
        "B-5-U2-C1",
        "B-1-U2-SW1",
    ]
    plt.close("all")


def test_example_with_effective_vertical_stress(example):
    """B-5's σ′v0 from vertical_stress(): OCR, Δe/e0 and the class in the box."""
    oed = ht.analysis.vertical_stress(
        example.oedometer(holes=["B-5"]), stratigraphy=example.stratigraphy()
    )
    _, ax, fit = ht.plot.consolidation_curve(oed, display_units="US")
    (record,) = fit.specimens
    stress = record["preconsolidation_stress"]
    in_situ = record["effective_vertical_stress"]
    (line,) = _lines(ax, "effective_vertical_stress")
    assert line.get_xdata()[0] == pytest.approx(in_situ, rel=REL)
    assert f"OCR = {stress / in_situ:.3g}, Δe/e0 = " in _box(ax)
    assert "(OCR 2-4 row)" in _box(ax)
    plt.close("all")
