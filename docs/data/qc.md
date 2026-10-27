# QC level 1, report and diff

| | |
|---|---|
| **Status** | done (M6); §4.11 (density, M14) specified |
| **Intent** | [`docs/work/m6-qc.md`](../work/m6-qc.md#intent) |
| **Parent** | SPEC §2.6 (units), §7 (data model), §8 (depth and geology), §9 (data quality), §11 (errors) |
| **Related** | [`ingest.md`](ingest.md) §8–§9 (value flags, findings raised at ingest). [`docs/work/qc-review.md`](../work/qc-review.md) (accepted findings, D008), [`docs/work/vertical-datum.md`](../work/vertical-datum.md) (L006, L007). TODO #6 (P001/P003 tolerances), #7 (minimally useful fields) |

## 1. Purpose and scope
Check a project's data for integrity problems (SPEC §9.1, level 1) and report them to the engineer, and show what ingest did to each value:
- `p.qc()` runs the level 1 rules over the canonical layer, adds the findings ingest stored, and returns a **report** that prints a summary and exports to CSV;
- `p.diff(group)` compares the file's text with the canonical value, cell by cell.

**Not in scope:** level 2 rules (not yet placed, SPEC §1.3); the geology map, `p.locations`, joins, datasets and excluding incomplete records (M7, [`datasets.md`](datasets.md)); storing rule overrides in the project (M7, with `to_yaml()`); HTML or Excel reports; changing data (SPEC §1.4).

## 2. Public API
```python
report = p.qc()                                   # every rule, default settings
report = p.qc(rules="site_x_qc.yaml")             # overrides from a file
report = p.qc(rules={"G002": {"thresholds": {"depth_tolerance": "0.05 ft"}},
                     "A004": {"enabled": False}},
              min_fields={"LOCA": {"recommended": ["LOCA_TYPE"]}})
report = p.qc(accepted="site_x_accepted.yaml")   # reviewed findings, each with a reason (§3.4)

report                       # summary: counts by severity and by rule
report.findings              # DataFrame, one row per finding (§5)
report.rules                 # DataFrame, the settings this run used (§5)
report.summary()             # DataFrame: rule_id, title, severity, count, open, accepted
report.accepted              # DataFrame, one row per accepted entry and what it matched (§5.4)
report.to_csv("qc_report.csv")   # writes qc_report.csv and qc_report_rules.csv

p.diff("ISPT")                               # every cell of ISPT
p.diff("ISPT", heading="ISPT_TOP")           # one heading (or a list)
p.diff("ISPT", changed_only=True)            # only cells ingest changed (§7)
```
- QC is computed on demand and never writes to the database (SPEC §9.2). Running it twice gives the same report.
- Depths and values in findings are in the **project's** display units (`p.settings.display_units`), not the session's.
- `report.to_csv(path)` writes the findings to `path` and the rules next to it as `<stem>_rules.csv`. Both are UTF-8 with a header row.
- **Errors** (SPEC §11), raised before any rule runs: an override file that isn't there or isn't YAML; an unknown rule ID (lists the IDs); an unknown key in a rule (lists `enabled`, `severity`, `thresholds`); an unknown threshold name (lists the rule's thresholds); an unknown severity (lists `error`, `warning`, `info`); a threshold of the wrong kind (§3.2); an unknown group or heading in `min_fields` (lists the ones in the AGS 4 dictionaries: 4.2, then the older versions ingest reads, since `IPRG` is 4.0.x only; and, once a project is open, the file). `p.diff()` on an unknown group or heading lists the ones that exist. For `accepted=` (§3.4): a file that isn't there or isn't YAML; not a list of mappings; a missing or blank `rule_id` or `reason`; an unknown key (lists the six); an unknown rule ID; `depth` without `loca_id`; `depth` with no unit or not a length. Each names the entry by its position and rule ("accepted entry 3 (D007): …").

## 3. Rule settings
### 3.1 Files
- **`src/hangtu/qc/rules.yaml`**: the default settings for every rule in §4, keyed by rule ID. Each has a `title`, a `severity`, `enabled` (default `true`) and, where the rule has any, named `thresholds`. The checks themselves live in code (`qc/`), which also declares each threshold's quantity kind. A project can change settings but can't add rules.
- **`src/hangtu/qc/min_fields.yaml`**: the minimally useful fields per group (§4.10), `required` and `recommended`.

```yaml
rules:
  G002:
    title: Gap in the geology log
    severity: warning
    thresholds:
      depth_tolerance: 0.01 m
  L005:
    title: Ground level is an outlier compared with nearby holes
    severity: warning
    thresholds:
      ground_level_difference: 3 m
      neighbor_count: 5
      fewest_neighbors: 2
      search_radius: 200 m
  S002:
    title: Improbable SPT N
    severity: warning
    thresholds:
      highest_spt_n: 100
```

### 3.2 Thresholds
- **A threshold with a unit is a quantity string**, `"<number> <unit>"`, read by `units.parse_quantity` with its declared quantity kind: `0.01 m`, `"0.05 ft"`, `150 %`, `1e-12 m/s`, `2 deg`. Any unit of the right dimension is accepted and converted to the canonical unit before the rule runs.
- **A count takes a plain number** (`highest_spt_n: 100`, `neighbor_count: 5`); a unit on a count is an error.
- A plain number where a unit is needed is an error that shows the example with a unit. Units are never guessed (SPEC §2.6).
- Threshold names follow the naming rules (CLAUDE.md): written out, no bare `min`/`max`.

### 3.3 Overrides
- `rules=` and `min_fields=` take a path to a YAML file or a dict, of the same shape as the default file but holding only what changes. A file may have the top-level `rules:` key or not.
- **Merged rule by rule, key by key:** an override of one threshold keeps the rule's other thresholds and its severity. `min_fields` overrides replace a group's `required` or `recommended` list as a whole.
- **Ingest rules** (V, M, U, T; §4.1) take `severity` and `enabled` only, applied when the report is built. The stored findings don't change. In `rules.yaml`, `V*` and `VLOG` have `severity: null`, meaning the severity stored at ingest, since python-ags4's rules differ.
- **`V*`** sets every python-ags4 rule at once; a single V rule ID given alongside it wins.
- Overrides are passed to each call and not stored with the project (M7).

### 3.4 Accepted findings
A reviewer records findings they have checked and accept, so the report shows what is still open. `accepted=` takes a path to a YAML file or a list of dicts: a list of entries, under a top-level `accepted:` key or not.

```yaml
accepted:
  - rule_id: L005
    reason: Valley site; ground levels follow the topography.
  - rule_id: D003
    group: VSPR
    reason: Velocity profiles run to 30 m for Vs30, below the borings.
  - rule_id: D007
    loca_id: BH-12
    depth: 41.5 ft
    reason: Specimen depth checked against the lab sheet.
```

- **Keys:** `rule_id` and `reason` are required; `loca_id`, `group`, `heading` and `depth` are optional. A given key must equal the finding's, exactly; a key left out matches anything, so fewer keys make a broader entry (`rule_id` alone accepts the rule on this site, but unlike disabling it, the findings are still listed and counted). `depth` needs `loca_id`. `V*` isn't accepted; single V rules are.
- **Depth** is a quantity string, read as a length, and matches a finding within **0.05 m**, compared in meters. The tolerance is fixed, because practitioners write depths with inconsistent precision. A finding with no depth never matches an entry with one.
- **Lines aren't keys**, since they move between revisions of a file.
- A finding matched by several entries takes the first one's `reason`; every entry counts all the findings it matches.
- Accepting changes nothing but the `accepted` and `reason` columns: severities and counts stay, and "clean" (§9) counts accepted findings too.
- Entries are passed to each call, not stored with the project, as overrides are. An entry that matches nothing is shown in `report.accepted` (§5.4), not ignored.

## 4. Rules
Every rule is listed in `rules.yaml` with the severity below. The thresholds are decided (2026-10-14), except the P001/P003 tolerances (TODO #6).

**General behavior:**
- **A rule needs the headings it reads.** If a group or heading is absent, the rule checks nothing for it and raises no finding; the rules table (§5.2) shows how many records each rule checked, so a rule that checked nothing is visible. Missing headings themselves are C001/C002's job.
- **Blank and flagged values** are skipped by range checks: an `NP`, `<x`, `OTHER` or blank value is not a number to compare. `LT`/`GT` values are checked at their bound only where the rule says so.
- **Depths** are compared in SI. "Record depth" in the D rules means each of a group's own depth headings: headings named `<GROUP>_TOP`, `<GROUP>_BASE` or `<GROUP>_DPTH` with a length unit, plus `SPEC_DPTH` in the `specimen` table. `SAMP_TOP` in a lab group is the sample's key and is checked once, in `SAMP`. Depths of other things (`ISPT_CAS`, `ISPT_WAT`) are not record depths.
- **Intervals** follow SPEC §8.3: `top ≤ d < base`, and `d = base` belongs to the last interval of the hole.
- One finding per offending record, unless the rule says otherwise.

### 4.1 From ingest (stored)
As in `ingest.md` §9, read back from the `finding` table: `V<rule>`, `VLOG`, `V000`, `M001`, `U001`–`U005`, `T001`. Severities as stored, unless overridden. `U004`, `U005` and `M001` join the list here.

### 4.2 Locations (L)
| ID | Rule | Severity | Thresholds |
|---|---|---|---|
| L001 | `LOCA_GL` blank | error | |
| L002 | No coordinates: `LOCA_NATE`/`LOCA_NATN` blank, and `LOCA_LAT`/`LOCA_LON` blank | warning | |
| L003 | `LOCA_FDEP` blank | warning | |
| L004 | Non-vertical section: `HORN_INCL` differs from 90° | warning | `inclination_tolerance: 2 deg` |
| L005 | Ground level differs from the median of the nearest holes (by `LOCA_NATE`/`LOCA_NATN`) | warning | `ground_level_difference: 3 m`, `neighbor_count: 5`, `fewest_neighbors: 2`, `search_radius: 200 m` |
| L006 | No vertical datum is known for the project (`p.settings.vertical_datum`) | info | |
| L007 | Vertical datums disagree: holes' `LOCA_DATM` differ, or differ from the datum set for the project | warning | |

- L004: one finding per `HORN` row. A hole with no `HORN` rows is taken as vertical, as AGS does.
- L005: neighbors are the up to `neighbor_count` nearest other holes within `search_radius` that have a ground level; a hole with fewer than `fewest_neighbors` isn't checked. The message gives the median and the holes used.
- L006: one finding for the project, no line. The message shows `p.settings.vertical_datum = "NAVD88"` and, where the file has `LOCA_DATM`, why it wasn't used (ingest.md §7): holes with it blank or with a `LOCA_LOCZ` (up to 10 named), holes that name different datums (L007), or a name not in the datum table (with the `ht.add_vertical_datum()` call).
- L007: one finding for the project, group `LOCA`, heading `LOCA_DATM`, no line. Only holes with a `LOCA_GL` and no `LOCA_LOCZ` count, since a `LOCA_LOCZ` makes `LOCA_DATM` possibly a local datum. Raised when those holes name different datums (each datum with its hole count and up to 5 holes), or when the project's datum is a setting and their `LOCA_DATM` names another (both named). Names are compared after the datum table's matching; a name not in it is compared by its text, normalized the same way. L006 also fires when holes disagree, since no datum is taken from the file.

### 4.3 Geology (G)
| ID | Rule | Severity | Thresholds |
|---|---|---|---|
| G001 | A location with records in other groups has no `GEOL` rows | warning | |
| G002 | Gap in a hole's geology: between consecutive intervals, above the first interval (top > 0), or below the last (base < `LOCA_FDEP`) | warning | `depth_tolerance: 0.01 m` |
| G003 | Overlapping geology intervals in a hole | error | `depth_tolerance: 0.01 m` |
| G004 | A geology code isn't in the project's geology map (M7) | warning | |

- Intervals sorted by top. A gap or overlap is reported when it exceeds `depth_tolerance`.
- G001 is a warning, not the draft's error: CPT soundings and probe holes often have no geology log, and that isn't wrong.
- G004 runs only when the project has a geology map, against the codes of `p.settings.geology_key`: one finding per code, at its first GEOL row, with the count (`datasets.md` §9). A blank code isn't a finding.

### 4.4 Depths (D)
| ID | Rule | Severity | Thresholds |
|---|---|---|---|
| D001 | Interval with base above top (`<GROUP>_BASE` < `<GROUP>_TOP`) | error | |
| D002 | Negative record depth | error | |
| D003 | Record depth below the hole's final depth | warning | `final_depth_tolerance: 0.1 m` |
| D004 | Record depth outside the hole's logged geology | warning | |
| D005 | An interval record (sample, test zone) crosses a geology boundary | info | |
| D007 | Specimen depth (`SPEC_DPTH`) outside its sample (`SAMP_TOP` to `SAMP_BASE`, or below `SAMP_TOP` when there is no base) by more than `rounding_tolerance` | warning | `depth_tolerance: 0.01 m`, `rounding_tolerance: 0.1 m` |
| D008 | Specimen depth just outside its sample, likely rounding: by more than `depth_tolerance`, up to `rounding_tolerance` | info | D007's |

- D002 and D003 give one finding per record, at its first offending depth heading.
- D003 compares with `LOCA_FDEP + final_depth_tolerance`. Skipped where `LOCA_FDEP` is blank (L003).
- D007 and D008 give one finding per specimen, at its first row in file order, even when several tests (`LLPL`, `GRAG`, …) share it. Which rule depends on the offset; within `depth_tolerance` neither fires. D008 is the lower band of D007's check, so its bounds are D007's thresholds; each rule can be disabled or have its severity changed on its own, and disabling D007 doesn't change D008's band. `rounding_tolerance` below `depth_tolerance` is an error naming both. A ft→m rounding offset in a lab table is usually 2 to 8 cm; a linking error is meters.
- D004 and D005 use `GEOL` as written, and are skipped for holes with no geology (G001). D004 checks the top depth of each record; GEOL itself is not checked against itself.
- SPT depth is `ISPT_TOP` here. The mid-drive depth (SPEC §8.2) is M7's, and doesn't change which hole or interval a test is in except within 0.45 m of a boundary.
- **D006 (duplicate) is dropped from the draft.** Two records with the same keys are already python-ags4's Rule 10a (`V10a`); two records at the same depth with different keys (two samples, two specimens) are legitimate.

### 4.5 SPT (S)
| ID | Rule | Severity | Thresholds |
|---|---|---|---|
| S001 | `ISPT_REP` can't be read: neither a complete test (`5,6,6 N=12`) nor an incomplete drive (`25/75 50/75`, `22-30-50/3"`), in the forms of ingest.md §8 | warning | |
| S002 | Improbable N: `ISPT_NVAL` above the threshold | warning | `highest_spt_n: 100` |
| S003 | No energy ratio: `ISPT_ERAT` blank | info | |
| S004 | N doesn't match the blows: `ISPT_NVAL` ≠ `ISPT_MAIN`, or ≠ `ISPT_INC3` + … + `ISPT_INC6` when all four are given, on a test with no `REFUSAL` flag | warning | |
| S005 | File N60 differs from N × `ISPT_ERAT` / 60 | warning | `n60_tolerance: 1` |

- S001 uses ingest's parser (ingest.md §8), so a report S001 accepts as an incomplete drive is the one ingest flagged `REFUSAL`.
- S002's message cites the ASTM D1586 termination criteria (50 blows in a 150 mm increment, 100 in total, or no advance over 10 blows): an N above 100 means the drive continued past them. A complete test is never flagged `REFUSAL` (ingest.md §8), so S002 checks it.
- S003: one finding per hole, with the count of tests ("3 of 4 SPTs in BH3 have no energy ratio"), not one per test.
- S005: only where `ISPT_N60`, `ISPT_NVAL` and `ISPT_ERAT` are all given. N60 is computed as in `ht.analysis.spt()`.

### 4.6 Atterberg limits (A)
| ID | Rule | Severity | Thresholds |
|---|---|---|---|
| A001 | `LLPL_LL` < `LLPL_PL` | error | |
| A002 | `LLPL_PI` differs from `LLPL_LL` − `LLPL_PL` | warning | `plasticity_index_tolerance: 1 %` |
| A003 | Improbable liquid limit | warning | `lowest_liquid_limit: 10 %`, `highest_liquid_limit: 150 %` |
| A004 | Non-plastic (`NP` flag on `LLPL_PL`, `LLPL_LL` or `LLPL_PI`) | info | |

- A004 is one finding per specimen, so the engineer sees which specimens are NP; it's info, not a defect.

### 4.7 Particle size (P)
| ID | Rule | Severity | Thresholds |
|---|---|---|---|
| P001 | `GRAT_PERP` increases as `GRAT_SIZE` decreases, within one specimen | error | `percent_passing_tolerance: 0.5 %` |
| P002 | A percentage outside 0–100 (`GRAT_PERP`, `GRAG_VCRE`, `_GRAV`, `_SAND`, `_SILT`, `_CLAY`, `_FINE`) | error | |
| P003 | `GRAG` fractions don't add up to 100 | warning | `fraction_sum_tolerance: 2 %` |
| P004 | Too few points on a grading curve | info | `fewest_points: 4` |

- P001: one finding per specimen, at the first point that rises.
- P003: the sum is `GRAG_VCRE` (blank counts as 0) + `GRAG_GRAV` + `GRAG_SAND` + fines, where fines is `GRAG_FINE`, else `GRAG_SILT` + `GRAG_CLAY`. Checked only when gravel, sand and fines are all given.
- P004: one finding per specimen with fewer `GRAT` rows than `fewest_points`. Moved here from the draft's `min_rows_per_specimen` in the fields file, since it's a threshold.

### 4.8 Permeability (K)
| ID | Rule | Severity | Thresholds |
|---|---|---|---|
| K001 | Hydraulic conductivity ≤ 0 or outside the range | warning | `lowest_hydraulic_conductivity: 1e-12 m/s`, `highest_hydraulic_conductivity: 1 m/s` |

- Headings checked: `PTST_K`, `FGHG_IPRM`, `FGHS_IPRM`, `IPRG_IPRM` (4.0.x). An `LT`/`GT` value is checked at its bound.

### 4.9 Ordering, wording
- Findings are sorted by severity (error, warning, info), then rule ID with its number in order (`V7` before `V10c`), then source line.
- Messages follow SPEC §11 and name the hole and depth, the heading, the value as the file wrote it and the threshold in display units, and what to check. A value is written in the file's unit first, so the supplier sees the number they wrote, then in the project's display unit when that differs: `6.00 m (19.7 ft)`. File values keep the file's decimal places where its TYPE gives them (`2DP`); other numbers have 3 significant figures. A threshold is written as given, then in the display unit: "ISPT_TOP 6.00 m (19.7 ft) in BH1 is below the final depth of the hole, LOCA_FDEP 5.00 m (16.4 ft). Check the test depth or the final depth."

### 4.10 Minimally useful fields (C)
| ID | Rule | Severity |
|---|---|---|
| C001 | A `required` field is missing | warning |
| C002 | A `recommended` field is missing | info |

- **Missing** means the heading isn't in the group, or the cell is blank. A flagged value (`NP`, `Dry`, `<x`) is not missing, and neither is a blank `ISPT_NVAL` that ingest flagged `REFUSAL` from its report (ingest.md §8).
- **C001:** one finding per record with a blank required field (these are the records M7 leaves out unless `include_incomplete=True`), or one per group when the heading is absent.
- **C002:** one finding per group and heading, with the count of blank records ("ISPT_ERAT is blank in 1 of 5 records"), so recommended fields don't flood the report.
- Groups not in the file aren't checked. The default list, from the draft (TODO #7), with `SPEC_REF`/`SPEC_DPTH` recommended (M7, so a lab result without a specimen depth is placed at its sample; `datasets.md` §14), `IPRG` added for 4.0.x files, and `GRAT`'s point count moved to P004:

```yaml
LOCA: {required: [LOCA_ID, LOCA_GL, LOCA_FDEP], recommended: [LOCA_TYPE, LOCA_NATE, LOCA_NATN, LOCA_GREF, LOCA_STAR]}
GEOL: {required: [LOCA_ID, GEOL_TOP, GEOL_BASE, GEOL_DESC], recommended: [GEOL_LEG, GEOL_GEOL]}
SAMP: {required: [LOCA_ID, SAMP_TOP, SAMP_TYPE], recommended: [SAMP_REF, SAMP_ID, SAMP_BASE]}
ISPT: {required: [LOCA_ID, ISPT_TOP, ISPT_NVAL],
       recommended: [ISPT_REP, ISPT_NPEN, ISPT_ERAT, ISPT_TYPE, ISPT_HAM, ISPT_WAT, ISPT_CAS,
                     ISPT_INC1, …, ISPT_INC6, ISPT_PEN1, …, ISPT_PEN6]}
LLPL: {required: [<SPEC_KEY>, LLPL_LL, LLPL_PL], recommended: [LLPL_PI, LLPL_425, LLPL_PREP]}
LNMC: {required: [<SPEC_KEY>, LNMC_MC]}
GRAG: {required: [<SPEC_KEY>], recommended: [GRAG_GRAV, GRAG_SAND, GRAG_SILT, GRAG_CLAY, GRAG_FINE, GRAG_UC]}
GRAT: {required: [<SPEC_KEY>, GRAT_SIZE, GRAT_PERP]}
PTST: {required: [<SPEC_KEY>, PTST_K], recommended: [PTST_TYPE, PTST_COND, PTST_TSTR]}
FGHG: {required: [LOCA_ID, FGHG_TOP, FGHG_BASE, FGHG_IPRM], recommended: [FGHG_TYPE]}
IPRG: {required: [LOCA_ID, IPRG_TOP, IPRG_BASE, IPRG_IPRM], recommended: [IPRG_TYPE]}
LDEN: {required: [<SPEC_KEY>, LDEN_BDEN], recommended: [LDEN_DDEN, LDEN_MC, LDEN_TYPE, LDEN_COND]}   # M14
LPDN: {required: [<SPEC_KEY>, LPDN_PDEN], recommended: [LPDN_TYPE]}                                # M14
IDEN: {required: [LOCA_ID, IDEN_DPTH, IDEN_IDEN], recommended: [IDEN_MC, IDEN_TYPE]}               # M14
# <SPEC_KEY> = LOCA_ID, SAMP_TOP, SAMP_REF, SAMP_TYPE, SAMP_ID (the sample key); SPEC_REF and SPEC_DPTH lead each lab group's recommended list (M7)
```
In the shipped file the lists are written out in full; `<SPEC_KEY>` is a YAML anchor.

### 4.11 Density (B) (M14)
From `docs/work/m14a-density-data.md`. Checks within one record, plus wide ranges that catch a value in the wrong unit, as A003 and K001 do. Checks across tests (saturation, ρs against ρd) are phase relations, M14 (b).

| ID | Rule | Severity | Thresholds |
|---|---|---|---|
| B001 | `LDEN_DDEN` differs from `LDEN_BDEN` / (1 + `LDEN_MC` / 100) | warning | `dry_density_tolerance: 0.03 Mg/m3` |
| B002 | `LDEN_DDEN` above `LDEN_BDEN` | error | |
| B003 | Improbable density: `LDEN_BDEN` or `IDEN_IDEN` outside the bulk range, `LPDN_PDEN` outside the particle range | warning | `lowest_bulk_density: 1.0 Mg/m3`, `highest_bulk_density: 2.8 Mg/m3`, `lowest_particle_density: 2.0 Mg/m3`, `highest_particle_density: 3.2 Mg/m3` |
| B004 | Assumed particle density (`ASSUMED` flag on `LPDN_PDEN`) | info | |

- B001: only where all three are given. The tolerance clears the rounding of 2DP densities and a water content rounded to 1 % (at most 0.020 Mg/m³, at ρ = 2.20 and w = 5 %). The message gives the expected dry density and the difference.
- B002 doesn't need a water content: a dry density can't exceed the bulk density for any w ≥ 0.
- B003's message names what lies outside the range (peat and organic soils below, ores and some rock above), so the engineer checks the material as well as the unit. An assumed value is checked like a measured one.
- B004 is one finding per record, so the engineer sees which particle densities are assumed; it's info, not a defect.

## 5. The report
### 5.1 `report.findings`
| Column | Content |
|---|---|
| `rule_id` | `G002`, `V10a`, … |
| `severity` | `error`, `warning` or `info`, after overrides |
| `accepted` | True if an accepted entry matches it (§3.4) |
| `reason` | the matching entry's reason, blank when open |
| `group` | AGS group, or blank for a project-wide finding (L006) |
| `loca_id` | the record's `LOCA_ID`, where it has one |
| `depth` | the record's depth (§4, "Record depth": its first of `_TOP`, `_DPTH`, `SPEC_DPTH`, `SAMP_TOP`) in display units |
| `depth_unit` | `ft` or `m` |
| `heading` | the heading the finding is about, where there is one |
| `value` | the cell's text exactly as in the file, where the finding is about one cell |
| `message` | §4.9 |
| `source_line` | the line in the AGS file (`_line`), where the finding is about one row |

- **Ingest findings** get `loca_id` and `depth` from the canonical row at their line, where there is one.
- `df.attrs["units"]` is `{"depth": <display unit>}`, as for any hangtu DataFrame.

### 5.2 `report.rules`
One row per rule, enabled or not, in rule order. After `V*` come the V rules the file raised and any named in an override; other V rules aren't listed, since python-ags4 has dozens.

| Column | Content |
|---|---|
| `rule_id`, `title` | from `rules.yaml`; a single V rule is titled `python-ags4 rule 10c` |
| `enabled`, `severity` | after overrides; `as stored` for `V*`, V rules and `VLOG` unless overridden, since their stored severities differ |
| `thresholds` | one text cell: `depth_tolerance = 0.05 ft; …`, each in the unit it was given. D008's reads `from D007: …` |
| `overridden` | `yes` if anything differs from the defaults, else `no` |
| `records_checked` | how many records the rule looked at; blank for ingest rules and disabled rules |
| `findings` | how many findings it raised |

`report.source` holds the project file (`file`, `path`), its `sha256`, its `ags_version`, the `hangtu_version` and the time of the run (`run_at`, local ISO 8601 to the second), and `accepted` (the accepted-findings file's path, `list`, or blank). `to_csv` writes them as `#` comment lines at the top of the rules file (`# file: site.ags`; with accepted entries, `# accepted: <path>, <n> entries, <m> match no finding`), so a report sent on its own says what it checked and that a review was applied; `pd.read_csv(path, comment="#")` reads it back.

### 5.3 Printed summary
```
QC report: site.ags (AGS 4.2), hangtu 0.2.0, 2026-10-14 15:02
  open: 2 errors, 5 warnings, 9 info · accepted: 23
  error    G003  Overlapping geology intervals              1
  error    U001  Unknown or ambiguous unit                  1
  warning  D003  Record depth below the final depth         2  (+1 accepted)
  warning  L005  Ground level is an outlier compared ...    0  (+22 accepted)
  ...
  2 accepted entries match no finding: report.accepted
  findings: report.findings · rules used: report.rules · save: report.to_csv("qc_report.csv")
```

- Counts are open findings; `(+n accepted)` follows a rule with accepted ones, and a rule with only accepted findings is still listed. With no `accepted=`, the line reads `2 errors, 5 warnings, 9 info` as before. The "match no finding" line appears only when there are such entries.

### 5.4 `report.accepted`
One row per accepted entry, in file order: `rule_id`, `loca_id`, `group`, `heading`, `depth` (as written), `reason`, `matches` (how many findings it matched), `status` (`matched`, `no match` or `rule disabled`). Empty, with those columns, when `accepted=` isn't given.

## 6. Changes from the draft
- `C001` split into `C001` (required, warning) and `C002` (recommended, info, one per heading).
- `D006` dropped (§4.4); `D007` added (specimen outside its sample).
- `G001` is a warning, not an error (§4.3); `G002` also covers gaps at the top and bottom of the log.
- `G004` deferred to M7.
- `S003` is one finding per hole.
- `GRAT`'s `min_rows_per_specimen` is now P004's `fewest_points`.
- `V000`, `VLOG`, `M001` and `U004` added from ingest.
- **The imperial rounding concern (TODO #6, G002/G003)** doesn't arise: a gap is the difference between two depths the file wrote in the same unit, so equal text converts to equal SI values. The 0.01 m default stands; a project can set `"0.05 ft"`.

## 7. `p.diff(group)`
One row per cell of the group, in file order:

| Column | Content |
|---|---|
| `_line` | the DATA line |
| `loca_id` | the row's `LOCA_ID`, where it has one |
| `heading` | |
| `text` | the file's text |
| `file_unit` | the file's `UNIT` row for the heading |
| `value` | the canonical value: SI number, ISO date, text, or blank |
| `unit` | canonical unit |
| `display_value` | `value` in the project's display units |
| `display_unit` | |
| `flag`, `bound` | from `value_flag` |
| `change` | what ingest did, below |

`change` is one of:
- `blank`: the cell is empty;
- `flagged`: the cell has a value flag (`NP`, `LT`, `REFUSAL`, `OTHER`, …);
- `not_converted`: the heading is `raw_only` (`U001`, `U003`, `U004`), so the value is blank;
- `converted`: a number converted to a different unit (ft → m, pcf → Mg/m³);
- `reformatted`: a date, time, angle or yes/no rewritten (`dd/mm/yyyy` → ISO, `hh:mm:ss` → seconds, `DMS` → degrees, `Y` → 1);
- `unchanged`: anything else (text, numbers already in the canonical unit, counts).

`heading=` takes a heading or a list, and only those headings are shown: key headings are included only if named. An unknown heading lists the group's headings. `changed_only=True` keeps `flagged`, `not_converted`, `converted` and `reformatted`. Display values use `units.to_display` with the heading's quantity kind; a heading with no kind is shown as stored.

## 8. Test files
Synthetic, written by `tests/data/ags/_make_files.py` (SPEC §12.3).
- **`qc_defects.ags`** (4.2, SI): five holes, one case per rule in §4.2–§4.10, each at a known line. Ingest findings (§4.1) keep their cases in `defects.ags` and `site_v404.ags`. Cases:

| Rule | Case |
|---|---|
| L001, L003 | BH5 with `LOCA_GL` and `LOCA_FDEP` blank |
| L002 | BH5 with no coordinates |
| L004 | `HORN` row for BH2 with `HORN_INCL` 80 |
| L005 | BH4 with ground level 8 m above its neighbors |
| L006, L007 | BH1–BH3 `LOCA_DATM` `NAVD88`, BH4 `NGVD29` (BH5 has no `LOCA_GL`): one L007, and L006 with "holes name different datums" |
| G001 | BH5 has `ISPT` and no `GEOL` |
| G002 | BH1: 2.50–3.00 missing; BH2: log stops 0.50 m above `LOCA_FDEP` |
| G003 | BH3: 2.00–4.00 and 3.50–6.00 |
| D001 | `SAMP` with base above top |
| D002 | `ISPT_TOP` −0.50 |
| D003 | `ISPT_TOP` 1.00 m below `LOCA_FDEP` |
| D004 | covered by the G002 gap in BH1: an `ISPT` at 2.75 |
| D005 | `SAMP` 2.30–2.80 across a 2.50 boundary |
| D007, D008 | `SPEC_DPTH` 0.30 m below its sample's base (D007); 0.05 m below another's (D008) |
| S001 | `ISPT_REP` "hard", and "50/76 ft" (a unit that isn't accepted). Accepted, raising nothing: `5,6,6 N=12`, `6,8/8,9,9,9 N=35`, `50/3"` and `22-30-50/3in` with `ISPT_NVAL` blank (no C001) |
| S002 | `ISPT_NVAL` 150; and `ISPT_NVAL` 126 with report `41,81,57,75/113 N=126` (a complete test, not a refusal) |
| S003 | BH4 with `ISPT_ERAT` blank on 2 tests |
| S004 | `ISPT_NVAL` 20, `ISPT_INC3`–`6` 4, 5, 5, 5 |
| S005 | N 20, `ISPT_ERAT` 75, `ISPT_N60` 30 (computed 25) |
| A001, A002, A003, A004 | LL 30 PL 35; LL 50 PL 20 PI 25; LL 8; PL `NP` |
| P001, P002, P003, P004 | a curve that rises at 0.425 mm; `GRAT_PERP` 104; fractions summing to 94; a curve with 3 points |
| K001 | `PTST_K` 0, `FGHG_IPRM` 5 m/s |
| B001, B002, B003, B004 | `LDEN` ρ 2.00, w 20, ρd 1.80 (expected 1.667); ρ 1.80, ρd 1.90, w blank; `LDEN_BDEN` 19.5 and `LPDN_PDEN` 26.5; `LPDN_PDEN` `#2.65` (M14) |
| C001, C002 | `GEOL_DESC` blank on one row; `LOCA_TYPE` absent |

- The good files (`site_si.ags`, `site_us.ags` and `site_v404.ags`) must stay QC-clean (§9, #2). They have `LOCA_DATM` `NAVD88` in every hole, so they raise no L006.
- Accepted entries are written in the tests (a YAML file in `tmp_path` and the same entries as a list), against `qc_defects.ags`.

## 9. Acceptance criteria
1. **One test per rule:** on `qc_defects.ags`, each rule in §4.2–§4.11 raises exactly the findings its case seeds, with the right `group`, `loca_id`, `heading` and `source_line`; no other errors or warnings. Each ingest rule (§4.1) appears in the report of `defects.ags` or `site_v404.ags` with `loca_id` and `depth` filled where the line has a row.
2. **Good files:** `site_si.ags`, `site_us.ags` and `site_v404.ags` give no errors or warnings. Their info findings are only `S003`, `A004`, `B004`, `C002`, `M001` (v404) and `U002` (US).
3. **Twin files:** `site_si.ags` and `site_us.ags` give the same findings (`rule_id`, `severity`, `group`, `loca_id`, `heading`, `depth` to 1e-9) apart from `U002`.
4. **Golden values:** L005's median and difference for BH4, S005's computed N60, P003's sum and A002's difference are hand-calculated in the test and match the message.
5. **Thresholds and overrides:** `"0.05 ft"` and `"0.01524 m"` give the same G002 findings; a disabled rule raises nothing and shows `enabled = False` in `report.rules`; a severity override changes the findings and the summary; `V*` with a single V rule follows §3.3; an override file and the same dict give the same report. Each error in §2 is raised with its message.
6. **Rules table:** has every rule; `overridden` and `records_checked` are right for an override and for a group the file doesn't have (`records_checked = 0`).
7. **CSV:** `to_csv` writes both files; reading the findings back with `pd.read_csv` gives the same table; the rules file starts with the `report.source` comment lines and reads back with `comment="#"`. `depth` is in ft with `display_units="US"` and m with `"SI"`, with `depth_unit` to match.
8. **Diff:** each `change` value appears on the test files (`converted` and pcf on `site_us.ags`; `flagged`, `reformatted` (DMS, `YN`) on `site_si.ags` and `T` on `site_v404.ags`; `not_converted` on `defects.ags`); `changed_only` and `heading=` filter as §7 says; display values follow `p.settings.display_units`.
9. **Read-only and quiet:** QC and diff leave the database file unchanged (same SHA-256), raise no Python warnings and print nothing.
10. **Accepted findings (§3.4):** on `qc_defects.ags`, `rule_id: L005` alone accepts BH4's L005; an entry with `loca_id` and `depth` accepts exactly one D007, written in ft or m; 0.04 m off matches and 0.06 m off doesn't; a `group` limits it to that group. Accepted findings keep their severity, with `accepted` and `reason` set; `summary()`'s `open` and `accepted` add up to `count`; the printed summary follows §5.3. An entry matching nothing is `no match` in `report.accepted`, one for a disabled rule is `rule disabled`, and a broad entry behind a specific one still counts its matches. A file and the same list give the same report, with or without the `accepted:` key. Each `accepted=` error in §2 is raised. `to_csv` writes `accepted` and `reason`, and the rules file has the `# accepted:` line.
11. **D007/D008:** a `rounding_tolerance` of `"0.5 m"` turns the 0.30 m case into D008; disabling D008 leaves the 0.05 m case unreported; `rounding_tolerance` below `depth_tolerance` raises the error.

## 10. Open questions
1. TODO #6: the P001/P003 tolerances, against real files.
2. TODO #7: conditional requirements (`SPEC_*` only where a sample has more than one specimen) stay in the roadmap.
