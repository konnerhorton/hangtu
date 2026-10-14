# P12 — Triaxial shearing: stress–strain curves and measured stress paths (draft notes)

| | |
|---|---|
| **ID / function** | P12 · `ht.plot.triaxial_shearing()` |
| **Status** | idea (draft notes) |
| **Type** | plot + light analysis |
| **Target version** | Later (needs a source of readings) |
| **Depends on** | P00, P11's `mohr_coulomb_fit` |
| **Related** | P11 |

---

## 1. Purpose
Shows how each specimen behaved during shearing, from readings at each strain step. Merged from the former P10 (stress–strain curves) and P12 (measured stress paths), because both draw the same readings. One function, two kinds of view chosen with `space=`:
- `"stress_strain"`: deviator stress against axial strain, with pore pressure (CU) or volumetric strain (CD).
- `"s_t"` or `"p_q"`: the measured stress path, with the failure envelope from P11.

Answers: did the specimens contract or dilate, how did pore pressure develop, where did they fail and by which criterion, and does a single envelope fit.

**Why it's later.** AGS carries only the stresses at failure (to verify against the 4.2 dictionary). Readings usually arrive as exports from the lab's software. P11 covers the failure points, with idealized drained paths, and is likely the most common case.

## 2. Reference figure
`space="s_t"`:
```
   t (kPa)
  200 ┤                    ___●  ← failure
      │                 _-‾  ·
  100 ┤          ___●‾    ·· ← K_f line (P11 fit)
      │       _-‾   ·  ·
      │    ╱  ← measured path (CU, contractive, then dilating)
    0 ┼───●──────●──────────────
      0   100  200  300  400   s′ (kPa)
```

`space="stress_strain"`:
```
   q (kPa)
  300 ┤        ___●‾‾‾‾‾‾‾‾‾‾‾  ← deviator stress, failure marked
      │     _-‾
  150 ┤   ╱      ......... ← pore pressure
      │  ╱  ...‾‾
    0 ┼─●───────────────────────
      0     5     10     15    20   axial strain (%)
```

## 3. Input data
**Row grain:** one row per reading: `specimen_id`, axial strain, deviator stress, pore pressure, cell pressure, and volumetric strain for drained tests. Column names to be proposed against the registry.

**Source:** not decided. Options: a CSV template like the Phase 1 ones, a reader for common lab software exports, or a user-defined AGS group if one becomes common.

## 4. Analysis / calculations
- Per reading: σ′3 = σ3 − u, σ′1 = σ′3 + q; then s′, t (or p′, q) as P11 §4.
- Failure point per specimen: by the failure criterion (`failure_criterion="max_deviator_stress"` or `"max_stress_ratio"`), marked in every view so they agree.
- Envelope: P11's `mohr_coulomb_fit` on the failure points, drawn as P11 §4.

## 5. Figure layout
Single panel, `default` size. In `stress_strain`, pore pressure (or volumetric strain) goes on a second y axis; whether that's clear enough, or needs a second panel, is open (§14).

## 6. Axes
| Space | X axis | Y axis |
|---|---|---|
| `stress_strain` | `Axial strain, ε_a (%)` | `Deviator stress, q (kPa)`; second axis `Pore pressure, u (kPa)` or `Volumetric strain, ε_v (%)` |
| `s_t`, `p_q` | as P11 §6 | as P11 §6 |

Equal aspect required in `s_t` and `p_q` (as P11); not in `stress_strain`. Limits from 0, or negative q for extension.

## 7. Data marks
| Series | Mark | Notes |
|---|---|---|
| Curve / path | solid line per specimen | color by specimen or unit |
| Pore pressure / volumetric strain (`stress_strain`) | dashed line, same color | |
| Failure point | filled dot | same criterion in every view |
| K_f line (`s_t`, `p_q`) | black line, labeled with c′, φ′ | from P11 |

## 8. Overlays and annotations
`fit=`, `result_box=`, `envelopes=` as P11, in `s_t` and `p_q`.

## 9. Units behavior
Stresses convert; strains in percent; φ′ in degrees.

## 10. API
`triaxial_shearing(df, *, space="stress_strain", failure_criterion="max_deviator_stress", fit=True, ...) -> (fig, ax, fit)`. To be settled with the data source.

## 11. Edge cases and data quality
To be written when the data source is decided.

## 12. Acceptance criteria and tests
- Failure points and envelope match P11's goldens when the readings end at P11's failure stresses.
- The failure point is the same reading in every view.

## 13. References
- Lambe, T.W. (1967). Stress path method. *J. Soil Mech. Found. Div.* 93(SM6), 309–331.
- ASTM D4767 (CU), D7181 (CD).

## 14. Open questions
- Where readings come from (§3).
- `stress_strain`: second y axis or a second panel for pore pressure? A second panel breaks the `(fig, ax)` contract.

**Pitfalls:**
- Picking the failure point by a different criterion than the lab reported, so P11 and P12 disagree on the same specimen.
- Plotting total pore pressure where excess pore pressure is meant, or the reverse; label which.

## 15. Future enhancements
- Total and effective paths together for CU tests; extension tests.
