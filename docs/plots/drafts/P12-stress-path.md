# P12 — Measured stress paths (draft notes)

| | |
|---|---|
| **ID / function** | P12 · `ht.plot.stress_path()` |
| **Status** | idea (draft notes) |
| **Type** | plot + light analysis |
| **Target version** | Later (needs a source of readings) |
| **Depends on** | P00, P10 (same readings data), P11's `mohr_coulomb_fit` |
| **Related** | P10, P11 |

---

## 1. Purpose
Shows how each specimen's stress state moved during shearing, in s′–t (MIT) or p′–q (Cambridge) space, with the failure envelope from P11. Answers: did the specimens dilate or contract, how did pore pressure develop, where did they fail, and does a single envelope fit.

**Why it's later.** It needs readings at each strain step. AGS carries only the stresses at failure (to verify against the 4.2 dictionary); readings usually arrive as exports from the lab's software. P11 covers the failure points, with idealized drained paths, and is likely the most common case. P10 (stress–strain curves) needs the same readings data, and the two should share its source when it exists.

## 2. Reference figure
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

## 3. Input data
**Row grain:** one row per reading: `specimen_id`, axial strain, deviator stress, pore pressure, cell pressure. Column names to be proposed with P10, against the registry.

**Source:** not decided. Options: a CSV template like the Phase 1 ones, a reader for common lab software exports, or a user-defined AGS group if one becomes common. Decide with P10.

## 4. Analysis / calculations
- Per reading: σ′3 = σ3 − u, σ′1 = σ′3 + q; then s′, t (or p′, q) as P11 §4.
- Failure point per specimen: by the failure criterion (maximum deviator stress or maximum stress ratio), shared with P10.
- Envelope: P11's `mohr_coulomb_fit` on the failure points, drawn as P11 §4.

## 5. Figure layout
Single panel, `default` size.

## 6. Axes
As P11 §6 for `s_t` and `p_q`. Limits from 0, or negative q for extension. Equal aspect required in both.

## 7. Data marks
| Series | Mark | Notes |
|---|---|---|
| Path | solid line per specimen | color by specimen or unit |
| Failure point | filled dot | |
| K_f line | black line, labeled with c′, φ′ | from P11 |

## 8. Overlays and annotations
`fit=`, `result_box=`, `envelopes=` as P11.

## 9. Units behavior
Stresses convert; φ′ in degrees.

## 10. API
`stress_path(df, *, space="s_t", failure_criterion=..., fit=True, ...) -> (fig, ax, fit)`. To be settled with P10.

## 11. Edge cases and data quality
To be written when the data source is decided.

## 12. Acceptance criteria and tests
- Failure points and envelope match P11's goldens when the readings end at P11's failure stresses.

## 13. References
- Lambe, T.W. (1967). Stress path method. *J. Soil Mech. Found. Div.* 93(SM6), 309–331.

## 14. Open questions
- Where readings come from (§3), shared with P10.

**Pitfalls:**
- Picking the failure point by a different criterion than the lab reported, so P11 and P12 disagree on the same specimen.

## 15. Future enhancements
- Total and effective paths together for CU tests; extension tests.
