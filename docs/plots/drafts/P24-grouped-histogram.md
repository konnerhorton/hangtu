# P24 (proposed) — Property histogram by group

| | |
|---|---|
| **ID / function** | P24 (proposed ID) · `ht.plot.histogram()` |
| **Status** | idea (draft notes) |
| **Type** | plot |
| **Target version** | open: v0.1 as a plain plot, or v0.3 folded into P08 |
| **Depends on** | P00; P01 presets |
| **Related** | P07 (same question as percentile bars), P08 (histogram + fitted PDF), P27 |

---

## 1. Purpose
Shows the distribution of one property, split by geology unit (or any group). Answers: what is the spread and shape of w (or LL, PL, PI, γ…) in each unit, and do units overlap. P07 answers "how do units compare" with bars; the histogram shows the shape (skew, bimodality) that bars hide.

A typical page shows four side by side (w, LL, PL, PI) as a first look at the index data.

## 2. Reference figure
Small multiples by default:
```
  Unit A  n=120 │   ▂▅█▇▃▁
  Unit B  n=86  │       ▁▃▆█▅▂
  Unit C  n=14  │  ▃█▃
                └──┬────┬────┬────┬──
                  10   20   30   40   Water content, w (%)
```
Overlaid translucent bars become unreadable beyond two groups; step outlines (`layout="overlay"`) are the overlay option.

## 3. Input data
**Row grain:** one row per observation (as P01/P07).

| Column | Req.? | Notes |
|---|---|---|
| *`value`* | ✔ | Any numeric registry column; the preset sets label and log scale |
| `geology_unit` (or `group_by=` column) | – | One histogram per group |
| `qualifier`, `non_plastic` | – | Counted, not binned (as P07) |

One call per property on the registry's wide columns, or `histograms()` for a grid, like P07's `geology_unit_comparisons`.

## 4. Analysis / calculations
- Bins shared across groups so shapes compare: `bins=` (number, edges or a NumPy rule; default `"auto"` over all data). On a log axis, bins equal in log space.
- `normalize="percent"` (default: % of the group's n), `"count"`, or `"density"`.

## 5. Figure layout
- `layout="stacked"` (default): one row per group, shared x, ordered as P07.
- `layout="overlay"`: one axes, step outlines per group.
- `histograms()`: one panel per property in a grid, like P07's grid.

## 6. Axes
| | X | Y |
|---|---|---|
| Quantity | value | percent of the group (or count) |
| Label | preset/registry label | `Percent of unit (%)` |
| Limits | P00 §8 over all data | per row, 0 to max (or shared with `sharey=True`) |

## 7. Data marks
Bars in the group color (stacked layout), or step lines (overlay). n per group in the row label.

## 8. Overlays and annotations
`reference_lines=`, `note=`, exclusion footnote (≤ 0 on log, qualified, NP). Fitted PDFs belong to P08.

## 9. Units behavior
As P01/P07: values convert; bins are computed after conversion.

## 10. API
`histogram(df, value, *, group_by="geology_unit", bins="auto", normalize="percent", layout="stacked", ...) -> (fig, axs)`.

## 11. Edge cases and data quality
- A group with 1 value: one bar; n shown.
- All values equal: a single bin centered on the value.

## 12. Acceptance criteria and tests
- Percentages per group sum to 100 (excluding counted exclusions).
- Shared bin edges across groups.

## 13. References
- Freedman, D. & Diaconis, P. (1981). On the histogram as a density estimator. *Z. Wahrscheinlichkeitstheorie* 57. (NumPy `"fd"` rule.)

## 14. Open questions
- Standalone v0.1 plot, or only the histogram panel of P08 (v0.3)? A quick look at w, LL, PL and PI per unit is an early need, which argues for v0.1.

**Pitfalls:**
- Separate bins per group, which makes shapes look different when they aren't.
- Translucent overlaid bars for more than two groups.

## 15. Future enhancements
- Kernel density outline as an alternative to bars.
