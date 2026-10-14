# Datasets, depth and geology joins

| | |
|---|---|
| **Status** | done (M7) |
| **Intent** | [`docs/work/m7-datasets.md`](../work/m7-datasets.md#intent) |
| **Parent** | SPEC §2.6 (units), §7 (data model), §8 (depth, elevation, geology), §10 (datasets, registry), §11 (errors) |
| **Related** | [`ingest.md`](ingest.md) (canonical layer, value flags), [`qc.md`](qc.md) (C001, G004, D004/D005). `docs/drafts/analysis.md` §1 (SPT). P01, P02, P03, P07 (the plots these feed) |

## 1. Purpose and scope
Turn a project's canonical tables into the DataFrames the plots take:
- **`p.locations`**: one row per hole;
- **datasets**: `p.spt()`, `p.atterberg()`, `p.grain_size()` and `p.permeability()`, with one row per test result (or per point on a grading curve). Each row gets a depth, an elevation and a geology unit by the SPEC §8 conventions, and uses registry column names (SPEC §10.3) with `df.attrs["units"]` set;
- **the geology map**: `p.set_geology_map(path)` maps the codes in the file to the units an engineer reports on;
- **QC G004**, unmapped geology code, deferred here from M6.

**Not in scope:** classification columns (`plasticity_class_*`, `gradation_uscs`, `uscs_symbol`, AASHTO), `p.grain_size_summary()` and `p.index_properties()`, which wait for the M8 analyses (SPEC §1.3, §13 #2); settings export (`to_yaml()`) and stored QC overrides; datasets for other tests (undrained strength, consolidation); inclined holes (QC L004); changing the data (SPEC §1.4).

## 2. Public API
```python
p.locations                              # one row per hole
p.settings.geology_key = "GEOL_FORM"     # which GEOL heading holds the code (§5.1)
p.set_geology_map("strata.csv")          # code → geology unit, soil class, order, color (§5.2)
p.geology_map                            # the stored map, or None
p.set_geology_map(None)                  # remove it

spt = p.spt()                            # §6.1
spt = p.spt(geology=["Alluvium"], holes=["BH1", "BH2"], depth=(0, 30))
spt = p.spt(hammer_efficiency=80)        # passed to ht.analysis.spt()
atterberg = p.atterberg()                # §6.2
curves = p.grain_size()                  # §6.3
k = p.permeability()                     # §6.4

fig, ax = ht.plot.spt_profile(p.spt(geology=["Alluvium"]))
```

**Common arguments** (names decided in SPEC §10.2), on every dataset:

| Argument | Keeps | Notes |
|---|---|---|
| `holes=` | rows whose `loca_id` is in the list | An ID not in the project is an error that lists the IDs |
| `geology=` | rows whose `geology_unit` is in the list | After the map. A unit that isn't in the data is an error that lists the units |
| `depth=(top, base)` | `top ≤ depth ≤ base` | Numbers in the dataset's display units, or quantity strings (`("0 ft", "30 ft")`). Either end may be `None` |
| `elevation=(low, high)` | `low ≤ elevation ≤ high` | As `depth=`. Rows with no elevation (no `LOCA_GL`) are left out and counted |
| `where=` | rows matching `{column: value or list of values}` | Any column of the dataset, compared for equality. Anything more complex is a plain pandas filter on the result |
| `contains=` | rows whose `geology_description` contains the text | Case-insensitive, plain text (no patterns); a list keeps rows matching any of them |
| `geology_fields=` | adds GEOL headings as columns | `["GEOL_FORM", "GEOL_LEG"]` → `geology_formation`, `legend_code` (§5.3) |
| `include_incomplete=False` | records C001 calls incomplete are left out | §7 |
| `display_units=None` | the units of the values returned | `"US"` or `"SI"`; else the project's `display_units` (§4) |

- **Filters run after the joins**, in the order above, so `geology=` and `depth=` see the joined values. A filter that leaves no rows returns an empty DataFrame with every column, which the plots draw as "No data".
- **A group that isn't in the file** returns an empty DataFrame with every column and a warning that names the group ("No ISPT group in site.ags, so there are no SPT results."; for `p.permeability()`, "No PTST, FGHG or IPRG group"). This isn't an error, so a script run over many projects doesn't stop.
- **Errors** (SPEC §11) say what is wrong and what to do: an unknown hole or unit lists the ones that exist; a `depth=` that isn't a pair, or a quantity string of the wrong dimension, shows an example; an unknown column in `where=` lists the columns; a `geology_fields=` heading that isn't a GEOL heading lists the ones in §5.3.

## 3. `p.locations`
One row per `LOCA` row, in file order.

| Column | From | Notes |
|---|---|---|
| `loca_id` | `LOCA_ID` | |
| `location_type` | `LOCA_TYPE` | The code as written (`CP`, `RC`, …) |
| `ground_level` | `LOCA_GL` | |
| `final_depth` | `LOCA_FDEP` | |
| `easting`, `northing` | `LOCA_NATE`, `LOCA_NATN` | In the file's grid, in display units like any length; no CRS conversion |
| `latitude`, `longitude` | `LOCA_LAT`, `LOCA_LON` | Decimal degrees (ingest.md §7) |
| `remarks` | `LOCA_REM` | |
| `source_line` | `_line` | The line in the AGS file |

It's a property, takes no filters, and has `df.attrs["units"]` like a dataset (§4).

## 4. Values, units and columns
- **Units:** values come back in the display units, `display_units=` if given, else the project's `p.settings.display_units` (and its `display_overrides`), converted from SI by each column's quantity kind in the registry. `df.attrs["units"]` names the unit of every numeric column, so the plots and `ht.units_of` read them (SPEC §2.6). The SI and US twin files give the same dataset for the same `display_units=`.
- **Vertical datum:** when the project has one (`p.settings.vertical_datum`), `df.attrs["vertical_datum"]` holds it, and the plots put it on elevation labels ahead of `ht.settings.vertical_datum` (P00 §7). Added in M9, when the examples showed a project's datum missing from its figures.
- **Columns** are registry names (SPEC §10.3), in the order of the tables in §6. New columns are added to `columns.yaml` (§11).
- **Rows** are in file order of the dataset's source group, then by group for `p.permeability()` (PTST, FGHG, IPRG). Nothing is sorted by depth; the plots don't need it.
- **`source_line`** on every row is the line of its record in the AGS file, so any value can be checked against the file and `p.diff()`.
- **Value flags** become columns (SPEC §7): `REFUSAL` → `spt_refusal`, `NP` → `non_plastic`, `LT`/`GT` → `qualifier` (`"<"`/`">"`, with the bound as the value). A flagged value is never turned into a blank, and a blank never into a flag. `OTHER` (unrecognized text, `T001`) gives a blank value; the text stays in `p.diff()`.
- **Values from older files:** headings that exist only from 4.1 (`ISPT_N60`, `SPEC_BASE`) are blank in a 4.0.x file (ingest.md §6).

## 5. Geology
### 5.1 Geology key
- **`p.settings.geology_key`** names the GEOL heading that holds each layer's code: `GEOL_GEOL` (default, SPEC §8.3), `GEOL_GEO2`, `GEOL_LEG`, `GEOL_FORM` or `GEOL_BGS`. It's a setting like `display_units` (P00 §3): `ht.settings.geology_key` is the default for new projects, and `p.settings.geology_key` is stored with the project.
- **No map:** `geology_unit` is the key's code as written.
- **Key heading not in the file:** `geology_unit` is blank on every row, with one warning that names the GEOL headings the file has: "GEOL has no GEOL_GEOL heading, so geology_unit is blank. The file has GEOL_FORM; use it with p.settings.geology_key = "GEOL_FORM"." hangtu doesn't choose another heading on its own (SPEC §2.6, never guess).

### 5.2 Geology map
`p.set_geology_map(path)` reads a CSV, or takes a DataFrame with the same columns, and stores it in `meta_geology_map`. It replaces any earlier map; `None` removes it. It's kept until the database is rebuilt: `from_ags(..., overwrite=True)` starts with no map.

| Column | Required | Meaning |
|---|---|---|
| `code` | ✔ | A value of the geology key, matched **exactly and case-sensitively** (SPEC §8.3) |
| `geology_unit` | ✔ | The unit it belongs to. Several codes can map to one unit |
| `soil_class` | – | Carried to the datasets' `soil_class` (categories: TODO #3) |
| `order` | – | Number that sets the units' order (top to bottom of the site, say). Blank: the order of first appearance in the map |
| `color` | – | A matplotlib color for the unit. Every code of one unit must give the same color, or it's an error |

- The header is `geology_unit`, not SPEC §8.3's `unit`, by the naming rules (CLAUDE.md). SPEC §8.3 changes with this spec.
- **Errors:** a missing required column, or a column hangtu doesn't read (such as SPEC §8.3's old `unit`); a blank `code` or `geology_unit`; a duplicate `code` (which covers a code mapped to two units); one unit with two colors, two soil classes or two orders; an `order` that isn't a number; a color matplotlib doesn't know. Each names the codes and the line of the CSV (or the row of a DataFrame). Nothing is stored when the map has an error.
- **In the datasets:** `geology_unit` is an ordered pandas categorical in the map's order, so tables and plots list the units top to bottom. `df.attrs["palette"]` holds the map's colors.
- **Plots:** read `df.attrs["palette"]` after `ht.settings.palette`, so a color set in the session still wins, and honor a categorical `geology_unit`'s order where they list units. This is the one plot change in M7: P00 §10's resolution becomes `palette=` argument → `ht.settings.palette` → `df.attrs["palette"]` → automatic, applied to every plot through the shared palette helper.
- **Unmapped codes:** a code that isn't in the map keeps its code as `geology_unit`, after the mapped units in the order, with one warning per call that lists the codes and their counts: "GEOL_GEOL codes not in the geology map: 'ALV' (12 rows), 'MG' (3 rows). They're kept as their own units. Add them to strata.csv." QC reports them as `G004` (§9).

### 5.3 Columns from GEOL
Every dataset carries `geology_unit`, `soil_class` and `geology_description` (`GEOL_DESC` of the layer the test is in). `geology_fields=` adds any of:

| Heading | Column |
|---|---|
| `GEOL_GEOL` | `geology_code` |
| `GEOL_GEO2` | `geology_code_secondary` |
| `GEOL_LEG` | `legend_code` |
| `GEOL_FORM` | `geology_formation` |
| `GEOL_BGS` | `bgs_lexicon_code` |

These are the codes as written, unmapped, so two keys can be compared side by side (`crosstab`, Phase 3).

### 5.4 Which layer a test is in
- A test is joined to the GEOL layers of its own hole (by `location_id`, SPEC §7) at its **depth** (§6), by SPEC §8.3: `top ≤ depth < base`; a depth equal to the base of the hole's deepest layer is in that layer.
- **Overlapping layers** (QC G003): the layer with the deepest top wins, which is SPEC §8.3's "lowest top". So where `0–3 m` and `2–5 m` overlap, 2.5 m is in the second.
  - An overlap is a QC error (G003), and which layer wins changes the result, so the dataset says so too: one warning per call with the holes and the number of rows placed in an overlap ("3 SPT results in BH2 and BH5 are in overlapping GEOL layers; each was put in the layer with the deepest top. p.qc() lists the overlaps (G003)."). There's no flag column: the warning and G003 point at the layers to fix.
- **No layer** (a gap in the log, below the log, a hole with no GEOL, or no depth): `geology_unit`, `soil_class` and `geology_description` are blank. QC reports these (G001, G002, D004); the dataset doesn't warn again.
- An interval test (a permeability zone, a sample) is placed by its depth (its midpoint) like any other. QC D005 says when it crosses a boundary.

## 6. Datasets
Depth rules are SPEC §8.2. `elevation = ground_level − depth` (SPEC §8.1), blank where either is blank. Every dataset ends with `geology_unit`, `soil_class`, `geology_description`, any `geology_fields=` columns, and `source_line`.

### 6.1 `p.spt()`
```python
p.spt(*, hammer_efficiency=None, cap=None, **common) -> DataFrame
```
One row per `ISPT` row. Built from the file, then passed through `ht.analysis.spt()` (analysis.md §1.3) with `hammer_efficiency=` and `cap=`, so refusal, N60 and capped N follow the same rules as CSV input.

| Column | From |
|---|---|
| `loca_id` | `LOCA_ID` |
| `ground_level` | `LOCA_GL` of the hole |
| `depth`, `depth_basis` | Mid-drive depth, below |
| `elevation` | `ground_level − depth` |
| `spt_n` | `ISPT_NVAL`, as given, refusals included |
| `spt_n_capped` | `ht.analysis.spt()` |
| `spt_n60` | `ISPT_N60` where the file gives it (SPEC §7), else `ht.analysis.spt()` |
| `energy_ratio` | `ISPT_ERAT` |
| `energy_source` | Where N60 came from: `file_n60` (`ISPT_N60`), `file_energy_ratio` (`ISPT_ERAT`), `hammer_efficiency` (the argument or `ht.settings`), or blank when N60 is blank |
| `spt_refusal` | True where `ISPT_NVAL` has the `REFUSAL` flag (ingest.md §8); otherwise left to `ht.analysis.spt()`, which uses `spt_penetration` |
| `spt_penetration` | `ISPT_NPEN` |
| `remarks` | `ISPT_REM` |

**Mid-drive depth** (SPEC §8.2), from the increment penetrations `ISPT_PEN1`–`ISPT_PEN6` (mm): the seating drive is increments 1–2 and the test drive 3–6.
- **`mid_drive`**, when `ISPT_PEN1` is given: `ISPT_TOP + seating + test / 2`, where `seating = PEN1 + PEN2` and `test = PEN3 + … + PEN6`. A blank increment after the last one given counts as 0 (the drive stopped there).
- **`mid_drive_nominal`**, when the increments aren't given (settles SPEC §13 #1): assume a 150 mm seating drive and that the rest of `ISPT_NPEN` is the test drive. `seating = min(NPEN, 150 mm)`, `test = max(NPEN − 150 mm, 0)`, depth `= ISPT_TOP + seating + test / 2`. A full 450 mm test gives `top + 300 mm`, as SPEC proposed. With no `ISPT_NPEN` either: `top + 300 mm`.
  - **This changes the proposal for short drives.** SPEC's `top + total − 150 mm` puts the point at the *end* of the test drive's first half-length, and inside the seating drive for totals under 300 mm (`top + 50 mm` for 200 mm). The rule above is the same mid-drive formula with nominal increments: 200 mm gives `top + 175 mm`, the middle of the 50 mm test drive.
  - Nominal values are 150 mm in every file: a US file's 6 in (152.4 mm) differs by under 5 mm, less than a depth's precision.

**Golden values** (hand-calculated, `site_si.ags`): BH1 at 3.00 m, `NPEN` 450 → depth 3.30 m, `mid_drive_nominal`, elevation 12.40 − 3.30 = 9.10 m. BH1 at 6.00 m, a refusal with increments 75, 75, 75 and 50 mm → 6.00 + 0.150 + 0.125 / 2 = 6.2125 m, `mid_drive`. BH2 at 2.00 m, no increments → 2.30 m. `joins.ags` holds the rest (§12).

### 6.2 `p.atterberg()`
One row per `LLPL` row.

| Column | From |
|---|---|
| `loca_id` | `LOCA_ID` |
| `specimen_id` | The project's specimen key (ingest.md §5), as text (`"12"`): unique in the project, stable until the database is rebuilt |
| `sample_reference` | `SAMP_ID` where given, else `SAMP_TYPE` + `SAMP_REF` at `SAMP_TOP`, as text (`U1 at 1.50 m`) |
| `specimen_reference` | `SPEC_REF` |
| `ground_level`, `depth`, `depth_basis`, `elevation` | Lab depth, below |
| `depth_top`, `depth_base` | `SPEC_DPTH` and `SPEC_BASE` when both are given, else blank |
| `liquid_limit`, `plastic_limit` | `LLPL_LL`, `LLPL_PL` |
| `plasticity_index` | `LLPL_PI`; where blank, `LL − PL` when both are numbers and the specimen isn't NP |
| `non_plastic` | True when `LLPL_LL`, `LLPL_PL` or `LLPL_PI` has the `NP` flag, else False |
| `water_content` | `LNMC_MC` of the same specimen (`specimen_id`), where there is exactly one; a specimen with several `LNMC` rows gets a blank and one warning per call that names them |
| `liquidity_index` | `(w − PL) / PI` |
| `consistency_index` | `(LL − w) / PI` |

- LI and Ic are blank when a value they need is blank, when the specimen is NP, or when PI ≤ 0.
- An NP specimen has `non_plastic = True` and blanks where the file wrote `NP` (ingest.md §8); a liquid limit the file gives is kept, and its PI isn't filled in. P07 counts it as NP, not as a blank (SPEC §4).

**Lab depth** (SPEC §8.2), for every lab dataset: `SPEC_DPTH` (`spec_depth`), else the sample's midpoint `(SAMP_TOP + SAMP_BASE) / 2` from `SAMP` (`sample_mid`), else `SAMP_TOP` (`sample_top`).

### 6.3 `p.grain_size()`
Long format: one row per `GRAT` row, in file order, so each specimen's points stay together.

| Column | From |
|---|---|
| `loca_id`, `specimen_id`, `sample_reference`, `specimen_reference` | As §6.2 |
| `ground_level`, `depth`, `depth_basis`, `elevation` | Lab depth (§6.2) |
| `particle_size` | `GRAT_SIZE` |
| `percent_passing` | `GRAT_PERP` |
| `qualifier` | `<`/`>` from an `LT`/`GT` flag on `GRAT_PERP` |

`particle_size` shows in mm in US output too, because `GRAT_SIZE` gets the `particle_size` quantity kind at ingest (§10, TODO #17).

### 6.4 `p.permeability()`
One row per hydraulic conductivity result, from three groups:

| Source group | Value | `source` | `test_type` | Depth (`depth_basis`) | `depth_top`, `depth_base` |
|---|---|---|---|---|---|
| `PTST` | `PTST_K` | `lab` | `PTST_TYPE` | lab depth (§6.2) | `SPEC_DPTH`, `SPEC_BASE` |
| `FGHG` | `FGHG_IPRM` | `field` | `FGHG_TYPE` | `(FGHG_TOP + FGHG_BASE) / 2` (`zone_mid`) | `FGHG_TOP`, `FGHG_BASE` |
| `IPRG` (4.0.x) | `IPRG_IPRM` | `field` | `IPRG_TYPE` | `(IPRG_TOP + IPRG_BASE) / 2` (`zone_mid`) | `IPRG_TOP`, `IPRG_BASE` |

Columns: `loca_id`, `ground_level`, `depth`, `depth_top`, `depth_base`, `depth_basis`, `elevation`, `hydraulic_conductivity`, `qualifier`, `source`, `test_type`, then the geology columns and `source_line`.
- `FGHS` stage values aren't included: `FGHG_IPRM` is the test's result. An `IPRG` file has one row per stage (ingest.md §6), and each is a result, so each is a row.
- A zone with only one of top and base gets a blank depth; it isn't guessed.

## 7. Incomplete records
- A record is **incomplete** when QC C001 says so (with `SPEC_REF` and `SPEC_DPTH` recommended, §14): a `required` field of its own group in `qc/min_fields.yaml` is blank (qc.md §4.10). Only the dataset's source group is checked, not its parents: a hole with no `LOCA_GL` keeps its tests, with a blank elevation.
- **Left out by default**, with one warning per call: "Left out 2 of 5 ISPT records with a blank required field (ISPT_NVAL on lines 98, 103). p.qc() lists them; include them with include_incomplete=True."
- `include_incomplete=True` keeps them, with their blanks.

## 8. Warnings
Each dataset call gives at most one warning per kind (`UserWarning`, as the rest of hangtu): the missing group (§2), the missing geology key (§5.1), unmapped codes (§5.2), overlapping layers (§5.4), records left out (§7), and specimens with several water contents (§6.2). A call on the good test files with a complete map gives none.

## 9. QC: G004
| ID | Rule | Severity | Thresholds |
|---|---|---|---|
| G004 | A geology code isn't in the project's geology map | warning | |

- Runs only when the project has a map; otherwise it checks nothing (records checked: 0).
- One finding per code, at its first GEOL row, with the count: "GEOL_GEOL 'ALV' (12 layers, first in BH3) isn't in the geology map, so its tests are kept under the code. Add it to the map." A blank code isn't a finding.
- Added to `qc/rules.yaml` and qc.md §4.3.

## 10. Ingest change (TODO #17)
- `GRAT_SIZE`, `LLPL_SIZE` and `PTST_SZUN` (particle sizes, unit mm in the dictionary) get the `particle_size` quantity kind instead of `small_length`, so US output keeps mm as US practice does (P00 §4.1). Other headings keep the kind their unit implies.
- The schema version goes up (the stored kinds change and `meta_geology_map` is new), so an M6 database asks to be re-ingested (ingest.md §2).

## 11. Registry
New columns, each checked against the whole registry (CLAUDE.md, "Naming"): `location_type`, `final_depth`, `easting`, `northing`, `latitude`, `longitude`, `remarks`, `source_line`, `energy_source`, `sample_reference`, `specimen_reference`, `geology_description`, `geology_code`, `geology_code_secondary`, `legend_code`, `geology_formation`, `bgs_lexicon_code`.
- Changed: `specimen_id` (the project's specimen key, as text, since the registry type is text and CSV users type their own IDs); `depth_top`/`depth_base`, `hydraulic_conductivity` and `test_type` get their new AGS sources (`SPEC_DPTH`/`SPEC_BASE`, `IPRG_*`).
- The CSV templates (`ht.template()`) don't change: they describe what a user types in, and a dataset is a superset of its template.

## 12. Test files
The good files (`site_si.ags`, `site_us.ags`, `site_v404.ags`) get, through the generator script and in all three so the twin tests still hold:
- SPT increments on some tests: a complete drive, and a refusal in the test drive;
- a `GEOL_GEOL` heading next to `GEOL_FORM`, so the default key works.

A new `joins.ags` (4.2, SI, passes python-ags4) holds the edge cases: a test exactly on a layer boundary and at the base of the deepest layer; overlapping layers; a gap in the log; a hole with no GEOL; a test with no `LOCA_GL`; an SPT refusal in the seating drive; a sample with no base; a specimen with no `SPEC_DPTH`; a code missing from the test map; an incomplete record. Two `LNMC` rows on one specimen break AGS Rule 10a (duplicate key), so that case is built in the test instead of in a file that passes python-ags4. A test map `strata.csv` sits next to it.

## 13. Acceptance criteria
1. **Feeds the plots unchanged:** `ht.plot.spt_profile(p.spt())`, `ht.plot.spt_histogram(p.spt())`, `ht.plot.profile(p.permeability(), "hydraulic_conductivity")`, `ht.plot.profile(p.atterberg(), "liquid_limit")` and `ht.plot.geology_unit_comparison(p.atterberg(), "plasticity_index")` run on the good files with no error, no warning and no hint, and with the map's colors and order.
2. **Twin files:** `site_si.ags` and `site_us.ags` give equal datasets and `p.locations` (values to 1e-9 relative), for `display_units="SI"` and for `"US"`.
3. **Older version:** `site_v404.ags` gives `p.permeability()` rows from `IPRG`, one per stage, with `source = "field"`.
4. **Depths:** every golden mid-drive, lab and zone depth matches its hand calculation, with the right `depth_basis` (§6.1, §6.2, §6.4).
5. **Geology:** each `joins.ags` boundary case lands in the layer §5.4 says; a depth in a gap is blank; overlapping layers resolve to the deepest top, with the overlap warning.
6. **Map:** mapped codes give their unit, soil class and order; an unmapped code is kept under its code with one warning, and is a G004 finding; each map error in §5.2 is raised; a session `ht.settings.palette` color beats the map's.
7. **Geology key:** with the key heading absent, `geology_unit` is blank and the warning names the headings present; `geology_fields=` adds the §5.3 columns.
8. **Flags:** a refusal gives `spt_refusal = True` and `spt_n` as written; NP gives `non_plastic = True` with blank limits; `<1` gives `qualifier = "<"` with value 1; none of them is blank where the file flagged it.
9. **Filters:** each common argument keeps exactly the rows it should, including quantity strings and `None` ends; each error in §2 is raised.
10. **Incomplete:** the incomplete record is left out with the warning, and kept with `include_incomplete=True`.
11. **N60 provenance:** `energy_source` is right for a file N60, a file ER, `hammer_efficiency=` and none.
12. **Units:** `df.attrs["units"]` covers every numeric column, and US output shows `particle_size` in mm.
13. **Empty:** a project with no `ISPT` gives an empty `p.spt()` with every column and the warning.

## 14. Decisions in review
1. **`SPEC_REF` and `SPEC_DPTH` move to `recommended`** in `qc/min_fields.yaml` (decided 2026-10-14, TODO #7). Required, they made §7 leave out every lab result without a specimen depth, so the lab depth fallback (`sample_mid`, `sample_top`, SPEC §8.2) could never run by default. A blank one is still reported, by C002.
