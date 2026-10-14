from pathlib import Path

import pytest

import hangtu as ht

DATA = Path(__file__).parents[1] / "data" / "ags"
STRATA = DATA / "strata.csv"


@pytest.fixture
def fresh(tmp_path):
    """Build a project from a test file, display units SI; safe to modify."""

    def build(name="site_si", **settings):
        settings.setdefault("display_units", "SI")
        return ht.Project.from_ags(
            DATA / f"{name}.ags", db=tmp_path / f"{name}.sqlite", **settings
        )

    return build
