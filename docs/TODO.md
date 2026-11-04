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

### 13. Representative values: what stays open · You · `docs/reference/eurocode7-summary.md` §3.2, §3.5 · when a project needs it
`ht.stats.representative()` was built in M18 (b) (`docs/work/m18b-representative-values.md`); its decisions are in SPEC §5 ("Representative values"). Two points stay open:
- **The Angus (1988) bound on the mean of a lognormal trend.** A lognormal line through ln x gives the median; the JRC report mentions Angus's approximation for a proper confidence bound on the mean. Not offered: verify it against the source before building it.
- **Γ² from a variance function.** The JRC report gives Γ² = θ/L, capped at 1, which hangtu uses. Vanmarcke's variance function for the exponential correlation model (in the EC7 summary §3.2, unverified) gives a smooth Γ² that needs no cap. Build only once it is checked against Vanmarcke (1983) and a user needs it; estimating θ from a CPT is a separate helper.

**References:**
- Angus, J.E. (1988). Inferences on the lognormal mean for complete samples. *Communications in Statistics – Simulation and Computation* 17(4).
- Vanmarcke, E.H. (1983). *Random Fields: Analysis and Synthesis*. MIT Press.

---

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

### 54. Scatter in the committed figures' data · Claude + You · `docs/plots/img/`, `docs/site/examples/`, P09 §12 (AC 11)
Some synthetic data behind the visual checks and site examples sits closer to its fitted lines and means than a site's data would, so the figures look cleaner than what a user will see. P09 asks for site-like scatter (CoV about 0.3, skew, uneven depths, an outlier or two). Check each image in `docs/plots/img/` and the examples that make them, and regenerate the ones whose data look too clean, with the scatter set on purpose. One commit per plot, each regenerating its image.

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

### 32. Published definitions of the model sets · You (copies) + Claude (verify) · SPEC §5 · Mohr–Coulomb for M18, the rest with their waves
**Mohr–Coulomb set for M18** (decided 2026-11-02): c′ and φ′ from the fits and correlations; ψ as an estimate; E′ and ν′ left blank until wave 5 (M23). Mohr–Coulomb is defined in any soil mechanics text, so a standard citation does.
- **ψ:** Bolton (1986), ψ = (φ′_peak − φ′_cv) / 0.8, floored at 0, for coarse-grained units, with φ′_cv a judgment per unit (no default); ψ = 0 for fine-grained units. The relation is for plane strain; used with a triaxial φ′ it is an approximation, and the result says so. The practice rule ψ = max(0, φ′ − 30°) is not offered: its only sources are software manuals (GEO5, PLAXIS), and it hides the same φ′_cv assumption (sheet 09, §5.2–5.3).
- **To verify against the primary:** Bolton, M.D. (1986), The strength and dilatancy of sands, *Géotechnique* 36(1), 65–78 (now [V] only through secondary sources).

**The other sets**, each checked by the wave that builds it: Hardening Soil (Schanz, Vermeer & Bonnier 1999?) and HS-small (Benz 2007?) with wave 5 (M23); Soft Soil (Vermeer & Neher 1999?) with wave 3; generalized Hoek–Brown (Hoek, Carranza-Torres & Corkum 2002) with wave 4 (M22). Confirm a non-vendor published source that defines each set's parameters; where only a software manual defines a model, say so.

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

### 51. Comparing groups with censored values · You + Claude · SPEC §5, `docs/work/m15d-compare.md` (Decision 7) · when a lab dataset needs it
`compare()` and `compare_groups()` take censored values at their value and count them, with a note that the means, and so Welch's results, are biased; the ranks treat a common bound as tied, and order bounds at different values as if they were measured. Statistics are designed for lab data (SPEC §5), so the cases that matter are lab ones: s_u from a hand vane or pocket penetrometer at the instrument's maximum (`>x`), hydraulic conductivity below what the test resolves (`<x`), percent passing `<x`. SPT refusals aren't the reason to build this. Candidates (Helsel et al. 2020, ch. 13): the Peto–Prentice generalized Wilcoxon test for values censored in one direction, preferred to Gehan's when censoring differs between groups, with a k-group form for `compare_groups()` (not in SciPy, about 50 lines and a hand-checked golden value); a likelihood ratio test from `fit()`'s censored likelihood (M15 (c)), one distribution against one per group, as the parametric counterpart; no test, with a note, when a comparison has values censored both ways. Build when a lab dataset with censored values needs a comparison.

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

### 53. Triaxial test standards · You (copies) + Claude (verify) · `docs/data/qc.md` §4.12, `docs/work/m11a-triaxial-data.md` (Sources)
QC X001's `lowest_pore_pressure_parameter_b: 0.95` is the B-value commonly quoted as the requirement before shearing, not yet checked against a standard. Check it, and what each allows for stiff soils (a lower B where B stops rising with back pressure), in ASTM D4767 (CU), ASTM D7181 (CD) and ISO 17892-9, with the clause. Then cite it in `qc/rules.yaml`, X001's message and qc.md. M11 (b) reads `failure_criterion` as written and only refuses to pool different ones (`docs/work/m11b-envelope-fit.md`, decision 4), and M11 (c) defines maximum deviator stress and maximum principal stress ratio from readings without a default (`docs/work/m11c-triaxial-shearing.md`, decision 4), so nothing built depends on which a standard requires. Check what D4767, D7181 and D2850 (UU) say of each, and of a limiting strain, before a fit, a QC rule or a docs page recommends one.

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
- **Idea:** hangtu could ship a set of recommended user-defined headings or groups, so a file can carry values that the AGS dictionary has no place for. One example is a specific gravity chosen for a geology unit; another is what an in situ hand penetrometer reads (`IPEN_IPEN`, s_u or q_u), which `p.undrained_strength()` takes as `hand_penetrometer_scale=` (M17 a). With those fields filled in, users get all of hangtu's functionality straight from the file.
- **Questions:**
  - Which values would be in the set?
  - A value carried in the AGS file: is it data, or a judgment? SPEC §4 keeps judgments in `judgments.yaml`, where they can be reviewed, so a judgment in the file would have to say where it came from.
  - How would the set be published? For example, as a `DICT` block users copy into their files.
  - How does this fit with wave 0 (M16, user-defined groups)?

---

## Later / far future (also on the Roadmap)
- Title block and company drafting-standard templates for `Sheet`.
- A helper for deciding cohesive vs cohesionless from lab data (fines %, PI).
