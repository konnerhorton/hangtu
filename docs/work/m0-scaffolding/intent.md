# M0: Scaffolding — intent

## Goal
An installable, empty `ags_kit` package with lint, tests and a CI workflow, so that M1 (the P00 framework) can start writing code straight away.

## Why
- M0 is the first run through the loop (`docs/reference/process.md`, "Starting from zero").
- Every later milestone assumes there is a package to import, a test runner, a linter and a CI matrix.

## Constraints
- SPEC §12.1, environment and distribution:
  - Python ≥ 3.12 and `uv`.
  - MIT license.
  - CI on Windows, macOS and Linux × Python 3.12–3.14, running ruff and pytest.
  - The Phase 1 dependencies only.
- SPEC §12.2: `src/` layout, package `ags_kit`, and tests that mirror the package.
- SPEC §12.4: M0 is done when CI is green.
- CLAUDE.md conventions: naming, American spelling, and commits.

## Decisions taken while planning
- **Dependency floors.** Every Phase 1 dependency gets a lower bound, and a CI job tests the oldest allowed versions (`--resolution lowest-direct`). Without that job, a floor is never actually checked. SPEC §12.1 is updated in the same commit.
- **CI is checked locally for now.** There is no GitHub repo yet, so the workflow is written and validated locally, and the full matrix runs later. A TODO item tracks creating the repo and confirming that CI is green. Until then, M0's "done when" is only partly met.
- **No separate `spec.md`.** SPEC §12 is the specification for scaffolding.

## Out of scope
- Any P00 code: settings, units, registry, style, `Sheet` (M1).
- The PyPI release workflow. It moves to M5, because the package name isn't settled (TODO 0) and publishing can't be tested before then.
- Creating the GitHub repo and pushing.
- A docs site (SPEC §13 Q3) and a README rewrite.

## SPEC sections touched
§12.1 (dependency floors).
