# Rename the package to hangtu — plan

Intent: [intent.md](intent.md). Spec: SPEC §1.1 (name decided in `4d810ca`).

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines is split. The unit is merged into `main` with `git merge --no-ff`, so `git revert -m 1 <merge>` undoes it whole.

## Substitutions
These are case-sensitive and use word boundaries:
- `ags_kit` → `hangtu`
- `ags-kit` → `hangtu`
- `AgsKit` → `Hangtu`
- `import ags_kit as ak` → `import hangtu as ht`
- `ak` → `ht` as a whole word, which covers `ak.` (for example, `target = ak` in `tests/plot/test_framework.py`)

**Left alone:**
- AGS4, AGSi, `python-ags4`, the `ags:` registry field, and future `read_ags` / `from_ags`.
- `docs/work/m0-*`, `m1-*` and `m2-*`, and git history.
- The pyproject `description` (branding, for later).
- The version, `0.1.0.dev0`.

## Build steps
1. **`rename: move the package to src/hangtu`**
   - `git mv src/ags_kit src/hangtu`, then `git mv src/hangtu/plot/ags_kit.mplstyle src/hangtu/plot/hangtu.mplstyle`.
   - `pyproject.toml`: `name = "hangtu"`, plus the `ags-kit` comment in `filterwarnings`.
   - `files("ags_kit")` in `_config.py` and `plot/style.py`, and the mplstyle path in `plot/style.py`.
   - `version("ags-kit")` in `__init__.py`.
   - Every `import ags_kit` / `from ags_kit` in `src/` and `tests/`. The `ak` alias stays for now, so this step only changes the module name.
   - `uv lock`, `uv sync`.
2. **`rename: AgsKitError → HangtuError, AgsKitHint → HangtuHint`**
   - `errors.py`, `__all__` in `__init__.py`, every raise, catch and `pytest.raises` / `pytest.warns`, and the comment in `config/defaults.yaml`.
   - `docs/plots/P00-framework.md` and `docs/plots/README.md`, which record these names.
3. **`rename: use the ht alias in tests, docstrings and messages`**
   - `ak` → `ht` in user-facing message text (`_settings.py`, `plot/_overlays.py`, `plot/_hints.py`, `plot/_legend.py`, `plot/_palette.py`), docstrings, YAML comments (`columns.yaml`, `config/defaults.yaml`), test regexes and test imports.
   - If the diff goes well past 300 lines, split it into source then tests.
4. **`rename: name the package hangtu in the docs`** (close-out)
   - `CLAUDE.md`: the title, the `src/hangtu/...` paths and the status line.
   - `README.md`: the title, `pip install hangtu` / `uv add hangtu`, and code samples. The pitch only gets the name swapped.
   - `SPEC.md`: the title, the `ak.` samples (§2.6, §3, §11), the package name in §12.2, and the paths in §10.3.
   - `docs/plots/*.md`, `docs/reference/process.md`, `docs/reference/eurocode7-summary.md`, and the paths in `TODO.md`.

## Verification
- After every step: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- **After step 1:**
  - `uv run python -c "import hangtu as ht; print(ht.__version__)"` prints `0.1.0.dev0`.
  - `import ags_kit` fails, with no stale dist-info or `__pycache__` left behind.
- **At the close-out:**
  - `git grep -n -E "ags_kit|ags-kit|AgsKit|\bak\b" -- ':!docs/work/m0-*' ':!docs/work/m1-*' ':!docs/work/m2-*' ':!docs/work/rename-hangtu'` finds nothing.
  - The lowest-versions run passes (CLAUDE.md "Commands"), then `git checkout uv.lock`.
  - `uv build` gives `hangtu-0.1.0.dev0-*.whl`, containing `hangtu/columns.yaml`, `hangtu/config/*.yaml`, `hangtu/units/*.yaml` and `hangtu/plot/hangtu.mplstyle`.

## After merge (by you)
- `mv ~/Documents/repos/ags-kit ~/Documents/repos/hangtu`.
- `mv ~/.claude/projects/-home-julia-Documents-repos-ags-kit ~/.claude/projects/-home-julia-Documents-repos-hangtu`.
- Delete `.venv` and run `uv sync` in the new folder.
