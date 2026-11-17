# M19 (b): compressibility

## Intent
M19's second unit (M19 (a) decision 1): stage B for sheet 06, the first derivation from `p.oedometer()`'s
increments. 🟡 marks a choice proposed here, awaiting review.

**Goal:** from `p.oedometer()` (or a CSV in the `oedometer` template), an engineer gets, per specimen, σ′p, Cc, Cr
and Cs, and, where σ′v0 at the specimen's depth is given, OCR and the sample quality by Δe/e0. Each value is
reproducible from the increments, says which points it used and which it left out and why, and says when it can't
be given. P13 draws the e–log σ′v curve with the fitted lines and σ′p, so the engineer can see whether the fit is
believable before using it.

**Why:**
- **Stage A has nothing to compare yet.** `p.oedometer()` (M19 a) gives the increments, but σ′p and OCR exist only
  as SPT correlations (M13 b2). The site page for sheet 06 says oedometer tests on good samples overrule them, and
  its Methods table lists "σ′p, Cc and Cs from an oedometer curve" as W3.
- **σ′p depends on the method by 10–20 %** (sheet 06 §6), and on disturbance more than either. So the method is
  fixed and stated, deterministic (the same increments give the same σ′p), and the quality grade sits next to it.
- **The example file can draw it.** `site.ags` has two specimens with eight to twelve increments and an
  unload–reload loop each (M19 (a) decision 10), so P13 and the docs page run on the example project.

**The derivation** (sheet 06 §5.1, §5.3, §5.8; sources under "Evidence"):
- **σ′p by Oikawa (1987):** two straight lines fitted to the loading branch (`load_branch = "loading"`) in
  log(1 + e) against log σ′v, the split between them searched by least squares, σ′p where they cross. It is
  deterministic (the same increments give the same σ′p) and needs no smoothing (decision 5).
- **Cc and Cr:** the slopes of e against log σ′v of the same two groups of points: Cc from the points above the
  split, Cr from those below.
- **Cs** from the unloading branch: the slope of e against log σ′v over an unload (🟡 which unload, and whether the
  reload is used too, in the spec step).
- **CR = Cc / (1 + e0)** on the result (decision 4).
- **σ′p by Pacheco Silva (1970) as the check:** the virgin line (Cc's) meets the horizontal through e0; down to the
  curve; across to the virgin line; σ′p is that point's stress (decision 2).
- **OCR = σ′p / σ′v0,** reading `effective_vertical_stress` from `ht.analysis.vertical_stress()` on the
  `p.oedometer()` rows, as the SPT OCR correlation does. Without the column, OCR is blank with a reason, never
  filled from an assumed σ′v0. An OCR below 1 is kept and flagged, not clipped (sheet 06 §7).
- **Δe/e0 = (e0 − e at σ′v0) / e0,** e at σ′v0 interpolated in log σ′v on the loading branch, graded by Lunne et al.
  (1997) into its four classes for OCR 1–2 and 2–4. Outside OCR 1–4 the value is given without a class.
- **The result** is a derived result (SPEC §5) like the envelope fits: one row per specimen, the points each line
  used, and the rows left out counted by reason. 🟡 One function, `compressibility_fit()` or similar, named in the
  spec step against the registry.

**Constraints:**
- The fit reads only the loading branch for σ′p, Cc and Cr; a reload slope is never Cc (sheet 06 §7).
- A specimen that can't give a value has a reason, not an error: too few points on either side of σ′p (sheet 06 §7,
  maximum stress below 2–3 σ′p), no unload, no loading branch.
- Points outside the method's reach are counted and reported, never dropped to make a fit work (SPEC §4,
  "Validity is reported").
- Golden values hand-calculated on the M19 (a) specimen BH1 U3 (twelve increments, one unload–reload loop, a second
  unload), and on one curve with no clear break.
- Every method cites a verified source, or it is cut rather than shipped unverified.

**SPEC and docs touched:**
- SPEC §4 (a bullet for the oedometer fit, as the envelope fits have), §5 (a derived result's names), §10.3 (new
  registry columns).
- 🟡 A new `docs/analysis/compressibility.md`, which (c) and (d) extend, rather than a section in `strength.md`:
  compressibility isn't strength.
- `docs/plots/P13-consolidation-curve.md` (promoted from the README's idea row in the spec step).
- Sheet 06 (§5.1's "standard construction [U]" becomes Oikawa; §5.2 and §5.4 marked later) and its site page
  (Methods, Pitfalls); sheet 11 and the parameter index (Eoed and Eur,oed move to (c)); `STATUS.md`'s M19 row.
- TODO: a new item for Casagrande and the work method, with a trigger (decision 2).

### Evidence (searched 2026-11-17)
- **The two-line method:** no source found names a least-squares two-line fit in e–log σ′v as a method. Umar &
  Sadrekarimi (CGJ manuscript cgj-2016-0203.R1, Table 1, p. 28) list the line-fit methods: Burland (1990) in the void
  index, and the bilogarithmic Butterfield (1979, ln(1 + e)–ln σ′v), Oikawa (1987, log(1 + e)–log σ′v), Onitsuka et
  al. (1995, ln(1 + e)–log σ′v) and Jose et al. (1989, log e–log σ′v). Of eleven methods on their database Oikawa
  ranked first by RMSE (33.2 kPa), Casagrande eighth (44.3), Pacheco Silva ninth (49.5) (Table 7, p. 34); bilogarithmic
  plots give straighter lines (p. 5). Oikawa (1987), *Soils and Foundations* 27(3), 99–104,
  doi:10.3208/sandf1972.27.3_99, a technical note (read from J-STAGE's scan): for soft soils, log f–log p (f = 1 + e)
  "is better" linear than e–log p, is "composed of two segments of straight line", and the stress where they
  intersect "agrees well with the consolidation yield stress" from Casagrande's construction (abstract, p. 99). Its
  data are soft soils (sensitive clays, organic soils, peat), which the spec step turns into the method's stated
  range. 🔬 The equations and the fitting procedure (pp. 100–104), and the published version of Umar &
  Sadrekarimi, in the spec step.
- **Pacheco Silva's construction:** steps (i)–(v) as above, quoted in Paniagua, L'Heureux, Yang & Lunne (2016),
  NGM 2016, §2.4, p. 548, citing Pacheco Silva (1970), Proc. 4th Brazilian Conf. SMFE, Rio de Janeiro, 225–232. It
  uses e0, "the specimen void ratio before any load has been applied". The same paper finds five methods within 14 %
  on good-quality samples.
- **Lunne et al. (1997) bands,** read in two secondary sources that agree: Krage, DeJong, DeGroot, Dyer & Lukas
  (2015), 6ICEGE, Table 1, and Thakur (2016), NGM 2016. OCR 1–2: < 0.04 very good to excellent, 0.04–0.07 good to
  fair, 0.07–0.14 poor, > 0.14 very poor; OCR 2–4: < 0.03, 0.03–0.05, 0.05–0.10, > 0.10. Δe is the change in void
  ratio on reconsolidation from the specimen's initial state to σ′v0 (Krage et al.). This confirms the intermediate
  bands sheet 06 had as [U].
- **mv's definition** (BS 1377-5, ISO 17892-5) wasn't found in an open source; it stays with TODO #73 and (c).

### Decisions (intent review, 2026-11-17)
1. **Eoed and Eur,oed move to (c),** changing M19 (a) decision 1. Eoed = 1/mv per increment, so it hangs on the same
   definition as TODO #73 (Δe over 1 + e at the increment's start, or over 1 + e0), and (c) recomputes mv and draws
   it on P14.
2. **Pacheco Silva is the one check on σ′p for now.** It reuses the fitted virgin line and e0, so it is
   deterministic. Casagrande (a smoothing choice for maximum curvature, a hidden judgment) and the work method (a
   strain definition, TODO #73) come later; a TODO records them with a trigger.
3. **Cr and Cs are reported separately:** Cr from the loading fit's flat line, Cs from an unload. Disturbance raises
   Cr, so keeping them apart shows it.
4. **CR = Cc / (1 + e0) is on the result,** so a lab's CR (ε–log σ′v) compares with it.
5. **σ′p by Oikawa (1987) rather than a two-line fit in e–log σ′v** (the search, under "Evidence"). M19 (a)
   decision 1 named a "bilinear fit"; this is one, in the plot its source says is straighter, and it is the best
   ranked in the one comparison found. Cc, Cr and Cs stay e–log σ′v slopes, as the sheet and the models define
   them.

### Out of scope
- mv, cv, k, Eoed and Eur,oed, P14 and P15 (c); rock swelling (d); K0 from OCR, SHANSEP and the Soft Soil set (M20).
- Cc from LL and other stage C correlations for sheet 06.
- Stage D for σ′p and Cc (`representative()`, `select()`) and TODO #59.
- CRS and Rowe cell tests (`ESCG`, `ESCT`) and the lab's reported σ′p and Cc.
- Casagrande, the work method and the other line-fit methods (decision 2).
- Strain-based curves (ε–log σ′v) as the fitted quantity; P13 may draw strain as an axis option (spec step).
