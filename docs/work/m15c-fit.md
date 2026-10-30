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
