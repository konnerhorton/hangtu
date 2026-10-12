# P27 (proposed) — Data against a published distribution, per unit

| | |
|---|---|
| **ID / function** | P27 (proposed ID) · `ht.plot.distribution_comparison()` |
| **Status** | idea (draft notes) |
| **Type** | plot (+ summary statistics) |
| **Target version** | v0.3, alongside P08 |
| **Depends on** | P24 (histogram), P08 (PDF drawing), P07 (baseline table) |
| **Related** | P07 (same question with percentile bars), TODO #8 (bounded data) |

---

## 1. Purpose
Compares a project's measured distribution of a property in each unit with a distribution published for the same unit (mean, standard deviation, min, max), e.g. regional statistics for a named formation. Answers: is this site's Unit B like the regional Unit B, or stronger, weaker, wetter? Typical properties: w, unit weight, c′, φ′.

P07 asks the same question with a report's range; P27 adds the shape: the histogram against the published curve.

## 2. Reference figure
One panel per unit (grid, two columns):
```
  Unit B — Water content, w (%)
  %  ┤        ▃█▅                  ┌──────────────────────┐
     │      ▂▆███▆▂    ╭─╮         │ Published: mean 18.9 │
     │    ▁▄███████▃ ╭╯  ╰╮        │            s.d. 4.2  │
     │  ▁▃█████████▅╯ ── ╰╮       │ Project:   mean 16.2 │
     │ ▁███████████████▃▁  ╰─      │ (n = 86)   s.d. 3.9  │
     └─────────────────────────    └──────────────────────┘
       10      20      30
```

## 3. Input data
**Data:** one row per observation (P07 shape): `value` column, `geology_unit`.

**Published statistics** (a user table, extending P07's baseline; proposed fields to check against the registry and P07's `fields:`):

| Field | Req.? | Notes |
|---|---|---|
| `geology_unit` | ✔ | |
| `property` | when > 1 property | as P07 |
| `mean` | ✔ | |
| `standard_deviation` | ✔ | |
| `low`, `high` | – | Published min and max; the curve is drawn only between them |
| `source` | – | citation |

## 4. Analysis / calculations
- Project statistics per unit: n, mean, standard deviation (sample, ddof = 1), in display units.
- **Published curve scaled to the histogram:** for `normalize="percent"`, y = 100 × bin width × f(x); for `"count"`, y = n × bin width × f(x); for `"density"`, y = f(x). f is the normal PDF; truncated to [low, high] if given (whether to renormalize the truncated curve is TODO #8).

## 5. Figure layout
One panel per unit, grid `columns=2`, shared x by default. Per-panel size as P07's `grid` kind.

## 6. Axes
P24's axes per panel; the unit name as the panel title.

## 7. Data marks
| Series | Mark |
|---|---|
| Project data | histogram bars, unit color |
| Published distribution | black line |
| Means | short vertical ticks at both means (optional) |

## 8. Overlays and annotations
- Stats box (on): published mean and s.d. (with source), project n, mean, s.d.
- Note when a unit has published statistics but no data (empty panel with "n = 0"), and vice versa.

## 9. Units behavior
- Data and published statistics convert to display units (mean and s.d. scale with linear conversions).
- Density and unit weight are different quantities: converting bulk density to unit weight (× g) is an explicit, documented step before plotting (registry: `bulk_unit_weight` is derived from RDEN × g), never done inside the plot.

## 10. API
```python
fig, axs = ht.plot.distribution_comparison(index, "water_content", published=regional, order=[...])
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| s.d. ≤ 0 in the table | Row not drawn; warning naming it |
| Unit in data, not in the table | Histogram only |
| A published row with min > mean or max < mean | Drawn; warning naming it (likely a transcription error) |

## 12. Acceptance criteria and tests
- Golden: bin width 2, percent histogram, N(18.9, 4.2): at x = 18.9, y = 100 × 2 × 0.09499 = 19.0.
- Curve area over the histogram's range ≈ the percent that range covers.

## 13. References
- None specific; published statistics come from the user's source.

## 14. Open questions
- New plot, or an option on P08 (`reference=` distributions per group)?

**Pitfalls:**
- Scaling the PDF by 100 alone to sit on a % histogram: right only when bins are 1 unit wide. Scale by bin width.
- Converting density to unit weight inline with a hard-coded 9.81.
- Trusting transcribed published tables: rows copied from the wrong line (identical numbers across different properties) are easy to miss. The sanity warning in §11 catches some of them.

## 15. Future enhancements
- Lognormal published distributions; Q–Q panel against the published distribution.
