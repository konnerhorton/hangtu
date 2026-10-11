import importlib
from importlib.metadata import version

import pytest

import ags_kit


def test_version_matches_installed_metadata():
    assert ags_kit.__version__ == version("ags-kit")


@pytest.mark.parametrize("module", ["pandas", "numpy", "matplotlib", "pint", "yaml"])
def test_phase_1_dependency_imports(module):
    importlib.import_module(module)
