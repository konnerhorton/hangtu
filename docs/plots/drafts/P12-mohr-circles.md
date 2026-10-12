# P12 — Mohr circles with Mohr–Coulomb envelope (draft notes)

| | |
|---|---|
| **ID / function** | P12 · `ht.plot.mohr_circles()` (+ `ht.analysis.mohr_coulomb_fit()`) |
| **Status** | idea (draft notes) |
| **Type** | plot + analysis |
| **Target version** | v0.5 |
| **Depends on** | P00; shares the fit with P11 |
| **Related** | P11 (s′–t points), P27 (fitted c′, φ′ compared with published values) |

---

## 1. Purpose
Draws the failure Mohr circles of a set of triaxial specimens (one sample's stages, or all specimens of a unit) with the fitted Mohr–Coulomb envelope, and states c′ and φ′. Answers: what strength parameters do these tests support, and how well does one line fit them. Used in lab data reports and to justify design strength.

Two scopes are both useful: **per sample**, and **per geology unit** (all circles of the unit on one chart, with one fit). Per-sample c′, φ′ also feed comparisons with published values (P27).

## 2. Reference figure
```
  τ (kPa)
  300 ┤                                  ┌─────────────────┐
      │                       ___------  │ c′ = 35 kPa      │
  200 ┤            ___-----‾‾‾  ╭──╮     │ φ′ = 19.5°       │
      │   ___---‾‾‾    ╭──╮  ╱    ╲     │ n = 3 circles    │
  100 ┤-‾‾      ╭──╮ ╱    ╲╱       ╲    └─────────────────┘
      │       ╱    ╲╱      ╲        ╲
    0 ┼──────┴──────┴───────┴────────┴──────────────
      0     100    200     300      400    500   σ′ (kPa)
```
**A good version:** equal aspect, so circles are circles; upper half only; the envelope drawn across the whole plot; the fit's numbers in a box.

## 3. Input data
**Row grain:** one row per specimen (or stage) at failure.

| Column | Description | Quantity kind | Unit | Req.? | Notes |
|---|---|---|---|---|---|
| *proposed* `effective_minor_principal_stress` | σ′3 at failure | stress | kPa | ✔ (or total) | |
| *proposed* `effective_major_principal_stress` | σ′1 at failure | stress | kPa | ✔ | |
| *proposed* `minor_principal_stress`, `major_principal_stress` | Total stresses (UU, total-stress CU) | stress | kPa | alt. | `stress="total"` |
| `specimen_id` | Circle identity / label | | | – | |
| `geology_unit` | Color, grouping of a combined fit | | | – | |
| `test_type` | e.g. CU, CD, UU | | | – | |

Proposed names are to be checked against the registry. Long but explicit, per CLAUDE.md naming.

**Minimum data:** 1 circle to draw; ≥ 2 circles to fit c′ and φ′; 1 circle with `cohesion=0` fixed.

## 4. Analysis / calculations
- **Function:** `ht.analysis.mohr_coulomb_fit(df, *, stress="effective", cohesion=None) -> MohrCoulombFit`
- **Method: least squares on the failure points in s′–t space** (MIT):
  1. s′ = (σ′1 + σ′3)/2, t = (σ′1 − σ′3)/2 per specimen.
  2. Fit t = a + s′ tan α (OLS, t on s′).
  3. sin φ′ = tan α; c′ = a / cos φ′.
  4. `cohesion=0`: fit through the origin (a = 0).
- **Result fields:** `cohesion` (stress), `friction_angle` (degrees), `a`, `alpha`, `n`, `r_squared`, `method`, the points used.
- **Edge cases:** tan α ≥ 1 → no valid φ′, error naming the specimens; a < 0 → reported as is, with a warning suggesting `cohesion=0`.
- Numerical alternatives (e.g. sweeping the tangent angle and minimizing the mean gap to each circle) approximate the same goal; the closed form is simpler and reproducible.

## 5. Figure layout
Single panel. Default size `default`; equal aspect means the τ range is about half the σ′ range (x to ≈ 1.1 × max σ′1).

## 6. Axes
| | X axis | Y axis |
|---|---|---|
| Quantity | normal stress σ′ | shear stress τ |
| Label (SI) | `Effective normal stress, σ′ (kPa)` | `Shear stress, τ (kPa)` |
| Label (US) | `… (psf)` | `… (psf)` |
| Limits | 0 to a nice number above 1.05 × max σ′1 | 0 to the matching height |

**Range constraints:** [x] equal aspect (README: required).

## 7. Data marks
| Series | Mark | Color by | Legend |
|---|---|---|---|
| Circles | upper semicircle, no fill | `geology_unit` or `specimen_id` | ✔ |
| Failure points (optional) | dot at (s′, t) | as circles | — |
| Envelope | straight line τ = c′ + σ′ tan φ′ | black | ✔ "Fit: c′ = …, φ′ = …" |

## 8. Overlays and annotations
| Overlay | Argument | Default | Notes |
|---|---|---|---|
| Fit envelope | `fit=` | on with ≥ 2 circles | `False` draws circles only |
| Result box | `result_box=` | on with the fit | c′, φ′, n, R² |
| User envelopes | `envelopes=` list of `(cohesion, friction_angle, label)` | off | e.g. design strength |

## 9. Units behavior
Stresses convert (kPa ↔ psf/ksf); φ′ in degrees in both; c′ in display units.

## 10. API
```python
fig, ax, fit = ht.plot.mohr_circles(triaxial, stress="effective", group_by="specimen_id")
fig, ax, fit = ht.plot.mohr_circles(triaxial[triaxial.geology_unit == "Till"])
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| σ′1 < σ′3 | Error naming the rows |
| Negative σ′3 | Drawn; warning (tension) |
| One circle | Drawn; no fit unless `cohesion=0` |
| Mixed total and effective | Error (`stress=` picks one) |

## 12. Acceptance criteria and tests
- Golden: σ′3 = 100, σ′1 = 300 and σ′3 = 200, σ′1 = 500 kPa → s′ = 200, 350; t = 100, 150; tan α = 1/3, a = 33.3 kPa; **φ′ = 19.47°, c′ = 35.36 kPa**; the line is tangent to both circles (distance from each center = radius).
- Equal aspect verified on the rendered axes.

## 13. References
- Lambe, T.W. & Whitman, R.V. (1969). *Soil Mechanics*. Wiley. (s′–t / stress path method.)
- ASTM D4767 (CU), D7181 (CD), D2850 (UU).

## 14. Open questions
- One fit per unit across samples or one per sample by default? Both are used; `group_by=` decides.

**Pitfalls:**
- Forcing the line through the origin whenever the intercept comes out negative, without saying so.
- Rounding c′ and φ′ inside the analysis; round only for display.

## 15. Future enhancements
- Curved (power-law) envelopes; peak vs critical-state envelopes.
