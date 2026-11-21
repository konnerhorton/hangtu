"""P14 against docs/plots/P14-consolidation-coefficients.md §12, AC 5 and 7.

AC 5 and 7 on the twin files and the example project; the other criteria are
in test_consolidation_coefficients.py. The values are the M19 (c1) spec's AC
1-3, hand-calculated there.
"""

import math
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

import hangtu as ht

AGS = Path(__file__).parents[1] / "data" / "ags"
#: 1 psf in kPa: 0.45359237 kg × 9.80665 m/s² / 0.3048² m² (exact).
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000


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


def _lines(ax, gid):
    return [line for line in ax.lines if line.get_gid() == gid]


def _at(lines, low, high):
    """The y value of the one segment from ``low`` to ``high``."""
    found = [
        line.get_ydata()[0]
        for line in lines
        if math.isclose(line.get_xdata()[0], low, rel_tol=1e-9)
        and math.isclose(line.get_xdata()[-1], high, rel_tol=1e-9)
    ]
    assert len(found) == 1
    return found[0]


def _footnote(ax):
    return " ".join(" ".join(text.get_text().split()) for text in ax.texts)


@pytest.mark.parametrize("name", ["site_si", "site_us"])
def test_footnote(name, request):
    """AC 5: the first increment is named, on either twin."""
    df = request.getfixturevalue(name)
    _, (_, lower) = ht.plot.consolidation_coefficients(df)
    assert (
        "Not drawn for BH1-U3-OED1: increment 1 (start stress not given)"
        in _footnote(lower)
    )
    plt.close("all")


@pytest.mark.parametrize("name", ["site_si", "site_us"])
def test_units_us(name, request):
    """AC 7: US display draws increment 4 in ft²/kip and ft²/yr, x in psf."""
    df = request.getfixturevalue(name)
    _, (upper, lower) = ht.plot.consolidation_coefficients(df, display_units="US")
    low, high = 100 / PSF, 200 / PSF
    volume = _at(_lines(upper, "volume_loading"), low, high)
    assert volume == pytest.approx(0.00754868948, rel=1e-6)
    root = _at(_lines(lower, "consolidation_root_time"), low, high)
    assert root == pytest.approx(22.6042118, rel=1e-6)
    assert lower.get_xlabel() == "Effective vertical stress, σ′v (psf)"
    assert "(ft²/kip)" in upper.get_ylabel()
    assert "(ft²/yr)" in lower.get_ylabel()
    plt.close("all")


@pytest.mark.parametrize("system", ["SI", "US"])
def test_twins_draw_alike(site_si, site_us, system):
    """The twin files draw the same recomputed m_v and c_v in either display."""
    drawn = []
    for df in (site_si, site_us):
        _, axs = ht.plot.consolidation_coefficients(df, display_units=system)
        drawn.append(
            [
                sorted(
                    (tuple(line.get_xdata()), tuple(line.get_ydata()))
                    for line in _lines(ax, gid)
                )
                for ax, gid in (
                    (axs[0], "volume_loading"),
                    (axs[0], "volume_unload_reload"),
                    (axs[1], "consolidation_root_time"),
                    (axs[1], "consolidation_log_time"),
                )
            ]
        )
        plt.close("all")
    for si, us in zip(*drawn, strict=True):
        assert len(si) == len(us)
        for (x_si, y_si), (x_us, y_us) in zip(si, us, strict=True):
            assert x_si == pytest.approx(x_us, rel=1e-9)
            assert y_si == pytest.approx(y_us, rel=1e-9)


def test_example_project(tmp_path):
    """The example project's specimens draw, in US units, without warnings."""
    p = ht.Project.from_ags(
        ht.examples.path("site.ags"), db=tmp_path / "site.sqlite", display_units="US"
    )
    p.set_geology_map(ht.examples.path("strata.csv"))
    fig, (upper, lower) = ht.plot.consolidation_coefficients(p.oedometer())
    assert len(_lines(upper, "volume_loading")) == 12
    assert len(_lines(upper, "volume_reported")) == 12
    assert _lines(lower, "consolidation_root_time")
    assert "Not drawn, no increments to draw:" in _footnote(lower)
    plt.close(fig)
