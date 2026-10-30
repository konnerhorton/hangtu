# Statistics

Summarize test values by geology unit, with the count, spread and percentiles a design report needs, and with every flagged value counted rather than dropped; then fit distributions to them.

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

## See also

- [`ht.stats.describe`](../reference/stats.md#hangtu.stats.describe), [`ht.stats.DescribeResult`](../reference/stats.md#hangtu.stats.DescribeResult)
- [`ht.stats.fit`](../reference/stats.md#hangtu.stats.fit), [`ht.stats.FitResult`](../reference/stats.md#hangtu.stats.FitResult), and the [distribution fit plot](../plots/distribution-fit.md)
- [Judgments](judgments.md): a summary informs a judgment, such as each unit's PI, but never sets one.
