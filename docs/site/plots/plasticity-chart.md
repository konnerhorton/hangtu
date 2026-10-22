# Plasticity chart

Liquid limit against plasticity index on the Casagrande chart, with the A-line, the U-line and the zones of USCS or BS 5930.

```python
--8<-- "plasticity-chart.py"
```

![Specimens on the USCS plasticity chart, colored by geology unit](../img/generated/plasticity-chart.png){ width="480" }

## What it shows

One point per specimen, colored by geology unit, in the zone of its class. The classes come from `ht.analysis.plasticity()`, so a point and its `plasticity_class_uscs` (or `_bs5930`) always agree. PI is LL − PL where it is blank. The axes have equal aspect, so the A-line's slope reads true.

Non-plastic specimens and rows with a blank LL or PI aren't drawn; the footnote counts them. The zone labels are the inorganic classes; OL and OH are never shown.

## Common options

| Argument | Does |
|---|---|
| `system="bs5930"` | BS 5930's lines and zones instead of USCS |
| `labels=True` | Each specimen's `specimen_id` beside its point |
| `zone_labels=False` | Hide the zone names |
| `regions=` | Your own polygons in LL–PI space, such as a project's soil groups (`ht.template("plasticity_regions")`) |
| `order=` | Units in stratigraphic order, for the legend |
| `xlim=`, `ylim=` | Fixed limits; the aspect stays equal |

## See also

- [`ht.plot.plasticity_chart`](../reference/plot.md#hangtu.plot.plasticity_chart), [`ht.analysis.plasticity`](../reference/analysis.md#hangtu.analysis.plasticity)
- [Water content profile](water-content-profile.md): the same specimens against depth
