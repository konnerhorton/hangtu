# M8: index plots, classification and gradation

## Intent

Shared intent for five units of work. Each one gets its own branch and is merged separately:

| Unit | Branch | Builds |
|---|---|---|
| Analyses | `m8-index-analysis` | `ht.analysis` plasticity classification, gradation (Dx, Cu, Cc, fractions), full USCS symbol, AASHTO group and group index |
| P04 | `m8-p04` | `ht.plot.plasticity_chart()` |
| P05 | `m8-p05` | `ht.plot.grain_size()` |
| Data for P06 | `m8-text-values` | Text values in a value column on P01 (TODO #15), and the datasets: the classification columns, `p.grain_size_summary()`, `p.index_properties()` |
| P06 | `m8-p06` | `ht.plot.water_content_profile()` |

The analyses are merged first. The other units branch off `main` after them, in the order of the table. This file lives on `m8-index-plots` until the intent is approved.

### Goal
Finish Phase 1's plots: P04 plasticity chart, P05 grain size distribution and P06 water content profile with Atterberg limits. Build the classification and gradation analyses they need (`docs/drafts/analysis.md` §2–3), and the datasets that M7 deferred until those analyses existed.

### Why
- M8 is next in SPEC §12.4 and is the first part of v0.2 (SPEC §1.3).
- The plasticity chart and the grain size curves are in the lab section of almost every geotechnical report. They're the most obvious gaps a v0.1 tester will notice.
- The classification and gradation analyses stand on their own: an engineer can get a USCS symbol, D10 or Cu for every specimen without drawing anything, and later plots use them (P17 uses the consistency index; P25 uses the size fractions).
- Users can't get `p.grain_size_summary()`, `p.index_properties()` and the classification columns from an AGS file until these analyses exist (`docs/data/datasets.md` §1, SPEC §10.2).

### Constraints
- Use the P00 framework and the P01 overlays (`plot/_overlays.py`). P06 builds on P01 and doesn't reimplement it.
- SPEC §2.6 (units; particle size stays in mm in both systems), §3 (plot contract), §4 (NP distinct from blank and counted; classification systems selectable per call and defined in the config), §10.3 and CLAUDE.md "Naming" (registry column names, checked against the whole registry), §11 (error messages), §12.1 (no new dependencies).
- Every standard's boundary, line and table lives in config with its citation, never in plot code (P05 draft pitfalls). One named system gives every boundary.
- Never drop data silently: NP specimens, curves with fewer than two points, Dx that can't be interpolated, and specimens a dataset can't combine are counted and reported.
- Dx is interpolated log-linearly and never extrapolated (analysis draft §3). Points are sorted by row, never one column at a time.
- Golden values are calculated by hand: A-line and U-line points, D-values from a hand-interpolated curve, Cu, Cc, and USCS and AASHTO symbols for boundary cases.
- **Done when** (SPEC §12.4): the P04–P06 acceptance criteria and the classification and Dx golden tests pass; each dataset feeds its plot unchanged; and `docs/plots/img/P04.png`, `P05-us.png`/`P05-si.png` and `P06-us.png`/`P06-si.png` are committed in each plot's close-out. TODO #15 meets its own criteria, written in its unit's spec step.

### Decisions (proposed, to settle in review)
1. **Where the specs live.** `docs/drafts/analysis.md` §2–3 is finished in place and marked decided, as §1 was in M3. P04 and P05 are promoted from `docs/plots/drafts/`. P06 has no draft, so its spec is written from scratch in its spec step.
2. **TODO #5 (verify the systems).** Verified in the analyses' spec step: ASTM D2487 USCS, AASHTO M 145, BS 5930 plasticity bands and ISO 14688-1 fractions. Claude doesn't have the standards themselves, so each value is checked against your copy (you are confirming the BS 5930 bands), or against a public secondary source that is named in the spec. TODO #5 closes when that's done.
3. **USCS scope.** The analysis gives the group symbol (including dual symbols such as SP-SM and GC-GM) from LL, PI, fines, sand and gravel percentages, Cu and Cc. The data don't say whether a soil is organic (that needs the oven-dried LL), so OL and OH are never assigned: the fine-grained symbol is the inorganic one, and the spec says so. Group names ("lean clay with sand") are left out. How a user records "organic" (no AGS heading holds it) and how P04 marks those specimens is TODO #22.
4. **P04 `regions=`** (P04 draft §14): in v0.2, as a user table of polygons in LL–PI space (`region`, then the vertices in order), so a region can be any shape, not only a rectangle. Drawing a project's group definitions is common, and the table is simple. The v0.4 item ("plasticity-chart data region", computed from the data) stays in v0.4, and returns its region in this same table, so it draws through `regions=` and keeps any shape.
5. **P05 header band** (P05 draft §14): with `astm_uscs`, fines is one band, because USCS has no clay–silt boundary. The `iso14688` system shows clay and silt separately. **Fraction systems** are one data structure: a named, ordered list of fractions with their boundaries in mm and a citation. The built-in ones (`astm_uscs`, `aashto`, `iso14688`) are read from config, and `fractions=` also takes a user's own in the same structure. The gradation analysis and the P05 header band both read it. `envelopes=` (user table) and `d_values=` are in v0.2.
6. **Text in a value column (TODO #15)** is built in its own unit before P06, because it changes P01 and P06 builds on P01. `NP` and `refusal` are recognized as flags (the `non_plastic` and `refusal` reasons). Any other text is counted, with a warning naming it, rather than being an error. Each text value is drawn as a marker at the left edge of the axis at its depth, one marker per unique text, with a legend entry such as "NP (3)". The stats box counts them the same way (`describe()` follows in Phase 3). The user cleans the data and reruns to remove them. P06 also reads NP from the `non_plastic` column that the datasets fill.
7. **SPEC §13 #2 (specimen combining in `p.index_properties()`).** Settled in P06's spec step. Proposed: one row per sample; where a sample has several specimens of a test, take the one nearest in depth to the water content specimen, and record which one in a column, with a warning that counts them. No row is multiplied.
8. **Column names.** New columns (the plasticity class, `gradation_uscs`, `uscs_symbol`, `aashto_group`, `aashto_group_index`, and one column per size fraction) are named in the analyses' spec and checked against the whole registry before they're added.

### Out of scope
- P25 (size fractions by geology unit). SPEC §1.3 doesn't list it for v0.2, and its draft now says so. The fractions this unit computes can already be drawn on P07.
- User-defined PSD regions and the plasticity chart's computed data region (v0.4).
- OL and OH, USCS group names and BS 5930 soil descriptions.
- Coloring P04 by USCS symbol (P04 draft §15), and envelopes computed from the data on P05 (P05 draft §15).
- Triaxial, clogging and SPT correlations (M11–M13).
- Changes to P01–P03 and P07, other than TODO #15 (decision 6) and fixing a mismatch that the "dataset feeds the plot unchanged" test finds.

### SPEC sections touched
- §4: the pointer to `analysis.md` §2–3 now says they're decided.
- §10.2: the M8 datasets are moved from "v0.2" to built at close-out, with columns in `docs/data/datasets.md`.
- §11: the Phase 1 sketch gets `grain_size()` and `water_content_profile()` calls.
- §12.4: M8 is marked done at close-out.
- §13 #2: settled (decision 7) and removed.
- `docs/drafts/analysis.md` §2–3; `docs/plots/P01-property-profile.md` §3, §8 and `docs/plots/README.md` "Out-of-range data" (decision 6); `docs/plots/README.md` (P04–P06 status); `docs/data/datasets.md` (its out-of-scope line, plus the new datasets); `docs/drafts/phase2-data.md` (the M8 datasets move out); `columns.yaml`; `config/defaults.yaml` or new config files for the systems; TODO #5 and #15 (closed), #22 (new).

## Plan: analyses

Spec: [`docs/drafts/analysis.md`](../drafts/analysis.md) §2–3, finished in the spec step (intent decision 1).

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines (not counting tests' data) is split.

### Package layout
```
src/hangtu/
  _data.py                        + flag_column(): reads a true/false column (moved from analysis/_spt.py)
  analysis/__init__.py            exports plasticity, gradation, uscs, aashto
  analysis/_plasticity.py         plasticity(), on_or_above_a_line(), the class rules (§2.4–2.5)
  analysis/_gradation.py          gradation(), passing_at(), d_value(), fraction systems (§3)
  analysis/_classification.py     uscs(), aashto() (§2.6–2.7)
  config/plasticity_systems.yaml  uscs and bs5930 lines and bands, with sources (§2.3)
  config/fraction_systems.yaml    astm_uscs, aashto, iso14688, with sources (§3.5)
  columns.yaml                    the new columns (decision 5)
tests/analysis/
  test_plasticity.py  test_gradation.py  test_fraction_systems.py  test_uscs.py  test_aashto.py
```
The modules are private (`_plasticity.py`), so `ht.analysis.plasticity` is the function and not a submodule, as with `_spt.py`.

### Decisions the build makes
Implementation choices §2–3 leave open. Any that changes what a user sees goes into the spec in the commit that builds it.
1. **One true/false reader.** `spt()` already reads `spt_refusal` cell by cell (true/false, 1/0, yes/no). It moves to `hangtu/_data.py` as `flag_column(df, column, hint)` in a refactor commit of its own, and `plasticity()` uses it for `non_plastic`.
2. **One A-line test.** `on_or_above_a_line(liquid_limit, plasticity_index, system)` in `_plasticity.py`, with the 1e-9 slack, is used by both class columns, by `uscs()` through them, and by P04 later.
3. **One passing function.** `passing_at(sizes, passing, size)` gives P(size) by the §3.5 rules (log-linear, exact at a point, P(0) = 0, the 100% and 0% ends, blank otherwise). `d_value(sizes, passing, x)` gives the finest crossing (§3.3). Fractions and D-values share the sorting and the monotonic check, so they can't disagree.
4. **The non-monotonic tolerance** is read from P001's default in `qc/rules.yaml` (0.5 %), not repeated, so it can't drift from QC. A project's QC override doesn't change it.
5. **Registry:** `plasticity_class_uscs`, `plasticity_class_bs5930`, `uscs_symbol`, `aashto_group` (text); `aashto_group_index` (number, count); `fraction_system` (text); `d15`, `d50`, `d85` (particle_size); `fines_content`, `sand_content`, `gravel_content`, `cobbles_content`, `boulders_content`, `silt_content`, `clay_content`, `silt_clay_content`, `fine_sand_content`, `coarse_sand_content` (percent, ratio). Each is checked against the whole registry by the naming test, with `ags: ["derived: docs/drafts/analysis.md §…"]`. GRAG fractions aren't read (analysis draft §3: always recomputed).
6. **Curves are grouped** on (`loca_id`, `specimen_id`) when `loca_id` is present, else `specimen_id`, keeping blanks in the keys and the order of first appearance (`groupby(..., sort=False, dropna=False)`). A curve whose key is blank is an error naming its rows, since its points can't be told apart.
7. **Fraction systems are checked by one validator**, run on the built-ins by a test and on a user's system at each call: names unique and unused in the registry (except the built-in fraction names), sizes in mm increasing, each lower = the previous upper, the first lower 0, the last upper `null` (open), parts inside their fraction.
8. **Units:** `particle_size` is resolved as SPEC §2.6 with `analysis=True` and converted to mm. The output's `attrs["units"]` lists the D-value columns in mm and keeps the input's other declared units.

### Build 1: `analysis: move the true/false column reader to _data`
- Refactor only (decision 1): `spt()` behaves the same, and its tests pass unchanged.

### Build 2: `analysis: add plasticity systems and ht.analysis.plasticity`
- `config/plasticity_systems.yaml`; `_plasticity.py` (§2.3–2.5; decisions 1–2); `columns.yaml`: the two class columns.
- Errors and warnings as §2.8 (the `plasticity()` ones).
- Tests, with the §2.9 golden values: the indices (LL 45, PL 20, w 30 → PI 25, LI 0.40, Ic 0.60); PI kept and warned when 1 point off; NP blanks; every USCS and BS 5930 class case listed; on the A-line → clay; PI > LL kept and warned; rows, order, `attrs` and `df` unchanged.

### Build 3: `analysis: add ht.analysis.gradation with D-values, Cu and Cc`
- `_gradation.py`: sorting, grouping, units, the monotonic check, `d_value()`, Cu and Cc, the carried columns (§3.3–3.4; decisions 3, 4, 6, 8). `columns.yaml`: `d15`, `d50`, `d85`.
- Tests on curve A (§3.7): D10 0.1261, D30 0.300, D60 0.7105 mm; Cu 5.633, Cc 1.004; D30 with the point at 30% removed; D10 blank on a curve starting at 15%; drops of 0.4 and 2 points; inches converted; rows shuffled give the same answer; fewer than two points; `d_values=(15, 85)`; the errors of §3.6.

### Build 4: `analysis: add fraction systems to ht.analysis.gradation`
- `config/fraction_systems.yaml`; the validator (decision 7); `passing_at()`; the `<fraction>_content` and `fraction_system` columns; `fractions=` as a name, a dict or a YAML path. `columns.yaml`: the fraction columns and `fraction_system`.
- Tests: curve A's fractions in all three systems (§3.7), including the blank ISO fractions; the fractions sum to 100 when none is blank; every built-in boundary against the §3.5 table (catches 0.475 and 20); a user system from a dict and from a file; an overlap, a gap and a name clash are errors naming the fraction.

### Build 5: `analysis: add ht.analysis.uscs`
- `_classification.py`: `uscs()` (§2.6): the `fraction_system` check, rescaling to the part finer than 75 mm, G/S, W/P, M/C, the dual symbols, the blanks counted by reason. `columns.yaml`: `uscs_symbol`.
- Tests: every §2.9 USCS symbol case; Cu and Cc from `d10`/`d30`/`d60` when blank; a missing or wrong `fraction_system` is an error; `gradation()` on curve A joined with its Atterberg row classifies end to end (SP).

### Build 6: `analysis: add ht.analysis.aashto`
- `aashto()` (§2.7): rounding, groups left to right, the group index, blanks counted. `columns.yaml`: `aashto_group`, `aashto_group_index`.
- Tests: every §2.9 AASHTO case, including A-2-4 against A-1 order, the A-7-5/A-7-6 split, a negative GI → 0, LL 40.4 rounding; a wrong `fraction_system` is an error.

### Build 7 (close-out): `analysis: close out the classification and gradation analyses`
- `docs/drafts/analysis.md` §2–3: any detail the build changed. The 🔬 values stay marked until TODO #5 is done.
- `CLAUDE.md`: the status line says the M8 analyses are done and P04 is next.
- This plan: a Results section, with notes for P04, P05 and the data unit.

### Verification
- After each build: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- At close-out: Python 3.13 and 3.14 (`uv run --isolated --python 3.1x pytest`); the lowest dependency versions, as in CLAUDE.md; `uv build`, and check that the wheel has both new config files and the new registry columns.

### Results
- 1664 tests pass on Python 3.12, 3.13 and 3.14, and with the lowest dependency versions (matplotlib 3.8.0, numpy 1.26.0, pandas 2.1.1, pint 0.24.4, pyyaml 6.0.1). The wheel has both new config files and the new registry columns.
- **Commits:** one per build step as planned, Build 1 being the refactor.
- **Changes from the plan:**
  - The fraction systems are in their own module, `analysis/_fractions.py`, rather than in `_gradation.py`, which was already about 300 lines (Build 4).
  - Two input errors in `plasticity()` that §2.8 didn't list: PL above LL on a plastic specimen, and a specimen marked NP with a PI. Recorded in §2.8.
  - A blank `specimen_id` in `gradation()` is an error (decision 6), recorded in §3.6.
  - A user's fraction system needs a `name`, not one of the built-in ones, so `uscs()` can't take it for `astm_uscs` (§3.5).
  - The Cu, Cc and fines limits in `uscs()` are compared with the A-line's 1e-9 slack: Cc = 0.3²/(0.1 × 0.9) computed as 0.9999999999999999 and made a well-graded sand poorly graded (§2.6).
  - `aashto()` leaves a group blank only when a missing value could decide it; a group a known value rules out is skipped (§2.7).
- **For P04:** draw the lines from `config/plasticity_systems.yaml` (`plasticity_system()`, `a_line()`, `on_or_above_a_line()` in `_plasticity.py`). The U-line's vertical part ends at PI = 7, as D2487 states it, while the sloped part starts at (16, 7.2); P04's spec decides how to join them.
- **For P05:** the header band reads the fraction system's `parts`; `fraction_system()` in `_fractions.py` resolves `fractions=` the same way `gradation()` does.
- **For the data unit:** `p.atterberg()` still computes LI and Ic itself (`datasets/_lab.py`); switch it to `plasticity()` there (§2.4). `index_properties()` runs `gradation()` twice (astm_uscs for `uscs()`, aashto for `aashto()`).
- **Still open:** the 🔬 values (TODO #5), including whether D2487 takes Cu and Cc from the curve rescaled to the part finer than 75 mm.

## Plan: P04

Spec: [`docs/plots/P04-plasticity-chart.md`](../plots/P04-plasticity-chart.md) (section numbers below are P04's unless marked otherwise).

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines (not counting tests' data) is split.

### Package layout
```
src/hangtu/
  columns.yaml               + template plasticity_regions: [label, liquid_limit, plasticity_index]
  plot/__init__.py           exports plasticity_chart
  plot/_values.py            color_groups() gains order= (Build 0)
  plot/_plasticity_chart.py  plasticity_chart(): zones, lines, labels, specimens
  plot/_regions.py           reads and checks the regions table, draws the polygons
  plot/_notes.py             + reason non_plastic_excluded
  plot/_layers.py            + P04 draw order
tests/plot/
  test_plasticity_chart.py              lines, zones, axes, specimens, counts
  test_plasticity_regions.py            the regions table
  test_plasticity_chart_acceptance.py   §12 against the example project and synthetic frames
```
- The module is `_plasticity_chart.py`, so `ht.plot.plasticity_chart` is the function and not a submodule (as `_profile.py`).
- `_regions.py` is separate because the table has its own rules (§8) and tests, as `_baseline.py` is for P07.

### Decisions the build makes
These fill gaps in P04. Any that changes what a user sees goes into P04 in the commit that builds it.
1. **Zones are polygons built from config.** Each zone is a list of half-planes in LL–PI space (left of LL = 50, on or above the A-line, PI ≥ 4, …) taken from `plasticity_systems.yaml` through `plasticity_system()` and `a_line()`. The polygon is the axes box clipped by those half-planes (Sutherland–Hodgman; every zone is convex). The same polygons give the CL-ML hatch, the zone label positions (their centroids) and the agreement test, so the drawing can't drift from the classes. No number from the standard is repeated in the plot module.
2. **USCS U-line:** the vertical part runs from PI = 0 to the sloped line's value at LL = 16 (0.9 × 8 = 7.2), computed from `u_line`, not from `vertical.up_to` (7, D2487's rounding). The config keeps `up_to: 7` as the standard writes it, with a comment pointing to P04 §14 #1. The left edge of the USCS zones is the U-line, so the region left of it (impossible soils) belongs to no zone and gets no label.
3. **BS 5930** zones are each band × (C on or above the A-line, M below), bounded above by PI = LL. Dividers at LL 70 and 90 end at PI = LL in data and are clipped by the 0–60 box, so the test reads their data, not their visible length.
4. **Equal aspect** with `ax.set_aspect("equal", adjustable="box")`, so in a `Sheet` panel the box shrinks rather than the limits changing. Line labels use `transform_rotates_text=True` with the line's angle in data, which stays right on screen when the aspect holds.
5. **x extension:** with no `xlim=`, the upper limit is 100, or `ceil(max LL / 20) × 20` when an LL is above 100 (115 → 120, 120 → 120). y is 0–60. Points beyond the limits (only possible with `xlim=`/`ylim=`, or PI > 60) go through `edge_markers` and are counted as `beyond_limit`.
6. **Zero rows** draw the empty chart with "No data", whatever the columns, without running the analysis, so `plasticity_chart(pd.DataFrame(), ax=panel)` works as a base. Any row needs `liquid_limit` (the analysis error).
7. **Counts:** NP rows get a new reason, `non_plastic_excluded` ("n non-plastic (NP) specimens not shown"), since the existing `non_plastic` wording is P07's ("n non-plastic (NP) values"). A row that isn't NP and has a blank LL or PI is one `nan` count, not one per column. The legend's n counts the specimens drawn, at the edge or not.
8. **Grouping:** `color_by` is any column (§15: `plasticity_class_uscs` works). `_values.color_groups()` gains `order=`, and P03's private `_groups()`, which is the same function with `order=`, is replaced by it in a refactor commit. Units in `order=` first, then the rest by name, then "(blank)" in gray. A `color_by` that isn't a column is an error, except `"geology_unit"`, which gives the hint (§3) and one color.
9. **`labels=True`** without a `specimen_id` column is an error naming the column. Blank IDs get no label.
10. **Regions table** (§8): read from a DataFrame or a CSV path (`ht.read_csv`), as P07's baseline. `label`, `liquid_limit` and `plasticity_index` are required. A blank `label`, a blank or non-numeric vertex, or fewer than three vertices is an error naming the region (or the rows, for a blank label). Vertices keep the table's row order. The centroid is the polygon's area centroid. `region_colors` keys not in the table warn, naming them; colors must be matplotlib colors (the palette check's wording).
11. **Draw order** in `_layers.py`: `REGIONS` 1.05, `ZONES` (CL-ML hatch) 1.15, `CHART_LINES` 1.2 (PI = LL, A-line, U-line, dividers), `ZONE_LABELS` 1.3, then `MARKERS`, `EDGE` and `ANNOTATIONS` as before (§7).
12. **No `units=` argument.** §10's signature has none: LL and PI are percentages, and `plasticity()` doesn't convert. `display_units` is checked like the other plots' and changes nothing.

### Build 0 (refactor): `plot: give color_groups an order and use it in P03`
- `_values.color_groups(df, color_by, palette, order=None)`; `_spt_histogram._groups()` removed in favor of it. No change in behavior.
- Tests: the P01 and P03 tests pass unchanged.

### Build 1: `P04: draw the plasticity chart's lines and zones`
- `_plasticity_chart.py`: `plasticity_chart()` with the full §10 signature. `regions=`/`region_colors=` raise `NotImplementedError` until Build 3, so no step ships a silent no-op.
- Zone polygons (decisions 1–3) for `uscs` and `bs5930`; the A-line, U-line, LL = 50 divider or the BS 5930 dividers, the PI = LL line; the CL-ML hatch; zone labels (`zone_labels=`) and line labels; band letters along the top for BS 5930.
- Axes (§6): labels, limits 0–100 × 0–60, ticks every 10, light major grid, equal aspect (decision 4). `xlim=`/`ylim=` checked with `_values.check_limits`. `system=` and `display_units=` checked. Empty input gives "No data" (decision 6).
- `_layers.py`: decision 11.
- Tests: every §12 geometry criterion for both systems, read back from the drawn lines and the hatch patch; the zone labels' text per system, and none with `zone_labels=False`; aspect 1 on the rendered axes, with default and user limits and in a `Sheet` panel; an unknown system is an error listing the systems; `assert_no_global_state`.

### Build 2: `P04: draw the specimens and count what isn't drawn`
- `plasticity()` on the data; scatter 5 pt in unit colors (decision 8), legend "Unit A (n = 24)" or "All specimens (n = …)"; the `geology_unit` hint.
- Footnote: NP (decision 7, new reason in `_notes.py`), blank LL or PI, `beyond_limit`; `note=`.
- x extension and edge markers (decision 5); `labels=` (decision 9).
- Tests: §12 agreement (a grid of points strictly inside the zones, right of the U-line and below PI = LL, falls in the zone polygon named by `plasticity_class_uscs` and `_bs5930`); §12 limits (LL 115 → 0–120, LL 100 → 0–100, PI 65 at the top edge and counted); NP and blank counts; `xlim=` edge markers and count; the analysis's warnings (PI > LL) pass through; text in `liquid_limit` is the analysis's error; `order=`, `palette=`, `color_by=None` and a `color_by` column that doesn't exist; `labels=True` text and its missing-column error; the hint once, and none with `geology_unit`; `assert_us_si_equivalent` with `("dimensionless", "dimensionless")`.

### Build 3: `P04: draw user regions from a table`
- `columns.yaml`: template `plasticity_regions` (§8), fields already in the registry.
- `_regions.py` (decision 10): read, check, draw outline 1 pt and fill alpha 0.12 in gray or `region_colors`, label at the centroid.
- Tests: a five-vertex non-rectangular region drawn closed, with its label at the hand-calculated centroid; the same from a CSV path; two regions; each error in decision 10; the `region_colors` warning and a bad color; `ht.template("plasticity_regions")` columns.

### Build 4 (close-out): `P04: add acceptance tests and close out P04`
- `test_plasticity_chart_acceptance.py`: every §12 automated criterion, on the example project (`ht.examples`: `atterberg.csv`, and `ht.plot.plasticity_chart(p.atterberg())` with no error, warning or hint, datasets.md §13 #14) and on synthetic frames.
- Visual check: `docs/plots/img/P04.png` (100 dpi) from the example project's Atterberg data with one region, looked at before committing. One file, since nothing converts (§9). The example data have no NP specimen, so the footnote count is checked in the synthetic tests.
- Close-out:
  - `docs/plots/README.md`: P04 status `built`.
  - P04: any detail the build changed, and the decisions above that aren't in it.
  - `README.md`: a `plasticity_chart` line in the plot examples (run by `test_readme.py`).
  - `CLAUDE.md`: the status line says P04 is done and P05 is next.
  - SPEC: no change expected (§11 already has the call; §12.4 waits for P06).
  - `TODO.md`: no change expected (#5 and #22 stay open).
  - This plan: a Results section.

### Verification
- After each build: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- At close-out: Python 3.13 and 3.14 (`uv run --isolated --python 3.1x pytest`); the lowest dependency versions, as in CLAUDE.md (`transform_rotates_text` needs matplotlib ≥ 3.6, so 3.8.0 is fine; check it there); `uv build`, and check that the wheel's `columns.yaml` has the `plasticity_regions` template.
- Look at `P04.png` against the §2 reference figure and the "A good version" list.

### Results
- 1745 tests pass on Python 3.12, 3.13 and 3.14, and with the lowest dependency versions (matplotlib 3.8.0, numpy 1.26.0, pandas 2.1.1, pint 0.24.4, pyyaml 6.0.1). The wheel has `_plasticity_chart.py`, `_regions.py` and the `plasticity_regions` template.
- **Commits:** the refactor (Build 0), one commit per build step as planned, and one fix the visual check showed: `P04: label CL-ML beside its zone`. At the default size the CL-ML zone is narrower than its label, whose white background hid the hatch. The label now sits just left of the U-line, level with the zone.
- **Changes from the plan**, each recorded in P04 in its commit:
  - Zone labels have a white background, so they read over the gridlines. BS 5930 band letters sit just above the axes rather than inside, where they ran into the CE and CV labels (§8).
  - The legend's n counts the specimens drawn, at the edge or not (§7). `color_by` that isn't a column, and `labels=True` without `specimen_id`, are errors (§11).
  - The lines read the slopes from `plasticity_system()` directly; `a_line()` isn't needed in the plot.
  - `README.md` has no `plasticity_chart` line. The example `atterberg.csv` carries the planted PI slip (QC A002, M9), which `plasticity()` warns about, and `test_readme.py` treats warnings as errors. A README example can come with the v0.2 release, on data without the slip or with the warning shown.
- **Example project:** `plasticity_chart(p.atterberg())` warns once, for the planted A002 row, and nothing else; the acceptance test asserts exactly that. On the datasets' good files (datasets.md §13 #14) it runs with no warning or hint.
- SPEC and `TODO.md`: no change (#5 and #22 stay open).
- **Visual check** (`docs/plots/img/P04.png`, the default 6.5 × 4.5 in figure saved at 100 dpi with `bbox_inches="tight"`, which trims it to 6.6 × 3.3 in): the example project's 14 specimens in the map's colors and order, with one five-vertex region. The A-line and U-line labels lie along their lines, CL-ML is hatched and labeled beside it, and the zone labels sit inside their zones. One thing to know:
  - With equal aspect, the 100 × 60 box doesn't fill the default figure's height once the legend takes its width, so there is white space above and below. `bbox_inches="tight"` on save trims it (P04 §5 notes the trimmed size), or the user passes `figsize=`.
- **For P05:** `_values.color_groups(..., order=)` is the shared grouping now (P01, P03, P04).
