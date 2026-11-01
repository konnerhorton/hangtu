# M17 (a): undrained strength and shear box data

## Intent
M17 is wave 2's second milestone (SPEC §12.4): undrained strength (UU, UCS, vane, pocket penetrometer), the shear
box (soil and rock joints), and the intact Hoek–Brown fit. It splits in three, data before analysis (decision 1).
This unit is the data: two datasets, `p.undrained_strength()` (stage A of sheet 05, with the s_u each test gives)
and `p.shear_box()` (stage A of sheets 04 for the shear box, and 22).

**Goal:**
- `p.undrained_strength()` (or `ht.template("strength")` for CSV): one row per test result from UU, unconfined
  compression, field and laboratory vane, hand penetrometer and fall cone, with its s_u, its remolded s_u and
  sensitivity where the test gives them, the test that produced it and the depth rule used. The rows go straight
  onto P01 and P07 and into `ht.stats.describe()`, which keep the tests apart because `test_type` is a source
  (SPEC §5).
- `p.shear_box()` (or `ht.template("shear_box")`): one row per shear box stage, soil and rock joint tests alike,
  with the normal stress, the peak and residual shear stress, the displacements and the lab's own c′ and φ′, ready
  for (b)'s fit.

**Why:**
- **Sheet 05 has nothing measured.** It is at C only (SPT, M13 b2), so the Stroud and Sowers estimates on P01 and
  P07 have no measured s_u beside them, and selection (M18) has no total-stress strength to work from. UU stages are
  in `p.triaxial()` (M11 a), but as deviator stress at failure, not as s_u, and the other five tests aren't read.
- **Sheets 04 and 22 have no shear box data.** 04 is part built from triaxial tests only; 22 has nothing, and (b)'s
  fit has no input without this unit.
- **One unit for both datasets** (decision 1): both are lab groups read by specimen depth, so one pass through
  `docs/data/datasets.md`, `qc.md` and the registry, and one regeneration of `site.ags` and the tests that pin its
  QC findings, rather than two. M14 (a) built two datasets in one unit the same way.

**Evidence** (AGS 4.2, read from python-ags4's copy of the dictionary, 2026-11-01):
- **Undrained strength:**
  - `TRIT_CU` and `TRET_CU`: "Undrained shear strength at failure" (kPa), beside `TRIT_DEVF`;
  - `LUCT_UCS`: "Unconfined compressive strength" (kPa), so s_u = q_u / 2, never `LUCT_UCS` itself;
  - `IVAN_IVAN`, `IVAN_IVAR` (field vane, peak and remolded), `LVAN_VNPK`, `LVAN_VNRM` (laboratory vane),
    `LFCN_FCPK`, `LFCN_FCRM` (fall cone): strengths, kPa;
  - `LPEN_PPEN`: "Hand penetrometer undrained shear strength" (kPa), so s_u by definition;
  - `IPEN_IPEN`: "Hand penetrometer result" (kPa, example "6.8 or >20"), which doesn't say whether it is s_u or
    q_u. Sheet 05 §5.3 and §7: the instruments are scaled in either, a factor of 2 apart;
  - the type codes mix tests that differ: `IVAN_TYPE` is BOREHOLE, CPT, FIELD (hand-held) or TORVANE; `LVAN_TYPE`
    HV, LV or TV; `TRIG_TYPE` UU or UUM. A borehole vane and a torvane in one `IVAN` group are not the same test.
- **Shear box:**
  - `SHBT_TESN` is the "Shear box stage/specimen reference", so the file doesn't say whether a set of rows is
    three stages on one specimen or three specimens;
  - three normal stresses: `SHBT_NORM` ("applied"), `SHBT_PVST` ("at peak") and `SHBT_RVST` ("at residual"), which
    the dictionary's examples give as 100, 100 and 125;
  - nothing marks a rock joint test: `SHBG_TYPE`'s codes are SMALL and LARGE SBOX and SMALL and LARGE RSHEAR (ring
    shear), and only `SHBT_DIA1`/`DIA2` ("rock joints") and `SHBG_ENCA` (encapsulation) suggest one;
  - `SHBG_PCOH`, `SHBG_PHI`, `SHBG_RCOH`, `SHBG_RPHI`: the lab's peak and residual fit; `SHBT_CRIT`: the criterion
    used; `SHBT_PDEN` can be assumed (`#`).
- **The registry is unchecked here:** `undrained_shear_strength` lists `TRIT.TRIT_CU`, `IVAN.IVAN_IVAN` and
  `LVAN.LVAN_VNPK` "to verify against the 4.2 dictionary", and the `strength` template predates the rule that a
  template is its dataset's columns (SPEC §2.6).

**Scope:**
- **`p.undrained_strength()`** (`docs/data/datasets.md` §6.11, new): one row per test result from `TRIT` (UU and
  UUM stages, through `p.triaxial()`'s rows), `LUCT`, `IVAN`, `LVAN`, `LPEN`, `IPEN` and `LFCN`, with
  `undrained_shear_strength`, the remolded s_u and sensitivity where given, `test_type`, `source`, `qualifier`
  (`>20`), the depth and `depth_basis` (SPEC §8.2), the geology columns and the common filters (§10.2).
  - **s_u from the test** (the stage B that is a definition): q_f / 2 for UU, q_u / 2 for unconfined compression,
    as reported for the vanes, the fall cone and `LPEN`. The lab's `TRIT_CU` is kept beside hangtu's q_f / 2 as a
    `reported_` column, not used in its place (as M11 (a) kept the lab's c′ and φ′).
- **`p.shear_box()`** (§6.12, new): one row per `SHBT` stage with its `SHBG` test: the three normal stresses, peak
  and residual shear stress, displacements and dilation, rates, reversals, specimen size, density and water
  content, `failure_criterion`, `test_stage`, the lab's peak and residual c and φ as `reported_` columns, and the
  test type, condition and encapsulation as written.
- **QC** (`docs/data/qc.md`, new sections):
  - undrained: `TRIT_CU` against `TRIT_DEVF / 2`; remolded above peak; a sensitivity below 1;
  - shear box: residual above peak; a stage with neither shear stress; `SHBT_PVST` or `SHBT_RVST` far from
    `SHBT_NORM`, if a threshold can be justified (spec step).
- **Templates:** `strength` reshaped to `p.undrained_strength()`'s columns, and `shear_box` new, so CSV and AGS
  data reach the plots and (b)'s fit in the same shape (SPEC §2.6).
- **The example file** (`site.ags`) gains some of these groups, drawn on pages 04 and 05.
- **Site pages:** 05 gains the tests as stage A and q / 2 as stage B; 04 the shear box as a stage A source; sheet
  22 is promoted to a page (the wave rule, `docs/reference/process.md`), with its stage A.

**Constraints:**
- SPEC §7, "only what the file says": s_u = q / 2 is computed in the dataset, never stored; the lab's own values
  are kept as reported.
- SPEC §2.6 and §4: never guess. Whether `IPEN_IPEN` is s_u or q_u (decision 4), whether shear box rows are stages
  of one specimen, and whether a test is of a rock joint (decision 9) aren't guessed.
- SPEC §5: `test_type` and `source` keep tests apart in the statistics; nothing here pools them.
- SPEC §6.2, blank vs flagged: `>20` is a bound with a flag, not 20 and not blank; an assumed `SHBT_PDEN` keeps
  its `#` flag (M14 a).
- SPEC §8.2: lab tests by specimen depth, then sample; field vane and hand penetrometer at their test depth.
- `docs/reference/process.md`: data, then analysis. The Bjerrum correction, conversions between tests and the shear
  box fit are analyses.

**SPEC and TODO touched:**
- SPEC:
  - §12.4, M17 in three units (decision 1, in this commit), and `CLAUDE.md`'s "Next" sentence with it;
  - §4 and §5, the lines naming "M17's fits (φu = 0, shear box, Hoek–Brown)", if decision 2 holds (spec step);
  - §8.2, the depth rows for field vane and hand penetrometer (spec step);
  - §10.2, both datasets in the list; §2.6, the `strength` and `shear_box` templates (close-out).
- Other docs: `docs/data/datasets.md` §6.11 and §6.12, `docs/data/qc.md`, `columns.yaml`, site pages 04, 05 and 22
  (new), the parameter index (04 A, 05 A and B, 22 A), `docs/site/guides/datasets.md`.
- TODO: none closed. A new item if the Bjerrum μ is deferred with an unverified source (decision 5).

### Decisions (intent review, 2026-11-01)
Accepted as proposed. Where a decision left a choice open (4: argument, judgment or file data; 8: whether stages
under one specimen fill `multistage_test`), the spec step settles it.

**The milestone**
1. **M17 splits in three, data before analysis** (`docs/reference/process.md`):
   - **(a) the data** (this unit): `p.undrained_strength()` with s_u = q / 2 and sensitivity, and `p.shear_box()`.
   - **(b) shear box fit:** τ on σ′n through `_line_fit`, free or through the origin, peak and residual, as a
     derived result beside `MohrCoulombFit`; whether P11 draws it is (b)'s question. Stage B of 04 and 22.
   - **(c) intact Hoek–Brown fit:** (σ1 − σ3)² on σ3 through `_line_fit`, free or with σci fixed (sheet 15
     §5.2–5.3, Hoek 2007 eqs. 6–9 [V]), from a CSV of rock triaxial results with its own template: AGS 4.2 has no
     rock triaxial group, and user-defined groups are wave 0 (SPEC §1.3). Stage B of 15 (and its CSV stage A).

   The two datasets share their plumbing but not their decisions, so the spec writes each as its own section and
   the build gives each its own commits. If the spec runs past one sitting, it can split there into (a1) and (a2)
   without changing this intent much. The undrained analysis stays in (a) because it is a definition (q / 2),
   which the dataset computes as it computes N60 and the classifications (SPEC §7). The two fits stay apart:
   Hoek–Brown brings its own template and validity rules (0 < σ3 < 0.5 σci, at least 5 points).

**Undrained strength**

2. **No φu = 0 fit of its own.** s_u per specimen is q_f / 2, so a UU set's φu = 0 strength is the mean of its
   specimens: `ht.stats.describe(p.undrained_strength(), value="undrained_shear_strength", by=...)`. Whether a set
   behaves as φu = 0 is the slope of `mohr_coulomb_fit(stress="total")`, which exists. A fit with the slope fixed
   at 0 would add a fixed-slope mode to the core to reproduce a mean. SPEC §4 and §5's "M17's fits (φu = 0, …)"
   would then read "M17's fits (shear box, Hoek–Brown)".
3. **One row per test result, the tests side by side, not one row per depth.** A UU specimen, a vane test and a
   hand penetrometer reading at the same depth are three rows with three `test_type`s, as the tests differ (sheet
   05 §1). The type code is kept, so a borehole vane and a torvane aren't one `test_type`. `source` names the AGS
   group. Nothing is combined or converted between tests.
4. **`IPEN_IPEN` needs the engineer to say what it is.** A required argument when the file has `IPEN` rows
   (`hand_penetrometer_reading="undrained_shear_strength"` or `"unconfined_compressive_strength"`, names to check),
   with no default, recorded on the rows; without it the `IPEN` rows are left out and counted, with a warning naming
   the argument, so the other tests still come back. Whether this is an argument, a judgment (SPEC §4, keyed by
   instrument or by file) or data the file should carry (TODO #45) is for review. `LPEN_PPEN` is s_u by its
   definition and needs nothing.
5. **The field vane's Bjerrum μ is out of this unit.** It is a judgment (SPEC §4 lists it) applied to one test's
   values, so it is an analysis; and sheet 05 §5.2 has μ = 1.7 − 0.54 log PI as [U]. The field vane is reported
   uncorrected, labeled so; the correction waits for selection (M18), which compares tests.
6. **`TRET_CU` (CU stages) is left out.** It is s_u at the consolidation stress, the SHANSEP input (sheet 05 §4),
   which is wave 3 (M20); beside UU and vane values it would invite pooling a different quantity. It stays readable
   through `p.triaxial()`.

**Shear box**

7. **All three normal stresses are kept; the dataset picks none.** `SHBT_NORM`, `SHBT_PVST` and `SHBT_RVST` are
   columns of their own. Which one a peak or residual point is plotted against is (b)'s decision, recorded on the
   fit as `effective_stress_basis` is on `triaxial_failure_stresses()`'s rows.
8. **Stages are rows, and multistage isn't inferred.** `SHBT_TESN` becomes `test_stage`. `multistage_test` is
   blank unless the file says (the dictionary's "stage/specimen reference" allows either reading). Several
   `SHBT_TESN` under one `SPEC_REF` is the likely reading of "stages on one specimen", but it is a reading, so it
   is for review whether it fills `multistage_test` or only a QC note.
9. **Soil and rock joint tests aren't told apart by hangtu.** No heading says which a test is (evidence above).
   The dataset carries `SHBG_TYPE`, `SHBG_ENCA` and `SHBT_DIA1`/`DIA2` as written, so the engineer can tell them
   apart (`where=` or `geology=`) and (b)'s fit groups by what they choose. Inferring "rock joint" from an
   encapsulation or a diameter was rejected: the dictionary suggests them for rock joints but makes neither a
   marker, and a blank one says nothing.
10. **Shear box stresses are reported as the lab gives them, without an effective or total label.** A shear box
    measures no pore pressure; the stresses are effective only if the test was drained (sheet 04 §5.2), which the
    rate shows but doesn't prove. The columns are named for what they are (normal stress, peak shear stress), and
    (b) decides how its fit's result names c′ and φ′.

### Open (for the spec step)
- **Names**, checked against the whole registry: the remolded s_u, sensitivity (`sensitivity` alone could be
  misread), the lab's s_u (`reported_undrained_shear_strength`), the hand penetrometer argument;
  `unconfined_compressive_strength` (soil q_u) against rock's uniaxial compressive strength (σci, wave 4), since
  "UCS" is both; the shear box columns (normal stress at peak and at residual, peak and residual shear stress,
  horizontal and vertical displacement at each), and the lab's peak and residual c and φ, whose
  `reported_effective_…` names exist for triaxial tests but may not suit a rock joint's c_j and φ_j.
- **`test_type` values:** the AGS codes where the group has them, or hangtu's names per test with the code kept
  beside it; what `LUCT_TYPE` ("UNDISTURBED", its only code) means for the row; and how ring shear (`RSHEAR`) and
  shear box (`SBOX`) are told apart in `p.shear_box()`.
- **Fall cone:** sheet 05 lists it as an index test; the milestone row doesn't. Proposed in, since it is one more
  group of the same shape; out if the review prefers the row as written.
- **Multistage UU (`UUM`):** each stage as a row, flagged with `multistage_test`, as `p.triaxial()` does.
- **QC thresholds:** whether `SHBT_PVST` far from `SHBT_NORM` and a residual with small displacement (sheet 22 §7:
  "residual needs several mm") have a threshold a source supports, or are left out.
- **The example file:** which groups, in which units, with values hand-worked in the generator's comments; a rock
  joint test in it or not.
- **The depth rows** for `IVAN_DPTH` and `IPEN_DPTH` in §8.2 (`test_depth`, as `IDEN`).

### Out of scope
- **M17 (b) and (c):** the shear box fit, with peak and residual, the choice of normal stress and through-origin
  fits; the Hoek–Brown fit and its template.
- **M18:** the Bjerrum correction (decision 5), mode and rate factors between tests (sheet 05 §5.7), the direct
  shear to triaxial conversion (sheet 04 §5.2), characteristic values and design lines, the Mohr–Coulomb set.
- **M20:** `TRET_CU` and SHANSEP (decision 6).
- **Wave 0 (M16):** shear box displacement curves and rock triaxial results from user-defined groups.
- **Wave 4:** Barton–Bandis, scale corrections and JRC/JCS (sheet 22 §5.4–5.5); rock UCS (`RUCS`).
- **Later:** CPT s_u (Nkt), direct simple shear (no AGS 4.2 group).

## Spec
The rules live in the topic docs: the datasets in `docs/data/datasets.md` §6.11 and §6.12, the QC rules in
`docs/data/qc.md` §4.13 and §4.14. This section lists what changes where, the decisions behind it (the intent's
decisions settled, with the open points of the intent decided) and the acceptance criteria.

### Changes
- **`docs/data/datasets.md`:** §6.11 `p.undrained_strength()` and §6.12 `p.shear_box()` (new); §1, §2, §8, §11
  and §12 updated for them.
- **`docs/data/qc.md`:** §4.13 undrained strength rules Q001–Q003 and §4.14 shear box rules H001–H003 (new); §4.10's
  minimum fields gain `LUCT`, `IVAN`, `LVAN`, `LPEN`, `IPEN`, `LFCN`, `SHBG` and `SHBT`; §8 has the defects cases.
- **`ht.analysis.undrained_shear_strength_from_tests()`** (new, decision 3), with its reference entry.
- **SPEC, in this commit:** §4 and §5, "M17's fits (φu = 0, shear box, Hoek–Brown)" becomes "M17's fits (shear
  box, Hoek–Brown)" (intent decision 2); §5's "Flags come from the registry" gains the rule of decision 9; §8.2
  gains the row for `IVAN` and `IPEN`. **At close-out:** §2.6, the `strength` and `shear_box` templates; §10.2, the
  two datasets; §4, a line for `undrained_shear_strength_from_tests()`.
- **Registry** (each name checked against the whole registry and every spec, 2026-11-01; decision 12):
  - new columns: `undrained_shear_strength_basis`, `remolded_undrained_shear_strength`, `remolded_qualifier`,
    `strength_sensitivity`, `reported_undrained_shear_strength`, `unconfined_compressive_strength`,
    `hand_penetrometer_reading`, `applied_normal_stress`, `normal_stress_at_peak`, `normal_stress_at_residual`,
    `peak_shear_stress`, `residual_shear_stress`, `horizontal_displacement_at_peak`,
    `horizontal_displacement_at_residual`, `vertical_displacement_at_peak`, `vertical_displacement_at_residual`,
    `peak_displacement_rate`, `residual_displacement_rate`, `shear_traverses`, `specimen_height`,
    `specimen_diameter_along_shear`, `specimen_diameter_across_shear`, `encapsulation`, `final_water_content`,
    `reported_peak_cohesion`, `reported_peak_friction_angle`, `reported_residual_cohesion`,
    `reported_residual_friction_angle`;
  - changed: `undrained_shear_strength` (its sources: q / 2, `IVAN_IVAN`, `LVAN_VNPK`, `LPEN_PPEN`, `LFCN_FCPK`;
    `TRIT_CU` moves to `reported_undrained_shear_strength`); `axial_strain_at_failure` (UU and unconfined
    compression, `LUCT_STRA`); new AGS sources for `test_type`, `sample_condition` (`LUCT_TYPE`, `SHBG_COND`),
    `test_stage`, `failure_criterion` (`SHBT_CRIT`), `water_content`, `bulk_unit_weight`, `dry_unit_weight`,
    `particle_density`, `particle_density_assumed`, `void_ratio`, `test_remarks` and `remarks`;
  - a quantity kind `displacement_rate` (decision 13);
  - the `strength` template reshaped and `shear_box` new (decision 14).
- **Test files:** the undrained and shear box groups in `site_si.ags`, `site_us.ags` and `site_v404.ags`
  (datasets.md §12); the edge cases in `joins.ags`; the Q and H cases in `qc_defects.ags`.
- **Example file:** `site.ags` gains `TRIG`/`TRIT` (UU), `IVAN`, `LVAN` and `LPEN`, drawn on page 05. The shear box
  groups wait for (b), whose page draws them (as M11 a left the triaxial groups to (b)).
- **Docs site:** both datasets in the datasets guide's table and the reference; the Q and H rules where the AGS
  and QC guide lists rules; page 05's tests and its "q / 2" method row linked to the function; page 04's shear box
  row; **page 22 promoted** from its sheet (decision 15).

### Decisions
**Undrained strength**
1. **One row per test result**, in group order `TRIT`, `LUCT`, `LVAN`, `LPEN`, `LFCN` (lab), then `IVAN`, `IPEN`
   (field), each in file order, with the columns of §6.11. `source` is `lab` or `field`, as in `p.density()` and
   `p.permeability()`.
2. **`test_type` is never blank, so tests never pool by accident.** It is the file's type code where the group has
   one and it is filled (`TRIG_TYPE`, `IVAN_TYPE`, `LVAN_TYPE`), as every other dataset; else a name for the
   group: `"unconfined compression"`, `"hand penetrometer"`, `"fall cone"`, and for a blank code
   `"total stress triaxial, type not given"`, `"in situ vane, type not given"`, `"laboratory vane, type not
   given"`. A blank `test_type` would pool a vane of unknown type with a fall cone in `describe()`. `LUCT_TYPE`
   (whose only dictionary code is `UNDISTURBED`) is a specimen condition, so it goes to `sample_condition`.
3. **s_u comes from `ht.analysis.undrained_shear_strength_from_tests(df, *, hand_penetrometer_scale=None)`**, which
   the dataset calls, so CSV and AGS rows follow the same rules (as `p.triaxial()` calls
   `triaxial_failure_stresses()`). Per row, from the one input it has:

   | Input on the row | s_u | `undrained_shear_strength_basis` |
   |---|---|---|
   | `deviator_stress_at_failure` (UU) | q_f / 2 | `half_deviator_stress` |
   | `unconfined_compressive_strength` | q_u / 2 | `half_unconfined_compressive_strength` |
   | `hand_penetrometer_reading`, scale `"unconfined_compressive_strength"` | reading / 2 | `half_hand_penetrometer_reading` |
   | `hand_penetrometer_reading`, scale `"undrained_shear_strength"` | reading | `hand_penetrometer_reading` |
   | `undrained_shear_strength` only (vanes, fall cone, `LPEN`) | as given | `as_reported` |

   - A row with two of these inputs is an error naming the rows (a CSV that typed the lab's s_u beside q_f puts it
     in `reported_undrained_shear_strength`).
   - For CSV input the analysis errors where the dataset blanks: q ≤ 0 (naming the rows), a hand penetrometer
     reading without `hand_penetrometer_scale=`, stresses of different dimensions. The dataset blanks or leaves
     out instead, with a warning, since a dataset doesn't stop on the file's data (§6.10's rule).
   - **Units:** each stress column resolves as SPEC §2.6; s_u comes back in `undrained_shear_strength`'s unit
     where declared, else in the unit of the first input column the frame has, in the table's order.
   - It returns a copy with `undrained_shear_strength`, its basis and `strength_sensitivity` filled.
4. **`hand_penetrometer_scale=` is an argument** of the dataset and the analysis, with no default (intent decision
   4 settled). It states what the instrument read, which is a fact about the investigation, not about the ground,
   so it is neither a judgment (SPEC §4 keys judgments by geology unit, hole or depth) nor guessed. With `IPEN`
   rows and no argument, the dataset leaves them out and counts them in one warning that names the argument and
   points to `IPEN_METH` and `IPEN_REM`; the other tests still come back. The basis column records it on every
   row. `LPEN_PPEN` is s_u by the dictionary's definition and takes no argument. TODO #45 (file-carried values)
   stays open; this doesn't need it.
5. **The lab's s_u is kept, not used.** `TRIT_CU` is `reported_undrained_shear_strength` on the UU rows, beside
   hangtu's q_f / 2; QC Q001 compares them. Where a test's only result is s_u (vanes, fall cone, `LPEN`), that value
   is the measurement and goes in `undrained_shear_strength`. The line between the two columns is "could hangtu
   compute it from the row": the same line M11 (a) drew for the lab's c′ and φ′.
6. **Sensitivity is `strength_sensitivity` = s_u / s_u,r**, from one test's peak and remolded values (field vane,
   laboratory vane, fall cone), both unflagged, with s_u,r > 0. A flagged value on either side, or s_u,r = 0,
   gives a blank, counted in one warning ("sensitivity left blank on 2 rows: a value beyond the instrument's
   range"); both values stay on the row. The name: `sensitivity` alone is used across the docs for a model's
   sensitivity to a parameter (sheet 05 §6), so it would be misread.
7. **Field vane values are uncorrected** (intent decision 5): `undrained_shear_strength_basis` is `as_reported` and
   the docstring and §6.11 say Bjerrum's μ isn't applied. `TRET_CU` isn't read (intent decision 6).
8. **UU rows come through `p.triaxial()`'s build**, so their depths, geology and stage columns are the same as
   there; `multistage_test` follows §6.10 (`UUM`, or several stages on one specimen). Every UU stage is a row.

**Flags**

9. **A second flag column for a second value on the row.** A vane gives two values, so its row has `qualifier` (for
   s_u) and `remolded_qualifier` (for s_u,r), both `"<"`, `">"` or blank. The registry gives
   `remolded_qualifier` the qualifier role with `values: [remolded_undrained_shear_strength]`, and a rule is added
   to the statistics' flag reading: **a value named in a qualifier column's `values:` reads only the qualifier
   columns that name it**, so `qualifier`, which names none, no longer applies to the remolded value. Other roles
   (`at_least`, `non_plastic`, `assumed`) are untouched, and no current qualifier column has `values:`, so nothing
   else changes. SPEC §5, "Flags come from the registry", gains the
   rule. Rejected: giving `qualifier` a `values:` list of every column it qualifies, which a new dataset would
   have to remember to extend.
10. **A hand penetrometer value beyond its range** (`>20`) is a bound with `qualifier = ">"` (SPEC §6.2). With the
    `unconfined_compressive_strength` scale, `>200` gives s_u > 100.

**Shear box**

11. **One row per `SHBT` stage**, in file order, with its `SHBG` test's values on each (§6.12). The decisions of
    the intent hold as written:
    - all three normal stresses are columns, and the dataset picks none (intent decision 7);
    - **no `multistage_test` column** (intent decision 8 settled): `SHBT_TESN` is a "stage/specimen reference", and
      a soil test's three specimens are commonly entered as three `SHBT_TESN` under one `SPEC_REF`, so several
      rows on one specimen isn't evidence of a multistage test either. A column that could only ever be blank
      would read as an answer. (b)'s fit, like `mohr_coulomb_fit()`, notes that stages weren't told apart, and
      reads the column when a user adds it;
    - no soil or rock joint label (intent decision 9); `test_type` is `SHBG_TYPE` as written, so shear box and
      ring shear stay apart (`SMALL SBOX`, `LARGE RSHEAR`);
    - no effective or total label on the stresses (intent decision 10).
12. **Names.** Checked against the registry and every spec (2026-11-01). Points that shaped them:
    - `applied_normal_stress`, not `normal_stress`: the M11 (b) fit's points already have `normal_stress` and
      `shear_stress`, the fitted tangent point, and the shear box rows will go through a fit beside them;
    - `peak_shear_stress` and `residual_shear_stress`, with `normal_stress_at_peak` and `normal_stress_at_residual`
      (`SHBT_PVST`, `SHBT_RVST`), so each pair reads as one point;
    - `reported_peak_cohesion` and so on, not `reported_effective_…`: the lab's shear box fit isn't labeled effective
      (decision 11), and a rock joint's c_j, φ_j aren't c′, φ′ of a soil;
    - `unconfined_compressive_strength` (soil q_u, ASTM D2166's term) and, in wave 4, `uniaxial_compressive_strength`
      (rock σci, D7012's term): both are "UCS", written out they aren't, and each label names its material;
    - existing names where the quantity is the same (`void_ratio` for `SHBT_IVR`, initial as for `TRET_IVR`;
      `water_content` for the initial `SHBT_MCI`; `particle_density` for `SHBT_PDEN`, with its `#` flag;
      `axial_strain_at_failure` for `LUCT_STRA`); `final_water_content` for `SHBT_MCF`;
    - `shear_traverses` (`SHBT_REVS`, the dictionary's "number of traverses"), `specimen_diameter_along_shear` and
      `specimen_diameter_across_shear` (`SHBT_DIA1`, `DIA2`), `specimen_height`, `encapsulation`.
13. **A quantity kind `displacement_rate`** (canonical mm/min; SI mm/min, US in/min), for `SHBT_DISP` and
    `SHBT_DISR`. `velocity` (m/s, ft/s) would show 0.024 mm/min as 4.0e-7 m/s. It comes after `velocity` in
    `defaults.yaml`, so ingest, which takes a unit's first matching kind, keeps assigning `velocity` to m/s headings;
    the dataset converts by the column's kind.

**Both**

14. **Templates:** `strength` is `p.undrained_strength()`'s columns without `source_line`,
    `undrained_shear_strength_basis` and `strength_sensitivity` (the analysis adds them); `shear_box` is
    `p.shear_box()`'s without `source_line`. The `strength` template gains columns; the P01 and P07 fixtures that
    use a few of them still work, since a frame needn't have every template column.
15. **Page 22 is promoted** from its sheet: what it is, units, typical values (Hoek 2023 ch. 4, Table 1, values
    quoted with the locator, after Barton 1974), tests (D5607 noted as withdrawn in 2025, the ISRM method), and
    methods with the shear box fit as M17 (b) and Patton, Barton–Choubey and the scale corrections as wave 4, each
    cited through Hoek 2023 ch. 4 [V]; the originals stay [U] and aren't cited as read. Stage A: `p.shear_box()`.
16. **QC (level 1):**
    - Q001 `TRIT_CU` differs from `TRIT_DEVF` / 2 (warning; `undrained_strength_tolerance: 1 kPa`: both 0DP in kPa,
      so rounding is at most 0.25 + 0.5 = 0.75 kPa);
    - Q002 a remolded value above its peak (`IVAN_IVAR`, `LVAN_VNRM`, `LFCN_FCRM`) (warning);
    - Q003 a strength of 0 or less (`LUCT_UCS`, `IVAN_IVAN`, `LVAN_VNPK`, `LPEN_PPEN`, `IPEN_IPEN`, `LFCN_FCPK`) (error);
    - H001 `SHBT_RES` above `SHBT_PEAK` (error: the peak is the largest shear stress of the stage);
    - H002 a stage with neither `SHBT_PEAK` nor `SHBT_RES` (warning);
    - H003 `SHBT_NORM` of 0 or less (error).
    - **Not rules**, for want of a threshold a source supports: `SHBT_PVST` or `SHBT_RVST` far from `SHBT_NORM`
      (they differ legitimately when the lab corrects for the contact area; the dictionary's example is 100, 100 and
      125) and a residual reached at a small displacement.
    - **Minimum fields:** `LUCT`: `LUCT_UCS` required, `LUCT_STRA` recommended; `IVAN`: `LOCA_ID`, `IVAN_DPTH`,
      `IVAN_IVAN` required, `IVAN_TYPE`, `IVAN_IVAR` recommended; `LVAN`: `LVAN_VNPK` required, `LVAN_TYPE`,
      `LVAN_VNRM` recommended; `LPEN`: `LPEN_PPEN`; `IPEN`: `LOCA_ID`, `IPEN_DPTH`, `IPEN_IPEN`; `LFCN`: `LFCN_FCPK`
      required, `LFCN_FCRM` recommended; `SHBG`: `SHBG_TYPE`, `SHBG_COND` recommended; `SHBT`: `SHBT_TESN`,
      `SHBT_NORM` required, `SHBT_PEAK`, `SHBT_RES`, `SHBT_DISP` recommended; lab groups with the sample key, as §4.10.
    - The letters: `Q` for undrained strength (`TRIG_TYPE`'s "quick undrained"), `H` for the shear box; `U` (units)
      and `S` (SPT) are taken.
17. **Depth:** lab tests by the §6.2 rule; `IVAN_DPTH` and `IPEN_DPTH` as test depths (`test_depth`, as `IDEN`).
    SPEC §8.2 gains the row.

### Sources
- **AGS 4.2 dictionary** (python-ags4 1.2.0, `Standard_dictionary_v4_2.ags`), checked 2026-11-01: the headings,
  units and descriptions quoted in the intent's evidence; the pick lists `TRIG_TYPE`, `IVAN_TYPE`, `LVAN_TYPE`,
  `LUCT_TYPE` and `SHBG_TYPE`.
- **s_u = q / 2** is derived, not cited. With φu = 0 the total-stress envelope is the horizontal line τ = s_u. It
  touches a Mohr circle of center s and radius t = (σ1 − σ3)/2 at its top, so s_u = t = q / 2 for any cell
  pressure; unconfined compression is the case σ3 = 0, so s_u = q_u / 2.
- **Sensitivity**, S_t = s_u / s_u,r: the definition (page 05's header). No coefficient.
- **Hoek, E. (2023)**, *Practical Rock Engineering*, ch. 4, "Shear strength of discontinuities", Rocscience: eqs.
  1–8 (pp. 2, 5, 6), p. 10, Table 1 (p. 11, after Barton 1974), Fig. 8 (p. 12). [V] in sheet 22; page 22 quotes
  only what the sheet marks [V], and nothing of this unit's code depends on it.
- **ASTM D5607-16**: withdrawn in 2025 with no replacement ([V] status, sheet 22 [4]).
- **Standard gravity and the US units** are exact by definition (P00 §4): 1 psf = 47.880259 Pa.

### Acceptance criteria
Golden values hand-calculated from the test files' values; 1 psf = 0.047880259 kPa. Tolerance 1e-9 relative unless
a criterion says otherwise.
1. **UU (`site_si.ags`, BH1-U4):** deviator 120, 124, 118 kPa give s_u 60, 62, 59 kPa, basis `half_deviator_stress`,
   `test_type` UU, `source` lab, `cell_pressure` 100, 200, 300, and `reported_undrained_shear_strength` 60, 62, 59
   (`TRIT_CU`, new in the file). The depths and geology are `p.triaxial()`'s for the same stages.
2. **Unconfined compression (BH1-U1):** `LUCT_UCS` 96 kPa gives s_u 48 kPa, basis
   `half_unconfined_compressive_strength`, `test_type` "unconfined compression", `sample_condition` UNDISTURBED.
3. **Vanes and fall cone:** field vane BH2 at 3.00 m (`BOREHOLE`) 42 and 14 kPa gives `strength_sensitivity` 3.0,
   depth 3.00 with `depth_basis` `test_depth`, source field; at 6.00 m 55 and 22 kPa gives 2.5; laboratory vane on
   BH2-U2 (`LV`) 38 and 12 kPa gives 3.1666667 (1e-7); fall cone on BH1-U3, 30 and 9 kPa, gives 3.3333333 (1e-7);
   each `as_reported`.
4. **Hand penetrometer:** `LPEN_PPEN` 45 kPa on BH1-U1 is s_u 45, `as_reported`. `IPEN` in BH3 at 0.50 and 0.80 m,
   150 and `>200` kPa: with no `hand_penetrometer_scale=`, both rows are left out with the warning naming the
   argument, and the other rows come back; with `"unconfined_compressive_strength"`, s_u 75 and 100 with
   `qualifier` ">" on the second, basis `half_hand_penetrometer_reading`; with `"undrained_shear_strength"`, 150 and
   200 with ">".
5. **US display:** s_u 60 kPa reads 1253.1261 psf and 48 kPa 1002.5008 psf (1e-6 relative, the precision of the
   hand calculation); sensitivity is unchanged.
6. **Twins:** `site_si.ags` and `site_us.ags` give equal `p.undrained_strength()` and `p.shear_box()` (1e-9
   relative) for each `display_units`, and no Q or H finding.
7. **Never pooled by accident:** `ht.stats.describe(p.undrained_strength(), value="undrained_shear_strength")` raises
   naming each `test_type` and `source` and its count; with `by="test_type"` it runs, one group per test.
8. **Flags (`joins.ags`):** a field vane with `IVAN_IVAN` `>120` and `IVAN_IVAR` 30 has `qualifier` ">",
   `remolded_qualifier` blank and a blank sensitivity, with the warning; `describe()` of
   `remolded_undrained_shear_strength` counts it as a plain value, and of `undrained_shear_strength` as censored.
   A remolded value of 0 gives a blank sensitivity, counted in the same warning.
9. **Blank types:** an `IVAN` row with `IVAN_TYPE` blank has `test_type` "in situ vane, type not given".
10. **The analysis on a CSV:** on a frame in `ht.template("strength")`'s shape with criterion 1's, 2's and 3's inputs,
    `ht.analysis.undrained_shear_strength_from_tests()` gives the same s_u, basis and sensitivity as the dataset. It
    raises, naming the rows, on a deviator stress of 0, on a row with both `deviator_stress_at_failure` and
    `undrained_shear_strength`, on a hand penetrometer reading without the scale, and on a strength in a length
    unit.
11. **Shear box (`site_si.ags`, BH2-D1, `SMALL SBOX`, `RECOMPACTED`):** three stages at `SHBT_NORM` 50, 100, 200 kPa
    with peak 38, 68, 128 and residual 30, 58, 112 kPa give three rows with `test_stage` "1", "2", "3",
    `applied_normal_stress` and `normal_stress_at_peak` equal, the lab's `SHBG_PCOH` 8 kPa and `SHBG_PHI` 31.0° as
    `reported_peak_cohesion` and `reported_peak_friction_angle` on each, and `SHBT_BDEN` 1.95 Mg/m³ as
    `bulk_unit_weight` 19.1229675 kN/m³. In US display the peak 68 kPa reads 1420.2095 psf (1e-6) and `SHBT_DISP`
    0.024 mm/min reads 0.00094488189 in/min (0.024 / 25.4).
12. **Rock joint and ring shear (`joins.ags`):** a test with `SHBG_ENCA` "Resin", `SHBT_DIA1`/`DIA2` and stresses
    in MPa comes back in display units, with `encapsulation` and both diameters as written and nothing labeling it
    a rock joint; a `SMALL RSHEAR` test with only `SHBT_RES` has a blank peak and is kept.
13. **QC (`qc_defects.ags`):** each Q and H rule raises exactly the findings its case seeds (qc.md §8). Q001's case
    (`TRIT_CU` 70 with `TRIT_DEVF` 120) gives an expected 60 kPa and a difference of 10 kPa in its message; `TRIT_CU`
    61 with the same deviator raises nothing. The tolerance takes a quantity string in psf as well as kPa.
14. **Good files stay clean:** the three good files raise no Q, H or C001 finding; their info findings gain nothing
    but C002 where a recommended heading is blank.
15. **Empty:** a file with none of the undrained groups gives an empty `p.undrained_strength()` with every column and
    the warning "No TRIT, LUCT, LVAN, LPEN, LFCN, IVAN or IPEN group"; with no `SHBT`, an empty `p.shear_box()` and
    "No SHBT group". An `SHBG` with no `SHBT` rows gives no row.
16. **Incomplete:** an `IVAN` row with `IVAN_IVAN` blank is left out with the §7 warning, and kept by
    `include_incomplete=True` with a blank s_u.
17. **Feeds the plots:** `ht.plot.profile(p.undrained_strength(), "undrained_shear_strength", color_by="test_type")`
    and `ht.plot.geology_unit_comparison(p.undrained_strength(), "undrained_shear_strength")` run on the good files
    with no warning beyond "mixes sources" on P07 (SPEC §5).
18. **Templates and registry:** `ht.template("strength")` and `ht.template("shear_box")` are their datasets' columns
    without decision 14's, in the same order (`tests/test_registry.py`); every new column has a description,
    quantity and AGS source.
19. **Common arguments:** `depth=`, `geology=`, `holes=` and `where={"test_type": "UU"}` filter both datasets as §2
    says.
20. **Reference:** `undrained_shear_strength_from_tests` in the API reference, with the docstring checklist of the
    sheets' `TEMPLATE.md`; page 22 builds with `zensical build --clean --strict`.

## Plan
Eight build commits, each with ruff and the touched tests green, and the whole suite in parallel before
each commit. A step past about 300 changed lines (not counting test data or the test-file generators) splits as
noted. One finding from reading the code, built into step 5: ingest stores a heading in mm/min under its first
matching kind, `velocity` (m/s), so `p.shear_box()` converts the rates to `displacement_rate` itself.

**Reused, not rebuilt:**
- **Dataset plumbing:** `Build` (`src/hangtu/datasets/_frame.py`: `rows()` drops incomplete records, `numbers()`,
  `texts()`, `qualifier()`, `flagged()`, `finish()` for geology, filters, display units, empty frames and the
  missing-group warning); `specimens()` and `SPECIMEN_COLUMNS` (`datasets/_lab.py`) for lab depth; the `IDEN`
  pattern in `datasets/_density.py` for field rows at `test_depth`; `STANDARD_GRAVITY` for unit weights.
- **UU rows:** `_stages(build, "TRIT")`, `is_multistage()` and the deviator-≤0 handling of `datasets/_triaxial.py`
  and `analysis/_triaxial.py`, so UU depths, stages and geology match `p.triaxial()` (decision 8).
- **Analysis pattern:** `analysis/_triaxial.py` (`triaxial_failure_stresses()`): `resolve_units`, `check_dimension`,
  `convert` (`hangtu.units`), `numeric_column`, `rows_text` (`_data`), `ColumnError`/`HangtuError`/`warn`.
- **QC:** `qc/_triaxial.py`'s shape (`@rule`, `Finding`, `RuleResult`, `_unflagged`, `_value`, `_where`,
  `SLACK` from `qc/_tests.py`), `rules.yaml` thresholds as quantity strings, `min_fields.yaml` with the
  `<SPEC_KEY>` anchor.
- **Statistics flags:** `read_flags()` in `src/hangtu/stats/_rows.py` (one change, step 1).
- **Test files:** `group()` and the SI/US twin mechanism of `tests/data/ags/_make_files.py`; the example
  generator `tests/data/_make_examples.py`.

### 1. `M17: read a second qualifier on rows with two values`
- `src/hangtu/stats/_rows.py` `read_flags()`: a value named in a qualifier-role column's `values:` reads only those
  qualifier columns (spec decision 9); other roles unchanged.
- `columns.yaml`: `remolded_undrained_shear_strength` (stress, ratio) and `remolded_qualifier` (text,
  `statistics: {role: qualifier, values: [remolded_undrained_shear_strength]}`).
- Tests: `tests/stats/test_flags.py` (or the existing describe-flags test file): a frame with `qualifier` ">" and
  `remolded_qualifier` blank → `describe()` of s_u counts one censored, of the remolded value none; and the reverse
  (AC 8's statistics half). Existing describe/fit tests stay green (no current qualifier has `values:`).

### 2. `M17: add undrained_shear_strength_from_tests()`
- `src/hangtu/analysis/_undrained.py` (new), exported in `analysis/__init__.py`: spec decision 3's table, the
  two-inputs error, q ≤ 0 and missing-scale errors naming rows, units (SPEC §2.6; s_u in the declared unit, else
  the first input's), sensitivity (decision 6) with its blank-and-count warning; returns a copy. Docstring by the
  sheets' `TEMPLATE.md` checklist (the derivation of s_u = q / 2, the basis values, uncorrected field vane).
- `columns.yaml`: `undrained_shear_strength_basis`, `strength_sensitivity`, `reported_undrained_shear_strength`,
  `unconfined_compressive_strength`, `hand_penetrometer_reading`; `undrained_shear_strength`'s sources (TRIT_CU
  out); `axial_strain_at_failure` gains `LUCT_STRA`.
- `docs/site/reference/analysis.md`: the entry (the reference test fails without it).
- Tests: `tests/analysis/test_undrained_strength.py` (new): each table row with hand values (q 120 → 60; q_u 96 →
  48; reading 150 → 75 or 150; vane 42/14 → St 3.0), AC 10's errors, flagged and zero remolded → blank St with the
  warning, units (a frame in psf → psf; a length unit raises).

### 3. `M17: add p.undrained_strength()`
- `src/hangtu/datasets/_undrained.py` (new): the seven groups in spec order (§6.11's tables), `test_type` fallbacks
  (decision 2), `LUCT_TYPE` → `sample_condition`, both qualifiers via `build.qualifier()`, `IPEN` rows left out and
  counted without `hand_penetrometer_scale=` (decision 4), then `undrained_shear_strength_from_tests()`.
- `src/hangtu/project.py`: `Project.undrained_strength()` with the common arguments and the docstring;
  `docs/site/reference/project.md` entry.
- `columns.yaml`: the `strength` template reshaped (decision 14); new AGS sources for `test_type`,
  `sample_condition`, `test_stage`, `water_content`, `bulk_unit_weight`, `dry_unit_weight`, `remarks`.
- Test files (`tests/data/ags/_make_files.py`, regenerated): `TRIT_CU` 60, 62, 59 on BH1-U4; `LUCT` 96 on BH1-U1;
  `LPEN` 45 on BH1-U1; `LVAN` LV 38/12 on BH2-U2; `LFCN` 30/9 on BH1-U3; `IVAN` BOREHOLE 42/14 at BH2 3.00 m and
  55/22 at 6.00 m; `IPEN` 150 and `>200` at BH3 0.50 and 0.80 m; ABBR codes; in `site_si`, `site_us`, `site_v404`
  (with every recommended heading filled, so no new C002). `joins.ags`: `IVAN_IVAN` `>120` with IVAR 30; IVAR 0;
  an `IVAN` with no type; an `IVAN` with `IVAN_IVAN` blank.
- Tests: `tests/datasets/test_undrained_strength.py` (new): AC 1–9, 15 (undrained half), 16, 17, 19;
  `tests/test_registry.py` covers the `strength` template (AC 18's half). Existing tests counting groups in the
  good files (`tests/test_project.py`, ingest acceptance) updated.
- Split if large: (3a) the lab groups, UU and the template; (3b) `IVAN`, `IPEN` and `hand_penetrometer_scale=`.

### 4. `M17: check undrained strength results in QC (Q001–Q003)`
- `src/hangtu/qc/_undrained.py` (new), registered in `qc/__init__.py`; `rules.yaml` Q001 (with
  `undrained_strength_tolerance: 1 kPa`), Q002, Q003; `min_fields.yaml` `LUCT`, `LVAN`, `LPEN`, `LFCN`, `IVAN`,
  `IPEN` (spec decision 16).
- `qc_defects.ags`: `TRIT_CU` 70 with `TRIT_DEVF` 120 (and a 61 that passes, built in the test); `LVAN_VNPK` 20 with
  VNRM 25; `LUCT_UCS` 0.
- Tests: `tests/qc/test_undrained.py` (new): AC 13's Q half (the 60 kPa expected and 10 kPa difference in Q001's
  message; the tolerance in psf); `tests/qc/test_qc_acceptance.py` keeps the good files clean (AC 14's Q half).

### 5. `M17: add p.shear_box()`
- `src/hangtu/config/defaults.yaml`: quantity kind `displacement_rate` after `velocity` (decision 13).
- `columns.yaml`: the shear box columns (spec Changes), `shear_box` template, new AGS sources.
- `src/hangtu/datasets/_shear_box.py` (new): one row per `SHBT` stage with its `SHBG` values (the `TRET`/`TREG`
  join of `_triaxial._stages()`), `SHBT_PDEN` with its `ASSUMED` flag (as `p.particle_density()`), unit weights × g,
  and the rates converted from ingest's m/s (a `velocity` heading) to mm/min before `finish()`.
- `src/hangtu/project.py`: `Project.shear_box()`; reference entry.
- Test files: `SHBG`/`SHBT` on BH2-D1 (SMALL SBOX, RECOMPACTED; NORM 50/100/200, PEAK 38/68/128, RES 30/58/112,
  PVST = NORM, DISP 0.024, BDEN 1.95, PCOH 8, PHI 31.0) in the three good files; in `joins.ags` a rock joint test in
  MPa with `SHBG_ENCA` "Resin" and `SHBT_DIA1`/`DIA2`, and a SMALL RSHEAR test with only `SHBT_RES`.
- Tests: `tests/datasets/test_shear_box.py` (new): AC 6 (twins), 11, 12, 15 (shear box half), 18, 19.

### 6. `M17: check shear box results in QC (H001–H003)`
- `src/hangtu/qc/_shear_box.py` (new); `rules.yaml` H001–H003; `min_fields.yaml` `SHBG`, `SHBT`.
- `qc_defects.ags`: PEAK 50 with RES 60; a stage with both blank; NORM 0.
- Tests: `tests/qc/test_shear_box.py` (new): AC 13's H half; the good files stay clean (AC 14).

### 7. `M17: draw undrained strength on the docs site`
- `tests/data/_make_examples.py`: UU (`TRIG`/`TRIT` with `TRIT_CU`), `IVAN`, `LVAN` and `LPEN` in the example
  project's clay, in psf, each value worked by hand in a comment; regenerate `src/hangtu/examples/data/site.ags`.
  `tests/test_examples.py`'s exact QC findings checked (recommended headings filled, so none new).
- `docs/site/examples/undrained-strength.py` (new): P01 of `p.undrained_strength()` colored by `test_type`, US.
- `docs/site/parameters/05-undrained-shear-strength.md`: the q / 2 method row and the tests linked to
  `undrained_shear_strength_from_tests()` and `p.undrained_strength()`; the figure; the hand penetrometer pitfall
  names `hand_penetrometer_scale=`. Page 04: the shear box row points to `p.shear_box()`. Page 22: stage A linked.
- `docs/site/guides/datasets.md`: both datasets in the table; the AGS and QC guide: Q and H rules.
- Run `docs/prepare_site.py` and `zensical build --clean --strict`.

### 8. `M17: close out (a)`
- SPEC: §2.6 the `strength` and `shear_box` templates; §10.2 both datasets; §4 a line for
  `undrained_shear_strength_from_tests()`; §12.4 M17 status "(a) done; (b) next".
- `docs/data/datasets.md` and `qc.md` status lines to done; the parameter index (04 A part built with the shear
  box, 05 A and B part built, 22 A built); `CLAUDE.md`'s Next sentence; TODO #45 text checked (stays open).
- What a future session would get wrong without being told, written where it will be read (e.g. ingest stores
  mm/min as m/s; a second value on a row needs its own qualifier).
- **Verification:** every AC reported met or not with its test; the whole suite in parallel; ruff check and format
  check; the lowest-versions run (then `git checkout uv.lock`); the strict docs build.
