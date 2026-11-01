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
