# P07: property by geology unit

## Intent

### Goal
Build a plot that compares measured values of a property, grouped by geology unit, with the design ranges stated in a report for each unit (a geotechnical baseline report, a GIR or a design basis).

#### What the figure looks like
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

### Why
- Checking new data against a baseline is a routine question on every project with a GBR or a design basis: "does what we measured in this phase fall inside what the report assumed?" It is usually done by hand in Excel.
- P07 is already planned as "box plot by unit with published-range bands" (`docs/plots/README.md`, SPEC §3 and §5). This figure is that plot in a better form for the comparison: percentile bars read more directly against a stated range than a box does, and showing every point means nothing is hidden. So this intent makes it P07 rather than a new ID.
- Building it before M3 gets the second categorical (non-depth) plot in early, while the P00 framework and the P01 overlays are fresh.

### Constraints
- Use the P00 framework (units, labels, limits, notes, edge markers, palette, legend, hints, errors) and reuse what fits from `plot/_overlays.py` (`overlay_units`, `ValueScale`, `stats_box`, `note`, `reference_lines`). Don't reimplement them.
- SPEC §2.6: input units resolve as argument → `df.attrs["units"]` → registry → "(units unknown)" plus a warning. Baseline values carry their own units and are converted to the display units, as the P01 `ranges` overlay does.
- SPEC §3: the plot contract (`(fig, ax)`, `ax=`, `display_units=`, no global matplotlib state). The multi-panel function returns `(fig, axs)`.
- SPEC §10.3 and CLAUDE.md "Naming": column names come from the registry. New overlay fields are checked against the whole registry.
- Never drop data silently: values beyond the axis limits are drawn at the edge with a count; NP, `<x` and other flagged values are counted; a unit that has a baseline but no data shows "n = 0".
- SPEC §11 (error messages) and §12.1 (no new dependencies). Percentiles come from NumPy; SPEC §5 says P07 doesn't need the statistics module.
- **Done when:** the P07 acceptance criteria pass, and `visual-check.png` (US and SI, several properties, realistic data with a sparse unit and out-of-range values) is committed in the close-out.

### Decisions
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

### Out of scope
- Statistical tests of data against the baseline (pass/fail, confidence intervals on percentiles). That belongs to `ht.stats.compare` in Phase 3.
- Vertical orientation, depth-split rows (one unit split by depth range), and grouping by anything other than geology unit. `group_by=` could come later.
- QC level 2 ranges (v0.4), even though they could use the same table.
- Examples, the README and the tutorial (M5).

### SPEC sections touched
- §3 (P07 name and description), §5 (the P07 sentence), §12.4 (P07 moves out of M5).
- `docs/plots/README.md` (P07 row and status), new `docs/plots/P07-geology-unit-comparison.md`.
- `columns.yaml` (`property`, `central` fields and the `baseline` template) and `config/defaults.yaml` (`min_count`, the `grid` figure size).

## Plan

Spec: [`docs/plots/P07-geology-unit-comparison.md`](../plots/P07-geology-unit-comparison.md) (section numbers below are P07's unless marked P01, P00 or SPEC).

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines is split.

### Package layout
```
src/hangtu/
  config/defaults.yaml          + settings summary_min_count; figure_sizes grid
  _settings.py                  validates summary_min_count
  columns.yaml                  + fields property, central; + baseline template; used_by P07
  plot/__init__.py              exports geology_unit_comparison, geology_unit_comparisons
  plot/_values.py               value-axis helpers shared by P01 and P07 (moved from _profile.py)
  plot/_geology_units.py        geology_unit_comparison(), geology_unit_comparisons()
  plot/_baseline.py             reads, checks and converts the baseline table
  plot/_layers.py               + P07 draw order
tests/plot/
  test_geology_unit_comparison.py    rows, points, axes, summaries, flags
  test_baseline.py                   the baseline table: format, units, drawing
  test_geology_unit_comparisons.py   the grid
  test_geology_unit_comparison_acceptance.py   §12 against the test data
tests/data/
  comparison_index.csv, comparison_vane.csv, comparison_baseline.csv
```
- The module is `_geology_units.py`, not `geology_unit_comparison.py`, so `ht.plot.geology_unit_comparison` is the function and not a submodule that hides it (the same reason as `_profile.py` in M2).
- `_baseline.py` is separate because the baseline table has its own rules (§8) and its own tests, and P07's grid calls it once per panel.

### Decisions the build makes
These fill gaps in P07. Each one goes into P07 in the commit that builds it.
1. **Shared value-axis helpers move to `plot/_values.py`** before P07 is built, in a refactor commit with no change in behavior: `check_limits`, `quantity_of`, `axis_text`, `start_at_zero`, `typical_range`, `value_limits`, `color_groups`, `qualifiers`, `qualifier_handles`, `legend_marker`, and the constants `NEUTRAL`, `BLANK_GROUP`, `QUALIFIERS`, `CARET_SIZE`. They lose their leading underscore, since another module now imports them. `_profile.py` imports them from there.
2. **Points and carets are scatter collections. Bars, caps, central markers and boxes are `Line2D` and patches.** `assert_us_si_equivalent` compares scatter offsets, so it then checks the data points only. Bars and markers get their own position tests (as P01 decision 8).
3. **Rows sit at y = 0, 1, 2, … with the y-axis inverted**, so the first unit is at the top and "above" is a negative offset in data units. The limits are (n − 0.5, −0.5). The baseline bar is at row − 0.28.
4. **Jitter** uses `numpy.random.default_rng(0)`, created once per call and drawn in row order. The same data gives the same figure, in US and SI alike.
5. **The box is drawn with a `Rectangle` and lines, not `ax.bxp`.** `bxp` changed from `vert=` to `orientation=` in matplotlib 3.10, and the oldest supported version is 3.8. Drawing it ourselves also keeps the quartiles on `percentile_method`.
6. **`percentile_method` is checked against a tuple of NumPy's 13 method names** in `_geology_units.py`, because NumPy has no public list. NumPy 1.26, the oldest supported version, has all of them.
7. **Blank values are skipped before anything is counted** (§14). Rows with a blank value never reach `Notes`, so the `nan` reason stays at zero. A row with a value but a blank `geology_unit` goes to the "(blank)" row.
8. **Count labels** are annotations at x = 1 (axes fraction), 4 pt to the right, on each row's center line. After a layout pass, the legend and footnote `offset` is set to the widest label plus 6 pt (`add_legend(..., offset=)`, `Notes.render(..., offset=)`), the same way P01 clears its secondary axis.
9. **No hint for missing optional columns.** `qualifier` and `non_plastic` don't unlock a feature an engineer would miss, and `geology_unit` is required, so no `HangtuHint` would ever be useful here.
10. **Baseline rows are filtered to the plotted property first.** Then the §8 checks (duplicates, `low` > `high`, blank unit) apply only to the rows being drawn. Rows for properties that aren't plotted are ignored without a warning, since they aren't data. A `baseline_units` key that is neither a `property` in the table nor the plotted value raises an error naming it, to catch typos.
11. **The grid returns `axs` as a 1-D array in `values` order** (`axs[i]` is `values[i]`), not the 2-D array of `plt.subplots`. An empty last cell is removed. The shared legend is `fig.legend(loc="outside lower center")`. One footnote below it lists each panel's notes, prefixed with the panel's quantity: "Consistency index, Ic: 4 values beyond axis limit, shown at the edge". Each panel's own counts stay in `ax.ags_notes`.
12. **In the grid, `units=` applies to every table.** With a dict of tables, each table keeps its own declared units.

### Build 0 (refactor): `P07: move the value-axis helpers out of the profile module`
- `plot/_values.py` with the helpers in decision 1; `_profile.py` imports them. No change in behavior.
- Tests: the P01 tests pass unchanged. They test the helpers through `profile()`, and no test imports them directly, so nothing else changes.

### Build 1: `P07: add the baseline template and comparison settings`
- `config/defaults.yaml`: `summary_min_count: 5`; `figure_sizes.grid: [3.75, 2.75]` (per panel, §5).
- `_settings.py`: `summary_min_count` must be an integer ≥ 1 (§11), with an error that gives an example.
- `columns.yaml`: fields `property` (text: the value column a baseline row applies to) and `central` (number: the report's central value); template `baseline: [geology_unit, property, low, central, high, source]`; `used_by` gains P07 for `non_plastic`, the four preset columns, `liquidity_index` and `consistency_index`.
- Tests: the setting's default, validation and reset; `ht.template("baseline")` columns and dtypes; the registry naming test covers the new fields.

### Build 2: `P07: draw values by geology unit`
- `plot/_geology_units.py`: `geology_unit_comparison()` with the full §10 signature. Arguments built in later steps raise `NotImplementedError` until then, so no step ships a silent no-op.
- Errors: missing `value` or `geology_unit` (listing the columns available), non-numeric values (TODO #15), `color_by` other than `"geology_unit"` or None.
- Preset: `preset=None` takes the preset named after `value` if there is one (§6); `preset=` and `log=` override it. Units, labels and limits use the `_values.py` helpers.
- Rows: the units in `order=`, then the rest by name, then "(blank)" (§6, decision 3). Tick labels are the unit names. Vertical gridlines only.
- Points: jittered scatter (decision 4), 3 pt, alpha 0.4, unit color or `NEUTRAL` with `color_by=None`. Log axis: values ≤ 0 are left out and counted. Blanks skipped (decision 7). Empty input gives "No data".
- Tests: row order with and without `order=`; the "(blank)" row; jitter within ±0.15 and the same on two calls; each preset picked by name, and overridden by `preset=` and `log=`; labels with units, and "(units unknown)" with its warning; log exclusion count; a blank value isn't counted; `assert_us_si_equivalent` with `("stress", "dimensionless")`; `assert_no_global_state`, also with `ax=` on a `Sheet` panel; empty input.

### Build 3: `P07: summarize each unit with percentile bars or boxes`
- `summary="percentiles"`: the bar from the first to the third percentile with caps, and the white-edged circle at the second (§7). `summary="box"` (decision 5). `summary=None`: points only.
- `percentiles` must be three ascending numbers in [0, 100], and `percentile_method` must be one of NumPy's methods (decision 6). Both errors give an example.
- `summary_min_count` from the argument or the settings; below it, no summary.
- Count labels "n = 288" / "n = 2 (no summary)" (decision 8).
- Legend: gray stand-ins for the summary ("Data p10–p90, p50", plus the method when it isn't linear) and for the points ("Data").
- Tests: the §12 golden values read back from the `Line2D` data (1–10 linear; [2, 4, 4, 5, 7, 9] linear, quartiles, whiskers and Hazen); a zero-length bar when all values are equal; n = 4 with the default gives no bar and "(no summary)"; `summary_min_count=0` is an error; legend text for linear, Hazen and box; the label positions and the legend clear of them.

### Build 4: `P07: draw the baseline ranges`
- `plot/_baseline.py`: reads a DataFrame or a CSV path (`ht.read_csv`), filters to the plotted property (decision 10), checks the rows (§8), and resolves units in the order `baseline_units=`, the table's declared units, then the value column's units with one warning that shows both ways to declare them.
- Drawing: the gray bar with caps at row − 0.28, the diamond at `central`, a `central`-only row as just the diamond, and a `low` ≤ 0 on a log axis starting at the edge. Units that are only in the baseline get a row with "n = 0".
- Value-axis limits include the baseline values (§6).
- `baseline_label=`, else the single `source`, else "Baseline", as the legend entry. It comes first in the legend.
- Tests: each §8 row rule (`central` only, neither, `low` > `high`, duplicate, blank unit, no `property` in a multi-property table); the three ways of declaring units and the warning; 2,000 psf → 95.76 kPa; a baseline-only unit gets a row with "n = 0"; bar and diamond positions in US and SI; the default limits cover a baseline wider than the data; legend text in each case.

### Build 5: `P07: draw out-of-range and flagged values`
- `xlim=`: points beyond it go through `edge_markers` and are counted; bars and boxes are cut at the edge without their caps (§7).
- Qualifiers: carets in place of points, counted, with legend entries (the `_values.py` helpers). NP rows (`non_plastic` true) are left out of points and summaries and counted.
- `reference_lines=` and `note=` through `_overlays.py`.
- Tests: edge counts, with the summary still at the true values; a bar cut at the edge has no cap on that side; caret direction and counts; NP counted and not summarized; reference line in psf drawn in kPa; draw order (§7) through `zorder`.

### Build 6: `P07: lay out several properties in a grid`
- `geology_unit_comparisons()`: a table or `{value: table}`; per-panel dicts for `preset`, `log`, `label`, `xlim` and `reference_lines`, where a key not in `values` is an error; `columns=2`; size from the `grid` setting per panel plus 0.6 in for the legend (§5).
- Each panel calls `geology_unit_comparison(ax=...)` without its own legend and footnote, through a private flag. Then one shared legend and one combined footnote are added (decision 11).
- A baseline without `property` and more than one value is an error (§8).
- Tests: 1, 2, 5 and 6 panels (axs length, the empty cell removed); the figure size; per-panel arguments reach the right panel; an unknown key; a dict of tables with different units; one legend for the figure; footnote lines carry the panel's quantity; each panel's `ax.ags_notes`.

### Build 7 (close-out): `P07: add test data, acceptance tests and close out P07`
- `tests/data/`: the three CSVs in §12, made to look like a real site: six units A–F, hundreds of water contents, a unit with n = 2, a consistency index below the axis, a unit only in the baseline, and a `central`-only baseline row.
- `test_geology_unit_comparison_acceptance.py`: every §12 automated criterion against the CSVs, with the footnote counts worked out by hand.
- Visual checks (100 dpi), looked at before committing:
  - `visual-check.png`: the grid in SI with six properties (water content, bulk unit weight, plasticity index, consistency index, s_u, k), against the baseline;
  - `visual-check-us.png`: the same grid in US. Two files, because a grid is a whole figure and can't sit on one `Sheet` beside its US twin.
- Close-out:
  - `docs/plots/README.md`: P07 status `built`.
  - `CLAUDE.md`: the status line says P07 is done and M3 is next.
  - P07: any detail the build changed, and the decisions above that aren't already in it.
  - SPEC §12.4: nothing more, since M2b was added in the spec commit.
  - `TODO.md`: no change expected (#16 stays open).
  - This plan: a Results section.

### Verification
- After each build: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- At close-out:
  - Python 3.13 and 3.14: `uv run --isolated --python 3.1x pytest`.
  - The lowest dependency versions, as in CLAUDE.md. `numpy.percentile(method=...)` needs NumPy ≥ 1.22, and `fig.legend(loc="outside lower center")` needs matplotlib ≥ 3.7; check both on the lowest versions.
  - `uv build`, and check that the wheel's `columns.yaml` has the `baseline` template and its `defaults.yaml` has the new settings.
- Look at both visual checks against the §2 reference figure and the "A good version" list.

### Results
- 751 tests pass on Python 3.12, 3.13 and 3.14, and with the lowest dependency versions (matplotlib 3.8.0, numpy 1.26.0, pandas 2.1.1, pint 0.24.4). The wheel's `columns.yaml` has the `baseline` template and its `defaults.yaml` has `summary_min_count` and the `grid` size.
- **Commits:** the refactor (Build 0), then one commit per build step as planned, plus two fixes:
  - `P07: apply non_plastic only to Atterberg values`. The realistic test data showed that applying `non_plastic` to every value dropped and counted the water contents of NP specimens. NP now applies to LL, PL, PI, LI and Ic only (P07 §3).
  - `P07: fix problems the realistic test data showed`. A `non_plastic` column read from CSV with blanks is object dtype, and `fillna` on it raised a pandas FutureWarning. Edge arrows at the lower limit covered the unit names, which now move clear of them.
- **Changes from the plan**, each recorded in P07 in its commit:
  - Summary, flag and grid tests are in their own files (`test_geology_unit_summaries.py`, `test_geology_unit_flags.py`) next to the planned ones, so each file stays readable. There is no `test_values.py`: no test imported the moved helpers.
  - `used_by` also lists P07 for `plasticity_index` and `source`.
  - A row of the baseline with only one of `low` and `high` draws no bar and warns (P07 §8).
  - Count labels move a further 14 pt right when a value is beyond the upper limit, so an edge arrow doesn't run into them (P07 §7).
  - In the grid, the legend and footnote sit in a band kept free of panels, instead of `fig.legend(loc="outside lower center")`: that legend overlapped a footnote placed below it. The default figure grows by the footnote's height.
  - The visual check has six properties from four CSVs; k comes from a fourth file, `comparison_perm.csv`.
- `TODO.md`: no change (#16 stays open). SPEC: no change beyond the spec commit.
- **Visual check** (`visual-check.png` in SI, `visual-check-us.png` in US, 7.5 × 9.3 in at 100 dpi): units in order with their palette colors in every panel; baseline bars above the data bars; "n = 0" for the unit with only a baseline; "n = 2 (no summary)"; the central-only k row; the cut bar and edge markers at −0.6 on the consistency index, with the unit names clear of them; the "<" caret on s_u; one legend and a footnote naming each panel. One thing to know:
  - A value exactly at a nice limit sits on the frame and is half hidden (PI = 25 here), because P00's limits stop at the nice value above the largest value. P01 has the same behavior.
