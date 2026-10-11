# TODO

Items to think through or research. Each item notes who owns it and the SPEC.md section it affects. Where you asked for a recommendation, Claude's view is included.

- **Owner key:** **You** = engineering judgment or research you want to do yourself. **Claude** = verification or build-time work.
- When an item is resolved, move the decision into SPEC.md and delete it here.

---

## Project

### 0. Rename the package · You · README, SPEC (throughout), pyproject.toml, repo directory · **Decide before the first PyPI release (milestone M5)**
**Why:**
- DIGGS support is on the roadmap.
- The target audience is US engineers, who are unfamiliar with both AGS and DIGGS; they work with .xlsx and .pdf. The name shouldn't assume they know either format.
- "AGS" is the acronym of a trade body whose official library is `python-ags4`, so `ags-kit` could look endorsed.

Keep "AGS" and "DIGGS" in the PyPI description, keywords and README so the package is still easy to find.

**Candidates free on PyPI (checked 2026-10-10):**
- `geotechkit` / `geotech-kit` (Claude's pick: clear to US and UK engineers, and not tied to a file format);
- `gikit` (second choice: short, but "GI" is UK/AU jargon);
- `borekit`, `borehole-kit`, `stratakit`, `subsurfacekit`, `soilkit`.

Check that the chosen name is still free on PyPI right before deciding.

**Steps once chosen:**
- update `pyproject.toml` (name and description);
- change the import name `ags_kit` → new name in SPEC, README and docs;
- update the `ak.` alias in the examples if desired;
- rename the repo directory;
- re-check PyPI availability right before the first release.

**Related decision:** the canonical data model is item 0b below.

### 0b. Canonical data model: AGS-shaped or observation-based? · You · SPEC §6, §7 · **Decide before Phase 2 starts (milestone M6)**
**Background:** AGS is often criticized as a *storage* model, as opposed to a transfer format. Claude's guesses at why (unconfirmed):
1. Depths are part of record identity: correcting a depth re-keys every child test, and the keys are formatted decimals.
2. No history or versioning.
3. `LOCA_ID` is unique only within a project.
4. One group per test type, a layout that changes between versions, and awkward generic queries.
5. Values stored as text, with per-file units and display-precision types.
6. Raw, derived and interpreted values mixed together, with no record of how values were derived.
7. Weak geometry: no CRS or vertical datum, inclined holes only via HORN.
8. Code lists (ABBR) that vary by file.

**Options:**
- **A. AGS 4.2-shaped canonical tables.**
  - Older AGS versions are mapped up to 4.2, and DIGGS is mapped into the same shape.
  - Extension tables hold datum/CRS, flags, provenance and integer surrogate keys.
  - Simplest to build; `p.sql()` users see familiar AGS names.
  - Generic cross-test queries and DIGGS mapping are harder.
- **B. Hybrid (Claude's lean, pending confirmation of the reasons):**
  - The **raw layer** stays AGS-shaped (faithful to the file; used by `p.diff()` and validation).
  - The **canonical layer** has:
    - entity tables with surrogate keys: `location`, `sample`, `specimen`, `geology_interval`;
    - a generic `observation` table: entity, depth, property, value_si, flag, method, source row;
    - structured tables where shape matters: PSD curves, SPT increments, and later triaxial stages and consolidation increments.
  - DIGGS (which follows the OGC Observations & Measurements pattern) maps naturally.
  - A new test type means new rows, not a layout change.
  - Costs a bit more design up front, and raw SQL becomes harder.

**Either way:** the public API (the friendly column registry, plot and stats functions) is the same, so this decision is internal.

**Next step:** confirm which reasons are decisive, especially identity/keys (#1, #3) vs layout and the observation model (#4).

**Timing:** with plots first (SPEC §1.3), nothing in Phase 1 depends on this decision. It must be settled at M6, before Phase 2 (ingest and database) starts.

---

## Units

### 1. `pcf` — density vs unit weight in US practice · You · docs/plots/P00-framework.md §4.3
**Question:** do US engineers (and US AGS files) use `pcf` correctly for density (lbm/ft³) vs unit weight (lbf/ft³)? You want ags-kit's convention to match how it's actually used, not just what is physically correct.

**Claude's take:** under standard gravity, 1 lbf = 1 lbm × g, so a value in "pcf" is *numerically identical* whichever meaning is intended. The real risk is only dimensional bookkeeping inside pint (mass vs force). ags-kit can follow usage exactly by doing the following:
- Accept `pcf` on any density or unit-weight heading, whatever the file's author meant.
- Convert it according to the **heading's quantity kind**: unit-weight headings → kN/m³; density headings → Mg/m³.
- Display both kinds as "pcf" in US mode.

What's left for you to check:
- Whether US files ever put unit weights into AGS *density* headings (e.g. `RDEN_BDEN`, `PTST_BDEN`, whose dictionary unit is Mg/m³), or the reverse.
- Whether display labels should say "unit weight" or "density".

**References to look at:**
- ASTM D7263, *Laboratory Determination of Density and Unit Weight of Soil Specimens*. Defines both terms and their units.
- ASTM D2937, *Density of Soil in Place by the Drive-Cylinder Method*.
- FHWA *Geotechnical Site Characterization* manual (FHWA NHI-16-072), for typical US reporting.

### 2. SPT N per 300 mm vs per 12 in · You · docs/plots/P00-framework.md §4.3, docs/drafts/analysis.md §1
**Your note:** you think the equipment is all based on 300 mm regardless of how it's reported.

**Claude's take:** the two standards define the test in their own units:
- **ASTM D1586** drives the sampler in three 6-in (152.4 mm) increments and counts N over the last 12 in (304.8 mm).
- **ISO 22476-3** uses a 150 mm seating drive and a 300 mm test drive.

So US-procedure blow counts genuinely are per 12 in. The 1.6% difference is far below SPT repeatability, which is why the spec treats N as a dimensionless count and never converts it. Increment *penetrations* (`ISPT_PEN*`, `ISPT_NPEN`) **are** converted, because they are lengths. Those penetrations drive the mid-drive depth calculation (SPEC §8.2), so the depth stays correct either way.

**To confirm:** that you're happy with this convention, and whether US files fill `ISPT_PEN*` as 6-in increments (152.4) or as nominal 150 mm values.

**References:**
- ASTM D1586/D1586M-18.
- ISO 22476-3:2005+A1:2011.
- Skempton, A.W. (1986). Standard penetration test procedures and the effects in sands of overburden pressure, relative density, particle size, ageing and overconsolidation. *Géotechnique* 36(3), 425–447.
- ASTM D4633 (SPT energy measurement).

---

## Geology and classification

### 3. `soil_class` categories · You · docs/drafts/analysis.md §1, SPEC §8.3
- **Current draft:** `coarse | fine | organic | fill | rock`.
- **What depends on it:**
  - SPT histograms: cohesive vs cohesionless (§8.1);
  - USCS organic flags (§8.2);
  - future tooling that suggests a class from lab data.
- **Questions:**
  - Should the categories be behavior-based (cohesive / cohesionless / intermediate) or material-based?
  - Do you need `intermediate`, e.g. silty sand with PI < 7?
  - How should fill be handled (by its dominant behavior)?
  - Is rock (weathered, IGM) worth separating?

### 4. SPT classification tables · You · docs/drafts/analysis.md §1 · needed for P03
Written to `src/ags_kit/config/spt_classes.yaml` (Terzaghi & Peck 1948 / Peck, Hanson & Thornburn 1974) for you to confirm:
- the boundaries;
- the boundary convention (lower bound inclusive);
- whether to classify on N or N60 by default.

### 5. Plasticity and gradation systems · Claude (verify) · docs/drafts/analysis.md §2–3 · needed for P04–P05 (Phase 1)
Verify against the source standards during M5:
- BS 5930:2015+A1:2020 plasticity terms (low < 35, intermediate 35–50, high 50–70, very high 70–90, extremely high > 90 LL);
- AASHTO M 145 / ASTM D3282 group and group-index rules;
- ASTM D2487-17 USCS;
- ISO 14688-1 size fractions.

---

## Quality control

### 6. QC thresholds — deeper review · You · docs/drafts/phase2-data.md (Level 1 rules)
The defaults are agreed for now. Revisit as real files are tested:
- **L005** (ground-level outlier): 3 m / 10 ft, 5 nearest holes within 200 m. Should it be terrain-dependent, or relative to a DEM later?
- **S002** (improbable N): > 100.
- **A003** (improbable LL): < 10 or > 150.
- **G002/G003** (gap/overlap tolerance): 0.01 m. Rounding in imperial files (0.1 ft = 0.03 m) may trigger false gaps. Consider making the tolerance unit-aware: 0.01 m or 0.05 ft.
- **P001/P003** tolerances.

### 7. Minimally useful fields · You · docs/drafts/phase2-data.md (Minimally useful fields)
- Review the YAML draft group by group.
- **Decided for now:** `SPEC_REF` and `SPEC_DPTH` are required.
- **Later (Roadmap):** conditional requirements, e.g. `SPEC_*` only required when a sample has more than one specimen.

---

## Statistics (research items, with Claude's recommendations)

### 8. Bounded data and the truncated normal · You · docs/drafts/phase3-stats.md
**Problem:** most geotechnical data are physically bounded:
- N ≥ 0, and capped at 100 by our refusal rule;
- 0 ≤ % ≤ 100;
- k > 0;
- PI ≥ 0.

A normal fit puts probability on impossible values.

**Claude's recommendation.** The key is to separate **truncation** (values beyond the bound cannot exist) from **censoring** (values beyond the bound exist but were recorded *at* the bound).
1. **Strictly positive quantities** (k, c_u, E, N): prefer **lognormal, gamma or Weibull**, which are bounded at 0 by construction. A normal fit is fine only when the CoV is small (below about 0.3, where the mass below zero is negligible). `fit()` should always report **P(X < lower bound)** for each fitted distribution as a diagnostic.
2. **SPT refusals capped at 100 are right-censored, not truncated.** The true N is *at least* 100.
   - Fitting them as observed 100s biases the fit.
   - Recommendation: when the dataset has a `refusal` column, `fit()` and `characteristic()` treat those rows as censored, using `scipy.stats.CensoredData` (SciPy ≥ 1.11) for maximum-likelihood fitting.
   - Plots and `describe()` include them as 100 with a note, per your decision.
   - The same mechanism handles lab values reported as `<x` or `>x`.
3. **Doubly bounded data** (%, e.g. fines content): offer a **beta** distribution on the rescaled data, and a **truncated normal** with fixed, known bounds (`scipy.stats.truncnorm`). This matters only when the data sit near a bound (e.g. fines near 0% in clean sands).
   - Note: SciPy's `truncnorm` parameterizes its bounds in standard units, so fitting with *fixed physical bounds* needs a small custom likelihood. This is easy, but should be tested.
4. **API:** `fit(x, distributions=..., bounds=(lo, hi), censored=mask)`. `bounds` enables `truncnorm`/`beta` and the out-of-bounds diagnostic.

**References:**
- Helsel, D.R. (2012). *Statistics for Censored Environmental Data Using Minitab and R*, 2nd ed. Wiley. The standard practical text on censored (non-detect) data.
- Johnson, N.L., Kotz, S. & Balakrishnan, N. (1994). *Continuous Univariate Distributions*, Vol. 1, 2nd ed. Wiley. Truncated normal and lognormal.
- Phoon, K.K. & Kulhawy, F.H. (1999). Characterization of geotechnical variability. *Canadian Geotechnical Journal* 36(4), 612–624.
- Baecher, G.B. & Christian, J.T. (2003). *Reliability and Statistics in Geotechnical Engineering*. Wiley. Chapters on distributions of soil properties.
- SciPy docs: `scipy.stats.CensoredData`, `scipy.stats.truncnorm`, `scipy.stats.fit`.

### 9. `describe()` sample-size floor · You · docs/drafts/phase3-stats.md
**Claude's recommendation:**
- Always compute, but suppress what is meaningless:
  - **n = 1**: mean = the value; no std or CoV.
  - **n < 3**: warning.
  - **P25/P75**: only reported when n ≥ 4.
  - **P5/P95**: only reported when **n ≥ 20**. Below that they are interpolations between the extreme values, and their summaries carry a note.
- **Percentile method:** Hyndman & Fan type 7 (the numpy default), stated in the output.
- **CoV** is only meaningful for ratio-scale, positive quantities (N, c_u, k). It is **meaningless for elevation or depth**, so `describe()` omits it for interval-scale columns (flagged in the column registry).

**References:**
- Hyndman, R.J. & Fan, Y. (1996). Sample quantiles in statistical packages. *The American Statistician* 50(4), 361–365.
- Phoon & Kulhawy (1999), above. Typical CoVs and the sample sizes behind them.

### 10. `compare(a, b)` — test selection · You · docs/drafts/phase3-stats.md
**Claude's recommendation (a change from the current spec):** drop the two-stage "test normality first, then choose the test" logic. Statisticians advise against it: the pre-test changes the error rates of the main test, and normality tests have little power at the small n we usually have.
- Instead, **always run Welch's t-test** (robust to unequal variances and sizes), and **report a rank-based test alongside** it (Mann-Whitney U, or Brunner-Munzel, which also tolerates unequal variances).
- Add an effect size with a confidence interval, and a plain-English note on whether the two tests agree.
- Offer `log=True` for lognormal-type data (k, c_u). This compares geometric means.
- Warn when n < 5 per group (very low power).

**References:**
- Welch, B.L. (1947). The generalization of "Student's" problem when several different population variances are involved. *Biometrika* 34, 28–35.
- Ruxton, G.D. (2006). The unequal variance t-test is an underused alternative to Student's t-test and the Mann–Whitney U test. *Behavioral Ecology* 17(4), 688–690.
- Delacre, M., Lakens, D. & Leys, C. (2017). Why psychologists should by default use Welch's t-test instead of Student's t-test. *International Review of Social Psychology* 30(1), 92–101.
- Rasch, D., Kubinger, K.D. & Moder, K. (2011). The two-sample t test: pre-testing its assumptions does not pay off. *Statistical Papers* 52, 219–231.
- Zimmerman, D.W. (2004). A note on preliminary tests of equality of variances. *British Journal of Mathematical and Statistical Psychology* 57, 173–181.
- Mann, H.B. & Whitney, D.R. (1947). *Annals of Mathematical Statistics* 18(1), 50–60.
- Brunner, E. & Munzel, U. (2000). The nonparametric Behrens–Fisher problem. *Biometrical Journal* 42, 17–25.
- Fagerland, M.W. & Sandvik, L. (2009). The Wilcoxon–Mann–Whitney test under scrutiny. *Statistics in Medicine* 28, 1487–1497.

### 11. `compare_groups()` — more than two groups · You · docs/drafts/phase3-stats.md
**Claude's recommendation:** the same "report both" approach as `compare()`:
- **Welch's ANOVA** with **Games-Howell** pairwise comparisons;
- alongside **Kruskal-Wallis** with **Dunn's** pairwise tests, with Holm correction.

**References:**
- Welch, B.L. (1951). On the comparison of several mean values: an alternative approach. *Biometrika* 38, 330–336.
- Games, P.A. & Howell, J.F. (1976). Pairwise multiple comparison procedures with unequal n's and/or variances. *Journal of Educational Statistics* 1, 113–125.
- Kruskal, W.H. & Wallis, W.A. (1952). Use of ranks in one-criterion variance analysis. *JASA* 47, 583–621.
- Dunn, O.J. (1964). Multiple comparisons using rank sums. *Technometrics* 6, 241–252.
- Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6, 65–70.

### 12. `fit()` goodness of fit · You · docs/drafts/phase3-stats.md
- Distributions agreed (normal, lognormal, Weibull, gamma; see item 8 for bounded ones).
- To read up on: why a KS test gives misleading p-values once the parameters have been estimated from the same data, and the Anderson-Darling alternative. Also AIC vs BIC at small n (AICc is better for n < ~40; Claude recommends reporting AICc).

**References:**
- Lilliefors, H.W. (1967). On the Kolmogorov-Smirnov test for normality with mean and variance unknown. *JASA* 62, 399–402.
- Stephens, M.A. (1974). EDF statistics for goodness of fit and some comparisons. *JASA* 69, 730–737.
- D'Agostino, R.B. & Stephens, M.A. (1986). *Goodness-of-Fit Techniques*. Marcel Dekker.
- Burnham, K.P. & Anderson, D.R. (2002). *Model Selection and Multimodel Inference*, 2nd ed. Springer. AICc.

### 13. `characteristic()` (Eurocode 7) · You · docs/drafts/phase3-stats.md, docs/reference/eurocode7-summary.md
Open research points:
- **Type C** needs the scale of fluctuation θ. How will users estimate it? Options: a user input, or typical values from the literature (Phoon & Kulhawy 1999), with a default to Type A or B.
- Verify the **lognormal** Annex A formulae (A.5–A.7) and the Angus (1988) mean bound against a purchased copy of EN 1997-1:2024.
- **Depth-trend** characteristic values: the regression prediction interval. Check the n−2 degrees-of-freedom convention.
- Interaction with censored SPT data (item 8).

**References:**
- JRC (2025), EUR 40260 (see the EC7 summary).
- Schneider, H.R. (1997). Definition and determination of characteristic soil properties. *Proc. 14th ICSMFE*, Hamburg.
- Vanmarcke, E.H. (1977). Probabilistic modeling of soil profiles. *J. Geotech. Eng. Div. ASCE* 103(11), 1227–1246.
- Vanmarcke, E.H. (1983). *Random Fields: Analysis and Synthesis*. MIT Press.
- Angus, J.E. (1988). Inferences on the lognormal mean for complete samples. *Communications in Statistics – Simulation and Computation* 17(4).

---

## Test data

### 14. Public AGS datasets · Claude + You · SPEC §12.3
You are also looking. Candidates found so far:

| Source | What | Access | License (to confirm) |
|---|---|---|---|
| [BGS AGS download service](https://www.bgs.ac.uk/technologies/geotechnical-data-services/ags-download-service/) / [AGS File Utilities](https://agsapi.bgs.ac.uk/) | 10,000+ UK boreholes, delivered as AGS4 regardless of original version; up to 50 holes per spatial download; one file per original project | Web UI + exporter API | Not stated on the page; check the BGS "Terms of use" (likely OGL-style) |
| [Hong Kong CEDD GI & LT records](https://data.gov.hk/en-data/dataset/hk-cedd-csu-cedd-gi-lt) | Public-works ground investigation and lab test reports as AGS files, updated monthly | data.gov.hk / CSDI portal, API listed | [GEO open data terms](https://www.ginfo.cedd.gov.hk/GEOOpenData/Disclaimer_en.html) (free for commercial and non-commercial use; confirm they cover the AGS data) |
| `python_ags4.data.load_test_data()` | Small test file bundled with python-ags4 | pip | LGPL-3.0 (bundled with the library) |
| [Geosetta](https://geosetta.org/api_docs/) | US public boring logs with AGS/DIGGS export (**US data**) | API | Check the terms; this may be our only source of real *US-unit* data |

- **Plan:**
  - Don't commit downloaded files unless the license clearly allows redistribution. Instead, a `scripts/fetch_test_data.py` downloads them into a git-ignored cache, and `pytest -m public` runs against that cache.
  - **"Advanced testing":**
    - ingest every cached file, and check invariants (no crash, row counts match the raw data, every QC finding has a source line);
    - generate **US-unit twins of real SI files** with our own converter, then check the round trip SI → US file → ingest = SI ingest;
    - performance budget (e.g. a 50-hole file ingests in under 10 s);
    - property-based unit tests with `hypothesis`.
- **To find:** large files with good SPT, Atterberg, PSD and permeability coverage.

---

## Later / far future (also on the Roadmap)
- Title block and company drafting-standard templates for `Sheet`.
- A helper for deciding cohesive vs cohesionless from lab data (fines %, PI).

## Done
- ✅ AGS heading names in SPEC checked against the python-ags4 dictionaries 4.0.3–4.2 (2026-10-10). All present. Version notes are in docs/drafts/phase2-data.md (Versions).
