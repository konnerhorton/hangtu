# Statistics

Summarize test values by geology unit, with the count, spread and percentiles a design report needs, and with every flagged value counted rather than dropped; fit distributions to them; and test whether groups differ.

```python
--8<-- "statistics.py"
```

``` { .text .no-copy }
--8<-- "statistics.txt"
```

## What `describe()` reports

`ht.stats.describe()` takes a dataset and the column to summarize, and optionally `by=`, the columns to group by. For each group it reports the count, mean, standard deviation, coefficient of variation (CoV), minimum, median, maximum and percentiles, in the column's units. `print(result)` shows them as a table with its notes; `result.to_frame()` gives one row per group; `result.to_dict()` gives everything, ready for a report.

A statistic is left blank (—) when there are too few values for it to mean anything, and the notes say why:

- the standard deviation and CoV need 2 values;
- each percentile needs at least one value beyond it on each side: P25 and P75 need 4 values, P10 and P90 need 10, P5 and P95 need 20;
- CoV needs a mean above 0, and isn't reported for a column with no true zero, such as elevation.

A group with fewer than 3 values warns. Percentiles are always Hyndman & Fan (1996) definition 7, the linear interpolation of NumPy and Excel's `PERCENTILE.INC`, so two summaries of the same rows never differ by method. P01's stats box and P07's bars come from the same calculation, so a figure and a table of the same values agree.

## Flagged values are counted

The registry says which columns flag a value (`ht.columns()`), and `describe()` reads them whenever they are in the dataset:

| Value | Treatment | Count |
|---|---|---|
| A refusal (`spt_refusal`), or `>` in `qualifier` | Summarized at the value the column holds; the notes say the mean is then an underestimate | `count_at_least` |
| `<` in `qualifier` | Summarized at its value; the mean is an overestimate | `count_at_most` |
| Non-plastic (`non_plastic`, or `NP` in the cell) | Left out; never a blank or a zero | `count_non_plastic` |
| Assumed (`particle_density_assumed`; a Gs from a judgment) | Left out with a warning, unless `include_assumed=True` | `count_assumed` |
| A correlation's band with no value (`_lower`, `_upper`) | Left out: a band is an interval, not two values | `count_range` |
| Other text, or a blank cell | Left out | `count_text`, `count_blank` |

`count` and the counts of rows left out add up to the group's rows. A refusal is summarized at whatever the column holds, so pick the column on purpose: `spt_n_capped` gives the refusal at the cap, `spt_n` the blows reported.

## Sources aren't pooled unawares

Rows from different sources in one summary raise an error that lists every value and its count: different correlations (`correlation_name`, blank for a measured value), lab and field tests (`source`), or test methods (`test_type`). Group by the column, filter the rows, or pool them on purpose with `pool=["source"]`. A pooled result records it, with the count of each source, so a reviewer can see it.

Two spellings of one test method count as two sources. The error lists them both, so you can see and fix the naming.

## Log scale

For values spanning orders of magnitude, such as hydraulic conductivity, `log=True` reports the geometric mean and the geometric standard deviation, a factor with no unit, in place of the mean, standard deviation and CoV. The minimum, median, maximum and percentiles are of the values themselves. Values at or below 0 are left out and counted.

## Units

The unit comes from `units=`, then from the dataset's declared units, and counts, percentages and dimensionless columns need none. A column whose unit is unknown is an error. `display_units="SI"` or `"US"` converts the values before summarizing; the session setting is never used, so a summary doesn't change with it.

## Fitting a distribution

`ht.stats.fit()` fits normal, lognormal, gamma and Weibull distributions to a column's values in each group, by maximum likelihood, and ranks them. It reads the rows exactly as `describe()` does: the same flags, sources, `pool=` and units.

```python
--8<-- "statistics-fit.py"
```

``` { .text .no-copy }
--8<-- "statistics-fit.txt"
```

**AICc ranks the fits.** Each fit's AICc weighs how well it fits against its two parameters; lower is better, and only the differences mean anything. As a rough guide (Burnham & Anderson 2004), a ΔAICc up to 2 is substantial support, 4 to 7 considerably less, and above 10 essentially none. Two fits within 2 of each other are both reasonable: here lognormal and gamma. The Akaike weights give each fit's share of the support. AICc compares fits within a group, never across groups.

**The Anderson-Darling p-value checks each fit.** It is computed by parametric bootstrap: 999 samples drawn from the fit, each refitted, so the check accounts for the parameters having been estimated from the same data. A small p-value (below 0.05, say) is evidence against the distribution. A large one isn't evidence for it, least of all with few values. SPT N60 is a whole number of blows times a factor, so many values tie, and a check made for continuous values reads the ties as misfit: expect small p-values for every candidate, and compare N60 fits by AICc and the Q-Q plot.

**Refusals are fitted as censored.** A refusal (`spt_refusal`) or a `>` value is known only to be at least the value the column holds, and a `<` value at most. `fit()` uses each as the probability beyond its limit, not as a measurement at it, so the refusals in the Terrace pull its fits up without pretending N60 is 66.7. A group with censored values has no Anderson-Darling check: judge its fit on the [Q-Q plot](../plots/distribution-fit.md).

**Bounds.** Most properties can't be negative, so for a column the registry marks as a ratio scale the lower bound is 0, and each fit reports `probability_below_lower_bound`: 0 for the lognormal, gamma and Weibull, and the share a normal fit puts below 0 (0.27 % here). For a percentage, pass `bounds=(0, 100)`: a beta distribution between the bounds joins the candidates. A value outside the bounds is an error. Lognormal, gamma and Weibull can't fit a value of 0 or less; a group with one fits the normal alone, and the notes say why.

**Few values.** A group needs at least 4 values that aren't censored, and below 10 the ranking and the check have little power; both warn.

`fit()` doesn't choose a distribution for you. It shows how the candidates compare, so the choice you make, and record, rests on the data.

## Comparing groups

`ht.stats.compare()` tests whether a property differs between two groups: two geology units (one parameter set or two?), two areas of a site, or two sources before you pool them (`by="correlation_name"`, `by="source"`). `ht.stats.compare_groups()` does the same for three or more, overall and for every pair. Both read the rows as `describe()` does: the same flags, counts, sources, `pool=` and units.

```python
--8<-- "statistics-compare.py"
```

``` { .text .no-copy }
--8<-- "statistics-compare.txt"
```

**Two tests, always.** Each function reports a test on the means and a test on the ranks, side by side:

| | Means | Ranks |
|---|---|---|
| `compare()` | Welch's t-test, with the difference and its interval | Brunner-Munzel, with the probability that a value in the first group exceeds one in the second |
| `compare_groups()`, overall | Welch's ANOVA | Kruskal-Wallis |
| `compare_groups()`, each pair | Games-Howell, with the difference and its interval | Dunn's test, Holm-adjusted |

The usual recipe, test for normality and then choose a t-test or a rank test, changes the error rates of the test it chooses, and at 5 to 20 values a normality test has little power anyway. So hangtu never pre-tests: it reports both, and the note says whether they agree. None of these tests assumes equal variances, and the rank tests don't assume the groups have the same shape. The pair p-values of `compare_groups()` are family-wise, adjusted for the number of pairs, and pairs are reported whatever the overall tests say.

**Reading a disagreement.** When the means differ but the ranks don't, one or two extreme values are usually moving a mean. When the ranks differ but the means don't, a skewed group or an extreme value is usually widening the spread; `log=True` compares geometric means, as their ratio, which such values move less. Either way, look at the values: the [geology unit comparison](../plots/geology-unit-comparison.md) draws them side by side.

**"No difference found" isn't "the same".** A p-value above the significance level says the data don't show a difference, not that there is none; with few values a real difference often goes undetected. The note gives the interval of the difference instead, so you can judge whether a difference that large would matter. Fewer than 5 values in a group warns; fewer than 2 is an error in `compare()`, and leaves the group out of `compare_groups()`'s tests.

**The significance level is a judgment.** α has no default: 0.05 is a convention, not a law, so you set it on purpose, in the call (`significance_level=0.05`) or in the [judgments file](judgments.md#the-significance-level). It decides the note's conclusions and the intervals' level (1 − α); the p-values don't depend on it. The result records it and where it came from.

**Independent values.** Every test here assumes the values are independent. Values from one hole, or from close together, aren't, and the p-values are then too small. hangtu doesn't yet account for this, so treat a small p-value from a few holes with care. Comparing two correlations' estimates for the same tests is a paired comparison, which these tests aren't made for.

**Bounds.** Refusals and `>`/`<` values enter at their value and are counted, as in `describe()`: the means, and so the tests on them, are biased, and the note says so. The ranks treat values at a common cap as tied at the top, which is closer to right.

## See also

- [`ht.stats.describe`](../reference/stats.md#hangtu.stats.describe), [`ht.stats.DescribeResult`](../reference/stats.md#hangtu.stats.DescribeResult)
- [`ht.stats.fit`](../reference/stats.md#hangtu.stats.fit), [`ht.stats.FitResult`](../reference/stats.md#hangtu.stats.FitResult), and the [distribution fit plot](../plots/distribution-fit.md)
- [`ht.stats.compare`](../reference/stats.md#hangtu.stats.compare), [`ht.stats.compare_groups`](../reference/stats.md#hangtu.stats.compare_groups), [`ht.stats.CompareResult`](../reference/stats.md#hangtu.stats.CompareResult), [`ht.stats.CompareGroupsResult`](../reference/stats.md#hangtu.stats.CompareGroupsResult)
- [Judgments](judgments.md): a summary informs a judgment, such as each unit's PI, but never sets one.
