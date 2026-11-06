# Property by geology unit

A property's values in each geology unit, with a summary bar, compared with a report's ranges.

```python
--8<-- "geology-unit-comparison.py"
```

![Plasticity index by geology unit](../img/generated/geology-unit-comparison.png){ width="560" }

## What it shows

Each geology unit is a row: its values as points, a summary bar (the 10th to 90th percentile with the median, by default), and the count. A unit with too few values for a summary shows its points and says so.

Pass `split_by=` a column to give each unit one sub-row per value of it, such as `test_type`, each with its own summary and count, labeled "Terrace · UU". With `color_by=` the same column, the legend has one entry per value. `ht.stats.compare_sources()` draws its comparison this way, one sub-row per source ([undrained shear strength](../parameters/05-undrained-shear-strength.md#comparing-the-sources)).

Pass `baseline=` a table of a report's ranges per unit, such as a geotechnical baseline report's, to draw them above each unit's data. `ht.template("baseline")` gives its columns. For several properties side by side, use `ht.plot.geology_unit_comparisons()`.

## Common options

| Argument | Does |
|---|---|
| `baseline=`, `baseline_label=` | A report's range per unit, and its legend text |
| `summary="box"` | A box plot instead of the percentile bar (`None` for none) |
| `percentiles=(25, 50, 75)` | The bar's ends and center, the same numbers as `ht.stats.describe()` |
| `order=` | Geology units in stratigraphic order |
| `split_by=` | One sub-row per value of a column in each unit, such as `test_type` |
| `preset=`, `log=`, `xlim=` | The property's scale and limits |

## See also

- [`ht.plot.geology_unit_comparison`](../reference/plot.md#hangtu.plot.geology_unit_comparison), [`ht.plot.geology_unit_comparisons`](../reference/plot.md#hangtu.plot.geology_unit_comparisons)
