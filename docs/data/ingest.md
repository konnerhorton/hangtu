# AGS4 ingest

| | |
|---|---|
| **Status** | done (M5) |
| **Intent** | [`docs/work/m5-ingest.md`](../work/m5-ingest.md#intent) |
| **Parent** | SPEC §2.2 (units), §6 (ingestion), §7 (data model), §11 (errors) |
| **Related** | P00 §4 (quantity kinds, aliases, pcf). [`qc.md`](qc.md) (M6) reports these findings; `docs/drafts/phase2-data.md` keeps the dataset notes for M7 |

## 1. Purpose and scope
Read one AGS4 file (4.0.3 to 4.2) into a project SQLite database, and open that database again later:
- a **raw layer**, exactly as in the file;
- a **canonical layer**: AGS 4.2-shaped, typed, in SI, with value flags and surrogate keys (SPEC §7);
- the **findings** raised while reading, stored for the QC report (M6).

**Not in scope:** the QC report, rules beyond ingest and `diff()` (M6, [`qc.md`](qc.md)); `p.locations`, the geology map, joins and datasets (M7); mid-drive SPT depth (SPEC §8.2, M7); DIGGS, AGS3 and more than one file per project; writing AGS (SPEC §1.4).

## 2. Public API
```python
p = ht.Project.from_ags("site.ags", db="site.sqlite")   # read the file, build the database
p = ht.Project.from_ags("site.ags", db="site.sqlite", overwrite=True)  # rebuild it
p = ht.Project.open("site.sqlite")                       # open an existing database

p                                  # summary: file, AGS version, groups, rows, findings by severity
p.settings                         # display_units, vertical_datum, … stored with the project
p.groups                           # ["LOCA", "GEOL", "ISPT", ...], in file order
p.table("ISPT")                    # canonical: typed, SI, df.attrs["units"] set
p.table("ISPT", raw=True)          # raw: text exactly as in the file, plus _line
p.sql("select * from ISPT where ISPT_NVAL > 50")   # read-only query, returns a DataFrame
```
- `db=None` puts the database next to the file, with the suffix `.sqlite`.
- **Project settings:** `from_ags` takes the session settings as keywords (`display_units="US"`, `vertical_datum="NAVD88"`, …; P00 §3) and stores them in `meta_project`; anything not given comes from `ht.settings` at the time of ingest. `p.settings` reads and changes them. Export and import (`to_yaml()`/`load_yaml()`) wait for M7.
- **`from_ags` on an existing database** raises an error unless `overwrite=True`; the message names `Project.open` and `overwrite=True`.
- **The database is self-contained.** `open` works without the AGS file. If the file is still at its stored path and its SHA-256 has changed, `open` warns that the database is out of date and shows the `from_ags(..., overwrite=True)` call.
- **Schema version:** if the database was written by an incompatible hangtu version, `open` raises an error saying to re-ingest.
- `p.sql(query, params=())` opens the connection read-only (`mode=ro`); `?` placeholders take `params`. `p.table()` on an unknown group lists the groups that exist; key columns and `YN` headings are nullable integers (`Int64`).

## 3. Pipeline
```
AGS file
  → SHA-256, size; read as UTF-8 (BOM accepted)
  → python-ags4 check_file()            → findings V… (never blocking)
  → python-ags4 AGS4_to_dataframe()     → text tables with line numbers
  → raw writer                          → raw_<GROUP>
  → dictionary per heading (§6)
  → keys (§5), typing and units (§7), value flags (§8)
  → canonical writer                    → <GROUP>, specimen
  → metadata writer                     → meta_*, finding
```
- Ingest fails only if the file can't be parsed (SPEC §6.2). Everything else is a finding.
- The whole build runs in one transaction into a temporary file, renamed over `db` at the end, so a failed ingest never leaves a half-built database.
- python-ags4's console and log output is captured and turned into findings; nothing is printed.

## 4. Database layout
| Table | One row per | Columns |
|---|---|---|
| `raw_<GROUP>` | DATA row in the file | `_line`, then every heading as TEXT, as in the file |
| `<GROUP>` (canonical) | DATA row | `_row` (primary key), `_line`, the surrogate keys that apply (§5), then the 4.2 headings, typed (§7) |
| `specimen` | distinct specimen (§5) | `specimen_id`, `sample_id`, `SPEC_REF`, `SPEC_DPTH` (in m, from the first row that names it) |
| `value_flag` | flagged cell | `group`, `_row`, `heading`, `flag`, `bound`, `text` |
| `finding` | finding | `rule`, `severity`, `group`, `heading`, `_line`, `message` |
| `meta_project` | setting | `key`, `value` |
| `meta_source` | ingest | `path`, `sha256`, `size`, `ags_version`, `ags_version_source`, `ingested_at`, `hangtu_version`, `schema_version` |
| `meta_heading` | heading in the file | `group`, `heading`, `file_unit`, `file_type`, `unit` (canonical), `quantity`, `status`, `standard` (in the 4.2 dictionary) |

- The canonical table for `UNIT`, `TYPE`, `ABBR`, `DICT` and `TRAN` is written like any other group; `meta_heading` is the typed summary.
- `meta_heading.status` is `converted` (to `unit`), `as_is` (a number with no unit, such as a count), `raw_only` (a `U001`, `U003` or `U004` column, NULL in the canonical table) or `not_numeric` (text, dates, yes/no).
- Canonical group names and headings are the file's (§6). A user-defined group keeps its own name.
- Tables are `STRICT` (SQLite ≥ 3.37; Python 3.12's bundled SQLite is newer on all CI platforms, checked in the build).

## 5. Keys
- **Locations:** `LOCA.location_id`. Every group whose 4.2 parent chain reaches `LOCA` carries `location_id`.
- **Samples:** `SAMP.sample_id`, matched on the 4.2 key headings (`LOCA_ID`, `SAMP_TOP`, `SAMP_REF`, `SAMP_TYPE`, `SAMP_ID`). Every group below `SAMP` carries `sample_id`.
- **Specimens:** AGS4 has no specimen group; a specimen is identified by its sample plus `SPEC_REF` and `SPEC_DPTH` inside each lab group. The `specimen` table holds each distinct combination found across all groups, and every group carrying those headings gets `specimen_id`. So `LLPL` and `LNMC` on the same specimen share a `specimen_id`.
- **Parents and key headings come from the dictionary:** the dictionary that describes the group (§6): 4.2 for standard groups, the file's version for groups 4.2 removed, and the file's `DICT` group for user-defined ones. A user-defined group with no `DICT` entry gets `location_id` if it has `LOCA_ID`, and no other keys.
- **Matching** compares key text exactly as written (`"1.50"` ≠ `"1.5"`), as AGS4 Rule 10 does. A row whose parent can't be found keeps a NULL key; python-ags4 already reports it (Rule 10b/10c).
- Joins inside hangtu use the surrogate keys only (SPEC §7).

## 6. Versions
- **The version** comes from `TRAN_AGS`. If it's missing or unrecognized, the file is read as 4.2 and finding `V000` says so.
- **Nothing is renamed between 4.0.3 and 4.2, only removed** (checked against python-ags4 1.2.0's dictionaries). So older files need no mapping: groups and headings keep their names, and each heading is read through one dictionary, in this order:
  1. the **4.2 dictionary**, for every group and heading it has;
  2. the **file's own version's dictionary**, for groups and headings that 4.2 removed;
  3. the file's **`DICT` group**, for user-defined groups and headings.
- **Removed by 4.2**, and kept under their own names with finding `M001` (info): the groups `IPRG`, `IPRT` (in-situ permeability, deprecated in 4.1, where `FGHG`/`FGHS`/`FGHT` were added alongside) and `ERES` (deprecated in 4.1, no 4.2 replacement); the headings `RUCS_E`, `RUCS_ESTR`, `RUCS_ETYP`, `RUCS_MU`, `PMTD_ARM1`–`3` (4.0.3–4.1.1), `PMTL.PMTD_SEQ` (4.0.3–4.1), and `GCHM_RDEV`, `WGPG_LIM`, `WGPG_ULIM` (4.1 only).
- **`IPRG` isn't turned into `FGHG`** (decided 2026-10-14). `IPRG` has a row per stage where `FGHG` has a row per test, and `FGHT` needs keys `IPRT` doesn't have (`FGHT_TIME`, `FGHI_INST`, `FGHT_TYPE`), so a mapping would invent data (SPEC §7, "only what the file says"). The permeability dataset (M7) reads `IPRG_IPRM` next to `FGHG_IPRM`.
- Headings that exist only from 4.1 (`ISPT_N60`, `SPEC_BASE`, `GRAG_CC`) are simply absent in older files; the datasets (M7) treat them as blank.
- Unit spellings that changed between versions (`degC` → `DegC`, `Bar` → `bar`, `µS/cm` → `uS/cm`) are handled by the unit aliases (§7). A few headings had no unit before 4.2 (`ISAG_SI`, `SCPT_MAGX`/`Y`/`Z`/`T`); in an older file with the unit blank they raise `U003` like any other, since the unit isn't declared.

## 7. Typing and units
**Type** from the file's `TYPE` row (the draft's type mapping, decided here):

| AGS TYPE | Canonical | Notes |
|---|---|---|
| `ID`, `PA`, `PT`, `PU`, `RL`, `RECORD LINK` | TEXT | |
| `X` with no physical unit | TEXT | |
| `X` with a physical unit or `%`, and `XN` | REAL + value flags (§8) | e.g. `LNMC_MC` is `X` with `%`. 46 such headings in 4.2 |
| `nDP`, `nSF`, `nSCI`, `MC`, `U` | REAL | Text that isn't a number → NULL + flag `OTHER` + `T001` |
| `DT` | TEXT, ISO 8601 | The `UNIT` row holds the format (`yyyy-mm-dd`, …) |
| `T` | REAL, seconds | Format from the `UNIT` row (`hh:mm:ss`, `mm:ss`) |
| `YN` | INTEGER 0/1 | |
| `DMS` | REAL, decimal degrees | |

**Units** from the file's `UNIT` row, per column (mixed units in one file are fine):
1. **Parse** the unit string with the hangtu alias table, then pint (P00 §4.2), case-sensitively. AGS spellings (`DegC`, `degC`, `Bar`, `ohm m`, `uS/cm`, `Mg/m3`, `kN/m3`) are added to `aliases.yaml`. A string pint reads without an alias is accepted with finding `U002` instead of a `UserWarning`.
2. **Expected dimension:** for a heading in a standard dictionary (4.2, or the file's version for headings 4.2 removed; §6), the dimension of its dictionary unit; for a user-defined heading, the dimension of its own unit.
3. **Canonical unit:** the dictionary unit for a heading in a standard dictionary. They're all SI and match the P00 canonical units (m, mm, kPa, kN/m³, Mg/m³, m/s, %, deg). For a user-defined heading, the P00 canonical unit with the same dimension, or else SI base units.
4. **Conversion:**
   - file unit understood, dimension matches → converted, `status = converted`;
   - **pcf** (P00 §4.3 #1) resolved by the expected dimension: density → Mg/m³, unit weight → kN/m³. Finding `U002` (info). In a user-defined heading, where nothing says which, the column isn't converted: `U001`;
   - **ton** (SPEC §2.2 and the draft's "ton" rule): explicit strings directly; a bare `ton`/`t` follows the file's unit system, from the length unit of `LOCA_GL` (else `GEOL_TOP`). Finding `U002`;
   - unit unknown or ambiguous → canonical column NULL, raw kept, `U001` (error);
   - dimension doesn't match the dictionary (e.g. `kPa` in a depth heading) → canonical column NULL, raw kept, `U004` (error);
   - a numeric heading with an empty unit, where the dictionary gives one → canonical column NULL, raw kept, `U003` (warning). Where the dictionary gives none (counts such as `ISPT_NVAL`), it's stored as is.
5. **Never guessed** (SPEC §2.2): a column is converted only from what the file declares, read through the dictionary.
- SPT N and other counts are never converted (P00 §4.3 #2).
- The vertical datum is a project setting (`meta_project`), not read from the file; AGS4 has no field for it (draft, "Units on ingest" #3).

## 8. Value flags
As decided in SPEC §6.2:
- Blank → NULL, no flag.
- `NP` → NULL + `NP`; `Dry` → NULL + `DRY`; refusal text in `ISPT_NVAL`/`ISPT_REP` → value kept + `REFUSAL`; `<x` / `>x` → `x` kept + `LT` / `GT` (with `bound`); `#x` (`GRAG_PDEN` "assumed") → `x` kept + `ASSUMED`.
- Anything else in a numeric column → NULL + `OTHER` + `T001` (info), with the text kept in `value_flag.text`.
- The recognized strings live in `src/hangtu/ags/value_flags.yaml`, matched case-sensitively after trimming spaces.
- **Refusal:** an `ISPT_REP` with a blows/penetration pair (`25/75 50/75`) means the test drive wasn't completed, so `ISPT_NVAL` on that row gets `REFUSAL`, with its value as given. `50/75` in `ISPT_NVAL` itself keeps the blows (50). A complete test is reported as `N=12`.
- **Dates, times and coordinates** that don't match their format are NULL + `OTHER` + `T001` like any other text. Dates are read with the `UNIT` row's format (`mm` is a month before `T` and minutes after it); a `DT` heading with no format accepts ISO 8601 only. `T` values are summed from `hh`, `mm` and `ss` (hours may exceed 24). `DMS` accepts a leading `-` or a trailing `N`/`S`/`E`/`W`. `YN` accepts `Y` and `N` only.

## 9. Findings raised at ingest
| Rule | Severity | When |
|---|---|---|
| `V<rule>` | python-ags4's | Each python-ags4 finding, rule name kept (`V10b`, …); `FYI` → info, `Warning`/`General` → warning, the rest error. Results with no rule number: `VFYI`, `VWARNING`, `VGENERAL`, `VPROCESS` |
| `VLOG` | warning or error | A problem python-ags4 only logs (e.g. a duplicate heading it renamed) |
| `V000` | warning | `TRAN_AGS` missing or unrecognized; read as 4.2 |
| `M001` | info | Group or heading from an older version that 4.2 removed; kept under its own name (§6) |
| `U001` | error | Unit unknown or ambiguous; column raw only |
| `U002` | info | Unit resolved by convention (pcf, ton, pint without alias) |
| `U003` | warning | Numeric heading with no unit where the dictionary has one; column raw only |
| `U004` | error | Unit dimension doesn't match the dictionary; column raw only |
| `T001` | info | Unrecognized text in a numeric column; flag `OTHER` |

`U004` and `M001` are new; `qc.md` §4.1 adds them to the QC rule list. One finding per heading for `U` rules; one per cell for `T001`.

## 10. Errors
Written for engineers (SPEC §11):
- File not found, or not an AGS4 file (no `GROUP` line): what was read, and what an AGS4 file starts with.
- Parse failure: the line number and python-ags4's reason.
- Not UTF-8: the first line that can't be read, and to save the file as UTF-8. No other encoding is tried, because that would be a guess.
- An AGS3 file: hangtu reads AGS4 only.
- Database exists: `Project.open(...)` or `overwrite=True`.
- Schema version mismatch: the hangtu version that wrote it, and the re-ingest call.

## 11. Test files
Synthetic, in `tests/data/ags/` (SPEC §12.3), written by a script there from hand-typed SI data. Small: 3 locations, enough rows to hit every rule.
- `site_si.ags` (4.2, SI): PROJ, TRAN, UNIT, TYPE, ABBR, DICT (one user-defined group), LOCA, GEOL, SAMP, ISPT, LLPL, LNMC, GRAG, GRAT, PTST, FGHG, FGHS. Includes `NP`, `Dry`, a refusal, `<0.1`, `#2.65`, blanks, and two lab groups on one specimen.
- `site_us.ags`: the same data in US units (ft, in, psf, tsf, pcf in a density and a unit-weight heading, cm/s), with values hand-converted.
- `site_v404.ags` (4.0.4): the same locations, with `IPRG`/`IPRT` in place of `FGHG`/`FGHS`, a removed `RUCS` heading, and the old unit spellings (`degC`, `Bar`).
- `defects.ags`: one case per ingest rule in §9 except `M001`, plus an orphan sample.
All but `defects.ags` pass python-ags4 validation with no errors.

## 12. Acceptance criteria
1. **Twin files:** `site_si.ags` and `site_us.ags` give identical canonical tables (values to 1e-9 relative), identical flags and identical keys. Not compared: `_line`, and the `UNIT`, `TYPE` and `DICT` groups, which describe the file rather than the data.
2. **Raw fidelity:** every raw cell equals the file's text, and `_line` points at its DATA line.
3. **Older versions:** `site_v404.ags` gives the same canonical tables as `site_si.ags` for the groups both have; `IPRG`/`IPRT` and the removed `RUCS` heading are kept under their own names, typed and in SI from the 4.0.4 dictionary, each with `M001`; `degC` and `Bar` convert without `U` findings.
4. **Keys:** every child row in the good files has its keys; `LLPL` and `LNMC` on one specimen share `specimen_id`; the orphan in `defects.ags` has NULL `sample_id` and a `V10` finding.
5. **Units:** pcf resolves to Mg/m³ in a density heading and kN/m³ in a unit-weight heading; every `U001`–`U004` case in `defects.ags` raises its finding, leaves the canonical column NULL and keeps the raw text.
6. **Flags:** each recognized string gives its flag and value/bound; unrecognized text gives `OTHER` + `T001`; blank gives NULL with no flag.
7. **Findings:** each rule in §9 is raised by `defects.ags` (`M001` by `site_v404.ags`, since a removed group needs an older version), with group, heading and line.
8. **Open:** `Project.open` reads back the same tables; a changed source file warns; a schema mismatch errors; `from_ags` on an existing database errors without `overwrite=True`.
9. **Atomic:** a parse failure leaves no database file and no existing database changed.
10. **Read-only SQL:** `p.sql()` rejects a write.
11. **Quiet:** ingesting the good files raises no Python warnings and prints nothing.

## 13. Open questions
1. Research items kept from the draft, not blocking: pcf in density headings in real US files (#5), nominal vs 152.4 mm SPT penetrations (#6). Ingest converts what the file declares either way.
