# M13 (b2): SPT correlations for s_u, σ′p/OCR and K0

## Intent
M13 is wave 1's first milestone (SPEC §1.3, §12.4). Unit (b1) (`docs/work/m13b1-spt-framework.md`) built (N1)60,
hammer efficiency by hole, the correlations framework and two φ′ correlations. The rest of the first SPT set
splits in two:
- **(b2)**, this one: strength and stress history, the SPT correlations for s_u (sheet 05), σ′p and OCR (06) and
  K0 (07), stage C of each.
- **(b3)**: stiffness, E (sheet 08) and Vs (10).

**Goal:** from a project's SPT data, its σ′v and, where a correlation needs it, a plasticity index, an engineer
gets estimates of s_u, σ′p/OCR and K0 from published SPT correlations, each on b1's framework: named on its rows,
reading the one input it was derived with, NaN with a reason outside its range, and comparable on P01 and P07.

**Why:** SPT is often the only data in the clays of a US project, and these correlations are applied by hand with
little check of the N basis or the soil they were derived from. They are also the first correlations on the
framework that aren't for sands, so they test the parts b1 left untested: a lab input (PI) beside N, a target in
stress units that converts for display, a field-N correlation, and a correlation published as a range.

**SPEC and TODO touched:** §4 (correlations: chaining discouraged, soil-class mapping; judgments: PI by geology
unit), §10.3 (new registry columns), §12.4 (M13 in four units: a, b1, b2, b3); P01 (a value range at a depth);
TODO #20 (s_u, σ′p/OCR, K0 settled here; E and Vs in b3), #37 (soil types, settled here as an opt-in USCS map).

### Decided
1. **Chaining is discouraged, not prevented.** A correlation's inputs are meant to be test data, or values derived
   directly from them (N60, (N1)60, σ′v), not another correlation's estimate: the transformation errors compound
   and the result reads as more certain than it is. The engineer may still do it; hangtu warns and records it
   (review decision 1) and offers no shortcut for it. K0 from φ′ and OCR (Mayne & Kulhawy 1982) and SHANSEP s_u
   from OCR are W3 (stage B), on measured inputs.
2. **On b1's framework, unchanged where it holds:** one function per published correlation, named after its
   source; its entry in `config/correlations.yaml` with the drift test; the one input column by registry name,
   with no argument to choose another; NaN with `correlation_note` and one warning by reason; every entry in
   `attrs["correlations"]`; the P01 footnote by note. A correlation whose equation, constants or range can't be
   verified against its source is cut, not built (b1 Decision 11).
3. **Candidates** (sheets 05–07, analysis draft §4.2), to verify in the spec step:
   - **s_u:** Stroud (1974), s_u = f1 N60 with f1 by PI; Sowers (1979), lines of s_u against N for low, medium
     and high plasticity; Terzaghi & Peck (1967), consistency classes giving a q_u band for an N range, the first
     range output.
   - **σ′p and OCR:** Mayne & Kemper (1988), σ′p ≈ 0.58 N pa, on field N (Kulhawy & Mayne 1990, Fig. 3-18).
   - **K0:** Kulhawy et al. (1989), K0 ≈ 0.073 N60 / (σ′v/pa), for clays, with its large bias stated (b = 2.16,
     δ = 0.70 on the TC304 database).
4. **Wave spec step** (process.md, "Stages and waves"): promote sheets 05, 06 and 07 to `docs/site/parameters/`,
   verify the [U] citations they use and hand-calculate golden values, apply the publishing rule (TODO #30), and
   propose the new names against the registry.

### Out of scope
- E and Vs (b3), and sheets 08 and 10.
- Stage B of each parameter: lab and vane s_u, the oedometer σ′p fits, Jaky and Mayne & Kulhawy K0 from measured
  φ′ and OCR, SHANSEP (W2, W3).
- CPT and DMT correlations (later waves). Relative density (M14).
- Selection between estimates and measured values (stage D, M18), and the two-panel correlation profile (TODO
  #38).
- PI keyed by depth within a unit, and PI from the nearest Atterberg test (not a good rule: review decision 4).

### Decisions (intent review, 2026-10-23)
1. **Chaining warns.** When an input column holds estimates (its rows carry a `correlation_name`), the function
   runs, warns that the input is itself an estimate and names that correlation, and records it on the rows in a
   new column (proposed `correlation_input`), since `correlation_name` is overwritten and `attrs` are easily lost.
   Reason: the engineer decides; the record keeps the chain reviewable.
2. **Range outputs, as target-specific columns.** A correlation that gives a band writes `<target>_lower` and
   `<target>_upper` (registry columns, so units and labels work) beside `<target>`, which holds the central value
   or NaN. Generic `estimate_lower` / `estimate_upper` columns were rejected: they would have no quantity in the
   registry. Reason: Terzaghi & Peck's classes are bands, and a band shouldn't be drawn as a point.
3. **P01 draws a value range at a depth.** When `<value>_lower` and `<value>_upper` exist, a horizontal bar
   between them at the test's depth, with the marker where there is a central value. A P01 spec change in this
   unit. Reason: valuable on its own, for any value reported as a range.
4. **Soil-class map, opt in** (TODO #37, option c). Each entry keeps the source's words in `applies_to`; beside
   them, hangtu's proposed USCS groups, labeled as hangtu's reading of the source, which a project can override.
   An argument (proposed `soil="uscs_symbol"`) turns it on; then rows outside the groups get NaN with a new note
   ("not for this soil") and rows with no class "soil type unknown". Without it, b1's rule holds: pass the rows
   a correlation applies to. USCS only for now. Reason: the mapping is an interpretation, so it is visible,
   overridable and never applied unasked.
5. **PI by geology unit, as a judgment.** `plasticity_index` in the judgments file, keyed by geology unit, with no
   default. A small general function puts a keyed judgment on the rows (as `vertical_stress()` puts σ′v), recorded
   in `attrs["judgments"]`; Stroud then reads the `plasticity_index` column like any input. The explicit argument
   always wins. A helper shows each unit's PI from the project's Atterberg tests (median, count, range) to inform
   the judgment; it never fills one in. Nearest-test PI was rejected as a rule; PI by depth may come later.

6. **A PI column on the rows wins over the judgments file**, with a warning when both are present and differ; the
   explicit argument wins over both. Reason: data the engineer put on the rows is the more specific choice.
7. **USCS comes from a column the user supplies** on the rows (`uscs_symbol`). hangtu doesn't derive it from
   `soil_class` or the log's description, and doesn't take it by geology unit. Reason: lab USCS is on samples, not
   SPT rows, and a derived class would be hangtu's guess.
8. **A band with no central value draws as the bar alone.** No midpoint is drawn or stored. Reason: a midpoint the
   source doesn't give would be hangtu's invention.
9. **Statistics on ranges are M15's:** a band is an interval, not two values. Noted as a constraint for M15
   (`docs/drafts/phase3-stats.md`) at the close-out, not designed here.

### Open (for the spec step)
- **Field N.** Mayne & Kemper read `spt_n`, not N60. Confirm from the source, and whether a field-N correlation
  should warn when the data has an energy ratio, since N60 would then be known.
- **σ′p or OCR as the target.** One correlation gives both (OCR = σ′p / σ′v0): one target column with the other
  derived, or two.
- **Size.** The P01 range bar, the soil map and the PI judgment each add work beyond the correlations. If the plan
  runs past one sitting, the P01 range bar goes first as its own small unit.

## Spec

The b2 correlations on b1's framework, the range outputs and P01's range bar, the opt-in USCS map, the chaining
warning, and PI by geology unit. Numbered items refer to this section's decisions unless they say "intent" or
"review".

### Sources checked in this step
| Item | Source and locator | Result |
|---|---|---|
| s_u, Stroud (1974) | FHWA GEC 5 (Loehr et al. 2016), Eq. 7.19, p. 7-38 | [V] s_u = f1 N60 pa / 100; f1 = 4.5 for PI ≳ 30 and 5.5 for PI ≅ 15; "somewhat lower bound values"; "SPT N-values are generally a poor predictor of undrained shear strength". No N range stated. Sheet 05's "≈ 4.4 kPa for PI > 30" is corrected |
| s_u, Terzaghi & Peck (1967) | Kulhawy & Mayne (1990), EPRI EL-6800, Table 4-10, p. 4-54, after Terzaghi & Peck (1967) p. 347 | [V] s_u/pa by N (blows/ft): 0–2 < 1/8; 2–4 1/8–1/4; 4–8 1/4–1/2; 8–15 1/2–1; 15–30 1–2; > 30 > 2. "Developed primarily using unconfined compression tests" (p. 4-53). N is field N: "the SPT N values have not all been standardized to the same energy level" (p. 4-53) |
| s_u, the table's fit | EPRI Eq. 4-59, p. 4-53 | [V] s_u/pa ≈ 0.06 N, "from the results of this table". Not built (Decision 6) |
| s_u, Sowers (1979) | EPRI Fig. 4-50, p. 4-54, after Djoenaidi | Only as lines on a chart, with no equation; the coefficients would be read off the chart. **Cut** (new TODO #39) |
| σ′p, Mayne & Kemper (1988) | EPRI Fig. 3-9, p. 3-10 ("based on Mayne and Kemper, p. 144, and others") | [V] σ′p = 0.47 N pa; n = 126, r² = 0.699, S.D. = 4.37 pa; 49 intact and 2 fissured clays, the fissured above the trend. N axis 0.5–200 blows/ft |
| OCR, Mayne & Kemper (1988) | EPRI Fig. 3-18, p. 3-18 ("p. 143, and others") | [V] OCR = 0.58 N pa / σ′v0; n = 112, r² = 0.661, S.D. = 3.82; 48 intact and 3 fissured clays. Axis N pa/σ′v0 1–100, OCR 1–50. Sheet 06's n = 110, r² = 0.766 are corrected |
| K0, Kulhawy et al. (1989) | EPRI Eq. 3-31, p. 3-27; Fig. 3-30, p. 3-28 ("Kulhawy, et al., p. 129") | [V] K0 = 0.073 N pa / σ′v0; n = 57, r² = 0.771, S.D. = 0.43; 13 intact and 5 fissured clays. Axis N pa/σ′v0 0–60. **N is field N**: sheet 07's N60 is corrected |
| K0, transformation bias | Ching & Schweckendiek (2021), TC304, Table 5.2, p. 178 | [V] Evaluated as 0.073 N60/(σ′v/pa) on CLAY/12/3997: n = 74, b = 2.16, δ = 0.70, where b is the mean of measured / predicted (§5.1, p. 176): measured K0 averaged about twice the estimate |
| References | EPRI §3 refs 11, 41; §4 ref 4; §6 ref 16; GEC 5 references | Mayne & Kemper (1988), GTJ 11(2), 139–147; Kulhawy, Jackson & Mayne (1989), Foundation Engineering: Current Principles and Practices, ASCE, 121–134; Terzaghi & Peck (1967), Soil Mechanics in Engineering Practice, 2nd ed., Wiley; Stroud (1974), ESOPT-II, Vol. 2, 367–375 |

### Changes
- **SPEC §4:** the "Correlations" bullet gains "chaining one correlation into another is discouraged, not
  prevented: it warns and is recorded (`correlation_input`)"; "a band is returned as `<target>_lower` and
  `<target>_upper`"; "an opt-in USCS map (`uscs=`) gives NaN with a reason for other soils". "Judgment inputs":
  `plasticity_index` by geology unit joins the first judgments. **§12.4:** M13's row names four units (a, b1,
  b2, b3).
- **P01 spec** (`docs/plots/P01-property-profile.md`): §3 gains the `<value>_lower` / `<value>_upper` columns, §7
  the range bar, §11 its edge cases, §12 its criteria (Decision 9).
- **M15 draft** (`docs/drafts/phase3-stats.md`): a constraint that a band is an interval (review 9), at the
  close-out.
- **`docs/drafts/analysis.md` §4.2:** s_u, σ′p/OCR and K0 marked as this unit's; Sowers cut (TODO #39).
- **`columns.yaml`, `defaults.yaml`, `config/correlations.yaml`, `_judgments.py`:** Decisions 5, 7, 10, 11.
- **TODO:** #20 records the b2 set and that E and Vs are b3's; #37 moves to Done (review 4, 7); new #39 (Sowers
  1979, verify against the source before building).
- **b1 rename** (Decision 2): the two φ′ functions, their config keys, tests, sheet 04, the correlations guide,
  its example and the reference page, in one refactor commit.
- **Docs site:** sheets 05, 06 and 07 promoted (Decision 13); the correlations guide gains ranges, the USCS map,
  PI by unit and chaining; reference entries for every new public name.
- **Parameter index:** at the close-out, stage C of 05, 06 and 07 becomes **part built** (SPT: M13 b2).

### Decisions
1. **Four correlations**, each on b1's framework (intent 2), reading the one N its source used:

   | Function | Target | Reads | Equation | Range |
   |---|---|---|---|---|
   | `undrained_shear_strength_stroud_1974` | `undrained_shear_strength` | `spt_n60`, `plasticity_index` | s_u = f1 N60 pa / 100 | PI ≥ 15 |
   | `undrained_shear_strength_terzaghi_peck_1967` | `undrained_shear_strength` (band) | `spt_n` | s_u/pa by N class, Table 4-10 | N ≥ 0 |
   | `preconsolidation_stress_mayne_kemper_1988` | `preconsolidation_stress` | `spt_n` | σ′p = 0.47 N pa | 0.5 ≤ N ≤ 200 (the chart's axis) |
   | `overconsolidation_ratio_mayne_kemper_1988` | `overconsolidation_ratio` | `spt_n`, `effective_vertical_stress` | OCR = 0.58 N pa / σ′v0 | 1 ≤ N pa/σ′v0 ≤ 100 (the chart's axis) |
   | `at_rest_earth_pressure_coefficient_kulhawy_et_al_1989` | `at_rest_earth_pressure_coefficient` | `spt_n`, `effective_vertical_stress` | K0 = 0.073 N pa / σ′v0 | 0 < N pa/σ′v0 ≤ 60 (the chart's axis) |

   All are for clays; pa = 100 kPa (b1 Decision 8), converted with pint. Refusals give no estimate (b1 Decision 2).
   Each docstring states the scatter the source gives, that SPT is a poor predictor in clay (GEC 5 p. 7-38; EPRI
   p. 4-53), and for K0 the TC304 bias. σ′p and OCR are two regressions on different data (0.47 vs 0.58), so
   they are two correlations with their own targets, not one derived from the other (intent, open item).
2. **Naming: target first.** b1's rule, one function named after its source, collides here (Mayne & Kemper give
   σ′p and OCR) and in b3 (Kulhawy & Mayne 1990 give E as well as φ′). Every correlation is named
   `<target>_<authors>_<year>`, with three or more authors as `<first>_et_al_<year>`, so tab completion groups by
   property. `correlation_name` and the config keys are the function name; the target in it is what lets
   Decision 8 tell Mayne & Kemper's two correlations apart. b1's two functions are renamed
   (`effective_friction_angle_hatanaka_uchida_1996`, `effective_friction_angle_kulhawy_mayne_1990`) in their own
   refactor commit; they are not in a release (0.1.0 predates b1), so no alias is kept.
3. **Stroud's f1.** GEC 5 gives two values, 4.5 at PI ≳ 30 and 5.5 at PI ≅ 15, and nothing between. PI ≥ 30
   gives s_u = 4.5 N60 pa/100; 15 ≤ PI < 30 gives the band 4.5–5.5 N60 pa/100 with no central value (review 8:
   nothing interpolated); PI < 15 is "below range".
4. **Field N.** Terzaghi & Peck, Mayne & Kemper and Kulhawy et al. were derived on N as measured (blows/ft), before
   energy correction was practice, so they read `spt_n`. No warning when the data has an energy ratio: the
   docstring says the source's N was field N from the hammers of its time, and that hangtu doesn't convert it.
5. **Terms in a range.** OCR and K0 have their range on N pa/σ′v0, not on one input. A config entry may define a
   named term (`normalized_n: spt_n × pa / effective_vertical_stress`) with its range; the function computes it
   and the framework checks it as it checks an input. The drift test covers its bounds.
6. **Band outputs** (review 2). A correlation that gives a band writes `<target>_lower` and `<target>_upper`,
   with `<target>` the central value or NaN. Terzaghi & Peck's classes are N lower bound inclusive, the boundaries
   of `config/spt_classes.yaml`'s `cohesive` table (the same source), so `spt_class(table="cohesive")` and the
   band agree. The "< 1/8" class has lower 0 (s_u can't be negative; the docstring says so); the "> 2" class has
   lower 2 pa and a blank upper, an open band. EPRI's s_u/pa ≈ 0.06 N is a fit through the same table and
   isn't built, so the table isn't counted twice in a comparison.
7. **Names** (checked against `columns.yaml`, `defaults.yaml`, the settings and the plot arguments; no collisions):

   | Name | Kind | Quantity | Label |
   |---|---|---|---|
   | `undrained_shear_strength_lower`, `_upper` | column | stress | as `undrained_shear_strength`, "(lower)" / "(upper)" |
   | `preconsolidation_stress` | column | stress | Preconsolidation stress, σ′p |
   | `overconsolidation_ratio` | column | dimensionless | Overconsolidation ratio, OCR |
   | `at_rest_earth_pressure_coefficient` | column | dimensionless | At-rest earth pressure coefficient, K0 |
   | `correlation_input` | column | text | The correlation whose estimate an input came from (Decision 8) |
   | `uscs=` | argument | – | Decision 10 |
   | the functions of Decisions 1, 11, 12 | API | – | |

   Presets for `preconsolidation_stress`, `overconsolidation_ratio` (log) and `at_rest_earth_pressure_coefficient`.
   `<target>_lower` / `_upper` exist in the registry only for targets that have a band correlation.
8. **Chaining warns** (review 1). Before computing, the framework checks each input column against the rows'
   `correlation_name`: where a row's correlation has that column as its target, the input is an estimate. The
   call runs, warns once ("spt_n60 … is an estimate from …; chaining correlations compounds their errors"), and
   writes the upstream name to `correlation_input` on those rows. Nothing in b2 takes an estimate, so the check is
   tested with a correlation built for the test.
9. **P01 range bar** (review 3, 8). When `<value>_lower` or `<value>_upper` is in `df`:
   - both bounds: a horizontal bar between them at the row's depth, in the group's color, with the marker at
     `<value>` when it isn't blank;
   - one bound only: P01's qualifier caret at it (▷ for a lower bound alone, ◁ for an upper bound alone), as a
     `qualifier` draws it, with the bar's style; no bar;
   - x-limits include the bounds; a bound beyond `xlim=` is drawn at the edge with the arrow and counted;
   - footnote: "n shown as a range"; a row with a value and no bounds draws as now. The stats box leaves ranges
     out and says so ("ranges not included: n"), until M15 (review 9);
   - a `qualifier` on a row with bounds is an error naming the rows.
10. **USCS map, opt in** (review 4, 7). Each entry gains `uscs:`, hangtu's proposed groups, with `uscs_basis:` saying
    it is hangtu's reading of `applies_to`:
    - the clay correlations (Stroud, Terzaghi & Peck, Mayne & Kemper, Kulhawy et al.): CL, CH
    - the φ′ correlations (Hatanaka & Uchida, Kulhawy & Mayne): SP, SW, SP-SM, SW-SM ("relatively clean"; no
      gravels)

    `uscs=None` (default) reads nothing. `uscs="proposed"` reads the user's `uscs_symbol` column on the rows and
    uses the entry's groups; a list (`uscs=["CL", "CH", "CL-ML"]`) uses those instead, recorded in attrs. Rows
    outside get NaN with "not for this soil", rows with a blank `uscs_symbol` "soil type unknown"; P01's footnote
    counts both. A missing `uscs_symbol` column is an error saying to add it (it is never derived).
11. **PI by geology unit** (review 5, 6). `plasticity_index` becomes a judgment kind: keyed `values`, `by:` a
    stratigraphy column, field `plasticity_index` (percent; `units: {plasticity_index: "%"}`), no project value
    without a reason, as `unit_weight`. `ht.analysis.add_judgment(df, name, *, value=None, judgments=None)` puts
    it on the rows: `value=` (one number, or `{key: value}`) wins; else an existing `plasticity_index` column on the
    rows, where filled, with blanks filled from the file and one warning counting rows where the two differ; else
    the file; else an error naming the judgment. Recorded in `attrs["judgments"]` as `vertical_stress()` does.
    Stroud reads the column like any input.
12. **The PI summary.** `ht.analysis.summary_by(df, value, *, by="geology_unit")` returns n, median, min and max
    per group, from any dataset (`p.atterberg()` for PI), to inform the judgment; it never writes one. SPEC §5's
    `describe` (M15) is the full version; this is kept small so M15 can replace or absorb it.
13. **Pages 05, 06 and 07** promoted under the publishing rule. The SPT methods link their functions; the lab and
    field methods (UU, vane, oedometer fits, Jaky, Mayne & Kulhawy) say W2 or W3. Their remaining [U] items
    (sheet 05: the Bjerrum μ fit, Lunne et al. 1997; sheet 06: the bilinear, Casagrande, Pacheco Silva and Becker
    constructions, Skempton's Cc, Mayne's generalized σ′p exponents, the Lunne sample-quality bands; sheet 07:
    Jaky's original form, Mayne 2007, Marchetti 1980) are verified with a locator or cut, and the commit lists
    which. The sheets get this step's corrections (Stroud's f1; Fig. 3-18's statistics; K0 on field N).

### Acceptance criteria
1. **s_u golden values** (pa = 100 kPa):

   | Function | N60 or N | PI | Expected (kPa) |
   |---|---|---|---|
   | `undrained_shear_strength_stroud_1974` | N60 10 | 40 | 45.0 |
   | `undrained_shear_strength_stroud_1974` | N60 20 | 30 | 90.0 |
   | `undrained_shear_strength_stroud_1974` | N60 10 | 20 | band 45.0–55.0, central blank |
   | `undrained_shear_strength_stroud_1974` | N60 10 | 12 | NaN, "below range" |
   | `undrained_shear_strength_terzaghi_peck_1967` | N 0, 2, 7, 8, 29, 30 | – | 0–12.5; 12.5–25; 25–50; 50–100; 100–200; 200 to open |

   US twin: Stroud's 45.0 kPa is 939.9 psf to 0.1 %.
2. **σ′p, OCR and K0 golden values:**

   | N | σ′v0 (kPa) | σ′p (kPa) | OCR | K0 |
   |---|---|---|---|---|
   | 10 | 100 | 470 | 5.80 | 0.730 |
   | 10 | 50 | 470 | 11.6 | 1.460 |
   | 20 | 50 | 940 | 23.2 | 2.920 |
   | 30 | 50 | 1410 | 34.8 | 4.380 (N pa/σ′v0 = 60, inside) |
   | 31 | 50 | 1457 | 35.96 | NaN, "above range" (62) |
   | 30 | 20 | 1410 | NaN, "above range" (150) | NaN, "above range" |
3. **Field N:** the three field-N correlations raise without `spt_n`, naming it; given `spt_n60` only, they
   raise rather than read it.
4. **Bands:** `undrained_shear_strength_lower` / `_upper` hold AC 1's bands; Terzaghi & Peck's class boundaries
   equal `spt_class(table="cohesive")`'s for the same N.
5. **Chaining:** an input that is a correlation's target on its rows warns once, names the upstream correlation,
   and fills `correlation_input`; an input that is data on a frame from another correlation doesn't warn.
6. **USCS map:** `uscs="proposed"` gives "not for this soil" for SP under Stroud and "soil type unknown" for a
   blank symbol; a list overrides; without `uscs_symbol` it raises; `uscs=None` reads nothing.
7. **PI judgment:** `value=` wins; a column's filled rows are kept, its blanks filled from the file, with the warning
   counting differences; a missing judgment raises naming it; attrs record the source and values used.
8. **P01 range bar:** both bounds draw a bar with the marker where the central value exists; one bound draws the
   caret; limits include the bounds; beyond `xlim=` is counted; the footnote and stats box say how many ranges; a
   `qualifier` with bounds raises. Visual check: `docs/plots/img/P01-ranges.png`, US.
9. **Config and docstrings:** the drift test covers every new entry, including term bounds and the USCS groups.
10. **Docs:** pages 05–07 build with `--strict`; the guide's new example runs clean; reference entries exist.

### Size
This is more than one sitting: four correlations, the framework's terms, bands and chaining, the USCS map, a
judgment kind with two functions, a P01 feature and three pages. The plan builds it in this order, on this
branch, so each part lands reviewed: (1) the P01 range bar; (2) framework terms, bands, chaining and the USCS map,
with Terzaghi & Peck; (3) PI judgment, `add_judgment`, `summary_by` and Stroud; (4) the field-N σ′p, OCR and K0
correlations; (5) the pages; (6) guide and close-out.
