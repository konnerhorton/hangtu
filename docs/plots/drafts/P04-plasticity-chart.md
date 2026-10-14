# P04 — Plasticity chart (draft notes)

| | |
|---|---|
| **ID / function** | P04 · `ht.plot.plasticity_chart()` (+ `ht.analysis.classify_fines()`) |
| **Status** | idea (draft notes) |
| **Type** | plot + classification |
| **Target version** | v0.2 (milestone M8) |
| **Depends on** | P00 |
| **Related** | `docs/drafts/analysis.md` §2, TODO #5 |

---

## 1. Purpose
Places each specimen's LL and PI on the Casagrande chart to classify the fines and compare units. Answers: are the units distinct, does a unit plot where its description says it should, and which specimens look misassigned. In every GIR lab section.

A second use: **project classification regions** (a project's own soil-group definitions in LL–PI space) shaded on the chart, so specimens can be checked against them.

## 2. Reference figure
```
  PI
  60 ┤                               /U       ░ = user region (optional)
     │                        CH or OH/   /A
  40 ┤                     /     ░░░░/
     │                  /    ░░░░ /    MH or OH
  20 ┤      CL or OL /  ● ●░░/ ●
   7 ┤  ▨▨▨CL-ML▨▨ /  ●   /        ML or OL
   4 ┤ ▨▨▨▨▨▨▨▨▨/     /
     ├────┬────┬────┬────┼────┬────┬────┬────┬────┤
     0   10   20   30   40   50   60   70   80  100   LL
```
**A good version:** equal aspect (1 PI = 1 LL on paper, so the A-line slope reads true), lines labeled along the line, zones labeled, NP count noted.

## 3. Input data
**Row grain:** one row per specimen (the `atterberg` template).

| Column | Description | Quantity kind | Unit | Req.? | Valid range | Notes |
|---|---|---|---|---|---|---|
| `liquid_limit` | LL | percent | % | ✔ | ≥ 0 | |
| `plasticity_index` | PI | dimensionless (registry) | — | ✔ (or `plastic_limit`) | 0 ≤ PI ≤ LL | Computed LL − PL if absent |
| `plastic_limit` | PL | percent | % | – | | |
| `non_plastic` | NP flag | bool | | – | | Counted, not drawn |
| `geology_unit` | Color | | | – | | |
| `specimen_id` | Point labels (`labels=True`) | | | – | | |

**Minimum data:** none (an empty chart with its lines is valid, e.g. as a base for `ax=` composition).

## 4. Analysis / calculations
- **Lines (USCS, ASTM D2487):**
  - A-line: PI = 0.73 (LL − 20), drawn from PI = 4 upward; below that, PI = 4 from the PI = LL line to the A-line (LL ≈ 25.5).
  - U-line: vertical at LL = 16 from PI = 0 to PI = 7, then PI = 0.9 (LL − 8).
  - CL-ML hatched zone: 4 ≤ PI ≤ 7 above the A-line.
  - LL = 50 divider (low/high).
  - PI = LL limit line (PI can't exceed LL), as a light line.
- **BS 5930 system:** A-line plus LL bands 35/50/70/90 (analysis draft §2; TODO #5).
- **Classification:** fine-grained symbol from LL/PI (analysis draft §2).

## 5. Figure layout
Single panel. Equal aspect forces a 100 × 60 data box; the figure is sized so the box fills the width (≈ 6.5 × 4.5 in works).

## 6. Axes
| | X axis | Y axis |
|---|---|---|
| Quantity | `liquid_limit` | `plasticity_index` |
| Label | `Liquid limit, LL (%)` | `Plasticity index, PI` |
| Limits | fixed 0–100, extended to a nice number if data exceed it (P00 §9) | fixed 0–60, likewise |
| Ticks | major 10 | major 10 |

**Range constraints:** [x] equal aspect; [x] fixed limits (extendable).

## 7. Data marks
| Series | Mark | Color by | Legend |
|---|---|---|---|
| Specimens | scatter | `geology_unit` | ✔ per unit |
| Out-of-range | edge marker + arrow | unit | count note |
| NP | — | — | note: "12 non-plastic specimens not plotted" |

## 8. Overlays and annotations
| Overlay | Argument | Default | Source | Notes |
|---|---|---|---|---|
| A-line, U-line, CL-ML zone, LL = 50 | `system="uscs"` | on | ASTM D2487; config | Labels rotated to match the line's slope on screen |
| Zone labels | `zone_labels=` | on | config | CL or OL, CH or OH, ML or OL, MH or OH, CL-ML |
| User regions | `regions=` | off | user table (`region`, vertices in `liquid_limit`, `plasticity_index`, optional `color`) | v0.4 roadmap item "plasticity-chart data region" |
| Specimen labels | `labels=` | off | `specimen_id` | |

## 9. Units behavior
Nothing converts (LL in %, PI dimensionless).

## 10. API
At M8. Expected: `plasticity_chart(df, *, system="uscs", regions=None, labels=False, color_by="geology_unit", ...) -> (fig, ax)`.

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| PI > LL | Drawn; warning naming the specimens (impossible) |
| PI < 0 | Error naming the rows |
| PI given and inconsistent with LL − PL | Warning; PI as given is plotted |
| Only LL and PL | PI computed |

## 12. Acceptance criteria and tests
- A-line is drawn from (25.48, 4) and passes through (50, 21.9); extended, it would cross PI = 0 at LL = 20.
- U-line passes through (16, 7.2) and (50, 37.8), with the vertical part at LL = 16 below PI = 7.
- 1 unit in x = 1 unit in y on the rendered axes.

## 13. References
- ASTM D2487-17. Standard Practice for Classification of Soils for Engineering Purposes (USCS).
- Casagrande, A. (1948). Classification and identification of soils. *Trans. ASCE* 113, 901–930.
- BS 5930:2015+A1:2020.

## 14. Open questions
- Does `regions=` belong in v0.2 or stay with the v0.4 user-defined region item? Project group definitions on the chart are common in practice.

**Pitfalls:**
- Starting the U-line at (16, 7.2) and leaving out its vertical segment at LL = 16.
- Drawing the CL-ML zone as two horizontal lines without the hatch, so it doesn't read as a zone.
- Hard-coding a project's regions instead of taking them as a user table.

## 15. Future enhancements
- Color by USCS symbol instead of unit.
