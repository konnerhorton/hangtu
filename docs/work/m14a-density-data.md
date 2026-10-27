# M14 (a): density data

## Intent
M14 is wave 1's second milestone (SPEC §1.3, §12.4): phase relations, activity, and LI and Ic as analyses. It
splits in two (decision 1). This unit, (a), is stage A for sheets 01 and 03: the measured densities, read from
the file into a dataset. (b) is stage B: phase relations with their consistency checks, and activity.

**Goal:** from an AGS file or a CSV, an engineer gets each specimen's measured bulk and dry density, water content
and particle density. The values are in registry columns with units, and an assumed particle density is kept
distinct from a measured one. They feed P01 and P07 as they are, give the engineer the data to choose unit weights
for the judgments file from, and are checked by QC rules that catch records that don't agree with themselves.

**Why:**
- **Nothing reads density data today.** `bulk_unit_weight` exists only for CSV input, and its registry source is
  `RDEN.RDEN_BDEN`, a rock group. None of the test files or the example file has `LDEN`, `LPDN` or `IDEN`. M13's
  `unit_weight` judgment asks the engineer to choose γ by geology unit (its examples say "median LDEN"), but
  hangtu has no way to show them the LDEN values.
- **Phase relations need γ, w and Gs on the same specimen** (sheet 03 §5.1, §7). Mixing a unit's mean γ with one
  sample's w adds scatter. Which specimen's values go together is a data-layer question, as it was for M8's
  `p.index_properties()` (SPEC §10.2), so it is settled here, before (b) builds formulas on it.
- **The sheets' pitfalls are QC findings:**
  - AGS gives particle density, not Gs.
  - A `#` prefix marks an assumed particle density (`value_flags.yaml`, `ASSUMED`). Assumed values must never be
    pooled with measured ones.
  - `LDEN_BDEN`, `LDEN_DDEN` and `LDEN_MC` on one row must satisfy ρd = ρ / (1 + w).

**Scope:** the groups `LDEN` (lab bulk and dry density, water content), `LPDN` (particle density) and `IDEN`
(field in-place density). The unit builds:
- the dataset or datasets (SPEC §10.2), with the common filters;
- a CSV template (§2.6);
- registry names;
- the groups in the SI/US twin test files, and a defects file for the new QC rules;
- QC level 1 rules from the sheets' pitfalls.

**SPEC and TODO touched:**
- SPEC: §10.2 (the new datasets), §10.3 (registry), §2.6 (templates), §9 (new rules, via `docs/data/qc.md`),
  §12.4 (M14 split into (a) and (b)), §1.3 "Not yet placed" (relative density, decision 4).
- Other docs: `docs/data/datasets.md`, `docs/data/qc.md`, and the parameter index (decision 5).
- TODO: #29 (the key for Gs, settled in (b)) and #45 (new: recommended user-defined fields).

### Decisions (intent review, 2026-10-27)
1. **M14 splits into data (a) and derivation (b), and later waves follow the same rule.** Whenever a wave or
   milestone proposes both a dataset and the analyses on it, they become separate units. Reasons: each fits in
   one review, and the shape of the data is settled before formulas are built on it. This goes in
   `docs/reference/process.md`, "Stages and waves", as a separate docs commit.
2. **The groups are LDEN, LPDN and IDEN.**
   - RDEN (rock density and porosity) stays in wave 4 with the rock lab datasets (M21).
   - The registry source of `bulk_unit_weight` gains LDEN. Whether it keeps RDEN is a spec question.
   - The initial state of specimens in strength and consolidation tests (`TRET`, `CONG` and `SHBT`, their
     `*_BDEN`, `*_DDEN` and `*_IVR`) stays in waves 2 and 3. Those values are taken on trimmed specimens, so they
     are compared with in situ values, never pooled with them (sheet 03 §7).
3. **Where there is no particle density test, Gs is a judgment** (built in (b)): `specific_gravity`, keyed by
   geology unit in the judgments file, with no default 2.65 (SPEC §4).
   - Reason: Gs is chosen from the measured values and the mineralogy, the way unit weight is.
   - Values the file marks as assumed (`#`) are kept, flagged and never treated as measured.
   - Whether a recommended user-defined AGS heading could carry Gs in the file instead is TODO #45.
4. **Relative density is deferred** out of M14, both from emax/emin (`RELD`, rare in files) and from SPT
   (Skempton 1986, stage C). It goes on SPEC §1.3's "Not yet placed" list at (a)'s close-out. M13 b3 had deferred
   it to M14.
5. **LI and Ic as analyses are already built.** `ht.analysis.plasticity()` (M8) takes a CSV frame. That leaves
   activity as the only part of sheet 02's stage B for M14. The parameter index, and the M14 row of SPEC §12.4,
   are corrected at (a)'s close-out.

### Open (for the spec step)
- **Shape of the datasets:**
  - One `p.density()` with LDEN and IDEN rows and a `test_type` column, or two datasets.
  - Particle density as its own dataset, or joined by sample, as `p.index_properties()` joins tests.
  - Which water content goes with a density: `LDEN_MC` on the same row, or `LNMC` on the same specimen.
- **Density or unit weight:** AGS stores ρ (Mg/m³), but the plots and `vertical_stress()` take γ. The dataset
  could give `bulk_density` and `dry_density`, unit weights (γ = ρ g), or both. Names (for example
  `specific_gravity` against `particle_density`) are checked against the whole registry.
- **The QC rules:** which pitfalls are level 1 (a record agreeing with itself, such as ρd against ρ / (1 + w) on
  one LDEN row, with the tolerance as a quantity string) and which wait for level 2 (plausible ranges, not yet
  placed).
- **IDEN:** its parent and depth heading in the 4.2 dictionary, and whether field density (usually shallow fill
  and compaction checks) belongs in the same dataset as lab density.
- **The example file:** whether `ht.examples`' `site.ags` gains these groups here or in (b), with page 03.

### Out of scope
- Everything in (b):
  - phase relations (e, n, S, γd, γsat derived from the rest);
  - consistency checks across tests (S > 1 below the water level);
  - the Gs judgment;
  - activity;
  - promoting sheet 03 (and 02) to a site page.
- RDEN and the specimen initial states (decision 2), relative density (decision 4), QC level 2.
- New plots. P01 and P07 take the new columns as they are.
