# M23 (a): the lab's triaxial moduli in `p.triaxial()`

## Intent
M23 is wave 5's first milestone (SPEC §1.3): soil modulus from the lab tests already read, for sheets 08 (E, ν),
11 (the Hardening Soil set) and 09 (soil dilatancy from curves), with P20. It is four units (`STATUS.md`). This one,
(a), is the data step (stage A for 08 and 11, triaxial route): the moduli the lab reports on each triaxial stage,
read into `p.triaxial()`. (b) derives E50, Eur and Rf from the q–ε₁ readings, which are the main route (see Why).

**Goal:** an engineer gets the lab's secant modulus at 50 % of the peak deviator stress, E50, and the axial strain
where it was measured, ε50, on each `TRET` stage of `p.triaxial()`, from an AGS file or the CSV template, in registry
columns with units. They are kept apart from anything hangtu derives, as the lab's c′ and φ′ are. A QC rule finds an
E50 that doesn't agree with the stage's own q and ε50. In (b) they become the check on hangtu's E50 from the curves,
and in (c) and (d) a source of E where a stage has no readings.

**Why:**
- **Nothing reads a measured soil modulus today.** `drained_youngs_modulus` comes only from SPT correlations
  (M13 b3), and `mohr_coulomb_set()` (M18 f) takes E′ as selected. The oedometer moduli (M19 b) are constrained
  moduli. So P01 has no lab E to set beside the correlations.
- **The values are in standard headings** (checked against python-ags4 1.2.0's dictionaries, 2026-11-24):
  - `TRET_E50`, "Secant modulus at 50 % peak deviator stress", MPa, 2DP;
  - `TRET_EP50`, "Strain at 50 % peak deviator stress", %, 2DP.

  Both were added in AGS 4.1: the 4.0.3 and 4.0.4 dictionaries don't have them. `TRIT` (UU) has neither, and
  neither does `LUCT`. So a total-stress Eu can only come from readings, in (b).
- **Labs often leave them out.** The private real 4.2 sample has 132 `TRET` stages and neither heading. Its lab sent
  the q–ε₁ curves instead (in a user-defined group, read through the readings map since M16). `site.ags` has neither
  heading. The headings are worth reading because they cost little, and a file that has them gives a check on (b). But
  (b) is the route most files will take, and this unit stays small.
- **Sheet 08's and 11's pitfalls that belong to the data:**
  - an E50 from a CU stage is undrained (Eu50), and one from a CD stage is drained (E′50). Sheet 11 §7 says not to use
    one as the other without converting it. `test_type` already says which applies on each row.
  - E50 is at the stage's σ′3 and depends on it (sheet 11 §5.1), so it has to come back with the consolidation
    stress. For an anisotropically consolidated stage (`CAU`, `CAD`), σ′3 is the radial stress `TRET_CRP`, which
    `p.triaxial()` doesn't read today.
  - by its definition, E50 = (q_peak / 2) / ε50 (sheet 11 §5.2). A value that breaks this is a unit slip (MPa against
    kPa, % against a fraction) or a typing error.

  Each becomes a column, a QC finding, or a blank that is counted, never dropped.

**Scope:**
- Two new columns on `p.triaxial()` from `TRET_E50` and `TRET_EP50`, blank on `TRIT` rows. They are the lab's
  values, named as such (as `reported_effective_friction_angle` is), and a CSV column of the same name.
- 🟡 `TRET_CVP` and `TRET_CRP` (effective vertical and radial stress at the end of consolidation), so (d) has σ′3 for
  anisotropic stages (see Open).
- A level 1 QC rule: E50 against the stage's q / 2 ÷ ε50, where the lab's failure criterion makes q at failure the
  peak (see Open).
- The CSV template (`triaxial.csv`) and the SI/US twin test files gain the columns. `site.ags` gains values for a few
  stages through `_make_examples.py`, with the CSVs written from it.
- `docs/data/datasets.md` §6.10 and `docs/data/qc.md` describe the columns and the rule.

**SPEC and docs touched:**
- SPEC §10.2–10.3 (new dataset columns, names checked against the whole registry) and §2.6 (the CSV template). SPEC
  §9 only through `docs/data/qc.md`.
- 🟡 Ingest: `TRET_E50` is a stress unit (MPa), and the `modulus` kind exists, so no new quantity kind is expected and
  `db.SCHEMA_VERSION` stays. The spec step checks which kind ingest gives the heading.
- The parameter index: sheet 08 A and sheet 11 A note the triaxial route. Sheet 08 is already on the site, and its
  page's "Tests" section gets the dataset's name. Sheet 11 isn't promoted here; (b) promotes it with the derivations.

### Out of scope
- **Every derivation:** E50, Eur and Rf from readings, Eu from s_u, the drained↔undrained conversion and ψ (M23 b);
  selecting E′ and ν′, P20 (M23 c); the HS set (M23 d).
- **`TRET_CU`**, s_u at the consolidation stress: the SHANSEP input, read in M20 (b).
- **Rock moduli** (`RUCS_ESEC`, `RUCS_ETAN` and the Poisson's ratios): M21 (a).
- **Turning the lab's E50 into a modulus column** (`drained_youngs_modulus` or an undrained one). That is a
  derivation with a drainage call, so it goes in (b).
- **Stage D for sheet 08** (`representative()`, `select()` of a lab E): M23 (c).

### Decisions (intent review, 2026-11-24)
1. **One column for E50, read with `test_type`.** It is named `reported_` + a secant modulus name, checked against
   the registry in the spec step. This matches how `p.triaxial()` keeps CU and CD stages in one frame, and (b) makes
   the drainage call when it turns the value into E′ or Eu. Rejected: separate `reported_drained_…` and
   `reported_undrained_…` columns. They would split the rows on a mapping from `TREG_TYPE`, which the dataset has
   avoided so far (decision 3 of M11 a).
2. **`TRET_CVP` and `TRET_CRP` are read here.** (d) needs σ′3 for each stage, and this is the unit that reads `TRET`
   headings. Without them, an anisotropic stage's `effective_consolidation_stress` (`TRET_CONP`, "effective stress
   at end of consolidation") is ambiguous: it could be the vertical stress, the radial stress or the mean. The spec
   step decides whether `CONP` stays the σ′3 of an isotropic stage only.
3. **The QC check runs only where q at failure is the peak.** `TRET_E50` is defined at 50 % of the *peak* deviator
   stress, and `TRET_DEVF` is q at the lab's failure criterion (`TREG_FCR`). The two are the same only when the
   criterion is the maximum deviator stress. Other stages are skipped and not counted as findings. The tolerance
   comes from the headings' rounding (2DP in MPa and %), worked out in the spec step.
4. **Full loop, kept short.** The unit is a few columns, one QC rule and fixtures, but the names and the QC rule are
   decisions. So it gets a short `## Spec` and a short `## Plan`.

### Example and test data (intent review, 2026-11-24)
- **Every `TRET` stage in `site.ags` has readings** in `triaxial_readings.csv` (12 CD, 3 CDM, 3 CU, all "Maximum
  deviator stress"). So the lab's E50 and ε50 for the example stages are worked out from those curves, at
  q = q_f / 2 by linear interpolation and rounded to the headings' 2DP, as a lab would report them. Values invented
  apart from the curves would disagree with (b)'s E50 for no reason, and make the cross-check in (b) meaningless.
- **Only some stages get them,** so the example also shows a file with blanks, as real files have.
- **`site.ags` has no anisotropic stage.** `TRET_CVP` = `TRET_CRP` = `TRET_CONP` on the isotropic stages, and one
  CAU or CAD test is added only if the spec step decides `CONP`'s meaning needs an example.
- **The QC rule's defects case** (an E50 in kPa, or ε50 as a fraction) goes in the test fixtures, not in
  `site.ags`.
- **Magnitudes are checked against the sheets' ranges:** E′ for sands and stiff clays (sheet 08 §3, [2] [V]), and
  E50 of 11–47 MPa at σ′3 near 100 kPa for quartz sands (sheet 11 §3, [3] [V]).

## Spec
The rules live in topic docs. This section lists what changes in each, the decisions, the sources and the
acceptance criteria.

### Changes
- **`src/hangtu/columns.yaml`:** four columns, in the `triaxial` template after the column named in brackets:
  | Column | Heading | Quantity | Label | After |
  |---|---|---|---|---|
  | `effective_vertical_consolidation_stress` | `TRET_CVP` | stress | Effective vertical consolidation stress, σ′vc | `effective_consolidation_stress` |
  | `effective_radial_consolidation_stress` | `TRET_CRP` | stress | Effective radial consolidation stress, σ′rc | `effective_vertical_consolidation_stress` |
  | `reported_axial_strain_at_50_percent_peak` | `TRET_EP50` | percent | Reported axial strain at 50 % of peak deviator stress, ε50 | `reported_effective_cohesion` |
  | `reported_secant_modulus_at_50_percent_peak` | `TRET_E50` | modulus | Reported secant modulus at 50 % of peak deviator stress, E50 | `reported_axial_strain_at_50_percent_peak` |

  The descriptions say that E50 is undrained (Eu50) on an undrained stage and drained (E′50) on a drained one, as
  `test_type` says, and that it is the lab's value, which hangtu doesn't use in place of its own.
- **`docs/data/datasets.md` §6.10:** the four rows in the column table (blank on `TRIT` rows). Three notes:
  - **E50 is read with `test_type`** (decision 1 of the intent review).
  - **`effective_consolidation_stress` is `TRET_CONP` as written.** On an anisotropically consolidated stage
    (`CAUC`, `CADC`, `CAUE`, `CADE`), the dictionary doesn't say whether it is the vertical, the radial or a mean
    stress. The two new columns say which, so read them there.
  - **Like the lab's c′ and φ′,** the lab's E50 and ε50 are carried beside the values hangtu derives, never in their
    place.
- **`docs/data/qc.md` §4.12:** rules X007 and X008 (below), with a note to X006: it reads `TRET_CONP` as the radial
  stress, which cell − back gives, so a lab that writes the vertical stress there on an anisotropic stage raises
  X006. Its message already gives both values. X006 is unchanged.
- **`src/hangtu/qc/rules.yaml`:** the two rules, with no new threshold. Both rules' tolerances come from
  the values' rounding, as E003's do.
- **`tests/data/ags/_make_files.py`:**
  - In `site_si.ags` and `site_us.ags`, the four headings are added at the end of `TRET` (`TRET_CVP` and `TRET_CRP`
    0DP kPa, `TRET_EP50` 2DP %, `TRET_E50` 2DP MPa; ksf in the US twin, at 10SF). New columns move no line.
  - BH1-U3 specimen 1 (`CU`, q_f 180 kPa) and BH2-U2 specimen 3 stage 1 (`CDM`, q_f 300 kPa) get the lab's values
    (AC 1). The other stages are left blank.
  - `site_v404.ags` doesn't get them: all four headings are new in 4.1. The README's list of 4.1 headings gains them.
  - `qc_defects.ags` gets one seeded X007 and one X008 case, and the README table gets their lines. AC 5–8's
    cases are built in `tests/qc/test_triaxial.py`. (Corrected in build step 3; see the build notes.)
- **`tests/data/_make_examples.py`:** `site.ags` adds `TRET_CVP`, `TRET_CRP` (0DP psf), `TRET_EP50` (2DP %) and
  `TRET_E50` (1DP ksf) to `TRET`, for the three CU stages on B-2-U2 and the CD stages on B-1-U5 and B-2-U4: nine
  stages. The other six (B-4-U4, B-6-U4 and the CDM test) stay blank. ε50 is read from each stage's own curve in
  `triaxial_readings.csv`: the strain where q first reaches q_f / 2, by linear interpolation between readings. E50 is
  (q_f / 2) / ε50 from the unrounded ε50, then both are rounded as written. On these isotropic stages,
  `TRET_CVP` = `TRET_CRP` = `TRET_CONP`. `triaxial.csv` is written from it.
- **`docs/site/parameters/08-elastic-stiffness-soil.md`:**
  - In "Tests", the triaxial row names `TRET_E50` and `TRET_EP50` and says `p.triaxial()` returns them.
  - The "Methods" table's last column cites internal waves (W2, W3, W5), which published text mustn't. The oedometer
    row links `ht.analysis.oedometer_increments()`, which is built. The triaxial and Vs rows say "planned".
- **`docs/plots/drafts/P19-pmt-hardening-soil.md`:** its proposed `secant_modulus_50` becomes
  `secant_modulus_at_50_percent_peak`, the name (b) will give hangtu's own E50 (decision 2).
- **Ingest:** nothing changes. A standard heading is stored in its dictionary unit, so `TRET_E50` is kept in MPa
  (as `RUCS_ESEC`'s GPa is), with no quantity kind: ingest matches a kind by dimension only for time. `p.triaxial()`
  converts it from the stored unit (`meta_heading`) to `modulus`'s kPa. `db.SCHEMA_VERSION` stays. (Corrected in
  build step 1: this bullet first said ingest stored it in kPa as a stress.)
- **The parameter index:** 08 A and 11 A note `p.triaxial()`'s E50 at close-out.

### Decisions
1. **The checks are two rules, X007 and X008,** both on the `TRET` stages whose failure criterion makes q_f the
   peak:
   | ID | Rule | Severity | Thresholds |
   |---|---|---|---|
   | X007 | `TRET_E50` differs from (`TRET_DEVF` / 2) / `TRET_EP50` | warning | none: the values' own rounding |
   | X008 | `TRET_EP50` at or above `TRET_STRN` | warning | none |

   - **X007** compares intervals, as E003 does. Each value is taken ± half a unit in the last place of its heading's
     `TYPE` (xDP or xSF), from the raw text. The recomputed interval, from q_f's and ε50's ends, is converted to
     `TRET_E50`'s unit. A finding means the two intervals don't overlap. Its message gives both values and says the
     usual causes: a unit slip (kPa written as MPa, or ε50 as a fraction rather than %), or values copied from
     different stages.
   - **X008:** the strain at half the peak can't be at or past the strain at the peak. It catches an ε50 given as a
     fraction in a file with no `TRET_E50`, which X007 can't. No tolerance: the two are different headings of one
     reading, and equal values are already wrong.
   - **Both skip** a stage where a value they need is blank or flagged, an extension type (q's sign, §6.10), q_f of 0
     or less (X003's), and a stage whose criterion isn't the peak (decision 3 of the intent review). Skipped stages
     aren't findings.
   - **Warnings, not errors:** a lab could report E50 by a definition other than the dictionary's (a tangent at
     50 %), and the engineer reads the lab's sheet before accepting the finding.
2. **Names.** The lab's value is `reported_` + the name hangtu's own E50 will take in (b), as
   `reported_effective_friction_angle` goes with `effective_friction_angle`. `secant_modulus_at_50_percent_peak`
   follows `time_to_50_percent_consolidation`: "50 percent" spelled out, and "secant" because the modulus is a secant.
   It isn't named `youngs_modulus` because `drained_youngs_modulus` is a selected or correlated working-strain E′,
   and E50 becomes one only after (b)'s drainage call. "Peak" stands for "peak deviator stress", which the label and
   description write in full. The shorter alternative, `reported_secant_modulus_50`, was rejected: "50" alone
   could be a stress level or a strain. Checked against the whole registry and every spec and draft (2026-11-24):
   none of the four names is taken. The only near one is P19's proposal, which changes to match.
3. **The radial and vertical stresses are `effective_…_consolidation_stress`,** beside `effective_consolidation_stress`
   (`TRET_CONP`), so the three sort together. The dictionary's "pressure" becomes "stress", as `TRET_CONP`'s does.
4. **The peak criterion** is `TREG_FCR`, trimmed and with case ignored, equal to "maximum deviator stress" (the
   dictionary's example, and `site.ags`'s) or "peak deviator stress". A blank `TREG_FCR` is skipped, since q_f's
   meaning is unknown. Many files leave it blank, so X007 won't run on them. A rule that guessed "peak" for a blank
   would raise findings on files that are right.
5. **`p.triaxial()` raises no new warning.** A blank E50 is the usual case (the intent's evidence), and the columns
   carry the lab's values as written.

### Sources
- **AGS 4.1 and 4.2 dictionaries** (python-ags4 1.2.0's `Standard_dictionary_v4_1.ags`, `_v4_2.ags`): `TRET_E50`
  "Secant modulus at 50 % peak deviator stress", MPa, 2DP; `TRET_EP50` "Strain at 50 % peak deviator stress", %, 2DP;
  `TRET_CVP` and `TRET_CRP` "Effective vertical/radial pressure at end of consolidation", kPa, 0DP. None of the four is
  in 4.0.3 or 4.0.4. Read 2026-11-24.
- **E50 as the secant from the origin to q = q_f / 2:** PLAXIS 2D 2025.1 Material Models Manual, Ch. 6, Eqs. 6–3,
  6–4 and Fig. 6–5 (sheet 11 [1], verified there). X007's E50 = (q_f / 2) / ε50 is that definition, with q_f the peak
  under decision 4.

### Acceptance criteria
Golden values are hand-calculated below. Tolerances are exact for values read through, and 1e-9 relative for the
SI/US twins, as for the other twin tests.

1. **Read through, SI:** in `p.triaxial()` from `site_si.ags`:
   - BH1-U3 specimen 1 (`CU`) has `reported_axial_strain_at_50_percent_peak` 0.60 %,
     `reported_secant_modulus_at_50_percent_peak` 15.00 MPa (15 000 kPa stored), and both consolidation stresses
     100 kPa. Hand check: (180 / 2) / 0.0060 = 15 000 kPa.
   - BH2-U2 specimen 3 stage 1 (`CDM`) has 0.25 % and 60.00 MPa: (300 / 2) / 0.0025 = 60 000 kPa.
   - Every other stage, and every `TRIT` row, has the four columns blank. The columns are in the template's order.
2. **Twins:** `site_us.ags` gives the same values in SI to 1e-9 relative, and in US units shows E50 as
   15 000 kPa / 47.880 26 kPa/ksf = 313.28 ksf (to 2DP) for BH1-U3 specimen 1.
3. **4.0.4:** `site_v404.ags` gives the four columns, blank on every row, with no error or warning.
4. **Anisotropic stage:** a `CAUC` stage built in the test with `TRET_CONP` 100, `TRET_CVP` 200 and `TRET_CRP`
   100 kPa returns the three as written. Nothing is derived from them.
5. **X007, the dictionary's example:** `TRET_DEVF` 360 kPa (0DP), `TRET_EP50` 3.22 % (2DP), `TRET_E50` 75.50 MPa
   (2DP), criterion "Maximum deviator stress". Recomputed: lowest (359.5 / 2) / 0.03225 = 5 573.6 kPa, highest
   (360.5 / 2) / 0.03215 = 5 606.5 kPa, so [5.574, 5.607] MPa. Reported [75.495, 75.505] MPa: they don't overlap,
   so there is one X007 finding, and the message gives 75.50 and 5.59 MPa. The dictionary's values are illustrative,
   not one stage, as E005's are.
6. **X007, at the edges:** q_f 180 kPa (0DP), ε50 0.60 % (2DP). Recomputed: lowest (179.5 / 2) / 0.00605 = 14 834.7
   kPa, highest (180.5 / 2) / 0.00595 = 15 168.1 kPa.
   - `TRET_E50` 15.16 MPa → [15.155, 15.165], inside: no finding.
   - 15.20 → [15.195, 15.205], above 15.168: one finding.
   - 15000 (kPa written as MPa): one finding.
   - ε50 written 0.006 (a fraction) with E50 15.00: the recomputed E50 is about 1 500 MPa, so one finding.
7. **X008:** `TRET_EP50` 9.00 % with `TRET_STRN` 8.5 %: one finding. 8.50 with 8.5: one finding (equal). 0.006 (a
   fraction) with E50 blank: no X007 (E50 blank) and no X008 (below the strain at failure). This is a gap the spec
   accepts, since nothing tells a small ε50 from a fraction without E50.
8. **Skips:** none of these raises X007 or X008:
   - the same values as AC 5 under criterion "Maximum stress ratio";
   - the same under a blank criterion;
   - a `CIDE` extension stage;
   - `TRET_E50` given and `TRET_EP50` blank;
   - a flagged `TRET_DEVF`.

   `"  MAXIMUM deviator STRESS "` and "Peak deviator stress" both count as the peak.
9. **Clean files:** `site_si.ags`, `site_us.ags`, `site_v404.ags` and the example `site.ags` stay QC-clean: no X007,
   X008 or other new finding. On `site.ags`, the nine stages' E50 and ε50 agree with their curves by construction.
   Hand check: B-1-U5 specimen 1's ε50 0.44 % and E50 about 22.5 MPa (470 ksf) at q_f 4 123 psf: 2 061.5 psf /
   0.0044 = 468.5 ksf, consistent within ε50's rounding.
10. **Published text:** the 08 site page has no W2, W3 or W5, the new columns' descriptions cite no internal file,
    and `tests/docs/test_site.py` and `tests/test_errors.py` pass.

## Plan
Draft, 2026-11-24. Five commits, each green: the tests it touches, then the CI command with `-n 2`. All on Opus, in
one session: the unit is small, and no run of Sonnet-suited work is large enough to be worth a model boundary. A
step past about 300 changed lines without test data splits as noted. Reused, not rebuilt:
- **Dataset:** `Build.numbers()`, `Build.texts()`, the `GROUPS` and `STAGE_NUMBERS` maps (`datasets/_triaxial.py`);
  the conversion of a heading stored in its dictionary unit to the column's kind, as `p.shear_box()` does for its
  rates (`datasets/_shear_box.py`, `RATES`).
- **QC:** `_types()`, `_stage()`, `_STAGES` (`qc/_triaxial.py`); `_unflagged()`, `_value()`, `SLACK`
  (`qc/_tests.py`); E003's interval comparison, `_rounding()`, `_half_place()` and its unit factor
  (`qc/_oedometer.py`); `data.text_at()`, `data.heading_info()`.
- **Test data:** `group()`, `without()`, `to_us()`, `US_OVERRIDE` (`tests/data/ags/_make_files.py`); the `_triaxial`
  builder in `tests/qc/test_triaxial.py`; `triaxial_curves()` and `triaxial_stages()` (`tests/data/_make_examples.py`).

**Settled before the build** (each corrects the Spec's text in the step named):
- **Ingest keeps `TRET_E50` in MPa** (checked in code, 2026-11-24). The Spec's Ingest bullet is wrong: a standard
  heading is converted to its *dictionary* unit, not to a kind's canonical unit, and `_quantity()` (`ags/_units.py`)
  matches a kind by dimension only for time ("a match by dimension would make MPa headings stresses"). So the table
  holds MPa, with `meta_heading.quantity` blank, as `RUCS_ESEC`'s GPa already is
  (`tests/ags/test_ingest_acceptance.py`). `Build.numbers()` returns the stored values unconverted, so `p.triaxial()` must convert `TRET_E50` from the
  table's `attrs["units"]` to `modulus`'s kPa, as `p.shear_box()` does `RATES`; reading it as a stage number would
  give 15 kPa for AC 1's 15 MPa. Nothing in ingest changes and `db.SCHEMA_VERSION` stays, as the Spec says. Step 1
  corrects the bullet.
- 🟡 **Column order against M17 (c)'s test.** `test_m17c_template_and_dataset_have_the_rock_columns`
  (`tests/datasets/test_triaxial.py`, about line 277) asserts `reported_intact_compressive_strength` comes right after
  `reported_effective_cohesion`, which the Spec's "after `reported_effective_cohesion`" breaks. Step 1 keeps the
  Spec's order (the soil's reported values together, then the rock's) and changes that assertion to the new
  neighbor, `reported_secant_modulus_at_50_percent_peak`. The alternative, the two after
  `reported_intact_hoek_brown_constant`, would put the lab's E50 among the rock columns.
- 🟡 **`qc_defects.ags` holds one case per rule; the edge cases are built in the test.** The Spec puts AC 5–7 in
  `qc_defects.ags`. AC 6 and 7 are seven stages, each a new specimen with its own `TREG` row, and every row added
  there moves the lines of each later group's cases in `test_qc_acceptance.py`. qc.md §5 AC 1 needs one seeded case
  per rule, so the file gets AC 5's stage (X007) and AC 7's first (X008); AC 6, the rest of AC 7 and AC 8 are built
  in `tests/qc/test_triaxial.py`, as X006's tolerance cases are. Step 3 corrects the Spec's bullet.
- **X007's rounding for an `xSF` heading** is half a unit in the last place the text writes (`_half_place()`), since
  a significant-figure TYPE's last place depends on the value; `xDP` comes from the TYPE (`_rounding()`), and a
  heading with no usable TYPE falls back to the text, as for `xSF`. On `site_us.ags`'s 10SF values the interval is
  then tiny, and the recomputed side (ε50 at 2DP %) carries the width.
- **The US twin's E50 is in ksf through `US_OVERRIDE`,** not a new `"MPa"` entry in `US`, so no other MPa heading
  changes how its twin is written. `TRET_CVP` and `TRET_CRP` join `TRET_US` and are written in psf, as `TRET_CONP`;
  the Spec's "ksf in the US twin" is read as E50's unit. `TRET_EP50` stays in %.

### 1. `M23: read the lab's E50 and consolidation stresses in p.triaxial()` (Opus)
- `src/hangtu/columns.yaml`: the four columns of the Spec's table, with descriptions that say the lab's E50 is Eu50
  on an undrained stage and E′50 on a drained one (as `test_type` says), and is carried beside hangtu's values,
  never in their place; no internal file cited. The `triaxial` template in the Spec's order. `tests/test_registry.py`
  green.
- `src/hangtu/datasets/_triaxial.py`: `TRIAXIAL_COLUMNS` in the template's order; `TRET_CVP` and `TRET_CRP` read as
  stage numbers of `TRET` only (a `TRET`-only map beside `STAGE_NUMBERS`, since `TRIT` has neither: blank on `TRIT`
  rows); `TRET_EP50` likewise (percent, stored as written); `TRET_E50` converted from its stored unit to kPa, as
  above. No new warning (Spec decision 5).
- `src/hangtu/project.py`: `Project.triaxial()`'s docstring names the four columns, E50's drainage read from
  `test_type`, and that `effective_consolidation_stress` is `TRET_CONP` as written.
- `tests/data/ags/_make_files.py`: the four headings at the end of `TRET_HEADINGS` and `tret_row()` gains
  `cvp`, `crp`, `ep50`, `e50` (default None); BH1-U3 specimen 1 gets 100, 100, 0.60, 15.00 and BH2-U2 specimen 3
  stage 1 gets 100, 100, 0.25, 60.00. `TRET_US` gains `TRET_CVP`, `TRET_CRP`, `TRET_E50`; `US_OVERRIDE` gains
  `TRET_E50: ("ksf", 47.880 26e-3 MPa)` from the file's existing `LBF` and `SQUARE_FOOT`. `site_v404.ags`'s
  `without(TRET, …)` drops the four. `qc_defects.ags`'s own `TRET` is unchanged here. Regenerate and check with
  `git diff --stat tests/data/ags` that only `site_si.ags`, `site_us.ags` and nothing else changed, and in those only
  `TRET`'s heading, unit and type lines and its rows.
- `tests/data/ags/README.md`: the 4.1 headings list gains the four; `site_si.ags`'s description names the two stages.
- `docs/data/datasets.md` §6.10: the four rows and the Spec's three notes.
- This file's Spec: the Ingest bullet corrected as settled above.
- Tests: `tests/datasets/test_triaxial.py`: AC 1 (both stages' four values, every other row blank, `TRIT` rows blank,
  the columns in the template's order; the M17 (c) assertion moved as settled above); the ingest check (`TRET_E50`
  stored in MPa with status `converted`, read as 15 000 kPa); AC 3 (`site_v404.ags`: four blank columns, no warning);
  AC 4 (a `CAUC` stage built in the test with `TRET_CONP` 100, `TRET_CVP` 200, `TRET_CRP` 100, returned as written).
  The twin test (`tests/datasets/test_datasets_acceptance.py` or wherever `p.triaxial()`'s twins are compared): AC 2,
  the SI values to 1e-9 relative and 313.28 ksf (2DP) in US display. `tests/test_examples.py`: the unit lists
  (`TRIAXIAL_STRESSES` and a modulus list) gain the new columns, blank on the example until step 4.
  `tests/datasets/test_triaxial.py::test_10_template_frame_gives_the_dataset_stresses` covers the CSV template.
  Then the whole suite: every triaxial and readings test reads the template's order.

### 2. `qc: share E003's rounding helpers with the triaxial rules` (Opus)
- `src/hangtu/qc/_oedometer.py` → `src/hangtu/qc/_text.py`: `_rounding()` and `_half_place()` move, renamed without
  the underscore where `_text`'s other public helpers have none; E003 imports them. No behavior change.
- Tests: `tests/qc/test_oedometer.py` unchanged and green. Its own commit, since it is a refactor (process.md, "Git
  and commits").

### 3. `M23: add QC rules X007 and X008 for the lab's E50` (Opus)
- `src/hangtu/qc/_triaxial.py`: a `_criteria(data)` beside `_types()` giving each `TRET` row's `TREG_FCR`, and
  `_peak(text)` (trimmed, case ignored, "maximum deviator stress" or "peak deviator stress"; blank is not the peak).
  `X007` and `X008` as the Spec's decision 1: both on `TRET` only, skipping a blank or flagged value they need, an
  `EXTENSION` type, q_f at or below 0 (X003's), and a non-peak or blank criterion; `records_checked` counts the stages
  compared. X007 from the raw text (`data.text_at()`): q_f's and ε50's intervals give the recomputed E50 in
  `TRET_DEVF`'s file unit per fraction, converted to `TRET_E50`'s file unit by a `ureg` factor as E003's; a finding
  where the intervals don't overlap (with `SLACK`). The message: both headings' values and units, where the stage is
  (`_stage()`), the recomputed value from the midpoints at `TRET_E50`'s decimals, and the usual causes (a unit slip,
  kPa as MPa or ε50 as a fraction, or values from different stages). X008: `TRET_EP50` ≥ `TRET_STRN` − `SLACK`. The
  module docstring names X007 and X008.
- `src/hangtu/qc/rules.yaml`: `X007` and `X008`, warnings, no thresholds, with a comment that X007's bounds are the
  values' own rounding (as E003's).
- `docs/data/qc.md` §4.12: the two rows, their skips and the peak criterion; the note to X006 from the Spec.
- `tests/data/ags/_make_files.py`: `qc_defects.ags`'s `TRET` gains `TRET_EP50` and `TRET_E50`, with AC 5's stage
  (`TRET_DEVF` 360, 3.22, 75.50) and AC 7's (`TRET_EP50` 9.00, `TRET_STRN` 8.5) on two new specimens and `TREG` rows
  ("Maximum deviator stress"). The lines that move are updated in `tests/qc/test_qc_acceptance.py`,
  `tests/qc/test_triaxial.py` and the README; `git diff` of `qc_defects.ags` shows only the new rows, columns and
  shifted lines.
- `tests/data/ags/README.md`: the X007 and X008 line in the defects table.
- This file's Spec: the `qc_defects.ags` bullet corrected as settled above.
- Tests: `tests/qc/test_triaxial.py`: AC 5 (one X007 at its line; the message has 75.50 and 5.59 MPa); AC 6's four
  cases (none, one, one, one) and AC 7's three (one, one, none and no X007), built with the `_triaxial` builder
  extended for the two headings and `TREG_FCR`; AC 8's five skips, and the two spellings that count as the peak;
  severities `warning`; `test_records_checked` gains X007 and X008. `tests/qc/test_qc_acceptance.py`: the two seeded
  lines, and AC 9's three test files with no X007 or X008 (as the other clean-file checks). `tests/test_errors.py`.

### 4. `M23: give site.ags's triaxial stages the lab's E50 from their curves` (Opus)
- `tests/data/_make_examples.py`: `tret()` splits so the curves don't read their own output: `tret_rows()` (today's
  rows, which `triaxial_stages()` reads) and `tret()`, which adds `TRET_CVP`, `TRET_CRP` (0DP psf, = `TRET_CONP`),
  `TRET_EP50` (2DP %) and `TRET_E50` (1DP ksf) for the nine stages of the Spec. ε50 is the strain where each stage's
  q curve from `triaxial_curves()` first reaches q_f / 2, linearly interpolated; E50 = (q_f / 2) / ε50 from the
  unrounded ε50, then both rounded. The curves come from a fresh `random.Random(2031)` in the order `curve_groups()`
  draws them, so they are the curves in the file; no draw is added to any other stream. A comment names the method
  and that the values aren't hand-calculated.
- Regenerate: `site.ags` changes only in `TRET`'s heading, unit and type lines and the nine rows' new cells;
  `triaxial_readings.csv` is unchanged; `triaxial.csv` and `rock_triaxial.csv` gain the four columns (blank in the
  rock file). Check with `git diff --stat`.
- `src/hangtu/examples/__init__.py`: the `triaxial.csv` description says which stages carry the lab's E50.
- Tests: `tests/test_examples.py`: AC 9's hand check (B-1-U5 specimen 1's ε50 0.44 % and E50 about 470 ksf at q_f
  4 123 psf, within ε50's rounding), the nine stages filled and six blank; the example stays QC-clean (no X007, X008).
  If the curve gives a different ε50 from the Spec's 0.44 %, stop: the Spec's hand check was read from the curve, so
  one of them is wrong.

### 5. `M23: close out (a): sheet 08's page, the index and the changelog` (Opus)
- `docs/site/parameters/08-elastic-stiffness-soil.md`: "Tests" names `TRET_E50`, `TRET_EP50` and `p.triaxial()`;
  the "Methods" table's last column drops W2, W3 and W5: the oedometer row links
  `ht.analysis.oedometer_increments()`, the triaxial and Vs rows say "planned".
- `docs/plots/drafts/P19-pmt-hardening-soil.md`: `secant_modulus_50` becomes `secant_modulus_at_50_percent_peak`.
- `docs/drafts/parameters/README.md`: 08 A and 11 A note `p.triaxial()`'s lab E50.
- `docs/prepare_site.py` and `zensical build --clean --strict`, for any example page that prints triaxial columns.
- Close-out: `STATUS.md` (M23 (a) done, (b) next); `CHANGELOG.md` Unreleased (the four columns on `p.triaxial()` and
  the template, QC rules X007 and X008); SPEC §10.2–10.3 and §2.6 read and changed only where they list the
  dataset's or template's columns; `docs/TODO.md` only if the build deferred something with a trigger.
- Tests: AC 10 (`tests/docs/test_site.py`, `tests/test_errors.py`); the CI command.

### Notes from the build
- **Step 1, the stored unit:** `Build.data.table()` (`qc/_data.Data.table`) carries no `attrs["units"]`; only
  `Project.table()` sets them. So `p.triaxial()` reads `TRET_E50`'s stored unit from `meta_heading`
  (`build.data.headings`). `p.shear_box()`'s `RATES` conversion reads the empty `attrs` and so never converts; it is
  harmless today because ingest already stores `SHBT_DISP` and `SHBT_DISR` in the dictionary's mm/min, but it would
  miss a stored unit other than the column's. Not fixed here.
- **Step 1, SI display:** `modulus` displays in MPa in SI (ksf in US), so AC 1's 15.00 MPa is the SI display value;
  the dataset holds 15 000 kPa.
- **Step 1, `joins.ags`** shares `TRET_HEADINGS`, so it drops the four headings with `without()` to stay unchanged.
  Both twins' `UNIT` groups gain a line (`MPa`; `ksf` in the US twin), after every cited line.
- **Step 3, the seeded cases** go on BH4-U1's two existing stages (the X005 case, otherwise clean), not on two new
  specimens: new `TREG` and `TRET` rows would have moved every later line of `qc_defects.ags`, which about fifteen
  test files cite. X007 on stage 1 (`TRET_EP50` 3.22 %, `TRET_E50` 75.50 MPa, q_f 150 kPa: 2.33 MPa recomputed), X008
  on stage 2 (`TRET_EP50` 9.00 % against `TRET_STRN` 5.0 %). AC 5's dictionary values are built in the test.
- **Step 3, X008's purpose:** the Spec's decision 1 says X008 "catches an ε50 given as a fraction in a file with no
  `TRET_E50`", but a fraction is smaller than the percentage and can't reach the strain at failure; AC 7's third case
  (0.006, no X008) is right. X008 catches a strain at failure written as a fraction, the two swapped, or values from
  different stages, and its message and `qc.md` say so.
- **Step 4, the count:** `site.ags` has 18 `TRET` stages (3 CU, 3 CDM, 12 CD), so the stages left blank (B-4-U4,
  B-6-U4 and the CDM test) are nine, not the Spec's "other six". ε50 for B-1-U5 specimen 1 is 0.44 % and E50
  470.0 ksf from its curve, as AC 9's hand check said. The CD moduli run from 397 ksf (19 MPa) at σ′3 1000 psf to
  2079 ksf (100 MPa) at 4000 psf: the hyperbolic curves are stiff at high σ′3, above sheet 11's 11–47 MPa near
  100 kPa scaled up by stress. They are the curves' values by construction and change only with the curves.
