# Property by geology unit

A property's values in each geology unit, with a summary bar, compared with a report's ranges.

```python
--8<-- "geology-unit-comparison.py"
```

![Plasticity index by geology unit](../img/generated/geology-unit-comparison.png){ width="560" }

## What it shows

Each geology unit is a row: its values as points, a summary bar (the 10th to 90th percentile with the median, by default), and the count. A unit with too few values for a summary shows its points and says so.

Pass `baseline=` a table of a report's ranges per unit, such as a geotechnical baseline report's, to draw them above each unit's data. `ht.template("baseline")` gives its columns. For several properties side by side, use `ht.plot.geology_unit_comparisons()`.

## Common options

| Argument | Does |
|---|---|
| `baseline=`, `baseline_label=` | A report's range per unit, and its legend text |
| `summary="box"` | A box plot instead of the percentile bar (`None` for none) |
| `percentiles=(25, 50, 75)` | The bar's ends and center, the same numbers as `ht.stats.describe()` |
| `order=` | Geology units in stratigraphic order |
| `preset=`, `log=`, `xlim=` | The property's scale and limits |

## See also

- [`ht.plot.geology_unit_comparison`](../reference/plot.md#hangtu.plot.geology_unit_comparison), [`ht.plot.geology_unit_comparisons`](../reference/plot.md#hangtu.plot.geology_unit_comparisons)
