# P26 (proposed) — Drained strength from plasticity index (Sørensen & Okkels)

| | |
|---|---|
| **ID / function** | P26 (proposed ID) · `ht.analysis.correlations.sorensen_okkels_2013()`; drawn with P07 |
| **Status** | idea (draft notes) |
| **Type** | analysis (correlation) + existing plot |
| **Milestone** | not yet placed (open) |
| **Depends on** | P07 (with `group_by=`), P04 data (PI) |
| **Related** | Cross-cutting finding 2 (correlations as analyses) |

---

## 1. Purpose
Estimates φ′ and c′ of clays from PI with the Sørensen & Okkels (2013) correlations, and compares them across units. Answers: what drained strength do the index tests suggest, as a check on (or a stand-in for) triaxial results. Four φ′ estimates (normally/over-consolidated × best estimate/lower bound) per unit, and c′ per unit.

## 2. Reference figure
P07 rows, one per unit × estimate:
```
                         φ′ (degrees)
                     15    20    25    30    35
  Unit A  NC best  │          ├──●──┤
          NC lower │       ├──●──┤
          OC best  │        ├──●──┤
          OC lower │      ├──●──┤
  Unit B  …
```

## 3. Input data
**Row grain:** one row per specimen with PI (the `atterberg` template).

| Column | Req.? | Notes |
|---|---|---|
| `plasticity_index` | ✔ | NP → no estimate, counted |
| `geology_unit` | – | |

**Output columns (proposed, to check):** `effective_friction_angle` and `effective_cohesion`, in a long table with a `method` column (e.g. `"sorensen_okkels_2013_oc_lower"`), so several estimates of one property sit in one column.

## 4. Analysis / calculations
log is base 10, PI in %. Coefficients to verify against the paper (§14):

| Estimate | Range | Formula |
|---|---|---|
| φ′_nc best | (to verify) | 43 − 10 log PI |
| φ′_nc lower | (to verify) | 39 − 11 log PI |
| φ′_oc best | 4 < PI < 50 | 45 − 14 log PI |
| φ′_oc best | 50 ≤ PI < 150 | 26 − 3 log PI |
| φ′_oc lower | 4 < PI < 50 | 44 − 14 log PI |
| φ′_oc lower | 50 ≤ PI < 150 | 30 − 6 log PI |
| c′_oc lower | 7 < PI < 30 | 30 kPa |
| c′_oc lower | 30 ≤ PI ≤ 80 | 48 − 0.6 PI kPa |
| c′_oc lower | PI > 80 | 0 |

Self-checks on the table: lower < best everywhere; at PI = 50 the OC pieces meet (best 45 − 14(1.699) = 21.2° and 26 − 3(1.699) = 20.9°; lower 20.2° and 19.8°); at PI = 30 the c′ pieces meet (48 − 0.6 × 30 = 30 kPa).

- Outside a formula's range → NaN and a count, never extrapolated.
- No rounding in the analysis.
- **Lower bound** ≈ the 5% fractile of the authors' dataset; it's for design checks, not a best estimate.

## 5. Figure layout
P07, with rows for unit × method (needs P07's future `group_by=`). Or one P07 panel per method.

## 6. Axes
P07: x `Effective friction angle, φ′ (degrees)` or `Effective cohesion, c′ (kPa)`.

## 7. Data marks
P07 marks. Color stays with the unit; the method goes in the row label.

## 8. Overlays and annotations
P07 baseline: triaxial results per unit (from P11) could be the "baseline" to compare against.

## 9. Units behavior
φ′ in degrees in both; c′ converts (kPa ↔ psf). The c′ formula is in kPa and is applied in kPa before conversion.

## 10. API
```python
est = ht.analysis.correlations.sorensen_okkels_2013(atterberg, consolidation="overconsolidated", estimate="lower_bound")
fig, ax = ht.plot.geology_unit_comparison(est, "effective_friction_angle")
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| PI ≤ 4 (or ≤ 7 for c′) | NaN, counted "outside correlation range" |
| NP | NaN, counted separately |
| Non-clay units | Computed if PI given; the docstring states the correlation is for clays (OC: clay fraction < 80%) |

## 12. Acceptance criteria and tests
- Golden: PI = 20 → log = 1.301: φ′_nc best 30.0°, lower 24.7°; φ′_oc best 26.8°, lower 25.8°; c′ lower 30 kPa. PI = 60 → log = 1.778: φ′_oc best 20.7°, lower 19.3°; c′ = 12 kPa.
- Lower < best for every PI in range (property test).

## 13. References
- Sørensen, K.K. & Okkels, N. (2013). Correlation between drained shear strength and plasticity index of undisturbed overconsolidated clays. *Proc. 18th ICSMGE*, Paris.

## 14. Open questions
- Validity range of the NC formulas; to read from the paper.
- Verify every coefficient against the paper.

**Pitfalls:**
- **Swapping best estimate and lower bound.** The pairs look alike (43 − 10 log vs 39 − 11 log; 26 − 3 log vs 30 − 6 log), and a swap is easy to miss. The lower < best property test catches it.
- Returning c′ = 0 for 7 < PI < 30 instead of 30 kPa; the continuity check at PI = 30 catches it.
- Rounding φ′ to whole degrees before summarizing.

## 15. Future enhancements
- c′ from s_u (Sørensen & Okkels eq. 13).
