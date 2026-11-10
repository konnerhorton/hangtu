# `read_csv` reads `<x` and `>x` as bounds (TODO #64)

## Intent

- **Goal:** `ht.read_csv` reads a bound written into a value cell (`<5`, `> 200`, `<1e-9`) as the number in the value column and the sign in the value's qualifier column, as AGS ingest does for `LT`/`GT` flags (SPEC §6.2).
- **Why:** today the cell stays text. An analysis stops with "not a number", P01 stops with an error, and the statistics leave the row out as text, so a censored lab value (a hand vane at its maximum, a hydraulic conductivity below what the test resolves) is lost unless the user splits the column by hand. CSV and AGS data should reach the analyses in the same shape (SPEC §2.6, CSV templates).
- **Constraints:**
  - Never guess: only a cell that is entirely `<` or `>` and a number is split; other text stays as written, and the existing messages still name it.
  - Never drop or overwrite a flag: a row whose qualifier column already holds a different sign, or two bounded values on one row sharing the generic `qualifier`, is an error naming the rows and columns.
  - Only registered number columns are split. `correlation_qualifier` is never written; only hangtu produces it.
- **Out of scope:** `NP` and `refusal` text (already read as text flags downstream); `set_units()` and frames not read by `read_csv`; declaring a file's units in one step (TODO #66).
- **Touches:** SPEC §2.6 (new bullet, below). TODO #64 is removed at close.

The SPEC §2.6 bullet "Bounds in a CSV" records the decision, in this commit.

## Plan

1. **Bound pattern** (`src/hangtu/_data.py`): `_BOUND` accepts an exponent (`<1e-9`, `> 2.5E+3`), and a new `split_bound(text) -> (sign, number) | None` reads one cell. Tests in `tests/test_data.py`: `<5`, `> 200`, `<1e-9`, `<.5`, `< -3` match; `<`, `<5 kPa`, `≤5`, `5<` don't.
   - Commit: `units: read exponents in a bound written as a value`
2. **Qualifier lookup** (`src/hangtu/registry.py` or beside `statistics_roles()`): `qualifier_for(column) -> str`, the qualifier with `role: qualifier`, `replaces` and `column` in its `values`, else `"qualifier"`. Never `correlation_qualifier` (it has `values` but no `replaces`). Tests: `remolded_undrained_shear_strength` → `remolded_qualifier`; `hydraulic_conductivity` and `undrained_shear_strength` → `qualifier`.
3. **Split in `read_csv`** (`src/hangtu/units/__init__.py`): after `pd.read_csv`, before `set_units`, for each registered `type: number` column holding a bound:
   - value → the number, column → float (other text left, so the column stays object where it has any);
   - sign → `qualifier_for(column)`, created as `""` where missing, blanks read as `""`;
   - `ColumnError` naming rows and columns for a differing existing sign, and for two columns on one row whose bounds go to the same qualifier.
   - Rows are named as a spreadsheet numbers them (header row 1) with the file's name, so they match what the user sees; after a pandas argument that shifts rows (`header`, `names`, `skiprows`, `index_col`, `comment`), by the frame's index. (Added at build review.)

   Docstring: a "Bounds" paragraph with an example. Tests in `tests/units/test_dataframes.py` (CSV written to `tmp_path`): each case of step 1 through `read_csv`; remolded goes to `remolded_qualifier`; an existing matching sign is kept, a differing one raises; two bounds on one row raise; `NP` and `12 ft` are left as text; an unregistered column is left as text; units still declared on the split column; end to end, `ht.stats.describe()` on a CSV with `>200` counts the row as censored, not as text.
   - Steps 2–3 commit: `units: read <x and >x in read_csv as a bound and qualifier`
4. **Messages and docs:** `BOUND_FIX` adds that `ht.read_csv` splits these on reading (the manual steps stay, for frames built otherwise); update the tests that match its text. `docs/site/getting-started/csv.md` gets a short "Bounds" note. CHANGELOG Unreleased line; remove TODO #64; STATUS if it lists the item.
   - Commit: `docs: say read_csv reads bounds written as values`

Before each commit: `uv run ruff check . && uv run ruff format .`, `uv run mypy`, the touched tests, then the whole suite once (`-n 2`).
