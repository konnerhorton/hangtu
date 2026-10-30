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
