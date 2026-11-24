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
- **UU stages:** they have no σ′3, so no E50 at a known effective stress; 🟡 they get Eu50 at their cell pressure, or a
  reason. The spec step decides.
