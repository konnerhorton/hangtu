# Statistics: what each function does

| | |
|---|---|
| **Status** | Living spec. `describe` (M15 a), `fit` (M15 c), `compare` and `compare_groups` (M15 d), `crosstab` (M15 e), `representative` (M18 b), `compare_sources` (M18 d) built |
| **Parent** | SPEC §5: the result object, "one calculation, many views", the input rules every function follows, and why statistics are designed for lab data |
| **Related** | [`m15a-describe.md`](../work/m15a-describe.md), [`m15c-fit.md`](../work/m15c-fit.md), [`m15d-compare.md`](../work/m15d-compare.md), [`m15e-crosstab.md`](../work/m15e-crosstab.md), [`m18a-refusals.md`](../work/m18a-refusals.md), [`m18b-representative-values.md`](../work/m18b-representative-values.md), [`m18d-sources-compared.md`](../work/m18d-sources-compared.md). Draft notes: [`../drafts/phase3-stats.md`](../drafts/phase3-stats.md). Background: [`../reference/eurocode7-summary.md`](../reference/eurocode7-summary.md) |

Update this file in the same commit as any change to a function's behavior, and SPEC §5 if the change alters a rule there.

## 1. `fit()`
Decided 2026-10-30, M15 (c), [`docs/work/m15c-fit.md`](../work/m15c-fit.md).
- Fits normal, lognormal, gamma and Weibull (two parameters, the positive ones located at 0), and beta between two given bounds, by maximum likelihood with censored values as censored.
- Ranks them by AICc.
- Checks each with an Anderson–Darling p-value by seeded parametric bootstrap: none when a value is censored, and with a note that ties read as misfit when a group has fewer distinct values than half its count (decided 2026-11-02, TODO #50).
- Reports each fit's probability beyond the physical bounds.
- A group needs 4 uncensored values.
- It never chooses the distribution: selection (M18) records that choice.
- Takes no `log=True`: a normal fit to the logs is its lognormal fit.

**Refusals** (decided 2026-11-02, TODO #49; built in M18 (a)):
- They stay right-censored at their N60 by default: that is the test's result as ASTM D1586 defines refusal, not a judgment.
- An optional judgment, an upper limit per geology unit (`spt_refusal_upper_limit`, SPEC §4), makes them interval-censored between their value and the limit, so the fitted tail can reflect the ground where the penetration shows refusals well above the cap. hangtu doesn't extrapolate blows from penetration.
- The limit is field N and scales per row by value / `spt_n` for N60 and (N1)60; `spt_n` and `spt_n_capped` take it as is.
- On the Q-Q panel an interval is placed as right-censored at its value.

## 2. `representative()`
Decided 2026-11-03, M18 (b), [`docs/work/m18b-representative-values.md`](../work/m18b-representative-values.md).
- Gives one view per call, constant per group or as a line with depth:
  - EC7's characteristic value (Types A, B and C, V_X computed or assumed, from the JRC report, EUR 40260, which quotes EN 1997-1:2024);
  - a percentile of the fitted distribution;
  - the mean less k standard deviations.
- The method, side, distribution and each input the method needs are required: none has a default, because each is the engineer's judgment.
- Type C's Γ² is θ/L, capped at 1, as the JRC gives it.
- A lognormal view works on ln x.
- A constant takes censored values through the censored maximum-likelihood fit; a trend (Bond & Harris 2008's confidence and prediction intervals) leaves them out and counts them.
- The result gives P01's `design_lines` frame, and P09 (`ht.plot.representative_profile()`, `RepresentativeResult.plot()`) draws it with the mean and the view ([`P09`](../plots/P09-representative-profile.md), M18 (c)).

## 3. `compare()` and `compare_groups()`
Decided 2026-10-30, M15 (d), [`docs/work/m15d-compare.md`](../work/m15d-compare.md).
- **No pre-tests:** no statistics function tests normality or equal variances to choose a method. Each reports a parametric and a rank-based result together, and a plain-English note on whether they agree. The note never says groups "are the same", only that the data don't show a difference at α, with the interval for scale.
- `compare()` gives Welch's t-test with the difference (or, with `log=True`, the ratio of geometric means) and its interval, beside the Brunner–Munzel test with the probability of superiority (a permutation p-value below 10 values per group, Karch 2021).
- `compare_groups()` gives Welch's ANOVA and Kruskal–Wallis, and every pair's Games–Howell interval and p beside Dunn's test with Holm's adjustment, both family-wise.
- The significance level is a judgment with no default (`significance_level`, SPEC §4); intervals are at 1 − α.
- Censored values enter at their value and are counted, as in `describe()` (better methods: TODO #51).
- The tests assume independent values, and the note says so.

## 4. `crosstab()`
Decided 2026-10-30, M15 (e), [`docs/work/m15e-crosstab.md`](../work/m15e-crosstab.md).
- Counts two text columns of the same rows against each other, values as written (SPEC §8.3's exact match), blanks as `"(blank)"`. It follows only the input rule "counts add up".
- Agreement is counted only when the user says what agrees (`agree="same"`, or a mapping that names every class it is asked about), never inferred.
- A row blank on either side is counted on its own, never as a mismatch.
- No test or chance-corrected agreement (TODO #52).

## 5. `compare_sources()`
Decided 2026-11-05, M18 (d), [`docs/work/m18d-sources-compared.md`](../work/m18d-sources-compared.md) (decisions 8–16).
- Puts every source of one parameter side by side, per geology unit (`by=`), for stage D: DataFrames of rows, a `MohrCoulombFit`'s main fit, and a `ShearBoxConversion` from `ht.analysis.friction_angle_from_shear_box()`. A `ShearBoxFit` is refused: a direct shear φ′ isn't a triaxial φ′ until converted (SPEC §5).
- **Never pooled, no `pool=`:** grouping by source is the point. A row's source is its non-blank registry source columns (`source`, `test_type`, `correlation_name`, `conversion_name`), joined, in `parameter_source`; a repeated label across arguments takes " (source n)".
- Row sources follow `describe()`'s input rules and statistics exactly (flags, bands and non-plastic values left out and counted, assumed values only with `include_assumed=True`, censored values at their value and counted, H&F 7 with each percentile's floor).
- A fit in a unit is one value with `count_points`, `r_squared`, its normal stress range and its points' depths, and no standard error. Fits per sample in a unit are summarized like rows.
- **Descriptive, no tests:** a fit's value is placed among each row source's values in the unit (`position` below, within or above the range; within it and from 4 values, `percentile_rank`, the inverse of H&F 7, ties at the middle of their run). `compare()` is the check for two row sources (SPEC §5: "tests are a check").
- Nothing is dropped: every unit of every source is listed, an empty pair with `count` 0 and a `no_value_reason`.
- Views: `.to_frame()`, `.positions()`, `.values()` (the long frame the figures draw, every row kept, a fit at the middle of its points' depths with `depth_top`/`depth_base`), `.profile()` (P01 of one unit, so its stats box equals that unit's table) and `.geology_unit_comparison()` (P07 with `split_by="parameter_source"` and `summary_min_count=1`, so the percentile floors alone decide where a bar is drawn).
