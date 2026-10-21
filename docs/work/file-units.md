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
