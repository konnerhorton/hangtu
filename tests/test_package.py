import importlib
from importlib.metadata import version

import pytest

import hangtu


def test_version_matches_installed_metadata():
    assert hangtu.__version__ == version("hangtu")


@pytest.mark.parametrize("module", ["pandas", "numpy", "matplotlib", "pint", "yaml"])
def test_phase_1_dependency_imports(module):
    importlib.import_module(module)
