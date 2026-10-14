# Rename the package to hangtu

## Intent

### Goal
Rename the package from `ags-kit` / `ags_kit` to **`hangtu`**, imported as `import hangtu as ht`. The change is mechanical only: the distribution name, the import package, the package-named error classes, the `ak` alias, and the prose that names the package.

### Why
- `ags-kit` is a working name (SPEC §1.1, TODO #0), and it has to be settled before the first PyPI release.
- It ties the package to one file format, while DIGGS support is on the roadmap.
- US engineers, the target audience, mostly don't know AGS.
- "AGS" is a trade body's acronym, and that body's official library is `python-ags4`, so `ags-kit` could look endorsed.
- Renaming now, after M2 and before M3, means fewer references to change than waiting until M5.

### Constraints
- **No behavior changes.** The same tests pass before and after, and only names change. Every build commit leaves ruff and pytest green.
- **Leave other uses of "AGS" alone:** AGS4, AGSi, `python-ags4`, the `ags:` registry field, and future `read_ags` / `from_ags`.
- **Frozen history stays as written.** `docs/work/m0-*`, `m1-*` and `m2-*` and git history aren't rewritten.
- **One unit, easy to undo.** It is merged into `main` with `git merge --no-ff`, so `git revert -m 1 <merge>` undoes the whole rename.
- **Commits by kind** (CLAUDE.md "Git and commits"), each a pure substitution:
  - the package move and import name;
  - the error class names;
  - the `ht` alias;
  - the docs.
- If a change alters a recorded decision, the spec that records it changes in the same commit. That applies to the error class names in P00.
- No new dependencies (SPEC §12.1).
- **Done when:**
  - a leftover search for `ags_kit|ags-kit|AgsKit|\bak\b` (outside frozen history) finds nothing;
  - `uv build` produces a `hangtu` wheel containing all the package data;
  - CI is green.

### Decisions to confirm
- **Error classes:** `AgsKitError` → `HangtuError` and `AgsKitHint` → `HangtuHint`. Users will see these names in tracebacks and `warnings` filters.
- **The style file:** `plot/ags_kit.mplstyle` → `plot/hangtu.mplstyle`.
- **No separate `spec.md`.** The spec commit records the name in SPEC §1.1, removes "rename settled (TODO 0)" from the M5 row in §12.4, and deletes TODO #0. Two items from TODO #0 move into §1.1:
  - "AGS and DIGGS stay in the description, keywords and README";
  - "check PyPI availability again just before the first release".

### Out of scope
- **Branding:** what the name means, the README pitch, and the PyPI description and keywords. The pyproject `description` stays as it is for now.
- Publishing a placeholder release to claim the name on PyPI.
- **Renaming the repo folder.** You'll do this after the merge, and move Claude's memory folder to match.
- The version stays at `0.1.0.dev0`.

### SPEC sections touched
- §1.1 (name decided), §12.2 (package layout) and §12.4 (M5 row).
- Every other mention of the name and every `ak.` sample changes mechanically in the close-out: §2.6, §3, §4, §10.3, §11 and the title.
- Docs: `docs/plots/P00-framework.md` (error class names), the other plot specs, `docs/plots/README.md`, `docs/reference/`, `README.md`, `CLAUDE.md` and `TODO.md`.

## Plan

Spec: SPEC §1.1 (name decided in `4d810ca`).

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines is split. The unit is merged into `main` with `git merge --no-ff`, so `git revert -m 1 <merge>` undoes it whole.

### Substitutions
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

### Build steps
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

### Verification
- After every step: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- **After step 1:**
  - `uv run python -c "import hangtu as ht; print(ht.__version__)"` prints `0.1.0.dev0`.
  - `import ags_kit` fails, with no stale dist-info or `__pycache__` left behind.
- **At the close-out:**
  - `git grep -n -E "ags_kit|ags-kit|AgsKit|\bak\b" -- ':!docs/work/m0-*' ':!docs/work/m1-*' ':!docs/work/m2-*' ':!docs/work/rename-hangtu.md'` finds nothing.
  - The lowest-versions run passes (CLAUDE.md "Commands"), then `git checkout uv.lock`.
  - `uv build` gives `hangtu-0.1.0.dev0-*.whl`, containing `hangtu/columns.yaml`, `hangtu/config/*.yaml`, `hangtu/units/*.yaml` and `hangtu/plot/hangtu.mplstyle`.

### After merge (by you)
- `mv ~/Documents/repos/ags-kit ~/Documents/repos/hangtu`.
- `mv ~/.claude/projects/-home-julia-Documents-repos-ags-kit ~/.claude/projects/-home-julia-Documents-repos-hangtu`.
- Delete `.venv` and run `uv sync` in the new folder.
