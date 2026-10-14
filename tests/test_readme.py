"""Every Python block in README.md runs (docs/work/m9-release.md, spec §6)."""

import re
from pathlib import Path

import matplotlib.pyplot as plt

README = Path(__file__).parents[1] / "README.md"


def test_readme_python_blocks_run(tmp_path, monkeypatch):
    text = README.read_text(encoding="utf-8")
    blocks = re.findall(r"```python\n(.*?)```", text, flags=re.DOTALL)
    assert len(blocks) == 2
    monkeypatch.chdir(tmp_path)
    namespace = {}
    for block in blocks:  # in order: later blocks use earlier imports
        exec(compile(block, str(README), "exec"), namespace)
    assert (tmp_path / "spt_profile.png").is_file()
    assert (tmp_path / "my_spt.csv").is_file()
    plt.close("all")
