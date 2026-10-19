# SPT histogram

The share of SPT tests in each relative density or consistency class, by geology unit.

```python
--8<-- "spt-histogram.py"
```

![SPT N60 classes in the coarse soil](../img/generated/spt-histogram.png){ width="440" }

## What it shows

Each geology unit has one bar per class: the percent of its tests in that class. Refusals get their own hatched class, last. The classes are those of `ht.analysis.spt_class()` (see [SPT analysis](../guides/spt.md#classes)).

Which table applies is your call: pick `table=` and pass only the rows it fits. For sand and clay on one page, draw two histograms on a [sheet](index.md#sheets).

## Common options

| Argument | Does |
|---|---|
| `table="cohesive"` | Consistency (very soft to hard) instead of relative density |
| `n="spt_n60"` | Classify N60 instead of field N; tests without N60 are left out and counted |
| `refusal="exclude"` | Leave refusals out (still counted) |
| `order=` | Geology units in stratigraphic order |
| `bar_labels=True` | The number of tests above each bar |

## See also

- [`ht.plot.spt_histogram`](../reference/plot.md#hangtu.plot.spt_histogram)
