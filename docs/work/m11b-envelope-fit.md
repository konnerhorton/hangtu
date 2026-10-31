# M11 (b): envelope fitting core, Mohr–Coulomb fit and P11

## Intent
M11 (a) gave each triaxial stage's principal stresses at failure (`p.triaxial()`, and
`ht.analysis.triaxial_failure_stresses()` for a CSV). This unit is stage B of sheet 04 for triaxial tests: the
fitting core wave 2 shares, its first use, `ht.analysis.mohr_coulomb_fit()`, and P11, which draws the fit.
P12 (curves and measured stress paths from readings) is M11 (c) (decision 1).

**Goal:** an engineer passes the failure points of a set of triaxial stages (one sample's, or a geology unit's)
and gets c′ and φ′ with everything needed to check them: the points used, the points left out and why, n, R²,
the stress range the fit holds over, and the lab's own reported values beside hangtu's. P11
(`ht.plot.failure_envelope()`) draws the same points and the same fit as Mohr circles, in s′–t or in p′–q, and
returns the fit.

**Why:**
- **Nothing fits the failure points yet.** Sheet 04 is at A (triaxial, M11 a) and C (SPT, M13 b1), with B empty.
  So the SPT estimates on P01 and P07 have no measured φ′ beside them, P26 and P27 (fitted c′ and φ′ against
  correlations and published values) have nothing to draw, and selection's first model set (M18, Mohr–Coulomb)
  has no measured c′ and φ′ to work from.
- **The lab's fit has to be checked** (sheet 04 §7): `reported_effective_friction_angle` and
  `reported_effective_cohesion` come back from `p.triaxial()` so that a fit by hangtu can be compared with them.
- **M17 reuses the core** for three more fits, so its shape is set here:
  - undrained strength, φu = 0 in total stress (sheet 05 §5.1);
  - the shear box, τ on σ′n, free or through the origin, peak and residual (sheets 04 §5.2 and 22 §5.1–5.2);
  - intact Hoek–Brown, (σ1 − σ3)² on σ3, free or with σci fixed (sheet 15 §5.2–5.3).

  Each is a least-squares line on transformed failure points, free or with its intercept fixed, followed by a
  back-transform to the criterion's parameters. The core is that line, the input rules, and the result
  (decision 3).
- **The fit has pitfalls that belong to it** (sheet 04 §5.1 and §7, P11 draft §11 and §14):
  - failure criteria, total and effective stress, or peak and residual points mixed in one fit;
  - multistage stages, which should be fitted with and without;
  - c′ read outside the stress range of the points;
  - c′ computed as a / cos α instead of a / cos φ′, or the s′–t intercept a drawn as c′;
  - a negative intercept forced to 0 without saying so.

**Scope:**
- **The fitting core** (internal): failure points in, a line fitted free or through a fixed intercept, the rows
  left out counted by reason, and a fit result object.
- **`ht.analysis.mohr_coulomb_fit()`**: the s′–t fit (P11 draft §4), with `stress="effective"` or `"total"`,
  `cohesion=` to fix c′, and `group_by=` for one fit per group.
- **P11, `ht.plot.failure_envelope()`**: the draft promoted to `docs/plots/P11-failure-envelope.md`, with its
  bare column names replaced by (a)'s registry names; the three spaces; idealized drained paths; user envelopes.
- **Sheet 04's site page** gains the triaxial fit as a stage B method, linked to the API reference.
- **The example file** (`ht.examples`' `site.ags`) gains triaxial groups ((a) spec decision 12), drawn on P11's
  site page.

**Constraints:**
- SPEC §3: `(fig, ax, fit)`, styling in a context manager, `ax=` for `Sheet`; equal aspect in all three spaces.
- SPEC §4: the fit reads the principal stresses `triaxial_failure_stresses()` writes and never recomputes them, so
  P11, (c) and M17 can't disagree with (a) about σ′.
- SPEC §2.6: units resolve explicit → `df.attrs["units"]` → error; stresses in display units, angles in degrees.
- SPEC §5's input rules, as far as they fit a regression: rows left out are counted and the counts add up; sources
  aren't pooled unawares; NaN never becomes 0.
- The fit result is its own object, not on the statistics base (`_Result`), and records a *derived* value
  (Eurocode 7's measured → derived → representative → design). *Property* and *parameter* keep their SPEC §5
  meanings. (Settled in (a)'s intent review, "Outline of (b)".)
- Golden values hand-calculated (P11 draft §12 has the first ones); rounding only for display.

**SPEC and TODO touched:**
- SPEC:
  - §12.4, M11 in three units (decision 1, in this commit), and `CLAUDE.md`'s "Next" sentence with it;
  - §4, a line for the fitting core and `mohr_coulomb_fit()`, since M17's fits follow it (close-out);
  - §5, a line saying where fit results sit beside the statistics results (spec step);
  - §10.3, any new names (the result's `.to_frame()` columns, P11's arguments), checked against the registry.
- Other docs: `docs/plots/P11-failure-envelope.md` (promoted), `docs/plots/README.md` (P11's status), the site page
  04, the parameter index (04 B), `docs/site/plots/` and `docs/site/reference/`.
- TODO: #53 (the failure criteria in D4767, D7181 and D2850; it stays open unless the standards are at hand).

### Decisions (intent review, 2026-10-31)
1. **M11 splits again: (b) the core, `mohr_coulomb_fit()` and P11; (c) P12.** P12 is the only part with new input,
   a CSV of readings with its own template, registry names and edge cases, so it follows data-then-analysis
   (`docs/reference/process.md`) as its own unit after this one. It reuses this unit's fit. Splitting the core from
   P11 was rejected: the core would be designed without the plot that uses it.
2. **The s′–t and p′–q formulas are written as derivations, not cited.** sin φ′ = tan α, c′ = a / cos φ′ and
   M = 6 sin φ′ / (3 − sin φ′) follow from the Mohr circle's geometry and the definitions of s′, t, p′ and q, so the
   spec writes out each step, as (a) did for σ′ = σ − u. Sheet 04 cut Lambe & Whitman (1969) as unverified, and a
   derivation can be checked without a copy.

### 🟡 Proposed, for review
3. **The core is a line, not a criterion.** One internal function fits y = a + b x by ordinary least squares,
   free or with a fixed, and keeps the points, their residuals, n, R² and the x range. Each criterion is a thin
   public function that transforms the points, calls it and back-transforms: Mohr–Coulomb here (s′–t), and in M17
   φu = 0, τ–σ′n and Hoek–Brown. A general nonlinear fitter is rejected: every fit wave 2 needs is linear in its
   transformed variables, and a closed form gives hand-checkable golden values.
4. **What a fit refuses to pool unawares** (an error naming each value and its count, `pool=` to pool on purpose,
   recorded on the result, as SPEC §5): more than one `failure_criterion`, and total-stress with effective-stress
   rows (`stress=` picks one). CU and CD stages pool without asking: both give effective-stress failure points,
   and fitting them together is common practice.
5. **Multistage stages are fitted with and without, in one calculation.** The result keeps both fits, the default
   view shows the fit with them and notes the other, and `multistage=False` makes the fit without them the main
   one. This follows "one calculation, many views" (SPEC §5) and sheet 04 §5.1's advice. Leaving them out by
   default was rejected: many projects' only effective-stress tests are multistage.
6. **Rows left out and counted, in this order:** blank principal stresses (extension, no pore pressure, the
   §6.10 blanks), the other stress basis (UU rows in an effective fit), and multistage stages when
   `multistage=False`. Error, not left out: σ′1 < σ′3 (P11 draft §11).
7. **Validity is behavior:**
   - fewer than 2 points: no fit, a result saying why (1 point fits with `cohesion=` fixed);
   - tan α ≥ 1: no valid φ′, an error naming the points;
   - a < 0: reported as fitted, with a warning that suggests `cohesion=0`; never forced;
   - the fit's σ′ range is on the result and in the summary; nothing extrapolates on its own.
8. **`group_by=` gives one fit per group**, and the result holds them all, with `.to_frame()` one row per group.
   P11 colors by group and draws one envelope per group. No `group_by=`: one fit of all the rows.
9. **The lab's values are a view of the result, not a fit of their own.** The result lists the distinct
   `reported_effective_friction_angle` and `reported_effective_cohesion` in each group with their counts, beside
   hangtu's c′ and φ′. It doesn't judge the difference.
10. **P11's default is `space="mohr"`,** the figure most reports show. The fit is always done in s′–t, and the other
   spaces draw it transformed, never refitted (P11 draft §4).
11. **Uncertainty of the fit:** the result keeps the standard errors of a and tan α from the regression, so M18 can
    use them, but this unit adds no interval on c′ and φ′ (the back-transform makes it nonlinear). To decide
    in the spec step whether a view shows them.

### Open (for the spec step)
- **Sources:** the derivations of decision 2, written out with their steps. The failure criteria in D4767, D7181
  and D2850 are TODO #53.
- **Names:** the result's fields and `.to_frame()` columns (`effective_cohesion`, `effective_friction_angle`,
  the intercept and slope in s′–t, the σ′ range), checked against the whole registry. `effective_friction_angle`
  exists as a correlation target, so a fitted φ′ written under that name would pool with the SPT estimates on
  P01 and P07, intended or not.
- **The result object:** what it shares with the statistics results (`.to_frame()`, `.to_dict()`, a summary, the
  hangtu version, the judgments used, if any), and whether it's the first of a family M17's fits join.
- **Whether `cohesion=0` is a judgment** (SPEC §4: judgments have no defaults). The free fit isn't a choice; fixing
  c′ is. Proposed: an argument only, recorded on the result, since it applies to one fit, not to a geology unit.
- **P11's edge cases** beyond the draft's §11: one group with too few points among several, `group_by=` with a
  column the rows don't have, and how the result box reads with several groups.

### Out of scope
- **M11 (c):** P12, the readings CSV and its template, and how a failure reading is picked from readings.
- **M17:** the φu = 0, shear box and Hoek–Brown fits, which reuse the core.
- **M18:** characteristic values of c′ and φ′, and the Mohr–Coulomb model set.
- **Later** (P11 draft §15): curved envelopes, peak and critical-state envelopes together, extension (a different
  M), a two-panel layout, and other regressions (fitting Mohr circles' tangents directly).
