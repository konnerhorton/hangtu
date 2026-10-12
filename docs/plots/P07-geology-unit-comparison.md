# P07 — Property by geology unit

| | |
|---|---|
| **ID / function** | P07 · `ht.plot.geology_unit_comparison()`, `ht.plot.geology_unit_comparisons()` |
| **Status** | built |
| **Type** | plot (percentiles only, no analysis module) |
| **Target version** | v0.1 |
| **Depends on** | P00 (framework); reuses the P01 presets and overlay helpers (`plot/_overlays.py`) |
| **Related** | SPEC §2.6 (units), §3 (plot contract), §5 (P07 doesn't need the statistics module). TODO #15 (text in value columns), TODO #16 (other summaries). Intent: `docs/work/p07-geology-unit-comparison/intent.md` |

---

## 1. Purpose
Compares the measured values of one property, grouped by geology unit, with the range a report states for each unit. The report is usually a geotechnical baseline report (GBR), but it can be a GIR, a design basis or a previous phase's interpretation. It answers:
- Do the values we measured fall inside the ranges the report assumed?
- Which units are better or worse than the baseline, and on which side?
- Which units have too little data to say?

It ends up in GBR compliance reviews, differing site condition assessments, phase-to-phase data reports and design checks. Several properties are usually shown together on one page, so a second function lays out one panel per property.

## 2. Reference figure
The built figure, from the test data: [`visual-check.png`](../work/p07-geology-unit-comparison/visual-check.png) (SI) and [`visual-check-us.png`](../work/p07-geology-unit-comparison/visual-check-us.png) (US).

```
            Water content, w (%)
      A |   ├──◆────────────────────┤                    n = 288
        | · ·:·:·├━━━━━●━━━━━━━┤·:· · ·
      B |       ├──────◆──────┤                          n = 540
        |  · ·:·:├━━━━●━━━━━┤·:· ·
      C |         ├────◆───┤                             n = 2 (no summary)
        |            ·  ·
      D |       ├──────◆──────┤                          n = 0
        |
        +------+------+------+------+------
        0     10     20     30     40     50

   ├─◆─┤ GBR baseline p10–p90, p50    ├━●━┤ Data p10–p90, p50    · Data
```

**A good version:**
- each unit's row reads as one comparison: baseline bar above, data bar below, with the points around the data bar;
- you can tell at a glance whether the data bar sits inside, across or outside the baseline bar;
- units are in stratigraphic order and keep the colors they have on every other plot;
- every unit in the data or the baseline has a row, and the count says how much the data bar can be trusted;
- nothing is silently missing: values off the axis, on the wrong side of a log axis or flagged are all counted.

## 3. Input data
**Row grain:** one row per observation (one test result), as in P01. Depth isn't used.

**Required:** the `value` column and `geology_unit`. The plot is about units, so a missing `geology_unit` is an error, not a hint.

| Column | Description | Quantity kind | Canonical unit | US display | SI display | Req.? | Typical range | Valid range | AGS source (Phase 2) | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| *`value`* (any column, named by `value=`) | The property compared | from the preset or registry | per quantity | per quantity | per quantity | ✔ | per preset (P01 §6) | — | e.g. `LLPL.LLPL_PI`, `IVAN.IVAN_IVAN` | Must be numeric; text is an error (TODO #15) |
| `geology_unit` | Geology unit: one row of the plot per unit | — | — | — | — | ✔ | | | mapped from GEOL | Blank → a "(blank)" row at the bottom |
| `qualifier` | `"<"`, `">"`, or empty | — | — | — | — | – | | {"", "<", ">"} | value flags `LT`/`GT` | As P01: drawn as a caret, counted, summarized at the reported value |
| `non_plastic` | True if the specimen was reported NP | — | — | — | — | – | | bool | value flag `NP` | Applies to Atterberg values only (LL, PL, PI, LI, Ic): a row with `True` isn't drawn or summarized, and is counted as "non-plastic (NP)". Its water content and other values still count. Anything other than True, False or blank is an error naming the rows |

**Grouping columns used:** `geology_unit` → rows, and color (default).

**Hints:** none. `geology_unit` is required, and the optional columns (`qualifier`, `non_plastic`) don't unlock a feature an engineer would miss, so P07 issues no `HangtuHint`.

**Value flags handled:**
- `qualifier` `<` / `>`: a caret ◁ / ▷ in place of the point, counted in the legend and the footnote, as P01 §7. The summary uses the reported value.
- `non_plastic`: counted in the footnote, not drawn. NP is distinct from blank everywhere (SPEC §4).
- Text in the value column (`"NP"`, `"<5"`): an error naming the rows, as P01. TODO #15 will change this for every plot.

**Minimum data:** none. A unit with no data but a baseline row still gets a row ("n = 0"). With no data and no baseline, the plot shows empty axes and a "No data" note.

## 4. Analysis / calculations
- **Summary per unit** (`summary="percentiles"`, the default): `numpy.percentile(values, percentiles, method=percentile_method)`. `percentiles` is three ascending numbers in [0, 100], `(10, 50, 90)` by default: the bar runs from the first to the third and the marker sits at the second. `percentile_method` is passed to NumPy unchanged and must be one of its 13 methods, `"linear"` by default (NumPy's default; Hyndman & Fan 1996 definition 7). Other summaries are TODO #16.
- **Box** (`summary="box"`): quartiles with `percentile_method`, whiskers to the furthest value within 1.5 × IQR of the box (Tukey 1977). There are no separate outlier marks, because every point is already drawn.
- **Which values are summarized:** the values drawn, in display units, as for the P01 stats box. Blanks, NP rows and values ≤ 0 on a log axis are left out. Values drawn at the edge of a fixed axis count at their true value, and qualified values at their reported value. On a log axis the percentiles are of the values (percentiles don't change under a log transform, apart from the interpolation between two values).
- **Small samples:** the summary is drawn only when n ≥ `summary_min_count` (default 5, `ht.settings.summary_min_count`). Below that, the points are drawn and the count label says "(no summary)".
- **Count:** n is the number of values summarized, i.e. drawn as points or carets.
- **Unit conversion** of the data and the baseline to the display units, using the resolution order in SPEC §2.6 (§9).

## 5. Figure layout
- **Panels:**
  - `geology_unit_comparison()`: a single panel.
  - `geology_unit_comparisons()`: one panel per value, in a grid `columns=2` wide, filled row by row; an odd last panel leaves its cell empty. Each panel has its own value axis, limits and units. One legend for the whole figure, centered below the grid.
- **Default size:**
  - single panel: the global `default` size (6.5 × 4.5 in).
  - grid: a new `grid` kind in `ht.settings.figure_sizes`, **per panel** (3.75 × 2.75 in), plus 0.6 in for the shared legend, plus 8.5 pt per footnote line. Six panels in two columns make 7.5 × 8.85 in, which fits a Letter page with 0.5 in margins. `figsize=` sets the size of the whole figure, and it is not grown for the footnote.
  - The shared legend (up to 4 entries per row) and the footnote below it sit in a band at the bottom of the figure that the panels are kept out of. Qualifier entries total their counts over the panels; each footnote line starts with its panel's quantity, e.g. "Consistency index, Ic: 4 values beyond axis limit, shown at the edge". Each panel's own counts are in its `ax.ags_notes`.
- **Orientation:** horizontal only: units on the vertical axis, values across.

## 6. Axes

| | X axis (value) | Y axis (geology units) |
|---|---|---|
| Quantity / column | `value` | `geology_unit` (categorical) |
| Label (US) | from the preset or registry, e.g. `Undrained shear strength, s_u (psf)` | none (the tick labels are the unit names) |
| Label (SI) | e.g. `Undrained shear strength, s_u (kPa)` | none |
| Scale | linear or log (from the preset or `log=`) | categorical, one row per unit, equally spaced |
| Direction | normal | first unit at the top |
| Position | bottom | left |
| Limits rule | P00 §8 over the data **and** the baseline values (so a baseline bar is never cut off by default); fixed preset limits if set; `xlim=` overrides | half a row above the first unit and below the last |
| Major / minor ticks | as P00 §8 | one tick per unit, no minor ticks |
| Gridlines | vertical, major (minor on log only) | **none** (deviation from the house style: horizontal lines between units would cross the bars) |

**Presets:** the P01 presets apply. Unlike P01, `preset=None` means "the preset named after the value column, if there is one", so `geology_unit_comparisons(df, ["water_content", "hydraulic_conductivity"])` gets the right labels and a log axis for k without a preset per panel. `preset=` and `log=` still override.

**Unit order:** units in `order=` come first, in that order, then the rest sorted by name, then "(blank)". This is the same order the palette uses (P00 §10). A unit in `order=` with no data and no baseline row gets no row.

**Range constraints:**
- [ ] Equal aspect: no.
- [ ] Shared limits: no. Each panel of the grid has its own value axis.
- [x] Log axis: whole decades, at least 2 (P00 §8).

## 7. Data marks

Each unit's row is one unit of height, centered on its tick. Offsets are fractions of that height, measured upward from the center. Rows sit at y = 0, 1, 2, … on an inverted axis, so the first unit is at the top. The jitter comes from `numpy.random.default_rng(0)`, drawn once per call in data order, so the same data gives the same figure in US and SI.

| Series | Mark | Color by | Position in the row | Size / width | Legend entry | Notes |
|---|---|---|---|---|---|---|
| Baseline bar | horizontal line from `low` to `high`, with end caps | neutral dark gray (`0.25`), the same for every unit | +0.28 | 1.2 pt, caps 0.12 high | ✔ `baseline_label` (§8) | Drawn when the unit has a baseline row with `low` and `high` |
| Baseline central value | diamond ◆ at `central` | dark gray | +0.28 | 5 pt | (part of the bar's entry) | Only when `central` is given. A row with only `central` draws just the diamond |
| Data points | scatter, jittered vertically | `geology_unit` (palette); one neutral data color with `color_by=None` | center ± 0.15, uniform | 3 pt, alpha 0.4, no edge | ✔ "Data" | Jitter is seeded, so the same data gives the same figure |
| Data bar (percentiles) | horizontal line from the first to the third percentile, with end caps | unit color | center | 2.0 pt, caps 0.16 high | ✔ e.g. "Data p10–p90, p50" | Drawn over the points. Only when n ≥ `summary_min_count` |
| Data central percentile | filled circle at the second percentile | unit color, white edge 0.8 pt | center | 6 pt | (part of the bar's entry) | |
| Data box (`summary="box"`) | box from the 25th to the 75th percentile, median line, whiskers with caps | unit color edges, white fill at alpha 0.6 | center, 0.3 high | 1.0 pt | ✔ "Data: quartiles, median, 1.5 IQR whiskers" | Replaces the bar and circle. Drawn as a patch and lines rather than `ax.bxp`, whose arguments changed in matplotlib 3.10 |
| Qualified values | caret ◁ / ▷ at the value, jittered as the points | unit color | center ± 0.15 | 5 pt | ✔ "less than (n)" / "greater than (n)" | As P01 §7 |
| Out-of-range values (fixed limits) | open marker at the axis edge + small arrow outward | unit color | jittered as the points | 3 pt | footnote | P00 §9. A bar or box running past a fixed limit is cut at the edge without its cap, so it reads as continuing. When a value lies beyond the lower limit, the unit names move 14 pt left so the arrows don't cover them |
| Count label | text "n = 288" | black (gray 0.4 for "n = 0") | center line, just outside the right spine | 7 pt | — | "n = 2 (no summary)" below `summary_min_count`. The legend and footnote move right to clear the widest label. When a value lies beyond the upper limit, the labels move a further 14 pt right to clear its edge arrow |

**Legend:** the marks are explained once, by gray stand-ins for the data bar and points (the unit colors are already named by the tick labels, so there is no per-unit color legend, a deviation from the plots README). Order: baseline, data summary, data points, then qualifiers and edge markers with counts. A single panel puts the legend outside on the right, moved right to clear the count labels (`add_legend(..., offset=)`), with the footnote below it. The grid puts one legend centered below all panels, with one footnote below it.

**Draw order (bottom → top):** reference lines → baseline bars → data points and carets → data bars or boxes → central markers → count labels → notes.

## 8. Overlays and annotations

| Overlay | Argument | Default | Source of definition | Style | Notes |
|---|---|---|---|---|---|
| Baseline | `baseline=` DataFrame or CSV path | off | User: the report's ranges (format below) | §7 | A CSV path is read with `ht.read_csv` |
| Baseline legend text | `baseline_label=` str | the table's `source` if it has one value, else "Baseline" | User | legend text | Says what the report's range is, e.g. "GBR baseline p10–p90, p50" or "GIR typical range". hangtu never adds a definition the user didn't give |
| Reference lines | `reference_lines=` list of `(value, label)` | off | User | As P01 §8: thin dotted vertical line, label above the axes | e.g. a design value that applies to every unit |
| Note | `note=` str | off | User | Lower-left text, 7 pt | |
| Exclusion notes | automatic | **on** | Counts of ≤ 0 on log, beyond limit, qualified, NP | Footnote below the legend, 7 pt gray | Blank values aren't counted: a blank cell in a wide table is a test not done (§14) |

There is no stats box: the count label and the summary bar already carry n and the percentiles. A stats box can come later (§15).

**Baseline format** (`ht.template("baseline")`):

| Field | Required | Description |
|---|---|---|
| `geology_unit` | ✔ | The unit the range applies to |
| `property` | when the table covers more than one property | The value column the row applies to, e.g. `water_content`. Rows for other properties are ignored |
| `low` | ✔ with `high` | Lower end of the report's range |
| `central` | – | The report's central value (p50, mean, "typical"; `baseline_label` says which) |
| `high` | ✔ with `low` | Upper end of the report's range |
| `source` | – | Citation, e.g. "GBR Table 4-2"; used for the default legend text |

- Rows are filtered to the plotted property first, so the checks below apply only to the rows being drawn.
- A row needs `low` and `high`, or `central` alone. A row with neither is not drawn, and a warning names it. A row with only one of `low` and `high` draws no bar (just its `central`, if any), and a warning names it.
- A row with `low` > `high` is not drawn, and a warning names it (as P01 ranges).
- Two rows for the same unit and property are an error naming them.
- A baseline row with a blank `geology_unit` is not drawn, and a warning names it.
- On a log axis, a `low` ≤ 0 starts the bar at the axis edge (as P01 ranges).
- Without a `property` column, every row applies to the plotted value. In the grid with more than one value, a table without `property` is an error saying to add it.
- `property`, `central` are fields of the overlay table (`columns.yaml` `fields:`), like `low` and `high`. They were checked against the registry, the presets and the unit aliases.

**Baseline units:**
1. `baseline_units=` `{property: unit}`, e.g. `{"bulk_unit_weight": "kN/m3", "undrained_shear_strength": "kPa"}`. This is the only way to give different units for different properties in one long table, since `df.attrs["units"]` is per column.
2. Units declared on the table's `low`, `central` and `high` with `ht.set_units` (single-property tables, as P01 ranges).
3. Otherwise the value column's units, with one warning per call that shows both ways to declare them.

A `baseline_units` key that is neither a `property` in the table nor the plotted value is an error naming it, to catch typos. A unit of the wrong kind (a length for s_u) is a `UnitsError`.

## 9. Units behavior
- **Value axis:** converted according to the preset or registry quantity, as P01 §9 (s_u psf / kPa, unit weight pcf / kN/m³, k cm/s / m/s, % in both).
- **Baseline:** converted from its declared units (§8) to the display units of its panel. The report's own unit appears only in `source` or `baseline_label`, if the user writes it there.
- **Percentiles** are computed after conversion; a linear conversion doesn't change which values they fall between, so US and SI give the same bars.
- **Not converted:** % values, counts, dimensionless values (consistency index, Miller number).

## 10. API
```python
def geology_unit_comparison(
    df: pd.DataFrame,
    value: str,
    *,
    baseline: pd.DataFrame | str | None = None,
    baseline_label: str | None = None,
    baseline_units: dict[str, str] | None = None,       # {property: unit}
    summary: Literal["percentiles", "box"] | None = "percentiles",   # None -> points only
    percentiles: tuple[float, float, float] = (10, 50, 90),
    percentile_method: str = "linear",                  # numpy.percentile(method=...)
    summary_min_count: int | None = None,               # None -> settings (5)
    points: bool = True,
    preset: str | None = None,                          # None -> the preset named after `value`, if any
    log: bool | None = None,
    label: str | None = None,
    xlim: tuple[float, float] | None = None,
    order: list[str] | None = None,                     # stratigraphic order of geology units, top first
    color_by: Literal["geology_unit"] | None = "geology_unit",
    reference_lines: list[tuple[float, str]] | None = None,
    note: str | None = None,
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,        # None -> settings "default" size
    ax: Axes | None = None,
    **style_overrides,
) -> tuple[Figure, Axes]: ...


def geology_unit_comparisons(
    data: pd.DataFrame | dict[str, pd.DataFrame],       # one table, or {value: table} per panel
    values: list[str],                                  # one panel per value, in this order
    *,
    columns: int = 2,
    baseline: pd.DataFrame | str | None = None,         # long table with a `property` column
    preset: dict[str, str] | None = None,               # per value; default as above
    log: dict[str, bool] | None = None,
    label: dict[str, str] | None = None,
    xlim: dict[str, tuple[float, float]] | None = None,
    reference_lines: dict[str, list[tuple[float, str]]] | None = None,
    figsize: tuple[float, float] | None = None,         # whole figure; None -> settings "grid" per panel
    # every other argument of geology_unit_comparison except `value`, `note` and `ax`,
    # written out in the signature and applied to all panels
    **style_overrides,
) -> tuple[Figure, np.ndarray]: ...       # axs[i] is the panel of values[i]
```

- The grid takes one table holding every value column, or a dict with one table per value, because properties often come from different tests (water content from the index tests, s_u from the vane tests). Each table keeps its own declared units.
- Per-panel arguments are dicts keyed by value. A key that isn't in `values` is an error naming it.
- The grid has no `ax=`: to put panels on a `Sheet`, call `geology_unit_comparison(ax=sheet[i])` per panel.

**Examples:**
```python
index = ht.read_csv("index.csv", units={"water_content": "%", "bulk_unit_weight": "pcf"})
gbr = ht.read_csv("gbr_baseline.csv")
fig, ax = ht.plot.geology_unit_comparison(
    index, "water_content", baseline=gbr,
    baseline_label="GBR baseline p10–p90, p50", order=["A", "B", "C", "D", "E", "F"],
)

fig, axs = ht.plot.geology_unit_comparisons(
    {"water_content": index, "bulk_unit_weight": index, "undrained_shear_strength": vane},
    ["water_content", "bulk_unit_weight", "undrained_shear_strength"],
    baseline=gbr, baseline_units={"bulk_unit_weight": "kN/m3", "undrained_shear_strength": "kPa"},
    baseline_label="GBR baseline p10–p90, p50", display_units="SI",
)
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| Empty input and no baseline | Empty axes with a "No data" note; no error |
| A unit with a baseline but no data | Row with the baseline bar and "n = 0" |
| A unit with data but no baseline | Row with the data only; nothing marks the missing baseline beyond its absence |
| n < `summary_min_count` | Points only; "n = 2 (no summary)" |
| All values in a unit equal | A zero-length bar, visible through its caps and circle |
| Missing `value` or `geology_unit` column | Error naming the column and the columns available |
| Blank `geology_unit` | A "(blank)" row at the bottom, in neutral gray |
| Units unknown for the value | Drawn with "(units unknown)" in the label, plus a warning (SPEC §2.6); the baseline is then drawn as given |
| Values ≤ 0 on a log axis | Not drawn or summarized; counted in the footnote |
| Blank values | Not drawn, summarized or counted: a test not done (§14) |
| Values beyond `xlim` | Edge marker + arrow + count; still summarized at their true value |
| Text in the value column | Error naming the rows (TODO #15) |
| `qualifier` other than `"<"`, `">"` or blank | Error listing the rows and values found (as P01) |
| `percentiles` not three ascending numbers in [0, 100] | Error with an example |
| Unknown `percentile_method` | Error listing NumPy's methods |
| Baseline problems | §8 (warnings for rows not drawn, errors for duplicates and a missing `property`) |
| Baseline `geology_unit` not in the data | Gets a row, "n = 0" (it's often a typo; the row makes it visible) |
| More than ~15 units in one panel | Drawn; rows get tight. No legend problem, since units are tick labels |
| More than 20 units | Colors repeat, with the palette's warning (P00 §10) |
| `summary_min_count` < 1 | Error |

## 12. Acceptance criteria and tests
- **Golden values** (hand-calculated, NumPy linear method):
  - values 1–10: p10 = 1.9, p50 = 5.5, p90 = 9.1;
  - values [2, 4, 4, 5, 7, 9]: p10 = 3.0, p50 = 4.5, p90 = 8.0; quartiles 4.0 and 6.5, whiskers 2 and 9;
  - the same values with `percentile_method="hazen"`: p10 = 2.2, p50 = 4.5, p90 = 8.8 (rank h = n·p + 0.5, e.g. h = 1.1 → 2 + 0.1 × (4 − 2));
  - 2,000 psf ↔ 95.76 kPa for a baseline bar given in kPa and plotted in US.
- **Visual checks:**
  - units top to bottom in `order`, then by name, then "(blank)";
  - baseline bar above, data bar on the center line, points around it;
  - a unit with n = 0 and one below `summary_min_count` labeled as such;
  - the legend says the percentiles and method used, and the baseline text as given;
  - unit colors match `ht.plot.legend_handles()`.
- **Automated:**
  - renders for each preset, linear and log, both summaries and `summary=None`;
  - percentiles drawn at the golden values (read back from the artists);
  - every unit in the data or baseline has a row; units missing from both don't;
  - baseline rows: missing, duplicate, `low` > `high`, blank unit, `central` only, multi-property without `property`;
  - `baseline_units`, declared table units and the fallback warning;
  - counts in `ax.ags_notes`: ≤ 0 on log, beyond limit, qualifiers, NP;
  - jitter is the same on two calls;
  - `ax=` draws into a Sheet panel; the grid lays out 1, 2, 5 and 6 panels;
  - **US vs SI:** the same bar positions after conversion and the same counts;
  - no change to global `rcParams`.
- **Test data** (synthetic CSVs in `tests/data/`):
  - `comparison_index.csv`: 6 units; water content and bulk unit weight (a unit with n = 2, a unit with none); plasticity and consistency indices in two units, with 3 NP specimens and 4 consistency indices below −0.6; US units;
  - `comparison_vane.csv`: s_u in two units, one `<` value, SI units;
  - `comparison_perm.csv`: k in three units, cm/s;
  - `comparison_baseline.csv`: long baseline for six properties in SI, a unit with no data, one `central`-only row, units declared with `baseline_units`.

## 13. References
- Hyndman, R.J. & Fan, Y. (1996). Sample quantiles in statistical packages. *The American Statistician* 50(4), 361–365. Definitions of the percentile methods NumPy offers.
- Tukey, J.W. (1977). *Exploratory Data Analysis*. Addison-Wesley. Box plot whiskers.
- ASCE (2007). *Geotechnical Baseline Reports for Construction: Suggested Guidelines*. Technical Committee on Geotechnical Reports of the Underground Technology Research Council. What a baseline states and how it is used.

## 14. Open questions
None open. Decided in review:
- **Blank values aren't counted** in P07's footnote (§8). The data tables are wide: the registry gives each property its own column (the `index` template holds `water_content` and `bulk_unit_weight` side by side, one row per sample), so a blank cell means the test wasn't done on that sample, not a missing value. Counting them would fill the footnote with tests that were never run. NP and qualified values are still counted. This differs from P01, which counts blanks.
- **Baseline units** for a long table come from `baseline_units={property: unit}`, keeping units as metadata rather than a unit column (§8).
- **`preset=None`** picks the preset named after the value column, in P07 only (§6).

## 15. Future enhancements
- Other summaries (min–max, mean ± k·σ, log-space statistics, user-computed values): TODO #16.
- A stats box per unit, once `ht.stats.describe` exists (Phase 3).
- Marking where the data bar falls outside the baseline (e.g. a shaded overlap, or a flag on the count label). Pass/fail tests belong to `ht.stats.compare` (Phase 3).
- Rows split by depth or elevation within a unit, and grouping by something other than geology unit (`group_by=`).
- Vertical orientation.
