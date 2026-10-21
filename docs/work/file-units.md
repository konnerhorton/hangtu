# File units: units the file defines

## Intent

### Goal
Read units the way the file defines them. A user-defined heading whose unit hangtu doesn't understand, but which the file's `UNIT` group defines, keeps its numbers as written instead of being dropped. `kN/mm` and `um` join the built-in aliases.

### Why
- hangtu 0.1.0 on a real 4.1.1 file raised U001 (error) on `%/log cycle`, the swell potential in a user-defined group (`RSWL_HSP`, `_HSPX`, `_HSPY`, `_VSP`). The file defines the unit in its `UNIT` group ("percent strain per log cycle of stress"), which AGS allows: a file may use any unit its `UNIT` group defines. The four columns ended up raw only, NULL in the canonical table.
- `kN/mm` and `um` gave four U002 notes on a file with nothing wrong in it. pint reads both correctly (kilonewton per millimeter, micrometer), but they aren't in `aliases.yaml`.
- hangtu reads each heading's `UNIT` row, but never reads the `UNIT` group (`UNIT_UNIT`, `UNIT_DESC`), so it can't tell a unit the file defines from a typo.

### Constraints
- **Never guess a unit** (SPEC §2.2, §2.6). A file-defined unit hangtu doesn't understand isn't converted or interpreted. Its numbers are stored as written, with `meta_heading.status = file_unit`, and `df.attrs["units"]` carries the file's string. A new info finding `U005` names the heading, the unit and the `UNIT_DESC`, and says the values are kept unconverted.
- **User-defined headings only.** A standard-dictionary heading has a fixed canonical unit, so an unknown unit there stays U001 even when the `UNIT` group defines it.
- An unknown unit that the `UNIT` group doesn't define stays U001.
- Plots already label a unit they can't parse as written (`x (%/log cycle)`) and don't convert it, so a `file_unit` column needs no plot change. Checked: no warning is raised, even with `display_units="US"`.
- `um` → micrometer and `kN/mm` → kilonewton / millimeter in `aliases.yaml`. Neither clashes with another unit.
- The twin files stay twins and QC-clean.
- **AGS 4.2 RUCS headings** (`RUCS_ESEC`/`ETAN`/`EAVG`/`MUS`/`MUT`/`MUAV`): one ingest test confirms they're typed and converted with no M001. hangtu has no RUCS-specific code, so this should need no code change.

### Out of scope
- Converting a file-defined unit, or reading a meaning out of `UNIT_DESC`.
- Checking that every unit in `UNIT` rows is listed in the `UNIT` group. python-ags4 already does that (AGS Rule 15).
- The other items from the same review: `vertical-datum` and `qc-review`.

### SPEC sections touched
- SPEC §2.2, if it says every numeric column is converted.
- `docs/data/ingest.md` §4 (the `file_unit` status), §7 (units, step 5) and §9 (`U005`); `docs/data/qc.md` §4.1; `src/hangtu/qc/rules.yaml`; `src/hangtu/units/aliases.yaml`.

### Decisions (intent review, 2026-10-21)
1. **A known unit with no P00 quantity kind keeps the file's unit.** A user-defined heading in `kN/mm` (a stiffness) isn't converted to SI base units (`kg / s ** 2`): its canonical unit is the file's string, as written, so a plot's label reads the way the file does. Units with a P00 kind (length, stress, …) are still converted. This changes ingest.md §7 step 4.
2. **`U005` is info.** The file declared the unit correctly, and the values are kept; a warning would put a correct file back in the report.

## Spec

The rules live in the data-layer specs; this section lists what changes and why.

### Changes
- **SPEC §2.2, Storage:** "Convert to SI on ingest" gains its two exceptions: a unit the file defines that hangtu doesn't know, and a known unit with no P00 quantity kind. Both are kept as written. **Unknown units:** "raw-only column + QC error `U001`", unless a user-defined heading's unit is defined in the file's `UNIT` group (`U005`).
- **`docs/data/ingest.md` §4:** `meta_heading.status` gains `file_unit` (a user-defined heading in a unit the file defines and hangtu doesn't know; numbers stored as written).
- **`docs/data/ingest.md` §7, Units:**
  - step 4: for a user-defined heading, the P00 canonical unit with the same dimension; **where no P00 kind has that dimension, the file's unit as written** (replaces "or else SI base units");
  - step 5 gains: *unit unknown, heading user-defined, unit listed in the file's `UNIT` group* → numbers stored as written, `status = file_unit`, `unit` = the file's string, `quantity` blank, finding `U005` (info);
  - the U001 bullet says it covers standard headings even when the `UNIT` group defines the unit, and its message then says so ("the file's UNIT group defines it as …, but LOCA_FDEP is a standard heading in m").
- **`docs/data/ingest.md` §9:** `U005`, info, "Unit defined by the file and kept as written; column not converted". **§11:** the new `defects.ags` cases. **§12:** criteria below.
- **`docs/data/qc.md` §4.1:** `U001`–`U005`.
- **`src/hangtu/qc/rules.yaml`:** `U005`, title "Unit defined by the file, kept as written", severity info.
- **`src/hangtu/units/aliases.yaml`:** `"um": "micrometer"` and `"kN/mm": "kilonewton / millimeter"`, in the first block (they aren't AGS dictionary units).
- **`sandbox/TODO_ht.md`:** items 8, 9 and 15 marked done at the close-out.

### Decisions
1. **A file-defined unit counts only when it's in the `UNIT` group**, matched exactly (`UNIT_UNIT`, case-sensitive, after trimming spaces), as AGS Rule 15 and SPEC §2.2 ("case-sensitive only") require. A unit that is in a `UNIT` row but missing from the `UNIT` group is still U001; python-ags4 reports the missing entry (Rule 15).
2. **Values are typed, not converted.** A `file_unit` column is a number column like any other: value flags (`<x`, `NP`, `T001`) apply as usual. Only the conversion is skipped.
3. **`df.attrs["units"]` carries the file's string**, so a plot labels the axis as the file writes it (`Swell potential (%/log cycle)`) and never converts it, whatever `display_units` is. Checked on 0.1.0: a unit string the plots can't parse is labeled as written, with no warning. A test keeps that true.
4. **A known unit with no P00 kind keeps the file's string** (intent decision 1). The column is `converted` with a factor of 1: the source and target units are the same, so the numbers don't change. `meta_heading.unit` is the file's string and `quantity` is blank. Only user-defined headings get here: a standard heading's canonical unit always comes from the dictionary.
5. **`U005` once per heading**, like the other `U` rules, at the heading's `UNIT` line. Its message names the heading, the unit, its `UNIT_DESC` and what was done: *`RSWL_HSP (RSWL)`: the unit "%/log cycle" isn't one hangtu knows, but the file's UNIT group defines it ("percent strain per log cycle of stress"). The values are kept as written, not converted.*
6. **AGS 4.2 `RUCS` headings** need no code, since ingest reads every heading through the 4.2 dictionary. The test writes a small 4.2 file in `tmp_path` rather than adding `RUCS` to the twin files. That would need a ksi alias and US values that aren't otherwise needed.

### Acceptance criteria
1. **File-defined unit:** in `defects.ags`, a user-defined heading in `%/log cycle`, defined in the `UNIT` group, is stored as written (`status = file_unit`, `unit = "%/log cycle"`), raises one `U005` quoting the `UNIT_DESC`, and no `U001`. `p.table()` gives its numbers, with `df.attrs["units"]` holding `%/log cycle`.
2. **Not defined:** a user-defined heading whose unknown unit is missing from the `UNIT` group still raises `U001` and stays raw only. `write_file` gains a way to leave one unit out of the generated `UNIT` group.
3. **Standard heading:** `LOCA_FDEP` in `Ft` (in the `UNIT` group) still raises `U001`, and the message says the `UNIT` group defines it but the heading is standard.
4. **Aliases:** a user-defined heading in `kN/mm` is converted with no `U002`, and its unit is `kN/mm` (not `kg / s ** 2`). One in `um` is converted to `m`, with no `U002`.
5. **4.2 RUCS:** a 4.2 file with `RUCS_ESEC` and `RUCS_ETAN` in GPa and `RUCS_MUS`/`RUCS_MUT` (no unit) is typed and converted, and raises no `M001` or `U` finding.
6. **Plot:** `ht.plot.profile()` on a `file_unit` column labels the axis with the file's unit, with `display_units` `"US"` and `"SI"`, and raises no warning.
7. **Good files:** unchanged and QC-clean; qc.md §9 #2 still holds.

## Plan

Five build commits, each green (ruff and pytest). Regenerate the test files with `uv run python tests/data/ags/_make_files.py` whenever the generator changes. The spec commit already updated SPEC §2.2, `ingest.md` and `qc.md`; the build brings the code and config up to them.

### 1. `file-units: um and kN/mm aliases`
- `src/hangtu/units/aliases.yaml`: `"um": "micrometer"` and `"kN/mm": "kilonewton / millimeter"`, in the first block.
- Tests (`tests/units/test_parse.py`): both read through the alias table with no `UserWarning`; `um` is a length.

### 2. `file-units: a unit no quantity kind covers keeps its string`
- `src/hangtu/ags/_units.py`: `_canonical()` returns the file's unit and string where `units._kind_of()` finds no P00 kind, in place of SI base units (Decision 4). The column stays `converted`, factor 1, `quantity` blank. The module docstring and ingest.md §7 step 4 already say so.
- Tests (`tests/ags/test_units.py`): `test_user_defined_heading_with_an_unusual_dimension_uses_si_base_units` becomes "keeps the file's unit": `kN/mm` stays `kN/mm` with quantity None and no finding (AC 4); `kg/m` still `kg/m`; `um` converts to `m` with no `U002` (AC 4).

### 3. `file-units: units the file's UNIT group defines (U005)`
- `src/hangtu/ags/_units.py`:
  - `resolve()` reads the file's `UNIT` group from `ags.tables["UNIT"]` into `{UNIT_UNIT.strip(): UNIT_DESC}` (empty when the group is missing) and passes it to `resolve_heading(..., defined=...)`.
  - New status `FILE_UNIT = "file_unit"`.
  - `_parse()` tells an *unknown* unit apart from an *ambiguous* one (pcf in a user-defined heading, a bare ton with no unit system), so only an unknown unit can become `file_unit`. A user-defined `pcf` heading stays `U001` even though the US file's `UNIT` group lists `pcf`.
  - Unknown unit, user-defined heading, unit in `defined` → `HeadingUnit(status=FILE_UNIT, unit=file_unit, quantity=None)` with `U005` (info), message as in Decision 5. Standard heading with the unit in `defined` → `U001`, and the message adds that the file's UNIT group defines it as "…", but the heading is standard, in the dictionary unit (AC 3).
- `src/hangtu/ags/_values.py`: no change expected. A `file_unit` column is typed like any number column (`HeadingUnit.convert` already passes it through unchanged), so value flags and `T001` apply (Decision 2). The `type_column` docstring names the status.
- `src/hangtu/qc/rules.yaml`: `U005`, "Unit defined by the file, kept as written", info. `src/hangtu/qc/_registry.py`: `U005` in `INGEST_RULES`.
- `p.diff()` (`qc/_diff.py`) shows a `file_unit` cell as `unchanged` and its value as stored (no quantity kind), with no code change. Its tests run on the project files, so the test is in step 4.
- Tests (`tests/ags/test_units.py`): `U005` with the `UNIT_DESC` in the message; unknown and not in `defined` → `U001` (AC 2); standard heading in `defined` → `U001` with the new sentence (AC 3); `pcf` in a user-defined heading, in `defined`, → still `U001`; matching is exact (`" %/log cycle "` trims, a case difference doesn't match).

### 4. `file-units: test-file cases`
- `tests/data/ags/_make_files.py`:
  - `UNIT_DESCRIPTIONS` gains `%/log cycle` ("percent strain per log cycle of stress"), `kN/mm` and `um` (`GPa` is already there).
  - `write_file(..., undefined_units=())` leaves those units out of the generated `UNIT` group (AC 2).
  - `defects_groups()`: `XUND` (already user-defined, no DICT) gains `XUND_SWEL` in `%/log cycle` (U005), `XUND_BLOW` in `blows/ft` (neither the alias table nor pint reads it), left out of the `UNIT` group (U001), `XUND_STIF` in `kN/mm` and `XUND_SIZE` in `um`. One `XUND` row: a second would raise V10a (no DICT keys), and a `<` flag in a `2DP` column V8, so flags on a `file_unit` column are tested in `tests/ags/test_values.py` instead.
- Tests:
  - `tests/ags/test_files.py`: python-ags4 reports the left-out unit (Rule 15) in `defects.ags`; the good files still pass.
  - `tests/ags/test_units.py`, `test_defects_file_unit_findings`: the four new headings' rules and statuses.
  - `tests/ags/test_ingest_acceptance.py`: `p.table("XUND")` gives `XUND_SWEL` as written with `df.attrs["units"]["XUND_SWEL"] == "%/log cycle"` and `meta_heading.status = file_unit`, one `U005`, no `U001` on it (AC 1); `XUND_ODD` blank with the raw text kept (AC 2); `LOCA_FDEP`'s `U001` message names the UNIT group (AC 3); `XUND_STIF` unit `kN/mm`, `XUND_SIZE` in m, no `U002` on either (AC 4); `U005` joins the AC 7 parameter list; the existing AC 1, 3 and 11 tests show the good files unchanged (AC 7).
  - `tests/qc/test_diff.py`: `XUND_SWEL` cells are `unchanged`, values as written.
  - `tests/qc/`: the defects report lists `U005` as info; qc.md §9 #2 and #3 still pass unchanged (AC 7).

### 5. `file-units: RUCS 4.2 headings, plot labels, close out`
- `tests/ags/test_ingest_acceptance.py`: a 4.2 file written in `tmp_path` with `write_file` (loaded as `test_files.py` loads `_make_files`), with LOCA, SAMP and a RUCS group holding `RUCS_ESEC` and `RUCS_ETAN` in GPa and `RUCS_MUS`/`RUCS_MUT` with no unit: typed, converted, no `M001` or `U` finding (AC 5, Decision 6). If it fails, the fix goes in this commit and the plan is updated.
- `tests/plot/test_profile.py`: `ht.plot.profile()` on `XUND_SWEL` (from `defects.ags`, with a depth column added) labels the axis `(%/log cycle)` with `display_units` `"US"` and `"SI"`, and raises no warning (AC 6, Decision 3).
- `CLAUDE.md` status paragraph: `file-units` done; `vertical-datum` and `qc-review` next.
- `sandbox/TODO_ht.md` (ignored by git, so not committed): items 8, 9 and 15 marked done.
