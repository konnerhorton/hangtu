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

## Spec
Numbered items refer to this section's decisions; "intent n" to the intent's. The choices proposed here were
agreed in review on 2026-10-30.

### Changes
- **SPEC §5:** `crosstab` built. The first two bullets ("an array, a Series, or a DataFrame plus `value=`/`by=`";
  `log=True`) and the input rules are scoped to the functions that summarize values; `crosstab()` takes a
  DataFrame and two text columns, and of the input rules follows only "counts add up", with blanks as a category
  (Decision 3). The result list gains `CrosstabResult`.
- **SPEC §8.3:** "compared using `crosstab`" becomes "compared with `ht.stats.crosstab()`".
- **SPEC §12.4:** M15 row, (e) done; M15 closed.
- **`docs/drafts/phase3-stats.md`:** the `crosstab` row decided, pointing here.
- **TODO:** new #52, chance-corrected agreement (Cohen's kappa) if a use appears
  where the two classifications are made independently (intent, out of scope).
- **Docs site:** `crosstab` and `CrosstabResult` in `docs/site/reference/stats.md`; a "Comparing
  classifications" section in `docs/site/guides/statistics.md`, with `docs/site/examples/statistics-crosstab.py`
  on the example project.
- **CLAUDE.md:** the status paragraph.

### Decisions
1. **`ht.stats.crosstab()`.**
   ```python
   crosstab(df, rows, columns, *, agree=None) -> CrosstabResult
   ```
   - `df` is a DataFrame; `rows` and `columns` name two of its columns (intent 3). A list, array or Series is an
     error that says to pass the frame and two column names.
   - A missing column is a `ColumnError` listing the frame's columns, as `describe()`. `rows == columns` is an
     error.
2. **Text only, judged by the registry.** A column the registry gives a `quantity` (a measurement) is an
   error naming it and pointing to `ht.stats.compare()` for values, or to binning it first (`pd.cut`) for a
   table. Every other column, a registry `type: text` column or one the registry doesn't know, is read as text
   whatever its dtype, so geology codes a CSV read as numbers (`101`) still work; a whole number is written without
   a decimal (`101`, not `101.0`), and other numbers as
   Python writes them.
3. **Values as written; blanks a category.** A value is its text exactly, case and inner spaces included (SPEC
   §8.3's exact, case-sensitive match), so `CL` and `cl` are two columns the reader sees, never merged
   silently. Leading and trailing spaces are kept too, for the same reason. NaN, None and empty or
   whitespace-only text are blank, shown as `"(blank)"`, the label `describe()` gives a blank group (intent 2).
4. **Order.** Each side lists only the values present (an unused category of an ordered categorical isn't a
   row of zeros). An ordered or unordered categorical keeps its category order, as `describe()`; other values
   sort as text. `"(blank)"` comes last on each side, then the totals.
5. **The table.** `.to_frame()` returns the counts: index named `rows`' column, columns named `columns`' column,
   integers, with a last row and column `"(total)"` (in parentheses, like `"(blank)"`, so it can't be
   mistaken for a class named "Total"). Every row of `df` is counted once, so the grand total is `len(df)`.
6. **Agreement, only with `agree=`** (intent 1, 4).
   - `agree="same"`: a row agrees when its two values are the same text.
   - `agree={row value: column value or list of column values, ...}`: a row agrees when its column value is in
     its row value's list. A row value with rows to compare that the mapping doesn't name is an error listing
     each such value and its count, and saying that `[]` means "agrees with nothing": a missing key is far more
     often an oversight than a deliberate "never agrees". Keys or listed values not in the data are fine, so one
     mapping serves several projects. Keys and values are compared as text (Decision 2), so `{101: "ALV"}`
     and `{"101": "ALV"}` are the same.
   - Any other `agree=` is an error showing both forms.
   - **Counts:** `count_compared` (both values present), `count_agreeing`, `count_disagreeing`,
     `count_blank_in_rows` (blank in `rows` only), `count_blank_in_columns` (blank in `columns` only) and
     `count_blank_in_both`; the last three and `count_compared` add up to `len(df)`. `proportion_agreeing` is
     `count_agreeing / count_compared`, NaN when nothing is compared. A row blank on either side is never a
     mismatch (intent 4).
   - Without `agree=`, every agreement field is None and there are no mismatches.
7. **The mismatches.** `.mismatches` is a DataFrame of the disagreeing rows in `df`'s order, indexed by `df`'s
   own index labels, so `df.loc[result.mismatches.index]` gives the full rows. Its columns are those of
   `loca_id`, `depth`, `sample_reference`, `specimen_id` and every `<test>_specimen_id` present in `df`, in
   `df`'s order, then `rows`' and `columns`' columns, then `source_line` if present (this list: the registry's
   identifiers that say where a row is and which test it came from). With no `agree=`, or nothing disagreeing,
   it is empty with those columns.
8. **`CrosstabResult`,** a frozen dataclass on the shared base: `kind="property"`, `function="crosstab"`,
   `value=None`, `unit=None`, the notes, judgments and version as every result; and `rows`, `columns`,
   `agree` (`"same"`, the mapping with each value as a list of text, or None), `row_values`, `column_values`
   (without blank or totals), `counts` (row class → column class → rows, `"(blank)"` last on each side where present;
   *changed in the build:* a nested mapping rather than one tuple per row, so `.to_dict()` labels every cell),
   the counts and proportion of Decision 6, and the mismatch records (`mismatch_columns`, `mismatch_index`,
   `mismatch_values`). `.mismatches` is built from
   those records, so `.to_dict()` holds everything and is JSON-serializable (an index label that isn't a str or
   int is written as text).
9. **The summary** (`print(result)`): a title (`legend_code × uscs_symbol`), the table with totals, then the
   notes:
   - with `agree=`: "Agree (same text): 2 of 8 rows with both values (25 %)." or "Agree (by the mapping): …";
   - one line per nonzero blank count: "12 rows have a legend_code but no uscs_symbol.";
   - with mismatches, the listing, the first 20 rows, then "… and 14 more: result.mismatches lists them all.";
   - without `agree=`: "No agreement counted: pass agree=\"same\" if the two columns use one vocabulary, or a
     mapping of which pairs agree."
   `_repr_html_` shows the same text, as the other results.
10. **No warning.** Blanks are counted in the table and the notes, so nothing is dropped and nothing warns.

### Sources
None: the function counts, with no equation or coefficient. The golden values are hand counts from the rows
listed below.

### Acceptance criteria
The example project (`site.ags`, `strata.csv`) as
`ht.analysis.uscs(p.index_properties(geology_fields=["GEOL_GEOL", "GEOL_LEG"]))`, 20 rows. Its `legend_code`
and `uscs_symbol`, read from the dataset row by row (loca_id, depth in ft):

| Rows | legend_code | uscs_symbol |
|---|---|---|
| B-1 1.5, B-3 1.5 | FILL | SC |
| B-1 13, B-2 13, B-4 13 | CL | CH |
| B-3 13, B-5 13 | CL | CL |
| B-6 13 | CL | ML |
| B-1, B-2, B-3, B-4, B-5, B-6 at 18 | CL | blank (no grain size) |
| the six Terrace rows (B-1 25.75 … B-6 30.75) | SP | blank (no plasticity class) |

1. **The table (example project):** `crosstab(d, "legend_code", "uscs_symbol")` gives

   | legend_code | CH | CL | ML | SC | (blank) | (total) |
   |---|---|---|---|---|---|---|
   | CL | 3 | 2 | 1 | 0 | 6 | 12 |
   | FILL | 0 | 0 | 0 | 2 | 0 | 2 |
   | SP | 0 | 0 | 0 | 0 | 6 | 6 |
   | (total) | 3 | 2 | 1 | 2 | 12 | 20 |

   with no `"(blank)"` row (no `legend_code` is blank), every agreement field None, an empty `.mismatches`, and
   the "No agreement counted" note.
2. **`agree="same"` (example project):** `count_compared` 8, `count_agreeing` 2, `count_disagreeing` 6,
   `count_blank_in_columns` 12, `count_blank_in_rows` 0, `count_blank_in_both` 0, `proportion_agreeing` 0.25.
   `.mismatches` has six rows in the dataset's order: B-1 1.5 (FILL, SC), B-1 13 (CL, CH), B-2 13 (CL, CH),
   B-3 1.5 (FILL, SC), B-4 13 (CL, CH), B-6 13 (CL, ML); its columns are `loca_id`, `sample_reference`, `depth`,
   `water_content_specimen_id`, `atterberg_specimen_id`, `grain_size_specimen_id`, `legend_code`,
   `uscs_symbol`, `source_line` (the dataset's own order), and `d.loc[result.mismatches.index]` returns those
   six rows. The summary says "2 of 8 rows with both values (25 %)" and "12 rows have a legend_code but no
   uscs_symbol."
3. **A mapping (example project):** `agree={"CL": "CL", "FILL": ["SC", "SM", "GC"], "SP": ["SP", "SP-SM"]}`
   gives `count_agreeing` 4 of 8 (0.5) and the four CH and ML rows as mismatches. Leaving `"FILL"` out is an
   error naming `'FILL' (2 rows)` and `[]`; `{"CL": "CL", "FILL": [], "SP": []}` gives 2 of 8.
4. **Categorical order (example project):** `crosstab(d, "geology_unit", "legend_code")` lists the rows Fill,
   Alluvium, Terrace (the map's order, not alphabetical) with Fill–FILL 2, Alluvium–CL 12, Terrace–SP 6, and
   the columns CL, FILL, SP.
5. **Categorical order, blanks and case (synthetic, 6 rows):** `rows` an ordered categorical
   `["B", "a", None, "B", "a", "C"]` with categories `["C", "B", "a", "Z"]`, `columns`
   `["x", "X", "x", None, "X", "y"]`. Rows C, B, a, (blank), with no Z row; columns X, x, y, (blank) (text sort,
   uppercase first; `X` and `x` stay apart). Counts C–y 1; B–x 1, B–(blank) 1; a–X 2; (blank)–x 1. Row totals
   1, 2, 2, 1; column totals 2, 2, 1, 1; grand total 6.
6. **Whitespace and spaces kept (synthetic):** an object column `["CL", "CL ", "  ", "cl"]` against
   `["CL", "CL", "CL", "CL"]` with `agree="same"`: rows `CL`, `CL `, `cl`, `(blank)`; `count_compared` 3,
   `count_agreeing` 1, `count_blank_in_rows` 1.
7. **Integer codes (synthetic):** a column `[101, 101, 102]` (int) and one `[101.0, NaN, 102.0]` (float, not in
   the registry) give rows `101`, `102` and columns `101`, `102`, `(blank)`; `agree="same"` gives 2 of 2, and
   `agree={101: "101", "102": [102]}` the same.
8. **Errors:** a missing column (`ColumnError`, listing columns); `rows == columns`; a registry measurement
   (`plasticity_index`) naming `compare()` and `pd.cut`; a Series or array as `df`; `agree=` of another type
   (`True`, `"equal"`) showing both forms; a mapping missing a row value (AC 3). Each message says what is wrong,
   where and what to do (CLAUDE.md).
9. **Counts add up:** in AC 1–7, the table's grand total is `len(df)`, and with `agree=`, `count_compared` and
   the three blank counts add up to `len(df)`, and `count_agreeing + count_disagreeing == count_compared`.
10. **Result:** `CrosstabResult` is frozen; `.to_dict()` goes through `json.dumps` for AC 1–7; `.mismatches`
    rebuilt from the dict's records equals the property. A comparison where every row is blank on one side, with
    `agree="same"`, gives `count_compared` 0 and `proportion_agreeing` NaN, written `null` by `.to_dict()`. An
    empty frame gives a table of only `"(total)"`, 0.
11. **Docs:** `crosstab` and `CrosstabResult` have reference entries (the existing test fails without them); the
    example runs in `docs/prepare_site.py` without a warning and prints its summary (the Atterberg limits, not
    AC 2's rows: Plan, step 3).

## Plan
Two build commits, then the docs pages (a docs commit, with approval) and the close-out: four commits in all,
each with ruff and the whole suite green. Reused, not rebuilt:
- `stats/_rows.BLANK_GROUP` (`"(blank)"`), and `_rows._frame_input`'s `ColumnError` wording for a missing
  column (the same sentence, written for two columns);
- `registry.column_info()` for Decision 2's `quantity` check;
- `stats/_result._Result` and `_plain()`; `DescribeResult.__str__`'s column-aligned text table, as a helper
  shared with `CrosstabResult` only if it lifts out without changing `describe()`'s output (else a short copy,
  noted in the commit).

New module `stats/_crosstab.py` (the function and its reading). `CrosstabResult` goes in `stats/_result.py`.
New tests in `tests/stats/`; an `example_index` fixture in `tests/stats/conftest.py` builds the example project
in `tmp_path` and returns `ht.analysis.uscs(p.index_properties(geology_fields=["GEOL_GEOL", "GEOL_LEG"]))`
with its warnings asserted, so AC 1–4 run on the spec's 20 rows.

### 1. `M15: ht.stats.crosstab(), the table`
- `stats/_crosstab.py`: `crosstab(df, rows, columns)` with Decisions 1–5: the input checks, the text reading
  (whole numbers without a decimal, blanks including whitespace-only as `"(blank)"`, other values exactly as
  written), the order (categories present in category order, else text sort, `"(blank)"` last), the counts.
  `agree=` is added in step 2.
- `stats/_result.py`: `CrosstabResult` (Decision 8) with every field, the agreement ones None;
  `.to_frame()` with `"(total)"`; `.mismatches` (empty, with the listing's columns); `.to_dict()`; `str()`
  with the title, table and Decision 9's "No agreement counted" note; `_repr_html_`.
- `stats/__init__.py` exports `crosstab` and `CrosstabResult`; `docs/site/reference/stats.md` entries (the
  reference test, AC 11's first part).
- Docstring: what it counts, blanks, order, `agree=` (described in step 2), an example on a small frame, and
  "See also" `describe()` and `compare()`.
- Tests: new `tests/stats/test_crosstab.py`: AC 1, AC 4, AC 5, AC 7's table, AC 8 except `agree=`, AC 9's table
  part, AC 10's empty frame; new `tests/stats/test_crosstab_result.py`: frozen, `.to_dict()` through
  `json.dumps`, the summary's table and note.

### 2. `M15: agreement and mismatches in crosstab()`
- `_crosstab.py`: the `agree=` argument, `"same"` or a mapping (Decision 6): the mapping read as text on both sides, a
  single value as a one-item list, the missing-key error listing each value and its count and `[]`; the six
  counts and `proportion_agreeing`; the mismatch records with the listing's columns (Decision 7) and index
  labels (text when not str or int).
- `_result.py`: `.mismatches` built from the records; the notes of Decision 9 (agreement line, blank-count
  lines, the first 20 mismatches then "… and N more").
- Docstring: the `agree=` forms, the counts, why a blank on one side is never a mismatch, and why no kappa
  (intent).
- Tests: new `tests/stats/test_crosstab_agree.py`: AC 2, AC 3, AC 6, AC 7's agreement, AC 8's `agree=` errors,
  AC 9 with `agree=`, AC 10's all-blank case and the records round trip; the 20-row cut-off in the summary on a
  synthetic frame of 25 mismatches.

### 3. `docs: comparing classifications` (docs commit, with approval)
- `docs/site/guides/statistics.md`: a "Comparing classifications" section before "See also": the log against
  the lab, choosing a geology key (SPEC §8.3), why agreement needs `agree=`, blanks on one side, reading
  `.mismatches` back into the frame.
- `docs/site/examples/statistics-crosstab.py`: the example project, `legend_code × plasticity_class_uscs` from
  `p.atterberg()` with `agree="same"`, then a mapping (AC 11). *Changed in the build:* not `uscs_symbol` from
  `p.index_properties()`, whose expected warnings (curves short of D10, specimens without a symbol) fail the
  site build, which allows no warning in an example.
- Check: `uv run python docs/prepare_site.py && uv run zensical build --clean --strict`, and read the example's
  output by eye.

### 4. `M15: close out (e)`
- SPEC §5 (the input bullets scoped to the functions that summarize values; `crosstab` built; `CrosstabResult`
  in the result list), §8.3 (`ht.stats.crosstab()`), §12.4 (M15 row: (e) done, M15 closed);
  `docs/drafts/phase3-stats.md` (the `crosstab` row decided, pointing here); TODO #52 (kappa) added; the
  CLAUDE.md status paragraph (M15 (e) done, next wave 0).
- The whole suite and the oldest-versions run, then `git checkout uv.lock`.
- Each acceptance criterion reported met or not, with evidence.

### Verification
- Per step: `uv run pytest tests/stats/test_crosstab*.py` while working; the whole suite
  (`uv run pytest -n auto --dist loadfile`) and `uv run ruff check . && uv run ruff format --check .` before
  each commit.
- Golden tables are the spec's hand counts from the listed rows, never from running the implementation.
- Read `print(result)` for AC 1–3 by eye before step 2's commit and in the site example.
