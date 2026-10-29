# Clogging diagram

Fine-grained specimens on Thewes & Burger's (2004) chart of clay clogging potential for TBM drives: plasticity index across, consistency index at in situ water content up.

```python
--8<-- "clogging-diagram.py"
```

![Specimens on the clogging diagram, colored by geology unit](../img/generated/clogging-diagram.png){ width="480" }

## What it shows

One point per specimen, colored by geology unit, in the zone of its `clogging_potential`: low, medium, medium-high or high. The zones come from `ht.analysis.clogging_potential()`, so a point and its zone always agree, and the footnote counts the specimens in each zone for a GBR or TBM specification. A point on a boundary between two zones takes the higher one.

Specimens beyond the axes, such as the soft clays wetter than their liquid limit (Ic below 0), are drawn at the edge and counted as outside the diagram, not given the nearest zone. Non-plastic specimens, a PI of 0 and missing values aren't drawn; the footnote counts each.

The chart screens index properties only. Mineralogy, the machine and conditioning are outside it.

## Common options

| Argument | Does |
|---|---|
| `zones=` | Your own zones instead, e.g. from another source (`ht.template("clogging_zones")`) |
| `labels=True` | Each specimen's `specimen_id` beside its point |
| `zone_counts=False` | Hide the footnote line counting the specimens in each zone |
| `zone_labels=False` | Hide the zone names |
| `order=` | Units in stratigraphic order, for the legend |
| `xlim=`, `ylim=` | Fixed limits |

For the zones as a table, without a figure:

```python
table = ht.analysis.clogging_potential(atterberg)
table.groupby("geology_unit")["clogging_potential"].value_counts()
```

## See also

- [`ht.plot.clogging_diagram`](../reference/plot.md#hangtu.plot.clogging_diagram), [`ht.analysis.clogging_potential`](../reference/analysis.md#hangtu.analysis.clogging_potential)
- [Plasticity chart](plasticity-chart.md), from the same Atterberg results
