# M6: QC level 1, report and diff — intent

## Goal
Check a project's data for integrity problems and report them to the engineer: `p.qc()` runs the level 1 rules (SPEC §9.1) over the canonical layer, adds the findings ingest already stored, and returns a report that prints a readable summary and exports to one flat CSV. `p.diff(group)` shows, cell by cell, what ingest did to each value: the file's text and unit, the SI value, the display value and any flag.

## Why
- It's the next Phase 2 unit (SPEC §1.3, §12.4 M6). Ingest (M5) stores the data and its own findings but has no way to show them except `p.sql("select * from finding")`.
- Engineers need to know what's wrong with a file before they plot it. A QC report they can send back to the data supplier is useful on its own, before any dataset exists.
- `diff()` is how an engineer checks a conversion they don't trust (pcf, ton, a mixed-unit column) without reading the database.
- The datasets (M7) depend on some of these rules: C001 decides which records are incomplete, and the geology and depth rules check the joins M7 will rely on.

## Constraints
- SPEC §9.2 (decided): rules (id, severity, thresholds) in YAML, overridable per project; QC computed on demand, only ingest validation persisted; findings export to one flat CSV (decision 2 adds a second file for the rules used); `p.diff(group)` compares raw and canonical.
- SPEC §7: rules read the canonical layer through `db.py` and join on surrogate keys, never AGS key columns. Every finding points at its source line.
- SPEC §2.6 and §8: thresholds are in SI and convert like any other quantity; depths and values in the report are shown in the project's display units, with the unit stated. Intervals use `top ≤ d < base` (§8.3).
- SPEC §11: messages say what is wrong, where (hole, depth, group, heading, line) and what to do.
- Starting rule list and thresholds: `docs/drafts/phase2-data.md` (Level 1 rules, Minimally useful fields), TODO #6 and #7. The spec step finishes them.
- No new dependency. Test files are synthetic.
- **Done when:** one defects-file test per rule (SPEC §12.4), the good test files give no warnings or errors, and the spec's acceptance criteria pass.

## Decisions (proposed, to settle in review)
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

## Out of scope
- Level 2 rules (engineering-judgment ranges per unit, v0.4).
- G004 and the geology map; `p.locations`; joins and datasets; excluding incomplete records (M7).
- Storing rule overrides in the project; fixing or editing data (hangtu never writes AGS, SPEC §1.4).
- An HTML or Excel report. CSV only for now (SPEC §9.2).

## SPEC sections touched
- §9: the framework confirmed or adjusted (§9.2: the rules table as a second CSV; thresholds as quantity strings), and the draft rule list replaced by a pointer to `docs/data/qc.md`.
- §10.1: `p.diff()` signature, if decision 2 changes it.
- §11: the Phase 2 sketch, if `p.qc()` changes.
- §12.2: the `qc/` package and its YAML files.
- §12.4: M6 done at close-out.
- `docs/data/ingest.md`: "Not in scope" lists `diff()` as M7; it is M6 (SPEC §12.4).
- `docs/drafts/phase2-data.md`: the Data quality section moves out. TODO #6 and #7 are updated with what the spec settles.
