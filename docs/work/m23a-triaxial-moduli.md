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
  - `qc_defects.ags` gets the X007 and X008 cases (AC 5–7), and the README table gets their lines.
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
- **Ingest:** nothing changes. `TRET_E50`'s unit (MPa) has the stress dimension, so ingest gives it the first kind
  with that dimension, `stress`, and stores it in kPa. That is also `modulus`'s canonical unit, so the dataset reads
  it without converting it again. `db.SCHEMA_VERSION` stays. The plan's first step confirms this with a test.
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
