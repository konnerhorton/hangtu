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

## Spec
The rules live in the topic docs: the readings map and the two datasets in `docs/data/datasets.md` §6.15–6.17, the
readings rules in `docs/analysis/strength.md` §2, the figure's side in P12. This section lists what changes where,
the decisions behind it and the acceptance criteria. 🟡 marks a choice proposed here, awaiting review.

### Changes
- **`docs/data/datasets.md`:** §6.15 the readings map, §6.16 `p.triaxial_readings()`, §6.17
  `p.shear_box_readings()` (new); §1, §2, §8 and §11.1 updated for them.
- **`docs/analysis/strength.md` §2:** each quantity read from its own rows; the loading part and the unload tail;
  a strain decrease in the loading part is a warning, no longer an error; Δu and εv interpolated in strain at a q
  reading; AGS readings need `failure_criterion=`.
- **P12:** §1 (where the readings come from), §3 (rows with only some quantities; the template's new columns),
  §4 (interpolation, candidates), §7 (curves in row order, the tail drawn), §11 (the new cases; strain decrease a
  warning), §15 (M16's item removed). §12's criteria stand; R1–R4 have every quantity on every row, so they don't
  change.
- **P31 §15:** the displacement curves read `p.shear_box_readings()`.
- **`docs/data/ingest.md`:** §4 `meta_readings_map`; §2 schema version 4, so an older database asks to be
  re-ingested.
- **SPEC:** §1.3 (wave 0's row: the curves it reads, rock triaxial through `TRIT`, no swelling against time; the
  order of work), §6.2 (user-defined groups reach a dataset only through the map), §7 (the map's metadata table),
  §10.1 (`p.set_readings_map`, `p.readings_map`). §10.2 needs no change: the readings datasets are datasets.
- **Registry** (each name checked against `columns.yaml` and every spec on 2026-11-18; none exists as a column):
  - new columns: `horizontal_displacement`, `shear_stress`, `vertical_displacement` (decision 7);
  - existing columns gain the readings datasets in `used_by`, and `axial_strain`, `deviator_stress`,
    `excess_pore_pressure` and `volumetric_strain` change their `ags:` note from "none: a user CSV" to "a
    user-defined group, through the readings map";
  - `ht.template("triaxial_readings")` gains `ground_level`, `depth_basis`, `elevation`, `soil_class` and
    `geology_description` (decision 5); `ht.template("shear_box_readings")` is new.
- **Code** (named for the plan): `Project.set_readings_map`, `Project.readings_map`, `Project.triaxial_readings`,
  `Project.shear_box_readings`; `meta_readings_map` and `SCHEMA_VERSION = 4` in `db.py`; the readings rules in
  `analysis/_triaxial_readings.py` and the plot.
- **Test files:** curve groups `XTDS` (q), `XTPW` (Δu), `XTVS` (εv) and `XSBS` (shear box) in `site_si.ags`,
  `site_us.ags` and `joins.ags`, after every other group so no earlier line moves, with their `DICT` rows, and
  `tests/data/ags/readings_map.csv`. `site_v404.ags` doesn't get them.
- **Example file:** `site.ags` gains the example stages' curves through `_make_examples.py` (decision 11), with
  `readings_map.csv` beside it in `ht.examples`; `triaxial_readings.csv` and a new `shear_box_readings.csv` are
  written from the project.
- **Docs site:** the two datasets in the datasets guide's table, a short section on the readings map, reference
  entries for the four new methods, and the new template in the templates guide.

### Decisions
1. **A readings map per project, stored as content** (intent 🟡; `datasets.md` §6.15). A CSV or DataFrame with
   `group`, `dataset`, `heading`, `column`, one row per mapped heading, stored in `meta_readings_map` like the
   geology map. Content rather than a path, unlike the judgments file: the map describes the one file a database
   holds and doesn't change while the engineer works, where judgments are edited during design and re-read.
   - **The parent comes from the file's `DICT`,** never from the map: the stage group follows from `DICT_PGRP`
     (`TREG`/`TRET` → `TRET`, `TRIG`/`TRIT` → `TRIT`, `SHBG`/`SHBT` → `SHBT`). The sample's curve groups are all
     children of the test group (`TREG`, `TRIG`, `SHBG`), keyed by the sample and specimen keys plus a stage and a
     point number; a child of the stage group is allowed too, since its keys hold the same stage.
   - **`dataset` names the destination,** not a "curve kind": an engineer reads it as the function they call.
     The parent must fit it, so a map that sends a `SHBG` child to `triaxial_readings` is an error.
   - **Checked when set, against the file;** every error stores nothing. A group the file doesn't have is an error
     (🟡), so a typo can't give an empty dataset silently; a map hangtu ships later for TODO #45's recommended
     groups would revisit this.
   - **User-defined groups only.** A standard group in the map is an error; TODO #72 (a user-defined heading in a
     standard group) extends the map when a second file needs it, as decided there.
2. **Units come from ingest, never the map.** A mapped numeric heading must have been converted to its column's
   quantity kind; anything else (wrong dimension, `U005`, raw only) is an error at `set_readings_map` naming the
   heading, its unit and the kind. Every unit in the sample's curve groups (`%`, `kPa`, `mm`) converts.
3. **One row per reading, never merged** (changes intent 🟡 "Several groups into one dataset"). The intent merged
   readings at the same strain. In the sample, 56 of 99 q curves repeat a strain within the curve (the first,
   vertical segment, where q rises at constant strain), so a merge by strain would pair the wrong q and Δu. Each
   reading keeps only its group's values, and the analysis reads each quantity from its own rows
   (`strength.md` §2). A CSV row with all three is the same rule's special case, so CSV behavior doesn't change.
4. **Δu and εv interpolated in strain at each q reading** (intent 🟡, the spec step's call). Linear in strain
   between the loading-part readings on either side, never extrapolated, and a row's own value always wins. The
   alternative, only readings with both, leaves almost nothing: 7 % of the sample's Δu strains are also q strains,
   and the q curve's peak is rarely one of them, so `pore_pressure_at_failure` would be blank on most CU stages.
   - **It warns** (decided in spec review, 2026-11-18): one warning per call of
     `triaxial_failure_from_readings()` counting and naming the stages whose Δu or εv at the failure reading was
     interpolated rather than read, so the engineer knows which failure values aren't the lab's readings. Paths
     interpolated away from failure don't warn.
   - Linear and not a smoothed fit: the readings are dense (median 355 per q curve), so the two neighbors are
     within a small strain step, and linear has no parameter to choose.
5. **The readings template gains the depth and geology columns** that `ht.template("triaxial")` has
   (`ground_level`, `depth_basis`, `elevation`, `soil_class`, `geology_description`), so the template stays its
   dataset's columns without `source_line` (`datasets.md` §11.1). They are optional, so existing CSVs still read.
   `source_line` becomes a reading column in `triaxial_failure_from_readings()`, or every AGS stage would fail the
   check that stage columns don't vary.
6. **Readings in file order; the unload tail is kept and read by rule** (intent 🟡 "Readings in reading order").
   - **File order, not the point number:** as `p.oedometer()` reads increments (M19 (a) decision 2), and the
     point number isn't mapped, so the map stays the columns a dataset has. In the sample, file order equals point
     order in every curve (99/99, 57/57, 42/42, 16/16, 30/30).
   - **The tail:** for each quantity, readings after the last one at the stage's largest strain are the unload
     tail: drawn, never a failure candidate, never interpolated from (`strength.md` §2). In the sample, 16 q
     curves end with one, 5 to 89 readings long. Leaving the tail out of the dataset would drop data; erroring
     (today's rule) would refuse 16 of 99 curves.
   - **A decrease inside the loading part is a warning, not an error** (🟡). The sample has 4 q curves with one
     point out of place mid-curve, by up to 0.11 % strain (e.g. 4.241 then 4.135 then 4.183 %), the same point in
     the Δu or εv curve of that stage. An error would refuse the whole call for one misplaced point; the warning
     names the stage, and the user fixes the file or accepts it. The error's other purpose, two stages under one
     `specimen_id`, is still caught by the stage-column check where their cell pressures differ.
7. **Names** (🟡, checked against the registry): `horizontal_displacement`, `shear_stress` and
   `vertical_displacement` for the shear box readings, as `horizontal_displacement_at_peak` and
   `vertical_displacement_at_peak` name the stage's values; `vertical_displacement` keeps the file's sign, as
   `SHBT_PDIN` does. `shear_stress` is also a key in the fit results' point records (`_shear_box_fit.py`,
   `_mohr_coulomb.py`), with the same meaning, τ; no column is named so. `test_stage` is reused for the stage
   heading, as the other datasets use it. The datasets are named after their templates: `p.triaxial_readings()`,
   `p.shear_box_readings()`.
8. **Stage values carried** are those P12 and the failure analysis read (`test_type`, `failure_criterion`,
   `effective_consolidation_stress`, `back_pressure`, `cell_pressure`; for the shear box `test_type` and
   `applied_normal_stress`), plus depth and geology. Specimen state (unit weights, water content) stays in
   `p.triaxial()` and `p.shear_box()`, joined on `specimen_id` and `test_stage` by a user who wants it, so the
   readings datasets don't repeat 40 columns on 35 000 rows.
9. **No failure criterion read from `TREG_FCR`.** The readings carry no lab mark, so the analysis needs
   `failure_criterion=`. Reading `TREG_FCR` as the rule would make the AGS route run without it, but the heading is
   free text: in the sample, 37 of 44 `TREG` rows leave it blank and the rest write "Maximum Stress Ratio" and
   "Maximum Deviator Stress", not the dictionary's wording. Matching text is guessing (SPEC §2.6; fuzzy matching
   is "Later" in SPEC §1.3).
10. **`RUCS` into `p.triaxial()` moves to M21** (intent 🟡; recommended). It has no curve, so it isn't wave 0's
    engine, and M21 reads the other rock lab groups with it. Adding UCS rows (`cell_pressure` 0) to `p.triaxial()`
    also puts rock rows in every soil envelope fit of that dataset, a choice to make with the other rock datasets.
    Until then `hoek_brown_fit()` takes UCS rows from a CSV, as now. Sheet 15's stage A moves from W0 to M21 in the
    parameter index at close-out.
11. **Example data:** `site.ags` gives each example triaxial stage q, Δu (undrained) and εv (drained) curves in
    three groups at their own strains, as the sample does, with a Δu and εv reading at each stage's failure strain
    so P12 AC 11 (the readings reproduce `p.triaxial()` exactly) holds without interpolation; the last stage of
    each multistage specimen has an unload tail. Each example shear box stage gets one group of τ and vertical
    displacement. Site-like scatter on the curves; values invented, and the generator says so.
12. **No QC rule compares a curve with its stage's reported values** in this unit. The sample's agree (largest q
    over `TRET_DEVF`: median 1.000, range 0.987–1.064). A rule is a later QC unit's, added to `docs/TODO.md` at
    close-out with that trigger.

### Sources
- **AGS 4.2 dictionary** (python-ags4 1.2.0): no group holds monotonic triaxial or shear box readings (`CTRD` is
  cyclic); `TRET`, `TRIT` and `SHBT` stages keyed by `_TESN`; `TREG_FCR` free text. Checked 2026-11-18.
- **The sample dataset** (one real project, outside the repo), for the shapes in decisions 1, 3, 4, 6 and 9.
  Counted on 2026-11-18 from the file itself.
- **Unit factors:** exact by definition. 1 kPa = 20.8854342 psf; 1 in = 25.4 mm.
- No correlation or empirical source is used: interpolation, the tail and the pick are rules on the readings.

### Acceptance criteria
Golden values hand-calculated. Tolerance 1e-9 relative unless a criterion says otherwise.

**The good files' curves** (`site_si.ags`; `site_us.ags` the same in psf and in):
- **BH1-U3 specimen 1, stage 1** (`CU`; cell 400, back 300 kPa; `TRET` q_f 180 kPa at 8.5 %, u_f 360 kPa):

  | Group | Readings (strain %, value) in file order |
  |---|---|
  | `XTDS` (q, kPa) | (0.0, 0), (2.0, 100), (4.0, 150), (6.0, 170), (8.5, 180), (10.0, 176), (12.0, 170), (11.8, 80), (11.6, 5) |
  | `XTPW` (Δu, kPa) | (0.0, 0), (3.0, 40), (7.0, 56), (10.0, 64), (12.0, 66), (11.7, 60) |

  q's loading part ends at 12.0 %, Δu's at 12.0 %; (11.8, 80), (11.6, 5) and (11.7, 60) are tails.
  Δu at the q readings: 0; 40 × 2/3 = 26.666667; 40 + 16 × 1/4 = 44; 40 + 16 × 3/4 = 52; 56 + 8 × 1.5/3 = 60;
  64 (own strain); 66; blank on the two tail readings.
- **BH2-U2 specimen 3, stage 3** (`CDM`; cell 700, back 300; `TRET` q_f 900 at 6.0 %, εv 3.40 %):
  `XTDS` (0, 0), (2, 500), (4, 800), (6, 900), (7, 880); `XTVS` (εv, %) (0, 0), (3, 2.0), (5, 3.0), (7, 3.8).
  εv at 6.0 % = 3.0 + 0.8 × 1/2 = 3.4.
- **BH2-D1 S1, stage 1** (`SMALL SBOX`, `SHBT_NORM` 50 kPa): `XSBS` (horizontal mm, τ kPa, vertical mm) (0.00, 0,
  0.00), (0.50, 20, 0.05), (1.00, 30, 0.15), (2.10, 38, 0.30), (4.00, 34, 0.25), (8.00, 31, 0.10), (12.00, 30,
  −0.40), matching the stage's peak (38 at 2.10, 0.30) and residual (30 at 12.00, −0.40).

**The edge cases** (`joins.ags`): J1-U3's stage 1 (`CU`; cell 400, back 300; `TRET_PWPF` blank) has `XTDS` (0.0, 0),
(1.0, 50), (2.0, 80), (1.9, 85), (3.0, 90), (4.0, 88), then one reading with a blank strain and q 70, and two
readings with `XTDS_TESN` "2" (no such `TRET` stage); `XTPW` (0.0, 0), (1.5, 20), (2.5, 30), (2.8, `<1`).

1. **Map stored:** `p.set_readings_map("readings_map.csv")` on the good files stores thirteen rows; `p.readings_map`
   returns them; `Project.open` gives them back; `p.set_readings_map(None)` removes them; `from_ags(...,
   overwrite=True)` starts with none.
2. **Map errors:** each error in `datasets.md` §6.15 is raised, built in the tests from a DataFrame against the
   good files, naming what it says; after any of them `p.readings_map` is what it was. Among them: `XTDS_DEVF`
   mapped to `axial_strain` (kPa against percent) names `XTDS_DEVF`, kPa and percent; `XSBS` mapped to
   `triaxial_readings` names its parent `SHBG` and the allowed parents; `TRET` in the map says it reads
   user-defined groups only; `XTQQ` lists `XSBS`, `XTDS`, `XTPW`, `XTVS` (and the files' other user-defined groups).
3. **Triaxial rows:** `p.triaxial_readings()` gives, for BH1-U3 stage 1, nine `XTDS` rows then six `XTPW` rows in
   file order, the q rows with `excess_pore_pressure` and `volumetric_strain` blank and the Δu rows with
   `deviator_stress` blank; each row has `test_type` `CU`, `test_stage` `"1"`, `cell_pressure` 400,
   `back_pressure` 300, `effective_consolidation_stress` 100, `failure_criterion` "Maximum deviator stress", the
   lab depth and geology of `p.triaxial()`'s row for that stage, blank `reported_failure_reading`, and its own
   `source_line`. Stages come in `p.triaxial()`'s order.
4. **Failure from AGS readings, maximum deviator stress:** `triaxial_failure_from_readings(p.triaxial_readings(),
   failure_criterion="max_deviator_stress")` gives BH1-U3 stage 1 at 8.5 %, q 180, u_f 360 kPa (Δu 60
   interpolated), and BH2-U2 stage 3 at 6.0 %, q 900, εv 3.4 (interpolated), u_f 300 (drained): equal to
   `p.triaxial()`'s `axial_strain_at_failure`, `deviator_stress_at_failure`, `pore_pressure_at_failure` and
   `volumetric_strain_at_failure` for those stages. One warning: the interpolation one, naming both stages (BH1-U3
   stage 1's Δu, BH2-U2 stage 3's εv). The tails raise none.
5. **Maximum stress ratio:** with `failure_criterion="max_stress_ratio"`, BH1-U3 stage 1 fails at the 12.0 %
   reading: σ′3 = 400 − 300 − 66 = 34, σ′1 = 204, ratio 6.0 (the 8.5 % reading gives 220 / 40 = 5.5, the
   10.0 % reading 212 / 36 = 5.888889), so u_f 366, q 170. The tail reading (11.8, 80) isn't a candidate. The
   12.0 % q reading has no Δu of its own, so its 66 (the Δu reading at the same strain) counts as interpolated in
   the warning.
6. **Paths:** in P12's `s_t` (effective), BH1-U3 stage 1's 2.0 % reading is at s′ = (73.333333 + 173.333333)/2 =
   123.333333, t = 50; the tail q readings aren't on the effective path and are on the `stress_strain` curve,
   which ends at (11.6, 5); the Δu twin axis line ends at (11.7, 60).
7. **Edge cases (`joins.ags`):**
   - `p.triaxial_readings()` leaves out the two stage-"2" readings in one warning naming `XTDS` and their lines,
     the blank-strain reading in the §7 warning (kept with `include_incomplete=True`), and the `<1` reading in the
     flag warning naming `XTPW` and its line; `include_incomplete=True` doesn't bring back the stage-"2" or `<1`
     readings.
   - `triaxial_failure_from_readings(..., failure_criterion="max_deviator_stress")` warns once naming J1-U3's
     stage 1 (strain falls from 2.0 to 1.9 % in the loading part), and fails it at 3.0 %, q 90, with u_f blank:
     3.0 % is outside the Δu readings (0–2.5 %, the `<1` at 2.8 % left out). A blank isn't interpolated, so no
     interpolation warning.
   - With `"max_stress_ratio"`, the candidates are the q readings at 0, 1.0, 2.0 and 1.9 % (inside 0–2.5 %); Δu
     there 0, 13.333333, 25 and 24; ratios 1, 136.666667 / 86.666667 = 1.576923, 155 / 75 = 2.066667 and
     161 / 76 = 2.118421; it fails at the 1.9 % reading, q 85, u_f 324, with the interpolation warning naming
     J1-U3 stage 1.
8. **CSV behavior kept:** P12's criteria 1–12 pass unchanged on R1–R4, except that R1 with two of stage A's
   readings swapped now gives the strain warning naming stage A, not an error. Two stages under one `specimen_id`
   without `test_stage` and with different `cell_pressure` still raise the stage-column error.
9. **Shear box rows:** `p.shear_box_readings()` gives BH2-D1 stage 1's seven rows in file order with
   `test_type` `SMALL SBOX`, `applied_normal_stress` 50, and the table's values; with `display_units="US"` the
   2.10 mm reading is 0.0826772 in (2.10 / 25.4) and τ 38 kPa is 793.646500 psf (38 × 20.8854342), to 1e-6
   relative.
10. **Twins:** `site_si.ags` and `site_us.ags` give equal `p.triaxial_readings()` and `p.shear_box_readings()`
    (1e-9 relative) for each `display_units`.
11. **Empty:** with no map, each readings dataset is an empty frame with every column and the no-map warning; with
    a map that names only shear box groups, `p.triaxial_readings()` is empty with the "names no
    triaxial_readings group" warning. A project with no curve groups and no map gives no other warning.
12. **Common arguments:** `holes=["BH2"]`, `depth=`, `geology=` and `where={"test_stage": "3"}` keep exactly the
    readings they should, a stage's readings together.
13. **Units:** `df.attrs["units"]` covers every numeric column of both datasets; `axial_strain` is in percent and
    the displacements in the `small_length` display unit.
14. **Templates:** `ht.template("triaxial_readings")` and `ht.template("shear_box_readings")` are their datasets'
    columns without `source_line`, in the same order (`tests/test_registry.py`); a CSV in the old template's
    columns reads and runs through `triaxial_failure_from_readings()` as before.
15. **Schema:** opening a version-3 database raises the re-ingest error.
16. **Example file:** `ht.examples` with its `readings_map.csv` gives `p.triaxial_readings()` and
    `p.shear_box_readings()` rows for every example triaxial and shear box stage; P12 AC 11 holds on
    `triaxial_readings.csv` written from it; the docs site's P12 examples run; `P12-us.png` is regenerated and
    looked at in the close-out.
17. **Sample file (manual, not in the suite):** with a map written for it, the sample dataset gives readings for
    99 `TRET` and 16 `TRIT` stages and 30 `SHBT` stages, no reading left out for a missing stage, and
    `triaxial_failure_from_readings(..., failure_criterion="max_deviator_stress")` runs with the strain warning
    naming the 4 stages of decision 6. Reported in the close-out, without the file's names or values.

## Plan
Seven build commits, each with ruff, mypy and the touched tests green, and the whole suite (`-n 2`) before each
commit. A step past about 300 changed lines (not counting test data or the test-file generators) splits as noted.
Steps 1–2 are Opus (the readings rules and how P12 draws them); steps 3–6 are Sonnet (registry, storage, datasets
and example data on existing patterns, decided by the tests' golden values); step 7 is Opus (close-out, the sample
file and the figure). Start a new session at steps 3 and 7.

**Reused, not rebuilt:**
- **Readings analysis:** `Readings` and `reduce_readings()` in `src/hangtu/analysis/_triaxial_readings.py`; P12
  reads through `reduce_readings()`, so the rules change in one place.
- **Map storage:** the geology map's path through `db.write_geology_map`/`read_geology_map` and
  `Project.set_geology_map` (`project.py` ~1250), and `datasets/_geology_map.py`'s reading of a CSV or DataFrame.
- **What the map is checked against:** the stored `DICT` table (`DICT_PGRP`), `meta_heading` (`standard`,
  `quantity`, `file_unit`) and the stored findings (`U001`–`U005`), so nothing re-reads the AGS file.
- **Dataset plumbing:** `Build` (`datasets/_frame.py`: `rows()`, `numbers()`, `texts()`, `flagged()`, `finish()`,
  `_empty()`); the stage rows of `datasets/_triaxial.py` (`_stages()`) and `datasets/_shear_box.py`; `specimens()`
  in `datasets/_lab.py` for `specimen_id` and lab depth.
- **Test files:** `group()` and the SI/US twins of `tests/data/ags/_make_files.py`; `tests/data/_make_examples.py`.

### 1. `M16: read each triaxial quantity from its own readings` (Opus)
- `src/hangtu/analysis/_triaxial_readings.py`, per `docs/analysis/strength.md` §2:
  - each quantity's readings are its rows with a value; the loading part and unload tail per quantity per stage;
  - `_check_strain` becomes one warning naming the stages whose loading part decreases (not an error);
  - Δu and εv at each q reading: own value, else linear in strain between the loading-part readings either side
    (sorted by strain, the last of equal strains in row order), blank outside their range and on tail readings,
    then a drained stage's blank Δu is 0; `pore`, `effective_minor` and `effective_major` use these values;
  - failure candidates are loading-part q readings only;
  - one warning per call naming the stages whose failure reading's Δu or εv wasn't the row's own;
  - `source_line` added to `READING_COLUMNS` (decision 5).
- 🟡 **The interpolation warning is the function's, not P12's:** `reduce_readings()` returns which stages were
  interpolated at failure, and `triaxial_failure_from_readings()` warns; `ht.plot.triaxial_shearing()` doesn't, so
  a figure of AGS-shaped readings draws without a warning on every CU stage. P12 §4's sentence is narrowed to say
  so in this commit.
- Docstring of `triaxial_failure_from_readings()`: the per-quantity rows, the tail, the interpolation and its
  warning, and that readings from an AGS file need `failure_criterion=`.
- Tests: `tests/analysis/test_triaxial_failure_from_readings.py`: AC 4, 5 and 7's analysis cases on hand-built
  frames in the AC tables' shape (BH1-U3 stage 1, BH2-U2 stage 3, J1-U3 stage 1 with the stage-"2", blank-strain
  and `<1` readings already removed), in kPa and in psf; AC 8 (`test_r2_decreasing_strain_raises` becomes the
  warning naming stage A; the two-stages-one-`specimen_id` error kept); a tail reading with the largest q is not
  picked; equal strains in the Δu readings take the last; a stage with every quantity on every row warns nothing
  about interpolation (R1–R4 unchanged).

### 2. `M16: draw partial readings and unload tails in P12` (Opus)
- `src/hangtu/plot/_triaxial_shearing.py`: `_draw_curves` draws each stage's q rows in row order, tail included;
  `_draw_second_axis` draws the Δu (or εv) rows in row order, tail included; `_draw_paths` uses the interpolated
  Δu, leaving out q readings without one (undrained effective path) and tail readings without their own Δu.
- Tests: `tests/plot/test_triaxial_shearing.py`: AC 6 on the step 1 frame (the 2.0 % reading at s′ 123.333333,
  t 50; the tail off the effective path; the `stress_strain` curve ending at (11.6, 5); the Δu line ending at
  (11.7, 60)); `test_decreasing_strain_raises` becomes the warning; `test_triaxial_shearing_acceptance.py` passes
  unchanged (AC 8).

### 3. `M16: add the shear box readings columns and readings templates` (Sonnet)
- `src/hangtu/columns.yaml`: `horizontal_displacement`, `shear_stress`, `vertical_displacement` (labels, kinds
  `small_length` and stress, descriptions; vertical keeps the file's sign); `used_by` gains the two readings
  datasets on every column they carry; the `ags:` note of `axial_strain`, `deviator_stress`,
  `excess_pore_pressure` and `volumetric_strain`; `triaxial_readings` template gains `ground_level`,
  `depth_basis`, `elevation`, `soil_class`, `geology_description` (decision 5); new `shear_box_readings` template
  in §6.17's order without `source_line`.
- `docs/site/guides/templates.md`: the new template and the triaxial one's new optional columns.
- Tests: `tests/test_registry.py`: the new template's columns registered (AC 14, registry half);
  `tests/analysis/test_triaxial_failure_from_readings.py`: a CSV in the old template's columns reads and runs as
  before (AC 14). `tests/test_examples.py` passes with the example CSV as it is (the new columns are optional).

### 4. `M16: store a readings map per project` (Sonnet)
- `src/hangtu/db.py`: `SCHEMA_VERSION` 3 → 4; `meta_readings_map` (`group`, `dataset`, `heading`, `column`, and
  the row order); `write_readings_map`/`read_readings_map` as the geology map's.
- `src/hangtu/datasets/_readings_map.py` (new): read a CSV or DataFrame; every check of `datasets.md` §6.15 in the
  order listed there, each a `HangtuError` naming the map line (or DataFrame row), group or heading and what to do;
  the mapped columns, required columns and allowed parents per dataset as constants shared with step 5.
- `src/hangtu/project.py`: `Project.set_readings_map(source)` (store nothing on any error) and the
  `readings_map` property; `from_ags(..., overwrite=True)` starts with none. `docs/site/reference/project.md`:
  both entries.
- Test files (`tests/data/ags/_make_files.py`, regenerated): `XTDS`, `XTPW`, `XTVS` and `XSBS` after every other
  group in `site_si.ags`, `site_us.ags` (psf, in) and `joins.ags`, with their `DICT` rows (`DICT_PGRP` `TREG` and
  `SHBG`, units `%`, `kPa`/`psf`, `mm`/`in`), keyed by the sample keys, `SPEC_REF`, a `_TESN` and a point number;
  the AC tables' readings on BH1-U3 specimen 1 stage 1, BH2-U2 specimen 3 stage 3, BH2-D1 S1 stage 1 and J1-U3
  stage 1; short plausible curves on the files' other `TRET` and `SHBT` stages. `tests/data/ags/readings_map.csv`
  (thirteen rows) and `tests/data/ags/README.md` (the groups and the map).
- Tests: `tests/datasets/test_readings_map.py` (new): AC 1, AC 2 (every §6.15 error from a DataFrame against
  `site_si.ags`, the map unchanged after each); `tests/test_db.py`: AC 15. Existing tests that count the good
  files' groups or QC findings updated (user-defined groups with `DICT` rows should raise none; any that do are
  named in the commit).
- Split if large: (4a) the test files and `README.md`, with the count updates; (4b) the map.

### 5. `M16: add p.triaxial_readings() and p.shear_box_readings()` (Sonnet)
- `src/hangtu/datasets/_readings.py` (new): for each mapped group, its rows joined to the stage rows on
  `specimen_id` and `test_stage` (text, exact); the stage values and lab depth of §6.16/§6.17; the order (stages in
  `p.triaxial()`'s or `p.shear_box()`'s order, groups in the map's order, rows in file order); the three left-out
  warnings naming the group and first lines (no stage; incomplete, kept by `include_incomplete=True`; flagged, not
  kept); the empty frame with every column and the no-map or no-group warning; then `Build.finish()` for geology,
  display units and the common arguments.
- `src/hangtu/project.py`: `Project.triaxial_readings()` and `Project.shear_box_readings()` with the common
  arguments and docstrings; `docs/site/reference/project.md` entries.
- Tests: `tests/datasets/test_readings.py` (new): AC 3, 7 (the dataset's warnings and
  `include_incomplete=True`), 9, 10, 11, 12, 13; AC 4–7 end to end: `triaxial_failure_from_readings()` and
  `ht.plot.triaxial_shearing()` on `p.triaxial_readings()` of `site_si.ags` and `joins.ags` give step 1's and
  step 2's values, and AC 4's rows equal `p.triaxial()`'s for those stages.
- Split if large: (5a) the triaxial dataset with AC 3–7, 10–13; (5b) the shear box dataset with AC 9 and its half
  of 10–13.

### 6. `M16: add readings curves to the example project` (Sonnet)
- `tests/data/_make_examples.py`: decision 11. Each example CU, CDM and UU stage's q curve in `XTDS`, each CU
  stage's Δu in `XTPW`, each CDM stage's εv in `XTVS`, at their own strains with site-like scatter, a Δu and εv
  reading at the stage's failure strain equal to its `TRET` value, and an unload tail on the last stage of each
  multistage specimen; each shear box stage's τ and vertical displacement in `XSBS` through its `SHBT` peak and
  residual. `DICT` rows, units the file's. Regenerate `src/hangtu/examples/data/site.ags`; write
  `readings_map.csv` beside it, and `triaxial_readings.csv` and `shear_box_readings.csv` from the project (in
  the file's units), the CSVs in their templates' columns.
- 🟡 **The example CSV keeps the lab's mark:** the generator sets `reported_failure_reading` True on each stage's
  q reading at its `TRET` failure strain, as a lab's CSV would, so the docs site's P12 examples (which use the
  mark) run unchanged. The AGS dataset itself carries no mark (§6.16).
- `src/hangtu/examples/__init__.py`: the docstring names `readings_map.csv` and `shear_box_readings.csv`.
- `docs/site/guides/datasets.md`: the two datasets in the table and a short section on the readings map. Run
  `docs/prepare_site.py` and `zensical build --clean --strict`.
- Tests: `tests/test_examples.py`: AC 16 (rows for every example triaxial and shear box stage; P12 AC 11 on the
  regenerated `triaxial_readings.csv`, with the interpolation warning asserted where the failure reading's Δu or
  εv is another row's); the file lists and the example's exact QC findings updated.

### 7. `M16: close out` (Opus)
- **Visual check:** regenerate `docs/plots/img/P12-us.png` from the new example readings (tails drawn), look at it.
- **Sample file (AC 17, manual):** with a map written for it outside the repo, the counts of AC 17; reported in
  the chat without the file's names or values.
- SPEC §10.1's methods checked against the build; `docs/data/datasets.md` §1/§2/§8 and status lines;
  `docs/data/ingest.md` if the schema note changed.
- `STATUS.md`: M16 done; next M19 (b). `CHANGELOG.md` Unreleased: `p.set_readings_map()`, `p.readings_map`,
  `p.triaxial_readings()`, `p.shear_box_readings()`, the `shear_box_readings` template and the triaxial one's new
  columns, readings with one quantity per row, the strain-decrease warning (was an error), the unload tail, the
  interpolation warning, and that an earlier database needs re-ingesting.
- Parameter index (`docs/drafts/parameters/README.md`): sheet 15's stage A from W0 to M21 (decision 10); sheet
  21's "waits for wave 0" updated.
- `docs/TODO.md`: #31 deleted (resolved); #72 and #45 point to the readings map; new items for the curve-against-
  reported-values QC rule (decision 12, trigger "a later QC unit") and `RUCS` into `p.triaxial()` (trigger M21).
- What a future session would get wrong without being told, written where it will be read.
- **Verification:** every AC reported met or not with its test; the whole suite (`-n 2`); ruff check and format
  check; mypy; the lowest-versions run (then `git checkout uv.lock`); the strict docs build.

### Notes from the build
- **Step 1, a drained stage's u_f:** AC 4 (BH2-U2 stage 3, u_f 300 from readings without Δu) and `strength.md` §2
  ("a drained stage's blank Δu is 0 … the failure row's `pore_pressure_at_failure` … use these values") need the
  failure row's u_f to be the back pressure in a drained stage with Δu blank. Until now it was blank there, and
  `triaxial_failure_stresses()` filled it with a warning. So R3's failure row now has u_f 200 kPa and no warning;
  its stresses, paths and every P12 criterion are unchanged. P12 §4's sentence says so.
- **Step 1 took two of step 2's test changes:** `test_decreasing_strain_raises` (now `_warns`) and the R3 plot
  tests that expected the back-pressure warning, since the analysis change makes them fail.
- **Step 2, the footnotes:** a row with only Δu or εv isn't counted as left out any more (it draws on the second
  axis); the curve footnote now reads "without axial strain, or without a deviator stress, Δu or ε_v". In effective
  stress, q readings left off a drawn path for want of a Δu (outside the stage's Δu readings, or on the tail) are
  counted: "Left out of the paths: 2 readings without Δu" for BH1-U3 stage 1's tail.
