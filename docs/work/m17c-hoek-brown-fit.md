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

## Spec
The plot's rules live in `docs/plots/P32-hoek-brown-envelope.md` (new; there was no draft, and P32 is free: the
drafts stop at P30). The fit's rules are here: `hoek_brown_fit()` has no topic doc of its own, and its docstring
becomes the reference once built. This section lists what changes where, the decisions (the intent's, settled, with
what was added or changed marked), the derivation and the acceptance criteria. 🟡 marks what the intent left open and
this draft proposes.

### Changes
- **`ht.analysis.hoek_brown_fit()`** and **`ht.analysis.HoekBrownFit`** (new), with reference entries.
- **`ht.plot.hoek_brown_envelope()`** (new, P32), with its spec, reference entry, site page and example.
  `docs/plots/README.md`: P32 in batch 2, `draft`.
- **The `triaxial` template and `p.triaxial()`** (decision 2): `failure_mode` after `failure_criterion`, and
  `reported_intact_compressive_strength` and `reported_intact_hoek_brown_constant` after the lab's c′ and φ′.
  `p.triaxial()` reads `TRET_MODE` and `TRIT_MODE` into `failure_mode` and leaves the reported pair blank (no AGS
  heading). `docs/data/datasets.md` §6.10 and §11.1 change in the build commit that adds them.
- **Registry** (decision 3): `failure_mode` (text, `ags: [TRET.TRET_MODE, TRIT.TRIT_MODE]`),
  `intact_compressive_strength` and `intact_hoek_brown_constant` (`ags: ["derived: docs/work/m17c-hoek-brown-fit.md"]`,
  `used_by: [P32]`), and the two `reported_` columns (`ags: ["none: a user CSV, M17 (c)"]`, as the readings
  columns' `"none: …"`). None collides: checked against `columns.yaml`, the plot specs and drafts, the sheets, the
  site and the code, 2026-11-05 (the only other mention is M17 (a)'s reservation of `uniaxial_compressive_strength`
  for wave 4, which these keep free). Result columns aren't registered, as `ShearBoxFit`'s aren't.
- **Judgments file** (decision 8): a new optional judgment, `fixed_intact_compressive_strength`, in
  `src/hangtu/_judgments.py` and `ht.judgments()`'s docstring. **SPEC §4** ("Absence is an error, with one
  exception") gains it as a second exception, in this commit.
- **SPEC §4** gains the fit's line at close-out (the envelope fits bullet); **§2.6** the `triaxial` template for
  rock as well as soil (close-out); **§12.4** M17 done and `CLAUDE.md`'s "Next" moves to M18 (d) (close-out). §5
  needs no line: the pooling exception for UCS rows (decision 7) is the fit's own, as `mohr_coulomb_fit()`'s CU/CD
  pooling is.
- **Example files** (decision 17): `rock_triaxial.csv` (new, MPa) in the `triaxial` template's shape;
  `judgments.yaml` gains the Sandstone's fixed σci; `ht.examples`' docstring names the new file.
- **Docs site:** page 15 promoted from sheet 15 as `docs/site/parameters/15-hoek-brown-constant.md`, with its
  example, in the nav; the parameter index's 15 A ("part built": the CSV through the `triaxial` template; AGS in
  wave 0) and 15 B (built).

### Decisions
1. **`hoek_brown_fit(df, *, group_by=None, failure_modes=None, fixed_intact_compressive_strength=None,
   judgments=None, multistage=True, stress="total", pool=None, units=None, display_units=None) -> HoekBrownFit`.**
   It reads the principal stresses at failure that `triaxial_failure_stresses()` writes, on rows from a CSV in
   `ht.template("triaxial")`'s shape or from `p.triaxial()`. `group_by=` is as in `shear_box_fit()`: one set of
   fits per group in `group_keys()` order (sorted, a categorical's own order, blank last), a missing column an
   error naming it, and no `group_by=` one group of every row. Common choices: `"geology_unit"`,
   `"specimen_id"`, a loading direction column of the user's.
2. **One template for soil and rock** (intent decision 1). The `triaxial` template gains `failure_mode` (text, as
   written: "Mode of failure", AGS `TRET_MODE`/`TRIT_MODE`, which 4.1.1 and 4.2 both have) and the lab's own σci and
   mi, `reported_intact_compressive_strength` and `reported_intact_hoek_brown_constant`. A rock specimen is one
   row: `cell_pressure` (σ3), `deviator_stress_at_failure` (σ1 − σ3); a UCS test has `cell_pressure` 0.
   `triaxial_failure_stresses()` doesn't change. Because a template is its dataset's columns (SPEC §2.6, checked by
   `tests/test_registry.py`), `p.triaxial()` gains the three columns too.
   - 🟡 **A lab that reports σ1** rather than the deviator: no column. `major_principal_stress_at_failure` is
     hangtu's output, and a second input for it would give two sources of σ1 on one row. Page 15 and the template's
     column description say to enter σ1 − σ3 in `deviator_stress_at_failure` (a spreadsheet column).
   - **`test_type` is free text for rock** (AGS has no rock code; ASTM D7012's are methods A–D). A blank or
     unlisted type reads as compression, as now.
3. **Names** (intent decision 6, *changed*): σci is `intact_compressive_strength`, as proposed; mi is
   `intact_hoek_brown_constant` 🟡, not `hoek_brown_constant_intact`, so the material comes first in both (and in
   wave 4's rock mass names, `rock_mass_hoek_brown_constant` for mb beside `rock_mass_compressive_strength`). Both
   take the parameter's name, since UCS and triaxial points are one method's input (SPEC §5). They stay apart from
   soil's `unconfined_compressive_strength` (q_u) and from wave 4's `uniaxial_compressive_strength`, a specimen's
   `RUCS_UCS` (M17 (a)): σci here is a fitted parameter, not a test value. Labels: "Intact compressive strength,
   σci" and "Hoek–Brown constant of intact rock, mi".
4. **The fit is the core's line** (SPEC §4, envelope fits): x = σ3, y = (σ1 − σ3)², `_line_fit(x, y)` free and
   `_line_fit(x, y, intercept=σci²)` with σci fixed; σci = √a and mi = b / σci (Derivation). It is least squares on
   Hoek's own line (Hoek 2007, eqs. 6–8), so the fit is derived, not cited (as M11 (b) decision 2); Hoek (2007)
   eq. 5 is the criterion's citation and eqs. 6–8 the regression's, which the free fit reproduces (AC 1). R² is the
   core's centered R², which for a free fit equals Hoek's eq. 9.
5. **Failure modes as written; the engineer names the ones to fit** (intent decision 4, as proposed).
   `failure_modes=` is a list of the values to fit, matched exactly as written; `None` in it fits rows with a blank
   mode.
   - When `failure_mode` has any value in the frame, `failure_modes=` is required: without it, an error lists each
     mode and its count (blank included) and says to name the shear ones. A name in `failure_modes=` that no row has
     is an error listing the values present (it catches "shear" against "Shear").
   - When the column is missing or blank throughout, every row is fitted, with a note that no mode was given, so
     splitting and defect failures can't be told apart (Hoek 2023, ch. 3, p. 6). `failure_modes=` then is an error
     saying the column has no values.
   - Rejected: a registry list of codes that mean "shear". The dictionaries don't agree on a vocabulary:
     `TRET_MODE`/`TRIT_MODE` list only "Brittle", which says nothing about shear against splitting, while M21's
     `RUCS_MODE` lists SHEAR, DIAGONAL SHEARING, AXIAL, ALONG FOLIATION, MULTIPLE FRACTURING and five more, and all
     are user-extendable (`PA`). Which of these is a shear failure is the engineer's call (SPEC §2.6, never guess).
6. **UCS rows are points at σ3 = 0** (intent decision 2): fitted with the triaxial points, as Hoek's regression
   does. The fitted rows at σ3 = 0 also give the group's **UCS count and mean** (`uniaxial_count`,
   `uniaxial_mean`), printed beside the free σci (sheet 15 §7's check), never used to fix it.
7. **Not pooled unawares:** within a group, fitted rows with more than one `failure_criterion` are an error naming
   each value and its count (a blank is a value of its own), as `mohr_coulomb_fit()`'s; `pool="failure_criterion"`
   pools them on purpose and the result records it; a frame without the column fits, with a note. `test_type`
   isn't checked (*added*): UCS and triaxial pool by the method's design, and rock has no pick list to tell any
   other pair of types apart. `pool=` takes only `"failure_criterion"`.
8. **The fixed σci** (intent decision 3, *names changed*). The free fit is always made. The fixed fit is made with
   σci from, in order (SPEC §4):
   - `fixed_intact_compressive_strength=`: a string with its unit (`"61 MPa"`) for every group, or a mapping from
     a group's key (the value, or a tuple of values with several `group_by` columns) to one. A bare number is an
     error asking for the unit (SPEC §2.6). A key that matches no group warns, naming it; a group the mapping
     doesn't list has no fixed fit, with that reason. An argument beside a file value warns (SPEC §4);
   - the judgments file's `fixed_intact_compressive_strength`, from `judgments=` or the project's file in
     `df.attrs`: entries keyed by a column (`by:`), a `units:` block, a positive value and a reason, and an
     optional `project:` value used, with a warning, for the keys not listed (as `unit_weight`). `by:` must be one of
     the `group_by` columns; otherwise each group's fixed fit is missing with a reason naming the column to group by.
   - Neither: the fixed fit is missing with the reason "no σci given: pass fixed_intact_compressive_strength= or add
     it to the judgments file". Absence isn't an error, because the free fit is the result and the fixed one an
     extra the engineer asks for: SPEC §4 lists it beside `spt_refusal_upper_limit`, in this commit.
   - 🟡 The judgment and argument are `fixed_intact_compressive_strength`, not `intact_compressive_strength`: M18 (d)
     will make the selected σci a judgment, and the fit's input shouldn't take that key first.
   - The result records each fixed value with its source (the argument, or the file's path and SHA-256), as every
     judgment is.
9. **Rows left out and counted**, each once under the first reason that applies: `count_no_principal_stresses`
   (σ3 or σ1 blank, as an extension test's are), then with `stress="effective"` `count_no_effective_stresses`, then
   `count_other_failure_mode` (decision 5, with a count per mode on the result), then, in the single-stage fit,
   `count_multistage_left_out`. `count` plus these is the group's rows. The free and fixed fits of one stage set fit
   the same rows.
10. **Validity is reported, not enforced by refitting** (intent decision 5):
    - free with fewer than 2 points or one σ3: no fit, with the core's reason ("1 point: a line needs at least 2",
      "all points at the same minor principal stress"); fixed with no point or every σ3 = 0: no fit ("no points",
      "all points at minor principal stress = 0");
    - free intercept a ≤ 0: no fit, "intercept σci² = −1325 is 0 or below: no σci"; slope b ≤ 0 in either fit: no
      fit, "slope mi σci = −55 is 0 or below: mi must be positive";
    - fewer than 5 points in a fit that has a result: fitted, with one warning per call naming the groups and citing
      Hoek (2007, ch. 11, p. 2), "at least five well spaced data points";
    - points at σ3 ≥ 0.5 σci of that fit (its own σci, free or fixed): kept and counted
      (`count_beyond_confining_range`), with one warning per call naming the groups and counts (Hoek 2007, ch. 11,
      p. 2). Rejected: a `max_confining_ratio=` argument. The limit moves with the σci each refit gives, so a ratio
      argument would make the fit iterate; the engineer filters the rows (`df[df[...] < 30]`) and refits, and the
      warning says so;
    - R² below 0.9: a note on the fit in the summary (Hoek 2007, p. 4: "high quality triaxial test data will usually
      give a coefficient of determination r² of greater than 0.9"), not a warning;
    - a negative σ3 (tension: wave 4, Read 2015) or σ1 < σ3 is an error naming the rows;
    - every fit has the σ3 range of its points (`lowest_minor_principal_stress`, `highest_minor_principal_stress`).
11. **Multistage stages** (intent decision 7): a group with a multistage stage (`multistage_test` True) gets the
    fits `"all"` and `"single_stage"`; `multistage=` picks the main one, and both are on the result and in the
    summary, as `mohr_coulomb_fit()`'s. A group with no single-stage row has no single-stage fit, "every stage is
    multistage". Without the column, a note says multistage stages weren't told apart.
12. **The back-calculated mi per point** (intent decision 9): mi = ((σ1 − σ3)² − σci²) / (σci σ3) (sheet 15 §5.4,
    eq. 5 solved for mi), with each fit's own σci, on the fit's points as `back_calculated_hoek_brown_constant` 🟡;
    NaN at σ3 = 0 and in a fit with no result. Nothing is fitted to it. The docstring notes that it is
    ill-conditioned at small σ3/σci, with sheet 15 §5.4's computed example (a 5 % error in σ1 gives mi = 19.2 at
    σ3 = 0.5 MPa for a true 8 with σci = 50 MPa), and gives no cutoff: below about 0.1 σci is a judgment.
13. 🟡 **`stress="total"`** (*added*; the intent didn't say which pair). Rock tests rarely measure pore pressure
    (ASTM D7012 has none), so `triaxial_failure_stresses()` leaves their effective pair blank, and a default of
    `"effective"` would leave every rock row out. `stress="effective"` fits the effective pair, for saturated tests
    with a measured pore pressure. Hoek's criterion is in effective stress (eq. 5's primes); the docstring says a
    total-stress fit assumes no pore pressure in the specimen. The names don't change, and the result records the
    pair.
14. **Units** (SPEC §2.6): the stress columns resolve `units=`, then `df.attrs["units"]`, else an error naming the
    column. σ3, σ1, the fixed σci and the lab's σci are converted to one unit before fitting, so mi is
    dimensionless: σ3's (the cell pressure's, as `triaxial_failure_stresses()` writes it), or `display_units=`'s
    (kPa, psf, or the settings override: MPa, psi). σci scales with the unit and mi doesn't (AC 4). A frame without
    the principal stresses is an error pointing to `triaxial_failure_stresses()` and `ht.template("triaxial")`.
15. **`HoekBrownFit`** 🟡 (the shape), a `_DerivedResult` with `kind = "derived"`:
    - `.to_frame()`: one row per group, stage set and fit, the main stage set first and in each the free fit
      first. Columns: the `group_by` columns; `stages` (`"all"`, `"single_stage"`); `line_kind` (`"free"`,
      `"fixed_strength"`); `intact_compressive_strength` (fitted, or the value fixed); `intact_hoek_brown_constant`;
      `r_squared`; `count`; `lowest_minor_principal_stress`; `highest_minor_principal_stress`;
      `count_beyond_confining_range`; `uniaxial_count`; `uniaxial_mean`; `intact_compressive_strength_source`
      (`"fitted"`, `"argument"`, `"judgments file"`); `reported_intact_compressive_strength`;
      `reported_intact_hoek_brown_constant`; `count_reported_pairs`; the four `count_…` of decision 9;
      `no_fit_reason`. A long frame by fit kind, as `ShearBoxFit`'s `line_kind`, so `intact_hoek_brown_constant`
      is one column M18 (d) reads, with `line_kind` saying which fit. `attrs["units"]` gives the stress columns'
      unit.
    - `.groups`: each group's key, row count and fits, each with its points (row, identifiers, σ3, σ1,
      `failure_mode`, `multistage_test`, `back_calculated_hoek_brown_constant`), the rows left out with their reasons
      and the count per failure mode left out.
    - The lab's pairs are a view (as M11 (b) decision 9): the distinct (σci, mi) pairs of the rows fitted, each with
      its count of rows, σci converted to the fit's unit. `.to_frame()` gives the pair when there is one, else
      blanks and the count. Nothing compares them.
    - The summary, per group: the main free fit ("free: σci = 63.9 MPa, mi = 12.4, R² = 0.951, 13 points, σ3 0 to
      20 MPa"), the fixed fit ("σci fixed at 61 MPa (judgments.yaml): mi = 13.4, R² = 0.949"), the other stage
      set's two fits, the UCS count and mean, the rows left out by reason and mode, the lab's pairs, and each fit's
      notes (fewer than 5 points, beyond 0.5 σci, R² below 0.9); then the call's notes. `.to_dict()` passes
      `json.dumps`.
16. **P32, `ht.plot.hoek_brown_envelope()`** (intent decision 8): its rules are in its spec. It calls
    `hoek_brown_fit()` with the shared arguments and draws its result, returning `(fig, ax, fit)` like P11 and P31.
    The (σ1 − σ3)² against σ3 view (the intent's open inset) is deferred to P32 §15 as `space="regression"`: the
    per-point mi and R² already show a poor fit, and an inset crowds a one-panel figure.
17. **The example data** 🟡 (values under "Example data"): `rock_triaxial.csv` in the `triaxial` template's shape,
    stresses in MPa (a rock lab's unit; the psi twin is tested, AC 4), depth in ft, from B-3's sandstone cores
    (61.5–71.5 ft, M17 (b) decision 13), `geology_unit` Sandstone. It is a CSV, not `TRIT` rows in `site.ags`,
    because a CSV is the input this unit relies on (M17 (a) decision 1) and AGS gives one unit per heading, so
    `site.ags` would store it in psf. `judgments.yaml` gains `fixed_intact_compressive_strength` for Sandstone, 61
    MPa, "mean of the three UCS tests that failed in shear, 60.8 MPa".

### Derivation
The criterion (Hoek 2007, ch. 11, eq. 5, p. 2): σ1 = σ3 + σci (mi σ3/σci + 1)^0.5. Moving σ3 across and squaring,
(σ1 − σ3)² = σci² (mi σ3/σci + 1) = mi σci σ3 + σci², a line in x = σ3, y = (σ1 − σ3)² with intercept a = σci² and
slope b = mi σci (eq. 6, p. 4; printed "y = mσci x + sσci", where s = 1 for intact rock and the intercept is σci²,
as eq. 7 and Table 1's cell formula, σci = √(intercept), make it). Back: **σci = √a** (a > 0) and **mi = b / σci**
(b > 0). Free least squares gives b = Sxy / Sxx and a = ȳ − b x̄ (M11 (b), Derivation 6), which is eqs. 7–8 with the
sums expanded: Sxy = Σxy − ΣxΣy/n, Sxx = Σx² − (Σx)²/n. With σci fixed, minimizing Σ(y − σci² − b x)² over b gives
b = Σx(y − σci²) / Σx², so mi = Σx(y − σci²) / (σci Σx²) (sheet 15 §5.3). Eq. 5 solved for mi at one point gives
decision 12's back-calculated mi.

### Example data
🟡 Proposed values, made about σci = 60 MPa and mi = 15 (sheet 15 §3: sandstone 17 ± 4) with site-like scatter
(memory: not points on the curve), a multistage specimen biased low at its later stages (sheet 15 §5.6), and two
non-shear failures. Every row: `loca_id` B-3, `failure_criterion` "Peak axial stress", `geology_unit` Sandstone,
`soil_class` rock, the lab's fit `reported_intact_compressive_strength` 64 MPa and
`reported_intact_hoek_brown_constant` 12.4 (its fit of the 13 shear rows, rounded). The generator's comments carry
the hand fits.

| Specimens | `test_type` | σ3 (`cell_pressure`, MPa) | σ1 (MPa) | `deviator_stress_at_failure` | `failure_mode` |
|---|---|---|---|---|---|
| 3 UCS | UCS | 0, 0, 0 | 54.2, 66.8, 61.5 | 54.2, 66.8, 61.5 | Shear |
| 1 UCS | UCS | 0 | 38.6 | 38.6 | Axial splitting |
| 7 single stage | Triaxial | 2.5, 2.5, 5, 10, 10, 15, 20 | 74.1, 83.9, 98.7, 117.4, 129.0, 151.2, 160.3 | 71.6, 81.4, 93.7, 107.4, 119.0, 136.2, 140.3 | Shear |
| 1 single stage | Triaxial | 10 | 88.0 | 78.0 | Along bedding |
| 1 multistage, 3 stages | Triaxial multistage | 5, 10, 20 | 93.0, 115.8, 153.4 | 88.0, 105.8, 133.4 | Shear (`multistage_test` True) |

### Sources
- **Hoek (2007):** *Practical Rock Engineering*, ch. 11 "Rock mass properties": eq. 5, p. 2 (the intact
  criterion; "0 < σ′3 < 0.5 σci"; "At least five well spaced data points should be included in the analysis");
  eqs. 6–9, p. 4 (the regression, r², and "greater than 0.9"); Table 1, p. 5 (a worked spreadsheet: five points,
  σci = 37.4, mi = 15.50, r² = 0.997). [V], re-read 2026-11-05 from the Rocscience PDF.
- **Hoek (2023):** *Practical Rock Engineering*, ch. 3 "Intact rock strength": eq. 1, p. 3; p. 6 ("The Hoek-Brown
  criterion is only applicable to shear failure … remove the results of tests exhibiting other types of failure";
  "a minimum of 3, but preferably 5 triaxial tests, in addition to the uniaxial compressive tests"; the
  brittle–ductile transition at 3 < σ1/σ3 < 5). [V], re-read 2026-11-05. Its Fig. 5 (Coburg limestone, σci = 130.4
  MPa, mi = 8.1, p. 7) isn't a golden value: plain least squares on its 15 points gives σci = 138.5 and mi = 6.98,
  because the figure fits each σ3's mean and standard deviation, a method this fit doesn't use.
- **AGS 4.1.1 and 4.2 dictionaries** (python-ags4's copies): `TRET_MODE` and `TRIT_MODE` "Mode of failure" (`PA`,
  example "Brittle"); `RUCS_MODE`'s list (decision 5).
- **The fit:** least squares on Hoek's line, derived above.
- **1 psi** = 0.45359237 × 9.80665 / 0.0254² Pa = 6894.75729 Pa, exact by definition, so 1 MPa = 145.037738 psi.
- 🔬 **The multistage bias** (sheet 15 §5.6: ISRM 1983, Youn & Tonon 2010, both [U]): page 15 states it as a
  judgment for review, uncited, until a source is read.

### Acceptance criteria
Golden values hand-calculated from the Derivation, with the sums written out and the arithmetic done exactly (in
fractions) and rounded to 9 significant figures; tolerance 1e-7 relative unless stated. Points are (σ3, σ1) in MPa.
1. **Hoek (2007) Table 1** (hand-built, no failure mode): (0, 38.3), (5, 72.4), (7.5, 80.5), (15, 115.6), (20,
   134.3); y = 1466.89, 4542.76, 5329, 10120.36, 13064.49; Σx = 47.5, Σy = 34523.5, Σxy = 475776.5, Σx² = 706.25
   (Table 1's sums), Sxx = 255, Sxy = 147803.25. Free: b = 197071/340 = 579.620588, a = 950847/680 = 1398.30441,
   **σci = 37.3939088, mi = 15.5004012, R² = 0.997147827** (Table 1: 37.4, 15.50, 0.997). σ3 range 0 to 20,
   0.5 σci = 18.70, so 1 point beyond (σ3 = 20) and its warning; `uniaxial_count` 1, `uniaxial_mean` 38.3.
   Back-calculated mi: NaN, 16.8180096, 14.0154577, 15.5498687, 15.5990454.
2. **Table 1 with σci fixed** (`fixed_intact_compressive_strength="38.3 MPa"`): a = 1466.89, Σx(y − a) =
   406099.225, b = 575.007752, **mi = 15.0132572**, R² = 0.997048983, `intact_compressive_strength_source`
   `"argument"`; back-calculated mi NaN, 16.0619843, 13.4451175, 15.0626110, 15.1404700. 0.5 × 38.3 = 19.15, so 1
   point beyond.
3. **The example sandstone** (`rock_triaxial.csv`, `failure_modes=["Shear"]`, `group_by="geology_unit"`, the
   example `judgments.yaml`):
   - all stages, 13 points (3 UCS, 7 single stage, 3 multistage): Σx = 100, Σy = 132377.83, Σxy = 1508743.35,
     Σx² = 1387.5; b = 127517611/160750 = 793.266631, a = 262399233/64300 = 4080.85899, **σci = 63.8816013,
     mi = 12.4177637, R² = 0.950690094**; fixed at 61 (from the file): Σx(y − 3721) = 1136643.35,
     b = 819.202414, **mi = 13.4295478**, R² = 0.948857038, source `"judgments file"`;
   - single stage, 10 points: b = 6917921/8000 = 864.740125, a = 12619687/3200 = 3943.65219, **σci = 62.7985047,
     mi = 13.7700751, R² = 0.966311262**; fixed at 61: mi = 14.4511428, R² = 0.965568515;
   - `uniaxial_count` 3 and `uniaxial_mean` 60.8333333 (365/6) in every fit; `count_other_failure_mode` 2
     (Axial splitting 1, Along bedding 1); `count_multistage_left_out` 3 in the single-stage fits; counts add to
     15; no point beyond 0.5 σci; the lab's pair (64, 12.4) × 13; the multistage note in the summary;
   - back-calculated mi in the all-stages free fit at σ3 = 2.5: 6.54774451 and 15.9363633 (the ill-conditioning
     decision 12 notes);
   - `multistage=False` puts the single-stage fits first with the same values.
4. **Units:** Table 1 converted to psi (× 145.037738) gives the same mi in both fits (1e-9 relative) and σci =
   5423.52793 psi free; with `display_units="SI"` the example gives σci = 63881.6013 kPa and the same mi; the
   fixed value `"8847.30 psi"` on the MPa frame converts before fitting. A bare number (`61`) raises asking for
   the unit; a frame without units raises naming the column.
5. **Failure modes:** the example without `failure_modes=` raises, listing Shear × 13, Axial splitting × 1, Along
   bedding × 1; `failure_modes=["shear"]` raises, listing the values present; `["Shear", "Along bedding"]` fits 14
   rows; a frame without `failure_mode` fits every row with the note; `failure_modes=` on such a frame raises; a
   blank mode among values is left out unless `None` is named.
6. **The fixed σci's sources:** the argument beside the file warns and wins; a mapping `{"Sandstone": "61 MPa",
   "Shale": "20 MPa"}` fits the Sandstone and warns about "Shale"; no argument and no file entry gives the fixed
   row with its reason; a file keyed `by: specimen_id` with `group_by="geology_unit"` gives the reason naming
   `specimen_id`; a file `project:` value fills an unlisted group with a warning; the result records each value's
   source.
7. **Validity (hand-built):**
   - UCS only, (0, 50), (0, 55), (0, 60): free "all points at the same minor principal stress", fixed at 55 "all
     points at minor principal stress = 0", `uniaxial_mean` 55;
   - one σ3, (10, 120), (10, 125), fixed at 50: free "all points at the same minor principal stress"; fixed
     y = 12100, 13225, b = 203250/200 = 1016.25, mi = 20.325; the fewer-than-5 warning;
   - (5, 30), (10, 60), (20, 100): Sxx = 350/3, Sxy = 45000, a = −1325: free no fit with the intercept reason;
   - (0, 60), (10, 65), (20, 70): b = −55: free no fit with the slope reason;
   - (0, 50), (5, 85), (10, 105), (20, 140), (40, 190): a = 3646.875, b = 487.875, σci = 60.3893616,
     mi = 8.07882360, R² = 0.987174208; σ3 = 40 ≥ 30.19, so `count_beyond_confining_range` 1 and the warning;
   - R² below 0.9 on a hand-built set: the note in the summary, no warning;
   - a negative σ3 and a row with σ1 < σ3 raise, naming the rows.
8. **Pooling and stresses:** two `failure_criterion` values raise, naming each with its count; `pool=
   "failure_criterion"` fits and `.pooled` records it; `pool="test_type"` raises listing what `pool=` takes; UCS
   and triaxial rows with different `test_type` fit without an error. `stress="effective"` on rows with blank
   effective stresses leaves them out under `count_no_effective_stresses`; `stress="mean"` raises.
9. **Views:** `.to_frame()` has decision 15's columns in order, the main stage set and the free fit first, and
   `attrs["units"]`; `.to_dict()` passes `json.dumps`; `kind` is `"derived"`; `print()` gives decision 15's lines.
   For every group and fit in AC 1–8, `count` plus the four `count_…` is the group's rows.
10. **The template and dataset:** `ht.template("triaxial")` has `failure_mode` and the two `reported_` columns in
    decision 2's places; `p.triaxial()` has them too (the registry test of SPEC §2.6 passes), with `TRET_MODE` and
    `TRIT_MODE` read as written from a test file that has them and blank otherwise; the soil stages of the example
    project give the same `mohr_coulomb_fit()` as before.
11. **Judgments file:** `fixed_intact_compressive_strength` with a missing `units:` block, a value of 0 or a missing
    reason raises naming the file and entry, as the other judgments.
12. **The plot:** P32's §12 criteria.
13. **Reference:** `hoek_brown_fit`, `HoekBrownFit` and `hoek_brown_envelope` in the API reference (the test that
    fails without an entry), with the docstring checklist of the sheets' `TEMPLATE.md`; page 15 links them.
