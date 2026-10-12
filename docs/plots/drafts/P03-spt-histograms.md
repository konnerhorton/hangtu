# P03 — SPT qualitative histograms (draft notes)

| | |
|---|---|
| **ID / function** | P03 · `ht.plot.spt_histogram()`, `ht.plot.spt_histograms()` (+ `ht.analysis.spt_class()`) |
| **Status** | idea (draft notes) |
| **Type** | plot + classification |
| **Target version** | v0.1 (milestone M3) |
| **Depends on** | P00 |
| **Related** | `docs/drafts/analysis.md` §1, TODO #3 (`soil_class`), TODO #4 (class tables). P02 |

---

## 1. Purpose
Shows what share of SPT tests in each unit falls in each density (cohesionless) or consistency (cohesive) class. It's how a GIR summarizes "Unit B is predominantly dense to very dense". Reviewers read it next to the N profile (P02).

## 2. Reference figure
```
  % of tests
  60 ┤            ▒▒
     │      ██    ▒▒                    █ Unit A (n = 84)
  40 ┤      ██ ▒▒ ▒▒ ██                 ▒ Unit B (n = 132)
     │   ██ ██ ▒▒ ▒▒ ██ ▒▒
  20 ┤▒▒ ██ ██ ▒▒ ▒▒ ██ ▒▒ ██ ▒▒
     ├──────┬──────┬──────┬──────┬──────┬──────
      V.loose Loose Medium Dense V.dense Refusal
       0–4    4–10  10–30 30–50  >50
```
Grouped (side-by-side) bars, not overlaid translucent bars: overlaid bars hide each other beyond two units.

## 3. Input data
**Row grain:** one row per SPT test (the `spt` template).

| Column | Description | Quantity kind | Canonical unit | Req.? | Notes |
|---|---|---|---|---|---|
| `spt_n` / `spt_n60` / `spt_n_capped` | Value classified | count | — | ✔ one | Default N60 per draft analysis §1 (to confirm, TODO #4) |
| `spt_refusal` | Refusal flag | bool | — | – | Own bar, "Refusal" |
| `geology_unit` | Grouping | — | — | – | One bar per unit per class |
| `soil_class` | Cohesive / cohesionless | — | — | – | Picks the class table (TODO #3) |

**Value flags handled:** refusal → its own category. Blank N → counted in a note, not a category.

**Minimum data:** ≥ 1 test.

## 4. Analysis / calculations
- **Class tables** (from config, TODO #4):
  - cohesionless (relative density): very loose 0–4, loose 4–10, medium dense 10–30, dense 30–50, very dense > 50;
  - cohesive (consistency): very soft < 2, soft 2–4, medium stiff 4–8, stiff 8–15, very stiff 15–30, hard > 30.
- **Boundary convention:** lower bound inclusive (draft; TODO #4).
- **Percent:** count in class / count in the unit × 100.
- **Refusal:** counted from `spt_refusal`, not inferred from N.

## 5. Figure layout
- `spt_histogram()`: one panel, one class table.
- `spt_histograms()`: two panels (cohesionless, cohesive), split by `soil_class` or by two filtered DataFrames (decided: two histograms, analysis draft §1).
- Default size: `default` (6.5 × 4.5 in) for one panel.

## 6. Axes
| | X axis | Y axis |
|---|---|---|
| Quantity | class (categorical, in table order) + "Refusal" | percent of tests in the unit |
| Label | class names with ranges on two lines ("Dense\n30–50") | `Tests in unit (%)` |
| Limits | — | 0 to a nice number ≥ the tallest bar |
| Gridlines | none | horizontal, major |

## 7. Data marks
| Series | Mark | Color by | Legend entry |
|---|---|---|---|
| Class share | grouped bars | `geology_unit` | ✔ "Unit A (n = 84)" |
| Refusal | bar in the "Refusal" slot, hatched | unit color | ✔ shared hatch entry |

## 8. Overlays and annotations
| Overlay | Argument | Default | Notes |
|---|---|---|---|
| Counts on bars | `bar_labels=` | off | n above each bar |
| Note | `note=` | off | |
| Exclusion note | automatic | on | blank N, and (with `n="spt_n60"`) rows with no ER |

## 9. Units behavior
Nothing converts. The x-axis title names the value classified (N or N60).

## 10. API
At M3. Expected: `spt_histogram(df, *, n="spt_n60", table="cohesionless", color_by="geology_unit", ...) -> (fig, ax)`.

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| N = 0 | Very loose / very soft |
| N exactly on a boundary | Lower bound inclusive (to confirm) |
| A unit with no tests | No bars; listed in a note if the user passed it in `order=` |
| Refusal with a numeric N | Counted as refusal only (one category per test) |

## 12. Acceptance criteria and tests
- Golden: N = [0, 4, 10, 29, 30, 50, 51], lower bound inclusive → very loose 1 (0), loose 1 (4), medium dense 2 (10, 29), dense 1 (30), very dense 2 (50, 51); total 7.
- Every test lands in exactly one category (sum of counts = n).

## 13. References
- Terzaghi, K. & Peck, R.B. (1948). *Soil Mechanics in Engineering Practice*. Wiley.
- Peck, R.B., Hanson, W.E. & Thornburn, T.H. (1974). *Foundation Engineering*, 2nd ed. Wiley.

## 14. Open questions
- TODO #3 and #4 as they stand.

**Pitfalls:**
- `pd.cut` bins are right-closed by default: `(0, 4], (4, 10], …` **drops N = 0** and puts N = 4 in "very loose". The golden test above catches it (pandas' default gives a total of 6).
- Applying the relative-density table to every soil, cohesive units included.
- Inferring refusal from a large N instead of the flag.

## 15. Future enhancements
- Stacked 100% bars (one bar per unit), a compact alternative when there are many units.
