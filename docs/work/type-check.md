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
