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
