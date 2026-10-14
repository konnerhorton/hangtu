# M7: Depth, elevation and geology joins, and datasets

## Intent

### Goal
Turn a project's canonical tables into the DataFrames the Phase 1 plots take: `p.spt()`, `p.atterberg()`, `p.grain_size()` and `p.permeability()` return one row per test (or per curve point), with registry column names, `df.attrs["units"]` attached, and each test's depth, elevation and geology unit joined on by the SPEC §8 conventions. `p.locations` gives one row per hole, and `p.set_geology_map(path)` maps the file's geology codes to the units an engineer reports on.

### Why
- It's the last Phase 2 unit before M8 (SPEC §1.3, §12.4 M7). Until now ingest and QC store and check the data, but an engineer can't get from an AGS file to a plot without writing SQL.
- The SPEC §11 sketch, `ht.plot.spt_profile(p.spt(geology=["Alluvium"]))`, is what v0.2 promises.
- Depth, elevation and geology joins are where results most easily go wrong without anyone noticing (a test put in the wrong unit at a boundary, an SPT at its top depth instead of its mid-drive depth), so they belong in one tested place rather than in each user's script.

### Constraints
- SPEC §8 (decided): `elevation = ground_level − depth`; test depth by data type with a `depth_basis` column; geology key configurable (default `GEOL_GEOL`), mapping file matched exactly and case-sensitively; interval rule `top ≤ d < base`, the last interval includes its base, the lowest top wins on overlaps.
- SPEC §10.2: datasets return exactly the shape the Phase 1 plots expect; common filters named `where=`, `contains=`, `elevation=`, `depth=`, `holes=`, `geology=`, `geology_fields=`, `include_incomplete=`, `display_units=`.
- SPEC §7: datasets read the canonical layer through `db.py` and join on surrogate keys; values hangtu calculates (N60, mid-drive depth, elevation) are computed, not stored; value flags become columns (`spt_refusal`, `non_plastic`, `qualifier`).
- SPEC §2.6 and CLAUDE.md: column names come from the registry, and new ones are checked against all of it; units travel in `df.attrs["units"]`.
- Never drop data silently: records left out (incomplete, outside any geology interval, unmapped code) are counted and said, not lost.
- Inputs: the dataset column lists in `docs/drafts/phase2-data.md`; M6's handoff (`qc/_data.py` for record depths, C001 as the incomplete set, G004 deferred here); TODO #17 (particle size in inches).
- No new dependency. Test files are the existing synthetic ones, extended where a case is missing.
- **Done when:** each dataset feeds its Phase 1 plot unchanged (P02 and P03 from `p.spt()`, P01 and P07 from the others), the SI and US twin files give the same datasets, and the spec's acceptance criteria pass, with hand-calculated mid-drive depths and boundary cases.

### Decisions (proposed, to settle in review)
1. **Where the spec lives:** `docs/data/datasets.md`, a topic doc next to `ingest.md` and `qc.md`. The dataset section of `docs/drafts/phase2-data.md` moves there.
2. **Datasets in this unit:** `p.spt()`, `p.atterberg()`, `p.grain_size()` (long curves) and `p.permeability()`, with the values the file gives and the analyses that already exist (`ht.analysis.spt()` for refusal, N60 and capped N).
   - **Deferred to M8**, because they need the classification and gradation analyses M8 builds: the classification columns (`plasticity_class_*`, `gradation_uscs`, `uscs_symbol`, AASHTO), `p.grain_size_summary()` and `p.index_properties()`, and with it SPEC §13 #2 (specimen combining).
   - `liquidity_index` and `consistency_index` are simple formulas and could come now; proposed: now.
3. **Settle SPEC §13 #1** (SPT mid-drive fallback when the increments are missing) in the spec step, since this unit is the first to use it.
4. **Geology:** `p.set_geology_map(path)` stores the mapping in `meta_geology_map`; codes the map doesn't cover are QC `G004` (deferred from M6), and in the datasets keep their code as `geology_unit` with a warning naming them, rather than being dropped. `geology_fields=` carries more GEOL headings side by side.
5. **Incomplete records** (QC C001, from `qc/min_fields.yaml`) are left out by default and counted in a warning; `include_incomplete=True` keeps them.
6. **TODO #17:** `GRAT_SIZE` gets the `particle_size` kind at ingest, so US output keeps sieve sizes in mm. This touches ingest and needs a re-ingest (schema version bump).
7. **Test files:** reuse `site_si.ags`, `site_us.ags` and `site_v404.ags`; add cases for depth boundaries, missing SPT increments, overlapping geology and unmapped codes, in the existing generator script.

### Out of scope
- The M8 items in decision 2.
- `p.settings.to_yaml()`/`load_yaml()` and storing QC overrides with the project (`docs/data/ingest.md`, `qc.md`): useful, but independent of the datasets. Proposed as a small unit of its own after M7.
- Datasets beyond the four (undrained strength across test types, consolidation, triaxial): later, as their plots arrive.
- Inclined holes (flagged by QC L004, SPEC §1.4); more than one file per project; AGSi.
- Changes to the Phase 1 plots, other than fixing a mismatch the "feeds the plot unchanged" test finds.

### SPEC sections touched
- §8.2: the nominal mid-drive fallback decided (§13 #1 removed).
- §8.3: the geology map's storage and behavior for unmapped codes, if decision 4 changes what it says.
- §10.2: dataset list and signatures confirmed, the M8 split noted, and the column lists replaced by a pointer to `docs/data/datasets.md`.
- §11: the Phase 2 sketch checked against the real API.
- §12.4: M7 done at close-out; M8 picks up the deferred datasets.
- `docs/data/ingest.md` (decision 6), `docs/data/qc.md` (G004), `docs/drafts/phase2-data.md` (dataset section moves out), `columns.yaml` (new columns), TODO #17.

## Plan

Spec: [`docs/data/datasets.md`](../data/datasets.md).

Each build step below is one commit with ruff and pytest passing. A step that goes past about 300 changed lines (not counting test data) is split.

### Package layout
```
src/hangtu/
  datasets/__init__.py        locations(), spt(), atterberg(), grain_size(), permeability()
  datasets/_geology_map.py    read and check a map (CSV or DataFrame), errors (§5.2)
  datasets/_joins.py          spt_depth(), lab_depth(), zone_depth(), place_in_geology(), elevation (§5.4, §6)
  datasets/_frame.py          shared pipeline: incomplete rows, geology columns, filters,
                              display units + attrs, warnings, empty frame (§2, §4, §7, §8)
  datasets/_spt.py  _lab.py  _permeability.py   one builder per dataset (§6.1–§6.4)
  project.py                  + locations, set_geology_map(), geology_map, spt(), atterberg(), ...
  db.py                       + meta_geology_map table, write/read helpers; SCHEMA_VERSION 2
  ags/_units.py               particle-size headings → particle_size kind (§10)
  _settings.py, config/defaults.yaml   + geology_key
  qc/_fields.py               incomplete-record helper shared with datasets
  qc/_geology.py, qc/rules.yaml        + G004
  qc/min_fields.yaml          SPEC_REF, SPEC_DPTH → recommended
  plot/_palette.py (+ callers) df.attrs["palette"] and categorical order
  columns.yaml                new and changed columns (§11)
tests/datasets/               test_geology_map.py  test_joins.py  test_frame.py  test_spt.py
                              test_lab.py  test_permeability.py  test_datasets_acceptance.py
tests/data/ags/               joins.ags, strata.csv (new); site_* gain GEOL_GEOL and SPT increments
```

### Decisions the build makes
Implementation choices the spec leaves open. Any choice that changes what a user sees goes into `datasets.md` in the commit that builds it.
1. **Datasets read through `qc._data.Data`.** It already caches canonical tables, flags, raw text (for blank vs flagged) and headings. That was M6's handoff; it gets no copy and no move. Datasets construct a `Data` for each call.
2. **The joins work in SI with no I/O.** `_joins.py` functions take DataFrames in m/mm and return depth, `depth_basis` and the geology row index. The golden tests call them directly. Conversion to display units happens once, last, in `_frame.py`.
3. **Display conversion** uses `units.to_display` per numeric column, with the registry's quantity kind, inside `settings.override(display_overrides=<project's>)`. That way the project's overrides apply rather than the session's, as in QC. `df.attrs["units"]` gets a unit string that `units.parse_unit` reads back. A test checks the round trip for every column.
4. **The incomplete-record helper** comes out of C001 as `incomplete_rows(data, group, required) -> Series[bool]` in `qc/_fields.py`. C001 and the datasets both use it, so they can't disagree. This is a refactor in its own commit.
5. **SPT refusal and N60** go through `ht.analysis.spt()` unchanged:
   - `spt_refusal` is True where the `REFUSAL` flag is set, else NA.
   - `spt_n60` is pre-filled from `ISPT_N60`.
   - `energy_source` is set from which input was used, before and after the call.
6. **`geology_unit`** is an ordered `pd.Categorical`: mapped units in map order, then unmapped codes in order of first appearance. With no map it's a plain object column (no order is known).
7. **Plots:** `resolve_palette(units, palette, order, data_palette=None)` takes the data's colors after `settings.palette`. Each caller passes `df.attrs.get("palette")` and, when `order` isn't given and the color column is categorical, its categories. The callers are `_values.py` (P01/P02), `_spt_histogram.py` (P03) and `_geology_units.py` (P07). The strata overlay keeps its own table.
8. **The schema version goes to 2** in the particle-size step. The `meta_geology_map` table is created by every ingest in the map step, so the same version covers both.

### Build 1: `M7: make SPEC_REF and SPEC_DPTH recommended fields`
- `qc/min_fields.yaml`: the anchor becomes the sample key, and `SPEC_REF`/`SPEC_DPTH` lead each lab group's `recommended` list (qc.md §4.10, already updated).
- Update the QC tests whose C001/C002 expectations change.

### Build 2: `M7: give particle-size headings the particle_size kind`
- `ags/_units.py`: `GRAT_SIZE`, `LLPL_SIZE` and `PTST_SZUN` → `particle_size`. `db.SCHEMA_VERSION = 2`.
- Tests: the quantity in `meta_heading`; `p.diff("GRAT")` and a P-rule message in US show mm; opening a version-1 database asks for a re-ingest.

### Build 3: `M7: add the geology_key setting`
- `_settings.py` validator (the five GEOL headings; an error lists them), `config/defaults.yaml`. It is stored per project through `from_ags` like the other settings.
- Tests in `tests/test_settings.py` and `tests/test_project.py`.

### Build 4: `qc: share the incomplete-record check` (refactor, decision 4)
- C001 output is unchanged; the existing tests pass as they are.

### Build 5: `M7: add the M7 cases to the AGS test files`
- `_make_files.py`:
  - `GEOL_GEOL` in `site_si`, `site_us` and `site_v404`;
  - `ISPT_INC1–6`/`ISPT_PEN1–6` on BH1 and BH2: a complete drive, and a refusal in the test drive, with exact inch values in the US twin;
  - new `joins.ags` with the spec §12 edge cases, and `strata.csv`.
- `tests/data/ags/README.md` gets the new rows. `test_files.py` checks that `joins.ags` passes python-ags4.
- Update the existing M5/M6 expectations the new headings change (C002 counts, twin comparisons).

### Build 6: `M7: add the dataset columns to the registry`
- `columns.yaml`: the spec §11 new and changed entries. The registry naming test covers them.

### Build 7: `M7: add the geology map`
- `db.py`: `meta_geology_map` (`code`, `geology_unit`, `soil_class`, `order`, `color`), plus `write_geology_map`/`read_geology_map`.
- `datasets/_geology_map.py`: read and check the map (§5.2 errors, with CSV line numbers).
- `Project.set_geology_map()`/`geology_map`.
- Tests (`test_geology_map.py`): round trip; `None` clears it; each error; a DataFrame input; `overwrite=True` drops the map.

### Build 8: `M7: check for unmapped geology codes (G004)`
- `qc/_geology.py` G004 and `rules.yaml`, through `Data` reading the map.
- Tests: no map → 0 checked; one finding per code with its count, at the first line; a blank code isn't a finding. The `qc_defects`/good-file QC expectations are unchanged without a map.

### Build 9: `M7: add depth and geology joins`
- `datasets/_joins.py` (decision 2).
- Tests (`test_joins.py`), golden values hand-calculated in comments:
  - mid-drive with increments: complete drive and stopped drive;
  - nominal fallback with `NPEN` 450 (`+300 mm`), 300 (BH1 6.00 → 6.225 m), 200 (`+175 mm`), 100 (seating only → `+100 mm`) and blank (`+300 mm`);
  - lab depth through all three fallbacks;
  - zone midpoint, and one end blank;
  - `top ≤ d < base`, the deepest layer's base, a gap, overlaps resolving to the deepest top, and no GEOL.

### Build 10: `M7: add p.locations and the shared dataset pipeline`
- `datasets/_frame.py` (decisions 3, 6) and `Project.locations`.
- Tests (`test_frame.py`):
  - each common filter, including quantity strings and `None` ends;
  - every §2 error;
  - `where=`/`contains=`;
  - the geology key absent, with its warning;
  - unmapped codes and the overlap warning;
  - incomplete rows left out, and kept with `include_incomplete=True`;
  - the empty frame with its warning;
  - attrs units in US and SI.

### Build 11: `M7: add p.spt()`
- `datasets/_spt.py`, `Project.spt()` (decision 5).
- Tests: §6.1 golden rows from `site_si`; refusal and `spt_n` as written; `energy_source` in all four cases; a file `ISPT_N60` kept.

### Build 12: `M7: add p.atterberg() and p.grain_size()`
- `datasets/_lab.py`.
- Tests:
  - PI filled from LL − PL;
  - NP gives blank limits and `non_plastic`;
  - the water content join, and the several-LNMC warning;
  - LI and Ic golden values, blank cases and PI ≤ 0;
  - `sample_reference` text;
  - grading points in file order, `qualifier` from `LT`.

### Build 13: `M7: add p.permeability()`
- `datasets/_permeability.py`.
- Tests: PTST, FGHG and IPRG rows with `source`/`test_type`/`depth_basis`; `<1` → qualifier; IPRG one row per stage from `site_v404`; FGHS not included.

### Build 14: `M7: color plots by the geology map` (decision 7)
- `plot/_palette.py` and its three callers.
- Tests in `tests/plot/`: a map color is used; `ht.settings.palette` wins over it; categorical order is respected in P03/P07 and in the P01 legend; no change without attrs.

### Build 15: `M7: test datasets against the acceptance criteria`
- `test_datasets_acceptance.py`: spec §13 #1–#13 end to end, on fixtures built once per session. #1 calls the five plots with `pytest.warns` not expected (warnings are errors).

### Build 16 (close-out): `M7: close out depth/geology joins and datasets`
- `datasets.md` status → done, with any user-visible decision above;
- SPEC §12.4 M7 done, and the §11 sketch checked against the API;
- `CLAUDE.md` state line (M7 done, M9 next);
- `README.md` if the v0.1 row needs it, and `TODO.md` if anything came up;
- this plan's Results.
- Not a plot unit, so no `docs/plots/img` figure. The hand check below looks at plots from `p.spt()` instead.

### Verification
- `uv run ruff check . && uv run ruff format --check . && uv run pytest` at every commit.
- Before the close-out: the lowest-version run (CLAUDE.md, Commands), then `git checkout uv.lock`.
- By hand:
  - ingest `site_us.ags`, set `geology_key`, set `strata.csv`, then print `p.spt()` and `p.atterberg()` and read them as an engineer (depths, `depth_basis`, units in attrs);
  - draw `spt_profile(p.spt())` and `geology_unit_comparison(p.atterberg(), "plasticity_index")` to PNGs in the scratchpad, and look at the colors and order;
  - on `joins.ags`, read each warning: does it say what is wrong, where, and what to do?

### Results
- 1500 tests pass on Python 3.12 and with the lowest dependency versions.
- **Commits:** one per build step, plus `analysis: allow for conversion rounding in the SPT refusal rule` between Build 11's code and its commit. Build 10 (the shared pipeline) went past the ~300-line guide and was left as one commit, since the joins, filters and warnings share `finish()` and its tests.
- **Changes from the plan and spec**, each recorded in `datasets.md` (or `analysis.md`) in the commit that made it:
  - The SPT refusal rule compares with a 1e-6 mm slack: 450 mm written in inches to 10 significant figures converts back to 449.99999992 mm, which the twin-file test caught as a refusal (analysis.md §1.3).
  - BH1's refusal in the site files has increments 75, 75, 75 and 50 mm, so its golden depth is 6.2125 m (`mid_drive`), not the spec draft's 6.225 m.
  - Two `LNMC` rows on one specimen break AGS Rule 10a, so that case is built in a test rather than kept in `joins.ags` (§12).
  - `specimen_id` stays text (the registry type), holding the project's specimen key.
  - The map check also rejects a column hangtu doesn't read, a blank code or unit, a non-numeric `order`, and one unit with two orders (§5.2).
  - An NP specimen keeps a liquid limit the file gives; only the flagged values are blank (§6.2).
  - `sample_reference` without `SAMP_ID` quotes `SAMP_TOP` as the file wrote it, in its unit (`U1 at 1.50 m`). `SAMP_ID` is part of the required sample key, so that case appears only with `include_incomplete=True`.
  - Warnings count in the singular or plural (`1 SPT result`), and `elevation=` warns about rows it leaves out for having no elevation.
  - G004 isn't in `qc_defects.ags`, since it needs a map; its case is `joins.ags` with `strata.csv`.
- **Read by hand** on `site_us.ags` with `strata.csv` (US): depths and elevations in ft with `mid_drive`/`mid_drive_nominal`, N60 sources, NP as `non_plastic`, units and palette in `attrs`. On `joins.ags`, each warning says what, where and what to do. `spt_profile` and `geology_unit_comparison` draw with the map's colors and order. Two things noted:
  - the test map's `tan` and `#d9b26f` are hard to tell apart; it's test data only;
  - a point exactly on P07's axis limit sits on the spine (TODO #18).
- **For M9:** the examples can use `site_us.ags` and `strata.csv` for the AGS → QC → plot path.
