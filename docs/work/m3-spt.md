# M3: P02–P03 and the SPT analysis

## Intent

Shared intent for three units of work, each on its own branch and merged on its own:

| Unit | Branch | Plan | Builds |
|---|---|---|---|
| SPT analysis | `m3-spt-analysis` | [plan](#plan-spt-analysis) | `ht.analysis.spt()`, `ht.analysis.spt_class()` |
| P02 | `m3-p02` | [plan](#plan-p02) | `ht.plot.spt_profile()` |
| P03 | `m3-p03` | [plan](#plan-p03) | `ht.plot.spt_histogram()` |

The analysis is merged first. P02 and P03 branch off `main` after it, in that order.

### Goal
Build the SPT analysis (from `docs/drafts/analysis.md` §1), P02 SPT N profile and P03 SPT class histogram.

### Why
- M3 is the next milestone in SPEC §12.4.
- SPT is the most common test in US practice. P02 and P03 are both on almost every report.
- P02 builds on P01, so it shows whether the P01 overlays can really be reused.
- The analysis stands on its own: an engineer can compute N60, refusals and classes without drawing anything.

### Constraints
- Use the P00 framework and the P01 overlays (`plot/_overlays.py`). Don't reimplement them.
- SPEC §2.6 (units), §3 (plot contract), §4 (refusals at the cap with a note, N60 NULL until an energy ratio is given), §10.3 and CLAUDE.md "Naming" (registry column names), §11 (error messages), §12.1 (no new dependencies).
- Never drop data silently: refusals, blank N, rows with no energy ratio and excluded refusals all show up as counts.
- Golden values for the analysis are calculated by hand (CLAUDE.md "Workflow rules").
- **Done when** (SPEC §12.4): the P02 and P03 acceptance criteria and the SPT golden tests pass, and each plot's `visual-check.png` (US and SI) is committed in its close-out.

### Decisions
1. **Where the analysis spec lives.** `docs/drafts/analysis.md` §1 is finished in place as the SPT spec and marked decided. Analyses stay in one file of their own, apart from the plot specs, so they can be used without a plot; Atterberg and grain size follow in M4. This may be revisited when the file grows.
2. **Three units of work**, as in the table above.
3. **Mid-drive depth** from increments is deferred to Phase 2 (SPEC §8.2, §13.1). For CSV input, `depth` is what the user gives. The P02 spec says so.
4. **Refusal** comes from `spt_refusal` where it is filled in, else is inferred from `spt_penetration` < 450 mm. Report-string parsing and `refusal="extrapolate"` are deferred to Phase 2.
5. **SPT class tables** (TODO #4): the boundaries in `analysis.md` §1 are confirmed, with the lower bound inclusive, so N = 0 is "very loose" and N = 10 is "medium dense". Classes are computed from whichever N column the user names; the default is `spt_n`. User-defined bins come later.
6. **Cohesive or cohesionless** is the user's call. They pick the table (`table="cohesionless"` or `"cohesive"`) and pass the rows it applies to. `soil_class` isn't read, and there is no two-panel `spt_histograms()`: two calls on a `Sheet` do that.
7. **N or N60.** P02 and P03 plot `spt_n` by default. With `n="spt_n60"`, rows without N60 are left out and counted, and if no row has it, the error says to set `ht.settings.hammer_efficiency` or fill in `energy_ratio`. N and N60 are never mixed in one plot, and the axis label names the column.

### Out of scope
- AGS ingest, increments, mid-drive depth and report-string parsing (Phase 2).
- `refusal="extrapolate"`, and user-defined class bins.
- Statistics on censored refusals (TODO #8, Phase 3).
- Correlations from N (friction angle, modulus, s_u).
- Examples, the README and the tutorial (M5).

### SPEC sections touched
- §4: the pointer to `analysis.md` §1 says it is decided.
- §11: `spt_histograms(spt)` in the API sketch becomes `spt_histogram(spt, table="cohesionless")`.
- §13.1: deferred to Phase 2 (decision 3).
- `docs/drafts/analysis.md` §1, `docs/plots/README.md` (P02 and P03 status), `TODO.md` (#3 no longer blocks P03; #4 closed).
- `columns.yaml` (`spt_class`) and `config/spt_classes.yaml` (new).

## Plan: SPT analysis

Spec: [`docs/drafts/analysis.md`](../drafts/analysis.md) §1, finished in the spec step (intent decision 1).

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines is split.

### Spec
`analysis.md` §1 was finished in the spec commit: the API (§1.3–1.4), the refusal, N60, cap and class rules, the errors (§1.5) and the golden values (§1.6). SPEC §4, §8.2 and §13.1 were updated with it.

### Package layout
```
src/hangtu/
  __init__.py                   exports analysis
  analysis/__init__.py          exports spt, spt_class
  analysis/_spt.py              spt(), spt_class()
  config/spt_classes.yaml       the two class tables, with sources
  columns.yaml                  + spt_class; used_by gains "analysis" where it applies
tests/analysis/
  test_spt.py                   N60, refusal, cap, units, errors
  test_spt_class.py             class tables and boundaries
```
- The module is `_spt.py`, not `spt.py`, so `ht.analysis.spt` is the function and not a submodule (the same reason as `plot/_profile.py`).

### Decisions the build makes
These are implementation choices §1 leaves open. Any that changes what a user sees goes into §1 in the commit that builds it.
1. **Penetration units are resolved only when a row needs them** (a blank `spt_refusal` with a filled-in `spt_penetration`), through `units.resolve_units(..., analysis=True)`, so a table with every refusal filled in needs no penetration units (§1.3).
2. **`spt_refusal` is parsed by one helper** that maps the accepted values (§1.3) to booleans and lists the rows holding anything else. A column of strings or objects read from CSV with blanks is handled without a pandas FutureWarning.
3. **Classes use `numpy.searchsorted(lowers, n, side="right") - 1`**, not `pd.cut` (§1.4 pitfall).
4. **`config/spt_classes.yaml`** holds each table as `{source, classes: [{name, lower}, ...]}`, read with `_config.load`. Each class's upper bound is the next lower bound, so a later `bins=` argument is just another list.
5. **`spt_class` is a registry column** (text, `used_by: [P03]`): the class name. Checked against the registry, with no collision with `soil_class`.
6. **Row lists in errors** use `plot._data.rows_text`, moved to a shared module if importing it from `plot` would make `analysis` depend on `plot`. Any move is a refactor commit of its own.

### Build 1: `analysis: add ht.analysis.spt for N60, refusal and the cap`
- `analysis/_spt.py`: `spt()` (§1.3; decisions 1, 2 and 6). Errors: no `spt_n` column, non-numeric N, negative N, a bad `energy_ratio`, unknown `spt_penetration` units.
- `ht.analysis` namespace, exported from `hangtu`.
- Tests, with the §1.6 golden values:
  - N60: N = 30, ER = 80 → 40.0; N = 25, ER = 55 → 22.917 (to 3 decimals); ER from the argument, from the settings, and from the row in preference to both; no ER anywhere → blank; an existing N60 kept.
  - Refusal: given True/False kept; blank with penetration 300 mm → True, 450 mm → False; penetration 12 in → True (304.8 mm), 18 in → False; both blank → False.
  - Cap: N = 120 → 100; refusal with N = 38 → 100; refusal with blank N → 100; `cap=50` and `ht.settings.spt_cap = 50`.
  - Rows and order unchanged; `df` not modified; `attrs["units"]` kept.
  - Each error's text says what, where and what to do.

### Build 2: `analysis: add SPT class tables and ht.analysis.spt_class`
- `config/spt_classes.yaml` (decision 4); `columns.yaml`: `spt_class` (decision 5).
- `spt_class()` (§1.4; decision 3). An unknown `table` is an error listing the two tables.
- Tests:
  - Cohesionless golden (§1.6): N = [0, 4, 10, 29, 30, 50, 51] → very loose, loose, medium dense, medium dense, dense, very dense, very dense.
  - Cohesive golden: N = [0, 1, 2, 4, 8, 15, 30, 31] → very soft, very soft, soft, medium stiff, stiff, very stiff, hard, hard.
  - Every non-blank row lands in exactly one category; the counts sum to n.
  - A refusal with N = 12 → "Refusal" only; blank N → blank; the categories keep table order with "Refusal" last.
  - `n="spt_n60"`; a missing `n` column lists the columns available.
  - The registry naming test covers `spt_class`.

### Build 3 (close-out): `analysis: close out the SPT analysis`
- `docs/drafts/analysis.md` §1: any detail the build changed, and decisions that change what a user sees.
- `TODO.md`: #4 closed (the tables and convention are decided, in `config/spt_classes.yaml`); #3 no longer lists the SPT histograms as depending on it.
- `CLAUDE.md`: the status line says the SPT analysis is done and P02 is next.
- This plan: a Results section.

### Verification
- After each build: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- At close-out: Python 3.13 and 3.14 (`uv run --isolated --python 3.1x pytest`); the lowest dependency versions, as in CLAUDE.md; `uv build`, and check that the wheel has `config/spt_classes.yaml` and `spt_class` in `columns.yaml`.

### Results
- 814 tests pass on Python 3.12, 3.13 and 3.14, and with the lowest dependency versions (matplotlib 3.8.0, numpy 1.26.0, pandas 2.1.1, pint 0.24.4, pyyaml 6.0.1). The wheel has `hangtu/analysis/`, `config/spt_classes.yaml`, and `spt_class` in `columns.yaml`.
- **Commits:** a refactor first, then one commit per build step as planned.
  - `analysis: move the column readers out of the plot package`. `rows_text` and `numeric_column` moved from `plot/_data.py` to `hangtu/_data.py` (decision 6), so `ht.analysis` doesn't import `ht.plot`.
- **Changes from the plan**, each recorded in §1 in the close-out:
  - `spt_refusal` cells are read one at a time rather than with pandas `fillna`, which raised a FutureWarning on an object column read from CSV with blanks (decision 2).
  - §1.5 lists the `cap=` error, the energy-ratio hint, and the `spt_class` errors as built: `n` limited to the three N columns, and a negative `spt_n60` filled in by the user.
  - §1.4 says how to get N60 classes: the setting, `energy_ratio`, or `spt()` first. `spt_class()` takes no `hammer_efficiency=` of its own.
- **For P02 and P03:** with no `spt_refusal` and no `spt_penetration` column, `spt()` finds no refusals and says nothing. The plots should give the hint in P02 decision 8. An `energy_ratio` of 0.8 is accepted as 0.8 %; only 0 and values over 100 are errors.
- `TODO.md`: #4 closed; #3 no longer blocks P03. SPEC: no change beyond the spec commit.

## Plan: P02

Spec: [`docs/plots/P02-spt-profile.md`](../plots/P02-spt-profile.md). Section numbers below are P02's unless marked P01, analysis or SPEC.

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines is split.

### Package layout
```
src/hangtu/
  config/defaults.yaml          + presets spt_n, spt_n60, spt_n_capped
  plot/__init__.py              exports spt_profile
  plot/_profile.py              profile() split into checks and a shared _draw_profile()
  plot/_values.py               + Flag: marker, size, legend text and notes reason for a flagged row
  plot/_notes.py                + reasons refusal_excluded, no_energy_ratio; fields in reason text
  plot/_spt_profile.py          spt_profile()
  columns.yaml                  used_by gains P02 where it applies
tests/plot/
  test_spt_profile.py           columns, labels, overlays, units, errors
  test_spt_refusals.py          refusal markers, cap, limits, N60
  test_spt_profile_acceptance.py   §12 against the test data
tests/data/
  spt.csv
```
- The module is `_spt_profile.py`, so `ht.plot.spt_profile` is the function, not a submodule (as `_profile.py`).

### Decisions the build makes
These fill gaps in P02. Any that changes what a user sees goes into P02 in the commit that builds it.
1. **One drawing function for P01 and P02.** A refactor commit moves the body of `profile()`, argument checks included (P02 needs the same checks), into a private `_draw_profile(df, value, *, ..., flags, flag_kinds, clear_of, extra_hints)`; `profile()` passes its arguments through. No change in behavior. `flags` is a per-row array of keys into a mapping `{key: Flag(marker, size, legend_text, reason)}`. P01 builds it from `qualifier` (`_values.QUALIFIERS` becomes `Flag`s); P02 builds it from `spt_refusal`. Overlays, limits, legend, stats box and notes are then shared, not copied.
2. **`spt_profile()` is a thin wrapper:** check `n` and `refusal`, run `ht.analysis.spt(df, hammer_efficiency=, cap=, units=)`, set the refusal rows' value to the cap (or drop them with a count), apply the N60 rules, then call `_draw_profile()` with the preset named by `n`.
3. **Refusals drawn at the cap are flagged rows**, with marker ▶ (`">"` filled), 6 pt, legend text "refusal", reason `refusal`. Out of range they go through `edge_markers` like P01 qualifiers, so they're counted both ways.
4. **Footnote detail and a caller's notes.** A reason's text can end in `{where}`, filled by `Notes.set_where(reason, text)`, so `refusal` reads "{n} refusal{s}{where}": "2 refusals, shown at N = 100" in P02 and "1 refusal" elsewhere. `_draw_profile()` takes a `notes=` argument, so P02 hands it a `Notes` already holding the detail, the counts of rows it left out, and any extra line. `Flag` stays a 4-tuple, so P07's unpacking is unchanged, and `ax.ags_notes` stays plain counts.
5. **New reasons:** `refusal_excluded` "{n} refusal{s} not shown"; `no_energy_ratio` "{n} test{s} without an energy ratio not shown".
6. **X upper limit with refusals:** after P01's limits are worked out, if any refusal is drawn and `xlim` isn't given, the upper limit becomes `nice_limits(0, 1.05 × cap)`'s upper bound when that is higher (120 for a cap of 100). This happens in `_draw_profile()` through a `clear_of=` value, so the limit logic stays in one place.
7. **Stats box with refusals:** the values summarized are the drawn ones, so refusals count at the cap (SPEC §4). When a stats box is asked for and there are refusals, the footnote adds "Statistics include refusals at N = 100" through `Notes.add_text`. Rows P02 leaves out (excluded refusals, tests without N60) are removed before drawing and counted in the notes it passes in.
8. **Hints:** P01's hint dictionary, plus `spt_refusal` when both `spt_refusal` and `spt_penetration` are missing from the input ("refusals can't be found"). The check is on the user's `df`, since the analysis output always has `spt_refusal`: `hint_missing()` takes a third argument, `{column: reason}` for columns the caller found missing, which join the one hint. `_draw_profile()` passes its `extra_hints` there.
9. **The refusal and N60 errors use `HangtuError`.** A missing `spt_n` is the analysis's `ColumnError`, unchanged.

### Build 0 (refactor): `P01: draw profiles through a shared function with flags`
- `_values.Flag`; `_draw_profile()` with `flags`, `clear_of` and extra hints (decisions 1, 6, 8), all with P01's behavior when unused.
- Tests: the P01 and P07 tests pass unchanged.

### Build 1: `P02: plot SPT N against depth or elevation`
- Presets (§6) in `defaults.yaml`; `_spt_profile.py` and the export; decisions 2, 8 and 9; `refusal="cap"` drawing (decision 3) but with the plain footnote, and no limit clearance yet.
- Tests: default column and label "SPT N"; "SPT N60" and "SPT N (capped)"; `vs="depth"` and `"elevation"`; color by unit; `connect=True`; each P01 overlay passed through (strata, water level, ranges, design lines, reference lines, stats box, note); `assert_us_si_equivalent` with `("length",)` and N unchanged; `assert_no_global_state`, also with `ax=` on a `Sheet` panel; empty input gives "No data"; a missing `spt_n` lists the columns; bad `n` and `refusal` values; the refusal hint shown only when both columns are missing.

### Build 2: `P02: draw refusals at the cap and N60 with counts`
- Decisions 4–7; `refusal="exclude"`; the N60 rules (§11).
- Tests:
  - golden: a refusal with N = 38 at x = 100, ▶ in the unit color; with `cap=50` and with `ht.settings.spt_cap = 50`, at 50; a refusal with blank N and one with N = 150 at the cap; a non-refusal N = 150 at 150;
  - N60 golden: N = 30, ER = 80 at 40.0; N = 90, ER = 80 at 120.0;
  - legend "refusal (2)"; footnote "2 refusals, shown at N = 100" and "N60 = 100" with `n="spt_n60"`; `ax.ags_notes["refusal"] == 2`;
  - `refusal="exclude"`: nothing at the cap, footnote "2 refusals not shown";
  - x upper limit 120 with refusals and the cap at 100; the P01 limit without them; `xlim=(0, 60)` puts refusals at the edge, counted both ways;
  - `n="spt_n60"` with ER on some rows (count) and on none (error text, §11);
  - stats box with refusals and its footnote line.

### Build 3 (close-out): `P02: add test data, acceptance tests and close out P02`
- `tests/data/spt.csv` (§12): realistic, four holes, three units plus fill, about 80 tests over 30 m in feet, ER on two holes only, a few refusals (one with blank N, some found from `spt_penetration` in inches), blank N rows.
- `test_spt_profile_acceptance.py`: every §12 automated criterion against the CSV, with the counts worked out by hand.
- **Visual check** (100 dpi), looked at before committing: `visual-check.png`, a `Sheet` with the profile in US and SI side by side, with strata and a water level.
- Close-out:
  - `docs/plots/README.md`: P02 status `built`; P02 status `built` and the decisions above that change what a user sees.
  - `CLAUDE.md`: status line, P02 done and P03 next.
  - This plan: a Results section.

### Verification
- After each build: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- At close-out: Python 3.13 and 3.14 (`uv run --isolated --python 3.1x pytest`); the lowest dependency versions, as in CLAUDE.md; `uv build`, and check the wheel's `defaults.yaml` has the SPT presets.
- Look at the visual check against the §2 reference figure and the "A good version" list.

### Results
- 867 tests pass on Python 3.12, 3.13 and 3.14, and with the lowest dependency versions (matplotlib 3.8.0, numpy 1.26.0, pandas 2.1.1, pint 0.24.4). The wheel has `plot/_spt_profile.py` and the three SPT presets in `defaults.yaml`.
- **Commits:** one per build step, as planned. The acceptance counts against `tests/data/spt.csv` matched the hand counts the first time.
- **Changes from the plan**, each recorded here in its commit:
  - Build 0 moved `profile()`'s whole body, checks included, into `_draw_profile()` (decision 1).
  - Build 1: the refusal hint could never fire, because `_draw_profile()` checked the analysis output, which always has `spt_refusal`. `hint_missing()` now takes columns the caller found missing (decision 8).
  - Build 2: footnote detail comes from `Notes.set_where()` and a `notes=` argument to `_draw_profile()`, not a field on `Flag`, so P07 is untouched (decisions 4 and 7).
  - `columns.yaml` needed no change: every column P02 reads already listed it.
- **P02 spec:** status `built`; the hint and N60 error texts as built; with no N at all, `n="spt_n60"` shows "No data" rather than the energy-ratio error; `refusal="exclude"` doesn't extend the axis.
- `TODO.md`: no change. SPEC: no change.
- **Visual check** (`visual-check.png`, Letter, 100 dpi): N in US with `connect=True` beside N60 in SI, with strata and a water level. Refusals at 100 clear of the frame (axis to 120), the hole lines running out to them, and the footnotes "5 refusals, shown at N = 100" and "N60 = 100" with "36 tests without an energy ratio not shown". Two things to know, both P01 behavior:
  - the legend lists units alphabetically (Alluvial sand before Fill), not in stratigraphic order; `palette=` or the session palette sets colors, but there is no `order=` in P01;
  - the strata in the figure are idealized, so a few points sit just outside their band.

## Plan: P03

Spec: `docs/plots/P03-spt-histograms.md`, promoted from `docs/plots/drafts/` in the spec step (renamed `P03-spt-histogram.md`, since there is one function). Section numbers below are P03's unless marked otherwise.

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines is split.

### Spec step: `P03: promote the SPT class histogram spec`
Move the draft and finish it:
- One function, `spt_histogram()`, with one table per call. The user picks the table and passes the rows it applies to (intent decision 6). `soil_class` and `spt_histograms()` are removed; §5 shows two calls on a `Sheet` instead.
- Default column `spt_n` (decision 7); the boundary convention is decided (decision 5).
- §10: the API below. §11: the cases below. §12: the acceptance criteria below.
- SPEC §11: `spt_histograms(spt)` becomes `spt_histogram(spt, table="cohesionless")`.
- `docs/plots/README.md`: the P03 row lists `spt_histogram` only, and links the spec. `docs/plots/drafts/README.md`: the P03 row points to it.

### Package layout
```
src/hangtu/
  plot/__init__.py              exports spt_histogram
  plot/_spt_histogram.py        spt_histogram()
  plot/_notes.py                (reasons from P02 reused)
tests/plot/
  test_spt_histogram.py         classes, bars, refusals, notes, errors
  test_spt_histogram_acceptance.py   §12 against the test data
```

### Decisions the build makes
They are in P03 from the spec step, since its API, edge cases and criteria depend on them. A build commit updates P03 only if one changes.
1. **`spt_histogram(df, *, n="spt_n", table="cohesionless", refusal="separate", color_by="geology_unit", order=None, hammer_efficiency=None, bar_labels=False, note=None, palette=None, units=None, display_units=None, figsize=None, ax=None, **style_overrides) -> (fig, ax)`**. `n` is `"spt_n"` or `"spt_n60"`: `spt_n_capped` gives the same classes as N unless the cap is below a class boundary, and then it misclassifies. `units=` goes to `ht.analysis.spt()`, for `spt_penetration`. `display_units` is accepted for the plot contract and changes nothing, since no value is converted (§9).
2. **Classes come from `ht.analysis.spt()` then `ht.analysis.spt_class()`**, so the boundaries and refusal rule are the analysis's, tested once.
3. **`refusal="separate"`** gives refusals their own hatched "Refusal" slot, last. **`"exclude"`** leaves them out and counts them (P02's reason). There is no `"cap"` option: a refusal is a refusal, not a "very dense" test.
4. **Percent** = tests in the class / tests classified in the unit × 100, refusals included in the denominator when they are shown. Blank N and (with `n="spt_n60"`) rows without N60 are left out of both and counted with P02's reasons. With no N60 anywhere, it's P02's error.
5. **Bars:** grouped side by side, in unit order (`order=`, then the rest by name, then "(blank)", as P07). Bar group width 0.8, split evenly. `color_by=None` gives one neutral bar per class, legend "All tests (n = …)". A unit in `order=` with no tests, or whose tests are all left out, gets no bars or legend entry and is listed in a note ("No classified tests: Unit C").
6. **X tick labels** are the class name, one word per line, then the range ("Dense\n30–50", "Very\ndense\n≥ 50", "Very\nsoft\n< 2"; changed in the close-out from two lines, which overlapped on a half-Letter `Sheet` panel), with the ranges built from the table, so they match the lower-bound-inclusive convention. The x-axis title names the column: "SPT N class" or "SPT N60 class", and the table: "(cohesionless)".
7. **Y axis** "Tests in unit (%)", from 0 to a nice limit at or above the tallest bar, horizontal major gridlines only.
8. **`bar_labels=True`** writes the count above each non-zero bar.
9. **Hints:** "No 'geology_unit' column: all tests are drawn as one group." when the default `color_by` column is missing, and P02's refusal hint when both `spt_refusal` and `spt_penetration` are missing.

### Build 1: `P03: draw the SPT class histogram`
- `_spt_histogram.py` and the export, decisions 1, 2, 4–7 and 9, with `refusal="separate"`.
- Tests:
  - The golden from §12: N = [0, 4, 10, 29, 30, 50, 51] in one unit → bar heights 14.3, 14.3, 28.6, 14.3, 28.6 % (1, 1, 2, 1, 2 of 7), read back from the patches.
  - The cohesive table: tick labels and order.
  - Every test in exactly one bar (the bar counts sum to n per unit).
  - Two units with different n: heights per unit, legend "Unit A (n = 4)".
  - Unit order with and without `order=`; "(blank)"; `color_by=None`.
  - Blank N counted; `n="spt_n60"` partial (count) and none (error); unknown `n=` and `table=`.
  - The two hints, and none when the columns are there.
  - `assert_no_global_state`, also with `ax=` on a `Sheet` panel; `display_units` changes nothing; empty input.

### Build 2: `P03: show refusals, bar labels and notes`
- Decisions 3 and 8; `note=`; the note for units in `order=` with no tests.
- Tests: the §12 golden with a refusal at N = 12 added: "Refusal" only, hatched, in the unit color, medium dense 2 of 8 (25.0 %); `refusal="exclude"`: the 7-test heights and "1 refusal not shown"; unknown `refusal=`; the shared hatch legend entry; bar labels on non-zero bars only; the no-tests note, for a unit in `order=` with no tests and for a unit whose tests are all blank.

### Build 3 (close-out): `P03: add acceptance tests and close out P03`
- Reuse `tests/data/spt.csv` from P02. The test splits it on `geology_unit`, as a user would: Fill and Alluvial sand are cohesionless, Glacial till and Residual soil cohesive.
- `test_spt_histogram_acceptance.py`: every §12 automated criterion against the CSV, counts worked out by hand.
- **Visual check** (100 dpi), looked at before committing: `visual-check.png`, a `Sheet` with the cohesionless and cohesive histograms side by side. One image is enough, since nothing converts between US and SI (§9); the plan says so in its Results.
- Close-out:
  - `docs/plots/README.md`: P03 status `built`.
  - P03 updated with the decisions above.
  - SPEC §12.4: M3 done. `CLAUDE.md` status line: M3 done, M4 next.
  - `TODO.md`: #3 updated (P03 no longer depends on it).
  - This plan: a Results section.

### Verification
- After each build: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- At close-out: Python 3.13 and 3.14; the lowest dependency versions (check `ax.bar` hatch colors with matplotlib 3.8, where `hatch.color` is an rcParam, not a bar argument).
- Look at the visual check against the §2 reference figure.

### Results
- 915 tests pass on Python 3.12, 3.13 and 3.14, and with the lowest dependency versions (matplotlib 3.8.0, numpy 1.26.0, pandas 2.1.1, pint 0.24.4). The refusal hatch takes the unit color on matplotlib 3.8 and 3.11: it follows the bar's explicit edge color.
- **Commits:** one per build step, plus one for the tick labels (below). Build 1 came to about 520 lines with its tests, over the 300-line guide; it is one idea (the plot and its tests), as P02's first build (447 lines) was.
- **Changes from the plan**, each recorded in its commit:
  - Build 2: `note=` goes in the footnote, not inside the axes as P01's does, where it would cover the bars (P03 §8). The y limit leaves room for bar labels.
  - Close-out: the tick labels put each word of a class name on its own line (decision 6, P03 §6). The visual check showed the two-line labels running into each other on a half-Letter `Sheet` panel.
- **Acceptance:** `tests/data/spt.csv` split on `geology_unit` into Fill and Alluvial sand (cohesionless) and Glacial till and Residual soil (cohesive). Two hand-worked expectations were wrong at first, not the code: the y limit for a tallest bar of 87 % is 100, since a step of 10 would give more than 8 ticks, and N = 8 at ER 82 % is N60 = 10.9, medium dense.
- **Visual check** (`visual-check.png`, Letter, 100 dpi, bar labels on): cohesionless beside cohesive. One image, since nothing converts between US and SI (§9). The test data's cohesive units are stiff, so almost every test is "Hard"; the 5 Residual soil refusals are a separate hatched bar.
- `TODO.md`: no change; #3 already said P03 doesn't depend on it. `SPEC.md`: no change at close-out. §12.4 has no done marker for any milestone, so none was added for M3; `CLAUDE.md` records it.
