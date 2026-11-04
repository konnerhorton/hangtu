# M17 (b): the shear box fit

## Intent
M17's second unit (SPEC §12.4; the split is M17 (a)'s decision 1): fit τ against σn for shear box stages, peak and
residual, free and through the origin, as a derived result beside `MohrCoulombFit`, on M11 (b)'s line-fit core.
It is stage B of sheets 04 (the shear box half; the triaxial half is done) and 22, and the input M18 (d)'s
Mohr–Coulomb set needs.

**Goal:**
- `ht.analysis.shear_box_fit(p.shear_box(), group_by=...)` (or a CSV in `ht.template("shear_box")`'s shape): per
  group, a peak and a residual line τ = c + σn tan φ, each free and through the origin, with n, R², the σn range
  fitted, the points fitted and those left out with their reasons, and the lab's own pairs listed beside them.
- A figure of the points and lines, τ against σn (decision 9), and the shear box groups in the example project,
  drawn on pages 04 and 22 (M17 (a) left them to this unit, as M11 (a) left the triaxial groups to M11 (b)).

**Why:**
- **Sheets 04 and 22 have data and no fit.** `p.shear_box()` (M17 a) gives each stage's peak and residual shear
  stress and its normal stresses, and nothing turns them into c and φ except the lab's own `SHBG_PCOH`/`SHBG_PHI`,
  which hangtu keeps as `reported_` and doesn't use (SPEC §7).
- **M18 (d) waits on it.** The Mohr–Coulomb set selects c′ and φ′ per geology unit from the tests; without this
  unit its only lab source is the triaxial fit.
- **The core was built for it.** SPEC §4 (envelope fits) names the shear box fit as a thin function on
  `hangtu.analysis._line_fit`. In τ–σn the criterion is the line itself, so x = σn, y = τ, b = tan φ, a = c: no
  transform, unlike s′–t.

**Evidence:**
- **Page 22, Methods** (Hoek 2023, ch. 4, eqs. 1–2 [V]): τp = cj + σn tan φj for peak, τr = σn tan φr for residual,
  and "report the free fit and the fit through the origin together: a large intercept from few stages is usually
  roughness, not cohesion".
- **Sheet 22 §5.2:** least squares through the origin, tan φ = Σσnτ / Σσn² (derived; `_line_fit`'s fixed-intercept
  case with a = 0), and the secant angle per stage, φsec = arctan(τ/σn).
- **Page 04:** "A direct shear φ′ is not a triaxial φ′: convert before combining them (Kulhawy & Mayne 1990,
  Eq. 4-10)". The conversion is selection's (M18), but the names here have to keep the two apart until then.
- **`p.shear_box()` keeps three normal stresses** (`applied_normal_stress`, `normal_stress_at_peak`,
  `normal_stress_at_residual`; M17 (a) decision 7) and picks none; the dictionary's example has 100, 100, 125.
  Sheet 22 §5.1: "SHBT_PEAK vs SHBT_PVST or SHBT_NORM".
- **No stage/specimen distinction** and no soil/rock joint label (M17 (a) decisions 8, 9, 11): the fit can't tell a
  multistage test or a rock joint from the file.
- **A first check** on `site_si.ags`'s BH2-D1 (σn 50, 100, 200 kPa; τp 38, 68, 128): the free least-squares line is
  τ = 8 + 0.6 σn exactly, so c = 8 kPa and φ = arctan 0.6 = 30.96°, the lab's 8 kPa and 31.0°. The spec writes this
  out as a golden value with the residual and through-origin fits.

**Scope:**
- **`shear_box_fit()`** and its result (`ShearBoxFit`, a `_DerivedResult`), with reference entries: `group_by=`,
  `pool=`, `units=`, `display_units=`, as `mohr_coulomb_fit()`; peak and residual, each free and through the origin.
- **Registry:** the fitted names (decision 2) and any result columns M11 (b)'s don't cover.
- **The figure** (decision 9): spec promoted to `docs/plots/`, built, PNG in `docs/plots/img/`, site page, reference.
- **Example file:** `site.ags` gains `SHBG`/`SHBT`: a soil set (peak and residual) and a rock joint set in MPa (decision 10).
- **Docs site:** pages 04 and 22's method rows link the function; the parameter index's 04 B and 22 B.

**Constraints:**
- SPEC §5, derived results: `kind = "derived"`, points fitted and left out with reasons, counts add up, the same
  views as `MohrCoulombFit` (`.to_frame()`, `.to_dict()`, the printed summary).
- SPEC §4, envelope fits: nothing forced through the origin unless asked; a group that can't give a parameter gets a
  reason, not an error.
- SPEC §5, not pooled unawares; SPEC §2.6, units resolve explicit → `attrs` → error, never guessed.
- M17 (a) decisions 8–10 stand: no multistage, rock-joint or effective/total label is inferred.
- The fit is derived, not cited (as M11 (b) decision 2): least squares on the criterion's own line. Hoek 2023 eqs.
  1–2 is the criterion's citation.

### Decisions (intent review, 2026-11-04)
Accepted as proposed, with decision 10 added from the review.

1. **One function for soil and rock joints.** Same line, same columns; the engineer separates them with `group_by=`
   or `where=` (M17 (a) decision 9). Names in the result say "peak" and "residual", not "joint" or "effective".
2. **Names keep shear box values apart from triaxial ones.** SPEC §5 says a fitted value takes the parameter's name,
   but `effective_friction_angle` here would pool a direct shear φ′ with a triaxial φ′ unawares, which page 04 warns
   against, and the stresses aren't labeled effective (M17 (a) decision 10). Proposed: `peak_cohesion`,
   `peak_friction_angle`, `residual_cohesion`, `residual_friction_angle`, matching the `reported_peak_…` columns,
   and a line in SPEC §5 saying a test's fit takes the test's name where the parameter's would pool unlike tests.
   The parameter's name with `test_type` kept on the result was rejected: it would leave only `test_type` to stop
   the pooling, and M18's conversion (Kulhawy & Mayne 1990, Eq. 4-10) is what turns one into the other.
3. **Both fits, always.** Each group gets four lines: peak and residual, each `"free"` and `"through_origin"`, as
   page 22 advises reporting them together. `cohesion=None` or `0` picks which is the main one in `.to_frame()`'s
   order and the summary (as `multistage=` does for `mohr_coulomb_fit()`); both are on the result.
4. **The normal stress a point is plotted against** is `normal_stress_at_peak` (or `_at_residual`) where the row has
   it, else `applied_normal_stress`, recorded per point as `normal_stress_basis`, with a note when a group mixes
   bases. `normal_stress="applied"` uses `applied_normal_stress` throughout. A required argument with no default
   was rejected: it fails on every file with only `SHBT_NORM`, and the rule hides nothing, since each point records
   its basis. Always `applied_normal_stress` was rejected: it ignores a lab's contact-area correction.
5. **Not pooled unawares:** more than one `test_type` (shear box and ring shear residuals differ) or
   `failure_criterion` in a group's fitted rows is an error naming each and its count; `pool=` pools on purpose.
6. **Rows left out and counted**, once each, per line: `count_no_shear_stress` (peak or residual blank for that
   line), `count_no_normal_stress`. A stage with a peak and no residual is in the peak fits only.
7. **Validity:** fewer than 2 points (1 through the origin) or all at one σn: no fit, with `_line_fit`'s reason;
   slope < 0: no fit, "no friction angle"; any slope ≥ 0 has an angle, so no upper limit; a negative intercept is
   kept with a warning suggesting the through-origin fit; residual above peak is QC's H001, not repeated here. The
   σn range fitted is on every line, and the summary says c is an intercept outside it.
8. **Secant angle per point**, arctan(τ/σn), on the result's points (sheet 22 §5.2): it shows a curved envelope
   that one straight line hides (page 22: "the envelope of a rough joint is curved"). No curved fit.
9. **A figure of its own, P31,** `ht.plot.shear_box_envelope(df, *, group_by=None, ..., ax=None,
   display_units=None)`: τ against σn, peak and residual points (filled and open), the free fit solid over the
   fitted range and dashed beyond, the through-origin fit lighter, the result box with c, φ, n, R² and the lab's
   pair. P11's Mohr view is also τ against σ, but draws circles from principal stresses and takes a
   `MohrCoulombFit`; adding a second input type to it would complicate a built plot. It is built in this unit, as
   M11 (b) built P11, so the fit's page has its figure; M17 (b2) was rejected.
10. **The example file has a soil set and a rock joint set in MPa**, so page 22 shows the same function and figure
    on joints and the example exercises the MPa units; `joins.ags` keeps the edge cases.

### Open (for the spec step)
- **Names** checked against the whole registry (decision 2, `normal_stress_basis`, the line kinds `"free"` and
  `"through_origin"`), and P31's ID against the drafts (P24–P30 are proposed IDs).
- **Golden values:** BH2-D1's peak and residual, free and through the origin, by hand; a rock joint set in MPa
  whose φ matches in kPa and psf; a ring shear set with residuals only.
- **Example file values**, hand-worked in the generator's comments, with site-like scatter (not points on a line).
- **Whether `mohr_coulomb_fit()`'s summary and `.to_frame()` code can be shared** with `ShearBoxFit` through the
  base, or stay apart (a refactor in its own commit if shared).

### Out of scope
- **M17 (c):** the intact Hoek–Brown fit.
- **M18:** the direct shear to triaxial conversion (Kulhawy & Mayne 1990, Eq. 4-10; page 04), characteristic c and
  φ, the correlation between c and φ (page 22, Variability), the Mohr–Coulomb set, choosing between free and
  through-origin fits.
- **Wave 4:** Patton, Barton–Bandis, JRC/JCS and scale corrections; the tangent to a curved envelope at a design σn
  (page 22, Hoek 2023 ch. 4 p. 10).
- **Wave 0:** shear box displacement curves (τ and dilation against displacement).
- **Later:** curved (power-law) envelopes; fully softened strength (D7608).

**SPEC and TODO touched:**
- SPEC §5, derived results (decision 2's naming line, in the spec commit); §4, the fit's line at
  close-out; §12.4, M17 status; `CLAUDE.md`'s "Next" sentence at close-out.
- Other docs: `docs/plots/P31-*.md` (new) and the plots README, `columns.yaml`, pages 04 and 22, the parameter
  index (04 B, 22 B), `docs/site/reference/analysis.md` and `plot.md`.
- TODO: none closed. #53 (failure criteria) stays open; the fit reads `failure_criterion` as written.
