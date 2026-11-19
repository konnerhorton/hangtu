# Changelog

What changed in each release of hangtu. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Until 1.0, names and arguments may still change between releases.

## Unreleased

Everything below is on `main` (`pip install git+https://github.com/konnerhorton/hangtu`) and in the
[documentation](https://konnerhorton.github.io/hangtu/), but not yet on PyPI.

### Added
- **Plots:** `plasticity_chart()`, `grain_size()`, `water_content_profile()`, `clogging_diagram()`,
  `distribution_fit()`, `representative_profile()`, `failure_envelope()`, `triaxial_shearing()`,
  `shear_box_envelope()` and `hoek_brown_envelope()`.
- **Datasets:** `p.grain_size_summary()`, `p.index_properties()`, `p.density()`, `p.particle_density()`,
  `p.triaxial()`, `p.undrained_strength()`, `p.shear_box()`, `p.oedometer()` and `p.stratigraphy()`.
  `p.oedometer()` gives one row per oedometer load increment, with the void ratios, the lab's m_v and c_v,
  and the specimen's initial state; swelling tests are kept too, including one with no increments.
- **Readings during a test from the AGS file:** many labs put the triaxial and shear box curves in groups of
  their own, since AGS has none for them. `p.set_readings_map()` names those groups and which heading holds which
  value (`p.readings_map` shows it), and `p.triaxial_readings()` and `p.shear_box_readings()` then give one row per
  reading, with its stage's cell, back and normal stresses, depth and geology. `ht.template("shear_box_readings")`
  is new, and `ht.template("triaxial_readings")` gains the depth and geology columns (optional, so existing CSVs
  still read). The example project carries readings for every triaxial and shear box stage.
- `oedometer_load_branch()` marks each oedometer increment as loading, unloading, reloading or held at a
  constant stress, and `ht.template("oedometer")` lays out oedometer tests for a CSV.
- **Classification and index analyses:** `plasticity()`, `uscs()`, `aashto()`, `gradation()`,
  `clay_activity()` and `clogging_potential()`.
- **Stresses and phase relations:** `vertical_stress()`, `spt_n1_60()` and `phase_relations()`.
- **Strength:** `triaxial_failure_stresses()`, `triaxial_failure_from_readings()`,
  `undrained_shear_strength_from_tests()`, the envelope fits `mohr_coulomb_fit()`, `shear_box_fit()` and
  `hoek_brown_fit()`, and `friction_angle_from_shear_box()`.
- **SPT correlations** in `ht.analysis.correlations`, one function per published correlation, for the
  friction angle, undrained shear strength, preconsolidation stress, OCR, K0, Young's modulus and shear
  wave velocity. Each result carries its source's statistics and advice on use.
- **The judgments file:** `judgments.yaml` next to a project holds the engineer's judgments (unit weight,
  water level, specific gravity, the significance level, the selected values and others). Open it with
  `ht.judgments()` or attach it to a project with `p.set_judgments()`; each result records the judgments it
  used. A judgment has no default: a missing one is an error that names it.
- **Statistics** in `ht.stats`: `describe()`, `fit()` (distribution fits, with SPT refusals as censored
  values), `representative()` (Eurocode 7 characteristic values and US views), `compare()`,
  `compare_groups()`, `crosstab()`, `compare_sources()`, `select()` and the Mohr–Coulomb parameter set,
  `mohr_coulomb_set()`.
- **QC:** oedometer checks (E001, E002, E004, E005): void ratios that don't follow on from one increment
  to the next, a void ratio that rises under a larger load, increments out of order, and an initial void
  ratio that disagrees with the densities.
- **QC:** `p.qc(accepted=...)` takes findings a reviewer has checked and accepted, each with a reason. They
  stay in the report, marked accepted, so it shows what is still open.
- The project's vertical datum is read from the file's `LOCA_DATM` and shown on elevation axes.
- Units that a file's `UNIT` group defines are kept as written.
- `legend=` on every plot with a legend; legends sit in a clear corner inside the axes.
- `spt()` records the cap and, by hole, each energy ratio and where it came from (the data, the argument or
  the setting) in `attrs["spt"]`.
- `p.grain_size_summary()` and `p.index_properties()` read gradings reported only as percentages (`GRAG`
  with no `GRAT` curve), in the fraction system the new project setting `grag_fraction_system` names
  (`"astm_uscs"`, `"aashto"` or `"iso14688"`). Without the setting their fractions are blank, with a warning.
  A new column, `grading_source`, says whether each grading is a `"curve"` or `"reported"`.
- `read_csv()` reads a bound written into a value cell (`<5`, `> 200`, `<1e-9`) as the number, with `<` or
  `>` in the value's qualifier column, as an AGS file's `LT` and `GT` flags are read.
- `spt_profile(n="spt_n1_60")` plots (N1)60 from `spt_n1_60()`, with refusals drawn at the cap as for N60.
- Type annotations ship with the package (`py.typed`).
- The documentation site, with a page and example for each plot and parameter, and the API reference.

### Changed
- A project database made by an earlier version needs ingesting again (`ht.Project.from_ags(...,
  overwrite=True)`): it now records the units of the oedometer's m_v and c_v, and the readings map. Opening an old
  one says so.
- `triaxial_failure_from_readings()` and `triaxial_shearing()` take readings with only some of q, Δu and ε_v on a
  row, as an AGS file gives them. Where the failure reading has no Δu or ε_v of its own, it is interpolated in
  strain from that quantity's readings, and a warning names the stages. Readings from an AGS file carry no lab
  mark, so they need `failure_criterion=`.
- The readings after a stage's largest strain (the unload before the next stage) are drawn and never taken as
  the failure reading. A strain that falls before then is a warning naming the stage, no longer an error.
- A drained stage's pore pressure at failure, read from readings without Δu, is the back pressure, with no warning.
- With neither `GRAT` nor `GRAG` in the file, the warning from `p.grain_size_summary()` and
  `p.index_properties()` names both groups.
- SPT: `ISPT_REP` is read as AGS defines it, and a refusal with a blank N is kept as a refusal.
- `profile()` draws text values (such as a classification) in its value column.
- A plot counts a row beyond an axis limit once, however many of its values are beyond it.
- A unit string that is pint's own name for the unit, such as `inch`, is read without a warning.
- A bound written into a value cell (`<10`) is warned about with the fix: put `<` or `>` in `qualifier` and
  the number in the value column.
- `ht.columns()` names the plots that read a column by function (`plot.profile`).
- The example `strength.csv` gives the UU tests' q_f without the s_u worked out from it, so
  `undrained_shear_strength_from_tests()` runs on the file as shipped.

## 0.1.0 (2026-10-15)

The first release meant for use.
- **Plots:** `profile()`, `spt_profile()`, `spt_histogram()` and `geology_unit_comparison()`, with the
  shared style, units and `Sheet`.
- **AGS4 ingest:** `ht.Project.from_ags()` reads a file into a project database, with units converted on
  ingest and flagged values (NP, refusals, `<x`) kept.
- **QC:** `p.qc()` checks the file and exports one flat CSV of findings; `p.diff()` compares two files.
- **Datasets:** `p.spt()`, `p.atterberg()`, `p.grain_size()` and `p.permeability()`, with depth, elevation
  and geology units joined.
- **Analyses:** `spt()` and `spt_class()`.
- CSV templates (`ht.template()`), the column registry (`ht.columns()`), `examples/` and the example data in
  `ht.examples`.

## 0.0.1 (2026-10-12)

A placeholder that claims the name on PyPI, with the first plots: `profile()` and `geology_unit_comparison()`.
