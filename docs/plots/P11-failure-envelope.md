# P11 — Failure envelope: Mohr circles, s′–t or p′–q

| | |
|---|---|
| **ID / function** | P11 · `ht.plot.failure_envelope()` (+ `ht.analysis.mohr_coulomb_fit()`) |
| **Status** | draft (M11 (b) spec, 2026-10-31) |
| **Type** | plot + analysis |
| **Milestone** | M11 (b) (SPEC §12.4), [`docs/work/m11b-envelope-fit.md`](../work/m11b-envelope-fit.md) |
| **Depends on** | P00; `p.triaxial()` and `ht.analysis.triaxial_failure_stresses()` (M11 a); `mohr_coulomb_fit()` (M11 (b) Spec) |
| **Related** | P12 (M11 (c), reuses the fit), P26 and P27 (drafts: fitted c′, φ′ against correlations and published values); sheet 04; TODO #53 |

---

## 1. Purpose
Draws the failure state of a set of triaxial stages (one sample's, or all of a geology unit's) with the fitted
Mohr–Coulomb envelope, and states c′ and φ′. Answers: what strength parameters do these tests support, over what
stress range, how well does one line fit them, and how does the fit compare with the lab's. Used in lab data
reports, calculation packages and to justify design strength.

One function draws the same failure points and the same fit in any of three spaces, chosen with `space=`:
- `"mohr"`: Mohr circles in σ′–τ, with the envelope τ = c′ + σ′ tan φ′.
- `"s_t"`: failure points in MIT s′–t, with the line t = a + s′ tan α.
- `"p_q"`: failure points in Cambridge p′–q, with the same envelope transformed.

The views differ in interpretation, not in data, so they share one input table, one fit, one set of overlays and
one set of edge cases. Stress–strain curves and paths measured during shearing need readings at each strain step,
which AGS doesn't carry; they are P12 (M11 (c)).

**Idealized drained paths.** In s′–t and p′–q, `paths="idealized_drained"` draws each stage's path as a drained
compression test at constant cell pressure would have taken it: from (σ′3, 0) to the failure point. It isn't the
measured path and is labeled as such.

## 2. Reference figure
`space="mohr"`:
```
  τ (kPa)
  300 ┤                                  ┌──────────────────────────┐
      │                       ___------  │ c′ = 35.4 kPa, φ′ = 19.5° │
  200 ┤            ___-----‾‾‾  ╭──╮     │ n = 2, R² = 1.000         │
      │   ___---‾‾‾    ╭──╮  ╱    ╲     │ σ′n 167–300 kPa           │
  100 ┤-‾‾      ╭──╮ ╱    ╲╱       ╲    └──────────────────────────┘
      │ - - - ╱    ╲╱      ╲        ╲   (dashed outside the fitted range)
    0 ┼──────┴──────┴───────┴────────┴──────────────
      0     100    200     300      400    500   σ′ (kPa)
```

`space="s_t", paths="idealized_drained"`:
```
   t (kPa)
  200 ┤                      ● ← failure
      │                  ╱  ·
  100 ┤           ●   ╱ ·· ← fitted line
      │       ╱  ·  ╱
      │   ╱ ··   ╱ ← idealized drained path (dashed)
    0 ┼╱────────╱──────────────
      0   100  200  300  400   s′ (kPa)
```
**A good version:** equal aspect, so circles are circles and slopes read true; upper half only; the envelope solid
over the stress range the points support and dashed beyond it; the fit's numbers in a box, beside the lab's.

## 3. Input data
**Row grain:** one row per stage at failure, as `p.triaxial()` returns, or a CSV in `ht.template("triaxial")`'s
shape passed through `ht.analysis.triaxial_failure_stresses()`.

| Column | Description | Quantity kind | Req.? | Notes |
|---|---|---|---|---|
| `effective_minor_principal_stress_at_failure` | σ′3f | stress | ✔ (`stress="effective"`) | from `triaxial_failure_stresses()` |
| `effective_major_principal_stress_at_failure` | σ′1f | stress | ✔ (`stress="effective"`) | |
| `minor_principal_stress_at_failure`, `major_principal_stress_at_failure` | σ3f, σ1f | stress | ✔ (`stress="total"`) | |
| `failure_criterion` | the lab's criterion, as written | text | – | not pooled unawares (§4) |
| `multistage_test` | the stage is one of a multistage test | bool | – | fitted with and without (§4) |
| `test_type` | AGS type code | text | – | `paths=` checks it; not pooled unawares in total stress |
| `reported_effective_friction_angle`, `reported_effective_cohesion` | the lab's fit | angle, stress | – | shown beside hangtu's |
| `specimen_id`, `test_stage` | names a point in messages | text | – | else the row's index |
| `geology_unit` | color, and a common `group_by=` | text | – | |

A frame without the principal stresses (a CSV straight from the template) is an error that says to call
`ht.analysis.triaxial_failure_stresses()` first. The plot never computes σ′ itself (SPEC §4).

**Grouping columns used:** `group_by=` (one fit and one color per group); `color_by=` (circles and points only).

**Value flags handled:** none on the stresses. Rows without the stresses the fit needs are left out and counted in
the footnote (§4).

**Minimum data:** 1 row to draw; 2 points per group to fit, or 1 with `cohesion=0`.

## 4. Analysis / calculations
`ht.analysis.mohr_coulomb_fit()` (M11 (b) Spec, decisions 3–13; the derivations and golden values are there).
The plot calls it with the shared arguments and draws its result; it computes nothing of its own apart from each
space's coordinates and the idealized paths.

**The fit is done in s′–t; the other spaces draw it transformed**, never refitted (with more than two points, a
regression in p′–q gives a different c′ and φ′):

| Space | Points | Envelope | Intercept on the y axis |
|---|---|---|---|
| `mohr` | circle center (s′, 0), radius t | τ = c′ + σ′ tan φ′ | c′ |
| `s_t` | (s′, t) | t = a + s′ tan α | a = c′ cos φ′ |
| `p_q` | p′ = (σ′1 + 2σ′3)/3, q = σ′1 − σ′3 | q = q₀ + M p′, M = 6 sin φ′ / (3 − sin φ′) | q₀ = 6 c′ cos φ′ / (3 − sin φ′) |

The p′–q line is for triaxial compression; extension has a different M (§15).

**Fitted range.** The envelope is solid between the lowest and highest tangent points of the fit (the result's
`lowest_normal_stress` and `highest_normal_stress`, mapped into each space: (σ′n, τ) in `mohr`, (s′, t̂) in `s_t`,
(s′ − t̂/3, 2t̂) in `p_q`, with t̂ the fitted t at the point's s′), and dashed from there to the axes' edges. c′ is
an intercept, read off the dashed part unless a point sits near σ′ = 0.

**Idealized drained path** (`paths="idealized_drained"`): σ′3 constant, σ′1 rising from σ′3, so from (σ′3, 0) with
slope 1 in s′–t (s′ and t grow by the same amount) and slope 3 in p′–q (p′ grows by Δσ′1/3, q by Δσ′1).

## 5. Figure layout
- **Panels:** one.
- **Default size:** the `default` kind (6.5 × 4.5 in). Equal aspect makes the y range about half the x range in
  `mohr`.
- **Legend:** README's rule. The result box takes the upper-left corner in `mohr` and `s_t` (the envelope climbs
  to the right, so the left is clear above it), the legend the first clear corner of the rest.

Two spaces side by side is the engineer's own layout: make the axes, call twice with `ax=`. A built-in two-panel
option is §15.

## 6. Axes
| Space | X axis | Y axis |
|---|---|---|
| `mohr` | `Effective normal stress, σ′ (kPa)` | `Shear stress, τ (kPa)` |
| `s_t` | `Mean effective stress, s′ (kPa)` | `Shear stress, t (kPa)` |
| `p_q` | `Mean effective stress, p′ (kPa)` | `Deviator stress, q (kPa)` |

- With `stress="total"` the primes and "effective" are dropped (`Normal stress, σ (kPa)`, `Mean stress, s (kPa)`).
- t is half the deviator stress, so it is labeled a shear stress, not a deviator stress (*changed from the draft*,
  which labeled both t and q "deviator stress").
- **Limits:** x from 0 (or a nice number below the lowest σ′3 if one is negative) to a nice number above the
  largest σ′1 (`mohr`), s′ (`s_t`) or p′ (`p_q`); y from 0 to the height equal aspect gives, at least a nice number
  above the largest τ, t or q.
- US labels use psf, or ksf with `ht.settings.display_overrides = {"stress": "ksf"}`, as P01 (*changed in the
  build*: P01 doesn't switch to ksf by itself, so neither does P11).
- Equal aspect leaves one axis short of the space the axes have; that axis is extended to fill it (*settled in the
  build*), which also gives the result box room above the envelope.

**Range constraints:** [x] equal aspect in all three spaces. Required for Mohr circles (README); required in s′–t
and p′–q too, so slopes (1 in s′–t, 3 in p′–q for the drained path, M) read true and figures are comparable.

## 7. Data marks
| Series | Mark | Color | Legend |
|---|---|---|---|
| Circles (`mohr`) | upper semicircle, no fill | by group, else `color_by` | one entry per color |
| Failure points | dot; in `mohr` at the top of the circle (s′, t) | as circles | — |
| Idealized paths (`s_t`, `p_q`) | thin dashed line per stage | as points | "Idealized drained path" (or "… (assumed CD)") |
| Envelope | line, solid over the fitted range, dashed beyond | black with one group; the group's color with several | "Fit" or "Fit, <group>" |
| Envelope without multistage stages | dotted line, same color | | "Fit without multistage stages" (only when it differs) |
| User envelopes | gray line | — | the label given |

**Draw order:** circles or paths → points → user envelopes → fits → box.

## 8. Overlays and annotations
| Overlay | Argument | Default | Notes |
|---|---|---|---|
| Fit envelope | `fit=` | `True` | `False` draws the points or circles only, and the result is None |
| Result box | `result_box=` | on with the fit | per group: c′, φ′, n, R², the σ′n range; then the lab's values where the rows have them, "Lab: c′ = 5 kPa, φ′ = 27.0° (3 stages)"; a group with no fit says why |
| Fit without multistage stages | `multistage=` | `True`: drawn dotted when the group has multistage stages | `False` makes the fit without them the main one, and the dotted line the fit with them |
| User envelopes | `envelopes=` list of `(cohesion, friction_angle, label)` | off | cohesion in the display units, φ in degrees; transformed into each space like the fit |
| Idealized paths | `paths=` | `None` | `"idealized_drained"` in `s_t` and `p_q` only |
| Footnote | — | when anything is left out | the result's counts: "Left out: 2 without effective stresses (UU), 1 extension stage" |
| `note` | as README | off | |

## 9. Units behavior
Stresses convert (kPa ↔ psf or ksf); φ′ in degrees in both; c′, a and q₀ in the display units. The fit is made in
the display units (`mohr_coulomb_fit(display_units=...)`), so the box, the axes and the result agree. US and SI
figures differ only in labels and in values scaled by the conversion; φ′ is the same.

## 10. API
```python
def failure_envelope(
    df: pd.DataFrame,
    *,
    space: Literal["mohr", "s_t", "p_q"] = "mohr",
    stress: Literal["effective", "total"] = "effective",
    group_by: str | list[str] | None = None,
    color_by: str | None = None,
    cohesion: float | None = None,
    multistage: bool = True,
    pool: str | list[str] | None = None,
    fit: bool = True,
    paths: Literal["idealized_drained"] | None = None,
    result_box: bool = True,
    envelopes: list[tuple[float, float, str]] | None = None,
    note: str | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides,
) -> tuple[Figure, Axes, MohrCoulombFit | None]:
```
- `stress=`, `group_by=`, `cohesion=`, `multistage=`, `pool=`, `units=` and `display_units=` go to
  `mohr_coulomb_fit()` as they are.
- `color_by=` colors circles and points when there's no `group_by=`. Its default is `geology_unit` when the rows
  have it, else one color. With `group_by=`, color is by group and `color_by=` is an error (one color per fit).

**Examples:**
```python
fig, ax, fit = ht.plot.failure_envelope(p.triaxial(where={"test_type": "CU"}))
fig, ax, fit = ht.plot.failure_envelope(p.triaxial(), space="s_t", group_by="geology_unit")
fig, ax, fit = ht.plot.failure_envelope(p.triaxial(geology=["TRC"]), space="p_q", paths="idealized_drained")
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| No principal stress columns | Error: call `ht.analysis.triaxial_failure_stresses()` first |
| σ′1 < σ′3 on a row | Error naming the rows (the fit's) |
| Negative σ′3 | Drawn; the fit's warning (tension); x axis extends below 0 |
| One point in a group | Drawn; no fit unless `cohesion=0`; the box says "no fit: 1 point (2 needed, or cohesion=0)" |
| A group with no fit among several | Its circles drawn, no envelope, its line in the box says why; the others are fitted |
| Slope outside 0 ≤ tan α < 1 | No envelope for the group; the box gives the reason (the fit's) |
| Negative intercept | Envelope drawn as fitted, the fit's warning, "c′ < 0" in the box; never forced to 0 |
| Mixed failure criteria, or (total) test types | The fit's error naming each value and count; `pool=` draws them as one fit |
| `paths="idealized_drained"` and a row's `test_type` isn't drained (`CD`, `CDM`, `CIDC`, `CADC`) | Error naming the types: the path is for drained tests at constant cell pressure and would mislead |
| `paths="idealized_drained"`, `test_type` blank or missing | Drawn, labeled "Idealized drained path (assumed CD)" |
| `paths=` with `space="mohr"` | Error: paths are drawn in s′–t or p′–q |
| `group_by=` column missing | The fit's error naming it |
| `color_by=` with `group_by=` | Error (§10) |
| Missing units | The fit's error naming the column (the box needs the unit), as P08 |
| Optional columns missing (`failure_criterion`, `multistage_test`, `geology_unit`) | One hint listing them and what each adds |

## 12. Acceptance criteria and tests
Golden values are the M11 (b) Spec's (AC 1–8), hand-calculated there. Tolerance 1e-9 relative on drawn data
unless stated.
1. **Mohr:** golden 1 (σ′3 = 100, σ′1 = 300 and 200, 500 kPa): circles centered at 200 and 350 with radii 100 and
   150; the envelope line crosses σ′ = 0 at τ = c′ = 35.35534 kPa with slope tan φ′ = 0.3535534; its distance from
   each center equals the radius; solid from σ′n = 166.6667 to 300 kPa, dashed beyond.
2. **The intercept depends on the space** (same data, read from the drawn lines): `s_t` crosses t at
   a = 33.33333 with slope 1/3; `p_q` crosses q at q₀ = 75 with M = 0.75, and (166.6667, 200) and (300, 300) lie on
   it.
3. **Through the origin:** golden 2 (100, 300 and 200, 600 kPa) draws φ′ = 30°, c′ = 0, M = 1.2, q₀ = 0, with and
   without `cohesion=0`.
4. **Idealized path** of σ′3 = 100, σ′1 = 300: (100, 0) to (200, 100) in s′–t; (100, 0) to (166.6667, 200) in
   p′–q. A `CU` row with `paths=` raises; a blank `test_type` draws the "(assumed CD)" label.
5. **Equal aspect** on the rendered axes in all three spaces (`ax.get_aspect() == 1`), and the limits of §6.
6. **Groups and multistage (test files):** `p.triaxial()` of `site_si.ags` with `stress="effective"` draws one fit
   of the six effective-stress stages (the spec's AC 5) and a dotted fit of the three single-stage ones; the box
   has both, the lab's values (two pairs) and a footnote "Left out: 3 without effective stresses". With
   `group_by="test_type"`, two envelopes in two colors.
7. **Returns:** `(fig, ax, fit)` with `fit` equal to `mohr_coulomb_fit()` on the same rows and arguments;
   `fit=False` returns None and draws no line; `ax=` draws into the given axes without a new figure.
8. **Units:** `display_units="US"` and `"SI"` on the twin files give the same φ′, c′ scaled by 47.880259 Pa/psf
   (1e-9 relative), and labels in psf and kPa.
9. **Edge cases:** each row of §11 that raises raises, with its message naming what §11 says; each that draws,
   draws (a hand-built frame per case).
10. **Visual check:** `docs/plots/img/P11-us.png` and `P11-si.png` at 100 dpi, the example project's triaxial
    stages in `mohr` (US) and `s_t` with idealized paths (SI), looked at and committed in the close-out.

## 13. References
The constructions are derived in the M11 (b) Spec (decision 2), not cited. ASTM D4767 (CU), D7181 (CD) and D2850
(UU) define the tests and failure criteria (TODO #53).

## 14. Open questions
- None; the choices are the M11 (b) Spec's, for review with it.

**Pitfalls:**
- Computing c′ as a / cos α, using α where φ′ belongs. Golden 1 catches it (35.36, not 35.14).
- Drawing a (the s′–t intercept) as c′, or c′ on the s′–t axis. AC 2 catches it.
- Refitting in p′–q instead of transforming the s′–t fit.
- Drawing idealized paths without saying so, or for undrained tests.
- Forcing the line through the origin whenever the intercept comes out negative, without saying so.
- Rounding c′ and φ′ inside the analysis; round only for display.
- Drawing the envelope solid across the whole plot, which reads as if c′ were measured at σ′ = 0.

## 15. Future enhancements
- Two-panel layout (Mohr and s′–t sharing one fit), and `MohrCoulombFit.plot()` to draw a result without refitting
  (as `FitResult.plot()`).
- Extension tests (negative q, M for extension).
- Curved (power-law) envelopes; peak and critical-state envelopes together.
