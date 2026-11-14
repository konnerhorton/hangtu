# GRAG fractions: read reported gradings into the gradation datasets

## Intent

### Goal
A sample whose grading is reported only as fractions in `GRAG`, with no `GRAT` curve, gets its fractions in
`p.grain_size_summary()` and `p.index_properties()`, so it can be classified (`uscs_symbol`), counted in fines
statistics and drawn where fractions are enough (P17). The engineer says once which fraction system the lab reported
in; hangtu never assumes it.

### Why
- **A real file lost most of its gradation data.** A 4.2 file extracted from a geotechnical report had 658 `GRAG`
  rows (gravel, sand, silt, clay, fines) and no `GRAT`. `p.grain_size_summary()` was empty, and `fines_content` was
  blank on every row of `p.index_properties()`: no lab USCS symbol, no clay activity, no fines statistics. Reports
  that print a summary table instead of curves are common, so any extractor working from them gives files like this.
- **Today only QC reads the fractions** (the fractions-sum check). The registry maps `GRAG_UC` and `GRAG_CC` and
  nothing else in `GRAG`; no dataset reads it.

### What the dictionary says (read before deciding)
AGS 4.2 defines the `GRAG` headings by size, with ISO 14688 boundaries:

| Heading | 4.2 description |
|---|---|
| `GRAG_VCRE` | Percentage of material tested greater than 63mm (cobbles) |
| `GRAG_GRAV` | … in range 63mm to 2mm (gravel) |
| `GRAG_SAND` | … in range 2mm to 63um (sand) |
| `GRAG_SILT` | … in range 63um to 2um (silt) |
| `GRAG_CLAY` | … less than 2um (clay) |
| `GRAG_FINE` | Percentage less than 63um |
| `GRAG_METH` | Test method |

But a lab reporting by ASTM D2487 (fines < 0.075 mm, gravel above 4.75 mm) puts its numbers in the same headings, and
`GRAG_METH` names the test (ASTM D6913, ISO 17892-4), which doesn't fix the reporting boundaries. Reading such a file as
ISO would put ASTM fines in an ISO column and give a wrong USCS symbol with no error. So the headings name a fraction,
and only the user can say what sizes it has (SPEC §2.6: never guess).

### Constraints
- **The system is stated, else no fractions** (intent review, decision 1). Without it, `GRAG`-only samples keep their
  rows with blank fractions, and one warning per call counts them and says how to state the system. The warning
  says that AGS defines the headings with ISO 14688 boundaries and that many labs report by ASTM in them.
- **Fractions are never converted between systems.** A fraction a system doesn't have, or that `GRAG` doesn't split
  finely enough, is blank. In particular `index_properties()` returns `astm_uscs` fractions, so `GRAG` reported by ISO
  14688 can't fill `fines_content` there (63 µm isn't 75 µm), though its clay can feed `clay_activity`.
- **No D-values without a curve.** `d10`, `d30` and `d60` stay blank; `uniformity_coefficient` and
  `curvature_coefficient` come from `GRAG_UC` and `GRAG_CC` where given.
- **A curve wins.** Where a specimen has `GRAT` points, everything comes from the curve as today, and `GRAG` isn't read
  for that specimen. Each row says which it came from.
- Never drop data silently; registry names only (SPEC §10.3); datasets don't stop on the file's data (`docs/data/datasets.md`
  §6.5).

### Out of scope
- The LDEN unit weight item from the same file (a user-defined heading); its own unit, once decided.
- A QC rule comparing `GRAG` with the curve on specimens that have both (to `docs/TODO.md`, with a trigger).
- Splitting `GRAG_VCRE` into cobbles and boulders, except where it is 0.
- The user's own fraction systems for `GRAG` (no rule says which heading fills which of their fractions).

### SPEC sections touched
- SPEC §2.6 (never guess), §4 (classification systems selectable; a setting, not a judgment, decision 4),
  §10.2–10.3 (datasets, registry).
- `docs/analysis/index-and-spt.md` §3.5 (fraction systems: how `GRAG` headings map to each system's fractions).
- `docs/data/datasets.md` §6.5 and §6.6 (rows from `GRAG`; the source column).
- `src/hangtu/columns.yaml` (the `GRAG` sources of the fraction columns; the new source column).

### Decisions (intent review, 2026-11-14)
1. **The fraction system of `GRAG` is stated by the user, else the fractions are left out with a warning.** Neither the
   AGS definition (ISO 14688) nor `GRAG_METH` is taken as the system: US labs often report ASTM fractions in ISO-defined
   headings, and a test method doesn't fix reporting boundaries.
2. **Two units.** This unit is the `GRAG` fractions only; the LDEN unit weight waits for its own decision (a heading map,
   possibly part of M16, or the extractor writing `LDEN_BDEN`).
3. **Which heading fills which fraction:**

   | System | From `GRAG` | Blank |
   |---|---|---|
   | `astm_uscs` | fines ← `GRAG_FINE` (else `GRAG_SILT` + `GRAG_CLAY`); sand ← `GRAG_SAND`; gravel ← `GRAG_GRAV`; cobbles and boulders ← 0 where `GRAG_VCRE` = 0 | cobbles and boulders where `GRAG_VCRE` > 0 |
   | `iso14688` | clay, silt, sand, gravel ← the heading of that name; cobbles and boulders as above | silt where only `GRAG_FINE` is given |
   | `aashto` | silt_clay ← fines as above; gravel ← `GRAG_GRAV`; boulders ← `GRAG_VCRE` | fine_sand, coarse_sand (`GRAG` doesn't split sand at 0.425 mm) |

   So from `aashto` `GRAG` the AASHTO group is blank wherever it needs the sand split; it is filled only where
   `aashto()` can decide on silt_clay and the limits alone (A-4 to A-7), if it can do that today.
4. **The system is a project setting,** `p.settings.grag_fraction_system = "astm_uscs"`, stored with the project like
   `vertical_datum`, so every dataset call reads it. There is no per-call argument: one file's `GRAG` was reported one
   way, and a setting keeps every dataset of the project consistent. A setting rather than a judgment: it is a fact
   about how the data was reported (like hammer efficiency, `docs/analysis/judgments.md` §5.10), not a choice of value.
5. **A source column**, `grading_source` (`"curve"` or `"reported"`), on `grain_size_summary()` and
   `index_properties()`, so the engineer can tell rows without D-values apart and filter on them. Checked against the
   registry in the spec step.
6. **`grain_size_summary()` gains one row per `GRAG` specimen with no `GRAT` points**, in file order after the
   curves, with the same columns; `p.grain_size()` (curve points) is unchanged. Its `fractions=` must match the
   `GRAG` system for those rows to be filled; otherwise they are blank and the warning says why.
7. **Test files:** a `GRAG`-only specimen (and one with both `GRAG` and `GRAT`) in the example site file through
   `_make_examples.py`, with invented values, and its US twin.

## Spec

The behavior lives in `docs/data/datasets.md` (§6.5, §6.6, new §6.13, §12, §13) and `docs/analysis/index-and-spt.md`
§3.5 (one paragraph pointing to it). This section holds the reasoning, the golden values and the review points; the
topic docs hold the rules.

### What changes in which doc
- **`docs/data/datasets.md` §6.13 (new), "Reported gradings (`GRAG`)":** the setting, which heading fills which
  fraction, the blank-`GRAG_VCRE` rule, the warnings. §6.5 and §6.6 read it.
- **§6.5 `p.grain_size_summary()`:** one row per `GRAG` specimen with no `GRAT` rows, after the curves;
  `grading_source`; an empty frame only when there is neither group.
- **§6.6 `p.index_properties()`:** `GRAG` specimens are grading candidates; the classification inputs from a reported
  grading; samples in order of `LNMC`, `LLPL`, `GRAT`, then `GRAG`; the missing-group warning names `GRAG` too.
- **§12, §13:** the test file `grag.ags`; acceptance criteria 17–24.
- **`docs/analysis/index-and-spt.md` §3.5:** a paragraph saying a reported grading's fractions come from `GRAG`
  through the project setting, with the link to datasets §6.13; `gradation()` itself is unchanged.
- **SPEC:** no change. §2.6 (never guess) and §4 (systems in config, selectable) hold as written; §4 already says
  hammer efficiency is data and a setting, the precedent for decision 4.

### The rule (datasets §6.13)
1. **The setting.** `grag_fraction_system`: `None` (default), `"astm_uscs"`, `"aashto"` or `"iso14688"`. A session
   setting like the others, so `from_ags(..., grag_fraction_system="astm_uscs")` stores it with the project and
   `p.settings.grag_fraction_system = ...` changes it later; it is read when a dataset is built, so no re-ingest. Any
   other value (a user's own system, a dict, a misspelling) is a `HangtuError` listing the three names and saying a
   user's own system can't be used for `GRAG`.
2. **Each heading means a size range in the stated system** `S`, made of `S`'s own fractions (`config/fraction_systems.yaml`):

   | Heading | `astm_uscs` | `aashto` | `iso14688` |
   |---|---|---|---|
   | `GRAG_FINE` | fines (< 0.075) | silt_clay (< 0.075) | clay + silt (< 0.063) |
   | `GRAG_SAND` | sand (0.075–4.75) | fine_sand + coarse_sand (0.075–2.0) | sand (0.063–2.0) |
   | `GRAG_GRAV` | gravel (4.75–75) | gravel (2.0–75) | gravel (2.0–63) |
   | `GRAG_VCRE` | cobbles + boulders (≥ 75) | boulders (≥ 75) | cobbles + boulders (≥ 63) |
   | `GRAG_SILT` | – | – | silt (0.002–0.063) |
   | `GRAG_CLAY` | – | – | clay (< 0.002) |

   `astm_uscs` and `aashto` have no clay–silt boundary, so there `GRAG_SILT` and `GRAG_CLAY` are read only as their
   sum, for a blank `GRAG_FINE`. Under every system a blank `GRAG_FINE` is `GRAG_SILT` + `GRAG_CLAY` where both are
   given (as QC P003 reads it).
3. **A requested fraction** `[lower, upper)`, in whichever system the dataset asks for, is:
   a. the sum of the headings whose ranges make it up exactly (one heading, or several next to each other), blank if
      any of them is blank;
   b. else 0, where it lies inside one heading's range and that heading is 0;
   c. else blank.

   Boundaries are compared exactly (they're the config's numbers). So `astm_uscs` and `aashto` share 0.075 mm and
   75 mm: an `astm_uscs` `GRAG` gives the `aashto` silt_clay and boulders, but not its sand split or its gravel
   (2.0 mm isn't a `GRAG` boundary in `astm_uscs`). `iso14688` shares none of the 0.075 and 4.75 mm boundaries, so an
   ISO `GRAG` gives no `astm_uscs` fraction but zeros. This is reading what the file says, not converting.
4. **A blank `GRAG_VCRE` counts as 0** where gravel, sand and fines (rule 2) are all given and add up to 100 within
   2 percentage points (QC P003's default tolerance). Otherwise a blank `GRAG_VCRE` is blank, and rule 3 leaves the
   fractions above it blank.
5. **Cu and Cc** are `GRAG_UC` and `GRAG_CC`; the D-values are blank.
6. **Which specimens:** a `GRAG` row is a reported grading where its specimen (the `GRAG` keys, which `GRAT` shares as
   its parent) has no `GRAT` row in the file, counted before `include_incomplete=` leaves any record out, so a curve
   whose points are incomplete doesn't silently turn into a reported grading. `grading_source` is `"curve"` or
   `"reported"`.
7. **Warnings**, one per kind per call:
   - **No system set** (rows kept, fractions blank): "3 gradings are reported only as fractions (GRAG), and their
     fractions are blank because the project's GRAG fraction system isn't set. AGS 4 defines these headings with ISO
     14688 boundaries (2 mm, 0.063 mm), but many labs report ASTM D2487 fractions (4.75 mm, 0.075 mm) in them. Set the
     system the lab used, for example p.settings.grag_fraction_system = "astm_uscs"."
   - **System differs from the one asked for** (`grain_size_summary(fractions=)` only): "3 gradings are reported as
     astm_uscs fractions (GRAG), so the aashto fractions with other boundaries are blank: fine_sand, coarse_sand,
     gravel." It lists only the fractions blank for that reason.
   - In `index_properties()`, an `iso14688` `GRAG` leaves `fines_content` and the USCS symbol blank: "3 samples'
     gradings are reported as iso14688 fractions (GRAG), so the USCS fractions (finer than 0.075 mm, …) and symbols
     are blank." `uscs()`'s own "no fractions" count for those rows isn't repeated.

### `index_properties()` from a reported grading
- **Choosing the specimen:** the grading candidates are the sample's `GRAT` specimens and its reported `GRAG`
  specimens, chosen by §6.6's rules 1–4 as one test. `grain_size_specimen_id` names it either way.
- **Returned fractions:** `astm_uscs` by rule 3, `fraction_system = "astm_uscs"`, D-values blank, Cu and Cc from rule 5.
- **USCS:** `uscs()` on those fractions. Its oversize is cobbles + boulders; where `GRAG_VCRE` > 0 those are blank in
  `astm_uscs` (rule 3c) but their sum is `GRAG_VCRE`, so `uscs()` is given that sum as the oversize (internally;
  the returned cobbles and boulders stay blank). Without it, `uscs()` would count blank oversize as 0 and classify the
  whole sample rather than the part finer than 75 mm.
- **AASHTO:** `aashto()` on the `aashto` fractions by rule 3. It already leaves the group blank only where a missing
  passing percentage could decide it, so a reported grading gets a group where fines and the limits are enough.
- **Activity:** the `iso14688` clay by rule 3, so only from an `iso14688` `GRAG` with `GRAG_CLAY`.

### Golden values (hand-worked; `grag.ags`, invented)
| Sample | `GRAG` | Limits | System | Expected |
|---|---|---|---|---|
| G1 | GRAV 22, SAND 45, FINE 33, VCRE blank | LL 32, PL 20 | `astm_uscs` | fines 33, sand 45, gravel 22, cobbles 0, boulders 0 (rule 4: 100); PI 12, A-line 0.73 × 12 = 8.76 < 12 → CL; fines > 12 % and sand > gravel → **SC**; AASHTO F = 33 ≤ 35 rules out A-1 (> 25) and A-3 (> 10), LL ≤ 40, PI ≥ 11 → **A-2-6**, GI = 0.01 (33 − 15)(12 − 10) = 0.36 → **0**; activity blank |
| G2 | GRAV 40, SAND 39, FINE 11, VCRE 10 | LL 30, PL 18 | `astm_uscs` | cobbles, boulders blank (3c); oversize 10 → fines 11 / 90 = 12.22 %, gravel 44.4 > sand 43.3; PI 12 > 0.73 × 10 = 7.3 → CL → **GC** (ignoring VCRE: fines 11 % → dual, no Cu → blank, so the two are told apart); AASHTO F = 12.2 → 12, PI 12 > 6 rules out A-1, not NP rules out A-3 → **A-2-6**, GI = 0.01 (12 − 15)(2) < 0 → **0** |
| G3 | GRAV 10, SAND 87, FINE 3, UC 8, CC 1.5 | – | `astm_uscs` | fines < 5 %, sand > gravel, Cu 8 ≥ 6, 1 ≤ Cc ≤ 3 → **SW**; D-values blank |
| G4 | GRAV 32, SAND 40, SILT 20, CLAY 8, VCRE 0 | LL 40, PL 28 | `iso14688` | `index_properties()`: fines, sand, gravel blank, cobbles and boulders 0 (3b), USCS blank with the ISO warning, AASHTO blank (F unknown); activity = 12 / 8 = **1.5**. `grain_size_summary(fractions="iso14688")`: clay 8, silt 20, sand 40, gravel 32, cobbles 0, boulders 0 |
| G5 | GRAV 22, SAND 45, SILT 25, CLAY 8 (FINE blank) | – | `astm_uscs` | fines **33** (SILT + CLAY) |
| G6 | GRAV 22, SAND 45, FINE 31.5, VCRE blank | – | `astm_uscs` | sum 98.5, within 2 → cobbles, boulders **0** |
| G7 | GRAV 20, SAND 45, FINE 30, VCRE blank | – | `astm_uscs` | sum 95 → cobbles, boulders **blank** |
| G8 | `GRAG` and a `GRAT` curve on one specimen | – | any | the curve's values, `grading_source = "curve"`; `GRAG` not read |

On G1, `grain_size_summary(fractions="aashto")` gives silt_clay 33, boulders 0 and fine_sand, coarse_sand and gravel
blank, with the second warning naming those three.

### Decisions (spec review, 2026-11-14)
8. **Rule 3 replaces decision 3's table with the general rule it follows.** On the system the user stated, the two
   give the same values; the rule also covers a dataset asking for another system, where a boundary is shared
   (`astm_uscs` and `aashto` at 0.075 and 75 mm). `index_properties()` needs exactly that for the AASHTO group. It
   refines decision 6 ("`fractions=` must match the `GRAG` system for those rows to be filled"): rows are filled where
   the boundaries match, and blank with a warning where they don't.
9. **Rule 4, a blank `GRAG_VCRE` is 0 when the rest adds up to 100.** Labs commonly leave the cobbles column empty
   when there are none; without the rule, every such row would have blank cobbles and boulders, and `aashto()`
   couldn't decide on boulders. The 2-point tolerance is P003's default, written into the spec rather than read from
   the QC settings, because a dataset doesn't take QC overrides.
10. **The oversize passed to `uscs()` internally** (G2), not a change to `uscs()`. `uscs()` treating a blank
    cobbles column as 0 is older behavior on curves too; a TODO item asks whether it should leave the symbol blank
    instead.
11. **Decision 7 revised: test data goes in a new `tests/data/ags/grag.ags`**, not in the example site file and
    not in the good files. The examples call `from_ags` without the setting in a dozen pages, and the good files are
    held to "no warnings"; a reported grading in either would raise the no-system warning in every one of them, or
    make every example set a setting that only one file needs. `grag.ags` (4.2, SI, passes python-ags4) holds G1–G8
    with `LLPL` where the table has limits; the site docs page on grain size gets a short paragraph on the setting.
12. **QC isn't changed.** A rule comparing `GRAG` with the curve on G8-like specimens goes to `docs/TODO.md`,
    triggered by the next file that has both.
13. **The good files already hold a reported grading** (found while planning, 2026-11-14): BH2-D1 has `GRAG` and no
    `GRAT`. Decision 11's reason holds for the examples (all their `GRAG` rows have curves) but not for the good
    files. So the good-file tests that build `grain_size_summary()` or `index_properties()` ingest with
    `grag_fraction_system="astm_uscs"`, BH2-D1 gets golden values (AC 24), and one test without the setting expects
    the warning. The twin files then check a reported grading in SI and US.

## Plan

Six build steps, each green. Steps 1, 2 and 6 on Sonnet; 3 to 5 on Opus (the rule, the classification inputs). Order:
1–2 (Sonnet), 3–5 (Opus), 6 (Sonnet), so each model's steps run in one session.

### 1. `settings: add grag_fraction_system` (Sonnet)
- `src/hangtu/_settings.py`: `_grag_fraction_system` validator, `None` or a name in `config/fraction_systems.yaml`;
  anything else (a dict, a path, an unknown name) is a `HangtuError` listing the three names and saying a user's own
  system can't be used for `GRAG`. Add it to `_VALIDATORS`.
- `src/hangtu/config/defaults.yaml`: `grag_fraction_system: null` with a comment.
- `src/hangtu/datasets/_frame.py` `Build.__init__`: `self.grag_fraction_system = stored.get("grag_fraction_system")`.
- `docs/plots/P00-framework.md` §3 settings table: the row.
- Tests: `tests/test_settings.py` (default `None`, each valid name, the error for `"unified"` and for a dict);
  `tests/test_project.py` (stored by `from_ags(..., grag_fraction_system=...)`; changed on `p.settings` and read by
  the next `Build` with no re-ingest). AC 17.

### 2. `tests: add grag.ags with reported gradings` (Sonnet)
- `tests/data/ags/_make_files.py`: `grag_groups()` writing `grag.ags` (4.2, SI): one hole, `LOCA`, `GEOL`, `SAMP`,
  `LLPL` on G1, G2 and G4, `GRAG` with G1–G8 exactly as the golden table, `GRAT` on G8 only (a four-point curve, as
  BH3-B1's). `GRAG_VCRE`, `GRAG_SILT`, `GRAG_CLAY`, `GRAG_UC`, `GRAG_CC` as headings. Invented values only.
- `tests/data/ags/README.md`: its row.
- Tests: the existing generator check (`tests/ags/test_files.py`) and the python-ags4 check cover the file; add it to
  their lists if they're explicit.

### 3. `grag-fractions: read GRAG headings as a stated system's ranges` (Opus)
- `src/hangtu/config/fraction_systems.yaml`: a `grag:` map per built-in system, heading → the fractions it spans
  (datasets §6.13 table), so the boundaries come from the systems' own entries and the config test checks them.
- `src/hangtu/datasets/_reported.py` (new):
  - `reported_specimens(build)`: the `GRAG` rows whose specimen has no `GRAT` row (before §7's filter), as specimen
    rows (`specimens(build, "GRAG", rows)`), with `GRAG_UC`, `GRAG_CC` and the headings as numbers.
  - `reported_fractions(frame, requested, stated)`: rules 1–3 and the blank-`VCRE` rule; returns the requested
    system's `<fraction>_content` columns and the names left blank because a boundary differs (for the warning).
  - The warning texts of §6.13 as functions, so steps 4 and 5 share them.
- Tests: `tests/datasets/test_reported.py`, on hand-built frames: G1, G3, G5, G6, G7 in `astm_uscs`; G1 asked as
  `aashto` (silt_clay 33, boulders 0, three blank and named); G4 in `iso14688`, and asked as `astm_uscs` (all blank
  but cobbles and boulders 0); `stated=None` gives all blank. Part of AC 18, 19.

### 4. `grag-fractions: reported gradings in grain_size_summary` (Opus)
- `src/hangtu/datasets/_lab.py` `grain_size_summary`: build from `GRAT` and `GRAG`; append one row per reported
  specimen after the curves, with blank D-values, Cu and Cc from `GRAG_UC`/`GRAG_CC`, fractions by step 3,
  `fraction_system` = the requested name, `grading_source`; the common filters act on them as on curves. With `GRAG`
  only, `p.grain_size()`'s "No GRAT group" warning isn't passed on; with neither, the warning names both.
- `src/hangtu/columns.yaml`: `grading_source` (text, `"curve"` or `"reported"`, checked against the registry);
  `GRAG.GRAG_FINE`, `GRAG_SAND`, `GRAG_GRAV`, `GRAG_VCRE`, `GRAG_SILT`, `GRAG_CLAY` in the fraction columns' `ags:`.
- `src/hangtu/project.py` `grain_size_summary` docstring: reported gradings, the setting, `grading_source`.
- Good-file fixtures: `tests/datasets/conftest.py` `fresh` and `tests/datasets/test_datasets_acceptance.py`
  `projects` ingest the good files with `grag_fraction_system="astm_uscs"` (decision 13); any other good-file caller
  of the two datasets that fails on the new warning does the same.
- Tests in `tests/datasets/test_grain_size_summary.py` on `grag.ags`: AC 18 (summary half), 19, 21, 22 (G8, and
  with its `GRAT` rows incomplete), 23; on the good files, BH2-D1's fractions and the no-system warning (AC 24,
  summary half); AC 15 still holds for the curves.

### 5. `grag-fractions: classify samples from reported gradings` (Opus)
- `src/hangtu/datasets/_index.py`: reported `GRAG` specimens join the grading candidates (one test with `GRAT` for
  rules 1–4, listed after `GRAT` in sample order); `_classify` takes the curves and the reported rows: `astm_uscs`
  fractions returned, `aashto` for `aashto()`, `iso14688` clay for `clay_activity()`, oversize = `GRAG_VCRE` for
  `uscs()` where cobbles and boulders are blank and `GRAG_VCRE` > 0; `grading_source`; the ISO warning; the
  missing-group message with `GRAG`.
- `src/hangtu/project.py` `index_properties` docstring.
- Tests in `tests/datasets/test_index_properties.py`: AC 20 (G1 SC A-2-6 0, G2 GC A-2-6 0, G3 SW, G4 blank with
  the warning and activity 1.5), 21, 22, 23; the good files' BH2-D1 ML, A-4, GI 0 (AC 24); the twin test (AC 2)
  passes with it. A test fixture with the classification inputs (oversize) is checked through the result, not
  internals.

### 6. `grag-fractions: document reported gradings; close out` (Sonnet)
- Site: `docs/site/guides/datasets.md` (a paragraph: gradings reported only as fractions, the setting, what stays
  blank), `docs/site/guides/ags-and-qc.md` (the setting among the project settings), and the grain size plot page
  if it describes `grain_size_summary()`. No internal references (the docs tests check).
- `CHANGELOG.md` Unreleased: reported gradings in `grain_size_summary()` and `index_properties()`, the setting, the
  `grading_source` column.
- `docs/TODO.md`: a QC rule comparing `GRAG` with the curve (trigger: the next file with both); whether `uscs()`
  should leave the symbol blank when cobbles or boulders are blank rather than count them as 0 (trigger: before M8's
  classification is next changed, or the next file with oversize).
- `STATUS.md`: the unit done; LDEN unit weight (item 2 of the file review) is next to decide.
- Whole suite (`uv run pytest -n 2 --dist loadfile`), ruff, mypy, `docs/prepare_site.py` and the strict site build.

