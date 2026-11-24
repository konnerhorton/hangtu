# Stiffness: E50, ε50 and Rf from triaxial readings

| | |
|---|---|
| **Status** | Living spec. E50 and ε50 (§1) and the failure ratio Rf (§2) from the readings during shearing. M23 (c) adds the selection of E′ and ν′ and P20; M23 (d) the Hardening Soil set |
| **Parent** | SPEC §4 (stiffness from readings) and §5 (derived results) |
| **Related** | [`m23b-moduli-from-readings.md`](../work/m23b-moduli-from-readings.md). The readings and their failure rows: [`strength.md`](strength.md) §2. The lab's E50: [`docs/data/datasets.md`](../data/datasets.md) (`p.triaxial()`). Sheets 08 and 11 in [`docs/drafts/parameters/`](../drafts/parameters/README.md) |

Update this file in the same commit as any change to `triaxial_stiffness_from_readings()`'s behavior, and SPEC §4 or
§5 if the change alters a rule there. The equations, sources, validity and each reason's wording are in the docstring,
the published reference ([`ht.analysis.triaxial_stiffness_from_readings`](../site/reference/analysis.md)); they
aren't repeated here.

## 1. E50 and ε50
- **Input and rows:** `triaxial_stiffness_from_readings(df, *, failure_criterion=None, failure_ratio_range=(0.7, 0.95),
  units=None)` reads the readings frame `triaxial_failure_from_readings()` reads, through the same private
  `reduce_readings()`, and returns its rows unchanged (columns, values, order and units) with seven columns added. So
  the stages, loading parts and failure readings are the ones P12 draws and the envelope fits use.
- **The origin** is the stage's first loading-part q reading at ε1 = 0, its q being q_0; without one, q_0 = 0. ε50 is
  interpolated only between readings: a stage whose first q reading is already at or above half the peak gets a reason
  ("no reading below half the peak"), never a chord from an origin the lab didn't read.
- **The peak** is the stage's largest loading-part q (the first on a tie), whatever the failure criterion: that is
  E50's definition and `TRET_E50`'s, so hangtu's value and the lab's mean the same thing. ε50 is interpolated between
  the last loading-part reading below q_50 before the peak and the next one; this is how `site.ags`'s lab values were
  generated, and they agree to their headings' rounding.
- **Strains** are percent. A strain column declared in another unit is a `UnitsError` (percent columns are never
  converted); undeclared, it is read as percent.
- **Units:** E50 in `cell_pressure`'s unit, ε50 in `%`.
- **Every stage gets a value or a reason,** UU and the later stages of a multistage test included; `test_type`,
  `cell_pressure` and `multistage_test` say what each row is, and selection (M23 c, d) leaves rows out by them.
  Drained and undrained values are never converted into each other here (sheet 11 §7).
- **No comparison column** with the lab's E50: the lab's values are on `p.triaxial()`'s rows, and a merge on
  `specimen_id` and `test_stage` shows both. The site page's example does that.
- Reasons: q never rises above q_0; no reading below half the peak; ε50 not above 0.

## 2. The failure ratio Rf
- **The fit:** the transformed hyperbola ε1/(q − q_0) against ε1 (ε1 a fraction), fitted by `line_fit()` (the
  envelope fits' core), over the loading-part q readings at row positions up to and including the failure reading's,
  with `failure_ratio_range[0] ≤ (q − q_0)/(q_f − q_0) ≤ failure_ratio_range[1]`. q_a = 1/b and Rf = (q_f − q_0)/q_a;
  q_a is reported measured from q_0. The intercept isn't used (the sources disagree on it).
- **The range is hangtu's rule** until Duncan & Chang (1970) is read: TODO #79. The range used is in
  `df.attrs["failure_ratio_range"]`; anything other than two numbers with 0 < lower < upper ≤ 1 is a `HangtuError`.
- **q_f** is the failure reading's q, by `failure_criterion=` or the lab's mark, so on a stage failed by the stress
  ratio, Rf's q_f and E50's peak differ.
- **Limits:** fewer than 3 readings in the range (the reason names the count), no fit (the line fit's reason), b ≤ 0
  (no asymptote; r² is kept), q_f not above q_0, or a failure reading with no q: blank with a reason. Rf > 1 is kept,
  not clipped, and one warning names the stages. r² is reported wherever a line was fitted.
- **No overrides per stage** yet: they wait on TODO #77, as the oedometer's do.
