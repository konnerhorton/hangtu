from pathlib import Path

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
