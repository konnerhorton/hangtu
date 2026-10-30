# M15 (b): correlation statistics with the results

## Intent
M15 is the statistics milestone (SPEC §1.3, §5, §12.4), split into four units (`docs/work/m15a-describe.md`,
decision 1). This unit, (b), makes a correlation's estimates carry the statistics of the source data they came
from, and the source's advice on using them, so they aren't lost once the values leave the function (TODO #40).

**Goal:** an engineer runs a correlation and each estimate row says how good the correlation is: the standard
deviation of its source data in the target's units where the source gives one, the source's n and r², and the
source's advice in the authors' words. A reviewer reading a CSV of the estimates, or a merged frame, sees them
without opening the docstring.

**Why:**
- **The statistics live only in text today.** Each entry's `scatter` in `config/correlations.yaml` is a free-text
  string ("n = 126, r² = 0.699, S.D. = 4.37 pa"). It reaches `ht.analysis.correlations.describe(name)`,
  `df.attrs["correlations"]` and the docstrings, but not the rows. `attrs` are lost on a merge or a file round
  trip, so the estimate is then a bare number.
- **A correlation's scatter is often larger than the spread of the data it is applied to.** Mayne & Kemper's
  σ′p has S.D. = 4.37 pa (about 440 kPa); Kulhawy et al.'s K0 has S.D. = 0.43, and on the TC304 clay database
  measured K0 averaged about twice the estimate (Ching & Schweckendiek 2021, b = 2.16, COV 0.70). An estimate
  shown without that reads as more certain than it is.
- **Selection (M18) needs it as data.** Comparing a parameter's sources, and later a characteristic value that
  accounts for transformation uncertainty, read the correlation's uncertainty from the rows, not from prose.
- **The advice is part of the result.** Several sources say how not to use them ("use the estimate to check
  oedometer σ′p, not in its place"). Today that is in the docstrings only.

**What the eleven correlations publish** (from `config/correlations.yaml`):

| Correlation | n | r² | Standard deviation | Later evaluation |
|---|---|---|---|---|
| σ′p, Mayne & Kemper (1988) | 126 | 0.699 | 4.37 pa | — |
| OCR, Mayne & Kemper (1988) | 112 | 0.661 | 3.82 | — |
| K0, Kulhawy et al. (1989) | 57 | 0.771 | 0.43 | b = 2.16, COV 0.70, n = 74 (Ching & Schweckendiek 2021) |
| Vs, Imai & Tonouchi (1982) | 1654 | 0.75 | — | — |
| Vs, Ohta & Goto (1978) | 289 | 0.52 | — | — |
| φ′, Hatanaka & Uchida (1996) | — | — | "±3° for most of the data" (not a standard deviation) | — |
| φ′ Kulhawy & Mayne; s_u Terzaghi & Peck, Stroud; E AASHTO, Kulhawy & Mayne | — | — | not stated; words only | — |

So three correlations have a standard deviation, five have n, and six have only words. The design has to make
"not stated" visible rather than blank.

**Scope:**
- `scatter` becomes structured in the config: n, r², a standard deviation with the scale it was given on (the
  target's units, or normalized, e.g. σ′p/pa), the source's own words kept verbatim, and later evaluations (bias
  b, COV, n, database, source) as a list;
- the per-row columns the estimates carry (decision 2), written by the shared `estimate()` in `_framework.py`, so
  every correlation, including future ones, gets them;
- the advice on use, at most a sentence per correlation in the authors' words (TODO #30's rule);
- registry entries for the new columns, `correlations.describe()`'s docstring, the correlations guide on the docs
  site, and the parameter pages that show a correlation's scatter (04–08, 10).

**Out of scope:**
- **Applying a bias or a transformation uncertainty to the estimate.** Correcting K0 by b = 2.16, or combining
  transformation and inherent variability into one COV, is selection (M18).
- **Drawing the standard deviation on P01** (e.g. ±1 S.D. whiskers): a TODO item for P01, not this
  unit, so (b) stays a data change.
- **`ht.stats.describe()` using the new columns.** It summarizes the estimates as now; the source rule
  (`correlation_name`) already stops two correlations being pooled unawares.
- New correlations, or re-verifying the existing ones beyond the statistics this unit reads (below).

**SPEC and TODO touched:**
- SPEC §4 (what a correlation's result carries), §5 (the result columns, if the `statistics:` registry field
  gains a kind for them), §12.4 (M15 row).
- Other docs: `docs/work/m15a-describe.md` decision 7 is superseded by decision 1 here; parameter pages 04–08 and
  10; the correlations guide.
- TODO: #40 (resolved here and deleted); a new item for P01 drawing the standard deviation.

### Decisions (intent review, 2026-10-30)
1. **Reconcile TODO #40 with M15 (a) decision 7 in favor of TODO #40, the later decision:** the source's own
   statistics go on the rows, not only in a table joined on `correlation_name`. Rows survive `pd.concat`, merges
   and CSV; a side table has to be joined back and can be forgotten. The cost is a few constant columns per
   correlation, which is small next to what is lost without them.
2. **The row columns:**
   - the standard deviation in the target's units, named after the target like the bands
     (`<target>_<suffix>`, beside `<target>_lower` / `_upper`), so two targets in one frame never share a
     column with mixed units, and `display_units=` converts it with the target. Blank where the source gives
     none, with the reason in the words column, never 0;
   - n and r², target-independent, named `correlation_<...>`;
   - the source's scatter in its words, and its advice on use, each a short text column.

   Names are proposed in the spec against the whole registry (no bare `n`, `r2` or `sd`).
3. **Later evaluations stay off the rows.** A bias and COV from another database (Ching & Schweckendiek's
   K0) describe the correlation's performance elsewhere, not the scatter of its own data, and using them is a
   selection step (M18). They are structured in the config and reach `correlations.describe(name)` and
   `df.attrs`, and the advice column can point to them.
4. **A spread that isn't a standard deviation stays words.** Hatanaka & Uchida's "±3° for most of the data"
   isn't converted into a standard deviation or a band; it goes in the words column only.

### Open (for the spec step)
- 🔬 **What each standard deviation is.** For σ′p, OCR and K0, check against the sources (Mayne & Kemper 1988;
  Kulhawy et al. 1989, or EPRI EL-6800 Figs. 3-18, 3-30) that the S.D. is the standard error of the regression
  in arithmetic space, constant over the range, so it converts to the target's units as a single number (σ′p:
  4.37 × pa = 437 kPa). If a regression was in log space, its S.D. is a ratio, not a value in kPa, and the
  column design has to allow for that.
- The words for "not stated": the source's own sentence where there is one (GEC 5's "a poor predictor of
  undrained shear strength"), or a fixed "Not stated by the source".
- Whether the advice column repeats on every row or only the scatter numbers do, if a long sentence on every row
  of a large frame turns out to be a burden in the CSV.

## Spec
Numbered items refer to this section's decisions; "intent n" to the intent's. Reviewed and accepted 2026-10-30;
🔬 marks a fact to verify against the source before it is built.

### Changes
- **`config/correlations.yaml`:** `scatter` becomes a mapping, and each entry gains `advice` and `evaluations`
  (Decision 1); the header comment describes them. Text that moves: the "Not stated. GEC 5 …" quotes leave
  `scatter` for `advice`; K0's TC304 sentence leaves `notes` for `evaluations`.
- **`_framework.estimate()`:** writes the new columns on every correlation's result (Decisions 2–3), and
  `OUTPUT_COLUMNS` gains them, so re-running a correlation on its own output warns that it replaced them.
- **Registry (`columns.yaml`):** the new columns, in the Correlations section (Decision 2).
- **`ht.analysis.correlations.describe()`:** its docstring lists the new fields. No signature change.
- **SPEC §4:** the correlations list gains a sub-bullet on the statistics and advice the rows carry
  (Decision 7, in this commit). §12.4's M15 row marks (b) done at the close.
- **Docs site:** a "Scatter and advice" section in `docs/site/guides/correlations.md`, with the example's output
  showing the columns. Parameter pages 04–08 and 10 keep their Variability sections as they are.
- **TODO:** #40 resolved and removed; a new item for P01 drawing a correlation's standard deviation (intent,
  out of scope).
- `docs/work/m15a-describe.md` decision 7 is history and isn't edited; intent decision 1 here supersedes it.

### Decisions
1. **The config entry.** Per correlation:
   ```yaml
   scatter:
     words: "n = 126, r² = 0.699, S.D. = 4.37 pa"   # the source's statement; "Not stated." when none
     data_count: 126                                 # the source's n; null when not stated
     r_squared: 0.699                                # null when not stated
     standard_deviation: {value: 4.37, unit: pa, scale: null}   # null when not stated
   advice: {words: "...", by: "Loehr et al. (2016), p. 7-38"}    # null when none
   evaluations:                                      # [] when none
     - {bias: 2.16, coefficient_of_variation: 0.70, data_count: 74,
        database: "TC304 clay database, CLAY/12/3997",
        cite: "Ching & Schweckendiek (2021)", locator: "Table 5.2, p. 178"}
   ```
   - **`words`** is the source's statement of its scatter and nothing else. "Not stated." when the source
     gives none (the open item on the words for "not stated"): the source's comments on use go in `advice`, so a
     quote isn't in two places.
   - **`standard_deviation.unit`:** a unit the units module reads, `pa` (the entry's own pa = 100 kPa, as in its
     equation), or null for a dimensionless target.
   - **`standard_deviation.scale`:** `arithmetic` (the standard error of the regression in the target's terms,
     the same over the range), `log10` or `ln` (a factor), or null while not verified. 🔬 All three are null at
     this spec: σ′p (4.37 pa), OCR (3.82) and K0 (0.43). That σ′p's is given in pa suggests arithmetic; K0's
     0.43 would be plausible on either scale. Each is checked against Mayne & Kemper (1988) and Kulhawy et al.
     (1989), or Kulhawy & Mayne (1990), Figs. 3-18 and 3-30, before its scale is set.
   - **Hatanaka & Uchida's "±3° for most of the data"** is `words` only; n, r² and the standard deviation are
     null (intent decision 4).
   - **`advice.by`** is a citation with its locator for the source's words, or `hangtu` for hangtu's own.
     `evaluations` holds other databases' checks of the correlation (intent decision 3).
2. **The row columns.** Names checked against the whole registry and `ht.stats`'s statistic names; none collide.

   | Column | Type | On which rows | Value |
   |---|---|---|---|
   | `<target>_correlation_standard_deviation` | number, in the target's units | rows with an estimate; NaN where `correlation_note` is set | `scatter.standard_deviation`, converted (Decision 3) |
   | `correlation_data_count` | number | every row | `scatter.data_count`, NaN when not stated |
   | `correlation_r_squared` | number | every row | `scatter.r_squared`, NaN when not stated |
   | `correlation_scatter` | text | every row | `scatter.words` |
   | `correlation_advice` | text | every row | `"<words>" (<by>)`, or `hangtu: <words>`; blank when none |

   - **`<target>_correlation_standard_deviation`, not `<target>_standard_deviation`:** beside a summary,
     "the standard deviation of σ′p" reads as the spread of the measured values; "correlation" says it is the
     correlation's scatter. It follows the bands in being named after the target, so two targets in one frame
     never share a column of mixed units, and the value's units carry over.
   - **`correlation_r_squared`:** r² is unambiguous notation and collides with no geotechnical quantity;
     `correlation_coefficient_of_determination` is the alternative. If accepted, `r_squared` joins CLAUDE.md's
     accepted short forms. `correlation_data_count`, not `_sample_size`, since "sample" is a soil sample here.
   - **Every row, not only estimated ones,** for the columns about the correlation, as `correlation_name` is:
     they describe the correlation the row names. The standard deviation belongs to an estimate, so it is blank
     where there is none, as the bands are.
   - **Written by every correlation**, from the shared `estimate()`, so future correlations get them without code.
3. **The standard deviation on the rows.**
   - **Only an arithmetic one.** A `scale: arithmetic` value is converted to the target's entry unit (pa → × 100
     kPa) and then to the display units with the target (`display_units=`), and recorded in `attrs["units"]`.
     A log-scale one is a factor, not a value in kPa; it stays in the config and `correlation_scatter`, and a
     column for it is designed when a verified source needs one. A null scale is never guessed (SPEC §2.6).
   - **The column exists for a target, not a correlation.** Every correlation whose target has a
     `<target>_correlation_standard_deviation` in the registry writes it, NaN where its source gives none or
     its scale isn't arithmetic. Results for one target then have the same columns and equal `attrs`, so
     `pd.concat` keeps the attrs and units (`docs/work/m13b1-spt-framework.md`, Decision 5).
   - **Registry entries are added for verified targets only** (`preconsolidation_stress`,
     `overconsolidation_ratio`, `at_rest_earth_pressure_coefficient`, each once its 🔬 is settled). If none is
     verified at build time, the code path is built and tested on a test entry, and no target writes the column
     yet; the close-out says so.
4. **Advice per correlation** (at most a sentence each, in the source's words where it has them; TODO #30):

   | Correlation | `advice.words` | `advice.by` |
   |---|---|---|
   | φ′, Hatanaka & Uchida (1996) | none | — |
   | φ′, Kulhawy & Mayne (1990) | "somewhat conservative, especially for depths less than 6 ft" | Loehr et al. (2016), pp. 7-54 to 7-55 |
   | s_u, Terzaghi & Peck (1967) | "SPT N-values are generally a poor predictor of undrained shear strength" | Loehr et al. (2016), p. 7-38 |
   | s_u, Stroud (1974) | "somewhat lower bound values" | Loehr et al. (2016), p. 7-38 |
   | σ′p, Mayne & Kemper (1988) | SPT N is a poor predictor in clay: use the estimate to check oedometer σ′p, not in its place. | hangtu |
   | OCR, Mayne & Kemper (1988) | SPT N is a poor predictor in clay: use the estimate to check oedometer OCR, not in its place. | hangtu |
   | K0, Kulhawy et al. (1989) | Measured K0 averaged about twice the estimate on another clay database (see `evaluations`): use it to check measured K0, not in its place. | hangtu |
   | E, AASHTO (2004) | "only approximate estimates" | Loehr et al. (2016), p. 8-25 |
   | E, Kulhawy & Mayne (1990) | "as a first order estimator" | Kulhawy & Mayne (1990), p. 5-17 |
   | Vs, Imai & Tonouchi (1982); Ohta & Goto (1978) | none | — |

   Each quote is already in the function's docstring, verified with M13. hangtu's own words say so (`hangtu:`),
   so a reviewer never takes them for the source's.
5. **Later evaluations stay off the rows** (intent decision 3). They are in the entry, so in
   `correlations.describe(name)` and `df.attrs["correlations"]`. The first is Ching & Schweckendiek's for K0.
   Mayne & Kulhawy (1982)'s (page 07) isn't a correlation hangtu builds, so it isn't added.
6. **Docstrings stay the reference.** Each function's **Scatter:** paragraph keeps the source's statistics and
   comments as now. The test that checks the docstrings against the config extends to `scatter` (each number
   stated appears in `words` and in the docstring) and `advice` (each quote appears in the docstring).
7. **SPEC §4** gains a sub-bullet in the correlations list stating Decisions 2, 4 and 5, in this commit.

### Acceptance criteria
1. Every config entry has `scatter` with `words`, `data_count`, `r_squared` and `standard_deviation`; `advice`;
   and `evaluations`. Each non-null number appears in `scatter.words`; each `advice.words` quote appears in the
   function's docstring. A missing key fails a test naming the entry.
2. Every correlation's result has `correlation_data_count`, `correlation_r_squared`, `correlation_scatter` and
   `correlation_advice` on every row, including rows with no estimate, with the entry's values: Mayne & Kemper's
   σ′p rows give 126, 0.699 and "n = 126, r² = 0.699, S.D. = 4.37 pa"; Terzaghi & Peck's give NaN, NaN,
   "Not stated." and its advice with `(Loehr et al. (2016), p. 7-38)`; Hatanaka & Uchida's advice is blank.
3. With a test entry whose standard deviation is `{value: 4.37, unit: pa, scale: arithmetic}` for
   `preconsolidation_stress`: rows with an estimate carry
   `preconsolidation_stress_correlation_standard_deviation` = 437 kPa (4.37 × 100 kPa) in SI and 9126.9 psf
   (437 / 0.04788026) in US, to 0.1 psf; rows with a `correlation_note` carry NaN; `attrs["units"]` gives the
   column's unit.
4. With `scale` null, `log10` or `ln`, the column is NaN on every row and the value appears only in
   `correlation_scatter`.
5. Two results for one target, one with a standard deviation and one without, concatenate with `pd.concat` and
   keep `attrs["units"]` and `attrs["correlations"]`.
6. A target with no registry standard-deviation column gets no such column.
7. Running a correlation on its own result warns that it replaced the new columns, as for `correlation_name`.
8. `ht.analysis.correlations.describe(name)` returns `scatter`, `advice` and `evaluations`; K0's `evaluations`
   gives b = 2.16, COV 0.70, n = 74, and its `notes` no longer repeats them.
9. 🔬 For each of σ′p, OCR and K0 whose scale is verified as arithmetic: its registry column exists and its rows
   carry the standard deviation (σ′p 437 kPa; OCR 3.82; K0 0.43). The close-out lists any left unverified.
10. The registry has an entry for each new column; the correlations guide shows them; ruff and the whole suite
    pass, and the docs site builds with `--strict`.
