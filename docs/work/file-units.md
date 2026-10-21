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
