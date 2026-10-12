# P25 (proposed) — Size fractions by geology unit

| | |
|---|---|
| **ID / function** | P25 (proposed ID) · `ht.plot.size_fractions()` (+ fractions from `ht.analysis.gradation()`) |
| **Status** | idea (draft notes) |
| **Type** | plot (+ fractions from the P05 analysis) |
| **Target version** | v0.1, with P05 (M4) |
| **Depends on** | P00, P05 analysis (fraction systems), P07 (summary marks) |
| **Related** | P05, P07 |

---

## 1. Purpose
Summarizes the gradation of many specimens at once: % gravel, sand, silt, clay and fines, per unit. Answers: what is each unit made of, and how variable is it, without drawing hundreds of curves.

## 2. Reference figure
Fractions across, units as colored groups within each fraction:
```
  %
 100┤
    │        ┬               ┬
  50┤   ┬   ┌┴┐  ┬     ┬    ┌┴┐  ┬         ■ Unit A
    │  ┌┴┐  │■│ ┌┴┐   ┌┴┐   │▒│ ┌┴┐        ▒ Unit B
   0┼──┴■┴──┴─┴─┴▒┴───┴■┴───┴─┴─┴▒┴──
      Gravel     Sand       Silt      Clay   Fines
```
Alternative (P07 grid): one panel per fraction, units as rows. Reuses P07 entirely; see §14.

## 3. Input data
Either:
- **Curves** (the `grain_size` template): fractions computed per specimen by the P05 analysis with the chosen system; or
- **Fractions per specimen** (one row per specimen), proposed columns `gravel_fraction`, `sand_fraction`, `silt_fraction`, `clay_fraction`, `fines_fraction` (percent; names to check against the registry), e.g. as reported by a lab.

`geology_unit` for grouping; `specimen_id` to label.

## 4. Analysis / calculations
- Fractions from the curve: passing at the system's boundaries (e.g. USCS: gravel = 100 − P(4.75 mm); sand = P(4.75) − P(0.075); fines = P(0.075)). Log-linear interpolation (P05).
- Lab-reported fractions may use a different system (AGS GRAG uses ISO boundaries); Phase 2 always recomputes from the curve (analysis draft §3). With user-supplied fractions, the user declares the system (`system=`, a label only).
- Summary: P07's percentiles (default p10–p50–p90) or Tukey boxes, with all points drawn.

## 5. Figure layout
Single panel; `default` size, landscape. Or the P07 grid.

## 6. Axes
| | X | Y |
|---|---|---|
| Quantity | fraction (categorical, coarse to fine) | percent |
| Label | fraction names with boundaries ("Sand\n0.075–4.75 mm") | `Percent by mass (%)` |
| Limits | — | fixed 0–100 |

## 7. Data marks
Per fraction × unit: jittered points + summary (P07 marks, vertical). Unit colors.

## 8. Overlays and annotations
`ranges=` per fraction and unit (e.g. a GBR's stated gradation), as P07's baseline. Note stating the fraction system.

## 9. Units behavior
Nothing converts; boundaries in mm in both systems.

## 10. API
`size_fractions(df, *, system="astm_uscs", fractions=("gravel", "sand", "fines"), summary="box", ...) -> (fig, ax)`.

## 11. Edge cases and data quality
- Fractions of a specimen not summing to 100 (user-supplied): warning naming the specimen.
- Curve not reaching a boundary (sieve-only test, no hydrometer): silt and clay not computed; fines still are; counted.

## 12. Acceptance criteria and tests
- Golden: P(4.75) = 80, P(0.075) = 25 → gravel 20, sand 55, fines 25.

## 13. References
- ASTM D2487-17; ISO 14688-1:2017.

## 14. Open questions
- New plot, or a P07 grid with fraction columns? A P07 grid needs nothing new except the fraction columns; this plot's only gain is all fractions on one axis.
- Silt and clay are not USCS fractions; show them only for systems that define them?

**Pitfalls:**
- Mixing fractions from different systems (lab-reported ISO with USCS curves) without saying so.

## 15. Future enhancements
- Ternary diagram (sand–silt–clay).
