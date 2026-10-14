from pathlib import Path

import pytest

import hangtu as ht

DATA = Path(__file__).parents[1] / "data" / "ags"
FILES = ("site_si", "site_us", "site_v404", "defects", "qc_defects")


@pytest.fixture(scope="session")
def projects(tmp_path_factory):
    """Each test file in a project database, display units US. Don't modify them."""
    folder = tmp_path_factory.mktemp("qc")
    return {
        name: ht.Project.from_ags(
            DATA / f"{name}.ags", db=folder / f"{name}.sqlite", display_units="US"
        )
        for name in FILES
    }
