# P01 — Property profile

| | |
|---|---|
| **ID / function** | P01 · `ak.plot.profile()` |
| **Status** | approved |
| **Type** | plot (no analysis, apart from computing elevation) |
| **Target version** | v0.1 |
| **Depends on** | P00 (framework: style, palette, unit resolution, out-of-range markers, legend rules) |
| **Related** | P02 SPT profile, P06 water content profile and P09 characteristic profile all build on this function. SPEC §2.6 (units for DataFrames), §8 (depth conventions) |

---

## 1. Purpose
Shows how **any single property varies with depth or elevation**, across one or many exploratory holes, colored by geology unit. It answers questions like:
- Is there a trend with depth?
- Do the units separate clearly?
- Are there outliers or suspicious holes?
- How do lab and field values compare?

It's the most-used plot in a factual or interpretive report, and the base the other profile plots build on. It needs a **log x-axis** for properties that span orders of magnitude (hydraulic conductivity).

It ends up in ground investigation reports (data presentation), interpretive and design reports (with design lines and ranges), and internal checks.
## 2. Reference figure
```
              Hydraulic conductivity, k (cm/s)
        10⁻⁷     10⁻⁶     10⁻⁵     10⁻⁴     10⁻³          ← x axis drawn at top here (default is bottom)
   120 ┼────────┼────────┼────────┼────────┼──┐
       │ ░░░░░░░░░░░░░ Fill ░░░░░░░░░░░░░░░░░░│ ▽ GWL      ← strata band + label (optional)
   110 ┤             ●     ○                   │
       │      ◁        ●  ┃                    │            ┃ = test interval (field test)
   100 ┤ ▒▒▒▒▒▒▒▒▒▒▒▒ Alluvium ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│            ◁ = "less than" value
       │                    ●   ●  ○           │            ● lab   ○ field (marker_by="source")
    90 ┤                 ●    ●     ●          │
 Elev  │            ┊ design line               │    Legend (outside right):
 (ft,  ┤  ▓▓▓▓▓▓▓▓▓ Upper Clay ▓▓▓▓▓▓▓▓▓▓▓▓▓▓│     ■ Fill  ■ Alluvium  ■ Upper Clay
 NAVD88)│   ●  ●  ●                           │     ● lab  ○ field
    70 ┼────────────────────────────────────────┘     ◁ less than (1)
                                                      "2 values ≤ 0 not shown on log axis"
```

**A good version:**
- the vertical axis reads naturally (elevation up, or depth down from 0);
- unit colors are the same as on every other plot;
- the x-axis covers whole decades on a log scale;
- nothing is silently missing: all exclusions and edge-clipped points are counted.

## 3. Input data
**Row grain:** one row per observation (one test result at one depth).

**Required:** the `value` column, plus **one of** `depth` or `elevation`. Everything else is optional. When optional columns that unlock features are missing, the plot emits one hint naming them and what they add (plots README, "Input data"). For example: "No `geology_unit` column: points are not colored by geology. No `loca_id`: `connect=` and per-hole water levels are unavailable."

| Column | Description | Quantity kind | Canonical unit | US display | SI display | Req.? | Typical range | Valid range | AGS source (Phase 2) | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| *`value`* (any column, named by the `value=` argument) | The property plotted | from the preset or registry | per quantity | per quantity | per quantity | ✔ | per preset (§6) | per preset | e.g. `PTST.PTST_K`, `FGHG.FGHG_IPRM` | Must be numeric. NaN rows dropped and counted |
| `depth` | Test depth below ground level | length | m | ft | m | ✔ one of `depth` / `elevation` | 0–60 m | ≥ 0 | SPEC §8.2 | The point plotted for interval tests (e.g. the zone midpoint) |
| `elevation` | Elevation of the test | length | m | ft | m | ✔ one of `depth` / `elevation` | site-dependent | any | derived | Computed from `ground_level − depth` if absent and both are given |
| `ground_level` | Ground level at the hole | length | m | ft | m | – | site-dependent | any | `LOCA.LOCA_GL` | With `depth` and no `elevation` column, elevation = `ground_level − depth` is computed |
| `depth_top`, `depth_base` | Top and base of the tested interval | length | m | ft | m | – | | top ≤ base | e.g. `FGHG_TOP/BASE`, `SAMP_TOP/BASE` | If present, the interval is drawn as a bar (§7) |
| `loca_id` | Exploratory hole ID | — | — | — | — | – | | | `LOCA.LOCA_ID` | Used for `connect=`, `marker_by=`, `secondary=` |
| `geology_unit` | Geology unit | — | — | — | — | – | | | mapped from GEOL | Default color grouping |
| `qualifier` | `"<"`, `">"`, or empty | — | — | — | — | – | | {"", "<", ">"} | value flags `LT`/`GT` | The true value is less than or greater than the plotted value |
| *any column* | Secondary grouping for marker shape | — | — | — | — | – | | | e.g. `source` (lab/field), `test_type` | Named by `marker_by=` |

**Grouping columns used:** `geology_unit` → color (default); `marker_by=` column → marker shape; `loca_id` → connecting lines.

**Value flags handled:**
- `qualifier="<"`: drawn as a left-pointing caret ◁ at the value;
- `qualifier=">"`: a right-pointing caret ▷;
- both are counted in the legend.

**Minimum data:** ≥ 1 valid point. With 0 points the plot shows empty axes and a "No data" note, without raising an error.

## 4. Analysis / calculations
n/a, apart from:
- **Elevation**, if needed: `elevation = ground_level − depth`, per row (SPEC §8.1). Interval bounds become elevations the same way.
- **Unit conversion** of every input and overlay to the display units (pint), using the resolution order in SPEC §2.6.
- **Log-axis exclusion:** values ≤ 0 can't be drawn on a log axis. They are excluded and counted in a note ("n values ≤ 0 not shown on log axis").

## 5. Figure layout
- **Panels:** single.
- **Default size:** the global `profile` size from settings (4.0 × 6.5 in plotting area, portrait, plus legend width; about 5.5 × 6.5 in in total with an outside legend). `figsize=` overrides it for one call (plots README, "Output").
- **Orientation:** portrait.

## 6. Axes

| | X axis (value) | Y axis (vertical) | Secondary Y (optional) |
|---|---|---|---|
| Quantity / column | `value` | `elevation` or `depth` (`vs=`) | depth, when `vs="elevation"` |
| Label (US) | from preset, e.g. `Hydraulic conductivity, k (cm/s)` | `Elevation (ft, NAVD88)` / `Depth (ft)` | `Depth (ft)` |
| Label (SI) | e.g. `Hydraulic conductivity, k (m/s)` | `Elevation (m, <datum>)` / `Depth (m)` | `Depth (m)` |
| Scale | linear or log (from the preset or `log=`) | linear | linear |
| Direction | normal | elevation: up · depth: **inverted** (0 at top) | inverted |
| Position | **bottom** (decided; `xaxis_position="top"` gives the borehole-log convention) | left | right |
| Limits rule | linear: from 0 if the preset is ratio-scale, else padded "nice" limits · log: whole decades enclosing the data · fixed preset limits if set · `xlim=` overrides | depth: 0 → nice ceiling of max depth/base · elevation: nice floor/ceiling with 5% padding · `ylim=` overrides | follows the primary axis |
| Major / minor ticks | linear: nice steps (1-2-5) · log: decades labeled `10ⁿ`, minor 2–9 unlabeled | nice steps (e.g. every 5 or 10 ft, 2 or 5 m) | same |
| Gridlines | major; minor on log only | major | none |

**Range constraints:**
- [ ] Equal aspect: no.
- [ ] Shared limits: no (but `ylim=` lets users align profiles placed side by side on a Sheet).
- [x] Log axis: always a whole number of decades, and at least 2.
- [x] Secondary depth axis **only when all rows share one ground level** (a single hole, or an idealized profile). Otherwise `secondary="depth"` raises a clear error, because the depth↔elevation mapping would be ambiguous.

**Presets** (general rules in the plots README, "Presets"):

| Preset | Column (registry) | Label | Quantity / US / SI unit | Scale | Start at 0 | Typical range (default axis) | Valid range |
|---|---|---|---|---|---|---|---|
| `hydraulic_conductivity` | `hydraulic_conductivity` | Hydraulic conductivity, k | hydraulic conductivity / cm/s / m/s | log | — | 1e-11 to 1e-2 m/s (1e-9 to 1 cm/s) | > 0 |
| `undrained_shear_strength` | `undrained_shear_strength` | Undrained shear strength, s_u | stress / psf / kPa | linear | yes | 0–300 kPa (0–6,000 psf) | ≥ 0 |
| `water_content` | `water_content` | Water content, w | % / % / % | linear | yes | 0–100% (organic soils up to 300%+) | ≥ 0 |
| `bulk_unit_weight` | `bulk_unit_weight` | Bulk unit weight, γ | unit weight / pcf / kN/m³ | linear | **no** | 14–23 kN/m³ (90–145 pcf) | 8–30 kN/m³ |
| *(none)* | any | `value` column name, or `label=` | from `df.attrs`/`units=` | `log=` (default linear) | yes if registry scale = ratio | data | — |

Presets live in `config/defaults.yaml`, with the typical range in the quantity's canonical unit (converted to display units when used). The valid ranges above are for reference only and aren't stored: nothing in P01 uses them, and QC level 2 (v0.4) will have its own ranges.

## 7. Data marks

| Series | Mark | Color by | Marker by | Size / width | Legend entry | Notes |
|---|---|---|---|---|---|---|
| Observations | scatter | `geology_unit` (palette); a single neutral color if `color_by=None` or the column is absent | `marker_by=` column (default: all circles) | 5 pt markers | ✔ per unit, ✔ per marker group | Filled markers |
| Test intervals | thin vertical line from `depth_top` to `depth_base` at x = value | same as the marker | — | 1.0 pt, round caps | — | `intervals="auto"`: drawn when both columns exist; `True` without them is an error. In elevation, each row uses its own ground level (`ground_level`, or `elevation + depth`); with neither, bars aren't drawn and a warning says why. Bounds count toward the vertical limits. No bar for a value drawn at the edge |
| Connecting lines | line through each hole's points, sorted by vertical position | neutral gray (holes cross units) | — | 0.6 pt, alpha 0.6 | — | Only with `connect=True`; off by default |
| Qualified values | caret ◁ / ▷ at the value | unit color | — | 6 pt | ✔ "less than (n)" / "greater than (n)" | Replaces the normal marker. Also counted in the footnote. Beyond a fixed limit, the caret is drawn open at the edge and counted both ways |
| Out-of-range (fixed limits) | open marker at the axis edge + small arrow pointing outward | unit color | — | 5 pt | ✔ footnote "n values beyond axis limit" | README policy |

**Marker cycle** for `marker_by`: ● ■ ▲ ◆ ▼ ✚ ✖ ⬟ ⬢ ★ (10 shapes), given to the groups sorted by name, with a "(blank)" group last. Beyond 10 groups, the shapes repeat and a warning suggests `connect=True` or splitting the data. With `marker_by`, the legend shows geology units as color patches, then the groups as gray markers.

**Draw order (bottom → top):** strata bands → ranges → reference and design lines → water level → interval bars → connecting lines → markers → qualifiers → annotations and notes.
## 8. Overlays and annotations

| Overlay | Argument | Default | Source of definition | Style | Notes |
|---|---|---|---|---|---|
| Strata bands | `strata=` DataFrame | off | User: `geology_unit` plus a depth or elevation pair (formats below) | Full-width horizontal bands in palette colors, alpha 0.12; unit name at the right edge inside the axes, 7 pt | Only meaningful for one stratigraphy (a single hole or an idealized profile). The user is responsible for that |
| Water level | `water_level=` float, or list of `(value, label)` | off | User | Dashed blue line 0.8 pt, ▽ symbol and label at the right end ("GWL" by default) | In the units of `vs` (declared or display) |
| Water level per hole | `water_level=` DataFrame: `loca_id, depth\|elevation[, label]` | off | User | Short ▽ tick at the right edge of the axes for each hole, labeled with `loca_id` when there are ≤ 6 holes | For several holes with different water levels. Units from `df.attrs` or `units=` |
| Published ranges | `ranges=` DataFrame or CSV | off | User: `low, high, label, source`, plus an optional depth or elevation pair (formats below) | Vertical translucent band (alpha 0.15, hatched outline) from low to high, over top–base or the full height. Label at the top | Values converted from the declared units |
| Design lines | `design_lines=` DataFrame | off | User or P09: `label, <vs column>, value` (one polyline per label) | Bold dashed 1.5 pt, dark gray; label at the line end | Same idea as AGSi parameter profiles; P09 produces these |
| Reference lines | `reference_lines=` list of `(value, label)` | off | User | Thin vertical line 0.6 pt, dotted; label at the top | e.g. a code limit |
| Stats box | `stats_box=True`, or a list of statistics | off | pandas (no scipy needed). Default: count, mean, std, median, min, max per unit. A list chooses the statistics, e.g. `stats_box=["count", "mean", "cov"]`; allowed: `count, mean, std, cov, median, min, max` | Text box, lower left, 7 pt | ≤ 6 units listed; otherwise overall only. std is shown as "—" when n < 2. On a log axis, statistics are of the plotted values (not log values) |
| Exclusion notes | automatic | **on** | Counts of NaN, ≤ 0 on log, beyond-limit, qualified | Footnote below the legend, 7 pt gray | **Always shown when non-zero** (no silent drops) |
| Note | `note=` str | off | User | Lower-left text, 7 pt | |

**User-supplied overlay formats** (`ak.template("strata")`, `"ranges"` and `"design_lines"` give the exact columns; the templates list both the depth and the elevation form, so fill in one and leave the other blank. A pair whose columns are all blank counts as absent):
- `strata`: `geology_unit` plus **either** `depth_top, depth_base` **or** `elevation_top, elevation_base`.
- `ranges`: `low, high, label, source`, plus optionally **either** `depth_top, depth_base` **or** `elevation_top, elevation_base` (otherwise the range covers the full height).
- `design_lines`: `label, depth|elevation, value`.

**Vertical reference of strata and ranges:**
- A pair that matches `vs` is drawn as given. Elevation strata are what make an idealized site profile over several holes possible.
- A pair that doesn't match `vs` is converted with `ground_level` (SPEC §8.1), which must be a single value for all rows of the main data (the same rule as `secondary="depth"`, §6).
- In depth, top ≤ base; in elevation, top ≥ base. A row with its top and base the wrong way round is not drawn, and a warning names it.
- `low`, `high`, `label` and `value` are fields of the overlay table, not data columns. They are listed in the `fields:` section of `columns.yaml`, so templates can use them, but `ak.columns()` leaves them out. `source` is the registry column.

Units come from `df.attrs` or `units=`; otherwise they are assumed to match the main data, with a warning.

## 9. Units behavior
- **Vertical:** ft (US) / m (SI). The datum appears in elevation labels from `settings.vertical_datum`; if it isn't set, the label is just "Elevation (ft)".
  - The length columns (`depth`, `elevation`, `ground_level`, `depth_top`, `depth_base`) are converted together, and each is converted before any subtraction. If any of them has no units, none is converted: all are drawn as given, the label says "(units unknown)", and the usual warning names the column.
  - With `vs="depth"` and no `depth` column, depth is `ground_level − elevation`.
- **Value:** converted according to the preset or registry quantity.
  - k: cm/s (US, decided) / m/s (SI). A log axis keeps whole decades in either unit, since the conversion is a factor of 100.
  - s_u: psf / kPa (per-quantity override, e.g. ksf).
  - Unit weight: pcf / kN/m³.
  - Moisture: % in both.
- **Overlays** are converted from their declared units to the display units.
- **Not converted:** % values, counts.

## 10. API
```python
def profile(
    df: pd.DataFrame,
    value: str,
    *,
    vs: Literal["elevation", "depth"] | None = None,  # None -> elevation if available (column, or depth + ground_level), else depth
    preset: str | None = None,              # "hydraulic_conductivity" | "undrained_shear_strength" | "water_content" | "bulk_unit_weight"
    log: bool | None = None,                # None -> from the preset (else linear)
    label: str | None = None,               # x-axis quantity text; units are appended automatically
    color_by: str | None = "geology_unit",
    marker_by: str | None = None,
    connect: bool = False,                  # lines per loca_id
    intervals: bool | Literal["auto"] = "auto",
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    xaxis_position: Literal["top", "bottom"] = "bottom",
    secondary: Literal["depth"] | None = None,
    # overlays
    strata: pd.DataFrame | None = None,
    water_level: float | list[tuple[float, str]] | pd.DataFrame | None = None,  # DataFrame = per hole
    ranges: pd.DataFrame | str | None = None,
    design_lines: pd.DataFrame | None = None,
    reference_lines: list[tuple[float, str]] | None = None,
    stats_box: bool | list[str] = False,    # True -> count, mean, std, median, min, max
    note: str | None = None,
    # common
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,     # explicit units for input columns (overrides df.attrs)
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,  # None -> settings "profile" size
    ax: Axes | None = None,
    **style_overrides,
) -> tuple[Figure, Axes]:
```

**Examples:**
```python
k = ak.read_csv("perm.csv", units={"depth": "ft", "depth_top": "ft", "depth_base": "ft",
                                   "ground_level": "ft", "hydraulic_conductivity": "cm/s"})
fig, ax = ak.plot.profile(k, "hydraulic_conductivity", preset="hydraulic_conductivity", marker_by="source",
                          water_level=[(112.5, "GWL (2026-03)")])

su = ak.read_csv("su.csv", units={"elevation": "ft", "undrained_shear_strength": "psf"})
fig, ax = ak.plot.profile(su, "undrained_shear_strength", preset="undrained_shear_strength", vs="elevation",
                          ranges=pd.DataFrame({"low": [1000], "high": [2000],
                                               "label": ["stiff"], "source": ["Terzaghi & Peck"]}),
                          display_units="SI")
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| Empty input, or all values NaN | Empty axes with a "No data" note; no error |
| Single point | Plotted. Axis limits come from the preset's typical range (or ±1 nice step) so the point isn't on the frame |
| Missing `value` column | `KeyError`-style message: "Column 'k' not found. Available columns: …" |
| Neither `depth` nor `elevation` | Error naming both columns and how to provide them |
| `vs="elevation"` given explicitly, with neither `elevation` nor `ground_level` + `depth` | Error explaining the two ways to provide it |
| `vs=None` with only `depth` | Plotted against depth, with the optional-columns hint mentioning `ground_level` |
| Optional columns missing (`geology_unit`, `loca_id`, `ground_level`, …) | Plot drawn; one hint listing what each missing column would add |
| Units unknown for value or vertical | Plot drawn with "(units unknown)" in the label, plus a warning naming the column and how to declare it (`ak.set_units`) |
| Values ≤ 0 on a log axis | Excluded and counted in the footnote |
| Values beyond `xlim`/`ylim` | Edge marker + arrow + count |
| `depth_top` > `depth_base` | Bar not drawn for that row; warning naming the row |
| A `geology_unit` value not in the palette | Auto-assigned a color, which is remembered for the session |
| Rows with a blank `geology_unit` (or `color_by` column) | Drawn in the neutral gray and listed as "(blank)" at the end of the unit legend. A unit with no point drawn gets no legend entry |
| `preset=` for a different quantity than a registered `value` column (e.g. `preset="water_content"` on `undrained_shear_strength`) | Error naming both quantities |
| Text in the `value` or a length column (`"NP"`, `"12 ft"`) | Error naming the rows. Counting flagged text such as `NP` is TODO #15 |
| More than 12 / 30 legend entries | README legend rules (columns / note) |
| Duplicate rows | Plotted as given (no de-duplication in plots) |
| `connect=True` without `loca_id` | Error: it was asked for explicitly, so a hint isn't enough |
| `secondary="depth"` with several ground levels | Clear error (§6) |
| `strata` or `ranges` with both a depth and an elevation pair, or (for `strata`) neither | Error naming the two pairs and saying to give one |
| `strata` or `ranges` pair doesn't match `vs`, and there are several ground levels (or none) | Error saying the pair can't be converted, and to give the pair that matches `vs` |
| Overlay row with top and base the wrong way round | Row not drawn; warning naming the row |
| `qualifier` other than `"<"`, `">"` or blank | Error listing the rows and the values found |
| Mixed lab and field data | Fine. Use `marker_by="source"` to distinguish them |

## 12. Acceptance criteria and tests
- **Golden values:**
  - elevation from `ground_level − depth` (e.g. GL 120.0 ft, depth 15.0 ft → 105.0 ft);
  - interval bounds converted the same way;
  - k = 1.0e-5 m/s displays as 1.0e-3 cm/s;
  - 10.0 ft ↔ 3.048 m;
  - 2,000 psf ↔ 95.76 kPa.
- **Visual checks:**
  - depth axis starts at 0 at the top;
  - elevation increases upward;
  - the log axis shows whole decades with `10ⁿ` labels;
  - the x-axis is at the bottom by default;
  - unit colors match the colors from `ak.plot.legend_handles()`;
  - carets point the right way;
  - footnote counts are correct.
- **Automated:**
  - renders for every preset, and for `vs` = depth/elevation;
  - labels contain units (and the datum when set);
  - every overlay argument on/off;
  - `ax=` draws into a Sheet panel without creating a new figure;
  - **US vs SI**: identical point positions after conversion and identical counts, differing only in labels and ticks;
  - log exclusion and out-of-range counts;
  - error messages for missing columns and units;
  - no change to global `rcParams` after the call.
- **Test data** (synthetic CSVs in `tests/data/`):
  - `profile_perm.csv`: 3 holes; lab (point) and field (interval) k; one `<` value; one value ≤ 0; one NaN; US units.
  - `profile_su.csv`: 2 units, an elevation column, SI units.
  - `profile_single.csv`: one point.

## 13. References
- Freeze, R.A. & Cherry, J.A. (1979). *Groundwater*. Prentice-Hall. Table 2.2: ranges of hydraulic conductivity.
- Terzaghi, K., Peck, R.B. & Mesri, G. (1996). *Soil Mechanics in Engineering Practice*, 3rd ed. Wiley. Consistency vs undrained strength.
- NAVFAC (1986). *Design Manual 7.01: Soil Mechanics*. Typical unit weights.

## 14. Open questions
None open. Review decisions are recorded in the body: overlay column names and the depth-or-elevation pairs for strata and ranges (§8), k shown in cm/s in US units (§9), x-axis at the bottom (§6), stats box contents (§8), `connect=` off by default (§7), per-hole water levels (§8), and only `value` plus depth or elevation required (§3).

## 15. Future enhancements
- `facet_by="loca_id"`: one panel per hole with a shared vertical axis (a borehole-by-borehole profile sheet).
- Several properties side by side with a shared y-axis (e.g. w, s_u and k panels): may become its own plot spec.
- Moving-window statistics / trend lines with confidence bands (overlaps with P09).
- Strata bands built automatically from a single hole's GEOL data (Phase 2).
