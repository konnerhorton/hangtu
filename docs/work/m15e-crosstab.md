# M15 (e): `crosstab()`, comparing two classifications of the same rows

## Intent
M15 is the statistics milestone (SPEC §1.3, §5, §12.4). Units (a)–(d) are built; `crosstab()` was split off
from (d) because it is categorical, runs no test and needs its own rule for what counts as a mismatch
(`docs/work/m15d-compare.md`, decision 1). This unit closes M15.

**Goal:** an engineer passes a dataset and two classification columns (the logged legend code against the lab
USCS symbol, or two GEOL keys) and gets a table of how many rows fall in each pair, with blanks counted in it,
and, when the two columns share a vocabulary or a mapping says which pairs agree, the share that agree and a
listing of the rows that don't, each with its hole, depth and sample, so it can be checked.

**Why:**
- **The log and the lab disagree, and nothing shows where.** In the example project the Alluvium is logged `CL`
  (`legend_code`, from `GEOL_LEG`) on every specimen, while the lab classifies three of the six as `CH` and one
  as `ML` (`ht.analysis.uscs()`). A unit weight or a correlation keyed by the logged class (SPEC §4, the
  `soil=` and `uscs=` arguments) inherits that disagreement. The engineer needs the count, and the rows.
- **Choosing the geology key is a comparison.** SPEC §8.3 makes the key a setting with no fallback and says
  several fields "can be carried side by side (`geology_fields=`) and compared using `crosstab`";
  `docs/data/datasets.md` §5.3 keeps the codes unmapped for exactly this. Today the user writes
  `pd.crosstab` by hand and loses the blanks.
- **`pd.crosstab` drops blanks silently** (CLAUDE.md: never drop data silently), ignores a categorical's
  order unless asked, and has no mismatch listing.
- **SPEC §12.4's M15 row** lists `crosstab` as unit (e).

**Scope:**
- `ht.stats.crosstab(df, rows, columns, *, agree=None)` (decision 3): one row of the table per value of
  `rows`, one column per value of `columns`, with totals.
  - **Blanks are a category**, shown as "(blank)" and counted, never dropped (decision 2).
  - **Order:** an ordered categorical (`geology_unit`) keeps its order; other values sort as text.
  - **Agreement only when asked** (decisions 1 and 4): `agree="same"` counts a pair as agreeing when the two
    values are the same text; `agree={row value: [column values], ...}` says which pairs agree (logged `SC` against
    lab `SC-SM`, or a GEOL code against a formation). With either, the result reports the agreement (agreeing
    rows over rows with both values) and lists every disagreeing row with its identifying columns
    (`loca_id`, `depth`, `sample_reference`, `specimen_reference` where present).
- `CrosstabResult` on the shared result base: `.to_frame()` the counts, `.mismatches` the listing as a
  DataFrame, `.to_dict()`, and a readable summary.
- A reference entry, a section in the statistics guide and a docs-site example on the example project
  (`legend_code` against `uscs_symbol`; `geology_unit` against `geology_code`).

**Out of scope:**
- **Tests and agreement statistics** (chi-square, Cramér's V, Cohen's kappa). A contingency test asks whether
  two classifications are related, which for a log and a lab classification of the same soil isn't in doubt;
  kappa corrects agreement for chance, which assumes the two raters classify independently, and a logger who
  has seen the lab results doesn't. The plain share that agree, with the rows, is what a reviewer checks.
  A TODO item records kappa in case a use appears.
- **Choosing or fixing the classification.** `crosstab()` reports; it never changes `geology_unit` or picks a
  key. Overriding a class stays with the judgments file and `add_judgment()` (SPEC §4).
- **A third grouping column** (one table per geology unit). Filtering the rows first does that.
- **Partial agreement inside USCS** (does logged `CL` agree with lab `CL-ML`?). There's no rule hangtu could
  apply without a judgment, so it goes in `agree=` as a mapping the user writes.
- **A figure** (a shaded table). No plot ID is proposed for it; it waits for a use.
- **Comparing numbers.** `crosstab()` takes text columns; a numeric column is an error that points to
  `ht.stats.compare()`.

**SPEC and TODO touched:**
- SPEC §5 (`crosstab` built; blanks are a category in a categorical summary), §8.3 (point the "compared using
  `crosstab`" line at the function), §12.4 (M15 row: (e) done, M15 closed).
- Other docs: `docs/drafts/phase3-stats.md` (the `crosstab` row decided, pointing here), CLAUDE.md status.
- TODO: a new item for kappa or another chance-corrected agreement.

### Decisions (intent review, 2026-10-30)
1. **A mismatch is defined by the user, not inferred.** Two columns can be compared only where they share a
   vocabulary or a mapping links them ("is `CL` a mismatch for Alluvium?" has no answer), so without `agree=`
   the result is the table alone. `crosstab()` doesn't turn `agree="same"` on when both columns look like one
   vocabulary: the registry doesn't record vocabularies, so that would be a guess.
2. **Blanks are a category.** A blank class is information (the log has a gap, the lab didn't classify the
   specimen), and dropping it, as `pd.crosstab` does, hides it.
3. **The arguments are `rows=`, `columns=` and `agree=`.** pandas' `index` reads as a developer's word to an
   engineer.
4. **A row blank in one column only is in the table but not in the agreement.** It is left out of the
   agreement's denominator and counted in the note ("4 rows have a lab class but no logged class"); listing it
   with the mismatches would mix "disagrees" with "wasn't classified".
5. **No `pool=` or `include_assumed=`.** Those input rules (SPEC §5) concern measured values; a class column
   carries no source or flag in the registry. If a class is ever derived from a correlation, this is revisited.
