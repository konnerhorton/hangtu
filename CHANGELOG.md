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
  `p.triaxial()`, `p.undrained_strength()`, `p.shear_box()` and `p.stratigraphy()`.
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
- **QC:** `p.qc(accepted=...)` takes findings a reviewer has checked and accepted, each with a reason. They
  stay in the report, marked accepted, so it shows what is still open.
- The project's vertical datum is read from the file's `LOCA_DATM` and shown on elevation axes.
- Units that a file's `UNIT` group defines are kept as written.
- `legend=` on every plot with a legend; legends sit in a clear corner inside the axes.
- `spt()` records the cap and, by hole, each energy ratio and where it came from (the data, the argument or
  the setting) in `attrs["spt"]`.
- `spt_profile(n="spt_n1_60")` plots (N1)60 from `spt_n1_60()`, with refusals drawn at the cap as for N60.
- Type annotations ship with the package (`py.typed`).
- The documentation site, with a page and example for each plot and parameter, and the API reference.

### Changed
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
