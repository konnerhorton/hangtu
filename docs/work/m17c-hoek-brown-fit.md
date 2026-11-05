# M17 (c): the intact Hoek–Brown fit

## Intent
This is M17's third and last unit (SPEC §12.4; M17 (a) decision 1 made the split). It fits σci and mi of the
intact Hoek–Brown criterion to rock triaxial and unconfined compression results, both free and with σci fixed, read
from a CSV in the `triaxial` template's shape. It runs on M11 (b)'s line-fit core. It is stage B of sheet 15 and the CSV
half of 15's stage A. It closes wave 2's fits before selection's M18 (d).

**Goal:**
- `ht.analysis.hoek_brown_fit(df, group_by=...)` on `triaxial_failure_stresses()`'s rows, from a CSV in
  `ht.template("triaxial")`'s shape (with `failure_mode` added): for each group, σci and mi from the free fit and from the fit with σci fixed. Each fit has n, R², the σ3 range fitted,
  the points fitted, the points left out with their reasons, and the per-specimen mi beside the points.
- A figure of σ1 against σ3 with the fitted curves. The example project gets a rock triaxial set drawn on page 15,
  which this unit promotes from its sheet (the wave rule, `docs/reference/process.md`).

**Why:**
- **Sheet 15 has nothing built.** The parameter index has 15 A and B in wave 2, but no dataset or fit exists, so
  rock in the example project stops at the shear box joints (M17 b).
- **M18 (d) needs it.** Selection compares sources and records model-set results. It should be designed against
  every wave 2 fit, not only the soil ones. The generalized Hoek–Brown set itself waits for wave 4 (M22), which
  builds on σci and mi.
- **The core already fits it.** Hoek's regression is a straight line: x = σ3, y = (σ1 − σ3)², slope b = mi σci and
  intercept a = σci². With σci fixed, the intercept is fixed at σci², and `line_fit(..., intercept=σci²)` gives
  sheet 15 §5.3's mi = Σx(y − σci²) / (σci Σx²) as b / σci. Neither fit needs new least-squares code. SPEC §4
  (envelope fits) already names this fit as "a thin function on the same core".

**Evidence:**
- **The criterion and regression** (sheet 15, [V]): σ1 = σ3 + σci (mi σ3/σci + 1)^0.5 (Hoek 2007, ch. 11, eq. 5,
  p. 2); the linear regression for σci² and mi (eqs. 6–8, p. 4); and r² (eq. 9, p. 4), with "good data" above 0.9.
  The spec re-reads these pages before writing golden values.
- **Validity** (sheet 15 §4, §5.2, §7): 0 < σ3 < 0.5 σci; at least five well-spaced points; shear failures only.
  Specimens that split axially or fail along a defect are removed first (Hoek 2023, ch. 3, p. 6 [V]). UCS tests
  enter as σ3 = 0.
- **No AGS 4.2 group for rock triaxial** (sheet 15 §4, checked). Some files put rock tests in `TRIG`/`TRIT` in kPa
  or in a user-defined group. User-defined groups are wave 0 (M16, TODO #31). A CSV is therefore the only input this
  unit can rely on (M17 (a) decision 1), until M16 reads the group into the same shape.
- **`triaxial_failure_stresses()` already handles a rock row.** It gives total σ3 and σ1 for every stage and leaves
  the effective stresses blank when there is no pore pressure or back pressure (as for `UU`), which is the case for
  a rock test with no pore pressure. Nothing in it is specific to soil.
- **Per-specimen mi is ill-conditioned** at small σ3/σci (sheet 15 §5.4, computed example). A 5 % error in σ1 gives
  mi = 19.2 at σ3 = 0.5 MPa against the true 8.
- **Multistage stages bias mi low** (sheet 15 §5.6, [U]): fit with and without them.
- **`unconfined_compressive_strength` is soil q_u** in the registry (M17 a). Rock UCS (σci, `RUCS`) has no name yet
  (wave 4, M21).

**Scope:**
- **`hoek_brown_fit()`** and its result (`HoekBrownFit`, a `_DerivedResult`), with reference entries. Its
  arguments are `group_by=`, `pool=`, `units=` and `display_units=`, as in `shear_box_fit()`, plus the fixed σci
  (decision 3) and the failure modes to fit (decision 4).
- **The `triaxial` template** (decision 1) gains `failure_mode` as written and the lab's own σci and mi as
  `reported_`. A rock specimen is one row, as a soil stage is: cell pressure and deviator stress at failure, with a
  UCS test as a row with a cell pressure of 0. The CSV is read with `ht.read_csv(..., units=...)`.
- **Registry:** the template's columns and the fitted names (decision 6).
- **The figure** (decision 8): its spec is promoted to `docs/plots/`, then built, with a PNG in `docs/plots/img/`,
  a site page and a reference entry.
- **Example data:** a CSV of a sandstone set in MPa (the unit M17 (a) added), with UCS and triaxial rows, one
  splitting failure and one multistage specimen. The values are hand-worked in the generator's comments, with
  site-like scatter.
- **Docs site:** page 15 promoted; the parameter index's 15 A (CSV) and 15 B.

**Constraints:**
- **SPEC §5, derived results:** `kind = "derived"`, the points fitted and those left out with reasons, counts that
  add up, and the same views as `ShearBoxFit` (`.to_frame()`, `.to_dict()`, the summary).
- **SPEC §4, envelope fits:** a group that can't give a parameter gets a reason, not an error. Nothing is fixed
  unless asked. **SPEC §4, judgments have no defaults:** a fixed σci comes from an argument or the judgments file,
  never from a rule that picks one (decision 3).
- **SPEC §2.6:** units resolve explicit → `attrs` → error, and none is guessed. mi is dimensionless only if σ1, σ3
  and σci share a unit, so the function converts them to one unit first.
- **SPEC §2.6 (templates):** a template is its dataset's columns. Rock rows in `TRIT` reach `p.triaxial()` in this
  shape today, and M16's user-defined groups and M21's `RUCS` must produce it too. One test has one shape.
- **The fit is derived, not cited** (as in M11 (b) decision 2 and M17 (b)). It is least squares on Hoek's line, and
  Hoek (2007) eqs. 5–8 is the citation for both the criterion and the regression.

### Decisions (intent review, 2026-11-05)
Accepted as proposed, with decision 1 revised in the review (one triaxial template for soil and rock).

1. **One triaxial template and one stress function for soil and rock** (revised in review, 2026-11-05). A triaxial
   test is the same test whatever the material: σ3 is the cell pressure and σ1 = σ3 + q_f. Some files already put
   rock tests in `TRIT`, which reach `p.triaxial()` in this shape, and M16 will read user-defined groups into it.
   `ht.template("triaxial")` therefore gains `failure_mode` (and the `reported_` σci and mi), and
   `triaxial_failure_stresses()` is unchanged. A UCS test is a row with a cell pressure of 0. A separate
   `rock_triaxial` template was rejected: one test would have two shapes, and M16 would have to choose between them.
   Rock rows leaving the soil-only columns blank costs nothing. Whether `mohr_coulomb_fit()` suits rock is the
   engineer's choice, made with `where=` or `geology=`. The spec checks whether a lab reporting σ1 rather than the
   deviator needs a column or a note on the page.
2. **UCS rows are points at σ3 = 0 in the same fit**, as Hoek's regression treats them (sheet 15 §5.2). They are
   not a separate dataset. Their `test_type` keeps them distinguishable, and the "not pooled unawares" check doesn't
   count unconfined against triaxial as two test types, because the method combines them by design.
3. **Both fits, always where possible.** The free fit is always made. The fixed fit is made when σci is given
   with `intact_compressive_strength=` (🟡 name), as a value or a per-group mapping, or in the judgments file. When
   neither gives σci, the fixed fit is missing with a reason naming both places. Taking the group's UCS mean or
   median automatically (sheet 15 §5.3, "e.g. to the UCS median") was rejected: which statistic to use, and whether
   the UCS tests represent the group, is a judgment (SPEC §4). The summary prints the group's UCS mean and count
   beside the free σci, so the engineer sees the check in sheet 15 §7.
4. **Failure modes are as written; the engineer names the ones to fit.** `failure_mode` is free text from the
   lab, so hangtu doesn't guess which values mean "shear" (SPEC §2.6). Proposed: `failure_modes=` is required
   whenever the column has values, and rows with other modes are left out and counted by mode. When the column is
   blank, all rows are fitted and the summary notes that no mode was given. The spec weighs this against a
   registry list of recognized codes.
5. **Validity is reported, not enforced by refitting.**
   - Fewer than 2 distinct σ3: no fit, with `line_fit`'s reason.
   - An intercept ≤ 0 (no real σci) or a slope ≤ 0 (mi ≤ 0): no fit, with a reason.
   - Fewer than 5 points: fitted, with a warning citing Hoek (2007, p. 2).
   - Points with σ3 ≥ 0.5 σci of that fit: kept and counted, with a warning. Refitting until the range is
     consistent was rejected, because it drops data by a rule the engineer didn't choose. A `max_confining_ratio=`
     argument (or plain `where=`) lets the engineer refit deliberately (spec step).
   - R² below 0.9: noted in the summary, not an error.
6. **Names.** The fitted values take the parameter's name, since no unlike tests are pooled (SPEC §5):
   σci as `intact_compressive_strength` and mi as `hoek_brown_constant_intact` (both 🟡). These are checked against
   the whole registry, against soil's `unconfined_compressive_strength`, and against what wave 4's `RUCS` dataset
   (M21) will need.
7. **Multistage stages are fitted by default and can be left out** with `multistage=False`, as in
   `mohr_coulomb_fit()`. The summary prints both fits when a group has multistage stages (sheet 15 §5.6), so the
   bias shows without a second call.
8. **A figure of its own, P32,** `ht.plot.hoek_brown_envelope(df, *, group_by=None, ..., ax=None,
   display_units=None)`. It plots σ1 against σ3, with UCS points on the axis and points left out drawn open with
   their reason. The free curve is solid over the fitted range and dashed beyond it, and the fixed curve is lighter.
   A result box gives σci, mi, n and R², with the lab's pair beside them. Adding it to P11 was rejected, for M17 (b)
   decision 9's reason: P11 draws Mohr circles and takes a `MohrCoulombFit`. The spec decides whether a
   (σ1 − σ3)² against σ3 inset, the regression's own line, is worth adding.
9. **Per-specimen mi is on the result's points,** with σci from that fit, and is NaN at σ3 = 0. A note says it is
   ill-conditioned below about 0.1 σci (sheet 15 §5.4, a judgment for review). It isn't used in the fit. It shows
   whether one curve suits the group, as the shear box's secant angle does.

### Open (for the spec step)
- **Names** checked against the whole registry: the new template columns (`failure_mode`, `reported_` σci and
  mi), the fitted names (decision 6) and the fixed-σci argument. Also check P32 against the
  drafts (P24–P30 are proposed).
- **Golden values:** Hoek's eqs. 6–8 by hand on a set of at least 5 points, free and with σci fixed. Check that
  mi is the same in MPa and psi. Also hand-work edge cases: a group with UCS rows only, one σ3 only, a splitting
  failure, a multistage specimen, and a point beyond 0.5 σci.
- **Whether Hoek (2007) gives a worked regression example** to reproduce, besides the hand calculation.
- **The judgments-file key** for a fixed σci (SPEC §4), if the review keeps the judgments-file route in decision 3.

### Out of scope
- **Wave 4 (M21, M22):** the `RUCS` and `RTEN` datasets from AGS; mi from σci/σt (Cai 2009, Hoek 2023; 15 C); mi
  from tables; tensile points in the fit (Read 2015); the rock mass chain (GSI, mb, s, a, D); the generalized
  Hoek–Brown set.
- **Wave 0 (M16):** rock triaxial results from `TRIT` or user-defined AGS groups.
- **M18:** choosing between the free and fixed fits, characteristic σci and mi, and the Mohr–Coulomb equivalent of
  a Hoek–Brown envelope.
- **Later:** weighted or nonlinear (σ1-space) fits; anisotropy by loading direction, which is left to the engineer's
  `group_by=`.

### SPEC and TODO touched
- **SPEC:**
  - §4 (envelope fits): the fit's line, at close-out;
  - §2.6: the `triaxial` template's new columns, for rock as well as soil (close-out);
  - §5: only if decision 2's pooling exception needs a line (spec step);
  - §12.4: M17 done, with `CLAUDE.md`'s "Next" sentence moving to M18 (d) at close-out.
- **Other docs:**
  - `columns.yaml`;
  - `docs/plots/P32-*.md` (new) and the plots README;
  - page 15 (new, from sheet 15) and the parameter index (15 A, 15 B);
  - `docs/site/reference/analysis.md` and `plot.md`.
- **TODO:** none closed. #31 (the sample dataset) stays open for rock triaxial in AGS files.
