# Changelog

What changed in each release of hangtu. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Until 1.0, names and arguments may still change between releases.

## Unreleased

Everything below is on `main` (`pip install git+https://github.com/konnerhorton/hangtu`) and in the
[documentation](https://konnerhorton.github.io/hangtu/), but not yet on PyPI.

### Added
- **Plots:** `plasticity_chart()`, `grain_size()`, `water_content_profile()`, `clogging_diagram()`,
  `distribution_fit()`, `representative_profile()`, `failure_envelope()`, `triaxial_shearing()`,
  `shear_box_envelope()`, `hoek_brown_envelope()`, `consolidation_curve()`, `consolidation_coefficients()` and
  `consolidation_time_curves()`.
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
- **Oedometer curves:** `oedometer_fit()` gives each specimen's preconsolidation stress σ′p, by Oikawa's two
  lines in log(1 + e) with Pacheco Silva's construction as a check, and Cc, Cr, Cs and CR; with σ′v0 from
  `vertical_stress()`, OCR and the sample quality Δe/e0 graded by Lunne et al. (1997). A curve with no clear break,
  too few points or too short a virgin line gets a reason instead of a value. `consolidation_curve()` draws the
  increments by branch with the fitted lines and both σ′p, so you can judge the fit before using it.
- **Oedometer increments:** `oedometer_increments()` recomputes m_v for each increment from its void ratios,
  beside the lab's, and gives the constrained modulus on loading (Eoed) and on unloading or reloading (Eur,oed),
  and k = c_v·m_v·γw from each of the lab's c_v. Each value belongs to its increment, and the increment spanning
  σ′v0 is marked rather than interpolated. `consolidation_coefficients()` draws m_v and c_v as segments over each
  increment's stress range, with the lab's m_v as a mark.
- **c_v from settlement–time readings:** `consolidation_coefficient_from_readings()` reads c_v for each oedometer
  increment from its dial gauge readings by both of BS 1377-5's constructions, root time (t90) and log time (t50),
  beside the lab's own. The readings can come from any datum and with either sign. A curve a construction can't read
  gets a reason instead of a value, and where the rule reads a curve badly you can override the time range of one
  part of the construction, with a reason that is kept on the result. `consolidation_time_curves()` draws each
  increment's curves with the constructions on them, so you can see where each t90 and t50 came from.
  `oedometer_increments(consolidation_coefficients=...)` adds k from these c_v, beside k from the lab's.
- **Oedometer readings from the AGS file:** the readings map takes oedometer groups too, and
  `p.oedometer_readings()` gives one row per reading with its increment's stress, void ratios and specimen height.
  `ht.template("oedometer_readings")` lays them out for a CSV, and `ht.template("consolidation_overrides")` the
  overrides. The example project carries readings for its oedometer tests. Elapsed times in a file are read in any
  unit of time and given in minutes.
- **Stiffness and dilatancy from triaxial readings:** `triaxial_stiffness_from_readings()` reads each stage's
  E50, the secant modulus at half the peak deviator stress, and its strain ε50 from the q–ε1 readings, so you can
  set it beside the lab's reported E50; and the failure ratio Rf of the Hardening Soil model's hyperbola, fitted to
  the readings between 0.7 and 0.95 of the failure stress. `triaxial_dilatancy_from_readings()` reads each drained
  stage's dilatancy angle ψ from the rate of volume change near failure. A stage a value can't be read from gets a
  reason instead, and the fit's range and ψ's window are arguments. The new site page, Hardening Soil stiffness,
  shows both on the example project.
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
- **QC:** oedometer checks (E001 to E005): void ratios that don't follow on from one increment to the next,
  a void ratio that rises under a larger load, a lab's m_v that doesn't follow from its own void ratios,
  increments out of order, and an initial void ratio that disagrees with the densities.
- **The lab's E50 in `p.triaxial()`:** `reported_secant_modulus_at_50_percent_peak` and
  `reported_axial_strain_at_50_percent_peak` (`TRET_E50`, `TRET_EP50`), the secant modulus to half the peak
  deviator stress and its strain, as the lab reports them; read E50 with `test_type`, since it is undrained on a CU
  stage and drained on a CD one. `effective_vertical_consolidation_stress` and
  `effective_radial_consolidation_stress` (`TRET_CVP`, `TRET_CRP`) say which stress an anisotropically
  consolidated stage was consolidated to. All four are in `ht.template("triaxial")` too.
- **QC:** triaxial checks X007 and X008: a lab's E50 that doesn't follow from its own q_f and ε50 (usually a unit
  slip), and an ε50 at or past the strain at failure. They run where the failure criterion is the maximum
  deviator stress.
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
- **Warnings where a plausible number may be wrong:**
  - A correlation run on rows whose `soil_class` it isn't for (a sand correlation on `fine` rows, any soil
    correlation on `rock`) keeps its estimates, warns with the count by geology unit, and notes the rows
    `soil class contradicts` in `correlation_note`. `profile()`'s footnote counts them, and
    `correlations.describe(name)["soil_classes"]` gives the classes each correlation is for.
  - `spt_class()` and `spt_histogram()` warn when rows' `soil_class` contradicts the class table.
  - `representative()` warns, and notes the group, when more than half its values are censored, or when the value
    lies beyond every measured value on the censored side. `fit()` warns when more than half are censored.
  - `mohr_coulomb_fit()` warns when a consolidation stress is far above any overburden at the sample's depth
    (above max(10 × 25 kN/m³ × depth, 500 kPa)): the stresses may be in another unit than declared, such as psf
    declared as kPa.
- **A whole file's units in one step:** `read_csv(path, system="US")` and `set_units(df, system="SI")` give each
  registered column with a unit its unit in that system, the one `ht.columns()` lists (US stress is psf, so name
  columns in ksf or tsf in `units=`, which wins over `system=`). `ht.columns(df)` lists a file's own columns with
  each one's US, SI and declared unit, to check before declaring. The unit texts `ht.columns()` shows, such as
  `kN/m³` and `ft²/yr`, are now read without a warning.

### Changed
- **Breaking:** `spt_class()` and `spt_histogram()` need `table=` (`"cohesionless"` or `"cohesive"`). The default
  of `"cohesionless"` classed clays as "Very loose" or "Loose" with no warning; which table applies is the
  engineer's call. Add `table="cohesionless"` to keep what a call gave before.
- A project database made by an earlier version needs ingesting again (`ht.Project.from_ags(...,
  overwrite=True)`): it now records the units of the oedometer's m_v and c_v, the readings map, and which headings
  hold a time. Opening an old one says so.
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
