# M16: curves in user-defined groups (wave 0)

## Intent
Wave 0 (SPEC §1.3), moved ahead of M19 (b). 🟡 marks a choice proposed here, awaiting review.

**Goal:** readings curves that a file carries in user-defined AGS groups reach datasets in the shape the CSV route
already uses: triaxial readings (q, Δu and εv against axial strain, per stage) as `p.triaxial_readings()` in
`ht.template("triaxial_readings")`'s shape, so P12 and `triaxial_failure_from_readings()` run straight from the AGS
file; and shear box readings (τ and vertical displacement against horizontal displacement, per stage) as a new
dataset and template. The user says which groups hold which curves, because the group names are the file's own.

**Why:**
- **Waves 4 and 5 need it** (SPEC §1.3): E50 and the stiffness sets read the curves, and P12 can now be drawn only
  from a CSV the user builds by hand (P12, "Where the readings come from").
- **The sample dataset is in (TODO #31):** one real project, kept outside the repo. What it shows is under
  "Evidence"; in short, AGS 4.2 has a home for every summary value it carries, and none for a curve.
- **Ingest already handles it:** the file reads in 13 s, every user-defined group lands in the raw layer, and its
  headings are typed and converted by the rules already in `docs/data/ingest.md` §7. So wave 0 is the step from the
  raw layer to datasets, not ingest.

**The approach:**
- 🟡 **A readings map per project**, set like the geology map and the judgments file (`p.set_readings_map(path)`,
  stored in the database so a reopened project keeps it). For each user-defined group it names the curve kind
  (triaxial or shear box) and which heading gives which registry column, for example `TECS_TESN` → `test_stage`,
  `TECS_STRN` → `axial_strain`, `TECS_DEVF` → `deviator_stress`. The parent group and keys come from the file's
  `DICT` (`DICT_PGRP`), as ingest already reads them. hangtu never guesses a mapping from a heading's name (SPEC
  §2.6). Rejected: recognizing this file's group names, since another file's author picks others; TODO #45's
  recommended groups could later ship as a map hangtu provides.
- **Stage values come from the parent test:** a reading row takes `test_type`, `cell_pressure`, `back_pressure` and
  `effective_consolidation_stress` from its stage's row in `p.triaxial()` (`TRET`/`TRIT`), and the normal stress from
  `p.shear_box()` (`SHBT`), joined on the sample keys and the stage. A reading with no parent stage is left out and
  counted, never kept without its stage.
- 🟡 **Several groups into one dataset:** q, Δu and εv may each come from their own group, read at their own strains.
  Each reading keeps only the values its group gives, blank in the other columns, and readings at the same strain in
  one stage merge into one row. What the stress-ratio criterion and P12's paths do where q and Δu aren't read at the
  same strain (interpolate in strain, or use only readings that have both) is decided in the spec step.
- 🟡 **Readings in reading order:** a multistage stage ends with an unload before the next stage, so strain falls at
  its end. `triaxial_failure_from_readings()` now refuses a stage whose strain decreases (`docs/analysis/strength.md`
  §2); the spec step decides whether readings are ordered by the reading number and the tail allowed, and how P12
  draws it.
- **Rock triaxial through `TRIT`:** AGS 4.2 holds rock triaxial results in `TRIG`/`TRIT` (`TRIT_CELL` = σ3,
  `TRIT_DEVF` = σ1 − σ3, `TRIT_MODE`), which `p.triaxial()` already reads. A file that carries them in a user-defined
  group is re-encoded by its author; hangtu reads no user-defined rock triaxial group.
- 🟡 **`RUCS` into `p.triaxial()`** as rows with `cell_pressure` 0, so `hoek_brown_fit()` runs on an AGS file without
  a CSV (sheet 15 lists stage A under W0). The alternative is M21, with the other rock lab datasets.

**Constraints:**
- Columns come from the registry; new names (the shear box readings, the map's keys) are checked against it in the
  spec step.
- Units resolve as for any column: a user-defined heading's unit is the file's, converted on ingest where hangtu
  knows it (`docs/data/ingest.md` §7). A mapped heading whose unit has the wrong dimension for its column is an error
  naming both, not a conversion.
- Nothing is dropped silently: readings left out (no parent stage, a blank required value) are counted in a warning
  naming the group and lines.
- Readings are treated as the lab's, whatever their source: no provenance column. The user checks them before
  analysis.
- Test files and examples are synthetic, with the sample file's shapes and none of its values. The examples' curves
  go into `site.ags` through `tests/data/_make_examples.py`, with realistic scatter.

**Out of scope:**
- Swelling against time: dropped from wave 0 (decision 1). Rock swelling summary values are M19 (d).
- Oedometer curves (e, m_v, c_v, k and work against stress): the `CONS` increments already carry them (decision 6).
- Consolidation curves against √t (triaxial and shear box consolidation stages): with P15, M19 (c).
- Curves derived from the stage values (Mohr circles, stress paths, failure points): hangtu computes them.
- A plot of the shear box curves: a new P-number later; P31 lists it as a later addition.
- Standard quantities in user-defined headings of standard groups (TODO #72): the map is built so it can take them,
  but only when a second file needs it.
- The non-curve user-defined groups in the sample file (a shear wave velocity profile, overcoring stresses,
  abrasivity and punch tests): waves 4 and 5, or not placed.

**SPEC and docs touched:**
- SPEC §1.3 (wave 0's row: no swelling against time, rock triaxial through `TRIT`; the order of work: M16 now),
  §6/§7 (user-defined groups reach datasets through the map), §10.3 (new registry columns and a template).
- `docs/data/datasets.md` (the two readings datasets, the map, §11.1's templates), `docs/analysis/strength.md` §2
  (readings order), P12 ("Where the readings come from", the errors table), P31 §later.
- `docs/drafts/parameters/README.md` (sheet 15's W0, sheet 21's "waits for wave 0"), `STATUS.md` (M16's row and
  next; M19 (b) after it), `docs/TODO.md` (#31 resolved and deleted; #72 and #45 point to the map).

### Evidence (the sample dataset, 2026-11-18)
- **Curve groups** (all children of a standard test group, keyed by the sample keys plus a stage heading and a point
  number): triaxial q–ε (99 CU/CD stages under `TRET`, 16 UU under `TRIT`), εv–ε (57 drained), Δu–ε (42 undrained);
  shear box τ–δh and δv–δh (30 tests under `SHBT`). Every curve joins its parent stage (99/99, 16/16, 30/30).
- **Each quantity is its own group,** read at its own strains: 7 % of the Δu curves' strains are also in the q
  curves. So one row per reading with q, Δu and εv together (the template's shape) isn't how the file gives them.
- **Strain falls at the end of 20 of 99 q curves,** all stage A or B of multistage tests: the unload before the next
  stage, by up to 0.34 % strain.
- **The curves agree with the reported values:** the largest q on each curve over `TRET_DEVF` has median 1.000 and
  range 0.987–1.064; UU and shear box peaks agree within 0.3 %.
- **AGS 4.2 homes:** rock triaxial σ3 and σ1 fit `TRIT`; the shear box failure points are `SHBT`; the oedometer curves
  repeat `CONS_INCE`, `CONS_INMV` and `CONS_CVRT`; a Vs profile fits `ISTA` only partly (one depth, not a layer).
  No 4.2 group holds a monotonic triaxial or shear box curve (`CTRD` is for cyclic tests).
- **Ingest today:** units the file defines but hangtu doesn't know (`cm2/s`, `m2/kN`, `kJ/m3`, `%/log cycle`) are
  kept as written (`U005`); `min^0.5` and `cm` are read with a `U002`. No error.

### Decisions (intent review, 2026-11-18)
1. **Swelling against time is dropped from wave 0.** The sample file has none, and rock swelling's summary values
   are M19 (d)'s.
2. **Rock triaxial goes through `TRIG`/`TRIT`,** not a user-defined group: AGS 4.2 has the headings, and
   `p.triaxial()` already reads them.
3. **No provenance column on readings.** They are treated as the lab's; the user checks them before analysis.
4. **Synthetic data only in the repo,** copying the sample file's shapes. The real file stays outside it.
5. **M16 goes now, before M19 (b).** M19 (b)'s intent stays on its own branch.
6. **The oedometer curve groups aren't read:** `CONS` carries the same increments, and k from c_v·m_v is M19 (c)'s.
