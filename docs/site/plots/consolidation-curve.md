# Consolidation curve

An oedometer test's increments as void ratio against log effective vertical stress, with the preconsolidation stress σ′p, the compression, recompression and swelling indexes Cc, Cr and Cs, and the sample quality where σ′v0 is known.

```python
--8<-- "consolidation-curve.py"
```

![The example project's B-5 oedometer specimen: the loading curve, an unload–reload loop, the Cc, Cr and Cs lines, σ′p by Oikawa and by Pacheco Silva, and σ′v0](../img/generated/consolidation-curve.png){ width="560" }

```text
--8<-- "consolidation-curve.txt"
```

## What it shows

Every increment, by its branch: loading points filled and joined in order, unloading points open circles, reloading points open diamonds, and constant-stress increments (a swell or creep stage) small crosses. The first loading point past an unload–reload loop is a filled diamond: it's on the virgin line's fit, but the curve can take an increment to rejoin the line after a loop, so check it sits on the line.

The lines are those `ht.analysis.oedometer_fit()` fits, drawn, never refitted:

- **Cc** over the loading points above σ′p and **Cr** over those below, each solid over the points it was fitted to and thin and dashed beyond. A reload is never used for Cc.
- **Cs** over the first unload, from the stress it starts at. Later unloads are on the fit's result, but not drawn.

## The two σ′p

The filled triangle is σ′p by Oikawa (1987): two straight lines fitted to the loading points in log(1 + e) against log σ′v, the split between them searched by least squares, and σ′p where they cross. It needs no smoothing and no judgment, so the same increments always give the same σ′p. The open triangle is the check, Pacheco Silva's (1970) construction on the Cc line and e0. Both sit on the loading curve, not where the Cc and Cr lines cross: those are fitted in e, Oikawa's in log(1 + e), and their crossings differ.

When the curve has no clear break (the upper line not at least twice as steep as the lower), when the lines cross outside the stresses tested, or when the test stops below 2 σ′p, the box says so and no σ′p, Cc or Cr is drawn. `space="log_specific_volume"` draws Oikawa's own lines, to see where σ′p came from:

```python
fig, ax, fit = ht.plot.consolidation_curve(oed, space="log_specific_volume")
```

`construction=True` adds Pacheco Silva's steps in thin gray lines, for a report.

## OCR and sample quality

With `effective_vertical_stress` on the rows, from `ht.analysis.vertical_stress()`, the dotted line marks σ′v0 and the box gives OCR = σ′p / σ′v0 and Δe/e0, the change in void ratio from e0 to σ′v0 on the loading curve, over e0. Lunne et al. (1997) grade Δe/e0 into four classes, in a row chosen by OCR (1–2 or 2–4); the box names the row it used.

The OCR is this test's own, and disturbance lowers σ′p and so the OCR. A disturbed sample can land in the more lenient OCR 1–2 row and grade better than it is. Read the class with the curve: a rounded break and a high Cr are the signs of disturbance the number can miss.

## Common options

| Argument | Does |
|---|---|
| `space="log_specific_volume"` | Draw log(1 + e) with Oikawa's two lines instead of Cc and Cr |
| `construction=True` | Add Pacheco Silva's construction |
| `result_box=False` | Leave the values out of the figure |
| `fit=False` | The points only |
| `display_units=` | `"US"` (psf) or `"SI"` (kPa); the fit is made in them |

For the numbers without a figure:

```python
fit = ht.analysis.oedometer_fit(oed)
fit.to_frame()
```

## See also

- [`ht.plot.consolidation_curve`](../reference/plot.md#hangtu.plot.consolidation_curve), [`ht.analysis.oedometer_fit`](../reference/analysis.md#hangtu.analysis.oedometer_fit)
- [Preconsolidation and compressibility](../parameters/06-preconsolidation-and-compressibility.md), the parameter page
- [Datasets](../guides/datasets.md): `p.oedometer()`
