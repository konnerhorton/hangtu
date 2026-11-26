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

