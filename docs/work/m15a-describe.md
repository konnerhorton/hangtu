# M15 (a): `describe()`, the result object and the input rules

## Intent
M15 is the statistics milestone (SPEC §1.3, §5, §12.4). It splits into four units (decision 1). This unit, (a),
builds the shared foundation: the `ht.stats` namespace, the result object every statistics function returns, the
rules for which values a function reads, and the first function, `describe()`. P01's stats box and P07's summary
then compute through it.

**Goal:** an engineer passes measured or estimated values (an array, a Series, or a DataFrame with `value=` and
`by=`) and gets n, mean, median, standard deviation, CoV and percentiles per group, in the column's units. Values
the data flags (refusals, `<x`, `>x`, assumed, NP, bands) are counted and named, never silently pooled or dropped.
A plot's summary and `describe()` give the same numbers for the same rows.

**Why:**
- **Wave 1 left real cases to summarize:** N60 by geology unit with refusals, PI and unit weight by unit,
  (N1)60 and σ′v against depth, and several s_u and φ′ estimates per unit, some only as bands. Statistics come
  ahead of wave 0 to be designed against these (SPEC §1.3).
- **Every later statistics function inherits (a)'s choices:** how a result records what it summarized, how flagged
  values enter, and what happens when rows from different sources meet. Settling them once, on the simplest
  function, keeps `fit()`, `compare()` and later `characteristic()` consistent.
- **Two summaries of the same data can disagree today.** P01's stats box and P07's percentiles each compute their
  own (TODO #16). SPEC §5's "one calculation, many views" needs one place that computes.

**Scope:**
- `ht.stats.describe()`, with `by=` and `log=True` (SPEC §5);
- the result object: `.to_frame()`, `.to_dict()`, a readable summary, the units, and whether it summarizes
  *properties* (test values) or *parameters* (SPEC §5), so `characteristic()` can use it later unchanged;
- the input rules (decisions 3–5);
- P01's stats box and P07's summary computed through `describe()` (decision 6);
- reference entries and a docs site page for `ht.stats`.

**SPEC and TODO touched:**
- SPEC: §5 (the input rules, the result object), §1.3 and §12.4 (M15's split, `characteristic()` and P09 moved
  to M18), §12.1 if (a) needs SciPy (likely not until (c)).
- Other docs: `docs/drafts/phase3-stats.md` (decided items move out), P01 §8 and P07 §5 (their summaries).
- TODO: #8 (the censoring part that `describe()` uses), #9, #16 and #13 (moved to M18); #40 is (b).

### Decisions (intent discussion, 2026-10-29)
1. **M15 splits into four units:**
   - (a) this unit;
   - (b) correlation statistics (TODO #40, decision 7);
   - (c) `fit()` and P08: censored and bounded fits (TODO #8), ranked by AICc and each checked with an
     Anderson–Darling test (TODO #12);
   - (d) `compare()`, `compare_groups()` and `crosstab()` (TODO #10, #11).

   `characteristic()` and P09 move to M18 (selection), which needs them, with TODO #13. The judgments they need
   (the type of estimate, θ, L, an assumed V_X), the lognormal formulae and the framing for US users are settled
   there.
2. **`describe()` follows TODO #9:**
   - n = 1 gives the value as the mean and no standard deviation or CoV;
   - n < 3 warns;
   - P25/P75 are reported from n ≥ 4 and P5/P95 from n ≥ 20;
   - percentiles are Hyndman & Fan type 7, stated in the output;
   - no CoV for interval-scale columns (`scale: interval` in the registry).
3. **Flagged values** (TODO #8):
   - Refusals and `<x`/`>x` are censored values. `describe()` includes them at their bound with a note and a count,
     as the plots do; `fit()` treats them as censored in (c).
   - NP is left out and counted, never treated as blank.
   - **Assumed values (`#`) are flagged.** M14 (a) decided that assumed values are never pooled with measured
     ones, so they are left out by default and counted; how a user asks for them (a separate call, or an opt-in
     that marks the result) is a spec question.
4. **Bands are intervals.** A row with `<target>_lower` and `<target>_upper` and no value is left out of
   `describe()` and counted, never pooled as two values or summarized by its midpoint (M13 b2). (c) can fit them
   as interval-censored values.
5. **Mixing sources raises an error.** Rows from more than one source in one summary are an error naming the
   sources and saying to pass `by=`, filter, or pool them.
   - **The source columns are marked in the registry**, so every statistics function reads the same list and a new
     one is added there, not in code. The first are `correlation_name` (blank for measured), `source` (lab or
     field) and `test_type`. The rule applies when a column is present; a frame without them can't be checked.
   - **`test_type` is included although AGS `*_TYPE` is free text.** Two spellings of one method then count as two
     sources; the error lists the distinct values, so the user can see and fix naming differences.
   - **Pooling is deliberate:** an argument (e.g. `pool=["source"]`) pools across a source column, and the result
     and its summary record it, so a reviewer sees it.
   - **Values derived through an assumed value or a judgment** (`specific_gravity_source`) follow decision 3, not
     this one.
   - **Plots summarize per group they draw** (P01's `color_by`, P07's units). A stats box that would mix sources is
     left out with a note; a figure never raises for it.
6. **P01 and P07 call `describe()`.** Their summaries come from the same calculation, so a figure and a table of
   the same rows can't disagree (TODO #16). P07 adopts `describe()`'s fixed percentiles and floors; its
   `percentiles=` and `percentile_method=` arguments go, which changes P07 §5.
7. **Correlation statistics (TODO #40) are unit (b), in `ht.analysis.correlations`:**
   - each correlation's `scatter` becomes structured in the config (n, r², a standard deviation with its basis,
     and the source's own words);
   - where the source gives a standard deviation that converts to the target's units, it goes on the rows beside
     `<target>`, `_lower` and `_upper`;
   - n, r², the source's advice (in the authors' words, at most a sentence each, TODO #30) and later evaluations
     go in one table per correlation, joined on `correlation_name` when wanted.

### Open (for the spec step)
- **The result object:** its class, its `.to_frame()` columns (one row per group), what `.to_dict()` holds, and
  how the summary reads.
- **The registry field** that marks a source column, and the name of the pooling argument.
- **Assumed values:** how a user includes them, and how the result says so.
- **`log=True`:** what it reports (geometric mean, log-space standard deviation) and its label.
- **P07's bar under the fixed set:** which of `describe()`'s percentiles its bar spans (P25–P75 from n ≥ 4, or
  P5–P95 from n ≥ 20), what it draws below those counts, and what replaces `summary_min_count`.
- **Units:** resolved like an analysis (SPEC §2.6), and whether `display_units=` applies to a result.
- **Names** for the new columns of `.to_frame()`, checked against the registry.

### Out of scope
- Units (b) to (d), and `characteristic()` with P09 (M18).
- Other summaries in P07 (min–max, mean ± kσ, user values; the rest of TODO #16).
- Effective sample size and spatial correlation (with `characteristic()`).
