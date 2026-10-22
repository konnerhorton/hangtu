# Water content profile

Water content against depth or elevation, with each specimen's plastic and liquid limits as a bar.

```python
--8<-- "water-content-profile.py"
```

![Water content and Atterberg limits against elevation, colored by geology unit](../img/generated/water-content-profile.png){ width="440" }

## What it shows

One point per specimen or sample at its water content, w, on a bar from its plastic limit (PL) to its liquid limit (LL) at the same depth, with a tick at each end. It shows whether the soil is near its liquid limit (soft, sensitive) or near its plastic limit (stiff), and whether that changes with depth. A row with only the limits draws the bar alone. It takes `p.atterberg()` or `p.index_properties()` as they come.

The limits are read as given:

- A row with **one limit** is a single tick, counted in the footnote with a warning. PL is never computed from LL − PI: fill in the missing limit, or remove the row.
- A row with **PL above LL** has no bar, and is counted with a warning.
- A **non-plastic** specimen (`non_plastic` True) has no bar. It is an open diamond at its water content or, without one, at the left edge as the text `NP` is. Either way it is counted.

The rest is the [property profile](profile.md) with the `water_content` preset.

## Common options

| Argument | Does |
|---|---|
| `limits=False` | Water content alone, as `ht.plot.profile(df, "water_content", preset="water_content")` |
| `xlim=` | Fixed limits; a bar beyond them is cut at the edge with an arrow, and counted |
| `stats_box=True` | Statistics of the water content |
| `vs=`, `strata=`, `water_level=`, ... | As the [property profile](profile.md) |

## See also

- [`ht.plot.water_content_profile`](../reference/plot.md#hangtu.plot.water_content_profile)
- [Datasets](../guides/datasets.md): `p.atterberg()` and `p.index_properties()`
