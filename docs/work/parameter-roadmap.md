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
