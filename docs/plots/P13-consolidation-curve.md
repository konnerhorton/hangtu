# P13 — Consolidation curve: e against log σ′v, with σ′p, Cc, Cr and Cs

| | |
|---|---|
| **ID / function** | P13 · `ht.plot.consolidation_curve()` (+ `ht.analysis.oedometer_fit()`) |
| **Status** | draft |
| **Type** | plot + analysis |
| **Milestone** | M19 (b) (`STATUS.md`), [`docs/work/m19b-compressibility.md`](../work/m19b-compressibility.md) |
| **Depends on** | P00; `p.oedometer()` (M19 a); `oedometer_fit()` (M19 (b) Spec) |
| **Related** | P14–P15 (mv, cv and k, M19 c); sheet 06; P01 (σ′p and OCR by depth, beside the SPT correlations) |

---

## 1. Purpose
Draws one or more oedometer specimens as e against log σ′v, every increment by its branch, with the fitted Cr, Cc
and Cs lines, σ′p by Oikawa and by Pacheco Silva, and σ′v0 where it is known. Answers: is there a clear break, do
the lines follow the points, which points did each line use and which were left out, how far past σ′p did the test
go, and how disturbed was the sample. The engineer looks at it before using σ′p or Cc: a fit can be computed from a
curve that doesn't support it.

## 2. Reference figure
```
  e
 0.80 ┤●──●──●─╮                         ┌──────────────────────────────────────┐
      │         ●╲                       │ BH1-U3: σ′p = 264 kPa (Oikawa)       │
 0.75 ┤        │ ▼ ●                     │   Pacheco Silva: 239 kPa             │
      │ σ′v0 ┆ │    ╲   ○                │   Cc = 0.282, Cr = 0.0508, Cs = 0.0216│
 0.70 ┤      ┆ │     ●   ○ ○             │   OCR = 3.31, Δe/e0 = 0.025: very good│
      │      ┆ │      ╲  ◇ ○             │   to excellent (OCR 2–4)             │
 0.65 ┤      ┆ │       ●◇  ○             └──────────────────────────────────────┘
      │      ┆ │        ╲
 0.55 ┤      ┆ │         ● ○
 0.50 ┤      ┆ │          ◆
      └──────┴─┴──────┴──────┴──────┴─────
        10     100     1000   σ′v (kPa, log)
  ● loading  ○ unloading  ◇ reloading  ◆ loading past a reload  ▼ σ′p (Oikawa)  ▽ σ′p (Pacheco Silva)
```
**A good version:** the loading points joined in order, so the curve reads as a test, not a scatter; the Cc and Cr
lines solid over the points they fitted and thin dashed beyond, so where each line came from is plain; σ′p marked
on the curve, not at the lines' crossing (the fit's decision 6); the unload–reload loop visible, not hidden under
the lines.

## 3. Input data
**Row grain:** one row per increment, as `p.oedometer()` returns, or a CSV in `ht.template("oedometer")`'s shape.

| Column | Description | Quantity kind | Req.? | Notes |
|---|---|---|---|---|
| `specimen_id` | one curve each | text | ✔ | |
| `applied_vertical_stress` | σ′v at the end of the increment | stress | ✔ | |
| `void_ratio_at_increment_end` | e | dimensionless | ✔ | |
| `load_branch` | loading, unloading, reloading, constant stress | text | – | added by the fit when missing |
| `void_ratio` | e0 | dimensionless | – | CR, Pacheco Silva and Δe/e0; drawn at the left edge |
| `effective_vertical_stress` | σ′v0 | stress | – | OCR, Δe/e0, the σ′v0 line |
| `loca_id`, `depth`, `geology_unit` | the result box's label and the color | | – | |

**Grouping columns used:** `specimen_id` (one curve, one color, one box entry each).

**Value flags handled:** none. Rows the fit leaves out are counted in the footnote (§8).

**Minimum data:** 1 row to draw; 6 loading points for σ′p (the fit's decision 5).

## 4. Analysis / calculations
`ht.analysis.oedometer_fit()` (M19 (b) Spec, decisions 1–17; the derivation and golden values are there). The plot
calls it and draws its result; it computes nothing of its own. The Cc, Cr and Cs lines are drawn from the result's
e–log σ′v lines; Oikawa's lines are in log(1 + e)–log σ′v and are drawn only with `space="log_specific_volume"`
(§10), where they are straight and cross at σ′p.

**Fitted range.** Each line is solid between the lowest and highest stress of the points it fitted and thin dashed
from there across the axes.

## 5. Figure layout
- **Panels:** one.
- **Default size:** the `default` kind (6.5 × 4.5 in).
- **Legend:** README's rule; the branch marks and the σ′p marks once each, colors per specimen. The result box takes
  the upper-right corner (the curve falls to the right, leaving it clear), the legend the first clear one of the
  rest.

## 6. Axes
| X axis | Y axis |
|---|---|
| `Effective vertical stress, σ′v (kPa)`, log | `Void ratio, e` |

- With `space="log_specific_volume"`: y is `Specific volume, 1 + e`, log.
- **Limits:** x from a decade boundary at or below the lowest stress (or σ′v0, if lower) to one at or above the
  highest; y from a nice number below the lowest e to one above e0 (or the highest e).
- US labels use psf, or ksf / tsf with `ht.settings.display_overrides`, as P01.

**Range constraints:** none; the x axis is always log (the method's).

## 7. Data marks
| Series | Mark | Color | Legend |
|---|---|---|---|
| Loading points | filled circle, joined in order by a thin line | by specimen | "Loading" |
| Loading points past a reload | filled diamond | as loading | "Loading past a reload" |
| Unloading points | open circle | as loading | "Unloading" |
| Reloading points | open diamond | as loading | "Reloading" |
| Constant stress points | small cross | as loading | "Constant stress" |
| Points left out (no e, stress ≤ 0) | not drawn | — | counted in the footnote |
| Cc and Cr lines | solid over their points, thin dashed beyond | black with one specimen, else the specimen's | one entry, "Cc and Cr (dashed beyond their points)" |
| Cs line (the first run) | solid over its run | as above, lighter | "Cs" |
| σ′p (Oikawa) | filled down-triangle on the curve at σ′p | as the specimen | "σ′p (Oikawa)" |
| σ′p (Pacheco Silva) | open down-triangle on the curve | as the specimen | "σ′p (Pacheco Silva)" |
| e0 | short tick at the left edge | as the specimen | — |
| σ′v0 | vertical dotted line | as the specimen | "σ′v0" |

"On the curve" is the loading curve's e at that stress, interpolated as the fit interpolates (linear in e against
log σ′v).

## 8. Overlays and annotations
| Overlay | Argument | Default | Source of definition | Style | Notes |
|---|---|---|---|---|---|
| Fit lines and σ′p | `fit=` | `True` | `oedometer_fit()` | §7 | `False` draws points only, and the result is None |
| Pacheco Silva construction | `construction=` | `False` | the fit's σA, e_B | thin gray lines | the three steps of the check, for a report |
| Result box | `result_box=` | on with the fit | the fit | upper right | per specimen: σ′p (both), Cc, Cr, Cs, CR; OCR and Δe/e0 with the class and "(OCR 1–2 row)"; a value that is blank gives its reason |
| Footnote | — | when anything is left out | the fit's counts | README | "Left out of BH1-U3: 2 reloading, 1 unloading after the first run"; "The Δe/e0 class uses this test's OCR: …" whenever a class is shown; a frame without `effective_vertical_stress` once, "No OCR or Δe/e0: run ht.analysis.vertical_stress() on the rows for σ′v0", rather than in each specimen's box entry |
| `note` | as README | off | | | |

## 9. Units behavior
Stresses convert (kPa ↔ psf, ksf, tsf); void ratios and the indexes don't. The fit is made in the display units
(`oedometer_fit(display_units=...)`), so the box and the axes agree.

## 10. API
```python
def consolidation_curve(
    df: pd.DataFrame,
    *,
    space: Literal["void_ratio", "log_specific_volume"] = "void_ratio",
    fit: bool = True,
    construction: bool = False,
    result_box: bool = True,
    note: str | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides,
) -> tuple[Figure, Axes, OedometerFit | None]:
```
- `units=` and `display_units=` go to `oedometer_fit()` as they are.
- `space="log_specific_volume"` draws log(1 + e) against log σ′v with Oikawa's two lines instead of Cc and Cr, so
  the engineer sees the fit σ′p came from; Cs and the construction aren't drawn there, and the lines only where σ′p
  is given.

**Examples:**
```python
oed = ht.analysis.vertical_stress(p.oedometer(where={"test_type": "OEDOMETER"}), p.stratigraphy())
fig, ax, fit = ht.plot.consolidation_curve(oed)
fig, ax, fit = ht.plot.consolidation_curve(oed, space="log_specific_volume")
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| A required column missing | The fit's error naming it and `ht.template("oedometer")` |
| No σ′p (too few points, no clear break, crossing outside, line too short) | Points drawn, no Cc, Cr or σ′p marks, the reason in the box; Cs drawn if given |
| No unload | No Cs line; "Cs: no unloading" in the box |
| No e0 | No e0 tick, no Pacheco Silva mark; CR and the check's reasons in the box |
| No σ′v0 | No σ′v0 line; OCR and Δe/e0 reasons in the box |
| OCR < 1 | Drawn as given, with the fit's warning; "OCR = 0.88 (< 1)" in the box |
| A specimen with no increments (`SWELLPRESS`) | Not drawn; the footnote names it |
| Many specimens | One color each; the box lists each (README's rule on long boxes) |
| `construction=True` without a check | Nothing extra drawn for that specimen |
| `space=` another value | Error listing the two |

## 12. Acceptance criteria and tests
Golden values are the M19 (b) Spec's (AC 1–11), hand-calculated there. Tolerance 1e-9 relative on drawn data unless
stated.
1. **Points:** BH1-U3 (`site_si.ags`) draws 7 loading points (one, at 1600 kPa, as a diamond), 3 unloading and 2
   reloading points at their (σ′v, e), the loading points joined in file order.
2. **Lines:** the Cc line passes through e = 1.42706111 at σ′v = 1 kPa with slope −0.282363888 per log cycle, solid
   from 400 to 1600 kPa (the upper group of the 4 | 3 split); the Cr line solid from 25 to 200 kPa; the Cs line
   solid from 50 to 800 kPa.
3. **σ′p marks:** the Oikawa triangle at σ′v = 264.401656 kPa on the loading curve, the Pacheco Silva one at
   239.040472 kPa; `construction=True` adds the three steps through σA = 166.247579 kPa and e_B = 0.755466667.
4. **`space="log_specific_volume"`:** log y axis, Oikawa's two lines crossing at 264.401656 kPa, no Cs line.
5. **σ′v0 and the box:** with σ′v0 = 80 kPa, the dotted line at 80 kPa and the box's "OCR = 3.31, Δe/e0 = 0.0252:
   very good to excellent (OCR 2–4 row)", and the footnote's caveat.
6. **No σ′p:** the Spec's AC 8 frame draws its points and Cs, no Cc, Cr or σ′p marks, and the box gives the no-break
   reason.
7. **Returns:** `(fig, ax, fit)` with `fit` equal to `oedometer_fit()` on the same rows and arguments; `fit=False`
   returns None and draws no line; `ax=` draws into the given axes without a new figure.
8. **Units:** `display_units="US"` and `"SI"` on the twin files give the same lines in e, σ′p scaled by 47.880259
   Pa/psf, and labels in psf and kPa.
9. **Edge cases:** each row of §11 that raises raises, with its message naming what §11 says; each that draws,
   draws (a hand-built frame per case).
10. **Visual check:** `docs/plots/img/P13-us.png` (the example project's two specimens, psf) and `P13-si.png`
    (BH1-U3, kPa, with σ′v0 and `construction=True`), at 100 dpi, looked at and committed in the close-out.

## 13. References
- Oikawa, H. (1987). Compression curve of soft soils. *Soils and Foundations* 27(3), 99–104: σ′p as the intersection
  of the two straight segments of log(1 + e)–log σ′v (p. 103).
- Pacheco Silva, F. (1970), via Paniagua et al. (2016), NGM 2016, §2.4: the check's construction.
- Lunne, T., Berre, T. & Strandvik, S. (1997), via Krage et al. (2015) and Thakur (2016): the Δe/e0 classes.

## 14. Open questions
- None open.

**Pitfalls:**
- Drawing σ′p where the Cc and Cr lines cross: they are fitted in e–log σ′v, Oikawa's in log(1 + e)–log σ′v, and the
  two crossings differ (BH1-U3: about 252 against 264 kPa).
- Joining every point in file order with one line, so the unload–reload loop reads as part of the virgin curve.
- Showing the Δe/e0 class without the OCR row it used.
- Rounding σ′p or the indexes inside the analysis; round only for display.

## 15. Future enhancements
- Strain (ε) instead of e on the y axis, once (c) settles the strain definition (TODO #73).
- Casagrande's and the work method's σ′p beside Oikawa's (TODO, M19 (b) close-out).
- `OedometerFit.plot()` to draw a result without refitting.
- σ′p and OCR by depth with the SPT correlations: P01 with the fit's frame, a docs example rather than a new plot.
