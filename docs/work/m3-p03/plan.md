# P03: SPT class histogram — plan

Intent: [m3-spt/intent.md](../m3-spt/intent.md). Spec: `docs/plots/P03-spt-histograms.md`, promoted from `docs/plots/drafts/` in the spec step (renamed `P03-spt-histogram.md`, since there is one function). Section numbers below are P03's unless marked otherwise.

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines is split.

## Spec step: `P03: promote the SPT class histogram spec`
Move the draft and finish it:
- One function, `spt_histogram()`, with one table per call. The user picks the table and passes the rows it applies to (intent decision 6). `soil_class` and `spt_histograms()` are removed; §5 shows two calls on a `Sheet` instead.
- Default column `spt_n` (decision 7); the boundary convention is decided (decision 5).
- §10: the API below. §11: the cases below. §12: the acceptance criteria below.
- SPEC §11: `spt_histograms(spt)` becomes `spt_histogram(spt, table="cohesionless")`.
- `docs/plots/README.md`: the P03 row lists `spt_histogram` only, and links the spec. `docs/plots/drafts/README.md`: the P03 row points to it.

## Package layout
```
src/hangtu/
  plot/__init__.py              exports spt_histogram
  plot/_spt_histogram.py        spt_histogram()
  plot/_notes.py                (reasons from P02 reused)
tests/plot/
  test_spt_histogram.py         classes, bars, refusals, notes, errors
  test_spt_histogram_acceptance.py   §12 against the test data
```

## Decisions the build makes
They are in P03 from the spec step, since its API, edge cases and criteria depend on them. A build commit updates P03 only if one changes.
1. **`spt_histogram(df, *, n="spt_n", table="cohesionless", refusal="separate", color_by="geology_unit", order=None, hammer_efficiency=None, bar_labels=False, note=None, palette=None, units=None, display_units=None, figsize=None, ax=None, **style_overrides) -> (fig, ax)`**. `n` is `"spt_n"` or `"spt_n60"`: `spt_n_capped` gives the same classes as N unless the cap is below a class boundary, and then it misclassifies. `units=` goes to `ht.analysis.spt()`, for `spt_penetration`. `display_units` is accepted for the plot contract and changes nothing, since no value is converted (§9).
2. **Classes come from `ht.analysis.spt()` then `ht.analysis.spt_class()`**, so the boundaries and refusal rule are the analysis's, tested once.
3. **`refusal="separate"`** gives refusals their own hatched "Refusal" slot, last. **`"exclude"`** leaves them out and counts them (P02's reason). There is no `"cap"` option: a refusal is a refusal, not a "very dense" test.
4. **Percent** = tests in the class / tests classified in the unit × 100, refusals included in the denominator when they are shown. Blank N and (with `n="spt_n60"`) rows without N60 are left out of both and counted with P02's reasons. With no N60 anywhere, it's P02's error.
5. **Bars:** grouped side by side, in unit order (`order=`, then the rest by name, then "(blank)", as P07). Bar group width 0.8, split evenly. `color_by=None` gives one neutral bar per class, legend "All tests (n = …)". A unit in `order=` with no tests, or whose tests are all left out, gets no bars or legend entry and is listed in a note ("No classified tests: Unit C").
6. **X tick labels** are the class name and range on two lines ("Dense\n30–50", "Very dense\n≥ 50", "Very soft\n< 2"), with the ranges built from the table, so they match the lower-bound-inclusive convention. The x-axis title names the column: "SPT N class" or "SPT N60 class", and the table: "(cohesionless)".
7. **Y axis** "Tests in unit (%)", from 0 to a nice limit at or above the tallest bar, horizontal major gridlines only.
8. **`bar_labels=True`** writes the count above each non-zero bar.
9. **Hints:** "No 'geology_unit' column: all tests are drawn as one group." when the default `color_by` column is missing, and P02's refusal hint when both `spt_refusal` and `spt_penetration` are missing.

## Build 1: `P03: draw the SPT class histogram`
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

## Build 2: `P03: show refusals, bar labels and notes`
- Decisions 3 and 8; `note=`; the note for units in `order=` with no tests.
- Tests: the §12 golden with a refusal at N = 12 added: "Refusal" only, hatched, in the unit color, medium dense 2 of 8 (25.0 %); `refusal="exclude"`: the 7-test heights and "1 refusal not shown"; unknown `refusal=`; the shared hatch legend entry; bar labels on non-zero bars only; the no-tests note, for a unit in `order=` with no tests and for a unit whose tests are all blank.

## Build 3 (close-out): `P03: add acceptance tests and close out P03`
- Reuse `tests/data/spt.csv` from P02. The test splits it on `geology_unit`, as a user would: Fill and Alluvial sand are cohesionless, Glacial till and Residual soil cohesive.
- `test_spt_histogram_acceptance.py`: every §12 automated criterion against the CSV, counts worked out by hand.
- **Visual check** (100 dpi), looked at before committing: `visual-check.png`, a `Sheet` with the cohesionless and cohesive histograms side by side. One image is enough, since nothing converts between US and SI (§9); the plan says so in its Results.
- Close-out:
  - `docs/plots/README.md`: P03 status `built`.
  - P03 updated with the decisions above.
  - SPEC §12.4: M3 done. `CLAUDE.md` status line: M3 done, M4 next.
  - `TODO.md`: #3 updated (P03 no longer depends on it).
  - This plan: a Results section.

## Verification
- After each build: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- At close-out: Python 3.13 and 3.14; the lowest dependency versions (check `ax.bar` hatch colors with matplotlib 3.8, where `hatch.color` is an rcParam, not a bar argument).
- Look at the visual check against the §2 reference figure.
