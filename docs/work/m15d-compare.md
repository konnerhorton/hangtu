# M15 (d): `compare()` and `compare_groups()`, testing whether groups differ

## Intent
M15 is the statistics milestone (SPEC §1.3, §5, §12.4), split into four units (`docs/work/m15a-describe.md`,
decision 1). This unit, (d), tests whether a property differs between two groups, or among several, and closes
the statistics milestone apart from `crosstab()` (decision 1). It follows the input rules (a) set (SPEC §5) and
builds TODO #10 and #11 as agreed on 2026-10-29.

**Goal:** an engineer passes a property's values for two groups (two arrays, or a DataFrame with `value=` and
`by=`) and gets the difference between them with a confidence interval, Welch's t-test and a rank-based test side
by side, and a plain-English note on whether the two agree. For three or more groups, `compare_groups()` gives
Welch's ANOVA with Games–Howell pairwise comparisons alongside Kruskal–Wallis with Dunn's pairwise tests (Holm).

**Why:**
- **Splitting or merging geology units is a selection question.** "Are the upper and lower alluvium different in
  N60?" decides whether they get one parameter set or two (stage D, SPEC §1.3). P07 shows the groups side by
  side; nothing yet says whether the difference is larger than the scatter.
- **Sources are compared before they're combined.** SPEC §5 refuses to pool sources unawares (`pool=`). Before
  pooling lab s_u with an SPT correlation's estimates, or two labs' results, the engineer needs to know whether
  they differ; `by="correlation_name"` or `by="source"` makes each source its own group.
- **The usual recipe is poor at our sample sizes.** "Test normality, then choose t or Mann–Whitney" changes the
  main test's error rates, and the normality test has little power at n ≈ 10 (TODO #10: Rasch et al. 2011,
  Zimmerman 2004). Reporting Welch and a rank test together, always, avoids the pre-test and shows when the
  conclusion depends on the method.
- **SPEC §12.4's M15 row** lists `compare` and `compare_groups`; SciPy is already a dependency (M15 (c)).

**Scope:**
- `ht.stats.compare()`: two groups, as `compare(a, b)` or `compare(df, value=..., by=...)` with exactly two
  groups (more is an error that points to `compare_groups()`); `by=`, `pool=`, `include_assumed=`, `log=`,
  `units=` and `display_units=` as `describe()`, and the significance level as a judgment (decision 5). It
  reports:
  - each group's n, mean and standard deviation (through `describe()`'s calculation, so they agree with it);
  - **Welch's t-test** and the difference in means with its confidence interval, in the value's units; with
    `log=True`, the ratio of geometric means with its interval (TODO #10);
  - **a rank-based test** with its own effect size, the probability that a value from one group exceeds one from
    the other, with its interval (Brunner–Munzel rather than Mann–Whitney, decision 3);
  - a plain-English note: whether the two tests agree, and what that does and does not mean (decision 5).
- `ht.stats.compare_groups()`: the same inputs with `by=` naming three or more groups. Welch's ANOVA with
  Games–Howell pairwise comparisons, and Kruskal–Wallis with Dunn's pairwise tests, Holm-corrected (TODO #11);
  one row per pair with both tests' adjusted p-values and the difference with its interval.
- `CompareResult` and `CompareGroupsResult` on the shared result base, with `.to_frame()`, `.to_dict()` and a
  readable summary.
- Welch's ANOVA, Games–Howell and Dunn aren't in SciPy, so they are written here from the papers, each checked
  against a worked example in its source or a hand calculation (the spec step verifies the TODO #10/#11
  citations and writes the golden values).
- Reference entries, the statistics guide extended, and an example on the docs site using the example project's
  cases (N60 between two geology units; PI across several; a correlation's s_u against another's).

**Out of scope:**
- **`crosstab()`:** its own unit, M15 (e) (decision 1).
- **Censored-data tests** (Gehan, Peto–Prentice; Helsel 2012). Censored values enter at their value and are
  counted, as in `describe()` (decision 4); a TODO item records the better method.
- **Equivalence tests (TOST).** "No significant difference" is not "the same"; the note says so, and a test that
  can conclude "the same within ±x" needs an engineer's x, a judgment for selection (M18).
- **Spatial correlation and effective sample size:** values from one hole aren't independent. The note says the
  tests assume independent values; accounting for it is M18.
- **Paired comparisons** (two methods on the same specimens). Every case above is two independent groups; paired
  data waits for a real use.
- **A comparison figure.** P07 already draws groups side by side; marking pairwise results on it waits for a use.
- **Comparing variances or whole distributions** (Levene, Kolmogorov–Smirnov).

**SPEC and TODO touched:**
- SPEC §4 (`significance_level` added to the list of judgments, decision 5), §5 (`compare` and `compare_groups` built; the rule that statistics functions don't pre-test assumptions
  but report a parametric and a rank test together, decision 2), §12.4 (M15 row: (d) and, if decision 1 holds,
  (e) `crosstab`).
- Other docs: `docs/drafts/phase3-stats.md` (the two rows decided, pointing here).
- TODO: #10 and #11 resolved and removed; a new item for censored-data comparisons.

### Decisions (intent review, 2026-10-30)
1. **`crosstab()` moves to its own unit, M15 (e).** It is categorical, runs no test, returns a different kind
   of result, and its mismatch listing needs a rule of its own (when do "CL" and "Alluvium" count as a mismatch?
   only when the two columns share a vocabulary or a mapping is given). Together the three functions are more
   than one sitting.
2. **No pre-tests, ever.** Neither function tests normality or equal variances to choose a method; both report
   the parametric and the rank-based result. This goes in SPEC §5 so later functions follow it.
3. **Brunner–Munzel as `compare()`'s rank test, not Mann–Whitney.** Mann–Whitney assumes equal shapes and
   misleads when variances differ (Fagerland & Sandvik 2009), which is the case Welch exists for; Brunner–Munzel
   doesn't, and its estimate is itself the effect size (probability of superiority). SciPy's version uses a t
   approximation that is poor below about 10 per group; whether to use its permutation form there is a spec
   question.
4. **Censored values as in `describe()`.** Refusals and `<x`/`>x` enter at their value and are counted, with a
   note that the means are biased; the rank test treats a common cap as tied at the top, which is closer to
   right. Bands are left out and counted (SPEC §5).
5. **The significance level is a judgment, `significance_level`, with no default** (SPEC §4). It resolves as
   every judgment does: the argument, then the judgments file, then an error naming it; the result records it
   and its source. It changes what the note concludes, and 0.05 is a convention, not a law, so the engineer sets
   it on purpose rather than inheriting it; a default here would also be the one judgment with one. It is
   project-wide (no key); whether it needs a `reason` there as other project-wide values do is a spec question.
   The note never says two groups "are the same": it says the data don't show a difference at that level, with
   the interval for scale. The p-values don't depend on it. 🟡 Whether the intervals' confidence level follows it
   (1 − significance level) or is its own argument is a spec question.
6. **Minimum n: an error below 2 values in a group, a warning below 5** (TODO #10), naming the group and its n.
   `compare_groups()` applies them per group.

## Spec
Numbered items refer to this section's decisions; "intent n" to the intent's. 🟡 marks a choice proposed here and
not yet agreed.

**What SciPy does** (checked 2026-10-30 on 1.15.3, 1.16.0, 1.17.0 and 1.18.1):
- `ttest_ind(equal_var=False)` gives Welch's t, its degrees of freedom and `.confidence_interval()` on every
  allowed version, and reproduces Helsel et al. (2020) Examples 5.3 and 5.4 to every printed digit (AC 1).
- `f_oneway(equal_var=False)` (Welch's ANOVA) and `tukey_hsd(equal_var=False)` (Games–Howell, with
  `.confidence_interval()`) arrived in **1.16.0**; 1.15.3 has neither.
- `brunnermunzel` gives the statistic and p-value but not its degrees of freedom or an interval for p̂, and it
  divides by zero when the groups don't overlap. Its statistic is positive when the *second* sample tends larger.
- `kruskal` corrects for ties. There is no Dunn's test and no Holm adjustment (`false_discovery_control` is
  Benjamini–Hochberg). `permutation_test` enumerates exactly when the permutations are fewer than `n_resamples`.

### Changes
- **SPEC §4:** `significance_level` added to the list of judgments, the first project-wide-only one (Decision 8).
- **SPEC §5:** `compare` and `compare_groups` built; the rule "no pre-tests: report a parametric and a rank-based
  result together" (intent 2); `crosstab` moved to (e); the result list gains `CompareResult` and
  `CompareGroupsResult`.
- **SPEC §12.1:** `scipy>=1.16.0` (Decision 1). **§12.4:** M15 row, (d) done and (e) `crosstab` added.
- **`docs/drafts/phase3-stats.md`:** the `compare` and `compare_groups` rows decided, pointing here; `crosstab`
  marked M15 (e).
- **TODO:** #10 and #11 removed; #48 widened to every statistics source not yet checked (Sources); new #49 for
  censored-data comparisons (Gehan, Peto–Prentice; Helsel et al. 2020 ch. 13 is a starting point).
- **Docs site:** `compare`, `compare_groups`, `CompareResult` and `CompareGroupsResult` in the reference; a
  "Comparing groups" section in the statistics guide, with an example on the example project; the judgments
  page gains `significance_level`.

### Decisions
1. 🟡 **SciPy floor raised to 1.16.0, and its Welch's ANOVA and Games–Howell used.** They are tested upstream
   and cite the original papers; writing them here would be about 150 lines plus tests to reproduce what 1.16
   already does. 1.16.0 (June 2025) needs Python ≥ 3.11, and hangtu needs 3.12. The oldest-versions run
   confirms the floor; a patch release is chosen instead if 1.16.0 fails it. Welch's t-test and Kruskal–Wallis
   come from SciPy too. Brunner–Munzel, Dunn and Holm are written here (Decisions 4, 6).
2. **`ht.stats.compare()`.**
   ```python
   compare(data, other=None, *, value=None, by=None, groups=None, log=False,
           significance_level=None, judgments=None, pool=None, include_assumed=False,
           units=None, display_units=None) -> CompareResult
   ```
   - **Two groups, three ways:** `compare(a, b)` with two arrays or Series (named by the Series' names, else
     `"first"` and `"second"`); `compare(df_a, df_b, value=...)` with two DataFrames (a lab frame and a
     correlation's estimates); or `compare(df, value=..., by=...)` with exactly two groups.
   - **`groups=`:** two keys of `by` to compare, in that order, so `by="geology_unit"` needn't be filtered
     first. Without it, `by` giving other than two groups is an error naming the groups and pointing to
     `groups=` and to `compare_groups()`; with it, an unknown key is an error listing the keys.
   - **Order:** every difference is first minus second, and the probability is of the first exceeding the
     second. The order is the arguments', `groups=`'s, or `describe()`'s group order; the result names both
     groups, so the direction is never implicit.
   - **`value=`, `by=`, `pool=`, `include_assumed=`, `units=`, `display_units=`:** as `describe()`, through the
     same row reading (`_rows.py`). The source check (SPEC §5) applies within each group, never across the two:
     comparing sources is what `by="correlation_name"` is for. Two frames must resolve to the same unit after
     `display_units=`, or it is an error naming both.
   - **`log=True`:** the parametric results are on ln x, and reported as the ratio of geometric means (first /
     second) with its interval, exp of the interval of the difference of ln x (Helsel et al. 2020 §5.3.4). The
     rank test is the same either way (ln keeps the order); the note says so. A value ≤ 0 with `log=True` is an
     error naming its count, as `describe()`.
3. **Welch's t-test** (Welch 1947; Helsel et al. 2020 §5.3.3, which says to use it always). From
   `ttest_ind(equal_var=False)`: `welch_t_statistic`, `welch_degrees_of_freedom`, `welch_p_value` (two-sided),
   and `difference` (mean of the first − mean of the second; with `log=True`, `ratio`) with
   `difference_lower`/`difference_upper` at the confidence level (Decision 8). Each group's `count`, `mean` and
   `standard_deviation` come from `describe()`'s calculation, so they agree with it.
   - Both standard deviations 0: no Welch result (blank, a note: "every value in both groups is the same").
4. **Brunner–Munzel** (intent 3), written here so the result can carry its degrees of freedom and an interval.
   - **The effect size**, `probability_of_superiority` = P(X₁ > X₂) + ½ P(X₁ = X₂), estimated as the mean over
     all n₁n₂ pairs of 1 (first larger), ½ (tied) or 0 (Karch 2021, p. 6, with the groups' roles swapped so it
     reads "the first exceeds the second"). 0.5 is no tendency either way.
   - **The statistic and its degrees of freedom** follow Brunner & Munzel (2000) as SciPy implements it; the
     statistic, `brunner_munzel_statistic`, is signed so it is positive when the first group tends larger.
   - **The p-value, by group size** (Karch 2021, p. 8: the permutation form has better Type I error control
     below 10 per group; the t approximation held 4.6–5.7 % above 10 in Brunner & Munzel's simulations):
     - both groups ≥ 10: the t approximation, two-sided;
     - either group < 10: a permutation test of the same statistic (Neubert & Brunner 2007), by
       `permutation_test`: exact when there are at most 9999 ways to split the values, else 9999 random splits
       from a fixed seed, so a result is reproducible. `brunner_munzel_method` records which
       (`"t"`, `"permutation, exact"`, `"permutation, 9999 resamples"`).
   - **The interval** for `probability_of_superiority` (`_lower`/`_upper`): p̂ ± t(df) × its standard error, at
     the confidence level, only when both groups have ≥ 10 values; below 10, blank with a note, because the
     approximation behind it is the one the permutation replaces. 🟡 Clipped to [0, 1], noted when it is.
   - **Groups that don't overlap** (p̂ = 0 or 1): the variance estimate is 0 and the t statistic infinite. The
     statistic is reported as ±inf; below 10 per group the permutation still gives a p-value (no split is more
     extreme); at 10 or more, the p-value is blank and the note says the groups don't overlap, every value of
     one above every value of the other. Never a division-by-zero warning to the user.
5. **`ht.stats.compare_groups()`.** The same arguments as `compare()` but `other=` and `groups=` (all groups
   of `by` are compared), and `by=` required.
   - **Overall tests:** Welch's ANOVA, `f_oneway(equal_var=False)` (Welch 1951; Delacre et al. 2019 eqs. 7–9):
     `welch_f_statistic`, `welch_degrees_of_freedom_numerator`, `_denominator`, `welch_p_value`; and
     Kruskal–Wallis with the tie correction, `kruskal` (Kruskal & Wallis 1952; Helsel et al. 2020 §7.1):
     `kruskal_wallis_statistic`, `kruskal_wallis_degrees_of_freedom`, `kruskal_wallis_p_value`.
   - **Pairs:** every pair, first in group order: `difference` (or `ratio`) with its Games–Howell interval and
     `games_howell_p_value` from `tukey_hsd(equal_var=False)` (Games & Howell 1976); and Dunn's `dunn_z_statistic`
     and `dunn_p_value`, Holm-adjusted (Decision 6). Both p-values are family-wise (adjusted for the number of
     pairs), so they compare like with like; the frame says so in its notes.
   - **Pairs are reported whatever the overall tests say.** A family-wise procedure doesn't need a significant
     overall test first (Helsel et al. 2020 §7.7).
   - **Two groups** are allowed (Welch's F is then Welch's t², Delacre et al. 2019; Games–Howell's p equals
     Welch's), with a note that `compare()` adds the Brunner–Munzel test and the probability of superiority.
   - **A group with fewer than 2 values** is left out of the tests, its row kept with its counts and the
     reason, with one warning naming the groups (as `fit()`, M15 (c) Decision 5). Fewer than 2 groups left is
     an error.
6. **Dunn's test and Holm's adjustment** (TODO #11), written here.
   - All values are ranked together (mid-ranks for ties), as Kruskal–Wallis ranks them. For groups i and j with
     mean ranks R̄ᵢ, R̄ⱼ: z = (R̄ᵢ − R̄ⱼ) / √{[N(N + 1)/12 − Σ(t³ − t)/(12(N − 1))](1/nᵢ + 1/nⱼ)}, with t each
     tie's size and N all values (Dunn 1964); the two-sided p is 2(1 − Φ(|z|)). Dinno (2015) describes the
     test and gives a worked example, which this reproduces (AC 8).
   - **Holm** (Holm 1979, as Dinno 2015 §2.3 describes it): order the m p-values from smallest, multiply the
     i-th by (m + 1 − i), cap at 1, and carry the running maximum forward so the adjusted values keep their
     order.
   - 🟡 **Holm, not Benjamini–Hochberg.** Helsel et al. (2020, p. 190) recommend Benjamini–Hochberg for pairwise
     rank tests, for its power. It controls the false discovery rate, while Games–Howell controls the
     family-wise error rate; with Holm both pair columns answer the same question, so "the two tests agree"
     means something. Benjamini–Hochberg could be an option later; TODO #11 agreed Holm.
7. **Censored values** (intent 4). Refusals and `<x`/`>x` enter at their value and are counted
   (`count_at_least`, `count_at_most`, as `describe()`), with a note that the means, and so Welch's results,
   are biased by them; ranks treat values at a common cap as tied at the top, which is closer to right but not
   right either. A group that is all censored at one value is reported with its counts and no tests. Better
   methods are TODO #49.
8. **The significance level and the confidence level** (intent 5).
   - **`significance_level`** (α) is a judgment: the argument, then `judgments=`, then the Project's file,
     then an error naming it and showing the file entry (SPEC §4). It must be strictly between 0 and 1; outside
     0.001–0.2 it warns, as `specific_gravity` warns outside its range. The result records it and where it came
     from.
   - **The confidence level is 1 − α and is not set on its own** 🟡. The two are complements, so they have
     distinct names (`significance_level` 0.05, `confidence_level` 0.95, both in the result and the frame) but
     one input. Tying them means Welch's interval excludes 0 exactly when its p-value is below α, and the same
     for Games–Howell, so the note and the interval can't disagree. A separate `confidence_level=` input would
     let them.
   - **The file entry** is project-wide only, with no keys, and needs a `reason` as every project-wide value
     does:
     ```yaml
     significance_level:
       project: {significance_level: 0.05, reason: "the usual convention; agreed with the reviewer"}
     ```
     A `values:` or `by:` under it is an error saying it takes only `project:`.
   - **What it changes:** the note's conclusions and the intervals' level. The p-values don't depend on it.
9. **The note** (intent 2, 5) is part of the result's notes, in this order:
   1. **What each test found**, at α, in words: "Welch's t-test finds the means differ (p = 0.003)"; "The
      Brunner–Munzel test doesn't find that values in A tend to exceed those in B, or the reverse (p = 0.41)".
   2. **Whether they agree.** Agree on a difference: the difference with its interval and p̂. Agree on none: "This
      doesn't show the groups are the same: the difference in means could be anywhere from a to b kPa." Disagree:
      Welch only, "the means differ but neither group's values tend to exceed the other's: often one or two
      extreme values moving a mean"; rank only, "values in A tend to exceed those in B but the means don't
      clearly differ: often a skewed group or an extreme value widening the spread; log=True compares geometric
      means". Each ends "look at the values (P07)".
   3. **What the tests assume:** independent values. Values from one hole, or close together, aren't; the
      p-values are then too small. Accounting for it is selection (M18).
   4. The censored, small-group, permutation and non-overlap notes as they apply.
   `compare_groups()` gives one such note per pair whose two pair tests disagree, and one for the overall tests.
10. **Minimum n** (intent 6): `compare()` errors below 2 values in either group, naming it and its n;
    both functions warn once below 5, naming the groups (TODO #10: very low power).
11. **`CompareResult` and `CompareGroupsResult`**, frozen dataclasses on the shared base, `function="compare"`
    or `"compare_groups"`, `kind="property"`.
    - **Fields:** the base's, plus `by`, `groups` (each group's key, counts and statistics), `log`, `pooled`,
      `include_assumed`, `significance_level`, `confidence_level`, the significance level's source, and the test
      results; `CompareGroupsResult` adds `pairs`.
    - **`CompareResult.to_frame()`:** one row: `group_1`, `group_2` (the keys, as text), `count_1`, `count_2`,
      `mean_1`, `mean_2`, `standard_deviation_1`, `standard_deviation_2` (geometric mean and the standard
      deviation of ln x with `log=True`, named `geometric_mean_1`, …), `difference` or `ratio`, `_lower`,
      `_upper`, the Welch columns, `probability_of_superiority` with `_lower`/`_upper`, the Brunner–Munzel
      columns, `significance_level`, `confidence_level`; then each group's counts of rows left out, suffixed
      `_1`/`_2`.
    - **`CompareGroupsResult.to_frame()`:** one row per pair, as above but with the Games–Howell and Dunn
      columns. **`.overall()`:** one row with the Welch's ANOVA and Kruskal–Wallis columns.
      **`.groups_frame()`:** `describe()`'s frame for the groups, so the counts left out are in one place.
    - **`.to_dict()`**, `str()` and the notebook repr as `DescribeResult`: the text is a view of the frames.
    - **Names:** checked against the registry on 2026-10-30; none of the new names is a column there. They are
      result columns, not registry columns, as `fit()`'s are. `difference_lower`/`_upper` follow the band
      convention (`<target>_lower`/`_upper`, SPEC §4).

### Sources
Checked 2026-10-30 against the copies in `sandbox/sources/` (not in the repo).
- **Welch's t-test, always, and on logs comparing geometric means:** Helsel, D.R., Hirsch, R.M., Ryberg, K.R.,
  Archfield, S.A. & Gilroy, E.J. (2020). *Statistical Methods in Water Resources*, USGS Techniques and Methods
  4-A3: §5.3.3, p. 127 ("Always assume unequal variances"); §5.3.4, p. 129 (logs compare geometric means);
  Example 5.1, p. 120 (the data), Examples 5.3 and 5.4, pp. 128–129 (the results). Verified.
- **Welch's ANOVA:** Delacre, M., Leys, C., Mora, Y.L. & Lakens, D. (2019). Taking parametric assumptions
  seriously: arguments for the use of Welch's F-test instead of the classical F-test in one-way ANOVA.
  *International Review of Social Psychology* 32(1), 13, doi:10.5334/irsp.198: eqs. 7–9 (W, wⱼ = nⱼ/sⱼ², the
  degrees of freedom), and W equals Welch's t² for two groups. Verified (open access). Helsel et al. (2020)
  §7.2.4, p. 174, prefers it to classic ANOVA, with no formula. Welch (1951) itself is 🔬 deferred.
- **Kruskal–Wallis:** Helsel et al. (2020) §7.1.3, eqs. 7.2–7.3 and Table 7.4, p. 168. Verified. Table 7.4
  prints K = 2.66 from mean ranks rounded to one decimal; the unrounded ranks give 2.6866667 (AC 7).
- **Multiple comparisons need no significant overall test first; Dunn uses the joint ranks:** Helsel et al.
  (2020) §7.7 and §7.7.2, pp. 185–191. Verified.
- **Dunn's test and the Holm adjustment:** Dinno, A. (2015). Nonparametric pairwise multiple comparisons in
  independent groups using Dunn's test. *Stata Journal* 15(1), 292–300: §2.2 (the test and its tie
  correction), §2.3 (Holm: the i-th smallest p times m + 1 − i), Example 1 (rank sums and z). Verified. Dinno
  doesn't print the z formula; Decision 6's is Dunn's (1964), checked by reproducing Example 1 (AC 8). Dunn
  (1964) and Holm (1979) themselves are 🔬 deferred.
- **Brunner–Munzel over Mann–Whitney, p̂, and the permutation form below 10:** Karch, J.D. (2021).
  Psychologists should use Brunner-Munzel's instead of Mann-Whitney's U test as the default nonparametric
  procedure. *Advances in Methods and Practices in Psychological Science* 4(2), doi:10.1177/2515245921999602:
  p̂ p. 6; Type I error and the permutation form p. 8. Verified (open access). Karch gives σ̂ only by reference
  to Neubert & Brunner (2007, p. 5194), so the statistic and its degrees of freedom are SciPy's
  `brunnermunzel` (which cites Brunner & Munzel 2000), checked against it (AC 3).
- 🔬 **Deferred (TODO #48), not available free:** Welch (1947) and (1951), *Biometrika*; Games & Howell (1976),
  *Journal of Educational Statistics* (SciPy's `tukey_hsd` cites it); Brunner & Munzel (2000) and Neubert &
  Brunner (2007), for σ̂ and the interval for p̂; Dunn (1964), *Technometrics*; Holm (1979), *Scandinavian
  Journal of Statistics*; Fagerland & Sandvik (2009). The docstrings cite the verified sources above and say
  which papers are not yet checked.

### Acceptance criteria
Hand-calculated from the formulas above or taken from a verified source's printed results; tolerance 1e-9
relative unless stated, or the source's printed precision.
1. **Welch, Helsel's data** (Example 5.1; industrial first, 10 values each): `difference` 0.028,
   `welch_t_statistic` 0.029044, `welch_degrees_of_freedom` 11.555, `welch_p_value` 0.9773, interval
   −2.081479 to 2.137479 at α = 0.05 (to the printed digits). With `log=True`: t 1.3578, df 14.684, p 0.195;
   `ratio` exp(0.3518488 + 0.1286373) = 1.6168603, interval exp(−0.275160) = 0.7594506 to exp(1.236132) =
   3.4422730 (1e-6).
2. **The note disagrees on Helsel's data:** at α = 0.05 Welch's p is 0.977 and Brunner–Munzel's 0.0403
   (AC 3), and the note says the rank test finds the first group's values tend to be higher while the means
   don't clearly differ, suggesting `log=True`.
3. **Brunner–Munzel:**
   - Helsel's data (10 and 10, the t approximation): `probability_of_superiority` 0.765 (76.5 of 100 pairs:
     counted by hand from Example 5.1's ranks); statistic +2.2392145 and p 0.0403155, equal to SciPy's
     `brunnermunzel(second, first)`; the degrees of freedom reproduce that p-value (1e-9); the interval is
     p̂ ± t × (p̂ − 0.5)/statistic, clipped to [0, 1].
   - 12, 15, 18, 20, 22 against 14, 16, 17, 21 (5 and 4, exact permutation over the 126 splits):
     p̂ 0.55, statistic 0.2245444, p 96/126 = 0.76190476; method `"permutation, exact"`; interval blank with
     the note. Splits whose groups don't overlap count as most extreme.
   - 1, 2, 3 against 4, 5, 6: p̂ 0, statistic −inf, exact permutation p 2/20 = 0.1, no warning from SciPy
     reaching the user. Twelve against twelve that don't overlap: p-value blank, the non-overlap note.
4. **Welch's ANOVA and Games–Howell**, on A: 12, 15, 18, 20, 22; B: 25, 28, 30, 35, 41, 44; C: 14, 16, 17, 21:
   - W 11.98457980, degrees of freedom 2 and 7.98204548, p 0.00394381, from Delacre et al.'s eqs. 7–9 by hand;
     equal to `f_oneway(equal_var=False)`;
   - Games–Howell p for A–B 0.00449133, A–C 0.98361561, B–C 0.00420186, and A–B's 95 % interval −26.6216109 to
     −6.2450558, equal to `tukey_hsd(equal_var=False)` (1e-6);
   - on Helsel's two groups, W = 0.029044² and Games–Howell's p = Welch's 0.9773249.
5. **Kruskal–Wallis and Dunn** on the same A, B, C (N = 15, no ties): mean ranks 5.2, 12.5, 4.75; H 10.1475,
   p 0.00625891; Dunn z A–B −2.6957037, B–C 2.6846788, A–C 0.15; unadjusted p 0.00702401, 0.00725995,
   0.88076462; Holm 0.02107204, 0.02107204 (3 × 0.00702401, then max(2 × 0.00725995, 0.02107204)), 0.88076462.
6. **Holm, with ties in the data,** on Helsel's Table 7.4 ranks: the tie term Σ(t³ − t) = 12; the six Dunn
   z values as Decision 6 (Summer–Spring 1.4294907, …); Holm-adjusted p all 0.91717953 or 1.
7. **Kruskal–Wallis, Helsel Table 7.4:** K 2.6866667 by eq. 7.3 (Helsel prints 2.66 from rounded means), the
   tie-corrected H 2.6890049, p 0.44209903 (Helsel: 0.44), equal to `kruskal`.
8. **Dunn, Dinno's Example 1:** from the printed rank sums (NE 9, 376.5; N Cntrl 12, 294.0; N = 50) and the tie
   term implied by the printed χ² (17.041 untied, 17.062 tied), NE–N Cntrl z = 2.69819, Dinno's 2.698212 to 1e-4
   (the χ² is printed to 3 decimals).
9. **The significance level:** missing everywhere is an error naming `significance_level` and showing the
   entry; the argument wins over the file with a warning; 0 or 1 is an error; 0.3 warns; a `values:` entry is an
   error; the result records 0.05, its source, and `confidence_level` 0.95; an interval at α = 0.10 is narrower
   than at 0.05 and the p-values are unchanged.
10. **Inputs:** `compare(a, b)`, two frames, and `by=` give the same result on the same values; `by=` with three
    groups and no `groups=` is an error naming them; `groups=("C", "A")` reverses the sign of `difference`
    and gives 1 − p̂; two frames in different units with no `display_units=` are an error; a two-source group is
    the source error, and two groups of one source each are not.
11. **Flags and counts:** `describe()`'s acceptance criteria 6–11 hold per group (NP, assumed, bands left out
    and counted, text values); refusals counted as `count_at_least` with the note; counts add up per group.
12. **Small groups:** `compare()` with a group of 1 is an error; groups of 3 and 4 warn once;
    `compare_groups()` with one group of 1 among four leaves it out with a warning, and with three groups of 1
    is an error.
13. **Units:** a psf frame compares in psf; `display_units="SI"` in kPa; the differences and intervals scale by
    0.04788026, and every p-value, statistic and p̂ is unchanged (1e-9).
14. **Result:** `.to_frame()` columns as Decision 11; `.to_dict()` passes `json.dumps`; `str()` shows every
    number in the frame to 3 significant figures and the note; `kind` is `"property"`.
