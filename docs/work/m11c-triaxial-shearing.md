# M11 (c): triaxial readings and P12 shearing curves

## Intent
M11 (a) read each triaxial stage's state at failure, and M11 (b) fitted c′ and φ′ to those states and drew them
as P11. Neither shows how a specimen got to failure. This unit is M11's last: P12, from a CSV of readings taken
during shearing (`docs/work/m11b-envelope-fit.md`, decision 1).

**Goal:** an engineer passes the readings of a set of triaxial stages, one row per strain step, and gets:
- `ht.plot.triaxial_shearing()` (P12): deviator stress against axial strain, with pore pressure or volumetric
  strain, or the measured stress path in s′–t or p′–q with P11's envelope over it;
- the failure reading of each stage, picked one way and marked the same in every view;
- those failure readings as a frame in `p.triaxial()`'s shape, so `mohr_coulomb_fit()` and P11 take them
  unchanged and can't disagree with P12 about where a stage failed.

**Why:**
- **The failure points can't be checked without the curves.** P11 shows where each stage failed, not whether
  the lab's failure point is reasonable: a CU specimen still dilating at the end of the test, a peak picked on
  a noisy curve, or a CD test that didn't reach failure all look like good points on P11. Sheet 04 §7 asks for
  the curves to be looked at before the fit is trusted.
- **Contractive or dilative behavior is read from the path,** not from c′ and φ′: the shape of a CU path in
  s′–t is how an engineer judges whether the soil is loose or dense, normally or over-consolidated.
- **The failure reading is where P11 and P12 can disagree** (P12 draft §14, "Pitfalls"): max deviator stress
  and max stress ratio give different points on the same CU curve, and the lab's `failure_criterion` is free
  text (M11 (a), decision 4). The reading picked has to be one, the same in every view and in the fit.
- **AGS doesn't carry readings.** `TRET` and `TRIT` have one row per stage (checked 2026-10-15). Readings
  arrive as exports from the lab's software, which the user shapes into a CSV (decided 2026-10-15, P12 draft
  §3). Once M16 lands they may also come from user-defined AGS groups.

**Scope:**
- **A readings template**, `ht.template("triaxial_readings")`, one row per reading: the stage's values repeated
  on each of its rows (`specimen_id`, `test_stage`, `test_type`, `cell_pressure`, `back_pressure`,
  `effective_consolidation_stress`, the lab's failure mark), then the reading's own (`axial_strain`,
  `deviator_stress`, `excess_pore_pressure`, `volumetric_strain`). The stage columns are the triaxial
  template's names; the reading columns are the bare names M11 (a) decision 2 kept free for them.
- **One analysis function** (name to settle in the spec step) that picks each stage's failure reading and
  returns it in the triaxial template's shape (`deviator_stress_at_failure`, `pore_pressure_at_failure`, ...),
  ready for `triaxial_failure_stresses()`.
- **P12, `ht.plot.triaxial_shearing()`**: the draft promoted to `docs/plots/P12-triaxial-shearing.md`, with its
  proposed names replaced by registry names, in the three spaces `"stress_strain"`, `"s_t"` and `"p_q"`.
- **Example data**: a readings CSV in `ht.examples`, consistent with the example file's triaxial stages, drawn
  on P12's site page.

**Constraints:**
- SPEC §3: `(fig, ax, fit)` as P11, styling in a context manager, `ax=` for `Sheet`; equal aspect in s′–t and
  p′–q, not in stress–strain.
- SPEC §4: principal stresses come from `triaxial_failure_stresses()` and the fit from `mohr_coulomb_fit()`,
  never recomputed in the plot. Per reading, the path uses the same definitions (σ′3 = σ3 − u, σ1 = σ3 + q).
- SPEC §2.6: units resolve explicit → `df.attrs["units"]` → error; stresses in display units, strains in
  percent.
- Never drop data silently: readings without what a view needs (a CU stage without pore pressure in s′–t) are
  left out of that view and counted; NaN never becomes 0.
- hangtu doesn't redo the lab's area or membrane corrections: `deviator_stress` is as the lab corrected it.
- Golden values hand-calculated: readings that end at P11's golden failure stresses give P11's c′ and φ′.

**SPEC and TODO touched:**
- SPEC:
  - §2.6, the templates line, for `triaxial_readings`;
  - §4, the triaxial line: failure readings reduce to the failure-stresses shape before anything fits them;
  - §10.3, new names checked against the whole registry;
  - §12.4, M11's status (close-out), and `CLAUDE.md`'s "Next" sentence.
- Other docs: `docs/plots/P12-triaxial-shearing.md` (promoted), `docs/plots/README.md` and
  `docs/plots/drafts/README.md` (P12's status), `docs/site/plots/`, `docs/site/reference/`, and sheet 04's site
  page (a line pointing to P12 as the check on the fit's points).
- TODO: #53 (the failure criteria in D4767, D7181 and D2850). Max deviator stress and max stress ratio are
  defined in this unit from the readings, not cited; what each standard requires stays #53.

### Settled before this intent
- **Readings come from a CSV the user shapes; no reader for lab software exports** (2026-10-15, P12 draft §3).
- **Reading names are bare, failure names end in `_at_failure`** (M11 (a), spec decision 2), so a frame of
  readings and a frame of failure points can't be mistaken for each other.
- **Pore pressure or volumetric strain goes on a second y axis, off by default** (M11 (a), "Outline of (b)").
- **P12 is one unit, after (b), reusing its fit** (M11 (b), decision 1).

### Decisions (intent review, 2026-11-01)
1. **One unit, not data then analysis.** `docs/reference/process.md` splits a dataset from the analyses on it.
   The readings here are a template and a few names, with no AGS ingest, no dataset method and no QC rules,
   and P12 is what decides their shape. Splitting them off would design a template without the plot that
   reads it. If the spec step finds the readings need QC rules of their own, split then.
2. **Readings reduce to failure rows, and the rest of the chain is (a)'s and (b)'s.** The new function returns
   one row per stage in the triaxial template's shape; `triaxial_failure_stresses()` adds the principal
   stresses, `mohr_coulomb_fit()` fits them, and P12 draws the envelope from that fit. So P11 and P12 can be
   drawn from the same failure rows, and a user can put them beside the lab's `p.triaxial()` rows to check the
   lab's failure points.
3. **Excess pore pressure, not total, on each reading.** Δu from the start of shearing, as the P12 draft has
   it. The failure row's `pore_pressure_at_failure` is then `back_pressure` + Δu at the failure reading, so
   it has the meaning (a) gave it (total, back pressure included). Asking for total pore pressure was rejected:
   lab exports give Δu as often as u, and a file mixing the two can't be told apart; asking for one, named
   for what it is, can be.
4. **Picking the failure reading, in this order:**
   1. the lab's mark on a reading (`failure_point`, one per stage; more than one is an error naming the stage);
   2. else `failure_criterion=`, `"max_deviator_stress"` or `"max_stress_ratio"` (σ′1/σ′3, effective stress
      only);
   3. else an error naming the argument.

   No default criterion: the two give different points on a CU curve, and which is right depends on the
   standard and the lab (TODO #53), so it's the user's choice (SPEC §4, judgments have no defaults). It is an
   argument, not an entry in the judgments file, because it applies to one set of tests, not to a geology
   unit. The criterion used is recorded on each failure row, in `failure_criterion`.
5. **Each view draws what its stages allow, and counts the rest.** Stress–strain draws every stage; s′–t and
   p′–q need effective stresses (CU with Δu, or CD) or `stress="total"` (UU), as P11. A stage left out of a
   view is counted in the figure's footnote, by reason.
6. **The second y axis keeps the contract.** `(fig, ax, fit)` returns the primary axis, and the twin is
   reached through matplotlib (`ax.get_shared_x_axes()`). The spec step settles whether that is enough, or
   whether the twin should also be returned or a two-panel `Sheet` offered (the P12 draft's open question,
   §14).

### Open (for the spec step)
- **Names**, checked against the whole registry: `axial_strain`, `deviator_stress`, `excess_pore_pressure`,
  `volumetric_strain`, the lab's failure mark (`failure_point` in the draft), and the new function. `pore_pressure`
  is taken (in situ u0), which is why the reading's is `excess_`.
- **Input checks:** stage values that differ between rows of one stage, strain not increasing, a stage with one
  reading, readings for a stage with no failure (a test stopped early).
- **Multistage stages:** each stage is its own curve and path, by `test_stage`; whether strain restarts at each
  stage or runs on, and how the curves are drawn either way.
- **The example readings:** how they are made (a hyperbolic curve to each example stage's failure state is one
  way), and that they say they are synthetic.
- **Sources:** the stress path in s′–t and p′–q follows from the definitions P11 already uses, so no citation is
  needed for it; Lambe (1967) in the draft's references is cut unless verified.

### Out of scope
- **M17:** undrained strength, the shear box, the Hoek–Brown fit.
- **M16:** readings from user-defined AGS groups.
- **Wave 5:** E50 and other stiffnesses from the curves.
- **Later** (P12 draft §15): total and effective paths together for CU, anisotropic consolidation
  (`TRET_CVP`, `TRET_CRP`), extension tests, a reader for lab software exports, and redoing the lab's area and
  membrane corrections.

## Spec
The plot's rules live in `docs/plots/P12-triaxial-shearing.md` (promoted from the draft). The readings and
`triaxial_failure_from_readings()` have no topic doc of their own; their rules are here, and the docstrings
become the reference once built. This section lists what changes where, the decisions (the intent's settled,
with changes noted), the golden readings and the acceptance criteria.

### Changes
- **`docs/plots/P12-triaxial-shearing.md`:** promoted, with registry names, the failure-reading rules, the
  second axis as an argument, and edge cases. `docs/plots/README.md`: P12 `draft`; `docs/plots/drafts/README.md`:
  P12 promoted.
- **`ht.analysis.triaxial_failure_from_readings()`** (new), with its reference entry.
- **`ht.plot.triaxial_shearing()`** (new), with its reference entry, site page and example.
- **Registry:** `axial_strain`, `deviator_stress`, `excess_pore_pressure`, `volumetric_strain` and
  `reported_failure_reading` (new, decision 7); the `triaxial_readings` template.
- **SPEC §2.6** (the templates line) and **§4** (the triaxial line), in this commit (decision 2). §12.4 and
  `CLAUDE.md` at close-out.
- **Example data:** `triaxial_readings.csv` in `ht.examples`, generated by `tests/data/_make_examples.py` for the
  example project's six triaxial stages (decision 10).
- **Docs site:** sheet 04's page gains a sentence under Methods pointing to P12 as the check on the fit's points;
  `docs/site/guides/` names the readings template beside the triaxial one.

### Decisions
1. **`triaxial_failure_from_readings(df, *, failure_criterion=None, units=None) -> DataFrame`**, one row per
   stage in `ht.template("triaxial")`'s shape (P12 §4). It reduces readings to the failure rows (a)'s chain
   already takes, and computes no principal stress itself: `triaxial_failure_stresses()` does that, for readings
   and AGS rows alike. A name with `from_readings` says what it reads; `triaxial_failure_readings` was rejected,
   since it returns stages, not readings.
2. **SPEC §4 gains the reduction**, and §2.6 the template (in this commit): readings reduce to failure rows
   before anything fits them, so P11, P12 and the fit can't disagree about where a stage failed (intent
   decision 2).
3. **The failure reading: `failure_criterion=` first, then the lab's mark, then an error** (*changed from intent
   decision 4*, which put the mark first). An explicit argument is how an engineer re-picks a set of tests to
   check the lab; with the mark first they would have to delete the column to do it. When the argument
   overrides marks, a note says how many stages had one. Still no default criterion (SPEC §4).
4. **Two criteria, defined from the readings:** `"max_deviator_stress"`, the largest q; `"max_stress_ratio"`,
   the largest σ′1/σ′3, effective stress only. Ties go to the lowest strain. The failure rows'
   `failure_criterion` is written "Maximum deviator stress" or "Maximum principal stress ratio", the wording of
   `TREG_FCR`'s example, so rows from readings and rows from AGS pool or refuse to pool by the same rule in
   `mohr_coulomb_fit()` (M11 (b) Spec, decision 4).
5. **The path starts at cell − back, not at `effective_consolidation_stress`.** Per reading, u = back + Δu, so
   the last point of a path is the failure row's point exactly. `effective_consolidation_stress` is carried and
   not used; a file where it differs from cell − back is `qc.md` X006's to find in AGS, and a P12 pitfall.
6. **A stage is (`specimen_id`, `test_stage`)**, `test_stage` blank or missing meaning one stage. Any column
   other than the five reading columns is a stage column, carried, and must be the same on all of a stage's
   readings (an error naming the stage and column otherwise). Strain must not decrease within a stage, which
   also catches two stages under one ID. Strain is drawn as given across stages, so a lab that restarts it per
   stage and one that runs it on both read right (settles the intent's open question on multistage).
7. **Names** (checked against `columns.yaml` and every spec, 2026-11-01; none is used): `axial_strain` and
   `volumetric_strain` (percent, from the start of shearing; ε_v positive in compression), `deviator_stress`
   (q = σ1 − σ3, as the lab corrected it), `excess_pore_pressure` (Δu from the start of shearing, positive for a
   rise), `reported_failure_reading` (bool, the lab's failure reading; `reported_` as the lab's c′ and φ′ are).
   The four readings are bare, the failure values end in `_at_failure` (M11 (a) Spec, decision 2). They are
   written for any test with readings during shearing, not only triaxial ones, so M17's UCS curves and wave 5's
   E50 can reuse them; a CPT's excess pore pressure will carry the `cpt_` prefix (CLAUDE.md, "Naming").
8. **`second_axis=` names its column** (`"excess_pore_pressure"` or `"volumetric_strain"`, default None, as M11
   (a) settled "off by default"). A bool was rejected: a set of CU and CD stages has both, and one axis can't
   show two quantities. The twin isn't returned (intent decision 6, kept): the contract stays `(fig, ax, fit)`,
   and the docstring shows how to reach it. A two-panel layout is P12 §15.
9. **Views and counts** (intent decision 5): `stress_strain` draws every stage; `s_t` and `p_q` draw what the
   stress basis allows and count the rest in the footnote, by reason. Arguments that only one kind of space takes
   are errors in the other (P12 §11), so a fit setting is never silently ignored.
10. **The example readings are synthetic and generated**, as `site.ags` is: for each example stage, readings at
    fixed strains along a hyperbola q = ε / (1/E_i + ε/q_ult), scaled so the largest q falls on the failure
    reading at the stage's `TRET_STRN`, `TRET_DEVF` and `TRET_PWPF` (Δu = `TRET_PWPF` − back pressure), with Δu
    and ε_v curves of the usual shape (CU: Δu rising, then flattening; CDM: ε_v contracting, then turning toward dilation, to end at
    `TRET_STV`). The
    numbers are in the generator, not hand-picked per reading; AC 11 checks that the failure readings agree with
    `site.ags`. The `ht.examples` docstring says the file is synthetic.

### Golden readings
Hand-built, in kPa and percent. Per reading σ′3 = cell − (back + Δu), σ′1 = σ′3 + q, ratio σ′1/σ′3.

**R1, two CU stages** (`test_type` `CU`, `failure_criterion` "Maximum deviator stress" on every row):

| Stage | Cell, back | ε_a (%) | q | Δu | σ′3 | σ′1 | σ′1/σ′3 |
|---|---|---|---|---|---|---|---|
| A | 400, 200 | 0 | 0 | 0 | 200 | 200 | 1 |
| | | 1 | 100 | 50 | 150 | 250 | 1.6666667 |
| | | 4 | 180 | 90 | 110 | 290 | 2.6363636 |
| | | 8 | **200** | 100 | 100 | 300 | 3.0 |
| | | 12 | 195 | 110 | 90 | 285 | **3.1666667** |
| | | 15 | 190 | 112 | 88 | 278 | 3.1590909 |
| B | 500, 200 | 0 | 0 | 0 | 300 | 300 | 1 |
| | | 1 | 150 | 40 | 260 | 410 | 1.5769231 |
| | | 4 | 270 | 80 | 220 | 490 | 2.2272727 |
| | | 8 | **300** | 100 | 200 | 500 | 2.5 |
| | | 12 | 290 | 115 | 185 | 475 | **2.5675676** |
| | | 15 | 280 | 120 | 180 | 460 | 2.5555556 |

- **Max deviator stress:** A at 8 %, B at 8 %: `deviator_stress_at_failure` 200, 300; `pore_pressure_at_failure`
  300, 300; σ′ (100, 300) and (200, 500), P11's golden 1 (M11 (b) Spec, AC 1): c′ = 25√2 = 35.355339 kPa,
  φ′ = arcsin(1/3) = 19.471221°.
- **Max stress ratio:** A at 12 %, B at 12 %: q 195, 290; u_f 310, 315; σ′ (90, 285) and (185, 475). s′ = 187.5,
  330; t = 97.5, 145; tan α = 47.5/142.5 = 1/3; a = 97.5 − 187.5/3 = 35; φ′ = 19.471221°;
  c′ = 35 / cos φ′ = 35 · 3/√8 = 37.123106 kPa; tangent points σ′n = 187.5 − 97.5/3 = 155 and
  330 − 145/3 = 281.66667 kPa.
- **Paths:** A at 4 %: s′ = (110 + 290)/2 = 200, t = 90; p′ = (290 + 2·110)/3 = 170, q = 180.

**R2, ties and checks:** stage E (`CU`, cell 400, back 200) with q 0, 150, 150, 140 at 0, 2, 4, 6 % and Δu 0, 50,
60, 70: max deviator stress picks 2 % (the first of the tie). The same with strain 0, 4, 2, 6 raises (strain
decreasing); with `cell_pressure` 400 on one reading and 410 on another raises (stage column differs).

**R3, a CD stage** (`CD`, cell 300, back 200, Δu blank): ε_a 0, 1, 3, 6, 9 %; q 0, 100, 200, 250, 240; ε_v 0,
0.3, 0.2, −0.4, −0.8 %. σ′3 = 100 throughout (u = back). Max q at 6 %: σ′ (100, 350); path at 6 %:
s′ = 225, t = 125, p′ = 100 + 250/3 = 183.33333, q = 250. Max stress ratio picks the same reading (σ′3 constant).
`pore_pressure_at_failure` is blank, so `triaxial_failure_stresses()` uses the back pressure, with its warning.

**R4, a UU stage** (`UU`, cell 200, no back pressure or Δu): ε_a 0, 2, 5, 10 %; q 0, 80, 120, 110. Max q at 5 %:
σ3 = 200, σ1 = 320 kPa; total path from (200, 0) to (260, 60) in s–t. No effective stresses;
`"max_stress_ratio"` on it raises.

### Sources
- **Per-reading stresses and the constructions:** definitions (σ′ = σ − u; s, t, p, q), derived in the M11 (b)
  Spec, "Derivations". No coefficient or cited value.
- **The criteria:** defined here from the readings (decision 4). 🔬 What ASTM D4767, D7181 and D2850 require of
  each is TODO #53; nothing here depends on it.
- **The example's hyperbola** (decision 10) only shapes synthetic data and is not a method hangtu offers, so it
  needs no citation; the generator says so.
- Lambe (1967), in the draft's references, is cut.

### Acceptance criteria
Golden values from the readings above, hand-calculated; tolerance 1e-9 relative unless stated.
1. **R1, max deviator stress:** the failure rows' q, u_f and ε_a as above; through `triaxial_failure_stresses()`
   and `mohr_coulomb_fit()`, c′ = 35.355339 kPa and φ′ = 19.471221° (1e-7, the hand calculation's precision);
   `failure_criterion` "Maximum deviator stress".
2. **R1, max stress ratio:** q 195, 290; u_f 310, 315; ε_a 12, 12; c′ = 37.123106 kPa, φ′ = 19.471221° (1e-7);
   σ′n range 155 to 281.66667 kPa; `failure_criterion` "Maximum principal stress ratio".
3. **The lab's mark** (decision 3): R1 marked at 12 % and no argument gives AC 2's rows with "Maximum deviator
   stress" carried from the readings; with the argument, AC 1's rows and a note naming 2 stages with a mark;
   unmarked and no argument raises naming both stages and `failure_criterion=`; two marks in a stage raise.
4. **R2:** the tie picks 2 %; decreasing strain and a differing stage column raise as above.
5. **R3:** failure at 6 %, `pore_pressure_at_failure` blank, `volumetric_strain_at_failure` −0.4;
   `triaxial_failure_stresses()` gives (100, 350) with its back-pressure warning.
6. **R4:** failure at 5 %, q 120; total stresses (200, 320); `"max_stress_ratio"` raises naming the stage.
7. **Rows:** one per stage in order of first reading; stage columns carried; `multistage_test` True for a `CDM`
   stage and for a specimen with two `test_stage` values; the output's `attrs["units"]` has the stress columns'
   units; `ht.template("triaxial")`'s columns, where the readings have them, in its order.
8. **Errors:** a missing required column names it and `ht.template("triaxial_readings")`; stresses without
   units raise naming the column; σ′3 ≤ 0 under `"max_stress_ratio"` raises naming the readings.
9. **Template:** `ht.template("triaxial_readings")` has P12 §3's columns in order; `ht.columns("triaxial_readings")`
   lists them.
10. **The plot:** P12's §12 criteria.
11. **Example:** P12 AC 11, and `triaxial_readings.csv` is regenerated unchanged by the generator check.
12. **Reference:** `triaxial_failure_from_readings` and `triaxial_shearing` in the API reference, with the
    sheets' `TEMPLATE.md` docstring checklist.
