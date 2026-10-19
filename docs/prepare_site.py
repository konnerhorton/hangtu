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
LOGO = Path(__file__).parent / "img" / "logo.txt"

# The small mark is drawn on a grid of character cells, CELL_WIDTH by
# CELL_HEIGHT. "=" is two bars across its cell and ":" two stacked squares, so
# the SVG needs no font and looks the same in every browser.
CELL_WIDTH = 6
CELL_HEIGHT = 10
STROKE = 2
ROWS = (3, 6)  # top of each bar or square in a cell
LOGO_COLORS = {"logo.svg": "#ffffff", "favicon.svg": "#3c3c3c"}


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


def logo_marks() -> tuple[list[str], list[str]]:
    """Return the wordmark and the small mark from ``docs/img/logo.txt``."""
    wordmark, small_mark = LOGO.read_text(encoding="utf-8").strip().split("\n\n")
    return wordmark.splitlines(), small_mark.splitlines()


def mark_svg(lines: list[str], color: str) -> str:
    """Draw an ASCII mark of "=" and ":" as SVG shapes on a square canvas."""
    width = CELL_WIDTH * max(len(line) for line in lines)
    height = CELL_HEIGHT * len(lines)
    side = max(width, height)
    left, top = (side - width) / 2, (side - height) / 2
    shapes = []
    for row, line in enumerate(lines):
        for column, char in enumerate(line):
            x = left + column * CELL_WIDTH
            for offset in ROWS:
                y = top + row * CELL_HEIGHT + offset
                if char == "=":
                    shapes.append((x, y, CELL_WIDTH))
                elif char == ":":
                    shapes.append((x + (CELL_WIDTH - STROKE) / 2, y, STROKE))
    rects = "".join(
        f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{STROKE}"/>'
        for x, y, w in shapes
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}" '
        f'fill="{color}">{rects}</svg>\n'
    )


def write_logo() -> None:
    """Write the header logo and the favicon from the small mark."""
    GENERATED.mkdir(parents=True, exist_ok=True)
    _, small_mark = logo_marks()
    for name, color in LOGO_COLORS.items():
        (GENERATED / name).write_text(mark_svg(small_mark, color), encoding="utf-8")
    print("Wrote logo.svg and favicon.svg")


def main() -> None:
    """Write every generated file."""
    run_examples()
    write_logo()


if __name__ == "__main__":
    main()
