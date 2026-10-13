# P02: SPT N profile — plan

Intent: [m3-spt/intent.md](../m3-spt/intent.md). Spec: [`docs/plots/P02-spt-profile.md`](../../plots/P02-spt-profile.md). Section numbers below are P02's unless marked P01, analysis or SPEC.

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines is split.

## Package layout
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

## Decisions the build makes
These fill gaps in P02. Any that changes what a user sees goes into P02 in the commit that builds it.
1. **One drawing function for P01 and P02.** A refactor commit moves the body of `profile()`, argument checks included (P02 needs the same checks), into a private `_draw_profile(df, value, *, ..., flags, flag_kinds, clear_of, extra_hints)`; `profile()` passes its arguments through. No change in behavior. `flags` is a per-row array of keys into a mapping `{key: Flag(marker, size, legend_text, reason)}`. P01 builds it from `qualifier` (`_values.QUALIFIERS` becomes `Flag`s); P02 builds it from `spt_refusal`. Overlays, limits, legend, stats box and notes are then shared, not copied.
2. **`spt_profile()` is a thin wrapper:** check `n` and `refusal`, run `ht.analysis.spt(df, hammer_efficiency=, cap=, units=)`, set the refusal rows' value to the cap (or drop them with a count), apply the N60 rules, then call `_draw_profile()` with the preset named by `n`.
3. **Refusals drawn at the cap are flagged rows**, with marker ▶ (`">"` filled), 6 pt, legend text "refusal", reason `refusal`. Out of range they go through `edge_markers` like P01 qualifiers, so they're counted both ways.
4. **Footnote text with fields.** `Notes.add` and `Notes.count` take keyword fields that fill the reason's text, so `refusal` reads "{n} refusal{s}, shown at {column} = {cap}" ("2 refusals, shown at N = 100"). Counts in `ax.ags_notes` stay plain integers by reason. The existing `refusal` text is only used by tests so far; it changes to the field form.
5. **New reasons:** `refusal_excluded` "{n} refusal{s} not shown"; `no_energy_ratio` "{n} test{s} without an energy ratio not shown".
6. **X upper limit with refusals:** after P01's limits are worked out, if any refusal is drawn and `xlim` isn't given, the upper limit becomes `nice_limits(0, 1.05 × cap)`'s upper bound when that is higher (120 for a cap of 100). This happens in `_draw_profile()` through a `clear_of=` value, so the limit logic stays in one place.
7. **Stats box with refusals:** the values summarized are the drawn ones, so refusals count at the cap (SPEC §4). When any are included, the footnote adds "Statistics include refusals at N = 100" through `Notes.add_text`.
8. **Hints:** P01's hint dictionary, plus `spt_refusal` when both `spt_refusal` and `spt_penetration` are missing from the input ("refusals can't be found"). The check is on the user's `df`, since the analysis output always has `spt_refusal`: `hint_missing()` takes a third argument, `{column: reason}` for columns the caller found missing, which join the one hint. `_draw_profile()` passes its `extra_hints` there.
9. **The refusal and N60 errors use `HangtuError`.** A missing `spt_n` is the analysis's `ColumnError`, unchanged.

## Build 0 (refactor): `P01: draw profiles through a shared function with flags`
- `_values.Flag`; `_draw_profile()` with `flags`, `clear_of` and extra hints (decisions 1, 6, 8), all with P01's behavior when unused.
- Tests: the P01 and P07 tests pass unchanged.

## Build 1: `P02: plot SPT N against depth or elevation`
- Presets (§6) in `defaults.yaml`; `_spt_profile.py` and the export; decisions 2, 8 and 9; `refusal="cap"` drawing (decision 3) but with the plain footnote, and no limit clearance yet.
- Tests: default column and label "SPT N"; "SPT N60" and "SPT N (capped)"; `vs="depth"` and `"elevation"`; color by unit; `connect=True`; each P01 overlay passed through (strata, water level, ranges, design lines, reference lines, stats box, note); `assert_us_si_equivalent` with `("length",)` and N unchanged; `assert_no_global_state`, also with `ax=` on a `Sheet` panel; empty input gives "No data"; a missing `spt_n` lists the columns; bad `n` and `refusal` values; the refusal hint shown only when both columns are missing.

## Build 2: `P02: draw refusals at the cap and N60 with counts`
- Decisions 4–7; `refusal="exclude"`; the N60 rules (§11).
- Tests:
  - golden: a refusal with N = 38 at x = 100, ▶ in the unit color; with `cap=50` and with `ht.settings.spt_cap = 50`, at 50; a refusal with blank N and one with N = 150 at the cap; a non-refusal N = 150 at 150;
  - N60 golden: N = 30, ER = 80 at 40.0; N = 90, ER = 80 at 120.0;
  - legend "refusal (2)"; footnote "2 refusals, shown at N = 100" and "N60 = 100" with `n="spt_n60"`; `ax.ags_notes["refusal"] == 2`;
  - `refusal="exclude"`: nothing at the cap, footnote "2 refusals not shown";
  - x upper limit 120 with refusals and the cap at 100; the P01 limit without them; `xlim=(0, 60)` puts refusals at the edge, counted both ways;
  - `n="spt_n60"` with ER on some rows (count) and on none (error text, §11);
  - stats box with refusals and its footnote line.

## Build 3 (close-out): `P02: add test data, acceptance tests and close out P02`
- `tests/data/spt.csv` (§12): realistic, four holes, three units plus fill, about 80 tests over 30 m in feet, ER on two holes only, a few refusals (one with blank N, some found from `spt_penetration` in inches), blank N rows.
- `test_spt_profile_acceptance.py`: every §12 automated criterion against the CSV, with the counts worked out by hand.
- **Visual check** (100 dpi), looked at before committing: `visual-check.png`, a `Sheet` with the profile in US and SI side by side, with strata and a water level.
- Close-out:
  - `docs/plots/README.md`: P02 status `built`; P02 status `built` and the decisions above that change what a user sees.
  - `CLAUDE.md`: status line, P02 done and P03 next.
  - This plan: a Results section.

## Verification
- After each build: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- At close-out: Python 3.13 and 3.14 (`uv run --isolated --python 3.1x pytest`); the lowest dependency versions, as in CLAUDE.md; `uv build`, and check the wheel's `defaults.yaml` has the SPT presets.
- Look at the visual check against the §2 reference figure and the "A good version" list.
