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
