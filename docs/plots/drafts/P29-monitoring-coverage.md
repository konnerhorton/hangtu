# P29 (proposed) — Groundwater monitoring coverage

| | |
|---|---|
| **ID / function** | P29 (proposed ID) · `ht.plot.monitoring_coverage()` |
| **Status** | idea (draft notes) |
| **Type** | plot |
| **Milestone** | not yet placed (needs monitoring data; open) |
| **Depends on** | P00 |
| **Related** | P30 |

---

## 1. Purpose
Shows when groundwater readings exist for each group of wells, as a timeline. Answers: which areas or wells have continuous records, where are the gaps, and over what period can water levels be compared. A data-inventory figure for GIRs and monitoring reports.

One dot per (date, group) with at least one reading from any well in the group; groups in a user-given order (e.g. along an alignment).

## 2. Reference figure
```
  Area
  North    │ ●●●●●●  ●●●●●●●●●●●●●●●●
  Shaft 1  │    ●●●●●●●●●     ●●●●●●●●
  Station  │         ●●●●●●●●●●●●●●●●●●●●
  South    │ ●   ●   ●    ●     ●
           └──┬────────┬────────┬────────┬──
            Jan 2021  Apr 2021  Jul 2021  Oct 2021
```

## 3. Input data
**Row grain:** one row per reading.

| Column (proposed) | Description | Req.? | AGS source (Phase 2) |
|---|---|---|---|
| `loca_id` | Well / standpipe | ✔ | MOND.LOCA_ID |
| `monitoring_datetime` | Date and time of the reading | ✔ | MOND.MOND_DTIM |
| `aquifer` | Monitored zone / aquifer | – | user mapping |
| any grouping column | e.g. area, structure | – | user column |

Proposed names to check against the registry.

## 4. Analysis / calculations
Readings binned to a period (`resolution="day"` default; "week", "month"); a mark per (group, period) with ≥ 1 reading. Optional: shade by the number of wells reporting.

## 5. Figure layout
Single panel, landscape, height growing with the number of groups.

## 6. Axes
| | X | Y |
|---|---|---|
| Quantity | date | group (categorical) |
| Ticks | auto date locator (`date_ticks=` override, e.g. every 3 months as "Mon\nYYYY") | one per group, in `order=` |

## 7. Data marks
Dots, or horizontal bars for continuous runs (`style="bars"`), colored by `aquifer` if given.

## 8. Overlays and annotations
`reference_dates=` list of `(date, label)` (e.g. construction start, dewatering), vertical lines.

## 9. Units behavior
n/a.

## 10. API
`monitoring_coverage(df, *, group_by="loca_id", resolution="day", color_by=None, order=None, ...) -> (fig, ax)`.

## 11. Edge cases and data quality
- Unparseable dates: counted in a note, never dropped silently.
- Time zones: naive datetimes assumed local; mixed → error.

## 12. Acceptance criteria and tests
- Two readings on one day in one group → one mark.
- Unparseable dates counted.

## 13. References
- AGS4 MONG/MOND groups (Phase 2 ingest).

## 14. Open questions
- Is groundwater monitoring in scope before Phase 2? It isn't on SPEC's roadmap yet.

**Pitfalls:**
- Coercing bad dates to NaT and dropping them.
- Hard-coding the grouping column.

## 15. Future enhancements
- A Sheet layout with the coverage on top and the P30 time series below, sharing the date axis.
