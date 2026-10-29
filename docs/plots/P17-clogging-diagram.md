# P17 — Clogging diagram

| | |
|---|---|
| **ID / function** | P17 · `ht.plot.clogging_diagram()` (uses `ht.analysis.clogging_potential()`) |
| **Status** | draft |
| **Type** | plot + classification |
| **Milestone** | M12 (wave 1) |
| **Depends on** | P00; `ht.analysis.plasticity()` for PI and Ic (M8) |
| **Related** | P04 (same pattern: the classes are an analysis, the chart draws them). P18 (Hollmann & Thewes 2013), not yet placed. TODO #21. M12 intent: `docs/work/m12-clogging-diagram.md` |

---

## 1. Purpose
Places fine-grained specimens on Thewes & Burger's (2004) chart of clay clogging potential for TBM drives, by plasticity index and consistency index at in situ water content. It answers: which geology units are likely to clog the cutterhead, chamber or spoil path, and how many specimens fall in each zone. It goes in tunnel GBRs and TBM specifications, with the counts quoted in a table.

The chart is a screen on index properties only. Mineralogy, the machine and conditioning are outside it, and the docstrings say so.

## 2. Reference figure
Thewes & Burger (2004), Fig. 🔬 (number to confirm). The zones are in §4.
```
  Consistency index, Ic
  1.5 ┤    ┌──┬───────────────────────────┐
      │ low│▒▒│▓▓▓▓▓▓▓ medium-high ▓▓▓▓▓▓▓│   ▒ medium
  1.3 ┤    │▒▒├───────────────────────────┤   ▓ medium-high
      │    │▒▒│███████████████████████████│   █ high
      │    │▒▒│█████████ high  ● ●████████│
      │    │▒▒│████████████ ●  ●██████████│
  0.75┤    │▒▒├───────────────────────────┤
  0.6 ┤    │▒▒▒▒▒▒▒▒▒▒▒ medium ▒▒▒▒▒▒▒▒▒▒▒│
      │    └──────────────────────────────┘
      │               low
  0.3 ┼────┬────┬────┬────┬────┬────┬────┤
      0   10   20   30   40   50   60   70
                  Plasticity index, PI
         3 specimens with Ic < 0.3 shown at limit
```
**A good version:**
- every zone carries its name in text inside it, so the chart reads in grayscale;
- specimens wetter than the liquid limit (Ic < 0) sit on the bottom edge with arrows, not off the chart;
- the footnote accounts for every input row that isn't a point.

## 3. Input data
**Row grain:** one row per specimen: `p.atterberg()`, `p.index_properties()`, or the `atterberg` template.

| Column | Description | Quantity kind | Req.? | Valid range | Notes |
|---|---|---|---|---|---|
| `water_content` | In situ w | percent | ✔ | ≥ 0 | From LNMC in `p.atterberg()` |
| `liquid_limit` | LL | percent | ✔ | ≥ 0 | |
| `plastic_limit` | PL | percent | ✔, or `plasticity_index` | | |
| `plasticity_index` | PI | dimensionless | – | 0 ≤ PI ≤ LL | Computed as LL − PL where blank |
| `consistency_index` | Ic | dimensionless | – | | Computed where blank; kept where given |
| `non_plastic` | NP flag | bool | – | | Counted, not drawn |
| `geology_unit` | Geology unit | — | – | | Color (default `color_by`) |
| `specimen_id` | Specimen | — | – | | Point labels with `labels=True` |

**Hints** (one per call): "No 'geology_unit' column: all specimens are drawn in one color."

**Value flags handled:** NP is counted in the footnote and never drawn: it has no PI or Ic.

**Minimum data:** none. An empty chart with its zones is valid.

## 4. Analysis / calculations
- **Function:** `ht.analysis.clogging_potential(df, *, method="thewes_burger_2004", zones=None) -> pd.DataFrame`. Returns a copy of `df` with `plasticity_index` and `consistency_index` filled in by `plasticity()` (so its warnings and errors are the same, tested once) and one new column, `clogging_potential`. No row is dropped or reordered.
- **Ic** = (LL − w) / PI, from `plasticity()`. Not computed a second time.
- **`clogging_potential`**: the name of the zone the specimen's (PI, Ic) falls in, as the source names it, or blank where the specimen can't be placed (NP, blank w, LL or PL, PI = 0) or falls outside the diagram (§4).
- **Zones** come from `config/clogging_methods.yaml`, which both the analysis and the chart read, so they can't disagree (as P04's `plasticity_systems.yaml`). Each zone is a polygon of (PI, Ic) vertices with its name and the method's citation.
- **On a boundary** 🟡: a point on the line between two zones takes the higher potential, so a borderline specimen is never reported as the safer one. A point on a zone's outer edge (PI = 10 or 70, Ic = 0.6 or 1.5) is in the zone. Boundaries are compared with a tolerance of 1e-9, as QC does, so 52 / 40 lands on Ic = 1.3.
- **`zones=`**: a user table in the same shape (§8) replaces the method's zones, in both the analysis and the chart, so a variant from another source can be used without being built in.

**`method="thewes_burger_2004"`** (checked against the paper, 2026-10-29; TODO #21). Four zones, listed from lowest potential to highest. As the paper draws them, high and medium-high are rectangles, medium is the border around them, and low is the rest of the diagram:

| Zone | Extent | Vertices (PI, Ic), in order |
|---|---|---|
| low | PI 0–70, Ic 0.3–1.5, outside medium | (0, 0.3), (70, 0.3), (70, 0.6), (10, 0.6), (10, 1.5), (0, 1.5) |
| medium | PI 10–70, Ic 0.6–1.5, outside the other two | (10, 0.6), (70, 0.6), (70, 0.75), (20, 0.75), (20, 1.5), (10, 1.5) |
| medium-high | PI 20–70, Ic 1.3–1.5 | (20, 1.3), (70, 1.3), (70, 1.5), (20, 1.5) |
| high | PI 20–70, Ic 0.75–1.3 | (20, 0.75), (70, 0.75), (70, 1.3), (20, 1.3) |

- **Outside the diagram** 🟡: a specimen with Ic < 0.3, Ic > 1.5 or PI > 70 is beyond what the paper draws, so `clogging_potential` is blank and the count reads "outside the diagram". It is still drawn, at the edge. Extending "low" past the axes would claim what the figure doesn't (a very plastic clay at PI 80 isn't shown to be low).
- **Validity** 🔬: as stated in the paper (soil type, machine type). Outside the stated range, the docstring says so; the function doesn't screen on soil type (that is P18's gradation step).

## 5. Figure layout
- **Panels:** single.
- **Default size:** `default` (6.5 × 4.5 in).
- **Orientation:** landscape.
- The legend goes in a clear corner (P00 §11); with the zones filling the box, usually below the x label.

## 6. Axes
| | X axis | Y axis |
|---|---|---|
| Quantity | `plasticity_index` | `consistency_index` |
| Label | `Plasticity index, PI` | `Consistency index, Ic` |
| Scale | linear | linear |
| Limits | 0–70, the paper's | 0.3–1.5, the paper's |
| Ticks | major every 10 | major every 0.1; the zone edges 0.6, 0.75 and 1.3 labeled too |
| Gridlines | major, light | major, light |

**Range constraints:**
- [x] Fixed limits regardless of data. `xlim=`/`ylim=` set them exactly. Points beyond, including every Ic below 0.3 (Ic < 0 is common in soft clays), are drawn at the edge and counted (README policy).
- [ ] Equal aspect: no; PI and Ic are different quantities.

## 7. Data marks
| Series | Mark | Color by | Legend entry | Notes |
|---|---|---|---|---|
| Specimens | scatter, 5 pt filled markers | `geology_unit` (palette) | ✔ per unit, "Unit A (n = 24)" counting the specimens drawn, at the edge or not | `color_by=None`: one neutral color, "All specimens (n = …)" |
| Beyond the limits | open marker at the edge + arrow | unit color | footnote count, "n with Ic < 0.3 shown at limit" for the bottom edge | `edge_markers()` (P00) |
| NP | none | — | — | Footnote "n non-plastic (NP) specimens not shown" |
| Blank w, LL or PI | none | — | — | Footnote "n specimens without w, LL or PL not shown" |
| PI = 0 | none | — | — | Footnote "n specimens with PI = 0 not shown" (Ic undefined) |

**Draw order (bottom → top):** zone fills → zone outlines → zone labels → specimens → specimen labels → footnote.

## 8. Overlays and annotations
| Overlay | Argument | Default | Source | Style | Notes |
|---|---|---|---|---|---|
| Zones | `method=` / `zones=` | `"thewes_burger_2004"` | config, cited | fill alpha 0.2, from green (low) through yellow and orange to red (high) as the potential rises (one step per zone, in the table's order); outline 0.8 pt in the same hue | Color is never the only carrier: each is labeled |
| Zone labels | `zone_labels=` | on | config | 8 pt gray on a white background, at the centroid of the zone's largest convex piece (as P04) | Medium's largest convex piece is its bottom strip (50 × 0.15) or its left strip (10 × 0.75), whichever is larger on screen |
| Zone counts | `zone_counts=` | on | the analysis | added to the footnote, one line: "High: 14 · Medium-high: 3 · Medium: 22 · Low: 8 · outside the diagram: 5 of 52 specimens" | Counts the specimens placed, so they match `clogging_potential` |
| Specimen labels | `labels=` | off | `specimen_id` | 6 pt beside each point | |
| Note | `note=` | off | user | added to the footnote | |

**`zones=` format** (`ht.template("clogging_zones")`): one row per vertex, in order around the polygon: `label, plasticity_index, consistency_index`. Zones are listed from the lowest potential to the highest; that order sets the colors and settles points on a shared boundary, so no new column is needed. Rows sharing a `label` make one polygon, closed automatically. Fewer than three vertices is an error naming the zone. Same shape as P04's `regions=`.

## 9. Units behavior
Nothing converts: PI is a percentage and Ic is dimensionless. `display_units` is accepted for the plot contract and changes nothing, so one figure serves US and SI.

## 10. API
```python
def clogging_potential(
    df: pd.DataFrame,
    *,
    method: Literal["thewes_burger_2004"] = "thewes_burger_2004",
    zones: pd.DataFrame | str | None = None,     # DataFrame or CSV path
) -> pd.DataFrame: ...

def clogging_diagram(
    df: pd.DataFrame,
    *,
    method: Literal["thewes_burger_2004"] = "thewes_burger_2004",
    zones: pd.DataFrame | str | None = None,
    color_by: str | None = "geology_unit",
    order: list[str] | None = None,
    labels: bool = False,
    zone_labels: bool = True,
    zone_counts: bool = True,
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
fig, ax = ht.plot.clogging_diagram(limits)
table = ht.analysis.clogging_potential(limits)
table.groupby("geology_unit")["clogging_potential"].value_counts()
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| Empty input | The chart with its zones and a "No data" note; no error |
| No `water_content` column | Error naming it: "Ic needs in situ water content; p.atterberg() joins it from LNMC" |
| No `liquid_limit`, or neither `plastic_limit` nor `plasticity_index` | Error from `plasticity()`, listing the columns |
| PL > LL, negative values, text in a value column | Error from `plasticity()` |
| `consistency_index` given and different from (LL − w) / PI | Kept as given (as `plasticity()` keeps a given PI) |
| PI = 0 (LL = PL) | Ic undefined: blank, not drawn, counted |
| Ic below 0.3, above 1.5 or PI above 70 | Classified by its true (PI, Ic), so outside the diagram: blank `clogging_potential`; drawn at the edge; counted on the edge line and in the zone line as "outside the diagram" |
| A `zones=` polygon with fewer than three vertices, or `label` missing | Error naming the zone |
| `color_by` names a column that isn't there | Error listing the columns (`"geology_unit"` gives the hint instead) |
| More than 12 / 30 units | README legend rules |

## 12. Acceptance criteria and tests
Listed in `docs/work/m12-clogging-diagram.md` (Spec) with the golden values.

## 13. References
- Thewes, M. & Burger, W. (2004). Clogging risks for TBM drives in clay. *Tunnels & Tunnelling International* 36(6), 28–31.

## 14. Open questions
1. 🔬 **Figure number and stated validity** (soil and machine type) from the paper (TODO #21). Axes, zones and limits are settled (§4, §6).
2. **The rest of the diagram is "low"** (decided 2026-10-29). 🟡 Beyond the axes is "outside the diagram", not low (§4).

**Pitfalls:**
- Dropping specimens with Ic below 0.3 or outside the axes instead of drawing them at the edge.
- Classifying by the clipped edge position instead of the true (PI, Ic).
- Zones identified only by color.
- A second Ic formula drifting from `plasticity()`.

## 15. Future enhancements
- P18 (Hollmann & Thewes 2013), which adds a gradation screen before the consistency check, as a second `method=`.
- Clogging potential as a P07 or P03-style count per geology unit, from the `clogging_potential` column.
