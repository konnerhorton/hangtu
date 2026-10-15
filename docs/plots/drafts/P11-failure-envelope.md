# P11 — Failure envelope: Mohr circles, s′–t or p′–q (draft notes)

| | |
|---|---|
| **ID / function** | P11 · `ht.plot.failure_envelope()` (+ `ht.analysis.mohr_coulomb_fit()`) |
| **Status** | idea (draft notes) |
| **Type** | plot + analysis |
| **Target version** | v0.2 (M11) |
| **Depends on** | P00 |
| **Related** | P12 (stress–strain curves and measured stress paths, reuses this fit), P26 and P27 (fitted c′, φ′ compared with correlations and published values) |

---

## 1. Purpose
Draws the failure state of a set of triaxial specimens (one sample's stages, or all specimens of a geology unit) with the fitted Mohr–Coulomb envelope, and states c′ and φ′. Answers: what strength parameters do these tests support, and how well does one line fit them. Used in lab data reports and to justify design strength.

One function draws the same failure points and the same fit in any of three spaces, chosen with `space=`:
- `"mohr"`: Mohr circles in σ′–τ, with the envelope τ = c′ + σ′ tan φ′.
- `"s_t"`: failure points in MIT s′–t, with the K_f line.
- `"p_q"`: failure points in Cambridge p′–q, with the same envelope transformed.

The views differ in interpretation, not in data, so they share one input table, one fit, one set of overlays and one set of edge cases. Merged from the former P11 (stress paths) and P12 (Mohr circles) drafts. Stress–strain curves and paths measured during shearing need readings at each strain step, which AGS doesn't carry; they are P12.

Two scopes are both useful: **per sample**, and **per geology unit** (all specimens of the unit on one chart, with one fit). Per-sample c′, φ′ also feed comparisons with published values (P27).

**Idealized drained paths.** In s′–t and p′–q, `paths="idealized_drained"` draws each specimen's path as a CD compression test at constant cell pressure would have taken it: from (σ′3, 0) to the failure point. It isn't the measured path and is labeled as such.

## 2. Reference figure
`space="mohr"`:
```
  τ (kPa)
  300 ┤                                  ┌─────────────────┐
      │                       ___------  │ c′ = 35 kPa      │
  200 ┤            ___-----‾‾‾  ╭──╮     │ φ′ = 19.5°       │
      │   ___---‾‾‾    ╭──╮  ╱    ╲     │ n = 3 specimens  │
  100 ┤-‾‾      ╭──╮ ╱    ╲╱       ╲    └─────────────────┘
      │       ╱    ╲╱      ╲        ╲
    0 ┼──────┴──────┴───────┴────────┴──────────────
      0     100    200     300      400    500   σ′ (kPa)
```

`space="s_t", paths="idealized_drained"`:
```
   t (kPa)
  200 ┤                      ● ← failure
      │                  ╱  ·
  100 ┤           ●   ╱ ·· ← fitted K_f line
      │       ╱  ·  ╱
      │   ╱ ··   ╱ ← idealized drained path (dashed)
    0 ┼╱────────╱──────────────
      0   100  200  300  400   s′ (kPa)
```
**A good version:** equal aspect, so circles are circles and slopes read true; upper half only; the envelope drawn across the whole plot; the fit's numbers in a box.

## 3. Input data
**Row grain:** one row per specimen (or stage) at failure. This is what AGS carries: the triaxial groups report the stresses at failure, not readings during shearing (checked against the 4.1–4.2 dictionaries, 2026-10-15: TRET and TRIT have one row per test or stage, `TRET_TESN`, at failure).

| Column | Description | Quantity kind | Unit | Req.? | Notes |
|---|---|---|---|---|---|
| *proposed* `effective_minor_principal_stress` | σ′3 at failure | stress | kPa | ✔ (or total) | |
| *proposed* `effective_major_principal_stress` | σ′1 at failure | stress | kPa | ✔ | |
| *proposed* `minor_principal_stress`, `major_principal_stress` | Total stresses (UU, total-stress CU) | stress | kPa | alt. | `stress="total"` |
| `specimen_id` | Specimen identity / label | | | – | |
| `geology_unit` | Color, grouping of a combined fit | | | – | |
| `test_type` | e.g. CU, CD, UU | | | – | Checked by `paths=` (§11) |

Proposed names are to be checked against the registry. Long but explicit, per CLAUDE.md naming.

**Where the principal stresses come from.** The file gives the cell pressure σ3 (`TRET_CELL`, `TRIT_CELL`), the deviator stress q_f (`TRET_DEVF`, `TRIT_DEVF`) and the pore pressure u_f (`TRET_PWPF`) at failure. Under "only what the file says" (SPEC §7) the principal stresses aren't stored: a Phase 2 dataset (`p.triaxial()`, not yet specified) derives σ′3 = σ3 − u_f and σ′1 = σ′3 + q_f, and the plot takes the principal stresses. Which failure criterion the lab used (maximum deviator stress or maximum stress ratio) is the lab's choice, carried as given.

**Minimum data:** 1 specimen to draw; ≥ 2 to fit c′ and φ′; 1 with `cohesion=0` fixed.

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

**Drawing the fit in each space.** The fit is always done in s′–t; the other spaces draw the same line transformed, never a separate regression (with more than two points, a regression in p′–q gives a different c′ and φ′).

| Space | Points | Envelope | Intercept on the y axis |
|---|---|---|---|
| `mohr` | circle center (s′, 0), radius t | τ = c′ + σ′ tan φ′ | c′ |
| `s_t` | (s′, t) | t = a + s′ tan α | a = c′ cos φ′ |
| `p_q` | p′ = (σ′1 + 2σ′3)/3, q = σ′1 − σ′3 | q = q₀ + M p′, M = 6 sin φ′ / (3 − sin φ′) | q₀ = 6 c′ cos φ′ / (3 − sin φ′) |

The p′–q line is for triaxial compression. Extension has a different M (§15).

**Idealized drained path** (`paths="idealized_drained"`): from (σ′3, 0) to the failure point; slope 1 in s′–t, 3 in p′–q.

## 5. Figure layout
Single panel. Default size `default`; equal aspect means the y range is about half the x range in `mohr` (x to ≈ 1.1 × max σ′1).

To show two spaces side by side (a common report layout), the engineer makes the axes and calls the function twice with `ax=`. A built-in two-panel option is a future enhancement (§15).

## 6. Axes
| Space | X axis | Y axis |
|---|---|---|
| `mohr` | `Effective normal stress, σ′ (kPa)` | `Shear stress, τ (kPa)` |
| `s_t` | `Mean effective stress, s′ (kPa)` | `Deviator stress, t (kPa)` |
| `p_q` | `Mean effective stress, p′ (kPa)` | `Deviator stress, q (kPa)` |
| Limits | 0 to a nice number above the largest value | 0 to the matching height |

US labels use psf (or ksf). With `stress="total"` the primes are dropped (`Normal stress, σ (kPa)`).

**Range constraints:** [x] equal aspect in all three spaces. Required for Mohr circles (README); required in s′–t and p′–q too, so slopes (45° drained path in s′–t, M in p′–q) read true and figures are comparable.

## 7. Data marks
| Series | Mark | Color by | Legend |
|---|---|---|---|
| Circles (`mohr`) | upper semicircle, no fill | `geology_unit` or `specimen_id` | ✔ |
| Failure points | dot; in `mohr` at the top of the circle (s′, t), optional | as circles | — |
| Idealized paths (`s_t`, `p_q`) | dashed line per specimen | as points | ✔ "Idealized drained path" |
| Envelope / K_f line | black line | — | ✔ "Fit: c′ = …, φ′ = …" |

## 8. Overlays and annotations
| Overlay | Argument | Default | Notes |
|---|---|---|---|
| Fit envelope | `fit=` | on with ≥ 2 specimens | `False` draws the points (or circles) only |
| Result box | `result_box=` | on with the fit | c′, φ′, n, R² |
| User envelopes | `envelopes=` list of `(cohesion, friction_angle, label)` | off | e.g. design strength; transformed into each space like the fit |
| Idealized paths | `paths=` | `None` | `"idealized_drained"` in `s_t` and `p_q` only |

## 9. Units behavior
Stresses convert (kPa ↔ psf/ksf); φ′ in degrees in both; c′, a and q₀ in display units.

## 10. API
```python
fig, ax, fit = ht.plot.failure_envelope(triaxial, space="mohr", stress="effective", group_by="specimen_id")
fig, ax, fit = ht.plot.failure_envelope(triaxial[triaxial.geology_unit == "Till"], space="s_t")
fig, ax, fit = ht.plot.failure_envelope(triaxial, space="s_t", paths="idealized_drained")
```
Signature: `failure_envelope(df, *, space="mohr", stress="effective", paths=None, fit=True, cohesion=None, group_by=None, result_box=True, envelopes=None, ax=None, display_units=None) -> (fig, ax, fit)`.

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| σ′1 < σ′3 | Error naming the rows |
| Negative σ′3 | Drawn; warning (tension) |
| One specimen | Drawn; no fit unless `cohesion=0` |
| Mixed total and effective | Error (`stress=` picks one) |
| `paths="idealized_drained"` and `test_type` is CU or UU | Error: the idealized path is for drained tests at constant cell pressure and would mislead |
| `paths="idealized_drained"` with no `test_type` | Drawn, labeled "Idealized drained path (assumed CD)" |
| `paths=` with `space="mohr"` | Error: paths are drawn in s′–t or p′–q |

## 12. Acceptance criteria and tests
- **Golden, c′ > 0:** σ′3 = 100, σ′1 = 300 and σ′3 = 200, σ′1 = 500 kPa → s′ = 200, 350; t = 100, 150; tan α = 1/3, a = 33.33 kPa; **φ′ = 19.47°, c′ = 35.36 kPa**; the line is tangent to both circles (distance from each center = radius).
- **The intercept depends on the space** (checked on the rendered line, same data): `mohr` crosses τ at c′ = 35.36; `s_t` crosses t at a = 33.33; `p_q` crosses q at q₀ = 75.00 with M = 0.75 (p′ = 166.67, 300; q = 200, 300 lie on it).
- **Golden, c′ = 0:** σ′3 = 100, σ′1 = 300 and σ′3 = 200, σ′1 = 600 kPa → s′ = 200, 400; t = 100, 200; tan α = 0.5, a = 0; **φ′ = 30°, c′ = 0**; M = 1.2, q₀ = 0. `cohesion=0` gives the same result.
- Idealized path of σ′3 = 100, σ′1 = 300: (100, 0) to (200, 100) in s′–t; (100, 0) to (166.67, 200) in p′–q.
- Equal aspect verified on the rendered axes in all three spaces.

## 13. References
- Lambe, T.W. (1967). Stress path method. *J. Soil Mech. Found. Div.* 93(SM6), 309–331.
- Lambe, T.W. & Whitman, R.V. (1969). *Soil Mechanics*. Wiley. (s′–t / stress path method.)
- ASTM D4767 (CU), D7181 (CD), D2850 (UU).

## 14. Open questions
- One fit per unit across samples or one per sample by default? Both are used; `group_by=` decides. What `fit` is returned when there are several groups (a list, or a table of results)?
- Is `space="mohr"` the right default? It's the figure most reports show.

**Pitfalls:**
- Computing c′ as a / cos(slope), using tan α where cos φ′ belongs. The golden test catches it.
- Drawing a (the s′–t intercept) as c′, or c′ on the s′–t axis. The intercept test catches it.
- Refitting in p′–q instead of transforming the s′–t fit.
- Drawing idealized paths without saying so.
- Forcing the line through the origin whenever the intercept comes out negative, without saying so.
- Rounding c′ and φ′ inside the analysis; round only for display.

## 15. Future enhancements
- Two-panel layout (Mohr and s′–t sharing one fit).
- Extension tests (negative q, M for extension).
- Curved (power-law) envelopes; peak vs critical-state envelopes.
