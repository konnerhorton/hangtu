# M19 (b): compressibility

## Intent
M19's second unit (M19 (a) decision 1): stage B for sheet 06, the first derivation from `p.oedometer()`'s
increments. 🟡 marks a choice proposed here, awaiting review.

**Goal:** from `p.oedometer()` (or a CSV in the `oedometer` template), an engineer gets, per specimen, σ′p, Cc, Cr
and Cs, and, where σ′v0 at the specimen's depth is given, OCR and the sample quality by Δe/e0. Each value is
reproducible from the increments, says which points it used and which it left out and why, and says when it can't
be given. P13 draws the e–log σ′v curve with the fitted lines and σ′p, so the engineer can see whether the fit is
believable before using it.

**Why:**
- **Stage A has nothing to compare yet.** `p.oedometer()` (M19 a) gives the increments, but σ′p and OCR exist only
  as SPT correlations (M13 b2). The site page for sheet 06 says oedometer tests on good samples overrule them, and
  its Methods table lists "σ′p, Cc and Cs from an oedometer curve" as W3.
- **σ′p depends on the method by 10–20 %** (sheet 06 §6), and on disturbance more than either. So the method is
  fixed and stated, deterministic (the same increments give the same σ′p), and the quality grade sits next to it.
- **The example file can draw it.** `site.ags` has two specimens with eight to twelve increments and an
  unload–reload loop each (M19 (a) decision 10), so P13 and the docs page run on the example project.

**The derivation** (sheet 06 §5.1, §5.3, §5.8; sources under "Evidence"):
- **σ′p by Oikawa (1987):** two straight lines fitted to the loading branch (`load_branch = "loading"`) in
  log(1 + e) against log σ′v, the split between them searched by least squares, σ′p where they cross. It is
  deterministic (the same increments give the same σ′p) and needs no smoothing (decision 5).
- **Cc and Cr:** the slopes of e against log σ′v of the same two groups of points: Cc from the points above the
  split, Cr from those below.
- **Cs** from the unloading branch: the slope of e against log σ′v over an unload (🟡 which unload, and whether the
  reload is used too, in the spec step).
- **CR = Cc / (1 + e0)** on the result (decision 4).
- **σ′p by Pacheco Silva (1970) as the check:** the virgin line (Cc's) meets the horizontal through e0; down to the
  curve; across to the virgin line; σ′p is that point's stress (decision 2). 🟡 In the spec step: what the check
  gives when e0 is blank or differs from the first increment's starting e (seating, flooding), and when the
  construction misses the measured curve.
- **OCR = σ′p / σ′v0,** reading `effective_vertical_stress` from `ht.analysis.vertical_stress()` on the
  `p.oedometer()` rows, as the SPT OCR correlation does. Without the column, OCR is blank with a reason, never
  filled from an assumed σ′v0. An OCR below 1 is kept and flagged, not clipped (sheet 06 §7).
- **Δe/e0 = (e0 − e at σ′v0) / e0,** e at σ′v0 interpolated in log σ′v on the loading branch, graded by Lunne et al.
  (1997) into its four classes for OCR 1–2 and 2–4. Outside OCR 1–4 the value is given without a class. 🟡 In the
  spec step: σ′v0 below the first increment's stress (extrapolate, or blank with a reason); whether Δe counts from e0
  or from after a `constant_stress` increment (flooding, swelling at the seating load); and which OCR picks the band,
  since disturbance lowers this test's σ′p and so can move a specimen into the more lenient OCR 1–2 band (said on the
  result or under Pitfalls).
- **The result** is a derived result (SPEC §5) like the envelope fits: one row per specimen, the points each line
  used, and the rows left out counted by reason. 🟡 One function, `compressibility_fit()` or similar, named in the
  spec step against the registry.

**Constraints:**
- The fit reads only the loading branch for σ′p, Cc and Cr; a reload slope is never Cc (sheet 06 §7).
- A specimen that can't give a value has a reason, not an error: too few points on either side of σ′p, a maximum
  stress too low to define the virgin line (sheet 06 §7 says 2–3 σ′p), no clear break, no unload, no loading branch.
  The spec fixes each as a number (a minimum count of points per line, a stress ratio), not a range.
- **No clear break is a result.** Oikawa's split search always returns two lines that cross somewhere, so the spec
  states when the crossing isn't a σ′p (for example, slopes too close to tell apart, or a crossing outside the
  measured stresses or not between the points either side of the split), and σ′p is then blank with that reason.
- **The first points past a reload aren't yet on the virgin line.** `load_branch` calls a point `loading` once its
  stress exceeds the previous maximum, but the curve takes an increment or two to rejoin the virgin line after an
  unload–reload loop. The spec decides whether those points are kept in the fit or left out with a counted reason,
  since they flatten Cc.
- Points outside the method's reach are counted and reported, never dropped to make a fit work (SPEC §4,
  "Validity is reported").
- Golden values hand-calculated on the M19 (a) specimen BH1 U3 (twelve increments, one unload–reload loop, a second
  unload), and on one curve with no clear break, whose expected result is a blank σ′p with the no-break reason.
- Every method cites a verified source, or it is cut rather than shipped unverified.

**SPEC and docs touched:**
- SPEC §4 (a bullet for the oedometer fit, as the envelope fits have), §5 (a derived result's names), §10.3 (new
  registry columns).
- 🟡 A new `docs/analysis/compressibility.md`, which (c) and (d) extend, rather than a section in `strength.md`:
  compressibility isn't strength.
- `docs/plots/P13-consolidation-curve.md` (promoted from the README's idea row in the spec step).
- Sheet 06 (§5.1's "standard construction [U]" becomes Oikawa; §5.2 and §5.4 marked later) and its site page
  (Methods, Pitfalls); sheet 11 and the parameter index (Eoed and Eur,oed move to (c)); `STATUS.md`'s M19 row.
- TODO: a new item for Casagrande and the work method, with a trigger (decision 2).

### Evidence (searched 2026-11-17)
- **The two-line method:** no source found names a least-squares two-line fit in e–log σ′v as a method. Umar &
  Sadrekarimi (CGJ manuscript cgj-2016-0203.R1, Table 1, p. 28) list the line-fit methods: Burland (1990) in the void
  index, and the bilogarithmic Butterfield (1979, ln(1 + e)–ln σ′v), Oikawa (1987, log(1 + e)–log σ′v), Onitsuka et
  al. (1995, ln(1 + e)–log σ′v) and Jose et al. (1989, log e–log σ′v). Of eleven methods on their database Oikawa
  ranked first by RMSE (33.2 kPa), Casagrande eighth (44.3), Pacheco Silva ninth (49.5) (Table 7, p. 34); bilogarithmic
  plots give straighter lines (p. 5). Oikawa (1987), *Soils and Foundations* 27(3), 99–104,
  doi:10.3208/sandf1972.27.3_99, a technical note (read from J-STAGE's scan): for soft soils, log f–log p (f = 1 + e)
  "is better" linear than e–log p, is "composed of two segments of straight line", and the stress where they
  intersect "agrees well with the consolidation yield stress" from Casagrande's construction (abstract, p. 99). Its
  data are soft soils (sensitive clays, organic soils, peat), which the spec step turns into the method's stated
  range. 🔬 The equations and the fitting procedure (pp. 100–104), and the published version of Umar &
  Sadrekarimi, in the spec step.
- **Pacheco Silva's construction:** steps (i)–(v) as above, quoted in Paniagua, L'Heureux, Yang & Lunne (2016),
  NGM 2016, §2.4, p. 548, citing Pacheco Silva (1970), Proc. 4th Brazilian Conf. SMFE, Rio de Janeiro, 225–232. It
  uses e0, "the specimen void ratio before any load has been applied". The same paper finds five methods within 14 %
  on good-quality samples.
- **Lunne et al. (1997) bands,** read in two secondary sources that agree: Krage, DeJong, DeGroot, Dyer & Lukas
  (2015), 6ICEGE, Table 1, and Thakur (2016), NGM 2016. OCR 1–2: < 0.04 very good to excellent, 0.04–0.07 good to
  fair, 0.07–0.14 poor, > 0.14 very poor; OCR 2–4: < 0.03, 0.03–0.05, 0.05–0.10, > 0.10. Δe is the change in void
  ratio on reconsolidation from the specimen's initial state to σ′v0 (Krage et al.). This confirms the intermediate
  bands sheet 06 had as [U].
- **mv's definition** (BS 1377-5, ISO 17892-5) wasn't found in an open source; it stays with TODO #73 and (c).

### Decisions (intent review, 2026-11-17)
1. **Eoed and Eur,oed move to (c),** changing M19 (a) decision 1. Eoed = 1/mv per increment, so it hangs on the same
   definition as TODO #73 (Δe over 1 + e at the increment's start, or over 1 + e0), and (c) recomputes mv and draws
   it on P14.
2. **Pacheco Silva is the one check on σ′p for now.** It reuses the fitted virgin line and e0, so it is
   deterministic. Casagrande (a smoothing choice for maximum curvature, a hidden judgment) and the work method (a
   strain definition, TODO #73) come later; a TODO records them with a trigger.
3. **Cr and Cs are reported separately:** Cr from the loading fit's flat line, Cs from an unload. Disturbance raises
   Cr, so keeping them apart shows it.
4. **CR = Cc / (1 + e0) is on the result,** so a lab's CR (ε–log σ′v) compares with it.
5. **σ′p by Oikawa (1987) rather than a two-line fit in e–log σ′v** (the search, under "Evidence"). M19 (a)
   decision 1 named a "bilinear fit"; this is one, in the plot its source says is straighter, and it is the best
   ranked in the one comparison found. Cc, Cr and Cs stay e–log σ′v slopes, as the sheet and the models define
   them.

### Out of scope
- mv, cv, k, Eoed and Eur,oed, P14 and P15 (c); rock swelling (d); K0 from OCR, SHANSEP and the Soft Soil set (M20).
- Cc from LL and other stage C correlations for sheet 06.
- Stage D for σ′p and Cc (`representative()`, `select()`) and TODO #59.
- CRS and Rowe cell tests (`ESCG`, `ESCT`) and the lab's reported σ′p and Cc.
- Casagrande, the work method and the other line-fit methods (decision 2).
- Strain-based curves (ε–log σ′v) as the fitted quantity; P13 may draw strain as an axis option (spec step).

## Spec
The plot's rules live in `docs/plots/P13-consolidation-curve.md` (new, promoted from the README's idea row). The
fit's rules are here until the close-out moves them into a new `docs/analysis/compressibility.md` (the intent's open
choice, taken: (c) and (d) extend it), and the docstring becomes the reference once built. This section lists what
changes where, the decisions, the derivation and the acceptance criteria. The spec review (2026-11-19) took every
proposal as drafted: the slope ratio of 2, the stress ratio of 2, Cs from the first unload, the names, and the strain
axis left to (c).

### Changes
- **`ht.analysis.oedometer_fit()`** and **`ht.analysis.OedometerFit`** (new), with reference entries.
- **`ht.plot.consolidation_curve()`** (new, P13), with its spec, reference entry, site page and example.
  `docs/plots/README.md`: P13's row becomes `draft` with the function's name, in this commit.
- **Registry** (decision 2): `compression_index`, `recompression_index`, `swelling_index`, `compression_ratio`,
  `preconsolidation_stress_pacheco_silva`, `normalized_void_ratio_change`, `sample_quality` (new), `used_by: [P13]`;
  `preconsolidation_stress` and `overconsolidation_ratio` (M13 b2's) gain P13. None collides: checked against
  `columns.yaml`, `src/`, `docs/` and `SPEC.md`, 2026-11-19 (`consolidation_curve` appears only in P13's README row).
- **SPEC §4** gains an "Oedometer fit" bullet at close-out, linking `compressibility.md` (as M17 (b)'s fit line):
  σ′p where two least-squares lines in log(1 + e)–log σ′v cross (Oikawa 1987), the split searched, so the same
  increments give the same σ′p; Pacheco Silva as the check; only the loading branch gives σ′p, Cc and Cr, and Cs
  comes from an unload, never a reload; a curve with no clear break, too few points or too short a virgin line gets
  a reason, not a value; nothing is extrapolated. §5 needs no change: the fitted σ′p takes the parameter's name, and
  the SPT correlation's rows keep apart by `correlation_name`, as §5 already says.
- **`docs/analysis/compressibility.md`** (new, at close-out) with the fit's rules; `strength.md` is unchanged.
- **Sheet 06 and its site page** (close-out): §5.1 becomes Oikawa (1987) [V], with this unit's fitting procedure;
  §5.2 and §5.4 are marked later; §5.3 cites Pacheco Silva via Paniagua et al. (2016); §5.8's intermediate bands
  [V] via Krage et al. (2015) and Thakur (2016). Sheet 11 and the parameter index: Eoed and Eur,oed move to (c).
- **`docs/TODO.md`** (close-out): Casagrande and the work method, with a trigger (intent decision 2).
- **Example data:** none new. `site.ags`'s B-4-U1-C1 and B-5-U2-C1 (M19 (a) decision 10) both give a σ′p, Cc, Cr
  and Cs (Example data, below).

### Decisions
1. **`oedometer_fit(df, *, units=None, display_units=None) -> OedometerFit`.** It reads `p.oedometer()`'s columns
   (or a CSV in `ht.template("oedometer")`'s shape) and fits each specimen's curve: one fit per `specimen_id`, in
   `group_keys()` order. There is no `group_by=`: a curve belongs to one specimen. A frame without `specimen_id`,
   `applied_vertical_stress` or `void_ratio_at_increment_end` is an error naming them and pointing to the
   template; a row with a blank `specimen_id` is an error naming its rows. Rows keep the frame's order within a
   specimen (`p.oedometer()`'s file order). `load_branch` is read where the frame has it, else added by
   `oedometer_load_branch()`, with a note.
2. **Names**, the registry's, with labels: `preconsolidation_stress` ("Preconsolidation stress, σ′p", Oikawa's,
   the main value), `preconsolidation_stress_pacheco_silva` ("…, σ′p by Pacheco Silva"), `compression_index`
   ("Compression index, Cc"), `recompression_index` ("Recompression index, Cr"), `swelling_index` ("Swelling index,
   Cs"), `compression_ratio` ("Compression ratio, CR = Cc/(1 + e0)"), `overconsolidation_ratio`,
   `normalized_void_ratio_change` ("Normalized change in void ratio, Δe/e0") and `sample_quality` (Lunne et al.'s
   class). Cc, Cr and Cs are positive numbers (the negated slopes), as the sheet and the models use them.
3. **The rows each value reads:**
   - σ′p, Cc and Cr: `loading` rows only (intent constraint). A reload slope is never Cc.
   - Cs: one unload run (decision 9).
   - Rows used by no line are counted, each once under the first reason that applies: `count_no_applied_stress`,
     `count_no_void_ratio` (e at the increment's end blank), `count_stress_not_positive` (log undefined),
     `count_constant_stress`, `count_reloading`, `count_unloading_not_used`. The loading points plus the Cs run's
     unloading rows plus these counts are the specimen's rows.
4. **σ′p by Oikawa (1987)** (Derivation): each loading point is x = log10 σ′v, y = log10(1 + e). Every split of the
   points, in stress order, into a lower group and an upper group of at least 3 points each is fitted with one
   least-squares line per group (the core, `_line_fit`, free); the split with the smallest total sum of squared
   residuals wins, the lower split on a tie. σ′p is where the two lines cross. Oikawa states the construction (the
   intersection of the two straight segments, p. 103) but no fitting procedure, so the search is hangtu's, stated
   as such in the docstring: deterministic, and the same increments give the same σ′p. Every split's sum of squares
   is on the result, so the engineer can see how clearly one won.
5. **When the crossing isn't a σ′p** (intent constraints). Checked in this order; the first that fails gives σ′p,
   Cc, Cr, CR and Pacheco Silva's σ′p blank with its reason (Cs doesn't depend on them and is still given):
   1. fewer than 6 loading points: "6 loading points are needed (3 per line), 5 given";
   2. **no clear break:** the upper line isn't falling, or isn't at least **2** times as steep as the lower line
      (|b2| ≥ 2 |b1|): "no clear break: the upper line is 1.17 times as steep as the lower, at least 2 is needed".
      Real curves give 5–12 (Example data), a straight e–log curve 1.2, and Cs/Cc of 0.1–0.3 (sheet 06 §3) means a
      ratio near 3–10 in intact clays;
   3. **the crossing outside the measured stresses** (below the lowest loading stress or above the highest):
      "the lines cross at 7.9 kPa, outside the loading stresses (10 to 320 kPa)". Not "between the two groups":
      with 3 points needed on the upper line, a curve whose break lies between its third-last and second-last
      points (B-5-U2-C1) crosses just past the upper group's first point, and is a good curve;
   4. **the virgin line too short:** the highest loading stress below **2** σ′p: "the highest loading stress is
      1.64 σ′p, at least 2 is needed to define the virgin line". Sheet 06 §7 says 2–3 σ′p; 2 is its lower end,
      since rule 1 already asks for 3 points on the line, and a test that ends between 2 and 3 σ′p is common in
      older data. The ratio is on the result, and the summary says so when it is below 3.
6. **Cc and Cr** are the e–log σ′v least-squares slopes (negated) of the same two groups of points (intent; decision
   5 there): Cc from the upper group, Cr from the lower. Their two lines don't cross exactly at σ′p (they are fitted
   in another space); P13 marks σ′p on the curve, not at their crossing.
7. **CR = Cc / (1 + e0)**, e0 the specimen's `void_ratio` (CONG_IVR); blank with a reason when e0 is blank.
8. **Points past a reload are kept** (intent constraint). A point is `loading` once it exceeds the previous
   maximum; the point at the previous maximum is `reloading` (equal counts as reloading) and is already left out.
   The next one is usually at twice that stress, past the loop's disturbance, and leaving it out would take the
   virgin line's highest points, the ones sheet 06 §7 says it most needs: BH1-U3 would have 6 loading points and a
   2-point virgin line. They are counted (`count_loading_after_reload`) and marked on P13, so the engineer sees
   them.
9. **Cs from the first unload run:** the point the unload starts from (the last row before it) and the
   consecutive `unloading` rows after it, at least 2 points, fitted by least squares in e–log σ′v. The reload is
   never used (a different branch, with hysteresis; sheet 06 §7). Every run's Cs is on the result with its start
   stress; the frame's `swelling_index` is the first run's, the loop the lab ran on purpose, rather than the final
   unload, often cut short. A specimen with no unload has Cs blank, "no unloading". A 2-point run notes that its
   line passes through both. Rejected: a fit over every unload together (the runs start from different stresses
   and needn't be parallel).
10. **Pacheco Silva (1970)** as the check (intent decision 2): (i) the virgin line (Cc's, in e–log σ′v) meets e =
    e0 at σA; (ii) e_B is the curve's void ratio at σA, interpolated linearly in e against log σ′v between the
    loading points either side; (iii) the horizontal through e_B meets the virgin line at the check's σ′p. Edge
    cases, resolved:
    - **e0** is the specimen's `void_ratio` only, "the specimen void ratio before any load has been applied"
      (Paniagua et al. 2016, §2.4). Blank e0 gives a blank check, "no initial void ratio"; it never falls back to
      the first increment's starting e, which already holds the seating load or a flooding swell. A difference
      between them isn't checked here.
    - **The construction misses the curve:** σA below the lowest loading stress or above the highest gives a blank
      check, "the construction falls outside the measured curve (σA = 5 kPa, loading from 10 kPa)". No
      extrapolation.
    - The check is never compared or warned about: both values are on the result, and P13 draws both.
11. **OCR = σ′p / σ′v0**, σ′v0 from `effective_vertical_stress` (`vertical_stress()`, run by the engineer on the
    `p.oedometer()` rows), converted to the fit's unit. A specimen whose rows give more than one non-blank σ′v0 is an
    error naming it. Blank σ′v0 or σ′p: OCR blank with the reason. OCR < 1 is kept, with one warning per call
    naming the specimens (disturbance, a wrong σ′v0 or underconsolidation; sheet 06 §7), never clipped.
12. **Δe/e0 = (e0 − e at σ′v0) / e0** (Lunne et al. 1997, via Krage et al. 2015), resolved:
    - **e at σ′v0** is interpolated linearly in e against log σ′v between the loading points either side of σ′v0.
    - **σ′v0 below the lowest loading stress** (or above the highest) gives a blank, "σ′v0 = 20 kPa is below the
      first loading stress (25 kPa)": the curve between the specimen's initial state and the first increment isn't
      measured, and extrapolating it would grade the sample on a guess.
    - **Δe counts from e0**, the initial void ratio, as Krage et al. define it ("from the specimen's initial state"),
      so a swell on flooding counts; `constant_stress` rows are never interpolated. A negative value (the specimen
      swelled past e0) is kept, with no class and a note.
13. **The class** (Lunne et al. 1997) uses this test's OCR, the only one at hand: 1 ≤ OCR < 2 uses the OCR 1–2 row,
    2 ≤ OCR ≤ 4 the OCR 2–4 row; outside, or with no OCR, the value is given without a class and the reason. For
    limits (l1, l2, l3): Δe/e0 < l1 "very good to excellent"; l1 ≤ Δe/e0 < l2 "good to fair"; l2 ≤ Δe/e0 ≤ l3
    "poor"; > l3 "very poor" (the table's "< 0.04" and "> 0.14" literally). **The caveat is on the result:**
    disturbance lowers σ′p and so this OCR, which can move a poor sample into the more lenient OCR 1–2 row; the
    docstring and the summary say so wherever a class is given, and the site page's Pitfalls repeat it.
14. **Validity** (intent: every method states its range). Oikawa's data are soils of the Akita plain with natural
    water content 25–941 % and e0 0.7–17 (p. 100); the agreement with Casagrande's σ′p is shown for w_n > 200 %
    (Figs. 9–10, p. 103), and below 200 % the e–log curve is itself linear in the normally consolidated range
    (conclusion 1, p. 104). The docstring states this; nothing is refused by water content, since the method is
    run on ordinary clays in the comparison that ranked it (🔬 below).
15. **`OedometerFit.to_frame()`**: one row per specimen: `specimen_id`, `loca_id`, `depth`, `geology_unit` (where
    the rows have them), `test_type`; the values of decision 2 and `effective_vertical_stress`, `void_ratio`;
    `count_loading_points`, `count_loading_after_reload`, `highest_stress_over_preconsolidation_stress`,
    `count_unload_runs`; the counts of decision 3; and one reason column per value that can be blank
    (`preconsolidation_stress_reason`, `swelling_index_reason`, `pacheco_silva_reason`,
    `overconsolidation_ratio_reason`, `normalized_void_ratio_change_reason`, `sample_quality_reason`).
    `attrs["units"]` gives the stress columns' unit. `.specimens` holds per specimen: each point (row, stress, e,
    branch, its role: `recompression`, `virgin`, `swelling` or left out with its reason, and whether it is past a
    reload), every split's sum of squares, both Oikawa lines (in log f–log σ′v), the Cc, Cr and each Cs line (in
    e–log σ′v), and the Pacheco Silva points (σA, e_B).
16. **The summary**, per specimen: "B-4-U1-C1: σ′p = 1620 psf (Oikawa; Pacheco Silva 1620 psf), Cc = 0.388, Cr =
    0.0382, Cs = 0.0590, CR = 0.186; 7 loading points, 4 on the virgin line, highest stress 9.85 σ′p", then OCR,
    Δe/e0 and its class with the caveat, the rows left out and the notes.
17. **Units** resolve as SPEC §2.6. The fit is made in `applied_vertical_stress`'s unit, or `display_units=`'s (kPa,
    psf), converted before fitting; `effective_vertical_stress` is converted to it. σ′p scales with the unit; the
    indexes, OCR and Δe/e0 don't change. Void ratios are dimensionless.
18. **P13, `ht.plot.consolidation_curve()`**: its rules are in its spec. It calls `oedometer_fit()` and draws its
    result, computing nothing of its own; it returns `(fig, ax, fit)`. The strain axis (the intent's "may")
    is left to Future enhancements: it needs e0 and a strain definition, which is TODO #73's question, settled in
    (c).

### Derivation
Oikawa (1987): f = 1 + e, the specific volume (p. 100); the log f–log p curve of a soft soil is "essentially
composed of two segments of straight line", and the stress where they intersect, p_y′, "agrees well with the
consolidation yield stress" by Casagrande's construction (p. 103; conclusions 4–5, p. 104). With the lines y = a1 +
b1 x (lower group) and y = a2 + b2 x (upper group), x = log10 σ′v and y = log10(1 + e), they cross at x = (a2 − a1) /
(b1 − b2), so **σ′p = 10^((a2 − a1) / (b1 − b2))**. Each line is the core's free least-squares fit: b = Sxy / Sxx,
a = ȳ − b x̄. The base of the logarithm cancels in the crossing; base 10 matches the indexes.

Cc and Cr are e–log σ′v slopes (sheet 06 §5.1): e = c − C log10 σ′v on each group, C = −Sxy / Sxx with y = e.

Pacheco Silva (Paniagua et al. 2016, §2.4): with the virgin line e = c_c − Cc log10 σ′v, (i) log10 σA = (c_c − e0) /
Cc; (ii) e_B = e_i + t (e_{i+1} − e_i), t = (log10 σA − log10 σ_i) / (log10 σ_{i+1} − log10 σ_i), for the loading
points i, i+1 either side of σA; (iii) log10 σ′p = (c_c − e_B) / Cc.

### Example data
Hand values for the example file's specimens (stresses in psf as stored; e as written), from the Derivation:
- **B-4-U1-C1** (13 ft): loading 250–16000 psf (7 points, the last past the reload). The 3 | 4 split wins (sums of
  squares 4.03e-6 against 2.32e-5): σ′p = 1624 psf, slope ratio 11.5, highest stress 9.85 σ′p, Cc = 0.388, Cr =
  0.0382, Cs = 0.0590, CR = 0.186; Pacheco Silva 1615 psf.
- **B-5-U2-C1** (18 ft): the 4 | 3 split wins (3.05e-6 against 9.93e-5): σ′p = 4232 psf, just past the 4000 psf
  point (decision 5.3), ratio 8.26, highest stress 3.78 σ′p, Cc = 0.254, Cr = 0.0326, Cs = 0.0399, CR = 0.137;
  Pacheco Silva 3943 psf.

The acceptance criteria use BH1-U3 (`site_si.ags`, kPa, exact) and hand-built frames; these are the docs page's.

### Sources
- **Oikawa, H. (1987).** Compression curve of soft soils. *Soils and Foundations* 27(3), 99–104,
  doi:10.3208/sandf1972.27.3_99. [V] from J-STAGE's scan, 2026-11-19: f = 1 + e (p. 100); the data (p. 100); the
  intersection as p_y′ and its agreement with Casagrande for w_n > 200 % (p. 103, Figs. 9–10); conclusions 1–5
  (p. 104). It gives no equation for the lines and no fitting procedure (decision 4).
- **Pacheco Silva (1970)**, via Paniagua, L'Heureux, Yang & Lunne (2016), NGM 2016, §2.4, p. 548 [V] (intent).
- **Lunne, Berre & Strandvik (1997)**, via Krage et al. (2015), 6ICEGE, Table 1, and Thakur (2016), NGM 2016 [V]
  (intent).
- 🔬 **Umar & Sadrekarimi**, the ranking behind intent decision 5, was read in its CGJ manuscript (cgj-2016-0203.R1);
  the published version isn't checked. The method's citation is Oikawa's, which stands alone; the ranking is only
  the reason it was chosen, so this doesn't block the build. The close-out cites the published version if found,
  else the manuscript as such.

### Acceptance criteria
Golden values hand-calculated from the Derivation (sums at 30 digits, rounded to 9 significant figures); tolerance
1e-7 relative unless stated. BH1-U3 is `site_si.ags`'s specimen (kPa): loading points (25, 0.795), (50, 0.788),
(100, 0.776), (200, 0.748), (400, 0.690), (800, 0.612), (1600, 0.520); unloads 800 → 200 (0.625) → 50 (0.638) and
1600 → 400 (0.538); reloads 200 (0.630), 800 (0.608); e0 = 0.800.
1. **σ′p (Oikawa):** BH1-U3's splits 3 | 4 and 4 | 3 have sums of squares 2.9810204e-5 and 1.1316206e-5; 4 | 3 wins,
   with lines a1 = 0.272639634, b1 = −0.0124551132, a2 = 0.427715041, b2 = −0.0764759614, and σ′p = 264.401656 kPa.
   Slope ratio 6.14012574, highest stress 6.05139931 σ′p.
2. **Cc, Cr, CR:** Cc = 0.282363888, Cr = 0.0508254999, CR = 0.156868827.
3. **Cs:** the first run (800, 200, 50 kPa) gives Cs = 0.0215925326 on the frame; the second run (1600, 400) is on the
   result with 0.0298973529 and its 2-point note. A frame with no unload has Cs blank, "no unloading".
4. **Pacheco Silva:** σA = 166.247579 kPa, e_B = 0.755466667, σ′p = 239.040472 kPa. With `void_ratio` blank, the
   check and CR are blank with "no initial void ratio".
5. **Counts:** BH1-U3 has 7 loading points, `count_loading_after_reload` = 1 (1600 kPa), `count_reloading` = 2,
   `count_unloading_not_used` = 1 (400 kPa), and 7 + 2 + 2 + 1 = 12 rows. A hand-built frame with a blank stress,
   a blank e, a stress of 0 and a `constant_stress` row counts each once under its reason.
6. **OCR and Δe/e0** (BH1-U3 with `effective_vertical_stress` set):
   - σ′v0 = 80 kPa: OCR = 3.30502070, e at σ′v0 = 0.779863137, Δe/e0 = 0.0251710786, "very good to excellent"
     (OCR 2–4 row);
   - σ′v0 = 150 kPa: OCR = 1.76267771, e = 0.759621050, Δe/e0 = 0.0504736875, "good to fair" (OCR 1–2 row);
   - σ′v0 = 20 kPa: OCR = 13.2200828, Δe/e0 blank, "σ′v0 = 20 kPa is below the first loading stress (25 kPa)";
   - σ′v0 = 300 kPa: OCR = 0.881338853, kept, with the warning naming BH1-U3, no class;
   - no `effective_vertical_stress` column: OCR, Δe/e0 and the class blank with the reason;
   - two σ′v0 values on one specimen's rows: an error naming it.
7. **Class limits:** hand-built values at each limit grade as decision 13 (0.04 → "good to fair" and 0.14 → "poor"
   in the OCR 1–2 row; 0.03 and 0.10 likewise in the 2–4 row); OCR exactly 2 uses the 2–4 row, OCR 4.0001 none.
8. **No clear break:** 8 points at 10 × 2^i kPa (i = 0–7), e = 1.200, 1.125, 1.049, 0.974, 0.899, 0.824, 0.748,
   0.673 (a straight e–log line), and an unload 1280 → 320 kPa (0.690): the best split (4 | 4) has slope ratio
   1.16891429 < 2, so σ′p, Cc, Cr, CR and the check are blank with the no-break reason; Cs = 0.0282363888.
9. **Crossing outside:** (10, 1.000), (20, 0.999), (40, 0.998), (80, 0.600), (160, 0.500), (320, 0.400): one split,
   ratio 133.464616, crossing at 7.93570770 kPa < 10 kPa: blank with the reason naming both.
10. **Virgin line too short:** (25, 0.795), (50, 0.788), (100, 0.776), (200, 0.766), (250, 0.745), (300, 0.722),
    (350, 0.702): the 4 | 3 split gives σ′p = 213.808933 kPa and 350 / σ′p = 1.63697557 < 2: blank with the reason.
11. **Too few points:** BH1-U3's first 5 loading points: blank, "6 loading points are needed (3 per line), 5 given".
12. **Ties and order:** a frame whose two best splits have equal sums of squares takes the lower; the same rows in
    another order of specimens give the same result; `group_keys()` order on the frame.
13. **Inputs:** a frame without `load_branch` gets it, with the note; a frame missing a required column, or a
    blank `specimen_id`, raises naming it; a template CSV with a blank optional column needs no unit for it.
14. **Units:** `site_us.ags` (psf) gives the same Cc, Cr, Cs, OCR and Δe/e0 as `site_si.ags`, and σ′p scaled by
    47.880259 Pa/psf (1e-9 relative); `display_units="SI"` on the psf file gives kPa.
15. **Example file:** B-4-U1-C1 and B-5-U2-C1 give the Example data's values (to the digits shown); the
    `SWELLPRESS` specimen with no increments gives every value blank, "no loading branch".
16. **Result object:** `kind = "derived"`, the function, unit and notes recorded; `.to_dict()` is JSON-serializable;
    `.to_frame()` has decision 15's columns; `.specimens` holds every split's sum of squares and every point's role.
17. **Published text** cites no internal file (the site and error tests pass).
