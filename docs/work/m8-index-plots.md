# M8: index plots, classification and gradation

## Intent

Shared intent for five units of work. Each one gets its own branch and is merged separately:

| Unit | Branch | Builds |
|---|---|---|
| Analyses | `m8-index-analysis` | `ht.analysis` plasticity classification, gradation (Dx, Cu, Cc, fractions), full USCS symbol, AASHTO group and group index |
| P04 | `m8-p04` | `ht.plot.plasticity_chart()` |
| P05 | `m8-p05` | `ht.plot.grain_size()` |
| Data for P06 | `m8-text-values` | Text values in a value column on P01 (TODO #15), and the datasets: the classification columns, `p.grain_size_summary()`, `p.index_properties()` |
| P06 | `m8-p06` | `ht.plot.water_content_profile()` |

The analyses are merged first. The other units branch off `main` after them, in the order of the table. This file lives on `m8-index-plots` until the intent is approved.

### Goal
Finish Phase 1's plots: P04 plasticity chart, P05 grain size distribution and P06 water content profile with Atterberg limits. Build the classification and gradation analyses they need (`docs/drafts/analysis.md` §2–3), and the datasets that M7 deferred until those analyses existed.

### Why
- M8 is next in SPEC §12.4 and is the first part of v0.2 (SPEC §1.3).
- The plasticity chart and the grain size curves are in the lab section of almost every geotechnical report. They're the most obvious gaps a v0.1 tester will notice.
- The classification and gradation analyses stand on their own: an engineer can get a USCS symbol, D10 or Cu for every specimen without drawing anything, and later plots use them (P17 uses the consistency index; P25 uses the size fractions).
- Users can't get `p.grain_size_summary()`, `p.index_properties()` and the classification columns from an AGS file until these analyses exist (`docs/data/datasets.md` §1, SPEC §10.2).

### Constraints
- Use the P00 framework and the P01 overlays (`plot/_overlays.py`). P06 builds on P01 and doesn't reimplement it.
- SPEC §2.6 (units; particle size stays in mm in both systems), §3 (plot contract), §4 (NP distinct from blank and counted; classification systems selectable per call and defined in the config), §10.3 and CLAUDE.md "Naming" (registry column names, checked against the whole registry), §11 (error messages), §12.1 (no new dependencies).
- Every standard's boundary, line and table lives in config with its citation, never in plot code (P05 draft pitfalls). One named system gives every boundary.
- Never drop data silently: NP specimens, curves with fewer than two points, Dx that can't be interpolated, and specimens a dataset can't combine are counted and reported.
- Dx is interpolated log-linearly and never extrapolated (analysis draft §3). Points are sorted by row, never one column at a time.
- Golden values are calculated by hand: A-line and U-line points, D-values from a hand-interpolated curve, Cu, Cc, and USCS and AASHTO symbols for boundary cases.
- **Done when** (SPEC §12.4): the P04–P06 acceptance criteria and the classification and Dx golden tests pass; each dataset feeds its plot unchanged; and `docs/plots/img/P04.png`, `P05-us.png`/`P05-si.png` and `P06-us.png`/`P06-si.png` are committed in each plot's close-out. TODO #15 meets its own criteria, written in its unit's spec step.

### Decisions (proposed, to settle in review)
1. **Where the specs live.** `docs/drafts/analysis.md` §2–3 is finished in place and marked decided, as §1 was in M3. P04 and P05 are promoted from `docs/plots/drafts/`. P06 has no draft, so its spec is written from scratch in its spec step.
2. **TODO #5 (verify the systems).** Verified in the analyses' spec step: ASTM D2487 USCS, AASHTO M 145, BS 5930 plasticity bands and ISO 14688-1 fractions. Claude doesn't have the standards themselves, so each value is checked against your copy (you are confirming the BS 5930 bands), or against a public secondary source that is named in the spec. TODO #5 closes when that's done.
3. **USCS scope.** The analysis gives the group symbol (including dual symbols such as SP-SM and GC-GM) from LL, PI, fines, sand and gravel percentages, Cu and Cc. The data don't say whether a soil is organic (that needs the oven-dried LL), so OL and OH are never assigned: the fine-grained symbol is the inorganic one, and the spec says so. Group names ("lean clay with sand") are left out. How a user records "organic" (no AGS heading holds it) and how P04 marks those specimens is TODO #22.
4. **P04 `regions=`** (P04 draft §14): in v0.2, as a user table of polygons in LL–PI space (`region`, then the vertices in order), so a region can be any shape, not only a rectangle. Drawing a project's group definitions is common, and the table is simple. The v0.4 item ("plasticity-chart data region", computed from the data) stays in v0.4, and returns its region in this same table, so it draws through `regions=` and keeps any shape.
5. **P05 header band** (P05 draft §14): with `astm_uscs`, fines is one band, because USCS has no clay–silt boundary. The `iso14688` system shows clay and silt separately. **Fraction systems** are one data structure: a named, ordered list of fractions with their boundaries in mm and a citation. The built-in ones (`astm_uscs`, `aashto`, `iso14688`) are read from config, and `fractions=` also takes a user's own in the same structure. The gradation analysis and the P05 header band both read it. `envelopes=` (user table) and `d_values=` are in v0.2.
6. **Text in a value column (TODO #15)** is built in its own unit before P06, because it changes P01 and P06 builds on P01. `NP` and `refusal` are recognized as flags (the `non_plastic` and `refusal` reasons). Any other text is counted, with a warning naming it, rather than being an error. Each text value is drawn as a marker at the left edge of the axis at its depth, one marker per unique text, with a legend entry such as "NP (3)". The stats box counts them the same way (`describe()` follows in Phase 3). The user cleans the data and reruns to remove them. P06 also reads NP from the `non_plastic` column that the datasets fill.
7. **SPEC §13 #2 (specimen combining in `p.index_properties()`).** Settled in P06's spec step. Proposed: one row per sample; where a sample has several specimens of a test, take the one nearest in depth to the water content specimen, and record which one in a column, with a warning that counts them. No row is multiplied.
8. **Column names.** New columns (the plasticity class, `gradation_uscs`, `uscs_symbol`, `aashto_group`, `aashto_group_index`, and one column per size fraction) are named in the analyses' spec and checked against the whole registry before they're added.

### Out of scope
- P25 (size fractions by geology unit). SPEC §1.3 doesn't list it for v0.2, and its draft now says so. The fractions this unit computes can already be drawn on P07.
- User-defined PSD regions and the plasticity chart's computed data region (v0.4).
- OL and OH, USCS group names and BS 5930 soil descriptions.
- Coloring P04 by USCS symbol (P04 draft §15), and envelopes computed from the data on P05 (P05 draft §15).
- Triaxial, clogging and SPT correlations (M11–M13).
- Changes to P01–P03 and P07, other than TODO #15 (decision 6) and fixing a mismatch that the "dataset feeds the plot unchanged" test finds.

### SPEC sections touched
- §4: the pointer to `analysis.md` §2–3 now says they're decided.
- §10.2: the M8 datasets are moved from "v0.2" to built at close-out, with columns in `docs/data/datasets.md`.
- §11: the Phase 1 sketch gets `grain_size()` and `water_content_profile()` calls.
- §12.4: M8 is marked done at close-out.
- §13 #2: settled (decision 7) and removed.
- `docs/drafts/analysis.md` §2–3; `docs/plots/P01-property-profile.md` §3, §8 and `docs/plots/README.md` "Out-of-range data" (decision 6); `docs/plots/README.md` (P04–P06 status); `docs/data/datasets.md` (its out-of-scope line, plus the new datasets); `docs/drafts/phase2-data.md` (the M8 datasets move out); `columns.yaml`; `config/defaults.yaml` or new config files for the systems; TODO #5 and #15 (closed), #22 (new).

## Plan: analyses

Spec: [`docs/drafts/analysis.md`](../drafts/analysis.md) §2–3, finished in the spec step (intent decision 1).

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines (not counting tests' data) is split.

### Package layout
```
src/hangtu/
  _data.py                        + flag_column(): reads a true/false column (moved from analysis/_spt.py)
  analysis/__init__.py            exports plasticity, gradation, uscs, aashto
  analysis/_plasticity.py         plasticity(), on_or_above_a_line(), the class rules (§2.4–2.5)
  analysis/_gradation.py          gradation(), passing_at(), d_value(), fraction systems (§3)
  analysis/_classification.py     uscs(), aashto() (§2.6–2.7)
  config/plasticity_systems.yaml  uscs and bs5930 lines and bands, with sources (§2.3)
  config/fraction_systems.yaml    astm_uscs, aashto, iso14688, with sources (§3.5)
  columns.yaml                    the new columns (decision 5)
tests/analysis/
  test_plasticity.py  test_gradation.py  test_fraction_systems.py  test_uscs.py  test_aashto.py
```
The modules are private (`_plasticity.py`), so `ht.analysis.plasticity` is the function and not a submodule, as with `_spt.py`.

### Decisions the build makes
Implementation choices §2–3 leave open. Any that changes what a user sees goes into the spec in the commit that builds it.
1. **One true/false reader.** `spt()` already reads `spt_refusal` cell by cell (true/false, 1/0, yes/no). It moves to `hangtu/_data.py` as `flag_column(df, column, hint)` in a refactor commit of its own, and `plasticity()` uses it for `non_plastic`.
2. **One A-line test.** `on_or_above_a_line(liquid_limit, plasticity_index, system)` in `_plasticity.py`, with the 1e-9 slack, is used by both class columns, by `uscs()` through them, and by P04 later.
3. **One passing function.** `passing_at(sizes, passing, size)` gives P(size) by the §3.5 rules (log-linear, exact at a point, P(0) = 0, the 100% and 0% ends, blank otherwise). `d_value(sizes, passing, x)` gives the finest crossing (§3.3). Fractions and D-values share the sorting and the monotonic check, so they can't disagree.
4. **The non-monotonic tolerance** is read from P001's default in `qc/rules.yaml` (0.5 %), not repeated, so it can't drift from QC. A project's QC override doesn't change it.
5. **Registry:** `plasticity_class_uscs`, `plasticity_class_bs5930`, `uscs_symbol`, `aashto_group` (text); `aashto_group_index` (number, count); `fraction_system` (text); `d15`, `d50`, `d85` (particle_size); `fines_content`, `sand_content`, `gravel_content`, `cobbles_content`, `boulders_content`, `silt_content`, `clay_content`, `silt_clay_content`, `fine_sand_content`, `coarse_sand_content` (percent, ratio). Each is checked against the whole registry by the naming test, with `ags: ["derived: docs/drafts/analysis.md §…"]`. GRAG fractions aren't read (analysis draft §3: always recomputed).
6. **Curves are grouped** on (`loca_id`, `specimen_id`) when `loca_id` is present, else `specimen_id`, keeping blanks in the keys and the order of first appearance (`groupby(..., sort=False, dropna=False)`). A curve whose key is blank is an error naming its rows, since its points can't be told apart.
7. **Fraction systems are checked by one validator**, run on the built-ins by a test and on a user's system at each call: names unique and unused in the registry (except the built-in fraction names), sizes in mm increasing, each lower = the previous upper, the first lower 0, the last upper `null` (open), parts inside their fraction.
8. **Units:** `particle_size` is resolved as SPEC §2.6 with `analysis=True` and converted to mm. The output's `attrs["units"]` lists the D-value columns in mm and keeps the input's other declared units.

### Build 1: `analysis: move the true/false column reader to _data`
- Refactor only (decision 1): `spt()` behaves the same, and its tests pass unchanged.

### Build 2: `analysis: add plasticity systems and ht.analysis.plasticity`
- `config/plasticity_systems.yaml`; `_plasticity.py` (§2.3–2.5; decisions 1–2); `columns.yaml`: the two class columns.
- Errors and warnings as §2.8 (the `plasticity()` ones).
- Tests, with the §2.9 golden values: the indices (LL 45, PL 20, w 30 → PI 25, LI 0.40, Ic 0.60); PI kept and warned when 1 point off; NP blanks; every USCS and BS 5930 class case listed; on the A-line → clay; PI > LL kept and warned; rows, order, `attrs` and `df` unchanged.

### Build 3: `analysis: add ht.analysis.gradation with D-values, Cu and Cc`
- `_gradation.py`: sorting, grouping, units, the monotonic check, `d_value()`, Cu and Cc, the carried columns (§3.3–3.4; decisions 3, 4, 6, 8). `columns.yaml`: `d15`, `d50`, `d85`.
- Tests on curve A (§3.7): D10 0.1261, D30 0.300, D60 0.7105 mm; Cu 5.633, Cc 1.004; D30 with the point at 30% removed; D10 blank on a curve starting at 15%; drops of 0.4 and 2 points; inches converted; rows shuffled give the same answer; fewer than two points; `d_values=(15, 85)`; the errors of §3.6.

### Build 4: `analysis: add fraction systems to ht.analysis.gradation`
- `config/fraction_systems.yaml`; the validator (decision 7); `passing_at()`; the `<fraction>_content` and `fraction_system` columns; `fractions=` as a name, a dict or a YAML path. `columns.yaml`: the fraction columns and `fraction_system`.
- Tests: curve A's fractions in all three systems (§3.7), including the blank ISO fractions; the fractions sum to 100 when none is blank; every built-in boundary against the §3.5 table (catches 0.475 and 20); a user system from a dict and from a file; an overlap, a gap and a name clash are errors naming the fraction.

### Build 5: `analysis: add ht.analysis.uscs`
- `_classification.py`: `uscs()` (§2.6): the `fraction_system` check, rescaling to the part finer than 75 mm, G/S, W/P, M/C, the dual symbols, the blanks counted by reason. `columns.yaml`: `uscs_symbol`.
- Tests: every §2.9 USCS symbol case; Cu and Cc from `d10`/`d30`/`d60` when blank; a missing or wrong `fraction_system` is an error; `gradation()` on curve A joined with its Atterberg row classifies end to end (SP).

### Build 6: `analysis: add ht.analysis.aashto`
- `aashto()` (§2.7): rounding, groups left to right, the group index, blanks counted. `columns.yaml`: `aashto_group`, `aashto_group_index`.
- Tests: every §2.9 AASHTO case, including A-2-4 against A-1 order, the A-7-5/A-7-6 split, a negative GI → 0, LL 40.4 rounding; a wrong `fraction_system` is an error.

### Build 7 (close-out): `analysis: close out the classification and gradation analyses`
- `docs/drafts/analysis.md` §2–3: any detail the build changed. The 🔬 values stay marked until TODO #5 is done.
- `CLAUDE.md`: the status line says the M8 analyses are done and P04 is next.
- This plan: a Results section, with notes for P04, P05 and the data unit.

### Verification
- After each build: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- At close-out: Python 3.13 and 3.14 (`uv run --isolated --python 3.1x pytest`); the lowest dependency versions, as in CLAUDE.md; `uv build`, and check that the wheel has both new config files and the new registry columns.

### Results
- 1664 tests pass on Python 3.12, 3.13 and 3.14, and with the lowest dependency versions (matplotlib 3.8.0, numpy 1.26.0, pandas 2.1.1, pint 0.24.4, pyyaml 6.0.1). The wheel has both new config files and the new registry columns.
- **Commits:** one per build step as planned, Build 1 being the refactor.
- **Changes from the plan:**
  - The fraction systems are in their own module, `analysis/_fractions.py`, rather than in `_gradation.py`, which was already about 300 lines (Build 4).
  - Two input errors in `plasticity()` that §2.8 didn't list: PL above LL on a plastic specimen, and a specimen marked NP with a PI. Recorded in §2.8.
  - A blank `specimen_id` in `gradation()` is an error (decision 6), recorded in §3.6.
  - A user's fraction system needs a `name`, not one of the built-in ones, so `uscs()` can't take it for `astm_uscs` (§3.5).
  - The Cu, Cc and fines limits in `uscs()` are compared with the A-line's 1e-9 slack: Cc = 0.3²/(0.1 × 0.9) computed as 0.9999999999999999 and made a well-graded sand poorly graded (§2.6).
  - `aashto()` leaves a group blank only when a missing value could decide it; a group a known value rules out is skipped (§2.7).
- **For P04:** draw the lines from `config/plasticity_systems.yaml` (`plasticity_system()`, `a_line()`, `on_or_above_a_line()` in `_plasticity.py`). The U-line's vertical part ends at PI = 7, as D2487 states it, while the sloped part starts at (16, 7.2); P04's spec decides how to join them.
- **For P05:** the header band reads the fraction system's `parts`; `fraction_system()` in `_fractions.py` resolves `fractions=` the same way `gradation()` does.
- **For the data unit:** `p.atterberg()` still computes LI and Ic itself (`datasets/_lab.py`); switch it to `plasticity()` there (§2.4). `index_properties()` runs `gradation()` twice (astm_uscs for `uscs()`, aashto for `aashto()`).
- **Still open:** the 🔬 values (TODO #5), including whether D2487 takes Cu and Cc from the curve rescaled to the part finer than 75 mm.
