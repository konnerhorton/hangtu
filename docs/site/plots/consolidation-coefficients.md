# Consolidation coefficients

An oedometer test's coefficient of volume compressibility m_v and coefficient of consolidation c_v, increment by increment, against log effective vertical stress, with the lab's m_v beside the one its void ratios give and the increments that span σ′v0.

```python
--8<-- "consolidation-coefficients.py"
```

![The example project's B-5 oedometer specimen: m_v of each increment above, the lab's root time and log time c_v below, and σ′v0 with the increments spanning it drawn thicker](../img/generated/consolidation-coefficients.png){ width="560" }

```text
--8<-- "consolidation-coefficients.txt"
```

## What it shows

Each increment is a horizontal segment from the stress it starts at to the stress it ends at. m_v is a secant over the increment, the change in void ratio over the change in stress, so it belongs to that range, not to a point in it: joining values drawn at the end stress would read as a smooth curve the test didn't measure. To use m_v, c_v or k at a design stress, take the increment whose range holds it.

The upper panel is m_v as `ht.analysis.oedometer_increments()` recomputes it from the void ratios, (e1 − e2) / ((1 + e1)(σ′2 − σ′1)), with e1 at the start of the increment (BS 1377-5:1990, 3.6.2.2.4). Loading increments are solid. Unloading and reloading increments are thin, dashed and lighter: BS 1377-5 defines m_v on loading increments only, and the unload and reload values are an extension, the basis of the unload–reload modulus Eur,oed.

## The lab's m_v

Each × is the lab's own m_v, drawn at the middle of its increment on the log axis, √(σ′1 σ′2). On a good file the × sits on its segment. A × that falls further below its segment at each later increment is the sign of a lab that divided by 1 + e0 of the specimen instead of 1 + e1 of the increment, which is larger once the specimen has compressed; QC rule E003 flags the increments where the two differ by more than the rounding allows.

## c_v and k

The lower panel is the lab's c_v as reported, by root time (solid) and by log time (dotted). The first increment has no start stress in the file, so its c_v is a × at its end stress. The two methods seldom agree; neither is preferred here, and the two are kept apart.

`oedometer_increments()` also gives the hydraulic conductivity k = c_v m_v γw of each increment, from each of the lab's c_v. It is a vertical k of a small specimen, usually below the field value since the specimen misses the fabric that drains the ground. Use it as a check on other measurements, not as a design value on its own.

## σ′v0

With `effective_vertical_stress` on the rows, from `ht.analysis.vertical_stress()`, the dotted line marks σ′v0 and the increments spanning it are drawn thicker: the first loading increment and the first unloading or reloading increment whose range holds it. Their values are the ones at σ′v0; nothing is interpolated between increments. In an overconsolidated specimen the loading increment at σ′v0 is on recompression, stiffer than the virgin branch.

## Common options

| Argument | Does |
|---|---|
| `branches=("loading",)` | Draw the loading increments only |
| `reported=False` | Leave out the lab's m_v |
| `display_units=` | `"US"` (psf, ft²/kip, ft²/yr) or `"SI"` (kPa, m²/MN, m²/yr) |
| `note=` | Add a line to the footnote |

For the numbers without a figure, `ht.analysis.oedometer_increments(oed)` returns the rows with m_v, Eoed, Eur,oed and k added, and why any is blank.

## See also

- [`ht.plot.consolidation_coefficients`](../reference/plot.md#hangtu.plot.consolidation_coefficients), [`ht.analysis.oedometer_increments`](../reference/analysis.md#hangtu.analysis.oedometer_increments)
- [Consolidation curve](consolidation-curve.md): the same increments as e against log σ′v
- [Datasets](../guides/datasets.md): `p.oedometer()`
