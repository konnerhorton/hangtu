# SPT report: read ISPT_REP the AGS way

## Intent

### Goal
Read `ISPT_REP` the way AGS and US logs write it. A complete test is its blows then `N=`; an incomplete drive is blows ending in a blows/penetration pair. Refusal is flagged only from an incomplete drive, and an incomplete drive with a blank `ISPT_NVAL` stays in the data as a refusal.

### Why
- hangtu 0.1.0 on a real 4.1.1 file (about 4,400 SPTs) raised 4,118 S001 warnings. S001 accepts only a bare `N=12`, so AGS's own dictionary example `6,8/8,9,9,9 N=35` and the ASTM form `5,6,6 N=12` both fail.
- Ingest flags `REFUSAL` when any `x/y` appears anywhere in `ISPT_REP` (`ags/_values.py`, `pattern.search`). Complete tests such as AGS's example (`8/8`) and `41,81,57,75/113 N=126` are flagged as refusals, and S002 then skips them (17 tests in that file).
- AGS gives no refusal token, and its September 2026 guidance on SPTs terminated early puts early termination in `ISPT_REM` and leaves N extrapolation to the designer. A file that follows it leaves `ISPT_NVAL` blank on an incomplete drive. hangtu then raises C001 on every such test and `p.spt()` leaves them out as incomplete, so refusals disappear from P02 and P03.

### Constraints
- **N comes from `ISPT_NVAL` only.** It is never derived from `ISPT_REP` or the increments.
- **Refusal comes from `ISPT_REP` only.** `ISPT_NPEN` isn't read for refusal at ingest. `ht.analysis.spt()` keeps its penetration check for CSV input.
- **Report forms:**
  - complete: an optional blow list (numbers separated by `,`, `/`, `-` or spaces), then `N=<n>`: `N=12`, `5,6,6 N=12`, `6,8/8,9,9,9 N=35`, `41,81,57,75/113 N=126`. Never a refusal.
  - incomplete drive, AGS style: space-separated blows/penetration pairs, `22/150 30/150 50/57`.
  - incomplete drive, log style (common in US logs): blows separated by `-`, `,` or spaces, with no `N=`, ending in one blows/penetration pair, `22-30-50/3"`.
- **A unit after a penetration** is accepted, with or without a space: `mm`, `cm`, `in` or `"` (`50/76mm`, `50/3in`, `50/3"`). Any other suffix fails S001. Penetrations in `ISPT_REP` are never converted or used as numbers (AGS gives the heading no unit), so accepting a unit guesses nothing; the penetration used by `p.spt()` comes from `ISPT_NPEN`, with its declared unit.
- **One parser** for the report, shared by ingest and S001, so the two can't disagree.
- A refusal flag on a blank `ISPT_NVAL` is a value, not a blank (SPEC §6.2; qc.md §4.10, "a flagged value is not missing"). C001 doesn't fire, and `p.spt()` keeps the row with `spt_n` blank, `spt_refusal` True and the capped N at the cap.
- S002 stays a warning. Its message cites the ASTM D1586 termination criteria (50 blows in a 150 mm increment, 100 in total, or no advance over 10 blows).
- The twin files stay twins and QC-clean. New cases go in `qc_defects.ags` and `joins.ags`.

### Out of scope
- The word "refusal" in an AGS cell. It stays unrecognized (`T001`), since AGS has no such token. The CSV path's `"refusal"` text is unchanged.
- Reading N or refusal from `ISPT_INC*`/`ISPT_PEN*`, or extrapolating N.
- The other items from the same review, each its own unit: file-defined units (`file-units`), `LOCA_DATM` (`vertical-datum`), accepted findings and D007 (`qc-review`).

### SPEC sections touched
- §6.2: "refusal" in the recognized-text list becomes "an incomplete drive in `ISPT_REP`".
- `docs/data/ingest.md` §8; `docs/data/qc.md` §4.5, §4.10 and §8; `docs/data/datasets.md` §6.1; `src/hangtu/ags/value_flags.yaml`; `docs/TODO.md` #6 (P003's 2 % tolerance held on a real file) and new research items (PMT depth at the probe center, slope-aware L005).

## Spec

The rules live in the data-layer specs; this section lists what changed and why.

### Changes
- **SPEC §6.2:** "refusal" in the recognized-text list is now "an incomplete drive in `ISPT_REP`".
- **`docs/data/ingest.md` §8, Refusal:** the report forms (complete test, incomplete drive, accepted units after a penetration), N from `ISPT_NVAL` only, and a refusal on a blank `ISPT_NVAL` as a value. Replaces "an `ISPT_REP` with a blows/penetration pair".
- **`docs/data/qc.md` §4.5:** S001 reads the report with ingest's parser; S002's message cites the D1586 termination criteria. **§4.10:** a blank `ISPT_NVAL` flagged `REFUSAL` isn't missing. **§8:** the new S001 and S002 cases.
- **`docs/data/datasets.md` §6.1:** `spt_n` and `spt_refusal` for a refusal with a blank N. **§12:** a `joins.ags` case for it. **§13 #8:** its acceptance criterion. §7 ("incomplete" means what C001 says) needs no change: it follows C001.

### Decisions
1. **One grammar for both incomplete-drive styles.** An incomplete drive is blows and pairs separated by `,`, `-` or spaces, ending in a pair, with no `N=`. That covers AGS's `25/75 50/75` and the US log's `22-30-50/3"` in one rule, and a single pair (`50/76mm`) is both.
2. **The form decides, not the numbers.** Penetrations in `ISPT_REP` have no declared unit, so hangtu doesn't add them up or compare them with 450 mm. `22/150 30/150 50/150` reads as an incomplete drive. A file that means a complete test writes `N=`.
3. **Units after a penetration:** `mm`, `cm`, `in`, `"`. Not `ft` or `'`: a partial increment is under 6 in, and nobody writes it in feet. Accepting a unit guesses nothing, because the number is never used.
4. **The patterns stay in `value_flags.yaml`** (`refusal: complete`, `incomplete`, `penetration_units`), so the grammar is config, not code; `ags/_values.py` builds the parser from it and `qc/_tests.py` imports the parser rather than keeping its own regexes.
5. **"Not missing" is decided in one place.** `Data.blank()` (QC) treats a cell with any value flag as not blank, so C001 and the datasets' incomplete check (which uses C001) both follow. Today it reads the raw text only, which is why the refusal flag on a blank `ISPT_NVAL` didn't count.
6. **`50/75` in `ISPT_NVAL` itself** keeps its current meaning (the blows, flagged `REFUSAL`). It's the N heading, so it doesn't break "N from `ISPT_NVAL` only".

### Acceptance criteria
1. **Parser:** each example in ingest.md §8 reads as its form; `hard`, `50/76 ft`, `refusal`, `N=` and a blank are neither. Complete tests are never flagged.
2. **Ingest flags:** `REFUSAL` on `ISPT_NVAL` for an incomplete drive, with the value as given or blank; none for AGS's example or `41,81,57,75/113 N=126`.
3. **QC:** on `qc_defects.ags`, S001 is raised for `hard` and `50/76 ft` only; S002 for N 150 and N 126; no C001 on the blank-N refusals. The good files stay QC-clean and the twins stay twins (qc.md §9 #2, #3).
4. **Dataset:** in `joins.ags`, the blank-N refusal is in `p.spt()` by default with `spt_n` blank, `spt_refusal` True and `spt_n_capped` = the cap; the incomplete record with a blank report is still left out.
5. **Plots:** P02 draws that refusal at the cap and P03 counts it in the refusal class, from `p.spt()` unchanged.
6. **Message:** S002's message names the D1586 criteria.
