# QC review: accepted findings and the D007 rounding tier

## Intent

### Goal
Let an engineer record which findings they have reviewed and accepted, with a reason, so that a reviewed file's report gets shorter and shows only what is still open. Split D007 so that specimen depths a few centimeters out (unit rounding) don't bury the real linking errors.

### Why
- On a real file, several findings are correct by the rule but expected on that site, and there's no way to say so. They come back on every run:
  - L005 on a valley site (22 hits): ground levels really do differ from nearby holes.
  - D003/D004 on a velocity profile (user-defined group) run to 30 m for Vs30, below the boring's final depth.
  - descriptions kept as printed in the source log.
  A report that never gets shorter stops being read.
- D007 raised 55 findings, and 40 were ft→m rounding in lab tables (2 to 8 cm). The 15 real linking errors (12 to 37 m out) were among them, and hangtu found a real bug in the file writer this way. Both kinds are useful, but not at the same severity.

### Constraints
- **The findings don't change.** An accepted finding stays in `report.findings` with its severity, plus `accepted` (True/False) and `reason`. The printed summary and `report.summary()` show open and accepted counts, and `to_csv` writes both columns. Hiding a finding would break "never drop data silently" for QC.
- **Every entry has a reason.** An entry without one is an error.
- **Entries are matched on content, not file lines**, since lines move between revisions of a file: `rule_id`, and optionally `loca_id`, `group`, `heading` and `depth`. Leaving keys out makes an entry broader:
  - all keys: one finding (`depth` as a quantity string, `"12.5 ft"`);
  - no `depth`: every finding of that rule in that hole (and group and heading, if given);
  - `rule_id` + `group`: every finding of that rule in that group (D003 on `VSPR`);
  - `rule_id` alone: the whole rule on this site (L005 on a valley site). This differs from disabling the rule: the findings are still listed and counted, as accepted.
- **An entry that matches nothing is reported**, not ignored. It may be stale after the file was fixed.
- **Errors as for overrides** (qc.md §2): a file that isn't there or isn't YAML, an unknown key, an unknown rule ID, a depth without a unit.
- Entries are passed to each call, not stored with the project, as overrides are (qc.md §3.3).
- **D007/D008:** two rule IDs, one severity each, so each keeps the normal override behavior. D007 (warning) for offsets beyond a rounding tolerance (default 0.1 m). D008 (info), "Specimen depth just outside its sample, likely rounding", for offsets between `depth_tolerance` (0.01 m) and the rounding tolerance.
- The twin files stay QC-clean. `qc_defects.ags` gains a 5 cm and a 0.30 m specimen offset.

### Out of scope
- Changing L005 (slope-aware neighbors) or D003 (geophysical profiles, PMT probe center). These go to `docs/TODO.md` as research items. Accepted findings cover the real-file cases now.
- A tool that writes the accepted-findings file from a report (decision 5).
- QC level 2 (SPEC §9.1).
- The other items from the same review: `file-units` and `vertical-datum`.

### SPEC sections touched
- SPEC §9.2: reviewed findings can be accepted per call, with a reason, and stay in the report.
- `docs/data/qc.md` §2 (API, errors), §3 (the accepted-findings file), §4.4 (D007, D008), §5.1–5.3 (columns, summary), §8 and §9; `src/hangtu/qc/rules.yaml`; the docs site's QC reference.

### Decisions (intent review, 2026-10-21)
1. **Accepted findings have their own argument and YAML file**: `p.qc(accepted="site_x_accepted.yaml")`, or a list of dicts. Rules say how to check, and accepted findings say what a reviewer decided about this file. They change at different times, and a reviewer may want to send one without the other.
2. **A depth matches within one fixed tolerance**, 0.05 m by default, whatever precision the entry is written with. Practitioners write depths with inconsistent precision, even within one data set, and the implied precision means little. The default can be tuned with use.
3. **Stale entries are shown in a `report.accepted` DataFrame**, one row per entry with its `matches` count, and the printed summary says when any match nothing ("2 accepted entries match no finding: report.accepted"). They aren't findings, since they're about the review file, not the AGS file. An entry for a disabled rule is shown as such, not as stale.
4. **D007 holds both thresholds** (`depth_tolerance: 0.01 m`, `rounding_tolerance: 0.1 m`), and D008 reads them. D008 is the lower band of D007's check, so its bounds belong to it. Overriding D008's severity or disabling it works as for any rule.
5. **A helper that writes entries from a report** (`report.accept(rows, reason=...)`) is out of scope. It is TODO #27. The broad entries cover the real-file cases, and the docs page shows how to build the list from `report.findings` in pandas.

## Spec

The rules live in `docs/data/qc.md`; this section lists what changes and why.

### Changes
- **SPEC §9.2:** a new bullet: *a reviewer can accept findings, each with a reason, in a YAML file passed per call (`p.qc(accepted=...)`). Accepted findings stay in the report, marked, and an entry that matches nothing is shown.*
- **`docs/data/qc.md` §2:** `accepted=` in the API block, and the new errors (Decision 6).
- **`docs/data/qc.md` new §3.4, Accepted findings:** the file, the keys and matching (Decisions 1–3).
- **`docs/data/qc.md` §4.4:** D007 is offsets beyond `rounding_tolerance` (warning). New D008 (info) is offsets beyond `depth_tolerance` up to `rounding_tolerance` (Decision 7).
- **`docs/data/qc.md` §5.1:** `accepted` and `reason` columns. **New §5.4**, `report.accepted`. **§5.2:** D008's thresholds cell. **§5.3:** open and accepted counts. **`report.summary()`** gains `open` and `accepted` (Decision 5).
- **`docs/data/qc.md` §8:** the D007/D008 cases and an accepted-findings test file. **§9:** criteria below.
- **`src/hangtu/qc/rules.yaml`:** D007's `rounding_tolerance: 0.1 m`; D008.
- **Docs site:** the QC guide gets a section on accepting findings, including building entries from `report.findings` with pandas (intent decision 5). The reference entry for `p.qc` covers `accepted=`.
- **`sandbox/TODO_ht.md`:** items 11, 12 and 13 marked done at the close-out.

### Decisions
1. **The file.** A YAML list of entries, under a top-level `accepted:` key or as a bare list (as rule files may or may not have `rules:`). `accepted=` also takes the same list directly (a list of dicts).
   ```yaml
   accepted:
     - rule_id: L005
       reason: Valley site; ground levels follow the topography (site visit 2026-09).
     - rule_id: D003
       group: VSPR
       reason: Velocity profiles run to 30 m for Vs30, below the borings.
     - rule_id: D007
       loca_id: BH-12
       depth: 41.5 ft
       reason: Specimen depth checked against the lab sheet; sample depth is right.
   ```
2. **Keys.** `rule_id` and `reason` are required. `loca_id`, `group`, `heading` and `depth` are optional. A given key must equal the finding's (exactly, case-sensitive, like AGS keys). A key left out matches anything. `depth` needs `loca_id`, since a depth means nothing without its hole. `rule_id` is one rule (`V10a`); `V*` isn't accepted, since accepting every validation finding at once hides too much.
3. **Depth matching.** `depth` is a quantity string (`"41.5 ft"`, `"12.65 m"`), read with `units.parse_quantity` as a length. It matches a finding whose depth is within **0.05 m** (about 0.16 ft) of it, compared in meters. That tolerance is fixed: a module constant, given in the docs and in `report.accepted`'s docstring, and not configurable for now (intent decision 2). A finding with no depth never matches an entry with one.
4. **Several entries on one finding.** The finding takes the `reason` of the first matching entry in file order. Every entry counts every finding it matches in `matches`, so a broad entry behind a specific one still counts and isn't shown as stale.
5. **The report.**
   - `report.findings` gains `accepted` (bool) and `reason` (blank when open), after `severity`. `severity` doesn't change.
   - `report.summary()`: `rule_id`, `title`, `severity`, `count`, `open`, `accepted`.
   - The printed summary counts open findings and adds the accepted ones:
     ```
     QC report: site.ags (AGS 4.2), hangtu 0.1.1, 2026-10-21 15:02
       open: 1 error, 3 warnings, 9 info · accepted: 24
       error    G003  Overlapping geology intervals              1
       warning  D007  Specimen depth outside its sample          2  (+1 accepted)
       warning  L005  Ground level is an outlier compared ...    0  (+22 accepted)
       ...
       2 accepted entries match no finding: report.accepted
       findings: report.findings · rules used: report.rules · save: report.to_csv("qc_report.csv")
     ```
     A rule with only accepted findings is still listed, so nothing disappears from view. The "match no finding" line appears only when there are such entries.
   - `report.accepted` (new §5.4): one row per entry, in file order. Columns: `rule_id`, `loca_id`, `group`, `heading`, `depth` (as written), `reason`, `matches`, `status`. `status` is `matched`, `no match` or `rule disabled`. It's an empty DataFrame with those columns when `accepted=` isn't given.
   - `to_csv`: the findings file has the two new columns. The rules file's `#` header gains `# accepted: <path or "list">, <n> entries, <m> match no finding`, so a report sent on its own says a review file was used. `report.source` gains `accepted` (the path, `list`, or blank).
6. **Errors** (SPEC §11), raised before any rule runs, in the style of qc.md §2: a file that isn't there or isn't YAML; not a list of mappings; a missing or blank `reason` or `rule_id`; an unknown key (lists the six); an unknown rule ID (lists the IDs); `depth` without `loca_id`; `depth` with no unit or not a length. Each names the entry by its position and `rule_id` ("accepted entry 3 (D007): …").
7. **D007 and D008.** D007's `depth_tolerance` (0.01 m) and `rounding_tolerance` (0.1 m) set the bands. D008 has no thresholds of its own (intent decision 4).
   - offset ≤ `depth_tolerance`: nothing;
   - `depth_tolerance` < offset ≤ `rounding_tolerance`: D008, info, "Specimen depth just outside its sample, likely rounding". The message gives the offset and says it's within the rounding tolerance;
   - offset > `rounding_tolerance`: D007, warning, as today.
   - `rounding_tolerance` below `depth_tolerance` is an error that names both values.
   - Each rule still gives one finding per specimen, at its first row, and each can be disabled or have its severity changed on its own. Disabling D007 doesn't change D008's band.
   - `report.rules` shows D008's thresholds cell as `from D007: depth_tolerance = 0.01 m; rounding_tolerance = 0.1 m`.
   - `records_checked` for both is the number of specimens D007 checks.
8. **Accepted findings and "clean".** "QC-clean" in the acceptance criteria (no errors or warnings) counts all findings, accepted or not. Accepting is a reviewer's decision about a real file, not something the test files rely on.

### Acceptance criteria
1. **Matching:** on `qc_defects.ags`, an entry with only `rule_id: L005` marks BH4's L005 accepted. An entry with `rule_id`, `loca_id` and `depth` marks exactly one D007, and does so with the depth written in ft (`display_units="US"`) or m. A depth 0.04 m off still matches, and one 0.06 m off doesn't. An entry with a `group` matches only that group.
2. **Report:** accepted findings keep their severity and have `accepted` True and the entry's `reason`. Open findings have `accepted` False and a blank `reason`. `summary()` has `open` and `accepted` adding up to `count`. The printed summary shows open counts, the `(+n accepted)` notes and the "match no finding" line, as in Decision 5.
3. **Stale entries:** an entry that matches nothing has `status = "no match"` in `report.accepted` and is counted in the printed line. An entry for a rule disabled by `rules=` has `status = "rule disabled"`. A broad entry behind a specific one counts its matches (Decision 4).
4. **Same report from a file and a list:** `accepted="file.yaml"` and the same entries as a list give the same report. With and without a top-level `accepted:` key give the same result.
5. **Errors:** each error in Decision 6 is raised with its message, naming the entry.
6. **CSV:** `to_csv` writes `accepted` and `reason`, reads back with `pd.read_csv`, and the rules file's header has the `# accepted:` line.
7. **D007/D008:** `qc_defects.ags` keeps its 0.30 m case (D007, warning) and gains a 0.05 m case in another hole (D008, info, no D007). `rounding_tolerance: "0.5 m"` turns the 0.30 m case into D008. Disabling D008 leaves the 0.05 m case unreported. `rounding_tolerance` below `depth_tolerance` raises the error.
8. **Good files** stay QC-clean, and their info list (qc.md §9 #2) is unchanged by this unit.
