# P30 (proposed) — Groundwater level time series

| | |
|---|---|
| **ID / function** | P30 (proposed ID) · `ht.plot.groundwater_time_series()` |
| **Status** | idea (draft notes) |
| **Type** | plot |
| **Milestone** | not yet placed (open) |
| **Depends on** | P00 |
| **Related** | P29; P01's water-level overlay (design groundwater) |

---

## 1. Purpose
Plots groundwater elevation against time for one or more wells, one line per monitored zone. Answers: what is the seasonal range, are levels trending, do nested piezometers show a vertical gradient, and how did construction affect them. Sets design groundwater levels in GIRs and GBRs.

A companion summary table gives min/mean/max elevation and depth per well and aquifer.

## 2. Reference figure
```
       Jan '21   Mar '21   May '21   Jul '21
  Elev ┼─────────┼─────────┼─────────┼──────
  (m)  │ ─────╮                 ╭──────── upper aquifer
  148  ┤      ╰──────╮     ╭────╯
       │             ╰─────╯
  144  ┤ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ lower aquifer
       └───────────────────────────────────
```

## 3. Input data
**Row grain:** one row per reading (as P29).

| Column (proposed) | Description | Quantity kind | Unit | Req.? | AGS source (Phase 2) |
|---|---|---|---|---|---|
| `loca_id` | Well | | | ✔ | MOND.LOCA_ID |
| `monitoring_datetime` | Reading time | | | ✔ | MOND.MOND_DTIM |
| `groundwater_elevation` | Water level elevation | length | m | ✔ (or depth + ground level) | derived |
| `groundwater_depth` | Depth to water below ground | length | m | alt. | MOND_RDNG with MOND_TYPE = WDEP |
| `ground_level` | | length | m | with depth | LOCA.LOCA_GL |
| `aquifer` | Monitored zone | | | – | user mapping |

Elevation = ground level − depth (SPEC §8.1). Names to check against the registry.

## 4. Analysis / calculations
- Elevation from depth if needed.
- **Summary table** (`ht.analysis.groundwater_summary(df, by=["loca_id", "aquifer"])`): n, first and last date, min, mean, max of elevation and depth, as a DataFrame the user can save to Excel or CSV.

## 5. Figure layout
Single panel, landscape (`default` size).

## 6. Axes
| | X | Y |
|---|---|---|
| Quantity | date | `groundwater_elevation` |
| Label | — (dates) | `Groundwater elevation (m, datum)` |
| Position | bottom | left |
| Ticks | auto date locator; `date_ticks=` override | nice |

## 7. Data marks
Line per (`loca_id`, `aquifer`); color by `loca_id` when several wells, line style by `aquifer`. Markers at readings when sparse (manual dips), lines only when dense (loggers).

## 8. Overlays and annotations
| Overlay | Argument | Notes |
|---|---|---|
| Design levels | `reference_lines=` `(elevation, label)` | e.g. design high groundwater |
| Ground level | `ground_level=True` | dashed line per well |
| Events | `reference_dates=` | as P29 |

## 9. Units behavior
Elevation and depth convert (m ↔ ft); datum label from settings.

## 10. API
`groundwater_time_series(df, *, wells=None, color_by="loca_id", linestyle_by="aquifer", ...) -> (fig, ax)`.

## 11. Edge cases and data quality
- Dry or blocked readings (AGS remarks): drawn as distinct markers and counted, not as gaps or zeros (never drop silently).
- Gaps longer than `gap=` (default 30 days): line broken, not interpolated.

## 12. Acceptance criteria and tests
- Elevation computed from depth matches hand values.
- A gap > 30 days breaks the line.
- Summary table: golden min/mean/max on a 5-reading fixture.

## 13. References
- AGS4 MONG/MOND.

## 14. Open questions
- As P29: scope and timing.
- How dry wells are reported in the data (a flag, a remark, or a depth equal to the well base).

**Pitfalls:**
- Joining readings across long gaps, which suggests data that doesn't exist.
- Treating a dry well as a missing reading.

## 15. Future enhancements
- Rainfall or river stage on a second panel sharing time.
