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

## Spec
The rules live in the topic docs: the datasets in `docs/data/datasets.md` §6.8–6.9, the QC rules in
`docs/data/qc.md` §4.11. This section lists what changes where, the decisions behind it and the acceptance
criteria. 🟡 marks a value proposed here, awaiting review.

### Changes
- **`docs/data/datasets.md`:** §6.8 `p.density()` and §6.9 `p.particle_density()` (new); §2, §8, §11 and §12
  updated for them.
- **`docs/data/qc.md`:** §4.11 density rules B001–B004 (new); §4.10's minimum fields gain `LDEN`, `LPDN` and
  `IDEN`; §8 has the defects cases.
- **SPEC:**
  - §2.6, the `density` and `particle_density` templates;
  - §8.2, field density at `IDEN_DPTH` (`test_depth`);
  - §10.2, the two datasets;
  - §12.4, M14 split into (a) and (b);
  - §1.3 "Not yet placed", relative density (intent decision 4).
- **Registry:**
  - new columns: `dry_unit_weight`, `particle_density`, `particle_density_assumed`,
    `particle_density_specimen_id`, `sample_condition` and `stabilizer_content`, each checked against the whole
    registry;
  - new AGS sources: `bulk_unit_weight` (`LDEN_BDEN`, `IDEN_IDEN` × g; RDEN is dropped until M21 reads it),
    `water_content` (`LDEN_MC`, `IDEN_MC`), `test_type` (`LDEN_TYPE`, `IDEN_TYPE`, `LPDN_TYPE`);
  - `depth_basis` gains `test_depth`.
- **Test files:** `LDEN`, `LPDN` and `IDEN` in `site_si.ags`, `site_us.ags` and `site_v404.ags`; the B cases in
  `qc_defects.ags`; the join cases in `joins.ags`.
- **Example file:** `ht.examples`' `site.ags` gains `LDEN` and `LPDN` (🟡 here rather than in (b)), so the
  datasets' docs example and a P01 of unit weight run from it.

### Decisions
1. **Two datasets.** `p.density()` returns lab (`LDEN`) and field (`IDEN`) results together, one row per
   result, with `source` = `lab` or `field` and `test_type`, the way `p.permeability()` mixes lab and field
   (§6.4). `p.particle_density()` returns one row per `LPDN` result. Reasons:
   - both lab and field results are a bulk unit weight at a depth, so one P01 or P07 compares them;
   - particle density is a different property, one an engineer reviews by geology unit when choosing the
     Gs judgment in (b).
2. **Unit weights, not densities.** `p.density()` gives `bulk_unit_weight` and `dry_unit_weight` as γ = ρ g,
   with g = 9.80665 m/s² (standard gravity, exact). Reasons:
   - every consumer takes γ: P01, P07, the `unit_weight` judgment, `vertical_stress()`;
   - the registry already derives `bulk_unit_weight` from a density × g;
   - US practice reports unit weight in pcf, and γ and ρ display as the same pcf number (P00 §4.3 #1).

   Particle density stays a density (`particle_density`, Mg/m³), as the file gives it. Gs = ρs / ρw is (b)'s,
   decided together with γw (`ht.settings.water_unit_weight`, 9.81) against ρw g (9.807), so the two can't
   disagree.
3. **The density specimen's own water content.** `water_content` is `LDEN_MC` (or `IDEN_MC`), measured on the
   same specimen, never `LNMC` from another one. That is the pairing phase relations need (sheet 03 §7).
   `p.index_properties()` doesn't change.
4. **Particle density joined by sample.** Each lab density row gets `particle_density` from an `LPDN` specimen
   of the same sample: the one nearest in depth to the density specimen, with ties broken as in
   `p.index_properties()` (§6.6). The chosen specimen is in `particle_density_specimen_id`. Field rows, and
   samples with no `LPDN`, are blank, and nothing is borrowed from another sample (SPEC §2.6, never guess).
   - Reason: Gs is run on a different specimen from density, but on the same sample; that pairing is the
     data-layer answer (b)'s formulas build on.
   - One warning per call counts the samples where a choice was made, as §6.6 does.
5. **An assumed particle density** (`#2.65`) has its value and `particle_density_assumed = True`. It is never
   blank, and the flag never drops off. It travels with the join (decision 4). QC B004 lists these values
   (info), and (b) decides how they are used.
6. **Recompacted and stabilized records are kept and labeled.** `sample_condition` (`LDEN_COND`: `UNDISTURBED`,
   `RECOMPACTED`) and `stabilizer_content` (`IDEN_STAB`) are columns. Reason: they aren't in situ values, but
   dropping them would drop data silently; `where={"sample_condition": "UNDISTURBED"}` filters them. The
   docstring and the dataset spec say so.
7. **Field density depth.** `IDEN_DPTH` is a point depth, `depth_basis = "test_depth"` (SPEC §8.2). `IDEN`'s
   parent is `LOCA`, so field rows have no sample or specimen columns.
8. **QC (level 1) checks a record against itself, plus wide improbable-value ranges that catch unit slips**, as
   A003 and K001 do:
   - B001: dry density differs from ρ / (1 + w) on one `LDEN` row, beyond 🟡 `dry_density_tolerance: 0.03 Mg/m3`.
     The worst case of 2DP densities and a water content rounded to 1 % is 0.020 Mg/m³ (ρ = 2.20, w = 5 %);
     0.03 clears it.
   - B002: dry density above bulk density (error; w ≥ 0 makes that impossible).
   - B003: bulk or particle density outside a wide range, 🟡 `1.0–2.8` and `2.0–3.2 Mg/m3`. They catch a value
     in kg/m³ or pcf read as Mg/m³. The message says what lies outside (peat lower, ores and some rock higher),
     so the engineer checks the material as well as the unit.
   - B004: assumed particle density (info), one per record, as A004 is for NP.

   Checks across tests (S > 1 below the water level, ρs against ρd) are phase relations: (b).
9. **Minimum fields** (qc.md §4.10):
   - `LDEN`: required `<SPEC_KEY>`, `LDEN_BDEN`; recommended `SPEC_REF`, `SPEC_DPTH`, `LDEN_DDEN`, `LDEN_MC`,
     `LDEN_TYPE`, `LDEN_COND`;
   - `LPDN`: required `<SPEC_KEY>`, `LPDN_PDEN`; recommended `SPEC_REF`, `SPEC_DPTH`, `LPDN_TYPE`;
   - `IDEN`: required `LOCA_ID`, `IDEN_DPTH`, `IDEN_IDEN`; recommended `IDEN_MC`, `IDEN_TYPE`.

   Bulk density is the result the test reports (ISO 17892-2), so a record without it is incomplete (§7). A
   record with only a dry density and a water content is left out by default, with the §7 warning naming it.
10. **Templates.** `ht.template("density")` and `ht.template("particle_density")` are the datasets' columns
    without those only hangtu produces (`source_line`, `particle_density_specimen_id`), as SPEC §2.6 does for
    the M7 templates. The existing `index` template is unchanged.

### Sources
- **AGS 4.2 dictionary** (python-ags4 1.2.0, `Standard_dictionary_v4_2.ags`): `LDEN`, `LPDN` (parent `SAMP`)
  and `IDEN` (parent `LOCA`): headings, types, units and pick lists (`LDEN_COND`, `LDEN_TYPE`, `LPDN_TYPE`,
  `IDEN_TYPE`). Checked 2026-10-27.
- **Standard gravity** g = 9.80665 m/s² (exact, by definition). The pound and foot are exact by definition (P00 §4).
- No correlation or empirical source is used. B003's ranges are thresholds, not cited values.

### Acceptance criteria
Golden values hand-calculated (γ = ρ × 9.80665; 1 pcf = 0.45359237 kg / 0.3048³ m³ = 0.0160185 Mg/m³, and as
a unit weight 0.157087 kN/m³). Tolerance 1e-9 relative, unless a criterion says otherwise.
1. **Lab row (`site_si.ags`):** an `LDEN` row with ρ 1.95, ρd 1.56 Mg/m³ and w 25.0 % gives
   `bulk_unit_weight` 19.1230 kN/m³ (1.95 × 9.80665 = 19.12297), `dry_unit_weight` 15.2984 kN/m³,
   `water_content` 25.0, `source = "lab"`, its lab depth and `depth_basis` (§6.2) and `sample_condition`.
2. **US display:** the same row with `display_units="US"` gives 121.735 and 97.388 pcf (to 1e-4 relative, the
   precision of the hand calculation).
3. **Field row:** an `IDEN` row in BH1 (ground level 12.40 m) at 0.50 m with ρ 1.85 Mg/m³ and w 15 % gives
   depth 0.50 m, elevation 11.90 m, `depth_basis = "test_depth"`, `bulk_unit_weight` 18.1423 kN/m³,
   `source = "field"`, the `IDEN_TYPE` as `test_type`, and blank sample and specimen columns.
4. **Particle density:** `p.particle_density()` gives 2.68 and `particle_density_assumed = False` for `2.68`;
   2.65 and `True` for `#2.65`. Neither is blank.
5. **Join (`joins.ags`):** a sample with one density specimen and two `LPDN` specimens gets the nearest one's
   value, named in `particle_density_specimen_id`, with the warning; on a depth tie, the lower `SPEC_REF`. A
   sample with no `LPDN` gets a blank, and so does a field row. An assumed value keeps its flag after the join.
6. **Kept and labeled:** a `RECOMPACTED` record and an `IDEN` record with a stabilizer are rows, with
   `sample_condition` and `stabilizer_content` filled.
7. **QC (`qc_defects.ags`):** each B rule raises exactly the findings its case seeds:
   - B001: ρ 2.00, w 20 %, ρd 1.80. Expected ρd = 2.00 / 1.20 = 1.667, a difference of 0.133 Mg/m³, which the
     message gives.
   - B002: ρ 1.80, ρd 1.90, w blank.
   - B003: `LDEN_BDEN` 19.5, which is kN/m³ written as Mg/m³; `LPDN_PDEN` 26.5.
   - B004: `#2.65`.

   The dictionary's own example (1.66, 57 %, 1.06: a difference of 0.0027) raises no B001. Each threshold
   takes a quantity string in pcf as well as Mg/m³.
8. **Good files stay clean:** `site_si.ags`, `site_us.ags` and `site_v404.ags` raise no B001–B003 and no C001.
   Their info findings add only B004 (each good file carries one assumed particle density) and C002.
9. **Twins:** the SI and US files give equal `p.density()` and `p.particle_density()` (1e-9 relative) for each
   `display_units`, and the same B findings.
10. **Incomplete:** an `LDEN` row with ρd and w but no ρ is left out with the §7 warning, and kept by
    `include_incomplete=True` with a blank `bulk_unit_weight`.
11. **Empty:** a file with none of the groups gives empty frames with every column and the missing-group
    warning ("No LDEN or IDEN group", "No LPDN group").
12. **Feeds the plots:** `ht.plot.profile(p.density(), "bulk_unit_weight")` and
    `ht.plot.geology_unit_comparison(p.density(), "bulk_unit_weight")` run on the good files with no warning,
    in pcf with `display_units="US"`.
13. **Templates:** `ht.template("density")` and `ht.template("particle_density")` are the datasets' columns
    without `source_line` and `particle_density_specimen_id`, in the same order (`tests/test_registry.py`).
14. **Common arguments:** `depth=`, `geology=`, `holes=` and `where={"source": "field"}` filter `p.density()`
    as §2 says, including its field rows.

## Plan
Six build commits, each with ruff and pytest green. Reused, not rebuilt:
- `Build` (`datasets/_frame.py`): `rows()`, `numbers()`, `texts()`, `flagged()`, `finish()`;
- `specimens()` (`datasets/_lab.py`);
- `_specimens()`, `_sample_keys()` and `_nearest()` (`datasets/_index.py`), for the join;
- the QC `@rule` registry and `THRESHOLDS` (`qc/_registry.py`), and the `_unflagged`, `_where` and `_value`
  helpers (`qc/_tests.py`).

γ = ρ × 9.80665 lands in canonical units, because canonical density is Mg/m³ and canonical unit weight is kN/m³.

### 1. `M14: add LDEN, LPDN and IDEN to the test files`
- `tests/data/ags/_make_files.py`:
  - **Good files:** the groups, with AC 1, 3 and 4's values, a `RECOMPACTED` record, a stabilized `IDEN` and one
    `#2.65`. One `LPDN` specimen per sample, and every recommended heading present.
  - **`joins.ags`:** the join cases of AC 5, and an `LDEN` row with no `LDEN_BDEN`.
  - **`qc_defects.ags`:** the B cases of AC 7.
  - Every new group is appended after the existing ones, so no line number moves.
- Regenerate the files. The existing tests stay green.

### 2. `M14: add QC rules B001-B004 and density minimum fields`
- `src/hangtu/qc/_density.py` (new), imported in `qc/__init__.py`.
- `THRESHOLDS` (kind `density`), `rules.yaml` and `min_fields.yaml` (decision 9).
- Tests: `tests/qc/test_density.py` (AC 7, with a threshold given in pcf); `test_qc_acceptance.py` (AC 8, and AC 9
  for the findings).

### 3. `M14: add p.particle_density()`
- `columns.yaml`: `particle_density`, `particle_density_assumed`, `LPDN_TYPE` as a source of `test_type`, and the
  `particle_density` template.
- `datasets/_density.py` (new), `datasets/__init__.py`, and `Project.particle_density()`.
- Tests: `tests/datasets/test_density.py` (AC 4, AC 11 empty); `tests/test_registry.py` `DATASETS` (AC 13).

### 4. `M14: add p.density(), lab and field unit weights`
- `columns.yaml`:
  - `dry_unit_weight`, `sample_condition` and `stabilizer_content`;
  - new sources for `bulk_unit_weight`, `water_content` and `test_type`;
  - `test_depth` in `depth_basis`;
  - the `density` template.
- `density()`: LDEN through `specimens()`, IDEN as a point test (`test_depth`), `G = 9.80665`. Particle density
  columns are blank at this step.
- `Project.density()`.
- Tests: AC 1–3 (golden values), 6, 10, 11, 12 and 14; `test_registry.py` `DATASETS` and `ONLY_HANGTU` (AC 13).

### 5. `M14: join particle density to p.density() by sample`
- Lab rows take the nearest `LPDN` specimen of the same sample (`_sample_keys()`, `_nearest()`), with one
  warning counting the returned samples where a choice was made.
- `columns.yaml`: `particle_density_specimen_id`.
- Tests: AC 5.

### 6. `M14: density data in the example file; close out (a)`
- `tests/data/_make_examples.py`: `LDEN` and `LPDN` in US units, near `judgments.yaml`'s unit weights, with no new
  QC warning. Regenerate the example data.
- `docs/site/guides/datasets.md`: the two datasets. Run `prepare_site.py` and the strict docs build.
- **Close-out:**
  - `datasets.md` and `qc.md` status;
  - the parameter index: 01 A and 03 A part built; 02 B with LI and Ic in M8 and activity in M14 (b);
  - the `CLAUDE.md` status paragraph.
- **Look at the output:** `ht.plot.profile(p.density(), "bulk_unit_weight")` on the example project, US and SI.
- **Verification:** every AC reported as met or not, with its test; the lowest-versions run; the strict docs build.
