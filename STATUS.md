# Status

**Next:** wave 0 (M16, user-defined groups and curves) once TODO #31 is settled; else wave 3 (M19, the
oedometer), whose Soft Soil set (M20) is built on M18's model-set base. Then waves 4–6.

Last checkpoint: 2, after `cleanup`, 2026-11-09, 1e39bac.

## Open
Each milestone names its wave (SPEC §1.3). A unit's close-out records its status here; a finished milestone
moves to Done, in one line (its unit's work file has the detail).

| M | Scope | Done when | Status |
|---|---|---|---|
| M16 | Wave 0: user-defined groups and curves | Curves from the sample dataset reach the datasets | Waits on TODO #31 |
| M19 | Wave 3: oedometer (σ′p, Cc, Cs, Eoed, Eur,oed, k from cv·mv, Grob and Huder–Amberg swelling); P13–P15 | Golden values; plot criteria | Not started |
| M20 | Wave 3: K0 from OCR, SHANSEP; the Soft Soil set | Golden values | Not started |
| M21 | Wave 4: rock lab datasets (UCS, tensile, point load, slake durability, intact moduli) and RQD | Datasets feed P01 and P07 | Not started |
| M22 | Wave 4: the Hoek–Brown chain, rock dilatancy, in situ stress; the generalized Hoek–Brown set with residual values | Published worked examples reproduced | Not started |
| M23 | Wave 5: soil stiffness (elastic, small-strain, Hardening Soil), soil dilatancy; P19, P20; the HS and HS-small sets | Golden values; plot criteria | Not started |
| M24 | Wave 6: field permeability tests | Golden values; censored values kept | Not started |

## Done
In build order. Milestones keep their numbers when the order changes, because other documents cite them, so M8
comes after M9 and M16 after M17. M10 (a feedback round) was dropped, and its number isn't reused.
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

## Releases
The latest is **0.1.0** (M9). Each release and what's unreleased: [`CHANGELOG.md`](CHANGELOG.md).

## Elsewhere
- Plots and their status: [`docs/plots/README.md`](docs/plots/README.md).
- Parameters and their stages A–D: [`docs/drafts/parameters/README.md`](docs/drafts/parameters/README.md).
