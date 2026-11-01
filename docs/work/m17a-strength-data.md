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
