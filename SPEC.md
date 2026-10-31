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
| [`docs/drafts/`](docs/drafts/) | The analyses draft spec and notes for later work (Phase 2 data, Phase 3 statistics) |
| [`docs/drafts/parameters/`](docs/drafts/parameters/README.md) | Draft reference sheets, one per ground parameter, and the index that tracks each parameter's stages (§1.3) |
| `docs/site/parameters/NN-*.md` | A parameter's page on the docs site, promoted from its sheet by the wave that builds it |
| [`docs/reference/eurocode7-summary.md`](docs/reference/eurocode7-summary.md) | Background for characteristic values |
| [`docs/TODO.md`](docs/TODO.md) | Research items and pending decisions |
| [`CLAUDE.md`](CLAUDE.md) | Working conventions and commands for Claude Code |
| [`docs/reference/process.md`](docs/reference/process.md) | How work moves from intent to merged code |

---

## 1. Scope and phasing

**Purpose (decided 2026-10-21):** hangtu derives the ground parameters a geotechnical design needs, from the test data through to a model-ready parameter set, for soil and rock. The plots, the data layer, the analyses and the statistics are steps toward those parameters. hangtu goes as far as constitutive-model parameter sets (Mohr–Coulomb, Hardening Soil and HS-small, generalized Hoek–Brown with residual values, Soft Soil), described by the published model rather than by a software package. It is also a reference a practitioner can learn from: the docs site has a page per parameter on what it is, why it matters to a design and how it is determined, and each method's docstring gives its equation, inputs, range of validity and source.

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
| **AGSi** (v1.0.1) | Interpreted output (ground model, property summaries, design parameters); later also input Later (export, then import) |
| **CSV / DataFrame** | Input for plots and statistics, using the documented column names. CSV only (decided): no Excel reader; users convert their own workbooks | **Phase 1** |

### 1.3 Phases and roadmap
**Why plots came first (decided):** plots are what users will use first, so building them first gets feedback soonest. Plot and analysis functions take DataFrames, so they don't need the AGS ingest or database to be useful. "Phase 1/2/3" name those bodies of work (plots, the data layer, statistics); they no longer set the build order. Waves and milestones do.

**Stages (decided 2026-10-21, `docs/work/parameter-roadmap.md`):** every parameter climbs the same four stages, each a deliverable on its own:
- **A. Data:** a dataset with the measured values in registry columns, and QC checks from the parameter's pitfalls.
- **B. Direct derivation:** definitions and fits on the test results.
- **C. Correlations:** indirect estimates through the correlations framework (§4), each with its applicability.
- **D. Selection:** all sources compared against depth or geology unit, statistics, a characteristic value or design line, and the model parameter set (§5).

**Waves (decided 2026-10-21):** a wave moves several parameters forward a stage each, grouped by the engine they share, so each engine is built once. A parameter's stages can sit in different waves. Sheet numbers are those of [`docs/drafts/parameters/`](docs/drafts/parameters/README.md), whose index holds the sheet × stage table and each stage's status.

| Wave | Engine | Moves |
|---|---|---|
| 0 | User-defined groups and curves | Curves (triaxial q–ε and εv, rock triaxial, swelling against time, shear box displacement) carried in the AGS file, read robustly; built against a sample dataset from real projects. Waves 4 and 5 need it. Wave 2 reads its curves and rock triaxial results from a CSV until then (TODO #19) |
| 1 | Stress and state | 01 and 03 A–B (vertical stress, phase relations), 02 B (activity; LI and Ic as analyses); SPT correlations and (N1)60, stage C for 04–08 and 10; P17 (drawn from Ic) |
| 2 | Strength envelopes | One fitting core for 04 A–B, 05 A–B, 22 A–B and 15 B (intact Hoek–Brown fit); P11–P12 |
| 3 | Oedometer | 06 A–B, 11 (Eoed, Eur,oed), 12 B (k from cv·mv), 21 A–B (Grob, Huder–Amberg); then 07 B (K0 from OCR) and 05 B (SHANSEP); P13–P15 |
| 4 | Rock | 13, 14, 23 A–B and 16 A (RQD); then the Hoek–Brown chain: 15 C, 16 B, 17–19, 09 (rock), 20. Kept after the soil waves |
| 5 | Stiffness | 08, 10 and 11 (the full set), 09 (soil); P19, P20 |
| 6 | Hydraulic | 12 A–C (field permeability tests) |

**Order of work:** wave 1, statistics, wave 2, wave 0, selection (stage D, starting with the Mohr–Coulomb set), then waves 3–6, each adding stage D and the model sets its sheets complete. Statistics come ahead of waves 2 and 0 because by then there are measured properties, derived values with depth trends and several correlations per property to compare, so they are designed against real uses. Wave 2 comes ahead of wave 0 (decided 2026-10-31, `docs/work/m11a-triaxial-data.md`) because nothing in it waits on curves in the AGS file: the values at failure are in standard groups (`TRET`, `TRIT`, `SHBT`), and readings during shearing come from a CSV the user shapes (TODO #19). Wave 0 is built against the sample dataset of real files (TODO #31), which isn't ready. §12.4 has the milestones.

**Releases** (decided 2026-10-21) are cut when a milestone leaves something usable, and aren't tied to waves or planned ahead. 0.1.0 (the plots P00–P03 and P07 and the data layer) is the first, on PyPI.

**Not yet placed**, built when needed: the Hollmann & Thewes (2013) clogging diagram (P18); relative density, from emax and emin (`RELD`) or from SPT (deferred from M14); QC level 2 (engineering-judgment ranges); standards comparison with a library of published ranges; user-defined PSD regions and the plasticity-chart data region; the compaction curve (P16).

**Later:**
- **AGSi export** (`to_agsi()`): 1D model elements per geology unit, carrying property summaries and parameters (including depth-trend design lines), with codes from the column registry. Not part of stage D.
- **AGSi import** (unit definitions and design parameters, compared with hangtu statistics).
- Exporters that write a model set in one program's input format.
- Multiple AGS files per project (merging, LOCA_ID conflicts, multiple datums).
- DIGGS ingestion; AGS3 → AGS4; CPT (P22).
- GeoPackage export; simple location plan (P21).
- Lateral earth pressure with depth (P23).
- Better UI; regex/fuzzy text matching; conditional minimally-useful-field rules.
- Cohesive/cohesionless helper; inch display for coarse particle sizes.
- Title block and drafting templates.

### 1.4 Non-goals
- Writing or editing AGS files (except test fixtures).
- Limit-state design calculations. hangtu stops at characteristic values, design lines and model parameter sets: deriving parameters is not design. Applying partial factors, capacity and stability checks, and running numerical models are out.
- A program's input format as the definition of a model set. Model sets follow the published model; exporters are thin (§5).
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
- **Judgments files** (§4) declare their units in a `units:` block per judgment (`{bulk_unit_weight: kN/m3}`), read with the same aliases; a field without a unit is an error naming the judgment.
- **CSV templates:** `ht.template("spt")` returns an empty DataFrame with the registry columns. `ht.template("spt").to_csv(...)` gives users a file to fill in. Each template column's description and expected quantity are listed by `ht.columns("spt")`. The `spt`, `atterberg`, `grain_size` and `permeability` templates are their Phase 2 dataset's columns in the same order, without those only hangtu produces (`source_line`, `energy_source`, `spt_n_capped`, `liquidity_index`, `consistency_index`), so CSV and AGS data reach the plots in the same shape (decided 2026-10-14, `docs/work/m9-release.md`). `stratigraphy` is `p.stratigraphy()`'s columns without `source_line` (M13); `density` and `particle_density` are their datasets' without `source_line` and `particle_density_specimen_id` (M14, `docs/work/m14a-density-data.md`); `triaxial` is `p.triaxial()`'s without `source_line`, the four principal stresses at failure and `effective_stress_basis`, which `ht.analysis.triaxial_failure_stresses()` adds (M11 a, `docs/work/m11a-triaxial-data.md`).

### 2.7–2.8 Settings and acceptance tests
Settings and Phase 1 tests: P00 §3 and §14. Phase 2 tests: the drafts file above.

---

## 3. Plotting (Phase 1)

Full conventions are in [`docs/plots/README.md`](docs/plots/README.md); each figure has its own spec. Summary of the decisions:
- **Function contract:** `ht.plot.<name>(df, *, ..., ax=None, display_units=None) -> (fig, ax)`. Analysis plots also return a result object. `ax=` enables `Sheet` composition. Analysis code lives in `ht.analysis.*` and can be used without plotting.
- **Input:** tidy DataFrames with registry column names (§10.3) and declared units (§2.6). There is no dependency on the database.
- **House style** (agreed for now): sans-serif font, 8–9 pt, light grids, legend inside the axes when a corner is clear, else below. Applied in a context manager, so the user's matplotlib state is untouched. No company drafting standard.
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
  - Batch 1 (P00–P07): all built; P06 closed M8.
  - The milestone of every other plot is in §12.4, or it is not yet placed (§1.3).

---

## 4. Analyses (Phase 1 unless noted)
Analysis code lives in `ht.analysis.*`, as plain functions usable without plotting. Detail is in [`docs/drafts/analysis.md`](docs/drafts/analysis.md): §1 SPT (refusal, N60, cap, classes) is decided; §2 Atterberg and classification and §3 grain size are decided (M8), with values to verify against the standards (TODO #5); §4 SPT correlations is specified with M13 (`docs/work/m13b1-spt-framework.md`). Decisions that more than one plot depends on:
- **SPT refusals** are included by default at the cap value (`spt_cap = 100`) with a note. Statistics treat them as censored.
- **N60** stays NULL until an energy ratio or `hammer_efficiency` is given. There is no default.
- **NP** is distinct from blank everywhere and shown as a count on plots.
- **Classification systems** (plasticity chart, size fractions, sieve axis) are selectable per call and defined in the config.
- **Correlations** (decided 2026-10-15; widened 2026-10-21) are stage C of every parameter (§1.3), from any input property (SPT N, PI, CPT qt, Is50, index properties). SPT correlations are the first set (M13). They live in `ht.analysis.correlations`, one function per published correlation, named target first: `<target>_<authors>_<year>`, with `<first>_et_al_<year>` for three or more authors (`undrained_shear_strength_stroud_1974`; decided 2026-10-23, `docs/work/m13b2-spt-strength-history.md`). Each one:
  - states its equation and cites its source, with constants kept in the source's units;
  - says when it applies and when it doesn't: soil types, input range, the input it was derived with (for SPT, field N, N60 or (N1)60), the data and region behind it, and known biases. The input is explicit: a column that doesn't match is an error, never a silent correction. This is in the docstring and in metadata attached to the result, so a plot or report can show it;
  - returns NaN with a count outside its range, and never clips or extrapolates the input;
  - returns rows that name the correlation (`correlation_name`), so several estimates of one property compare on P01 (`color_by=`) or P07.
  - reads the one column its correlation was derived with, by its registry name, with no argument to point it at another. A correlation published at another hammer energy is used in its 60 % form, from a cited source (decided 2026-10-22, `docs/work/m13b1-spt-framework.md`). One derived on field N reads `spt_n`, and says so;
  - gives a band, where its source does, as `<target>_lower` and `<target>_upper` beside `<target>`, which holds the central value or NaN; nothing is interpolated between the source's values;
  - carries its source's statistics and advice on use on every row (`correlation_data_count`, `correlation_r_squared`, `correlation_scatter`, `correlation_advice`, and `<target>_correlation_standard_deviation` where the source gives an arithmetic standard deviation), so they survive a merge or a file round trip. The advice is in the source's words where it has them, else marked as hangtu's. Other databases' checks of a correlation (bias, COV) are in its metadata, not on the rows; applying them is selection (decided 2026-10-30, `docs/work/m15b-correlation-statistics.md`);
  - takes test data or values derived directly from them as inputs. Chaining one correlation into another is discouraged, not prevented: it warns and is recorded on the rows (`correlation_input`);
  - reads soil type only when asked: an opt-in USCS map (`uscs=`) gives NaN with a reason for rows outside hangtu's proposed groups, which the user can override, from a `uscs_symbol` column the user supplies (decided 2026-10-23, `docs/work/m13b2-spt-strength-history.md`);
  - takes a coefficient the source gives by soil type from a required argument naming the source's row (`soil=`, one row or one per geology unit), never inferred; `uscs=` checks the row and doesn't choose it, since a USCS symbol can't split the sources' rows (decided 2026-10-26, `docs/work/m13b3-spt-stiffness.md`);
  - names its target as the source describes the estimate (`drained_youngs_modulus`, with the strain level in its notes), so estimates at different strain levels or drainage can't be confused (decided 2026-10-26).
- **Effective vertical stress** (decided 2026-10-15; reshaped 2026-10-22, `docs/work/m13a-judgments.md`) comes from `ht.analysis.vertical_stress()`, integrated through each hole's log: `p.stratigraphy()` or a CSV in `ht.template("stratigraphy")`'s shape, always passed explicitly. Unit weights are judgments keyed by a log column (geology unit, USCS symbol), not a depth profile; the water level is a judgment by hole. Pore pressure is hydrostatic. (N1)60 (`ht.analysis.spt_n1_60()`, C_N by a required `method=`, `docs/work/m13b1-spt-framework.md`) and the correlations take its σ′v column.
- **Triaxial stresses at failure** (decided 2026-10-31, `docs/work/m11a-triaxial-data.md`) come from `ht.analysis.triaxial_failure_stresses()`, for CSV stages and `p.triaxial()` alike, and are what M11 (b)'s fit, P11, P12 and M17 read: σ3 is the cell pressure, σ1 = σ3 + q_f and σ′ = σ − u_f, with u_f the file's pore pressure, else the back pressure in a drained test (recorded in `effective_stress_basis`), else blank. Extension stages are blank.
- **Phase relations** (decided 2026-10-28, `docs/work/m14b-phase-relations.md`): `ht.analysis.phase_relations()` gives e, n, S, γd and γsat from one specimen's γ, w and Gs. Gs = ρs / ρw with ρw = γw / g, so a row with a measured ρs has e = ρs (1 + w) / ρ − 1 whatever γw is set to. Gs comes from the row's measured ρs, else its assumed (`#`) ρs, which a judgment never replaces, else the `specific_gravity` judgment. S above 100 % is flagged, never corrected.
- **Judgment inputs** (decided 2026-10-21, `docs/work/parameter-roadmap.md`): a judgment (the disturbance factor D, GSI, σ′3max, Bjerrum's μ, a design unit weight profile, a groundwater level) is never filled in by hangtu, as N60 stays blank without an energy ratio.
  - **Resolution:** explicit argument → `judgments=` (a `Judgments` from `ht.judgments(path)`, or a path) → the Project's file, whose path its datasets carry in `df.attrs` → an error that names the judgment, what it is keyed by and how to set it. An argument overriding a file value warns, as does a `judgments=` that differs from the Project's file. There is no session (`ht.settings`) level: a judgment belongs to a project, and a session value would follow the user to the next one.
  - **Keyed by what it depends on:** each judgment declares its keys (geology unit, hole, depth range, a named design case) and whether one project-wide value is allowed. A value at a coarser key than allowed is an error, not a fallback (TODO #29). Where a project-wide value is allowed it needs a `reason`, and it fills the keys the file doesn't list, with a warning naming them; without one, an unlisted key is an error.
  - **A plain file next to the project** (`judgments.yaml`) is the source of truth, reviewable and kept in version control. A `Project` records its path (`p.set_judgments(path)`) and reads it on each call, and never copies it into SQLite. It works without a `Project` too, for CSV input. Format: `docs/work/m13a-judgments.md`, Spec.
  - **Recorded on every result:** each judgment used, with its value, key and source (the argument, or the file's path and SHA-256), in `df.attrs` and on result objects.
  - The first judgments are `unit_weight` and `water_level` (M13), then `plasticity_index` by geology unit, put on the rows by `ht.analysis.add_judgment()`; a PI column already on the rows wins over the file (M13 b2); then `specific_gravity` by geology unit, used only where a row has no particle density (M14 b). Then `significance_level` (α), the first judgment with one project-wide value and no keys: `ht.stats.compare()` and `compare_groups()` test at it and give intervals at 1 − α; a `values:` or `by:` under it is an error (M15 d, `docs/work/m15d-compare.md`, Decision 8). **Hammer efficiency is data, not a judgment** (decided 2026-10-22): `ISPT_ERAT` (`energy_ratio`) is used first, and `hammer_efficiency` stays an argument and session setting that fills blanks, with a warning naming the holes; the argument also takes values by hole, `{loca_id: ER}` (M13). **γw is a setting** (`ht.settings.water_unit_weight`, default 9.81 kN/m³), not a judgment.

---

## 5. Statistics (Phase 3) and model sets
- The functions that summarize values take an array, a Series, or a DataFrame plus `value=`/`by=`; `crosstab()` takes a DataFrame and two text columns.
- They accept `log=True`, except `fit()`: a normal fit to the logs is its lognormal fit (M15 (c)).
- They return result objects with readable summaries, `.to_frame()` and `.to_dict()` (the latter for later AGSi export).
- Results record whether they summarize test values (*properties*) or give interpreted design values (*parameters*), plus the method, n and source.
- **One calculation, many views** (decided 2026-10-21): a result computes and keeps everything (values, n, the statistics behind each value, outliers, the judgments used, §4). What the user asks for (characteristic values, p-values, variance, outlier detail) changes the view (`.to_frame()`, `.to_dict()`, the summary), never the calculation, so two reports of one result can't disagree.
- **Statistics feed stage D** (§1.3): comparing the sources of a parameter by depth or geology unit, and its characteristic value or design line.
- **Model sets** (decided 2026-10-21) are results of the same kind: a set per geology unit for a published model (Mohr–Coulomb; Hardening Soil and HS-small; generalized Hoek–Brown with residual values; Soft Soil), defined by the model's published description (TODO #32). Writing one program's input format is a thin exporter on top, never the definition (Later).

- **Input rules** (decided 2026-10-29, M15 (a), [`docs/work/m15a-describe.md`](docs/work/m15a-describe.md)), followed by every statistics function that summarizes values. `crosstab()` counts classes and follows only "counts add up", with a blank as a class of its own, `"(blank)"`:
  - **Flags come from the registry.** A `statistics:` field on a column (`columns.yaml`, P00 §5) marks it as a flag (`at_least`, `qualifier`, `non_plastic`, `assumed`) or a source (`source`), so every function reads one list and a new one is added there, not in code.
  - **Censored values** (refusals, `<x`, `>x`) enter `describe()` at their value and are counted, with a note that the mean is then biased; `fit()` treats them as censored.
  - **Non-plastic and assumed values are left out and counted**, never treated as blank or 0. Assumed values (M14 (a)) are included only on request (`include_assumed=True`), and the result says so.
  - **A band is an interval** (`<target>_lower`/`_upper` with no value, M13 b2): left out and counted, never pooled as two values or summarized by its midpoint. `fit()` leaves them out and counts them too: a correlation's band is the spread of its coefficient, not a measurement known to lie in an interval (M15 (c), [`docs/work/m15c-fit.md`](docs/work/m15c-fit.md); TODO #8).
  - **Sources aren't pooled unawares.** Rows from more than one source in one summary (`correlation_name`, blank for a measured value; `source`; `test_type`) are an error naming each value and its count; `pool=` pools on purpose and the result records it. Plots summarize per group they draw and say "mixes sources" instead of raising.
  - **Counts add up:** each row is counted once, under the first reason that applies, so `count` and the counts of rows left out add up to the group's rows.
  - **Percentiles are Hyndman & Fan (1996) definition 7 everywhere**, with no method argument. A percentile is reported only with a value beyond it on each side (n × min(p, 100 − p) / 100 ≥ 1: P25/P75 from 4 values, P5/P95 from 20); the standard deviation and CoV need 2 values, and CoV a ratio scale and a mean above 0.
  - **Units** resolve as for an analysis (§2.6); `display_units=` converts before the statistics and never falls back to the session setting.
- **The result object:** a frozen dataclass per function (`DescribeResult`, `FitResult`, `CompareResult`, `CompareGroupsResult`, `CrosstabResult`), on a shared base recording `kind` (*property* or *parameter*), the function, the value and its unit, the notes, the input's judgments and the hangtu version. It keeps no reference to the input.
- **Fitting** (decided 2026-10-30, M15 (c), [`docs/work/m15c-fit.md`](docs/work/m15c-fit.md)): `fit()` fits normal, lognormal, gamma and Weibull (two parameters, the positive ones located at 0), and beta between two given bounds, by maximum likelihood with censored values as censored; ranks them by AICc; checks each with an Anderson–Darling p-value by seeded parametric bootstrap, none when a value is censored; and reports each fit's probability beyond the physical bounds. A group needs 4 uncensored values. It never chooses the distribution: selection (M18) records that choice.
- **No pre-tests** (decided 2026-10-30, M15 (d), [`docs/work/m15d-compare.md`](docs/work/m15d-compare.md)): no statistics function tests normality or equal variances to choose a method. Each reports a parametric and a rank-based result together, and a plain-English note on whether they agree, which never says groups "are the same", only that the data don't show a difference at α, with the interval for scale.
- **Comparing groups** (decided 2026-10-30, M15 (d)): `compare()` gives Welch's t-test with the difference (or, with `log=True`, the ratio of geometric means) and its interval, beside the Brunner–Munzel test with the probability of superiority (a permutation p-value below 10 values per group, Karch 2021). `compare_groups()` gives Welch's ANOVA and Kruskal–Wallis, and every pair's Games–Howell interval and p beside Dunn's test with Holm's adjustment, both family-wise. The significance level is a judgment with no default (`significance_level`, §4); intervals are at 1 − α. Censored values enter at their value and are counted, as in `describe()` (better methods: TODO #51). The tests assume independent values, and the note says so.
- **Comparing classifications** (decided 2026-10-30, M15 (e), [`docs/work/m15e-crosstab.md`](docs/work/m15e-crosstab.md)): `crosstab()` counts two text columns of the same rows against each other, values as written (SPEC §8.3's exact match), blanks as `"(blank)"`. Agreement is counted only when the user says what agrees (`agree="same"`, or a mapping that names every class it is asked about), never inferred; a row blank on either side is counted on its own, never as a mismatch. No test or chance-corrected agreement (TODO #52).
- Functions: `describe` (built, M15 (a)); `fit` (built, M15 (c), with P08); `compare`, `compare_groups` (built, M15 (d)); `crosstab` (built, M15 (e)); `characteristic` (M18, with selection). Draft behavior is in [`docs/drafts/phase3-stats.md`](docs/drafts/phase3-stats.md) (TODO #8, #13).

P07 (property by geology unit against a report's baseline ranges) and P01's stats box summarize through the calculation `describe()` uses, so a figure and a table of the same rows agree (M15 (a), TODO #16).

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
| Field density (`IDEN`) | `IDEN_DPTH`, a point test (M14) | `test_depth` |
| Intervals (geology, samples) | Top and base kept as-is | — |

### 8.3 Geology
- **Geology key** (decided): configurable as the setting `geology_key`, default `GEOL_GEOL`. Options: `GEOL_GEO2`, `GEOL_LEG`, `GEOL_FORM`, `GEOL_BGS`, plus a mapping file. hangtu never falls back to another heading on its own. Several fields can be carried side by side (`geology_fields=`) and compared with `ht.stats.crosstab()`.
- **Mapping file** (CSV: `code, geology_unit, soil_class, order, color`; stored with the project):
  - **exact, case-sensitive match** (decided);
  - `soil_class` drives the cohesive/cohesionless split (🔬 TODO #3);
  - `color` feeds the palette.
- **Interval rule** (decided): `top ≤ d < base`. At the bottom of the hole, `d = base` belongs to the last interval. For overlaps, the lowest top (the deepest) wins, except in `vertical_stress()`, which can't integrate through two layers at once and errors.
- Unmapped codes are kept as their own units, with a warning and QC G004; they are never dropped.

---

## 9. Data quality (Phase 2)

### 9.1 Levels
| Level | What | When |
|---|---|---|
| 1: Integrity | Format, units, structure, internal consistency | v0.1 |
| 2: Engineering judgment | User-defined plausible ranges per unit and property | Not yet placed (§1.3) |

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
`p.groups`, `p.table(group, raw=False)`, `p.locations`, `p.set_geology_map(path)`, `p.geology_map`, `p.set_judgments(path)`, `p.judgments`, `p.diff(group, heading=None, changed_only=False)`, `p.sql(...)` (read-only, SI).

### 10.2 Ready-made datasets (Phase 2)
- `p.spt()`, `p.atterberg()`, `p.grain_size()` and `p.permeability()` (M7, v0.1); `p.grain_size_summary()`, `p.index_properties()` and the classification columns (M8); `p.stratigraphy()`, one row per GEOL layer (M13); `p.density()` (lab and field unit weights, each with its own specimen's water content) and `p.particle_density()` (M14 a); `clay_activity` in `p.index_properties()` (M14 b); `p.triaxial()`, one row per triaxial stage at failure, effective- and total-stress stages together (M11 a).
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

**Phase 1: plots on your own data**
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
fig, ax = ht.plot.water_content_profile(atterberg)                   # P06

sheet = ht.Sheet(size="tabloid", layout=(1, 2), title="Site X")
ht.plot.spt_profile(spt, ax=sheet[0])
ht.plot.profile(k, value="hydraulic_conductivity", preset="hydraulic_conductivity", ax=sheet[1])
sheet.save("site_x.pdf")
```

**Phase 2: the same plots, fed from AGS**
```python
p = ht.Project.from_ags("site.ags", db="site.sqlite", display_units="US")   # later: ht.Project.open("site.sqlite")
p.set_geology_map("strata.csv")
p.qc().to_csv("qc_report.csv")
fig, ax = ht.plot.spt_profile(p.spt(geology=["Alluvium"]))

p.set_judgments("judgments.yaml")                                    # unit weights, water levels (§4)
spt = ht.analysis.vertical_stress(p.spt(), stratigraphy=p.stratigraphy())
```

**Phase 3: statistics**
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
- **Docs:** the README and `examples/` for v0.1 (decided 2026-10-14), and a docs site built with Zensical, ahead of the second release rather than after feedback, so potential users can find what hangtu does and the site grows with each feature (decided 2026-10-16, `docs/work/docs-site.md`).
  - The source is `docs/site/` (`zensical.toml` at the root); the internal specs elsewhere in `docs/` aren't published. `docs/prepare_site.py` runs each page's example and writes the figures, the column page and the logo before a build.
  - The API reference is generated from the numpy docstrings (mkdocstrings), so a docstring is user documentation. Math is MathJax.
  - The site follows `main`, not the last release: `docs.yml` deploys to GitHub Pages when a push to `main` changes what the site is built from. Users who want what the site describes install from GitHub.
  - Zensical and `mkdocstrings-python` are in a `docs` dependency group, not runtime dependencies. Zensical is pinned exactly while it is alpha.
- **Phase 1 dependencies:** `pandas>=2.1.1,<3`, `numpy>=1.26`, `matplotlib>=3.8`, `pint>=0.24.4`, `pyyaml>=6.0.1`. Each floor is the oldest release that installs and imports on Python 3.12 with current transitive dependencies, and a lowest-version CI job keeps it honest.
- **Phase 2 adds** `python-ags4>=1.2.0` (LGPL-3.0, used unmodified, which is compatible with MIT; 1.2.0 is the first release with the 4.2 dictionary). It brings `click`, `rich`, `openpyxl` and `defusedxml` with it; its standard dictionaries (4.0.3–4.2) are what ingest reads units, types and keys from. The project database uses the `sqlite3` module with STRICT tables, which need SQLite ≥ 3.37; a test checks it on every CI platform.
- **Phase 3 adds** `scipy>=1.16.0`, a dependency since M15 (c) (`ht.stats.fit()`, its first use). 1.11 was the first release whose `fit` takes censored data; the floor rose to 1.16.0 in M15 (d) for `f_oneway(equal_var=False)` (Welch's ANOVA) and `tukey_hsd(equal_var=False)` (Games–Howell), which `ht.stats.compare_groups()` uses (`docs/work/m15d-compare.md`, Decision 1).
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
Rows are in build order; each milestone after M8 names its wave, or statistics or selection (§1.3). Milestones keep their numbers when the order changes, because other documents refer to them, so M8 comes after M9 and M16 after M17. M10 (a feedback round) was dropped, and its number isn't reused. A milestone can split into several units of work, as M8 did; units without a milestone go where §1.3's order of work puts them.

| M | Deliverable | Done when |
|---|---|---|
| M0 | Scaffolding: src layout, deps, ruff, pytest, CI matrix, MIT license | CI green |
| M1 | **P00 framework**: settings, units for DataFrames (§2.6), column registry, style, palette, label and out-of-range helpers, `Sheet` | Framework tests pass; a dummy plot composes on a Sheet |
| M2 | **P01** property profile | P01 acceptance criteria met |
| M2b | **P07** property by geology unit (moved ahead of M3 from M5) | P07 acceptance criteria met |
| M3 | **P02–P03** + SPT analysis | P02/P03 criteria + SPT golden tests |
| M4 | Phase 2 design: data model decided (§7) and Phase 2 built ahead of the rest of Phase 1. Each later Phase 2 unit turns its part of `docs/drafts/phase2-data.md` into its own intent and spec | Decisions recorded in SPEC |
| M5 | AGS4 ingest: raw and canonical layers in SQLite, units on ingest, value flags (§6, §7) | Twin-file test and ingest acceptance criteria met |
| M6 | QC level 1, CSV report and `diff()` (§9) | One defects-file test per rule |
| M7 | Depth/elevation/geology joins and ready-made datasets (§8, §10) | Datasets feed the Phase 1 plots directly |
| M9 | Examples (CSV → plot and AGS → QC → plot), CSV templates, README → **v0.1.0 on PyPI** | Examples run from a clean `pip install` |
| M8 | **P04–P06** + classification and gradation analyses, and the datasets that need them | P04–P06 criteria + classification/Dx golden tests |
| M13 | Wave 1, in four units: (a) the judgments file (§4), `p.stratigraphy()` and vertical stress; (b1) (N1)60, hammer efficiency by hole, the correlations framework and φ′ from SPT; (b2) the **SPT correlations** for s_u, σ′p/OCR and K0, with bands, chaining, the USCS map and PI by geology unit; (b3) E and Vs from SPT | Golden values from each source; out-of-range counts |
| M14 | Wave 1, in two units (data, then analysis; `docs/reference/process.md`): (a) `p.density()` and `p.particle_density()` from LDEN, IDEN and LPDN, with QC; (b) phase relations (γ, γd, e, n, S with consistency checks), the Gs judgment and activity. LI and Ic are already analyses (`ht.analysis.plasticity()`, M8) | Golden values; consistency checks on the test files |
| M12 | Wave 1: **P17** clogging diagram (Thewes & Burger 2004) | P17 criteria; zones match the source |
| M15 | Statistics, in five units: (a) `describe`, the result object and the input rules (done); (b) correlation statistics with the results (done); (c) `fit` (bounded and censored, AICc, Anderson–Darling) and P08 (done); (d) `compare`, `compare_groups` (done); (e) `crosstab` (done) | Hand-calculated and scipy reference values; the example project's cases |
| M11 | Wave 2, in two units (data, then analysis): (a) `p.triaxial()`, the stresses at failure from TREG/TRET and TRIG/TRIT, with QC; (b) the envelope fitting core and **P11–P12** triaxial: Mohr–Coulomb fit, failure envelope, stress–strain curves and measured stress paths | P11/P12 criteria + fit golden tests |
| M17 | Wave 2: undrained strength (UU, UCS, vane, pocket penetrometer), the shear box (soil and rock joints), intact Hoek–Brown fit | Golden values from each source |
| M16 | Wave 0: user-defined groups and curves | Curves from the sample dataset reach the datasets |
| M18 | Selection (stage D): sources compared by depth or geology unit, EC7 `characteristic` values (moved from M15, TODO #13) with P09, design lines, model-set results; the Mohr–Coulomb set | A set per unit, its judgments recorded; views agree; JRC worked examples |
| M19 | Wave 3: oedometer (σ′p, Cc, Cs, Eoed, Eur,oed, k from cv·mv, Grob and Huder–Amberg swelling); P13–P15 | Golden values; plot criteria |
| M20 | Wave 3: K0 from OCR, SHANSEP; the Soft Soil set | Golden values |
| M21 | Wave 4: rock lab datasets (UCS, tensile, point load, slake durability, intact moduli) and RQD | Datasets feed P01 and P07 |
| M22 | Wave 4: the Hoek–Brown chain, rock dilatancy, in situ stress; the generalized Hoek–Brown set with residual values | Published worked examples reproduced |
| M23 | Wave 5: soil stiffness (elastic, small-strain, Hardening Soil), soil dilatancy; P19, P20; the HS and HS-small sets | Golden values; plot criteria |
| M24 | Wave 6: field permeability tests | Golden values; censored values kept |

---

## 13. Open questions
None open. #1 (SPT mid-drive fallback) was settled in M7 and #2 (specimen combining) in M8, §10.2.
