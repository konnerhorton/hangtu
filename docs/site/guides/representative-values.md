# Representative values

Turn a parameter's values into the cautious estimate a design report states, per geology unit, constant or as a line with depth: Eurocode 7's characteristic value, a low percentile, or the mean less a multiple of the standard deviation. Every choice behind the number is an argument you give, and the result records it with the statistics it came from.

```python
--8<-- "representative-values.py"
```

``` { .text .no-copy }
--8<-- "representative-values.txt"
```

![The SPT N60 profile with each unit's characteristic value: a line with depth in the Alluvium, constant in the Fill and the Terrace](../img/generated/representative-values.png)

## One view per call, every judgment on the call

`ht.stats.representative()` reads the rows exactly as [`fit()`](statistics.md#fitting-a-distribution) does: the same flags, counts, sources, `pool=` and units. Then it computes one view, the one you name:

| `method=` | What it gives | Inputs it needs |
|---|---|---|
| `"characteristic"` | Eurocode 7's characteristic value | `estimate=`, and for Type C `scale_of_fluctuation=` and `failure_length=` (or `sensitivity_index=`); `coefficient_of_variation=` optional |
| `"percentile"` | A percentile of the fitted normal or lognormal distribution | `percentile=` |
| `"standard_deviations"` | The mean less (or plus) k standard deviations | `standard_deviations=` (k) |

`side=` (`"low"` or `"high"`) and `distribution=` (`"normal"` or `"lognormal"`) are needed by all three. None of these has a default: whether a strength is cautious on the low side, whether the failure averages over a long surface, which distribution the values follow, are your judgments, and a default would make them for you without saying so ([judgments](judgments.md)). Leaving one out is an error naming it, and so is an input that belongs to another method, so a call can't carry a judgment that silently did nothing.

Two views are two calls on the same rows. Both read the same mean, standard deviation and fit, so they can't disagree on the data, only in what they make of it.

`side="low"` is for a value where less is unfavorable (a strength, a stiffness); `side="high"` for one where more is (a compressibility, a unit weight acting as a load).

## Eurocode 7's characteristic value

The characteristic value of EN 1997-1:2024 (Formula 4.5), as the JRC report restates it (Orr et al. 2025):

$$X_k = \bar{x} \mp k_n s, \qquad k_n = c\,\sqrt{\Gamma^2 + 1/n}$$

with $\bar{x}$ and $s$ the mean and standard deviation of the values, and $n$ their count. $\Gamma^2$ is the type of estimate, $c$ the case.

**The type of estimate** (`estimate=`) depends on how much ground the failure averages over:

| `estimate=` | EC7 type | $\Gamma^2$ | When |
|---|---|---|---|
| `"mean"` | A | 0 | The failure averages over a large volume: a long slip surface in one unit, a pile shaft |
| `"fractile"` | B | 1 | A local failure, over a length shorter than the ground's scale of fluctuation |
| `"intermediate"` | C | $\theta / L$, at most 1 | In between, which is most real cases |

The choice matters more than anything else in the calculation. In the example, Type A gives the Alluvium N60 4.4; Type B on the same values gives 1.5.

**The case** (`coefficient_of_variation=`) says where the spread comes from:

- **Case 2, computed** (leave it out): $s$ from the data, and $c = t_{0.95,\,n-1}$, Student's t, which grows as $n$ falls.
- **Case 3, assumed** (give $V_X$, e.g. `0.30`): $X_k = \bar{x}(1 \mp k_n V_X)$, and $c = 1.645$, the normal 95 % quantile. Use it when there are too few values to estimate the spread, with a $V_X$ from experience or published ranges; record where it came from.
- **Case 1, known** from prior experience of the same ground: the same formula as Case 3, given the same way.

**Type C needs the scale of fluctuation** $\theta$, roughly the distance over which the ground's deviations from its trend stay correlated, and the length of the failure surface $L$, in the same direction ($\theta_v$ for a pile shaft, $\theta_h$ for a long, mostly horizontal slip surface). Give both in one length unit, any one: only their ratio enters. $\Gamma^2 = \theta / L$, capped at 1 as the JRC report adopts. If you have $\Gamma^2$ itself, give `sensitivity_index=` instead. hangtu doesn't estimate $\theta$: it comes from a CPT profile of the unit, detrended, or from published values for a comparable deposit. SPT spacing can't resolve it, because the tests are about as far apart as $\theta_v$ itself, so Type C on SPT values rests on a $\theta$ from elsewhere.

**How many values.** EN 1997-1 sets no minimum; the JRC report (§5.1) gives criteria to judge it by. A $V_X$ computed from a few values is unreliable, so with few values an assumed $V_X$ (Case 3) is often the better route. A group with fewer than 2 values gets no value, with the reason in the frame.

**A characteristic value at or below 0** from a normal distribution warns: it is a sign the values are lognormal (JRC §5.1.3). So does `hydraulic_conductivity` with `distribution="normal"`, for which Formula 4.5 should not be used.

## A percentile, and the mean less k standard deviations

The views US practice uses:

- **`method="percentile"`**: the `percentile`-th percentile of the normal or lognormal distribution that `fit()` fits to the group by maximum likelihood, the same distribution the [distribution fit plot](../plots/distribution-fit.md) draws. It has no allowance for a small sample, unlike EC7's fractile, so with few values it is less cautious than Type B. `side` must agree with it: a percentile below 50 for `"low"`, above 50 for `"high"`; a "low" 95th percentile is an error, since it is more likely a slip than a choice. The percentile of the values themselves, with no distribution, is [`describe()`'s](statistics.md#what-describe-reports).
- **`method="standard_deviations"`**: $\bar{x} \mp k s$, with $k$ = `standard_deviations`. Two values of $k$ have names of their own in the JRC report: Schneider's $k = 0.5$, a simple estimate of the mean (Type A), and the simplified fractile's $k = 1.75$, a simple Type B. They are values of $k$ here, not methods.

## Lognormal values

With `distribution="lognormal"`, every view is computed on $\ln x$ and transformed back: $X_k = \exp(m \mp k_n s_{\ln})$, with $m$ and $s_{\ln}$ the mean and standard deviation of $\ln x$ (the JRC report's Annex IV). With $V_X$ assumed, $s_{\ln} = \sqrt{\ln(1 + V_X^2)}$. The result gives the geometric mean $e^m$ and geometric standard deviation $e^{s_{\ln}}$. Values at or below 0 can't be logged: they are left out, counted (`count_not_positive`) and warned about.

The report has a second lognormal route (Annex V), which takes the parameters from the mean and standard deviation of $x$ rather than of $\ln x$; the two give different values from the same data. hangtu offers only the first, because it is what "transform, apply the normal formulae, transform back" means, and it is the lognormal fit `fit()` gives. If a report you are checking used the other, expect a difference.

Use it for values spanning orders of magnitude (hydraulic conductivity), or skewed values whose normal characteristic value comes out near or below 0.

## Lines with depth

Undrained strength and N60 often rise with depth through a unit. A constant value is then too low at depth and too high near the top. `trend="depth"` (or `"elevation"`) fits a least-squares line per group, $\hat{x}(z) = a_0 + a_1 z$, with the residual standard deviation $s_e$, and gives the view along it (Bond & Harris 2008, as the JRC report gives it):

| View | Line |
|---|---|
| Characteristic, `estimate="mean"` | $\hat{x}(z) \mp t_{0.95,\,n-2}\, s_e \sqrt{1/n + (z - \bar{z})^2 / \sum (z_i - \bar{z})^2}$, the confidence band |
| Characteristic, `estimate="fractile"` | The same with $\sqrt{1 + 1/n + \dots}$, the prediction band |
| Percentile | $\hat{x}(z) + z_p\, s_e$ |
| Standard deviations | $\hat{x}(z) \mp k\, s_e$ |

The bands curve away from the middle of the data, so a line is given only over its group's depths, never extended above or below them. If the line will be used over a short stretch, a straight line through that stretch is your call to make, on the figure.

- **What it needs.** At least 3 values at 2 or more depths in a group; fewer gives that group no line, with the reason. The depth column needs its unit, like the value.
- **Not with an assumed $V_X$ or Type C.** The report gives the trend only with the spread from the data, and leaves Type C on a trend out of its scope, so both are errors.
- **Its assumptions.** The scatter about the line is the same at every depth, random and normal. hangtu doesn't test them: the result keeps $R^2$ and the residuals (`result.groups[i]["line"]`), so you can look. A scatter that widens with depth breaks the first; a lognormal line, through $\ln x$, often fixes it.
- **Lognormal lines** are through $\ln x$ and transformed back, so the mean line is the median of $x$, not its mean.

## Censored values

A refusal, a `>` value and a `<` value aren't measurements at their value: each is known only to lie beyond it.

- **Constant views** take them as `fit()` does, through the censored maximum-likelihood fit, so the mean and standard deviation aren't biased low (or high) at their limits. That standard deviation is with $n$, not $n - 1$, and EC7's $k_n$ factors assume complete data; a note says both. The refusals' upper limit, `spt_refusal_upper_limit=`, works as in `fit()`, from the call, `judgments=` or the project's [judgments file](judgments.md). In the example, the Terrace's 11 refusals enter this way.
- **Lines with depth** leave them out and count them (`count_censored`), with a warning. A note says which way that moves the line: leaving out refusals and `>` values makes a low-side line more cautious and a high-side line less, and `<` values the reverse.

Statistics in hangtu are designed for lab data. The example uses SPT N60 because it has a depth trend and refusals to show; for SPT values, the simple views are usually all the data can support.

## Design lines

`result.design_lines()` gives each group's value as the frame P01's `design_lines=` draws ([profile](../plots/profile.md)), in the result's units: two points for a constant, at the group's shallowest and deepest value; 50 points along a line with depth. Each line is labeled with its group and view ("Alluvium: characteristic, mean, low"). `mean=True` adds the mean line (the median for lognormal) to compare it with. A constant needs a `depth` or `elevation` column in the data to place it.

Frames from several calls join with `pd.concat`, as in the example, to show a line in one unit and constants in the others.

## What the result records

`print(result)` shows the values with the view, its inputs and the notes. `result.to_frame()` gives one row per group: the value (or, for a line, its coefficients and its value at the top and base), $n$, the counts of rows left out by reason, the mean, standard deviation, $V_X$, the t or normal factor, $k_n$ and $\Gamma^2$. `result.to_dict()` gives all of it, every input included, ready for a report, so a reviewer can redo the number.

hangtu stops here. Partial factors, the conversion factor $\eta$ and design values are the design's, not the parameter's.

## See also

- [`ht.stats.representative`](../reference/stats.md#hangtu.stats.representative), [`ht.stats.RepresentativeResult`](../reference/stats.md#hangtu.stats.RepresentativeResult)
- [Statistics](statistics.md): summaries, fitted distributions and comparisons of the same rows
- [Judgments](judgments.md): the refusals' upper limit

## References

- Orr, T., Sorgatz, J., Estaire, J. et al. (2025). *Determination of representative values from derived values for verification with limit states with EN 1997*. JRC, EUR 40260, doi:10.2760/0980105 (CC BY 4.0). It quotes EN 1997-1:2024.
- Bond, A. & Harris, A. (2008). *Decoding Eurocode 7*. Taylor & Francis.
