# M2: P01 property profile — plan

Intent: [intent.md](intent.md). Spec: [`docs/plots/P01-property-profile.md`](../../plots/P01-property-profile.md) (section numbers below are P01's unless marked SPEC or P00).

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines is split.

## Package layout
```
src/ags_kit/
  config/defaults.yaml   + presets: (§6)
  columns.yaml           + elevation_top, elevation_base; + fields: and the strata, ranges, design_lines templates
  registry.py            templates may name overlay fields as well as columns
  plot/__init__.py       exports profile
  plot/_profile.py       profile(): the public plot
  plot/_presets.py       preset(name): loads and checks a preset
  plot/_vertical.py      the vertical reference: depth or elevation, ground level, conversions (SPEC §8.1)
  plot/_overlays.py      strata, water_level, ranges, design_lines, reference_lines, stats_box, note
tests/plot/
  test_profile.py, test_profile_intervals.py, test_profile_overlays.py, test_vertical.py, test_presets.py
  test_profile_acceptance.py   §12 against the test data
tests/data/
  profile_perm.csv, profile_su.csv, profile_single.csv
```
- The module is `_profile.py`, not `profile.py`, so `ak.plot.profile` is the function and not a submodule that hides it (the same reason as `registry.py` in M1).
- `_vertical.py` and `_overlays.py` are private and take plain arguments (axes, a `Vertical` reference, the display system), so P02, P06 and P09 can call them without going through `profile()` (intent, "Overlays are built for reuse").

## Decisions the build makes
These fill gaps in P01. Each one goes into P01 in the commit that builds it.
1. **Overlay fields in templates.** `low`, `high`, `label` and `value` are overlay fields, not data columns (P01 §8), so they don't go in `columns:`. A new `fields:` section of `columns.yaml` lists them with a type and description. `ak.template()` and the registry test accept a name from either section; `ak.columns()` still lists columns only.
2. **Overlay units.** An overlay's units come from its own `df.attrs` (P01 §8), read with `units_of`, not `resolve_units`, whose warning talks about axis labels. Otherwise values are assumed to be in the main data's units: `low`, `high`, `value` and reference lines in the value column's unit, vertical pairs in the vertical column's unit. One warning per overlay names the assumption and shows the `ak.set_units` call. A number given for `water_level` or `reference_lines` is in the main data's units. A string such as `"112.5 ft"` goes through `parse_quantity` (P00 §4.3 #4).
3. **Per-hole water levels in depth while plotting elevation** are converted with each hole's own ground level, looked up by `loca_id` in the main data. This is unambiguous per hole, unlike strata. A hole with no ground level isn't drawn, and a warning names it.
4. **Intervals in elevation** need each row's ground level: the `ground_level` column, or `elevation + depth` when both exist. Without either, bars aren't drawn and a warning says why.
5. **`connect=True` without `loca_id`**, and **`secondary="depth"` with `vs="depth"`**, raise `ColumnError` / `AgsKitError`. They were asked for explicitly, so a hint isn't enough.
6. **Stats box values** are the values drawn, in display units: blanks and values ≤ 0 on a log axis are left out; edge-clipped values count at their true value, qualified values at their reported value. Counting non-numeric values such as `NP` is TODO #15; until then, Build 3 raises an error naming those rows.
7. **Preset valid ranges** aren't stored. Nothing in P01 uses them, and QC level 2 (v0.4) will have its own ranges (plots README, "Presets").
8. **Overlay marks are lines, patches and text, never scatter collections.** `assert_us_si_equivalent` compares scatter offsets, and a ▽ drawn at an axes-fraction x would break it. Overlay positions get their own US/SI tests.

## Build 1: `P01: add profile presets and overlay templates`
- `config/defaults.yaml`: `presets:` with the four presets in §6: `column`, `label`, `quantity`, `log`, `start_at_zero`, `typical` (in the canonical unit, converted to display units when used).
- `plot/_presets.py`: `preset(name)` returns the entry. An unknown name raises `AgsKitError` listing the presets.
- `columns.yaml`: `elevation_top`, `elevation_base` (length, interval scale); `fields:` (decision 1); templates `strata`, `ranges`, `design_lines`. `registry.py` accepts fields in templates.
- Tests: each preset loads and its column and quantity match the registry; typical ranges have the right dimension; unknown preset error; `ak.template("strata")` columns and dtypes; the registry naming test covers fields.

## Build 2: `P01: resolve the vertical reference`
- `plot/_vertical.py`:
  - `choose_vs(df, vs)`: `None` → elevation if there is an `elevation` column or `depth` + `ground_level`, else depth. Errors for neither column (§11) and for `vs="elevation"` without a way to get it, each naming both ways to provide it.
  - `vertical_values(df, vs, units)`: returns the vertical values in display units, computing `ground_level − depth` after converting both (P00 §4.3 #3).
  - `single_ground_level(df)`: the one ground level, or None when there are several or none. Used by `secondary="depth"` and overlay pair conversion.
  - `Vertical`: a frozen dataclass (`vs`, display system, unit text, single ground level) handed to overlays.
  - `convert_pair(top, base, from_vs, vertical)`: draws a pair as given when it matches `vs`, converts it with the single ground level otherwise, and raises the §11 error when it can't.
- Tests: golden values (GL 120.0 ft, depth 15.0 ft → 105.0 ft; 10.0 ft ↔ 3.048 m); depth in ft and GL in m convert before subtracting; each error message; the conversion rules for pairs.

## Build 3: `P01: draw the core property profile`
- `plot/_profile.py`: `profile()` with the full §10 signature. Arguments built in later steps raise `NotImplementedError` until then, so no step ships a silent no-op.
- Units through `resolve_units` (with `quantities` from the preset), `to_display`, labels from the preset, the registry, `label=` or the column name; the datum on elevation labels only.
- Axes: linear or log x (`log=` over the preset), `nice_limits` with `start_at_zero` from the preset or the registry scale and `typical` for a single point; `log_limits`; `apply_vertical_axis`; `xlim=` / `ylim=` with edge markers on both axes; `xaxis_position`.
- Notes: blanks, ≤ 0 on log, beyond limit. Empty input or all blank: empty labeled axes with a centered "No data" note, no error.
- Color by `geology_unit` (palette), or one neutral color when `color_by=None` or the column is missing. Hint listing missing `geology_unit`, `loca_id`, `ground_level` (only when plotting depth).
- Errors: missing value column lists the available columns; a non-numeric value column says which rows aren't numbers.
- Tests: renders for every preset and both `vs`; depth axis 0 at top, elevation up; whole log decades with `10ⁿ` labels; x-axis at the bottom by default; labels contain units and the datum; "(units unknown)" plus warning; log exclusion and edge counts; unit colors match `legend_handles()`; `assert_no_global_state` (also with `ax=` on a `Sheet` panel); `assert_us_si_equivalent` for every preset; empty and single-point input.

## Build 4: `P01: draw test intervals and qualified values`
- Intervals (`intervals="auto"` draws when `depth_top` and `depth_base` exist; `True` without them is a `ColumnError`): `vlines` in the marker color, 1.0 pt, round caps, converted to elevation with decision 4. A row with top > base isn't drawn, and a warning names it. Bounds count toward the vertical limits.
- Qualifiers: `<` and `>` drawn as ◁ / ▷ (6 pt) instead of the marker, counted in notes, with legend entries "less than (n)" / "greater than (n)". A qualifier other than `<`, `>` or blank raises an error listing the bad rows.
- Tests: interval golden value (top 10.0, base 20.0 ft, GL 120.0 ft → 110.0 to 100.0 ft); swapped row warns and isn't drawn; carets point the right way (marker paths); counts in notes and the legend.

## Build 5: `P01: group markers and connect points by hole`
- `marker_by=`: marker cycle ● ■ ▲ ◆ ▼ ✚ ✖ ⬟ ⬢ ★, legend section of gray markers after the unit colors. More than 10 groups repeat shapes, with a warning suggesting `connect=True` or splitting the data.
- `connect=True`: one gray line per `loca_id` (0.6 pt, alpha 0.6), sorted by vertical position (decision 5 for a missing `loca_id`).
- Tests: shapes per group; 11 groups warn; one line per hole with sorted y; legend section order.

## Build 6: `P01: add strata and water level overlays`
- `plot/_overlays.py`: overlay units (decision 2), and `draw_strata`, `draw_water_level`.
- Strata: one pair required (§11 error for both or neither), converted with `convert_pair`; full-width bands at alpha 0.12 in palette colors, unit name at the right edge inside the axes, 7 pt. Swapped rows warn and aren't drawn.
- Water level: a number, a `(value, label)` list or a per-hole DataFrame (decision 3). Dashed blue 0.8 pt line with ▽ and label at the right end; per hole, a short ▽ tick at the right edge, labeled with `loca_id` for ≤ 6 holes.
- Tests: depth strata drawn in elevation with one ground level; the error with several; elevation strata over several holes; swapped row; strata colors match the point colors; water level in each form; positions in US and SI.

## Build 7: `P01: add ranges, design lines and reference lines`
- Ranges: `low, high, label, source` plus an optional pair (same rules as strata); a translucent hatched band (alpha 0.15) over the pair or the full height, label at the top. A CSV path is read with `read_csv`.
- Design lines: one dashed 1.5 pt dark-gray polyline per `label`, with the vertical column matching or converted like a pair; label at the line end.
- Reference lines: dotted 0.6 pt vertical lines, label at the top. `note=`: lower-left text, 7 pt.
- Draw order from §7, set with `zorder` constants in one place.
- Tests: each overlay on and off; a range in psf drawn in kPa (2,000 psf → 95.76 kPa); design line in depth drawn in elevation; the draw order; positions in US and SI.

## Build 8: `P01: add the secondary depth axis and stats box`
- `secondary="depth"`: `ax.secondary_yaxis("right", functions=...)` mapping elevation ↔ depth with the single ground level; inverted and labeled `Depth (ft)`. Several ground levels raise the §6 error.
- Stats box (decision 6): `count, mean, std, cov, median, min, max`; default without `cov`; std "—" when n < 2; per unit up to 6 units, else overall only; lower left, 7 pt. An unknown statistic raises an error listing the allowed ones.
- Tests: secondary tick positions match GL − elevation; the error; stats golden values on a hand-calculated frame; n = 1; 7 units gives overall only.

## Build 9 (close-out): `P01: add test data, acceptance tests and close out P01`
- `tests/data/`: the three CSVs in §12.
- `test_profile_acceptance.py`: every §12 automated criterion against the CSVs, with the footnote counts checked by hand.
- `docs/work/m2-p01-property-profile/visual-check.png` (100 dpi): `profile_perm.csv` in US with strata, water level, ranges and the stats box, beside `profile_su.csv` in SI with a design line and the secondary depth axis, on one `Sheet`. Look at it before committing.
- Close-out:
  - `docs/plots/README.md`: P01 status `built`.
  - `CLAUDE.md`: status line says M2 is done and M3 is next.
  - P01: any detail the build changed; the decisions above that aren't already in it.
  - `columns.yaml`: `used_by` updated for the overlay columns.
  - `TODO.md`: no change expected.
  - This plan: a Results section.

## Verification
- After each build: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- At close-out:
  - Python 3.13 and 3.14: `uv run --isolated --python 3.1x pytest`.
  - The lowest dependency versions, as in CLAUDE.md. `secondary_yaxis(functions=...)` and `vlines(capstyle=...)` must work on matplotlib 3.8.
  - `uv build`, and check that the wheel's `defaults.yaml` contains the presets.
- Look at `visual-check.png` against the §2 reference figure and the "A good version" list.

## Results
- 608 tests pass on Python 3.12, 3.13 and 3.14, and with the lowest dependency versions (matplotlib 3.8.0, numpy 1.26.0, pandas 2.1.1, pint 0.24.4). `secondary_yaxis(functions=...)` works on matplotlib 3.8. The wheel's `defaults.yaml` has the four presets, and its `columns.yaml` has `fields:` and the three overlay templates.
- **Build 3 was split in two** because it came to about 900 lines: the linear profile (`60fbc39`), then log axes and fixed limits (`c0ca924`). A further commit (`54daea3`) fixed the label clashes the visual check showed.
- **Changes from the plan**, each recorded in P01 (or P00) in its commit:
  - Interval bars are lines broken by NaN, not `vlines`: a `LineCollection` reports a dummy (0, 0) offset that the US/SI position checks would read as a point.
  - `_data.py` (`numeric_column`, `rows_text`) and `_layers.py` (the §7 draw order) are new private modules. `ValueScale` in `_overlays.py` converts overlay values as `Vertical` converts positions.
  - Length columns convert together: if any has no units, none is converted (P01 §9). `vs="depth"` also works from `elevation` plus `ground_level`.
  - Templates list both pairs; a pair left blank counts as absent, and in `ranges` a row with a blank pair covers the full height.
  - `add_legend` and `Notes.render` take an `offset` so the legend and footnote clear the secondary depth axis (P00 §11).
  - Strata labels sit at the top right of each band; full-height range and reference line labels sit just above the axes when the x-axis is at the bottom.
  - Per-hole water levels use an optional `label` column, as P01 §8 lists, falling back to `loca_id`.
  - The stats box adds an "All" row under the units, follows the legend order, and writes numbers to 3 significant figures.
  - The shared profile test data are fixtures in `tests/plot/conftest.py`, because `--import-mode=importlib` stops test modules importing each other.
- `columns.yaml`: every overlay column already listed P01 in `used_by`, so no change. `TODO.md`: no change.
- **Visual check** (`visual-check.png`, US and SI on a Letter sheet): elevation up with the datum, whole decades with `10ⁿ` labels, unit colors shared by points and strata, interval bars, the "<" caret, gray marker groups after the unit colors, the footnote counts, and the depth axis on the right with the legend clear of it. Two things to know:
  - A value exactly on a whole decade (k = 1.0e-3 cm/s) sits on the frame, because P00's `log_limits` doesn't add a decade for it.
  - The stats box is in the lower left, as P01 §8 places it, and can cover points there; a wider `ylim=` leaves room under the data.
