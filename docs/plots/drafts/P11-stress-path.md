# P11 — Stress paths (draft notes)

| | |
|---|---|
| **ID / function** | P11 · `ht.plot.stress_path()` |
| **Status** | idea (draft notes) |
| **Type** | plot + analysis (shares the fit with P12) |
| **Target version** | v0.5 |
| **Depends on** | P00, P12's `mohr_coulomb_fit` |
| **Related** | P10, P12 |

---

## 1. Purpose
Shows how each specimen's stress state moved to failure in s′–t (MIT) or p′–q (Cambridge) space, with the failure envelope. Answers: did the specimens dilate or contract, where did they fail, and does a single envelope fit.

**When only failure stresses are available** (common in summary tables), the figure can still show each specimen's *idealized drained* path: a 45° line in s′–t from (σ′3, 0) to the failure point (s′, t), which is the path of a CD compression test at constant cell pressure. It's a useful fallback, but it isn't the measured path and must be labeled as such.

## 2. Reference figure
```
   t (kPa)
  200 ┤                      ● ← failure
      │                  ╱  ·
  100 ┤           ●   ╱ ·· ← fitted K_f line
      │       ╱  ·  ╱
      │   ╱ ··   ╱
    0 ┼╱────────╱──────────────
      0   100  200  300  400   s′ (kPa)
```

## 3. Input data
Two shapes:

**Measured paths** (P10 data): one row per reading — `specimen_id`, axial strain, deviator stress, pore pressure, cell pressure. Defined by P10's spec.

**Failure points only:** one row per specimen with σ′3 and σ′1 at failure (proposed names as in P12 §3).

## 4. Analysis / calculations
- s′ = (σ′1 + σ′3)/2, t = (σ′1 − σ′3)/2; p′ = (σ′1 + 2σ′3)/3, q = σ′1 − σ′3.
- **Idealized path** (`path="idealized_drained"`): from (σ′3, 0) to (s′, t) — slope 1 in s′–t, 3 in p′–q.
- **K_f line:** t = a + s′ tan α, then sin φ′ = tan α and c′ = a / cos φ′ (P12 §4).

## 5. Figure layout
Single panel, `default` size.

## 6. Axes
| | X axis | Y axis |
|---|---|---|
| s′–t | `Mean effective stress, s′ (kPa)` | `Deviator stress, t (kPa)` |
| p′–q | `Mean effective stress, p′ (kPa)` | `Deviator stress, q (kPa)` |
| Limits | from 0 | from 0 (or negative for extension) |

**Range constraints:** [x] equal aspect for s′–t (README); p′–q not required.

## 7. Data marks
| Series | Mark | Notes |
|---|---|---|
| Path | line per specimen | dashed when idealized, solid when measured; legend says which |
| Failure point | filled dot | |
| K_f line | black line, labeled with c′, φ′ | |

## 8. Overlays and annotations
`fit=` (on with ≥ 2 specimens), `result_box=`, `envelopes=` as P12.

## 9. Units behavior
Stresses convert; φ′ in degrees.

## 10. API
`stress_path(df, *, space="s_t", path="measured" | "idealized_drained", fit=True, ...) -> (fig, ax, result)`.

## 11. Edge cases and data quality
Idealized paths for a test that wasn't drained at constant cell pressure (CU, UU) would mislead: if `test_type` says CU or UU, error saying the idealized path doesn't apply.

## 12. Acceptance criteria and tests
- Golden as P12 §12 (φ′ = 19.47°, c′ = 35.36 kPa).
- Idealized path of σ′3 = 100, σ′1 = 300 runs from (100, 0) to (200, 100).

## 13. References
- Lambe, T.W. (1967). Stress path method. *J. Soil Mech. Found. Div.* 93(SM6), 309–331.

## 14. Open questions
- Is the idealized-path fallback worth keeping, given P12 shows the same failure points?

**Pitfalls:**
- Computing c′ as a / cos(slope), using tan α where cos φ′ belongs. The golden test catches it.
- Drawing idealized paths without saying so.

## 15. Future enhancements
- Extension tests; total and effective paths together for CU tests.
