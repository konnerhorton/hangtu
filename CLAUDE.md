# ags-kit

Python library of plots, analyses and (later) AGS4 ingest/QC for geotechnical engineers. M0 (scaffolding) done; M1 (P00 framework) is next.

## Where things are
- `SPEC.md`: product spec and cross-cutting decisions. Read the relevant section before designing anything.
- `docs/plots/PXX-*.md`: one spec per figure, with acceptance criteria. `docs/plots/README.md` has the shared plot conventions.
- `docs/work/<id>-<slug>/`: intent and plan for each unit of work (see `docs/reference/process.md`).
- `docs/drafts/`: the draft column registry and unit aliases (ship at M1), the analyses draft spec (`analysis.md`, M3–M4) and notes for later phases. Items marked "decided" are decided; the rest is not. Finish the relevant draft as the feature spec before building from it.
- `TODO.md`: research items and pending decisions, referenced as "TODO #n".

## Commands
- `uv sync`: install
- `uv run pytest`: tests (warnings are errors; assert expected ones with `pytest.warns`)
- `uv run ruff check . && uv run ruff format .`: lint and format
- `uv run ruff check . && uv run ruff format --check . && uv run pytest`: what CI runs (`.github/workflows/ci.yml`)
- Oldest allowed dependency versions: `UV_RESOLUTION=lowest-direct UV_PROJECT_ENVIRONMENT=<scratch dir> uv run pytest`, then `git checkout uv.lock`, because it rewrites the lock

## Conventions
- **Users are engineers, not developers.** Every analysis is a plain function on a DataFrame. Keep objects thin.
- **Plot contract:** `ak.plot.<name>(df, *, ..., ax=None, display_units=None) -> (fig, ax)`. Apply styling in a context manager and never change global matplotlib state.
- **Column names come from the registry** (`columns.yaml`, SPEC §10.3). Don't invent column names in a function.
- **Units:** resolve them in the order explicit argument → `df.attrs["units"]` → registry/settings → error (analysis) or "(units unknown)" (plot). Never guess a unit (SPEC §2.6).
- **Never drop data silently.** Draw out-of-range values at the edge with a count, and keep flagged values (NP, refusal, `<x`) distinct from blank.
- **Error messages** say what is wrong, where, and what to do. Don't show raw tracebacks for anticipated data problems.
- Use American spelling everywhere: prose, docs, comments and identifiers (color, behavior, recognize, analyze, gray, judgment).

## Naming
Explicit is better than implicit. Names are written out in full, or full enough that they can't be misread:
- **Column, preset, argument and function names never use bare symbols or abbreviations** that could mean two things. `undrained_shear_strength`, not `su` or `cu`; `uniformity_coefficient`, not `cu`; `hydraulic_conductivity`, not `k`; `liquid_limit`, not `ll`; `geology_unit`, not `unit`.
- **Prefix test-specific quantities with the test**: `spt_n`, `spt_n60`, `spt_refusal`.
- **Symbols belong in labels**, not names: the registry `label` says "Undrained shear strength, s_u".
- **Units never appear in names** (`particle_size`, not `size_mm`). Units live in `df.attrs["units"]`.
- **Accepted short forms** are notation that is unambiguous in geotechnical work (`d10`, `d30`, `d60`) and AGS identifiers (`loca_id`). Add a short form to this list only after checking it can't collide with another quantity.
- New names are checked against the whole registry before they are added.

## Git and commits
- **Each unit of work gets its own branch** off `main`, named after it (`m0-scaffolding`, `p01-property-profile`). It is merged into `main` after review.
- **Each loop step gets its own commit:** intent, spec, plan, then the build. The close-out updates (statuses, SPEC, TODO) go in the last build commit.
- **During a build, commit at each green, coherent point.** Usually that's one plan step, with ruff and pytest passing. Use judgment: a commit is one idea a reviewer can follow in a single read. If a step goes past roughly 300 changed lines (not counting test data), split it.
- **Don't mix kinds of change.** A refactor or rename gets its own commit, separate from new behavior.
- **Never commit failing tests or lint errors.** Work in progress waits in the working tree.
- **Message:** `<scope>: <imperative summary>`, at most 72 characters. The scope is the work item (`M0`, `P01`) or an area (`spec`, `docs`, `registry`, `units`). The body says *why* and names any SPEC section or TODO item a decision touched. No attribution lines.
  Example: `P01: count values beyond axis limits in the footnote`
- **Approval:** Claude commits intermediate build steps of an approved plan without asking. Everything else needs the user's approval first: intent, spec and plan commits, docs-only commits, branch creation and merges, pushes, and anything that rewrites history. For a commit, show the message and wait.

## Workflow rules
- If a change alters a decision recorded in `SPEC.md` or a plot spec, update that file **in the same commit**.
- Don't renumber `SPEC.md` sections. `TODO.md` and the plot specs refer to them by number.
- Test against the acceptance criteria in the feature's spec, and hand-calculate golden values for analyses.
- Don't add dependencies beyond those in SPEC §12.1 without asking.
