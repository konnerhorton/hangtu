from pathlib import Path

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
