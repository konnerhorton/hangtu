# P07: property by geology unit against baseline ranges — intent

## Goal
Build a plot that compares measured values of a property, grouped by geology unit, with the design ranges stated in a report for each unit (a geotechnical baseline report, a GIR or a design basis).

### What the figure looks like
One panel per property. Values run across the horizontal axis, and geology units are categories on the vertical axis, in stratigraphic order from top to bottom. Each unit's row holds, from top to bottom:
1. **The baseline bar**, a little above the row's center line: a horizontal line from the report's `low` to its `high`, with a diamond at `central` when it is given.
2. **The data points**, centered on the row: every measured value as a small, semi-transparent point, jittered vertically within the row so stacked values stay visible.
3. **The data bar**, on the row's center line and drawn over the points: a thicker horizontal line from the data's p10 to its p90, with a filled circle at p50. The circle has a white edge so it stays visible against the points.

The bars have short end caps, so a range with low = high still shows. The count of values ("n = 288") sits just outside the right edge of the axes, level with the row.

Values beyond the axis limits sit at the edge as edge markers, with a count in the footnote (the P00 rule). For example, a consistency index of −2 on an axis that starts at −0.6.

```
            Water content, w (%)
      A |   ──◆────────────────────   (baseline)        n = 288
        | · ·:·:·━━━━━●━━━━━━━·:· · ·   (data)
      B |       ──────◆──────                           n = 540
        |  · ·:·:━━━━━●━━━━━·:· ·
      ...
        +------------------------------
          0     10     20     30     40

   ── ◆ GBR baseline p10–p90, p50    ━━ ● Data p10–p90, p50    · Data
```

**Several properties:** `geology_unit_comparisons()` lays the panels out in a grid, two columns wide, filled row by row. Each panel has its own value axis with the house label (`Quantity, symbol (unit)` on the horizontal axis, not a panel title), its own limits, and only the units that have data or a baseline for that property. For example, a plasticity index panel tested only in units D and F shows two rows. One shared legend explains the marks once, centered below the grid.

**Gridlines:** light vertical gridlines at the major value ticks, and none between units.

## Why
- Checking new data against a baseline is a routine question on every project with a GBR or a design basis: "does what we measured in this phase fall inside what the report assumed?" It is usually done by hand in Excel.
- P07 is already planned as "box plot by unit with published-range bands" (`docs/plots/README.md`, SPEC §3 and §5). This figure is that plot in a better form for the comparison: percentile bars read more directly against a stated range than a box does, and showing every point means nothing is hidden. So this intent makes it P07 rather than a new ID.
- Building it before M3 gets the second categorical (non-depth) plot in early, while the P00 framework and the P01 overlays are fresh.

## Constraints
- Use the P00 framework (units, labels, limits, notes, edge markers, palette, legend, hints, errors) and reuse what fits from `plot/_overlays.py` (`overlay_units`, `ValueScale`, `stats_box`, `note`, `reference_lines`). Don't reimplement them.
- SPEC §2.6: input units resolve as argument → `df.attrs["units"]` → registry → "(units unknown)" plus a warning. Baseline values carry their own units and are converted to the display units, as the P01 `ranges` overlay does.
- SPEC §3: the plot contract (`(fig, ax)`, `ax=`, `display_units=`, no global matplotlib state). The multi-panel function returns `(fig, axs)`.
- SPEC §10.3 and CLAUDE.md "Naming": column names come from the registry. New overlay fields are checked against the whole registry.
- Never drop data silently: values beyond the axis limits are drawn at the edge with a count; NP, `<x` and other flagged values are counted; a unit that has a baseline but no data shows "n = 0".
- SPEC §11 (error messages) and §12.1 (no new dependencies). Percentiles come from NumPy; SPEC §5 says P07 doesn't need the statistics module.
- **Done when:** the P07 acceptance criteria pass, and `visual-check.png` (US and SI, several properties, realistic data with a sparse unit and out-of-range values) is committed in the close-out.

## Decisions
- **This is P07.** P07 is renamed from "Box plot by unit" to **"Property by geology unit"**. The function is `ht.plot.geology_unit_comparison()`. The summary mark is a percentile bar by default, and `summary="box"` gives a conventional box plot, so the original P07 is still covered.
- **P07 moves ahead of M3.** M5 is split: P07 becomes its own unit now, and M5 keeps the examples, CSV templates, README and PyPI release. SPEC §12.4 changes in the spec commit.
- **The baseline table** comes in as a plain DataFrame or CSV through `baseline=`, like the P01 overlays. One table can feed every panel, so it is long-format:

  | `geology_unit` | `property` | `low` | `central` | `high` | `source` |
  |---|---|---|---|---|---|
  | A | `water_content` | 4 | 14 | 27 | GBR Table 4-2 |

  - `low`, `high` and `source` already exist as overlay fields. `property` holds a registry column name and is only needed when the table covers more than one property. `central` (the report's p50, mean or "typical" value) is optional.
  - `property` and `central` are new fields. They were checked against the registry, the presets and the unit aliases and collide with nothing. A `baseline` template is added to `columns.yaml`, so `ht.template("baseline")` gives the exact columns.
  - Units come from the table's `attrs["units"]` or the `units=` argument, otherwise the value column's units with the same hint the P01 `ranges` overlay gives.
  - The argument and template are called `baseline`, not `ranges`. The table means something different from P01's ranges (one range per unit, not one per band), and a GIR or design basis fills it in the same way.
- **Legend wording.**
  - Data: `percentiles=(10, 50, 90)` by default, changeable per call, and written in the legend ("Data p10–p90, p50"). `percentile_method=` is passed to NumPy's `numpy.percentile(method=...)` and defaults to `"linear"` (NumPy's default). Any method other than linear is named in the legend ("Data p10–p90, p50 (Hazen)"). Other summaries are TODO #16.
  - Baseline: the user states what the report's range means with `baseline_label=` (e.g. "GBR baseline p10–p90, p50", or "GIR typical range"). Without it, the legend uses the table's `source` (or "Baseline" when there are several sources) and claims no definition.
  - The legend explains the marks once, below the panels (or to the right of a single panel).
- **Small samples.** The points are always drawn. The summary bar is drawn only when n ≥ `min_count` (default 5, a setting). Below that, the count label says why, e.g. "n = 2 (no summary)".
- **Color.** Points and the data bar take the unit's palette color, so a unit looks the same here as on every profile. The baseline bar is a neutral dark gray with a diamond marker, the same for every unit, and is also set apart by its position and the legend (never by color alone). `color_by=None` draws all the data in one neutral color.
- **Order and layout.**
  - Units run top to bottom in stratigraphic `order` when it is known, otherwise sorted, and `order=` overrides it (the same order as the SPEC §3 palette rules).
  - Every unit that appears in the data **or** in the baseline gets a row, so a baseline with no data reads "n = 0" and data with no baseline is visible as such.
  - Multi-panel: `ht.plot.geology_unit_comparisons(df, values=[...], baseline=...)` returns `(fig, axs)`, one panel per property. Each panel shows only the units that have data or a baseline for that property. It is built on `geology_unit_comparison(ax=...)`, so `ht.Sheet` composition works too.
  - One panel uses the `default` figure size (6.5 × 4.5 in). The grid uses a new `grid` kind in `ht.settings.figure_sizes`, sized for a Letter page.
- **Horizontal only:** units on the vertical axis, values across. No `orient=` argument in this version.
- **One unit of work** on this branch. The spec commit holds the P07 spec, the README row and SPEC §3, §5 and §12.4, then comes the plan commit. The build commits are about 300 lines or less each, in this order: categorical axis and points → summary bars and counts → baseline table and units → edge markers, flags and hints → multi-panel function → test data and visual check.

## Out of scope
- Statistical tests of data against the baseline (pass/fail, confidence intervals on percentiles). That belongs to `ht.stats.compare` in Phase 3.
- Vertical orientation, depth-split rows (one unit split by depth range), and grouping by anything other than geology unit. `group_by=` could come later.
- QC level 2 ranges (v0.4), even though they could use the same table.
- Examples, the README and the tutorial (M5).

## SPEC sections touched
- §3 (P07 name and description), §5 (the P07 sentence), §12.4 (P07 moves out of M5).
- `docs/plots/README.md` (P07 row and status), new `docs/plots/P07-geology-unit-comparison.md`.
- `columns.yaml` (`property`, `central` fields and the `baseline` template) and `config/defaults.yaml` (`min_count`, the `grid` figure size).
