# M5 AGS4 ingest: plan

Intent: [intent.md](intent.md). Spec: [`docs/data/ingest.md`](../../data/ingest.md).

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines (not counting test data) is split.

## Spec changes in this commit
Checking python-ags4 1.2.0's five dictionaries (4.0.3, 4.0.4, 4.1, 4.1.1, 4.2) showed that **nothing is renamed between versions, only removed**. `IPRG`/`IPRT` are deprecated in 4.1, where `FGHG`/`FGHS`/`FGHT` were added alongside them, and are removed in 4.2. They don't map one to one: `IPRG` has a row per stage, `FGHG` a row per test, and `FGHT` needs keys `IPRT` doesn't have. The same is true of `ERES`, which has no 4.2 replacement.

Decided in review (2026-10-14): **no version mapping.** Groups and headings 4.2 removed are kept under their own names, read through their own version's dictionary, with `M001`. So there is no `version_map.yaml`. This commit updates:
- `docs/data/ingest.md` §3, §4, §5, §6 (rewritten, with the full list of removals), §7 (which dictionary gives the expected and canonical unit), §9 (`M001`), §11 (`site_v404.ags`), §12 AC 3, §13 (open question 1 closed);
- `SPEC.md` §6.1, §6.2 (Versions) and §7 (Canonical layer): "mapped up" replaced by the rule above.

## Package layout
```
src/hangtu/
  __init__.py                 exports Project
  project.py                  Project: from_ags, open, settings, groups, table, sql, repr
  db.py                       the only module that talks to SQLite (SPEC §7): schema, writers, read-only reads
  ags/__init__.py             ingest(path, ...) -> the tables db.py writes
  ags/_read.py                hash, decode, python-ags4 parse and check, output capture, findings V…
  ags/_dictionary.py          heading info from 4.2 → file version → DICT (§6); version, V000, M001
  ags/_units.py               heading units: U001–U004, pcf, ton (§7)
  ags/_values.py              typing and value flags (§7, §8), T001
  ags/_keys.py                location_id, sample_id, specimen table (§5)
  ags/value_flags.yaml        recognized flag strings (§8)
  units/aliases.yaml          + every unit string in the five dictionaries
tests/ags/
  test_files.py               the test files themselves (validation)
  test_read.py  test_dictionary.py  test_units.py  test_values.py  test_keys.py
  test_db.py  test_project.py
  test_ingest_acceptance.py   §12 criteria, end to end
tests/data/ags/
  site_si.ags  site_us.ags  site_v404.ags  defects.ags
```

## Decisions the build makes
Implementation choices the spec leaves open. Any that changes what a user sees goes into `ingest.md` in the commit that builds it.
1. **python-ags4 floor is 1.2.0**, the first release that ships the 4.2 dictionary (1.1.0 has 4.0.3–4.1.1 only). It requires `pandas>=2.1,<3`, which fits ours. Its dictionaries are found with `importlib.resources.files("python_ags4")`, never copied into hangtu.
2. **An unrecognized `TRAN_AGS`** makes python-ags4 fall back to the 4.1.1 dictionary, so ingest passes `standard_AGS4_dictionary="4.2"` in that case, to match §6.
   **python-ags4 results become findings like this:** `AGS Format Rule <n>` → `V<n>` (`V10b`, …), severity error; `FYI (…)` → `V<n>` of the related rule, or `VFYI`, severity info; `Warning`/`General` → warning; `Validator Process Error` → error. `Summary of data` and `Metadata` aren't findings. The line comes from the result's `line` where it is a number.
3. **Captured output:** stdout and stderr are redirected, and python-ags4's `logger` gets a temporary handler with propagation switched off, for the duration of each call. Messages that carry information (`DICT group not found…`) are dropped when `check_file` already reports the same thing. Any other message becomes a `V` warning, so nothing is lost.
4. **Line numbers** come from `AGS4_to_dataframe(..., get_line_numbers=True)`, which returns a third dict and a `line_number` column. The `UNIT` and `TYPE` rows go into `meta_heading`, and only `DATA` rows reach `raw_<GROUP>`.
5. **Encoding:** the file is read as UTF-8, with a BOM accepted. If it isn't valid UTF-8, the error names the first bad line and says to save the file as UTF-8. Nothing falls back to another encoding, which would be a guess. This adds a bullet to `ingest.md` §10.
6. **Date and time formats never reach the unit parser.** For `DT` and `T` headings the `UNIT` row is a format, read by `_values.py` (pint reads `hh:mm` as hectohours × millimeters). An unparseable date or time → NULL + `OTHER` + `T001`.
7. **Unit aliases:** every unit string in the five dictionaries goes into `aliases.yaml` as an explicit entry. That includes the ones pint can't read or misreads (`m2/yr`, `kg/m3`, `Nm`, `m2/MN`, `cm3`, `mm2`, `cm2`, `MJ/m3`, `W/(K-m)`, `(K-m)/W`, `ppmv`, `Bar`, `µS/cm`, `mm:ss`…). A test reads the five dictionaries and checks each non-format unit resolves through an alias, so the dictionaries' own units never raise `U002`. Ingest calls `units._lookup` (alias, then pint, with no warning) rather than `parse_unit`, which warns.
8. **`M001` is for removals only.** Groups and headings from the file's version dictionary that 4.2 removed get `M001`. User-defined ones get no `M` finding, since python-ags4 already reports undeclared groups and headings (Rule 9, Rule 18).
9. **Keys** are given in file order, starting at 1, so the twin files get identical keys. Sample matching uses whichever of the five `SAMP` key headings both tables have. A specimen needs a `sample_id`: an orphan sample's specimen gets a NULL `specimen_id` and isn't added to `specimen`.
10. **SQL identifiers are always double-quoted**, because `group` is a keyword and user-defined headings can be anything Rule 19 allows. Tables are `STRICT`. A test checks `sqlite3.sqlite_version >= 3.37`, and CI runs it on all three operating systems.
11. **Atomic build:** the database is written to `<db>.tmp-<random>` in the same directory, then moved over `db` with `os.replace` once every connection is closed. If anything fails, the temporary file is removed.
12. **Read-only connection:** `sqlite3.connect(Path(db).resolve().as_uri() + "?mode=ro", uri=True)`, so Windows paths and spaces work.
13. **`p.settings`** is a `Settings`-like object over `meta_project`. It checks values with the same validators as `ht.settings` (`_settings._VALIDATORS`) and writes each assignment straight away, stored as JSON. `from_ags` stores every setting.
14. **`p.table()`** sets `df.attrs["units"]` to `{heading: canonical unit string}`, for the headings that have one. The strings are the dictionary's (`kPa`, `Mg/m3`), so `ht.units_of` and the plots read them through the aliases. `value_flag`, `finding` and the `meta_*` tables are read with `p.sql()` until M6/M7.
15. **US twin precision:** `site_us.ags` declares `10SF` as the `TYPE` of converted numeric headings, so its values carry enough digits for AC 1's 1e-9 tolerance. python-ags4 accepts a `TYPE` that differs from the dictionary's, and the file's own `TYPE` row is what Rule 8 checks against.
16. **Schema version** is a constant integer in `db.py`, and is raised whenever the layout changes. `open` compares it for equality.

## Build 1: `M5: add python-ags4 and the synthetic AGS test files`
- `pyproject.toml`: `python-ags4>=1.2.0`; `uv.lock`.
- `tests/data/ags/`: the four files in §11, written by `_make_files.py` from SI data typed in by hand. The US twin divides by exact factors from their definitions (0.3048 m/ft, 0.45359237 kg/lb, standard gravity), not by pint, so the twin test checks hangtu against independent arithmetic (decision 15). AGS files can't hold comments, so each file's purpose is in `tests/data/ags/README.md`. A test fails if a committed file differs from what the script writes.
- `tests/ags/test_files.py`: `site_si`, `site_us` and `site_v404` pass `check_file` with no findings at all. `defects.ags` produces the python-ags4 rules it was built to trigger, including the orphan sample (Rule 10).

## Build 2: `M5: read AGS files into text tables and findings`
- `ags/_read.py`: SHA-256 and size from the bytes; decoding (decision 5); `check_file` → findings (decision 2); `AGS4_to_dataframe` with line numbers (decision 4); capture (decision 3). Errors from §10: file not found, not AGS4 (no `GROUP` line), parse failure with line and reason, not UTF-8.
- Tests: the line numbers of a few known DATA rows; a BOM file reads the same as one without; nothing is printed or logged (`capsys`, `caplog`); each error's text says what, where and what to do.

## Build 3: `M5: read heading types, units and keys from the dictionaries`
- `ags/_dictionary.py`: reads the five python-ags4 dictionaries (cached), the version from `TRAN_AGS` (`V000`), and the lookup order 4.2 → file version → `DICT` (§6). For each heading it gives the type, unit, key status and parent group. `M001` for removals (decision 8).
- Tests: `ISPT_NVAL` from 4.2; `IPRG_IPRM` (m/s) and `RUCS_E` from 4.0.4, each with `M001`; a user-defined group's parent and keys from `DICT`; a user-defined group with no `DICT` entry; `TRAN_AGS` missing and `"4.9"` → read as 4.2 + `V000`.

## Build 4: `units: add the AGS4 dictionary unit spellings`
- `units/aliases.yaml`: decision 7. This is a separate commit because it changes what `ht.read_csv`/`set_units` accept too. Each entry is checked against pint.
- Tests: every non-format unit in the five dictionaries resolves through an alias; `"Bar"` and `"bar"` both resolve; `hh:mm` isn't an alias.

## Build 5: `M5: resolve heading units on ingest`
- `ags/_units.py`: §7 Units, steps 1–5: canonical unit and conversion factor per heading; `U001`–`U004`; pcf by expected dimension (reusing `units.convert`); ton by the file's length system; user-defined headings through `units._kind_of`.
- Tests: ft → m, psf → kPa, cm/s → m/s; the same string `pcf` in two headings (P00 §4.3 #1): in a density heading (`RDEN_BDEN`, dictionary unit Mg/m³) it's lb/ft³, so 125 pcf → 2.0023 Mg/m³; in a unit-weight heading (dictionary unit kN/m³) it's lbf/ft³, so 125 pcf → 19.636 kN/m³. Two separate conversions, never one into the other; pcf in a user-defined heading → `U001`; `tsf`, `t/m2` and a bare `t` with ft and with m; `kPa` in a depth heading → `U004`; blank unit in a dictionary heading with a unit → `U003`, and in `ISPT_NVAL` → stored as is; `degC` from 4.0.4 → no finding.

## Build 6: `M5: type values and flag NP, Dry, refusals and bounds`
- `ags/_values.py`, `ags/value_flags.yaml`: the §7 type table, DT/T/YN/DMS parsing (decision 6), §8 flags, `T001`.
- Tests (AC 6): `NP`, `Dry`, a refusal in `ISPT_NVAL` and `ISPT_REP`, `<0.1`, `>50`, `#2.65`, blank, `abc`; ` NP ` trimmed, `np` → `OTHER`; `X` with `%` (`LNMC_MC`) numeric with flags, `X` without a unit stays text; `2026-10-14T09:30` → ISO; `01:20:00` → 4800 s; `52:30:15.0N` style DMS → decimal degrees (hand value); `Y`/`N` → 1/0.

## Build 7: `M5: resolve location, sample and specimen keys`
- `ags/_keys.py`: §5, with decision 9.
- Tests (AC 4): every child row in `site_si.ags` has its keys; `LLPL` and `LNMC` on one specimen share `specimen_id`; `"1.50"` doesn't match `"1.5"`; the orphan has NULL `sample_id` and `specimen_id`.

## Build 8: `M5: write the project database`
- `db.py`: the §4 layout (decisions 10, 11, 12, 16); writers for the raw, canonical and meta tables; `read_table`, `read_sql`.
- `ags/__init__.py`: `ingest()` chains build 2 → 7 into the tables `db.py` writes.
- Tests: AC 2 (every raw cell equals the file's text, `_line` correct); AC 9 (a parse failure leaves no file, and an existing database is byte-identical afterwards); STRICT tables; the SQLite version.
- If this step goes past 300 lines, `ingest()` and its tests become a commit of their own.

## Build 9: `M5: add ht.Project to build and open a project database`
- `project.py`: §2 in full, with decisions 13 and 14; the §10 errors; `repr` summary. Exported as `ht.Project`.
- Tests (AC 8, 10): `open` reads back the same tables; a changed source file warns with the re-ingest call; a moved source file doesn't warn; a schema mismatch errors; `from_ags` on an existing database errors without `overwrite=True`; `db=None` → `site.sqlite` next to the file; `p.sql("delete …")` is rejected; `p.table("NOPE")` lists the groups; `p.settings.display_units = "XX"` errors and leaves the stored value; the settings persist across `open`.

## Build 10: `M5: test ingest against the acceptance criteria`
- `tests/ags/test_ingest_acceptance.py`, one test (or parametrized set) per criterion, end to end through `ht.Project`: AC 1 (twin files: every canonical table, flag and key equal, values to 1e-9 relative), AC 3 (`site_v404.ags`), AC 5, AC 7 (each §9 rule from `defects.ags`, with group, heading and line), AC 11 (no warnings and no output for the good files). AC 2, 4, 6, 8, 9 and 10 are already covered in builds 6–9; this file points to them rather than repeating them.

## Build 11 (close-out): `M5: close out AGS4 ingest`
- `docs/data/ingest.md`: status → done; anything the build changed (decision 5 in §10, and any that changes what a user sees).
- `SPEC.md`: §12.1 `python-ags4>=1.2.0`, and SQLite ≥ 3.37 checked on CI; §12.2 `ht.Project` among the top-level names, and `ags/` and `db.py`; §12.4 M5 done.
- `TODO.md`: the "AGS heading names checked" entry notes there are no renames; anything new found in the build.
- `CLAUDE.md`: the status line says M5 is done and M6 is next.
- This plan: a Results section.

## Verification
- After each build: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- At close-out: Python 3.13 and 3.14 (`uv run --isolated --python 3.1x pytest`); the lowest dependency versions, as in CLAUDE.md (python-ags4 1.2.0 is then the floor actually tested); `uv build`, and check that the wheel has `ags/value_flags.yaml` and the new aliases.
- Not visual: M5 has no figure, so there's no `visual-check.png`.
