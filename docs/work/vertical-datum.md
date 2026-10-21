# Vertical datum: read LOCA_DATM

## Intent

### Goal
Take the project's vertical datum from the file when the file states it, and warn when the file and the project disagree. Today the datum comes only from `vertical_datum=` at ingest or `p.settings`, and L006 asks for it even when every hole names one.

### Why
- hangtu 0.1.0 on a real 4.1.1 file raised L006 ("the project's vertical datum isn't set"), although every hole had `CGVD28` in `LOCA_DATM`.
- `LOCA_DATM` is a standard heading. In 4.2 it is "Local vertical datum referencing system used" (4.0.3 to 4.1.1: "Local datum referencing system used"). `docs/data/ingest.md` §7 says "AGS4 has no field for it", which is wrong.
- When holes name different datums, their elevations can't be compared, and nothing in hangtu says so.

### What the dictionary says (read before deciding)
`LOCA_DATM` sits in a set of headings for a *local* system, next to the national one:

| Heading | 4.2 description |
|---|---|
| `LOCA_GREF` | National grid referencing system used |
| `LOCA_LREF` | Local grid referencing system used |
| `LOCA_DATM` | Local vertical datum referencing system used |
| `LOCA_LOCZ` | Level or start of traverse to local datum |
| `LOCA_GL` | Ground level relative to datum of location or start of traverse |

Read strictly, `LOCA_DATM` names the datum of `LOCA_LOCZ` (the level in the local system), not necessarily the datum of `LOCA_GL`, the elevation hangtu uses. In a file with only `LOCA_GL` filled, as in US practice and the file reviewed, the datum it names can only be `LOCA_GL`'s. In a UK file with both, `LOCA_GL` is usually to the national datum and `LOCA_DATM` belongs to `LOCA_LOCZ`. hangtu doesn't read `LOCA_LOCZ`. See decision 1.

### Constraints
- **Never guess** (SPEC §2.6). Use the file's datum only where the file says it unambiguously. Never pick one when holes differ.
- **An explicit setting wins.** `vertical_datum=` at ingest, or `p.settings.vertical_datum` later, is the project's datum. A file that disagrees raises a finding, but its datum is never used instead.
- **Where the datum came from is stored** (`meta_project`: `setting` or `LOCA_DATM`), so QC knows whether to compare, and a reader of the project can tell.
- **One severity per rule ID**, as decided for D007/D008 in `qc-review`, so each rule keeps the normal override behavior. L006 (info) stays "no datum known". A new L007 (warning) covers "datums disagree".
- The twin files gain `LOCA_DATM` and stay twins and QC-clean. L006 then no longer fires on them, so qc.md §9 #2's list of info findings changes.
- **Datum names are explicit** (decision 3): written as official sources (EPSG) write them, from a built-in table.

### Out of scope
- Converting between datums, or computing elevations per hole datum. A project with mixed datums is a SPEC §1.3 "Later" item (multiple datums).
- Horizontal reference systems (`LOCA_GREF`, `LOCA_LREF`) and `LOCA_LOCZ`.
- The other items from the same review: `file-units` and `qc-review`.

### SPEC sections touched
- SPEC §7 ("Extension tables for things AGS lacks: datum/CRS"): AGS has a vertical datum heading. The extension table holds the project setting and where it came from.
- `docs/data/ingest.md` §2 (project settings) and §7 (the datum paragraph); `docs/data/qc.md` §4.2 (L006, new L007) and §8, §9; `src/hangtu/qc/rules.yaml`; P00 §7 and the settings docs on where the datum comes from.

### Decisions (intent review, 2026-10-21)
1. **`LOCA_DATM` counts as `LOCA_GL`'s datum only where `LOCA_LOCZ` is blank.** Every hole with a `LOCA_GL` must have the same `LOCA_DATM` and a blank `LOCA_LOCZ`; then `LOCA_DATM` can't belong to a local level. Otherwise nothing is set, and L006 quotes the file's `LOCA_DATM` values as a hint. This narrows the 2026-10-20 decision ("LOCA_DATM defaults the project setting").
2. **A blank `LOCA_DATM` in any hole with a `LOCA_GL` means no datum is set.** A blank hole could be on another datum. L006 names the blank holes, so the user can fix the file and ingest again.
3. **Datum names come from a built-in table**, not from free text. `src/hangtu/vertical_datums.yaml` lists each datum by its short name as EPSG writes it (`NAVD88`, `NGVD29`, `CGVD28`, `CGVD2013`, `ODN`, …), with its EPSG code, its full name and the spellings accepted for it. `LOCA_DATM` is read only when it matches the table, and the short name is stored. A user can add a datum at run time, as `ht.add_unit_alias` adds a unit. An explicit setting not in the table (a local "Site datum") is still accepted, with an info note. No pyproj: it isn't in SPEC §12.1, and the table is all hangtu needs.
4. **No finding when the datum comes from the file.** The source is stored and shown with the project's settings and on elevation labels; a finding on every clean report would be noise.
