# M11 (a): triaxial data

## Intent
M11 is wave 2's first milestone (SPEC §1.3, §12.4). Wave 2 is "one fitting core" for soil strength (sheets 04 and
05), joint strength (22) and the intact Hoek–Brown fit (15). M11 builds that core and its first use, c′ and φ′
from triaxial tests, drawn as P11 (failure envelope) and P12 (shearing curves and stress paths). M17 then reuses
the core for undrained strength, the shear box and the Hoek–Brown fit.

M11 splits in two, data first (decision 2): this unit, (a), is stage A of sheet 04 for triaxial tests, the
stresses at failure read from the file into a dataset. (b) is stage B: the fitting core, `mohr_coulomb_fit()`,
P11 and P12.

**Goal:** from an AGS file or a CSV, an engineer gets each triaxial specimen's or stage's state at failure: the
test type, cell pressure, deviator stress and pore pressure, and from them σ′3 and σ′1 (σ3 and σ1 for total-stress
tests). The values are in registry columns with units, multistage stages and the lab's failure criterion are marked
on each row, and the lab's own c′ and φ′ come with them. They feed P01 and P07 as they are, are what (b) fits, and
are checked by QC rules that catch records that can't give a valid result.

**Why:**
- **Nothing reads strength tests today.** `effective_friction_angle` exists only as an SPT correlation output
  (M13 b1). Sheet 04 is part built at stage C, but stages A and B are empty. So the correlations have nothing
  measured to be compared with on P01 or P07, and selection (M18, starting with the Mohr–Coulomb set) has no
  measured c′ and φ′ to work from. None of the test files or the example file has a triaxial group.
- **The values at failure are in standard groups** (checked against python-ags4 1.2.0's 4.2 dictionary,
  2026-10-31):
  - `TREG`: `TREG_TYPE` (a pick list, CD to CAUE, with multistage CDM and CUM), `TREG_FCR` (the failure
    criterion, free text, example "Maximum deviator stress"), and `TREG_PHI` and `TREG_COH` (the lab's fit);
  - `TRET`, one row per test or stage (`TRET_TESN`): `TRET_CELL`, `TRET_DEVF`, `TRET_PWPF`, `TRET_CONP`,
    `TRET_BACK`, `TRET_BVAL`, `TRET_STV`, `TRET_DRN`;
  - `TRIG` and `TRIT` for total stress (UU: `TRIT_CELL`, `TRIT_DEVF`).

  None of them has readings during shearing. P12's come from a CSV the user shapes (TODO #19), in (b).
- **Sheet 04's pitfalls that belong to the data:**
  - failure criteria and multistage stages mixed in one fit, so each row says which it is;
  - CU without pore pressure can't give φ′;
  - saturation (`TRET_BVAL`) below what the test standard requires;
  - the lab's `TREG_PHI`/`TREG_COH` to recompute and compare.

  Each becomes a column, a QC finding, or a blank that is counted, never dropped.

**Scope:**
- **One dataset** (SPEC §10.2), `p.triaxial()`, from `TREG`/`TRET` and `TRIG`/`TRIT`. It has one row per stage at
  failure, effective-stress and total-stress rows together, told apart by `test_type` (decision 3), and the common
  filters. σ′3 = σ3 − u_f and σ′1 = σ′3 + q_f are computed by the dataset and never stored (SPEC §7), as N60 is.
- **A CSV template** in the dataset's shape (SPEC §2.6), so CSV and AGS data reach (b) in the same shape.
- **Registry names** for the new columns, checked against the whole registry.
- **The groups in the SI/US twin test files**, and a defects case for each new QC rule.
- **Level 1 QC rules** from the pitfalls, among them saturation against the test standard (decision 7).

**SPEC and TODO touched:**
- SPEC:
  - §1.3 and §12.4, the order of work (committed in `eeba488`);
  - §12.4, M11 in two units and the shear box in M17 (decisions 2 and 6, in this commit);
  - §10.2, §10.3 and §2.6 (the dataset, registry names, template);
  - §9 via `docs/data/qc.md` (new rules).
- Other docs: `docs/data/datasets.md`, `docs/data/qc.md`, and the parameter index (04 A).
- TODO: #31 (wave 0's sample dataset, unchanged but now later); #19 (decided, stays).

### Decisions (intent review, 2026-10-31)
1. **Wave 2 comes before wave 0, and M16 moves after M17** (SPEC §1.3, §12.4, `README.md`, `CLAUDE.md`, the
   parameter index; committed separately). Wave 0 is built against a sample dataset of real files (TODO #31) that
   isn't ready. Wave 2 doesn't need it: its values at failure are standard groups, and its readings come from a
   CSV (TODO #19). Once M16 lands, the readings and rock triaxial results can also come from the AGS file.
2. **M11 splits into data (a) and analysis (b)**, following `docs/reference/process.md` ("Stages and waves").
   Splitting off P12 alone was rejected: its input is a CSV, so it doesn't wait on M16, and it shares the fit with
   P11.
3. **One dataset**, with effective-stress and total-stress rows together, told apart by `test_type`.
4. **`TREG_FCR` is read as written and compared exactly** (SPEC §8.3). No mapping to a short list for now; that
   may change once it has been used on real files.
5. **The lab's `TREG_PHI` and `TREG_COH` come back in the dataset**, so (b) can compare them with hangtu's fit.
6. **The shear box (`SHBG`/`SHBT`) goes to M17**, soil and rock joints together, since both are in one group.
7. **Saturation is a QC rule, not a filter or a judgment.** It checks a record against its test standard, not a
   plausible range, so it is level 1. The threshold comes from the standard, verified in the spec step (D4767 is
   thought to require B ≥ 0.95; unverified). The dataset carries the B-value and leaves the choice of specimens
   to (b).
8. **Multistage stages are marked on each row**, from `TREG_TYPE` (CDM, CUM) and `TRET_TESN`. The dataset keeps
   every stage, and (b) decides whether a fit leaves them out.

### Open (for the spec step)
- **Columns:** which `TREG`/`TRET`/`TRIG`/`TRIT` headings come back (initial state such as `TRET_BDEN` and
  `TRET_IVR`, strain at failure, `TRET_CU`, `TRET_E50`), and the names, checked against the whole registry. P11
  and P12 propose `effective_minor_principal_stress`, `deviator_stress` and others.
- **Pore pressure:** σ′3 at failure from `TRET_CELL` − `TRET_PWPF`, or from `TRET_CONP` and the excess pore
  pressure, and what happens when they disagree or one is blank. For CD tests, whether a blank `TRET_PWPF` means
  the back pressure (sheet 04 §5.1) or stays blank. Never guessed: a blank that can't be derived stays blank,
  and is counted.
- **The multistage marker:** a flag, a stage number, or both; how `TRET_TESN` is read when `TREG_TYPE` is blank.
- **The QC rules:** which of the pitfalls are level 1, and their thresholds as quantity strings. Candidates:
  saturation below the standard's B-value; a CU stage without `TRET_PWPF`; σ′3 ≤ 0 at failure; a `TREG` with no
  `TRET` rows, or the reverse.
- **The example file:** whether `ht.examples`' `site.ags` gains triaxial groups here or in (b), with the plot
  pages.
- **Sources:** the B-value threshold and the failure-criterion definitions in ASTM D4767, D7181 and D2850 (and the
  ISO 17892-8/-9 counterparts), checked against the standards.

### Outline of (b), for context
The fitting core (input rules for failure points, a fit result object, grouping, points left out and counted),
`mohr_coulomb_fit()`, P11 `failure_envelope()` and P12 `triaxial_shearing()` with its readings template, the plot
specs promoted from `docs/plots/drafts/`, and sheet 04's site page. Settled for (b) in this review:
- **The fit result is its own object**, not on the statistics base (`_Result`, SPEC §5). Results of derivations
  may need a family of their own, apart from statistics results.
- **A fitted c′ and φ′ is a derived value** (Eurocode 7's measured → derived → representative → design), as an SPT
  correlation estimate is. The result records that, with its method and points. SPEC §5's *property* and
  *parameter* keep their meanings: *parameter* stays for values selected in M18.
- **P12 puts pore pressure (or volumetric strain) on a second y axis, off by default.**

Left for (b)'s intent: what a fit refuses to pool unawares, what M17's fits need from the core, what P11 returns
with several groups, P11's default `space=`, how P12 picks the failure reading, and the sources for the s′–t and
p′–q constructions.

### Out of scope
- Everything in (b) (above).
- **M17:** undrained strength as a parameter (s_u from UU, UCS, vane, pocket penetrometer; `TRET_CU` and
  `TRIT_CU` as s_u), the shear box (decision 6), the intact Hoek–Brown fit.
- **M16:** readings and rock triaxial results from user-defined AGS groups.
- **Later:** anisotropic consolidation and extension tests (`TRET_CVP`, `TRET_CRP`, carried if the spec keeps
  them, but not interpreted); E50 from the curves (wave 5); a reader for lab software exports (TODO #19: none).

## Spec
The rules live in the topic docs: the dataset in `docs/data/datasets.md` §6.10, the QC rules in `docs/data/qc.md`
§4.12. This section lists what changes where, the decisions behind it (agreed in review, 2026-10-31) and the
acceptance criteria. 🔬 marks a value still to verify.

### Changes
- **`docs/data/datasets.md`:** §6.10 `p.triaxial()` (new); §2, §8, §11 and §12 updated for it.
- **`docs/data/qc.md`:** §4.12 triaxial rules X001–X006 (new); §4.10's minimum fields gain `TREG`, `TRET`, `TRIG`
  and `TRIT`; §8 has the defects cases.
- **`ht.analysis.triaxial_failure_stresses()`** (new, decision 4), with its reference entry.
- **SPEC, at close-out:** §2.6, the `triaxial` template; §10.2, the dataset; §4, a line for the failure stresses
  (decision 4), which (b), P11, P12 and M17 all read.
- **Registry:**
  - new columns: `test_stage`, `multistage_test`, `failure_criterion`, `effective_consolidation_stress`,
    `back_pressure`, `pore_pressure_parameter_b`, `cell_pressure`, `deviator_stress_at_failure`,
    `pore_pressure_at_failure`, `axial_strain_at_failure`, `volumetric_strain_at_failure`,
    `minor_principal_stress_at_failure`, `major_principal_stress_at_failure`,
    `effective_minor_principal_stress_at_failure`, `effective_major_principal_stress_at_failure`,
    `effective_stress_basis`, `reported_effective_friction_angle`, `reported_effective_cohesion`, `test_remarks`;
    each checked against the whole registry (none exists, and none collides: decision 2);
  - new AGS sources: `test_type` (`TREG_TYPE`, `TRIG_TYPE`), `sample_condition` (`TREG_COND`, `TRIG_COND`),
    `water_content` (`TRET_IMC`, `TRIT_IMC`), `bulk_unit_weight` and `dry_unit_weight` (`TRET_BDEN`,
    `TRET_DDEN`, `TRIT_BDEN`, `TRIT_DDEN` × g), `void_ratio` (`TRET_IVR`), `remarks` (`TRET_REM`, `TRIT_REM`);
  - the `triaxial` template (decision 11).
- **Test files:** the triaxial groups in `site_si.ags`, `site_us.ags` and `site_v404.ags` (datasets.md §12); the
  edge cases in `joins.ags`; the X cases in `qc_defects.ags`.
- **Docs site:** `p.triaxial()` in the datasets guide's table (`docs/site/guides/datasets.md`) and its reference
  entry; the X rules where the AGS and QC guide lists rules. The example file and a page that draws the data wait
  for (b) (decision 12).
- **TODO:** #53 (new), the triaxial standards.

### Decisions
1. **One row per stage at failure**, `TRET` rows then `TRIT` rows, each in file order, with the columns of §6.10.
   A `TREG` or `TRIG` row carries the test (type, criterion, condition, the lab's fit) onto each of its stages.
   Reason: the stage is what AGS gives at failure, and what (b) fits; a test-level row would have to choose a
   stage.
2. **Values at failure end in `_at_failure`; the state before shearing doesn't** (`cell_pressure`,
   `back_pressure`, `effective_consolidation_stress`, `pore_pressure_parameter_b`). Reasons:
   - `pore_pressure` is taken: it is the in situ u0, which `vertical_stress()` writes. A triaxial frame passed
     through `vertical_stress()` (to read σ′3c against σ′v0) would have its pore pressure overwritten.
   - P12's readings (b) have a deviator stress and a pore pressure at every strain step. With the suffix, a frame
     of readings and a frame of failure points can't be mistaken for each other, by P11 or by the user.
   - The names are long, but explicit (CLAUDE.md, "Naming"). The P11 and P12 drafts' bare names are replaced when
     (b) promotes them.
3. **u_f is `TRET_PWPF`, else the back pressure in a drained test, and `effective_stress_basis` says which.**
   A drained test holds the pore pressure at the back pressure (sheet 04 §5.1), so a blank `TRET_PWPF` there is
   read as `TRET_BACK`, with a count in one warning. The basis column makes the choice visible on every row, as
   `depth_basis = "mid_drive_nominal"` does. Nothing else is filled: an undrained stage without a pore pressure,
   or a type the dictionary doesn't list, gets blank σ′ (SPEC §2.6, never guess), and QC X002 lists the undrained
   ones. Rejected: σ′3 = `TRET_CONP` for drained tests, which assumes the cell pressure didn't change after
   consolidation; X006 checks that instead.
4. **The principal stresses come from `ht.analysis.triaxial_failure_stresses(df)`**, which `p.triaxial()` calls,
   so CSV and AGS rows follow the same rules (as `p.spt()` calls `ht.analysis.spt()`).
   - Reads `test_type`, `cell_pressure`, `deviator_stress_at_failure`, and `pore_pressure_at_failure` and
     `back_pressure` where present; adds the four principal stresses and `effective_stress_basis`; returns a copy.
   - σ3 = cell pressure; σ1 = σ3 + q_f; σ′3 = σ3 − u_f; σ′1 = σ′3 + q_f (decision 3 for u_f).
   - Units resolve as SPEC §2.6; the stresses come back in the cell pressure's unit.
   - For CSV input, the analysis errors on what a dataset blanks: a missing required column, a deviator stress of
     0 or less in a compression test, and pore pressure, cell pressure and deviator stress in different
     dimensions. Each error names the rows. The dataset blanks those rows instead, with a warning (§6.10), since
     a dataset doesn't stop on the file's data.
   - Without `pore_pressure_at_failure` (a UU set, say) it gives the total stresses only, without a warning.
5. **Extension tests are kept with blank principal stresses** and one warning naming them. The dictionary gives
   no sign convention for `TRET_DEVF` in extension, and extension makes the axial stress the minor one. Extension
   is out of scope (intent); blanks are better than wrong values.
6. **`multistage_test` is True when the type says so or the specimen has more than one stage** (intent decision
   8). Either is evidence; QC X005 flags where they disagree. `test_stage` is the stage reference as text.
   - The generic names `test_stage` and `multistage_test`, rather than `triaxial_stage`: M17's shear box has
     stages too (`SHBT_TESN`), and the columns mean the same there.
7. **The specimen's initial state uses the existing names** (`water_content`, `bulk_unit_weight`,
   `dry_unit_weight`, `void_ratio`). They are the same quantities, on a specimen set up for the test. They are in
   their own dataset, so they aren't pooled with `p.density()` by accident (M14 a, intent decision 2), and the
   docstring and §6.10 say they aren't in situ values.
8. **The lab's fit is `reported_effective_friction_angle` and `reported_effective_cohesion`.** It is the lab's
   derived value, neither a measurement nor hangtu's fit. Under `effective_friction_angle` it would be pooled on P01
   and P07 with the SPT estimates, and (b) couldn't tell it from its own result when it compares them.
9. **The B-value is `pore_pressure_parameter_b`** (Skempton's pore pressure parameter B). `b_value` is a bare
   symbol, and means other things elsewhere.
10. **QC (level 1), X001–X006 in qc.md §4.12:** a stage that can't give a valid failure state (X002–X004), a test
    whose stages don't match its type (X005), a record that disagrees with itself (X006), and a stage that doesn't
    meet its standard's saturation requirement (X001, intent decision 7).
    - `consolidation_stress_tolerance: 2 kPa` (X006): three 0DP values in kPa, so rounding is at most 1.5 kPa.
    - 🔬 `lowest_pore_pressure_parameter_b: 0.95` (X001): to check against the standards (TODO #53). Until then
      the rule ships with 0.95 and its message says it is the commonly quoted value, not a cited one.
    - **Minimum fields** (qc.md §4.10): a stage needs its sample key, `*_TESN`, `*_CELL` and `*_DEVF` to give a
      failure state, so those are required; a test needs its type. Pore pressure, consolidation stress, back
      pressure, B-value and strain are recommended.
11. **The `triaxial` template** is the dataset's columns without those hangtu computes: `source_line`, the four
    principal stresses and `effective_stress_basis` (decision 4). A CSV user types the file's values and calls
    `triaxial_failure_stresses()`.
12. **The example file gains triaxial groups in (b)**, with P11's and P12's pages, so the data is shown where
    it is drawn. (a) is checked on the test files.

### Sources
- **AGS 4.2 dictionary** (python-ags4 1.2.0, `Standard_dictionary_v4_2.ags`): `TREG` and `TRIG` (parent `SAMP`),
  `TRET` (parent `TREG`, key `TRET_TESN`) and `TRIT` (parent `TRIG`, key `TRIT_TESN`): headings, types, units and
  the pick lists `TREG_TYPE`, `TRIG_TYPE`, `TREG_COND`, `TRIG_COND`. Checked 2026-10-31. `TRET_PWPF` is
  "Porewater pressure at failure", the total pore pressure; `TRET_CONP` is "Effective stress at end of
  consolidation/start of shear stage".
- **Effective stress**, σ′ = σ − u, and σ1 = σ3 + q in triaxial compression: definitions, used without a
  correlation or coefficient.
- **Standard gravity** g = 9.80665 m/s², and the pound and foot, are exact by definition (P00 §4).
- 🔬 **The B-value before shearing**, ASTM D4767, ASTM D7181, ISO 17892-9: not yet checked (TODO #53).

### Acceptance criteria
Golden values hand-calculated from the test files' values. 1 psf = 0.45359237 × 9.80665 / 0.3048² Pa =
47.880259 Pa. Tolerance 1e-9 relative unless a criterion says otherwise.
1. **CU stage (`site_si.ags`):** BH1, sample U2 at 5.00 m, specimen 1, `CU`: `TRET_CELL` 400, `TRET_BACK` 300,
   `TRET_CONP` 100, `TRET_PWPF` 360, `TRET_DEVF` 180 kPa give σ3 = 400, σ1 = 580, σ′3 = 400 − 360 = 40,
   σ′1 = 40 + 180 = 220 kPa, `effective_stress_basis = "pore_pressure_at_failure"`, `multistage_test = False`, and
   the `TREG` values on the row (`failure_criterion` "Maximum deviator stress", `reported_effective_friction_angle`
   27.0, `reported_effective_cohesion` 5). Its initial `TRET_BDEN` 2.05 and `TRET_DDEN` 1.62 Mg/m³ give
   `bulk_unit_weight` 20.1036 and `dry_unit_weight` 15.8868 kN/m³ (× 9.80665).
2. **Drained, back pressure:** BH2's `CDM` specimen has three stages: cell 400, 500, 700; back 300; `TRET_PWPF` 300,
   blank, 300; deviator 300, 520, 900 kPa. They give σ′3 = 100, 200, 400 and σ′1 = 400, 720, 1300 kPa; stage 2 has
   `effective_stress_basis = "back_pressure"`, and one warning counts 1 stage. Every stage has
   `multistage_test = True` and its `test_stage` ("1", "2", "3").
3. **UU stage:** BH1's `UU` specimens at 8.00 m: cell 100, 200, 300 and deviator 120, 124, 118 kPa give σ1 = 220,
   324, 418 kPa, and blank effective stresses and basis, with no warning.
4. **US display:** criterion 1's stage with `display_units="US"` gives σ′3 = 835.4174 psf and σ′1 = 4594.7955 psf
   (40 and 220 kPa ÷ 0.047880259, to 1e-6 relative, the precision of the hand calculation).
5. **Twins:** `site_si.ags` and `site_us.ags` give equal `p.triaxial()` (1e-9 relative) for each `display_units`,
   and the same X findings (none).
6. **Blank, never guessed (`joins.ags`):** a `CU` stage with `TRET_PWPF` blank has blank σ′ and basis, and keeps
   its total stresses; an extension stage (`CIDE`) has blank principal stresses, with the warning naming it; a
   stage with no `TREG` row is kept, with blank test type, criterion and reported fit.
7. **Incomplete:** a stage with `TRET_CELL` blank is left out with the §7 warning, and kept by
   `include_incomplete=True` with blank principal stresses.
8. **QC (`qc_defects.ags`):** each X rule raises exactly the findings its case seeds (qc.md §8). X006's case
   (`TRET_CONP` 150, cell 400, back 300) gives an expected 100 kPa and a difference of 50 kPa in its message; a
   `TRET_CONP` 101 with the same cell and back raises nothing. Each threshold takes a quantity string in psf or ksf
   as well as kPa, and 0.95 accepts a B-value of 0.95.
9. **Good files stay clean:** `site_si.ags`, `site_us.ags` and `site_v404.ags` raise no X finding and no C001;
   their info findings gain nothing but C002 where a recommended heading is blank.
10. **The analysis on a CSV:** `ht.analysis.triaxial_failure_stresses()` on a frame in `ht.template("triaxial")`'s
    shape, with criterion 1's and 2's values, gives the same principal stresses and basis as the dataset. It
    raises, naming the rows, on a deviator stress of 0 in a `CU` row, on a missing `cell_pressure` column, and on
    a pore pressure in a length unit. Without `pore_pressure_at_failure` it gives total stresses only.
11. **Empty:** a file with no `TRET` or `TRIT` gives an empty frame with every column and the warning "No TRET or
    TRIT group".
12. **Feeds the plots:** `ht.plot.profile(p.triaxial(), "deviator_stress_at_failure")` and
    `ht.plot.geology_unit_comparison(p.triaxial(), "axial_strain_at_failure")` run on the good files with
    no warning.
13. **Template:** `ht.template("triaxial")` is the dataset's columns without `source_line`, the four principal
    stresses and `effective_stress_basis`, in the same order (`tests/test_registry.py`).
14. **Common arguments:** `depth=`, `geology=`, `holes=` and `where={"test_type": "CU"}` filter `p.triaxial()` as
    §2 says.
