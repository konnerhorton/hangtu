# P14 — Consolidation coefficients: m_v and c_v against log σ′v

| | |
|---|---|
| **ID / function** | P14 · `ht.plot.consolidation_coefficients()` (+ `ht.analysis.oedometer_increments()`) |
| **Status** | built (M19 (c1)); images: [`img/P14-us.png`](img/P14-us.png), [`img/P14-si.png`](img/P14-si.png) |
| **Type** | plot + light analysis |
| **Milestone** | M19 (c1) (`STATUS.md`), [`docs/work/m19c-consolidation.md`](../work/m19c-consolidation.md) |
| **Depends on** | P00; `p.oedometer()` (M19 a); `oedometer_increments()` (M19 (c1) Spec) |
| **Related** | P13 (the e–log σ′v curve of the same increments); P15 (c_v's time curves, M19 (c2)); sheets 06, 11, 12 |

---

## 1. Purpose
Draws, for one or more oedometer specimens, the coefficient of volume compressibility m_v and the coefficient of
consolidation c_v of each increment against the stress range the increment spans. Answers: how m_v and c_v change
with stress, where σ′v0 falls among the increments, whether the lab's m_v agrees with the one its void ratios give,
and how far apart the lab's root time and log time c_v are. The engineer looks at it before taking m_v, c_v or k
for a design stress range: each is a value over an increment, not at a point.

## 2. Reference figure
```
 m_v (m²/MN)                                             log
  0.2 ┤        ━━━━━━━━━━━━━━━━━━━━━━  ×       ×
      │   ━━━━━    ×    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  0.1 ┤                                         ━━━━━━━━━━━━━━━━━━━━━━
      │                 ┆σ′v0                              ━━━━━━━━━━━━━━━━━━━━━━━━━━
 0.05 ┤        ─ ─ ─ ─ ─┆─ ─ ─ ─ (unload, open)
      └────────┬────────┆───────┬──────────────┬──────────────┬──────
 c_v (m²/yr)            ┆                                          log
   3 ┤                  ┆  ━━━━━━━━━━━━━  root time
   2 ┤                  ┆  ┅┅┅┅┅┅┅┅┅┅┅┅┅  log time
     └────────┬─────────┆──────┬──────────────┬──────────────┬──────
             25        50     100            200            400    σ′v (kPa), log
```
A good version: each increment a horizontal segment from its start stress to its end stress, so the reader sees the
range a value belongs to; loading solid and unloading or reloading lighter, so the design branch stands out; the
lab's m_v as a mark on the same segment, so a disagreement is visible at a glance.

## 3. Input data
**Row grain:** one row per increment, as `p.oedometer()` returns, or a CSV in `ht.template("oedometer")`'s shape.

| Column | Description | Quantity kind | Req.? | Notes |
|---|---|---|---|---|
| `specimen_id` | one series each | text | ✔ | |
| `applied_vertical_stress` | σ′v at the end of the increment | stress | ✔ | |
| `void_ratio_at_increment_start`, `void_ratio_at_increment_end` | e1, e2 | dimensionless | ✔ (end), – (start) | the start falls back to the previous end |
| `load_branch` | loading, unloading, reloading, constant stress | text | – | added by `oedometer_increments()` when missing |
| `reported_coefficient_of_volume_compressibility` | the lab's m_v | volume_compressibility | – | drawn as a mark |
| `reported_coefficient_of_consolidation_root_time`, `…_log_time` | the lab's c_v | consolidation_coefficient | – | the lower panel; without either, it says so |
| `effective_vertical_stress` | σ′v0 | stress | – | the σ′v0 line |
| `loca_id`, `depth`, `geology_unit` | the legend's label | | – | |

**Grouping columns used:** `specimen_id` (one color each).

**Value flags handled:** none. Increments with no m_v (the first, a constant stress) are counted in the footnote.

**Minimum data:** 2 increments of one specimen for one m_v segment.

## 4. Analysis / calculations
`ht.analysis.oedometer_increments()` (M19 (c1) Spec; the equations and golden values are there). The plot calls it
on the frame and draws its columns; it computes nothing of its own. c_v is the lab's, as reported; (c2) adds c_v
from time readings.

## 5. Figure layout
- **Panels:** two, stacked, sharing the x axis: m_v above, c_v below.
- **Default size:** a new `stacked` kind in P00's `figure_sizes`, (6.5, 6.0) in: `default`'s width, two panels high.
- **Legend:** README's rule, in the upper panel: the branch styles and the lab's mark once each, colors per specimen.
  The lower panel's legend names root time and log time. When no corner of the upper panel is clear, its entries
  join the lower panel's legend, which goes below the x label if that panel has no clear corner either: below the
  upper panel's x axis is the lower panel.

## 6. Axes
| X axis (shared) | Y axis, upper | Y axis, lower |
|---|---|---|
| `Effective vertical stress, σ′v (kPa)`, log | `Coefficient of volume compressibility, m_v (m²/MN)`, log | `Coefficient of consolidation, c_v (m²/yr)`, log |

- Both y axes log: over a test m_v spans one to two decades (BH1-U3: 0.0099 to 0.17 m²/MN), c_v often more.
- **Limits:** x from a decade boundary at or below the lowest start stress (or σ′v0, if lower) to one at or above the
  highest end stress; y as README's log rule.
- US labels: psf (or ksf / tsf with `ht.settings.display_overrides`), ft²/kip and ft²/yr.

**Range constraints:** none.

## 7. Data marks
| Series | Mark | Color | Legend |
|---|---|---|---|
| m_v, loading increment | solid horizontal segment from σ′1 to σ′2 | by specimen | "m_v, loading" |
| m_v, unloading or reloading increment | thin dashed segment | as loading, lighter | "m_v, unloading or reloading" |
| m_v not positive | not drawn on a log axis | — | counted in the footnote |
| Lab's m_v | × at the segment's geometric midpoint, √(σ′1 σ′2) | as the specimen | "m_v reported by the lab" |
| c_v, root time | solid segment from σ′1 to σ′2 | as the specimen | "c_v, root time (lab)" |
| c_v, log time | dotted segment | as the specimen | "c_v, log time (lab)" |
| σ′v0 | vertical dotted line through both panels | as the specimen | "σ′v0" |
| The increments at σ′v0 | segment drawn thicker | as above | — |

Segments rather than points: m_v is a secant over the increment (BS 1377-5:1990, 3.6.2.2.4), and drawing it at
one stress (the end, the mean or the geometric mean) would be a choice the value doesn't carry. The first increment,
whose start stress isn't known, has no m_v segment; its c_v is drawn as a × at its end stress, since it has no span.

## 8. Overlays and annotations
| Overlay | Argument | Default | Source of definition | Style | Notes |
|---|---|---|---|---|---|
| Lab's m_v | `reported=` | `True` | `reported_coefficient_of_volume_compressibility` | § 7 | `False` leaves the marks out |
| Branches | `branches=` | `("loading", "unloading", "reloading")` | `load_branch` | § 7 | a subset draws only those; an unknown value is an error listing the three |
| Footnote | — | when anything isn't drawn | `oedometer_increments()`'s reasons | README | "Not drawn for BH1-U3-OED1: increment 1 (start stress not given)", the specimen named as P13 names it; "No c_v reported" is written in the lower panel instead (§11) |
| `note` | as README | off | | | |

## 9. Units behavior
Stresses convert (kPa ↔ psf, ksf, tsf); m_v (m²/MN ↔ ft²/kip) and c_v (m²/yr ↔ ft²/yr) through their kinds.
`display_units=` goes to `oedometer_increments()`, so the axes and the returned columns agree.

## 10. API
```python
def consolidation_coefficients(
    df: pd.DataFrame,
    *,
    reported: bool = True,
    branches: Sequence[str] = ("loading", "unloading", "reloading"),
    note: str | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    **style_overrides,
) -> tuple[Figure, np.ndarray]:
```
- Returns `(fig, axs)` (README: a multi-panel figure). No `ax=`: two panels need a figure, as P08.
- No result object: `oedometer_increments()` returns a DataFrame, which the engineer calls for the numbers.

**Examples:**
```python
oed = ht.analysis.vertical_stress(p.oedometer(where={"test_type": "OEDOMETER"}), p.stratigraphy())
fig, axs = ht.plot.consolidation_coefficients(oed)
fig, axs = ht.plot.consolidation_coefficients(oed, branches=("loading",))
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| A required column missing | `oedometer_increments()`'s error naming it and `ht.template("oedometer")` |
| No c_v in either column | Lower panel empty with "No c_v reported" in it |
| No σ′v0 | No σ′v0 line, no thick segments |
| m_v 0 or negative (the void ratio moved against the stress change) | Not drawn on the log axis; the footnote names the increment |
| A specimen with no increments (`SWELLPRESS`) | Not drawn; the footnote names it |
| `branches=` empty or unknown | Error listing the three values |

## 12. Acceptance criteria and tests
Golden values are the M19 (c1) Spec's, hand-calculated there. Tolerance 1e-9 relative on drawn data unless stated.
1. **m_v segments:** BH1-U3 (`site_si.ags`) draws 11 m_v segments: 6 solid (increments 2–6 and 11) and 5 dashed
   (7–10 and 12); increment 4's runs from 100 to 200 kPa at 0.157657658 m²/MN, increment 7's from 200 to 800 kPa at
   0.0134408602.
2. **Lab's marks:** 6 × marks, increment 4's at (141.421356 kPa, 0.16 m²/MN).
3. **c_v:** increment 4's root time segment from 100 to 200 kPa at 2.1 m²/yr and log time at 1.8.
4. **σ′v0:** with σ′v0 = 80 kPa, the dotted line at 80 kPa and increments 3 (loading) and 8 (unloading) thicker.
5. **Footnote:** "Not drawn for BH1-U3-OED1: increment 1 (start stress not given)".
6. **Branches:** `branches=("loading",)` draws 6 m_v segments and no dashed one.
7. **Units:** `display_units="US"` on `site_si.ags` draws increment 4 at 0.00754868948 ft²/kip and 22.6042118
   ft²/yr, x in psf.
8. **Returns:** `(fig, axs)` with two axes sharing x.
9. **Edge cases:** each row of §11 that raises raises with the message it names; each that draws, draws (a
   hand-built frame per case).
10. **Visual check:** `docs/plots/img/P14-us.png` (the example project's specimens, psf) and `P14-si.png` (BH1-U3,
    kPa, with σ′v0 = 80 kPa), at 100 dpi, looked at and committed in the close-out.

## 13. References
- BS 1377-5:1990, 3.6.2.2.4: m_v per loading increment, from the height at the increment's start.
- BS 1377-5:1990, 3.7, item (i): m_v and c_v reported for each load increment, to two significant figures.

## 14. Open questions
- None open.

**Pitfalls:**
- Drawing m_v at the increment's end stress and joining the points, which reads as a tangent curve.
- Drawing unload m_v in the loading style: BS defines m_v on loading increments only.

## 15. Future enhancements
- c_v from time readings beside the lab's (M19 (c2), with P15).
- Eoed = 1/m_v on a modulus axis instead of m_v.
- σ′p from `oedometer_fit()` as a vertical line, where c_v often drops.
