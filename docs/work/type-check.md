# Type check: run mypy on the package

## Intent

### Goal
Make mypy pass on `src/hangtu` and run it in CI next to ruff, so the type annotations, which are published in the API reference, stay accurate.

### Why
- The package is almost fully annotated (781 of 791 single-line signatures have a return type), but nothing checks the annotations, and they have drifted.
- A trial run on `main` at `1bd9201` (mypy, `--ignore-missing-imports`, `types-PyYAML`, no pandas-stubs) found 135 errors in 44 files. The ones sampled are wrong annotations, not runtime bugs:
  - `analysis/_spt.py:70` returns `dict[str, float | None]` but is annotated `float | dict[str, float] | None`.
  - `plot/_vertical.py:113` returns `str` where the annotation says `Literal['depth', 'elevation']`.
  - `stats/_fit.py:393` and `:535` do arithmetic on values typed as possibly `None`.
  - `plot/_values.py:99` calls `.get` on a value typed `dict[str, Any] | None`.
- Annotations are user documentation: mkdocstrings shows them in the API reference (SPEC §12.1, Docs). A wrong one misleads an engineer reading it and an AI agent writing code against hangtu.
- A checker catches unhandled `None`, the kind of bug closest to SPEC's "never drop data silently".
- The package has no `py.typed` marker, so a user's type checker and IDE ignore its annotations.

### Constraints
- **No behavior changes.** The fixes correct annotations and narrow types (`if x is None` and similar). If mypy finds a real bug, it gets its own commit with a test that fails before the fix.
- **Not strict.** The goal is checking the annotations that exist, not full typing coverage. Settings go in `[tool.mypy]` in `pyproject.toml`.
- **pandas-stubs is not used.** In the trial it added about 40 errors, mostly pandas' wide scalar unions (`Series.get` and similar), and none of the sampled ones were real problems.
- A `# type: ignore` names its error code (`# type: ignore[arg-type]`) and is used only where a third-party library's typing is the problem, not to silence a wrong annotation.
- mypy and `types-PyYAML` are new dev dependencies (SPEC §12.1 lists the dev dependencies). They are not runtime dependencies.
- The choice of mypy over pyright or ty can be revisited later; the config and CI step are small enough to swap.

### Out of scope
- Strict mode, `disallow_untyped_defs`, and annotating the remaining ~10 unannotated functions beyond what mypy needs.
- Type-checking `tests/`, `docs/` and `examples/`.
- pandas-stubs (above).
- Changing a public signature's meaning. A wrong annotation is corrected to match what the function already does.

### SPEC sections touched
- SPEC §12.1: the dev dependency list gains `mypy` and `types-PyYAML`; the CI line gains the type check.
- `CLAUDE.md`, Commands: the mypy command, and the "what CI runs" line.
- `.github/workflows/ci.yml`: a mypy step.
- `pyproject.toml`: `[tool.mypy]` and the dev dependencies.
- `src/hangtu/py.typed`: new.

### Decisions (intent review, 2026-11-02)
1. **Run mypy in one CI job** (Linux, Python 3.12), not in the 3 × 3 matrix. The result doesn't depend on the OS, and nine runs would add time for nothing. The `lowest` job doesn't run it either.
2. **`python_version = "3.12"`** in the config, matching `requires-python`, so code that only type-checks on a newer Python is caught.
3. **Ship `py.typed` in this unit.** It makes the annotations part of what users' tools see, which is the point of fixing them. The alternative is to wait until the annotations have been checked for a release.
4. **Settings:** `check_untyped_defs = true`, `warn_unused_ignores = true`, `warn_redundant_casts = true`, and `ignore_missing_imports` only for libraries without type information (`python_ags4`, `pint` if needed, `scipy` if needed), not globally.
5. **Branch and id: `type-check`.**

## Spec

There is no other home for this spec: it is a tooling change with no feature doc.

### Baseline
mypy 2.4.1 on `src/hangtu` at `f59d0b5`, in the project environment (pandas 2.3.3, numpy 2.5.4, matplotlib 3.11.2, pint 0.26.1, scipy 1.18.1), with the settings in Decision 1: **241 errors in 61 files.** By package: `plot` 121, `analysis` 58, `ags` 43, `stats` 40, `datasets` 14, `qc` 8, others 7. By code: `arg-type` 114, `assignment` 34, `union-attr` 21, `operator` 14, `index` 13, `attr-defined` 11, `return-value` 8, `call-overload` 8, the rest 18.

The trial in the intent (135 errors) ran with `ignore_missing_imports` for every library and without `check_untyped_defs`, so matplotlib's and numpy's type information was partly unused. The errors fall into three groups:
- **hangtu's own annotations:** wrong return types, `X | None` values used without a check, `str` passed where a `Literal` is declared.
- **Gaps in a library's type information:** `RcParams` indexed with a `str` variable (`plot/style.py`), `Colormap.colors`, `FigureCanvasBase.get_renderer`, `LayoutEngine.set(rect=...)`, positional `Axes.text` arguments.
- **hangtu's attributes on an `Axes`:** `ax.ags_notes`, `ax.grain_size_header`, `ax.grain_size_sieves` and `ax._grain_size_divider` (6 errors). Tests read `ax.ags_notes`.

### Changes
- **`pyproject.toml`:**
  - `mypy>=2.4.1` and `types-PyYAML` (floor: the version current when this unit was built) in the `dev` group; `uv.lock` updated.
  - `[tool.mypy]` with the settings in Decision 1.
- **`src/hangtu/py.typed`:** new, empty (PEP 561).
- **`src/hangtu/**`:** annotation and narrowing fixes until mypy passes (Decisions 2–4).
- **`.github/workflows/ci.yml`:** a `typecheck` job (Decision 5).
- **SPEC §12.1:** the CI line becomes "(ruff + pytest; mypy in one job)"; the dev dependencies line gains `mypy` and `types-PyYAML`.
- **`CLAUDE.md`, Commands:** `uv run mypy`, and the "what CI runs" line gains it.

### Decisions
1. **Settings.**
   ```toml
   [tool.mypy]
   files = ["src/hangtu"]
   python_version = "3.12"
   check_untyped_defs = true
   warn_unused_ignores = true
   warn_redundant_casts = true

   [[tool.mypy.overrides]]
   module = ["pandas.*", "scipy.*", "python_ags4.*", "mpl_toolkits.*"]
   ignore_missing_imports = true
   ```
   These four ship without type information (pandas without pandas-stubs, per the intent). numpy, matplotlib, pint and PyYAML (through `types-PyYAML`) are checked. `files` lets a bare `uv run mypy` check the package and nothing else.
2. **A wrong annotation is corrected to what the code does,** not the other way round (intent, No behavior changes). Where a value can really be `None`, the code gets an explicit check that raises the error it would have raised anyway, or the annotation admits `None`. A check never changes what is returned for valid input.
3. **Library typing gaps get a targeted ignore with its code:** `# type: ignore[attr-defined]` and so on, with no comment unless the reason isn't obvious from the line. `cast()` is used instead where the value's type is known and the cast makes the code clearer (for example, an `rcParams` key built from a string). `warn_unused_ignores` removes these once a library fixes its typing.
4. **hangtu's attributes on an `Axes` stay,** with `# type: ignore[attr-defined]` where they are set and read in `src/`. Moving them into an `Axes` subclass or a side table would change how the plot functions and tests work, which is outside this unit. A later unit can change this if the pattern spreads.
5. **CI: one `typecheck` job** on `ubuntu-latest`, Python 3.12, running `uv sync --locked` then `uv run mypy`. It uses the locked versions only: matplotlib's and numpy's type information changes between releases, so a mypy result holds for one set of versions. The `lowest` job doesn't run mypy, and a lock upgrade that brings new errors is fixed in the same commit as the upgrade.
6. **A real bug found by mypy** is fixed in its own commit, with a test that fails before the fix and the bug named in the commit body. If it changes documented behavior, stop and ask before fixing it.

### Acceptance criteria
1. **Passes:** `uv run mypy` reports `Success: no issues found` on `src/hangtu`.
2. **No blanket ignores:** `grep -rn "type: ignore" src/hangtu` shows no bare `# type: ignore` (every one names a code), and no module-level `# mypy: ignore-errors`. The `[tool.mypy]` table has no `disable_error_code` and no override other than the four in Decision 1.
3. **The sampled annotations are right:** `analysis/_spt.py:70`, `plot/_vertical.py:113`, `stats/_fit.py:393` and `:535`, and `plot/_values.py:99` (intent, Why) are fixed by an annotation or a check, not by an ignore.
4. **No behavior change:** the full suite passes with the same counts as on `f59d0b5` (plus any test added under Decision 6), ruff passes, and the docs site builds with `--strict` and no griffe warnings.
5. **Annotations ship:** the wheel from `uv build` contains `hangtu/py.typed`.
6. **CI runs it:** `ci.yml` has the `typecheck` job. A type error planted in the working tree (not committed) makes `uv run mypy` exit non-zero; the check is recorded here.
7. **Docs:** SPEC §12.1 and `CLAUDE.md` Commands name mypy, and the "what CI runs" line in `CLAUDE.md` matches `ci.yml`.

## Plan

Each step is one commit, green on ruff and the full suite. mypy isn't in CI until step 7, so a commit can leave errors in packages a later step fixes; each fix step ends with `uv run mypy` clean for the files it touches. A real bug found along the way (Decision 6) gets its own commit before the step it was found in.

How each error is fixed: a wrong annotation is changed to what the code returns (Decision 2); an `X | None` used unchecked gets a check that raises the error the code would have hit anyway, or an annotation that admits `None`; a library typing gap gets `# type: ignore[<code>]`, or `cast()` where clearer (Decision 3).

### Step 1: `type-check: configure mypy and ship py.typed`
- `pyproject.toml`: `mypy>=2.4.1` and `types-PyYAML` in `dev`; `[tool.mypy]` and the override from Decision 1. `uv lock`.
- `src/hangtu/py.typed`, empty.
- Baseline on `5639507` (AC4): 3,411 passed, no skips or xfails.
- AC5: `uv build`, and the wheel lists `hangtu/py.typed`.

### Step 2: `type-check: fix annotations in ags and the top-level modules`
- `ags/` (mostly `_units.py`, 31 errors), `_judgments.py`, `project.py`, `registry.py`, `sheet.py`, `units/__init__.py`.

### Step 3: `type-check: fix annotations in analysis`
- Mostly `_vertical_stress.py` (18), `_mohr_coulomb.py`, `correlations/_framework.py`; `_spt.py:70` (AC3).

### Step 4: `type-check: fix annotations in stats`
- Mostly `_fit.py` (19), including `:393` and `:535` (AC3), and `_significance.py`.

### Step 5: `type-check: fix annotations in datasets and qc`

### Step 6: `type-check: fix annotations in plot`
- `_vertical.py:113` and `_values.py:99` (AC3), the `Axes` attributes (Decision 4), `style.py`'s `rcParams` keys (Decision 3).
- Split in two if it passes ~300 changed lines: the shared helpers (`_legend`, `_notes`, `_overlays`, `_profile`, `style`), then the plot functions.

### Step 7: `type-check: run mypy in CI and close out`
- `.github/workflows/ci.yml`: the `typecheck` job (Decision 5).
- SPEC §12.1: the CI line and the dev dependencies.
- `CLAUDE.md`: `uv run mypy` in Commands and in the "what CI runs" line; a convention that a `# type: ignore` names its code and covers only a library's typing gap.
- Check AC1–AC4, AC6 and AC7, including the strict docs build, and record AC6 and the final counts here.
