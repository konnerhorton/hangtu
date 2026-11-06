# M18 (d): compare a parameter's sources by depth and geology unit

## Intent
M18 is selection, stage D (SPEC §1.3, §5, §12.4). Its units: (a) SPT refusals (done), (b) representative values
(done), (c) P09 (done), **(d) this unit, sources compared**, and (e) the selection as a judgment, the model-set
results and the Mohr–Coulomb set. The old (d) is split in two (decided 2026-11-05): comparing sources, and
recording the selection, are two separate designs, and each fits in one review.

**Goal:** put every source of one parameter side by side, per geology unit and against depth, so an engineer
can see whether they agree before choosing one (unit (e)). For φ′ the sources are the triaxial fit
(`mohr_coulomb_fit()`), the shear box fit (`shear_box_fit()`, first converted to a triaxial φ′) and the SPT
correlations. For s_u they are the tests side by side (`undrained_shear_strength_from_tests()`) and the SPT
correlations.

**Why:**
- **Choosing a value means comparing its sources first.** SPEC §5 says statistics feed stage D by "comparing
  the sources of a parameter by depth or geology unit". Today an engineer can draw P01 with
  `marker_by="correlation_name"`, but the fitted φ′ values aren't rows in that frame, and P01's stats box reads
  "mixes sources" rather than giving each source's numbers.
- **The sources come in different shapes.** A fit gives one value per group, with n, r² and its stress range,
  and no standard error. A correlation gives one estimate per row, some of them bounds (M18 (a)). A test gives
  one value per specimen, labeled by `test_type`. Comparing them honestly means keeping those shapes apart: a
  fit's single value isn't a sample that `compare()` can test.
- **A direct shear φ′ isn't a triaxial φ′.** SPEC §5 (derived results) keeps them apart by name
  (`peak_friction_angle`) "until selection converts it (M18)". Page 04 gives the conversion: tan φ′ds =
  tan φ′ps · cos φ′cv, with φ′ps ≈ 1.10 φ′tc for normally consolidated cohesive soils (Kulhawy & Mayne 1990,
  Eq. 4-10 and Table 4-5, p. 4-25 [V]). It needs φ′cv, which is a judgment, and so does ψ in (e).
- **What depends on it:** unit (e) records which source and method the engineer chose, and its result says
  what the other sources gave.

**Scope:**
- **One comparison per parameter.** It takes the frames and results the engineer already has (a test frame,
  correlation frames, fit results) and returns a result in SPEC §5's shape (one calculation, many views) with,
  per geology unit and source: n, `describe()`'s statistics for row sources, the fitted value, n and stress
  range for fit sources, and bounds counted as `describe()` counts them. 🟡 Its name and home
  (`ht.stats.compare_sources()`?) are for the spec, checked against the registry.
- **Sources are named, never pooled.** Each source keeps the label it already has (`correlation_name`,
  `test_type`, `source`, the fit's method). Grouping by source is the point of the comparison, so SPEC §5's
  "sources aren't pooled unawares" holds without `pool=`.
- **Tests only where the shapes allow them.** Between two row sources (UU against field vane, two correlations)
  the comparison reports `compare()`'s paired results, with `significance_level` as a judgment. A fit's value is
  shown against the row sources' spread (within their range, or which percentile it falls at), and never
  tested. 🟡 Whether the tests are in (d) at all, or the comparison stays descriptive, is for the spec: SPEC §5
  says selection pools units "on geology and plots; tests are a check".
- **The shear box conversion**, from `peak_friction_angle` to a triaxial φ′ by Kulhawy & Mayne (1990)
  Eq. 4-10, as its own function. φ′cv is a judgment keyed by geology unit, with no default (SPEC §4). The result
  records the conversion and its inputs, and the converted value keeps a name that says it was converted. 🟡 The
  name of the φ′cv judgment, and whether the 1.10 factor is applied outside normally consolidated cohesive soils
  (warn, or refuse unless asked?), are for the spec. Verify Eq. 4-10 and Table 4-5 again from the source when
  hand-calculating the golden values.
- **The figure.** By depth: P01 with the row sources colored or marked by source, and each fit's value drawn
  as a line over its specimens' depth range. By unit: P07 with one column per source. 🟡 Whether that means new
  options on P01 and P07 or a new plot ID (which would be its own unit of work) is for the spec. The
  preference is to reuse P01 and P07.
- **Parameters exercised:** sheet 04 (φ′, c′) and sheet 05 (s_u), the two with more than one source today. The
  other M18 sheets (01–03, 15, 22) have one source each, so their stage D is `representative()` (M18 (b)) and
  the selection in (e).
- Golden values: the conversion hand-calculated from Kulhawy & Mayne, and a comparison table hand-built from the
  example data (Terrace φ′ from SPT, triaxial and shear box; s_u from UU, vane and SPT). The data needs
  site-like scatter, not points on a line.
- Docs: the statistics guide, site pages 04 and 05 (the conversion and the comparison), the API reference.

**Constraints:**
- SPEC §4: judgments (φ′cv, the significance level) have no defaults, resolve argument → `judgments=` → the
  project's file, and are recorded on the result. Correlations are compared as they come and never re-run with
  other inputs.
- SPEC §5: input rules (flags from the registry, counts add up, bands and non-plastic values left out and
  counted, censored values counted as bounds, H&F 7 percentiles, units); statistics designed for lab data, so SPT
  sources get the simple treatment; one calculation, many views; a figure and a table of the same rows agree.
- SPEC §5, derived results: a shear box φ′ and a triaxial φ′ don't pool unawares. Only the conversion makes
  them comparable, and the result says so.
- Never drop data silently: a source with no value for a unit is listed with its reason.
- No new dependencies.

**Out of scope:**
- **The selection as a judgment, model-set results, the Mohr–Coulomb set and ψ (Bolton 1986):** M18 (e).
  (e) reuses the φ′cv judgment this unit adds.
- **Rock discontinuity strength (sheet 22):** a joint's φj isn't converted or compared with a soil φ′.
- **Correcting the field vane** (Bjerrum's μ): a judgment for selection (SPEC §4), so it belongs to (e) if
  anywhere.
- **Standard errors or confidence intervals for the fits:** if the comparison needs one, the spec adds it to
  the fit's result in its own build step, with a test.
- **The two-panel correlation profile (TODO #38):** related, but a P01 feature of its own.
- **Censored comparisons in `compare()`** (TODO #51).

**SPEC and TODO touched:**
- SPEC §12.4: the M18 row becomes (a)–(e), with (d) sources compared and (e) the selection, model sets and the
  Mohr–Coulomb set.
- SPEC §5: "Statistics feed stage D" (the comparison, once built); derived results (the shear box conversion
  is no longer pending).
- SPEC §4: the φ′cv judgment in the judgments list (`src/hangtu/_judgments.py`).
- TODO #32: ψ's φ′cv now comes from (d), and the rest of #32 moves to (e).
- Site pages 04 and 05; the parameter index (sheets 04 and 05, stage D part built) at close.

## Spec
Numbered items are this section's decisions. The intent's 🟡 items are settled here: name and home
(decision 9), tests (decision 14), the φ′cv judgment and the 1.10 factor (decisions 1 and 5), and the figure
(decisions 18 and 19). The spec review (2026-11-05) settled the names, the `conversion_name` pattern, the tick
label, the example data (decision 20) and the fit's line in its source's color (decision 18).

### Sources
- **K&M 1990:** Kulhawy, F.H. & Mayne, P.W. (1990). *Manual on Estimating Soil Properties for Foundation Design*.
  EPRI EL-6800. Checked against the EPRI scan on 2026-11-05:
  - Eq. 4-10, **p. 4-12** (the intent's "p. 4-25" is wrong, and so is the citation on site page 04 and draft
    sheet 04, which the close-out fixes): tan φds = tan φpsc cos φcv. The same page says "for typical ranges of
    φcv, the PSC values from this equation will be some 2 to 7 degrees higher than the direct shear values".
  - Table 4-2, p. 4-14, cohesionless soils: PSC = 1.12 φtc; DS = tan⁻¹[tan(1.12 φtc) cos φcv].
  - Table 4-5, p. 4-25, normally consolidated cohesive soils: PSC = 1.10 φtc; DS = tan⁻¹[tan(1.10 φtc) cos φcv],
    with footnote 2 on the DS row: "Speculative, based on results from sand". TC is defined as CIUC, CK0UC or CAUC.
  - p. 4-10: φcv "is unique and independent of test type. The same is true for the residual friction angle".
- **H&F 1996:** Hyndman & Fan (1996), definition 7, as everywhere in `ht.stats` (SPEC §5). Its inverse gives
  the percentile rank (decision 13). No new source.

### The conversion
```python
ht.analysis.friction_angle_from_shear_box(
    fit,                                  # a ShearBoxFit
    *,
    soil,                                 # "cohesionless" | "normally_consolidated_cohesive", or {geology_unit: one of them}
    critical_state_friction_angle=None,   # judgment, in degrees: a number, or {geology_unit: degrees}
    judgments=None,
) -> ShearBoxConversion
```
The names `friction_angle_from_shear_box` and `ShearBoxConversion` aren't in the registry or code. The
correlation-style name `effective_friction_angle_kulhawy_mayne_1990` is already taken by the SPT correlation.

1. **The equations, and the ratio by soil type** (K&M Eq. 4-10, Tables 4-2 and 4-5):
   - φ′psc = tan⁻¹(tan φ′ds / cos φ′cv), which is Eq. 4-10 solved for φ′psc;
   - φ′tc = φ′psc / r, with r = 1.12 for `soil="cohesionless"` (Table 4-2) and r = 1.10 for
     `"normally_consolidated_cohesive"` (Table 4-5).

   This settles the intent's question about applying 1.10 outside normally consolidated cohesive soils. The
   source gives a different ratio for cohesionless soils, so each soil takes its own ratio, and both are verified.
   Overconsolidated cohesive soils, rock and joints aren't covered by either table, so `soil=` accepts only the
   two values above. Any other value is an error that says what the tables cover and suggests comparing
   `peak_friction_angle` unconverted instead. hangtu offers no `ratio=` of the engineer's own: that would be an
   unpublished correlation.
2. **Peak angle only, every line kind.** The free line and the line through the origin are both converted, and
   the result keeps the fit's main line first.
   - Residual angles aren't converted: K&M p. 4-10 says φr is independent of test type. The docs say so.
   - The cohesion intercept isn't converted, because K&M give no conversion for it. The result keeps
     `peak_cohesion` as fitted, with a note, and `compare_sources()` refuses a conversion for
     `value="effective_cohesion"` (decision 10).
3. **`soil=` is required and never inferred** from `soil_class` or a USCS symbol (SPEC §4, the correlations
   principle). A mapping keyed by geology unit needs the fit grouped by `geology_unit`. A unit the mapping
   doesn't list is an error that names the unit.
4. **What a conversion asserts.** Converting treats the shear box stresses as effective and the test as drained
   (ASTM D3080), which `shear_box_fit()` doesn't assume (M17 (b), decision 2). So the result always notes it.
   For `normally_consolidated_cohesive`, the note also quotes Table 4-5's footnote: speculative, based on results
   from sand.
5. **The φ′cv judgment, `critical_state_friction_angle`** (SPEC §4):
   - It is keyed by `geology_unit`, with no project-wide value: φ′cv is set by mineralogy and grading (site
     page 04). Every entry needs a `reason`, as `fixed_intact_compressive_strength` does, because the value
     comes from a ring shear test, a correlation from PI, or the literature, and the review needs to know which.
     The angle is in degrees.
   - Resolution: the argument → `judgments=` → the Project's file that the shear box fit's input carried
     (decision 17) → an error naming the judgment, its key and how to set it.
   - A number as the argument is accepted only for a fit with one group. A fit with more groups needs a mapping,
     because a single value would be coarser than the key allows (SPEC §4).
   - A value outside 0 < φ′cv < 90° is an error. hangtu gives no plausibility warning, because no range has been
     verified for one.
   - The result records the value, the key and the source, as every judgment is recorded.
   - (e) reuses the judgment for ψ (Bolton 1986).
6. **Validity limit: a peak below critical state.** When φ′ds < tan⁻¹(sin φ′cv), Eq. 4-10 gives φ′psc < φ′cv,
   a peak below the critical-state angle. That is a measured peak the equation doesn't describe.
   - The value is still converted and flagged in `below_critical_state`, and a warning names the groups.
   - A fitted φ′ds ≤ 0, or a group the fit couldn't fit, gets no value and a `no_conversion_reason` (the fit's
     own `no_fit_reason` where there is one).
7. **The result, `ShearBoxConversion`,** is a derived result (SPEC §5), on `_DerivedResult`.
   - `.to_frame()` gives one row per group and line kind, with these columns: the keys, `line_kind`,
     `peak_friction_angle`, `critical_state_friction_angle`, `conversion_soil`, `plane_strain_friction_angle`,
     `effective_friction_angle`, `conversion_name`, `below_critical_state`, `count`, the normal stress range,
     `no_conversion_reason`.
   - `conversion_name` is `"friction_angle_from_shear_box_kulhawy_mayne_1990"`.
   - The result keeps the fit's peak points, with their depths (decision 17), and the judgment.
   - **The converted value is named `effective_friction_angle`, with `conversion_name`** (spec review), the same pattern
     as a correlation's estimate with `correlation_name` (SPEC §5). The converted value estimates the same
     parameter as a triaxial φ′. `conversion_name` is the name that says it was converted. It is registered as a
     source column (`statistics: {role: source}`), so a frame with triaxial and converted rows can't pool them
     unawares. A column of its own (`converted_effective_friction_angle`) was turned down: P01, P07 and
     `compare_sources()` would need to be told it is φ′.
   - New registry columns (checked against the registry, code and docs on 2026-11-05; none is used):
     `critical_state_friction_angle`, `plane_strain_friction_angle`, `conversion_name`, `conversion_soil`.

### The comparison
```python
ht.stats.compare_sources(
    *sources,                 # DataFrames of rows; MohrCoulombFit; ShearBoxConversion
    value,                    # the parameter, a registry column: "effective_friction_angle", "undrained_shear_strength", …
    by="geology_unit",
    percentiles=DEFAULT_PERCENTILES,   # describe()'s
    include_assumed=False,
    units=None,               # {column: unit}, applied to every DataFrame source
    display_units=None,
) -> SourceComparison
```
8. **Inputs follow SPEC §5's rules** through the calculation `describe()` uses, applied per unit and source:
   - flags come from the registry;
   - bands, non-plastic values and blanks are left out and counted;
   - assumed values are used only with `include_assumed=True`;
   - censored values enter at their value and are counted (`count_at_least`, …);
   - counts add up;
   - percentiles follow H&F 7, each with its floor.

   Units resolve per DataFrame as for an analysis (§2.6). Everything is converted to `display_units` if given,
   else to the unit of the first source that has one, and angles are in degrees. A DataFrame whose value has no
   unit is an error naming its position among the sources.
9. **The name and home: `ht.stats.compare_sources()`,** returning `SourceComparison`. It lives in `ht.stats`
   because it summarizes values, as `describe()` does. It takes the frames and fit results the engineer already
   has, and never runs a correlation or a fit again (SPEC §4).
10. **What each source is, and its label** (`parameter_source`, a new registry column, a source column):
    - **A DataFrame** gives its rows of `value`. Each row's label is the non-blank values of the registry's source
      columns (`correlation_name`, `test_type`, `source`, `conversion_name`, in registry order), joined by ", ".
      So one frame can hold several sources, such as two correlations or three test types. A row with none of
      them is labeled "(no source given)" and is still a source of its own, never dropped.
    - **A `MohrCoulombFit`** gives the main fit of each group (its first: `stages` as the fit ordered them), for
      `effective_friction_angle` or `effective_cohesion`. Its label is "Mohr-Coulomb fit" with its points' test
      types, such as "Mohr-Coulomb fit (CD, CU)" (a hyphen, as the fit's own text writes it).
    - **A `ShearBoxConversion`** gives its main line's converted value, for `effective_friction_angle` only,
      labeled "shear box, converted (Kulhawy & Mayne 1990)".
    - **Errors:**
      - a `ShearBoxFit` with `value="effective_friction_angle"` (or `effective_cohesion`) is an error that names
        `ht.analysis.friction_angle_from_shear_box()` (SPEC §5: no pooling unawares);
      - a total stress `MohrCoulombFit` with an effective `value` is an error;
      - a `HoekBrownFit` is an error, because it is rock and out of scope;
      - any `value` a source doesn't give is an error naming what the source gives.
    - Two sources with the same label take " (source 2)", " (source 3)" after it, in the order passed, so
      nothing merges silently.
11. **A fit's groups must be keyed by every `by` column.** Otherwise it's an error that names the fit's keys and
    says to fit again with `group_by=`. Extra keys, such as `sample_reference`, give several fit values in a unit.
    Fitted per sample, those values are a sample of the unit and are summarized like rows. One fit per unit is a
    single value, with n = 1, so no statistic beyond it is given.
12. **Never pooled, and no `pool=`.** Grouping by source is the point of the comparison (intent). Each unit and
    source pair is summarized on its own. A fit source also reports `count_points` (its fitted points). Where the
    unit has one fit, it also reports `r_squared`, the normal stress range and `stages` or `line_kind`. No
    standard error is given (out of scope).
13. **A fit against a row source's spread: a position, never a test.** For each unit, each fit source with
    exactly one value there, and each DataFrame source with at least one counted value:
    - `position` is `"below"`, `"within"` or `"above"` the row source's lowest to highest value (bounds at their
      value).
    - When the fit value is within that range and the row source has at least 4 values (the P25/P75 floor,
      SPEC §5), `percentile_rank` gives its rank in percent. The rank is the inverse of H&F 7: for
      x₍ᵢ₎ ≤ v ≤ x₍ᵢ₊₁₎ (0-based, sorted), h = i + (v − x₍ᵢ₎)/(x₍ᵢ₊₁₎ − x₍ᵢ₎) and rank = 100 h / (n − 1), so the
      H&F 7 quantile at the rank is v again. A value equal to a run of tied values takes the middle of the run.
14. **No tests in the comparison** (settles the intent's 🟡). SPEC §5 says selection pools units "on geology and
    plots; tests are a check", and SPT and the correlations from it get the simple treatment (decided
    2026-11-02). The comparison stays descriptive and takes no `significance_level`. `compare()` remains the
    check for two row sources, and the docs show it on UU against field vane.
15. **Nothing is dropped silently.** The units listed are the union of every source's `by` keys. Each source and
    unit pair with no value gets a row with `count` 0 and a `no_value_reason`:
    - "no rows in this unit";
    - "all n rows left out" (the counts give the reasons);
    - the fit's `no_fit_reason`;
    - the conversion's `no_conversion_reason`.
16. **The result, `SourceComparison`,** has kind *property* (it summarizes values; the parameter is chosen in
    (e)), on the shared base (SPEC §5):
    - `.to_frame()` gives one row per unit and source, units in `describe()`'s order and sources in the order
      passed. Its columns: the `by` keys, `parameter_source`, `source_kind` (`"rows"` or `"fit"`), `count`,
      `describe()`'s statistics and counts left out, `count_points`, `r_squared`, `lowest_normal_stress`,
      `highest_normal_stress`, `shallowest_depth`, `deepest_depth`, `no_value_reason`.
    - `.positions()` gives one row per unit, fit source and row source, with the fit value, the row source's
      count, lowest and highest values, `position` and `percentile_rank`.
    - `.values()` gives the long frame the figures draw. It has the `by` columns, `parameter_source`, `value`, and
      where present `loca_id`, `depth`, `elevation`, `ground_level` and the flag columns, with `attrs["units"]`.
      Every row is kept, including those left out of the statistics, because the figures count them as the
      table does. A fit value is one row at the middle of its points' depths, with `depth_top` and `depth_base`
      at the shallowest and deepest, so P01 draws its depth range as an interval bar (P01 §7). A fit whose points
      have no depth has a blank depth, and P01 counts it.
    - `.profile(**kwargs)` draws one unit, named by its `by` column (`.profile(geology_unit="Terrace")`, required
      when the comparison has more than one unit): `ht.plot.profile()` of that unit's `.values()` rows, with
      `color_by="parameter_source"` and `stats_box=True`. P01's stats box gives one line per source when
      `color_by` is a source column (P01 §8), but it summarizes each source over every row drawn, so only per
      unit do the figure and `.to_frame()` agree.
    - `.geology_unit_comparison(**kwargs)` returns P07 with `split_by="parameter_source"` and
      `color_by="parameter_source"` (decision 19).
    - `.to_dict()` (JSON) and the printed summary work as on the other results.
    - Every column name is checked against the registry in the build.

### Changes to the fits
17. **The fits keep what the comparison and the conversion read.**
    - `mohr_coulomb_fit()` and `shear_box_fit()` keep `depth`, `elevation` and `ground_level` with each point
      when the input has them (added to `_IDENTIFIERS`).
    - Every derived result records the input's `attrs["judgments_file"]`, on `_DerivedResult`, so the conversion
      can reach the Project's file.
    - Their values don't change. `.to_dict()` gains the fields.

### The figures (reuse P01 and P07; no new plot ID)
18. **By depth: P01 unchanged.** Row sources are colored by `parameter_source`, fits are drawn as points with
    interval bars over their specimens' depths, and the stats box has a line per source (decision 16). P01
    draws an interval bar in the marker's color, so a fit's bar is in its source's color (spec review). A dashed design line
    per fit (P01's `design_lines=`) would be gray for every source, so it isn't used.
19. **By unit: P07 gains `split_by=`** (P07 §4, §7, §10–§12, changed in this commit). It promotes the "grouping
    by something other than geology unit" item from P07's future enhancements:
    - Each geology unit gets one sub-row per value of the `split_by` column, consecutive under the unit, in
      order of first appearance.
    - The tick label is "Terrace · Mohr-Coulomb fit (CD)".
    - Each sub-row has its own summary and count, so a sub-row split by a source column never "mixes sources".
    - A unit's baseline is drawn once, on its first sub-row.
    - `color_by` also accepts the `split_by` column, and the legend then has one entry per value.
    - `geology_unit_comparisons()` takes `split_by=` too.
    - With `split_by=None`, P07 is unchanged.

### Data and docs
20. **Example data: added to site.ags, the CSVs written from it** (spec review: every example is AGS
    first). site.ags has one multistage CDM specimen and one shear box sample in Terrace, and its s_u tests are
    in Alluvium only, which is too thin to compare. So the build:
    - adds TRIX/TREG/TRET triaxial specimens (CD, several holes and depths) and SHBG/SHBT shear box samples in
      Terrace, and UU, laboratory vane, field vane and hand penetrometer tests in Alluvium, through
      `tests/data/_make_examples.py`, with site-like scatter (CoV about 0.1 for φ′ and 0.3 for s_u, skew, one
      outlier). Each new test draws from its own seeded sequence, as `TRIAXIAL_SAMPLES` does, so no existing
      value changes;
    - writes `triaxial.csv`, `shear_box.csv` and `strength.csv` from the project (`p.triaxial()`,
      `p.shear_box()`, `p.undrained_strength()`) in their template shapes, as `write_csvs()` writes `spt.csv`;
    - updates the tests and pages whose counts of site.ags rows move, in the same commit.
    `rock_triaxial.csv` (M17 (c)) isn't in site.ags; moving it there is outside this unit. The golden values use
    the small fixtures below, not the example data.
21. **Docs:**
    - site page 04: the conversion, the comparison, and the citation fixed to Eq. 4-10 p. 4-12, Tables 4-2 p. 4-14
      and 4-5 p. 4-25;
    - site page 05: the comparison, with `compare()` on UU against field vane;
    - the statistics guide, `docs/analysis/statistics.md` §5;
    - the P07 page;
    - the judgments guide (`critical_state_friction_angle`);
    - API reference entries for `compare_sources`, `SourceComparison`, `friction_angle_from_shear_box` and
      `ShearBoxConversion`.

### Golden values
The hand values below were computed with Python's `math` and NumPy, from the formulas above, not the
implementation. Tolerance: 1e-6 relative for the statistics and the conversion. For angles fitted from the
σ′1 values, which are rounded to 3 decimals, the tolerance is 1e-3°.
- **G1, conversion** (φ′ds, φ′cv → φ′psc; φ′tc cohesionless / normally consolidated cohesive):
  - 30°, 32° → 34.2470°; 30.5777° / 31.1336°.
  - 28°, 30° → 31.5485°; 28.1683° / 28.6804°.
  - 25°, 33° → 29.0744°; 25.9593° / 26.4313°. Below critical state: tan⁻¹(sin 33°) = 28.5744° > 25°, so it
    warns and flags.
  - Each φ′psc − φ′ds (4.25°, 3.55°, 4.07°) is within K&M's "2 to 7 degrees" (p. 4-12).
- **G2, φ′ in Terrace** (`by="geology_unit"`):
  - **Correlation A** (`correlation_name` Hatanaka & Uchida): 31.2, 34.8, 36.1, 33.0, 38.4 (at least, by
    `correlation_qualifier`), 35.5, 32.7, 37.9. n 8, `count_at_least` 1, mean 34.95, s 2.540529, CoV 0.072690,
    median 35.15. P25 32.925 and P75 36.55 aren't among describe()'s default percentiles (5, 25, 75, 95), so the
    test passes `percentiles=(25, 75)`. P5 and P95 are blank, because each needs 20 values.
  - **Correlation B** (Kulhawy & Mayne SPT): 34.0, 36.5, 39.2, 35.1, 41.0, 37.3, plus one band row and one blank.
    n 6, `count_band` 1, `count_blank` 1, mean 37.183333, s 2.591846, P25 35.45, median 36.9, P75 38.725.
  - **Triaxial fit:** CD stages with σ′3 50, 100, 200 kPa and σ′1 192.592, 385.184, 770.368 kPa (c′ 0,
    φ′ 36°: (1 + sin 36°)/(1 − sin 36°) = 3.851840), at depths 4.0, 6.5 and 9.0 m. φ′ is 36.000°. Its row in
    `.values()` has depth 6.5, `depth_top` 4.0 and `depth_base` 9.0.
    - Against A: within, rank 69.0476 % (h = 4 + 0.5/0.6, n − 1 = 7).
    - Against B: within, rank 32.8571 % (h = 1 + 0.9/1.4, n − 1 = 5).
    - H&F 7 of A at 69.0476 % and of B at 32.8571 % both give 36.000.
  - **Shear box, converted:** τ = σn tan 30° at σn 50, 100, 200 kPa (28.867513, 57.735027, 115.470054),
    cohesionless, φ′cv 32° → 30.5777°. It is below both A and B, so it has no rank.
  - **Alluvium:** correlation A only. B is listed with count 0 and "no rows in this unit". The triaxial fit has
    one stage there and is listed with its `no_fit_reason`.
- **G3, s_u in Alluvium:**
  - UU 42, 55, 61, 48 kPa: n 4, mean 51.5, s 8.266398, P25 46.5, median 51.5, P75 56.5.
  - Field vane 58, 71, 66 kPa: n 3, mean 65.0, s 6.557439, with P25 and P75 blank (each needs 4 values).
  - Stroud (1974) estimates 1200, 1500, 1350 psf, converted to kPa (× 0.047880259): 57.456311, 71.820388,
    64.638350, with mean 64.638350 and s 7.182039.
  - With `display_units="US"`, the UU mean is 1075.600 psf.
  - `.positions()` is empty, because there is no fit source.

### Acceptance criteria
1. **Conversion:** G1 for both soils. A `soil=` mapping by unit works. Both line kinds are converted. Residual
   angles and `peak_cohesion` are kept unconverted, with a note. The notes of decision 4 are on every result.
2. **`soil=`:** missing, or any value but the two, is an error that names them and says what K&M's tables
   cover. A mapping missing a unit is an error that names the unit.
3. **φ′cv:** it resolves from the argument, from `judgments=` and from the Project's file through the fit. When
   absent, the error names `critical_state_friction_angle`, its key and how to set it. A number for a fit with
   several groups is an error, as are a value outside (0, 90)° and an entry without a reason. The result records
   the value, key and source.
4. **Below critical state:** G1's third case warns and names the group, and `below_critical_state` is true. A
   fit with no line gives no value, with its reason.
5. **The comparison table** matches G2 and G3: the statistics and the counts left out per unit and source, with
   counts adding up to each source's rows in the unit.
6. **Positions** match G2: the ranks, "below", no rank under 4 values, and H&F 7 at the rank returns the value.
7. **Sources and labels:** labels follow decision 10. Repeated labels get suffixes. Each error of decisions 10
   and 11 fires and names what to do.
8. **Nothing dropped:** every unit and source pair is listed, and the empty ones give their reasons (G2,
   Alluvium).
9. **Units:** G3 in kPa and US. A DataFrame without a unit for `value` is an error naming its position.
10. **Figures:** `.profile()` draws one unit with no warning, and needs the unit named when there are several.
    It has one stats box line per source, and those numbers equal that unit's rows of `.to_frame()`. Each fit
    is drawn as an interval bar from `depth_top` to `depth_base`, and a fit with no depth is counted in the
    footnote. `.geology_unit_comparison()` draws one sub-row per source, and its
    percentiles equal `.to_frame()`'s.
11. **P07 `split_by=`:** sub-rows, their order and tick labels, the counts, the baseline once per unit, and a
    color legend when `color_by` is the split column. The grid takes it. With `split_by=None` the existing P07
    tests pass unchanged.
12. **Fits:** the points of `mohr_coulomb_fit()` and `shear_box_fit()` carry `depth` (and elevation, ground
    level) when given. Derived results record `judgments_file`. Fitted values are unchanged. `.to_dict()` of
    every new and changed result is JSON.
13. **Docs:** reference entries exist (a test fails without them). The examples run in `prepare_site.py`. The
    PNGs `docs/plots/img/P07-sources.png` (by unit) and `docs/plots/img/P01-sources.png` (by depth), in US and
    SI, are looked at and committed (CLAUDE.md, visual check).

### Changes to other docs
- **SPEC §4, judgment inputs** (this commit): φ′cv joins the examples of judgments.
- **SPEC §5, derived results** (this commit): the shear box conversion is decided, by K&M Eq. 4-10 with a ratio
  by soil type and the φ′cv judgment. The converted value is `effective_friction_angle` with `conversion_name`.
- **SPEC §5, "Statistics feed stage D"** (this commit): `compare_sources()` gives the comparison. It is
  descriptive, a fit is placed against a row source's spread and never tested, and `compare()` is the check.
- **P07 spec** (this commit): `split_by=`, in §4, §7, §10, §11 and §12; the Related row; the item removed from
  §15.
- **At close-out:**
  - `docs/analysis/statistics.md` §5;
  - site pages 04 and 05, and the citation in draft sheet 04;
  - the parameter index (sheets 04 and 05, stage D part built);
  - TODO #32 (ψ's φ′cv is now a judgment; the rest moves to (e));
  - SPEC §12.4's M18 status;
  - CLAUDE.md's "next".

## Plan
Draft, 2026-11-06. Eleven commits, each green: first the tests the step touches, then the CI command with
`-n 3`. Steps 1–6 run on Opus (the fits' new fields, the judgment, the conversion with its citations and validity
limit, the comparison's calculation). Steps 7–9 run on Sonnet (P07's `split_by=` and the example data; P07 §12
and the spec's counts decide correctness). Steps 10–11 run on Opus (the site pages' citations, the figures judged
against the spec, close-out). That makes two session boundaries, after 6 and after 9. A step past about 300
changed lines, not counting test data, splits as noted.

Reused, not rebuilt:
- **Stats:** `read_input`, `convert`, `scale`, `read_flags`, `choose_rows`, `group_keys`, `breakdown`,
  `source_mix`, `warn_left_out`, `warn_text` (`stats/_rows.py`); `summarize`, `check_percentiles`,
  `percentile_name`, `percentile_floor`, `DEFAULT_PERCENTILES`, `COUNTS`, the note builders (`stats/_describe.py`);
  `_Result`, `_plain`, `_table`, `_cell`, `_number` (`stats/_result.py`).
- **Fits:** `_DerivedResult` (`analysis/_derived.py`); `MohrCoulombFit.groups` (`stages`, `points`) and
  `ShearBoxFit.groups` (`strengths["peak"]["lines"]`, `points`); `_label`, `_names`, `_cell`
  (`analysis/_fit_groups.py`).
- **Judgments:** `Kind`, `KINDS`, `POSITIVE` (`_judgments.py`); `read_judgments`, `from_file`, `take`,
  `warn_unused` (`analysis/_judgment_values.py`), as `_hoek_brown_fit.py` uses them for
  `fixed_intact_compressive_strength`.
- **Units:** `resolve_units`, `convert`, `to_display` (`hangtu.units`).
- **Plots:** `ht.plot.profile()` with `intervals=`, `color_by=` a source column and `stats_box=` (P01 §7, §8),
  unchanged; `geology_unit_comparison()`/`geology_unit_comparisons()` (`plot/_geology_units.py`), extended in
  step 7.

### 1. `M18: keep depths and the judgments file on fit results` (Opus)
- `analysis/_mohr_coulomb.py`, `analysis/_shear_box_fit.py`: `depth`, `elevation`, `ground_level` added to
  `_IDENTIFIERS`, so each point carries them when the input has them (decision 17). Fitted values unchanged.
  The depths are kept as given, so each fit also records `depth_units` (`{column: unit}` from `units=` →
  `attrs["units"]`; a column with no declared unit is left out, never guessed), which step 6's `.values()`
  reads (added in the build).
- `analysis/_derived.py`: `_DerivedResult` gains `judgments_file: str | None`, from the input's
  `attrs["judgments_file"]`; `mohr_coulomb_fit()`, `shear_box_fit()` and `hoek_brown_fit()` pass it.
- Tests: `tests/analysis/test_mohr_coulomb_fit.py`, `test_shear_box_fit.py`, `test_hoek_brown_fit.py` (AC 12):
  points carry depth, elevation and ground level when given and not when absent; `judgments_file` from a
  Project's frame and None from a hand-built one; `.to_dict()` is JSON; every existing golden unchanged.

### 2. `M18: add the critical_state_friction_angle judgment` (Opus)
- `src/hangtu/_judgments.py`: a `Kind` for `critical_state_friction_angle` (decision 5): keyed `values`, field
  `critical_state_friction_angle` (angle, degrees, through the units block as other angles), `by="geology_unit"`,
  no `project:` value, `reason_required=True`; a new open-interval check (0, 90) beside `POSITIVE`, with no
  `PLAUSIBLE` range. `ht.judgments()`'s docstring gains its entry and an example.
- `columns.yaml`: `critical_state_friction_angle` (angle, "Critical state friction angle, φ′cv",
  `ags: ["derived: docs/work/m18d-sources-compared.md"]`). `tests/test_registry.py` checks the name.
- Tests: `tests/test_judgments.py` (AC 3, file part): a valid entry reads, with its `str()` line; a missing
  reason, a `project:` value, 0 and 90 each raise naming the file and the entry.

### 3. `M18: convert a shear box φ′ to triaxial (Kulhawy & Mayne 1990)` (Opus)
- `src/hangtu/analysis/_shear_box_conversion.py` (new), exported with `ShearBoxConversion` in
  `analysis/__init__.py`:
  - `friction_angle_from_shear_box(fit, *, soil, critical_state_friction_angle=None, judgments=None)`: a
    non-`ShearBoxFit` raises naming what it takes;
  - `soil=` (decisions 1, 3): required, the two values or a mapping by `geology_unit`; anything else raises
    naming the two values, what Tables 4-2 and 4-5 cover, and that `peak_friction_angle` can be compared
    unconverted; a mapping needs the fit grouped by `geology_unit`, and a missing unit raises naming it;
  - φ′cv (decision 5): the argument (a number only for a one-group fit, else a mapping by unit) →
    `judgments=` → the file in `fit.judgments_file` → an error naming the judgment, its key and how to set it.
    `read_judgments()` gains a form that takes the recorded path instead of a frame's attrs. Out of (0, 90)°
    raises. Value, key and source recorded;
  - the equations (decision 1) for both line kinds of the peak strength, main line first (decision 2); residual
    and `peak_cohesion` kept unconverted, with notes; decision 4's notes on every result, Table 4-5's footnote
    for the cohesive soil;
  - decision 6: below critical state converted, flagged in `below_critical_state`, one warning naming the
    groups; φ′ds ≤ 0 or no line gives no value and `no_conversion_reason` (the fit's `no_fit_reason` first);
  - `ShearBoxConversion(_DerivedResult)`: `.groups` (with the fit's points and depths), `.to_frame()` with
    decision 7's columns in order and `attrs["units"]`, `__str__`, `.to_dict()`;
  - docstring per the sheets' `TEMPLATE.md` checklist: Eq. 4-10 (K&M 1990 p. 4-12), Tables 4-2 (p. 4-14) and 4-5
    (p. 4-25, with footnote 2), the "2 to 7 degrees" remark, the drained and effective-stress assumption, residual
    unchanged (p. 4-10), the validity limit, an example on a hand-built fit. Each page re-checked against the
    scan while writing it.
- `columns.yaml`: `plane_strain_friction_angle`, `conversion_name` (`statistics: {role: source}`),
  `conversion_soil`, checked by `tests/test_registry.py`.
- `docs/site/reference/analysis.md`: `friction_angle_from_shear_box`, `ShearBoxConversion` (AC 13).
- Tests: `tests/analysis/test_shear_box_conversion.py` (new), on hand-built shear box frames: AC 1 (G1 for both
  soils, the mapping, both line kinds, residual and cohesion kept, the notes), 2, 3 (resolution from argument,
  `judgments=` and a Project's file in `tmp_path`; the number-for-several-groups and range errors), 4.

### 4. `M18: compare a parameter's row sources by geology unit` (Opus)
- `src/hangtu/stats/_compare_sources.py` (new), exported with `SourceComparison` in `stats/__init__.py`:
  - `compare_sources(*sources, value, by="geology_unit", percentiles=..., include_assumed=False, units=None,
    display_units=None)` for DataFrame sources in this step; other types raise "not yet" until step 5;
  - each frame read through `read_input`/`convert`/`read_flags`/`choose_rows` (decision 8), units per frame,
    converted to `display_units` or the first frame's unit; a frame without a unit raises naming its position;
  - labels (decision 10): the registry's source columns in registry order, joined by ", ", "(no source given)"
    for none, " (source 2)" suffixes for repeats across sources;
  - per unit and label, `summarize()` plus the counts (decisions 12, 15); units the union of `by` keys, in
    `describe()`'s order; empty pairs with count 0 and `no_value_reason`;
  - `SourceComparison(_Result)`, kind `"property"`: `.to_frame()` with decision 16's columns (the fit columns
    blank here), `__str__`, `.to_dict()`.
- `columns.yaml`: `parameter_source` (text, `statistics: {role: source}`) and `source_kind`, checked by
  `tests/test_registry.py`.
- `docs/site/reference/stats.md`: `compare_sources`, `SourceComparison` (AC 13).
- Tests: `tests/stats/test_compare_sources.py` (new): AC 5 for G2's correlations A and B and all of G3 (counts
  adding up per unit and source), 7's labels and suffixes, 8's "no rows in this unit" and "all n rows left out",
  9 (G3 in kPa and US, the psf Stroud frame, the unitless-frame error).

### 5. `M18: place fit values among the sources they're compared with` (Opus)
- `_compare_sources.py`:
  - `MohrCoulombFit` sources (the main fit per group, label with test types) and `ShearBoxConversion` sources
    (the main line) (decision 10); the errors for a `ShearBoxFit` (naming the conversion), a total-stress fit with
    an effective `value`, a `HoekBrownFit`, a conversion asked for `effective_cohesion`, and any `value` a source
    doesn't give;
  - decision 11: fits keyed by every `by` column, else an error naming the keys and `group_by=`; several fits per
    unit summarized like rows, one fit reported as a value with `count_points`, `r_squared`, the stress range,
    `stages`/`line_kind`, and its depths;
  - empty pairs from `no_fit_reason` and `no_conversion_reason`;
  - `.positions()` (decision 13): position against the row source's range, `percentile_rank` by the inverse of
    H&F 7 from 4 values, the middle of a tied run; a private helper beside `summarize()`.
- Tests, same file: AC 5 and 6 on G2 (triaxial fit and converted shear box against A and B, the ranks, "below",
  H&F 7 at the rank returns 36.000), 7's errors, 8 (Alluvium: B with "no rows in this unit", the fit with its
  `no_fit_reason`), a per-sample fit summarized like rows, `.positions()` empty for G3, `.to_dict()` JSON.
- If step 4 or 5 passes about 300 lines, the views of decision 16 (`__str__`, `.to_dict()`) move to their own
  commit after 5.

### 6. `M18: draw the sources compared against depth` (Opus)
- `_compare_sources.py`: `.values()` (decision 16): the long frame with `by`, `parameter_source`, `value` and,
  where present, `loca_id`, `depth`, `elevation`, `ground_level` and the flag columns, every row kept,
  `attrs["units"]`; a fit as one row at the middle of its points' depths with `depth_top`/`depth_base`, blank
  depth when its points have none. `.profile(**kwargs)` calls `ht.plot.profile(values, value,
  color_by="parameter_source", stats_box=True, intervals="auto", **kwargs)`.
- If P01 warns on rows with no interval beside rows with one, or counts the fits differently from the table,
  stop: that is a change to P01's spec, not a build detail.
- **Decided in the build (2026-11-06):** P01's stats box summarizes a source over every row it draws, so
  across several units it pools them and can't equal the per-unit table. `.profile()` therefore draws one
  unit, named by its `by` column (`.profile(geology_unit="Terrace")`), required when the comparison has more
  than one unit (an error lists the units). P01 unchanged. Defaults `figsize=(7, 7)` and `legend="bottom"`:
  at P01's default size the long source names collapse the axes (matplotlib's constrained_layout warning).
  Decision 16 and AC 10 say "per unit" (this step's commit). Plot tests need
  `ht.settings.override(hints=False)` for P01's ground-level hint.
- Tests: `tests/stats/test_compare_sources_views.py` (new), AC 10's depth part: `.values()` row counts and G2's
  fit row (6.5, 4.0, 9.0); `.profile()` draws with no warning, one stats box line per source whose numbers
  equal `.to_frame()`'s, an interval bar per fit, a fit without depth counted in the footnote.

### 7. `P07: split each geology unit into sub-rows by a column` (Sonnet)
- `plot/_geology_units.py`: `split_by=` on `geology_unit_comparison()` and `geology_unit_comparisons()` (P07
  §4, §7, §10, §11, already specified): sub-rows per value in order of first appearance, "(blank)" last;
  tick labels "unit · value"; each sub-row summarized and counted on its own through the existing summary path;
  the thin rule between units; the baseline once per unit, on its first sub-row; `color_by` also the split
  column, with one legend entry per value; the errors of §11's new rows.
- Tests: `tests/plot/test_geology_unit_comparison_split.py` (new), P07 §12's `split_by=` criteria and AC 11; the
  existing P07 tests unchanged and green.

### 8. `M18: compare the sources geology unit by geology unit` (Sonnet)
- `_compare_sources.py`: `.geology_unit_comparison(**kwargs)` calls P07 with `split_by="parameter_source"`,
  `color_by="parameter_source"` (decision 19).
- **Decided in the build (2026-11-06):** P07 draws a summary only from `summary_min_count` values (5 by
  default, a drawing threshold), but the table gives P25 and P75 from 4. So `.geology_unit_comparison()` passes
  `summary_min_count=1` and the percentile floors alone decide, and the figure has a bar wherever the table has
  the percentiles. It needs `by="geology_unit"` alone (an error otherwise), passes the units in the table's
  order and the comparison's `display_units`, and defaults to `legend="bottom"` and a 9 in wide figure, for the
  long source names. P07 never summarizes assumed values, so with `include_assumed=True` it warns when there
  are any. P07 unchanged.
- Tests: `test_compare_sources_views.py`, AC 10's unit part: one sub-row per source, percentiles equal to
  `.to_frame()`'s, no "mixes sources".

### 9. `M18: add triaxial, shear box and s_u tests to the example site` (Sonnet)
- `tests/data/_make_examples.py` (decision 20): CD TRIX/TREG/TRET specimens in Terrace (several holes and depths)
  and SHBG/SHBT samples in Terrace; UU, laboratory vane, field vane and hand penetrometer tests in Alluvium; each
  from its own seeded sequence, CoV about 0.1 for φ′ and 0.3 for s_u, skew, one outlier, so no existing value
  changes (checked by diffing the regenerated `site.ags` against the old one: only added rows). `write_csvs()`
  writes `triaxial.csv`, `shear_box.csv` and `strength.csv` in their template shapes. `judgments.yaml` gains a
  `critical_state_friction_angle` for Terrace with its reason. The module docstring says what was added.
- `src/hangtu/examples/data/`: regenerated files.
- The tests and pages whose counts of site.ags rows move (found by the full suite and `prepare_site.py`),
  updated in this commit.
- Tests: the full suite; `tests/test_examples.py` reads the new CSVs.

### 10. `M18: document the sources compared and the shear box conversion` (Opus)
- `docs/site/examples/sources-compared-friction-angle.py` and `sources-compared-undrained.py` (new), on the
  example site: φ′ in Terrace from SPT correlations, the triaxial fit and the converted shear box; s_u in Alluvium
  from UU, vane, hand penetrometer and Stroud, with `compare()` on UU against field vane. `prepare_site.py` runs
  them.
- Site pages 04 (the conversion, the comparison, the citation fixed to Eq. 4-10 p. 4-12, Tables 4-2 p. 4-14 and
  4-5 p. 4-25, re-checked against the scan) and 05 (the comparison, `compare()` as the check); draft sheet 04's
  citation; `docs/site/plots/geology-unit-comparison.md` (`split_by=`); `docs/site/guides/judgments.md`
  (`critical_state_friction_angle`); `docs/analysis/statistics.md` §5.
- `docs/plots/img/P01-sources-us.png`, `P01-sources-si.png`, `P07-sources-us.png`, `P07-sources-si.png` at 100
  dpi from the example site, looked at against decisions 18 and 19 and P07 §7 (AC 13).
- Tests: `tests/docs/test_site.py`; `zensical build --clean --strict`.

### 11. `M18: close out (d), sources compared` (Opus)
- `SPEC.md`: §4 (φ′cv among the judgments, if the spec commit didn't), §5 derived results and "Statistics feed
  stage D" checked against what was built, §12.4's M18 row: (d) done, (e) next.
- `docs/drafts/parameters/README.md`: sheets 04 and 05, stage D part built.
- `docs/TODO.md` #32: ψ's φ′cv is the judgment; the rest moves to (e).
- `CLAUDE.md`: "Done through … M18 (a)–(d)", next M18 (e).
- Each acceptance criterion reported met or not, with evidence; anything a future session would get wrong
  written where it will be read.
