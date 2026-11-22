# P15 — Consolidation time curves: root time and log time constructions per increment

| | |
|---|---|
| **ID / function** | P15 · `ht.plot.consolidation_time_curves()` (+ `ht.analysis.consolidation_coefficient_from_readings()`) |
| **Status** | draft (M19 (c2)) |
| **Type** | plot + analysis |
| **Milestone** | M19 (c2) (`STATUS.md`), [`docs/work/m19c2-cv-readings.md`](../work/m19c2-cv-readings.md) |
| **Depends on** | P00; `p.oedometer_readings()` or `ht.template("oedometer_readings")`; `consolidation_coefficient_from_readings()` (M19 (c2) Spec) |
| **Related** | P14 (c_v against stress, the same increments); P13; sheets 06, 12 |

---

## 1. Purpose
Draws, for the increments of one oedometer specimen, the vertical displacement against √t and against log t, with
each construction of BS 1377-5:1990, 3.6.3 drawn on it: the lines, the points they were fitted to, d0, d50, d90,
d100, t50 and t90. Answers: did the construction find a believable t50 and t90, which readings decided it, how far
apart the two methods and the lab's c_v are, and where an override was used. It is the plot 3.7 (h) asks a report to
give, made so the same readings always give the same picture.

## 2. Reference figure
```
 Increment 4: 100 → 200 kPa
 δ_v (mm)  root time                          δ_v (mm)  log time
 0.27 ┤●                                       0.27 ┤
      │ ╲●  early line (filled: fitted)             │●●●●
      │  ╲ ●                                        │     ●●  ╲ tangent
      │   ╲  ●                                      │ d0 ─ ─ ─ ●╲ ─ ─ ─ ─ ─
      │    ╲ ┆  ●   1.15 line                       │ d50 ─ ─ ─ ┆ ●
      │ d90 ─┆─ ─ ─ ●○○○○○○                        │ d100 ─ ─ ─┆─ ─ ●○──○──○  secondary
 0.58 ┤      ┆t90                              0.58 ┤           ┆t50
      └──────┴──────────────── √t (√min)            └───────────┴────────────── t (min), log
   c_v 2.15 m²/yr (lab 2.1)                     c_v 2.06 m²/yr (lab 1.8)
```
A good version: compression downward on both panels, the readings each line was fitted to filled and the rest open,
the construction lines thin and labeled, and the result written in the panel with the lab's value beside it, so a
reviewer judges the construction and its consequence in one look.

## 3. Input data
**Row grain:** one row per reading, as `p.oedometer_readings()` returns, or a CSV in
`ht.template("oedometer_readings")`'s shape, with each increment's values on every reading.

| Column | Description | Quantity kind | Req.? | Notes |
|---|---|---|---|---|
| `specimen_id`, `test_stage` | the specimen and increment | text | ✔ | one specimen per figure |
| `elapsed_time` | t since the load was applied | time | ✔ | |
| `vertical_displacement` | the reading, in the file's datum and sign | small_length | ✔ | |
| `applied_vertical_stress` | σ′2, for the panel title | stress | – | σ′1 from the previous increment |
| `specimen_height`, `void_ratio`, `void_ratio_at_increment_start`, `void_ratio_at_increment_end` | for H̄ | | – | without them, t50 and t90 are drawn and c_v isn't |
| `load_branch` | | text | – | added when missing |
| `reported_coefficient_of_consolidation_root_time`, `…_log_time` | the lab's c_v | consolidation_coefficient | – | written beside the result |

**Grouping columns used:** `specimen_id` (one per figure), `test_stage` (one row of panels each).

**Value flags handled:** none; readings left out by the analysis are counted in the footnote.

**Minimum data:** one increment with 3 readings after t = 0.

## 4. Analysis / calculations
`ht.analysis.consolidation_coefficient_from_readings()` (M19 (c2) Spec, decisions 1–9; golden values there). The plot
calls it with `overrides=` and draws its lines and points; it computes nothing of its own.

## 5. Figure layout
- **Panels:** one row per increment, two columns: root time (left) and log time (right). `methods=` draws one column.
- **Default size:** `default`'s width, 2.4 in per row plus 1.1 in for the title, legend and footnote. At most 6
  increments in one figure; more raise an error naming `increments=`, since a taller figure isn't readable on a page. A
  loop over `increments=` draws them all.
- **Legend:** once, below the last row's x labels: readings (fitted, not fitted), the construction lines, the points.
- **Panel title:** "Increment 4: 100 → 200 kPa" (the increment's `test_stage`, σ′1 → σ′2; "(unloading)" or
  "(reloading)" appended off the loading branch), once per row, over the left panel. σ′1 is the stress of the
  increment numbered one before, where the rows have it; without it, "Increment 2: to 50 kPa". The x labels name the
  method, so the panels have no method title. The specimen named as P13 names it in the figure title, with its depth.

## 6. Axes
| X axis, left | X axis, right | Y axis (both) |
|---|---|---|
| `Square root of time, √t (√min)`, linear from 0 | `Time, t (min)`, log | `Vertical displacement, δ_v (mm)` |

- **Orientation:** the increment's movement points down: the y axis is inverted where the readings rise over the
  increment (s = +1), not where they fall. Each panel's own y limits, so a small increment isn't flattened.
- **Limits:** x on the right from the decade at or below the first reading after t = 0 to beyond the last reading.
  x on the left from 0 to a nice limit past 2.5 √t90 (past the last fitted early reading where there's no t90, and
  never past the last reading); the readings beyond it go at the right edge as open markers with an arrow, counted in
  the footnote (README's out-of-range rule). Reason: at the standard's reading times the last reading is at 1440 min
  (√t ≈ 38) and t90 is usually near 20 min (√t ≈ 4.5), so an axis to the last reading squeezes the construction into
  the panel's first eighth, where it can't be judged (decided 2026-11-22, in the build). y as README's linear rule,
  over the readings and the construction points, shared by the row's panels.
- US labels: in; time stays in minutes.

**Range constraints:** none.

## 7. Data marks
| Series | Mark | Color | Legend |
|---|---|---|---|
| Reading fitted by a line, or in a 1:4 pair (t_i or 4 t_i) | filled circle | the specimen's | "Reading used" |
| Other reading | open circle, joined by a thin line (the interpolation) | as above | "Reading" |
| t = 0 reading | on the root time panel only (no position on log t) | as above | counted in the footnote |
| Early line, extended to t = 0 | solid thin | dark gray | "Early line" |
| 1.15 line | dashed thin | dark gray | "1.15 line" |
| Tangent at inflexion, secondary line | solid thin, extended to their crossing | dark gray | "Tangent and secondary line" |
| d0, d50, d90, d100 | dotted horizontal across the panel, labeled just outside its right edge | gray | "d0, d50, d90, d100; t50, t90" |
| t50, t90 | dotted vertical from the curve to the axis, labeled at the axis | gray | as above |
| Result | text in the panel's upper right, clear of the curve, which runs from upper left to lower right: "c_v 2.15 m²/yr (lab 2.1)", 3SF for hangtu's, the lab's as written | black | — |
| An override | "(override)" after the result, and the overridden line dash-dotted | as above | "Line over an override range" |
| A construction that stops | the lines it got to (the early line; the secondary line and tangent), and its reason; readings filled only where a drawn line was fitted to them | as above | — |

## 8. Overlays and annotations
| Overlay | Argument | Default | Source of definition | Style | Notes |
|---|---|---|---|---|---|
| Overrides | `overrides=` | `None` | `ht.template("consolidation_overrides")` | §7 | passed to the analysis |
| Lab's c_v | `reported=` | `True` | the `reported_` columns | in the result text | "lab —" when blank |
| Methods | `methods=` | `("root_time", "log_time")` | | | one or both |
| Increments | `increments=` | every increment with readings | `test_stage` values, as text | | an unknown one is an error listing them |
| Footnote | — | when anything isn't drawn | the analysis's notes | README | readings left out; the t = 0 reading not on log t |
| Reason | — | where a construction gives none | the `_reason` columns | in the panel, centered | the readings are still drawn |
| `note` | as README | off | | | |

## 9. Units behavior
Displacements convert (mm ↔ in), c_v (m²/yr ↔ ft²/yr); times are drawn in minutes in both systems. `display_units=`
goes to the analysis, so the panels and the returned frame agree.

## 10. API
```python
def consolidation_time_curves(
    df: pd.DataFrame,
    *,
    specimen: str | None = None,
    increments: Sequence[str] | None = None,
    methods: Sequence[str] = ("root_time", "log_time"),
    overrides: pd.DataFrame | None = None,
    reported: bool = True,
    note: str | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    **style_overrides,
) -> tuple[Figure, np.ndarray]:
```
- `specimen=` is required when the frame holds more than one specimen (an error lists them).
- Returns `(fig, axs)`, `axs` shaped (rows, columns). No `ax=`: the figure is a grid, as P14.
- No result object: `consolidation_coefficient_from_readings()` returns the numbers.

**Examples:**
```python
readings = p.oedometer_readings()
fig, axs = ht.plot.consolidation_time_curves(readings, specimen="BH1-U3-OED1", increments=["3", "4", "5"])
overrides = ht.read_csv("overrides.csv", units={"elapsed_time_start": "min", "elapsed_time_end": "min"})
fig, axs = ht.plot.consolidation_time_curves(readings, specimen="BH1-U3-OED1", overrides=overrides)
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| A required column missing | The analysis's error naming it and `ht.template("oedometer_readings")` |
| More than one specimen, no `specimen=` | Error listing the specimens |
| More than 6 increments | Error naming `increments=` |
| A construction gives a reason | The readings drawn; the reason in the panel; the other method still drawn |
| No H̄ | Constructions drawn; "c_v not computed: no specimen height or void ratio for H̄" in place of the result |
| A `constant_stress` increment | Not drawn; the footnote names it |
| Readings left out (blank, negative time) | Counted in the footnote |

## 12. Acceptance criteria and tests
Golden values are the M19 (c2) Spec's, hand-calculated there. Tolerance 1e-9 relative on drawn data unless stated.
1. **Root time panel:** BH1-U3 increment 4 (`site_si.ags`) draws 15 readings at √t, 6 filled (0.1–4 min), the three past
   the x limit (240–1440 min) at its edge; the early line from (0, 0.286233001) with slope 0.0619114129 mm/√min; the
   1.15 line; t90 at √19.7847853; d90 at 0.525696071 mm; "c_v 2.15 m²/yr (lab 2.1)".
2. **Log time panel:** 14 readings (no t = 0), filled at 0.5, 1, 2, 4, 8, 15, 240, 480 and 1440 min; the tangent
   and secondary lines crossing at 29.0882465 min, 0.560523057 mm; d0 0.286666667, d50 0.423594862 mm; t50
   4.82957834 min; "c_v 2.06 m²/yr (lab 1.8)".
3. **Orientation:** both y axes inverted (the readings rise); with the readings negated, not inverted, and the same
   lines drawn at the negated values.
4. **Override:** a root time `early` override of 0.25–4 min draws 5 filled early readings, the early line dash-dotted,
   and "c_v 2.16 m²/yr (lab 2.1) (override)".
5. **Reason:** an increment whose readings stop at 10 min draws its readings and "t90 after the last reading" on the
   root time panel, and its log time reason on the other.
6. **Units:** `display_units="US"` draws increment 4's d0 (root time) at 0.0112690158 in and writes "c_v 23.1
   ft²/yr (lab 23)" (the lab's 2.1 m²/yr keeps its two figures, README "Numbers in a box"); times in minutes.
7. **Layout:** `methods=("log_time",)` gives one column; `increments=["3", "4"]` two rows; seven increments raise
   naming `increments=`; two specimens without `specimen=` raise listing them.
8. **Returns:** `(fig, axs)` with `axs.shape == (rows, columns)`.
9. **Edge cases:** each row of §11 that raises raises with the message it names; each that draws, draws (a
   hand-built frame per case).
10. **Visual check:** `docs/plots/img/P15-si.png` (BH1-U3, increments 3–5, kPa and mm) and `P15-us.png` (an example
    project specimen with scatter, in), at 100 dpi, looked at and committed in the close-out.

## 13. References
- BS 1377-5:1990, 3.6.3.2.1–3.6.3.2.4: the log time construction and c_v = 0.026 H̄²/t50.
- BS 1377-5:1990, 3.6.3.3.1–3.6.3.3.3: the root time construction and c_v = 0.111 H̄²/t90.
- BS 1377-5:1990, 3.7, items (h) and (k): plots of compression against log or root time for each increment, and the
  fitting method used.

## 14. Open questions
- None open.

**Pitfalls:**
- Drawing the log time curve with the t = 0 reading at some small time: it has no place on a log axis.
- Inverting the y axis by the branch instead of by the readings: a gauge that reads down on loading would be drawn
  upside down.
- Smoothing the curve for the drawing: the constructions interpolate linearly, and the drawn curve is the one they
  used.

## 15. Future enhancements
- C_sec from the secondary line over one log cycle (3.6.5), which the log time panel already draws.
- Stored overrides (TODO #77).
