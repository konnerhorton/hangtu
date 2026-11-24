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
