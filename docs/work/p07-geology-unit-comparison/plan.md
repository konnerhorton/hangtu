# P07: property by geology unit — plan

Intent: [intent.md](intent.md). Spec: [`docs/plots/P07-geology-unit-comparison.md`](../../plots/P07-geology-unit-comparison.md) (section numbers below are P07's unless marked P01, P00 or SPEC).

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines is split.

## Package layout
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

## Decisions the build makes
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

## Build 0 (refactor): `P07: move the value-axis helpers out of the profile module`
- `plot/_values.py` with the helpers in decision 1; `_profile.py` imports them. No change in behavior.
- Tests: the P01 tests pass unchanged. They test the helpers through `profile()`, and no test imports them directly, so nothing else changes.

## Build 1: `P07: add the baseline template and comparison settings`
- `config/defaults.yaml`: `summary_min_count: 5`; `figure_sizes.grid: [3.75, 2.75]` (per panel, §5).
- `_settings.py`: `summary_min_count` must be an integer ≥ 1 (§11), with an error that gives an example.
- `columns.yaml`: fields `property` (text: the value column a baseline row applies to) and `central` (number: the report's central value); template `baseline: [geology_unit, property, low, central, high, source]`; `used_by` gains P07 for `non_plastic`, the four preset columns, `liquidity_index` and `consistency_index`.
- Tests: the setting's default, validation and reset; `ht.template("baseline")` columns and dtypes; the registry naming test covers the new fields.

## Build 2: `P07: draw values by geology unit`
- `plot/_geology_units.py`: `geology_unit_comparison()` with the full §10 signature. Arguments built in later steps raise `NotImplementedError` until then, so no step ships a silent no-op.
- Errors: missing `value` or `geology_unit` (listing the columns available), non-numeric values (TODO #15), `color_by` other than `"geology_unit"` or None.
- Preset: `preset=None` takes the preset named after `value` if there is one (§6); `preset=` and `log=` override it. Units, labels and limits use the `_values.py` helpers.
- Rows: the units in `order=`, then the rest by name, then "(blank)" (§6, decision 3). Tick labels are the unit names. Vertical gridlines only.
- Points: jittered scatter (decision 4), 3 pt, alpha 0.4, unit color or `NEUTRAL` with `color_by=None`. Log axis: values ≤ 0 are left out and counted. Blanks skipped (decision 7). Empty input gives "No data".
- Tests: row order with and without `order=`; the "(blank)" row; jitter within ±0.15 and the same on two calls; each preset picked by name, and overridden by `preset=` and `log=`; labels with units, and "(units unknown)" with its warning; log exclusion count; a blank value isn't counted; `assert_us_si_equivalent` with `("stress", "dimensionless")`; `assert_no_global_state`, also with `ax=` on a `Sheet` panel; empty input.

## Build 3: `P07: summarize each unit with percentile bars or boxes`
- `summary="percentiles"`: the bar from the first to the third percentile with caps, and the white-edged circle at the second (§7). `summary="box"` (decision 5). `summary=None`: points only.
- `percentiles` must be three ascending numbers in [0, 100], and `percentile_method` must be one of NumPy's methods (decision 6). Both errors give an example.
- `summary_min_count` from the argument or the settings; below it, no summary.
- Count labels "n = 288" / "n = 2 (no summary)" (decision 8).
- Legend: gray stand-ins for the summary ("Data p10–p90, p50", plus the method when it isn't linear) and for the points ("Data").
- Tests: the §12 golden values read back from the `Line2D` data (1–10 linear; [2, 4, 4, 5, 7, 9] linear, quartiles, whiskers and Hazen); a zero-length bar when all values are equal; n = 4 with the default gives no bar and "(no summary)"; `summary_min_count=0` is an error; legend text for linear, Hazen and box; the label positions and the legend clear of them.

## Build 4: `P07: draw the baseline ranges`
- `plot/_baseline.py`: reads a DataFrame or a CSV path (`ht.read_csv`), filters to the plotted property (decision 10), checks the rows (§8), and resolves units in the order `baseline_units=`, the table's declared units, then the value column's units with one warning that shows both ways to declare them.
- Drawing: the gray bar with caps at row − 0.28, the diamond at `central`, a `central`-only row as just the diamond, and a `low` ≤ 0 on a log axis starting at the edge. Units that are only in the baseline get a row with "n = 0".
- Value-axis limits include the baseline values (§6).
- `baseline_label=`, else the single `source`, else "Baseline", as the legend entry. It comes first in the legend.
- Tests: each §8 row rule (`central` only, neither, `low` > `high`, duplicate, blank unit, no `property` in a multi-property table); the three ways of declaring units and the warning; 2,000 psf → 95.76 kPa; a baseline-only unit gets a row with "n = 0"; bar and diamond positions in US and SI; the default limits cover a baseline wider than the data; legend text in each case.

## Build 5: `P07: draw out-of-range and flagged values`
- `xlim=`: points beyond it go through `edge_markers` and are counted; bars and boxes are cut at the edge without their caps (§7).
- Qualifiers: carets in place of points, counted, with legend entries (the `_values.py` helpers). NP rows (`non_plastic` true) are left out of points and summaries and counted.
- `reference_lines=` and `note=` through `_overlays.py`.
- Tests: edge counts, with the summary still at the true values; a bar cut at the edge has no cap on that side; caret direction and counts; NP counted and not summarized; reference line in psf drawn in kPa; draw order (§7) through `zorder`.

## Build 6: `P07: lay out several properties in a grid`
- `geology_unit_comparisons()`: a table or `{value: table}`; per-panel dicts for `preset`, `log`, `label`, `xlim` and `reference_lines`, where a key not in `values` is an error; `columns=2`; size from the `grid` setting per panel plus 0.6 in for the legend (§5).
- Each panel calls `geology_unit_comparison(ax=...)` without its own legend and footnote, through a private flag. Then one shared legend and one combined footnote are added (decision 11).
- A baseline without `property` and more than one value is an error (§8).
- Tests: 1, 2, 5 and 6 panels (axs length, the empty cell removed); the figure size; per-panel arguments reach the right panel; an unknown key; a dict of tables with different units; one legend for the figure; footnote lines carry the panel's quantity; each panel's `ax.ags_notes`.

## Build 7 (close-out): `P07: add test data, acceptance tests and close out P07`
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

## Verification
- After each build: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- At close-out:
  - Python 3.13 and 3.14: `uv run --isolated --python 3.1x pytest`.
  - The lowest dependency versions, as in CLAUDE.md. `numpy.percentile(method=...)` needs NumPy ≥ 1.22, and `fig.legend(loc="outside lower center")` needs matplotlib ≥ 3.7; check both on the lowest versions.
  - `uv build`, and check that the wheel's `columns.yaml` has the `baseline` template and its `defaults.yaml` has the new settings.
- Look at both visual checks against the §2 reference figure and the "A good version" list.
