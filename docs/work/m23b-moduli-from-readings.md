# M23 (b): moduli and dilatancy from the triaxial readings

## Intent
M23 is wave 5's first milestone (SPEC §1.3), in four units (`STATUS.md`). (a) read the lab's E50 and ε50 into
`p.triaxial()`. This unit, (b), is stage B for sheets 08, 11 and 09 on the triaxial route: hangtu's own E50, Rf and ψ
from each stage's readings during shearing, which is the route most files will take. (c) selects E′ and ν′ and draws
P20; (d) builds the Hardening Soil set.

**Goal:** an engineer passes triaxial readings (`p.triaxial_readings()` or the `triaxial_readings` CSV template) to one
analysis and gets one row per stage with E50, the axial strain where it was read (ε50), the failure ratio Rf, and, on a
drained stage with volume change, the dilatancy angle ψ. Each value says how it was read, sits beside the lab's E50 from
(a) where the stage has one, and a stage that can't give a value gets a reason, not a number.

**Why:**
- **E50 from the curves is the main route.** Labs often leave `TRET_E50` out: the private real sample's 132 `TRET`
  stages have none, but its lab sent the curves (99 q–ε₁ stages, and εv for the drained ones, counted 2026-11-24).
  `site.ags` has curves for all 18 `TRET` stages, and (a) gave nine of them the lab's E50 from those curves, so the two
  routes can be checked against each other on the example.
- **The HS set needs E50 and Rf per stage, at the stage's σ′3** (sheet 11 §5.1–5.2), and (d) fits E50ref and m across
  σ′3. (a) gave each stage σ′3, including `effective_radial_consolidation_stress` for anisotropic stages.
- **ψ is published today only by rule.** `mohr_coulomb_set()` gives ψ from Bolton's relation or ψ = 0 (sheet 09's
  site page, "hangtu doesn't read ψ from test curves yet"). The readings already carry `volumetric_strain`, and
  `triaxial_failure_from_readings()` already splits each stage into its loading part and unload tail. 15 of the
  example's stages and the real sample's drained stages have εv.
- **Each value is a reading of one test by a stated rule** (SPEC §4, "three kinds of choice"): E50 by its definition,
  the secant from the origin to q_f / 2 (PLAXIS Material Models Manual, Eqs. 6–3, 6–4, Fig. 6–5, verified for (a)); Rf
  = q_f / q_a from the hyperbola fitted to the curve (same source, Eq. 6–6 [V]); ψ from the rate of volume change at
  peak (sheet 09 §5.1, [6] Eq. 15 [V]). So the rule is stated and documented, not a judgment or a default.

**Constraints:**
- **q_f is the failure reading `triaxial_failure_from_readings()` picks**, by the caller's `failure_criterion=` or the
  lab's mark (SPEC §4, no default). E50 is defined at half the *peak* q, which on a stage failed by the stress ratio
  isn't q_f (decision 2).
- **Drained and undrained stay apart** (sheet 11 §7, sheet 08's pitfalls): a CU stage's E50 is Eu50 and a CD stage's is
  E′50. The result keeps `test_type` and never converts one into the other here.
- **Never drop data silently:** a stage with too few readings, no reading below q_f / 2, or no εv gets a reason column.
  Nothing is extrapolated past the readings.
- **Golden values by hand** from curves written out in the spec, and the cross-check with (a)'s E50 on `site.ags`.
- **No new dependency** (SPEC §12.1): the hyperbolic fit is a line fit in ε₁/q against ε₁, so the envelope-fit core's
  least squares (SPEC §4) or numpy is enough.

**Scope:**
- One public analysis, 🟡 `ht.analysis.triaxial_stiffness_from_readings()` (name checked against the registry in the
  spec step), on the readings frame, reusing `triaxial_failure_from_readings()`'s loading part and failure reading
  rather than picking them again.
- New registry columns for E50, ε50, Rf and ψ from readings, with their reasons, kept apart from the lab's
  `reported_secant_modulus_at_50_percent_peak` (SPEC §5, "names keep unlike values from pooling unawares").
- A comparison of hangtu's E50 with the lab's where both exist: 🟡 a column with the ratio, or a note counting stages
  that differ beyond the headings' rounding.
- Promote sheet 11 to the site (stage A–B content only, [V] values); sheet 08's and 09's pages lose "planned" and "later"
  on the triaxial route. A docs example on the example project.
- `docs/analysis/strength.md` gains a section (or 🟡 a new `docs/analysis/stiffness.md`, since (c) and (d) will add to
  it).

**SPEC and docs touched:**
- SPEC §4: one bullet for the new analysis, like the oedometer's.
- SPEC §10.3: the new columns, names checked against the whole registry.
- The parameter index: stage B for 08, 09 and 11 (triaxial route).
- No ingest change: the readings are read already (M16), and no new quantity kind is expected (`modulus` exists).

### Decisions (intent review, 2026-11-24)
1. **(b) keeps the three values that come from the curves (E50, Rf, ψ), and the rest of the milestone's (b) list
   moves.** `STATUS.md` gave (b) six things, too many for one sitting.
   - **Eur from unload–reload loops is deferred, with a TODO.** No file in hand has a loop: `site.ags`'s curves have no
     strain reversal before the largest strain, and the real sample's 99 stages have 4 reversals and no point marked
     as unload–reload. `triaxial_failure_from_readings()` also treats strain that falls within a loading part as a
     reading out of place, so loops would change its rules. Trigger: the first real file with loops.
   - **The drained↔undrained conversion (sheet 08 §5.4, [V]) moves to (c).** It needs ν′, which (c) selects. Done
     here, it would need ν′ as a new judgment that (c) then replaces.
   - **Eu from s_u (Duncan & Buchignani 1976) moves to (c) as a correlation, or is dropped.** Sheet 08 §5.2 has it [U]:
     its table is "the commonly reproduced table, not checked against the source", which is a chart. It goes in only
     with the source (or USACE EM 1110-1-1904 Fig. D-2) to read the chart from.
2. **E50 is at half the stage's largest q in its loading part, whatever the failure criterion.** That is E50's
   definition and `TRET_E50`'s ("50 % peak deviator stress"), so hangtu's value and the lab's mean the same thing. Rf
   uses q_f at the failure reading. Rejected: a blank unless the criterion is the largest q, which would leave the
   stress-ratio stages without a modulus they have.
3. **Rf's hyperbola is fitted by a stated rule:** the loading part's readings between two fractions of q_f, the fractions
   decided in the spec step from a verified source (Duncan & Chang 1970 use 70 % and 95 %, not yet read [U]). Without
   one, the rule is hangtu's, stated as such, and Rf goes out with its fitted range. The PLAXIS manual defines q_a and
   Rf but not which readings to fit.
4. **ψ comes from total strain increments at the failure reading,** the rate of dilation over a stated window of
   readings around it, with the assumption in the docstring. Sheet 09 §5.1 says to use plastic strains ([6] p. 485
   [V]); near peak the elastic part is small, and plastic strains would need E and ν′ for each stage, which (c)
   selects.
5. **No overrides for each test in this unit.** The rule's inputs (the fit's range, the ψ window) are arguments, and
   overrides per stage wait on TODO #77, as the oedometer's do (SPEC §4, "three kinds of choice").
6. **No plot here.** P20 in (c) is the stiffness figure. Rejected for now: drawing the E50 secant and the hyperbola on
   P12 (`triaxial_shearing()`).

### Out of scope
- **Eur, the drained↔undrained conversion and Eu from s_u** (decision 1).
- **Selecting E′ and ν′, P20** (M23 c); **E50ref, m and the rest of the HS set** (M23 d).
- **ψ from the shear box** (`SHBT_PDIN`, `SHBT_PDIS`) and the pressuremeter (`PMTP_AD`): other tests, later.
- **ψ in the Mohr–Coulomb set** from these values: the set reads ψ by `selection`, which can name this method once it
  exists. That wiring is (c)'s.
- **UU stages' ψ:** they have no volume change to read. (Their E50 and Rf are in, Spec decision 7.)

## Spec

### Changes
- **Two public analyses** in `ht.analysis`, each on a readings frame (`p.triaxial_readings()` or the
  `triaxial_readings` template), each returning one row per stage: the rows `triaxial_failure_from_readings()` returns,
  with the same `failure_criterion=` and `units=`, plus its own columns. Both reduce the readings through the one
  private `reduce_readings()`, so the stages, loading parts and failure readings are the ones P12 and the envelope fits
  use. Two functions rather than one, because a name has to say what it returns, and ψ isn't a stiffness:
  - `triaxial_stiffness_from_readings(df, *, failure_criterion=None, failure_ratio_range=(0.7, 0.95), units=None)`:
    E50, ε50, Rf, q_a and the fit's r²;
  - `triaxial_dilatancy_from_readings(df, *, failure_criterion=None, dilatancy_from=0.95, units=None)`: ψ and the rate
    of dilation it comes from.
- **Registry** (`columns.yaml`), checked against the whole registry and every spec (no collisions):

  | Column | Quantity | Description (short) |
  |---|---|---|
  | `secant_modulus_at_50_percent_peak` | modulus | E50 from the readings, undrained or drained as `test_type` says |
  | `axial_strain_at_50_percent_peak` | percent | ε50, where the readings reach half the peak |
  | `secant_modulus_at_50_percent_peak_reason` | text | why a stage has no E50 |
  | `failure_ratio` | dimensionless | Rf = q_f / q_a |
  | `asymptotic_deviator_stress` | stress | q_a, the hyperbola's asymptote |
  | `failure_ratio_r_squared` | dimensionless | r² of the transformed line fit |
  | `failure_ratio_reason` | text | why a stage has no Rf |
  | `dilatancy_angle` | angle | existing; its description widens to a stage's ψ from readings |
  | `dilation_rate` | dimensionless | −dεv/dε1 over the window, positive when dilating |
  | `dilatancy_angle_reason` | text | why a stage has no ψ |

  Names drop (a)'s `reported_` prefix: the lab's value and hangtu's are the same quantity by the same definition, kept
  apart by the prefix (SPEC §5, "names keep unlike values from pooling unawares"). `dilatancy_angle` is reused because a
  measured value takes the parameter's name (same rule); the Mohr–Coulomb set's ψ is a set constant, not a stage row,
  so the two never meet in one frame.
- **Docs:** a new `docs/analysis/stiffness.md` (§1 E50, §2 Rf), which (c) and (d) extend; `docs/analysis/strength.md`
  gains §9, ψ from readings, beside §2. `CLAUDE.md`'s list of analysis docs names `stiffness.md`.
- **Site:** reference entries for both functions; sheet 11 promoted to `docs/site/parameters/11-…` with its [V]
  content and an example on the example project; sheet 08's "E50 and Eu from triaxial tests" row and sheet 09's "From
  the test curves" row name the functions; the parameter index gets stage B (triaxial route) for 08, 09 and 11.
- **Sheet 11's citation** of the PLAXIS manual moves to the 2026.1 copy read for this spec: the hyperbola is Fig. 6–1,
  p. 69, not "Fig. 6–5".

### Decisions
1. **E50 is the secant from the stage's origin to half the peak.** The peak, q_p, is the largest q among the stage's
   loading-part q readings (intent decision 2). The origin is (ε1 = 0, q_0), with q_0 the q of the stage's reading at
   zero strain, or 0 where it has none. Then q_50 = q_0 + (q_p − q_0) / 2; ε50 is interpolated linearly between the
   last loading-part reading below q_50 and the next one, in row order before the peak; E50 = (q_50 − q_0) / ε50, with
   ε50 as a fraction. q_0 = 0 on an isotropic stage, so E50 is PLAXIS's definition (Eqs. 6–3, 6–4, Fig. 6–1); on an
   anisotropic stage whose lab gives q from the consolidated state, measuring q from q_0 is Obrzud & Truty's
   q_m = q − q_0 (Eqs. 2.12–2.14). The interpolation is the one (a) used for `site.ags`'s lab values, so the two agree
   (AC 9). Because a chord replaces the curve between two readings, E50 differs from a smooth curve's by up to about
   1 % at typical reading spacing (golden G1: 19 881 kPa against 20 000), which is the method, not an error.
2. **Rf from the transformed hyperbola.** PLAXIS Eq. 6–3 rearranges to ε1 / q = 1/E_i + ε1 / q_a, a straight line in
   ε1 / q against ε1 (Obrzud & Truty Eq. 2.11, ε1 / q = a + b ε1). hangtu fits that line by ordinary least squares and
   takes q_a = 1 / b and Rf = (q_f − q_0) / q_a, with q and q_f measured from q_0 (decision 1) and q_f the failure
   reading's q. Only the slope is used, because the sources disagree on the intercept: PLAXIS Eq. 6–4 gives
   a = (2 − Rf) / (2 E50), Obrzud & Truty's Eq. 2.10 gives a = 1 / (2 E50). Both give b = 1 / q_a, so Rf doesn't
   depend on which governs, and E50 comes from decision 1, never from a.
3. **The fit's readings: loading-part q readings up to the failure reading with 0.7 ≤ (q − q_0) / (q_f − q_0) ≤ 0.95.**
   This is hangtu's rule, stated as such: neither source in hand says which readings to fit (PLAXIS defines q_a and Rf
   only; Obrzud & Truty fit the whole curve in their Fig. 2.8). The lower bound leaves out the start, where bedding and
   seating errors dominate the ratio ε1 / q; the upper leaves out the approach to failure, where the curve leaves the
   hyperbola for the Mohr–Coulomb line (Fig. 6–1). Duncan & Chang (1970) are commonly said to use 70 % and 95 %;
   TODO #79 tracks reading them and confirming the bounds; the docstring says they are hangtu's until then.
   🟡 `failure_ratio_range=` changes the bounds; the range used is in `df.attrs`.
4. **Rf's limits.** Fewer than 3 readings in the range: blank, with a reason. b ≤ 0 (no asymptote: the transformed
   points don't rise): blank, with a reason. Rf > 1 (q_a below q_f): kept, not clipped, and counted in one warning;
   PLAXIS says Rf "should obviously be smaller than or equal to 1" (p. 69), so a value above 1 says the curve isn't
   hyperbolic in the range, which the engineer should see. r² is reported on every fitted row.
5. **ψ from the rate of dilation near peak.** Vermeer & de Borst (1984, Eqs. 3.2–3.3) define
   sin ψ = ε̇v^p / (−2 ε̇1^p + ε̇v^p) with tension positive; with compression positive, as `volumetric_strain` and
   `axial_strain` are, and r = −dεv / dε1, it reads sin ψ = r / (2 + r). Total strains stand in for plastic ones
   (intent decision 4): the source says that near the end of hardening "the elastic strain rate is almost zero, so that
   all further strain increments are of a plastic nature" (p. 12), and that εv against ε1 is then linear, "the
   so-called rate of dilation is found to be a constant". So r is the least-squares slope of εv against ε1 over the
   stage's loading-part εv readings from the strain where q first reaches `dilatancy_from` × q_f (🟡 0.95, hangtu's
   rule; TODO #79) to the failure reading's strain, inclusive.
6. **ψ's limits.** A stage that isn't drained (`CU`, `UU` and their variants): blank, reason "undrained: no volume
   change". No εv readings in the window, or fewer than 2: blank, with a reason. r ≤ −1 (contraction faster than
   axial strain, so sin ψ ≤ −1): blank, with a reason naming the rate. A negative ψ (a stage still contracting at
   peak, r < 0) is kept: it is what the readings say, and selection in (c) decides what to do with it.
7. **Every stage, including UU and later stages of a multistage test, gets E50 and Rf.** A UU stage's are undrained at
   its cell pressure; the carried `test_type`, `cell_pressure` and `multistage_test` say what each row is, so (c) and
   (d) can leave rows out by those columns rather than this analysis deciding. The docstring says that a later stage's
   specimen was sheared in an earlier one.
8. **No comparison column with the lab's E50.** The lab's values are on `p.triaxial()`'s rows, not the readings, so a
   comparison needs a merge the user can see. The site example merges and shows both; AC 9 checks they agree.
9. **Units.** Moduli and q_a come back in `cell_pressure`'s unit, as `deviator_stress_at_failure` does; ε50 in
   `axial_strain`'s. A strain column declared in another unit than percent is converted before the fraction is taken.
10. **No interpolation at failure is new.** Both analyses read q, εv and ε1 at readings; the failure row's columns
    (and the warning when Δu or εv at failure was interpolated) are `triaxial_failure_from_readings()`'s, unchanged.

### Sources
- **PLAXIS 2D 2026.1 Material Models Manual** (Seequent), §6.1, pp. 68–69: Eq. 6–3 (the hyperbola, −ε1 =
  (1/E_i) q / (1 − q/q_a), q < q_f), Eq. 6–4 (E_i = 2 E50 / (2 − Rf)), Eq. 6–6 (q_a = q_f / Rf), Fig. 6–1 (E50 the
  secant to q_f / 2), and "R_f … should obviously be smaller than or equal to 1. In PLAXIS, R_f = 0.9 is chosen as a
  suitable default". Read from page images, 2026-11-24.
- **Obrzud & Truty (2018),** *The Hardening Soil Model – A Practical Guidebook*, Z_Soil.PC 100701, rev. 21.10.2018:
  Eqs. 2.2, 2.8, 2.10–2.11 (the hyperbola in transformed form), 2.12–2.14 (q_m = q − q_0 for an anisotropically
  consolidated clay), pp. 13, 22–23; §3.3.3, p. 106 (Rf 0.75–1, CICD and CICU ranges after Kempfert 2006). Read
  2026-11-24.
- **Vermeer & de Borst (1984),** Non-associated plasticity for soils, concrete and rock, *Heron* 29(3): Eqs. 3.1–3.3
  and the text around them, pp. 12–13. Read from page images, 2026-11-24. Sheet 09's "Eqs. 3.2–3.3 not re-checked"
  becomes [V].
- **Duncan & Chang (1970):** [U], not in hand; TODO #79 (decision 3).

### Golden values
Hand calculations from the sources' equations, independent of the implementation.

**G1, a drained stage on PLAXIS's hyperbola** (kPa, strain in %). E50 = 20 000, Rf = 0.9, q_f = 300, so
q_a = 333.333 and E_i = 2 × 20 000 / 1.1 = 36 363.64 (Eqs. 6–4, 6–6). q = ε1 E_i / (1 + ε1 E_i / q_a), rounded to
0.01 kPa; failure at ε1 = q_f / (E_i (1 − Rf)) = 8.25 %; one reading past failure.

| ε1 (%) | 0 | 0.1 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 | 1.5 | 2 | 3 | 4 | 6 | 8.25 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q (kPa) | 0 | 32.79 | 59.70 | 101.27 | 131.87 | 155.34 | 173.91 | 206.90 | 228.57 | 255.32 | 271.19 | 289.16 | 300.00 | 295.00 |
| εv (%) | 0 | | | | | | 0.25 | | 0.35 | | 0.20 | −0.10 | −1.45 | |

with one more εv reading at 7.0 %, −0.70.
- **E50:** q_50 = 150, between 131.87 (0.6 %) and 155.34 (0.8 %): ε50 = 0.6 + 0.2 × 18.13 / 23.47 = 0.75450 %;
  E50 = 150 / 0.0075450 = **19 881 kPa** (exact curve: 0.75 %, 20 000; decision 1).
- **Rf:** the range is 210 ≤ q ≤ 285, so the readings at 2, 3 and 4 %. ε1/q = 8.7501e-5, 1.17500e-4, 1.47500e-4 per
  kPa at ε1 = 0.02, 0.03, 0.04; slope b = 2.99988e-3 /kPa, q_a = **333.35 kPa**, Rf = 300 × b = **0.9000**
  (± 0.0005, from the 0.01 kPa rounding), r² > 0.9999. The intercept, 2.750e-5, is 1/E_i (Eq. 6–4), not 1/(2 E50) =
  2.5e-5: a check that the test curve is PLAXIS's.
- **ψ:** q first reaches 0.95 × 300 = 285 at the 6 % reading, so the εv readings at 6.0, 7.0 and 8.25 %, which lie on
  a line of slope −0.6: r = 0.6, sin ψ = 0.6 / 2.6, ψ = **13.34°**.

**G2, `site.ags`'s B-1-U5 specimen 1** (CD, σ′3 1000 psf, psf; the example's readings as committed):
- q_f = 4123 at 5.1 %. q_50 = 2061.5, between 1501 (0.25 %) and 2244 (0.5 %): ε50 = 0.25 + 0.25 × 560.5 / 743 =
  **0.4386 %**, E50 = **470.0 ksf**, as (a) wrote to `TRET_E50` (its notes from the build).
- Rf: 2886.1 ≤ q ≤ 3916.85, the readings at 1.0, 1.5 and 2.0 % (2994, 3429, 3595): b = 2.22327e-4 /psf,
  q_a = **4498 psf**, Rf = **0.917**, r² = 0.998. The example's curves are hyperbolas with q_a = 1.1 q_f
  (`_make_examples.py`), so Rf ≈ 0.909 with their 1.5 % scatter: a sanity check, not the golden.
- ψ: q first reaches 3916.85 at 3.0 %; εv readings at 3.5, 4.5, 5.1 % (0.77, 0.76, 0.73): slope −0.02347, r = 0.0235,
  ψ = **0.66°**. Small, because the example's εv curve is a parabola whose slope is 0 at 0.75 ε_f; the example isn't
  reshaped (out of scope).

**G3, G1 anisotropic:** G1's q plus 50 kPa at every reading (q_0 = 50). E50, ε50 and Rf are G1's (decision 1, Obrzud &
Truty Eq. 2.14).

### Acceptance criteria
1. `triaxial_stiffness_from_readings()` on G1 gives ε50 0.7545 % (± 0.0001), E50 19 881 kPa (± 1), q_a 333.35 kPa
   (± 0.2), Rf 0.9000 (± 0.0005), r² > 0.9999.
2. On G3 it gives G1's E50, ε50 and Rf, to the same tolerances.
3. On G2 (read from `site.ags` through `p.triaxial_readings()` and from the CSV template), E50 470.0 ksf (± 0.1), ε50
   0.4386 % (± 0.0001), q_a 4498 psf (± 1), Rf 0.917 (± 0.001).
4. `triaxial_dilatancy_from_readings()` gives ψ 13.34° (± 0.01) and `dilation_rate` 0.600 on G1, 0.66° (± 0.01) and
   0.0235 on G2.
5. Rf's reasons: a stage with 2 readings in the range is blank with a reason naming the count; a stage whose ε1/q falls
   across the range (b ≤ 0) is blank with a reason; a stage with Rf > 1 keeps the value, and one warning counts the
   stages.
6. ψ's reasons: a CU and a UU stage are blank with "undrained"; a CD stage without εv, or with 1 εv reading in the
   window, is blank with a reason; a stage with r ≤ −1 is blank with a reason; a stage contracting at peak keeps its
   negative ψ.
7. E50's reasons: a stage whose q readings never rise above q_0 is blank with a reason. Every row has either a value or
   a reason in each pair, never both blank.
8. Both functions return `triaxial_failure_from_readings()`'s rows unchanged (same columns, values and order) with
   their columns added, for the same `failure_criterion=`; with `failure_criterion="max_stress_ratio"` on a CU stage
   whose ratio peaks before q does, E50 is still at half the largest q (intent decision 2) and Rf uses the failure
   reading's q.
9. On `site.ags`, for each of the nine stages (a) gave a lab E50, hangtu's E50 and ε50 equal
   `reported_secant_modulus_at_50_percent_peak` and `reported_axial_strain_at_50_percent_peak` to their headings'
   rounding (2DP).
10. Units: E50 and q_a carry `cell_pressure`'s unit in `df.attrs["units"]`, ε50 `axial_strain`'s; readings in kPa and
    in psf give the same E50 after conversion; `failure_ratio_range` and `dilatancy_from` are in `df.attrs`.
11. Every published docstring, message and site page cites no internal file (`tests/docs/test_site.py`,
    `tests/test_errors.py`), and both functions have reference entries.

## Plan
Draft, 2026-11-24. Four commits, each green: the tests it touches, then the CI command with `-n 2`. All on Opus, in
one session: steps 2–3 are calculations with validity limits, and step 4 touches citations and the site, so no run of
Sonnet-suited work is large enough to be worth a model boundary. A step past about 300 changed lines without tests
splits as noted. Reused, not rebuilt:
- **Readings:** `reduce_readings()`, `Reduced` (readings, stages, picks, rows, interpolated), `Readings.q_loading`,
  `_loading_part()`, `_interpolate()`, `_name()`, `_warn_interpolated()`, `DRAINED`
  (`analysis/_triaxial_readings.py`, `analysis/_triaxial.py`).
- **Line fit:** `line_fit()` and its `Line` (slope, r², `no_fit_reason`) from `analysis/_line_fit.py`, for both
  Rf's transformed line and ψ's slope (no new dependency).
- **Units:** `resolve_units()`, `parse_unit()`, `check_dimension()` (`units/__init__.py`).
- **Test data:** the example project and `ht.examples.path("triaxial_readings.csv")`; `E50_SAMPLES` and `tret()` in
  `tests/data/_make_examples.py` (the nine stages with the lab's E50, for AC 9).

**Settled before the build** (each corrects or narrows the Spec's text in the step named):
- **Strain units are checked, not converted** (checked in code, 2026-11-24). Spec decision 9 says a strain declared in
  another unit than percent is converted. `axial_strain` and `volumetric_strain` are `percent` columns, and
  `check_dimension()` accepts only `%` for that kind (a kind with no canonical unit is never converted). So both
  functions resolve the two columns' units where declared and raise `UnitsError` for anything but `%`; undeclared,
  they are read as percent, as `triaxial_failure_from_readings()` reads them today. Step 2 corrects decision 9.
- **AC 9's tolerance is each heading's half place:** ε50 within 0.005 % (`TRET_EP50`, 2DP) and E50 within 0.05 ksf
  (`TRET_E50`, 1DP, not 2DP as AC 9 says). (a) computed both from the same curves as written to the file, so the
  difference is only the rounding. Step 2 corrects AC 9.
- 🟡 **The origin is a reading only where the stage has one.** q_0 is the q of the stage's first loading-part q
  reading at ε1 = 0 (decision 1). Where the stage has no such reading, q_0 = 0, and ε50 is interpolated between
  readings only: a stage whose first loading-part q reading is already at or above q_50 gets E50's reason ("no reading
  below half the peak"), as the intent's constraints say, rather than a chord from an origin the lab didn't read. The
  alternative, interpolating from (0, 0), is what a curve with its zero dropped would want; it is a one-line change if
  you prefer it.
- **The peak** is the first loading-part q reading at the largest q (the lowest strain on a tie), as `pick()` breaks
  ties; ε50's bracketing readings are the loading-part q readings before it in row order.
- **Rf's readings** are the loading-part q readings at row positions up to and including the failure reading's, inside
  the range (decision 3); ε1 as a fraction (the slope b is the same either way, ε1/q's scale isn't).
- 🟡 **ψ's start is measured from q_0 too:** the window starts at the first loading-part q reading with
  (q − q_0) ≥ `dilatancy_from` × (q_f − q_0), as Rf's range is measured. Decision 5 says "`dilatancy_from` × q_f";
  the two agree on every isotropic stage (G1, G2), and measuring both from q_0 keeps G3's equivalence. Step 3
  corrects decision 5.
- **A blank `test_type`** gets ψ's reason "test_type blank: drainage unknown", not "undrained"; only the `DRAINED`
  types are read for ψ.
- **Argument checks:** `failure_ratio_range` is two numbers with 0 < lower < upper ≤ 1, and `dilatancy_from` a number
  with 0 < it ≤ 1; anything else is a `HangtuError` naming the argument and the rule.
- **Layout:** two private modules beside the readings one, `analysis/_triaxial_stiffness.py` and
  `analysis/_triaxial_dilatancy.py`, each calling `reduce_readings()` and then `_warn_interpolated()` as
  `triaxial_failure_from_readings()` does, so its rows and warnings are the same (AC 8).
- 🟡 **TODO #79's trigger is "before M23 (b) merges",** and Duncan & Chang (1970) aren't in hand. At close-out you
  either confirm 0.7–0.95 and 0.95 as hangtu's stated rules, and #79 keeps only the reading of the paper with the
  trigger "when Duncan & Chang (1970) is in hand", or the merge waits for the paper. Step 4 records whichever you
  choose; the build doesn't depend on it.

### 1. `M23: keep each stage's εv loading part in the readings` (Opus)
- `src/hangtu/analysis/_triaxial_readings.py`: `Readings` gains `volumetric_loading` (a boolean mask, like
  `q_loading`), set in `_read_stage()` from the εv loading part it already computes. No behavior change.
- `tests/analysis/conftest.py`: `readings()` and the golden path move here from
  `tests/analysis/test_triaxial_failure_from_readings.py`, which imports them (`from .conftest import ...`), for the
  two new test files.
- Tests: `tests/analysis/test_triaxial_failure_from_readings.py` and `tests/plot/` P12 tests unchanged and green; one
  test that the mask on the golden readings marks the εv loading part and not the tail. Its own commit, since it is a
  refactor (process.md, "Git and commits").

### 2. `M23: E50, ε50 and Rf from the triaxial readings` (Opus)
- `src/hangtu/columns.yaml`: the seven stiffness columns of the Spec's table (`secant_modulus_at_50_percent_peak`,
  `axial_strain_at_50_percent_peak`, `secant_modulus_at_50_percent_peak_reason`, `failure_ratio`,
  `asymptotic_deviator_stress`, `failure_ratio_r_squared`, `failure_ratio_reason`), each `ags: ["derived: …"]` naming
  the function, descriptions saying E50 is Eu50 on an undrained stage and E′50 on a drained one as `test_type` says,
  and that it sits beside the lab's `reported_` value; no internal file cited. Not added to any template (they are an
  analysis's output). `tests/test_registry.py` green.
- `src/hangtu/analysis/_triaxial_stiffness.py`: `triaxial_stiffness_from_readings()` by Spec decisions 1–4, 7, 9 and
  the settled points above. Per stage: q_0, q_p, q_50, ε50, E50 or its reason; Rf's range, `line_fit()` on ε1/(q − q_0)
  against ε1, q_a = 1/b, Rf = (q_f − q_0)/q_a, r², or the reason (fewer than 3 readings, naming the count; b ≤ 0; the
  line fit's own reason). One warning counting the stages with Rf > 1. `df.attrs["units"]`: E50 and q_a in
  `cell_pressure`'s unit, ε50 in `%`, Rf and r² none; `df.attrs["failure_ratio_range"]`. The docstring is the reference
  entry: the equations, PLAXIS 2026.1 Eqs. 6–3, 6–4, 6–6 and Fig. 6–1, p. 69, Obrzud & Truty (2018) Eqs. 2.10–2.14,
  the fit range as hangtu's rule, the intercept not used and why, that a later stage's specimen was sheared in an
  earlier one, the chord's ~1 % difference from a smooth curve, and an example on the example readings.
- `src/hangtu/analysis/__init__.py`: export it.
- `docs/site/reference/analysis.md`: its entry, beside `triaxial_failure_from_readings`.
- `docs/analysis/stiffness.md` (new): §1 E50 and ε50, §2 Rf (the rules, limits and reasons; links to the API
  reference rather than restating the docstring). `CLAUDE.md`: the analysis docs list names it.
- `SPEC.md` §4: one bullet, like the oedometer's, for E50, ε50 and Rf from readings (covering step 3's ψ too, so §4
  changes once); §10.3 if it lists column families, else nothing there.
- This file's Spec: decision 9 and AC 9 corrected as settled above.
- Tests: `tests/analysis/test_triaxial_stiffness_from_readings.py`, with G1 and G3 built in the test from the Spec's
  table (kPa, isotropic `CD`):
  - AC 1 (G1: ε50, E50, q_a, Rf, r²) and AC 2 (G3 the same);
  - AC 3 (G2, B-1-U5 specimen 1, from `p.triaxial_readings()` on the example project and from the CSV template,
    `failure_criterion="max_deviator_stress"`, compared in ksf/psf after conversion);
  - AC 5 (two readings in range: reason naming 2; ε1/q falling: b ≤ 0 reason; Rf > 1 kept, one warning with the count,
    asserted with `pytest.warns`);
  - AC 7 (q never above q_0: reason; the 🟡 no-reading-below-q_50 case; every row has a value or a reason in each
    pair, never both and never neither);
  - AC 8 for this function (the failure columns equal `triaxial_failure_from_readings()`'s, values and order, for
    both criteria; a CU stage with the ratio peaking first: E50 at half the largest q, Rf from the failure reading's q);
  - AC 9 (the nine `E50_SAMPLES` stages merged with `p.triaxial()` on `specimen_id` and `test_stage`, within the half
    places above);
  - AC 10 (units in attrs; kPa and psf readings give the same E50; the range in attrs; a strain declared in another
    unit raises; bad `failure_ratio_range` raises).
  - `tests/test_examples.py`: the new modulus columns join its unit lists if it checks every modulus column.
- Split if past ~300 lines without tests: the docs (`stiffness.md`, SPEC, CLAUDE.md) go in a commit of their own after
  the code.

### 3. `M23: ψ from the rate of dilation in the triaxial readings` (Opus)
- `src/hangtu/columns.yaml`: `dilation_rate` and `dilatancy_angle_reason`; `dilatancy_angle`'s description widens to
  "a Mohr–Coulomb set's ψ (by rule or selected), or a drained triaxial stage's ψ from its readings", and its `ags`
  names both derivations.
- `src/hangtu/analysis/_triaxial_dilatancy.py`: `triaxial_dilatancy_from_readings()` by Spec decisions 5–6 and the
  settled points above: the window's start strain from the q readings, the εv readings in the εv loading part
  (`volumetric_loading`, step 1) with strain in [start, ε_f], `line_fit()` slope s, r = −s, sin ψ = r / (2 + r), ψ in
  `deg`. Reasons: undrained; drainage unknown; no εv readings in the window, or 1 (naming the count); r ≤ −1 (naming
  the rate). Negative ψ kept. `df.attrs["dilatancy_from"]`. The docstring: Vermeer & de Borst (1984) Eqs. 3.1–3.3,
  pp. 12–13, the sign change to compression positive, total strains for plastic ones and the quoted reason, the window
  as hangtu's rule, valid for drained compression stages only.
- `src/hangtu/analysis/__init__.py`, `docs/site/reference/analysis.md`: export and entry.
- `docs/analysis/strength.md`: §9, ψ from readings, beside §2; the header's list of contents names it.
- This file's Spec: decision 5's start corrected as settled above.
- Tests: `tests/analysis/test_triaxial_dilatancy_from_readings.py`: AC 4 (G1 13.34° and 0.600; G2 0.66° and 0.0235,
  from the example project); AC 6 (a CU and a UU stage "undrained"; a CD stage without εv, and one with 1 εv reading in
  the window; r ≤ −1; a contracting stage's negative ψ); AC 8 for this function; AC 10's attrs and argument check.

### 4. `M23: close out (b): sheet 11's page, ψ and E50 on the site` (Opus)
- `docs/site/parameters/11-hardening-soil-stiffness.md` (new), promoted from the draft with stage A–B content only
  and [V] values: what it is, E50 and Rf from a triaxial curve (§5.2) with the PLAXIS citation moved to the 2026.1 copy
  (Fig. 6–1, p. 69, not "Fig. 6–5"), the oedometer moduli already built (§5.3), and the rest (HS set, E50ref, m) named
  as later without restating unverified content. Values and citations only, no copied tables or charts.
  `zensical.toml`: in the nav after 10.
- `docs/site/examples/hardening-soil-stiffness.py` (new): the example project's readings, both functions with
  `failure_criterion="max_deviator_stress"`, merged with `p.triaxial()` to show hangtu's E50 beside the lab's for the
  nine stages (Spec decision 8), and ψ for the drained ones. It must run warning-free (or assert the Rf > 1 warning if
  the example's scatter gives one).
- `docs/site/parameters/08-elastic-stiffness-soil.md`: the "E50 and Eu from triaxial tests" row names
  `triaxial_stiffness_from_readings()` instead of "planned"; Eu from s_u and the conversion stay later (intent
  decision 1).
- `docs/site/parameters/09-dilatancy.md`: the "From the test curves" row names `triaxial_dilatancy_from_readings()`
  (CD triaxial; direct shear later), with total strain increments near peak; line 59's "doesn't read ψ from test
  curves yet" rewritten for the shear box only; Vermeer & de Borst's Eqs. 3.2–3.3 marked verified.
- `docs/drafts/parameters/11-hardening-soil-stiffness.md` and `09-dilatancy.md`: the same citation fixes, so the
  draft and the page don't disagree.
- `docs/drafts/parameters/README.md`: stage B (triaxial route) for 08, 09 and 11.
- Close-out: `STATUS.md` ((b) done, (c) next, the "In progress" block cleared); `CHANGELOG.md` Unreleased (the two
  functions, in the user's words); `docs/TODO.md` #79 as you decide (settled above), its pointer moved from this file
  to `docs/analysis/stiffness.md` §2 and `strength.md` §9, and the Eur TODO from intent decision 1 with its trigger
  ("the first real file with unload–reload loops"); `SPEC.md` if the build settled anything cross-cutting.
- Tests: `tests/docs/test_site.py`, `tests/test_errors.py` (AC 11); `uv run python docs/prepare_site.py` and
  `zensical build --clean --strict`; then the whole suite. Look at the generated example output before committing.
