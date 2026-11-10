# TODO

Items to think through or research. Each item notes who owns it and the SPEC.md section it affects. Where you asked for a recommendation, Claude's view is included.

- **Owner key:** **You** = engineering judgment or research you want to do yourself. **Claude** = verification or build-time work.
- When an item is resolved, move the decision into SPEC.md or its living spec and delete it here.

---

## Geology and classification

### 3. `soil_class` categories · You · SPEC §8.3
- **Defined so far** (SPEC §8.3): `coarse` and `fine` are read by the Mohr–Coulomb set's ψ; `fill`, `rock` and `organic` are recognized and read by nothing yet (ψ for them is an error asking for a selection); other values are accepted. A Project's datasets carry the classes in `attrs["soil_classes"]`.
- **Still open:** the rest of the split and the column's name, below.
- **No longer needed for the SPT histograms (P03):** the user picks the class table and passes the rows it applies to. `soil_class` could later pick the table automatically.
- **What depends on it:**
  - USCS organic flags (§8.2);
  - future tooling that suggests a class from lab data.
- **Questions:**
  - Should the categories be behavior-based (cohesive / cohesionless / intermediate) or material-based?
  - Do you need `intermediate`, e.g. silty sand with PI < 7?
  - How should fill be handled (by its dominant behavior)?
  - Is rock (weathered, IGM) worth separating?
  - Should the column be renamed (`material_class` or `ground_class`) now the example site has a rock unit (Sandstone, `rock`) and the draft list has `fill`, neither a soil class? 0.1.0 is on PyPI, so the old header would be read through a deprecation period. Decide with the categories, as a unit of its own.

### 5. Plasticity and gradation systems · Claude (verify) · docs/analysis/index-and-spt.md §2–3 · needed for P04–P05 (Phase 1)
Verify against the source standards:
- BS 5930:2015+A1:2020 plasticity terms (low < 35, intermediate 35–50, high 50–70, very high 70–90, extremely high > 90 LL);
- AASHTO M 145 / ASTM D3282 group and group-index rules;
- ASTM D2487-17 USCS;
- ISO 14688-1 size fractions.
- the sieve lists in `config/sieves.yaml` (ASTM E11 sizes and designations; the ISO list at the ISO 14688-1 boundaries), used by P05.

### 22. Organic soils (OL, OH) in USCS · You · docs/analysis/index-and-spt.md §2; P04
- **Problem:** USCS splits OL from ML and OH from MH by the oven-dried LL, which isn't in AGS LLPL, so the analysis gives only the inorganic symbol.
- **To decide:**
  - Where a user records that a specimen is organic: a per-specimen column, `soil_class = organic` (#3), or a field the user names.
  - How P04 marks organic specimens so they read differently from the rest (e.g. hollow markers with a legend entry).

### 24. NP specimens with LL under 20 · You · docs/analysis/index-and-spt.md §2.5
- **Problem:** `plasticity()` classes an NP specimen at PI = 0. Below LL 20 the A-line's PI is negative, so PI = 0 is on or above it, and BS 5930 gives `CL` (a clay) for a non-plastic soil. USCS gives `ML` only because PI = 0 is under 4. The test file's NP sand has LL 21 to stay clear of it.
- **To decide:**
  - Whether an NP specimen is always M (silt) in both systems, whatever its LL.
  - How a plastic specimen with LL under 20 is classed, where the A-line doesn't reach (both charts start their zones at LL 20 or above).

---

## Quality control

### 6. QC thresholds — P001/P003 tolerances · You · docs/data/qc.md §4.7
Revisit as real files are tested:
- **P001** (grading curve rises): 0.5 percentage points.
- **P003** (GRAG fractions don't sum to 100): ±2 percentage points. Held on a real 4.1.1 file (2026-10-21): 3 findings, each 5 to 10 points from 100 and each a genuine error in the source report's tables; none came from rounding.

### 25. Pressuremeter depth at the probe center · You · docs/data/qc.md §4.4 (D003)
`PMTG_DPTH` is the center of the probe, so the hole went at least half the probe's expanding length deeper. D003 compares the center with `LOCA_FDEP`, so it misses a test whose center is above the final depth but whose lower half isn't. D003 could add half the probe length, when it is known. Minor; seen once on a real file.

### 26. Slope-aware L005 · You + Claude · docs/data/qc.md §4.2 (L005)
On a real file, a valley gave 22 L005 hits that were real topography. Options: compare a hole with a plane fitted through its neighbors rather than their median, or scale the tolerance with the distance to them. Meanwhile, accepted findings (qc.md §3.4) accept them per project.

### 27. Writing accepted findings from a report · You + Claude · docs/data/qc.md §2
Typing accepted-findings entries (qc.md §3.4) by hand is slow when a reviewer accepts many findings one at a time. A helper such as `report.accept(rows, reason=...)` could write or extend the YAML file from rows of `report.findings`. Left out because it is a second API; revisit once accepted findings have been used on a real review.

### 28. D003/D004 for geophysical profiles · You + Claude · docs/data/qc.md §4.4 (D003, D004)
A downhole or surface velocity profile (often a user-defined group) can run below `LOCA_FDEP`, for example to 30 m for Vs30, and outside the logged geology. D003 and D004 report it as a depth error. Options: exempt groups that hold a geophysical profile, or report them as info. Accepted findings (qc.md §3.4, `group:` entries) cover it per project for now.

### 7. Minimally useful fields · You · docs/data/qc.md §4.10
- Review the default list group by group against real files.
- **Later (Roadmap):** conditional requirements, e.g. `SPEC_*` only required when a sample has more than one specimen.

---

## Statistics (research items, with Claude's recommendations)

### 8. The truncated normal, and bands in `fit()` · You · `docs/analysis/statistics.md` §1
Two options for `fit()` (statistics.md §1 has what is built):
1. **A truncated normal with fixed physical bounds**, for doubly bounded data near a bound (fines near 0 %). SciPy's `truncnorm` takes its bounds in standard units, so fixed bounds need a small custom likelihood, tested on its own. Beta covers the case meanwhile.
2. **Bands as interval-censored values.** `fit()` leaves bands (`<target>_lower`/`_upper` with no value) out and counts them, because a correlation's band is the spread of its coefficient, not a measurement known to lie in an interval. Fitting one as an interval would treat a modeling range as data; revisit only if a source gives true intervals.

**References:**
- Johnson, N.L., Kotz, S. & Balakrishnan, N. (1994). *Continuous Univariate Distributions*, Vol. 1, 2nd ed. Wiley. Truncated normal and lognormal.
- SciPy docs: `scipy.stats.truncnorm`.

### 13. Representative values: what stays open · You · `docs/reference/eurocode7-summary.md` §3.2, §3.5 · when a project needs it
Two points of `ht.stats.representative()` (statistics.md §2) stay open:
- **The Angus (1988) bound on the mean of a lognormal trend.** A lognormal line through ln x gives the median; the JRC report mentions Angus's approximation for a proper confidence bound on the mean. Not offered: verify it against the source before building it.
- **Γ² from a variance function.** The JRC report gives Γ² = θ/L, capped at 1, which hangtu uses. Vanmarcke's variance function for the exponential correlation model (in the EC7 summary §3.2, unverified) gives a smooth Γ² that needs no cap. Build only once it is checked against Vanmarcke (1983) and a user needs it; estimating θ from a CPT is a separate helper.

**References:**
- Angus, J.E. (1988). Inferences on the lognormal mean for complete samples. *Communications in Statistics – Simulation and Computation* 17(4).
- Vanmarcke, E.H. (1983). *Random Fields: Analysis and Synthesis*. MIT Press.

---

## Plots

### 23. Text in P07's value column · You + Claude · P07 §3, §11
- **Problem:** P01 draws text values (`NP`, `refusal`, other text) at the left edge and counts them, but P07 still raises an error naming the rows, so the user cleans the column first.
- **To decide:** P07 has no depth axis, so the left-edge markers don't carry over. Count them under each unit (a line under the axis, or in the summary), or keep the error?
- **Reuse:** `hangtu._data.text_values()` reads the column, and `plot/_text_values.py` orders and labels the texts and builds the stats box's "Also" line.

### 16. Other summaries in P07 · You + Claude · P07; SPEC §5
- **Problem:** P07 summarizes through `ht.stats.describe()`'s calculation (SPEC §5), but each unit only with percentiles. A report's baseline may have been summarized some other way, so the data bar and the baseline bar aren't always like for like.
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

### 46. A correlation's standard deviation on P01 · You + Claude · P01, `docs/analysis/correlations.md` §2
A correlation puts its standard deviation on its rows (`<target>_correlation_standard_deviation`), but P01 doesn't draw it. Proposed: ±1 standard deviation as a whisker on each estimate, named in the legend, drawn only where the column has a value. Open: whether a whisker of the source's scatter beside the soil's own spread reads as a confidence interval, which it isn't.

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

### 21. Thewes & Burger (2004) diagram · You (from the paper) · P17 §14
Axes, zones and limits are settled (P17 §4, §6). Still needed from the paper: the figure number and any stated validity (soil or machine type).

### 54. Scatter in the committed figures' data · Claude + You · `docs/plots/img/`, `docs/site/examples/`, P09 §12 (AC 11)
Some synthetic data behind the visual checks and site examples sits closer to its fitted lines and means than a site's data would, so the figures look cleaner than what a user will see. P09 asks for site-like scatter (CoV about 0.3, skew, uneven depths, an outlier or two). Check each image in `docs/plots/img/` and the examples that make them, and regenerate the ones whose data look too clean, with the scatter set on purpose. One commit per plot, each regenerating its image.

### 57. pcf in AGS density headings · Claude + You · `docs/data/ingest.md` §7 (U002); P00 §4.3 · when real US files are available
Check real US files for unit weights put into AGS *density* headings (`RDEN_BDEN`, `PTST_BDEN`, dictionary unit Mg/m³), or the reverse. Ingest resolves pcf by the heading's expected dimension either way, so a unit weight in a density heading would be read as a density. References: ASTM D7263, ASTM D2937, FHWA NHI-16-072.

### 58. How US files fill `ISPT_PEN*` · Claude + You · SPEC §8.2; P00 §4.3 · when real US files are available
Check whether US files fill `ISPT_PEN*` as 6-in increments (152.4 mm) or as nominal 150 mm values. They drive the mid-drive depth (SPEC §8.2), and are converted as lengths either way.

---

## Parameters (SPEC §1.3, `docs/drafts/parameters/README.md`)

### 29. Judgment keys · You · SPEC §4 · settle each when its wave starts
Each judgment declares what it is keyed by and whether one project-wide value is allowed. Proposed:
- GSI by geology unit;
- the disturbance factor D by design case (excavation method and zone);
- σ′3max by design case;
- Bjerrum's μ from PI, so by specimen.

The built judgments and their keys are in `docs/analysis/judgments.md` §5.

### 31. Curves in real files · You · input for wave 0's intent (M16)
Which user-defined groups and headings real files use for triaxial stress–strain curves, rock triaxial, swelling against time and shear box displacement, gathered from the sample dataset being prepared from real projects. Rock triaxial and UCS rows are read into `ht.template("triaxial")`'s shape, with `failure_mode` (SPEC §2.6).

### 32. Published definitions of the model sets · You (copies) + Claude (verify) · SPEC §5 · each set with its wave
One citation in the Mohr–Coulomb set (`docs/analysis/statistics.md` §7) is still unchecked:
- **Bolton, M.D. (1986), The strength and dilatancy of sands, *Géotechnique* 36(1), 65–78** (paywalled, not at hand): the 0.8 relation and the stress condition it was derived for. hangtu cites Kulhawy & Mayne (1990) Eq. 4-16, p. 4-20, which writes it for triaxial compression (φ′tc = φ′cv + 0.8 ψ); the groundhog docs give it for plane strain, and Obrzud & Truty (2018, p. 86) use it for both. The hand calculation doesn't change; the docstring of `mohr_coulomb_set()`, the dilatancy site page and sheet 09 say which condition holds once the primary is read.

**The other sets**, each checked by the wave that builds it on the model-set base: Hardening Soil (Schanz, Vermeer & Bonnier 1999?) and HS-small (Benz 2007?) with wave 5 (M23); Soft Soil (Vermeer & Neher 1999?) with wave 3; generalized Hoek–Brown (Hoek, Carranza-Torres & Corkum 2002) with wave 4 (M22). Confirm a non-vendor published source that defines each set's parameters; where only a software manual defines a model, say so.

### 34. γw as a judgment · You · SPEC §4
`ht.settings.water_unit_weight` is one session value. Sites with both seawater and fresh water (or brines) need two, so γw may become a judgment keyed by hole or zone.

### 35. `strata=` from a per-hole stratigraphy · You + Claude · P01 §8
P01's `strata=` takes one stratigraphy; the user filters `p.stratigraphy()` to one hole. Later, `strata=` could take the per-hole table directly (one hole, or with a `loca_id` filter) and convert a depth pair to elevation with that hole's ground level.

### 36. Wolff (1989) · Claude (verify) · page 04, `docs/analysis/correlations.md` · before building it
φ′ = 27.1 + 0.3 (N1)60 − 0.00054 (N1)60², a fit to Peck, Hanson & Thornburn (1974). Verify the equation, its coefficient (copies print 0.00054 or 0.00053) and its N basis against Wolff (1989), ASCE GSP 23, 96–106, then build it as a correlation.

### 39. Sowers (1979) · Claude (verify) · page 05, `docs/analysis/correlations.md` · before building it
s_u against N for low, medium and high plasticity, known only as lines on EPRI EL-6800 Fig. 4-50 (after Djoenaidi), with no equation: the coefficients would be read off a chart. Build it only once the lines' equations are verified against Sowers (1979) itself.

### 38. Correlation profile: the input beside the estimates · You + Claude · P01, SPEC §4
Today the estimates draw on one P01 profile by `correlation_name`, and a blank estimate shows only as a footnote count. A two-panel figure on a shared depth axis would show why: the left panel the input the correlation read (N60 or (N1)60, and σ′v where it is used) with each correlation's range drawn as limits, the right panel the estimates. A test with no estimate is then visible on the left, outside a range or marked as a refusal.

Proposed: two panels, not one axes with twinned x axes. A second x axis on the same profile makes the reader match each marker to one of two unrelated scales; the input and estimate markers interleave at the same depths, and the axis limits of each are arbitrary relative to the other. Two panels keep one quantity per axis (P01's contract) and still line up by depth. Open: a helper (`ht.plot.correlation_profile(est, ...)`) or a recipe in the correlations guide using `ht.Sheet` with `ax=`; `Sheet` has no shared vertical axis yet, so either needs one (matching depth limits across panels).

### 51. Comparing groups with censored values · You + Claude · SPEC §5, `docs/analysis/statistics.md` §3 · when a lab dataset needs it
`compare()` and `compare_groups()` take censored values at their value and count them, with a note that the means, and so Welch's results, are biased; the ranks treat a common bound as tied, and order bounds at different values as if they were measured. Statistics are designed for lab data (SPEC §5), so the cases that matter are lab ones: s_u from a hand vane or pocket penetrometer at the instrument's maximum (`>x`), hydraulic conductivity below what the test resolves (`<x`), percent passing `<x`. SPT refusals aren't the reason to build this. Candidates (Helsel et al. 2020, ch. 13): the Peto–Prentice generalized Wilcoxon test for values censored in one direction, preferred to Gehan's when censoring differs between groups, with a k-group form for `compare_groups()` (not in SciPy, about 50 lines and a hand-checked golden value); a likelihood ratio test from `fit()`'s censored likelihood, one distribution against one per group, as the parametric counterpart; no test, with a note, when a comparison has values censored both ways. Build when a lab dataset with censored values needs a comparison.

### 52. Chance-corrected agreement in `crosstab()` · You · SPEC §5, `docs/analysis/statistics.md` §4 · when a use appears
`crosstab()` reports the share of rows that agree and lists the rest, with no test or kappa: a log and a lab classification of the same soil are plainly related, and Cohen's kappa assumes the two classifications were made independently, which a log written after the lab results isn't. Revisit if a use appears where they are independent (two loggers, two labs), and decide then whether kappa, weighted kappa for ordered classes, or another measure fits, with its interval.

### 47. The scale of three correlation standard deviations · Claude (verify) · `config/correlations.yaml`, `docs/analysis/correlations.md` §2
Mayne & Kemper's σ′p (S.D. = 4.37 pa) and OCR (3.82), and Kulhawy et al.'s K0 (0.43), have `scale: null`, so none is on the rows yet. Check each against Mayne & Kemper (1988), Kulhawy et al. (1989) or Kulhawy & Mayne (1990), Figs. 3-9, 3-18 and 3-30: whether it is the regression's standard error on the arithmetic values (then `scale: arithmetic`, and its registry column `<target>_correlation_standard_deviation` is added) or on log values (a factor, which needs a column design first). σ′p's, given in pa, suggests arithmetic.

### 48. Statistics sources not yet checked · Claude (verify) · SPEC §5, `docs/analysis/statistics.md` §1, §3; sources listed in `docs/work/m15c-fit.md` and `docs/work/m15d-compare.md`
`fit()` cites the NIST e-Handbook (§1.3.5.14) for the Anderson–Darling statistic and SciPy's documentation for the bootstrap p-value and the Kaplan–Meier estimate, because the original papers aren't available free. Check each against the paper when a copy is at hand, and update the docstrings and the statistics guide:
- Stephens (1974), *JASA*, doi:10.2307/2286009 (the A² statistic).
- Stute, González Manteiga & Presedo Quindimil (1993), *Metrika* (a parametric bootstrap with estimated parameters; the reference SciPy's `goodness_of_fit` gives).
- Kaplan & Meier (1958), *JASA* (the estimator).

`compare()` and `compare_groups()` cite Helsel et al. (2020), Delacre et al. (2019), Dinno (2015) and Karch (2021), all checked, and SciPy for what they describe only by reference. Not yet checked against the papers:
- Welch (1947) and (1951), *Biometrika* (the t-test and the ANOVA).
- Games & Howell (1976), *Journal of Educational Statistics* (SciPy's `tukey_hsd` cites it).
- Brunner & Munzel (2000), *Biometrical Journal*, and Neubert & Brunner (2007), *Computational Statistics & Data Analysis* (the variance estimate, the interval for p̂, the permutation form).
- Dunn (1964), *Technometrics*, and Holm (1979), *Scandinavian Journal of Statistics*.
- Fagerland & Sandvik (2009), *Statistics in Medicine* (why not Mann–Whitney).

Titles, volumes and pages are to be taken from each paper, not from memory.

### 53. Triaxial test standards · You (copies) + Claude (verify) · `docs/data/qc.md` §4.12, `docs/analysis/strength.md` §2–§5; sources listed in `docs/work/m11a-triaxial-data.md`
QC X001's `lowest_pore_pressure_parameter_b: 0.95` is the B-value commonly quoted as the requirement before shearing, not yet checked against a standard. Check it, and what each allows for stiff soils (a lower B where B stops rising with back pressure), in ASTM D4767 (CU), ASTM D7181 (CD) and ISO 17892-9, with the clause. Then cite it in `qc/rules.yaml`, X001's message and qc.md. `mohr_coulomb_fit()` and `shear_box_fit()` read `failure_criterion` as written and only refuse to pool different ones (strength.md §3–§5; for the shear box, ASTM D3080 and D6467), and `triaxial_failure_from_readings()` defines maximum deviator stress and maximum principal stress ratio from readings without a default (strength.md §2), so nothing built depends on which a standard requires. Check what D4767, D7181 and D2850 (UU) say of each, and of a limiting strain, before a fit, a QC rule or a docs page recommends one.

### 41. Gravelly sands under `not_for` · You + Claude · page 04, `docs/analysis/correlations.md` §2
Hatanaka & Uchida (1996) is `not_for` gravelly soils, but the USCS check reads only the group symbol. The example site's Terrace is "SAND with gravel (SP)": SP passes, so its rows get estimates with no note. USCS group names (ASTM D2487) add "with gravel" at ≥ 15 % gravel, which the symbol does not carry.
- **Questions:**
  - Read the group name or description (`geology_description`, or a `uscs_name` column), the gravel fraction from gradation tests, or leave it to the user to pass the rows?
  - If flagged: no estimate ("not for this soil"), or an estimate with a note?
  - Which other entries have `not_for` terms the symbol can't check (micaceous sands, fissured clays)?

### 44. Strata labels clipped above the axes · Claude · P01 §7, `src/hangtu/plot/_overlays.py`
- **Problem:** a strata label is drawn 2 pt below the top of its band, clipped to the axes. When the band's top is beyond the vertical limit, the label falls outside the frame and is cut off or lost. `docs/plots/img/P06-si.png` shows it: the Fill band starts at 11.1 m and the axis at 11 m, so "Fill" is clipped at the top. US hides it only because the limit happens to be above the band.
- **Wanted:** every band that shows inside the axes keeps a readable label.
- **Questions:**
  - Place the label at the top of the visible part of the band (the band's top clipped to the axis limit), or move the limit out to the band's top?
  - A band too thin on the axes for its label: leave the label out, or count it in the footnote?

### 45. Recommended user-defined AGS fields · You + Claude · SPEC §4, §6.2
- **Idea:** hangtu could ship a set of recommended user-defined headings or groups, so a file can carry values that the AGS dictionary has no place for. One example is a specific gravity chosen for a geology unit; another is what an in situ hand penetrometer reads (`IPEN_IPEN`, s_u or q_u), which `p.undrained_strength()` takes as `hand_penetrometer_scale=`. With those fields filled in, users get all of hangtu's functionality straight from the file.
- **Questions:**
  - Which values would be in the set?
  - A value carried in the AGS file: is it data, or a judgment? SPEC §4 keeps judgments in `judgments.yaml`, where they can be reviewed, so a judgment in the file would have to say where it came from.
  - How would the set be published? For example, as a `DICT` block users copy into their files.
  - How does this fit with wave 0 (M16, user-defined groups)?

### 55. The sandstone triaxial set in site.ags · Claude · `tests/data/_make_examples.py`, `src/hangtu/examples/__init__.py`
- **Rule:** example data goes into `site.ags` first, and the example CSVs are written from that project.
- **Problem:** `rock_triaxial.csv` is made on its own, in MPa, and isn't in `site.ags`.
- **Wanted:** B-3's sandstone UCS and triaxial tests in `site.ags` (TREG/TRET, and the UCS group), with `rock_triaxial.csv` written from `p.triaxial()`, so the Hoek–Brown examples and P32 read the same tests as the file.
- **Questions:**
  - Does the AGS file carry `failure_mode`, which `hoek_brown_fit()` needs, or is it added after ingest?
  - The file is in US units while the CSV is in MPa: convert on writing, or keep the CSV in the file's units?

### 56. Named design cases as a selection key · You · SPEC §4, §5, `docs/analysis/judgments.md` §5.9 · when a project needs two selections of one unit
One unit can need two selected values of one parameter: EC7's Type A (a mean) for a long slip surface and Type B (a fractile) for a footing, or short- and long-term cases. SPEC §4 lists a named design case among a judgment's possible keys, but the `selection` judgment is keyed by parameter and geology unit only. Until a case key exists, `select(selection=...)` or a second judgments file passed as `judgments=` gives one case at a time. Open: the key's place in the file (a `cases:` level above the parameter, or one per entry), how `select()` names the case (`case=`), and how model sets carry it (one set per case).

### 59. Shared result code in `ht.stats`, and module size · Claude · `src/hangtu/stats/`, `src/hangtu/project.py` · for M19's intent
- **Problem:** seven `ht.stats` modules each write their own `_notes()` (`_compare`, `_crosstab`, `_describe`, `_fit`, `_refusal_limit`, `_representative`, `_select`), and the count lines are built in `_fit._count()` and twice in `_result.py`. A new result type would add another copy. `_select.py`, `_result.py`, `_compare_sources.py` and `project.py` are each over 1,100 lines.
- **Open:** whether the notes and counts share one helper, and whether the four modules split, as a refactor unit of its own before M19 adds the oedometer results.

## Agent-use review (2026-11-09)
A review of the whole package asked one question: if an AI agent does the work and an engineer signs it off, how likely is a wrong answer, and how easy is it to catch? It used probe scripts plus two agent trials (an SPT correlation task and a lab strength task, from the public docs only). Items 60–61 can give a plausible wrong number with nothing to flag it; 62–67 lead an agent to misuse; 68–69 are friction.

### 60. A correlation on rows its `soil_class` rules out · You + Claude · SPEC §4, `docs/analysis/correlations.md` §2 · related to #3, #41
- **Problem:** `effective_friction_angle_hatanaka_uchida_1996` on the Alluvium (lean clay) rows gives φ′ = 28–32° for every row. The only warning is about range bounds, although the frame carries `soil_class == "fine"` and `attrs["soil_classes"]`. SPEC §4 reads soil type only when asked (`uscs=`), so this follows the spec; an agent passing the whole frame won't ask.
- **Options:**
  - warn, and note it in `correlation_note`, when `soil_class` contradicts the entry's `applies_to`;
  - give those rows NaN with a reason unless `uscs=` or an explicit override is passed;
  - leave it as decided.
- **Recommendation (Claude):** the first. It costs nothing when the classes agree, and it reads a column the user already supplied rather than inferring one.

### 61. `spt_class()` defaults to the cohesionless table · You + Claude · `docs/analysis/index-and-spt.md` §1.4, `src/hangtu/analysis/_spt.py`
- **Problem:** `spt_class(clay_rows)` returns "Very loose" and "Loose" for clays with no warning. Its docstring says the table is the engineer's call, but `table="cohesionless"` and `n="spt_n"` are defaults. P03's `spt_histogram()` has the same defaults.
- **Proposed:** make `table=` required in both, which matches SPEC §4's "no defaults for judgments". Also warn when `soil_class` contradicts the table (#3).
- **Open:** whether `n=` is a judgment too (field N or N60 for a class table), or a convention that stays a default.

### 62. Example CSVs that fail their own analyses · Claude · `tests/data/_make_examples.py`, `tests/test_examples.py`
- **Problem:** `undrained_shear_strength_from_tests()` on `strength.csv` raises "more than one input to s_u" on the UU rows, because both s_u and q_f are filled in. The trial agent edited the data by hand to make it run. The hand penetrometer values sit in `undrained_shear_strength` with `hand_penetrometer_reading` blank, so `hand_penetrometer_scale=` never applies, while the docs example says the instrument read q_u. The docs examples take the AGS route only, so no test runs the CSVs.
- **Wanted:** each example CSV passes the analysis its template feeds, tested, with the penetrometer readings in `hand_penetrometer_reading`.

### 63. `representative()` with most values censored · You + Claude · `docs/analysis/statistics.md`
- **Problem:** with 25 of 40 Hatanaka & Uchida values "at least 44.5°", the censored normal fit gives a mean of 45.4° and a characteristic value of 44.6°. That is above every real estimate (max 44.1°) and above the correlation's ceiling. The note explains how censored values were treated but doesn't warn about the result.
- **Proposed:** warn when more than half the values are censored, or when the representative value is beyond the largest (or, low side, the smallest) uncensored value.
- **Open:** the threshold, and whether `fit()` and `compare_sources()` warn the same way.

### 64. `read_csv` and bounds written as text · You · `src/hangtu/units/__init__.py`, SPEC §2.6
- **Open:** should `ht.read_csv` split `<x`/`>x` into the qualifier column when the template has one, as AGS ingest does for value flags?

### 66. The CSV route leads to invented inputs · Claude + You · `docs/site/getting-started/csv.md`, `src/hangtu/examples/data/`
- **Problem:** no page shows a CSV stratigraphy for `vertical_stress()`, nor the triaxial and undrained strength analyses from CSV; every example starts from `site.ags`. The trial agent tried `strata.csv` as the log (it is the geology map), then made up layer boundaries midway between tests. The lab agent built about 24 unit declarations by hand from `ht.columns()`.
- **Proposed:** ship `stratigraphy.csv` with the examples; add one CSV-route example per analysis family; rename `strata.csv` to `geology_map.csv` (examples-ags-first: written from `site.ags`).
- **Open (You):** a way to declare a file's units in one step, e.g. from each column's `quantity` and a stated system. It is a declaration, not a guess, but it would cover columns the user never looked at.

### 67. Stress units declared wrong · You · SPEC §2.2, §2.6
- **Problem:** the triaxial CSV in psf declared as kPa gives c′ = 104 kPa and σ′n up to 3,680 kPa at 18 ft, with no check. The summary prints the unit, so a reviewer could catch it; an agent won't. Typical ranges are never used for QC (P00), by design.
- **Idea:** a physical check rather than a typical range, for example a consolidation stress more than about 10× the overburden at the sample depth warns.

### 69. Friction from the agent trials · Claude · plots, `src/hangtu/units/`
- `spt_profile(n="spt_n1_60")` is rejected; the agent fell back to `profile()` and marked refusals by hand.
- A long `note=` collapses the axes, and the only sign is matplotlib's warning.
- `failure_envelope()` with two units on shared equal axes crams the clay circles near the origin.
- `fit(group_by=[...])` returns count-0 rows for groups with nothing to fit.

---

## Later / far future (also on the Roadmap)
- Title block and company drafting-standard templates for `Sheet`.
- A helper for deciding cohesive vs cohesionless from lab data (fines %, PI).
