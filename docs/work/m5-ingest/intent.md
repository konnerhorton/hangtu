# M5: AGS4 ingest — intent

## Goal
Read an AGS4 file (4.0.3 to 4.2) into a project SQLite database: a raw layer exactly as in the file, and a canonical layer that is AGS 4.2-shaped, typed, in SI, with value flags and surrogate keys (SPEC §6, §7). Open the database again later and query it.

## Why
- It's the first Phase 2 unit (SPEC §1.3 build order, §12.4 M5). QC (M6) and the datasets (M7) both read the canonical layer, so it comes first.
- It's what makes hangtu useful on real AGS files rather than hand-built CSVs.
- It tests the data model decision (SPEC §7) against real files early, while reversing it is still cheap.

## Constraints
- SPEC §6 (pipeline, versions, one file per project, blank vs flagged), §7 (data model rules), §2.2 (convert to SI on ingest, never guess units, case-sensitive aliases), §11 (error messages).
- `python-ags4` is added as a dependency (allowed by SPEC §12.1). No other new dependency. SQLite comes with Python; `STRICT` tables need SQLite ≥ 3.37, so check the version shipped with Python 3.12 on all three CI platforms.
- Units on ingest follow `docs/drafts/phase2-data.md` (Units on ingest), which the spec step finishes: "ton" by context, mixed units per column, datum as a setting.
- Never drop data silently: anything that can't be typed or converted stays in the raw layer and becomes a finding (`V`, `U001`–`U003`, `T001`).
- No company data: the test files are synthetic (SPEC §1.1, §12.3).
- **Done when:** the spec's acceptance criteria pass, including the twin-file test (the same data in an SI file and a US file ingests to identical canonical tables) and one older-version file mapped up to 4.2.

## Decisions (proposed, to settle in review)
1. **Where the spec lives:** `docs/data/ingest.md`, a topic doc that outlives the unit (process.md). `docs/drafts/phase2-data.md` keeps the QC and dataset notes until M6 and M7.
2. **Entry point:** `ht.Project.from_ags(path, db=..., overwrite=False)` and `ht.Project.open(db)`, as in the SPEC §11 sketch. Opening checks the file hash and the schema version (SPEC §7).
3. **Project access in this unit:** `p.groups`, `p.table(group, raw=False)` and `p.sql(...)`, so the result can be inspected. `p.locations` and `p.diff()` wait for M6/M7.
4. **Every group goes in.** All groups, user-defined ones included, are written to the raw layer and typed into the canonical layer from their `TYPE` row. A numeric heading is converted to SI from its `UNIT` row by pint. A short mapping file (`heading_quantities.yaml`) is needed only where the unit alone isn't enough: numeric headings of type `X` (`LNMC_MC`), and units whose meaning depends on the quantity (`pcf`, `%`, `ton`).
5. **Findings are stored, not reported.** Ingest writes its findings (`V`, `U`, `T`) to a table. The report, the rule YAML and `p.qc()` are M6.
6. **Test files:** a small synthetic SI file and its US twin, covering PROJ, TRAN, UNIT, TYPE, ABBR, LOCA, GEOL, SAMP, ISPT, LLPL, LNMC, GRAG, GRAT, PTST and FGHG; a 4.0.4 file with IPRG, to test mapping up; and a defects file for the ingest findings. Each passes python-ags4 validation except the defects file.

## Out of scope
- QC rules beyond the ones ingest raises, the QC report and `diff()` (M6).
- Depth/elevation/geology joins, the geology map and the ready-made datasets (M7).
- Mid-drive SPT depth (SPEC §8.2, M7).
- DIGGS, AGS3, more than one file per project.
- Writing or editing AGS files (SPEC §1.4).
- The open research items in the Units on ingest notes: pcf in density headings (#5) and nominal SPT penetrations (#6). Ingest converts what the file declares; the research can change a mapping later.

## SPEC sections touched
- §6: pipeline and rules confirmed or adjusted by the spec.
- §11: the Phase 2 API sketch, if decision 2 or 3 changes it.
- §12.1: `python-ags4` with its version floor; SQLite version note.
- §12.4: M5 done at close-out.
- `docs/drafts/phase2-data.md`: Ingestion and Units on ingest move to `docs/data/ingest.md`.
