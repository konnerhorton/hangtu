# P04 — Plasticity chart

| | |
|---|---|
| **ID / function** | P04 · `ht.plot.plasticity_chart()` (uses `ht.analysis.plasticity()`) |
| **Status** | built |
| **Type** | plot + classification |
| **Milestone** | M8 |
| **Depends on** | P00, the plasticity analysis (`docs/drafts/analysis.md` §2) |
| **Related** | SPEC §4 (NP, classification systems). P06, P07. TODO #5 (verify the lines), #22 (organic soils). M8 intent: `docs/work/m8-index-plots.md` |

---

## 1. Purpose
Places each specimen's liquid limit and plasticity index on the Casagrande chart, to classify the fines and compare geology units. It answers: are the units distinct, does each unit plot where its description says it should, and which specimens look as if they're in the wrong unit. It's in the lab section of almost every geotechnical report.

A second use: a project's own soil groups, drawn as regions in LL–PI space, so specimens can be checked against them.

## 2. Reference figure
```
  Plasticity index, PI
  60 ┤                               /U       ░ = user region (optional)
     │                        CH    /   /A
  40 ┤                          /     ░░░░/
     │                       /    ░░░░ /    MH
  20 ┤      CL           /  ● ●░░/ ●
   7 ┤ │▨▨CL-ML▨▨▨▨▨▨ /  ●   /        ML
   4 ┤ │▨▨▨▨▨▨▨▨▨▨/     /
     ├─┴──┬────┬────┬────┼────┬────┬────┬────┬────┤
     0   10   20   30   40   50   60   70   80  100
                      Liquid limit, LL (%)
                     12 non-plastic (NP) specimens not shown
```
**A good version:**
- equal aspect, so 1 PI = 1 LL on paper and the A-line's slope reads true;
- line and zone labels sit on or beside what they name, rotated to match the line on screen;
- the CL-ML zone reads as a zone (hatched), not as two lines;
- every specimen is either a point or counted in the footnote.

## 3. Input data
**Row grain:** one row per specimen: the `atterberg` template, `p.atterberg()` or `p.index_properties()`.

| Column | Description | Quantity kind | Req.? | Valid range | Notes |
|---|---|---|---|---|---|
| `liquid_limit` | LL | percent | ✔ | ≥ 0 | |
| `plasticity_index` | PI | dimensionless | ✔, or `plastic_limit` | 0 ≤ PI ≤ LL | Computed as LL − PL where blank (analysis §2.4) |
| `plastic_limit` | PL | percent | – | | |
| `non_plastic` | NP flag | bool | – | | Counted, not drawn |
| `geology_unit` | Geology unit | — | – | | Color (default `color_by`) |
| `specimen_id` | Specimen | — | – | | Point labels with `labels=True` |

**Hints** (one per call): "No 'geology_unit' column: all specimens are drawn in one color."

**Value flags handled:** NP is counted in the footnote and never drawn: it has no PI.

**Minimum data:** none. An empty chart with its lines is valid, for example as a base on a `Sheet`.

## 4. Analysis / calculations
- `plasticity_chart()` runs `ht.analysis.plasticity()`, so PI, NP and the warnings (PI > LL, PI far from LL − PL) are the analysis's, tested there once.
- **Lines and zones** come from `config/plasticity_systems.yaml`, through `a_line()` and `plasticity_system()`, so the chart and the classes can't disagree.

**`system="uscs"`** (ASTM D2487-17, Figure 4) 🔬:
- **A-line:** PI = 0.73 (LL − 20), drawn from PI = 4 (LL = 25.48) up to the top of the axes. Below PI = 4 the ML and CL-ML boundary is the horizontal line PI = 4.
- **U-line:** vertical at LL = 16 from PI = 0 to PI = 7.2, then PI = 0.9 (LL − 8). D2487 writes "vertical at LL = 16 to PI = 7"; 7 is its rounding of 0.9 × (16 − 8) = 7.2, so the line is drawn without a step.
- **CL-ML zone:** the polygon (16, 4), (25.48, 4), (29.59, 7), (16, 7), hatched: between PI 4 and 7, right of the U-line and left of the A-line.
- **LL = 50** divider, from the PI = 0 axis to the U-line.
- **Zone labels:** CL, CH, ML, MH, CL-ML. They name the inorganic classes, as `plasticity()` does. "CL or OL" style labels wait for TODO #22.

**`system="bs5930"`** (BS 5930:2015+A1:2020) 🔬:
- **A-line:** PI = 0.73 (LL − 20), from PI = 0.
- **Plasticity bands:** vertical dividers at LL = 35, 50, 70 and 90, from PI = 0 to the PI = LL line, with the band letter (L, I, H, V, E) along the top.
- **Zone labels:** C above the A-line and M below it, in each band (CL, CI, …, ME).
- No U-line: BS 5930 doesn't draw one.

**Both systems:** a light PI = LL line, since PI can't exceed LL.

## 5. Figure layout
- **Panels:** single.
- **Default size:** `default` (6.5 × 4.5 in). Equal aspect makes the 100 × 60 box fill the width.
  - For information: the zone labels and the A-line usually block every corner, so the legend usually goes below the x label (P00 §11). That is expected.
- **Orientation:** landscape.

## 6. Axes
| | X axis | Y axis |
|---|---|---|
| Quantity | `liquid_limit` | `plasticity_index` |
| Label | `Liquid limit, LL (%)` | `Plasticity index, PI` |
| Scale | linear | linear |
| Limits | 0–100; when an LL is above 100, extended to the next multiple of 20 | 0–60, always (a PI above 60 is drawn at the edge and counted) |
| Ticks | major every 10 | major every 10 |
| Gridlines | major, light | major, light |

**Range constraints:**
- [x] Equal aspect: always, also with `xlim=`/`ylim=`.
- [x] Fixed limits. Only x is extended, and only by an LL above 100; nothing shrinks the box. `xlim=`/`ylim=` set them exactly; points beyond are drawn at the edge (README policy).

## 7. Data marks
| Series | Mark | Color by | Legend entry | Notes |
|---|---|---|---|---|
| Specimens | scatter, 5 pt filled markers | `geology_unit` (palette) | ✔ per unit, "Unit A (n = 24)": the specimens drawn, at the edge or not | `color_by=None`: one neutral color, "All specimens (n = …)" |
| Beyond `xlim`/`ylim` | open marker at the edge + arrow | unit color | footnote count | README policy |
| NP | none | — | — | Footnote "n non-plastic (NP) specimens not shown" |
| Blank LL or PI | none | — | — | Footnote "n blank values not shown" |

**Draw order (bottom → top):** user regions → CL-ML hatch → PI = LL line → A-line, U-line and dividers → zone and line labels → specimens → specimen labels → footnote.

## 8. Overlays and annotations
| Overlay | Argument | Default | Source | Style | Notes |
|---|---|---|---|---|---|
| Lines and zones | `system=` | `"uscs"` | config, cited | black 0.8 pt; PI = LL light gray dotted | §4 |
| Zone labels | `zone_labels=` | on | config | 8 pt gray on a white background (over the gridlines), at the centroid of the zone's largest convex piece, so it is inside the zone | CL-ML is too small to hold its label, so the label sits just left of the U-line, level with the zone (inside it when `xlim=` leaves no room). BS 5930 band letters sit just above the axes |
| Line labels | (with the lines) | on | | "A-line", "U-line" along the line, rotated to its angle on screen | |
| User regions | `regions=` | off | user table (below) | outline 1 pt and fill alpha 0.12, gray unless `region_colors=` names a color; label at the polygon's centroid | Any shape (M8 intent, decision 4) |
| Specimen labels | `labels=` | off | `specimen_id` | 6 pt beside each point | |
| Note | `note=` | off | user | added to the footnote | |

**`regions=` format** (`ht.template("plasticity_regions")`): one row per vertex, in order around the polygon: `label, liquid_limit, plasticity_index`. Rows sharing a `label` make one polygon, closed automatically. A region needs at least three vertices; fewer is an error naming it. `label` is the existing overlay field.

## 9. Units behavior
Nothing converts: LL and PI are percentages. `display_units` is accepted for the plot contract and changes nothing, so one figure serves US and SI.

## 10. API
```python
def plasticity_chart(
    df: pd.DataFrame,
    *,
    system: Literal["uscs", "bs5930"] = "uscs",
    color_by: str | None = "geology_unit",
    order: list[str] | None = None,              # unit order in the legend, as P07
    labels: bool = False,
    zone_labels: bool = True,
    regions: pd.DataFrame | str | None = None,   # DataFrame or CSV path
    region_colors: dict[str, str] | None = None,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    note: str | None = None,
    palette: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides,
) -> tuple[Figure, Axes]:
```

**Example:**
```python
limits = p.atterberg()
fig, ax = ht.plot.plasticity_chart(limits, system="uscs")
fig, ax = ht.plot.plasticity_chart(limits, regions="project_groups.csv")
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| Empty input | The chart with its lines and a "No data" note; no error |
| No `liquid_limit` column | Error from `plasticity()`, listing the columns |
| PI > LL | Drawn; the analysis warns, naming the rows |
| PI given and more than 1 point from LL − PL | Drawn as given; the analysis warns |
| PL > LL, or negative values | Error from the analysis |
| Text such as "NP" in `liquid_limit` | Error naming the rows (the analysis); use `non_plastic` |
| `color_by` names a column that isn't there | Error listing the columns (`"geology_unit"` gives the hint instead) |
| `labels=True` and no `specimen_id` column | Error naming the column; blank IDs get no label |
| A region with fewer than three vertices, or `label` missing | Error naming the region |
| A region in `region_colors` that isn't in `regions` | Warning naming it |
| More than 12 / 30 units | README legend rules |

## 12. Acceptance criteria and tests
- **Geometry** (USCS), read back from the drawn lines:
  - the A-line starts at (25.48, 4) and passes through (50, 21.9); extended, it would cross PI = 0 at LL = 20;
  - the U-line passes through (16, 7.2) and (50, 37.8), with its vertical part at LL = 16 from PI 0 to 7.2;
  - the CL-ML polygon is (16, 4), (25.48, 4), (29.59, 7), (16, 7);
  - the LL = 50 divider stops at the U-line (PI = 37.8).
- **Geometry** (BS 5930): dividers at LL 35, 50, 70, 90, each ending at PI = LL; the A-line from (20, 0).
- **Agreement with the analysis:** for a grid of points, the zone each point is drawn in matches `plasticity_class_uscs` (and `_bs5930`).
- **Aspect:** 1 unit in x is 1 unit in y on the rendered axes, with default and user limits.
- **Limits:** LL 115 in the data extends x to 120 and leaves y at 0–60; LL 100 leaves x at 0–100; a PI of 65 is drawn at the top edge and counted.
- **Counts:** NP and blank specimens are counted in the footnote; out-of-range points with `xlim=` are drawn at the edge and counted.
- **Regions:** a non-rectangular region (five vertices) is drawn closed, with its label at the centroid; from a CSV path too.
- **Automated:** renders for both systems; `ax=` draws into a `Sheet` panel; no change to `rcParams`; the same figure for US and SI.
- **Visual check:** `docs/plots/img/P04.png` from the example project's Atterberg data, with one region.
- **Test data:** the example project (`ht.examples`) and synthetic frames for the geometry and edge cases.

## 13. References
- ASTM D2487-17. Standard Practice for Classification of Soils for Engineering Purposes (Unified Soil Classification System).
- Casagrande, A. (1948). Classification and identification of soils. *Transactions of the ASCE* 113, 901–930.
- BS 5930:2015+A1:2020. Code of practice for ground investigations.

## 14. Open questions
None open. Decided in review:
1. **U-line joint** at (16, 7.2), not a step at PI = 7 (§4).
2. **Zone labels without "or OL/OH"** until TODO #22 decides how organic soils are recorded (§4).
3. **Regions** are gray unless `region_colors=` says otherwise, so they can't be confused with geology unit colors (§8).
4. **Only x extends**, in steps of 20 and only for an LL above 100; y stays 0–60 (§6).

## 15. Future enhancements
- Color by USCS symbol instead of geology unit (`color_by="plasticity_class_uscs"` works already as a column; a fixed palette for classes would make it read better).
- Organic specimens drawn differently (TODO #22).
- A region computed from the data (not yet placed, SPEC §1.3), returned in the `regions=` format.
