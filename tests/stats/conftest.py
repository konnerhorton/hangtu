import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import hangtu as ht

DATA = Path(__file__).parents[1] / "data" / "ags"


@pytest.fixture
def fresh(tmp_path):
    """Build a project from a test file, display units SI."""

    def build(name="site_si", **settings):
        settings.setdefault("display_units", "SI")
        return ht.Project.from_ags(
            DATA / f"{name}.ags",
            db=tmp_path / f"{name}.sqlite",
            overwrite=True,
            **settings,
        )

    return build


#: Helsel et al. (2020) Example 5.1: NH4orgN in precipitation, mg/L.
INDUSTRIAL = [0.59, 0.87, 1.10, 1.10, 1.20, 1.30, 1.60, 1.70, 3.20, 4.00]
RESIDENTIAL = [0.30, 0.36, 0.50, 0.70, 0.70, 0.90, 0.92, 1.00, 1.30, 9.70]


@pytest.fixture
def helsel():
    """Helsel et al. (2020) Example 5.1: industrial, then residential."""
    return list(INDUSTRIAL), list(RESIDENTIAL)


@pytest.fixture
def three_groups():
    """The spec's A, B, C (m15d, AC 4 and 5) as a frame of s_u in kPa."""
    values = {
        "A": [12, 15, 18, 20, 22],
        "B": [25, 28, 30, 35, 41, 44],
        "C": [14, 16, 17, 21],
    }
    frame = pd.DataFrame(
        {
            "geology_unit": [key for key, items in values.items() for _ in items],
            "undrained_shear_strength": [
                float(v) for items in values.values() for v in items
            ],
        }
    )
    return ht.set_units(frame, {"undrained_shear_strength": "kPa"})


@pytest.fixture(scope="module")
def example_index(tmp_path_factory):
    """The example project's index properties with USCS symbols (m15e, 20 rows)."""
    folder = tmp_path_factory.mktemp("example")
    p = ht.Project.from_ags(ht.examples.path("site.ags"), db=folder / "site.sqlite")
    p.set_geology_map(ht.examples.path("strata.csv"))
    # The example's expected warnings: Terrace curves stop above D10, and the
    # specimens without grain size or a plasticity class have no symbol.
    with (
        pytest.warns(UserWarning, match="D10 in 6 curves"),
        pytest.warns(UserWarning, match="uscs_symbol is blank for 6 of 14"),
        pytest.warns(UserWarning, match="aashto_group is blank for 6 of 14"),
        pytest.warns(UserWarning, match="uscs_symbol is blank for 12 of 20"),
    ):
        index = p.index_properties(geology_fields=["GEOL_GEOL", "GEOL_LEG"])
        return ht.analysis.uscs(index)


# --- Shared with the select(), model-set and Mohr-Coulomb set tests ---

PHI = "effective_friction_angle"
COHESION = "effective_cohesion"
STRESSES = [
    "minor_principal_stress_at_failure",
    "major_principal_stress_at_failure",
    "effective_minor_principal_stress_at_failure",
    "effective_major_principal_stress_at_failure",
]
FIT = "Mohr-Coulomb fit (CD)"
G1 = {
    "source": "A",
    "method": "characteristic",
    "estimate": "mean",
    "side": "low",
    "distribution": "normal",
    "reason": "a mean over a long slip surface",
}
FITTED = {"source": FIT, "method": "fitted", "reason": "three CD stages"}


def phi(name, values):
    frame = pd.DataFrame(
        {
            "geology_unit": "Sand",
            "depth": np.arange(1.0, len(values) + 1),
            "correlation_name": name,
            PHI: values,
        }
    )
    return ht.set_units(frame, {PHI: "deg", "depth": "m"})


def sources():
    return phi("A", [34.0, 36.0, 37.0, 38.0, 40.0]), phi(
        "B", [33.0, 35.0, 36.0, 39.0, 41.0]
    )


def triaxial(mean_stresses, cohesion=5.0, angle=30.0, **columns):
    """CD stages on t = c′ cos φ′ + s′ sin φ′, at each s′, totals 300 kPa above."""
    s = np.asarray(mean_stresses, dtype=float)
    t = cohesion * math.cos(math.radians(angle)) + s * math.sin(math.radians(angle))
    minor, major = s - t, s + t
    df = pd.DataFrame(
        {
            STRESSES[0]: minor + 300,
            STRESSES[1]: major + 300,
            STRESSES[2]: minor,
            STRESSES[3]: major,
            "test_type": "CD",
            "geology_unit": "Sand",
            "depth": [3.0, 4.0, 5.0][: len(s)] if len(s) <= 3 else 4.0,
            **columns,
        }
    )
    df.attrs["units"] = {**dict.fromkeys(STRESSES, "kPa"), "depth": "m"}
    return df


def g3_fit():
    """G3: three CD stages at s′ = 100, 200, 300 kPa; c′ = 5 kPa, φ′ = 30°."""
    return ht.analysis.mohr_coulomb_fit(
        triaxial([100.0, 200.0, 300.0]), group_by="geology_unit"
    )


# --- Shared with the compare_sources() tests ---

SU = "undrained_shear_strength"
HATANAKA = "effective_friction_angle_hatanaka_uchida_1996"
KULHAWY = "effective_friction_angle_kulhawy_mayne_1990"
STROUD = "undrained_shear_strength_stroud_1974"
BAND = r"left out 1 rows of 'effective_friction_angle' that give only a range"
#: 1 psf in kPa (exact): 0.45359237 kg × 9.80665 m/s² / 0.3048² m² / 1000.
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000


def _compare(*sources, **kwargs):
    """Compare, failing on any warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return ht.stats.compare_sources(*sources, **kwargs)


def _spt_phi():
    """G2's correlations A and B in one frame, as an SPT frame holds them."""
    a = [31.2, 34.8, 36.1, 33.0, 38.4, 35.5, 32.7, 37.9]
    b = [34.0, 36.5, 39.2, 35.1, 41.0, 37.3, np.nan, np.nan]
    alluvium = [30.1, 31.5, 29.8]
    df = pd.DataFrame(
        {
            "loca_id": [f"BH{i % 4 + 1:02d}" for i in range(19)],
            "geology_unit": ["Terrace"] * 16 + ["Alluvium"] * 3,
            "depth": np.linspace(1.5, 19.5, 19),
            PHI: [*a, *b, *alluvium],
            f"{PHI}_lower": [np.nan] * 14 + [33.0, np.nan] + [np.nan] * 3,
            f"{PHI}_upper": [np.nan] * 14 + [38.0, np.nan] + [np.nan] * 3,
            "correlation_name": [HATANAKA] * 8 + [KULHAWY] * 8 + [HATANAKA] * 3,
            "correlation_qualifier": [""] * 4 + [">"] + [""] * 14,
        }
    )
    df.attrs["units"] = {
        PHI: "deg",
        f"{PHI}_lower": "deg",
        f"{PHI}_upper": "deg",
        "depth": "m",
    }
    return df


def _su():
    """G3: UU and field vane in kPa."""
    df = pd.DataFrame(
        {
            "geology_unit": "Alluvium",
            "source": ["lab"] * 4 + ["field"] * 3,
            "test_type": ["UU"] * 4 + ["in situ vane"] * 3,
            SU: [42.0, 55.0, 61.0, 48.0, 58.0, 71.0, 66.0],
        }
    )
    df.attrs["units"] = {SU: "kPa"}
    return df


def _stroud():
    """G3: Stroud (1974) estimates in psf."""
    df = pd.DataFrame(
        {
            "geology_unit": "Alluvium",
            SU: [1200.0, 1500.0, 1350.0],
            "correlation_name": STROUD,
        }
    )
    df.attrs["units"] = {SU: "psf"}
    return df


CONVERTED = "shear box, converted (Kulhawy & Mayne 1990)"
NEGATIVE = r"the free line's intercept is negative"


def _triaxial_frame(points, **columns):
    """CD stages with effective (σ′3, σ′1) and totals 300 kPa above them."""
    minor, major = (np.array(v, dtype=float) for v in zip(*points, strict=True))
    df = pd.DataFrame(
        {
            STRESSES[0]: minor + 300,
            STRESSES[1]: major + 300,
            STRESSES[2]: minor,
            STRESSES[3]: major,
            "test_type": "CD",
            **columns,
        }
    )
    df.attrs["units"] = {**dict.fromkeys(STRESSES, "kPa"), "depth": "m"}
    return df


def _mohr_coulomb(group_by="geology_unit"):
    """G2's triaxial fit: φ′ 36° in Terrace at 4.0-9.0 m; one stage in Alluvium."""
    df = _triaxial_frame(
        [(50, 192.592), (100, 385.184), (200, 770.368), (100, 400.0)],
        geology_unit=["Terrace"] * 3 + ["Alluvium"],
        depth=[4.0, 6.5, 9.0, 3.0],
    )
    # σ′1 is rounded to 3 decimals, so the free intercept is a hair below 0.
    with pytest.warns(UserWarning, match=r"intercept is negative") as caught:
        fit = ht.analysis.mohr_coulomb_fit(df, group_by=group_by)
    assert len(caught) == 1, [str(w.message) for w in caught]
    return fit


def _conversion():
    """G2's shear box: τ = σn tan 30°, cohesionless, φ′cv 32° → 30.5777°."""
    df = pd.DataFrame(
        {
            "geology_unit": "Terrace",
            "applied_normal_stress": [50.0, 100.0, 200.0],
            "peak_shear_stress": [28.867513, 57.735027, 115.470054],
            "depth": [5.0, 5.0, 5.0],
        }
    )
    df.attrs["units"] = {
        "applied_normal_stress": "kPa",
        "peak_shear_stress": "kPa",
        "depth": "m",
    }
    with pytest.warns(UserWarning, match=NEGATIVE):
        fit = ht.analysis.shear_box_fit(df, group_by="geology_unit", cohesion=0)
    return ht.analysis.friction_angle_from_shear_box(
        fit, soil="cohesionless", critical_state_friction_angle={"Terrace": 32}
    )


def _g2(**kwargs):
    with pytest.warns(UserWarning, match=BAND):
        return ht.stats.compare_sources(
            _spt_phi(), _mohr_coulomb(), _conversion(), value=PHI, **kwargs
        )
