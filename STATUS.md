# Status

**Next:** M19 (c2), c_v from settlement–time readings by both constructions and P15: its intent starts from the c_v
parts of `docs/work/m19c-consolidation.md`. Then M19 (d), rock swelling; M20's Soft Soil set on M18's model-set base.
Then waves 4–6.

Last checkpoint: 3, after M19 (a), 2026-11-15, 4f03bfd.

## In progress
- **M19 (c2)** on `m19c2-cv-readings`: plan steps 1–5 committed (the `time` kind, `p.oedometer_readings()`, root
  and log time and overrides in `consolidation_coefficient_from_readings()`). Next: step 6, k from the recomputed
  c_v in `oedometer_increments()`, on Opus, from `docs/work/m19c2-cv-readings.md` `## Plan` and its "Notes from the
  build".

## Open
Each milestone names its wave (SPEC §1.3). A unit's close-out records its status here; a finished milestone
moves to Done, in one line (its unit's work file has the detail).

| M | Scope | Done when | Status |
|---|---|---|---|
| M19 | Wave 3: oedometer (σ′p, Cc, Cs, Eoed, Eur,oed, k from cv·mv, Grob and Huder–Amberg swelling); P13–P15. Five units: (a) data, (b) compressibility and P13, (c1) mv, Eoed, Eur,oed, k and P14, (c2) cv from readings and P15, (d) rock swelling | Golden values; plot criteria | (a) done (`p.oedometer()`, QC E001–E005); (b) done (`oedometer_fit()`, **P13**); (c1) done (`oedometer_increments()`, QC E003, **P14**); (c2) next |
| M20 | Wave 3: K0 from OCR, SHANSEP; the Soft Soil set | Golden values | Not started |
| M21 | Wave 4: rock lab datasets (UCS, tensile, point load, slake durability, intact moduli) and RQD | Datasets feed P01 and P07 | Not started |
| M22 | Wave 4: the Hoek–Brown chain, rock dilatancy, in situ stress; the generalized Hoek–Brown set with residual values | Published worked examples reproduced | Not started |
| M23 | Wave 5: soil stiffness (elastic, small-strain, Hardening Soil), soil dilatancy; P19, P20; the HS and HS-small sets | Golden values; plot criteria | Not started |
| M24 | Wave 6: field permeability tests | Golden values; censored values kept | Not started |

## Done
In build order. Milestones keep their numbers when the order changes, because other documents cite them, so M8
comes after M9 and M16 after M18. M10 (a feedback round) was dropped, and its number isn't reused.
- **M0:** scaffolding: src layout, deps, ruff, pytest, CI matrix, MIT license.
- **M1:** **P00** framework: settings, units for DataFrames, column registry, style, palette, `Sheet`.
- **M2, M2b:** **P01** property profile; **P07** property by geology unit.
- **M3:** **P02–P03** and the SPT analysis.
- **M4:** Phase 2 design: the data model (SPEC §7).
- **M5:** AGS4 ingest: raw and canonical layers, units on ingest, value flags.
- **M6:** QC level 1, the CSV report and `diff()`.
- **M7:** depth, elevation and geology joins, and the first datasets.
- **M9:** examples, CSV templates, README; **0.1.0 on PyPI**.
- **M8:** **P04–P06**, and the classification and gradation analyses.
- **M13:** wave 1: the judgments file, stratigraphy, vertical stress; (N1)60, the correlations framework and the SPT correlations.
- **M14:** wave 1: density and particle density data; phase relations, the Gs judgment and activity.
- **M12:** wave 1: **P17** clogging diagram (Thewes & Burger 2004).
- **M15:** statistics: `describe`, correlation statistics, `fit` and **P08**, `compare`, `compare_groups`, `crosstab`.
- **M11:** wave 2: `p.triaxial()`, the envelope fitting core and **P11**, **P12** from a CSV of readings.
- **M17:** wave 2: `p.undrained_strength()`, `p.shear_box()`; the shear box fit and **P31**; the intact Hoek–Brown fit and **P32** from a CSV of rock tests.
- **M18:** selection (stage D): SPT refusals in `fit()`; `representative()` (EC7 characteristic, JRC worked examples, and US views); **P09**; `compare_sources()` and the shear box φ′ conversion; `select()`; the model-set base and `mohr_coulomb_set()`.
- **M16:** wave 0: the readings map, `p.triaxial_readings()` and `p.shear_box_readings()` from user-defined groups; readings with one quantity per row, unload tails and interpolation in `triaxial_failure_from_readings()` and **P12**.

## Releases
The latest is **0.1.0** (M9). Each release and what's unreleased: [`CHANGELOG.md`](CHANGELOG.md).

## Elsewhere
- Plots and their status: [`docs/plots/README.md`](docs/plots/README.md).
- Parameters and their stages A–D: [`docs/drafts/parameters/README.md`](docs/drafts/parameters/README.md).
