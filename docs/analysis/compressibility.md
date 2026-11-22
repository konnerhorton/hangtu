# Compressibility: the oedometer fit, increments and c_v from readings

| | |
|---|---|
| **Status** | Living spec. The oedometer fit: σ′p, Cc, Cr, Cs, CR, OCR and the sample quality (§1–7). The increments: m_v, Eoed, Eur,oed and k (§8). c_v from settlement–time readings (§9). Rock swelling extends it later |
| **Parent** | SPEC §4 (the oedometer fit) and §5 (derived results) |
| **Related** | [`m19a-oedometer-data.md`](../work/m19a-oedometer-data.md), [`m19b-compressibility.md`](../work/m19b-compressibility.md), [`m19c-consolidation.md`](../work/m19c-consolidation.md), [`m19c2-cv-readings.md`](../work/m19c2-cv-readings.md). The datasets: [`docs/data/datasets.md`](../data/datasets.md) (`p.oedometer()`, `p.oedometer_readings()`). The figures: [P13](../plots/P13-consolidation-curve.md), [P14](../plots/P14-consolidation-coefficients.md), [P15](../plots/P15-consolidation-time-curves.md). Sheet 06 in [`docs/drafts/parameters/`](../drafts/parameters/README.md) |

Update this file in the same commit as any change to `oedometer_fit()`'s, `oedometer_increments()`'s or
`consolidation_coefficient_from_readings()`'s behavior, and
SPEC §4 or §5 if the change alters a rule there. The equations, sources, validity and each reason's wording are in the
docstrings, the published reference ([`ht.analysis.oedometer_fit`](../site/reference/analysis.md),
[`ht.analysis.oedometer_increments`](../site/reference/analysis.md),
[`ht.analysis.consolidation_coefficient_from_readings`](../site/reference/analysis.md)); they aren't repeated here.

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

## 8. Increments: m_v, the moduli and k
`oedometer_increments()` adds columns to the rows it is given (a copy, no row dropped or reordered); it is not a
derived result, since each value belongs to one increment.
- **m_v per increment** from the void ratio at the increment's start, e1, not the specimen's e0 (BS 1377-5:1990,
  3.6.2.2.4, in void ratios). Per `specimen_id` in row order, σ′1 is the previous row's stress, written to
  `applied_vertical_stress_at_increment_start`; e1 is the row's `void_ratio_at_increment_start`, else the previous
  row's end, with a note. The first increment's start is the seating load, which no file gives: blank, with the
  reason. The recomputed value and the lab's (`reported_coefficient_of_volume_compressibility`) stay apart.
- **Unloading and reloading** use the same formula, as hangtu's extension: BS 1377-5 defines m_v on loading
  increments only, and the docstring says so.
- **An m_v of 0 or less is kept** as computed (E002 reports the loading case); the moduli and k of that row are blank
  with the reason.
- **Eoed and Eur,oed** = 1/m_v, in two columns by branch (`constrained_modulus` on loading rows,
  `unload_reload_constrained_modulus` on unloading and reloading rows), since stage D selects each on its own. Each is
  a secant over its increment, so no stress is chosen to report it at: the row gives σ′1 and σ′2, and P14 draws the
  segment. Sheet 11's Cc and Cs forms are a tangent of a fitted line, a different value, left to the Hardening Soil
  reference moduli.
- **At σ′v0**, the increment spanning it, never an interpolation: `spans_effective_vertical_stress` is True on the
  first loading row with σ′1 < σ′v0 ≤ σ′2 and on the first unloading or reloading row whose range holds σ′v0. A σ′v0
  no increment spans gives all False and a note; nothing is extrapolated. Values of two increments aren't
  interpolated because each is a secant over its own range.
- **k = c_v·m_v·γw** per increment, one column for each of the lab's c_v (`hydraulic_conductivity_root_time`,
  `…_log_time`), so neither method is preferred; m_v the recomputed one, γw `ht.settings.water_unit_weight` (a setting,
  not a judgment), recorded in `attrs`. The relation is Terzaghi's definition of c_v rearranged (Freeze & Cherry 1979,
  §8.3, Eq. 8.22). Not under `hydraulic_conductivity`, which holds permeameter and field values: lab and field k aren't
  pooled. With `consolidation_coefficients=` (the rows of §9), the same relation gives k from hangtu's c_v in two
  more columns (`hydraulic_conductivity_from_readings_root_time`, `…_log_time`), joined on `specimen_id` and
  `test_stage` as text, with the c_v, its basis and its reason carried beside them. Lab and recomputed values stay in
  separate columns. A reduced row matching no increment is one warning naming them (data the call drops); an
  increment with no reduced row is blank, "no readings".
- **Notes** (the branch added, a start void ratio borrowed, no σ′v0 column, no increment spanning σ′v0) go to
  `attrs["oedometer_increments"]["notes"]`, not warnings: the σ′v0 note would fire on every call on `p.oedometer()`.
- **Strain**, for a plot's ε axis and the work method (TODO #76), is ε = (H0 − H)/H0 = (e0 − e)/(1 + e0), referred to
  the initial thickness (BS 1377-5:1990, 3.6.2.1). The strain on H1, the increment's start, belongs to m_v only.
- **Units:** with `display_units=`, `applied_vertical_stress` and `effective_vertical_stress` are written converted
  too, so a row's σ′1 and σ′2 share a unit. The `reported_` columns are never converted; P14 converts them to draw.

## 9. c_v from readings
`consolidation_coefficient_from_readings()` reduces settlement–time readings (one row per reading, §6.18 of
`datasets.md` or the `oedometer_readings` template) to one row per increment, with c_v by the root time and log time
constructions of BS 1377-5:1990, 3.6.3. Both are given; neither is preferred, as the lab's two c_v columns aren't.
The constructions are a test read by a stated rule, not a judgment (SPEC §4, "Choices"): where the rule reads a curve
badly, an override replaces one part's range and is recorded.
- **Grouping:** by `specimen_id` and `test_stage`, increments in order of first appearance, readings sorted by
  `elapsed_time` within each. A blank time or displacement and a negative time are left out, one note per kind.
  `constant_stress` increments get no c_v. Unloads and reloads get the same constructions as hangtu's extension (BS
  defines them on load increments). A blank `specimen_id` or `test_stage` is an error: the reading has no increment.
- **Orientation, not datum:** y = s (d − d_first), s the sign of the increment's movement, so every construction
  works on a curve that grows; points are written back in the file's datum and sign. A shift or a change of sign
  gives the same c_v. The t = 0 reading sets d_first only (it precedes the immediate compression).
- **Root time:** the early line is least squares on √t over the readings with t > 0 and y ≤ ½ y_last; the 1.15 line
  from its intercept d0; t90 where the curve (readings joined linearly in √t) first falls to the 1.15 line after the
  early portion; c_v = 0.111 H̄²/t90.
- **Log time:** the secondary line is least squares over the last log cycle (t ≥ t_last/10); the tangent at the
  inflexion is the steepest three-reading line before it; a tangent less than twice as steep as the secondary line is
  "no clear secondary portion" (the factor of §3's break). d0 is the mean of the three largest 1:4 pairs before the
  tangent's middle reading; d100 where the lines cross; t50 where the curve (linear in log t) reaches (d0 + d100)/2;
  c_v = 0.026 H̄²/t50.
- **Linear interpolation,** not a smooth curve: what a hand construction on the standard's plot does. A monotone
  cubic moved results by a few percent on Terzaghi curves, less than the two methods differ.
- **H̄ = (H1 + H2)/2** from the specimen height and the increment's void ratios, not from the readings (whose datum
  is the file's). Blank inputs give a blank c_v with the reason, and the construction's times and points still given.
  BS's coefficients (0.026, 0.111), not Terzaghi's T50 and T90, so c_v matches a BS lab's; the docstring gives the
  difference (0.4 %). Double drainage.
- **A construction that can't read the curve gives a reason, never a guess:** too few readings, no movement, an
  early portion too short or not straight, t90 after the last reading, too few readings in the last cycle or 1:4
  pairs, no clear secondary portion, d100 outside the readings, t50 before the first reading. Each reason's wording
  is in the docstring.
- **Overrides** (`overrides=`, `ht.template("consolidation_overrides")`): one row per part (`early` for either
  method; `inflexion`, `secondary` for log time) with an inclusive time range and a required reason. Only that part's
  range changes. An override for an increment the frame lacks, a duplicate, an unknown method or portion, a reversed
  or open range, a blank reason or times without units is an error naming the row, since a typo would otherwise run
  as the rule. A range too short to fit is a reason, not an error. Recorded in each method's `_basis` (`rule`,
  `override`) and in `attrs`. Storing them with the project is TODO #77.
- **Result:** one row per increment with its identity and increment values from its first reading, the times, the
  points (d0, d50, d90, d100), H̄, both c_v with basis and reason. Notes go to
  `attrs["consolidation_coefficient_from_readings"]["notes"]`. Times stay in minutes in both unit systems;
  `display_units=` converts displacements, H̄ and c_v.
- **P15 draws the same fit:** the plot calls the same private `constructions()`, so a panel never disagrees with the
  frame.
