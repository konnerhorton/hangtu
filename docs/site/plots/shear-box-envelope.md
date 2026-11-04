# Shear box envelope

Shear box stages in τ–σn, peak and residual, with the lines fitted to them, free and through the origin, and c and φ beside the lab's own values.

```python
--8<-- "shear-box-envelope.py"
```

![Shear box stages of the example project's Alluvium and Terrace, peak and residual, with one set of lines per geology unit](../img/generated/shear-box-envelope.png){ width="560" }

## What it shows

One point per stage: filled for the peak shear stress, open for the residual. The lines are those `ht.analysis.shear_box_fit()` fits to them, τ = c + σn tan φ by least squares. Here each geology unit has its own: two undisturbed tests in the Alluvium and a recompacted one in the Terrace.

Each strength gets two lines. The free fit is solid over the normal stresses tested and dashed beyond: c is where the dashed line meets σn = 0, outside the stresses tested, so read it as an intercept, not a measured strength. The fit through the origin is drawn dotted beside it. Report the two together: a large intercept from few stages is usually roughness, not cohesion (Hoek 2023, ch. 4). The box gives each line's c, φ, the number of points, R², the range of σn, and the lab's own c and φ where the file reports them. hangtu doesn't judge the difference.

The axes have equal aspect, so a line's slope reads as its angle.

## Which normal stress

A shear box file can give three normal stresses: the one applied (`SHBT_NORM`) and the ones at peak and at residual (`SHBT_PVST`, `SHBT_RVST`), which a lab may correct for the shrinking contact area. Each point is drawn at the one the fit used: the stress at peak or residual where the row has it, else the applied one. The footnote says when a strength's points mix them. `normal_stress="applied"` uses the applied stress throughout.

## Not a triaxial φ′

The fitted values are named `peak_friction_angle` and `residual_friction_angle`, not `effective_friction_angle`: the file doesn't say whether the stresses are effective, and a direct shear φ isn't a triaxial φ′ until it's converted. Keep them apart until selection.

## Rock joints

The same function and figure fit joints and bedding planes: separate them from soil tests with `group_by=` or `p.shear_box(geology=...)`, since nothing in an AGS file labels a test as a rock joint. To show a joint set in MPa from a file stored in psf or kPa:

```python
with ht.settings.override(display_overrides={"stress": "MPa"}):
    fig, ax, fit = ht.plot.shear_box_envelope(joints, display_units="SI")
```

[Discontinuity shear strength](../parameters/22-discontinuity-shear-strength.md) shows it on the example project's sandstone.

## Common options

| Argument | Does |
|---|---|
| `group_by=` | One set of lines per group, such as `"geology_unit"` or `"specimen_id"` |
| `cohesion=0` | Make the line through the origin the main one, drawn solid; the free fit is still drawn and returned |
| `strengths=` | `("peak",)` or `("residual",)` to draw one; the fit returned has both |
| `normal_stress="applied"` | Fit and draw every point at the applied normal stress |
| `envelopes=` | Your own lines, `[(cohesion, friction_angle, label)]` |
| `pool=` | Fit rows with different test types or failure criteria together, on purpose |
| `fit=False` | The points only |

For the numbers without a figure:

```python
fit = ht.analysis.shear_box_fit(stages, group_by="geology_unit")
fit.to_frame()
```

## See also

- [`ht.plot.shear_box_envelope`](../reference/plot.md#hangtu.plot.shear_box_envelope), [`ht.analysis.shear_box_fit`](../reference/analysis.md#hangtu.analysis.shear_box_fit)
- [Drained shear strength](../parameters/04-drained-shear-strength-soil.md) and [Discontinuity shear strength](../parameters/22-discontinuity-shear-strength.md), the parameter pages
- [Datasets](../guides/datasets.md): `p.shear_box()`
