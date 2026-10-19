"""Write the docs site's generated files before a build.

Spec: docs/work/docs-site.md, Spec §5.

Run from the repo root, then build:

    uv run python docs/prepare_site.py
    uv run zensical build --clean --strict
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SITE = Path(__file__).parent / "site"
EXAMPLES = SITE / "examples"
GENERATED = SITE / "img" / "generated"


def run_example(script: Path, folder: Path) -> subprocess.CompletedProcess:
    """Run a page example in ``folder`` as a user would, in a fresh Python."""
    env = {**os.environ, "MPLBACKEND": "Agg"}
    env.pop("PYTHONWARNINGS", None)
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=folder,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )


def run_examples() -> None:
    """Run each page example and copy the figure it saves to ``img/generated/``."""
    GENERATED.mkdir(parents=True, exist_ok=True)
    for script in sorted(EXAMPLES.glob("*.py")):
        with tempfile.TemporaryDirectory() as tmp:
            done = run_example(script, Path(tmp))
            if done.returncode != 0 or done.stderr:
                sys.exit(f"Example {script.name} failed or warned:\n{done.stderr}")
            figure = Path(tmp) / f"{script.stem}.png"
            if figure.is_file():
                shutil.copy(figure, GENERATED / figure.name)
        print(f"Ran {script.name}")


def main() -> None:
    """Write every generated file."""
    run_examples()


if __name__ == "__main__":
    main()
