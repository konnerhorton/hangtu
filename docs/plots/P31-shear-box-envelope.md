# P31 — Shear box envelope: τ against σn, peak and residual

| | |
|---|---|
| **ID / function** | P31 · `ht.plot.shear_box_envelope()` (+ `ht.analysis.shear_box_fit()`) |
| **Status** | draft |
| **Type** | plot + analysis |
| **Milestone** | M17 (b) (SPEC §12.4), [`docs/work/m17b-shear-box-fit.md`](../work/m17b-shear-box-fit.md) |
| **Depends on** | P00; `p.shear_box()` (M17 a); `shear_box_fit()` (M17 (b) Spec) |
| **Related** | P11 (the triaxial envelope; its Mohr view is also τ against σ); sheets 04 and 22; TODO #53 |

---

## 1. Purpose
Draws a set of shear box stages (one test's, a geology unit's, or a joint set's) as points in τ–σn, peak and
residual, with the fitted lines, free and through the origin, and states c and φ for each. Answers: what peak and
residual strength do these tests support, over what normal stress, how well does one line fit them, how much of
the intercept goes away through the origin, and how does the fit compare with the lab's. Used in lab data reports,
calculation packages, and to judge whether a joint's intercept is cohesion or roughness (page 22).

A figure of its own, not a fourth space of P11 (M17 (b) intent, decision 9): P11 draws circles from principal
stresses and takes a `MohrCoulombFit`; here the points are measured pairs and the result is a `ShearBoxFit`.

## 2. Reference figure
```
  τ (kPa)
  150 ┤                                   ┌───────────────────────────────────┐
      │                            ● ╱    │ Peak: c = 8 kPa, φ = 31.0°        │
      │                          ╱  ╱ ○   │   n = 3, R² = 1.000, σn 50–200 kPa│
  100 ┤                       ╱  ╱  ╱     │   through origin: φ = 33.2°       │
      │                  ● ╱ ·╱  ╱        │ Residual: c = 3 kPa, φ = 28.6°    │
   50 ┤          ● ╱ ○ ╱ ·╱  ╱            │ Lab: c = 8 kPa, φ = 31.0°         │
      │  - - -╱ ○ ╱ ·╱ ╱                  └───────────────────────────────────┘
    0 ┼╱─────┴────┴────┴──────────┴────────────────
      0     50   100  150        200      250   σn (kPa)
  ● peak  ○ residual  ── free fit (dashed beyond the points)  ··· through the origin
```
**A good version:** equal aspect, so a line's slope reads as its angle; the free line solid over the σn the points
cover and dashed from there to σn = 0 and the right edge, so c reads as an intercept, not a measurement; the
through-origin line lighter, so the eye compares the two; peak and residual told apart by the mark, groups by color.

## 3. Input data
**Row grain:** one row per stage, as `p.shear_box()` returns, or a CSV in `ht.template("shear_box")`'s shape.

| Column | Description | Quantity kind | Req.? | Notes |
|---|---|---|---|---|
| `peak_shear_stress`, `residual_shear_stress` | τp, τr | stress | ✔ (one of them) | a blank leaves the stage out of that strength |
| `applied_normal_stress` | σn applied (`SHBT_NORM`) | stress | ✔ unless the next ones are given | |
| `normal_stress_at_peak`, `normal_stress_at_residual` | σn at peak and residual (`SHBT_PVST`, `SHBT_RVST`) | stress | – | used first where given (the fit's decision 5) |
| `test_type`, `failure_criterion` | as written | text | – | not pooled unawares (the fit's decision 6) |
| `reported_peak_cohesion`, `reported_peak_friction_angle`, and the residual pair | the lab's fit | stress, angle | – | shown beside hangtu's |
| `specimen_id`, `test_stage` | names a point in messages | text | – | else the row's index |
| `geology_unit` | color, and a common `group_by=` | text | – | |

**Grouping columns used:** `group_by=` (one set of lines and one color per group); `color_by=` (points only, without
`group_by=`).

**Value flags handled:** none on the stresses. Rows the fit leaves out are counted in the footnote (§4).

**Minimum data:** 1 row to draw; per strength, 2 points at different σn for the free line, 1 for the line through
the origin.

## 4. Analysis / calculations
`ht.analysis.shear_box_fit()` (M17 (b) Spec, decisions 1–17; the derivation and golden values are there). The plot
calls it with the shared arguments and draws its result; it computes nothing of its own. Points are drawn at the
σn the fit used (each point's `normal_stress_basis`), so the points and the line agree.

**Fitted range.** The free line is solid from `lowest_normal_stress` to `highest_normal_stress` of its strength and
dashed from there to σn = 0 and to the right edge. The through-origin line is drawn from 0 to the right edge, thin
and lighter (no solid part: it is a constraint, not a range).

## 5. Figure layout
- **Panels:** one.
- **Default size:** the `default` kind (6.5 × 4.5 in).
- **Legend:** README's rule; marks (peak, residual) and line kinds (free, through the origin) once each, colors per
  group. The result box takes the upper-left corner (the lines climb to the right), the legend the first clear one
  of the rest.

## 6. Axes
| X axis | Y axis |
|---|---|
| `Normal stress, σn (kPa)` | `Shear stress, τ (kPa)` |

- No prime: the stresses aren't labeled effective (M17 (a) decision 10).
- **Limits:** x from 0 to a nice number above the largest σn; y from 0 (or a nice number below a negative free
  intercept) to the height equal aspect gives, at least a nice number above the largest τ. As P11, the axis equal
  aspect leaves short is extended to fill the axes.
- US labels use psf, or ksf with `ht.settings.display_overrides = {"stress": "ksf"}`, as P01 and P11.

**Range constraints:** [x] equal aspect, so a slope reads as its angle and figures compare.

## 7. Data marks
| Series | Mark | Color | Legend |
|---|---|---|---|
| Peak points | filled circle | by group, else `color_by` | "Peak" (black when there are colors) |
| Residual points | open circle, same size | as peak | "Residual" |
| Free line | solid over the fitted range, dashed beyond | black with one group; the group's color with several | "Free fit" |
| Through-origin line | thin dotted, 60 % opacity | as the free line | "Through the origin" |
| User envelopes | gray line | — | the label given |

With `cohesion=0`, the line kinds swap styles: the main line is the one drawn solid and dashed (the fit's
decision 4).

## 8. Overlays and annotations
| Overlay | Argument | Default | Source of definition | Style | Notes |
|---|---|---|---|---|---|
| Fit lines | `fit=` | `True` | `shear_box_fit()` | §7 | `False` draws points only, and the result is None |
| Strengths | `strengths=` | `("peak", "residual")` | — | — | `("peak",)` or `("residual",)` draws one; the fit still has both |
| Result box | `result_box=` | on with the fit | the fit | text box, upper left | per group and strength: the main line's c, φ, n, R², the σn range; the other line's φ (and c when free); "Lab: c = 8 kPa, φ = 31.0°" where the rows have it; a line with no fit says why |
| User envelopes | `envelopes=` list of `(cohesion, friction_angle, label)` | off | user | gray | c in the display units, φ in degrees |
| Footnote | — | when anything is left out, or a line mixes bases | the fit's counts and notes | README | "Left out of residual: 1 without a shear stress"; "Peak σn: 2 at peak, 1 applied" |
| `note` | as README | off | | | |

## 9. Units behavior
Stresses convert (kPa, MPa ↔ psf or ksf); φ in degrees in both; c in the display units. The fit is made in the
display units (`shear_box_fit(display_units=...)`), so the box, the axes and the result agree. A joint set draws
in MPa inside `ht.settings.override(display_overrides={"stress": "MPa"})` with `display_units="SI"` (how page 22
shows the example's joints, stored in psf), or in a frame's own unit with `display_units=None`.

## 10. API
```python
def shear_box_envelope(
    df: pd.DataFrame,
    *,
    group_by: str | list[str] | None = None,
    color_by: str | None = None,
    cohesion: float | None = None,
    normal_stress: Literal["at_peak_or_residual", "applied"] = "at_peak_or_residual",
    pool: str | list[str] | None = None,
    strengths: Sequence[Literal["peak", "residual"]] = ("peak", "residual"),
    fit: bool = True,
    result_box: bool = True,
    envelopes: list[tuple[float, float, str]] | None = None,
    note: str | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides,
) -> tuple[Figure, Axes, ShearBoxFit | None]:
```
- `group_by=`, `cohesion=`, `normal_stress=`, `pool=`, `units=` and `display_units=` go to `shear_box_fit()` as
  they are.
- `color_by=` colors points when there's no `group_by=`; its default is `geology_unit` when the rows have it, else
  one color. With `group_by=`, color is by group and `color_by=` is an error (one color per set of lines), as P11.

**Examples:**
```python
fig, ax, fit = ht.plot.shear_box_envelope(p.shear_box(), group_by="geology_unit")
with ht.settings.override(display_overrides={"stress": "MPa"}):
    fig, ax, fit = ht.plot.shear_box_envelope(p.shear_box(geology=["Sandstone"]), display_units="SI")
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| No shear stress column, or no normal stress the fit can use | The fit's error naming them and `ht.template("shear_box")` |
| One point in a strength | Drawn; the through-origin line only; the box says "free: no fit: 1 point: a line needs at least 2" |
| Only residuals (a ring shear test) | Open points and residual lines; the box has no peak line, the footnote counts the stages without a peak |
| A line with no fit (slope < 0, same σn) | Its points drawn, no line, its reason in the box; the other lines drawn |
| Negative free intercept | Drawn as fitted, below 0, with the fit's warning and "c < 0" in the box; never forced |
| Negative τ or σn | The fit's error naming the rows |
| Mixed test types or failure criteria | The fit's error naming each value and count; `pool=` draws them as one set |
| A strength's points mix normal stress bases | Drawn at each point's basis; the footnote counts them |
| `strengths=` empty or with another value | Error listing `"peak"` and `"residual"` |
| `color_by=` with `group_by=` | Error (§10) |
| Missing units | The fit's error naming the column (the box needs the unit) |
| Optional columns missing (`failure_criterion`, `test_type`, `geology_unit`) | One hint listing them and what each adds |

## 12. Acceptance criteria and tests
Golden values are the M17 (b) Spec's (AC 1–8), hand-calculated there. Tolerance 1e-9 relative on drawn data unless
stated.
1. **Lines:** BH2-D1 (`site_si.ags`) draws the peak free line crossing σn = 0 at τ = 8 kPa with slope 0.6, solid
   from σn = 50 to 200 kPa and dashed beyond; the peak through-origin line through (0, 0) with slope 49/75; the
   residual lines with intercept 3 and slopes 191/350 and 99/175.
2. **Points:** 3 filled at (50, 38), (100, 68), (200, 128) and 3 open at (50, 30), (100, 58), (200, 112), at the
   σn of their basis (a hand-built mixed-basis frame draws each at its own and has the footnote).
3. **`cohesion=0`** swaps the styles of the line kinds (§7) and the box's order; the values don't change.
4. **Equal aspect** on the rendered axes (`ax.get_aspect() == 1`), and §6's limits, including below 0 for AC 8's
   negative intercept in the fit's spec.
5. **Groups:** `site.ags` with `group_by="geology_unit"` draws two sets of lines in the Alluvium's and the
   Terrace's colors, the box with both and two lab pairs per strength for the Alluvium (the fit's AC 6).
6. **Strengths:** `strengths=("residual",)` on `joins.ags`'s J1-D2 draws one open point and the through-origin
   line at φ = 11.859779°; the box says why there is no free line.
7. **Returns:** `(fig, ax, fit)` with `fit` equal to `shear_box_fit()` on the same rows and arguments; `fit=False`
   returns None and draws no line; `ax=` draws into the given axes without a new figure.
8. **Units:** `display_units="US"` and `"SI"` on the twin files give the same φ, c scaled by 47.880259 Pa/psf
   (1e-9 relative), and labels in psf and kPa; the example's Sandstone joints with the MPa override label MPa and
   draw the free peak line through τ = 0.1 MPa at σn = 0.
9. **Edge cases:** each row of §11 that raises raises, with its message naming what §11 says; each that draws,
   draws (a hand-built frame per case).
10. **Visual check:** `docs/plots/img/P31-us.png` (the example project's soil sets by geology unit, psf) and
    `P31-si.png` (the example's Sandstone joints, MPa), at 100 dpi, looked at and committed in the close-out.

## 13. References
- Hoek, E. (2023). *Practical Rock Engineering*, ch. 4, eqs. 1–2: the linear peak and residual criterion, and the
  advice to report the free and through-origin fits together (page 22, [V]).
- The fit is least squares on the criterion's line, derived in the M17 (b) Spec. ASTM D3080 (shear box) and D6467
  (ring shear) define the tests and failure criteria (TODO #53).

## 14. Open questions
- None beyond the M17 (b) Spec's 🟡 items, for review with it.

**Pitfalls:**
- Drawing the free line solid across the whole axis, which reads as if c were measured at σn = 0.
- Plotting points against `applied_normal_stress` while the fit used `normal_stress_at_peak`, so the line misses
  the points.
- Drawing only the free line, or replacing it with the through-origin line when its intercept is negative.
- Rounding c and φ inside the analysis; round only for display.

## 15. Future enhancements
- `ShearBoxFit.plot()` to draw a result without refitting (as `FitResult.plot()`).
- The secant angle against σn as a second panel, to show a curved envelope (sheet 22 §5.2).
- Curved (power-law) and Barton–Bandis envelopes (wave 4), and the tangent at a design σn.
- Displacement curves (τ and dilation against displacement, wave 0).
