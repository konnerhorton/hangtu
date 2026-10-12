# P05 — Grain size distribution (draft notes)

| | |
|---|---|
| **ID / function** | P05 · `ht.plot.grain_size()` (+ `ht.analysis.gradation()`) |
| **Status** | idea (draft notes) |
| **Type** | plot + analysis (Dx, Cu, Cc, gradation) |
| **Target version** | v0.1 (milestone M4) |
| **Depends on** | P00 |
| **Related** | `docs/drafts/analysis.md` §3, TODO #5. P25 (size-fraction comparison) |

---

## 1. Purpose
Draws particle-size distribution curves, one per specimen, on a log size axis with the soil-fraction names above. Answers: what is this soil, how well graded is it, and does it fall inside a project's or a specification's envelope. In every GIR lab section, and in filter and grouting design.

Two features worth having from the start: the **fraction header band** above the plot, and **envelopes** shaded behind the curves.

## 2. Reference figure
```
     ┌──────┬────────────┬───────────────────┬───────────────┐
     │ Clay │    Silt    │ Fine │Med│Coarse  │ Fine │ Coarse │   ← header band
     │      │            │       Sand        │    Gravel     │
     ├──────┴────────────┴───────────────────┴───────────────┤
 100 ┤            #200      #100  #40   #10  #4  ⅜"  ¾" 1½"  │   ← sieve labels
     │                          ______________________/      │
  % ┤                  ______/ ░░░░░░░░ envelope ░░░░░        │
 pass│          ______/  ┊D60                                │
     │  ______/ ┊D30     ┊                                   │
   0 ┼──┴───────┴────────┴───────────────────────────────────┤
    0.001     0.01      0.1       1        10       100   Particle size (mm)
```

## 3. Input data
**Row grain:** one row per curve point (the `grain_size` template).

| Column | Description | Quantity kind | Unit | Req.? | Valid range | Notes |
|---|---|---|---|---|---|---|
| `specimen_id` | Curve identity | | | ✔ | | One curve per specimen (within `loca_id`) |
| `particle_size` | Sieve or hydrometer size | particle_size | mm | ✔ | > 0 | Never converted (mm in both systems) |
| `percent_passing` | % passing | percent | % | ✔ | 0–100 | |
| `geology_unit` | Color | | | – | | |
| `loca_id` | Hole | | | – | | |

**Minimum data:** ≥ 2 points per curve; fewer → curve skipped and noted.

## 4. Analysis / calculations
- Dx by log-linear interpolation, never extrapolated; Cu, Cc; USCS gradation (analysis draft §3). Points sorted by size; non-monotonic passing is flagged, not hidden.
- **Fraction systems** (configurable, decided): `astm_uscs` default.

## 5. Figure layout
Single panel plus the header band (a thin axes on top, sharing x). Default size: `default`, landscape. A full Letter landscape sheet (11 × 8.5 in) is a common report size; `figsize=` covers it.

## 6. Axes
| | X axis | Y axis |
|---|---|---|
| Quantity | `particle_size` | `percent_passing` |
| Label | `Particle size (mm)` | `Percent passing (%)` |
| Scale | log, whole decades | linear |
| Limits | fixed decades covering the data, at least 0.001–100 mm | fixed 0–100 |
| Grid | major and minor | major every 10% |
| Secondary | sieve labels along the top inside edge | — |

## 7. Data marks
| Series | Mark | Color by | Legend |
|---|---|---|---|
| Curves | line with point markers | `geology_unit` (or one color per specimen with `color_by="specimen_id"`) | ✔ |
| D-values | dashed leader lines to the axes + label "D60 = 0.42 mm" | black | — |
| Envelope | filled band between lower and upper curves | user color, alpha 0.3 | ✔ envelope label |

## 8. Overlays and annotations
| Overlay | Argument | Default | Source | Notes |
|---|---|---|---|---|
| Header band | `fractions=` | `"astm_uscs"` | config, cited | `None` hides it |
| Sieve labels | `sieves=` | on; US list in US display, ISO list in SI | config | |
| D-values | `d_values=` | off | §4 | `True` → D10, D30, D60; or a list |
| Envelopes | `envelopes=` | off | user table: `label, particle_size, lower, upper` | e.g. a project's soil-group gradation bands |

## 9. Units behavior
Particle size stays in mm in both systems (registry decision). Sieve labels switch between the US and ISO lists.

## 10. API
At M4. Expected: `grain_size(df, *, fractions="astm_uscs", d_values=False, envelopes=None, color_by="geology_unit", ...) -> (fig, ax)`.

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| Non-monotonic passing | Drawn as given; warning naming the specimen |
| Passing never reaches 10% | D10 not computed; label omitted; noted |
| > 20 curves | Legend rules (README); suggest `color_by="geology_unit"` |

## 12. Acceptance criteria and tests
- USCS header boundaries at 0.075, 0.425, 2.0, 4.75, 19 and 75 mm (ASTM D2487).
- Golden D-values from a hand-interpolated curve.

## 13. References
- ASTM D2487-17; ASTM D6913; ISO 14688-1:2017.

## 14. Open questions
- Should the USCS header show a clay/silt split at all? USCS treats "fines" as one fraction; the 0.002 mm (or 0.005 mm) boundary comes from other systems.

**Pitfalls:**
- Sorting particle size and percent passing **independently** to make a curve monotonic: it silently re-pairs the points. Sort the rows by size.
- Hard-coding boundaries per plot: it's easy to end up with two versions (silt/sand at 0.075 mm in one, 0.05 mm in another). Take every boundary from one named system.
- Typos in boundaries: fine/medium sand is 0.425 mm (#40), not 0.475; fine/coarse gravel is 19 mm (¾"), not 20. The header test above catches both.

## 15. Future enhancements
- Envelope computed from the data (min/max or percentiles per unit), drawn as a band.
