"""The docs site (docs/work/docs-site.md, Spec §8)."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
EXAMPLES = sorted((ROOT / "docs" / "site" / "examples").glob("*.py"))


def _load_prepare_site():
    script = ROOT / "docs" / "prepare_site.py"
    spec = importlib.util.spec_from_file_location("prepare_site", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare_site = _load_prepare_site()


@pytest.mark.parametrize("script", EXAMPLES, ids=lambda path: path.name)
def test_page_example_runs_clean(tmp_path, script):
    # Criterion 3: each example runs in an empty folder after installing hangtu.
    done = prepare_site.run_example(script, tmp_path)
    assert done.returncode == 0, done.stderr
    assert done.stderr == ""  # no warning, no traceback
    if "savefig(" in script.read_text(encoding="utf-8"):
        assert (tmp_path / f"{script.stem}.png").is_file()
