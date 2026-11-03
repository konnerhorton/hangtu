# M18 (b): representative values

## Intent
M18 is selection, stage D (SPEC §1.3, §5, §12.4), in four units (`docs/work/m18a-refusals.md`): (a) SPT
refusals (done), **(b) this unit**, (c) P09, (d) sources compared, the selection as a judgment, and the
Mohr–Coulomb set.

### Goal
- One statistics function computes, per geology unit, the representative value of a parameter from its values,
  constant or as a line with depth, and offers it in the views engineers use: Eurocode 7's characteristic value
  and the cautious estimates US practice uses (a lower percentile, the mean less a multiple of the standard
  deviation).
- Its result gives each view as a number per unit and as the `design_lines` frame P01 already draws, so a
  selection (M18 (d)) and P09 (M18 (c)) read one calculation.

### Why
- **Stage D needs a value per unit, and hangtu stops at the distribution.** `describe()` and `fit()` summarize;
  nothing turns the values into the cautious estimate a design report states. Engineers do it by hand in a
  spreadsheet today, and the report can't show how.
- **EC7's characteristic value is one view, not the frame** (decided 2026-11-02, TODO #13). Most users are in the
  US and want a design line with depth or a cautious estimate per unit in their own terms. "One calculation, many
  views" (SPEC §5): the result keeps n, the mean, the standard deviation and the trend fit, and each view reads
  them, so two views of one set can't disagree on the data.
- **Depth trends are common and done by eye.** s_u and N60 rise with depth in most units; a constant value per
  unit is then too low at depth and too high near the top. EC7's depth-dependent procedure (a regression with
  its confidence or prediction interval, the EC7 summary §3.5) gives a defensible line.
- **The choices are judgments, and today they are invisible.** Which estimate (mean or fractile), which side
  (low or high), what V_X (computed or assumed), the scale of fluctuation and the failure length: only the
  engineer knows them (EC7 summary §3.2), and a result that hides them can be off by a factor of two.
- **What depends on it:** P09 (M18 (c)) draws it; selection (M18 (d)) records which view each unit and parameter
  uses.

### Scope
- **The function:** `ht.stats.representative(df, value=, by=, ...)` (decision 1), returning a
  `RepresentativeResult` of kind *parameter* (SPEC §5).
- **Constant per unit, or a line with depth** (`trend=None | "depth" | "elevation"`): a least-squares line, its
  confidence interval for a mean estimate and its prediction interval for a fractile.
- **The views**, each named by the user, none by default:
  - EC7 characteristic value, Formula 4.5 and Annex A as the JRC report (2025) restates them: Type A (mean) and
    Type B (fractile); V_X computed (Case 2) or assumed (Case 3); normal or lognormal; low or high side.
  - Type C, from Γ² computed by the variance function from θ and L (both arguments, in length units), with
    `gamma2=` as an override (decision 3).
  - A percentile of a fitted normal or lognormal distribution, the one the user names (decision 4).
  - Mean − k·s, k given by the user (Schneider's 0.5 and the simplified fractile's 1.75 are then just values
    of k, named in the docs, not methods).
- **Flagged values follow SPEC §5's input rules.** With censored values in a group, the mean and s come from
  `fit()`'s censored maximum-likelihood normal (or lognormal) fit, with a note that the k_n factors assume
  complete data (decision 2). Bounds from the correlations, and refusals with the M18 (a) limit, enter the same
  way. 🟡 How a depth trend takes censored values (a censored regression, or leaving them out and counting them)
  is for the spec.
- **Warnings the JRC guidance gives:** n below its guidance for the case (EC7 summary §3.7), a negative
  characteristic value from a normal fit (a sign the data are lognormal), a trend whose residuals aren't
  constant.
- **Golden values** from the JRC report's worked examples (Annexes I–III), and hand calculations for the US views.
- Docs: a "Representative values" guide, the API reference, and the statistics guide's pointer.

### Constraints
- SPEC §4: judgments have no defaults, are recorded on the result, and resolve argument → `judgments=` →
  the project's file. 🟡 In (b) the view's inputs (estimate, side, V_X, θ, L, k, p) are required arguments;
  the judgments file names them per unit and parameter in (d), when the selection becomes a judgment.
- SPEC §5: input rules (counts add up, flags from the registry, sources not pooled unawares, H&F 7 percentiles,
  units); one calculation, many views; a result object with `.to_frame()`, `.to_dict()` and a summary.
- SPEC §5, "statistics are designed for lab data": SPT N and its correlations get the simple treatment. 🟡 Type C
  on SPT is not worth offering (TODO #13).
- Never cite from memory: every formula and k_n is checked against the JRC report (public, CC BY 4.0), which
  quotes EN 1997-1:2024. The lognormal Annex A formulae and Angus (1988) are checked in the spec step, or left
  out (TODO #13).
- No new dependencies: SciPy has Student's t and the normal quantiles.

### Out of scope
- **P09**, the figure (M18 (c)). (b) gives the `design_lines` frame; P01 draws it as it does today.
- **The selection as a judgment**, sources compared by depth or unit, and model sets (M18 (d)).
- **Estimating θ from data** (detrending a CPT, fitting a correlation model). θ is an input; a helper is later.
- **Nominal values** (EC7's cautious estimate without statistics): a value with a reason, which (d)'s judgment
  file records.
- **Partial factors, η and design values**: hangtu stops at the representative value (EC7 summary §5).
- **Bivariate c′–φ′ characteristic values**: they come with the Mohr–Coulomb set in (d), if at all.
- **Non-linear trends.** A line on depth only; 🟡 whether `log=True` (a line through ln values) is in (b) is
  for the spec.

### SPEC sections touched
- SPEC §5: the function list (`characteristic` becomes `representative`, decision 1), the views and their
  defaults (none), how censored values enter.
- SPEC §12.4: M18 (b)'s status.
- `docs/TODO.md` #13: resolved into SPEC §5 and deleted, or narrowed to what stays open (Type C, lognormal).
- `docs/drafts/phase3-stats.md`: its `characteristic` row points to the built function.
- `docs/reference/eurocode7-summary.md` §7: the proposed API is superseded by the spec.

### Decisions (intent review, 2026-11-03)
1. **The function is `ht.stats.representative()`, not `characteristic()`.** EC7's 2nd-generation term covers a
   statistical and a cautious estimate (EC7 summary §2), and it reads plainly to US users; `characteristic` would
   frame the US views as variants of an EC7 method. The EC7 view keeps the name "characteristic value".
2. **Censored values enter through the censored maximum-likelihood fit.** The mean and s come from `fit()`'s
   normal or lognormal fit, so refusals (with or without the M18 (a) limit), `<x`/`>x` and bounded correlation
   estimates are treated as in `fit()`, not biased low at their value as in `describe()`. The note says EC7's
   k_n factors assume complete data.
3. **Type C is in, from θ and L.** It is most real cases (JRC), and it adds one term to k_n; Γ² comes from the
   variance function, with `gamma2=` to give it directly. θ and L are inputs, never defaults; estimating θ is
   out of scope.
4. **The percentile view is of the fitted distribution**, normal or lognormal as the user names, so it handles
   censored values and a small n, and matches P08. The empirical percentile stays `describe()`'s.

## Spec
Numbered items are this section's decisions; "intent decision n" is the review's. Sources: the JRC report (Orr,
Sorgatz, Estaire et al. 2025, EUR 40260, CC BY 4.0), which quotes EN 1997-1:2024; every formula below was
checked against it on 2026-11-03 (page numbers are the report's printed ones).

### The function
```python
ht.stats.representative(
    data, *, value=None, by=None,
    method,                       # "characteristic" | "percentile" | "standard_deviations"
    side,                         # "low" | "high"
    distribution,                 # "normal" | "lognormal"
    trend=None,                   # None (constant) | "depth" | "elevation"
    estimate=None,                # characteristic: "mean" | "fractile" | "intermediate" (Types A, B, C)
    coefficient_of_variation=None,  # characteristic: None = computed (Case 2), a number = assumed (Case 3)
    scale_of_fluctuation=None, failure_length=None,  # intermediate: θ and L
    sensitivity_index=None,       # intermediate: Γ² given directly, instead of θ and L
    percentile=None,              # percentile: e.g. 5
    standard_deviations=None,     # standard_deviations: the multiple k
    pool=None, include_assumed=False, units=None, display_units=None,
) -> RepresentativeResult
```
1. **One view per call, every judgment on the call** (spec decision, 2026-11-03). `method`, `side` and
   `distribution` are required, and so is each input its method needs; there are no defaults (SPEC §4). An input
   that doesn't belong to the method is an error naming the method's inputs, so a call can't carry a judgment
   that silently did nothing. Each call returns one result for one view; two views are two calls on the same
   rows, and both read the same statistics. In (b) the inputs are arguments only; M18 (d) reads them from the
   judgments file per unit and parameter.
2. **Inputs follow SPEC §5's rules** as `fit()` does: `value=`/`by=`, flags from the registry, bands and
   non-plastic values left out and counted, sources not pooled unawares (`pool=`), assumed values only with
   `include_assumed=True`, units as for an analysis, `display_units=` converting first. A trend needs the
   `depth` or `elevation` column.

### The views (constant per group)
The mean x̄ and standard deviation s are the sample's (s with n − 1, Formula A.4) when a group has no censored
value; with any, they are the censored maximum-likelihood fit's (intent decision 2), and the note says EC7's k_n
assume complete data. For `distribution="lognormal"` everything below is applied to ln x and transformed back
(the JRC's Annex IV procedure for Annex A Formulae A.5–A.7); values at or below 0 are then left out and counted.

3. **Characteristic value** (Formula 4.5, p. 55; k_n from Table 13, p. 58, and Equation 18, p. 58):
   - X_k = x̄ ∓ k_n s with V_X computed (Case 2), X_k = x̄ (1 ∓ k_n V_X) with V_X assumed (Case 3; the same
     formula serves Case 1, V_X known, which the docs say). `∓` is − for `side="low"`, + for `"high"`.
   - k_n = c √(Γ² + 1/n), with c = t₀.₉₅,ₙ₋₁ for Case 2 and N₉₅ = 1.645 (the normal 95 % quantile, computed,
     not the table's rounded 1.64) for Case 3; Γ² = 0 for `estimate="mean"` (Type A), 1 for `"fractile"`
     (Type B).
   - Lognormal: X_k = exp(m ∓ k_n s_ln), with m and s_ln the mean and standard deviation of ln x (Annex IV,
     pp. 160–162); with V_X assumed, s_ln = √(ln(1 + V_X²)). The report has two lognormal routes: Annex IV
     works on ln x, and Annex V (Equations 72–74, p. 175) takes λ and ζ from the moments of x. hangtu takes
     Annex IV's, because it is what "transform, apply the normal formulae, transform back" means (§5.2.4) and
     it is the lognormal maximum-likelihood fit `fit()` already gives (spec decision, 2026-11-03). Equation 74
     is printed as ζ = √ln(1 + σ/μ) without the square; Table 57's values follow only from the usual
     ζ² = ln(1 + V²) (c_CU: 33.75 and 50.35 against the printed 33.8 and 50.4), so the square is the report's
     typo, and the docs use the usual form.
4. **Type C** (`estimate="intermediate"`): Γ² = θ / L, capped at 1 (Equation 17, p. 57, and its text: "a
   maximum value of 1 is adopted"). **This replaces intent decision 3's variance function**, which isn't in the
   report and wasn't verified (spec decision, 2026-11-03). θ and L are in the vertical column's length unit
   (only their ratio enters; the docs say so); `sensitivity_index=` gives Γ² directly, between 0 and 1, and
   can't be given with θ or L. Offered on any value; the docs say SPT spacing can't resolve θ_v (EC7 summary
   §3.2), so θ comes from published values or a CPT.
5. **Percentile** (intent decision 4): the `percentile`-th percentile of the normal or lognormal fit `fit()`
   gives the group (maximum likelihood, censored values as censored), so it matches P08. `side` must agree
   with it (below 50 for "low", above for "high"), or it's an error: a "low" P95 is a slip, not a choice.
6. **Standard deviations:** x̄ ∓ k s, k = `standard_deviations` > 0. Schneider's k = 0.5 (Equation 20, p. 64)
   and the simplified fractile's k = 1.75 (Equation 23, p. 65) are values of k the docs name, not methods.

### Trends (`trend="depth"` or `"elevation"`)
7. **Bond & Harris (2008), as the JRC gives it** (Equations 39–43, pp. 83–85; spec decision, 2026-11-03): a
   least-squares line x = a₀ + a₁ z with residual standard deviation sₑ (n − 2), and
   - mean (Type A): x̂(z) ∓ t₀.₉₅,ₙ₋₂ sₑ √(1/n + (z − z̄)² / Σ(zᵢ − z̄)²), the confidence interval;
   - fractile (Type B): x̂(z) ∓ t₀.₉₅,ₙ₋₂ sₑ √(1 + 1/n + (z − z̄)² / Σ(zᵢ − z̄)²), the prediction interval.
   The lines curve away from the data's centre, so they are given over the depths of the group's values only,
   never extended (the report's "linearize in the area of interest" is left to the engineer and P09).
   - With `coefficient_of_variation=` or Type C, a trend is an error: the report gives the trend only with
     sₑ from the data, and says Type C on a trend is beyond its scope (p. 82).
   - Percentile: x̂(z) + z_p sₑ, the fitted line's normal residuals. Standard deviations: x̂(z) ∓ k sₑ.
   - Lognormal: the line is fitted to ln x and the ends transformed back (§5.2.4, p. 86); a mean estimate is
     then of the median, and the note says so (the Angus (1988) mean bound is not offered: TODO #13).
   - A trend needs 3 values with distinct depths in a group (n − 2 ≥ 1); fewer gives that group no line, with a
     reason.
8. **Censored values are left out of a trend and counted** (spec decision, 2026-11-03). The note says which way
   that moves the line: leaving out refusals and `>` values makes a low-side line more cautious and a high-side
   line less, and `<` values the reverse. A censored regression is out of scope (SPEC §5, statistics are designed
   for lab data).
9. **No pre-tests** (SPEC §5): the trend's assumptions (constant variance, random scatter, normal residuals,
   p. 86) are stated in the note and the docs, not tested; the result keeps R² and the residuals for a plot.

### Result
10. **`RepresentativeResult`**, kind *parameter*, on the shared base (SPEC §5): it records the method and every
    input (`side`, `distribution`, `estimate`, the V_X case, θ, L and Γ², k, the percentile), the statistics
    behind each value (n, the counts left out by reason, x̄, s, V_X, k_n and the t or N factor; for a trend a₀,
    a₁, sₑ, R², z̄ and the depth range), and the notes.
    - `.to_frame()`: one row per group. A constant view has `value`; a trend has the line's coefficients and the
      value at the top and base of the group's values.
    - `.design_lines(mean=False)`: the frame `ht.template("design_lines")` describes (`label`, `depth` or
      `elevation`, `value`), in the result's units. A constant is two points, at the group's shallowest and
      deepest value; a trend is the curve at 50 depths across them. `mean=True` adds the mean (or median) line.
      The label names the group and the view ("Clay: characteristic, fractile, low").
    - `.to_dict()` and the printed summary, as the other results.
    - Column names are checked against the registry in the build.
11. **Warnings** (each names the group):
    - a characteristic value at or below 0 from a normal distribution: "the data may be lognormal" (JRC 5.1.3);
    - `value="hydraulic_conductivity"` with `distribution="normal"`: Table A.1 note 2, Formula 4.5 "should not be
      used" (p. 57);
    - a group with fewer than 2 values (constant) or 3 (trend) gets no value, with the reason in the frame.

### Acceptance criteria
1. Each method's required inputs are required: leaving one out is an error naming it and an example; an input of
   another method is an error naming the method's inputs (decision 1).
2. Type A, V_X assumed and computed, match the JRC's Annex I (G1) and Annex IV (G3).
3. Types B and C, normal and lognormal, both sides, match the hand values (G4), and Γ² from θ/L is capped at 1.
4. The percentile matches the quantile of `fit()`'s distribution for the same rows (G6), and a percentile on the
   wrong side of 50 is an error.
5. Standard deviations match x̄ ∓ k s (G4).
6. Censored values: a constant view uses the censored ML fit and notes it; a trend leaves them out, counts them
   and notes the direction; counts add up.
7. Trends match the hand values (G5) at three depths, for the mean, the fractile and k sₑ; the trend with V_X
   assumed or Type C is an error; fewer than 3 values gives a reason.
8. `.design_lines()` draws on P01 with no warning: two points per constant, 50 per trend, over the group's depth
   range; `mean=True` adds the mean line.
9. The warnings of decision 11 fire, and the result records every input and statistic (`.to_dict()` is JSON).

### Golden values
Hand-calculated from the formulas above (NumPy and SciPy for t and the normal quantiles, not the
implementation). Tolerance: 1e-6 relative against the hand values; the JRC's printed values to their rounding.
- **G1, JRC Annex I (Coca), Table 33, c′ (kPa):** 27, 45, 47, 46, 4.5, 9.5 (n = 6, x̄ = 29.833, s = 19.232).
  Type A, low: V_X assumed 0.40 → 21.819 (JRC Table 35: 21.82); computed → 14.012 (14.01).
- **G2, Annex I, tan φ′:** 0.61, 0.63, 0.47, 0.55, 0.51, 0.53. Type A, low, computed → 0.50013, φ′ 26.57°
  (JRC: 26.56°). With V_X assumed 0.10 the formula gives 0.51311, 27.16°, where the JRC prints 26.86°: their
  table doesn't follow from their own inputs, so the hand value is the golden one.
- **G3, Annex IV (Puurs), Table 48, k_v falling head (m/s, lognormal, Type A, low, computed):** clay, tests
  12–22 (1.2, 1.7, 3.8, 3.2, 2.8, 5.7, 3.3, 2.2, 9.8, 110, 2.9 × 10⁻¹⁰): s_ln 1.2132, k_n 0.5465 → 2.2091e-10
  (Table 51: 1.213, 0.546, 2.2E-10); without test 21: 2.2009e-10 (0.590, 0.580, 2.2E-10); peat, tests 23–25
  (5.2, 12, 12 × 10⁻¹⁰): 4.0237e-10 (Table 52: 1.686, 0.483, 4.0E-10). Normal on these warns (decision 11).
- **G4, c′ of G1, low:** Type B computed → −12.025 (warns, decision 11); Type B assumed 0.40 → 8.6320;
  Type C, Γ² = 0.3, computed → 3.3598; assumed 0.40 → 16.424; standard deviations k = 1 → 10.601.
- **G5, trend:** depth 2, 4, 6, 8, 10; values 20, 26, 29, 37, 40 (a₁ 2.55, a₀ 15.1, sₑ 1.30384, t₀.₉₅,₃ 2.35336).
  Low side at depths 2 / 6 / 10: mean 17.8232 / 29.0278 / 38.2232; fractile 16.3187 / 27.0387 / 36.7187;
  k = 1: 18.8962 / 29.0962 / 39.2962.
- **G6, percentile 5, normal, c′ of G1:** the ML fit (x̄ 29.833, σ̂ 17.556 with n) → 0.95586.

### Changes to other docs
- SPEC §5: the function list (`characteristic` → `representative`, intent decision 1); the views, their
  required inputs and Γ² = θ/L; censored values (the ML fit for a constant, left out of a trend).
- `docs/reference/eurocode7-summary.md` §3.2 and §7: Γ² is θ/L capped at 1 in the JRC; the variance function is
  Vanmarcke's, unverified; §7's API points to this spec.
- `docs/TODO.md` #13 at close-out: the decided points move to SPEC §5; what stays open is the Angus mean bound
  for a lognormal trend and the variance function.

## Plan
Approved 2026-11-03. One green commit per step; each runs the tests it touches, then the CI command with `-n 3`.
All steps on Opus: each implements a calculation or touches citations, except step 5, too small to justify a
session boundary of its own. Suggested new session after step 3.

**Spec amendment (plan review, 2026-11-03):** `representative()` also takes `spt_refusal_upper_limit=` and
`judgments=`, resolved as in `fit()` (argument → `judgments=` → the project's file → none), so a constant
view's ML fit takes refusals as interval-censored under the limit (intent decision 2). A trend still leaves
refusals out. Step 2 adds both to the spec's signature in the same commit.

### 1. `M18: share fit()'s row reading with the statistics to come` (Opus)
A refactor, no behavior change.
- `src/hangtu/stats/_fit.py`: move the body from `read_input()` to each group's `Values` and counts into a
  `read_groups(data, value, by, pool, include_assumed, spt_refusal_upper_limit, judgments, units,
  display_units, function, positive_only)` returning the `Input`, the unit, the refusal-limit record and notes,
  and per group its key, row mask, `Values` and counts; `fit()` calls it. Its group dict building, notes and
  errors stay in `fit()`.
- Tests: the existing `tests/stats/test_fit*.py` and `test_fit_refusal_limit.py` pass unchanged.

### 2. `M18: add representative()'s characteristic value` (Opus)
- `src/hangtu/stats/_representative.py` (new): the signature of spec decision 1, plus the amendment.
  - `_check()`: `method`, `side`, `distribution` required; each method's inputs required and others an error
    naming the method's inputs, with an example (criterion 1); `sensitivity_index` between 0 and 1 and not with
    θ or L; θ, L, V_X > 0; trend with V_X or Type C an error (raised now, trend built in step 4).
  - Per group (`read_groups(..., positive_only=distribution == "lognormal")`): x̄ and s as the sample's (n − 1)
    without censoring, else `estimate("normal"|"lognormal", ...)` with a note that k_n assumes complete data;
    lognormal on ln x. k_n = c √(Γ² + 1/n), c = `scipy.stats.t.ppf(0.95, n − 1)` (Case 2) or
    `norm.ppf(0.95)` (Case 3); Γ² from `estimate`, or min(θ/L, 1) (spec decisions 3, 4). Fewer than 2 values:
    no value, with the reason.
  - Warnings (decision 11): X_k ≤ 0 from a normal; `hydraulic_conductivity` with normal.
  - Docstring: every formula with the JRC page, Formula 4.5, Table 13, Equations 17–18; Annex IV for
    lognormal; inputs with units; Cases 1–3; references.
- `src/hangtu/stats/_result.py`: `RepresentativeResult(_Result)`, kind `"parameter"`: every input and, per
  group, n, the left-out counts, x̄, s, V_X, k_n, the factor, the value, the reason; `.to_frame()`, `.to_dict()`,
  `__str__`, `_repr_html_`, as `FitResult`.
- `stats/__init__.py` exports; `docs/site/reference/stats.md` entries for both.
- Frame column names checked against `columns.yaml` (an Explore subagent sweep; reuse `mean`,
  `standard_deviation`, `coefficient_of_variation` as `describe()` names them).
- The spec's signature in `docs/work/m18b-representative-values.md` gains the two arguments.
- Tests: `tests/stats/test_representative.py` (new): criterion 1; G1, G2 (the hand value 0.51311, not the
  JRC's 26.86°), G3 (clay with and without test 21, peat; normal on them warns) for criterion 2; G4's Type B
  and C values, θ/L above 1 capped, both sides (criterion 3); a refusal in a group uses the ML fit and notes it,
  with and without `spt_refusal_upper_limit` (criterion 6, constant); counts add up.
  `tests/stats/test_representative_result.py` (new): `.to_dict()` is JSON and records every input (criterion 9).

### 3. `M18: add the percentile and standard-deviations views` (Opus)
- `_representative.py`: percentile = `frozen(distribution, estimate(...)).ppf(p/100)` (always the ML fit,
  spec decision 5); `side` against 50 checked; standard deviations x̄ ∓ k s (decision 6). Docstring names
  Schneider's k = 0.5 (Eq. 20) and the simplified fractile's 1.75 (Eq. 23) as values of k.
- Tests: G6 against `fit()`'s normal for the same rows, a "low" P95 an error (criterion 4); G4's k = 1 →
  10.601 (criterion 5).

### 4. `M18: add depth and elevation trends to representative()` (Opus)
- `_representative.py`: `trend=` reads `depth` or `elevation` (a `ColumnError` without it); censored rows left
  out and counted with the direction note (spec decision 8); 🟡 a row with a value but no depth (elevation)
  left out and counted as `count_blank_depth` (`count_blank_elevation`), named against the registry in this
  step. Least squares a₀, a₁, sₑ (n − 2), R², z̄, Σ(z − z̄)², the depth range; the confidence (mean), prediction
  (fractile), z_p sₑ (percentile) and k sₑ (standard deviations) lines; lognormal on ln x with the median note.
  Fewer than 3 values or fewer than 2 distinct depths: no line, with the reason. Assumptions stated in the note
  (decision 9).
- Result: a trend group keeps the line's statistics and residuals; `.to_frame()` gives the coefficients and the
  values at the top and base.
- Tests: G5 at depths 2/6/10 for mean, fractile and k = 1 (criterion 7); elevation gives the same line mirrored;
  V_X or Type C with a trend an error; 2 values gives a reason; refusals left out, counted and noted
  (criterion 6, trend).

### 5. `M18: give representative()'s design_lines frame` (Opus)
- `_result.py`: `.design_lines(mean=False)`: constant as two points at the group's shallowest and deepest
  value, a trend at 50 depths across them; `mean=True` adds the mean (median) line; labels "<group>: <method>,
  <estimate>, <side>"; units in `attrs`.
- Tests: `tests/stats/test_representative_result.py`: point counts and ranges; `tests/plot/test_profile_overlays.py`:
  the frame draws on P01 with no warning, constant and trend (criterion 8).

### 6. `M18: document representative values; close out (b)` (Opus)
- `docs/site/guides/representative-values.md` (new) with `docs/site/examples/representative-values.py`, in the
  `nav` of `zensical.toml`: the views, which judgments each needs, Cases 1–3, Type C and θ (SPT can't resolve
  θ_v), the lognormal routes, trends and their assumptions, censored values. The figure looked at.
- `docs/site/guides/statistics.md`: a pointer. `docs/reference/eurocode7-summary.md` §3.2 and §7 (Γ² = θ/L in
  the JRC, the variance function Vanmarcke's and unverified, §7 → the spec). `docs/drafts/phase3-stats.md`:
  the `characteristic` row points to `representative`.
- Close-out: `docs/TODO.md` #13 narrowed to the Angus mean bound and the variance function (decided points are
  in SPEC §5 already); SPEC §12.4 M18 "(b) done; (c) next"; the "Next" sentence in `CLAUDE.md`; the lesson
  check (CLAUDE.md conventions, SPEC, memory).

## Verification
- Each acceptance criterion mapped to a test above; golden values from the spec, 1e-6 relative.
- Full CI command locally with `-n 3`; `uv sync --group docs && uv run python docs/prepare_site.py && uv run
  zensical build --clean --strict`.
- Look at P01 with a constant and a trend design line from the guide's example.
