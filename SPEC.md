# hangtu — Product Specification

**Status:** Draft.

**What belongs here:** decisions that constrain more than one feature, plus scope and phasing. Per-feature detail lives in that feature's spec (e.g. `docs/plots/PXX-*.md`). Detail for later phases is held in `docs/drafts/` until those phases start. Update this file in the same commit as any change that alters a decision. How the process works: [`docs/reference/process.md`](docs/reference/process.md).

**Conventions**
- **Decided**: agreed in review.
- 🟡 **Proposed**: Claude's proposed default, awaiting review.
- ❓ **Open**: needs input (collected in §13).
- 🔬 **Research**: tracked in [TODO.md](TODO.md).

**Document map**
| Document | Contents |
|---|---|
| `SPEC.md` (this file) | Scope, phasing, cross-cutting decisions (units, data, conventions, QC, statistics, engineering) |
| [`docs/plots/README.md`](docs/plots/README.md) | Shared plot conventions, and the plot list with each plot's status |
| `docs/plots/PXX-*.md` | One spec per figure, from [`TEMPLATE.md`](docs/plots/TEMPLATE.md) |
| [`docs/drafts/`](docs/drafts/) | The analyses draft spec and notes for later phases (Phase 2 data, Phase 3 statistics) |
| [`docs/reference/eurocode7-summary.md`](docs/reference/eurocode7-summary.md) | Background for characteristic values |
| [`TODO.md`](TODO.md) | Research items and pending decisions |
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
  - Check that the name is still free on PyPI right before the first release (M5).

### 1.2 Formats
| Format | Role | When |
|---|---|---|
| **AGS4** (4.0.3–4.2) | Factual input | Phase 2 |
| **DIGGS** | Factual input (mapped into the same internal model) | Later |
| **AGSi** (v1.0.1) | Interpreted output (ground model, property summaries, design parameters); later also input | v0.5 export, later import |
| **CSV / DataFrame** | Input for plots and statistics, using the documented column names. CSV only (decided): no Excel reader; users convert their own workbooks | **Phase 1** |

### 1.3 Phases and roadmap
**Why plots come first (decided):** plots are what users will use first, so building them first gets feedback soonest. Plot and analysis functions take DataFrames, so they don't need the AGS ingest or database to be useful.

| Version | Phase | Content |
|---|---|---|
| **v0.1** | **1: Plots** | - Plot framework (P00): style, palette, unit-aware labels, out-of-range markers, `Sheet`.<br>- Batch 1 plots **P01–P07**: property profile, SPT profile, SPT histograms, plasticity chart, grain size, water content profile, box plots.<br>- The analyses they need: SPT N60/refusal/classes, plasticity classification, Dx/Cu/Cc/gradation.<br>- Units handling for DataFrames (§2.6), the column registry, CSV templates.<br>- **First PyPI release; feedback round.** |
| **v0.2** | **2: Data** | - AGS4 ingest (units on ingest, value flags) into SQLite.<br>- QC level 1 with CSV report and diff tool.<br>- Depth/elevation/geology conventions and joins.<br>- Ready-made datasets (SPT, Atterberg/index properties, grain size, permeability) that feed the Phase 1 plots directly.<br>- **Blocked by TODO 0b (internal data model).** |
| **v0.3** | **3: Statistics** | - `describe`, `fit` (bounded and censored), `compare`, `compare_groups`, `crosstab`, EC7 `characteristic`.<br>- Plots P08 (distribution fit) and P09 (characteristic value profile). |
| v0.4 | | - Clogging (P17–P18; Thewes & Burger 2004, Hollmann & Thewes 2013).<br>- QC level 2 (engineering-judgment ranges).<br>- Standards comparison with a library of published ranges.<br>- User-defined PSD regions; plasticity-chart data region.<br>- Compaction curve (P16). |
| v0.5 | | - Triaxial (P10–P12) and consolidation (P13–P15) analyses and plots.<br>- **AGSi export** (`to_agsi()`): 1D model elements per geology unit, carrying property summaries and parameters (including depth-trend design lines), with codes from the column registry. |
| v0.6 | | - Soil modulus from multiple sources (P20).<br>- Pressuremeter → Hardening Soil parameters (P19).<br>- (N1)60. |
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
| Storage (Phase 2) | **Convert to SI on ingest**; original text and unit kept in the raw layer |
| Display | `display_units = "US" \| "SI"`: a session or project setting, plus a `display_units=` argument on every plot, query and stats function. Per-quantity overrides are in the config |
| Engine | [`pint`](https://pint.readthedocs.io) with a hangtu registry (custom definitions + alias table) |
| Unknown units | Never guessed. Phase 1: clear error naming the column. Phase 2: raw-only column + QC error `U001` |
| Alias matching | **Case-sensitive only** (explicit is better than implicit) |
| Canonical units | One SI unit per quantity kind. SPT N and blow counts are counts and never converted |

### 2.3–2.5 Unit table, aliases, traps
Phase 1: [`docs/plots/P00-framework.md`](docs/plots/P00-framework.md) §4. Rules that only apply on AGS ingest: [`docs/drafts/phase2-data.md`](docs/drafts/phase2-data.md) (Units on ingest).

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
- **CSV templates:** `ht.template("spt")` returns an empty DataFrame with the registry columns. `ht.template("spt").to_csv(...)` gives users a file to fill in. Each template column's description and expected quantity are listed by `ht.columns("spt")`.

### 2.7–2.8 Settings and acceptance tests
Settings and Phase 1 tests: P00 §3 and §14. Phase 2 tests: the drafts file above.

---

## 3. Plotting (Phase 1)

Full conventions are in [`docs/plots/README.md`](docs/plots/README.md); each figure has its own spec. Summary of the decisions:
- **Function contract:** `ht.plot.<name>(df, *, ..., ax=None, display_units=None) -> (fig, ax)`. Analysis plots also return a result object. `ax=` enables `Sheet` composition. Analysis code lives in `ht.analysis.*` and can be used without plotting.
- **Input:** tidy DataFrames with registry column names (§10.3) and declared units (§2.6). There is no dependency on the database.
- **House style** (agreed for now): sans-serif font, 8–9 pt, light grids, legend outside right. Applied in a context manager, so the user's matplotlib state is untouched. No company drafting standard.
- **Axes:** depth points downward and elevation upward. Labels include units and the datum (e.g. "Elevation (ft, NAVD88)").
- **Log scales:** supported by profile, histogram, box and fit plots (for permeability etc.).
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
  - Batch 1 (P00–P07) is v0.1.
  - P08–P09 are v0.3.
  - Batch 2 lab analyses (P10–P16) are v0.4–v0.5.

---

## 4. Analyses (Phase 1 unless noted)
Analysis code lives in `ht.analysis.*`, as plain functions usable without plotting. Detail (SPT refusal and N60, plasticity systems, classification, Dx/Cu/Cc) is in the draft spec [`docs/drafts/analysis.md`](docs/drafts/analysis.md) (§1 SPT, §2 Atterberg, §3 grain size). Decisions that more than one plot depends on:
- **SPT refusals** are included by default at the cap value (`spt_cap = 100`) with a note. Statistics treat them as censored.
- **N60** stays NULL until an energy ratio or `hammer_efficiency` is given. There is no default.
- **NP** is distinct from blank everywhere and shown as a count on plots.
- **Classification systems** (plasticity chart, size fractions, sieve axis) are selectable per call and defined in the config.

---

## 5. Statistics (Phase 3, v0.3)
- All functions take an array, a Series, or a DataFrame plus `value=`/`by=`.
- All accept `log=True`.
- They return result objects with readable summaries, `.to_frame()` and `.to_dict()` (the latter for later AGSi export).
- Results record whether they summarize test values (*properties*) or give interpreted design values (*parameters*), plus the method, n and source.

- Functions: `describe`, `fit`, `compare`, `compare_groups`, `crosstab`, `characteristic`. Draft behavior is in [`docs/drafts/phase3-stats.md`](docs/drafts/phase3-stats.md) (TODO #8–#13).

Box plots with published-range overlays (P07) are a Phase 1 *plot* and don't need the statistics module.

---

## 6. Ingestion (Phase 2, v0.2)
Decided constraints only. The pipeline, type mapping and version notes are in [`docs/drafts/phase2-data.md`](docs/drafts/phase2-data.md).

### 6.1 Pipeline
- `python-ags4` validates and parses the file. hangtu writes a raw layer, maps older versions up to 4.2, then types, converts units and flags values into the canonical layer.

### 6.2 Rules
- **Validation** (decided): *ingest with warnings*. Each python-ags4 finding becomes a QC finding `V<rule>`. Ingest fails only if the file can't be parsed.
- **Versions:** 4.0.3, 4.0.4, 4.1, 4.1.1 and 4.2. **The reference version is 4.2.** Older versions are mapped up.
- **One file per project** (decided). The file's SHA-256 is stored and checked on open.
- **User-defined groups and headings** are kept in the raw layer, and typed where the unit is known.
- **Blank vs flagged** (decided): blank → NULL, no flag. Recognized text (`NP`, `Dry`, refusal, `<x`, `>x`) → NULL or bound + a value flag. Unrecognized text → flag `OTHER` + QC `T001`. NP is never the same as blank.

---

## 7. Data model (Phase 2) — ❓ pending TODO 0b

**Decided, whichever option is chosen:**
- **SQLite only.** All access goes through `db.py`.
- **Raw layer:** `raw_<GROUP>`, every heading as TEXT exactly as in the file, plus `_line`. Used by validation and `diff()`.
- **Metadata tables** (`meta_*`) for settings, source files, heading units, value flags and the geology map.
- **Integer surrogate keys** for locations, samples and specimens. AGS keys are kept as columns.
- **Extension tables** for things AGS lacks: datum/CRS, flags, provenance.
- **The public API never depends on the canonical layout.** Users see the column registry (§10.3), datasets and functions. Only `sql()` and `table()` expose internal names.

**Pending choice:** AGS 4.2-shaped tables vs. a hybrid entity/observation model (TODO 0b; options in the drafts file).

---

## 8. Depth, elevation and geology conventions
Apply in both phases. In Phase 1 they are applied by the analysis functions to the columns users supply.

### 8.1 Elevation
- `elevation = ground_level − depth`. Plots accept either an `elevation` column, or `depth` plus `ground_level`.
- Vertical holes only (decided). Non-vertical holes are flagged (QC `L004`).

### 8.2 Test depth
| Data | Depth used (decided) | `depth_basis` |
|---|---|---|
| SPT | Middle of the test drive: `top + seating penetration + test penetration / 2`, from the increment penetrations | `mid_drive` |
| SPT, increments missing | 🟡 `top + 300 mm`. If total penetration is under 450 mm: `top + total − 150 mm` (not less than `top`) | `mid_drive_nominal` |
| Lab tests | Specimen depth → else sample midpoint → else sample top | `spec_depth` / `sample_mid` / `sample_top` |
| Field permeability | Midpoint of the test zone | `zone_mid` |
| Intervals (geology, samples) | Top and base kept as-is | — |

### 8.3 Geology
- **Geology key** (decided): configurable, default `GEOL_GEOL`. Options: `GEOL_GEO2`, `GEOL_LEG`, `GEOL_FORM`, `GEOL_BGS`, or a mapping file. Several fields can be carried side by side (`geology_fields=`) and compared using `crosstab`.
- **Mapping file** (CSV: `code, unit, soil_class, order, color`):
  - **exact, case-sensitive match** (decided);
  - `soil_class` drives the cohesive/cohesionless split (🔬 TODO #3);
  - `color` feeds the palette.
- **Interval rule** (decided): `top ≤ d < base`. At the bottom of the hole, `d = base` belongs to the last interval. For overlaps, the lowest top wins.

---

## 9. Data quality (Phase 2)

### 9.1 Levels
| Level | What | When |
|---|---|---|
| 1: Integrity | Format, units, structure, internal consistency | v0.2 |
| 2: Engineering judgment | User-defined plausible ranges per unit and property | v0.4 |

### 9.2 Framework (decided)
- `p.qc()` returns a report; findings export to **one flat CSV**.
- Rules (id, severity, thresholds) live in YAML and can be overridden per project.
- QC is computed on demand; only ingest validation is persisted.
- `p.diff(group)` compares raw and canonical values cell by cell.
- The draft rule list (U/T/L/G/D/S/A/P/K/C) and the minimally-useful-fields YAML are in [`docs/drafts/phase2-data.md`](docs/drafts/phase2-data.md) (TODO #6, #7).

---

## 10. Datasets and column registry

### 10.1 Project access (Phase 2)
`p.groups`, `p.table(group, raw=False)`, `p.locations`, `p.diff(group)`, `p.sql(...)` (read-only, SI).

### 10.2 Ready-made datasets (Phase 2)
- `p.spt()`, `p.atterberg()`, `p.grain_size()` / `p.grain_size_summary()`, `p.index_properties()`, `p.permeability()`.
- They return DataFrames in **exactly the shape the Phase 1 plots expect**: the same registry column names, with units attached. Draft column lists are in the drafts file.
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

**Phase 1 (v0.1): plots on your own data**
```python
import hangtu as ht

ht.settings.display_units = "US"
ht.settings.vertical_datum = "NAVD88"

spt = ht.read_csv("spt.csv", units={"depth": "ft", "ground_level": "ft"})
k = ht.read_csv("perm.csv", units={"depth": "ft", "hydraulic_conductivity": "cm/s"})

fig, ax = ht.plot.profile(k, value="hydraulic_conductivity", preset="hydraulic_conductivity")       # log axis, P01
fig, ax = ht.plot.spt_profile(spt, vs="elevation")                   # P02
fig, axs = ht.plot.spt_histograms(spt)                               # P03
fig, ax = ht.plot.plasticity_chart(atterberg, system="uscs")         # P04

sheet = ht.Sheet(size="tabloid", layout=(1, 2), title="Site X")
ht.plot.spt_profile(spt, ax=sheet[0])
ht.plot.profile(k, value="hydraulic_conductivity", preset="hydraulic_conductivity", ax=sheet[1])
sheet.save("site_x.pdf")
```

**Phase 2 (v0.2): the same plots, fed from AGS**
```python
p = ht.Project.from_ags("site.ags", db="site.sqlite", display_units="US")
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
- **CI:** GitHub Actions on Windows, macOS and Linux × Python 3.12–3.14 (ruff + pytest). Release to PyPI on tag (trusted publishing).
- **Phase 1 dependencies:** `pandas>=2.1.1,<3`, `numpy>=1.26`, `matplotlib>=3.8`, `pint>=0.24.4`, `pyyaml>=6.0.1`. Each floor is the oldest release that installs and imports on Python 3.12 with current transitive dependencies, and a lowest-version CI job keeps it honest.
- **Phase 2 adds** `python-ags4` (LGPL-3.0, used unmodified, which is compatible with MIT).
- **Phase 3 adds** `scipy>=1.11`.
- **Dev dependencies:** `pytest>=8.0`, `ruff>=0.17`, `hypothesis>=6.100`, optionally `pytest-mpl`.

### 12.2 Package layout
- `src/` layout, package `hangtu`.
- Top-level namespaces: `ht.plot`, `ht.analysis`, `ht.stats` (Phase 3), `ht.Sheet`, `ht.settings`, plus `read_csv`, `set_units`, `units_of`, `columns`, `template`.
- Data files ship inside the package: `columns.yaml` (registry), `config/defaults.yaml`, `units/*.yaml`.
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
| M | Deliverable | Done when |
|---|---|---|
| M0 | Scaffolding: src layout, deps, ruff, pytest, CI matrix, MIT license | CI green |
| M1 | **P00 framework**: settings, units for DataFrames (§2.6), column registry, style, palette, label and out-of-range helpers, `Sheet` | Framework tests pass; a dummy plot composes on a Sheet |
| M2 | **P01** property profile | P01 acceptance criteria met |
| M3 | **P02–P03** + SPT analysis | P02/P03 criteria + SPT golden tests |
| M4 | **P04–P06** + classification and gradation analyses | P04–P06 criteria + classification/Dx golden tests |
| M5 | **P07**, examples, CSV templates, README/tutorial; PyPI name check → **v0.1.0 on PyPI** | Examples run from a clean `pip install` |
| M6 | Feedback round; Phase 2 design closed (**TODO 0b**) | Decisions recorded in SPEC |
| M7+ | Phase 2 milestones (ingest → QC → joins/datasets), then Phase 3 | Defined at M6 |

---

## 13. Open questions
1. **SPT nominal mid-drive fallback** (§8.2): OK as proposed?
2. **`index_properties()` specimen combining:** when one sample has several specimens of a test, use the one nearest the other test's depth and flag it, or keep every combination?
3. **Docs site** for v0.1.0, or README + examples only?
4. **Phase 1 data entry beyond CSV:** is `read_csv` + templates enough for the first feedback round? Or should v0.1 include a thin `ht.read_ags()` that returns python-ags4 tables converted to SI, without the database or QC, so testers can try plots on real AGS files? This would mean building part of Phase 2 (units on ingest) early. 🟡 Lean: CSV first; add `read_ags` only if testers ask.
