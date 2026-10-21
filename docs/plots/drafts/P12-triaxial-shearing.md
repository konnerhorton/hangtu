# P12 — Triaxial shearing: stress–strain curves and measured stress paths (draft notes)

| | |
|---|---|
| **ID / function** | P12 · `ht.plot.triaxial_shearing()` |
| **Status** | idea (draft notes) |
| **Type** | plot + light analysis |
| **Milestone** | M11 (wave 2) |
| **Depends on** | P00, P11's `mohr_coulomb_fit` |
| **Related** | P11 |

---

## 1. Purpose
Shows how each specimen behaved during shearing, from readings at each strain step. Merged from the former P10 (stress–strain curves) and P12 (measured stress paths), because both draw the same readings. One function, two kinds of view chosen with `space=`:
- `"stress_strain"`: deviator stress against axial strain, with pore pressure (CU) or volumetric strain (CD).
- `"s_t"` or `"p_q"`: the measured stress path, with the failure envelope from P11.

Answers: did the specimens contract or dilate, how did pore pressure develop, where did they fail and by which criterion, and does a single envelope fit.

**Where the readings come from.** AGS carries only the values at failure: TRET and TRIT have one row per test or stage (checked against the 4.1–4.2 dictionaries, 2026-10-15). Readings usually arrive as exports from the lab's software, so the user shapes them into a CSV (§3; decided 2026-10-15). P11 covers the failure points, with idealized drained paths, and is likely the most common case.

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
**Source (decided 2026-10-15):** a CSV the user shapes outside hangtu, from the lab's export. No reader for lab software formats.

**Row grain:** one row per reading. Values that belong to the specimen repeat on each of its rows, so the file is one sheet.

**Minimum columns** (names *proposed*, to check against the registry):

| Column | Per | Unit | Req.? | Notes |
|---|---|---|---|---|
| `specimen_id` | specimen | | ✔ | Groups readings into one curve or path |
| `test_type` | specimen | | ✔ | `UU`, `CU` or `CD`. Picks total or effective stress, and pore pressure or volume change |
| *proposed* `effective_consolidation_stress` | specimen | stress | ✔ CU, CD | σ′3c: cell pressure minus back pressure at the start of shearing (AGS `TRET_CONP`). Where the effective path starts |
| *proposed* `cell_pressure` | specimen | stress | ✔ UU | σ3. UU is total stress only |
| *proposed* `axial_strain` | reading | % | ✔ | |
| *proposed* `deviator_stress` | reading | stress | ✔ | Already corrected for area and membrane. hangtu doesn't redo the lab's corrections |
| *proposed* `excess_pore_pressure` | reading | stress | ✔ CU | Δu from the start of shearing. Asked for as excess, not total, so the two can't be confused |
| *proposed* `volumetric_strain` | reading | % | ✔ CD | Δu = 0 |
| `loca_id`, `depth`, `geology_unit` | specimen | | – | Grouping, labels, a fit per unit |
| *proposed* `failure_point` | reading | bool | – | The lab's failure reading, one per specimen. Without it, `failure_criterion=` picks one |

**Assumptions:** isotropic consolidation and triaxial compression. Anisotropic consolidation (`TRET_CVP`, `TRET_CRP`) and extension are enhancements (§15).

## 4. Analysis / calculations
- Per reading: σ′3 = σ′3c − Δu (Δu = 0 for CD), σ′1 = σ′3 + q; UU uses σ3 and σ1 = σ3 + q in total stress. Then s′, t (or p′, q) as P11 §4.
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
- `stress_strain`: second y axis or a second panel for pore pressure? A second panel breaks the `(fig, ax)` contract.

**Pitfalls:**
- Picking the failure point by a different criterion than the lab reported, so P11 and P12 disagree on the same specimen.
- Plotting total pore pressure where excess pore pressure is meant, or the reverse; label which.

## 15. Future enhancements
- Total and effective paths together for CU tests; extension tests.
