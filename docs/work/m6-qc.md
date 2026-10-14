# M6: QC level 1, report and diff

## Intent

### Goal
Check a project's data for integrity problems and report them to the engineer: `p.qc()` runs the level 1 rules (SPEC §9.1) over the canonical layer, adds the findings ingest already stored, and returns a report that prints a readable summary and exports to one flat CSV. `p.diff(group)` shows, cell by cell, what ingest did to each value: the file's text and unit, the SI value, the display value and any flag.

### Why
- It's the next Phase 2 unit (SPEC §1.3, §12.4 M6). Ingest (M5) stores the data and its own findings but has no way to show them except `p.sql("select * from finding")`.
- Engineers need to know what's wrong with a file before they plot it. A QC report they can send back to the data supplier is useful on its own, before any dataset exists.
- `diff()` is how an engineer checks a conversion they don't trust (pcf, ton, a mixed-unit column) without reading the database.
- The datasets (M7) depend on some of these rules: C001 decides which records are incomplete, and the geology and depth rules check the joins M7 will rely on.

### Constraints
- SPEC §9.2 (decided): rules (id, severity, thresholds) in YAML, overridable per project; QC computed on demand, only ingest validation persisted; findings export to one flat CSV (decision 2 adds a second file for the rules used); `p.diff(group)` compares raw and canonical.
- SPEC §7: rules read the canonical layer through `db.py` and join on surrogate keys, never AGS key columns. Every finding points at its source line.
- SPEC §2.6 and §8: thresholds are in SI and convert like any other quantity; depths and values in the report are shown in the project's display units, with the unit stated. Intervals use `top ≤ d < base` (§8.3).
- SPEC §11: messages say what is wrong, where (hole, depth, group, heading, line) and what to do.
- Starting rule list and thresholds: `docs/drafts/phase2-data.md` (Level 1 rules, Minimally useful fields), TODO #6 and #7. The spec step finishes them.
- No new dependency. Test files are synthetic.
- **Done when:** one defects-file test per rule (SPEC §12.4), the good test files give no warnings or errors, and the spec's acceptance criteria pass.

### Decisions (proposed, to settle in review)
1. **Where the spec lives:** `docs/data/qc.md`, a topic doc next to `ingest.md`. The QC sections of `docs/drafts/phase2-data.md` move there; the dataset notes stay for M7.
2. **API:**
   - `report = p.qc(rules=None)`: `rules` is a path to a YAML file or a dict that overrides the defaults (severity, thresholds, `enabled`) rule by rule.
   - `report.findings` is a DataFrame with the draft's columns (`rule_id, severity, group, loca_id, depth, heading, value, message, source_line`); `report.summary()` counts by rule and severity; `repr(report)` prints that summary.
   - `report.rules` is a table of the rule settings the run used (id, title, enabled, severity, each threshold with its unit). `report.to_csv(path)` writes the findings to `path` and the rules next to it (`<stem>_rules.csv`), so a report sent to a data supplier shows what it was checked against. This changes SPEC §9.2's "one flat CSV": the findings stay one flat file, with the rules as a second.
   - `p.diff(group, heading=None, changed_only=False)` returns one row per cell.
3. **Rule settings in YAML, rule logic in code.** Default settings ship in `src/hangtu/qc/rules.yaml`: per rule ID a `title`, `severity`, `enabled` and named `thresholds`. The checks live in `qc/rules.py`; a project can change settings but not add rules.
   - **Thresholds are quantity strings with units** (`depth_tolerance: 0.01 m`, `highest_liquid_limit: 150 %`), read by the hangtu unit parser, so an override can be given in any unit of the right dimension (`"0.05 ft"`; TODO #6). Counts take a plain number (`highest_spt_n: 100`).
   - Threshold names follow the CLAUDE.md naming rules (`highest_hydraulic_conductivity`, not `max`).
   - **Overrides** are a dict or a YAML file of the same shape, holding only what changes, merged into the defaults rule by rule: `p.qc(rules={"G002": {"thresholds": {"depth_tolerance": "0.05 ft"}}})`. An unknown rule ID or threshold name, a wrong dimension, a plain number where a unit is needed, or an unknown severity is an error, raised before any rule runs.
   - **Ingest rules** (V, U, T, M) take `severity` and `enabled` only, applied when the report is built; the stored findings don't change. `V*` sets all python-ags4 rules at once; a single ID overrides it.
   - **Minimally useful fields** go in a separate `src/hangtu/qc/min_fields.yaml` (`required` and `recommended` per group), overridden with `p.qc(min_fields=...)`. M7 reads the same file to decide which records are incomplete.
   - **Overrides are passed in, not stored.** Storing them with the project waits for the settings export (`to_yaml()`, M7).
4. **Rules in this unit:** every level 1 rule in the draft that can be checked from the canonical layer alone:
   - V, U, T, M: read back from the stored ingest findings, with `U004` and `M001` added to the list;
   - L001–L006, G001–G003, D001–D006, S001–S005, A001–A004, P001–P004, K001, C001.
   - **Deferred to M7:** G004 (unmapped geology code), because it needs the geology map. D004/D005 (outside geology, straddles a boundary) use `GEOL` as written, with the default geology key.
5. **Test depth for the D rules** is the record's top depth (`ISPT_TOP`, `SAMP_TOP`, `SPEC_DPTH`). The SPT mid-drive depth (SPEC §8.2) is M7's; a top-depth check is enough to catch a test below the hole or outside the logged geology.
6. **C001 reports, it doesn't exclude.** Leaving incomplete records out of datasets (`include_incomplete=`) is M7's.
7. **Test files:** a new `qc_defects.ags`, written by the existing script, with one case per rule. `defects.ags` stays the ingest defects file. `site_si.ags`, `site_us.ags` and `site_v404.ags` must give no QC errors or warnings, and the twin files the same findings.

### Out of scope
- Level 2 rules (engineering-judgment ranges per unit, v0.4).
- G004 and the geology map; `p.locations`; joins and datasets; excluding incomplete records (M7).
- Storing rule overrides in the project; fixing or editing data (hangtu never writes AGS, SPEC §1.4).
- An HTML or Excel report. CSV only for now (SPEC §9.2).

### SPEC sections touched
- §9: the framework confirmed or adjusted (§9.2: the rules table as a second CSV; thresholds as quantity strings), and the draft rule list replaced by a pointer to `docs/data/qc.md`.
- §10.1: `p.diff()` signature, if decision 2 changes it.
- §11: the Phase 2 sketch, if `p.qc()` changes.
- §12.2: the `qc/` package and its YAML files.
- §12.4: M6 done at close-out.
- `docs/data/ingest.md`: "Not in scope" lists `diff()` as M7; it is M6 (SPEC §12.4).
- `docs/drafts/phase2-data.md`: the Data quality section moves out. TODO #6 and #7 are updated with what the spec settles.

## Plan

Spec: [`docs/data/qc.md`](../data/qc.md).

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines (not counting test data) is split.

### Package layout
```
src/hangtu/
  project.py                  + Project.qc(), Project.diff()
  db.py                       + read_findings(), read_flags(), read_headings() (read-only helpers)
  qc/__init__.py              run(path, rules, min_fields) -> Report
  qc/rules.yaml               default rule settings (§3.1)
  qc/min_fields.yaml          default minimally useful fields (§4.10)
  qc/_settings.py             load, merge and check overrides; thresholds to SI (§3)
  qc/_data.py                 Data: canonical tables, flags, record depths, loca_id by line
  qc/_registry.py             the @rule decorator and the list of rules in code
  qc/_report.py               Report: findings, rules, source, summary(), repr, to_csv()
  qc/_locations.py            L001–L006
  qc/_geology.py              G001–G003
  qc/_depths.py               D001–D005, D007
  qc/_tests.py                S, A, P, K rules
  qc/_fields.py               C001, C002
  qc/_diff.py                 diff(path, group, heading, changed_only)
tests/qc/
  test_settings.py  test_report.py  test_locations.py  test_geology.py
  test_depths.py  test_tests.py  test_fields.py  test_diff.py
  test_qc_acceptance.py       §9 criteria, end to end
tests/data/ags/
  qc_defects.ags              new (§8)
```

### Decisions the build makes
Implementation choices the spec leaves open. Any that changes what a user sees goes into `qc.md` in the commit that builds it.
1. **Threshold kinds are a table in code; rules register by ID.** `qc/_registry.py` holds `THRESHOLDS = {"L005": {"ground_level_difference": "length", "neighbor_count": "count", ...}, ...}`, one entry per rule with thresholds, using P00 quantity kinds (`length`, `angle`, `percent`, `hydraulic_conductivity`, `count`). It is written in Build 1, since override checks need the kinds before any rule exists. Rule functions register later with `@rule("L005")`, as `(data, settings) -> RuleResult(findings, records_checked)`. A test checks that `rules.yaml`, `THRESHOLDS` and the registered functions agree: the same rule IDs (functions from Build 5 on, decision below), and the same threshold names. The kinds aren't inferred from the YAML defaults, because pint treats `deg` and `%` as both dimensionless, so `"2 %"` would pass as an angle.
2. **Thresholds are converted once, before any rule runs:** each quantity string goes through `units.parse_quantity` with its declared kind and then `units.convert` to the kind's canonical unit (m, deg, m/s); percent and counts stay as given. The original text is kept for `report.rules` (§5.2, "in the unit it was given").
3. **Rules read through `qc/_data.py`**, which reads each canonical table once per run via `db.py` (SPEC §7) and caches it. It also builds:
   - each group's **record depth** headings (§4, "Record depth") from `meta_heading` (name pattern plus `quantity = length`);
   - a **line → (group, `loca_id`, depth)** lookup, used to fill ingest findings (§5.1) and every rule's finding;
   - **value flags** per (group, `_row`, heading), so range checks skip flagged cells and K001 reads `LT`/`GT` bounds.
4. **Finding text in display units:** rules build messages with a helper that formats an SI value as `6.00 m (19.7 ft)`, file unit first, then the project's display unit when it differs, through `units.to_display`, so the supplier sees the number they wrote and the engineer sees it in their units. This refines `qc.md` §4.9 in Build 4. Numbers are written to the file's decimal places where the TYPE row gives them, else 3 significant figures.
5. **Severity and `enabled` are applied after the rules run**, in `_report.py`, for computed and ingest findings alike. A disabled rule isn't run at all (`records_checked` blank), and appears in `report.rules` with `enabled = False`.
6. **`V*` matching:** an override key `V*` applies to every stored finding whose rule starts with `V`; a key naming one V rule (`V10a`) overrides `V*` for that rule. `V*` and the V rules found in the file are listed in `report.rules`; V rules not raised aren't, since python-ags4 has dozens.
7. **`report.source`** is a dict read from `meta_source` (path, SHA-256, AGS version), plus hangtu's version and the run time in local ISO 8601 to the second.
8. **S005's N60** calls `ht.analysis.spt()`'s formula through a small shared helper in `analysis/_spt.py` (`n60(n, energy_ratio)`), so QC and the analysis can't disagree. Refactored in its own commit.
9. **L005 distance** is plain Euclidean distance on `LOCA_NATE`/`LOCA_NATN` (projected grid, in m after ingest). Holes with latitude and longitude only aren't checked (no projected distance); the rules table's `records_checked` shows how many were.
10. **Cascades in the defects file are listed, not avoided.** Some cases necessarily raise a second rule (a negative `ISPT_TOP` is also outside the geology, D004). The acceptance test holds the exact expected set of `(rule_id, source_line)` at error and warning, cascades included, each with a comment saying which case causes it.
11. **`p.diff()` reads raw and canonical tables by `_line`** and the `value_flag` table, through `db.py`, and doesn't use `qc/_data.py`'s caching (it's one group). `change` comes from `meta_heading.status` and `file_type` (§7): `converted` when status is `converted` and the file unit differs from the canonical unit after alias resolution; `reformatted` for `DT` where the text differs from the stored ISO string, and always for `T`, `DMS` and `YN`.
12. **CSV:** `to_csv` writes the findings with `index=False`, and the rules file with the `#` source lines first, then the table. The rules path is `<path stem>_rules.csv` in the same folder. Both overwrite.

### Build 1: `M6: add the QC rule settings and override checks`
- `qc/rules.yaml` (every rule in §4 with title, severity and thresholds), `qc/min_fields.yaml` (§4.10, `<SPEC_KEY>` as a YAML anchor), `qc/_settings.py`, `qc/_registry.py` with `THRESHOLDS` and the `@rule` decorator (decision 1).
- Thresholds are checked with `units.parse_quantity(text, kind)`, which runs `check_dimension`; `count` takes a plain number only. `min_fields` groups and headings are checked against the 4.2 dictionary (`ags._dictionary.standard`) here, and against the file's own headings once `p.qc()` exists (Build 4).
- `pyproject.toml`: package data for the two YAML files if the build config needs it.
- Tests (`test_settings.py`): defaults load; `rules.yaml` and `THRESHOLDS` name the same thresholds; a threshold override in ft equals the m value; each error in spec §2 (unknown rule, key, threshold, severity, wrong dimension, plain number for a length, unit on a count, missing file, bad YAML, unknown `min_fields` group or heading) with its message; overrides merge key by key; a file and a dict give the same settings; `V*` precedence.

### Build 2: `M6: add the QC defects test file`
- `_make_files.py` writes `qc_defects.ags` (§8): five holes, a `HORN` group, and one case per rule. `tests/data/ags/README.md` gets its row, listing the case and line for each rule.
- `test_files.py`: the file is written by the script, and python-ags4 finds no errors in it (the cases are engineering defects, not format ones).

### Build 3: `analysis: share the N60 formula`
- Refactor only: `n60(n, energy_ratio)` in `analysis/_spt.py`, used by `spt()`. Existing SPT golden tests pass unchanged.

### Build 4: `M6: add p.qc() and the QC report`
- `qc/_data.py`, `qc/_report.py`, `qc/__init__.run()`, `Project.qc()`; `db.py` read helpers.
- Ingest findings (§4.1) in the report with `loca_id` and `depth` filled from their line; severity/enabled overrides; `report.rules`, `summary()`, `repr`, `source`, `to_csv()`. No computed rules yet, so the registry is empty and the consistency test (decision 1) is skipped until Build 5 adds the first.
- Tests (`test_report.py`): `defects.ags` findings appear with their lines; overrides change severity and drop disabled rules; `V*`; summary counts; CSV round trip and the `#` source lines; `depth` in ft for US and m for SI; the printed summary's layout.

### Build 5: `M6: check locations and geology (L, G)`
- `qc/_locations.py`, `qc/_geology.py`. The registry consistency test turns on, with the YAML entries for rules not yet built marked so the test knows they're pending (removed in Build 8).
- Tests: each rule on `qc_defects.ags` at its line; L005 golden median and difference for BH4, hand-calculated in the test; L004 tolerance edges (88° no, 87.9° yes); G002 at the top and bottom of the log; G002/G003 tolerance edges and `"0.05 ft"`; L006 once per project.

### Build 6: `M6: check record depths (D)`
- `qc/_depths.py`: record depths per group (decision 3); D001–D005, D007.
- Tests: each rule at its line; D003 tolerance edge; D004 interval rule `top ≤ d < base` with `d = base` at the bottom of the hole (SPEC §8.3); `SAMP_TOP` in lab groups not checked twice.

### Build 7: `M6: check SPT, Atterberg, particle size and permeability`
- `qc/_tests.py`: S001–S005, A001–A004, P001–P004, K001. Split into `(S, A)` and `(P, K)` commits if over 300 lines.
- Tests: each rule at its line; golden values for S005 (N 20, ER 75 → 25), A002 (50 − 20 = 30 vs 25), P003 (94); S003 one per hole with the count; K001 at an `LT` bound; refusal rows skipped by S004.

### Build 8: `M6: check minimally useful fields (C)`
- `qc/_fields.py`: C001 per record or per absent heading, C002 per heading with counts; `min_fields=` overrides.
- Tests: blank vs flagged (an `NP` is not missing); absent heading → one finding; C002 counts; a group not in the file isn't checked. The pending marks from Build 5 are gone: every YAML rule has code.

### Build 9: `M6: add p.diff()`
- `qc/_diff.py`, `Project.diff()`.
- Tests (`test_diff.py`): each `change` value (spec §9 #8); `heading=` with one and several; `changed_only`; unknown group or heading lists what exists; display values follow `p.settings.display_units`.

### Build 10: `M6: test QC against the acceptance criteria`
- `test_qc_acceptance.py`: spec §9 #1 (exact error/warning set on `qc_defects.ags`, decision 10), #2 (good files), #3 (twins), #5–#7 end to end, #9 (database SHA-256 unchanged after `qc()` and `diff()`, no warnings, nothing printed).

### Build 11 (close-out): `M6: close out QC level 1, report and diff`
- `qc.md` status → done, with any decision above that changed what a user sees; `SPEC.md` §12.4 M6 done; the API sketch in §11 checked against `p.qc()`; `CLAUDE.md` state line (M6 done, M7 next); `TODO.md` if anything came up; this plan's Results.

### Verification
- `uv run ruff check . && uv run ruff format --check . && uv run pytest` at every commit.
- Before the close-out: the lowest-version run (CLAUDE.md, Commands), then `git checkout uv.lock`.
- Run `p.qc()` and `p.diff("ISPT", changed_only=True)` on `site_us.ags` and `qc_defects.ags` by hand and read the printed summary and messages as an engineer would: does each say what is wrong, where, and what to do?

### Results
- 1351 tests pass on Python 3.12 and with the lowest dependency versions; the QC and ingest tests (296) also pass on 3.13 and 3.14. The wheel has `hangtu/qc/` with `rules.yaml` and `min_fields.yaml`; no `pyproject.toml` change was needed.
- **Commits:** one per build step, with two split for size: Build 4 (the data layer, then the report and `p.qc()`) and Build 5 (L, then G). Build 7 went in as `(S, A)` then `(P, K)` as planned. Build 1 went past the ~300-line guide and was left as one commit.
- **Changes from the plan**, each recorded in `qc.md` in the commit that made it:
  - `min_fields` groups and headings are checked against the older AGS 4 dictionaries too, since the default `IPRG` entry is 4.0.x only, and against the file's own headings (§2).
  - `V*` and `VLOG` default to the severity stored at ingest; `report.rules` shows `as stored` (§3.3, §5.2). A single V rule is titled `python-ags4 rule 10c`, and V rules sort with their numbers in order (§4.9).
  - Message numbers (decision 4): unconverted values (percent, counts) are written as the file wrote them, `SCI` values in the file's notation, and very small or large numbers in scientific notation (§4.9).
  - D002 and D003 give one finding per record at the first offending heading; D007 one per specimen, however many tests share it (§4.4).
  - The pending rules in the registry test are listed in the test, not marked in `rules.yaml` (Build 5), so the shipped file never carried build markers.
  - "Blank" in L001–L003 and C001/C002 means empty in the file, so a column ingest kept raw-only (U001) isn't also reported as blank.
  - Tolerances are compared with a 1e-9 slack, so a value exactly at the tolerance isn't reported because of unit conversion.
  - §9 #8: the `T` case for `reformatted` is on `site_v404.ags`; no 4.2 good file has a `T` column.
- **Cascades** on `qc_defects.ags` are listed in `test_qc_acceptance.py`: D004 on lines 96 and 103 (from D002 and D003), and C001 on line 58 (BH5's blank LOCA fields, from L001 and L003).
- **Read by hand:** `p.qc()` on `site_us.ags` gives only info (A004, C002, L006, S003, U002), and on `qc_defects.ags` every message names the hole, depth, heading and value in the file's unit and the display unit, and says what to check. C002 is most of the info lines, by design (one per heading).
- **For M7:**
  - `GRAT_SIZE` gets the `small_length` kind at ingest, so US output shows sieve sizes in inches (TODO #17).
  - Rules read through `qc/_data.py`, which M7's datasets could reuse for record depths and the row at a line.
  - C001 is per record, which is the "incomplete" set that `include_incomplete=` will filter.
- SPEC: §12.2 changed in the spec step; nothing at close-out. The §11 sketch matches `p.qc()`.
