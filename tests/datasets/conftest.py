import importlib.util
from pathlib import Path

import pytest

import hangtu as ht

DATA = Path(__file__).parents[1] / "data" / "ags"
STRATA = DATA / "strata.csv"


def _load_make_files():
    spec = importlib.util.spec_from_file_location(
        "_make_files", DATA / "_make_files.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


make_files = _load_make_files()


@pytest.fixture
def fresh(tmp_path):
    """Build a project from a test file, display units SI; safe to modify.

    The GRAG fraction system is astm_uscs unless given, since the good files'
    BH2-D1 is a reported grading (datasets.md §12).
    """

    def build(name="site_si", **settings):
        settings.setdefault("display_units", "SI")
        settings.setdefault("grag_fraction_system", "astm_uscs")
        return ht.Project.from_ags(
            DATA / f"{name}.ags",
            db=tmp_path / f"{name}.sqlite",
            overwrite=True,
            **settings,
        )

    return build
