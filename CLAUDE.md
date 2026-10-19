# hangtu

Python library of plots, analyses and AGS4 ingest/QC for geotechnical engineers. M0 (scaffolding), M1 (P00 framework), M2 (P01 property profile), M2b (P07 property by geology unit) and M3 (SPT analysis, P02 SPT profile, P03 SPT class histogram) done, and the package renamed from ags-kit to hangtu. Phase 2 comes next, ahead of the remaining plots (SPEC §1.3): M4 decided the data model (AGS 4.2-shaped tables, SPEC §7), M5 (AGS4 ingest into SQLite, `ht.Project`) and M6 (QC level 1: `p.qc()`, the report and `p.diff()`) M7 (depth, elevation and geology joins, datasets: `p.spt()`, `p.atterberg()`, `p.grain_size()`, `p.permeability()`) and M9 (examples, `ht.examples`, templates that follow the datasets, README; version 0.1.0) are done. Releasing 0.1.0 to PyPI comes next, then v0.2 (SPEC §1.3, §12.4): P04–P06 (M8), triaxial P11–P12 (M11), clogging P17 (M12) and SPT correlations with (N1)60 (M13). In M8, the analyses (`ht.analysis.plasticity()`, `gradation()`, `uscs()`, `aashto()`) P04 (`ht.plot.plasticity_chart()`), P05 (`ht.plot.grain_size()`) and text values in P01's value column (TODO #15) are done ([`docs/work/m8-index-plots.md`](docs/work/m8-index-plots.md)), and the index datasets (`p.grain_size_summary()`, `p.index_properties()`, branch `m8-text-values`) are next.

## Where things are
- `SPEC.md`: product spec and cross-cutting decisions. Read the relevant section before designing anything.
- `docs/data/`: data-layer specs that outlive a unit of work (`ingest.md`, M5; `qc.md`, M6; `datasets.md`, M7).
- `docs/plots/PXX-*.md`: one spec per figure, with acceptance criteria. `docs/plots/README.md` has the shared plot conventions.
- `docs/plots/drafts/`: draft notes for plots not yet specified, in the TEMPLATE format, including proposed IDs P24–P30. They are not decisions. When a plot's unit of work starts, promote its draft to `docs/plots/PXX-*.md` in the spec step.
- `docs/work/<id>.md`: intent, plan and (when there is no other feature spec) spec for each unit of work, as `## Intent`, `## Spec` and `## Plan` sections (see `docs/reference/process.md`). `docs/work/` files for merged units are history. Read one only when the task or a spec points to it.
- `src/hangtu/columns.yaml` and `src/hangtu/units/aliases.yaml`: the column registry and unit aliases.
- `docs/drafts/`: the analyses draft spec (`analysis.md`, M3 and M8) and notes for later phases. Items marked "decided" are decided; the rest is not. Finish the relevant draft as the feature spec before building from it.
- `docs/TODO.md`: research items and pending decisions, referenced as "TODO #n".

## Commands
- `uv sync`: install
- `uv run pytest`: tests (warnings are errors; assert expected ones with `pytest.warns`)
- `uv run ruff check . && uv run ruff format .`: lint and format
- `uv run ruff check . && uv run ruff format --check . && uv run pytest`: what CI runs (`.github/workflows/ci.yml`)
- Oldest allowed dependency versions: `UV_RESOLUTION=lowest-direct UV_PROJECT_ENVIRONMENT=<scratch dir> uv run pytest`, then `git checkout uv.lock`, because it rewrites the lock

## Conventions
- **Users are engineers, not developers.** Every analysis is a plain function on a DataFrame. Keep objects thin.
- **Plot contract:** `ht.plot.<name>(df, *, ..., ax=None, display_units=None) -> (fig, ax)`. Apply styling in a context manager and never change global matplotlib state.
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
- **Accepted short forms** are notation that is unambiguous in geotechnical work (`d10`, `d30`, `d60`, and `d<x>` generally), AGS identifiers (`loca_id`), and the names of classification standards (`uscs`, `aashto`, `bs5930`). Add a short form to this list only after checking it can't collide with another quantity.
- New names are checked against the whole registry before they are added.

## Git and commits
- **Each unit of work gets its own branch** off `main`, named after it (`m0-scaffolding`, `p01-property-profile`). It is merged into `main` after review with `git merge --no-ff`, so each unit is one merge commit: `git log --first-parent main` lists the units, and `git revert -m 1 <merge>` undoes one whole.
- **Each loop step gets its own commit:** intent, spec, plan, then the build. The close-out updates (statuses, SPEC, TODO) go in the last build commit.
- **During a build, commit at each green, coherent point.** Usually that's one plan step, with ruff and pytest passing. Use judgment: a commit is one idea a reviewer can follow in a single read. If a step goes past roughly 300 changed lines (not counting test data), split it.
- **Don't mix kinds of change.** A refactor or rename gets its own commit, separate from new behavior.
- **Never commit failing tests or lint errors.** Work in progress waits in the working tree.
- **Stage files by name** (`git add <path> ...`), never with `git add -A`, `git add .` or `git commit -a`. The working tree can hold local files that aren't ignored, and a broad add sweeps them into a public commit.
- **Message:** `<scope>: <imperative summary>`, at most 72 characters. The scope is the work item (`M0`, `P01`) or an area (`spec`, `docs`, `registry`, `units`). The body says *why* and names any SPEC section or TODO item a decision touched. No attribution lines.
  Example: `P01: count values beyond axis limits in the footnote`
- **Approval:** Claude commits intermediate build steps of an approved plan without asking. Everything else needs the user's approval first: intent, spec and plan commits, docs-only commits, branch creation and merges, pushes, and anything that rewrites history. For a commit, show the message and wait.

## Workflow rules
- If a change alters a decision recorded in `SPEC.md` or a plot spec, update that file **in the same commit**.
- Don't renumber `SPEC.md` sections. `docs/TODO.md` and the plot specs refer to them by number.
- Test against the acceptance criteria in the feature's spec, and hand-calculate golden values for analyses.
- **Visual check:** at the end of each plot unit of work, save a PNG of the plot's output (100 dpi, realistic data, both US and SI when units matter) as `docs/plots/img/PXX.png` (or `PXX-si.png` and `PXX-us.png` when US and SI need separate figures), look at it, and commit it in the close-out so a reviewer sees the figure without running code. Plot specs and later docs may reuse these images.
- Don't add dependencies beyond those in SPEC §12.1 without asking.
- **The repo is public.** Don't name private sources, contacts or their companies in docs, TODOs, code or commit messages. Describe the idea, not who said it ("AGS is often criticized as a storage model"); the user keeps the source in their own notes.
