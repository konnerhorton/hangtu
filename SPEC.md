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
| [`docs/analysis/`](docs/analysis/) | Living specs for analyses that span units of work: the correlation contract, what each statistics function does |
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
| 0 | User-defined groups and curves | Curves (triaxial q–ε and εv, rock triaxial, swelling against time, shear box displacement) carried in the AGS file, read robustly; built against a sample dataset from real projects. Waves 4 and 5 need it. Wave 2 reads its curves and rock triaxial results from a CSV until then (decided 2026-10-15; the P12 draft §3) |
| 1 | Stress and state | 01 and 03 A–B (vertical stress, phase relations), 02 B (activity; LI and Ic as analyses); SPT correlations and (N1)60, stage C for 04–08 and 10; P17 (drawn from Ic) |
| 2 | Strength envelopes | One fitting core for 04 A–B, 05 A–B, 22 A–B and 15 B (intact Hoek–Brown fit); P11–P12 |
| 3 | Oedometer | 06 A–B, 11 (Eoed, Eur,oed), 12 B (k from cv·mv), 21 A–B (Grob, Huder–Amberg); then 07 B (K0 from OCR) and 05 B (SHANSEP); P13–P15 |
| 4 | Rock | 13, 14, 23 A–B and 16 A (RQD); then the Hoek–Brown chain: 15 C, 16 B, 17–19, 09 (rock), 20. Kept after the soil waves |
| 5 | Stiffness | 08, 10 and 11 (the full set), 09 (soil); P19, P20 |
| 6 | Hydraulic | 12 A–C (field permeability tests) |

**Order of work:** wave 1, statistics, wave 2, wave 0, selection (stage D, starting with the Mohr–Coulomb set), then waves 3–6, each adding stage D and the model sets its sheets complete. Statistics come ahead of waves 2 and 0 because by then there are measured properties, derived values with depth trends and several correlations per property to compare, so they are designed against real uses. Wave 2 comes ahead of wave 0 (decided 2026-10-31, `docs/work/m11a-triaxial-data.md`) because nothing in it waits on curves in the AGS file: the values at failure are in standard groups (`TRET`, `TRIT`, `SHBT`), and readings during shearing come from a CSV the user shapes (decided 2026-10-15; the P12 draft §3). Wave 0 is built against the sample dataset of real files (TODO #31), which isn't ready. §12.4 has the milestones.

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
- **CSV templates:** `ht.template("spt")` returns an empty DataFrame with the registry columns, for users to fill in (`.to_csv(...)`); `ht.columns("spt")` describes each. A template is its Phase 2 dataset's columns in the same order, without those only hangtu produces, so CSV and AGS data reach the plots in the same shape (decided 2026-10-14). Each template's columns: [`docs/data/datasets.md`](docs/data/datasets.md) §11.1.

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
Analysis code lives in `ht.analysis.*`, as plain functions usable without plotting. SPT, Atterberg and classification, and grain size are specified in [`docs/drafts/analysis.md`](docs/drafts/analysis.md) §1–§3 (decided; values to verify against the standards, TODO #5). Decisions that more than one feature depends on:
- **SPT refusals** are included by default at the cap value (`spt_cap = 100`) with a note. Statistics treat them as censored, and a correlation gives them as a bound (below).
- **N60** stays NULL until an energy ratio or `hammer_efficiency` is given. There is no default.
- **NP** is distinct from blank everywhere and shown as a count on plots.
- **Classification systems** (plasticity chart, size fractions, sieve axis) are selectable per call and defined in the config.
- **Correlations** (decided 2026-10-15; widened 2026-10-21) are stage C of every parameter (§1.3): `ht.analysis.correlations`, one function per published correlation, named `<target>_<authors>_<year>`. The contract every one follows is in [`docs/analysis/correlations.md`](docs/analysis/correlations.md). Its principles:
  - each cites its source, states its equation and says when it applies, in the docstring and in metadata on the result;
  - its input is explicit: it reads the one registry column it was derived with (field N, N60 or (N1)60), and a column that doesn't match is an error, never a silent correction. Soil type is read only when asked (`uscs=`), and a coefficient by soil type comes from a required `soil=`, never inferred;
  - outside its range it returns NaN with a count, never a clipped or extrapolated input. The one exception is an SPT correlation's N input: a refusal, or N beyond an inclusive range limit, gives the estimate at its N or the limit, marked as a bound in `correlation_qualifier`, so selection keeps the row as censored (M18 (a), `docs/work/m18a-refusals.md`);
  - every row names its correlation (`correlation_name`) and carries its source's band and statistics, so estimates compare on P01 and P07 and survive a merge;
  - chaining one correlation into another warns and is recorded (`correlation_input`).
- **Effective vertical stress** (decided 2026-10-15; reshaped 2026-10-22, `docs/work/m13a-judgments.md`) comes from `ht.analysis.vertical_stress()`, integrated through each hole's log: `p.stratigraphy()` or a CSV in `ht.template("stratigraphy")`'s shape, always passed explicitly. Unit weights are judgments keyed by a log column (geology unit, USCS symbol), not a depth profile; the water level is a judgment by hole. Pore pressure is hydrostatic. (N1)60 (`ht.analysis.spt_n1_60()`, C_N by a required `method=`) and the correlations take its σ′v column.
- **Triaxial stresses at failure** (decided 2026-10-31, `docs/work/m11a-triaxial-data.md`) come from `ht.analysis.triaxial_failure_stresses()`, for CSV stages and `p.triaxial()` alike. It is the one place σ1, σ3 and σ′ are computed, and P11, P12, the envelope fits and M17 read it. Readings during shearing reduce first to one failure row per stage by `ht.analysis.triaxial_failure_from_readings()`, with the engineer's `failure_criterion=` (no default) or the lab's marked reading (M11 c, `docs/work/m11c-triaxial-shearing.md`).
- **Envelope fits** (decided 2026-10-31, `docs/work/m11b-envelope-fit.md`) share one least-squares line core (`hangtu.analysis._line_fit`): transform the points, fit free or with a fixed intercept, back-transform. `mohr_coulomb_fit()` is the first; M17's shear box and Hoek–Brown fits are thin functions on the same core. A group that can't give a parameter gets a reason, not an error; nothing is forced through the origin unless asked. A φu = 0 strength needs no fit: s_u = q_f / 2 per specimen, and a set's value is their mean.
- **Undrained strength** (decided 2026-11-01, `docs/work/m17a-strength-data.md`) comes from `ht.analysis.undrained_shear_strength_from_tests()`, for CSV rows and `p.undrained_strength()` alike, with `undrained_shear_strength_basis` on every row (the in situ hand penetrometer's scale is a required argument, never guessed). Tests are kept side by side by `test_type` and `source`, never combined or converted between, and the field vane is uncorrected (Bjerrum's μ is a judgment for selection).
- **Phase relations** (decided 2026-10-28, `docs/work/m14b-phase-relations.md`): `ht.analysis.phase_relations()` gives e, n, S, γd and γsat from one specimen's γ, w and Gs. Gs comes from the row's measured ρs, else its assumed (`#`) ρs, which a judgment never replaces, else the `specific_gravity` judgment. S above 100 % is flagged, never corrected.
- **Judgment inputs** (decided 2026-10-21, `docs/work/parameter-roadmap.md`): a judgment (the disturbance factor D, GSI, σ′3max, Bjerrum's μ, a design unit weight profile, a groundwater level) is never filled in by hangtu, as N60 stays blank without an energy ratio. Format and resolution: `docs/work/m13a-judgments.md`, Spec; the judgments hangtu reads, their keys and their checks: `src/hangtu/_judgments.py`.
  - **Resolution:** explicit argument → `judgments=` (a `Judgments` from `ht.judgments(path)`, or a path) → the Project's file, whose path its datasets carry in `df.attrs` → an error that names the judgment, what it is keyed by and how to set it. An argument overriding a file value warns, as does a `judgments=` that differs from the Project's file. There is no session (`ht.settings`) level: a judgment belongs to a project, and a session value would follow the user to the next one.
  - **Keyed by what it depends on:** each judgment declares its keys (geology unit, hole, depth range, a named design case) and whether one project-wide value is allowed. A value at a coarser key than allowed is an error, not a fallback (TODO #29). Where a project-wide value is allowed it needs a `reason`, and it fills the keys the file doesn't list, with a warning naming them; without one, an unlisted key is an error.
  - **A plain file next to the project** (`judgments.yaml`) is the source of truth, reviewable and kept in version control. A `Project` records its path (`p.set_judgments(path)`) and reads it on each call, and never copies it into SQLite. It works without a `Project` too, for CSV input.
  - **Recorded on every result:** each judgment used, with its value, key and source (the argument, or the file's path and SHA-256), in `df.attrs` and on result objects.
  - **Absence is an error,** with one exception: `spt_refusal_upper_limit`, because without it `fit()` keeps refusals right-censored, the test's result (M18 (a)).
  - **Hammer efficiency is data, not a judgment** (decided 2026-10-22): `ISPT_ERAT` (`energy_ratio`) is used first, and `hammer_efficiency` stays an argument and session setting that fills blanks, with a warning naming the holes; the argument also takes values by hole, `{loca_id: ER}`. **γw is a setting** (`ht.settings.water_unit_weight`, default 9.81 kN/m³), not a judgment.

---

## 5. Statistics (Phase 3) and model sets
`ht.stats`: `describe`, `fit`, `compare`, `compare_groups`, `crosstab` (M15) and `representative` (M18 (b)). What each function does: [`docs/analysis/statistics.md`](docs/analysis/statistics.md).
- The functions that summarize values take an array, a Series, or a DataFrame plus `value=`/`by=`, and accept `log=True` (except `fit()`, whose lognormal fit is the log option); `crosstab()` takes a DataFrame and two text columns.
- **The result object:** a frozen dataclass per function (`DescribeResult`, `FitResult`, …), on a shared base recording `kind` (*property*: a summary of test values; *parameter*: an interpreted design value), the function, the value and its unit, the method, n, the notes, the input's judgments and the hangtu version. It has a readable summary, `.to_frame()` and `.to_dict()` (the latter for later AGSi export), and keeps no reference to the input.
- **One calculation, many views** (decided 2026-10-21): a result computes and keeps everything (values, n, the statistics behind each value, outliers, the judgments used, §4). What the user asks for (characteristic values, p-values, variance, outlier detail) changes the view (`.to_frame()`, `.to_dict()`, the summary), never the calculation, so two reports of one result can't disagree.
- **Derived results** (decided 2026-10-31, M11 (b), [`docs/work/m11b-envelope-fit.md`](docs/work/m11b-envelope-fit.md)): a fit of test results (`ht.analysis.mohr_coulomb_fit()`, M17's shear box and Hoek–Brown fits) returns a result of its own family in `ht.analysis`, recording `kind = "derived"` (Eurocode 7's measured → derived → representative → design), the method, the points it fitted and those left out with their reasons, with the same views. A fitted value takes the parameter's name (`effective_friction_angle`), as a measured value does; correlation estimates carry `correlation_name` and a lab's own fit is `reported_`, so none pools with another unawares. A test's fit takes the test's name instead where the parameter's would pool unlike tests: the shear box fit gives `peak_friction_angle`, not `effective_friction_angle`, because a direct shear φ′ isn't a triaxial φ′ until selection converts it (M18), and its stresses aren't labeled effective (M17 (b), [`docs/work/m17b-shear-box-fit.md`](docs/work/m17b-shear-box-fit.md), decision 2).
- **Statistics feed stage D** (§1.3): comparing the sources of a parameter by depth or geology unit, and its characteristic value or design line.
- **Model sets** (decided 2026-10-21) are results of the same kind: a set per geology unit for a published model (Mohr–Coulomb; Hardening Soil and HS-small; generalized Hoek–Brown with residual values; Soft Soil), defined by the model's published description (TODO #32). Writing one program's input format is a thin exporter on top, never the definition (Later). **The selection is a judgment** (decided 2026-11-02, M18): per geology unit and parameter, the judgments file names a method hangtu computes (a characteristic value, a percentile, …, with its inputs) or gives a value with a reason, and the set records which.
- **Input rules** (decided 2026-10-29, M15 (a), [`docs/work/m15a-describe.md`](docs/work/m15a-describe.md)), followed by every statistics function that summarizes values. `crosstab()` follows only "counts add up", with a blank as a class of its own:
  - **Flags come from the registry.** A `statistics:` field on a column (`columns.yaml`, P00 §5) marks it as a flag (`at_least`, `qualifier`, `non_plastic`, `assumed`) or a source (`source`), so every function reads one list and a new one is added there, not in code. A qualifier flag whose `values:` names a column and that says `replaces: qualifier` is the only qualifier read for it, so a row with two values (a vane's peak and remolded s_u) has a flag column for each (decided 2026-11-01, `docs/work/m17a-strength-data.md`); any other qualifier flag is read alongside the generic one, so a correlation's `correlation_qualifier` and a lab's `qualifier` both count in a pooled frame (M18 (a), `docs/work/m18a-refusals.md`, decision 5).
  - **Censored values** (refusals, `<x`, `>x`) enter `describe()` at their value and are counted, with a note that the mean is then biased; `fit()` treats them as censored.
  - **Non-plastic and assumed values are left out and counted**, never treated as blank or 0. Assumed values (M14 (a)) are included only on request (`include_assumed=True`), and the result says so.
  - **A band is an interval** (`<target>_lower`/`_upper` with no value, M13 b2): left out and counted, never pooled as two values or summarized by its midpoint. `fit()` leaves them out and counts them too: a correlation's band is the spread of its coefficient, not a measurement known to lie in an interval (M15 (c), [`docs/work/m15c-fit.md`](docs/work/m15c-fit.md); TODO #8).
  - **Sources aren't pooled unawares.** Rows from more than one source in one summary (`correlation_name`, blank for a measured value; `source`; `test_type`) are an error naming each value and its count; `pool=` pools on purpose and the result records it. Plots summarize per group they draw and say "mixes sources" instead of raising.
  - **Counts add up:** each row is counted once, under the first reason that applies, so `count` and the counts of rows left out add up to the group's rows.
  - **Percentiles are Hyndman & Fan (1996) definition 7 everywhere**, with no method argument. A percentile is reported only with a value beyond it on each side (n × min(p, 100 − p) / 100 ≥ 1: P25/P75 from 4 values, P5/P95 from 20); the standard deviation and CoV need 2 values, and CoV a ratio scale and a mean above 0.
  - **Units** resolve as for an analysis (§2.6); `display_units=` converts before the statistics and never falls back to the session setting.
- **Statistics are designed for lab data** (decided 2026-11-02): tests, comparisons and censored-data methods are designed around lab results, where testing is controlled. SPT N and the correlations from it get the simple, transparent treatment (counted, noted, shown on the plot), not methods that lend a crude measure more precision than it has. Selection pools geology units on geology and plots; tests are a check.
- **Engineers choose, hangtu reports.** `fit()` never picks the distribution, `representative()` has no default method, side, distribution or input, and the significance level is a judgment. No function tests normality or equal variances to choose a method: each reports a parametric and a rank-based result together, with a note on whether they agree that never says groups "are the same".
- **Refusals in `fit()`** stay right-censored at their N60, the test's result as ASTM D1586 defines it; the optional `spt_refusal_upper_limit` judgment makes them interval-censored (decided 2026-11-02, TODO #49).

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
| Field vane, hand penetrometer in situ (`IVAN`, `IPEN`) | `IVAN_DPTH`, `IPEN_DPTH`, point tests (M17 a) | `test_depth` |
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
- `p.spt()`, `p.atterberg()`, `p.grain_size()` and `p.permeability()` (M7, v0.1); `p.grain_size_summary()`, `p.index_properties()` and the classification columns (M8); `p.stratigraphy()`, one row per GEOL layer (M13); `p.density()` (lab and field unit weights, each with its own specimen's water content) and `p.particle_density()` (M14 a); `clay_activity` in `p.index_properties()` (M14 b); `p.triaxial()`, one row per triaxial stage at failure, effective- and total-stress stages together (M11 a); `p.undrained_strength()`, one row per undrained strength result, the tests side by side, and `p.shear_box()`, one row per shear box stage (M17 a).
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
ht.stats.representative(spt, value="spt_n60", by="geology_unit", method="characteristic", estimate="mean", side="low", distribution="normal", coefficient_of_variation=0.30)
```

**Error-message standard:** messages are written for engineers. They say what is wrong, where, and what to do. No raw tracebacks for anticipated data problems.

---

## 12. Engineering

### 12.1 Environment and distribution
- Python ≥ 3.12, developed with `uv`.
- PyPI + public GitHub, MIT license.
- **CI:** GitHub Actions on Windows, macOS and Linux × Python 3.12–3.14 (ruff + pytest), and mypy in one job on the locked versions. Release to PyPI on a `v*` tag (trusted publishing, `release.yml`): the tag must match the version in `pyproject.toml`, and the test suite runs against the built wheel on all three operating systems before upload. A manual run publishes to TestPyPI instead. Before either upload, the scripts in `examples/` run against the built wheel in an empty directory on all three operating systems.
- **0.0.1** is a placeholder release that claims the name on PyPI before v0.1 (decided 2026-10-12). It contains the M2b state: P00, P01 and P07.
- **0.1.0** (M9) is the first release meant for use: P00–P03 and P07, the SPT analysis, AGS4 ingest, QC and the four datasets, with `examples/` and the example data in `ht.examples`.
- **Docs:** the README, `examples/` and a docs site built with Zensical from `docs/site/` (`zensical.toml` at the root), which grows with each feature (decided 2026-10-16, `docs/work/docs-site.md`). The rest of `docs/` is internal and not published. The API reference is generated from the numpy docstrings (mkdocstrings), so a docstring is user documentation. The site follows `main`, not the last release (`docs.yml`). Zensical and `mkdocstrings-python` are in a `docs` dependency group; Zensical is pinned exactly while it is alpha.
- **Runtime dependencies** (floors in `pyproject.toml`, each the oldest release that installs and imports on Python 3.12; a lowest-version CI job keeps them honest):
  - Phase 1: `pandas` (<3), `numpy`, `matplotlib`, `pint`, `pyyaml`.
  - Phase 2: `python-ags4` (LGPL-3.0, used unmodified, which is compatible with MIT; its standard dictionaries, 4.0.3–4.2, are what ingest reads units, types and keys from). The project database uses `sqlite3` with STRICT tables (SQLite ≥ 3.37, checked on every CI platform).
  - Phase 3: `scipy`, whose floor (1.16.0) is set by `ht.stats.compare_groups()` (Welch's ANOVA, Games–Howell).
- **Dev dependencies:** `pytest`, `ruff`, `hypothesis`, `pytest-xdist`, `mypy` and `types-PyYAML`, optionally `pytest-mpl`. mypy checks the annotations that exist, not strictly, without pandas-stubs (`docs/work/type-check.md`); the package ships `py.typed`.

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
Rows are in build order; each milestone after M8 names its wave, or statistics or selection (§1.3). Milestones keep their numbers when the order changes, because other documents refer to them, so M8 comes after M9 and M16 after M17. M10 (a feedback round) was dropped, and its number isn't reused. A milestone can split into several units of work, as M8 did; units without a milestone go where §1.3's order of work puts them. The Status column is where a unit's close-out records it; a finished milestone moves to the Done table, in one line (its unit's work file has the detail). `CLAUDE.md` names only what's next.

**Done:**
| M | Deliverable |
|---|---|
| M0 | Scaffolding: src layout, deps, ruff, pytest, CI matrix, MIT license |
| M1 | **P00** framework: settings, units for DataFrames, column registry, style, palette, `Sheet` |
| M2, M2b | **P01** property profile; **P07** property by geology unit |
| M3 | **P02–P03** + SPT analysis |
| M4 | Phase 2 design: data model decided (§7) |
| M5 | AGS4 ingest: raw and canonical layers, units on ingest, value flags |
| M6 | QC level 1, CSV report and `diff()` |
| M7 | Depth/elevation/geology joins and the first datasets |
| M9 | Examples, CSV templates, README → **v0.1.0 on PyPI** |
| M8 | **P04–P06** + classification and gradation analyses |
| M13 | Wave 1: judgments file, stratigraphy, vertical stress; (N1)60, the correlations framework and the SPT correlations |
| M14 | Wave 1: density and particle density data; phase relations, the Gs judgment and activity |
| M12 | Wave 1: **P17** clogging diagram (Thewes & Burger 2004) |
| M15 | Statistics: `describe`, correlation statistics, `fit` and P08, `compare`, `compare_groups`, `crosstab` |
| M11 | Wave 2: `p.triaxial()`, the envelope fitting core and **P11**, **P12** from a CSV of readings |

**Open:**
| M | Deliverable | Done when | Status |
|---|---|---|---|
| M17 | Wave 2, in three units (`docs/work/m17a-strength-data.md`): (a) `p.undrained_strength()` and `p.shear_box()`, with QC; (b) the shear box fit, peak and residual; (c) the intact Hoek–Brown fit, from a CSV of rock triaxial results | Golden values from each source | (a) done; (b) next |
| M16 | Wave 0: user-defined groups and curves | Curves from the sample dataset reach the datasets |  |
| M18 | Selection (stage D), in four units (`docs/work/m18a-refusals.md`): (a) SPT refusals: the judged upper limit in `fit()` and at-least estimates from the correlations; (b) representative values: EC7 `characteristic` (moved from M15, TODO #13) and the views US practice uses, constant or as design lines; (c) **P09**; (d) sources compared by depth or geology unit, the selection as a judgment, model-set results and the Mohr–Coulomb set (after M17 (b)) | A set per unit, its judgments recorded; views agree; JRC worked examples | (a)–(c) done; (d) next |
| M19 | Wave 3: oedometer (σ′p, Cc, Cs, Eoed, Eur,oed, k from cv·mv, Grob and Huder–Amberg swelling); P13–P15 | Golden values; plot criteria |  |
| M20 | Wave 3: K0 from OCR, SHANSEP; the Soft Soil set | Golden values |  |
| M21 | Wave 4: rock lab datasets (UCS, tensile, point load, slake durability, intact moduli) and RQD | Datasets feed P01 and P07 |  |
| M22 | Wave 4: the Hoek–Brown chain, rock dilatancy, in situ stress; the generalized Hoek–Brown set with residual values | Published worked examples reproduced |  |
| M23 | Wave 5: soil stiffness (elastic, small-strain, Hardening Soil), soil dilatancy; P19, P20; the HS and HS-small sets | Golden values; plot criteria |  |
| M24 | Wave 6: field permeability tests | Golden values; censored values kept |  |

---

## 13. Open questions
None open. #1 (SPT mid-drive fallback) was settled in M7 and #2 (specimen combining) in M8, §10.2.
