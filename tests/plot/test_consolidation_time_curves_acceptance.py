"""P15 against docs/plots/P15-consolidation-time-curves.md §12 on the AGS files.

AC 1, 2 and 6 on BH1-U3's increment 4 in site_si.ags and site_us.ags, through
p.oedometer_readings(), and the example project's specimens in US units. The
values are the M19 (c2) spec's AC 1 and 2, hand-calculated there.
"""

import math
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

import hangtu as ht

AGS = Path(__file__).parents[1] / "data" / "ags"
REL = 1e-8
ZERO = 0.286233001
TIME_90 = 19.7847853
AT_50 = 0.423594862
TIME_50 = 4.82957834
PLOT = ht.plot.consolidation_time_curves


@pytest.fixture(autouse=True)
def _no_hints():
    ht.settings.hints = False


@pytest.fixture(autouse=True)
def _close():
    yield
    plt.close("all")


def _readings(path, system, tmp_path_factory, readings_map):
    p = ht.Project.from_ags(
        path,
        db=tmp_path_factory.mktemp(path.stem) / "p.sqlite",
        overwrite=True,
        display_units=system,
    )
    p.set_readings_map(readings_map)
    return p.oedometer_readings()


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    return {
        name: _readings(
            AGS / f"{name}.ags", system, tmp_path_factory, AGS / "readings_map.csv"
        )
        for name, system in (("site_si", "SI"), ("site_us", "US"))
    }


@pytest.fixture(scope="module")
def example(tmp_path_factory):
    return _readings(
        ht.examples.path("site.ags"),
        "US",
        tmp_path_factory,
        ht.examples.path("readings_map.csv"),
    )


def draw(df, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return PLOT(df, **kwargs)


def line(ax, gid):
    (found,) = [line for line in ax.lines if line.get_gid() == gid]
    return found


def result(ax):
    return [t.get_text() for t in ax.texts if t.get_gid() == "result"]


@pytest.mark.parametrize("name", ["site_si", "site_us"])
def test_ac1_ac2_on_the_twin_files(site, name):
    _, axs = draw(site[name], increments=["3", "4", "5"], display_units="SI")
    assert axs.shape == (3, 2)
    root, log = axs[1]
    assert root.get_title(loc="left") == "Increment 4: 100 → 200 kPa"
    assert line(root, "level_d0").get_ydata()[0] == pytest.approx(ZERO, rel=REL)
    assert line(root, "time_t90").get_xdata()[0] == pytest.approx(
        math.sqrt(TIME_90), rel=REL
    )
    assert line(log, "level_d50").get_ydata()[0] == pytest.approx(AT_50, rel=REL)
    assert line(log, "time_t50").get_xdata()[0] == pytest.approx(TIME_50, rel=REL)
    # The lab's c_v as the file writes it: site_us.ags has it in ft²/yr to 10
    # significant figures, which the m²/yr text keeps (README "Numbers in a box").
    lab = {"site_si": ("2.1", "1.8"), "site_us": ("2.100000000", "1.800000000")}
    assert result(root) == [f"c_v 2.15 m²/yr (lab {lab[name][0]})"]
    assert result(log) == [f"c_v 2.06 m²/yr (lab {lab[name][1]})"]
    # The lab reports c_v on increment 4 only.
    assert result(axs[0, 0])[0].endswith("(lab —)")
    assert axs[0, 0].figure._suptitle.get_text() == "BH1-U3-OED1, 5.20 m"


def test_ac6_us_units(site):
    # The lab's 2.1 m²/yr keeps its two figures in ft²/yr.
    _, axs = draw(site["site_si"], increments=["4"], display_units="US")
    root, _ = axs[0]
    assert line(root, "level_d0").get_ydata()[0] == pytest.approx(
        0.0112690158, rel=1e-6
    )
    assert result(root) == ["c_v 23.1 ft²/yr (lab 23)"]


def test_the_example_specimens_in_us_units(example):
    for specimen in ("B-4-U1-C1", "B-5-U2-C1"):
        fig, axs = draw(
            example,
            specimen=specimen,
            increments=["2", "3", "4", "5", "6", "11"],
            display_units="US",
        )
        assert axs.shape == (6, 2)
        assert "in" in axs[0, 0].get_ylabel()
        assert fig._suptitle.get_text().startswith(specimen)


def test_the_example_fast_increment_draws_both_reasons(example):
    _, axs = draw(example, specimen="B-5-U2-C1", increments=["3"])
    root, log = axs[0]
    reasons = [
        [t.get_text().replace("\n", " ") for t in ax.texts if t.get_gid() == "reason"]
        for ax in (root, log)
    ]
    assert reasons == [
        ["fewer than 3 readings in the first half of the increment's movement"],
        ["fewer than 3 pairs of times in the ratio 1:4 before the inflexion"],
    ]
    assert result(root) == result(log) == []
