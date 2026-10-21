# P28 (proposed) — Undrained shear strength from SPT (Sowers)

| | |
|---|---|
| **ID / function** | P28 (proposed ID) · `ht.plot.spt_strength_chart()` (+ `ht.analysis.correlations.sowers_1979()`) |
| **Status** | idea (draft notes) |
| **Type** | reference chart + analysis (correlation); results drawn with P07 or P01 |
| **Milestone** | correlation M13 (analysis draft §4); reference chart open |
| **Depends on** | P00; P02 data; P07/P01 for the results |
| **Related** | Cross-cutting finding 2 |

---

## 1. Purpose
Two parts:
1. **Reference chart:** Sowers' chart of s_u against N for three soil classes (CH, CL, SC-ML), as wedges from the origin. Shows the correlation and its spread; with data overlaid, it compares measured s_u with SPT N where both exist.
2. **Correlation:** s_u (min and max) per SPT test from N and the USCS class, summarized per unit with P07, or against depth with P01.

## 2. Reference figure
```
  s_u (kPa)
  600 ┤                          ╱ CH
      │                      ╱ ╱
  400 ┤                  ╱ ╱  ╱ CL
      │              ╱ ╱  ╱ ╱
  200 ┤          ╱ ╱ ╱ ╱  ╱── SC-ML
      │      ╱╱╱╱╱──────
    0 ┼──┬────┬────┬────┬────┬────┤
      0  10   20   30   40   50   60   SPT N
```
Each class is a band between two lines through the origin, hatched, labeled.

## 3. Input data
**Row grain:** one row per SPT test.

| Column | Req.? | Notes |
|---|---|---|
| `spt_n` | ✔ | Sowers (1979) predates energy correction; which N to use is §14 |
| *proposed* `uscs_symbol` | ✔ for the correlation | From lab classification or field descriptions |
| `geology_unit`, `depth`/`elevation` | – | for P07/P01 |
| `undrained_shear_strength` | – | to overlay measured s_u on the chart (pairs at the same depth) |

## 4. Analysis / calculations
- s_u = k × N, with k in kgf/cm² per blow (values read off Sowers' chart, to verify):

  | Class | k min | k max |
  |---|---|---|
  | CH | 0.102 | 0.173 |
  | CL | 0.051 | 0.102 |
  | SC-ML | 0.026 | 0.051 |

  1 kgf/cm² = 98.0665 kPa. The constants are stored in the source unit and converted with pint, so the citation stays in kgf/cm².
- USCS → class: CH → CH; CL → CL; SC, ML, SC-ML → SC-ML; anything else → no estimate, counted.
- **Range:** the chart covers N 0–60. N > 60 → no estimate, counted "outside the correlation range".
- Refusals: no estimate, counted.

## 5. Figure layout
Chart: one panel, portrait. Results: P07 or P01.

## 6. Axes
| | X | Y |
|---|---|---|
| Quantity | SPT N | s_u |
| Label | `SPT N` | `Undrained shear strength, s_u (kPa)` / `(psf)` |
| Limits | fixed 0–60 | fixed: the CH maximum at N = 60 (≈ 1,018 kPa), or a lower limit with the wedge clipped and marked (§14) |

## 7. Data marks
Wedges: gray fill with a hatch per class, black edges, labeled. Optional overlay: measured (N, s_u) pairs colored by unit.

## 8. Overlays and annotations
`data=` overlay of measured pairs; `note=`; citation note in the corner.

## 9. Units behavior
One chart: the y-axis follows `display_units` (kPa / psf). The original kgf/cm² version is available with `display_units={"undrained_shear_strength": "kgf/cm2"}` if pint supports it.

## 10. API
```python
fig, ax = ht.plot.spt_strength_chart(data=paired)                  # reference chart, optional data
est = ht.analysis.correlations.sowers_1979(spt, n="spt_n")          # adds s_u min/max (long, with `method`)
fig, ax = ht.plot.geology_unit_comparison(est, "undrained_shear_strength")
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| N > 60 | No estimate; counted |
| No USCS symbol | No estimate; counted. The user may pass `uscs_by_unit={unit: symbol}` to assign one per unit |
| Coarse-grained symbol (SP, GW…) | No estimate; counted |

## 12. Acceptance criteria and tests
- Golden: N = 20, CL → s_u = 1.02–2.04 kgf/cm² = 100.0–200.1 kPa. N = 10, CH → 1.02–1.73 kgf/cm² = 100.0–169.7 kPa.
- N = 61 → NaN and a count of 1.

## 13. References
- Sowers, G.F. (1979). *Introductory Soil Mechanics and Foundations: Geotechnical Engineering*, 4th ed. Macmillan.

## 14. Open questions
- N or N60? Sowers used N from the hammers of the time; most practice applies it to field N. Should `n=` default to `spt_n` with a note?
- Fixed y-limit: show the full CH wedge (≈ 1,020 kPa at N = 60), or clip at a lower value (e.g. 600 kPa) and mark the clipping?
- Verify the k values against Sowers' figure.
- `uscs_symbol` is a new name; "USCS" is unambiguous in geotechnical work but must be added to CLAUDE.md's accepted short forms if used.

**Pitfalls:**
- Clipping N > 60 to 60 before applying the correlation: it silently reports s_u at N = 60 for every stiffer test.
- A hard-coded unit → USCS fallback map; make it an explicit argument.
- Two copies of the chart for two unit systems; use display units.

## 15. Future enhancements
- Other N–s_u correlations (Terzaghi & Peck; Stroud 1974 f1 × N) in the same module and chart.
