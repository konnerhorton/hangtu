# hangtu — Product Specification

**Status:** Draft.

**What belongs here:** decisions that constrain more than one feature, plus scope and phasing. Per-feature detail lives in that feature's spec (e.g. `docs/plots/PXX-*.md`). Detail for later phases is held in `docs/drafts/` until those phases start. Update this file in the same commit as any change that alters a decision. How the process works: [`docs/reference/process.md`](docs/reference/process.md).

**Conventions**
- **Decided**: agreed in review.
- 🟡 **Proposed**: Claude's proposed default, awaiting review.
- ❓ **Open**: needs input (collected in §13).
- 🔬 **Research**: tracked in [TODO.md](docs/TODO.md).

**Document map**
| Document | Contents |
|---|---|
| `SPEC.md` (this file) | Scope, phasing, cross-cutting decisions (units, data, conventions, QC, statistics, engineering) |
| [`docs/plots/README.md`](docs/plots/README.md) | Shared plot conventions, and the plot list with each plot's status |
| `docs/plots/PXX-*.md` | One spec per figure, from [`TEMPLATE.md`](docs/plots/TEMPLATE.md) |
| [`docs/drafts/`](docs/drafts/) | The analyses draft spec and notes for later phases (Phase 2 data, Phase 3 statistics) |
| [`docs/reference/eurocode7-summary.md`](docs/reference/eurocode7-summary.md) | Background for characteristic values |
| [`docs/TODO.md`](docs/TODO.md) | Research items and pending decisions |
| [`CLAUDE.md`](CLAUDE.md) | Working conventions and commands for Claude Code |
| [`docs/reference/process.md`](docs/reference/process.md) | How work moves from intent to merged code |

---

## 1. Scope and phasing

### 1.1 Users and distribution
- **Persona:** a geotechnical engineer with beginner-to-intermediate Python, self-taught through postgraduate work.
  - They think in **scripts and functions** more than objects.
  - So everything analytical is a plain function on a DataFrame.
  - The (Phase 2) `Project` object is kept deliberately thin.
- **Project model** (decided): open source, developed independently. Published on **PyPI** and public GitHub under the **MIT** license. No company data is used in development or testing.
- **Name** (decided): **`hangtu`**, imported as `import hangtu as ht`. It replaces the working name `ags-kit`, which tied the package to one file format and could look endorsed by the AGS trade body.
  - Keep "AGS" and "DIGGS" in the PyPI description, keywords and README, so the package is still easy to find.
  - The name is claimed on PyPI by the 0.0.1 placeholder release (§12.1).

### 1.2 Formats
| Format | Role | When |
|---|---|---|
| **AGS4** (4.0.3–4.2) | Factual input | Phase 2 |
| **DIGGS** | Factual input (mapped into the same internal model) | Later |
| **AGSi** (v1.0.1) | Interpreted output (ground model, property summaries, design parameters); later also input | v0.5 export, later import |
| **CSV / DataFrame** | Input for plots and statistics, using the documented column names. CSV only (decided): no Excel reader; users convert their own workbooks | **Phase 1** |

### 1.3 Phases and roadmap
**Why plots came first (decided):** plots are what users will use first, so building them first gets feedback soonest. Plot and analysis functions take DataFrames, so they don't need the AGS ingest or database to be useful.

**Build order (decided 2026-10-13):** after M3 (P01–P03 and P07), Phase 2 is built before the rest of Phase 1 (P04–P06, §12.4). The data layer is the more useful piece for current work, and the remaining plots don't depend on it, so either order works.

**First release (decided 2026-10-14):** v0.1 ships after M7, with the plots built so far and the whole data layer, rather than with all of Phase 1 and no AGS. Testers can then try hangtu on their own AGS files, which tells us more than CSV input alone. P04–P06 move to v0.2.

**v0.2 widened (decided 2026-10-15):** the triaxial plots (P11–P12), the clogging diagram (P17) and published SPT correlations (§4) join P04–P06 in v0.2. They are what current work needs next. (N1)60 comes with them, because several correlations use it. Phases name content; versions name releases, so Phase 1 spans v0.1 and v0.2. The table below lists versions by content; §12.4 has the build order.

| Version | Phase | Content |
|---|---|---|
| **v0.1** | **1: Plots** (part) and **2: Data** | - Plot framework (P00): style, palette, unit-aware labels, out-of-range markers, `Sheet`.<br>- Plots **P01–P03 and P07**: property profile, SPT profile, SPT histograms, property by geology unit.<br>- SPT analysis: N60, refusal, classes.<br>- Units handling for DataFrames (§2.6), the column registry, CSV templates.<br>- AGS4 ingest (units on ingest, value flags) into SQLite.<br>- QC level 1 with CSV report and diff tool.<br>- Depth/elevation/geology conventions and joins.<br>- Datasets (SPT, Atterberg, grain size curves, permeability) that feed the plots directly.<br>- **First PyPI release.** |
| **v0.2** | **1: Plots** (rest) and lab and in-situ analyses | - Plots **P04–P06**: plasticity chart, grain size, water content profile.<br>- The analyses they need: plasticity classification, Dx/Cu/Cc/gradation.<br>- The datasets that need them: classification columns, `grain_size_summary()`, `index_properties()`.<br>- Triaxial: failure envelope with the Mohr–Coulomb fit (P11); stress–strain curves and measured stress paths (P12).<br>- Clogging: Thewes & Burger (2004) diagram (P17), from the consistency index.<br>- **SPT correlations** (§4): published correlations from SPT N to other properties, each with its applicability, compared on P01 and P07.<br>- (N1)60. |
| **v0.3** | **3: Statistics** | - `describe`, `fit` (bounded and censored), `compare`, `compare_groups`, `crosstab`, EC7 `characteristic`.<br>- Plots P08 (distribution fit) and P09 (characteristic value profile). |
| v0.4 | | - Clogging: Hollmann & Thewes (2013) diagram (P18).<br>- QC level 2 (engineering-judgment ranges).<br>- Standards comparison with a library of published ranges.<br>- User-defined PSD regions; plasticity-chart data region.<br>- Compaction curve (P16). |
| v0.5 | | - Consolidation (P13–P15) analyses and plots.<br>- **AGSi export** (`to_agsi()`): 1D model elements per geology unit, carrying property summaries and parameters (including depth-trend design lines), with codes from the column registry. |
| v0.6 | | - Soil modulus from multiple sources (P20).<br>- Pressuremeter → Hardening Soil parameters (P19). |
| Later | | - **AGSi import** (unit definitions and design parameters, compared with hangtu statistics).<br>- Multiple AGS files per project (merging, LOCA_ID conflicts, multiple datums).<br>- DIGGS ingestion; AGS3 → AGS4; CPT (P22).<br>- GeoPackage export; simple location plan (P21).<br>- Lateral earth pressure with depth (P23).<br>- Better UI; regex/fuzzy text matching; conditional minimally-useful-field rules.<br>- Cohesive/cohesionless helper; inch display for coarse particle sizes.<br>- Title block and drafting templates. |

### 1.4 Non-goals (through v0.3)
- Writing or editing AGS files (except test fixtures).
- Limit-state design calculations.
- Inclined-hole geometry (flagged only).
- GIS and mapping.
- Multi-user database access.

---

## 2. Units

### 2.1 Background
- An AGS4 file declares units per column in its `UNIT` row, and every unit used must be defined in the file's `UNIT` group (AGS4 Rule 15).
- The dictionary only *suggests* SI units. US files commonly use `ft`, `in`, `psf`, `ksf`, `tsf`, `pcf`, `%`, and particle sizes in `mm` (sieves) or `in` (coarse particles).
- The UNIT row is **not always a physical unit**. For type `DT` it holds a date format, and for `T` an elapsed-time format.

### 2.2 Decisions
| Item | Decision |
|---|---|
| Storage (Phase 2) | **Convert to SI on ingest**; original text and unit kept in the raw layer. Two exceptions are kept as written: a unit the file defines that hangtu doesn't know, and a known unit no quantity kind covers (`kN/mm`) ([`docs/data/ingest.md`](docs/data/ingest.md) §7) |
| Display | `display_units = "US" \| "SI"`: a session or project setting, plus a `display_units=` argument on every plot, query and stats function. Per-quantity overrides are in the config |
| Engine | [`pint`](https://pint.readthedocs.io) with a hangtu registry (custom definitions + alias table) |
| Unknown units | Never guessed. Phase 1: clear error naming the column. Phase 2: raw-only column + QC error `U001`, except a user-defined heading whose unit the file's `UNIT` group defines: numbers kept as written, not converted, info `U005` |
| Alias matching | **Case-sensitive only** (explicit is better than implicit) |
| Canonical units | One SI unit per quantity kind. SPT N and blow counts are counts and never converted |

### 2.3–2.5 Unit table, aliases, traps
Phase 1: [`docs/plots/P00-framework.md`](docs/plots/P00-framework.md) §4. Rules that only apply on AGS ingest: [`docs/data/ingest.md`](docs/data/ingest.md) §7.

### 2.6 Units for DataFrames (Phase 1)
Plots and analyses work on DataFrames that may come from anywhere, so the units of each column must be declared or known:

```python
spt = ht.read_csv("spt.csv", units={"depth": "ft", "elevation": "ft"})  # declare units on load
spt = ht.set_units(df, {"depth": "ft", "hydraulic_conductivity": "cm/s"})  # or on an existing DataFrame
ht.units_of(spt)                                                        # -> {"depth": "ft", ...}
```
- Units are stored in `df.attrs["units"]`. Columns whose quantity kind is dimensionless or a count (`spt_n`, `spt_n60`, `liquid_limit`, …) need no declaration.
- **Resolution order in every plot or analysis:**
  1. an explicit argument;
  2. `df.attrs["units"]`;
  3. the column registry plus the session/project display system (Phase 2 datasets only);
  4. otherwise **error for an analysis**, or **"(units unknown)" label plus a warning for a plot**. Nothing is silently guessed.
- **Where attrs get lost:** `df.attrs` survives filtering, column selection, `.copy()` and sorting. It is **lost or unreliable** after `merge`/`join`, `concat` of frames with different attrs, `groupby().agg()`, file round trips, and user-built frames. Hence the explicit-argument fallback, and the clear error or label when units are unknown.
- **CSV templates:** `ht.template("spt")` returns an empty DataFrame with the registry columns. `ht.template("spt").to_csv(...)` gives users a file to fill in. Each template column's description and expected quantity are listed by `ht.columns("spt")`. The `spt`, `atterberg`, `grain_size` and `permeability` templates are their Phase 2 dataset's columns in the same order, without those only hangtu produces (`source_line`, `energy_source`, `spt_n_capped`, `liquidity_index`, `consistency_index`), so CSV and AGS data reach the plots in the same shape (decided 2026-10-14, `docs/work/m9-release.md`).

### 2.7–2.8 Settings and acceptance tests
Settings and Phase 1 tests: P00 §3 and §14. Phase 2 tests: the drafts file above.

---

## 3. Plotting (Phase 1)

Full conventions are in [`docs/plots/README.md`](docs/plots/README.md); each figure has its own spec. Summary of the decisions:
- **Function contract:** `ht.plot.<name>(df, *, ..., ax=None, display_units=None) -> (fig, ax)`. Analysis plots also return a result object. `ax=` enables `Sheet` composition. Analysis code lives in `ht.analysis.*` and can be used without plotting.
- **Input:** tidy DataFrames with registry column names (§10.3) and declared units (§2.6). There is no dependency on the database.
- **House style** (agreed for now): sans-serif font, 8–9 pt, light grids, legend outside right. Applied in a context manager, so the user's matplotlib state is untouched. No company drafting standard.
- **Axes:** depth points downward and elevation upward. Labels include units and the datum (e.g. "Elevation (ft, NAVD88)").
- **Log scales:** supported by profile, histogram, geology-unit comparison and fit plots (for permeability etc.).
- **Out-of-range data is never dropped silently:** it's drawn at the edge with an arrow and a count. Flagged values (refusal, NP, `<x`, `>x`) are drawn distinctly or counted.
- **Geology colors:** a `{unit: color}` palette, resolved in this order:
  1. an explicit `palette=` argument;
  2. the session/project palette (from the mapping file's `color` in Phase 2);
  3. automatic assignment from `tab20`, in stratigraphic `order` if known, otherwise sorted unit names. It is remembered for the session, so a unit keeps the same color in every plot.

  Helpers: `ht.plot.palette_cmap()` and `ht.plot.legend_handles()`.
- **Sheets:** `ht.Sheet(size="tabloid", layout=(2, 2), title=...)`.
  - GridSpec, with spanning panels.
  - Sizes: Letter, Tabloid (default), ANSI D, A4, A3.
  - Exports to PDF, PNG or SVG.
  - Simple title only; no title block (Later).
- **Plot list and status:** see `docs/plots/README.md`.
  - Batch 1 (P00–P07): P00–P03 and P07 are v0.1, P04–P06 are v0.2 (§1.3).
  - P08–P09 are v0.3.
  - P11–P12 and P17 are v0.2; P13–P16 are v0.4–v0.5.

---

## 4. Analyses (Phase 1 unless noted)
Analysis code lives in `ht.analysis.*`, as plain functions usable without plotting. Detail is in [`docs/drafts/analysis.md`](docs/drafts/analysis.md): §1 SPT (refusal, N60, cap, classes) is decided; §2 Atterberg and classification and §3 grain size are decided (M8), with values to verify against the standards (TODO #5); §4 SPT correlations is a draft until M13. Decisions that more than one plot depends on:
- **SPT refusals** are included by default at the cap value (`spt_cap = 100`) with a note. Statistics treat them as censored.
- **N60** stays NULL until an energy ratio or `hammer_efficiency` is given. There is no default.
- **NP** is distinct from blank everywhere and shown as a count on plots.
- **Classification systems** (plasticity chart, size fractions, sieve axis) are selectable per call and defined in the config.
- **Correlations** (decided 2026-10-15; SPT first, in v0.2) live in `ht.analysis.correlations`, one function per published correlation. Each one:
  - states its equation and cites its source, with constants kept in the source's units;
  - says when it applies and when it doesn't: soil types, input range, which N it was derived with (field N, N60 or (N1)60), the data and region behind it, and known biases. This is in the docstring and in metadata attached to the result, so a plot or report can show it;
  - returns NaN with a count outside its range, and never clips or extrapolates the input;
  - returns rows that name the correlation, so several estimates of one property compare on P01 (`color_by=`) or P07.
- **Effective vertical stress** (decided 2026-10-15) comes from `ht.analysis.vertical_stress()`, with the unit weight (a value or a profile, step or linear) and the groundwater level for each hole given in the call. (N1)60 and the correlations take its σ′v column. Detail in analysis draft §4.1.

---

## 5. Statistics (Phase 3, v0.3)
- All functions take an array, a Series, or a DataFrame plus `value=`/`by=`.
- All accept `log=True`.
- They return result objects with readable summaries, `.to_frame()` and `.to_dict()` (the latter for later AGSi export).
- Results record whether they summarize test values (*properties*) or give interpreted design values (*parameters*), plus the method, n and source.

- Functions: `describe`, `fit`, `compare`, `compare_groups`, `crosstab`, `characteristic`. Draft behavior is in [`docs/drafts/phase3-stats.md`](docs/drafts/phase3-stats.md) (TODO #8–#13).

P07 (property by geology unit against a report's baseline ranges) is a Phase 1 *plot*: it computes its percentiles with NumPy and doesn't need the statistics module.

---

## 6. Ingestion (Phase 2, v0.1)
Decided constraints only. The pipeline, database layout, keys, version mapping, typing and units are in [`docs/data/ingest.md`](docs/data/ingest.md).

### 6.1 Pipeline
- `python-ags4` validates and parses the file. hangtu writes a raw layer, then types, converts units and flags values into the canonical layer, reading each heading through the 4.2 dictionary.

### 6.2 Rules
- **Validation** (decided): *ingest with warnings*. Each python-ags4 finding becomes a QC finding `V<rule>`. Ingest fails only if the file can't be parsed.
- **Versions:** 4.0.3, 4.0.4, 4.1, 4.1.1 and 4.2. **The reference version is 4.2.** No group or heading was renamed from 4.0.3 to 4.2, only removed, so older files need no mapping: groups and headings that 4.2 removed (`IPRG`, `IPRT`, `ERES`, a few headings) are kept under their own names and read through their own version's dictionary (decided 2026-10-14).
- **One file per project** (decided). The file's SHA-256 is stored and checked on open.
- **User-defined groups and headings** are kept in the raw layer, and typed where the unit is known.
- **Blank vs flagged** (decided): blank → NULL, no flag. Recognized text (`NP`, `Dry`, an incomplete drive in `ISPT_REP` (refusal), `<x`, `>x`) → NULL or bound + a value flag. Unrecognized text → flag `OTHER` + QC `T001`. NP is never the same as blank.

---

## 7. Data model (Phase 2)

**Canonical layer** (decided 2026-10-13, was TODO 0b): **AGS 4.2-shaped tables**, typed and in SI, rather than a hybrid entity/observation model.
- **Why:** most criticisms of AGS as a storage model assume a long-lived database that people edit. hangtu reads one file per project (§6.2), never writes AGS (§1.4), and can rebuild the database from the file at any time. Correcting a depth means a new file and a re-ingest, not re-keying child records, and the file is the history.
- An observation model would need a property vocabulary for every heading, user-defined groups included. AGS-shaped tables take every group, user-defined ones too, as they come.
- Queries across test types (all undrained strengths, whatever the test) and the method behind each value are handled by the datasets (§10.2), which combine groups into rows with `source` and `test_type` columns.
- **The choice can be reversed.** If an observation model is needed later (for DIGGS, or generic queries), it can be built as a view or a generated table on top of these tables, using the AGS sources in the column registry, followed by a re-ingest. Nothing needs migrating.

**Rules:**
- **SQLite only.** All access goes through `db.py`.
- **Raw layer:** `raw_<GROUP>`, every heading as TEXT exactly as in the file, plus `_line`. Used by validation and `diff()`.
- **Canonical layer:** one table per group, named after it (`ISPT`), with the AGS 4.2 heading names. Groups and headings from older versions that 4.2 removed keep their own names (§6.2), and DIGGS will later be mapped into the same shape.
- **Integer surrogate keys** for locations, samples and specimens. Every child table carries `location_id`, `sample_id` and `specimen_id` as they apply, resolved at ingest. Joins use them, never the AGS key columns, which are kept as columns. A child record whose parent can't be found is a QC finding.
- **Value flags** live in a table of their own, one row per flagged cell (table, row, heading, flag, bound), so a flag can be attached to any numeric heading. Datasets expose them as columns (`non_plastic`, `spt_refusal`).
- **Only what the file says.** Values hangtu calculates (N60, classifications, Dx) are not stored; the datasets and analyses compute them. A value given in the file (e.g. `ISPT_N60`) is stored as given.
- **Provenance:** every canonical row keeps its source file and `_line`, for `diff()` and QC messages.
- **Schema version** is stored in the metadata. If it doesn't match the installed hangtu on open, the user is told to re-ingest.
- **Metadata tables** (`meta_*`) for settings, source files, heading units, value flags and the geology map.
- **Extension tables** for things AGS lacks: the project's vertical datum and where it came from (a setting, or the file's `LOCA_DATM` where that is unambiguous; [`docs/data/ingest.md`](docs/data/ingest.md) §7), horizontal CRS, flags, provenance.
- **The public API never depends on the canonical layout.** Users see the column registry (§10.3), datasets and functions. Only `sql()` and `table()` expose internal names.

---

## 8. Depth, elevation and geology conventions
Apply in both phases. In Phase 1 they are applied by the analysis functions to the columns users supply.

### 8.1 Elevation
- `elevation = ground_level − depth`. Plots accept either an `elevation` column, or `depth` plus `ground_level`.
- Vertical holes only (decided). Non-vertical holes are flagged (QC `L004`).

### 8.2 Test depth
| Data | Depth used (decided) | `depth_basis` |
|---|---|---|
| SPT (Phase 2, AGS) | Middle of the test drive: `top + seating penetration + test penetration / 2`, from the increment penetrations | `mid_drive` |
| SPT (Phase 2), increments missing | The same formula with a nominal 150 mm seating drive and the rest of the total penetration as the test drive; `top + 300 mm` for a full test or no total (decided 2026-10-14, `docs/data/datasets.md` §6.1) | `mid_drive_nominal` |
| SPT (Phase 1, CSV) | `depth` as given; the template has no increments (decided, analysis.md §1.2) | — |
| Lab tests | Specimen depth → else sample midpoint → else sample top | `spec_depth` / `sample_mid` / `sample_top` |
| Field permeability | Midpoint of the test zone | `zone_mid` |
| Intervals (geology, samples) | Top and base kept as-is | — |

### 8.3 Geology
- **Geology key** (decided): configurable as the setting `geology_key`, default `GEOL_GEOL`. Options: `GEOL_GEO2`, `GEOL_LEG`, `GEOL_FORM`, `GEOL_BGS`, plus a mapping file. hangtu never falls back to another heading on its own. Several fields can be carried side by side (`geology_fields=`) and compared using `crosstab`.
- **Mapping file** (CSV: `code, geology_unit, soil_class, order, color`; stored with the project):
  - **exact, case-sensitive match** (decided);
  - `soil_class` drives the cohesive/cohesionless split (🔬 TODO #3);
  - `color` feeds the palette.
- **Interval rule** (decided): `top ≤ d < base`. At the bottom of the hole, `d = base` belongs to the last interval. For overlaps, the lowest top (the deepest) wins.
- Unmapped codes are kept as their own units, with a warning and QC G004; they are never dropped.

---

## 9. Data quality (Phase 2)

### 9.1 Levels
| Level | What | When |
|---|---|---|
| 1: Integrity | Format, units, structure, internal consistency | v0.1 |
| 2: Engineering judgment | User-defined plausible ranges per unit and property | v0.4 |

### 9.2 Framework (decided)
- `p.qc()` returns a report; the findings export to **one flat CSV**, with the rule settings the run used written next to it (`<stem>_rules.csv`), so a report sent on its own says what it was checked against.
- Rules (id, severity, thresholds) live in YAML and can be overridden per call. **Thresholds are quantity strings with units** (`0.01 m`, `"0.05 ft"`), read like any other unit (§2.6); counts are plain numbers.
- QC is computed on demand; only ingest validation is persisted.
- **Reviewed findings can be accepted**, each with a reason, in a YAML file passed per call (`p.qc(accepted=...)`). Accepted findings stay in the report, marked, and an entry that matches nothing is shown, so a review never hides data.
- `p.diff(group)` compares raw and canonical values cell by cell.
- Rules, report and diff: [`docs/data/qc.md`](docs/data/qc.md).

---

## 10. Datasets and column registry

### 10.1 Project access (Phase 2)
`p.groups`, `p.table(group, raw=False)`, `p.locations`, `p.set_geology_map(path)`, `p.geology_map`, `p.diff(group, heading=None, changed_only=False)`, `p.sql(...)` (read-only, SI).

### 10.2 Ready-made datasets (Phase 2)
- `p.spt()`, `p.atterberg()`, `p.grain_size()` and `p.permeability()` (M7, v0.1); `p.grain_size_summary()`, `p.index_properties()` and the classification columns (M8, built for v0.2).
- **Several specimens of a test in one sample** (decided 2026-10-15, M8): `p.index_properties()` uses the one nearest in depth to the water content specimen and names it in a column, with a warning. No row is multiplied (`docs/data/datasets.md` §6.6).
- They return DataFrames in **exactly the shape the Phase 1 plots expect**: the same registry column names, with units attached, in the project's display units unless `display_units=` says otherwise. Columns and rules: [`docs/data/datasets.md`](docs/data/datasets.md).
- **Common filters:** `where=`, `contains=`, `elevation=`, `depth=`, `holes=`, `geology=`, `geology_fields=`, `include_incomplete=`, `display_units=` (naming decided).

### 10.3 Column registry (both phases)
- `src/hangtu/columns.yaml` is the single source of truth for friendly column names. For each column it records:
  - description;
  - quantity kind (for units);
  - scale (ratio or interval);
  - the AGS source (`ISPT.ISPT_NVAL`, or `derived: ...`);
  - later, an optional AGSi code.
- `ht.columns("spt")` prints it, `ht.template()` builds CSV templates from it, and docstrings are generated from it.
- Phase 1 plot specs define the columns they need; the registry is assembled from those definitions.
- Schema and rules: P00 §5. Entries: [`src/hangtu/columns.yaml`](src/hangtu/columns.yaml). **Names are written out in full** (decided; explicit is better than implicit): `undrained_shear_strength`, not `su`/`cu`. Rules and accepted short forms are in CLAUDE.md, "Naming".

---

## 11. API sketch

**Phase 1 (v0.1–v0.2): plots on your own data**
```python
import hangtu as ht

ht.settings.display_units = "US"
ht.settings.vertical_datum = "NAVD88"

spt = ht.read_csv("spt.csv", units={"depth": "ft", "ground_level": "ft"})
k = ht.read_csv("perm.csv", units={"depth": "ft", "hydraulic_conductivity": "cm/s"})

fig, ax = ht.plot.profile(k, value="hydraulic_conductivity", preset="hydraulic_conductivity")       # log axis, P01
fig, ax = ht.plot.spt_profile(spt, vs="elevation")                   # P02
fig, ax = ht.plot.spt_histogram(spt, table="cohesionless")           # P03
fig, ax = ht.plot.plasticity_chart(atterberg, system="uscs")         # P04
fig, ax = ht.plot.grain_size(curves, d_values=True)                  # P05

sheet = ht.Sheet(size="tabloid", layout=(1, 2), title="Site X")
ht.plot.spt_profile(spt, ax=sheet[0])
ht.plot.profile(k, value="hydraulic_conductivity", preset="hydraulic_conductivity", ax=sheet[1])
sheet.save("site_x.pdf")
```

**Phase 2 (v0.1): the same plots, fed from AGS**
```python
p = ht.Project.from_ags("site.ags", db="site.sqlite", display_units="US")   # later: ht.Project.open("site.sqlite")
p.set_geology_map("strata.csv")
p.qc().to_csv("qc_report.csv")
fig, ax = ht.plot.spt_profile(p.spt(geology=["Alluvium"]))
```

**Phase 3 (v0.3): statistics**
```python
ht.stats.describe(spt, value="spt_n60", by="geology_unit")
ht.stats.characteristic(spt.loc[spt.geology_unit == "Alluvium", "spt_n60"], estimate="mean", vx=0.30, vx_source="assumed")
```

**Error-message standard:** messages are written for engineers. They say what is wrong, where, and what to do. No raw tracebacks for anticipated data problems.

---

## 12. Engineering

### 12.1 Environment and distribution
- Python ≥ 3.12, developed with `uv`.
- PyPI + public GitHub, MIT license.
- **CI:** GitHub Actions on Windows, macOS and Linux × Python 3.12–3.14 (ruff + pytest). Release to PyPI on a `v*` tag (trusted publishing, `release.yml`): the tag must match the version in `pyproject.toml`, and the test suite runs against the built wheel on all three operating systems before upload. A manual run publishes to TestPyPI instead. Before either upload, the scripts in `examples/` run against the built wheel in an empty directory on all three operating systems.
- **0.0.1** is a placeholder release that claims the name on PyPI before v0.1 (decided 2026-10-12). It contains the M2b state: P00, P01 and P07.
- **0.1.0** (M9) is the first release meant for use: P00–P03 and P07, the SPT analysis, AGS4 ingest, QC and the four datasets, with `examples/` and the example data in `ht.examples`.
- **Docs:** the README and `examples/` for v0.1 (decided 2026-10-14), and a docs site built with Zensical, ahead of v0.2 rather than after feedback, so potential users can find what hangtu does and the site grows with each feature (decided 2026-10-16, `docs/work/docs-site.md`).
  - The source is `docs/site/` (`zensical.toml` at the root); the internal specs elsewhere in `docs/` aren't published. `docs/prepare_site.py` runs each page's example and writes the figures, the column page and the logo before a build.
  - The API reference is generated from the numpy docstrings (mkdocstrings), so a docstring is user documentation. Math is MathJax.
  - The site follows `main`, not the last release: `docs.yml` deploys to GitHub Pages when a push to `main` changes what the site is built from. Users who want what the site describes install from GitHub.
  - Zensical and `mkdocstrings-python` are in a `docs` dependency group, not runtime dependencies. Zensical is pinned exactly while it is alpha.
- **Phase 1 dependencies:** `pandas>=2.1.1,<3`, `numpy>=1.26`, `matplotlib>=3.8`, `pint>=0.24.4`, `pyyaml>=6.0.1`. Each floor is the oldest release that installs and imports on Python 3.12 with current transitive dependencies, and a lowest-version CI job keeps it honest.
- **Phase 2 adds** `python-ags4>=1.2.0` (LGPL-3.0, used unmodified, which is compatible with MIT; 1.2.0 is the first release with the 4.2 dictionary). It brings `click`, `rich`, `openpyxl` and `defusedxml` with it; its standard dictionaries (4.0.3–4.2) are what ingest reads units, types and keys from. The project database uses the `sqlite3` module with STRICT tables, which need SQLite ≥ 3.37; a test checks it on every CI platform.
- **Phase 3 adds** `scipy>=1.11`.
- **Dev dependencies:** `pytest>=8.0`, `ruff>=0.17`, `hypothesis>=6.100`, optionally `pytest-mpl`.

### 12.2 Package layout
- `src/` layout, package `hangtu`.
- Top-level namespaces: `ht.plot`, `ht.analysis`, `ht.stats` (Phase 3), `ht.Project` (Phase 2), `ht.Sheet`, `ht.settings`, `ht.examples` (example data files), plus `read_csv`, `set_units`, `units_of`, `columns`, `template`.
- Phase 2 modules: `ags/` (the ingest pipeline), `qc/` (QC rules and report), `datasets/` (joins and datasets), `db.py` (the only module that talks to SQLite, §7) and `project.py`.
- Data files ship inside the package: `columns.yaml` (registry), `config/defaults.yaml`, `units/*.yaml`, `ags/value_flags.yaml`, `qc/rules.yaml`, `qc/min_fields.yaml`, and the example data in `examples/data/`.
- Tests mirror the package (`tests/plot/`, `tests/units/`, …), with synthetic data in `tests/data/`. Runnable scripts go in `examples/`.

### 12.3 Testing
- **Phase 1:**
  - synthetic CSV datasets with hand-calculated answers (N60, mid-drive depth, Dx/Cu/Cc, USCS/AASHTO boundary cases);
  - plot smoke tests: renders; labels and units; every overlay toggle; `ax=` composition;
  - US vs SI equivalence: same figure apart from labels and ticks;
  - acceptance criteria from each plot spec.
- **Phase 2:**
  - synthetic SI/US twin AGS files (both pass python-ags4), plus a defects file (one per QC rule);
  - public data (BGS, Hong Kong CEDD) fetched into a git-ignored cache (`pytest -m public`), with invariants, US-unit twins of real files, and a performance budget (🔬 TODO #14).
- **Phase 3:** JRC worked examples for EC7; scipy reference values.

### 12.4 Milestones
Rows are in build order. M8 comes after M9 since v0.1 moved ahead of P04–P06 (§1.3); it keeps its number because other documents refer to it. M10 (a feedback round) was dropped, and its number isn't reused.

| M | Deliverable | Done when |
|---|---|---|
| M0 | Scaffolding: src layout, deps, ruff, pytest, CI matrix, MIT license | CI green |
| M1 | **P00 framework**: settings, units for DataFrames (§2.6), column registry, style, palette, label and out-of-range helpers, `Sheet` | Framework tests pass; a dummy plot composes on a Sheet |
| M2 | **P01** property profile | P01 acceptance criteria met |
| M2b | **P07** property by geology unit (moved ahead of M3 from M5) | P07 acceptance criteria met |
| M3 | **P02–P03** + SPT analysis | P02/P03 criteria + SPT golden tests |
| M4 | Phase 2 design: data model decided (§7) and build order changed (§1.3). Each later Phase 2 unit turns its part of `docs/drafts/phase2-data.md` into its own intent and spec | Decisions recorded in SPEC |
| M5 | AGS4 ingest: raw and canonical layers in SQLite, units on ingest, value flags (§6, §7) | Twin-file test and ingest acceptance criteria met |
| M6 | QC level 1, CSV report and `diff()` (§9) | One defects-file test per rule |
| M7 | Depth/elevation/geology joins and ready-made datasets (§8, §10) | Datasets feed the Phase 1 plots directly |
| M9 | Examples (CSV → plot and AGS → QC → plot), CSV templates, README → **v0.1.0 on PyPI** | Examples run from a clean `pip install` |
| M8 | **P04–P06** + classification and gradation analyses, and the datasets that need them | P04–P06 criteria + classification/Dx golden tests |
| M11 | **P11–P12** triaxial: Mohr–Coulomb fit, failure envelope, stress–strain curves and measured stress paths | P11/P12 criteria + fit golden tests |
| M12 | **P17** clogging diagram (Thewes & Burger 2004) | P17 criteria; zones match the source |
| M13 | **SPT correlations** and (N1)60 → **v0.2** | Golden values from each source; out-of-range counts |
| M14+ | Phase 3 | Defined when Phase 3 starts |

---

## 13. Open questions
None open. #1 (SPT mid-drive fallback) was settled in M7 and #2 (specimen combining) in M8, §10.2.
