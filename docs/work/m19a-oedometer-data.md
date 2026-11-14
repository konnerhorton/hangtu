# M19 (a): oedometer data

## Intent
M19 is wave 3's first milestone (SPEC §1.3): the oedometer, one engine for sheets 06 (σ′p, Cc, Cs), 11 (Eoed,
Eur,oed), 12 B (k from cv·mv) and 21 (rock swelling), drawn as P13–P15. M19 splits in four, data first
(decision 1). This unit, (a), is stage A for those sheets: the oedometer tests read from the file into a
dataset.

**Goal:** from an AGS file or a CSV, an engineer gets each oedometer specimen's load increments. Each one has the
stress and void ratio at its start and end, and the lab's mv and cv. The specimen's initial state (void ratio,
height, water content, densities, condition) and any swelling values come with them. The values are in registry
columns with units, and loading, unloading and reloading are marked on each increment. They feed P01 and P07 as they
are, are what (b)–(d) derive from, and are checked by QC rules that catch records that can't give a valid result.

**Why:**
- **Nothing reads consolidation tests today.** `preconsolidation_stress` and `overconsolidation_ratio` exist only as
  SPT correlation outputs (M13 b2), so sheet 06 has nothing measured to compare them with on P01. The datasets
  spec puts consolidation out of scope (`docs/data/datasets.md` §1), and `site.ags` has no `CONG` or `CONS`.
- **The values are in standard groups** (checked against python-ags4 1.2.0's 4.2 dictionary, 2026-11-14):
  - `CONG`, one row per specimen: `CONG_TYPE` (a pick list: Oedometer, Hydraulic cell, Settlement on saturation,
    Measurement of swelling, Measurement of swelling pressure, Expandability), `CONG_COND` (Undisturbed,
    Remoulded), `CONG_IVR`, `CONG_HIGT`, `CONG_SDIA`, `CONG_MCI`, `CONG_MCF`, `CONG_BDEN`, `CONG_DDEN`,
    `CONG_PDEN` (# prefix when assumed), `CONG_SATR`, `CONG_SPRS` (swelling pressure, kPa), `CONG_SATH` (height
    change on saturation, %), `CONG_CORR` (corrected for equipment deformation);
  - `CONS`, one row per increment (`CONS_INCN`): `CONS_INCF` (stress at end, kPa), `CONS_IVR` and `CONS_INCE`
    (void ratio at start and end), `CONS_INMV` (the lab's mv, m²/MN), `CONS_CVRT` and `CONS_CVLG` (cv by root time
    and log time, m²/yr), `CONS_INSC` (secondary compression), `CONS_TEMP`.

  No group holds settlement against time, so P15's readings come from a CSV template (decision 3).
- **Sheet 06's and 11's pitfalls that belong to the data:**
  - σ′p and Cc come from the loading branch, Cs and Eur,oed from an unload–reload loop, so each increment says which
    branch it is on;
  - a curve with too few increments past the expected σ′p (maximum stress under 2–3 σ′p) can't give Cc;
  - void ratios that don't chain (one increment's end isn't the next one's start) or that rise under loading;
  - the lab's mv to recompute from the void ratios and compare.

  Each becomes a column, a QC finding, or a blank that is counted, never dropped.

**Scope:** the `CONG` and `CONS` groups (decision 4), joined to their sample like the other datasets (depth,
elevation, geology unit); `p.oedometer()`; an `oedometer` CSV template and an `oedometer_readings` template
(time against settlement per increment, for P15 in (c)); QC rules for the data pitfalls above; oedometer tests
added to `site.ags` through `_make_examples.py`, with the CSVs written from it.

**SPEC and TODO touched:**
- SPEC §8.2 (test depth), §10.2–10.3 (a new dataset and registry columns). The split into units goes in
  `STATUS.md`.
- `docs/data/datasets.md` §1 (consolidation moves in scope) and a new §6 subsection; `docs/data/qc.md` for the new
  rules.
- TODO #59 is left for later (decision 2). TODO #67's physical check (a consolidation stress far above the
  overburden) is the same kind of check as this unit's QC; the spec step decides whether to take it.

### Decisions (intent review, 2026-11-14)
1. **M19 is four units:** (a) oedometer data; (b) compressibility: σ′p (a bilinear fit, with Casagrande, Pacheco
   Silva and the work method as checks), Cc, Cs, OCR, Eoed and Eur,oed, sample quality by Δe/e0, P13; (c) mv, cv,
   k = cv·mv·γw, P14 and P15; (d) rock swelling, Huder–Amberg and Grob, from `CONS` increments and `CONG_SPRS`.
   M20 (K0 from OCR, SHANSEP, the Soft Soil set) follows. Reason: data first, and each fits one review.
2. **TODO #59 (shared result code in `ht.stats`, module size) waits** until the unit that puts σ′p and Cc into
   `representative()` and `select()`. Reason: M19 (a)–(d) add a dataset and analyses, not `ht.stats` results.
3. **P15's time–settlement readings come from a CSV template now,** as wave 2 did for triaxial readings; wave 0
   adds the AGS route. Reason: AGS 4.2 has no group for them, and cv fitting is P15's whole purpose.
4. **`CONG` and `CONS` only.** The CRS and Rowe cell groups (`ESCG`, `ESCT`, which carry the lab's σ′p, Cc and Cs)
   come later, marked as rate-dependent so they aren't mixed with incremental tests. Reason: incremental-load tests
   are the common case, and CRS σ′p differs from them by method.
5. **One row per increment,** with the specimen's values repeated. Reason: it matches `p.triaxial()`'s one row per
   stage, and it is what P13 and the fits read.
6. **The branch is marked from the stress sequence:** a stress below the previous one is unloading, and a stress
   rising again before it passes the previous maximum is reloading. The column is `load_branch`, checked against
   the registry in the spec step.

### Open (for the spec step)
- **Names** for the new columns (stress and void ratio at an increment's end, mv, cv by two methods, swelling
  pressure, height change on saturation), checked against the whole registry. Existing ones are reused:
  `void_ratio`, `water_content`, `bulk_unit_weight`, `dry_unit_weight`, `sample_condition`, `test_type`.
- **The swelling `CONG_TYPE`s** (Measurement of swelling, swelling pressure, Expandability): read here and left for
  (d), or read in (d).
- **Assumed particle density** (`CONG_PDEN` with #): kept as a flag, as `p.particle_density()` does.
- **Which QC rules,** and whether TODO #67's physical check is one of them.

### Out of scope
- Every derivation: σ′p, Cc, Cs, Eoed, k and swelling (M19 b–d).
- `ESCG` and `ESCT` (decision 4); settlement-against-time readings from AGS (wave 0).
- Stage D for sheet 06 (`representative()`, `select()`) and TODO #59.

## Spec
The rules live in the topic docs: the dataset in `docs/data/datasets.md` §6.14, the QC rules in `docs/data/qc.md`
§4.15. This section lists what changes where, the decisions behind it and the acceptance criteria. 🟡 marks a value
or name proposed here, awaiting review; 🔬 marks something to verify against a source before the build.

### Changes
- **`docs/data/datasets.md`:** §6.14 `p.oedometer()` (new); §1 (consolidation in scope), §2, §8, §11, §11.1 and §12
  updated for it.
- **`docs/data/qc.md`:** §4.15 oedometer rules E001–E005 (new); §4.10's minimum fields gain `CONG` and `CONS`; §8
  has the defects cases.
- **`ht.analysis.oedometer_load_branch()`** (new, decision 3), with its reference entry. Its rule goes in a new
  section of `docs/analysis/` only if (b) needs one; until then the docstring and datasets.md §6.14 hold it.
- **`docs/plots/P00-framework.md` §4.1 and `config/defaults.yaml`:** two quantity kinds (decision 6). Ingest then
  stores `CONS_INMV`, `CONS_CVRT` and `CONS_CVLG` with a kind, so the database schema version goes up
  (`docs/data/ingest.md` §2) and an older database asks to be re-ingested.
- **SPEC:** §10.2, the dataset. §8.2 doesn't change: `CONG` is a lab test placed by the lab-test row.
- **Registry** (each name checked against `columns.yaml` on 2026-11-14; none exists, and none collides):
  - new columns: `applied_vertical_stress`, `void_ratio_at_increment_start`, `void_ratio_at_increment_end`,
    `load_branch`, `reported_coefficient_of_volume_compressibility`,
    `reported_coefficient_of_consolidation_root_time`, `reported_coefficient_of_consolidation_log_time`,
    `swelling_pressure`, `height_change_on_saturation`, `specimen_diameter`, `equipment_deformation_corrected`;
  - new AGS sources for existing columns: `test_type` (`CONG_TYPE`), `sample_condition` (`CONG_COND`),
    `test_stage` (`CONS_INCN`), `water_content` (`CONG_MCI`), `final_water_content` (`CONG_MCF`),
    `bulk_unit_weight` and `dry_unit_weight` (`CONG_BDEN`, `CONG_DDEN` × g), `particle_density` (`CONG_PDEN`),
    `degree_of_saturation` (`CONG_SATR`), `void_ratio` (`CONG_IVR`), `specimen_height` (`CONG_HIGT`),
    `test_remarks` (`CONG_REM`), `remarks` (`CONS_REM`);
  - the `oedometer` template (decision 9).
- **Test files:** `CONG`/`CONS` in `site_si.ags`, `site_us.ags` and `site_v404.ags`; the edge cases in `joins.ags`;
  the E cases in `qc_defects.ags`.
- **Example file:** `site.ags` gains two oedometer tests through `_make_examples.py` (decision 10), and
  `oedometer.csv` is written from it.
- **Docs site:** `p.oedometer()` in the datasets guide's table and its reference entry; the E rules where the AGS
  and QC guide lists rules.

### Decisions
1. **One row per increment** (intent decision 5): each `CONS` row in file order, with its `CONG` row's values
   repeated. The specimen's columns are its initial state (and `final_water_content`); the increment's are the
   stress at its end, the void ratios at its start and end, and the lab's mv and cv.
   - **A `CONG` row with no `CONS` rows is one row** with blank increment columns. A swelling pressure test
     (`SWELLPRESS`) often reports only `CONG_SPRS`, and a settlement on saturation test only `CONG_SATH`; dropping
     the specimen would drop them silently. This differs from `p.triaxial()`, where a `TREG` with no stages
     gives no row, because a triaxial result is always in a stage.
   - **Every `CONG_TYPE` is read** (`OEDOMETER`, `HYDRAULIC CELL`, `SETTLESAT`, `SWELL`, `SWELLPRESS`,
     `EXPANDABILITY`, and any other text as written), with `test_type` saying which. (d) interprets the swelling
     types; (b) fits only the types it names. Reason: leaving rows out by type would be dropping data, and
     `test_type` filters them in one line.
2. **Increment order is file order.** AGS lists an increment's rows in sequence, and `CONS_INCN` is free text
   (`"3"`, `"3a"`, `"Flood"`). QC E004 flags a file whose numeric `CONS_INCN` values aren't increasing in file
   order, so a resorted file is caught rather than reordered by a guess.
3. **`load_branch` comes from `ht.analysis.oedometer_load_branch(df)`,** which `p.oedometer()` calls, so CSV and
   AGS rows follow one rule (as `p.triaxial()` calls `triaxial_failure_stresses()`). Per `specimen_id`, in row
   order, comparing each `applied_vertical_stress` with the previous one and with the largest so far:
   - `loading`: the first increment, or a stress above every earlier stress;
   - `unloading`: a stress below the previous one;
   - `reloading`: a stress above the previous one but not above the largest so far (equal to it counts as
     reloading: the curve has only just come back to it);
   - `constant_stress`: a stress equal to the previous one (flooding, or a creep stage held at one stress).
   - A blank stress gives a blank branch, and the next row is compared with the last stress given. A specimen
     with no increments has a blank branch.
   - The function returns a copy with the column added. On a CSV frame without `specimen_id` or
     `applied_vertical_stress` it raises an error naming the missing column.
   - 🟡 The four values and `constant_stress` as the name for a held stress.
4. **Names** (🟡, checked against the registry):
   - **`applied_vertical_stress`** for `CONS_INCF`, as `applied_normal_stress` is the shear box's. Not
     `effective_vertical_stress`, which is the in situ σ′v0 that `vertical_stress()` writes; a frame passed
     through it would be overwritten (the reason M11 (a) gave for `pore_pressure_at_failure`). In a drained
     oedometer the applied stress at the end of an increment is the effective stress, and the description says so.
   - **`void_ratio_at_increment_start`, `void_ratio_at_increment_end`**, and `void_ratio` for the specimen's
     initial `CONG_IVR`, as `p.triaxial()` and `p.shear_box()` use it.
   - **`reported_` for the lab's mv and cv:** they are the lab's derived values, which (c) recomputes (mv from the
     void ratios, cv from P15's readings) and compares, as M11 (a) decision 8 did for c′ and φ′. They are written
     out (`coefficient_of_volume_compressibility`, `coefficient_of_consolidation`) since `mv` and `cv` are bare
     symbols.
   - **`test_stage` for `CONS_INCN`,** the generic stage column the triaxial, vane and shear box datasets already
     use, rather than a new `load_increment`. Its description gains "an oedometer increment".
   - **`height_change_on_saturation`** (`CONG_SATH`, %) is kept with the file's sign: the dictionary doesn't
     say whether swelling is positive. The description says so, and (d) decides how to read it.
5. **The specimen's initial state uses the existing names** (`water_content`, `bulk_unit_weight`,
   `dry_unit_weight`, `particle_density`, `particle_density_assumed`, `degree_of_saturation`, `void_ratio`,
   `specimen_height`), as M11 (a) decision 7 did: they are a specimen set up for the test, in their own dataset,
   so they aren't pooled with `p.density()` by accident.
   - Densities become unit weights (× g), as in every dataset (M14 (a) decision 2).
   - **An assumed particle density** (`#2.65`) keeps its value with `particle_density_assumed = True`, as
     `p.particle_density()` and `p.shear_box()` do. It is never borrowed from `LPDN`: the lab's own value for the
     specimen is the one its void ratio was computed with.
6. **Two quantity kinds** (P00 §4.1; 🟡 the US displays):

   | Kind | Canonical | US display | SI display | Columns |
   |---|---|---|---|---|
   | `volume_compressibility` | m²/MN | ft²/kip | m²/MN | mv |
   | `consolidation_coefficient` | m²/yr | ft²/yr | m²/yr | cv |

   ft²/kip is the inverse of ksf, the US display of `modulus`, so mv and Eoed = 1/mv read in matching units. The
   aliases `m2/MN` and `m2/yr` already exist. `CONS_INSC` (secondary compression, whose definition, e or strain
   per log cycle, the dictionary doesn't give) and `CONS_TEMP` aren't read; (c) decides on them.
   - *Changed in the plan step (2026-11-14):* a `time` kind is left to (c). Ingest converts every heading to its
     kind's canonical unit, so a `time` kind would also convert about 20 standard headings in s, min or day (CPT,
     DMT, pressuremeter durations) that nothing here reads.
7. **QC (level 1), E001–E005 in qc.md §4.15** (🟡 the letter, since `E` is free; the thresholds). Each checks a
   specimen against itself: a record whose numbers can't all be right. Ranges for Cc or σ′p are level 2.

   | ID | Rule | Severity | Thresholds |
   |---|---|---|---|
   | E001 | Void ratios don't chain: an increment's `CONS_IVR` differs from the previous increment's `CONS_INCE` | warning | `void_ratio_chain_tolerance: 0.002` |
   | E002 | The void ratio rose over an increment whose stress is above the previous one | warning | `void_ratio_chain_tolerance` |
   | E003 | `CONS_INMV` differs from Δe / (1 + e_start) / Δσ′ by more than the rounding of the values allows | warning | |
   | E004 | Numeric `CONS_INCN` values aren't increasing in file order | warning | |
   | E005 | `CONG_IVR` differs from ρs / ρd − 1 (`CONG_PDEN`, `CONG_DDEN`) | warning | `initial_void_ratio_tolerance: 0.02` |

   - E001 and E002's tolerance clears the 3DP rounding of two void ratios (at most 0.001). The first increment
     isn't chained to `CONG_IVR`, since flooding or seating can change the void ratio between them.
   - E002 is a warning, not an error: a swelling soil can still swell under a small load increase. The message
     says so.
   - E003 skips the first increment (its start stress is the seating load, which the file doesn't give) and any
     increment whose Δσ′ is 0 or less. "Allows" is interval arithmetic: e ± 0.0005 (3DP), the stresses as
     written, and the reported mv ± half a unit in its second significant figure (2SF). A finding means the two
     intervals don't overlap. 🔬 The definition, mv = Δe / ((1 + e_start) Δσ′) with e at the start of the
     increment, is to be checked against BS 1377-5 and ISO 17892-5 before the build. A lab that divides by 1 + e0
     of the specimen gives values 5–20 % apart at later increments, which this rule would flag. If either
     standard defines mv on e0, the rule takes the one the standard gives, and the message names it.
   - E005 only where all three are given. 2DP densities move ρs / ρd − 1 by at most 0.010 (ρs 2.70, ρd 1.50);
     0.02 clears it. The message says when ρs is assumed (`#`). The dictionary's own example (ρd 1.75, ρs 2.65,
     e0 0.800) raises it: 2.65 / 1.75 − 1 = 0.514. The example's values are illustrative and not one specimen.
   - **TODO #67's physical check isn't taken here.** An oedometer is loaded far past the overburden by design
     (often 10–30 σ′v0), so "consolidation stress far above overburden" doesn't fit this test. It belongs to the
     triaxial's `TRET_CONP`, and #67 stays open.
8. **Minimum fields** (qc.md §4.10):
   - `CONG`: required `<SPEC_KEY>`; recommended `SPEC_REF`, `SPEC_DPTH`, `CONG_TYPE`, `CONG_COND`, `CONG_IVR`,
     `CONG_HIGT`.
   - `CONS`: required `<SPEC_KEY>`, `CONS_INCN`, `CONS_INCF`, `CONS_INCE`; recommended `CONS_IVR`.

   An increment with no stress or no end void ratio can't place a point on the curve, so it is incomplete (§7):
   left out by default with the §7 warning, kept by `include_incomplete=True`. Leaving one out breaks the chain
   around it, which E001 reports as well.
9. **Templates:**
   - `ht.template("oedometer")` is the dataset's columns without `source_line` and `load_branch`, which
     `oedometer_load_branch()` adds.
   - *Changed in the plan step (2026-11-14):* `ht.template("oedometer_readings")` (intent decision 3) moves to
     (c), with the `time` kind it needs (decision 6). It is still a CSV template rather than wave 0's AGS route;
     (c) is the first unit that reads it, and it designs the columns with the fit that reads them.
10. **Example data** (`ht.examples`, through `_make_examples.py`, with site-like scatter): two specimens in the
    example's clay unit, one lightly overconsolidated and one stiffer, each with eight to twelve increments and
    one unload–reload loop, plus a swelling pressure test with no increments. Enough for (b)'s σ′p and Cc and P13
    to draw from the example file. The values are invented and say so in the generator.

### Sources
- **AGS 4.2 dictionary** (python-ags4 1.2.0, `Standard_dictionary_v4_2.ags`): `CONG` (parent `SAMP`; its keys
  include `SPEC_REF` and `SPEC_DPTH`) and `CONS` (parent `CONG`, key `CONS_INCN`); headings, types, units, and the
  pick lists `CONG_TYPE` and `CONG_COND`. Checked 2026-11-14.
- **Unit factors:** exact by definition (1 ft = 0.3048 m, 1 lbf = 4.4482216152605 N). 1 m²/MN = 10.7639104 ft² /
  224.808943 kip = 0.0478803 ft²/kip; 1 m²/yr = 10.7639104 ft²/yr; 1 kPa = 20.8854342 psf.
- 🔬 **mv's definition** for E003: BS 1377-5 and ISO 17892-5 (decision 7). Needed from the user, or E003 waits.
- No correlation or empirical source is used. The E thresholds are rounding bounds, not cited values.

### Acceptance criteria
Golden values hand-calculated. Tolerance 1e-9 relative unless a criterion says otherwise.

The good files' specimen (BH1, 🟡 sample U3) is: `CONG_TYPE` `OEDOMETER`, `UNDISTURBED`, ρ 1.92, ρd 1.50,
ρs 2.70 Mg/m³, w 28.0 %, S 95 %, e0 0.800 (= 2.70 / 1.50 − 1), H 20.00 mm, D 75.00 mm, with these increments:

| # | σ′ (kPa) | e start | e end | mv reported (m²/MN) | mv recomputed | Branch |
|---|---|---|---|---|---|---|
| 1 | 25 | 0.800 | 0.795 | | (skipped) | loading |
| 2 | 50 | 0.795 | 0.788 | 0.16 | 0.007 / 1.795 / 25 kPa = 0.1560 | loading |
| 3 | 100 | 0.788 | 0.776 | 0.13 | 0.012 / 1.788 / 50 = 0.1342 | loading |
| 4 | 200 | 0.776 | 0.748 | 0.16 | 0.028 / 1.776 / 100 = 0.1577 | loading |
| 5 | 400 | 0.748 | 0.690 | 0.17 | 0.058 / 1.748 / 200 = 0.1659 | loading |
| 6 | 800 | 0.690 | 0.612 | 0.12 | 0.078 / 1.690 / 400 = 0.1154 | loading |
| 7 | 200 | 0.612 | 0.625 | | | unloading |
| 8 | 50 | 0.625 | 0.638 | | | unloading |
| 9 | 200 | 0.638 | 0.630 | | | reloading |
| 10 | 800 | 0.630 | 0.608 | | | reloading |
| 11 | 1600 | 0.608 | 0.520 | 0.068 | 0.088 / 1.608 / 800 = 0.06841 | loading |
| 12 | 400 | 0.520 | 0.538 | | | unloading |

(1/kPa = 1000 m²/MN.) Increment 4 has `CONS_CVRT` 2.1 and `CONS_CVLG` 1.8 m²/yr.

1. **Rows:** `p.oedometer()` gives twelve rows for this specimen in file order, with `test_stage` `"1"`–`"12"`,
   the stresses and void ratios of the table, and the specimen's values on each: `bulk_unit_weight` 18.82877 kN/m³
   (1.92 × 9.80665 = 18.828768), `dry_unit_weight` 14.70998 kN/m³ (1.50 × 9.80665 = 14.709975), `water_content`
   28.0, `particle_density` 2.70, `particle_density_assumed` False, `degree_of_saturation` 95, `void_ratio` 0.800,
   `specimen_height` 20.00 mm, `specimen_diameter` 75.00 mm, the lab depth and `depth_basis` (§6.2), and
   `test_type` `OEDOMETER`.
2. **Branches:** `load_branch` is the table's column, including increment 10 (800 kPa, equal to the earlier
   maximum) as `reloading` and 11 as `loading`.
3. **Branch rule on a CSV frame:** `oedometer_load_branch()` on the stresses 100, 100, 50, blank, 100, 200 of one
   specimen gives `loading`, `constant_stress`, `unloading`, blank, `reloading`, `loading`; on two specimens in one
   frame it starts each at `loading`; without `applied_vertical_stress` it raises an error naming it.
4. **US display:** with `display_units="US"`, increment 6 gives `applied_vertical_stress` 16708.35 psf
   (800 × 20.8854342), increment 2's mv 0.00766085 ft²/kip (0.16 × 0.0478803), increment 4's cv by root time
   22.60421 ft²/yr (2.1 × 10.7639104); to 1e-6 relative, the precision of the factors.
5. **Twins:** `site_si.ags` and `site_us.ags` give equal `p.oedometer()` (1e-9 relative) for each `display_units`,
   and the same E findings (none).
6. **No increments:** a `joins.ags` `SWELLPRESS` specimen with `CONG_SPRS` 150 kPa and no `CONS` rows is one row:
   `swelling_pressure` 150 kPa, `test_type` `SWELLPRESS`, blank increment columns and `load_branch`.
7. **Every type kept:** a `SETTLESAT` specimen with `CONG_SATH` −1.1 % gives `height_change_on_saturation` −1.1, as
   written; a type the dictionary doesn't list is kept with its text.
8. **Assumed particle density:** a `CONG_PDEN` of `#2.65` gives 2.65 and `particle_density_assumed = True`, never
   blank.
9. **Incomplete:** a `CONS` row with `CONS_INCE` blank is left out with the §7 warning, and kept with
   `include_incomplete=True` with a blank `void_ratio_at_increment_end`.
10. **QC (`qc_defects.ags`):** each E rule raises exactly the findings its case seeds:
    - E001: an increment ending at 0.700 followed by one starting at 0.690 (0.010 apart);
    - E002: 100 → 200 kPa with e 0.776 → 0.781 (up 0.005);
    - E003: increment 2 of the table with `CONS_INMV` 0.32 (recomputed 0.156; intervals 0.134–0.178 and
      0.315–0.325 don't overlap). The table's own mv values raise nothing: increment 6's intervals are
      0.1139–0.1169 (Δe 0.077–0.079, 1 + e 1.6895–1.6905) and 0.115–0.125;
    - E004: `CONS_INCN` 1, 2, 4, 3 in file order;
    - E005: `CONG_IVR` 0.650 with ρd 1.50, ρs 2.70 (expected 0.800; 0.150 apart).
11. **Good files stay clean:** `site_si.ags`, `site_us.ags` and `site_v404.ags` raise no E finding and no C001 for
    `CONG` or `CONS`.
12. **Empty:** a file with no `CONG` gives an empty frame with every column and the warning "No CONG group". A
    `CONS` row whose `CONG` is missing (Rule 10c) is built in the test, as the triaxial's is, and kept with blank
    specimen columns.
13. **Feeds the plots:** `ht.plot.profile(p.oedometer(), "void_ratio")` and
    `ht.plot.geology_unit_comparison(p.oedometer().drop_duplicates("specimen_id"), "void_ratio")` run on the good
    files with no warning.
14. **Templates:** `ht.template("oedometer")` is the dataset's columns without `source_line` and `load_branch`, in
    the same order (`tests/test_registry.py`).
15. **Common arguments:** `depth=`, `geology=`, `holes=` and `where={"test_type": "OEDOMETER"}` filter
    `p.oedometer()` as §2 says, keeping or dropping a specimen's increments together.
16. **Example file:** `ht.examples` gives `p.oedometer()` rows for decision 10's three specimens, with no E finding,
    and `oedometer.csv` read with `ht.read_csv()` equals the dataset's template columns.

## Plan
Seven build commits, each with ruff, mypy and the touched tests green, and the whole suite (`-n 2`) before each
commit. A step past about 300 changed lines (not counting test data or the test-file generators) splits as noted.
Steps 1–4 are Sonnet (wiring on existing patterns, decided by the tests); steps 5–7 are Opus (the QC arithmetic,
E003's source, close-out). Start a new session at step 5.

**Reused, not rebuilt:**
- **Dataset plumbing:** `Build` (`src/hangtu/datasets/_frame.py`: `rows()`, `numbers()`, `texts()`, `flagged()`,
  `finish()`); `specimens()` and `SPECIMEN_COLUMNS` (`datasets/_lab.py`) for lab depth; the parent join of
  `_stages()` in `datasets/_triaxial.py` (`CONS` under `CONG` as `TRET` under `TREG`, broken links kept with blank
  parent columns); the `ASSUMED` flag and × g of `datasets/_shear_box.py` for `CONG_PDEN` and the densities.
- **Analysis pattern:** `analysis/_triaxial.py` (`ColumnError`, returns a copy).
- **QC:** `qc/_shear_box.py`'s and `qc/_triaxial.py`'s shape (`@rule`, `Finding`, `RuleResult`, `_unflagged`,
  `_value`, `_where`), `rules.yaml` thresholds, `min_fields.yaml` with the `<SPEC_KEY>` anchor.
- **Test files:** `group()` and the SI/US twins of `tests/data/ags/_make_files.py`; the example generator
  `tests/data/_make_examples.py`.

### 1. `M19: add quantity kinds for mv and cv` (Sonnet)
- `src/hangtu/config/defaults.yaml`: `volume_compressibility` (meter² / meganewton; US foot² / kip, "ft²/kip"; SI
  m²/MN) and `consolidation_coefficient` (meter² / year; US foot² / year; SI m²/yr), placed so no existing unit
  matches them first. Aliases for `ft2/kip` and `ft2/yr` in `units/aliases.yaml` if the US twin file needs them.
- `src/hangtu/db.py`: `SCHEMA_VERSION` 2 → 3; `docs/data/ingest.md` §2 says why.
- `docs/plots/P00-framework.md` §4.1: the two rows.
- Tests: `tests/units/`: 0.16 m²/MN → 0.00766085 ft²/kip and 2.1 m²/yr → 22.60421 ft²/yr (1e-6 relative); a
  `CONS_INMV` heading ingested from a minimal AGS string is stored with kind `volume_compressibility`; the
  schema-mismatch test reads version 3.

### 2. `M19: add oedometer_load_branch()` (Sonnet)
- `src/hangtu/analysis/_oedometer.py` (new), exported in `analysis/__init__.py`: spec decision 3, per
  `specimen_id` in row order; `ColumnError` naming a missing column; returns a copy. Docstring: the four values and
  the rule, with equal-to-maximum as reloading.
- `columns.yaml`: `applied_vertical_stress` (stress, ratio) and `load_branch` (text), each with its description
  (decision 4); `docs/site/reference/analysis.md` entry.
- Tests: `tests/analysis/test_oedometer_load_branch.py` (new): AC 3, and AC 2's twelve stresses of the table on a
  hand-built frame (in kPa and in psf, the same branches).

### 3. `M19: add p.oedometer()` (Sonnet)
- `columns.yaml`: the rest of the spec's new columns and AGS sources; `test_stage`'s description; the `oedometer`
  template (decision 9).
- `src/hangtu/qc/min_fields.yaml`: `CONG` and `CONS` (decision 8; here, since §7 leaves records out by it, as M17
  (a) found).
- `src/hangtu/datasets/_oedometer.py` (new): one row per `CONS` row in file order with its `CONG` values; a `CONG`
  with no `CONS` as one row (decision 1); unit weights × g; `CONG_PDEN`'s flag; then
  `oedometer_load_branch()`; "No CONG group" for an empty file.
- `src/hangtu/project.py`: `Project.oedometer()` with the common arguments and the docstring;
  `docs/site/reference/project.md` entry.
- Test files (`tests/data/ags/_make_files.py`, regenerated): the AC table's specimen on BH1 (🟡 U3, or the nearest
  existing undisturbed sample in the clay) in `site_si`, `site_us` (psf) and `site_v404`, every recommended heading
  filled so no new C002; `CONG`/`CONS` ABBR codes. `joins.ags`: a `SWELLPRESS` with `CONG_SPRS` 150 and no
  `CONS`; a `SETTLESAT` with `CONG_SATH` −1.1; a type not in the dictionary; `CONG_PDEN` `#2.65`; a `CONS` row with
  `CONS_INCE` blank.
- Tests: `tests/datasets/test_oedometer.py` (new): AC 1, 2, 4–9, 12, 13, 15; `tests/test_registry.py` covers the
  template (AC 14). Existing tests counting groups in the good files updated.
- Split if large: (3a) the good-file specimen, `Project.oedometer()` and AC 1–5, 13–15; (3b) the `joins.ags` cases
  and AC 6–9, 12.

### 4. `M19: add oedometer tests to the example project` (Sonnet)
- `tests/data/_make_examples.py`: decision 10's three specimens in the example's clay, in the file's units, with
  site-like scatter and each increment's void ratios chained to 3DP and mv written from them by the E003 formula
  (so step 6 finds nothing); regenerate `src/hangtu/examples/data/site.ags` and write `oedometer.csv` from it.
- `docs/site/guides/datasets.md`: `p.oedometer()` in the table. Run `docs/prepare_site.py` and
  `zensical build --clean --strict`.
- Tests: `tests/test_examples.py`: AC 16's rows and CSV half; its exact QC findings updated (C002 only if a
  recommended heading is blank by design).

### 5. `M19: check oedometer results in QC (E001, E002, E004, E005)` (Opus)
- `src/hangtu/qc/_oedometer.py` (new), registered in `qc/__init__.py`; `rules.yaml` E001, E002, E004, E005 with
  `void_ratio_chain_tolerance: 0.002` and `initial_void_ratio_tolerance: 0.02`; `docs/data/qc.md` §4.15.
- `qc_defects.ags`: AC 10's E001, E002, E004 and E005 cases.
- `docs/site/guides/ags-and-qc.md`: the E rules.
- Tests: `tests/qc/test_oedometer.py` (new): AC 10's four cases with their messages (the 0.010, 0.005 and 0.150
  differences; the assumed-ρs wording); a case at exactly each tolerance raises nothing; `test_qc_acceptance.py`
  and `test_examples.py` keep the good files and the example clean (AC 11, 16).

### 6. `M19: check the lab's mv against the void ratios (E003)` (Opus)
- **Before it:** the mv definition checked against BS 1377-5 and ISO 17892-5 (spec decision 7, 🔬), with the clause
  in `qc.md` §4.15 and the rule's docstring. If neither standard is at hand, the step doesn't run: E003 goes to
  `docs/TODO.md` with the trigger "when BS 1377-5 or ISO 17892-5 is at hand, or before (c) recomputes mv", and
  step 7 notes it.
- `qc/_oedometer.py`: E003 with the interval arithmetic of decision 7; `rules.yaml`; `qc_defects.ags`: AC 10's
  E003 case.
- Tests: AC 10's E003 case (0.32 against 0.134–0.178) and the table's six mv values raising nothing (increment 6 at
  0.1139–0.1169 against 0.115–0.125); the first increment and an unloading increment skipped.

### 7. `M19: close out (a)` (Opus)
- SPEC §10.2: `p.oedometer()`. `docs/data/datasets.md` §1, §6.14 and the status line; `qc.md`'s status line.
- `STATUS.md`: M19's row reads "(a) done; (b) next", with the four units named; `CHANGELOG.md` Unreleased:
  `p.oedometer()`, `ht.analysis.oedometer_load_branch()`, the E rules, the `oedometer` template, and that a
  database made by an earlier version needs re-ingesting.
- Parameter index (`docs/drafts/parameters/README.md`): stage A of 06, 11 and 12 (oedometer) part built; 21 A part
  built (`CONG_SPRS`, `CONG_SATH`; rock free swell waits for wave 0).
- `docs/TODO.md`: #67's text notes the oedometer was considered and doesn't fit (it stays open); E003 if step 6
  deferred it.
- What a future session would get wrong without being told, written where it will be read (for example, a new
  quantity kind converts every AGS heading with that dimension at ingest, so check the dictionary before adding
  one).
- **Verification:** every AC reported met or not with its test; the whole suite (`-n 2`); ruff check and format
  check; mypy; the lowest-versions run (then `git checkout uv.lock`); the strict docs build.
