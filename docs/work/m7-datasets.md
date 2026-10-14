# M7: Depth, elevation and geology joins, and datasets

## Intent

### Goal
Turn a project's canonical tables into the DataFrames the Phase 1 plots take: `p.spt()`, `p.atterberg()`, `p.grain_size()` and `p.permeability()` return one row per test (or per curve point), with registry column names, `df.attrs["units"]` attached, and each test's depth, elevation and geology unit joined on by the SPEC §8 conventions. `p.locations` gives one row per hole, and `p.set_geology_map(path)` maps the file's geology codes to the units an engineer reports on.

### Why
- It's the last Phase 2 unit before M8 (SPEC §1.3, §12.4 M7). Until now ingest and QC store and check the data, but an engineer can't get from an AGS file to a plot without writing SQL.
- The SPEC §11 sketch, `ht.plot.spt_profile(p.spt(geology=["Alluvium"]))`, is what v0.2 promises.
- Depth, elevation and geology joins are where results most easily go wrong without anyone noticing (a test put in the wrong unit at a boundary, an SPT at its top depth instead of its mid-drive depth), so they belong in one tested place rather than in each user's script.

### Constraints
- SPEC §8 (decided): `elevation = ground_level − depth`; test depth by data type with a `depth_basis` column; geology key configurable (default `GEOL_GEOL`), mapping file matched exactly and case-sensitively; interval rule `top ≤ d < base`, the last interval includes its base, the lowest top wins on overlaps.
- SPEC §10.2: datasets return exactly the shape the Phase 1 plots expect; common filters named `where=`, `contains=`, `elevation=`, `depth=`, `holes=`, `geology=`, `geology_fields=`, `include_incomplete=`, `display_units=`.
- SPEC §7: datasets read the canonical layer through `db.py` and join on surrogate keys; values hangtu calculates (N60, mid-drive depth, elevation) are computed, not stored; value flags become columns (`spt_refusal`, `non_plastic`, `qualifier`).
- SPEC §2.6 and CLAUDE.md: column names come from the registry, and new ones are checked against all of it; units travel in `df.attrs["units"]`.
- Never drop data silently: records left out (incomplete, outside any geology interval, unmapped code) are counted and said, not lost.
- Inputs: the dataset column lists in `docs/drafts/phase2-data.md`; M6's handoff (`qc/_data.py` for record depths, C001 as the incomplete set, G004 deferred here); TODO #17 (particle size in inches).
- No new dependency. Test files are the existing synthetic ones, extended where a case is missing.
- **Done when:** each dataset feeds its Phase 1 plot unchanged (P02 and P03 from `p.spt()`, P01 and P07 from the others), the SI and US twin files give the same datasets, and the spec's acceptance criteria pass, with hand-calculated mid-drive depths and boundary cases.

### Decisions (proposed, to settle in review)
1. **Where the spec lives:** `docs/data/datasets.md`, a topic doc next to `ingest.md` and `qc.md`. The dataset section of `docs/drafts/phase2-data.md` moves there.
2. **Datasets in this unit:** `p.spt()`, `p.atterberg()`, `p.grain_size()` (long curves) and `p.permeability()`, with the values the file gives and the analyses that already exist (`ht.analysis.spt()` for refusal, N60 and capped N).
   - **Deferred to M8**, because they need the classification and gradation analyses M8 builds: the classification columns (`plasticity_class_*`, `gradation_uscs`, `uscs_symbol`, AASHTO), `p.grain_size_summary()` and `p.index_properties()`, and with it SPEC §13 #2 (specimen combining).
   - `liquidity_index` and `consistency_index` are simple formulas and could come now; proposed: now.
3. **Settle SPEC §13 #1** (SPT mid-drive fallback when the increments are missing) in the spec step, since this unit is the first to use it.
4. **Geology:** `p.set_geology_map(path)` stores the mapping in `meta_geology_map`; codes the map doesn't cover are QC `G004` (deferred from M6), and in the datasets keep their code as `geology_unit` with a warning naming them, rather than being dropped. `geology_fields=` carries more GEOL headings side by side.
5. **Incomplete records** (QC C001, from `qc/min_fields.yaml`) are left out by default and counted in a warning; `include_incomplete=True` keeps them.
6. **TODO #17:** `GRAT_SIZE` gets the `particle_size` kind at ingest, so US output keeps sieve sizes in mm. This touches ingest and needs a re-ingest (schema version bump).
7. **Test files:** reuse `site_si.ags`, `site_us.ags` and `site_v404.ags`; add cases for depth boundaries, missing SPT increments, overlapping geology and unmapped codes, in the existing generator script.

### Out of scope
- The M8 items in decision 2.
- `p.settings.to_yaml()`/`load_yaml()` and storing QC overrides with the project (`docs/data/ingest.md`, `qc.md`): useful, but independent of the datasets. Proposed as a small unit of its own after M7.
- Datasets beyond the four (undrained strength across test types, consolidation, triaxial): later, as their plots arrive.
- Inclined holes (flagged by QC L004, SPEC §1.4); more than one file per project; AGSi.
- Changes to the Phase 1 plots, other than fixing a mismatch the "feeds the plot unchanged" test finds.

### SPEC sections touched
- §8.2: the nominal mid-drive fallback decided (§13 #1 removed).
- §8.3: the geology map's storage and behavior for unmapped codes, if decision 4 changes what it says.
- §10.2: dataset list and signatures confirmed, the M8 split noted, and the column lists replaced by a pointer to `docs/data/datasets.md`.
- §11: the Phase 2 sketch checked against the real API.
- §12.4: M7 done at close-out; M8 picks up the deferred datasets.
- `docs/data/ingest.md` (decision 6), `docs/data/qc.md` (G004), `docs/drafts/phase2-data.md` (dataset section moves out), `columns.yaml` (new columns), TODO #17.
