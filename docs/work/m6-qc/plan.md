# M6 QC level 1, report and diff: plan

Intent: [intent.md](intent.md). Spec: [`docs/data/qc.md`](../../data/qc.md).

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines (not counting test data) is split.

## Package layout
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

## Decisions the build makes
Implementation choices the spec leaves open. Any that changes what a user sees goes into `qc.md` in the commit that builds it.
1. **Rules declare themselves in code.** `@rule("L005", thresholds={"ground_level_difference": "length", "neighbor_count": "count", ...})` registers a function `(data, settings) -> RuleResult(findings, records_checked)`. A test checks that the IDs in `rules.yaml` and in the registry are the same set and that each rule's threshold names and kinds match the YAML, so the two can't drift.
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

## Build 1: `M6: add the QC rule settings and override checks`
- `qc/rules.yaml` (every rule in §4 with title, severity and thresholds), `qc/min_fields.yaml` (§4.10, `<SPEC_KEY>` as a YAML anchor), `qc/_settings.py`, `qc/_registry.py` with the decorator only.
- `pyproject.toml`: package data for the two YAML files if the build config needs it.
- Tests (`test_settings.py`): defaults load; a threshold override in ft equals the m value; each error in spec §2 (unknown rule, key, threshold, severity, wrong dimension, plain number for a length, unit on a count, missing file, bad YAML, unknown `min_fields` group or heading) with its message; overrides merge key by key; a file and a dict give the same settings; `V*` precedence.

## Build 2: `M6: add the QC defects test file`
- `_make_files.py` writes `qc_defects.ags` (§8): five holes, a `HORN` group, and one case per rule. `tests/data/ags/README.md` gets its row, listing the case and line for each rule.
- `test_files.py`: the file is written by the script, and python-ags4 finds no errors in it (the cases are engineering defects, not format ones).

## Build 3: `analysis: share the N60 formula`
- Refactor only: `n60(n, energy_ratio)` in `analysis/_spt.py`, used by `spt()`. Existing SPT golden tests pass unchanged.

## Build 4: `M6: add p.qc() and the QC report`
- `qc/_data.py`, `qc/_report.py`, `qc/__init__.run()`, `Project.qc()`; `db.py` read helpers.
- Ingest findings (§4.1) in the report with `loca_id` and `depth` filled from their line; severity/enabled overrides; `report.rules`, `summary()`, `repr`, `source`, `to_csv()`. No computed rules yet, so the registry is empty and the consistency test (decision 1) is skipped until Build 5 adds the first.
- Tests (`test_report.py`): `defects.ags` findings appear with their lines; overrides change severity and drop disabled rules; `V*`; summary counts; CSV round trip and the `#` source lines; `depth` in ft for US and m for SI; the printed summary's layout.

## Build 5: `M6: check locations and geology (L, G)`
- `qc/_locations.py`, `qc/_geology.py`. The registry consistency test turns on, with the YAML entries for rules not yet built marked so the test knows they're pending (removed in Build 8).
- Tests: each rule on `qc_defects.ags` at its line; L005 golden median and difference for BH4, hand-calculated in the test; L004 tolerance edges (88° no, 87.9° yes); G002 at the top and bottom of the log; G002/G003 tolerance edges and `"0.05 ft"`; L006 once per project.

## Build 6: `M6: check record depths (D)`
- `qc/_depths.py`: record depths per group (decision 3); D001–D005, D007.
- Tests: each rule at its line; D003 tolerance edge; D004 interval rule `top ≤ d < base` with `d = base` at the bottom of the hole (SPEC §8.3); `SAMP_TOP` in lab groups not checked twice.

## Build 7: `M6: check SPT, Atterberg, particle size and permeability`
- `qc/_tests.py`: S001–S005, A001–A004, P001–P004, K001. Split into `(S, A)` and `(P, K)` commits if over 300 lines.
- Tests: each rule at its line; golden values for S005 (N 20, ER 75 → 25), A002 (50 − 20 = 30 vs 25), P003 (94); S003 one per hole with the count; K001 at an `LT` bound; refusal rows skipped by S004.

## Build 8: `M6: check minimally useful fields (C)`
- `qc/_fields.py`: C001 per record or per absent heading, C002 per heading with counts; `min_fields=` overrides.
- Tests: blank vs flagged (an `NP` is not missing); absent heading → one finding; C002 counts; a group not in the file isn't checked. The pending marks from Build 5 are gone: every YAML rule has code.

## Build 9: `M6: add p.diff()`
- `qc/_diff.py`, `Project.diff()`.
- Tests (`test_diff.py`): each `change` value (spec §9 #8); `heading=` with one and several; `changed_only`; unknown group or heading lists what exists; display values follow `p.settings.display_units`.

## Build 10: `M6: test QC against the acceptance criteria`
- `test_qc_acceptance.py`: spec §9 #1 (exact error/warning set on `qc_defects.ags`, decision 10), #2 (good files), #3 (twins), #5–#7 end to end, #9 (database SHA-256 unchanged after `qc()` and `diff()`, no warnings, nothing printed).

## Build 11 (close-out): `M6: close out QC level 1, report and diff`
- `qc.md` status → done, with any decision above that changed what a user sees; `SPEC.md` §12.4 M6 done; the API sketch in §11 checked against `p.qc()`; `CLAUDE.md` state line (M6 done, M7 next); `TODO.md` if anything came up; this plan's Results.

## Verification
- `uv run ruff check . && uv run ruff format --check . && uv run pytest` at every commit.
- Before the close-out: the lowest-version run (CLAUDE.md, Commands), then `git checkout uv.lock`.
- Run `p.qc()` and `p.diff("ISPT", changed_only=True)` on `site_us.ags` and `qc_defects.ags` by hand and read the printed summary and messages as an engineer would: does each say what is wrong, where, and what to do?

## Results
(Filled in at close-out.)
