"""mohr_coulomb_fit()'s overburden check (docs/work/reliability-guards.md, AC 7, 8).

The limit is max(10 × 25 kN/m³ × z, 500 kPa), hangtu's rule. By hand: at
5.4864 m (18 ft) it is 1,371.6 kPa; at 1 m, 500 kPa (the floor); at 10 m,
2,500 kPa.
"""

import warnings

import numpy as np
import pandas as pd
import pytest

import hangtu as ht

STRESSES = [
    "minor_principal_stress_at_failure",
    "major_principal_stress_at_failure",
    "effective_minor_principal_stress_at_failure",
    "effective_major_principal_stress_at_failure",
]
WARNING = r"another unit than declared \(psf declared as kPa\?\)"


def stages(minor, depth, depth_unit="m", consolidation=None, unit="kPa"):
    """Three stages with σ′1 = 3 σ′3 (φ′ = 30°), totals 100 above them."""
    minor = np.asarray(minor, dtype=float)
    data = {
        STRESSES[0]: minor + 100,
        STRESSES[1]: 3 * minor + 100,
        STRESSES[2]: minor,
        STRESSES[3]: 3 * minor,
        "depth": depth,
    }
    units = {**dict.fromkeys(STRESSES, unit), "depth": depth_unit}
    if consolidation is not None:
        data["effective_consolidation_stress"] = consolidation
        units["effective_consolidation_stress"] = unit
    df = pd.DataFrame(data)
    df.attrs["units"] = units
    return df


def fit_warnings(df):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = ht.analysis.mohr_coulomb_fit(df)
    return result, [str(w.message) for w in caught]


def test_psf_declared_as_kpa_warns_naming_the_row():
    # TODO's trial case: σ′c 3,680 "kPa" at 18 ft (limit 1,371.6 kPa).
    df = stages(
        [900.0, 1800.0, 3000.0],
        [18.0, 18.0, 18.0],
        depth_unit="ft",
        consolidation=[920.0, 1840.0, 3680.0],
    )
    _, messages = fit_warnings(df)
    (message,) = [m for m in messages if "overburden" in m]
    # 920 kPa is under the limit; the rows labeled 1 and 2 (index) are over it.
    assert message.startswith("mohr_coulomb_fit(): rows 1, 2 have")
    assert "3,680 kPa" in message


def test_usual_stresses_do_not_warn():
    # 400 kPa at 1 m (floor 500), 1,000 at 10 m (limit 2,500): no warning.
    df = stages([100.0, 400.0, 1000.0], [1.0, 1.0, 10.0])
    _, messages = fit_warnings(df)
    assert not any("overburden" in m for m in messages)


def test_without_a_depth_nothing_is_checked():
    df = stages([900.0, 1800.0, 3000.0], [np.nan] * 3)
    _, messages = fit_warnings(df)
    assert not any("overburden" in m for m in messages)
    df = stages([900.0, 1800.0, 3000.0], [1.0] * 3).drop(columns="depth")
    _, messages = fit_warnings(df)
    assert not any("overburden" in m for m in messages)


@pytest.mark.parametrize(("depth", "unit"), [(2.0, "m"), (2.0 / 0.3048, "ft")])
def test_the_limit_is_the_same_in_ft_and_m(depth, unit):
    # At 2 m the limit is the floor, 500 kPa: 501 warns, 499 doesn't.
    df = stages([100.0, 499.0, 501.0], [depth] * 3, depth_unit=unit)
    _, messages = fit_warnings(df)
    (message,) = [m for m in messages if "overburden" in m]
    assert "501 kPa" in message


def test_sigma_3_is_read_where_the_consolidation_stress_is_blank():
    df = stages([100.0, 200.0, 2600.0], [10.0] * 3, consolidation=[100, 200, None])
    _, messages = fit_warnings(df)
    assert any("2,600 kPa" in m for m in messages)


def test_stresses_in_another_unit_are_compared_in_kpa():
    # 30,000 psf = 1,436 kPa at 5 m (limit 1,250): warns; 20,000 psf doesn't.
    df = stages([10_000.0, 20_000.0, 30_000.0], [5.0] * 3, unit="psf")
    _, messages = fit_warnings(df)
    (message,) = [m for m in messages if "overburden" in m]
    assert "1,436 kPa" in message


def test_the_fit_is_unchanged():
    df = stages([900.0, 1800.0, 3000.0], [18.0] * 3, depth_unit="ft")
    result, _ = fit_warnings(df)
    plain, _ = fit_warnings(df.drop(columns="depth"))
    main, other = result.groups[0]["fits"][0], plain.groups[0]["fits"][0]
    assert main["friction_angle"] == pytest.approx(30.0, rel=1e-9)
    assert main["friction_angle"] == other["friction_angle"]
    assert main["cohesion"] == other["cohesion"]
