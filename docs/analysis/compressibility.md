# Compressibility: the oedometer fit

| | |
|---|---|
| **Status** | Living spec. The oedometer fit: σ′p, Cc, Cr, Cs, CR, OCR and the sample quality. mv, cv, k and Eoed, and rock swelling, extend it later |
| **Parent** | SPEC §4 (the oedometer fit) and §5 (derived results) |
| **Related** | [`m19a-oedometer-data.md`](../work/m19a-oedometer-data.md), [`m19b-compressibility.md`](../work/m19b-compressibility.md). The dataset: [`docs/data/datasets.md`](../data/datasets.md) (`p.oedometer()`). The figure: [P13](../plots/P13-consolidation-curve.md). Sheet 06 in [`docs/drafts/parameters/`](../drafts/parameters/README.md) |

Update this file in the same commit as any change to `oedometer_fit()`'s behavior, and SPEC §4 or §5 if the change
alters a rule there. The equations, sources, validity and each reason's wording are in the docstring, the published
reference ([`ht.analysis.oedometer_fit`](../site/reference/analysis.md)); they aren't repeated here.

## 1. Input and grouping
- `oedometer_fit(df, *, units=None, display_units=None) -> OedometerFit` reads `p.oedometer()`'s columns or a CSV in
  `ht.template("oedometer")`'s shape. Required: `specimen_id`, `applied_vertical_stress`,
  `void_ratio_at_increment_end`; missing ones, a blank `specimen_id`, a negative void ratio and an unknown
  `load_branch` are errors naming the rows.
- **One fit per `specimen_id`,** in `group_keys()` order; no `group_by=`, since a curve belongs to one specimen. Rows
  keep the frame's order within a specimen (the order the increments were applied).
- `load_branch` is read where present, else added by `oedometer_load_branch()`, with a note. A point is `loading`
  once its stress exceeds the previous maximum; the point at the previous maximum is `reloading`.
- `void_ratio` (e0) and `effective_vertical_stress` (σ′v0) are one value per specimen; more than one non-blank value
  is an error naming it.
- **Units** resolve as SPEC §2.6. The fit is made in `applied_vertical_stress`'s unit, or `display_units=`'s,
  converted before fitting; σ′v0 is converted to it. Only σ′p and σ′v0 scale with the unit.

## 2. Which rows each value reads
- **σ′p, Cc and Cr:** `loading` rows only. A reload slope is never Cc. The loading points past a reload are kept
  (`count_loading_after_reload`, marked on P13): leaving them out would take the virgin line's highest points.
- **Cs:** the first unload run, the point it starts from and the consecutive `unloading` rows after it, at least 2
  points. Every run's Cs is on `.specimens`; the frame's is the first run's, the loop the lab ran on purpose. The
  reload is never used, and the runs are never fitted together.
- **Counted, never dropped:** every row no line uses is counted once, under the first reason that applies:
  `count_no_applied_stress`, `count_no_void_ratio`, `count_stress_not_positive`, `count_constant_stress`,
  `count_reloading`, `count_unloading_not_used`.

## 3. σ′p by Oikawa (1987), and when it isn't one
- Two least-squares lines in x = log10 σ′v, y = log10(1 + e), one per group of a split of the loading points in
  stress order, at least 3 points a group. Every split is tried; the smallest total sum of squares wins, the lower
  split on a tie. σ′p is where the two lines cross. Oikawa gives the construction, not a fitting procedure, so the
  search is hangtu's, and the same increments always give the same σ′p.
- **Checked in this order;** the first that fails blanks σ′p, Cc, Cr, CR and the check, with its reason (Cs is still
  given):
  1. fewer than 6 loading points;
  2. no clear break: the upper line isn't falling, or isn't at least **2** times as steep as the lower;
  3. the crossing outside the loading stresses (not "between the groups": a break between the third-last and
     second-last points crosses just past the upper group's first point, and is a good curve);
  4. the highest loading stress below **2** σ′p (sheet 06 §7 says 2–3; the ratio is on the result, and the summary
     remarks below 3).
- Nothing is extrapolated, and nothing is refused by water content: Oikawa's data are soft soils, stated in the
  docstring as the method's tested range.

## 4. Cc, Cr, Cs and CR
- e–log10 σ′v least-squares slopes, negated, as the soil models use them: Cc from the upper group, Cr from the lower,
  Cs from the first unload. Their lines don't cross exactly at σ′p (fitted in another space); P13 marks σ′p on the
  loading curve.
- CR = Cc / (1 + e0), e0 the specimen's `void_ratio`; blank e0 gives "no initial void ratio".

## 5. The check: Pacheco Silva (1970)
- The Cc line meets e0 at σA; e_B is the loading curve's e at σA (linear in e against log σ′v between the loading
  points either side); the horizontal through e_B meets the Cc line at the check's σ′p.
- e0 is `void_ratio` only, never the first increment's starting e (which holds the seating load or a swell). σA
  outside the loading stresses gives a blank with the reason. The two σ′p are both reported and drawn, never
  compared or warned about.
- Casagrande's construction and the work method aren't built: TODO lists them with their trigger.

## 6. OCR, Δe/e0 and the sample quality
- OCR = σ′p / σ′v0. Blank σ′v0 or σ′p gives a blank with the reason, never an assumed σ′v0. OCR below 1 is kept,
  with one warning per call naming the specimens.
- Δe/e0 = (e0 − e at σ′v0) / e0, e at σ′v0 interpolated on the loading points. σ′v0 outside the loading stresses
  gives a blank; Δe counts from e0, so a swell on flooding counts; a negative value has no class and a note.
- **The class** (Lunne et al. 1997, the limits as Krage et al. 2015, Table 1 give them) uses this test's OCR: OCR
  1 ≤ OCR < 2 the OCR 1-2 row, 2 ≤ OCR ≤ 4 the OCR 2-4 row; outside, no class with the reason. Boundaries: below l1,
  l1 ≤ x < l2, l2 ≤ x ≤ l3, above l3. **The caveat travels with the class:** disturbance lowers σ′p and so this OCR,
  which can move a poor sample into the more lenient row; the summary, P13's footnote and the site pages say so.

## 7. The result
- `OedometerFit`, a derived result (SPEC §5): `.to_frame()` has one row per specimen with its identifiers, the
  values, the counts and one `…_reason` column per value that can be blank; `.specimens` holds each point's role,
  every split's sum of squares, every line and the check's σA and e_B, so P13 draws without computing.
- The fitted σ′p takes the parameter's name, `preconsolidation_stress`, as the SPT correlation's estimate does; the
  two keep apart by `correlation_name` (SPEC §5).
