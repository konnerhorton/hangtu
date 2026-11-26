# reliability-guards: warn where a plausible number is wrong

## Intent

### Goal
Four ways that hangtu returns a plausible wrong number with nothing to flag it now warn, or refuse to guess: an SPT
class table defaulted onto clays, a correlation run on rows whose `soil_class` it doesn't apply to, a representative
value driven by censored values, and stresses declared in the wrong unit.

### Why
- The agent-use review (2026-11-09, TODO #60–69) asked how likely a wrong answer is when an agent does the work and an
  engineer signs it off. TODO #60, #61, #63 and #67 give a number that looks right with nothing to catch it:
  - **#61:** `spt_class(clay_rows)` returns "Very loose" and "Loose", because `table="cohesionless"` is a default.
  - **#60:** Hatanaka & Uchida (1996) on the Alluvium (lean clay) rows gives φ′ = 28–32° for every row. The only
    warning is about the range, though the rows carry `soil_class == "fine"`.
  - **#63:** with 25 of 40 values "at least 44.5°", `representative()` gives a characteristic value of 44.6°, above
    every real estimate (largest 44.1°) and above the correlation's ceiling. The note explains the method, not the
    result.
  - **#67:** a triaxial CSV in psf declared as kPa gives c′ = 104 kPa and σ′n up to 3,680 kPa at 18 ft, with no
    check.
- Users asked for reliability before more features: wave 5 (M23 c) waits on this unit.

### Constraints
- SPEC §4: judgments have no defaults. The class table is a judgment; which N column to classify is data (N is
  defined by ASTM D1586), so `n="spt_n"` stays a default.
- SPEC §2.6: never guess a unit. #67 is a check that warns; it never converts or rejects.
- SPEC §4: a correlation reads soil type only when asked (`uscs=`). #60 reads a column the user already supplied
  (`soil_class`) and warns; it doesn't infer a class or blank an estimate.
- Warnings are errors in the test suite and the docs examples, so every example that now warns is fixed in the step
  that adds the warning.
- 0.1.0 is on PyPI with `spt_class()` and `spt_histogram()`. A break is accepted (no deprecation period); the
  CHANGELOG says so.

### Out of scope
- **#41** (gravelly sands that pass the SP symbol check): needs its own design (group name, gradation, or the user's
  rows). Stays in TODO.
- **#3** (the rest of the `soil_class` split, and its name): this unit reads only `coarse`, `fine` and `rock`.
- **#78**, **#24**, **#71**: smaller reliability items, for a later unit.
- A QC rule for #67 on AGS files: AGS stresses arrive in the dictionary's unit, so the CSV route is where the
  mistake happens. A QC rule can follow if a real file needs it.
- The reverse of #67 (kPa declared as psf, stresses about 20× too small): not seen in the trials.

### SPEC sections touched
- SPEC §4 (correlations bullet, line ~171): soil type is read only when asked, *and* a contradicting `soil_class`
  warns.
- `docs/analysis/index-and-spt.md` §1.4 (`table=` required, the class check); P03's spec (`table=` required).
- `docs/analysis/correlations.md` §2 (the class check, the new note).
- `docs/analysis/statistics.md` §1–2 (the censoring warnings).
- `docs/analysis/strength.md` §4 (the overburden check in `mohr_coulomb_fit()`).
- P01's spec (the footnote counts the new note).
- `src/hangtu/config/correlations.yaml` (a `soil_classes` field per entry).

### Decisions (intent review, 2026-11-26)
1. **`table=` is required in `spt_class()` and `spt_histogram()`, with no deprecation period.** It is a judgment
   (SPEC §4); 0.1.0 has few users, and a deprecation would keep the wrong default working for a release.
2. **`n=` keeps its default, `spt_n`.** N is defined by ASTM D1586, so it is data, not a judgment. Which N a class
   table was built on is a fact of the table's source, not the engineer's call.
3. **A correlation on rows whose `soil_class` contradicts it warns and notes the rows, and keeps the estimate.** It
   costs nothing when the classes agree, and reads a column the user supplied rather than inferring one. Blanking the
   estimates was rejected: it would change SPEC §4's opt-in `uscs=` into a default.
4. **Censoring warns when more than half of a group's values are censored, or when the representative value lies
   beyond the uncensored values on the censored side.** `fit()` warns on the first condition.
5. **Stresses warn when a consolidation stress is far above the overburden at the sample's depth** (about 10×), in
   the triaxial fit only. The oedometer is loaded 10–30× past σ′v0 by design, so it isn't checked.

## Spec

### Changes
- **`spt_class()`, `spt_histogram()`:** `table` has no working default. The signature keeps `table=None` so that
  leaving it out raises our own message rather than Python's bare `TypeError`: "spt_class() needs table=: "cohesionless"
  (relative density) or "cohesive" (consistency). Which applies is the engineer's call; pass the rows it applies to."
  A `soil_class` that contradicts the table warns: `cohesionless` on `fine` rows, `cohesive` on `coarse` rows, either
  on `rock` rows. Other classes (`fill`, `organic`, blank, user-defined) aren't checked.
- **Correlations:** each entry in `correlations.yaml` gets `soil_classes:`, hangtu's reading of `applies_to` (like
  `uscs:`): Hatanaka & Uchida and Kulhawy & Mayne φ′: `[coarse]`; Terzaghi & Peck, Stroud, Mayne & Kemper (σ′p, OCR),
  Kulhawy et al. K0: `[fine]`; AASHTO E′ by its soil row (silts `[fine]`, sands and gravels `[coarse]`); Kulhawy &
  Mayne E′: `[coarse]`; Imai & Tonouchi and Ohta & Goto Vs: `null` (all soils, not checked). A row whose class is
  `coarse`, `fine` or `rock` and not in the list keeps its estimate, gets the `correlation_note`
  "soil class contradicts" when it has no other note, and is counted in one warning per call naming the geology
  units. The class comes from the `soil_class` column, else from `attrs["soil_classes"]` by `geology_unit`; with
  neither, nothing is checked.
- **P01's footnote** counts the new note: "{n} soil class contradicts the correlation".
- **`representative()`:** per group, a warning and a group note when `count_censored > count / 2`, or when the
  representative value is above the largest uncensored value (right-censored values) or below the smallest
  (left-censored values). `select()` inherits both through `representative()`.
- **`fit()`:** the same warning and note on the first condition (it has no representative value).
- **`mohr_coulomb_fit()`:** for each point with a depth, an upper bound on the overburden is
  σ_v,max = γ_max · z with γ_max = 25 kN/m³. One warning per call lists the rows whose effective consolidation
  stress (or σ′3 at failure, where the stress isn't given) exceeds max(10 · σ_v,max, 500 kPa), and says the likely
  cause: "the stresses may be in another unit than declared (psf as kPa?)". Rows without a depth aren't checked.

### Decisions
1. **γ_max = 25 kN/m³ and a 500 kPa floor.** An upper bound needs no unit weights or stratigraphy, so the check
   runs on a bare CSV. 25 kN/m³ is above any soil's bulk unit weight. The floor stops false warnings on shallow
   samples tested at the usual 100–400 kPa (at 1 m the bound alone is 250 kPa). Checked against #67's case: 18 ft
   (5.5 m) gives max(1,375, 500) = 1,375 kPa < 3,680 kPa, so it warns. A shallow psf file tested at 1× σv (2 m,
   ≈ 40 kPa ≈ 835 psf) also warns (835 > 500). Both numbers are hangtu's rule, stated as such, with no source.
2. **The class note comes last in `correlation_note`'s priority.** A row with no estimate keeps its reason for
   being blank, and a bound keeps "refusal" or "above range"; the warning counts every contradicting row whatever its
   note.
3. **`rock` contradicts every soil table and correlation; `fill` and `organic` aren't checked.** Fill behaves as
   its dominant soil, and organic clay is still a clay; both are TODO #3.
4. **The checks read `soil_class` as given.** hangtu doesn't derive a class from USCS or gradation.

### Acceptance criteria
1. **Table required:** `spt_class(df)` and `spt_histogram(df)` without `table=` raise `HangtuError` naming both
   tables. With `table=` given, results are unchanged (existing tests).
2. **SPT class check:** `spt_class(rows, table="cohesionless")` on 3 `fine` and 2 `coarse` rows warns once, naming 3
   rows; `table="cohesive"` on the same rows warns naming 2; rows with `soil_class` blank or `fill` don't warn.
3. **Correlation check:** Hatanaka & Uchida on the example site's Alluvium rows (`fine`) warns once, with the count
   and the unit; every estimate equals the estimate without the check; rows with no other note get
   "soil class contradicts". On the Terrace rows (`coarse`) it doesn't warn. AASHTO with `soil=` a silt row on
   `coarse` rows warns.
4. **Class from attrs:** a frame without a `soil_class` column but with `attrs["soil_classes"]` and `geology_unit`
   is checked the same way, including when `geology_unit` is categorical.
5. **Censored count:** `representative()` on 3 uncensored values (30, 32, 34) and 4 right-censored at 40 warns
   (4 > 3.5) and adds the group note; on 4 uncensored and 3 censored it doesn't warn on the count. `fit()` on the
   first set warns.
6. **Beyond the uncensored values:** a right-censored group whose representative value is above its largest
   uncensored value warns; a left-censored group below its smallest warns; a characteristic value below the smallest
   value of a right-censored group (the usual low side) doesn't.
7. **Overburden check:** #67's case (σ′c 3,680 "kPa" at 5.5 m) warns naming the row; 400 kPa at 1 m, 1,000 kPa at
   10 m and rows without a depth don't; the threshold in ft gives the same result as in m.
8. **No silent change:** every number every function returned before is unchanged; only warnings and notes are
   added.
9. **Docs:** the site builds strict, every example runs without a new warning, and the reference pages show
   `table=` as required.

