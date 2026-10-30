# M15 (c): `fit()` and P08, distribution fits with censored and bounded data

## Intent
M15 is the statistics milestone (SPEC §1.3, §5, §12.4), split into four units (`docs/work/m15a-describe.md`,
decision 1). This unit, (c), fits probability distributions to a property's values and draws the fit (P08). It
follows the input rules (a) set (SPEC §5) and builds the parts of TODO #8 and #12 that were agreed for it.

**Goal:** an engineer passes a property's values (an array, a Series, or a DataFrame with `value=` and `by=`)
and gets each candidate distribution's fitted parameters, ranked by AICc, each checked for goodness of fit, with
the probability it puts beyond a physical bound. Refusals, `<x` and `>x` are fitted as censored values, not as
measurements. A two-panel figure (histogram with the fitted PDFs, and a Q-Q plot) shows the fit, so the ranking
can be checked by eye.

**Why:**
- **A normal fit puts probability on impossible values.** Most geotechnical data are bounded: N ≥ 0, k > 0,
  0 ≤ fines ≤ 100 % (TODO #8). Lognormal, gamma and Weibull are bounded at 0 by construction. The result should
  say how much a normal fit puts below 0, so the choice is visible.
- **Refusals are censored, not measured.** N60 by geology unit in the example project has refusals recorded at
  the cap; the true N is *at least* that. `describe()` counts them and notes the bias (SPEC §5); a fit can do
  better, by maximum likelihood on censored data (`scipy.stats.CensoredData`), and SPEC §5 already says it will.
- **Selection needs a distribution.** `characteristic()` (M18) and the comparisons in (d) assume one (normal or
  lognormal); `fit()` is how an engineer checks which, and records it.
- **SPEC §12.4's M15 row** lists `fit` and P08; SPEC §12.1 already allows `scipy>=1.11` for Phase 3, and this is
  the first unit that needs it.

**Scope:**
- `ht.stats.fit()`, with `by=`, `pool=`, `include_assumed=`, `units=` and `display_units=` as `describe()`, and
  a `FitResult` on the shared result base (`_result.py`): `.to_frame()` (one row per group and distribution),
  `.to_dict()`, a readable summary, and `.plot()`;
- candidate distributions: normal, lognormal, gamma and Weibull (TODO #12), each 2-parameter with the location
  at 0 for the positive ones (🟡 proposed: no 3-parameter fits, which need more data than we usually have);
  with `bounds=`, beta on the rescaled data (TODO #8 point 3; truncated normal deferred, decision 2);
- censored values from the registry's flags (SPEC §5): refusals and `>x` right-censored, `<x` left-censored;
  bands (`<target>_lower`/`_upper`) as interval-censored values (SPEC §5 "may");
- ranking by AICc and an Anderson–Darling check for each fit (TODO #12); P(X below the lower bound), and above
  the upper one when given, for each fit (TODO #8 point 1);
- P08 promoted from `docs/plots/README.md` to `docs/plots/P08-distribution-fit.md`, built, with its PNG and docs
  page; `scipy` added to the dependencies;
- reference entries, the statistics guide extended, and an example on the docs site.

**Out of scope:**
- **`compare()`, `compare_groups()`, `crosstab()`:** unit (d).
- **`characteristic()`, P09, effective sample size, spatial correlation:** M18.
- **Discrete distributions for N.** N is a count; it is fitted as continuous, as is usual, and the docstring says so.
- **P24 (grouped histogram) and P27 (published distributions)** stay drafts. P08 draws one value's fit; whether
  P24 is P08's histogram panel alone is decided with P24.
- **Fitting a trend with depth** (detrending before fitting): selection (M18).
- **Mixtures and 3-parameter distributions.**

**SPEC and TODO touched:**
- SPEC §5 (`fit` built; its view of censored values and bands; `fit()` has no `log=`, decision 3), §12.1
  (`scipy>=1.11` added), §12.4 (M15 row).
- Other docs: `docs/drafts/phase3-stats.md` (the `fit` row decided, pointing here), `docs/plots/README.md` (P08's
  row and status), the new `docs/plots/P08-distribution-fit.md`.
- TODO: #12 resolved and removed; #8 keeps only the truncated normal (decision 2).

### Decisions (intent review, 2026-10-30)
1. **Anderson–Darling by Monte Carlo, only when no value is censored.** AD's usual p-values assume complete
   data, and with parameters estimated from the same data they need distribution-specific tables (Stephens) or a
   Monte Carlo (`scipy.stats.goodness_of_fit`, SciPy ≥ 1.10); neither covers censored data. With no censored
   value, the p-value comes from a Monte Carlo with a fixed seed, so a result is reproducible. With censored
   values there is no AD p-value, a note says why, and the Q-Q plot uses censored-data plotting positions
   (Helsel 2012) so the fit can still be judged by eye. A censored AD by parametric bootstrap was rejected as more
   code than the cases need.
2. **Truncated normal is deferred.** SciPy's `truncnorm` takes its bounds in standard units, so fixed physical
   bounds need a custom likelihood (TODO #8 point 3). Beta covers doubly bounded data (fines near 0 %) and the
   four positive distributions cover the rest. It stays in TODO #8.
3. **`fit()` has no `log=`.** A normal fit to the logs is the lognormal fit it already makes; SPEC §5's "all
   accept `log=True`" gains this exception.
4. **Minimum n: an error below 4 uncensored values per group, a warning below 10.** AICc needs n > k + 1, so 4
   for two parameters; below 10 the ranking and the AD check have little power, and the warning says so.
5. **P08's call:** `ht.plot.distribution_fit(df, value=..., ...)` calls `fit()` and draws it, and
   `FitResult.plot()` draws an existing result through the same code. How several groups are drawn (one figure
   per group, as `geology_unit_comparisons()`, or a `group=` argument) is settled in the spec.

## Spec
Numbered items refer to this section's decisions; "intent n" to the intent's. Every choice proposed here was
agreed in review on 2026-10-30. The figure's spec is [`docs/plots/P08-distribution-fit.md`](../plots/P08-distribution-fit.md).

**What SciPy does** (checked 2026-10-30 on 1.11.4, the oldest allowed, and 1.18.1):
- `rv_continuous.fit(CensoredData, ...)` fits normal, lognormal, gamma and Weibull with left, right and interval
  censoring, and beta with fixed `floc`/`fscale`, on both versions, in under 0.05 s each.
- `scipy.stats.goodness_of_fit(..., statistic="ad")` gives a Monte Carlo p-value with the parameters estimated,
  but refits with its own routine: its normal fit uses the n − 1 standard deviation, so its statistic isn't the
  one for our maximum-likelihood fit, and Weibull takes about 30 s at its default 9999 samples. It takes no
  censored data.
- `scipy.stats.anderson()` has tables only for some distributions and changes its API in 1.17 (a
  `FutureWarning` without `method=`, which fails our tests). Not used.
- `scipy.stats.ecdf()` gives the Kaplan–Meier estimate for right-censored data only.

### Changes
- **SPEC §5:** `fit` built; how it reads censored values and bands (Decisions 3, 4); `fit()` takes no `log=`
  (intent 3); the result object's list gains `FitResult`.
- **SPEC §12.1:** `scipy>=1.11` moves from "Phase 3 adds" to the dependencies. **§12.4:** M15 row, (c) done.
- **`docs/plots/P08-distribution-fit.md`:** new, from the README's row; README row → `built`, function
  `distribution_fit`.
- **`docs/drafts/phase3-stats.md`:** the `fit` row decided, pointing here.
- **CLAUDE.md "Naming":** `aicc` added to the accepted short forms (Decision 6).
- **TODO:** #12 removed; #8 keeps only the truncated normal (intent 2) and bands as intervals (Decision 4); new
  #48 for the deferred sources.
- **Docs site:** `fit`, `FitResult` and `distribution_fit` in the reference; a "Fitting a distribution" section
  in the statistics guide, with an example; the P08 page.

### Decisions
1. **`ht.stats.fit()`.**
   ```python
   fit(data, *, value=None, by=None, distributions=None, bounds="auto", pool=None,
       include_assumed=False, units=None, display_units=None) -> FitResult
   ```
   - **`data`, `value=`, `by=`, `pool=`, `include_assumed=`, `units=`, `display_units=`:** as `describe()`
     (M15 (a) Decision 1): the same three input forms, groups, source check, assumed values, text values, units
     and order of checks. The rows are read by the code `describe()` uses, moved to a shared module (Plan), so
     both functions choose the same rows.
   - **`distributions=`:** names from `"normal"`, `"lognormal"`, `"gamma"`, `"weibull"`, `"beta"`. `None` fits
     the first four, plus beta when `bounds` has two finite ends. An unknown name is an error listing the
     names; beta without two finite bounds is an error saying to pass `bounds=(low, high)`.
   - **`bounds=`:** `(low, high)` in the value's (display) units, either end `None`. `"auto"` gives
     `(0, None)` for a column the registry marks `scale: ratio`, and `(None, None)` otherwise (an interval-scale
     column, or one not in the registry). Percentages need `bounds=(0, 100)` passed: the registry doesn't record
     upper bounds. A value outside the bounds is an error naming its count and the bounds, since it is either a
     data error or wrong bounds.
2. **The distributions** (intent scope; all fitted by maximum likelihood):

   | Name | SciPy | Parameters fitted (k = 2 for all) | Fixed |
   |---|---|---|---|
   | `normal` | `norm` | mean, standard deviation | — |
   | `lognormal` | `lognorm` | σ of ln x, median (`scale`) | location 0 |
   | `gamma` | `gamma` | shape, scale | location 0 |
   | `weibull` | `weibull_min` | shape, scale | location 0 |
   | `beta` | `beta` | α, β | location `low`, scale `high − low` |

   - Without censoring, normal and lognormal use their closed forms (mean and the n, not n − 1, standard
     deviation, of x or ln x); the others use SciPy's `fit`. With censoring, all use `fit(CensoredData)`.
   - **Values ≤ 0** (a 0 % fines, N = 0) can't be fitted by lognormal, gamma or Weibull. They are kept, those
     three are left out for that group, and a note says why with the count; normal (and beta, if 0 is inside the
     bounds and above `low`) still fits. They are not dropped to make the others fit.
   - **A fit that fails to converge** is left out for that group with SciPy's message in the notes, never
     reported as if it had.
3. **Censored values** (SPEC §5, TODO #8 point 2). From the registry's `statistics:` roles:
   - `at_least` (a refusal) and `qualifier` `>` are right-censored at the row's value; `qualifier` `<` is
     left-censored. A refusal with a blank value is counted with the blanks, as in `describe()`.
   - All candidates are fitted to the same censored data, so their likelihoods compare (Decision 6).
   - The result counts them (`count_at_least`, `count_at_most`, as `describe()`) and notes the share censored.
   - No threshold on the share censored: the fit is reported, the share is in the summary, and the Q-Q panel
     shows how far the uncensored values carry it.
4. **Bands are left out and counted, as in `describe()`** (changes the intent's scope, which had them as
   interval-censored). A correlation's band is the spread of its coefficient (Stroud's f1 from 4.0 to 6.0), not a
   measurement known only to lie in an interval; fitting it as interval-censored would treat a modeling range as
   data. Leaving it out also keeps every group's plotting positions to one censoring direction (Decision 8). It
   stays in TODO #8 as a possible later option.
5. **Minimum n** (intent 4). Per group, counting uncensored values:
   - fewer than 4: no fits for that group; its row has the counts and the reason, with one warning naming the
     groups. It is an error only when no group can be fitted, so one small unit doesn't stop a `by=` call;
   - 4 to 9: fitted, with one warning naming the groups and saying the ranking and the AD check have little
     power below 10 values.
6. **Ranking by AICc** (TODO #12).
   - ln L is the log-likelihood at the fit: Σ ln f(xᵢ) over uncensored values, plus ln F(c) for each
     left-censored and ln(1 − F(c)) for each right-censored value at its bound c.
   - AIC = 2k − 2 ln L; AICc = AIC + 2k(k + 1)/(n − k − 1), with n all the values fitted, censored included, and
     k = 2 (n ≥ 4 keeps the denominator positive).
   - Each fit is reported with `aicc`, `delta_aicc` (from the group's lowest) and `akaike_weight`
     (exp(−Δ/2) normalized over the group's fits), and ranked 1, 2, … by AICc. Ties keep the order of the
     table in Decision 2.
   - The notes give Burnham & Anderson's rough guide (p. 271): Δ ≤ 2 substantial support, 4–7 considerably
     less, > 10 essentially none, so close fits aren't read as a clear winner.
   - A group's fits are compared only within it: AICc across groups means nothing, and the frame says so in
     the notes.
   - **`aicc` as a name:** added to CLAUDE.md's accepted short forms. "AICc" is the term every source uses,
     and spelled out ("akaike_information_criterion_corrected") it is harder to read than to misread. It
     collides with nothing in the registry.
7. **Anderson–Darling** (intent 1).
   - The statistic, for n values in order with the fitted CDF F:
     A² = −n − (1/n) Σᵢ (2i − 1)[ln F(x₍ᵢ₎) + ln(1 − F(x₍ₙ₊₁₋ᵢ₎))].
   - **The p-value is a parametric bootstrap**, written in hangtu rather than `goodness_of_fit` so it tests
     the fit we report: draw 999 samples of size n from the fitted distribution, refit each with the same
     routine, compute A² of each, and p = (1 + the number ≥ the observed A²)/(1 + 999). The generator is
     seeded with a fixed value, so the same data give the same p-value. 999 samples give a standard error of
     about 0.007 at p = 0.05, enough for a check; 9999 cost ten times the time for a third digit nobody reads.
   - **Weibull through the Gumbel of ln x:** ln of a Weibull variable is a Gumbel (minimum) variable, the fit is
     the same maximum-likelihood fit, and A² is unchanged under the transform. Fitting `gumbel_l` to ln x takes
     about a tenth of the time of `weibull_min` with the location fixed, which matters 999 times.
   - **With any censored value in the group, no AD:** `anderson_darling_statistic` and
     `anderson_darling_p_value` are blank and the notes say "no Anderson–Darling check: n values are censored;
     judge the fit on the Q-Q plot". Never 0, never computed on the uncensored values alone.
   - The p-value is reported, not a pass or fail. The notes say what it means: a small p-value (below 0.05,
     say) is evidence against the distribution; a large one is not evidence for it, especially below 10 values.
8. **Plotting positions** (for P08's Q-Q panel, and in the result so a table can show them):
   - Without censoring, Hazen's positions, pᵢ = (i − 0.5)/n (Hazen 1914, p. 1549). Helsel et al. (2020,
     p. 22) prefer Weibull's i/(n + 1) for quantile plots, because i/n puts the largest value at p = 1; Hazen's
     doesn't (its largest is 1 − 0.5/n), and it extends to censored data as the midpoint of each value's
     Kaplan–Meier step, which Weibull's doesn't.
   - With right-censored values, the midpoint of each uncensored value's step in the Kaplan–Meier estimate of
     the CDF (`scipy.stats.ecdf`), (F(xᵢ⁻) + F(xᵢ))/2, which reduces to Hazen's without censoring. With
     left-censored values, the same on −x.
   - A group with both left- and right-censored values has no plotting positions (SciPy has no estimator for
     both, and Turnbull's is more than this unit needs); the Q-Q panel says so. Its fits and AICc stand.
9. **Bound diagnostics** (TODO #8 point 1): for each fit, `probability_below_lower_bound` = F(low) and
   `probability_above_upper_bound` = 1 − F(high), blank where the bound is `None`. 0 by construction for the
   positive distributions at low = 0 and for beta, reported as 0, not blank, so the column reads the same down
   the frame. A normal fit with more than 1 % below the lower bound gets a note.
10. **`FitResult`**, a frozen dataclass on the shared base (`_result.py`), `function="fit"`, `kind="property"`.
    - **Fields:** the base's, plus `by`, `pooled`, `include_assumed`, `bounds`, `distributions`, and `groups`:
      one record per group with its counts, its fits (name, SciPy parameters by name, ln L, AICc, Δ, weight,
      rank, A², p-value, the bound probabilities, convergence) and its plotting positions.
    - **`.to_frame()`:** one row per group and distribution, ranked: the `by` columns, `distribution`, `rank`,
      `count`, `count_censored`, the fitted distribution's `mean`, `standard_deviation`, `median`,
      `percentile_5` and `percentile_95` (in the value's units, so fits compare at a glance),
      `parameters` (text, "shape = 3.08, scale = 23.3 kPa"), `log_likelihood`, `aicc`, `delta_aicc`,
      `akaike_weight`, `anderson_darling_statistic`, `anderson_darling_p_value`,
      `probability_below_lower_bound`, `probability_above_upper_bound`; then the counts of rows left out, as
      `describe()`. A group with no fits has one row with `distribution` blank and its counts.
    - **`.distribution(name, group=None)`:** the fitted SciPy frozen distribution, for use downstream (M18);
      `group` required when there is more than one.
    - **`.to_dict()`**, `str()` and the notebook repr as `DescribeResult`: the text is a view of the frame.
    - **`.plot(group=None, **kwargs)`:** P08 for one group of this result, without refitting.
11. **No new SciPy beyond §12.1.** `scipy>=1.11` (CensoredData's `fit` arrived in 1.11); the oldest-versions run
    covers it.

### Sources
Checked 2026-10-30 against the copies in `sandbox/sources/` (not in the repo).
- **AICc, Δᵢ and Akaike weights:** Burnham, K.P. & Anderson, D.R. (2004). Multimodel inference: understanding
  AIC and BIC in model selection. *Sociological Methods & Research* 33(2), 261–304: AICc p. 270 ("should be used
  unless n/K > about 40"), Δᵢ = AICᵢ − AIC_min and its rough guide (Δ ≤ 2 substantial support, 4–7 considerably
  less, > 10 essentially none) p. 271, wᵢ = exp(−Δᵢ/2)/Σ exp(−Δᵣ/2) p. 272. Verified. (The 2002 book is not at
  hand; the paper states the same formulas.)
- **Anderson–Darling statistic:** NIST/SEMATECH *e-Handbook of Statistical Methods*, §1.3.5.14, A² = −N − S with
  S = Σ (2i − 1)/N [ln F(Yᵢ) + ln(1 − F(Y_{N+1−i}))], citing Stephens (1974). Verified. It also says published
  critical values exist only for some distributions (normal, lognormal, Weibull, …, not gamma) and depend on
  constants that differ between sources, which is the reason for the bootstrap (Decision 7). Stephens (1974)
  itself is 🔬 deferred (TODO #48).
- **Fitting censored values by maximum likelihood rather than at their limit:** Helsel, D.R., Hirsch, R.M.,
  Ryberg, K.R., Archfield, S.A. & Gilroy, E.J. (2020). *Statistical Methods in Water Resources*, USGS Techniques
  and Methods 4-A3, §12.7, pp. 356–357: substituting the reporting limit or a fraction of it "is highly
  inappropriate" and gives biased estimates; MLE with the censored values specified as censored is the better
  parametric approach. Verified (in the context of trend tests; the principle is the one Decision 3 applies).
- **Hazen plotting positions:** Hazen, A. (1914). Storage to be provided in impounding reservoirs for municipal
  water supply. *Trans. ASCE* 77, 1539–1669, p. 1549: each of n ranked terms is plotted "at the percentage which
  corresponds to the middle of its strip", (i − ½)/n. Helsel et al. (2020) Table 2.2, p. 23, lists it as type 5.
  Verified. The midpoint of each value's Kaplan–Meier step is the same rule with censoring: each uncensored
  value's strip is its KM step.
- 🔬 **Deferred (TODO #48), not available free:** Stephens (1974) *JASA*; Stute, González Manteiga & Presedo Quindimil
  (1993) *Metrika*, for the parametric bootstrap p-value with estimated parameters; Kaplan & Meier (1958)
  *JASA*, for the estimator. Volumes and pages are taken from the papers when checked. The docstrings cite the NIST handbook
  and SciPy's `goodness_of_fit` and `ecdf` documentation for these until the papers are checked, and say so.

### Acceptance criteria
Hand-calculated from the formulas above; tolerance 1e-9 relative unless stated.
1. **Normal and lognormal, closed form** (10, 12, 15, 20, 23 kPa):
   - normal: mean 16, standard deviation 4.8579831 (√23.6), ln L −14.99780945, AICc 39.99561889, P(X < 0)
     4.946575e−4 (Φ(−16/4.8579831));
   - lognormal: mean of ln x 2.72535369, σ of ln x 0.30924660, median 15.2618109, ln L −14.85337983, AICc
     39.70675966;
   - with only these two: lognormal rank 1, Δ 0.28885923 for normal, weights 0.53604477 and 0.46395523;
   - A² normal 0.26640897, lognormal 0.23962352 (1e-6).
2. **Gamma and Weibull:** parameters, ln L and AICc equal SciPy's `gamma.fit(x, floc=0)` and
   `weibull_min.fit(x, floc=0)` and their `logpdf` sums (1e-6); the Weibull fit through `gumbel_l` on ln x
   equals `weibull_min`'s (1e-6).
3. **AD p-value:** on 30 values drawn from a normal, the p-value is within 0.03 of `goodness_of_fit`'s at 9999
   samples on the same fit; on 30 values from an exponential, the normal fit's p-value is below 0.05; the same
   data give the same p-value on two calls.
4. **Censored:** SPT N60 12, 18, 25, 31, 40 with two refusals at 100 (`spt_refusal`): `count_at_least` 2; each
   fit's parameters equal SciPy's `fit(CensoredData(uncensored=[...], right=[100, 100]))` (1e-6); ln L equals
   the sum of Decision 6 computed from SciPy's `logpdf` and `logsf` at those parameters; AD blank with the note.
   A `<0.1` row is left-censored the same way.
5. **Plotting positions:** 10, 12, 15, 20, 23 give 0.1, 0.3, 0.5, 0.7, 0.9; with two right-censored values at
   30 added, 1/14, 3/14, 5/14, 7/14, 9/14 (Kaplan–Meier steps of 1/7). A group with both `<` and `>` values has
   none, with the note.
6. **Bounds:** `bounds="auto"` on a ratio-scale column gives `(0, None)`; on `elevation`, `(None, None)` and
   blank bound probabilities. Fines with `bounds=(0, 100)` add beta, whose parameters equal
   `beta.fit(x, floc=0, fscale=100)` (1e-6). A value of 105 with those bounds is an error. `"beta"` without
   bounds is an error.
7. **Values ≤ 0:** a group with an N of 0 fits normal only, with the note and count.
8. **Minimum n:** a group of 3 values gets a row with no fits and a warning; groups of 3 and 6 warn for both
   (once each kind); all groups below 4 is an error.
9. **Inputs, flags and sources:** `describe()`'s acceptance criteria 6–11 and 15 hold for `fit()` where they
   apply (NP, assumed, bands left out and counted, the source error and `pool=`, the three input forms); the
   counts add up to the group's rows.
10. **Units:** a psf frame fits in psf; `display_units="SI"` fits in kPa. With c = 0.04788026 kPa/psf, the
    normal mean and standard deviation scale by c, the lognormal median by c and its σ of ln x not at all, and
    each ln L shifts by −m ln c (m the uncensored values; a density scales by 1/c, a censored term's
    probability doesn't), so every AICc shifts by 2m ln c and `delta_aicc`, the weights and the ranks are
    unchanged (1e-9). `bounds` are read in display units.
11. **Result:** `.to_frame()` columns as Decision 10, ranked within each group; `.to_dict()` passes
    `json.dumps`; `.distribution("lognormal")` returns a frozen `lognorm` with AC 1's parameters; `str()`
    shows every number in the frame to 3 significant figures; `kind` is `"property"`.
12. **No `log=`:** passing it is Python's `TypeError`; the docstring says to use lognormal.
