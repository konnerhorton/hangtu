# P17 — Clogging potential diagram (draft notes)

| | |
|---|---|
| **ID / function** | P17 · `ht.plot.clogging_diagram()` |
| **Status** | idea (draft notes) |
| **Type** | plot + light analysis (consistency index) |
| **Target version** | v0.4 |
| **Depends on** | P00 |
| **Related** | P18 (Hollmann & Thewes 2013). Registry `consistency_index` (`used_by: [P17]`) |

---

## 1. Purpose
Places fine-grained specimens on a chart of clogging potential for slurry or EPB tunnel boring machines, using their consistency at in-situ water content. Answers: which units are likely to clog the cutterhead or chamber, and how many specimens fall in the high zone. Used in tunnel GBRs and TBM specifications.

## 2. Reference figure
A working layout with LL across and Ic up (zones to be checked against the source, §14):
```
  Ic
 2.0 ┤
     │
 1.5 ┤░░░▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒   ░ low   ▒ medium   █ high
 1.25┤░░░▒▒▒████████████████████████▒
     │░░░▒▒▒████████ ● ●  ██████████▒
 0.75┤░░░▒▒▒████████████████████████▒
 0.6 ┤░░░▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
 0.3 ┤░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
   0 ┼───┬───┬───┬───┬───┬───┬───┬
     0  10  20  30  40  50  60  70   LL (%)
```
Working zone polygons (LL, Ic), **unverified**:
- **Low:** (0, 0.3) → (0, 1.5) → (10, 1.5) → (10, 0.6) → (70, 0.6) → (70, 0.3).
- **Medium:** LL 10–70, Ic 0.6–1.5, excluding the high zone.
- **High:** LL 20–70, Ic 0.75–1.25.

## 3. Input data
**Row grain:** one row per specimen with all three of w, LL, PL.

| Column | Unit | Req.? | Notes |
|---|---|---|---|
| `water_content` | % | ✔ | In-situ w |
| `liquid_limit` | % | ✔ | |
| `plastic_limit` or `plasticity_index` | % / — | ✔ | |
| `consistency_index` | — | – | Computed if absent |
| `non_plastic` | bool | – | NP specimens can't be placed: counted |
| `geology_unit` | | – | Color |

## 4. Analysis / calculations
- Ic = (LL − w) / (LL − PL) (analysis draft §2); NaN when LL = PL.
- Zone membership per specimen (low / medium / high / outside), returned in the result so the counts can go in a report table.

## 5. Figure layout
Single panel, `default` size.

## 6. Axes
| | X axis | Y axis |
|---|---|---|
| Quantity | per the source diagram (see §14) | `consistency_index` |
| Limits | fixed per the source | fixed per the source (working: 0–2) |

## 7. Data marks
Scatter colored by unit; out-of-range values at the edge with counts (Ic < 0 is common in very wet soils and must not vanish). Zones as translucent fills (green / amber / red, alpha 0.2), **each labeled with text** (README: color is never the only carrier).

## 8. Overlays and annotations
| Overlay | Argument | Default | Notes |
|---|---|---|---|
| Zones | `zones=` | the source's | from config with citation; a user table overrides |
| Zone counts | `zone_counts=` | on | "High: 14 of 52" |

## 9. Units behavior
Nothing converts.

## 10. API
`clogging_diagram(df, *, method="thewes_burger_2004", zones=None, ...) -> (fig, ax, result)`.

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| LL = PL | Ic undefined; counted |
| Ic < 0 or above the axis | Edge marker + count |
| Missing w | Specimen can't be placed; counted |

## 12. Acceptance criteria and tests
- Golden: w = 20, LL = 40, PL = 20 → Ic = 1.0 → high zone with the working zones above.
- Zones reproduce the source figure (once verified).

## 13. References
- Thewes, M. & Burger, W. (2004). Clogging risks for TBM drives in clay. *Tunnels & Tunnelling International*, June 2004.
- Hollmann, F.S. & Thewes, M. (2013). Assessment method for clay clogging and disintegration of fines in mechanised tunnelling. *Tunnelling and Underground Space Technology* 37, 96–106.

## 14. Open questions
- **Axes and zones of the published diagram.** The roadmap says P17 is Thewes & Burger (2004), whose diagram (from memory, to verify) plots **PI against Ic**, not LL against Ic as in the working layout above. Confirm the axes and zone coordinates against the paper before building; if the working layout turns out to be a variant, it becomes a user `zones=` table rather than the built-in.

**Pitfalls:**
- Dropping specimens with Ic < 0 or outside the axes instead of drawing them at the edge.
- Zones identified only by color.

## 15. Future enhancements
- P18 (Hollmann & Thewes 2013), which adds a gradation-based screen before the consistency check.
