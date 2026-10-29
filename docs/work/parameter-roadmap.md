# Parameter roadmap: derive ground parameters, wave by wave

## Intent

### Goal
Re-plan hangtu around its purpose: **deriving the ground parameters a geotechnical design needs**, from the test
data through to a model-ready parameter set, for soil and rock. Record that purpose in SPEC, replace the
version roadmap (SPEC §1.3, §12.4) with a wave-based one, and set up the documents each wave will be built from.
This unit decides the roadmap only. Each wave is then its own unit (or several) through intent → spec → plan →
build.

The parameters are the 23 reference sheets drafted outside the repo (unit weight and stress through slake
durability). Their scope:

| # | Sheet | # | Sheet |
|---|---|---|---|
| 01 | Unit weight and vertical stress | 13 | Intact rock strength |
| 02 | Index properties | 14 | Intact rock deformability |
| 03 | Specific gravity and void ratio | 15 | Hoek-Brown mi |
| 04 | Drained shear strength of soil | 16 | GSI and disturbance |
| 05 | Undrained shear strength | 17 | Rock mass strength |
| 06 | Preconsolidation and compressibility | 18 | Rock mass modulus |
| 07 | At-rest earth pressure (soil) | 19 | Post-peak (residual) rock mass |
| 08 | Elastic stiffness of soil | 20 | In situ stress in rock |
| 09 | Dilatancy | 21 | Swelling of rock |
| 10 | Small-strain stiffness | 22 | Discontinuity shear strength |
| 11 | Hardening Soil stiffness | 23 | Slake durability |
| 12 | Hydraulic conductivity | | |

### Why
- The plots, the data layer and the analyses built so far are steps toward parameters, but nothing in SPEC says
  so. The version table orders features (plots, then statistics, then consolidation) rather than the parameters
  they lead to, which makes it hard to see where the library is going or how far along any parameter is.
- Many parameters share their math or their data: the shear box groups serve soil strength and joint strength,
  the oedometer serves σ′p, Eoed, k and rock swelling, and one Hoek–Brown formula chain serves six rock sheets.
  Planning by parameter, with phases that overlap where the engines are shared, builds each engine once.
- hangtu should also be a **reference a practitioner can learn from**: for each parameter, what it is, why it
  matters to a design, and how it is determined, with the tests, equations, ranges of validity and sources.
  The docs site is where that goes, and reading the code teaches the method too.

### Constraints
- **Every parameter climbs the same four phases**, each a deliverable on its own:
  - **A. Data:** a dataset with the measured values in registry columns, and QC checks from the sheet's pitfalls.
  - **B. Direct derivation:** definitions and fits on the test results.
  - **C. Correlations:** indirect estimates through the correlations framework (SPEC §4), each with its
    applicability.
  - **D. Selection:** all sources compared against depth or geology unit, statistics and a characteristic value
    or design line, and the constitutive-model parameter set.
- **Waves group phases that share an engine.** A wave moves several parameters forward a phase each, and a
  parameter's phases can sit in different waves. Proposed waves, in order:
  0. **User-defined groups and curves.** Read user-defined AGS groups robustly, so test curves (triaxial q–ε and
     εv, rock triaxial, swelling vs time, shear box displacement) travel in the AGS file. Built against the
     sample dataset being prepared from real projects. Needed before M11's stress–strain plot (P12), wave 2's
     rock triaxial fit and wave 5.
  1. **Stress and state** (with M13): vertical stress, phase relations, the rest of the index properties
     (liquidity and consistency index, activity); SPT correlations as phase C for sheets 04–08 and 10. The
     clogging diagram (M12, P17) joins this wave: it isn't a parameter sheet, but it is drawn from the
     consistency index this wave adds.
  - **Statistics (Phase 3)** follow wave 1, before wave 0. By then there are measured properties (index, SPT,
    unit weight), derived values with depth trends (σ′v, (N1)60) and several correlations per property to
    compare, so the statistics are designed against real uses rather than in the abstract.
  2. **Strength envelopes** (with M11): one fitting core for soil strength (04, 05), joint strength (22) and the
     intact Hoek–Brown fit (15).
  3. **Oedometer:** σ′p and compressibility (06), Eoed and Eur,oed (11), k from cv·mv (12), Grob and Huder-Amberg
     swelling (21); then K0 from OCR (07) and SHANSEP (05).
  4. **Rock:** rock lab datasets (13, 14, 23) and RQD (16), then the Hoek–Brown chain (15–19), rock dilatancy
     (09) and in situ stress (20). Kept in this order, after the soil waves.
  5. **Stiffness:** soil elastic, small-strain and Hardening Soil stiffness (08, 10, 11), soil dilatancy (09).
  6. **Hydraulic:** field permeability tests (12).
  - **Selection** (phase D) builds on the statistics and applies to every sheet. AGSi export moves to "Later";
    it isn't part of phase D.
- **Order of work:** the queued real-file review items, P06, then wave 1, statistics, wave 0, wave 2 and on.
  Milestones keep their M numbers (M14, M15…), each naming its wave. Releases aren't tied to waves.
- **The output goes as far as constitutive-model parameter sets** (Mohr–Coulomb, Hardening Soil and HS-small,
  generalized Hoek–Brown with residual values, Soft Soil), **described by the published model, not by a
  software package.** Writing a set in one program's input format is a thin exporter on top, never the
  definition.
- **Judgment inputs have no package defaults.** D, GSI, σ′3max, Bjerrum's μ and the like are never filled in by
  hangtu, as N60 stays blank without an energy ratio (SPEC §4). The user can set them once for a project, as
  `hammer_efficiency` already works as a setting, and resolve in the same order as units: explicit argument →
  project setting → error that names the missing judgment. To keep that safe (proposed, to settle in the spec):
  - **Keyed by what the judgment depends on.** GSI by geology unit, D by excavation zone, σ′3max by design case,
    μ by plasticity. A single project-wide value is allowed only where the judgment really is project-wide.
  - **Visible where a reviewer looks.** Project judgments live in a plain file next to the project (reviewable
    and kept in version control), not only inside the SQLite database.
  - **Recorded on every result** with the value and where it came from (argument or project setting), so a
    result read on its own says which judgments made it.
- **Sources are verified as each wave needs them**, not all at once. A wave's spec step checks the unverified
  citations it uses and hand-calculates golden values from the verified source.
- **Public-repo rules** (CLAUDE.md): the reference sheets don't name the project they were written for, and
  carry neutral ids instead of its spec ids. Before any sheet content is published (repo or docs site), check
  that it can be: equations and citations can, but tables and figures reproduced from copyrighted books and
  papers may not. This check happens with the source verification, wave by wave.
- **Naming** follows CLAUDE.md: symbols go in labels, not names (`geological_strength_index` or an agreed short
  form, not `gsi`, unless it is added to the accepted short forms after the collision check). Each wave's spec
  step proposes its names against the whole registry.
- **The practitioner reference is the site page, and each fact is written once.** One page per parameter
  (`docs/site/parameters/NN-*.md`) gives the phenomenon, why it matters to a design, the tests, typical values,
  how the methods compare, sensitivity and pitfalls. Each method's equation, inputs, range of validity and
  source live once, in its function's docstring, and the page links to the API reference (rendered from the
  docstrings) instead of restating them. A wave's spec step promotes the sheets it covers straight to site
  pages; there is no separate internal copy, and the wave's acceptance criteria go in its `docs/work/` file.
- Everything decided so far in SPEC still holds: plain functions on DataFrames, the plot contract, units, never
  dropping data silently, flagged values distinct from blank.

### Deliverables of this unit
- **SPEC §1** gains the purpose (parameters, model sets, practitioner reference), and §1.3 and §12.4 are rewritten
  as the wave roadmap. Milestones already planned (M8's P06, M11, M12, M13) are placed in it, statistics move
  ahead of wave 0, and AGSi export moves to "Later". §1.4's non-goals are checked against it ("limit-state design
  calculations" stays out; deriving parameters is not design).
- **The sheets move into the repo** as drafts, scrubbed of the project name and spec ids, with their [V]/[U]
  tags kept: `docs/drafts/parameters/NN-*.md`, plus the template and an index. They are not decisions until a
  wave promotes them to site pages. Because promotion publishes them, the copyright check happens then, and
  tables that can't be reproduced are cited instead.
- **The template is revised** for the split above: the page keeps the overview sections, and the derivation
  blocks (§5) become the checklist each function's docstring must cover.
- **process.md and CLAUDE.md** describe waves and parameter sheets ("Where things are", the loop).
- **TODO** items for the open questions below.

### Out of scope
- Building any wave, including the user-defined group ingest (wave 0 gets its own intent).
- Verifying sources or doing the copyright check (done per wave).
- The docs site pages for parameters (each wave adds the pages for what it builds).
- Exporters to specific software formats.
- The real-file review items already queued (`file-units`, `vertical-datum`, `qc-review`) and P06, which go
  ahead as planned.
- AGSi export (moved to "Later").

### Decided direction, detail in the specs
- **Model sets are result objects** that convert to a DataFrame (`.to_frame()`, `.to_dict()`), like the planned
  statistics results. A set computes and keeps everything (values, n, the statistics behind each value,
  outliers, the judgments used); what the user asks for (characteristic values, p-values, variance, outlier
  detail) changes the view, not the calculation. So two reports of the same set never disagree.

### SPEC sections touched
§1 (purpose, new), §1.3 (roadmap), §1.4 (non-goals check), §4 (correlations widen beyond SPT; judgment inputs),
§5 (statistics feed phase D and the model sets), §12.4 (milestones), document map.

## Spec

This unit changes documents only, so this section is its feature spec: the decisions the intent left to the spec,
what each file gets, and how to check the result. The roadmap itself goes into SPEC §1.3 and §12.4; it is drafted
here in enough detail to review.

### Decisions
1. **Stages, not phases.** The four steps a parameter climbs are **stages A–D** (data, derivation, correlation,
   selection). "Phase 1/2/3" already names plots, data and statistics throughout SPEC and the data specs, and two
   meanings of "phase" in one roadmap would be misread. "Phase 1/2/3" stays as the name of those three bodies of
   work but no longer orders anything; waves and milestones do.
2. **The purpose goes at the top of SPEC §1**, as an unnumbered paragraph ahead of §1.1, so no section is
   renumbered. It says: hangtu derives the ground parameters a geotechnical design needs, from the test data to a
   model-ready parameter set, for soil and rock; the plots, data layer, analyses and statistics are steps toward
   that; and the docs site is a practitioner reference for each parameter (what, why, how, with sources).
3. **No version table.** §1.3 keeps the "why plots came first" reason and the stages and waves; the build-order
   history (the 2026-10-13, -14 and -15 paragraphs) is removed, since git keeps it. Releases are cut when a
   milestone leaves something usable and aren't planned ahead. 0.1.0 on PyPI is still next. SPEC, README,
   `docs/plots/README.md`, the plot drafts index and `docs/data/qc.md` lose their planned version targets (v0.2–v0.6)
   in favor of a milestone or "Later"; released versions (0.0.1, 0.1.0) stay.
4. **Waves in §1.3** are a short table (wave, shared engine, what it moves). The sheet × stage matrix lives once, in
   the parameter index (decision 11), not in SPEC.

   | Wave | Engine | Moves |
   |---|---|---|
   | 0 | User-defined groups and curves | Curves (triaxial q–ε and εv, rock triaxial, swelling against time, shear box displacement) carried in the AGS file; the input waves 2, 4 and 5 need |
   | 1 | Stress and state | 01 B, 03 B, 02 B (activity; LI and Ic as analyses); SPT correlations, stage C for 04–08 and 10; P17 |
   | 2 | Strength envelopes | 04 B, 05 A–B, 22 B, 15 B on one fitting core; P11–P12 |
   | 3 | Oedometer | 06 B, 11 (Eoed, Eur,oed), 12 (k from cv·mv), 21 B, then 07 B and 05 (SHANSEP); P13–P15 |
   | 4 | Rock | 13, 14, 23 A–B and 16 A (RQD), then the Hoek–Brown chain: 15 C, 16 B, 17–19, 09 (rock), 20 |
   | 5 | Stiffness | 08, 10, 11 (full set), 09 (soil); P19, P20 |
   | 6 | Hydraulic | 12 A–C (field tests) |

   LI and Ic are in the datasets already (`p.atterberg()`); wave 1 adds them as plain functions so CSV users get
   them too, as every analysis must be.
5. **Milestones in §12.4**, in build order. Done rows stay. M8's remaining P06 stays M8. New numbers start at M14.

   | M | Wave | Deliverable |
   |---|---|---|
   | M8 (rest) | — | P06 water content profile |
   | M13 | 1 | Vertical stress, (N1)60, SPT correlations |
   | M14 | 1 | Phase relations (γ, γd, e, n, S with consistency checks), activity, LI and Ic as analyses |
   | M12 | 1 | P17 clogging diagram |
   | M15 | Statistics | `describe`, `fit`, `compare`, `compare_groups`, `crosstab`; P08 (`characteristic` and P09 moved to M18) |
   | M16 | 0 | User-defined groups and curves |
   | M11 | 2 | The envelope fitting core; P11–P12; 04 B |
   | M17 | 2 | Undrained strength datasets and derivations (UU, UCS, vane, pocket penetrometer), joint strength, intact Hoek–Brown fit |
   | M18 | Selection | Stage D: sources compared against depth or geology unit, characteristic values and design lines, model-set results; the Mohr–Coulomb set first |
   | M19 | 3 | Oedometer: σ′p, Cc, Cs, Eoed, Eur,oed, k from cv·mv, Grob and Huder–Amberg swelling; P13–P15 |
   | M20 | 3 | K0 from OCR, SHANSEP; the Soft Soil set |
   | M21 | 4 | Rock lab datasets (UCS, tensile, point load, slake durability, intact moduli) and RQD |
   | M22 | 4 | The Hoek–Brown chain, rock dilatancy, in situ stress; the generalized Hoek–Brown set with residual values |
   | M23 | 5 | Soil stiffness (elastic, small-strain, Hardening Soil), soil dilatancy; P19, P20; the HS and HS-small sets |
   | M24 | 6 | Field permeability tests |

   A milestone can still split into several units of work, as M8 did. The real-file review items (`file-units`,
   `vertical-datum`, `qc-review`) are units without a milestone and go ahead of M8's P06.
6. **Selection gets its own milestone after wave 2** (M18). By then there are measured strengths, SPT-based
   estimates of the same properties and the statistics, which is what selection compares; a Mohr–Coulomb set is the
   first one all its inputs exist for. Each later wave then adds stage D for its sheets and the model sets they
   complete (Soft Soil in M20, Hoek–Brown in M22, HS and HS-small in M23).
7. **Not on a wave**, kept in a "Not yet placed" list in §1.3 and built when needed: P18 (Hollmann & Thewes), QC
   level 2, the standards comparison library, user-defined PSD regions and the plasticity-chart data region, P16
   (compaction). The existing "Later" list stays, with AGSi export (and import) in it.
8. **Judgment inputs** (§4, new bullet; was "proposed" in the intent):
   - **No package defaults.** A judgment (D, GSI, σ′3max, Bjerrum's μ, a design unit weight profile, a groundwater
     level) is never filled in by hangtu.
   - **Resolution:** explicit argument → the project's judgments file → an error that names the judgment, what it
     is keyed by and how to set it. There is no session (`ht.settings`) level: a judgment belongs to a project, and
     a session value would follow the user from one project to the next.
   - **Keyed by what it depends on.** Each judgment declares its keys (geology unit, hole, depth range, a named
     design case) and whether one project-wide value is allowed. A value given at a coarser key than allowed is an
     error, not a fallback.
   - **A plain file next to the project** (`judgments.yaml`), the source of truth, reviewable and kept in version
     control. A `Project` records its path and reads it on each call; it is never copied into SQLite, so the two
     can't disagree. It works without a `Project` too, for CSV users.
   - **Recorded on every result:** each judgment used, with its value, key and source (the argument, or the file's
     path and SHA-256), in `df.attrs` and on result objects, so a result read on its own says which judgments made
     it.
   - **When:** the file format and API are specified in M13's spec, because the unit weight profile and the
     groundwater level of `vertical_stress()` are the first judgments a user wants to set once per project. The
     call arguments decided in analysis draft §4.1 stay, as the first step of the resolution.
   - `hammer_efficiency` is unchanged for now (a session setting; an energy ratio is equipment data more than
     judgment). Whether it moves into the file, keyed by hole or rig, is a TODO.
9. **Correlations widen beyond SPT** (§4): the framework's rules apply to any input property (PI, CPT qt, Is50,
   index properties), not only N. SPT correlations are the first set (M13). The input-N rule becomes "the input is
   explicit": each correlation declares the quantity and variant it was derived with.
10. **Model sets and results** (§5, new bullets): statistics results and model sets are the same kind of object.
    A result computes and keeps everything (values, n, the statistics behind each value, outliers, the judgments
    used); what the user asks for (characteristic values, p-values, variance, outlier detail) changes the view
    (`.to_frame()`, `.to_dict()`, the summary), never the calculation, so two reports of one result can't disagree.
    A model set is described by the published model (Mohr–Coulomb; Hardening Soil, Schanz et al. 1999; HS-small,
    Benz 2007; generalized Hoek–Brown, Hoek et al. 2002; Soft Soil, Vermeer & Neher 1999; to confirm, TODO);
    exporters to a program's input format are thin and come later.
11. **The parameter index is the tracker.** `docs/drafts/parameters/README.md` lists the 23 sheets with, for each
    stage, its wave and status (planned, built), like the plot list in `docs/plots/README.md`. Each wave's
    close-out updates it. It answers "how far along is each parameter".
12. **Non-goals** (§1.4, title loses "through v0.3"): "limit-state design calculations" stays out, worded so the
    line is clear: hangtu stops at characteristic values, design lines and model parameter sets; applying partial
    factors, capacity and stability checks, and running numerical models are out. Added: a program's input format as
    the definition of a model set (exporters only). The rest is unchanged.
13. **Moving the sheets in** (`docs/drafts/parameters/NN-*.md`, file names as in the source):
    - **Scrub:** the "Spec ids" row and README column go; the sheet number is the id. "spec S6 primary" and the like
      are dropped: which method is primary is decided in the wave's spec. A reference to a private extract of a
      source, with its path, becomes "via an extract of the source", keeping the [V] and locator. No project, client or private
      path is named anywhere.
    - **Kept as is:** the [V]/[U] tags and locators, the _[Judgment — for review]_ tags, the section structure
      (the sheets aren't restructured to the new template until they're promoted).
    - **American spelling** in prose (behavior, remolded, mobilized, program, center, analyzed, tunneling, …);
      reference titles keep the source's spelling.
    - **Copyright screen before the drafts commit.** The repo is public, so committing a draft publishes it. Values
      with a citation are kept; a source table or chart reproduced nearly whole (for example a full table of mi by
      rock type, the descriptors of the GSI chart, digitized curves) is cut to the values the sheet needs with the
      table's locator, or to the locator alone. The build commit lists what was cut, per sheet. The full check
      (TODO) still happens per wave, before promotion to the site.
14. **The template** (`docs/drafts/parameters/TEMPLATE.md`) becomes the site page's outline plus the docstring
    checklist:
    - **Page:** header table (parameters, material, models that use it, depends on, feeds); phenomenon; why it
      matters to a design (by analysis type, not one project's); units; typical values; tests (ASTM, ISO/BS, AGS
      groups and headings); methods (one row per method: what it uses, when it applies, a link to its function in
      the API reference); how the methods compare; sensitivity and variability; pitfalls (each noted as a QC rule,
      a warning or a docstring note once built); references.
    - **Docstring checklist**, replacing the sheets' §5 blocks: equation; inputs with units; valid for (material and
      the range of data behind it); scatter; assumptions; out-of-range behavior (NaN with a count); judgments taken;
      source with its locator, verified. The equation and its source are written once, in the docstring.
15. **Site pages** go in `docs/site/parameters/NN-*.md`, with a "Parameters" nav section, when a wave promotes a
    sheet. None are added in this unit.

### Changes by file
- **`SPEC.md`:** document map (`docs/drafts/parameters/`; the site's parameter pages); §1 purpose (decision 2);
  §1.2 AGSi row "Later"; §1.3 rewritten (decisions 3, 4, 7); §1.4 (decision 12); §3 plot-list bullets without
  versions; §4 correlations widened (decision 9) and judgment inputs (decision 8); §5 heading without "v0.3", the
  stage D and model-set bullets (decision 10); §11 headings without versions; §12.4 (decision 5).
- **`docs/drafts/parameters/`:** the 23 sheets, `TEMPLATE.md` (decision 14), `README.md` (index and tracker,
  decision 11, with the [V]/[U] conventions from the source README).
- **`docs/reference/process.md`:** stages and waves; a wave's spec step verifies the [U] citations it uses, does the
  copyright check, proposes names against the registry, and promotes its sheets to site pages; its close-out
  updates the parameter index. "Starting from zero" step 3 points to the wave milestones.
- **`CLAUDE.md`:** status paragraph (no v0.2; the order of work); "Where things are" gains the parameter drafts and
  site pages; a workflow rule for a wave's spec step (sources, copyright, promotion).
- **`docs/TODO.md`:** new items:
  - **#29 Judgment keys** (You): the key and the project-wide rule for each judgment (proposed: GSI by geology
    unit, D by design case, σ′3max by design case, μ from PI), confirmed when its wave starts.
  - **#30 What can be published** (You + Claude): which sheet content can be reproduced (cited values, tables,
    digitized charts, figure descriptors), settled before the first promotion.
  - **#31 Curves in real files** (You): the user-defined groups and headings real files use for curves and rock
    triaxial, gathered from the sample dataset; input for wave 0's intent.
  - **#32 Published definitions of the model sets** (Claude, verify): a non-vendor source defining each model set's
    parameters (decision 10).
  - **#33 Energy ratio as a judgment** (You): whether `hammer_efficiency` moves into the judgments file, keyed by
    hole or rig.
- **`README.md`:** the roadmap table becomes the purpose and the waves, without version numbers.
- **`docs/plots/README.md`, `docs/plots/drafts/README.md`, `docs/data/qc.md`:** version targets become milestones
  or "Later".

### Acceptance criteria
1. **Scrubbed:** a search for the source project's and codebase's names, "spec ids" and `spec [SR][0-9]` finds
   nothing outside this work doc, and no private path appears in `docs/drafts/parameters/`.
2. **Tags kept:** each sheet's [V] and [U] counts match the source, except where the copyright screen cut content,
   which the commit body lists.
3. **Roadmap:** SPEC §1.3 has the stages, the wave table and the "Not yet placed" list and no version table;
   §12.4's rows are in build order and each new row names its wave; v0.2–v0.6 appear nowhere in SPEC, README,
   CLAUDE.md or the plot docs, except as history in `docs/work/`.
4. **Placed:** every item of the old v0.2–v0.6 rows and "Later" is in a milestone, "Not yet placed" or "Later".
5. **Size:** SPEC.md stays under 450 lines.
6. **Links:** every relative link in the changed and new files resolves.
7. **CI:** `uv run ruff check . && uv run ruff format --check . && uv run pytest` passes, and
   `zensical build --clean --strict` passes (nothing under `docs/drafts/` is published).

## Plan

Documents only, so "green" for each commit means ruff and pytest pass, `zensical build --clean --strict` passes,
and the relative links in the files the commit touches resolve (checked with a scratch script, not committed).
The sheets are content moved in, so the 300-line guide is applied to what a reviewer reads: the scrub and the
screen, listed in each commit body.

### 1. `parameter-roadmap: soil parameter sheets as drafts`
- `docs/drafts/parameters/01-*.md` … `12-*.md`, copied from the sheets outside the repo, then:
  - scrub (Decision 13): the "Spec ids" row, "spec S# primary" labels, local-extract paths, any project name;
  - American spelling in prose, reference titles as published;
  - copyright screen: cited values and references kept; a source table or chart reproduced nearly whole is cut to
    the values the sheet needs plus its locator, or to the locator alone.
- Links between sheets point to sheets that land in commit 2 (13–23); the check for this commit allows those.
- Commit body: what the screen cut, per sheet, and the [V]/[U] counts that changed because of it (AC 1, 2).

### 2. `parameter-roadmap: rock parameter sheets as drafts`
- `docs/drafts/parameters/13-*.md` … `23-*.md`, the same treatment. Sheets 15 (mi by rock type) and 16 (GSI chart,
  RQD and JCond89 ratings) are the most likely to carry whole tables.
- Commit body as in step 1. After this commit every cross-sheet link resolves (AC 6).

### 3. `parameter-roadmap: parameter index and template`
- `docs/drafts/parameters/README.md`: status line (drafts, not decisions; promoted per wave), the [V]/[U] and
  judgment-tag conventions, and the index and tracker (Decision 11): one row per sheet with its parameters and, for
  stages A–D, the wave and status. Built so far is shown as built (the SPT dataset and N60 for 04–08's stage A
  inputs, the Atterberg and index datasets for 02 A–B, `p.permeability()` for 12 A).
- `docs/drafts/parameters/TEMPLATE.md` (Decision 14): the page outline and the docstring checklist.

### 4. `spec: the parameter roadmap`
- `SPEC.md`: every change in "Changes by file" (Decisions 2–10, 12), in one commit since they are one decision.
  §13 and the section numbers are unchanged. Check the size (AC 5) and that every item of the old version rows and
  "Later" is placed (AC 4), listing where each went in the commit body.

### 5. `docs: version targets become milestones`
- `README.md` roadmap: the purpose and the waves, no version numbers.
- `docs/plots/README.md`, `docs/plots/drafts/README.md`, `docs/data/qc.md`: version targets become milestones or
  "Later" (AC 3).
- The plot specs, the plot drafts and `docs/plots/TEMPLATE.md` too (found while building): their "Target version"
  field becomes "Milestone".

### 6. `parameter-roadmap: close out`
- `docs/reference/process.md`: stages and waves, a wave's spec-step duties, the close-out updating the index.
- `CLAUDE.md`: status paragraph (order of work, no v0.2), "Where things are", the wave spec-step rule.
- `docs/TODO.md`: #29–#33 (numbered #28–#32 on the branch; `main` had taken #28 meanwhile).
- Final checks: AC 1 (`git grep`), AC 3 (`git grep -E 'v0\.[2-6]'` outside `docs/work/`), AC 6 over all changed
  files, AC 7 (CI commands and the strict site build).
