# Consolidation time curves

An oedometer specimen's settlement during each load increment, against the square root of time and against log time, with the coefficient of consolidation c_v read from each curve by the root time and log time constructions of BS 1377-5:1990, beside the lab's value, so you can see where each t90 and t50 came from.

```python
--8<-- "consolidation-time-curves.py"
```

![The example project's B-4 oedometer specimen, increments 3 to 5: root time constructions on the left, log time constructions on the right, each with its c_v beside the lab's](../img/generated/consolidation-time-curves.png){ width="560" }

```text
--8<-- "consolidation-time-curves.txt"
```

## Why recompute c_v

A lab reports c_v, not how it read it. Both constructions are drawn by hand on the lab's plot, and where a line is drawn is a judgment the report doesn't show. hangtu reads the curve by a fixed rule, so the same readings always give the same c_v, and draws the construction, so you can judge whether the rule found a believable t90 and t50. Where the recomputed value and the lab's differ, the figure shows which readings decided it.

The readings come from the lab's file: `p.oedometer_readings()` reads them from the file's own groups through the readings map (see [Datasets](../guides/datasets.md)), or a CSV in `ht.template("oedometer_readings")`'s shape gives them, one row per reading with its increment's values.

## Root time (left)

Displacement against √t. The early line is fitted by least squares to the readings in the first half of the increment's movement, after the load was applied (3.6.3.3.1), and extended to t = 0, where it gives the corrected zero d0. The dashed 1.15 line starts at d0, with abscissae 1.15 times the early line's (3.6.3.3.2). Where the curve first falls to the 1.15 line is d90 and t90, and

c_v = 0.111 H̄² / t90 (m²/year, H̄ in mm, t90 in minutes; 3.6.3.3.3)

with H̄ the specimen's average height over the increment, from its void ratios. Filled readings are the ones the early line was fitted to. The x axis stops past t90: a day's readings drawn to the end would squeeze the construction against t = 0, so the later readings sit at the right edge and the footnote counts them.

## Log time (right)

Displacement against log t. The secondary line is fitted to the readings in the last log cycle of time, and the tangent at the inflexion to the steepest three consecutive readings before it; they cross at d100 (3.6.3.2.2). d0 is the mean of 2 y(t) − y(4t) over the three latest pairs of times in the ratio 1:4 before the inflexion (3.6.3.2.1), which assumes the early curve is a parabola. d50 is midway, t50 where the curve reaches it, and

c_v = 0.026 H̄² / t50 (m²/year; 3.6.3.2.4).

Filled readings are on the tangent, on the secondary line, or in a 1:4 pair. The t = 0 reading has no place on a log axis.

## When there's no value

A construction that can't be made gives a reason instead of a value, written in the panel, with the readings and the lines it got to still drawn. Nothing is extrapolated past the readings. The common ones:

- "fewer than 3 pairs of times in the ratio 1:4 before the inflexion" and "fewer than 3 readings in the first half of the increment's movement": the increment consolidated too fast for the reading times. The example's B-5 specimen has one (its third increment).
- "t90 after the last reading": the readings stop before the curve reaches the 1.15 line.
- "no clear secondary portion": the curve is still steep in its last log cycle, so there is no second line to cross the tangent.

The full list is in [`ht.analysis.consolidation_coefficient_from_readings`](../reference/analysis.md#hangtu.analysis.consolidation_coefficient_from_readings).

## The two methods and the lab's value

Each panel writes hangtu's c_v to three figures beside the lab's, as the lab wrote it ("lab —" where the lab gave none). The two constructions often differ. The root time construction sometimes finds no straight early portion where log time works, and the reverse where secondary compression is large (BS 1377-5:1990, 3.6.3.1, note). Where c_v changes with stress within an increment, log time reads an equivalent c_v at 50 % consolidation and root time at 90 %, so they differ by design: log time gives the higher value when c_v falls as the stress rises, and root time when it rises (Abuel-Naga & Pender 2012, pp. 44–47). hangtu gives both and prefers neither.

## Overrides

When a rule reads a curve badly, give the time range for that part of the construction yourself, with your reason. B-5's fourth increment moves only 0.003 in, and its first reading pulls the early line steeper than the curve, giving a root time c_v twice the log time value. Fitting the early line from 0.25 min brings it beside log time:

```python
--8<-- "consolidation-time-curves-override.py"
```

![B-5's fourth increment with the root time early line fitted from 0.25 to 4 min, dash-dotted and marked as an override](../img/generated/consolidation-time-curves-override.png){ width="560" }

An override is a frame in `ht.template("consolidation_overrides")`'s shape, one row per overridden part: `early` for either method, `inflexion` or `secondary` for log time. The overridden line is dash-dotted and the result says "(override)"; the overrides used are recorded on the analysis's result. They are passed on each call, so keep them in a CSV beside your project and read it with `ht.read_csv(..., units={"elapsed_time_start": "min", "elapsed_time_end": "min"})`.

## Common options

| Argument | Does |
|---|---|
| `specimen=` | The specimen drawn, by its `specimen_id` or its name ("B-4-U1-C1"); needed when the rows hold more than one |
| `increments=["3", "4"]` | The increments drawn, by `test_stage`, up to 6 |
| `methods=("log_time",)` | One construction only |
| `overrides=` | Time ranges that replace a rule's, as above |
| `reported=False` | Leave out the lab's value |
| `display_units=` | `"US"` (in, ft²/yr) or `"SI"` (mm, m²/yr); times are in minutes in both |

For the numbers without a figure, `ht.analysis.consolidation_coefficient_from_readings(readings)` gives one row per increment with each construction's points, c_v and why any is blank, and `ht.analysis.oedometer_increments(oed, consolidation_coefficients=rows)` adds the hydraulic conductivity that follows from it.

## See also

- [`ht.plot.consolidation_time_curves`](../reference/plot.md#hangtu.plot.consolidation_time_curves), [`ht.analysis.consolidation_coefficient_from_readings`](../reference/analysis.md#hangtu.analysis.consolidation_coefficient_from_readings)
- [Consolidation coefficients](consolidation-coefficients.md): the lab's c_v of each increment against stress
- [Datasets](../guides/datasets.md): `p.oedometer_readings()` and the readings map
