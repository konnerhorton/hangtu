# Property profile

Any property against depth or elevation, colored by geology unit.

```python
--8<-- "profile.py"
```

![Hydraulic conductivity against elevation on a log axis](../img/generated/profile.png){ width="440" }

## What it shows

One point per test. A test over an interval, such as a field permeability test, is a bar over the zone it tested. The vertical axis is elevation when the data has it (or depth and ground level), else depth.

A **preset** sets the label, units, scale and limits for a common property: `"hydraulic_conductivity"`, `"undrained_shear_strength"`, `"water_content"` or `"bulk_unit_weight"`. Any other column plots with `label=` and `log=` as needed.

## Value ranges

A value reported as a range at one depth, such as a correlation's band, is drawn from two more columns, `<value>_lower` and `<value>_upper` (for s_u, `undrained_shear_strength_lower` and `undrained_shear_strength_upper`): a bar between the bounds at the test's depth, with the point where the value itself isn't blank. A bound given alone is a caret at it, ▷ for a lower bound and ◁ for an upper. The footnote counts the rows shown as a range, and the stats box leaves them out and says how many, since a range isn't one value.

## Common options

| Argument | Does |
|---|---|
| `vs="depth"` | Plot against depth instead of elevation |
| `preset=`, `log=`, `label=` | The property's scale and axis text |
| `xlim=`, `ylim=` | Fixed limits; values beyond are drawn at the edge and counted |
| `xaxis_position="top"` | The value axis at the top, as on a boring log |
| `strata=`, `water_level=` | Geology boundaries and water levels across the plot |
| `ranges=`, `design_lines=`, `reference_lines=` | A report's ranges, design lines or fixed values to compare with |
| `stats_box=True` | Count, mean, standard deviation, median, minimum and maximum |
| `legend=` | `"auto"`: inside, in a corner clear of data, else below; or `"bottom"`, `"right"`, `False` |

## See also

- [`ht.plot.profile`](../reference/plot.md#hangtu.plot.profile)
