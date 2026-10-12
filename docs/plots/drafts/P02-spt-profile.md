# P02 — SPT N profile (draft notes)

| | |
|---|---|
| **ID / function** | P02 · `ht.plot.spt_profile()` (+ `ht.analysis.spt()` for N60, refusal, test depth) |
| **Status** | idea (draft notes) |
| **Type** | plot + light analysis |
| **Target version** | v0.1 (milestone M3) |
| **Depends on** | P00, P01 |
| **Related** | `docs/drafts/analysis.md` §1 (SPT), SPEC §4, §8.2. TODO #4. P03 (shown beside it) |

---

## 1. Purpose
Shows SPT N (or N60) against elevation or depth for many holes at once, colored by geology unit. It answers: how dense or stiff is each unit, does N trend with depth, and are there holes or zones that stand out. It's the most common figure in a GIR's in-situ testing section, usually shown next to the SPT class histogram (P03).

## 2. Reference figure
```
                    SPT N
           0    20    40    60    80   100
     150 ┼─────┼─────┼─────┼─────┼─────┤
         │  ●     ●                    │
 Elev    │     ●  ●   ●                │   ■ Fill
 (m)     │        ●     ●      ●       │   ■ Unit A
     130 ┤           ●    ●       ●   ▷│   ■ Unit B
         │                ●    ●     ▷ │   ▷ refusal (shown at cap, 5)
     110 ┼─────────────────────────────┘
```
**A good version** is P01 with SPT conventions: refusals visible as a distinct marker at the cap, and the N column used named on the axis (N, N60, N capped).

## 3. Input data
**Row grain:** one row per SPT test. Columns are the `spt` template.

| Column | Description | Quantity kind | Canonical unit | US display | SI display | Req.? | Typical range | Valid range | AGS source | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `spt_n` | N as reported | count | — | — | — | ✔ (or `spt_n60`) | 0–100 | ≥ 0 | ISPT.ISPT_NVAL | |
| `spt_n60` | N corrected to 60% energy | count | — | — | — | – | 0–100 | ≥ 0 | derived | NULL until ER is known (SPEC §4) |
| `spt_refusal` | Refusal or partial penetration | bool | — | — | — | – | | | derived | |
| `depth` / `elevation` | Test depth (mid-drive) or elevation | length | m | ft | m | ✔ one | | | SPEC §8.2 | |
| `geology_unit` | Geology unit | — | | | | – | | | | Color |
| `loca_id` | Hole | — | | | | – | | | | Optional connecting lines |

**Value flags handled:** refusal → distinct marker at `spt_cap` (100), counted. Rows with blank N are counted, as P01.

**Minimum data:** ≥ 1 point.

## 4. Analysis / calculations
Defined in `docs/drafts/analysis.md` §1 (N60, refusal detection, `spt_n_capped`, mid-drive depth).

## 5. Figure layout
Single panel, `profile` size (4.0 × 6.5 in), portrait, as P01.

## 6. Axes
As P01 §6 with the N preset: x linear from 0, nice limit above the data or the cap; y elevation (up) or depth (down).

## 7. Data marks
As P01 §7. Additional series: refusal marker (filled triangle pointing right at the cap value, unit color), legend entry with count.

## 8. Overlays and annotations
P01 overlays (strata, ranges, design lines, reference lines, water level).

## 9. Units behavior
N is never converted; only the vertical axis changes (m / ft).

## 10. API
To be written at M3. Expected shape: `spt_profile(df, *, n="spt_n", vs="elevation", refusal="cap", connect=False, ...) -> (fig, ax)`, a thin wrapper over `profile()`.

## 11. Edge cases and data quality
As P01, plus: `n="spt_n60"` with all N60 blank → error saying to set `hammer_efficiency` or supply `energy_ratio`.

## 12. Acceptance criteria and tests
At M3.

## 13. References
- `docs/drafts/analysis.md` §1 and its references.

## 14. Open questions
None beyond TODO #4.

**Pitfalls:**
- Plotting the SPT *top* depth instead of the mid-drive depth (SPEC §8.2, decided).
- Inferring refusal from a large N (e.g. N ≥ 150) instead of using `spt_refusal` and the cap of 100 (SPEC §4, decided).

## 15. Future enhancements
- Color by any column (cross-cutting finding 1), e.g. an upper/lower elevation split.
