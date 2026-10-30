# hangtu

Python library that derives the ground parameters a geotechnical design needs, from AGS4 or CSV test data through to model parameter sets, for soil and rock, with plots, analyses, AGS4 ingest/QC and statistics along the way (SPEC §1). The roadmap is organized as stages A–D per parameter and waves 0–6 (SPEC §1.3, §12.4; [`docs/work/parameter-roadmap.md`](docs/work/parameter-roadmap.md)). Done: M0–M9 (the plot framework, P01–P07, SPT analysis, AGS4 ingest into SQLite with `ht.Project`, QC level 1, the joins and datasets, examples, the index analyses and datasets; version 0.1.0; M8 in [`docs/work/m8-index-plots.md`](docs/work/m8-index-plots.md)) and the real-file review items: `spt-report`, `file-units`, `vertical-datum` and `qc-review` (accepted findings, `p.qc(accepted=...)`, D008; each in `docs/work/`), and M13 unit (a): the judgments file, `p.stratigraphy()` and `ht.analysis.vertical_stress()` ([`docs/work/m13a-judgments.md`](docs/work/m13a-judgments.md); sheet 01 is the first page in `docs/site/parameters/`), and M13 unit (b1): `ht.analysis.spt_n1_60()`, hammer efficiency by hole, and `ht.analysis.correlations` with the first φ′ correlations ([`docs/work/m13b1-spt-framework.md`](docs/work/m13b1-spt-framework.md); page 04), and M13 unit (b2): the SPT correlations for s_u, σ′p, OCR and K0, bands as `<target>_lower`/`_upper` drawn by P01, the opt-in USCS map, the chaining warning, and PI by geology unit with `ht.analysis.add_judgment()` ([`docs/work/m13b2-spt-strength-history.md`](docs/work/m13b2-spt-strength-history.md); pages 05–07), and M13 unit (b3): drained E and Vs from SPT, a coefficient by the source's soil row (`soil=`), the `modulus` and `velocity` kinds ([`docs/work/m13b3-spt-stiffness.md`](docs/work/m13b3-spt-stiffness.md); pages 08 and 10), which closes M13, and the plot layout defaults: the legend inside a clear corner (`legend=`), correlations named by citation, and whole-figure sizes with a `chart` kind ([`docs/work/p00-layout-defaults.md`](docs/work/p00-layout-defaults.md)), and M14 unit (a): `p.density()` (lab and field unit weights, each with its specimen's own water content and its sample's particle density) and `p.particle_density()`, QC B001–B004, and test files with UNIT, TYPE and ABBR after the data groups ([`docs/work/m14a-density-data.md`](docs/work/m14a-density-data.md)), and M14 unit (b): `ht.analysis.phase_relations()` with the `specific_gravity` judgment, `ht.analysis.clay_activity()` and activity in `p.index_properties()` ([`docs/work/m14b-phase-relations.md`](docs/work/m14b-phase-relations.md); pages 02 and 03), which closes M14, and M12: `ht.analysis.clogging_potential()` and the P17 clogging diagram (Thewes & Burger 2004; [`docs/work/m12-clogging-diagram.md`](docs/work/m12-clogging-diagram.md)), which closes wave 1, and M15 unit (a): `ht.stats.describe()` and its result object, the input rules every statistics function follows (flags and sources marked in the registry, `pool=`), and P01 and P07 summarizing through it ([`docs/work/m15a-describe.md`](docs/work/m15a-describe.md); the statistics guide), and M15 unit (b): each correlation's estimates carry its source's n, r², scatter and advice on the rows, a standard deviation in the target's units once its scale is verified (TODO #47), and other databases' checks in the entry's `evaluations` ([`docs/work/m15b-correlation-statistics.md`](docs/work/m15b-correlation-statistics.md)). 0.1.0 is on PyPI. Next, in order: the rest of statistics (M15 (c) `fit()` and P08, (d) `compare()`), wave 0 (M16 user-defined groups and curves), wave 2 (M11 triaxial P11–P12, M17), selection (M18) and waves 3–6. The docs site (Zensical, `docs/site/`, [`docs/work/docs-site.md`](docs/work/docs-site.md)) is built and follows `main`.

## Where things are
- `SPEC.md`: product spec and cross-cutting decisions. Read the relevant section before designing anything.
- `docs/data/`: data-layer specs that outlive a unit of work (`ingest.md`, M5; `qc.md`, M6; `datasets.md`, M7).
- `docs/plots/PXX-*.md`: one spec per figure, with acceptance criteria. `docs/plots/README.md` has the shared plot conventions.
- `docs/drafts/parameters/`: one draft reference sheet per ground parameter (tests, methods, sources with [V]/[U] tags), the page template with the docstring checklist, and the index (`README.md`) that tracks each parameter's stages A–D. Sheets are not decisions until a wave promotes them to `docs/site/parameters/`.
- `docs/plots/drafts/`: draft notes for plots not yet specified, in the TEMPLATE format, including proposed IDs P24–P30. They are not decisions. When a plot's unit of work starts, promote its draft to `docs/plots/PXX-*.md` in the spec step.
- `docs/work/<id>.md`: intent, plan and (when there is no other feature spec) spec for each unit of work, as `## Intent`, `## Spec` and `## Plan` sections (see `docs/reference/process.md`). `docs/work/` files for merged units are history. Read one only when the task or a spec points to it.
- `src/hangtu/columns.yaml` and `src/hangtu/units/aliases.yaml`: the column registry and unit aliases.
- `docs/drafts/`: the analyses draft spec (`analysis.md`, M3 and M8) and notes for later phases. Items marked "decided" are decided; the rest is not. Finish the relevant draft as the feature spec before building from it.
- `docs/TODO.md`: research items and pending decisions, referenced as "TODO #n".
- `docs/site/`: the public docs site (Zensical; config in `zensical.toml`). Each page's example is a file in `docs/site/examples/`; `docs/prepare_site.py` runs them and writes the generated files. The rest of `docs/` is internal and not published.

## Commands
- `uv sync`: install
- `uv run pytest -n auto --dist loadfile`: the whole suite in parallel, about 1.5 minutes (warnings are errors; assert expected ones with `pytest.warns`)
- `uv run pytest <files>`: only the tests a change touches; add `--lf` to rerun only the last failures
- `uv run ruff check . && uv run ruff format .`: lint and format
- `uv run ruff check . && uv run ruff format --check . && uv run pytest -n auto --dist loadfile`: what CI runs (`.github/workflows/ci.yml`)
- `uv sync --group docs && uv run python docs/prepare_site.py && uv run zensical serve`: the docs site locally (`zensical build --clean --strict` is what CI runs)
- Oldest allowed dependency versions: `UV_RESOLUTION=lowest-direct UV_PROJECT_ENVIRONMENT=<scratch dir> uv run pytest`, then `git checkout uv.lock`, because it rewrites the lock (commit an intended lock change first, or the checkout discards it)

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
- **Accepted short forms** are notation that is unambiguous in geotechnical work (`d10`, `d30`, `d60`, and `d<x>` generally), AGS identifiers (`loca_id`), the names of classification standards (`uscs`, `aashto`, `bs5930`), `r_squared` for the coefficient of determination, and `aicc` for the corrected Akaike information criterion (AICc). Add a short form to this list only after checking it can't collide with another quantity.
- New names are checked against the whole registry before they are added.

## Git and commits
- **Each unit of work gets its own branch** off `main`, named after it (`m0-scaffolding`, `p01-property-profile`). It is merged into `main` after review with `git merge --no-ff`, so each unit is one merge commit: `git log --first-parent main` lists the units, and `git revert -m 1 <merge>` undoes one whole.
- **Each loop step gets its own commit:** intent, spec, plan, then the build. The close-out updates (statuses, SPEC, TODO) go in the last build commit.
- **During a build, commit at each green, coherent point.** Usually that's one plan step, with ruff and pytest passing. While working on a step, run the tests it touches; run the whole suite in parallel once, before the commit. Use judgment: a commit is one idea a reviewer can follow in a single read. If a step goes past roughly 300 changed lines (not counting test data), split it.
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
- **Docs site:** a plot's close-out adds its page (`docs/site/plots/`, with an example in `docs/site/examples/`, linked in the `nav` in `zensical.toml`) and its entry in `docs/site/reference/plot.md`. New public functions get a reference entry; a test fails without one. Docstrings are published in the API reference.
- **Waves:** a wave's spec step promotes its parameter sheets to site pages, verifies the [U] citations it uses, checks what can be published (values and citations, not whole tables or charts), and proposes names against the registry; its close-out updates the parameter index (`docs/reference/process.md`, "Stages and waves").
- **Judgments have no defaults:** a judgment input resolves explicit argument → the project's judgments file → an error naming it (SPEC §4).
- Don't add dependencies beyond those in SPEC §12.1 without asking.
- **The repo is public.** Don't name private sources, contacts or their companies in docs, TODOs, code or commit messages. Describe the idea, not who said it ("AGS is often criticized as a storage model"); the user keeps the source in their own notes.
