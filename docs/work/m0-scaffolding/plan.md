# M0: Scaffolding — plan

Intent: [intent.md](intent.md). There is no separate spec; SPEC §12 is the spec.

Each build step is one commit, with ruff and pytest passing.

## Build 1: `M0: add package skeleton, dependencies and tool config`
- `pyproject.toml`:
  - `version = "0.1.0.dev0"`. 0.1.0 is the release target.
  - `[build-system]` uses `uv_build`. It's uv-native, so there's no extra tool, and it includes package data files under `src/ags_kit/` by default, as needed for `columns.yaml` at M1.
  - `dependencies`:
    - `pandas>=2.1.1,<3` (2.1.0 has no Python 3.12 wheels and fails to build from source)
    - `numpy>=1.26`
    - `matplotlib>=3.8`
    - `pint>=0.24.4` (0.24.0–0.24.3 fail to import with current `flexparser`)
    - `pyyaml>=6.0.1` (the first version with Python 3.12 wheels)
  - `[dependency-groups] dev = ["pytest>=8.0", "ruff>=0.17", "hypothesis>=6.100"]`. They need floors too, because `lowest-direct` also lowers dev dependencies (unfloored `hypothesis` resolved to 0.0.1).
  - `[tool.ruff]`:
    - `target-version = "py312"`
    - lint `select = ["E", "F", "W", "I", "UP", "B", "SIM", "RUF", "D"]` with `pydocstyle.convention = "numpy"` (matches pandas and matplotlib, which users already read)
    - per-file ignore of `D` for `tests/**`
    - `[tool.ruff.format] exclude = ["*.md"]`: ruff 0.17 formats Python blocks in Markdown, which would reflow the hand-aligned API sketches in SPEC and the plot specs
  - `[tool.pytest.ini_options]`:
    - `testpaths = ["tests"]`
    - `addopts = ["-ra", "--strict-markers", "--strict-config", "--import-mode=importlib"]`
    - `xfail_strict = true`
    - `filterwarnings = ["error"]`, so deprecations surface early. Expected warnings are asserted with `pytest.warns`.
    - One exception: ignore pyparsing's "deprecated - use" warnings raised from matplotlib. matplotlib < 3.10.7 calls pyparsing APIs that newer pyparsing deprecates. It works, so the floor stays at 3.8 rather than excluding users over a harmless warning.
- `src/ags_kit/__init__.py`: a module docstring, and `__version__` from `importlib.metadata.version("ags-kit")`. No subpackages yet; M1 creates `plot/` and `analysis/`.
- `tests/test_package.py`:
  - `import ags_kit` works, and `__version__` equals the installed metadata version.
  - Each Phase 1 dependency imports. This catches broken wheels across the matrix.
- `uv.lock` regenerated with `uv lock`.
- **SPEC §12.1:** write the new floors (Phase 1 and dev) into the spec, in the same commit as the pyproject change (CLAUDE.md workflow rule).

## Build 2: `M0: add CI workflow`
- `.github/workflows/ci.yml`:
  - Runs on push to `main` and on pull requests.
  - **`test` job:** matrix of `ubuntu-latest`, `windows-latest` and `macos-latest` × Python `3.12`, `3.13`, `3.14`, with `fail-fast: false`. Steps:
    - `astral-sh/setup-uv` (pinned major version)
    - `uv sync --locked --python ${{ matrix.python }}`
    - `uv run ruff check .`
    - `uv run ruff format --check .`
    - `uv run pytest`
  - **`lowest` job:** ubuntu, Python 3.12, `uv sync --resolution lowest-direct`, then `uv run pytest`. This proves the floors.
  - Set `MPLBACKEND: Agg` at the workflow level, ready for M1 plots.

## Build 3 (close-out): `M0: record commands and close out scaffolding`
- `CLAUDE.md`:
  - Replace "Pre-code: M0 (scaffolding) is next." with the current status.
  - Update the Commands section: remove "Set up at M0", and keep or adjust the three commands to match what landed. Use `ruff format --check` in the CI-equivalent check line.
- `TODO.md`: add an item, owned by You and Claude: "Create the public GitHub repo, push, and confirm M0 CI is green on the full matrix and the lowest job". It references SPEC §12.1 and §12.4.
- `pyproject.toml` `description`: leave as is. It's renamed with TODO 0.

## Verification (local, since there's no remote)
- `uv sync && uv run ruff check . && uv run ruff format --check . && uv run pytest` passes on 3.12.
- Run the other Python versions installed locally: `uv run --isolated --python 3.13 pytest` and `uv run --isolated --python 3.14 pytest`.
- Run the lowest job locally in a scratch environment: `UV_PROJECT_ENVIRONMENT=<scratchpad>/lowest uv sync --resolution lowest-direct --python 3.12 && UV_PROJECT_ENVIRONMENT=... uv run pytest`. If a floor fails to resolve or build, raise it, and update both SPEC §12.1 and `plan.md` in that commit. Note: `uv sync --resolution lowest-direct` rewrites `uv.lock`, so run `uv lock` afterward (and never use `--locked` in the lowest job).
- Validate the workflow schema: `uvx check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/ci.yml`. This uses a throwaway tool and adds no project dependency.
- `uv build` produces an sdist and a wheel. Check that the wheel contains `ags_kit/__init__.py`.
- Windows and macOS can't be checked locally. That stays open in the new TODO item.
