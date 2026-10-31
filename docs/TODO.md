# TODO

Items to think through or research. Each item notes who owns it and the SPEC.md section it affects. Where you asked for a recommendation, Claude's view is included.

- **Owner key:** **You** = engineering judgment or research you want to do yourself. **Claude** = verification or build-time work.
- When an item is resolved, move the decision into SPEC.md and delete it here.

---

## Geology and classification

### 3. `soil_class` categories · You · SPEC §8.3
- **Current draft:** `coarse | fine | organic | fill | rock`.
- **No longer needed for the SPT histograms (P03):** the user picks the class table and passes the rows it applies to (M3 intent, decision 6). `soil_class` could later pick the table automatically.
- **What depends on it:**
  - USCS organic flags (§8.2);
  - future tooling that suggests a class from lab data.
- **Questions:**
  - Should the categories be behavior-based (cohesive / cohesionless / intermediate) or material-based?
  - Do you need `intermediate`, e.g. silty sand with PI < 7?
  - How should fill be handled (by its dominant behavior)?
  - Is rock (weathered, IGM) worth separating?

### 5. Plasticity and gradation systems · Claude (verify) · docs/drafts/analysis.md §2–3 · needed for P04–P05 (Phase 1)
Verify against the source standards during M8:
- BS 5930:2015+A1:2020 plasticity terms (low < 35, intermediate 35–50, high 50–70, very high 70–90, extremely high > 90 LL);
- AASHTO M 145 / ASTM D3282 group and group-index rules;
- ASTM D2487-17 USCS;
- ISO 14688-1 size fractions.
- the sieve lists in `config/sieves.yaml` (ASTM E11 sizes and designations; the ISO list at the ISO 14688-1 boundaries), used by P05.

### 22. Organic soils (OL, OH) in USCS · You · docs/drafts/analysis.md §2; P04
- **Problem:** USCS splits OL from ML and OH from MH by the oven-dried LL, which isn't in AGS LLPL. In M8 the analysis gives only the inorganic symbol (M8 intent, decision 3).
- **To decide:**
  - Where a user records that a specimen is organic: a per-specimen column, `soil_class = organic` (#3), or a field the user names.
  - How P04 marks organic specimens so they read differently from the rest (e.g. hollow markers with a legend entry).

### 24. NP specimens with LL under 20 · You · docs/drafts/analysis.md §2.5
- **Problem:** `plasticity()` classes an NP specimen at PI = 0. Below LL 20 the A-line's PI is negative, so PI = 0 is on or above it, and BS 5930 gives `CL` (a clay) for a non-plastic soil. USCS gives `ML` only because PI = 0 is under 4. Found in the M8 index datasets, where the test file's NP sand has LL 21 to stay clear of it.
- **To decide:**
  - Whether an NP specimen is always M (silt) in both systems, whatever its LL.
  - How a plastic specimen with LL under 20 is classed, where the A-line doesn't reach (both charts start their zones at LL 20 or above).

---

## Quality control

### 6. QC thresholds — P001/P003 tolerances · You · docs/data/qc.md §4.7
Revisit as real files are tested:
- **P001** (grading curve rises): 0.5 percentage points.
- **P003** (GRAG fractions don't sum to 100): ±2 percentage points. Held on a real 4.1.1 file (2026-10-21, `spt-report`): 3 findings, each 5 to 10 points from 100 and each a genuine error in the source report's tables; none came from rounding.

### 25. Pressuremeter depth at the probe center · You · docs/data/qc.md §4.4 (D003)
`PMTG_DPTH` is the center of the probe, so the hole went at least half the probe's expanding length deeper. D003 compares the center with `LOCA_FDEP`, so it misses a test whose center is above the final depth but whose lower half isn't. D003 could add half the probe length, when it is known. Minor; seen once on a real file.

### 26. Slope-aware L005 · You + Claude · docs/data/qc.md §4.2 (L005)
On a real file, a valley gave 22 L005 hits that were real topography. Options: compare a hole with a plane fitted through its neighbors rather than their median, or scale the tolerance with the distance to them. The per-project way to accept findings is `qc-review`.

### 27. Writing accepted findings from a report · You + Claude · docs/data/qc.md §2
Typing accepted-findings entries (`qc-review`) by hand is slow when a reviewer accepts many findings one at a time. A helper such as `report.accept(rows, reason=...)` could write or extend the YAML file from rows of `report.findings`. Left out of `qc-review` because it is a second API; revisit once accepted findings have been used on a real review.

### 28. D003/D004 for geophysical profiles · You + Claude · docs/data/qc.md §4.4 (D003, D004)
A downhole or surface velocity profile (often a user-defined group) can run below `LOCA_FDEP`, for example to 30 m for Vs30, and outside the logged geology. D003 and D004 report it as a depth error. Options: exempt groups that hold a geophysical profile, or report them as info. Accepted findings (`qc-review`, `group:` entries) cover it per project for now.

### 7. Minimally useful fields · You · docs/data/qc.md §4.10
- Review the default list group by group against real files.
- **Decided for now:** `SPEC_REF` and `SPEC_DPTH` are recommended, not required (M7, docs/data/datasets.md §14), so lab results without them fall back to the sample depth.
- **Later (Roadmap):** conditional requirements, e.g. `SPEC_*` only required when a sample has more than one specimen.

---

## Statistics (research items, with Claude's recommendations)

### 8. The truncated normal, and bands in `fit()` · You · docs/drafts/phase3-stats.md · after M15 (c)
The rest of this item is built (M15 (c), SPEC §5): refusals and `<x`/`>x` are fitted as censored, positive distributions are bounded at 0, beta fits between two bounds, and each fit reports its probability beyond the bounds. Two options remain:
1. **A truncated normal with fixed physical bounds**, for doubly bounded data near a bound (fines near 0 %). SciPy's `truncnorm` takes its bounds in standard units, so fixed bounds need a small custom likelihood, tested on its own. Beta covers the case meanwhile.
2. **Bands as interval-censored values.** `fit()` leaves bands (`<target>_lower`/`_upper` with no value) out and counts them, because a correlation's band is the spread of its coefficient, not a measurement known to lie in an interval. Fitting one as an interval would treat a modeling range as data; revisit only if a source gives true intervals.

**References:**
- Johnson, N.L., Kotz, S. & Balakrishnan, N. (1994). *Continuous Univariate Distributions*, Vol. 1, 2nd ed. Wiley. Truncated normal and lognormal.
- SciPy docs: `scipy.stats.truncnorm`.

### 13. `characteristic()` (Eurocode 7) · You · docs/drafts/phase3-stats.md, docs/reference/eurocode7-summary.md · M18
**Deferred** (2026-10-29) to M18 (selection), with P09, which needs it. Its judgments (the type of estimate, θ, L, an assumed V_X), the lognormal formulae and the framing for US users are settled there.

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

### 49. Refusals with a known penetration in `fit()` · You · SPEC §5, `docs/work/m15c-fit.md` (Decision 3) · before M18
`fit()` takes a refusal as right-censored at its N60: "at least the cap", with no upper limit, so how far the fitted tail reaches above the cap is the distribution's assumption, not the data's. In the example Terrace, 11 of 40 tests are refusals at N60 66.7, and the fits put 24–27 % of their probability above it (lognormal P99 137).

The penetration says more. Every Terrace refusal is 50 blows for 11 in of total penetration (`spt_penetration` is seating plus test drive), so about 5 in into the 12 in test drive; scaled to a foot that is N ≈ 120, N60 ≈ 160, well above the cap. Whether the 50 blows include the seating drive depends on how the file reports them. Options:
1. Keep right-censoring (today): honest, but it ignores the penetration.
2. Interval-censor each refusal between the cap and an extrapolated N60 from its penetration. Extrapolating blows isn't standard practice, so this is a judgment and needs a source or a judgment key (SPEC §4).
3. A judged upper limit for refusals per geology unit (a judgment, with no default).
Which one matters most for selection (M18): a characteristic value of N is sensitive to this tail.

### 50. Anderson–Darling p-values on heavily tied values · You + Claude · `docs/work/m15c-fit.md` (Decision 7) · with M15 (d) or M18
The Anderson–Darling check assumes continuous values. N60 takes few distinct values (whole blows × a factor), and the ties read as misfit: the example Alluvium's 30 tests take 6 distinct values, and every fit's p-value is 0.001–0.014 although the Q-Q plot shows a reasonable fit. The statistics guide warns about it; `fit()` doesn't. Options: a note when a group has few distinct values (the threshold to decide, e.g. fewer than half its n), leaving the AD columns blank there as for censored values, or a check that allows for discreteness. Decide what counts as "heavily tied" first.

## Plots

### 23. Text in P07's value column · You + Claude · P07 §3, §11
- **Problem:** P01 draws text values (`NP`, `refusal`, other text) at the left edge and counts them (TODO #15, done in M8), but P07 still raises an error naming the rows, so the user cleans the column first.
- **To decide:** P07 has no depth axis, so the left-edge markers don't carry over. Count them under each unit (a line under the axis, or in the summary), or keep the error?
- **Reuse:** `hangtu._data.text_values()` reads the column, and `plot/_text_values.py` orders and labels the texts and builds the stats box's "Also" line.

### 16. Other summaries in P07 · You + Claude · P07; SPEC §5
- **Built in M15 (a):** P07 and P01's stats box summarize through `ht.stats.describe()`'s calculation, so they never give different numbers for the same data; P07's `percentile_method=` is gone (Hyndman & Fan definition 7 everywhere) and its default bar is p25–p75.
- **Problem:** P07 still summarizes each unit only with percentiles. A report's baseline may have been summarized some other way, so the data bar and the baseline bar aren't always like for like.
- **Wanted:** a way to match how the report summarized its data:
  - **other summaries**: min–max, mean ± k·σ, and the geometric mean and log-space percentiles for log quantities such as hydraulic conductivity;
  - **a summary the user computes**: pass per-unit values in, as for the baseline table.
- **To decide:**
  - Which of these does v0.1 need, if any?
  - Is it an extension of `summary=`, or a callable?
  - The geometric mean is now in `describe(log=True)`: P07 can draw it from there.
  - How does the legend name the method?
- **Claude's view:** each new summary is a `describe()` statistic first, which P07 then draws.

### 42. Compacting a sparse profile · You + Claude · P01, `docs/plots/README.md`
- **Problem:** a profile whose data are widely spaced in depth leaves most of the axes empty. `docs/plots/img/P01-ranges.png` runs 0–50 ft for a dozen rows, with gaps of 5–10 ft between them, and reads as mostly white space.
- **Wanted:** a rule for when a profile counts as too sparse, and an option to compact it.
- **Questions:**
  - What does the rule measure: the share of the depth axis with data, the largest gap, or rows per unit of figure height?
  - What does compacting do: a shorter figure, depth limits fit to the data instead of from the ground surface, or a broken depth axis across long empty stretches?
  - Is it on by default, or only when asked? A depth axis that doesn't start at the surface, or that breaks, must say so on the figure.
  - Do P02–P07 and `Sheet` need the same, so panels on a shared depth axis stay aligned (TODO #38)?

### 43. Subscripts in labels · You + Claude · `src/hangtu/columns.yaml`, `docs/plots/README.md`
- **Problem:** axis labels print symbols as typed: "Undrained shear strength, s_u" shows the underscore, not s with a subscript u. The registry also writes them inconsistently: "σ′_v0" but "σ′p".
- **Wanted:** symbols drawn as real subscripts on figures (matplotlib mathtext, e.g. `$s_u$`, `$\sigma'_{v0}$`).
- **Questions:**
  - Where does the markup live: a separate `symbol` field in the registry, kept apart from the plain `label`, or converted from the label at draw time?
  - Warnings, error messages, docstrings and the docs site stay plain text. Do they keep "s_u", or move to Unicode where it exists (s with ᵤ is uneven across fonts)?
  - One spelling for every symbol in the registry, checked by a test.

---

### 46. A correlation's standard deviation on P01 · You + Claude · P01, `docs/work/m15b-correlation-statistics.md`
M15 (b) puts a correlation's standard deviation on its rows (`<target>_correlation_standard_deviation`), but P01 doesn't draw it. Proposed: ±1 standard deviation as a whisker on each estimate, named in the legend, drawn only where the column has a value. Open: whether a whisker of the source's scatter beside the soil's own spread reads as a confidence interval, which it isn't.

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

### 21. Thewes & Burger (2004) diagram · You (from the paper) · P17 §14 · needed for M12's spec
Axes, zones and limits are settled (P17 §4, §6). Still needed from the paper: the figure number and any stated validity (soil or machine type).

---

## Parameters (SPEC §1.3, `docs/work/parameter-roadmap.md`)

### 29. Judgment keys · You · SPEC §4 · settle each when its wave starts
Each judgment declares what it is keyed by and whether one project-wide value is allowed. Proposed:
- GSI by geology unit;
- the disturbance factor D by design case (excavation method and zone);
- σ′3max by design case;
- Bjerrum's μ from PI, so by specimen;
- settled in M13 (`docs/work/m13a-judgments.md`): unit weight by a log column (`by:`, usually `geology_unit`), water level by hole, each with an optional project-wide value that needs a `reason` and fills unlisted keys with a warning.
- settled in M14 (b) (`docs/work/m14b-phase-relations.md`): specific gravity by a log column (usually `geology_unit`), with the same optional project-wide value; used only where a row has no particle density.

### 31. Curves in real files · You · input for wave 0's intent (M16)
Which user-defined groups and headings real files use for triaxial stress–strain curves, rock triaxial, swelling against time and shear box displacement, gathered from the sample dataset being prepared from real projects.

### 32. Published definitions of the model sets · Claude (verify) · SPEC §5 · needed for M18
Confirm a non-vendor published source that defines each model set's parameters: Mohr–Coulomb; Hardening Soil (Schanz, Vermeer & Bonnier 1999?); HS-small (Benz 2007?); generalized Hoek–Brown (Hoek, Carranza-Torres & Corkum 2002); Soft Soil (Vermeer & Neher 1999?). Where only a software manual defines a model, say so.

### 34. γw as a judgment · You · SPEC §4
`ht.settings.water_unit_weight` is one session value. Sites with both seawater and fresh water (or brines) need two, so γw may become a judgment keyed by hole or zone.

### 35. `strata=` from a per-hole stratigraphy · You + Claude · P01 §8
P01's `strata=` takes one stratigraphy; the user filters `p.stratigraphy()` to one hole. Later, `strata=` could take the per-hole table directly (one hole, or with a `loca_id` filter) and convert a depth pair to elevation with that hole's ground level.

### 36. Wolff (1989) · Claude (verify) · page 04, `docs/work/m13b1-spt-framework.md` · before building it
φ′ = 27.1 + 0.3 (N1)60 − 0.00054 (N1)60², a fit to Peck, Hanson & Thornburn (1974). Verify the equation, its coefficient (copies print 0.00054 or 0.00053) and its N basis against Wolff (1989), ASCE GSP 23, 96–106, then build it as a correlation.

### 39. Sowers (1979) · Claude (verify) · page 05, `docs/work/m13b2-spt-strength-history.md` · before building it
s_u against N for low, medium and high plasticity, known only as lines on EPRI EL-6800 Fig. 4-50 (after Djoenaidi), with no equation: the coefficients would be read off a chart. Cut from M13 b2. Build it only once the lines' equations are verified against Sowers (1979) itself.

### 38. Correlation profile: the input beside the estimates · You + Claude · P01, SPEC §4 · with M13 b2 or M18
Today the estimates draw on one P01 profile by `correlation_name`, and a blank estimate shows only as a footnote count. A two-panel figure on a shared depth axis would show why: the left panel the input the correlation read (N60 or (N1)60, and σ′v where it is used) with each correlation's range drawn as limits, the right panel the estimates. A test with no estimate is then visible on the left, outside a range or marked as a refusal.

Proposed: two panels, not one axes with twinned x axes. A second x axis on the same profile makes the reader match each marker to one of two unrelated scales; the input and estimate markers interleave at the same depths, and the axis limits of each are arbitrary relative to the other. Two panels keep one quantity per axis (P01's contract) and still line up by depth. Open: a helper (`ht.plot.correlation_profile(est, ...)`) or a recipe in the correlations guide using `ht.Sheet` with `ax=`; `Sheet` has no shared vertical axis yet, so either needs one (matching depth limits across panels).

### 51. Comparing groups with censored values · You + Claude · SPEC §5, `docs/work/m15d-compare.md` (Decision 7) · before M18
`compare()` and `compare_groups()` take refusals and `<x`/`>x` at their value and count them, with a note that the means, and so Welch's results, are biased; the ranks treat a common cap as tied at the top, closer to right but not right either. A group that is all bounds at one value isn't tested. Tests made for censored data compare groups properly: the Gehan and Peto–Prentice generalized Wilcoxon tests, and the score tests of survival analysis (Helsel et al. 2020, ch. 13, is a starting point). Decide which, and whether `fit()`'s censored likelihood (M15 (c)) gives a parametric counterpart.

### 52. Chance-corrected agreement in `crosstab()` · You · SPEC §5, `docs/work/m15e-crosstab.md` (intent, out of scope) · when a use appears
`crosstab()` reports the share of rows that agree and lists the rest, with no test or kappa: a log and a lab classification of the same soil are plainly related, and Cohen's kappa assumes the two classifications were made independently, which a log written after the lab results isn't. Revisit if a use appears where they are independent (two loggers, two labs), and decide then whether kappa, weighted kappa for ordered classes, or another measure fits, with its interval.

### 47. The scale of three correlation standard deviations · Claude (verify) · `config/correlations.yaml`, `docs/work/m15b-correlation-statistics.md`
Mayne & Kemper's σ′p (S.D. = 4.37 pa) and OCR (3.82), and Kulhawy et al.'s K0 (0.43), have `scale: null`, so none is on the rows yet. Check each against Mayne & Kemper (1988), Kulhawy et al. (1989) or Kulhawy & Mayne (1990), Figs. 3-9, 3-18 and 3-30: whether it is the regression's standard error on the arithmetic values (then `scale: arithmetic`, and its registry column `<target>_correlation_standard_deviation` is added) or on log values (a factor, which needs a column design first). σ′p's, given in pa, suggests arithmetic.

### 48. Statistics sources not yet checked · Claude (verify) · SPEC §5, `docs/work/m15c-fit.md` and `docs/work/m15d-compare.md` (Sources)
M15 (c) cites the NIST e-Handbook (§1.3.5.14) for the Anderson–Darling statistic and SciPy's documentation for the bootstrap p-value and the Kaplan–Meier estimate, because the original papers aren't available free. Check each against the paper when a copy is at hand, and update the docstrings and the statistics guide:
- Stephens (1974), *JASA*, doi:10.2307/2286009 (the A² statistic).
- Stute, González Manteiga & Presedo Quindimil (1993), *Metrika* (a parametric bootstrap with estimated parameters; the reference SciPy's `goodness_of_fit` gives).
- Kaplan & Meier (1958), *JASA* (the estimator).

M15 (d) cites Helsel et al. (2020), Delacre et al. (2019), Dinno (2015) and Karch (2021), all checked, and SciPy for what they describe only by reference. Not yet checked against the papers:
- Welch (1947) and (1951), *Biometrika* (the t-test and the ANOVA).
- Games & Howell (1976), *Journal of Educational Statistics* (SciPy's `tukey_hsd` cites it).
- Brunner & Munzel (2000), *Biometrical Journal*, and Neubert & Brunner (2007), *Computational Statistics & Data Analysis* (the variance estimate, the interval for p̂, the permutation form).
- Dunn (1964), *Technometrics*, and Holm (1979), *Scandinavian Journal of Statistics*.
- Fagerland & Sandvik (2009), *Statistics in Medicine* (why not Mann–Whitney).

Titles, volumes and pages are to be taken from each paper, not from memory.

### 41. Gravelly sands under `not_for` · You + Claude · page 04, `docs/work/m13b1-spt-framework.md`
Hatanaka & Uchida (1996) is `not_for` gravelly soils, but the USCS check reads only the group symbol. The example site's Terrace is "SAND with gravel (SP)": SP passes, so its rows get estimates with no note. USCS group names (ASTM D2487) add "with gravel" at ≥ 15 % gravel, which the symbol does not carry.
- **Questions:**
  - Read the group name or description (`geology_description`, or a `uscs_name` column), the gravel fraction from gradation tests, or leave it to the user to pass the rows?
  - If flagged: no estimate ("not for this soil"), or an estimate with a note?
  - Which other entries have `not_for` terms the symbol can't check (micaceous sands, fissured clays)?
- **The warning's wording:** done in M13 b3 (`docs/work/m13b3-spt-stiffness.md`, Decision 8). The warning gives the range only when some rows are outside it, in the docstring's terms and units (`N pa/σ′v0`, `σ′v0 > 0 kPa`).

### 44. Strata labels clipped above the axes · Claude · P01 §7, `src/hangtu/plot/_overlays.py`
- **Problem:** a strata label is drawn 2 pt below the top of its band, clipped to the axes. When the band's top is beyond the vertical limit, the label falls outside the frame and is cut off or lost. `docs/plots/img/P06-si.png` shows it: the Fill band starts at 11.1 m and the axis at 11 m, so "Fill" is clipped at the top. US hides it only because the limit happens to be above the band.
- **Wanted:** every band that shows inside the axes keeps a readable label.
- **Questions:**
  - Place the label at the top of the visible part of the band (the band's top clipped to the axis limit), or move the limit out to the band's top?
  - A band too thin on the axes for its label: leave the label out, or count it in the footnote?

### 45. Recommended user-defined AGS fields · You + Claude · SPEC §4, §6.2 · raised in `docs/work/m14a-density-data.md`
- **Idea:** hangtu could ship a set of recommended user-defined headings or groups, so a file can carry values that the AGS dictionary has no place for. One example is a specific gravity chosen for a geology unit. With those fields filled in, users get all of hangtu's functionality straight from the file.
- **Questions:**
  - Which values would be in the set?
  - A value carried in the AGS file: is it data, or a judgment? SPEC §4 keeps judgments in `judgments.yaml`, where they can be reviewed, so a judgment in the file would have to say where it came from.
  - How would the set be published? For example, as a `DICT` block users copy into their files.
  - How does this fit with wave 0 (M16, user-defined groups)?

---

## Later / far future (also on the Roadmap)
- Title block and company drafting-standard templates for `Sheet`.
- A helper for deciding cohesive vs cohesionless from lab data (fines %, PI).

## Done
- ✅ #10 and #11 Comparing groups decided and built (2026-10-30, M15 (d)): no pre-tests; `compare()` reports Welch's t-test with the difference and its interval beside Brunner–Munzel with the probability of superiority (permutation below 10 per group); `compare_groups()` Welch's ANOVA and Games–Howell beside Kruskal–Wallis and Dunn with Holm; a plain-English note; fewer than 5 per group warns; α a judgment. SPEC §4, §5.
- ✅ #40 Correlation statistics decided and built (2026-10-30, M15 (b)): each estimate row carries its source's n, r², scatter in its own words and advice on use (quoted with its citation, or marked as hangtu's), and an arithmetic standard deviation in the target's units once verified (#47). Other databases' checks (bias, COV) stay in the entry's `evaluations`; applying them is M18. SPEC §4.
- ✅ #9 `describe()` floors decided and built (2026-10-29, M15 (a)): n = 1 gives the value as the mean and no std or CoV; fewer than 3 values warns; a percentile is reported only with a value beyond it on each side (P25/P75 from 4, P5/P95 from 20); Hyndman & Fan definition 7, stated in the output; no CoV on an interval scale or a mean ≤ 0. SPEC §5.
- ✅ #20 Which SPT correlations for M13 settled (2026-10-26, M13 b1–b3): φ′ from Hatanaka & Uchida (1996) and Kulhawy & Mayne (1990); s_u from Stroud (1974) and Terzaghi & Peck (1967); σ′p, OCR and K0 from Mayne & Kemper (1988) and Kulhawy et al. (1989); E from AASHTO (2004) and Kulhawy & Mayne (1990), by a required soil row; Vs from Imai & Tonouchi (1982) and Ohta & Goto (1978) in Wair et al.'s (2012) N60 forms. Each verified against its source; Wolff (1989) and Sowers (1979) cut (#36, #39).
- ✅ #37 Soil types for correlations decided (2026-10-23, M13 b2): an opt-in USCS map. Each config entry keeps the source's words and gains hangtu's proposed USCS groups, labeled as hangtu's reading; `uscs="proposed"` or a list of groups turns it on and reads a `uscs_symbol` column the user supplies, never derived. Rows outside get NaN, "not for this soil"; a blank symbol, "soil type unknown". SPEC §4.
- ✅ #30 What can be published decided (2026-10-22, M13, `docs/work/m13a-judgments.md` Decision 9): a site page may reproduce single values and ranges with their citation and locator, short sets of class boundaries as commonly cited (about ten rows or fewer), and equations with their source. It doesn't reproduce a source table or chart whole, values read off a chart beyond the few a method needs, a chart's descriptors (GSI), or quoted text beyond a sentence. Figures on the site are hangtu's own.
- ✅ #33 Energy ratio decided (2026-10-22, M13): hammer efficiency is data, not a judgment. `ISPT_ERAT` is used first; `hammer_efficiency` (argument or setting) fills blanks with a warning naming the holes, and takes values by hole in M13 unit (b). SPEC §4.
- ✅ #15 Text in a value column built (2026-10-19, M8): P01 draws each text value as an open marker at the left edge at its depth, one shape per text, with a legend entry and a footnote count. `NP` and `refusal` (any case) are recognized; other text is counted with a warning naming it. The stats box adds "Also: NP 3, 'dry' 2". In P01 §3, §7, §8. P07 is TODO #23.
- ✅ #19 Source of triaxial readings decided (2026-10-15): a CSV the user shapes from the lab's export, one row per reading, minimum columns in the P12 draft §3. AGS 4.1–4.2 `TRET` and `TRIT` carry values at failure only, which feed P11.
- ✅ #18 A point exactly on the axis limit decided and built (2026-10-14, M9): a value on a limit hangtu picks moves that limit out one step (a tick step, or a decade on a log axis). A lower limit of 0 stays, and limits the user sets are used as given. In P00 §8.
- ✅ #17 Particle size shown in inches decided (2026-10-14): `GRAT_SIZE`, `LLPL_SIZE` and `PTST_SZUN` get the `particle_size` kind at ingest, so US output keeps mm. In docs/data/datasets.md §10 and ingest.md §7.
- ✅ #6 QC thresholds kept as the defaults (2026-10-14): L005 (3 m from the median of the 5 nearest holes within 200 m), S002 (N > 100), A003 (LL < 10 or > 150), G002/G003 (0.01 m; a project can set any unit, and imperial rounding doesn't cause false gaps). In docs/data/qc.md §4. P001/P003 stay open.
- ✅ #4 SPT classification tables decided (2026-10-13): the Terzaghi & Peck / Peck, Hanson & Thornburn boundaries, lower bound inclusive, classified on whichever N column the user names (default `spt_n`). In `src/hangtu/config/spt_classes.yaml`; spec in docs/drafts/analysis.md §1.4. User-defined bins come later.
- ✅ #0c Repo published on GitHub; the full CI matrix (Windows, macOS, Linux × Python 3.12–3.14) and the `lowest` job are green, so M0 is done (2026-10-12). 0.0.1 is on PyPI, released by `release.yml` (SPEC §12.1).
- ✅ #1 `pcf` and #2 SPT N per 12 in decided (2026-10-11). Recorded in P00 §4.3; the follow-ups that only matter on ingest are in docs/drafts/phase2-data.md (Units on ingest, items 5–6).
- ✅ AGS heading names in SPEC checked against the python-ags4 dictionaries 4.0.3–4.2 (2026-10-10). All present. Rechecked at M5 (2026-10-14): nothing is renamed between versions, only removed; the list and the rule are in docs/data/ingest.md §6.
