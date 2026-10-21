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

## Spec

The rules live in the data-layer specs; this section lists what changes and why.

### Changes
- **SPEC §7, Extension tables:** "datum/CRS" becomes "the project's vertical datum and where it came from (a setting, or `LOCA_DATM`); horizontal CRS". AGS has a vertical datum heading, but no project-level one.
- **`docs/data/ingest.md` §2, Project settings:** where `vertical_datum` comes from (Decision 1), and that `p.settings` shows its source.
- **`docs/data/ingest.md` §7:** the last bullet ("The vertical datum is a project setting … AGS4 has no field for it") becomes a short **Vertical datum** paragraph: when `LOCA_DATM` is read (Decision 2), the datum table (Decision 3), and that elevations are never converted between datums.
- **`docs/data/qc.md` §4.2:** L006 is reworded ("No vertical datum is known for the project"), and its message says why the file's `LOCA_DATM` wasn't used, where there is one. New **L007**, warning, "Vertical datums disagree" (Decision 4). **§8:** `qc_defects.ags` cases for L007 and the L006 reasons. **§9 #2:** the good files' info findings no longer include `L006`.
- **`docs/plots/P00-framework.md` §3** (the `vertical_datum` setting) and **§7** (labels): a known datum is stored and labeled by its short name; the data's datum may come from the file.
- **`src/hangtu/qc/rules.yaml`:** L006 retitled, L007 added.
- **New `src/hangtu/vertical_datums.yaml`** and **`ht.add_vertical_datum()`**, with a docs site reference entry (`docs/site/reference/`).
- **`sandbox/TODO_ht.md`:** item 10 marked done at the close-out.

### Decisions
1. **Where the project's datum comes from**, in this order:
   1. `vertical_datum=` passed to `from_ags`, or `p.settings.vertical_datum` set later. Source: `setting`.
   2. The file's `LOCA_DATM`, when Decision 2 allows it. Source: `LOCA_DATM`.
   3. `ht.settings.vertical_datum` at ingest. Source: `setting`.

   **The file comes before the session setting.** A session's datum is often left over from the last project, while the file's is a fact about this file. An explicit argument still wins, because the engineer may know the file is wrong. The source is stored in `meta_project` next to the setting, and `p.settings` shows it (`vertical_datum='CGVD28'  # from LOCA_DATM`).
2. **`LOCA_DATM` is read only when all of these hold** for the holes with a `LOCA_GL`:
   - every one has a `LOCA_DATM`;
   - none has a `LOCA_LOCZ` (otherwise `LOCA_DATM` may be the local level's datum);
   - they all name the same datum (after Decision 3's matching);
   - that datum is in the datum table.
   Otherwise no datum is taken from the file, and L006 says which condition failed: it names up to 10 holes with a blank `LOCA_DATM` or a `LOCA_LOCZ`, or the unknown name with the `ht.add_vertical_datum()` call. Holes with no `LOCA_GL` don't count: their datum doesn't affect an elevation.
3. **The datum table** (`vertical_datums.yaml`, read like `aliases.yaml`). Each entry has a short name (the key, as EPSG abbreviates the datum), `name` (EPSG's full name), `epsg` (the EPSG datum code) and `spellings` (other ways files write it). It starts with the datums US, Canadian and UK files use:

   | Short name | EPSG name | EPSG datum code |
   |---|---|---|
   | `NAVD88` | North American Vertical Datum 1988 | 5103 |
   | `NGVD29` | National Geodetic Vertical Datum 1929 | 5102 |
   | `CGVD28` | Canadian Geodetic Vertical Datum of 1928 | 5114 |
   | `CGVD2013` | Canadian Geodetic Vertical Datum of 2013 | 1127 |
   | `ODN` | Ordnance Datum Newlyn | 5101 |

   The codes and names are checked against epsg.io in the build. Plain `MSL` isn't listed: mean sea level isn't one datum without a place and an epoch. A user who means a particular one adds it.
   - **Matching:** a name matches an entry when it equals the short name, the EPSG name or one of the spellings, compared case-insensitively and ignoring spaces, `-` and `_` (`NAVD 88`, `navd-88`). Only names in the table match. There's no fuzzy matching, so `NAVD1988` matches only if it's listed as a spelling.
   - **Stored as the short name**, so labels read `Elevation (ft, NAVD88)` whatever the file wrote.
   - **`ht.add_vertical_datum(short_name, *, name, epsg=None, spellings=())`** adds an entry for the session, as `ht.add_unit_alias` does. A short name already in the table is an error.
   - **A setting not in the table is accepted as written** (a local "Site datum"), with a `HangtuHint` naming `ht.add_vertical_datum()`. That's an explicit statement by the engineer, and hangtu doesn't second-guess it. Only reading the *file* needs the table.
4. **L007 (warning)**, one finding for the project, group `LOCA`, heading `LOCA_DATM`, no line. It is raised when either:
   - holes with a `LOCA_GL` and no `LOCA_LOCZ` name different datums: the message lists each datum with its hole count and up to 5 holes; or
   - the project's datum comes from a setting, and `LOCA_DATM` (same holes) names a different one: the message names both and the holes.
   Names are compared after Decision 3's matching. A name not in the table is compared by its text, normalized the same way, so `NAVD88` against `NAVD 88` is no finding, but `NAVD88` against `North American Vertical Datum of 1988` is one unless that is a listed spelling (it will be). Holes with a `LOCA_LOCZ` are left out, since their `LOCA_DATM` may be a local datum. When holes disagree, no datum is taken from the file, so L006 fires too. That's right, because both are true.
5. **No datum conversion and no per-hole datum.** Elevations are `LOCA_GL` as written. Mixed datums stay a "Later" item (SPEC §1.3).

### Acceptance criteria
1. **From the file:** `site_si.ags`, `site_us.ags` and `site_v404.ags` gain `LOCA_DATM` = `NAVD88` in every hole. Ingested with no setting, the project's datum is `NAVD88` from `LOCA_DATM`, `p.spt()` carries it in `df.attrs["vertical_datum"]`, and QC raises no L006 or L007. The twins stay twins.
2. **Spellings:** `NAVD 88` in every hole is stored as `NAVD88`. An unknown name in every hole (`Anytown datum`) sets nothing, and L006 names it and shows `ht.add_vertical_datum`. After `ht.add_vertical_datum("ATD", name="Anytown datum")` and a new ingest, it's `ATD`.
3. **Conditions** (Decision 2), each from a small file in `tmp_path` or a case in `qc_defects.ags`: a hole with a blank `LOCA_DATM`, a hole with a `LOCA_LOCZ`, two datums. Each sets nothing, and L006's message names the reason and the holes.
4. **Order** (Decision 1): `from_ags(..., vertical_datum="NGVD29")` on a file with `NAVD88` keeps `NGVD29` and raises L007, naming both. `ht.settings.vertical_datum = "NGVD29"` with no argument gives `NAVD88` from the file and no L007. Setting `p.settings.vertical_datum` later changes the source to `setting`.
5. **L007:** `qc_defects.ags` gives BH1–BH3 `NAVD88` and BH4 `NGVD29` (BH5 has no `LOCA_GL`, so it's ignored), giving one L007 listing both datums with their counts. L006 also fires there, with "holes name different datums" as its reason. A hole with a `LOCA_LOCZ` and a different `LOCA_DATM` raises no L007.
6. **Settings:** `ht.settings.vertical_datum = "navd 88"` stores `NAVD88`. `"Site datum"` is stored as written, with a `HangtuHint`. `ht.add_vertical_datum` with an existing short name raises an error that names it.
7. **Labels:** an elevation axis from a project whose datum came from `LOCA_DATM` reads `Elevation (m, NAVD88)`.
8. **Docs:** `ht.add_vertical_datum` has a reference entry (the docs test fails without one).

## Plan

Five build commits, each green (ruff and pytest). Regenerate the test files with `uv run python tests/data/ags/_make_files.py` whenever the generator changes. The spec commit already updated SPEC §7, `ingest.md` (§2, §7, §9 #12), `qc.md` (§4.2, §8, §9) and P00 §3 and §7; the build brings the code, config and tests up to them.

### 1. `vertical-datum: datum table and ht.add_vertical_datum`
- New `src/hangtu/vertical_datums.yaml`: the five datums of Decision 3, each with `name`, `epsg` and `spellings` (`NAVD 88`, `NAVD 1988`, `North American Vertical Datum of 1988`, and the like). Codes and names checked against epsg.io before the commit.
- New `src/hangtu/vertical_datums.py` (imports only `_config` and `errors`, so `_settings` can import it):
  - `_normalize(text)`: casefold, drop spaces, `-` and `_`.
  - `match(text) -> str | None`: the short name whose short name, `name` or a spelling normalizes to the same text; None otherwise.
  - `add_vertical_datum(short_name, *, name, epsg=None, spellings=())`: adds a session entry; a short name already in the table (after normalizing) raises `HangtuError` naming it. Docstring with an example, as `add_unit_alias`.
  - `_reset()`: back to the shipped table.
- `src/hangtu/_settings.py`: `_vertical_datum` stores `match(value)` when it matches, else the value as written with a `HangtuHint` naming `ht.add_vertical_datum()` (Decision 3). The hint is for assignment only: `Settings._validate` gains `hint=True`, and `ProjectSettings.__getattr__` reads a stored value back with `hint=False`.
- `src/hangtu/__init__.py`: export `add_vertical_datum`. `tests/conftest.py`: the autouse fixture also calls `vertical_datums._reset()`.
- `docs/site/reference/data.md`: `::: hangtu.add_vertical_datum` under Settings (AC 8; `tests/docs/test_site.py` fails without it).
- Tests (new `tests/test_vertical_datums.py`, `tests/test_settings.py`): matching (`NAVD 88`, `navd-88`, the EPSG name, a spelling → `NAVD88`; `NAVD1988` unlisted and `MSL` → None); `ht.settings.vertical_datum = "navd 88"` stores `NAVD88`, `"Site datum"` is kept with a `HangtuHint` (AC 6); `add_vertical_datum("ATD", name="Anytown datum")` makes `match("anytown datum") == "ATD"`; an existing short name raises an error naming it (AC 6).

### 2. `vertical-datum: LOCA_DATM in the test files`
Data only; nothing reads `LOCA_DATM` yet, so every test stays as it is.
- `tests/data/ags/_make_files.py`:
  - `LOCA` gains `("LOCA_DATM", "X", "")` with `NAVD88` in every hole, so `site_si.ags`, `site_us.ags` and `site_v404.ags` carry it (the 4.0.4 dictionary has the heading). `to_us()` leaves it alone, so the twins stay twins.
  - `qc_defects_groups()`: LOCA gains `LOCA_DATM`, `NAVD88` for BH1–BH3, `NGVD29` for BH4, blank for BH5 (no `LOCA_GL`). Line numbers don't move.
- Tests: `tests/ags/test_files.py` (python-ags4 still passes the good files and `qc_defects.ags`) and the twins test pass unchanged.

### 3. `vertical-datum: take the project's datum from LOCA_DATM`
- `src/hangtu/vertical_datums.py`: `from_locations(loca: pd.DataFrame) -> FileDatum`, a pure function shared by ingest and QC. It looks at holes with a `LOCA_GL` and returns `FileDatum(datum, reason, holes, names)`: `datum` is the short name when all of Decision 2's conditions hold, else None with `reason` one of `blank`, `local_level`, `different`, `unknown` (`None` when the file has no `LOCA_DATM` at all), the holes behind it, and `names` (each name the holes give, matched or normalized as L007 compares them, with its holes). The conditions are checked in that order, so a file with blanks and two datums reports the blanks.
- `src/hangtu/project.py`:
  - `from_ags`: the datum by Decision 1's order, from `result.canonical["LOCA"]`. `meta_project` gains `vertical_datum_source`: `"setting"`, `"LOCA_DATM"`, or null when no datum is known. An explicit `vertical_datum=None` counts as explicit.
  - `ProjectSettings.__setattr__("vertical_datum", …)` also writes the source `"setting"` (null for None). `__repr__` leaves the source out of the list and puts it as a comment on the datum's line (`vertical_datum='NAVD88',  # from LOCA_DATM`). A database built before this has no source key and reads as `"setting"`; no schema change (`meta_project` is key/value).
- Tests:
  - `tests/test_vertical_datums.py`: `from_locations` on small DataFrames, one per condition, with the holes named (AC 3); holes with no `LOCA_GL` are ignored; `NAVD 88` everywhere gives `NAVD88` (AC 2).
  - `tests/test_project.py`: on `site_si.ags`, no setting → `NAVD88` from `LOCA_DATM` (AC 1); `vertical_datum="NGVD29"` wins, source `setting`; `ht.settings.vertical_datum = "NGVD29"` loses to the file (AC 4); `p.settings.vertical_datum = "NGVD29"` later changes the source to `setting` (AC 4); the repr comment; `Anytown datum` in every hole (a file in `tmp_path`) sets nothing, and after `ht.add_vertical_datum("ATD", name="Anytown datum")` a new ingest gives `ATD` (AC 2).
  - `tests/ags/test_ingest_acceptance.py`: ingest.md §9 #12 on the three good files; `p.spt()` carries `df.attrs["vertical_datum"] == "NAVD88"` (AC 1).
  - `tests/qc/test_qc_acceptance.py`: the good files' allowed info findings no longer include `L006` (qc.md §9 #2).

### 4. `vertical-datum: L006 says why, L007 when datums disagree`
- `src/hangtu/qc/rules.yaml`: L006 retitled "No vertical datum is known for the project"; new L007, "Vertical datums disagree", warning.
- `src/hangtu/qc/_locations.py` (module docstring: L001 to L007):
  - L006: unchanged when a datum is set. Otherwise the message adds the reason from `from_locations(data.table("LOCA"))`: up to 10 holes with a blank `LOCA_DATM` or with a `LOCA_LOCZ`, "holes name different datums", or the unknown name with `ht.add_vertical_datum("…", name="…")`.
  - L007 (Decision 4): one finding, group `LOCA`, heading `LOCA_DATM`, no line, from `FileDatum.names` (holes with a `LOCA_GL` and no `LOCA_LOCZ`): more than one name → each with its hole count and up to 5 holes; else, when `vertical_datum_source` is `setting` and the one name differs from the project's datum (both through `match`, or normalized text) → both named, with the holes. Checked = 1, as L006.
- `tests/qc/conftest.py`: a `loca_datum(*rows)` helper, rows as (`LOCA_ID`, `LOCA_GL`, `LOCA_DATM`, `LOCA_LOCZ`).
- Tests (`tests/qc/test_locations.py`, `test_qc_acceptance.py`):
  - `qc_defects.ags`: one L007 naming `NAVD88` (3 holes) and `NGVD29` (1 hole, BH4), group `LOCA`, heading `LOCA_DATM`; L006 with "holes name different datums" (AC 5). The rule parameter list gains `("L007", …)`, and the cascade list notes L006 with L007.
  - Small files: a blank `LOCA_DATM`, a `LOCA_LOCZ`, an unknown name, each giving L006 with its reason and holes and no L007 (AC 3, AC 2); `vertical_datum="NGVD29"` on `NAVD88` holes → L007 naming both (AC 4); `ht.settings.vertical_datum = "NGVD29"` with `NAVD88` holes → no L007 (AC 4); a hole with a `LOCA_LOCZ` and another datum → no L007 (AC 5); `NAVD 88` against a `NAVD88` setting → no L007.
  - The existing `test_l006_once_per_project` keeps working on a small file with no `LOCA_DATM`, since `qc_defects.ags` now gives a reason.

### 5. `vertical-datum: elevation labels, docs, close out`
- `tests/plot/test_profile.py` (or `test_profile_acceptance.py`): `ht.plot.profile()` on `p.spt()` from `site_si.ags`, ingested with no datum setting, in elevation reads `Elevation (m, NAVD88)` (AC 7). No code change expected: the datasets already carry the stored datum.
- `docs/site/guides/ags-and-qc.md`: one sentence: the datum comes from `LOCA_DATM` when every hole names the same known datum, and `vertical_datum=` overrides it.
- `tests/data/ags/README.md`: `qc_defects.ags` lists L006/L007 by their `LOCA_DATM` case instead of "L006 always"; the good files have `LOCA_DATM` `NAVD88`.
- `CLAUDE.md` status paragraph: `vertical-datum` done; `qc-review` next.
- `sandbox/TODO_ht.md` (ignored by git, so not committed): item 10 marked done.
