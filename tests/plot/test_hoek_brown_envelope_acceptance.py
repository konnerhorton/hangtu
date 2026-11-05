"""P32 against the acceptance criteria of docs/plots/P32-hoek-brown-envelope.md §12.

AC 2 and 3 on the example sandstone (rock_triaxial.csv); the other criteria
are in test_hoek_brown_envelope.py. The fit's values are the M17 (c) spec's
AC 3, hand-calculated there.
"""

import numpy as np
import pytest

import hangtu as ht

REL = 1e-7
#: rock_triaxial.csv's stresses are in MPa and its depths in ft.
UNITS = {
    "depth": "ft",
    "cell_pressure": "MPa",
    "deviator_stress_at_failure": "MPa",
    "back_pressure": "MPa",
    "pore_pressure_at_failure": "MPa",
    "reported_intact_compressive_strength": "MPa",
}


@pytest.fixture(autouse=True)
def _no_hints():
    ht.settings.hints = False


@pytest.fixture(scope="module")
def sandstone():
    df = ht.read_csv(ht.examples.path("rock_triaxial.csv"), units=UNITS)
    return ht.analysis.triaxial_failure_stresses(df)


def _draw(df, **kwargs):
    return ht.plot.hoek_brown_envelope(
        df,
        group_by="geology_unit",
        failure_modes=["Shear"],
        judgments=ht.examples.path("judgments.yaml"),
        **kwargs,
    )


def _lines(ax, gid):
    return [line for line in ax.lines if line.get_gid() == gid]


def _marks(ax, gid):
    return sorted(
        (
            line.get_marker(),
            float(line.get_xdata()[0]),
            float(line.get_ydata()[0]),
        )
        for line in _lines(ax, gid)
    )


def _box(ax):
    return next(text for text in ax.texts if text.get_gid() == "result_box").get_text()


def _legend(ax):
    return [t.get_text().replace("\n", " ") for t in ax.get_legend().get_texts()]


def test_2_points(sandstone):
    _, ax, _ = _draw(sandstone)
    filled = _marks(ax, "point")
    assert [marker for marker, *_ in filled].count("o") == 10
    assert [marker for marker, *_ in filled].count("s") == 3
    assert ("s", 20.0, 153.4) in filled
    assert ("o", 0.0, 54.2) in filled
    assert _marks(ax, "left_out_point") == [("D", 0.0, 38.6), ("^", 10.0, 88.0)]
    for line in _lines(ax, "left_out_point"):
        assert line.get_markerfacecolor() == "white"
    legend = _legend(ax)
    assert "Left out: Axial splitting (1)" in legend
    assert "Left out: Along bedding (1)" in legend
    assert {"Single stage", "Multistage"} <= set(legend)


def test_2_curves_and_box(sandstone):
    _, ax, fit = _draw(sandstone)
    (solid,) = _lines(ax, "free")
    assert solid.get_ydata()[0] == pytest.approx(63.8816013, rel=REL)
    assert solid.get_xdata()[-1] == 20
    (fixed,) = _lines(ax, "fixed_strength")
    assert fixed.get_ydata()[0] == pytest.approx(61, rel=1e-12)
    x, y = np.asarray(fixed.get_xdata()), np.asarray(fixed.get_ydata())
    constant = ((y[-1] - x[-1]) ** 2 - 61**2) / (61 * x[-1])
    assert constant == pytest.approx(13.4295478, rel=REL)
    box = _box(ax)
    assert "Free (all stages): σci = 63.9 MPa, mi = 12.4" in box
    assert "n = 13, R² = 0.951, σ3 0 to 20.0 MPa" in box
    assert "σci fixed at 61.0 MPa (judgments.yaml): mi = 13.4" in box
    assert "Single stage: σci = 62.8 MPa, mi = 13.8" in box
    assert "UCS: 3 tests, mean 60.8 MPa" in box
    assert "Lab: σci = 64 MPa, mi = 12.4" in box
    assert fit.unit == "MPa"


def test_3_multistage_false(sandstone):
    _, ax, _ = _draw(sandstone, multistage=False)
    assert _marks(ax, "left_out_point") == [
        ("D", 0.0, 38.6),
        ("^", 10.0, 88.0),
        ("s", 5.0, 93.0),
        ("s", 10.0, 115.8),
        ("s", 20.0, 153.4),
    ]
    assert "Left out: multistage (3)" in _legend(ax)
    (solid,) = _lines(ax, "free")
    assert solid.get_ydata()[0] == pytest.approx(62.7985047, rel=REL)
    # mi from the curve's end: ((σ1 - σ3)² - σci²) / (σci σ3).
    x, y = solid.get_xdata()[-1], solid.get_ydata()[-1]
    strength = solid.get_ydata()[0]
    assert ((y - x) ** 2 - strength**2) / (strength * x) == pytest.approx(
        13.7700751, rel=REL
    )
    lines = _box(ax).splitlines()
    first = next(i for i, line in enumerate(lines) if "Free (single stage)" in line)
    second = next(i for i, line in enumerate(lines) if "All stages:" in line)
    assert first < second
    assert "All stages: σci = 63.9 MPa, mi = 12.4" in lines[second]
