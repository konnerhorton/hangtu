# Representative value profile

A property's values against depth with the representative value [`ht.stats.representative()`](../guides/representative-values.md) computed for each geology unit, beside the mean it came from, so a reviewer sees in one figure what was selected, from which values, and how cautious it is.

```python
--8<-- "representative-profile.py"
```

![Undrained shear strength in three clay units, each with its constant characteristic value, its mean and the band between them](../img/generated/representative-profile.png){ width="450" }

## What it shows

**The values** are drawn as the [property profile](profile.md) draws them, colored by unit: `<` and `>` values as triangles pointing the way the true value lies, refusals and values beyond the axis at the edge, each counted in the footnote.

**Each unit's lines**, in its color: the representative value solid, the mean (the median, for a lognormal view) dashed, and the band between them shaded, so the size of the reduction shows at every depth. A line spans only the depths of its unit's values. The lines are exactly `result.design_lines(mean=True)`: the plot computes nothing of its own.

**The table** at the lower left names the view and every judgment behind it, then gives each unit's n and value, or for a line with depth its value at the top and base of the unit's values. A unit with no value has "—" and the reason.

**The footnote** counts what the lines left out: censored values and values with no depth, which a line with depth can't use; assumed values and ranges, which are drawn but not in the lines; and the units with no line.

Here the Crust has 2 values, so its characteristic value is far below them: with n = 2, Student's t is 6.3. The Lower clay's spread is wide (CoV 0.44), and its band shows it.

## Lines with depth

`trend="depth"` gives each unit's view as a line with depth. Censored values are left out of a line, with a warning, and counted in the footnote:

```python
fig, ax, result = ht.plot.representative_profile(
    strength, value="undrained_shear_strength", by="geology_unit",
    method="characteristic", estimate="mean", side="low",
    distribution="normal", trend="depth",
)
```

The characteristic line curves away from the mean toward the top and base of a unit's values, where the fitted line is least certain. A line that bends a long way, as the Lower clay's would here, says the values don't support a trend well: look at its $R^2$ in `result.to_frame()`.

## Common options

| Argument | Does |
|---|---|
| `by=` | The column grouping and coloring the values, e.g. `"geology_unit"`; one column |
| `trend="depth"` | A line with depth per unit instead of a constant |
| `mean=False`, `band=False`, `table=False` | Leave out the mean line, the band or the table |
| `values=False`, `ax=` | Add a second view to a profile already drawn, without drawing the values again |
| `vs="elevation"` | Against elevation; a constant needs one ground level for all rows |
| `log=True`, `xlim=` | P01's axis options, and its `strata=`, `water_level=`, `note=` and the rest |

Every judgment (`method=`, `side=`, `distribution=`, `estimate=`, …) is `representative()`'s and has no default; see [representative values](../guides/representative-values.md).

A second view on the same figure, the 10th percentile beside the characteristic value:

```python
fig, ax, result = ht.plot.representative_profile(strength, ...)
ht.plot.representative_profile(
    strength, value="undrained_shear_strength", by="geology_unit",
    method="percentile", percentile=10, side="low", distribution="lognormal",
    values=False, ax=ax,
)
```

To draw a result you already have, pass the rows it was computed from:

```python
result = ht.stats.representative(strength, ...)
fig, ax = result.plot(strength)
```

## See also

- [`ht.plot.representative_profile`](../reference/plot.md#hangtu.plot.representative_profile), [`ht.stats.representative`](../reference/stats.md#hangtu.stats.representative)
- [Representative values](../guides/representative-values.md), and the [property profile](profile.md) it builds on
