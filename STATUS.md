# Status

**Next:** M23 (c), E′ and ν′ selected and in the Mohr–Coulomb set, with the drained↔undrained conversion, Eu from
s_u if its source is in hand, and **P20**. Then the rest of wave 5 (M23 d, M25, M26), M20, and waves 4 and 6. M19 (d), rock swelling, moved into M21 with the other rock lab tests.

Last checkpoint: 4, after M19 (c2), 2026-11-24, 6791dcc.

## In progress
- Tutorial unit (the rest of TODO #66): an AGS file to a parameter set, as site pages and `examples/`, then a
  marimo copy. Not started; its CSV examples use `system=` from units-system.
- M23 (c): paused on `m23c-modulus-selection`; its draft intent's "Open for the intent review" list is not
  reviewed yet. First step: review that list with the user, record the decisions, and amend the intent (Opus).

## Open
Each milestone names its wave (SPEC §1.3). A unit's close-out records its status here; a finished milestone
moves to Done, in one line (its unit's work file has the detail).

| M | Scope | Done when | Status |
|---|---|---|---|
| M23 | Wave 5: soil modulus from the lab tests already read: E, ν (08), the Hardening Soil set (11), soil dilatancy from curves (09); P20. Four units: (a) the lab's triaxial moduli in `p.triaxial()`; (b) E50, Rf and ψ from the triaxial readings; (c) E′ and ν′ selected and in the Mohr–Coulomb set, the drained↔undrained conversion, Eu from s_u, **P20**; (d) the HS set (E50ref and m across σ′3, Eoedref, Eurref, K0nc by rule) | Golden values; plot criteria | (a) done: the lab's E50, ε50 and σ′vc, σ′rc in `p.triaxial()`, QC X007–X008; (b) done: `triaxial_stiffness_from_readings()` (E50, ε50, Rf) and `triaxial_dilatancy_from_readings()` (ψ), sheet 11's page; Eur from loops deferred (TODO #80); (c) next |
| M25 | Wave 5: in situ modulus tests (pressuremeter, flat dilatometer, plate load); P19. Three units: (a) data (`PMTG`/`PMTL`, `DMTG`/`DMTP`, `PLTG`); (b) the moduli and **P19**; (c) these sources in P20 and the HS set | Golden values; plot criteria | Not started |
| M26 | Wave 5: small-strain stiffness (10) and the HS-small set. Three units: (a) Vs and G0 data (`ISTA`, `LDYN`, `RESG`/`RESP`); (b) G0 from Vs, Hardin-type G0, γ0.7; (c) the HS-small set | Golden values | Not started |
| M20 | Wave 3: K0 from OCR, SHANSEP; the Soft Soil set. Four units: (a) K0 from OCR; (b) CU-stage s_u data (`TRET_CU`); (c) SHANSEP; (d) the Soft Soil set | Golden values | Not started |
| M21 | Wave 4: rock lab datasets and RQD, then stage B for 13, 14, 21 and 23. Units: (a) UCS and intact moduli (TODO #75); (b) tensile and point load; (c) slake durability; (d) RQD; (e) rock swelling (Grob, Huder–Amberg; 21 B, data part built in M19 a); then stage B for 13, 14 and 23 | Datasets feed P01 and P07; golden values | Not started |
| M22 | Wave 4: the Hoek–Brown chain; the generalized Hoek–Brown set. Units: (a) GSI, D, mb, s, a, σcm, Em; (b) residual values and rock dilatancy; (c) in situ stress; (d) the generalized Hoek–Brown set | Published worked examples reproduced | Not started |
| M24 | Wave 6: field permeability tests; split at its intent | Golden values; censored values kept | Not started |

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
- **M19:** wave 3: `p.oedometer()` and `p.oedometer_readings()`; `oedometer_fit()` and **P13**; `oedometer_increments()` and **P14**; `consolidation_coefficient_from_readings()` and **P15**.
- **reliability-guards:** warnings where a plausible number may be wrong (TODO #60, #61, #63, #67): `soil_class` against correlations and the SPT class tables, `table=` required, censored values driving `representative()` and `fit()`, triaxial stresses far above the overburden.
- **units-system:** `system="US"` or `"SI"` on `read_csv()` and `set_units()`, and `ht.columns(df)` (TODO #66's open item).

## Releases
The latest is **0.1.0** (M9). Each release and what's unreleased: [`CHANGELOG.md`](CHANGELOG.md).

## Elsewhere
- Plots and their status: [`docs/plots/README.md`](docs/plots/README.md).
- Parameters and their stages A–D: [`docs/drafts/parameters/README.md`](docs/drafts/parameters/README.md).
