# M5: AGS4 ingest

## Intent

### Goal
Read an AGS4 file (4.0.3 to 4.2) into a project SQLite database: a raw layer exactly as in the file, and a canonical layer that is AGS 4.2-shaped, typed, in SI, with value flags and surrogate keys (SPEC §6, §7). Open the database again later and query it.

### Why
- It's the first Phase 2 unit (SPEC §1.3 build order, §12.4 M5). QC (M6) and the datasets (M7) both read the canonical layer, so it comes first.
- It's what makes hangtu useful on real AGS files rather than hand-built CSVs.
- It tests the data model decision (SPEC §7) against real files early, while reversing it is still cheap.

### Constraints
- SPEC §6 (pipeline, versions, one file per project, blank vs flagged), §7 (data model rules), §2.2 (convert to SI on ingest, never guess units, case-sensitive aliases), §11 (error messages).
- `python-ags4` is added as a dependency (allowed by SPEC §12.1). No other new dependency. SQLite comes with Python; `STRICT` tables need SQLite ≥ 3.37, so check the version shipped with Python 3.12 on all three CI platforms.
- Units on ingest follow `docs/drafts/phase2-data.md` (Units on ingest), which the spec step finishes: "ton" by context, mixed units per column, datum as a setting.
- Never drop data silently: anything that can't be typed or converted stays in the raw layer and becomes a finding (`V`, `U001`–`U003`, `T001`).
- No company data: the test files are synthetic (SPEC §1.1, §12.3).
- **Done when:** the spec's acceptance criteria pass, including the twin-file test (the same data in an SI file and a US file ingests to identical canonical tables) and one older-version file mapped up to 4.2.

### Decisions (proposed, to settle in review)
1. **Where the spec lives:** `docs/data/ingest.md`, a topic doc that outlives the unit (process.md). `docs/drafts/phase2-data.md` keeps the QC and dataset notes until M6 and M7.
2. **Entry point:** `ht.Project.from_ags(path, db=..., overwrite=False)` and `ht.Project.open(db)`, as in the SPEC §11 sketch. Opening checks the file hash and the schema version (SPEC §7).
3. **Project access in this unit:** `p.groups`, `p.table(group, raw=False)` and `p.sql(...)`, so the result can be inspected. `p.locations` and `p.diff()` wait for M6/M7.
4. **Every group goes in.** All groups, user-defined ones included, are written to the raw layer and typed into the canonical layer from their `TYPE` row. A numeric heading is converted to SI from its `UNIT` row by pint. A short mapping file (`heading_quantities.yaml`) is needed only where the unit alone isn't enough: numeric headings of type `X` (`LNMC_MC`), and units whose meaning depends on the quantity (`pcf`, `%`, `ton`).
5. **Findings are stored, not reported.** Ingest writes its findings (`V`, `U`, `T`) to a table. The report, the rule YAML and `p.qc()` are M6.
6. **Test files:** a small synthetic SI file and its US twin, covering PROJ, TRAN, UNIT, TYPE, ABBR, LOCA, GEOL, SAMP, ISPT, LLPL, LNMC, GRAG, GRAT, PTST and FGHG; a 4.0.4 file with IPRG, to test mapping up; and a defects file for the ingest findings. Each passes python-ags4 validation except the defects file.

### Out of scope
- QC rules beyond the ones ingest raises, the QC report and `diff()` (M6).
- Depth/elevation/geology joins, the geology map and the ready-made datasets (M7).
- Mid-drive SPT depth (SPEC §8.2, M7).
- DIGGS, AGS3, more than one file per project.
- Writing or editing AGS files (SPEC §1.4).
- The open research items in the Units on ingest notes: pcf in density headings (#5) and nominal SPT penetrations (#6). Ingest converts what the file declares; the research can change a mapping later.

### SPEC sections touched
- §6: pipeline and rules confirmed or adjusted by the spec.
- §11: the Phase 2 API sketch, if decision 2 or 3 changes it.
- §12.1: `python-ags4` with its version floor; SQLite version note.
- §12.4: M5 done at close-out.
- `docs/drafts/phase2-data.md`: Ingestion and Units on ingest move to `docs/data/ingest.md`.

## Plan

Spec: [`docs/data/ingest.md`](../data/ingest.md).

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines (not counting test data) is split.

### Spec changes in this commit
Checking python-ags4 1.2.0's five dictionaries (4.0.3, 4.0.4, 4.1, 4.1.1, 4.2) showed that **nothing is renamed between versions, only removed**. `IPRG`/`IPRT` are deprecated in 4.1, where `FGHG`/`FGHS`/`FGHT` were added alongside them, and are removed in 4.2. They don't map one to one: `IPRG` has a row per stage, `FGHG` a row per test, and `FGHT` needs keys `IPRT` doesn't have. The same is true of `ERES`, which has no 4.2 replacement.

Decided in review (2026-10-14): **no version mapping.** Groups and headings 4.2 removed are kept under their own names, read through their own version's dictionary, with `M001`. So there is no `version_map.yaml`. This commit updates:
- `docs/data/ingest.md` §3, §4, §5, §6 (rewritten, with the full list of removals), §7 (which dictionary gives the expected and canonical unit), §9 (`M001`), §11 (`site_v404.ags`), §12 AC 3, §13 (open question 1 closed);
- `SPEC.md` §6.1, §6.2 (Versions) and §7 (Canonical layer): "mapped up" replaced by the rule above.

### Package layout
```
src/hangtu/
  __init__.py                 exports Project
  project.py                  Project: from_ags, open, settings, groups, table, sql, repr
  db.py                       the only module that talks to SQLite (SPEC §7): schema, writers, read-only reads
  ags/__init__.py             ingest(path, ...) -> the tables db.py writes
  ags/_findings.py            the Finding record
  ags/_read.py                hash, decode, python-ags4 parse and check, output capture, version, findings V…
  ags/_dictionary.py          heading info from 4.2 → file version → DICT (§6); M001
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

### Decisions the build makes
Implementation choices the spec leaves open. Any that changes what a user sees goes into `ingest.md` in the commit that builds it.
1. **python-ags4 floor is 1.2.0**, the first release that ships the 4.2 dictionary (1.1.0 has 4.0.3–4.1.1 only). It requires `pandas>=2.1,<3`, which fits ours. Its dictionaries are found with `importlib.resources.files("python_ags4")`, never copied into hangtu.
2. **An unrecognized `TRAN_AGS`** makes python-ags4 fall back to the 4.1.1 dictionary, so ingest passes `standard_AGS4_dictionary="4.2"` in that case, to match §6.
   **python-ags4 results become findings like this:** `AGS Format Rule <n>` → `V<n>` (`V10b`, …), severity error; `FYI (…)` → `V<n>` of the related rule, or `VFYI`, severity info; `Warning`/`General` → warning; `Validator Process Error` → error. `Summary of data` and `Metadata` aren't findings. The line comes from the result's `line` where it is a number.
3. **Captured output:** stdout and stderr are redirected, and python-ags4's `logger` gets a temporary handler with propagation switched off, for the duration of each call. Each logged warning or error becomes a `VLOG` finding, once (`check_file` parses the file again, so messages come twice), except `DICT group not found…`, which is normal for a file without user-defined groups. Some problems are only logged: python-ags4 renames a duplicate heading and reports it nowhere else.
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

### Build 1: `M5: add python-ags4 and the synthetic AGS test files`
- `pyproject.toml`: `python-ags4>=1.2.0`; `uv.lock`.
- `tests/data/ags/`: the four files in §11, written by `_make_files.py` from SI data typed in by hand. The US twin divides by exact factors from their definitions (0.3048 m/ft, 0.45359237 kg/lb, standard gravity), not by pint, so the twin test checks hangtu against independent arithmetic (decision 15). AGS files can't hold comments, so each file's purpose is in `tests/data/ags/README.md`. A test fails if a committed file differs from what the script writes.
- `tests/ags/test_files.py`: `site_si`, `site_us` and `site_v404` pass `check_file` with no findings at all. `defects.ags` produces the python-ags4 rules it was built to trigger, including the orphan sample (Rule 10).

### Build 2: `M5: read AGS files into text tables and findings`
- `ags/_read.py`: SHA-256 and size from the bytes; decoding (decision 5); `AGS4_to_dataframe` with line numbers (decision 4); the version from `TRAN_AGS` and `V000`, here rather than in build 3 because `check_file` needs the version; `check_file` → findings (decision 2); capture (decision 3). Errors from §10: file not found, not AGS4 (no `GROUP` line), parse failure with line and reason, not UTF-8.
- Tests: the line numbers of a few known DATA rows; a BOM file reads the same as one without; nothing is printed or logged (`capsys`, `caplog`); each error's text says what, where and what to do.

### Build 3: `M5: read heading types, units and keys from the dictionaries`
- `ags/_dictionary.py`: reads the five python-ags4 dictionaries (cached) and applies the lookup order 4.2 → file version → `DICT` (§6). For each heading it gives the type, unit, key status and parent group. `M001` for removals (decision 8).
- Tests: `ISPT_NVAL` from 4.2; `IPRG_IPRM` (m/s) and `RUCS_E` from 4.0.4, each with `M001`; a user-defined group's parent and keys from `DICT`; a user-defined group with no `DICT` entry.

### Build 4: `units: add the AGS4 dictionary unit spellings`
- `units/aliases.yaml`: decision 7. This is a separate commit because it changes what `ht.read_csv`/`set_units` accept too. Each entry is checked against pint.
- Tests: every non-format unit in the five dictionaries resolves through an alias; `"Bar"` and `"bar"` both resolve; `hh:mm` isn't an alias.

### Build 5: `M5: resolve heading units on ingest`
- `ags/_units.py`: §7 Units, steps 1–5: canonical unit and conversion factor per heading; `U001`–`U004`; pcf by expected dimension (reusing `units.convert`); ton by the file's length system; user-defined headings through `units._kind_of`.
- Tests: ft → m, psf → kPa, cm/s → m/s; the same string `pcf` in two headings (P00 §4.3 #1): in a density heading (`RDEN_BDEN`, dictionary unit Mg/m³) it's lb/ft³, so 125 pcf → 2.0023 Mg/m³; in a unit-weight heading (dictionary unit kN/m³) it's lbf/ft³, so 125 pcf → 19.636 kN/m³. Two separate conversions, never one into the other; pcf in a user-defined heading → `U001`; `tsf`, `t/m2` and a bare `t` with ft and with m; `kPa` in a depth heading → `U004`; blank unit in a dictionary heading with a unit → `U003`, and in `ISPT_NVAL` → stored as is; `degC` from 4.0.4 → no finding.

### Build 6: `M5: type values and flag NP, Dry, refusals and bounds`
- `ags/_values.py`, `ags/value_flags.yaml`: the §7 type table, DT/T/YN/DMS parsing (decision 6), §8 flags, `T001`.
- Tests (AC 6): `NP`, `Dry`, a refusal in `ISPT_NVAL` and `ISPT_REP`, `<0.1`, `>50`, `#2.65`, blank, `abc`; ` NP ` trimmed, `np` → `OTHER`; `X` with `%` (`LNMC_MC`) numeric with flags, `X` without a unit stays text; `2026-10-14T09:30` → ISO; `01:20:00` → 4800 s; `52:30:15.0N` style DMS → decimal degrees (hand value); `Y`/`N` → 1/0.

### Build 7: `M5: resolve location, sample and specimen keys`
- `ags/_keys.py`: §5, with decision 9.
- Tests (AC 4): every child row in `site_si.ags` has its keys; `LLPL` and `LNMC` on one specimen share `specimen_id`; `"1.50"` doesn't match `"1.5"`; the orphan has NULL `sample_id` and `specimen_id`.

### Build 8: `M5: write the project database`
- `db.py`: the §4 layout (decisions 10, 11, 12, 16); writers for the raw, canonical and meta tables; `read_table`, `read_sql`.
- `ags/__init__.py`: `ingest()` chains build 2 → 7 into the tables `db.py` writes.
- Tests: AC 2 (every raw cell equals the file's text, `_line` correct); AC 9 (a parse failure leaves no file, and an existing database is byte-identical afterwards); STRICT tables; the SQLite version.
- Split in two, since it goes past 300 lines: `M5: chain the ingest steps into canonical tables` (`ags.ingest()` and its tests) first, then `db.py`.

### Build 9: `M5: add ht.Project to build and open a project database`
- `project.py`: §2 in full, with decisions 13 and 14; the §10 errors; `repr` summary. Exported as `ht.Project`.
- Tests (AC 8, 10): `open` reads back the same tables; a changed source file warns with the re-ingest call; a moved source file doesn't warn; a schema mismatch errors; `from_ags` on an existing database errors without `overwrite=True`; `db=None` → `site.sqlite` next to the file; `p.sql("delete …")` is rejected; `p.table("NOPE")` lists the groups; `p.settings.display_units = "XX"` errors and leaves the stored value; the settings persist across `open`.

### Build 10: `M5: test ingest against the acceptance criteria`
- `tests/ags/test_ingest_acceptance.py`, one test (or parametrized set) per criterion, end to end through `ht.Project`: AC 1 (twin files: every canonical table, flag and key equal, values to 1e-9 relative), AC 3 (`site_v404.ags`), AC 5, AC 7 (each §9 rule from `defects.ags`, with group, heading and line), AC 11 (no warnings and no output for the good files). AC 2, 4, 6, 8, 9 and 10 are already covered in builds 6–9; this file points to them rather than repeating them.

### Build 11 (close-out): `M5: close out AGS4 ingest`
- `docs/data/ingest.md`: status → done; anything the build changed (decision 5 in §10, and any that changes what a user sees).
- `SPEC.md`: §12.1 `python-ags4>=1.2.0`, and SQLite ≥ 3.37 checked on CI; §12.2 `ht.Project` among the top-level names, and `ags/` and `db.py`; §12.4 M5 done.
- `TODO.md`: the "AGS heading names checked" entry notes there are no renames; anything new found in the build.
- `CLAUDE.md`: the status line says M5 is done and M6 is next.
- This plan: a Results section.

### Verification
- After each build: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- At close-out: Python 3.13 and 3.14 (`uv run --isolated --python 3.1x pytest`); the lowest dependency versions, as in CLAUDE.md (python-ags4 1.2.0 is then the floor actually tested); `uv build`, and check that the wheel has `ags/value_flags.yaml` and the new aliases.
- Not visual: M5 has no figure, so there's no `visual-check.png`.

### Results
- 1218 tests pass on Python 3.12, 3.13 and 3.14, and with the lowest dependency versions (pandas 2.1.1, numpy 1.26.0, matplotlib 3.8.0, pint 0.24.4, pyyaml 6.0.1, python-ags4 1.2.0). The wheel has `hangtu/ags/` with `value_flags.yaml`, `db.py`, `project.py`, and the new aliases.
- **Commits:** one per build step as planned, with build 8 split in two (`ags.ingest()`, then `db.py`).
- **Changes from the plan**, each recorded in `ingest.md` in the commit that made it:
  - The test files are written by `tests/data/ags/_make_files.py` from hand-typed SI data, not by hand, and a test checks the committed files match it. The US twin divides by exact factors from their definitions, not by pint.
  - `M001` can't come from a 4.2 file, so AC 7 takes it from `site_v404.ags` (§11, §12).
  - `V000` is raised by the reader, because `check_file` needs the version: python-ags4 falls back to the 4.1.1 dictionary for an unknown version, so ingest passes 4.2 explicitly (decision 2).
  - python-ags4 reports some problems only in its log (a duplicate heading it renamed). Those become `VLOG` findings, so decision 3's idea of dropping log messages that `check_file` repeats was dropped. The rule names for results without a rule number (`VFYI`, `VWARNING`, `VGENERAL`, `VPROCESS`) are in §9.
  - Refusal: a blows/penetration pair in `ISPT_REP` flags `ISPT_NVAL` (§8). Date, time, DMS and yes/no parsing rules are in §8 too.
  - `specimen.SPEC_DPTH` is in canonical units, so the twins give the same table (§4). `meta_heading.status` values are listed in §4.
  - AC 1 doesn't compare `_line` or the `UNIT`, `TYPE` and `DICT` groups, which describe the file rather than the data.
  - `p.sql()` takes `params` for `?` placeholders; key and `YN` columns come back as `Int64` (§2).
- **For M6:** findings are in the `finding` table with rule, severity, group, heading and line. The new rules for the QC list are `M001`, `U004`, `VLOG` and the `V` names without a rule number. `diff()` can pair `raw_<GROUP>` and `<GROUP>` rows on `_line`.
- **For M7:** canonical columns are AGS headings, and `df.attrs["units"]` uses the dictionary's unit strings, which all resolve through the aliases. The datasets map headings to registry names. `IPRG_IPRM` sits next to `FGHG_IPRM` for permeability (§6).
- SPEC: §6.1, §6.2 and §7 changed in the plan commit (no version mapping); §12.1 and §12.2 at close-out.
