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

## Spec
The plot's rules live in `docs/plots/P31-shear-box-envelope.md` (new; there was no draft). The fit's rules are
here: `shear_box_fit()` has no topic doc of its own, and its docstring becomes the reference once built. This
section lists what changes where, the decisions (the intent's, settled, with what was added or changed marked),
the derivation and the acceptance criteria. 🟡 marks what the intent left open and this draft proposes.

### Changes
- **`ht.analysis.shear_box_fit()`** and **`ht.analysis.ShearBoxFit`** (new), with reference entries.
- **`ht.plot.shear_box_envelope()`** (new, P31), with its spec, reference entry, site page and example.
  `docs/plots/README.md`: P31 in batch 2, `draft`.
- **Registry:** `peak_cohesion`, `peak_friction_angle`, `residual_cohesion`, `residual_friction_angle` (new,
  decision 2), `ags: ["derived: docs/work/m17b-shear-box-fit.md"]`, `used_by: [P31]`. None collides: checked
  against `columns.yaml`, the plot specs, the sheets and the code, 2026-11-04 (the only other mentions are this
  file's). Result columns aren't registered, as M11 (b)'s `line_intercept` isn't.
- **SPEC §5, derived results:** one sentence (decision 2), in this commit. **§4** gains the fit's line at
  close-out (the envelope fits bullet); **§12.4** M17 (b) done at close-out.
- **`docs/data/datasets.md` §6.12:** "a user who knows can add one, and the fit reads it" becomes "a user who knows
  can add one and fit with `group_by="multistage_test"` or `where=`" (decision 12), in this commit.
- **The shared code** (decision 14): a refactor commit moves `mohr_coulomb_fit()`'s group, pooling and lab-pair
  helpers into a module both fits import, with no change in behavior.
- **Example file** (decision 13, *changed*): `site.ags` gains a sandstone unit (`SST`) cored below the Terrace in
  B-3, with its row in `strata.csv` and its unit weight in `judgments.yaml`, and `SHBG`/`SHBT`: the soil sets and a
  rock joint set, all stored in psf.
- **Docs site:** page 22's two "M17 (b)" method rows link `shear_box_fit()`, and its example draws the joint set;
  page 04 gains a row "Least-squares fit of shear box results" linking it (the existing "Direct shear envelope
  (Kulhawy & Mayne 1990, Eq. 4-10)" row is the conversion and stays M18's, decision 2); the parameter index's
  04 B (the shear box half) and 22 B built.

### Decisions
1. **`shear_box_fit(df, *, group_by=None, cohesion=None, normal_stress="at_peak_or_residual", pool=None,
   units=None, display_units=None) -> ShearBoxFit`.** It reads `p.shear_box()`'s columns (or a CSV in
   `ht.template("shear_box")`'s shape, which has the same ones) and fits each group's peak and residual. One
   function for soil and rock joints (intent decision 1): the engineer separates them with `group_by=` or `where=`.
2. **Names** (intent decision 2, as proposed): the fitted values are `peak_cohesion`, `peak_friction_angle`,
   `residual_cohesion` and `residual_friction_angle`, beside the lab's `reported_peak_…` and `reported_residual_…`.
   SPEC §5 gains: "A test's fit takes the test's name instead where the parameter's would pool unlike tests: the
   shear box fit gives `peak_friction_angle`, not `effective_friction_angle`, because a direct shear φ′ isn't a
   triaxial φ′ until selection converts it (M18), and its stresses aren't labeled effective (M17 a)." Page 04's
   Kulhawy & Mayne row is that conversion, so the fit doesn't link to it.
3. **The fit is the core's line, untransformed** (SPEC §4): x = σn, y = τ, `_line_fit(x, y)` free and
   `_line_fit(x, y, intercept=0)` through the origin; c = a, φ = arctan b (Derivation). No coefficient is used, so
   the fit is derived, not cited (as M11 (b) decision 2); Hoek (2023, ch. 4, eqs. 1–2) is the criterion's citation.
4. **Four lines per group, always** (intent decision 3): peak and residual, each `"free"` and `"through_origin"`.
   `cohesion=None` makes `"free"` the main line, `cohesion=0` `"through_origin"`; the main one comes first in
   `.to_frame()` and the summary, and both are on the result. Another `cohesion=` value is an error saying the
   fit is free or through the origin. *Changed from `mohr_coulomb_fit()`*: there, `cohesion=0` replaces the free
   fit; here both are always made, as page 22 advises reporting them together.
5. **The normal stress of each point** (intent decision 4): with `normal_stress="at_peak_or_residual"` 🟡 (the
   value's name), a peak point takes `normal_stress_at_peak` where the row has it, else `applied_normal_stress`;
   a residual point `normal_stress_at_residual`, else `applied_normal_stress`. `normal_stress="applied"` takes
   `applied_normal_stress` throughout. Each point records `normal_stress_basis` (`"at_peak"`, `"at_residual"` or
   `"applied"`), and a line whose points have more than one basis gets a note naming each and its count. Any
   other value of `normal_stress=` is an error listing the two.
6. **Not pooled unawares** (intent decision 5): within a group, each strength's fitted rows (after those left
   out, decision 7) with more than one `test_type` or `failure_criterion` are an error naming each value and its
   count, as `mohr_coulomb_fit()`'s (a blank is a value of its own). Peak and residual are checked apart: a ring
   shear test with only a residual and a shear box test with only a peak share no line. `pool=` takes
   `"test_type"` and `"failure_criterion"` and the result records it; a column the rows don't have isn't checked,
   and the notes say so.
7. **Rows left out and counted** (intent decision 6), per strength, each once under the first reason that applies:
   `count_no_{peak,residual}_shear_stress` (the shear stress blank), then `count_no_{peak,residual}_normal_stress`
   (no normal stress by decision 5's rule). A stage with a peak and no residual is in the peak lines only. The
   strength's `count` plus these is the group's rows. Both lines of a strength fit the same rows.
8. **Validity is behavior** (intent decision 7):
   - free with fewer than 2 points, or all at one σn: no line, with the core's reason ("1 point: a line needs at
     least 2", "all points at the same normal stress"); through the origin with no point, or every σn = 0: no
     line ("no points", "all points at normal stress = 0");
   - slope b < 0: no line, "slope tan φ = −0.2 is below 0: no friction angle". Every b ≥ 0 has an angle below 90°,
     so there is no upper limit;
   - a free intercept a < 0: kept as fitted, one warning per call naming the groups and strengths and pointing to
     the through-origin line on the result; never forced;
   - 🟡 *added*: a negative shear or normal stress on a row the fit would use is an error naming the rows and
     saying to check the sign (a shear box shears under compression, and the residual is a magnitude). Zero is
     kept;
   - residual above peak is QC's H001 and isn't repeated;
   - every line has the σn range of its points (`lowest_normal_stress`, `highest_normal_stress`), and the summary
     says c is an intercept at σn = 0, outside it;
   - a free line of 2 points notes that it passes through both (R² = 1 by construction); a through-origin line of
     1 point has R² NaN (the core's).
9. **The secant angle per point** (intent decision 8), φsec = arctan(τ/σn) in degrees, on the result's points as
   `secant_friction_angle`; NaN where σn = 0. Nothing is fitted to it.
10. **`group_by=`**, as `mohr_coulomb_fit()`: one set of lines per group, in `group_keys()` order (sorted, a
    categorical's own order, blank last); a missing column is an error naming it. No `group_by=`: one group of
    every row. Common choices: `"specimen_id"` (one test), `"geology_unit"`, `"test_type"`.
11. **The lab's pairs are a view** (as M11 (b) decision 9): per strength, the distinct (`reported_…_cohesion`,
    `reported_…_friction_angle`) pairs of the rows fitted, each with its count of stages, converted to the fit's
    unit. `.to_frame()` gives the pair when there is one, else blanks and the count. Nothing compares them.
12. **`multistage_test` isn't read** 🟡 (*added*: M17 (a)'s §6.12 said "the fit reads it", and the intent didn't
    say how). The file can't tell a multistage shear box from specimens entered as stages (M17 (a) decision 8), and
    a user who adds the column fits with `group_by="multistage_test"` or `where=`, which gives the same lines
    without a second set of rows. `docs/data/datasets.md` §6.12 changes in this commit.
13. **The example data** (intent decision 10, *changed* in the spec review, 2026-11-04): AGS gives each heading
    one unit per group, so `site.ags` (psf) can't store a joint set in MPa. The joint set is stored in psf and
    shown in MPa when the page runs: page 22's example fits it inside
    `ht.settings.override(display_overrides={"stress": "MPa"})` with `display_units="SI"`, which the fit's
    conversion (`units.to_display`) and `p.shear_box()` already read. MPa input stays tested on `joins.ags` and a
    hand-built frame (AC 12). A joint needs rock to sit in, so the site gains bedrock:
    - **B-3 is cored into sandstone** below its soil: Terrace to 61.5 ft as now, then `SST` (Sandstone) from 61.5
      to 71.5 ft, so `LOCA_FDEP` becomes 71.5. The generator takes the rock top as the end of the SPTs, so B-3's
      SPTs, and every other seeded value in the file, stay as they are (the plan checks the file's other groups are
      unchanged).
    - **`strata.csv`** gains `SST,Sandstone,rock,4,<color>`; 🟡 `soil_class` `rock` (its categories are TODO #3).
      **`judgments.yaml`** gains Sandstone's bulk unit weight, 🟡 150 pcf, so `vertical_stress()` integrates
      through B-3's log.
    - Every figure grouped by geology unit can show a fourth unit where B-3's rock is drawn; the close-out reruns
      the site's examples and looks at each.
    Rejected: a CSV of its own in MPa (a second example, and the site with no rock its joints come from); the whole
    `SHBT` group in kPa (unlike a US lab's file). Values and hand fits are under "Example data".
14. **Shared code** (the intent's open item): `_names`, `_label`, `_cell`, the pooling check and the lab-pair
    collection move from `_mohr_coulomb.py` to one module (`hangtu.analysis._fit_groups`), in a refactor commit
    before the fit. `.to_frame()` and `__str__` stay per class: `MohrCoulombFit` has one row per fit of stages,
    `ShearBoxFit` one row per line kind with peak and residual side by side (decision 15), so a shared version
    would be a switch on the class.
15. **`ShearBoxFit.to_frame()`** 🟡 (the shape): one row per group and line kind, the main one first. Columns:
    the `group_by` columns; `line_kind` (`"free"`, `"through_origin"`); then for peak and for residual, in that
    order: `{s}_cohesion`, `{s}_friction_angle`, `{s}_r_squared`, `{s}_count`, `{s}_lowest_normal_stress`,
    `{s}_highest_normal_stress`, `{s}_normal_stress_basis` (the basis, or `"mixed"`), `reported_{s}_cohesion`,
    `reported_{s}_friction_angle`, `count_reported_{s}_pairs`, `count_no_{s}_shear_stress`,
    `count_no_{s}_normal_stress`, `{s}_no_fit_reason`. Counts of rows left out start with `count_`, as everywhere
    else (SPEC §5); the rest start with the strength. Through the origin, `{s}_cohesion` is 0. Wide, not long, so
    `peak_friction_angle` is one column M18 (d) reads, never a value column whose meaning a `strength` column
    changes. `attrs["units"]` gives the stress columns' unit; angles are degrees. `.groups` holds each group's
    key, its row count and per strength its lines and points (row, identifiers, `normal_stress`, `shear_stress`,
    `normal_stress_basis`, `secant_friction_angle`).
16. **The summary**, per group: per strength, the main line ("peak, free: c = 8 kPa, φ = 31.0°, R² = 1.000, 3
    points, σn 50 to 200 kPa"), the other line ("through the origin: φ = 33.2°, R² = 0.990"), the rows left out,
    the lab's pairs and the line's notes; then the call's notes, including c as an intercept outside the range.
17. **Units** resolve as SPEC §2.6 (`units=`, then `df.attrs["units"]`, else an error naming the column). The
    columns read are the two shear stresses and the three normal stresses; a column with a value the fit uses
    needs a unit that is a stress, and 🟡 a column that is blank throughout needs none (a template's CSV has every
    column). The fit is made in `peak_shear_stress`'s unit (else `residual_shear_stress`'s), or in
    `display_units=`'s (kPa, psf), converted before fitting; c scales with the unit and φ doesn't change. A frame
    with neither shear stress column, or no normal stress column `normal_stress=` can use, is an error naming them
    and pointing to `ht.template("shear_box")`.
18. **P31, `ht.plot.shear_box_envelope()`** (intent decision 9): its rules are in its spec. It calls
    `shear_box_fit()` with the shared arguments and draws its result, computing nothing of its own; it returns
    `(fig, ax, fit)` like P11.

### Derivation
The criterion (Hoek 2023, ch. 4, eqs. 1–2): τp = c + σn tan φp, and τr = c + σn tan φr (eq. 2 writes the residual
through the origin; the free residual line is fitted too, decision 4). It is a line in τ–σn with intercept a = c
and slope b = tan φ, so the core fits it as given: x = σn, y = τ. Back: **c = a, φ = arctan b**, defined for every
b ≥ 0 (0 ≤ φ < 90°). Least squares minimizes Σ(τ − a − b σn)²: free, b = Sxy / Sxx and a = ȳ − b x̄ (M11 (b),
Derivation 6); through the origin, minimizing Σ(τ − b σn)² over b gives b = Σσnτ / Σσn² (sheet 22 §5.2). The secant
angle of a point is the slope of the line from the origin through it: φsec = arctan(τ / σn).

### Example data
🟡 Proposed values, with site-like scatter about a line (memory: not points on the line); the generator's comments
carry each set's hand fit.
- **`site.ags`, Alluvium (lean clay), small shear box, undisturbed**, two tests on 17.5 ft tubes, σn (`SHBT_NORM`)
  1000, 2000 and 4000 psf:
  - B-3-U3: τp 700, 1130, 2240; τr 430, 760, 1610. The lab's own fits: c 145 psf, φ 27.4°; c 5 psf, φ 21.7°.
  - B-6-U2: τp 610, 1250, 2080; τr 380, 840, 1500. The lab's: c 195 psf, φ 25.6°; c 50 psf, φ 20.2°.
- **`site.ags`, Terrace (sand), small shear box, recompacted**, B-3-D4 (30 ft), σn 1000, 2000, 4000 and 6000 psf:
  τp 760, 1420, 2650, 4120; τr 610, 1180, 2430, 3590. The lab's: c 71 psf, φ 33.7°; c 3 psf, φ 31.0°.
- **`site.ags`, Sandstone, bedding plane joints, encapsulated in resin** (`SHBG_ENCA`), one core sample B-3-C5
  (64.0 ft), two specimens (`SPEC_REF` 1 and 2), `SHBG_TYPE` blank (AGS has no rock joint code, M17 (a)
  decision 9), σn 0.5, 1.0 and 2.0 MPa, written in psf at 10 significant figures (as `site_us.ags`) so the MPa
  values come back to 1e-9:
  - Specimen 1: τp 0.52, 0.86, 1.71; τr 0.33, 0.57, 1.20. The lab's: c 0.095 MPa, φ 38.7°; c 0.015 MPa, φ 30.4°.
  - Specimen 2: τp 0.45, 0.93, 1.62; τr 0.29, 0.62, 1.13 (MPa). The lab's: c 0.105 MPa, φ 37.5°; c 0.035 MPa,
    φ 28.9°.
  - In the file (psf): σn 10442.7171, 20885.4342, 41770.8684; specimen 1's τp 10860.4258, 17961.4734, 35714.0925.

### Sources
- **Hoek (2023):** *Practical Rock Engineering*, ch. 4, eqs. 1–2, the linear peak and residual criterion, and the
  advice to report the free and through-origin fits together. [V] on page 22 (M17 (a)'s wave step).
- **The fit:** least squares on the criterion's line, derived above; no coefficient or table value is used.
- **1 psf** = 0.45359237 × 9.80665 / 0.3048² Pa = 47.880259 Pa, exact by definition (P00 §4).
- 🔬 **The failure criteria** of ASTM D3080 and D6467: TODO #53, as M11 (b). The fit reads `failure_criterion` as
  written and only checks that a line's rows share one.

### Acceptance criteria
Golden values hand-calculated from the Derivation, the sums written out, with the arithmetic done exactly (in
fractions) and rounded to 9 significant figures; tolerance 1e-7 relative unless stated. Points are (σn, τ).
1. **BH2-D1 peak (`site_si.ags`, 3 stages, kPa):** (50, 38), (100, 68), (200, 128); x̄ = 116.666667, ȳ = 78,
   Sxx = 11666.6667, Sxy = 7000. Free: b = 0.6, a = 8, so `peak_cohesion` 8 kPa, `peak_friction_angle`
   30.963757°, R² = 1, the lab's pair (8 kPa, 31.0°) × 3. Through the origin: Σσnτ = 34300, Σσn² = 52500,
   b = 49/75 = 0.653333333, φ = 33.157924°, R² = 1 − 42.6666667/4200 = 0.98984127. Range 50 to 200 kPa. Secant
   angles 37.234834°, 34.215702°, 32.619243°. Basis `"at_peak"` on every point (the file has `SHBT_PVST`).
2. **BH2-D1 residual:** (50, 30), (100, 58), (200, 112); Sxy = 6366.66667, b = 191/350 = 0.545714286, a = 3:
   `residual_cohesion` 3 kPa, `residual_friction_angle` 28.621928°, R² = 0.999917772; the lab's (2 kPa, 28.5°).
   Through the origin: Σσnτ = 29700, b = 99/175 = 0.565714286, φ = 29.497461°, R² = 0.998190988. Basis
   `"at_residual"`.
3. **US twin (`site_us.ags`):** the same φ for all four lines (1e-9 relative), `peak_cohesion` 167.083474 psf and
   `residual_cohesion` 62.6563027 psf (8 and 3 kPa / 0.047880259), from the file's own psf; with
   `display_units="SI"`, 8 and 3 kPa.
4. **`normal_stress="applied"`** on BH2-D1: the same lines (`SHBT_NORM` = `SHBT_PVST` there), basis `"applied"`.
   A hand-built frame whose rows have `normal_stress_at_peak` 52 and 205 on two and blank on the third uses 52,
   100 and 205, with bases `"at_peak"` × 2 and `"applied"` × 1 and the mixed-basis note; `"applied"` uses 50,
   100, 200.
5. **Rock joint set (`site.ags`'s Sandstone, both specimens, shown in MPa with the override of decision 13):** peak (0.5, 0.52), (1, 0.86), (2, 1.71),
   (0.5, 0.45), (1, 0.93), (2, 1.62); x̄ = 1.16666667, ȳ = 1.015, Sxx = 2.33333333, Sxy = 1.83: b = 549/700 =
   0.784285714, a = 0.1 MPa, φ = 38.106583°, R² = 0.993557064; through the origin, Σσnτ = 8.935, Σσn² = 10.5,
   b = 1787/2100 = 0.850952381, φ = 40.396201°, R² = 0.98432697. Residual: Sxy = 1.33, b = 0.57, a = 0.025 MPa,
   φ = 29.683140°, R² = 0.994099135; through the origin Σσnτ = 6.16, b = 44/75, φ = 30.398728°, R² = 0.993006382.
   Without the override, `display_units="SI"` gives c = 100 and 25 kPa and `"US"` 2088.54342 and 522.135856 psf;
   φ the same (1e-9 relative) in all three. With `group_by="specimen_reference"`, specimen 1's peak b = 561/700,
   a = 0.095 MPa, φ = 38.709683°. `group_by="geology_unit"` gives the Sandstone group beside AC 6's two.
6. **`site.ags` soil sets, `group_by="geology_unit"`:**
   - Alluvium, 6 points: peak Sxx = 9333333.33, Sxy = 4660000, b = 699/1400 = 0.499285714, a = 170 psf,
     φ = 26.532301°, R² = 0.989167965; through the origin b = 467/840 = 0.555952381, φ = 29.071975°,
     R² = 0.97278579. Residual Sxy = 3570000, b = 0.3825, a = 27.5 psf, φ = 20.931853°, R² = 0.992243133;
     through the origin b = 47/120, φ = 21.388623°, R² = 0.991510439. Two lab pairs per strength,
     `count_reported_peak_pairs` 2 and the pair columns blank.
   - Terrace, 4 points: peak Sxx = 14750000, Sxy = 9832500, b = 3933/5900 = 0.666610169, a = 71.0169492 psf,
     φ = 33.687826°, R² = 0.998350334; through the origin b = 973/1425, φ = 34.325536°, R² = 0.997555186.
     Residual b = 3539/5900 = 0.599830508, a = 3.05084746 psf, φ = 30.956615°, R² = 0.999722222; through the
     origin b = 1141/1900, φ = 30.985925°, R² = 0.999720407.
   - `display_units="SI"` gives the Alluvium's c 8.13964403 and 1.31670712 kPa.
7. **Ring shear, residual only (`joins.ags`, J1-D2):** one point (0.10, 0.021) MPa. Residual free: no line,
   "1 point: a line needs at least 2"; through the origin b = 0.21, φ = 11.859779°, R² NaN. Peak: both lines
   "no points" / the core's reason, `count_no_peak_shear_stress` 1. The joint test J1-U3 (one peak point
   (0.50, 0.42), no residual): through the origin φ = 40.030259°. The whole of `joins.ags`'s `p.shear_box()` in
   one group fits without a pooling error (J1-U3's blank `test_type` is in the peak lines only, J1-D2's
   `SMALL RSHEAR` in the residual only), and each strength's counts add up to 2.
8. **Validity (hand-built, kPa):** (100, 80), (200, 60) gives free b = −0.2 and no line with the slope reason,
   the through-origin line b = 0.4 with R² = −9 (centered, kept); (100, 20), (200, 80), (300, 140) gives
   a = −40, b = 0.6 and the negative-intercept warning naming the group and "peak", with the through-origin
   b = 3/7, φ = 23.198591°, R² = 0.904761905; two points at σn = 100 give no free line, "same normal stress";
   a point at σn = 0 has `secant_friction_angle` NaN and is fitted; a negative τ or σn raises naming the row; a
   2-point free line has the two-point note.
9. **Pooling:** BH2-D1's rows with a `SMALL RSHEAR` row added to the residuals raise, naming `SMALL SBOX` × 3 and
   `SMALL RSHEAR` × 1 under `test_type`; a blank `failure_criterion` beside "Maximum shear stress" raises;
   `pool=["test_type", "failure_criterion"]` fits them and `.pooled` records it; `pool="geology_unit"` is an
   error listing what `pool=` takes. A frame without `failure_criterion` fits, with the note.
10. **Lines and order:** `cohesion=0` puts `"through_origin"` first in `.to_frame()` and the summary with the same
    values as AC 1–2; `cohesion=5` raises. `.to_frame()` has decision 15's columns in order and `attrs["units"]`;
    `.to_dict()` passes `json.dumps`; `kind` is `"derived"`; `print()` gives decision 16's lines.
11. **Counts add up:** for every group and strength in AC 1–9, `{s}_count` plus the two `count_no_{s}_…` is the
    group's rows.
12. **Units and columns:** a frame without units raises naming the column; a shear stress in a length unit
    raises; a template CSV with blank `normal_stress_at_peak` and no unit for it fits on `applied_normal_stress`;
    a frame with neither shear stress raises, naming `ht.template("shear_box")`; `normal_stress="peak"` and a
    missing `group_by` column raise saying what to do. **MPa input:** a hand-built frame with `attrs["units"]` in
    MPa (AC 5's points) fits in MPa with `display_units=None` (`unit` `"MPa"`, c = 0.1) and in kPa with
    `"SI"`; `joins.ags`'s J1-U3, stored in MPa, gives AC 7's φ.
13. **Not used:** `multistage_test`, when present, changes nothing (decision 12).
14. **The plot:** P31's §12 criteria.
15. **Reference:** `shear_box_fit`, `ShearBoxFit` and `shear_box_envelope` in the API reference (the test that
    fails without an entry), with the docstring checklist of the sheets' `TEMPLATE.md`.

## Plan
Draft, 2026-11-04. Seven commits, each green: the tests it touches, then the CI command with `-n 3`. Steps 1–3
on Opus (the calculation, its validity limits and docstring), 4–6 on Sonnet (data, plot drawing and docs site, with
the spec's values and P31's criteria deciding correctness), 7 on Opus (the figure judged against P31, close-out):
two session boundaries, after 3 and after 6. A step past about 300 changed lines without test data splits as noted.
Reused, not rebuilt:
- **Fit:** `line_fit()` (`analysis/_line_fit.py`), free and with `intercept=0`, and its `no_fit_reason`s;
  `_DerivedResult` (`analysis/_derived.py`); `group_keys()`, `breakdown()` (`stats/_rows.py`); `_plain()`
  (`stats/_result.py`); `format_number()` (`plot/_overlays.py`).
- **Units:** `resolve_units`, `parse_unit`, `check_dimension`, `convert`, `to_display` (`hangtu.units`), as
  `_mohr_coulomb.py`'s `_stresses()` and `_reported()` use them; `numeric_column`, `rows_text` (`_data`);
  `ColumnError`, `HangtuError`, `warn` (`errors`).
- **Data:** `STAGE_NUMBERS` and the column list of `datasets/_shear_box.py`, for the columns read and the template.
- **Plotting:** `plot/_envelope_drawing.py` (P11's solid-in-range, dashed-beyond line and the result box) where it
  fits, and `style.context`/`style_axes`, `figure_size`, `axis_label`, `add_legend`, `Notes`, `hint_missing`,
  `nice_limits`, `resolve_palette`, as `plot/_failure_envelope.py` uses them.

### 1. `M17: move the fit helpers mohr_coulomb_fit() shares to a module` (Opus)
Refactor only (spec decision 14), no change in behavior.
- `src/hangtu/analysis/_fit_groups.py` (new): `_names`, `_label`, `_cell`, the pooling check (`_check_sources`,
  taking the function's name for its message instead of the module's `_FUNCTION`) and the lab-pair collection
  (`_pairs`, `_same`). `_reported()` gains the two column names as arguments so the shear box fit can read its
  `reported_peak_…`/`reported_residual_…` pairs through it, and moves too.
- `src/hangtu/analysis/_mohr_coulomb.py`: imports them; nothing else changes.
- Tests: `tests/analysis/test_mohr_coulomb_fit.py` and `tests/plot/test_failure_envelope*.py` unchanged and green.

### 2. `M17: add shear_box_fit() for one group` (Opus)
- `columns.yaml`: `peak_cohesion`, `residual_cohesion` (stress), `peak_friction_angle`,
  `residual_friction_angle` (angle), ratio scale, labels "Peak cohesion, c_p", "Peak friction angle, φ_p",
  "Residual cohesion, c_r", "Residual friction angle, φ_r", `ags: ["derived: docs/work/m17b-shear-box-fit.md"]`,
  `used_by: [P31]` (decision 2). `tests/test_registry.py` stays green.
- `src/hangtu/analysis/_shear_box_fit.py` (new), exported with `ShearBoxFit` in `analysis/__init__.py`:
  - arguments as decision 1; `cohesion=` other than None or 0 and `normal_stress=` other than its two values are
    errors (decisions 4, 5);
  - units (decision 17): the shear and normal stress columns with a value the fit uses resolved and checked as
    stresses, a column blank throughout skipped, converted to the fit's unit before fitting; the missing-columns
    error naming `ht.template("shear_box")`;
  - per strength: each point's σn and `normal_stress_basis` (decision 5), the mixed-basis note; rows left out and
    counted under the first reason (decision 7); the negative-stress error (decision 8);
  - four lines through `line_fit()`, c = a, φ = arctan b (Derivation), and decision 8's validity: the core's
    reasons, the slope reason, the negative-intercept warning (one per call), the two-point note, the σn range;
  - the secant angle per point (decision 9);
  - `ShearBoxFit(_DerivedResult)`: `.groups`, `.to_frame()` with decision 15's columns in order and
    `attrs["units"]`, `__str__` as decision 16, `.to_dict()`;
  - docstring per the sheets' `TEMPLATE.md` checklist: τ = c + σn tan φ (Hoek 2023, ch. 4, eqs. 1–2), the two
    least-squares slopes, inputs and outputs with units, validity, the basis rule, the derived-not-cited note
    pointing to this spec, the naming rule (decision 2), an example on `p.shear_box()`.
- `docs/site/reference/analysis.md`: `shear_box_fit` and `ShearBoxFit` (AC 15).
- Tests: `tests/analysis/test_shear_box_fit.py` (new), with `site_si.ags` and `site_us.ags` loaded through
  `Project.from_ags` as `tests/plot/test_failure_envelope_acceptance.py` does: AC 1–4, 8, 10, 12 (units, columns,
  MPa input on a hand-built frame and `joins.ags`'s J1-U3), and AC 11 for those.
- If past about 300 lines: (2a) the lines and validity on hand-built frames and BH2-D1 (AC 1–3, 8), then (2b)
  bases, units and errors (AC 4, 12).

### 3. `M17: fit shear box groups, check pooling, list the lab's pairs` (Opus)
- `_shear_box_fit.py`: `group_by=` (decision 10), the pooling check per strength with `pool=` and its notes
  (decision 6), the lab's pairs per strength through `_fit_groups` converted to the fit's unit (decision 11),
  `cohesion=` choosing the main line's order (decision 4); `multistage_test` not read (decision 12).
- Tests, same file: AC 7 (`joins.ags`'s ring shear and joint tests, one group without a pooling error), 9, 10
  (`cohesion=0`), 11 for those, 13.

### 4. `M17: add sandstone and shear box tests to the example project` (Sonnet)
- `tests/data/_make_examples.py` (decision 13 and "Example data"):
  - `ROCK = {"B-3": (71.5, "SST")}`: B-3's soil base stays `HOLES`' 61.5 ft, so `ispt()`, `samples()` and every
    seeded value keep their sequence; `loca()` writes the rock's base as `LOCA_FDEP`, `geol()` adds the `SST` layer
    from 61.5 to 71.5 ft; `DESCRIPTIONS` gains `SST` ("Sandstone", a gray fine-grained sandstone description).
  - `CORE_SAMPLES = [("B-3", 64.0, 65.0, "C", "5")]`, apart from `samples()` as `TRIAXIAL_SAMPLES` is, written to
    `SAMP`; `ABBR` gains `SAMP_TYPE` `C` (core) and the `SHBG_TYPE` code the soil tests use (`SMALL SBOX`).
  - `shbg()` and `shbt()`: B-3-U3 and B-6-U2 (Alluvium, undisturbed), B-3-D4 (Terrace, recompacted), B-3-C5
    specimens 1 and 2 (Sandstone, `SHBG_ENCA` resin, `SHBG_TYPE` blank), the stage values and the lab's pairs of
    "Example data", stresses in psf (the joint set's at 10 significant figures from MPa × 1e6 / 47.880259), each
    set's hand fit in a comment beside it. `site_groups()` appends them after the undrained groups, so no existing
    line moves.
- `src/hangtu/examples/data/strata.csv` (through `STRATA` in the generator): `SST,Sandstone,rock,4,<color>`;
  `judgments.yaml`: Sandstone `bulk_unit_weight: 150`, with its reason (B-3's water level is above it, and
  `vertical_stress()` uses the bulk weight where no saturated one is given).
- Regenerate `src/hangtu/examples/data/site.ags`. A one-off script (not committed) compares every group but `LOCA`,
  `GEOL`, `SAMP`, `UNIT`, `TYPE`, `ABBR` and the new two with `HEAD`'s file, and checks those six differ only by the
  rows above. `tests/test_examples.py`'s python-ags4 check, its QC findings and the generator check stay green; a
  new QC finding is a data mistake to fix, not an expected finding to add.
- Tests, in `tests/analysis/test_shear_box_fit.py`: AC 5 (the Sandstone set, with and without the MPa override,
  per specimen) and 6 (the soil sets by geology unit, and in SI), and AC 11 for them. Other tests on `site.ags`
  (`tests/test_project.py`, the plot acceptance tests, `tests/stats/conftest.py`) are checked for group and unit
  counts and stay green.

### 5. `M17: add ht.plot.shear_box_envelope() (P31)` (Sonnet)
- `src/hangtu/plot/_shear_box_envelope.py` (new), exported in `plot/__init__.py`, as P31 §10: calls
  `shear_box_fit()` with the shared arguments and draws its result: filled peak and open residual points at their
  basis's σn, the main line solid over the fitted range and dashed beyond, the other kind lighter, `strengths=`,
  the user envelopes, the result box (c, φ, n, R², the lab's pair or count), the footnote, equal aspect and P31 §6's
  limits; `color_by=` as P31 §10; returns `(fig, ax, fit)`, `fit=False` returns None.
- `docs/site/reference/plot.md`: `shear_box_envelope`.
- Tests: `tests/plot/test_shear_box_envelope.py` (new), P31 AC 1–4, 6, 7 and 9 read from the drawn artists (line
  intercepts, slopes and solid/dashed extents, marker fill, `ax.get_aspect()`);
  `tests/plot/test_shear_box_envelope_acceptance.py` (new), AC 5 and 8 on the example project and the twin files.
- If past about 300 lines: (5a) points, lines, limits and returns (AC 1–4, 7), then (5b) groups, strengths, units,
  the box and edge cases (AC 5, 6, 8, 9).

### 6. `M17: draw the shear box tests on the docs site` (Sonnet)
- `docs/site/examples/shear-box-envelope.py` (new): the example project's soil sets by geology unit, US units.
  `docs/site/plots/shear-box-envelope.md` (new): what it shows, the two line kinds, the fitted range, the basis of
  σn, the lab's values, common options; linked in `zensical.toml`'s `nav` and `docs/site/plots/index.md`.
- `docs/site/parameters/22-discontinuity-shear-strength.md`: the two "M17 (b)" method rows link `shear_box_fit()`;
  its example fits and draws the Sandstone joints inside the MPa override (decision 13).
  `docs/site/parameters/04-drained-shear-strength-soil.md`: the row "Least-squares fit of shear box results"
  linking it, beside the Kulhawy & Mayne row, which stays M18's.
- `docs/site/guides/datasets.md`: `p.shear_box()`'s row points to P31.
- Run `docs/prepare_site.py` and `zensical build --clean --strict`.

### 7. `M17: close out (b)` (Opus)
- **Visual check:** `docs/plots/img/P31-us.png` (the example's soil sets by geology unit, psf) and `P31-si.png`
  (the Sandstone joints, MPa), 100 dpi, looked at against P31, committed. Every site example grouped by geology
  unit rerun and its figure looked at for the fourth unit (decision 13).
- **Close-out:**
  - `docs/plots/P31-shear-box-envelope.md` status `built` with its images; `docs/plots/README.md` P31 `built`;
  - SPEC §4: the envelope fits bullet gains the shear box fit; §12.4 M17 "(a), (b) done; (c) next";
  - the parameter index: 04 B built (the shear box half), 22 B built;
  - the `CLAUDE.md` "Next" sentence (M17 (c));
  - TODO #53's text checked against what was built (it stays open);
  - TODO #3 gains a question: whether `soil_class` is renamed (`material_class` or `ground_class`) now the example
    site has a rock unit and the draft list already has `fill`, with the old header read through a deprecation
    period (0.1.0 is on PyPI). Decided with the categories, as a unit of its own; M17 (b) writes `rock` under the
    current name;
  - what a future session would get wrong without being told, written where it will be read.
- **Verification:** every AC of the Spec and of P31 §12 reported as met or not, with its test; the whole suite with
  `-n 3`; ruff; mypy; the lowest-versions run (then `git checkout uv.lock`); the strict docs build.
