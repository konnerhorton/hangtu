# M13 (b3): Young's modulus and shear wave velocity from SPT

## Intent
M13 is wave 1's first milestone (SPEC §1.3, §12.4). Units (a), (b1) and (b2) built the judgments file and σ′v,
(N1)60 and the correlations framework, and the SPT correlations for φ′, s_u, σ′p/OCR and K0. This unit, (b3), is
the last of M13: stiffness, stage C of E (sheet 08) and Vs (sheet 10).

**Goal:** from a project's SPT data and its σ′v, an engineer gets estimates of Young's modulus and shear wave
velocity from published SPT correlations, on the framework as b1 and b2 left it: named on their rows, reading the
one input each was derived with, NaN with a reason outside its range, and comparable on P01 and P07.

**Why:** E from N is one of the most used and most misused SPT correlations in US practice. Its coefficients are
picked from a table by a soil description, and its unit is easy to misread: FHWA NHI-06-088 Table 5-16 gives
E = 4, 7, 10, 12 × (N1)60 in **tsf**, and the same factors read as **ksf** halve E (sheet 08 §2). Vs from N is the usual fallback for a site class or a G0 when no seismic
test was run. Both test parts of the framework the earlier units didn't:
- **a coefficient chosen by soil type** from the source's own wording, not a soil-type check on a single
  equation (b2's USCS map only says yes or no);
- **a target whose meaning depends on strain level.** E from N is a working-strain secant modulus; Vs gives a
  small-strain stiffness one to two orders of magnitude higher. An estimate that doesn't say which it is invites
  the classic mistake of using G0 as a design E (sheet 08 §7);
- constants in US customary units (tsf), converted with pint, where a golden value catches the unit trap.

**SPEC and TODO touched:** §4 (correlations: a coefficient by soil type), §10.3 (new registry columns), §12.4
(M13 done); TODO #20 (E and Vs settled here, closing it), #40 (deferred to M15), #41 (the warning's wording).

### Decided
1. **On the framework as b1 and b2 left it:** one function per published correlation, named target first
   (`<target>_<authors>_<year>`, SPEC §4); its entry in `config/correlations.yaml`; the one input column by
   registry name; NaN with `correlation_note`; bands as `<target>_lower`/`_upper` where the source gives one;
   chaining warns; the opt-in USCS map. A correlation whose equation, constants, N basis or range can't be
   verified against its source is cut, not built.
2. **Candidates** (sheets 08 and 10, analysis draft §4.2), to verify in the spec step:
   - **E:** AASHTO (2004) via FHWA NHI-06-088 Table 5-16, E = C (N1)60 tsf with C = 4, 7, 10, 12 by soil
     description (sheet 08 §5.1, [V] via an extract; ksi form in GEC 5 Table 8-11); Kulhawy & Mayne (1990),
     E/pa by N60 by soil type (analysis draft §4.2, [U]: not yet read in EPRI EL-6800).
   - **Vs:** Imai & Tonouchi (1982) and Ohta & Goto (1978), as given in GEC 5 Table 8-5 (sheet 10 §5.7, [V] for
     the GEC 5 form). The N basis needs checking: GEC 5 writes N60, while the original Japanese data are at the
     energy of their own hammers.
3. **Wave spec step** (process.md, "Stages and waves"): promote sheets 08 and 10 to `docs/site/parameters/`,
   publishing only [V] content and listing the methods not built here by wave (W2, W3, W5), verify the [U]
   citations the built correlations use and hand-calculate golden values, apply the publishing rule (TODO #30),
   and propose the new names against the registry.

### Out of scope
- G0 from Vs (G0 = ρVs²), E0 and the strain reduction E/E0 (sheet 08 §5.3), and γ0.7: stage B, W5. A G0 from a
  correlated Vs would also be chaining.
- E from s_u (Duncan & Buchignani 1976, [U]), from CPT, DMT, pressuremeter or the lab; ν; the Hardening Soil
  moduli (sheet 11).
- Vs from CPT, and site class (Vs30, ASCE 7).
- Relative density (M14); selection between estimates (M18).

### Decisions (intent review, 2026-10-26)
1. **Soil type for a coefficient: a required argument, with the USCS map on top.** A correlation whose
   coefficient depends on soil type takes a required argument naming the source's row (proposed `soil=`), with no
   default, like a judgment. With the existing `uscs=` opt-in, the row can come from `uscs_symbol` through
   hangtu's proposed map instead. One function per row was rejected: it multiplies functions for one
   correlation. Reason: the row is the engineer's reading of the log, so it is stated in the call, or read
   through a map that is visible and overridable (b2 review 4).
2. **The target is named in the correlation's own terms.** The column says what the source says the estimate
   is: for the SPT E correlations, a drained modulus (`drained_youngs_modulus`, to check against the registry),
   with the strain level and loading the source implies stated in the entry's `notes` and docstring. Reason: E
   without "drained" or a strain level is the ambiguity this unit exists to avoid, and W2 and W5 will add Eu,
   E50, Eur and E0 beside it.
3. **TODO #40 (correlation statistics) is deferred to M15**, where statistics are designed against their uses
   (comparison, characteristic values). b3 keeps scatter in `describe()` and the docstring, as b1 and b2 do.
4. **TODO #41's warning wording is done here**, in its own commit: the warning states the range only when some
   rows are outside it, and in the user's terms (e.g. field N over σ′v0/pa, not `normalized_n`). Its other
   question (gravelly sands under `not_for`, read from the group name or gradation) stays open unless the spec
   step finds b3 needs it.

### Open (for the spec step)
- **N basis of the Vs correlations.** GEC 5 Table 8-5 writes N60; check against the originals or a cited 60 %
  form (SPEC §4), and cut what can't be verified.
- **Kulhawy & Mayne (1990) E.** Read it in EPRI EL-6800: its equation, N basis, soil rows and whether its rows
  match AASHTO's, so both take the same `soil=` vocabulary or each its own.

## Spec

The E and Vs correlations from SPT on the framework as b2 left it, a coefficient chosen by the source's soil row,
two quantity kinds, TODO #41's warning wording, and pages 08 and 10. Numbered items refer to this section's
decisions unless they say "intent" or "review".

### Sources checked in this step
| Item | Source and locator | Result |
|---|---|---|
| E, AASHTO | FHWA NHI-06-088 (2006), Table 5-16, p. 5-85, "after AASHTO 2004 with 2006 Interims" | [V] Es (tsf) = 4, 7, 10, 12 × N1,60 for "Silts, sandy silts, slightly cohesive mixtures"; "Clean fine to medium sands and slightly silty sands"; "Coarse sands and sands with little gravel"; "Sandy gravel and gravels". pp. 5-83 to 5-84: "for preliminary design", "The definition of Es is not always consistent for the various correlations". No N range |
| E, AASHTO (ksi) | FHWA GEC 5 (Loehr et al. 2016), Table 8-11, p. 8-26, "modified from AASHTO, 2014"; §8.9.1, p. 8-25 | [V] Es (ksi) = 0.056, 0.097, 0.139, 0.167 × (N1)60: the tsf factors rounded (4 tsf = 0.0556 ksi, 0.8 % off; 12 tsf = 0.1667 ksi). §8.9.1 calls them "approximate estimates" of an "equivalent modulus" at working strains. The tsf form is built: it is the older source's own unit and its round numbers |
| E, Kulhawy & Mayne (1990) | EPRI EL-6800, Eqs. 5-26a–c, pp. 5-17 to 5-18 | [V] E/pa ≈ 5 N60 (sands with fines), 10 N60 (clean NC sands), 15 N60 (clean OC sands), "as a first order estimator"; "all attempts to date which correlate a modulus with N show considerable scatter". In the section on cohesionless soils, beside Fig. 5-13 "Comparative Plot of Drained Modulus Correlations for Sand". No N range, no statistics |
| Vs, Imai & Tonouchi (1982) | Wair et al. (2012), PEER 2012/08, Table 4.2, p. 28, Eq. (4.6); §4.1.3, p. 18; §4.2, p. 27 | [V] Vs = 97.0 N^0.31 on uncorrected N; Vs = 93.7 N60^0.31 at an assumed 67 % Japanese energy (Seed et al. 1985). H, P, T; alluvium and fill; n = 1654 pairs, 386 borings, 250 sites in Japan; r² = 0.75; N "from less than one bpf to nearly 400 bpf". Check: 97.0 (10 × 60/67)^0.31 = 191.39 against 93.7 × 10^0.31 = 191.31 m/s (0.04 %) |
| Vs, Ohta & Goto (1978) | Wair et al. (2012), Table 4.2, Eq. (4.3); §4.1.2, p. 18 | [V] Vs = 85.3 N^0.35 → 82.1 N60^0.35 (67 %), Quaternary alluvium, r² = 0.52; 289 pairs, mostly alluvial plains in Japan; N 2 to 200 bpf. The Holocene and Pleistocene forms (4.4, 4.5) need a geologic age and aren't built |
| Vs, GEC 5 Table 8-5 | GEC 5, Table 8-5, p. 8-20, "modified from Wair, et al., 2012" | [V] equations and r² match Wair row by row, but **the Notes column is shifted up one row**: GEC 5 labels 82.1 N60^0.35 "Holocene", 89.5 "Pleistocene", 130.3 "Holocene, Pleistocene, Tertiary; Alluvium, Fill" and Imai & Tonouchi's 93.7 "Tertiary"; Wair has Q, H, P and H/P/T. Wair, the source GEC 5 names, governs. Sheet 10 §5.7 is corrected |

### Changes
- **SPEC §4:** the "Correlations" bullet gains: a coefficient the source gives by soil type is chosen by a
  required argument naming the source's row (`soil=`), never inferred, and `uscs=` checks it rather than choosing
  it (Decision 3); the target is named as the source describes the estimate (Decision 2). **§12.4:** M13 done, at
  the close-out.
- **`config/defaults.yaml`:** two quantity kinds, `modulus` and `velocity` (Decision 6), and P01 presets for the
  new columns.
- **`columns.yaml`:** `drained_youngs_modulus`, `shear_wave_velocity` (Decision 7).
- **`config/correlations.yaml`:** four entries, and `rows:` for a coefficient by soil row (Decision 3); a `label`
  per range input or term for the warning (Decision 8).
- **`_framework.py`:** the soil row, and the warning's wording (Decision 8).
- **`docs/drafts/analysis.md` §4.2:** E and Vs marked as this unit's.
- **TODO:** #20 moves to Done; #40's "before b3 or M15" becomes "M15" (intent review 3); #41's wording item done,
  its gravelly-sands question kept.
- **Docs site:** sheets 08 and 10 promoted (Decision 9); the correlations guide gains the soil row and the strain
  level; reference entries for every new public name.
- **Parameter index:** at the close-out, stage C of 08 and 10 becomes **part built** (SPT: M13 b3).

### Decisions
1. **Four correlations:**

   | Function | Target | Input | Equation | Range |
   |---|---|---|---|---|
   | `drained_youngs_modulus_aashto_2004` | `drained_youngs_modulus` | `spt_n1_60` | E = C (N1)60 tsf, C by `soil=` | (N1)60 > 0 |
   | `drained_youngs_modulus_kulhawy_mayne_1990` | `drained_youngs_modulus` | `spt_n60` | E = C N60 pa, C by `soil=` | N60 > 0 |
   | `shear_wave_velocity_imai_tonouchi_1982` | `shear_wave_velocity` | `spt_n60` | Vs = 93.7 N60^0.31 m/s | 0 < N60 ≤ 447 |
   | `shear_wave_velocity_ohta_goto_1978` | `shear_wave_velocity` | `spt_n60` | Vs = 82.1 N60^0.35 m/s | 2.23 ≤ N60 ≤ 223 |

   - **AASHTO, named 2004:** the edition NHI-06-088 cites, and the source of the tsf constants built. The
     docstring cites AASHTO (2004) via NHI-06-088 and gives GEC 5's ksi form (AASHTO 2014) as the same factors
     rounded.
   - **E has no range in either source.** N of 0 gives E = 0, which is no estimate, so the lower bound is
     hangtu's (> 0, "below range"), said so in `notes`. There is no upper bound; the docstrings say the sources
     give none.
   - **Vs ranges** are the sources' N ranges at the 67 % energy Wair et al. assumed, as b1 did for Hatanaka &
     Uchida's 78 %: Imai & Tonouchi "less than one" to "nearly 400" → 0 < N60 ≤ 400 × 67/60 = 447; Ohta & Goto
     2 to 200 → 2.23 ≤ N60 ≤ 223. Both are "approximately" in the source, which `notes` says.
   - **Input:** the N60 forms of Wair et al. (SPEC §4: a correlation from another energy is used in its 60 % form
     from a cited source). The 67 % is Wair's assumption for Japanese practice, not measured; `notes` says so.
   - Refusals give no estimate (b1 Decision 2). No chaining is possible: every input is test data.
2. **Naming the target** (intent review 2). Both E sources describe a drained, working-strain modulus for
   granular soils: EPRI's beside "Drained Modulus Correlations for Sand", GEC 5's as an "equivalent modulus"
   at working strains. `notes` says what each source calls it (Es, E) and that it is not a small-strain E0, nor
   an Eu; AASHTO's silt row is noted as the one where drained loading is hangtu's reading. Vs is a measurement
   quantity with no such ambiguity.
3. **The soil row** (intent review 1, refined). An entry with `rows:` names each of the source's rows, with the
   source's wording, its coefficient, and hangtu's proposed USCS groups:

   | Function | `soil=` | Source's wording | C | Proposed USCS |
   |---|---|---|---|---|
   | AASHTO | `"silts"` | Silts, sandy silts, slightly cohesive mixtures | 4 tsf | ML, CL-ML |
   | AASHTO | `"clean_fine_to_medium_sands"` | Clean fine to medium sands and slightly silty sands | 7 tsf | SP, SW, SP-SM, SW-SM |
   | AASHTO | `"coarse_sands"` | Coarse sands and sands with little gravel | 10 tsf | SP, SW, SP-SM, SW-SM |
   | AASHTO | `"gravels"` | Sandy gravel and gravels | 12 tsf | GP, GW, GP-GM, GW-GM |
   | K & M | `"sands_with_fines"` | sands with fines | 5 | SM, SC, SP-SM, SW-SM, SP-SC, SW-SC |
   | K & M | `"clean_normally_consolidated_sands"` | clean NC sands | 10 | SP, SW |
   | K & M | `"clean_overconsolidated_sands"` | clean OC sands | 15 | SP, SW |

   - `soil=` is required, with no default: one row name for every row of `df`, or `{geology_unit: row}`, read
     from the `geology_unit` column. A unit on the rows that the mapping doesn't name is an error naming it; an
     unknown row name is an error listing the rows. The row used is on each result row (proposed column
     `correlation_soil`) and in attrs.
   - **`uscs=` checks the row; it doesn't choose it.** This changes intent review 1, which let the USCS map pick
     the row: the sources' rows split what a USCS symbol can't (fine against coarse sand, NC against OC), so a
     symbol can't choose one. With `uscs="proposed"`, rows whose `uscs_symbol` is outside the chosen row's groups
     get NaN, "not for this soil", as in b2. Agreed in spec review (2026-10-26): explicit wins.
4. **Vs and soil type.** Both Vs correlations are for "all soils" in Wair's grouping, so their entries have no
   proposed USCS groups: `uscs="proposed"` raises, saying so; a list of groups still works.
5. **Units of the constants.** AASHTO's C is in tsf (1 tsf = 2000 lbf/ft² = 95.76 kPa) and converted with pint;
   Kulhawy & Mayne's is a multiple of pa = 100 kPa (b1 Decision 8); Vs is in m/s. The tsf constant is the unit
   trap the intent names: the golden values check 140 tsf → 13 406 kPa, not the 6 703 kPa of reading it as ksf.
6. **Two quantity kinds.** `modulus`: canonical kPa, displayed in MPa (SI) and ksf (US), so an E reads 13.4 MPa
   or 280 ksf rather than 13 406 kPa or 280 000 psf. `velocity`: canonical m/s, displayed in m/s and ft/s.
   `stress` and `hydraulic_conductivity` stay first in `quantity_kinds`, so a kPa or m/s heading from an AGS file
   is still canonicalized as now (`_kind_of` takes the first match), and a unit error on a velocity column names
   the kind by its dimension's first kind; a test pins both.
7. **Registry names**, checked against `columns.yaml`: `drained_youngs_modulus` ("Drained Young's modulus, E′",
   modulus, derived) and `shear_wave_velocity` ("Shear wave velocity, V_s", velocity; AGS
   `ISTA.ISTA_WVL` where `ISTA_WVTY` is S, to verify against the 4.2 dictionary, for W5's dataset). Neither
   collides. W2 and W5 add `undrained_youngs_modulus`, `small_strain_shear_modulus` and the rest beside them.
8. **The warning's wording** (TODO #41). The no-estimate warning states the range only when some rows are below or
   above it, and names each range input by a `label` in its entry, in the user's terms ("N pa / σ′v0", "(N1)60"),
   not by the term's internal name. When every blank is for soil, refusal or a blank input, it ends after the
   counts. The b1 and b2 entries gain the labels.
9. **Pages 08 and 10**, promoted under the publishing rule, [V] content only (working system over coverage). The
   SPT methods link their functions; the rest list their wave (W2: Eu from triaxial; W3: Eoed; W5: Vs to G0, E0
   and strain reduction, Hardin, HS-small, γ0.7). [U] items not built here (Duncan & Buchignani; Phoon &
   Kulhawy; Darendeli; ASCE 7 site classes; the ±50 % on γ0.7) stay in the sheets, not on the pages. The sheets
   get this step's corrections (the template sentence in 08 §2; Imai & Tonouchi's geology in 10 §5.7, with Wair
   as the source).

### Acceptance criteria
1. **E golden values** (1 tsf = 95.7605 kPa; pa = 100 kPa):

   | Function | `soil=` | N | Expected (kPa) | US |
   |---|---|---|---|---|
   | AASHTO | `clean_fine_to_medium_sands` | (N1)60 20 | 13 406 (140 tsf) | 280.0 ksf |
   | AASHTO | `silts` | (N1)60 10 | 3 830 | 80.0 ksf |
   | AASHTO | `gravels` | (N1)60 10 | 11 491 | 240.0 ksf |
   | AASHTO | any | (N1)60 0 | NaN, "below range" | |
   | K & M | `clean_normally_consolidated_sands` | N60 20 | 20 000 | 417.7 ksf |
   | K & M | `sands_with_fines`, `clean_overconsolidated_sands` | N60 10 | 5 000, 15 000 | |

   The AASHTO 140 tsf is not 6 703 kPa (the ksf misreading).
2. **Vs golden values:**

   | Function | N60 | Expected (m/s) | US (ft/s) |
   |---|---|---|---|
   | Imai & Tonouchi | 10 | 191.3 | 627.7 |
   | Imai & Tonouchi | 30 | 268.9 | 882.3 |
   | Imai & Tonouchi | 0 / 450 | NaN, "below range" / "above range" | |
   | Ohta & Goto | 10 | 183.8 | 603.0 |
   | Ohta & Goto | 2 / 224 | NaN, "below range" / "above range" | |

   Cross-check against the uncorrected forms: 97.0 (10 × 60/67)^0.31 = 191.4 and 85.3 (10 × 60/67)^0.35 = 183.7,
   within 0.1 %.
3. **Input:** each raises without its input column, naming it and what adds it; AASHTO given `spt_n60` only raises.
4. **Soil row:** a missing `soil=` raises listing the rows; an unknown name raises; a mapping by geology unit
   applies each row and raises naming an unmapped unit; the row is on each result row and in attrs.
5. **USCS check:** with `uscs="proposed"` and `soil="clean_fine_to_medium_sands"`, GP gives "not for this soil";
   a blank symbol "soil type unknown"; on a Vs correlation `"proposed"` raises and a list works.
6. **Units:** `drained_youngs_modulus` displays in MPa and ksf, `shear_wave_velocity` in m/s and ft/s; P01 draws
   both with labels; an AGS kPa and an m/s heading are canonicalized as before.
7. **Warning wording:** all blanks for soil → no range sentence; some above range → the range in labels
   ("N pa / σ′v0 ≤ 60"), for b2's K0 entry too.
8. **Config and docstrings:** the drift test covers the new entries, rows and labels.
9. **Docs:** pages 08 and 10 build with `--strict`; the guide's example runs clean; reference entries exist.

### Size
About one sitting, smaller than b2: no plot feature and no judgment kind. Order: (1) the warning's wording;
(2) the kinds and registry columns; (3) the soil row in the framework, with the two E correlations; (4) the two
Vs correlations; (5) pages 08 and 10; (6) guide and close-out.

## Plan
Seven build commits on this branch, each with ruff and pytest green. Numbers in parentheses are the spec's
decisions (D) and acceptance criteria (AC).

### Reused
- `src/hangtu/analysis/correlations/_framework.py`: `entry`, `inputs`, `notes`, `estimate`, `uscs_groups`,
  `soil`, `range_text`, `MADE_BY`; `PA` from `analysis/_overburden.py`.
- `hangtu.units`: `to_display`, `convert`, `parse_unit` (constants converted with pint, as Stroud/Mayne & Kemper).
- Test patterns: `tests/analysis/test_correlations.py` (`FUNCTIONS`, `_drift`, `chain_entry` fixture for a
  made-up entry), `tests/analysis/test_stress_history.py` (golden values, US twins), `tests/units/test_display.py`.
- Docs: `docs/site/parameters/07-*.md` as the page shape; `docs/site/reference/correlations.md`;
  `tests/docs/test_site.py` (reference entries, examples run clean, columns page).

### Build steps

#### 1. `M13: say a correlation's range only for rows outside it` (TODO #41; spec D8, AC 7)
- `config/correlations.yaml`: each `range` key and `terms` entry gains a `label` in the user's terms
  (`spt_n1_60` → "(N1)60", `normalized_n` → "N pa / σ′v0", `effective_vertical_stress` → "σ′v0", …); schema
  comment updated.
- `_framework.py`: `range_text()` writes labels; `estimate()`'s warning adds "Its range is …" only when some
  rows are "below range" or "above range".
- Tests (`test_correlations.py`, `test_stress_history.py`): all-soil blanks → no range sentence; K0 above range →
  "N pa / σ′v0 ≤ 60"; `_drift` also checks each label appears in the docstring (docstrings updated where not).

#### 2. `M13: modulus and velocity kinds, E and Vs registry columns` (spec D6, D7; AC 6)
- `config/defaults.yaml` `quantity_kinds`: `modulus` (canonical kPa; SI MPa, US ksf) and `velocity` (canonical
  m/s; SI m/s, US ft/s), after `stress` and `hydraulic_conductivity` so `_kind_of` keeps its first matches.
  `presets`: `drained_youngs_modulus`, `shear_wave_velocity`.
- `units/aliases.yaml`: `"ft/s"` (and `"ksi"` if absent), checked against the table.
- `columns.yaml`: `drained_youngs_modulus` (label "Drained Young's modulus, E′", modulus, `derived:`),
  `shear_wave_velocity` ("Shear wave velocity, V_s", velocity; ags `ISTA.ISTA_WVL`, to verify) and
  `correlation_soil` (step 3's column).
- Tests (`tests/units/test_display.py`, AGS units tests): 13 406 kPa → 13.41 MPa / 280.0 ksf; 191.31 m/s →
  627.7 ft/s; an AGS `kPa` and `m/s` heading still canonicalize as stress and hydraulic conductivity.

#### 3. `M13: a coefficient by the source's soil row (soil=)` (spec D3, D4; AC 4, 5)
- `config/correlations.yaml` schema: optional `rows: {name: {wording, coefficient, uscs}}`.
- `_framework.py`: `soil_rows(df, item, soil) -> np.ndarray` — required; a row name, or `{geology_unit: row}`
  read from `geology_unit`; errors list the rows / name unmapped or blank units / name the missing column.
  `notes()` takes the per-row soil: with `uscs="proposed"` each row is checked against its own row's groups; an
  entry with neither `uscs` nor `rows` raises on `"proposed"` ("for all soils"). `estimate()` writes
  `correlation_soil` (blank for correlations without rows) and records `soil` in attrs like `uscs`.
- Tests with a made-up entry (as `chain_entry`): missing / unknown `soil=`, mapping and unmapped unit, the USCS
  check per row, "proposed" raising on an entry without groups.

#### 4. `M13: drained Young's modulus from AASHTO and Kulhawy & Mayne` (spec D1–D3, D5; AC 1, 3, 8)
- New `analysis/correlations/_stiffness.py`: `drained_youngs_modulus_aashto_2004` (`spt_n1_60`, C in tsf →
  kPa) and `drained_youngs_modulus_kulhawy_mayne_1990` (`spt_n60`, C × pa), with docstrings to the TEMPLATE
  checklist (equation, rows and their wording, input, range > 0 as hangtu's, strain level, scatter, sources and
  locators). Entries in `correlations.yaml`; exports in `__init__.py`; `reference/correlations.md`.
- `tests/analysis/test_stiffness.py`: AC 1's table, including 140 tsf = 13 406 kPa ≠ 6 703; US twins; AASHTO
  raises given only `spt_n60`; refusal → no estimate. `FUNCTIONS` in `test_correlations.py` extended (drift,
  "no argument chooses the input").

#### 5. `M13: shear wave velocity from Imai & Tonouchi and Ohta & Goto` (spec D1, D4; AC 2, 5, 8)
- `_stiffness.py`: `shear_wave_velocity_imai_tonouchi_1982`, `shear_wave_velocity_ohta_goto_1978` (N60
  forms of Wair et al. 2012, the 67 % assumption and GEC 5's shifted notes stated). Entries, exports, reference.
- Tests: AC 2's table with range ends (0, 447; 2.23, 223) and the cross-check against the uncorrected forms;
  `uscs="proposed"` raises, a list works.

#### 6. `docs: pages 08 and 10` (spec D9)
- `docs/site/parameters/08-elastic-stiffness-soil.md`, `10-small-strain-stiffness.md` from TEMPLATE: [V] only, SPT
  methods link their functions, the rest by wave (W2, W3, W5); nav in `zensical.toml`.
- Sheets 08 and 10 corrected (the template sentence in 08 §2; Imai & Tonouchi's geology in 10 §5.7 from Wair) with
  a pointer to the page. Commit message lists [U] items left in the sheets. Over ~300 lines → one commit per page.

#### 7. `M13: correlations guide on soil rows and strain level; close-out`
- `docs/site/guides/correlations.md` + an example (`docs/site/examples/correlations-stiffness.py`): E by
  `soil={geology_unit: row}` on the example project's sands with `uscs="proposed"`, Vs from both, P01 by
  `correlation_name`, a paragraph on strain level (E from N is not E0 from Vs).
- Close-out: SPEC §12.4 (M13 done); `CLAUDE.md` status (M13 done; next M14); TODO #20 → Done, #40 → "M15", #41
  wording item done; `docs/drafts/analysis.md` §4.2; parameter index rows 08, 10 stage C → part built (SPT: M13
  b3).

### Verification
- Each step: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- Steps 6–7: `uv run python docs/prepare_site.py` and `uv run zensical build --clean --strict`; look at the
  guide's P01 figure (E in MPa/ksf, Vs in m/s/ft/s) myself.
- Final: report AC 1–9 met or not, with evidence.
