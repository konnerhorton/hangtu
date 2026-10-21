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
