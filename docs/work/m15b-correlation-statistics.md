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
