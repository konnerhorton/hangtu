# Strength: stresses at failure, envelope fits, undrained strength and the shear box conversion

| | |
|---|---|
| **Status** | Living spec. Stresses at failure (M11 a), envelope fits (M11 b, M17 b–c), failure from readings (M11 c), undrained strength from tests (M17 a) and the shear box conversion (M18 d) built |
| **Parent** | SPEC §4 (triaxial stresses at failure, envelope fits, undrained strength) and §5 (derived results) |
| **Related** | [`m11a-triaxial-data.md`](../work/m11a-triaxial-data.md), [`m11b-envelope-fit.md`](../work/m11b-envelope-fit.md), [`m11c-triaxial-shearing.md`](../work/m11c-triaxial-shearing.md), [`m17a-strength-data.md`](../work/m17a-strength-data.md), [`m17b-shear-box-fit.md`](../work/m17b-shear-box-fit.md), [`m17c-hoek-brown-fit.md`](../work/m17c-hoek-brown-fit.md), [`m18d-sources-compared.md`](../work/m18d-sources-compared.md). The datasets: [`docs/data/datasets.md`](../data/datasets.md) §6.10–6.12. The figures: P11, P12, P31, P32 in [`docs/plots/`](../plots/README.md). The judgments: [`judgments.md`](judgments.md) |

Update this file in the same commit as any change to these functions' behavior, and SPEC §4 or §5 if the change
alters a rule there. Each fit's derivation is in its docstring's Notes, the published reference; it isn't repeated
here.

## 1. Triaxial stresses at failure
`ht.analysis.triaxial_failure_stresses(df)` is the one place σ1, σ3, σ′1 and σ′3 are computed. `p.triaxial()` calls
it, so CSV and AGS rows follow the same rules, and P11, P12 and every fit read its columns, never computing them.
- σ3 = `cell_pressure`; σ1 = σ3 + q_f (`deviator_stress_at_failure`); σ′3 = σ3 − u_f; σ′1 = σ′3 + q_f.
- **u_f** is `pore_pressure_at_failure`, else the back pressure in a drained test (which holds the pore pressure
  there), counted in one warning; `effective_stress_basis` says which on every row. Nothing else is filled: an
  undrained stage without a pore pressure gets blank σ′ (QC X002 lists them). σ′3 = consolidation pressure isn't
  used: it assumes the cell pressure didn't change after consolidation (QC X006 checks that).
- Without `pore_pressure_at_failure` (a UU set, a rock test) it gives the total pair only, with no warning.
- **Extension tests** keep blank principal stresses, with one warning: the dictionary gives no sign convention
  for the deviator in extension, and blanks are better than wrong values.
- **Errors for CSV input** where a dataset blanks with a warning instead: a missing required column, q_f ≤ 0 in a
  compression test, stresses of different dimensions. Each names the rows. A dataset doesn't stop on the file's
  data.
- Units resolve as SPEC §2.6; the stresses come back in the cell pressure's unit.
- One template for soil and rock (`ht.template("triaxial")`): a rock UCS test is a row with `cell_pressure` 0, and a
  lab that reports σ1 enters σ1 − σ3 as the deviator, so σ1 has one source on a row.

## 2. Failure from readings
`ht.analysis.triaxial_failure_from_readings(df, *, failure_criterion=None, units=None)` reduces readings during
shearing to one failure row per stage in the `triaxial` template's shape, so P11, P12 and the fits can't disagree
about where a stage failed. It computes no principal stress: `triaxial_failure_stresses()` does.
- **The failure reading:** `failure_criterion=` first (an engineer re-picking the lab's tests), then the lab's
  mark (`reported_failure_reading`), else an error. No default. When the argument overrides marks, a note counts
  them.
- **Two criteria:** `"max_deviator_stress"` (the largest q) and `"max_stress_ratio"` (the largest σ′1/σ′3,
  effective stress only); ties go to the lowest strain. The rows' `failure_criterion` is written "Maximum deviator
  stress" or "Maximum principal stress ratio", as AGS writes it, so rows from readings and from AGS pool, or refuse
  to, by one rule (§3).
- **The path starts at cell − back**, with u = back + Δu per reading, so a path's last point is its failure row's.
  `effective_consolidation_stress` is carried, not used.
- **A stage is (`specimen_id`, `test_stage`).** Other columns are stage columns, carried, and must be the same on
  all of a stage's readings. Strain must not decrease within a stage (which also catches two stages under one ID).

## 3. The line-fit core and what every fit shares
**The core** (`hangtu.analysis._line_fit`): each fit transforms its points into x and y, fits y = a + b x by ordinary
least squares, free or with a fixed, and back-transforms a and b into the criterion's parameters.
- Free: b = Sxy / Sxx, a = ȳ − b x̄. Fixed a: b = Σx(y − a) / Σx².
- R² is the centered 1 − SSres / SStot in both cases, so a fixed fit can have a low or negative R² and compares with
  the free one; NaN with one point or all y equal.
- It can't fit, and says why, with fewer than 2 points or one x (free), or no point or every x = 0 (fixed).
- No standard errors: the residuals are kept, and how a fit's uncertainty enters a selected value is selection's.

**Groups:** `group_by=` gives one fit per group in `group_keys()` order (sorted, a categorical's own order, blank
last), as the statistics functions order them; a missing column is an error. No `group_by=` is one group of every
row.

**Not pooled unawares:** within a group, fitted rows with more than one `failure_criterion` (and, per fit,
`test_type` as §4–§5 say) are an error naming each value and its count; a blank is a value of its own. `pool=`
names columns to pool on purpose and the result records it. A column the rows don't have isn't checked, and a note
says so.

**Rows left out are counted,** each once under the first reason that applies; `count` plus the counts is the
group's rows. Every line of one stage set fits the same rows.

**Multistage stages** (`mohr_coulomb_fit()`, `hoek_brown_fit()`): a group with a `multistage_test` stage gets fits
`"all"` and `"single_stage"`; `multistage=` picks the main one and both are on the result. Without the column a note
says stages weren't told apart. `shear_box_fit()` doesn't read the column: the file can't tell a multistage shear
box from specimens entered as stages, and `group_by="multistage_test"` gives the same lines.

**Validity is reported, never enforced by refitting:** a group that can't give a parameter has a reason, not an
error, so one bad group doesn't stop the others; a negative free intercept is kept, with a warning naming the groups;
nothing is forced through the origin unless asked; one warning per kind per call. Every fit records the stress
range of its points, and the summary says a cohesion is an intercept outside it. A free line of 2 points notes that
it passes through both.

**The lab's values are a view:** each group lists the distinct `reported_…` pairs of its fitted rows, with their
counts of stages, converted to the fit's unit. `.to_frame()` gives the pair when the group has one, else blanks and
the count. Nothing compares them (QC does).

**Names:** a fitted value takes the parameter's name (`effective_friction_angle`), as a measured value does, unless
that would pool unlike tests (§5). The line's own values are `line_intercept` and `line_slope`.

**Units** resolve as SPEC §2.6. Every stress is converted to one unit before fitting: the minor principal stress's,
or `display_units=`'s (kPa for SI, psf for US). A cohesion scales with the unit; an angle and mi don't change.

**Derived results** (SPEC §5): each fit returns a frozen dataclass on `_DerivedResult` in `ht.analysis`, `kind =
"derived"`, recording the function, the unit, the notes, the input's judgments, the hangtu version, the input's
`attrs["judgments_file"]` (so a later step reaches the Project's judgments: `friction_angle_from_shear_box()`) and
its `attrs["soil_classes"]` (so a model set reads the geology map's classes), with `.to_dict()` (JSON-serializable),
`.to_frame()` and a printed summary. It keeps the points it fitted (identifiers, stresses, and `depth`, `elevation`
and `ground_level` where the input has them), not a reference to the input.

## 4. `mohr_coulomb_fit()`
- Reads the principal stresses at failure, effective (`stress="effective"`) or total, and fits the s–t line,
  t = c cos φ + s sin φ, then c and φ from its intercept and slope. A frame without the stresses is an error saying
  to call `triaxial_failure_stresses()` first.
- **Pooling:** `failure_criterion` always; with `stress="total"`, `test_type` too (UU and CU total envelopes
  differ). CU and CD stages pool in effective stress.
- **Counted:** `count_no_principal_stresses`, `count_no_effective_stresses` (effective fit only),
  `count_multistage_left_out`. σ′1 < σ′3 on a row is an error.
- **Validity:** a slope tan α outside 0 ≤ tan α < 1 has no friction angle (sin φ = tan α), so no fit, with the reason;
  a point with σ′3 < 0 is kept, with a warning (tension).
- **`cohesion=` takes None or 0.** It is an argument recorded on the result, not a judgment (it applies to one
  fit, not a geology unit). With c fixed at a non-zero value, a = c cos φ depends on the slope and the s–t fit is no
  longer a line, so another value is an error. With 0 it replaces the free fit.
- Names: `effective_cohesion`, `effective_friction_angle`; total: `total_stress_cohesion`,
  `total_stress_friction_angle`. The lab's effective pair isn't listed beside a total fit.

## 5. `shear_box_fit()`
- Fits τ against σn untransformed: c = a, φ = arctan b. One function for soil and rock joints; the engineer separates
  them with `group_by=` or `where=`.
- **Four lines per group, always:** peak and residual, each `"free"` and `"through_origin"`. `cohesion=None` makes
  `"free"` the main line, `cohesion=0` `"through_origin"`; both are always made, as page 22 advises reporting them
  together.
- **The normal stress of a point:** `normal_stress="at_peak_or_residual"` takes `normal_stress_at_peak` (or
  `_at_residual`) where the row has it, else `applied_normal_stress`; `"applied"` takes the applied one throughout.
  Each point records `normal_stress_basis`; a line with more than one basis gets a note.
- **Names take the test's:** `peak_cohesion`, `peak_friction_angle`, `residual_cohesion`, `residual_friction_angle`,
  not `effective_…`, because a direct shear φ′ isn't a triaxial φ′ until converted (§8) and its stresses aren't
  labeled effective.
- **Pooling:** `test_type` and `failure_criterion`, peak and residual checked apart (a ring shear test with only a
  residual and a shear box with only a peak share no line).
- **Counted,** per strength: `count_no_{peak,residual}_shear_stress`, then `count_no_{peak,residual}_normal_stress`.
- **Validity:** a slope below 0 has no friction angle (every b ≥ 0 has one below 90°); a negative shear or normal
  stress is an error asking to check the sign; residual above peak is QC H001's.
- `secant_friction_angle`, arctan(τ/σn) per point (NaN at σn = 0), is on the points; nothing is fitted to it.

## 6. `hoek_brown_fit()`
- Fits Hoek's line (Hoek 2007, eqs. 6–8): x = σ3, y = (σ1 − σ3)², σci = √a, mi = b / σci. The free fit reproduces
  Hoek's regression, and its R² equals his eq. 9. UCS rows are points at σ3 = 0 in the same fit, and also give the
  group's `uniaxial_count` and `uniaxial_mean`, printed beside the free σci as a check, never used to fix it.
- **Both fits, where possible:** the free fit always; the fit with σci fixed when σci is given as an argument or
  the `fixed_intact_compressive_strength` judgment ([`judgments.md`](judgments.md) §5.7), never picked by a rule.
  Without it, the fixed fit is missing with a reason, since the free fit is the result.
- **Failure modes as written; the engineer names the ones to fit.** When `failure_mode` has any value,
  `failure_modes=` (matched exactly; `None` for blank) is required, and the error lists each mode and its count. A
  name no row has is an error listing those present. When the column is missing or blank, every row is fitted, with
  a note that splitting and defect failures can't be told apart. No registry list of "shear" codes: the
  dictionaries' vocabularies don't agree, and which mode is a shear failure is the engineer's call.
- **`stress="total"` by default:** rock tests rarely measure pore pressure, so the effective pair is usually blank.
  The docstring says a total-stress fit assumes no pore pressure in the specimen.
- **Pooling:** `failure_criterion` only (`pool=` takes only it). `test_type` isn't checked: UCS and triaxial pool by
  the method's design.
- **Counted:** `count_no_principal_stresses`, then `count_no_effective_stresses` (effective fit),
  `count_other_failure_mode` (with a count per mode), then `count_multistage_left_out` in the single-stage fit.
- **Validity:** a free intercept ≤ 0 (no σci) or a slope ≤ 0 (mi must be positive) is no fit; fewer than 5 points
  warns (Hoek 2007, ch. 11); points at σ3 ≥ 0.5 σci of that fit are kept and counted
  (`count_beyond_confining_range`) with a warning, never refitted away, because the limit moves with each refit's
  σci and the engineer filters and refits; R² below 0.9 is a note; σ3 < 0 or σ1 < σ3 is an error.
- `back_calculated_hoek_brown_constant` per point, with that fit's σci (NaN at σ3 = 0), ill-conditioned at small
  σ3/σci; nothing is fitted to it, and no cutoff is given.
- Names: `intact_compressive_strength`, `intact_hoek_brown_constant` (material first, as wave 4's rock mass names),
  apart from soil's `unconfined_compressive_strength` and a specimen's `uniaxial_compressive_strength`.

## 7. Undrained strength from tests
`ht.analysis.undrained_shear_strength_from_tests(df, *, hand_penetrometer_scale=None)` gives s_u on every row from
the one input it has; `p.undrained_strength()` calls it, so CSV and AGS rows follow the same rules.

| Input on the row | s_u | `undrained_shear_strength_basis` |
|---|---|---|
| `deviator_stress_at_failure` (UU) | q_f / 2 | `half_deviator_stress` |
| `unconfined_compressive_strength` | q_u / 2 | `half_unconfined_compressive_strength` |
| `hand_penetrometer_reading`, scale `"unconfined_compressive_strength"` | reading / 2 | `half_hand_penetrometer_reading` |
| `hand_penetrometer_reading`, scale `"undrained_shear_strength"` | reading | `hand_penetrometer_reading` |
| `undrained_shear_strength` only (vanes, fall cone, `LPEN`) | as given | `as_reported` |

- A φu = 0 strength needs no fit: a set's value is the mean of its specimens' s_u.
- **Two inputs on a row** is an error naming the rows; a lab's s_u beside q_f goes in
  `reported_undrained_shear_strength`, which is kept, not used (QC Q001 compares). The line between the two: could
  hangtu compute it from the row.
- **`hand_penetrometer_scale=`** states what the instrument read, a fact of the investigation, so it is a required
  argument, neither a judgment nor guessed. Without it, a dataset leaves `IPEN` rows out and counts them; the
  analysis errors.
- **Tests are kept side by side** by `test_type` and `source`, never combined or converted between. The field vane is
  uncorrected: Bjerrum's μ is selection's, a judgment.
- **`strength_sensitivity`** = s_u / s_u,r from one test's peak and remolded values, both unflagged, with s_u,r > 0;
  otherwise blank, counted in one warning. A hand penetrometer beyond its range is a bound (`qualifier = ">"`).
- **Errors for CSV input** where a dataset blanks or leaves out with a warning: q ≤ 0, a reading without the scale,
  stresses of different dimensions.
- **Units:** s_u in `undrained_shear_strength`'s declared unit, else in the first input column's, in the table's
  order.

## 8. The shear box φ′ conversion
`ht.analysis.friction_angle_from_shear_box(fit, *, soil, critical_state_friction_angle=None, judgments=None)` takes
a `ShearBoxFit` and returns `ShearBoxConversion`, a derived result (§3).
- **The equations** (Kulhawy & Mayne 1990, Eq. 4-10 and Tables 4-2, 4-5): φ′psc = tan⁻¹(tan φ′ds / cos φ′cv), then
  φ′tc = φ′psc / r, r = 1.12 for `soil="cohesionless"` and 1.10 for `"normally_consolidated_cohesive"`.
- **`soil=` is required and never inferred** from `soil_class` or a USCS symbol. Only the two values the tables
  cover; another is an error suggesting `peak_friction_angle` unconverted. No `ratio=` of the engineer's own: that
  would be an unpublished correlation. A mapping by geology unit needs the fit grouped by `geology_unit`.
- **φ′cv** is the `critical_state_friction_angle` judgment, by geology unit ([`judgments.md`](judgments.md) §5.8),
  resolved through the Project's file the fit's input carried.
- **Peak angle only, every line kind:** residual angles aren't converted (φr is independent of test type, K&M
  p. 4-10), and the cohesion isn't (no conversion is given; it is kept as fitted, with a note).
- **What it asserts:** the shear box stresses are effective and the test drained (ASTM D3080), which `shear_box_fit()`
  doesn't assume, so the result always notes it; for normally consolidated cohesive soils, also Table 4-5's
  footnote (speculative, based on results from sand).
- **Below critical state:** when φ′ds < tan⁻¹(sin φ′cv), φ′psc < φ′cv; the value is converted, flagged in
  `below_critical_state`, and warned about. A φ′ds ≤ 0 or a group with no fit gets a `no_conversion_reason`.
- **The converted value is `effective_friction_angle` with `conversion_name`**
  (`"friction_angle_from_shear_box_kulhawy_mayne_1990"`), as a correlation's estimate carries `correlation_name`.
  `conversion_name` is a source column, so triaxial and converted rows can't pool unawares, and P01, P07 and
  `compare_sources()` read it as φ′ without being told.
- `.to_frame()`: one row per group and line kind, the main line first: the keys, `line_kind`,
  `peak_friction_angle`, `critical_state_friction_angle`, `conversion_soil`, `plane_strain_friction_angle`,
  `effective_friction_angle`, `conversion_name`, `below_critical_state`, `count`, the normal stress range and
  `no_conversion_reason`. It keeps the fit's peak points with their depths, and the judgment.
