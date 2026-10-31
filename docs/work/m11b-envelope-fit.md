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

## Spec
The plot's rules live in `docs/plots/P11-failure-envelope.md` (promoted from the draft). The fit's rules are
here: `mohr_coulomb_fit()` and the core have no topic doc of their own, and their docstrings become the reference
once built. This section lists what changes where, the decisions (the intent's proposals 3–11 settled, with the
changes noted), the derivations of decision 2 and the acceptance criteria.

### Changes
- **`docs/plots/P11-failure-envelope.md`:** promoted, with (a)'s registry names, the fitted range drawn solid and
  dashed beyond it, the result box with the lab's values, multistage fits, `color_by=`, and edge cases for groups.
  `docs/plots/README.md`: P11 `draft`; `docs/plots/drafts/README.md`: P11 promoted, P12 to M11 (c).
- **`ht.analysis.mohr_coulomb_fit()`** and **`ht.analysis.MohrCoulombFit`** (new), with reference entries.
- **The core** (internal, `hangtu.analysis._line_fit`): the line fit of decision 3 and the derived-result base of
  decision 12.
- **`ht.plot.failure_envelope()`** (new), with its reference entry, site page and example.
- **Registry:** `effective_cohesion`, `total_stress_cohesion`, `total_stress_friction_angle` (new, decision 11);
  `effective_friction_angle` gains `mohr_coulomb_fit()` as a source. None collides (checked against
  `columns.yaml`, 2026-10-31).
- **SPEC §5:** one bullet for derived results (decision 12), in this commit. **§4** gains the fit's line at
  close-out; **§10.3** nothing beyond the registry.
- **Example file:** `site.ags` gains `TREG` and `TRET`: a CU set in the Alluvium (`ALV`) and a CDM test in the
  Terrace (`TRC`), values chosen in the plan, drawn on P11's site page.
- **Docs site:** page 04's "s′–t fit of triaxial results" row links `mohr_coulomb_fit()`; the parameter index's
  04 B is part built (triaxial; the shear box in M17).

### Decisions
1. **`mohr_coulomb_fit(df, *, stress="effective", group_by=None, cohesion=None, multistage=True, pool=None,
   units=None, display_units=None) -> MohrCoulombFit`.** It reads the principal stresses at failure that
   `triaxial_failure_stresses()` writes (`stress="effective"`: `effective_minor_principal_stress_at_failure` and
   `effective_major_principal_stress_at_failure`; `"total"`: the total pair), and never computes them. A frame
   without them is an error that says to call `ht.analysis.triaxial_failure_stresses()` first.
2. **The constructions are derived, not cited** (intent decision 2). The derivations are under "Derivations"
   below; the docstring states the result of each and points to this spec.
3. **The core is a line** (intent proposal 3, as proposed). `_line_fit(x, y, *, intercept=None)` fits
   y = a + b x by ordinary least squares, free or with a fixed, and returns a, b, n, R², the residuals and the
   reason it can't fit. Mohr–Coulomb uses it with x = s′, y = t. M17's fits will be thin functions on it.
   - Free: b = Sxy / Sxx, a = ȳ − b x̄, with Sxx = Σ(x − x̄)², Sxy = Σ(x − x̄)(y − ȳ).
   - Fixed a: b = Σx(y − a) / Σx² (least squares with one unknown).
   - R² = 1 − Σ(y − ŷ)² / Σ(y − ȳ)², the centered definition in both cases, so a fit through the origin can
     have a low or negative R² and is comparable with the free fit. NaN with one point or when all y are equal.
   - Can't fit: free with fewer than 2 points or Sxx = 0 ("all points at the same mean stress"); fixed with no
     point or Σx² = 0.
   - No standard errors (*changed from intent proposal 11*): the intervals on c′ and φ′ that need them belong to
     M18, which decides how a fit's uncertainty enters a characteristic value. The residuals are kept, so M18 can
     compute them from the result.
4. **Not pooled unawares** (intent proposal 4): within each group, the rows fitted (after those left out, decision
   6) with more than one `failure_criterion` value are an error naming each value and its count; a blank is a value
   of its own, so a blank beside a named criterion is mixed. With `stress="total"`, `test_type` is checked the same
   way (UU and CU total envelopes differ). `pool=` names the columns to pool on purpose, and the result records it.
   CU and CD stages pool without asking in effective stress. A column the rows don't have isn't checked, and the
   notes say so ("failure_criterion not given").
5. **Multistage stages are fitted with and without** (intent proposal 5, as proposed). A group with at least one
   `multistage_test` True gets two fits: `"all"` and `"single_stage"`. `multistage=True` makes `"all"` the main
   one, `False` `"single_stage"`. Without the column there is one fit, and a note says stages weren't told apart.
   A group whose stages are all multistage has a `"single_stage"` fit with no points and that reason.
6. **Rows left out and counted** (intent proposal 6, reasons renamed), each once under the first that applies:
   `count_no_principal_stresses` (a total principal stress blank: extension and incomplete rows),
   `count_no_effective_stresses` (effective fit only: the total stresses but an effective one blank, such as UU or
   CU without pore pressure), `count_multistage_left_out` (`multistage=False`).
   `count` plus these is the group's rows. σ′1 < σ′3 on any row is an error naming the rows.
7. **Validity is behavior** (intent proposal 7, *changed*: a group that can't give φ′ is a reason, not an error,
   so one bad group doesn't stop the others):
   - fewer than 2 points (1 with `cohesion=0`), or Sxx = 0: no fit, with the reason;
   - tan α < 0 or ≥ 1: no fit, reason "slope tan α = 3.0 is outside 0 ≤ tan α < 1: no friction angle fits". sin φ′
     = tan α has no angle from 0° to 90° there;
   - a < 0: fitted and kept, warning naming the groups and suggesting `cohesion=0`; never forced;
   - a point with σ′3 < 0: kept, warning naming the rows (tension);
   - the σ′n range of the tangent points is on every fit (`lowest_normal_stress`, `highest_normal_stress`), and the
     summary says c′ is an intercept outside it;
   - one warning per kind per call, naming the groups or rows; a fit of two points notes that it passes through
     both (R² = 1 by construction).
8. **`group_by=`** (intent proposal 8, as proposed): one fit per group, groups in order of first appearance; a
   missing column is an error naming it. No `group_by=`: one group of every row.
9. **The lab's values are a view** (intent proposal 9): each group lists its distinct
   (`reported_effective_cohesion`, `reported_effective_friction_angle`) pairs with their counts of stages, from the
   rows fitted. `.to_frame()` gives the pair when the group has one, else blanks and `count_reported_pairs`.
   Nothing compares them. Total-stress fits don't list them (the lab's values are effective).
10. **`cohesion=` takes None or 0 only.** It is an argument recorded on the result, not a judgment: it applies to
    one fit, not to a geology unit (SPEC §4). Another value is an error saying why: c′ fixed at a non-zero value
    makes a = c′ cos φ′ depend on the slope, so the s′–t fit is no longer a line.
11. **Names.** The fitted values are `effective_cohesion` and `effective_friction_angle` (total: `total_stress_cohesion`,
    `total_stress_friction_angle`). A fit of test results is the derived value of the parameter, so it takes the
    parameter's name, as a measured value does; correlation estimates carry `correlation_name` and the lab's values
    `reported_`, so none is pooled with another unawares (SPEC §5). The line's own values are `line_intercept` (a)
    and `line_slope` (tan α), not `s_t_…`, which reads as S_t, sensitivity. The tangent-point range is
    `lowest_normal_stress` and `highest_normal_stress`.
12. **Derived results are a family of their own** (SPEC §5, new bullet). A frozen dataclass base in `ht.analysis`,
    `kind = "derived"`, with the function, the unit, the notes, the judgments of the input (none here) and the
    hangtu version, `.to_dict()` (JSON-serializable, as the statistics results), `.to_frame()` and a printed
    summary. `MohrCoulombFit` is the first; M17's fits join it. It keeps the points it fitted (identifiers and
    stresses), not a reference to the input. *Property* and *parameter* keep their SPEC §5 meanings.
13. **`MohrCoulombFit.to_frame()`**: one row per group and fit (`stages`: `"all"`, then `"single_stage"` where it
    exists, the main one first): the `group_by` columns, `stages`, the cohesion and friction angle (decision 11),
    `line_intercept`, `line_slope`, `r_squared`, `count`, `lowest_normal_stress`, `highest_normal_stress`, the lab's
    pair and `count_reported_pairs` (effective only), the counts left out, and `no_fit_reason`. `attrs["units"]`
    gives the stress columns' unit; angles are degrees.
14. **Units** resolve as SPEC §2.6 (`units=`, then `df.attrs["units"]`, else an error naming the column). The two
    stresses must both be stresses, else an error. The fit is made in the minor principal stress's unit, or in
    `display_units=`'s (kPa for SI, psf for US), converted before fitting; the line is linear, so c′ scales with
    the unit and φ′ doesn't change.

### Derivations
Notation: σ1, σ3 the major and minor principal stresses at failure (effective, or total with `stress="total"`);
s = (σ1 + σ3)/2 and t = (σ1 − σ3)/2, the Mohr circle's center and radius; p = (σ1 + 2σ3)/3 and q = σ1 − σ3 in
triaxial compression (σ2 = σ3, σ1 axial). The envelope is τ = c + σ tan φ, with 0 ≤ φ < 90°.
1. **Tangency gives the s–t line.** The envelope touches the circle when the distance from the center (s, 0) to
   the line equals the radius. The line τ − σ tan φ − c = 0 has unit normal (−sin φ, cos φ), so the distance from
   (s, 0) is (s tan φ + c) cos φ = s sin φ + c cos φ. Setting it equal to t: **t = c cos φ + s sin φ**, a line in
   s–t with intercept a = c cos φ and slope tan α = sin φ.
2. **Back to c and φ:** φ = arcsin(tan α), defined for 0 ≤ tan α < 1; c = a / cos φ. (Not a / cos α: α is the
   slope angle in s–t, not the friction angle.)
3. **The tangent point.** The radius to the tangent point is along the normal, (−sin φ, cos φ), so for a circle
   of the fitted radius t̂ = a + s tan α at center s: **σn = s − t̂ sin φ, τ = t̂ cos φ**. It lies on the envelope:
   c + (s − t̂ sin φ) tan φ = c + s tan φ − t̂ sin²φ / cos φ, and with t̂ = c cos φ + s sin φ this is
   (c cos φ + s sin φ) cos φ = t̂ cos φ.
4. **p–q.** With σ1 = s + t and σ3 = s − t: p = s − t/3 and q = 2t, so s = p + q/6 and t = q/2. Substituting into
   t = a + s sin φ: q/2 = a + (p + q/6) sin φ, so q (3 − sin φ)/6 = a + p sin φ, and
   **q = 6 c cos φ / (3 − sin φ) + p · 6 sin φ / (3 − sin φ)**: M = 6 sin φ / (3 − sin φ), q₀ = 6 c cos φ / (3 − sin φ).
5. **Idealized drained path.** σ3 constant and σ1 rising by Δ from σ3: s and t each grow by Δ/2 (slope 1 in s–t,
   from (σ3, 0)); p grows by Δ/3 and q by Δ (slope 3 in p–q, from (σ3, 0)).
6. **Least squares.** Minimizing Σ(y − a − b x)² over a and b gives the normal equations, whose solution is decision
   3's b = Sxy / Sxx, a = ȳ − b x̄; with a fixed, minimizing over b alone gives b = Σx(y − a) / Σx².

### Sources
- **The constructions:** derived above (decision 2). No coefficient or table value is used.
- **1 psf** = 0.45359237 × 9.80665 / 0.3048² Pa = 47.880259 Pa, exact by definition (P00 §4).
- 🔬 **The failure criteria** (maximum deviator stress, maximum principal stress ratio) in ASTM D4767, D7181 and
  D2850: TODO #53. The fit reads `failure_criterion` as written and only checks that a group has one; nothing here
  depends on what each criterion means.

### Acceptance criteria
Golden values hand-calculated from the derivations, with the arithmetic done to 9 significant figures; tolerance
1e-7 relative (the precision of the hand calculation) unless stated. Points are (σ′3, σ′1) in kPa.
1. **Golden 1, free:** (100, 300), (200, 500): s′ = 200, 350; t = 100, 150; tan α = 50/150 = 1/3,
   a = 125 − (1/3)(275) = 33.333333; φ′ = arcsin(1/3) = 19.471221°; c′ = 33.333333 / √(8/9) = 25√2 = 35.355339
   kPa; R² = 1; tangent points σ′n = 200 − 100/3 = 166.66667 and 350 − 150/3 = 300 kPa. Two-point note.
2. **Golden 1, `cohesion=0`:** tan α = (200·100 + 350·150) / (200² + 350²) = 72500/162500 = 29/65 = 0.44615385;
   φ′ = 26.497185°; c′ = 0; R² = 1 − (10.769231² + 6.1538462²)/1250 = 57/65 = 0.87692308.
3. **Golden 2:** (100, 300), (200, 600): tan α = 0.5, a = 0, φ′ = 30°, c′ = 0 (to 1e-12 absolute), free and with
   `cohesion=0`. One point (100, 300) with `cohesion=0`: φ′ = 30°, R² NaN; without: no fit, "1 point".
4. **CU set (`site_si.ags`, BH1-U3):** (40, 220), (90, 353), (180, 593): s′ = 130, 221.5, 386.5; t = 90, 131.5,
   206.5; tan α = 0.454233427, a = 30.9252437; φ′ = 27.015622°, c′ = 34.713036 kPa, R² = 0.999999682; tangent
   points 89.1301 to 292.7069 kPa (1e-6). The lab's pair (5 kPa, 27.0°) with 3 stages.
5. **Pooled, effective (`site_si.ags`, all of `p.triaxial()`):** the CU set and BH2-U2's CDM stages (100, 400),
   (200, 720), (400, 1300) fit together: tan α = 0.503104935, a = 21.9774766, φ′ = 30.205634°, c′ = 25.430262 kPa,
   R² = 0.998125121, `count` 6; the `"single_stage"` fit is AC 4's; `count_no_effective_stresses` 3 (the UU
   specimens); the lab's pairs (5, 27.0) × 3 and (29, 30.0) × 3, `count_reported_pairs` 2.
6. **Total stress:** the CU set's totals (400, 580), (500, 763), (700, 1113) give tan α = 0.278759064,
   a = −45.7744608, φ′ = 16.186156°, c′ = −47.663803 kPa, with the negative-intercept warning naming the group.
   All of `site_si.ags` in total stress raises, naming `CU` × 3, `CDM` × 3 and `UU` × 3 under `test_type`, and
   "Maximum deviator stress" × 6 and blank × 3 under `failure_criterion` (the UU tests have none);
   `pool=["test_type", "failure_criterion"]` fits them and records both. The UU specimens alone, (100, 220), (200, 324), (300, 418), have
   tan α = −0.00481368 and no fit, with the slope reason.
7. **Validity:** (300, 500), (100, 900) gives tan α = 3.0 and no fit, with the reason; (100, 250), (300, 1000) gives
   tan α = 0.578947368, a = −26.3157895, φ′ = 35.376540°, c′ = −32.274861 kPa and the warning; two points at the
   same s′ ((100, 300), (150, 250)) give no fit, "same mean stress"; a row with σ′1 < σ′3 raises naming it; a point
   with σ′3 = −10 is fitted, with the tension warning.
8. **Pooling:** two `failure_criterion` values in one group raise, naming each and its count; a blank and a named
   one raise; `pool="failure_criterion"` fits them, and `.pooled` records it. A group without the column fits, with
   the note.
9. **Multistage:** with `multistage=False`, AC 5's main fit is AC 4's and `count_multistage_left_out` is 3; the
   `"all"` fit is still in the result. A group of only BH2-U2's stages with `multistage=False` has no main fit,
   with its reason.
10. **Groups and counts:** `group_by="test_type"` on `site_si.ags` gives three groups (CU, CDM, UU), the UU one
    with no fit; every group's `count` and counts left out add up to its rows. `.to_frame()` has decision 13's
    columns in order and `attrs["units"]`; `.to_dict()` passes `json.dumps`.
11. **Units:** the twin files give the same φ′ (1e-9 relative) and c′ in psf = c′ in kPa / 0.047880259 under
    `display_units="US"`; a frame in psf (`attrs["units"]`) fitted with `display_units="SI"` gives kPa; a frame
    without units raises naming the column; stresses in a length unit raise.
12. **Errors:** a frame from `ht.template("triaxial")` without the principal stresses raises with
    "triaxial_failure_stresses()" in the message; `cohesion=5`, `stress="drained"` and a missing `group_by` column
    each raise saying what to do.
13. **The plot:** P11's §12 criteria.
14. **Reference:** `mohr_coulomb_fit`, `MohrCoulombFit` and `failure_envelope` in the API reference (the test that
    fails without an entry), with the docstring checklist of the sheets' `TEMPLATE.md`.
