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

## Spec
Numbered items refer to this section's decisions; "intent n" to the intent's. 🟡 marks a choice proposed here,
awaiting review.

### Changes
- **SPEC §5:** the input rules every statistics function follows (Decisions 3–6), the result object (Decision 2),
  and `describe()` in the function list as built.
- **SPEC §1.3 and §12.4:** M15 split into (a)–(d); `characteristic()` and P09 move to M18 (intent 1). §12.4's M15
  row: `describe`, `fit`, `compare`, `compare_groups`, `crosstab`; P08; "done when" scipy reference values and
  the example project's cases. M18's row gains `characteristic` and P09.
- **SPEC §4:** the bullet on PI by geology unit names `ht.stats.describe()` in place of `summary_by()`
  (Decision 9).
- **`docs/drafts/phase3-stats.md`:** `describe` marked decided, pointing here; the constraint from M13 b2 is
  settled (Decision 4); the `characteristic` row moves under M18.
- **Registry (`columns.yaml`):** a `statistics:` field on the source and flag columns (Decision 3), described in
  the file's header and in P00 §5. No new data columns.
- **P01 §8** (the stats box) and **P07 §5, §7, §8, §10** (the summary): Decisions 7 and 8.
- **`ht.analysis.summary_by()` removed** (Decision 9), with the pages and docstrings that name it.
- **TODO:** #9 and #16 (the part built here) resolved and removed; #8 and #12 keep only what (c) builds; #13 points
  to M18; #40 points to (b).
- **Docs site:** `docs/site/reference/stats.md` (mkdocstrings for `ht.stats`), a guide page
  `docs/site/guides/statistics.md` with an example in `docs/site/examples/`, both in the `nav`.

### Decisions
1. **`ht.stats.describe()`.**
   ```python
   describe(data, *, value=None, by=None, percentiles=(5, 25, 75, 95), log=False, pool=None,
            include_assumed=False, units=None, display_units=None) -> DescribeResult
   ```
   - **`data`:** a DataFrame with `value=` (required), a Series (its name is the value; `value=` is an error), or a
     list or array of numbers. Flags, sources and `by=` need a DataFrame; with a Series or array they are errors
     saying so.
   - **`by`:** a column name or a list of them. One summary per combination present, sorted by each column's
     categorical order if it has one, else by name; a blank key is its own group, `"(blank)"`, last (as
     `summary_by()`). `by=None` summarizes all rows as one group, `"All"`.
   - **Values read:** the value column's numbers. Text in it is read with `text_values()` as P01 does: `NP` and
     `refusal` are recognized, other text is counted by its spelling with one warning naming it. Blank cells are
     counted, not warned about. A bool column, or one with no numbers and no recognized text, is an error.
   - **Statistics per group** (TODO #9, intent 2):

     | Statistic | Column in `.to_frame()` | Reported when |
     |---|---|---|
     | count | `count` | always (0 for a group with no numbers) |
     | mean | `mean` | count ≥ 1 |
     | standard deviation (n − 1) | `standard_deviation` | count ≥ 2 |
     | coefficient of variation | `coefficient_of_variation` | count ≥ 2, ratio scale, mean > 0 |
     | minimum, median, maximum | `minimum`, `median`, `maximum` | count ≥ 1 |
     | each of `percentiles` | `percentile_<p>` (`percentile_25`, `percentile_2_5`) | count × min(p, 100 − p) / 100 ≥ 1 |

     - **`percentiles=`** chooses which percentiles are reported: numbers strictly between 0 and 100, ascending,
       no repeats (else an error with an example). The default is TODO #9's set. The median is always reported as
       `median`; 50 in the list adds `percentile_50` with the same value.
     - **One floor rule for every percentile:** P*p* is reported only when there is at least one value beyond it
       on each side, count × min(p, 100 − p) / 100 ≥ 1. It gives TODO #9's floors (P25/P75 from 4 values, P5/P95
       from 20) and extends them to any choice (P10/P90 from 10, P2.5 from 40).
     - **The method is fixed:** Hyndman & Fan (1996) definition 7 (`numpy.percentile`'s `"linear"`), named in
       the result. There is no method argument, so two summaries of the same rows can't differ by it.

     A statistic below its floor is NaN, and the summary says why ("P5/P95 need 20 values"). CoV is NaN on a
     column the registry marks `scale: interval` (elevation, depth) and for a column not in the registry it is
     reported, with the summary saying the scale is unknown. One warning names the groups with count < 3.
   - **`log=True`** 🟡: `geometric_mean` = exp(mean of ln x) and `geometric_standard_deviation` = exp(standard
     deviation of ln x), a dimensionless factor whatever the log's base, replace `mean`, `standard_deviation` and
     `coefficient_of_variation`. Percentiles, minimum, median and maximum stay of the values: a percentile doesn't
     change under a log transform apart from the interpolation between two values, and P01 and P07 already
     summarize log axes this way. Values ≤ 0 are left out and counted (`count_not_positive`), with one warning.
   - **Units:** the value's unit resolves `units=` → `attrs["units"]` → the registry for dimensionless and count
     kinds → an error naming the column and how to declare it, as for an analysis (SPEC §2.6). A list or array
     takes `units=` if given; without it the result's unit is `None` and the summary says "(units not given)".
     `display_units=` 🟡 converts the values before the statistics are computed; `None` keeps the column's unit.
     It never falls back to `ht.settings.display_units`, so a summary doesn't change unit with a session setting.
     CoV and the geometric standard deviation don't change with units.
   - **Errors and warnings** follow the house rule (what, where, what to do). Warnings: unknown text, count < 3,
     values left out (assumed, bands, ≤ 0 on `log=True`), one each per call.
2. **The result object.** `DescribeResult`, a frozen dataclass in `ht.stats`, on a private base that (c), (d) and
   M18's results share 🟡.
   - **Fields:** `kind` (`"property"` here; `"parameter"` for M18's results, SPEC §5), `function`
     (`"describe"`), `value`, `unit`, `by`, `log`, `pooled` (the pooled columns), `include_assumed`,
     `percentile_method` (`"Hyndman & Fan (1996) definition 7"`), `groups` (one record per group with its
     statistics, counts and source breakdown), `notes` (the text lines of the summary), `judgments` (copied from
     `attrs["judgments"]` when the input carries them, so a summary of σ′v-derived values records the
     judgments behind them), and `hangtu_version`.
   - **`.to_frame()`:** one row per group: the `by` columns, then the statistics of Decision 1, then the counts
     (Decision 3: `count_at_least`, `count_at_most`, `count_non_plastic`, `count_assumed`, `count_range`,
     `count_blank`, `count_text`, `count_not_positive` with `log=True`). `attrs["units"]` gives the unit of each
     statistic that has one.
   - **`.to_dict()`:** every field, JSON-serializable (NaN as `None`), for reports and later AGSi export.
   - **`str(result)`** (and the notebook repr): a readable table of the frame's statistics with units in the
     header, then the notes. The text is a view of the same numbers; it never recomputes.
   - The result keeps no reference to the input frame.
3. **Flags are read from the registry.** A `statistics:` field on a flag or source column says how statistics
   functions treat it, so `describe()`, `fit()` and `compare()` read one list (intent 5) 🟡:
   ```yaml
   spt_refusal:
     statistics: {role: at_least, values: [spt_n, spt_n60, spt_n_capped, spt_n1_60]}
   qualifier:
     statistics: {role: qualifier}            # "<" at most, ">" at least, on the row's value
   non_plastic:
     statistics: {role: non_plastic, values: [liquid_limit, plastic_limit, plasticity_index,
                                              liquidity_index, consistency_index, clay_activity]}
   particle_density_assumed:
     statistics: {role: assumed, values: [particle_density]}
   specific_gravity_source:
     statistics: {role: assumed, when: [assumed, judgment],
                  values: [specific_gravity, void_ratio, porosity, degree_of_saturation, saturated_unit_weight]}
   correlation_name:
     statistics: {role: source}
   source:
     statistics: {role: source}
   test_type:
     statistics: {role: source}
   ```
   A flag applies only when its column is in the frame and the value column is one of its `values` (all, for
   `qualifier`). A test checks every name in `values` is a registry column.
   - **`at_least` and `qualifier`** (intent 3): the row is included at its value and counted (`count_at_least`,
     `count_at_most`); the summary notes that the mean and the upper (or lower) percentiles are then
     underestimates (or overestimates). `describe()` never replaces a value: a refusal is counted at what the
     column holds, so `spt_n_capped` gives SPEC §4's "at the cap" and `spt_n` the blows reported. A refusal with a
     blank value is counted with the blanks, as a refusal.
   - **`non_plastic`:** left out, counted (`count_non_plastic`), never as a blank or 0. `NP` text in the value
     column counts the same.
   - **`assumed`:** left out unless `include_assumed=True`, counted (`count_assumed`), with one warning saying how
     many and how to include them (intent 3, M14 (a)). With `include_assumed=True` they are included, still
     counted, and the summary says "includes n assumed values".
4. **Bands are left out** (intent 4). With a value column `<target>`, a row with `<target>_lower` or
   `<target>_upper` and a blank value is not a blank: it is counted (`count_range`) and left out, with one warning.
   A row with a value and a band contributes its value. This is P01's stats box rule, now in one place.
5. **Sources** (intent 5). Within each group, every present `role: source` column not in `by` or `pool` must hold
   one value; a blank is a value (`"(blank)"`: for `correlation_name`, measured). Otherwise it's an error:
   ```
   describe() can't pool rows from different sources in group 'Alluvium':
     correlation_name: 'undrained_shear_strength_stroud_1974' (8 rows),
                       'undrained_shear_strength_terzaghi_peck_1967' (8 rows)
   Summarize each with by=['geology_unit', 'correlation_name'], filter the rows,
   or pool them on purpose with pool=['correlation_name'].
   ```
   - The listing shows every distinct value with its count, so two spellings of one `test_type` are visible.
   - **`pool=`:** a column name or list. A column that isn't a source column, or isn't in the frame, is an error.
     A pooled result records the column in `pooled`, and each group's source breakdown (value → count) is in its
     record and in the summary: "Pooled across source: lab 12, field 4".
   - The check runs after flags, bands and blanks are taken out, on the rows that would be summarized, so a
     correlation's blank estimates beside measured values don't make a mix.
   - The `value` column, or a `by` column, can't also be in `pool` (error).
6. **Order of checks.** Checks run in a fixed order, so a row is counted once, under the
   first that applies: blank group key → band → non-plastic → assumed → text → blank → `≤ 0` under `log=True`.
   The counts add up to the group's rows (a test checks it).
7. **P01's stats box calls `describe()`** (intent 6). Statistics are unchanged: P01 already summarizes the drawn
   values in display units, leaves ranges out, counts text and shows std "—" below n = 2 and CoV "—" on an
   interval scale. It now passes the rows it drew to the same private calculation `describe()` uses, by its
   legend groups, with `log=False`, and draws its existing text from the result. Changes:
   - A line whose rows mix sources reads "mixes sources (correlation_name)" in place of numbers; with
     `color_by="correlation_name"` each line is one source and only the "All" line is replaced. The figure never
     raises for a mix.
   - Assumed values are left out and counted on the "Also" line ("assumed 2"); the plot still draws them.
   - `describe()`'s warnings aren't raised from the plot: what they say is on the box, as now.
8. **P07's summary calls `describe()`** (intent 6; changed in spec review: with `percentiles=` on `describe()`,
   P07 keeps its argument instead of adopting a fixed set).
   - **`summary="percentiles"`:** `percentiles=` stays, three ascending numbers (the bar's ends and its marker),
     passed to `describe()` unchanged, so the bar is `describe()`'s numbers. 🟡 **The default changes from
     (10, 50, 90) to (25, 50, 75)**: a p10–p90 bar on fewer than 10 values is the interpolation between extreme
     values the floors exist to prevent. A user's (10, 50, 90) still works and draws from 10 values.
   - **A unit whose percentiles are below their floor**, or with n < `summary_min_count`, draws its points and no
     bar; its count label says why: "n = 6 (no summary: p10 needs 10 values)" or "n = 2 (no summary)".
   - **`summary="box"`**: the box's quartiles and median come from `describe()` (P25/P75, so from 4 values); the
     whiskers stay Tukey's (the furthest value within 1.5 IQR), computed from the values, since they aren't a
     percentile.
   - **`percentile_method=` is removed** 🟡. It is in 0.1.0, so passing it is an error saying percentiles use
     Hyndman & Fan definition 7 everywhere, not Python's bare `TypeError`. TODO #16 keeps the other summaries
     (min–max, mean ± kσ, user values).
   - **`summary_min_count`** stays: a drawing threshold, not a statistic, default 5, as now.
   - Sources, assumed values and warnings as P01 (Decision 7); a unit whose rows mix sources draws its points,
     no bar, and its count label says "(mixes sources)".
9. **`ht.analysis.summary_by()` is removed** 🟡. It was added after 0.1.0 (M13 b2), so no release has it, and
   its own docstring says `describe()` may replace it. Two summary functions on `main` is the disagreement intent
   6 removes. The judgments guide, the correlations guide, page 05, the `correlations-clay` example and the
   docstrings of `add_judgment()`, `phase_relations()` and the judgments loader switch to
   `ht.stats.describe(p.atterberg(), value="plasticity_index", by="geology_unit")`.
10. **No new dependency.** `describe()` uses NumPy only; SciPy arrives with (c) (SPEC §12.1).

### Acceptance criteria
Hand-calculated; tolerance 1e-9 relative unless stated.
1. **Statistics** (values 10, 12, 15, 20, 23 kPa): count 5, mean 16, standard deviation 5.4313902 (√29.5), CoV
   0.33946189, minimum 10, median 15, maximum 23, P25 12, P75 20; P5 and P95 NaN with the summary's reason.
2. **P5/P95 floor** (values 1 to 20): mean 10.5, standard deviation 5.9160798 (√35), P5 1.95, P25 5.75, median
   10.5, P75 15.25, P95 19.05. With 19 values, P5 and P95 are NaN.
   **Chosen percentiles:** `percentiles=(10, 90)` on the same values gives `percentile_10` 2.9 and
   `percentile_90` 18.1, and no other percentile columns; on 9 values both are NaN, on 10 they are reported.
   `percentiles=(2.5,)` makes `percentile_2_5`, NaN below 40 values. `(90, 10)`, `(0, 50)` and `(25, 25)` are
   errors.
3. **Small counts:** one value gives mean = median = the value and NaN standard deviation and CoV; counts 1 and 2
   warn once, naming the groups; a group with no numbers has a row with count 0.
4. **Interval scale:** `elevation` gives NaN CoV, with the reason; `depth` too.
5. **`log=True`** (1, 10, 100 m/s; and 0 and −1 added): `geometric_mean` 10, `geometric_standard_deviation` 10,
   median 10; `count_not_positive` 2 with one warning; no `mean` or `coefficient_of_variation` column.
6. **Refusals** (`spt_n_capped` 12, 18, 25, 100 with `spt_refusal` on the last): count 4, `count_at_least` 1,
   mean 38.75, median 21.5, and the note. The same rows with `value="spt_n"` and a blank N on the refusal: count
   3, the refusal counted with the blanks.
7. **Qualifiers:** `<0.1` and `>500` rows are included at their value and counted as `count_at_most` and
   `count_at_least`.
8. **NP:** a `p.atterberg()` frame with NP rows gives `count_non_plastic` equal to their number, and the same
   statistics as the frame without them; `NP` text in a CSV value column counts the same.
9. **Assumed:** `p.particle_density()` from `site_si.ags` with one `#2.65` row: left out with one warning by
   default; included with `include_assumed=True` and noted. Gs from `phase_relations()` with
   `specific_gravity_source` `judgment` is treated the same.
10. **Bands:** a Stroud frame with band-only rows gives `count_range` equal to them and the statistics of the
    rows with values.
11. **Sources:** two correlations' s_u in one unit raise the error of Decision 5, with both names and counts;
    `by=["geology_unit", "correlation_name"]` gives two rows; `pool=["correlation_name"]` gives one, with
    `pooled` and the breakdown. Measured and estimated rows mix the same way (blank `correlation_name`).
    `p.permeability()` with lab and field rows raises naming `source`; two spellings of a `test_type` are both
    listed. `pool=["geology_unit"]` is an error (not a source column).
12. **Counts add up:** for every group in the tests above, the counts sum to the group's rows.
13. **Units:** a CSV frame in psf gives the statistics in psf; `display_units="SI"` gives them in kPa (AC 1's
    values × 0.04788026); a frame with no unit for a stress column raises naming it; a plain list without
    `units=` reports "(units not given)".
14. **Result:** `.to_frame()` columns and `attrs["units"]` as Decision 2; `.to_dict()` passes `json.dumps`;
    `str(result)` contains every number in the frame to 3 significant figures; `kind` is `"property"`; a
    σ′v-derived frame's judgments appear in `judgments`.
15. **Inputs:** a Series and an array give AC 1's numbers; `by=` or `pool=` with an array is an error; a missing
    value column lists the available ones; a bool column is an error.
16. **P01:** its existing stats box tests pass unchanged; a frame colored by `correlation_name` shows each
    correlation's line and replaces "All" with "mixes sources (correlation_name)"; an assumed row is drawn and
    counted on the "Also" line.
17. **P07:** by default the bar spans P25–P75 with the median (positions match `describe()` on the same values);
    `percentiles=(10, 50, 90)` draws p10–p90 on 20 values (AC 2's 2.9 and 18.1) and, on 6 values, points only
    with "(no summary: p10 needs 10 values)"; the box's quartiles equal `describe()`'s; `percentile_method=`
    raises with the message of Decision 8; a unit mixing sources draws points with "(mixes sources)". Updated
    `docs/plots/img/P07.png`, looked at.
18. **`summary_by` is gone:** no name in `src/` or `docs/site/` refers to it, and the site builds with
    `--strict`.
19. **Registry:** every `statistics.values` entry is a registry column; the reference page lists `describe` and
    `DescribeResult`.
