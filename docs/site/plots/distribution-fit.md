# Distribution fit

The distributions fitted to one property's values in one group, drawn so the ranking from `ht.stats.fit()` can be checked by eye before a distribution is used.

```python
--8<-- "distribution-fit.py"
```

![SPT N60 in the Terrace, with four fitted distributions and a Q-Q plot](../img/generated/distribution-fit.png){ width="560" }

## What it shows

**On the left**, a histogram of the values with each fitted density: the rank-1 fit solid, the others dashed. The bars are scaled so their area is the share of values that aren't censored, so they and the densities sit on one scale. Refusals, `>` and `<` values aren't in the bars; they are open triangles at their limit, pointing the way the true value lies, counted in the legend ("≥ 66.7: 11").

**On the right**, a Q-Q plot: each value against the quantile the chosen fit (the rank-1 fit by default) gives it. A good fit puts the points on the 1:1 line. The tails are where fits differ, and where a poor fit shows first. With censored values, each value's position comes from the Kaplan-Meier estimate, so the refusals still shape it.

**Under the Q-Q plot**, the fit table: each fit's rank, ΔAICc and Anderson-Darling p-value, which is "—" when values are censored. The footnote counts the rows left out and says why a distribution wasn't fitted. See [fitting a distribution](../guides/statistics.md#fitting-a-distribution) for what the numbers mean.

Here the lognormal and gamma fits are within 2 of each other in AICc, and the Q-Q points follow the line up to the refusals: either is a reasonable choice. The normal fit is 5 behind and puts 0.27 % of its probability below 0.

## Common options

| Argument | Does |
|---|---|
| `by=`, `group=` | The groups, and the one drawn, e.g. `by="geology_unit", group="Terrace"` |
| `qq=` | The fit on the Q-Q plot, e.g. `qq="normal"` |
| `distributions=` | The fits drawn, e.g. `["normal", "lognormal"]` |
| `bounds=(0, 100)` | A percentage's bounds; adds beta |
| `log=True` | Log axes and log-spaced bins, for values spanning orders of magnitude |
| `bins=` | The number of bins, or a NumPy rule such as `"fd"` |
| `table=False` | No fit table |

To draw a fit you already have, without fitting again:

```python
result = ht.stats.fit(spt, value="spt_n60", by="geology_unit")
fig, axs = result.plot(group="Alluvium")
```

## See also

- [`ht.plot.distribution_fit`](../reference/plot.md#hangtu.plot.distribution_fit), [`ht.stats.fit`](../reference/stats.md#hangtu.stats.fit)
- [Statistics](../guides/statistics.md), and the [SPT histogram](spt-histogram.md) for the classes the same values fall in
