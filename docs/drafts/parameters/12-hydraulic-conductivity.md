# 12 — Hydraulic conductivity

| | |
|---|---|
| **Parameters** | k (hydraulic conductivity, soil), k (equivalent rock-mass conductivity), kh / kv (anisotropy), Lu (Lugeon value), T (transmissivity) |
| **Material** | Both |
| **Constitutive models that use it** | All coupled / consolidation analyses (MC, HS, HB with flow or consolidation); seepage / inflow (Darcy) |
| **Depends on** | [01-unit-weight-and-vertical-stress](01-unit-weight-and-vertical-stress.md) (σ′v0 at test), [02-index-properties](02-index-properties.md), [03-specific-gravity-and-void-ratio](03-specific-gravity-and-void-ratio.md) (e, D10), [06-preconsolidation-and-compressibility](06-preconsolidation-and-compressibility.md) (mv, cv) |
| **Feeds** | [06-preconsolidation-and-compressibility](06-preconsolidation-and-compressibility.md) (time rate), [11-hardening-soil-stiffness](11-hardening-soil-stiffness.md) (consolidation runs), [21-swelling-rock](21-swelling-rock.md) (rate of water access) |

## 1. Phenomenon
k is the Darcy coefficient relating discharge velocity to hydraulic gradient for water at test temperature. In soil it
is controlled by pore size (D10, e, fines, fabric, layering); in rock it is controlled almost entirely by open,
connected discontinuities, so intact-rock k is orders of magnitude below rock-mass k. Values span about 13 orders of
magnitude and are close to log-normally distributed [6]. k is strongly scale dependent (lab specimen < borehole
interval < pumping test < tunnel scale in fractured ground) and anisotropic (kh > kv in bedded or varved deposits).
It decreases with effective stress (fracture closure, consolidation), so depth/stress at the test must be recorded.

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| k | m/s | ft/day; cm/s; US gal/day/ft² | 1 m/s = 100 cm/s = 2.835×10⁵ ft/day = 2.120×10⁶ gpd/ft²; 1 gpd/ft² = 4.716×10⁻⁷ m/s (computed; cf. [6] Table 2.3) |
| T = k·b | m²/s | gpd/ft; ft²/day | K(cm/s) = (T/b)·4.716×10⁻⁵ with T in gpd/ft, b in ft [5] |
| Lu | L/min/m at 1 MPa (10 bar) | — | 1 Lu ≈ 1.3×10⁻⁷ m/s (Thiem form with ln(R/r) ≈ 5.0, computed) [9] [U] |
| mv, cv (oedometer) | m²/MN, m²/yr (AGS units) | ft²/kip, ft²/yr | k(m/s) = 3.109×10⁻¹⁰ · cv(m²/yr) · mv(m²/MN) with γw = 9.81 kN/m³ (computed) |

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| Clean gravel / clean sand | ~10⁻² to 10⁻⁶ m/s | [6] Table 2.2 [U] (table is an image; not read) |
| Silt, loess, glacial till | ~10⁻⁵ to 10⁻¹² m/s | [6] Table 2.2 [U] |
| Unweathered marine clay | ~10⁻⁹ to 10⁻¹³ m/s | [6] Table 2.2 [U] |
| Shale (intact / mass) | ~10⁻⁹ to 10⁻¹³ m/s intact; mass k set by joints | [6] Table 2.2 [U] |
| Limestone / dolomite; fractured rock | ~10⁻⁵ to 10⁻⁹ m/s; karst much higher | [6] Table 2.2 [U] |
| Packer-test bands | <1 Lu "very tight" … >100 Lu "open / closely spaced or voids" | Quiñones-Rozo (2010) via [9] [U] |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Lab, flexible-wall (fine soil) | D5084-24 | ISO 17892-11:2019 | PTST: PTST_K, PTST_TSTR, PTST_HYGR, PTST_VOID, PTST_CELL, PTST_TEMP | k at stated mean σ′ |
| Lab, rigid-wall (coarse soil) | D2434-26 | ISO 17892-11 | PTST (as above) | k (remolded/reconstituted) |
| Oedometer (indirect) | D2435/D2435M-25 | ISO 17892-5; BS 1377-5 | CONS: CONS_INCF, CONS_INMV, CONS_CVRT, CONS_CVLG; CONG | k = cv·mv·γw per increment (§5.4) |
| Single-well rising/falling head (slug) | D4044/D4044M-15 (withdrawn 2024, no replacement) | ISO 22282-2 | FGHG: FGHG_TESN, FGHG_TDIA, FGHG_SFAC, FGHG_SFRF, FGHG_CNFG, FGHG_IPRM; FGHT: FGHT_DURN, FGHT_RDNG | k of test zone (§5.1–5.2) |
| Packer (water-pressure / Lugeon) | D4630-19 (constant head injection); D4631-18 (pressure pulse) | ISO 22282-3 | FGHG: FGHG_IPRM, FGHG_ILUG, FGHG_FTYP, FGHG_HEAD, FGHG_FLOW; FGHS: FGHS_STG, FGHS_HEAD, FGHS_FLOW, FGHS_IPRM, FGHS_ILUG | Lu per stage, representative k (§5.3) |
| Pumping test | D4050-20 | ISO 22282-4 | PUMG: PUMG_TEST; PUMT: PUMT_DTIM, PUMT_DPTH, PUMT_QUAT (l/s) | T, S; k = T/b (§5.5) |
| Grading (for Hazen) | D6913 / D7928 | ISO 17892-4 | GRAT: GRAT_SIZE, GRAT_PERP; GRAG: GRAG_UC, GRAG_FINE | D10 (§5.6) |

AGS units: FGHG_IPRM, FGHS_IPRM, PTST_K in m/s; FGHG_ILUG dimensionless (example "10 or <1", i.e. censored values are
written with "<"). FGHG_METH example "BS EN ISO 22282-2:2012"; PTST_METH example "BS EN ISO 17892-11:2019".

## 5. Derivations and correlations

### 5.1 Hvorslev basic time lag — Hvorslev (1951)
$$K = \frac{A}{F\,T_0},\qquad F_8 = \frac{2\pi L}{\ln\!\left[L/D + \sqrt{1+(L/D)^2}\right]},\qquad K \approx \frac{r^2\ln(L/R)}{2\,L\,T_0}\ (L/R>8)$$
- **Inputs:** r standpipe radius, R intake radius, D = 2R, L intake length (m); T0 = time for (H−h)/(H−H0) = 0.37 (s).
- **Valid for:** rising/falling head in a piezometer intake in uniform soil, no storage (quasi-steady); semi-log plot linear.
- **Scatter:** Hvorslev's Case 7/8 shape factors are approximate; Mathias & Butler give an exact spheroid form [2].
- **Source:** [1]; F8 form [V] via [2] eq. 12; K = r² ln(L/R)/(2LT0) and L/R > 8 [V] via [6] §8.5 eq. 8.34. The
  large-L/D form was checked numerically against A/(F8·T0) (agree within 0.5 % for L/R ≥ 10, computed).

### 5.2 Bouwer & Rice slug test — Bouwer & Rice (1976)
$$K = \frac{r_c^2\,\ln(R_e/r_w)}{2L_e}\cdot\frac{1}{t}\ln\frac{y_0}{y_t}$$
- **Inputs:** rc casing radius, rw well (screen + pack) radius, Le screen length, Re effective radius (empirical A, B, C
  coefficients from electrical analog), yt head displacement at t.
- **Valid for:** unconfined aquifer, fully or partially penetrating well; Thiem-based quasi-steady.
- **Source:** [3] [U] — basis (Thiem, analog-derived Re) seen in the abstract; equation form not seen in the original.

### 5.3 Lugeon value and Houlsby interpretation — Lugeon (1933); Houlsby (1976)
$$Lu = \frac{Q}{L}\cdot\frac{P_0}{P},\quad P_0 = 1\ \text{MPa (10 bar)};\qquad k \approx 1.3\times10^{-7}\,\text{m/s per Lu}$$
- **Inputs:** Q (L/min), L test length (m), P net test pressure at the interval (bar or MPa).
- **Procedure:** five 10-min stages a–b–c–b–a; the pattern of Lu across stages identifies laminar, turbulent,
  dilation, wash-out or void-filling behavior and so the representative value (e.g. average for laminar; peak stage
  for turbulent; low-pressure stages for dilation; highest/final for wash-out; final/lowest for void filling) [4].
- **Valid for:** isotropic, homogeneous equivalent porous medium; the k conversion assumes laminar radial flow.
- **Source:** Lu formula and five-stage procedure [V] via [9] (NGI slides); Houlsby summary [V] abstract [4];
  representative-value rules and 1.3×10⁻⁷ conversion [U] (seen only in secondary summaries).

### 5.4 Oedometer-derived k — Terzaghi consolidation theory
$$k = c_v\, m_v\, \gamma_w$$
- **Inputs:** cv (CONS_CVRT or CONS_CVLG, m²/yr), mv (CONS_INMV, m²/MN), γw. Use the increment spanning σ′v0.
- **Valid for:** saturated fine soil, increment in the primary-consolidation range. Typically lower than in situ k
  (fabric, fissures and silt partings not captured) _[Judgment — for PE review]_.
- **Source:** definitional relation (cv = k/(mv γw)) [U] — no locator checked.

### 5.5 Cooper-Jacob straight line — Cooper & Jacob (1946)
$$T = \frac{2.30\,Q}{4\pi\,\Delta s}\ \ (\text{SI}),\qquad T\,[\text{gpd/ft}] = \frac{264\,Q\,[\text{gpm}]}{\Delta s\,[\text{ft/log cycle}]},\qquad k = T/b$$
- **Valid for:** constant-rate pumping, confined (or small-drawdown unconfined) aquifer, late time (u small).
- **Source:** [5] US-unit form [V] via an extract of the source (264 = 2.30/(4π) in US units).

### 5.6 Hazen (D10) and Chapuis (D10, e)
$$k\,[\text{cm/s}] = C\,D_{10}^2\,[\text{cm}],\ C \approx 100\text{–}150;\qquad k\,[\text{cm/s}] = 2.4622\left[\frac{D_{10}^2\,e^3}{1+e}\right]^{0.7825}\ (D_{10}\ \text{mm})$$
- **Valid for:** clean, uniform sand and gravel. Hazen is valid only near loose packing [7]; Chapuis fitted to
  D10 = 0.13–1.98 mm, e = 0.4–1.5; not valid for crushed or plastic silty soils.
- **Scatter:** log10(measured/predicted) mean / SD: extended Hazen 0.07 / 0.23; NAVFAC 0.21 / 0.36; Chapuis 0.00 / 0.10 [7].
- **Source:** Hazen form [V] via [8] (MnDOT review table); Chapuis eq. and statistics [V] via [7] abstract.

### 5.7 Statistics of k (log-normal, censored)
- Work in log10 k: report geometric mean (= p50 of a log-normal), and p10 / p90 from mean ± 1.2816·SD of log10 k.
- Results at a test detection limit (e.g. "<1E-9", "<1 Lu") are left-censored: do not substitute the limit and average.
  Use Kaplan-Meier, regression-on-order-statistics or censored MLE [10] [U]; report the censored count.
- Equivalent rock-mass k for flow parallel to layers ≈ thickness-weighted arithmetic mean; normal to layers ≈ harmonic
  mean _[Judgment — for PE review]_.

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Tunnel inflow, steady (Goodman et al. 1965) | Q0 = 2πkH0 / [2.3 log10(2H0/r)] per unit length [11] eq. 2; H0 depth below water table, r radius | High: Q ∝ k (one order in k = one order in Q); Heuer (1995) found Goodman steady-state values overpredict observed inflows and recommends empirical reduction (~1/8 often quoted) [12] [U] |
| Dewatering / shaft and portal design | Drawdown and pumping rate through T = k·b | High |
| Consolidation settlement (soft soil) | Time rate only, via cv = k/(mv γw); final settlement unaffected | Moderate (time, not magnitude) |
| Coupled FE (MC/HS/HB) undrained → drained | Drainage type choice; excess pore pressure dissipation during and after excavation; face stability under seepage | Moderate–high near the drained/undrained boundary |
| Lining loads (watertight lining) | Full hydrostatic pressure; drained lining loads depend on k_lining / k_ground ratio | Low for watertight; moderate for drained |
| Swelling rock | Rate of water access to the swelling zone | Moderate (time dependence) |

**Typical variability:** COV of k (saturated clay) 68–90 %; partially saturated 130–240 % [13] [U]. These are
arithmetic COVs of a log-normal variable; for statistics use the SD of log10 k. Hazen/Chapuis transformation error as
in §5.6 [7]. Scale effect and fracture connectivity usually dominate over test scatter in rock
_[Judgment — for PE review]_.

## 7. Pitfalls and QA checks
- Do not pool lab (PTST, CONS) and field (FGHG, PUMT) k; scale differs — report lab as a check.
- Check FGHG_FTYP / stage pattern before using a packer k; wash-out and dilation stages are not representative.
- Packer tests in tight rock often hit the measurement limit: keep the "<" flag through to statistics (censored).
- Slug tests in low-k soils: skin, smear and incomplete development bias k low; check the semi-log line is straight.
- Lugeon test pressure P is the net pressure at the interval (gauge + column − friction losses − groundwater).
- Record test depth / σ′ (k falls with stress); CONS-derived k must use the increment at σ′v0.
- State kh vs kv; vertical oedometer k is kv.
- Temperature correction to 20 °C for lab k (PTST_TEMP).

## References
[1] Hvorslev, M.J. (1951). Time lag and soil permeability in ground-water observations. Bulletin No. 36, US Army Corps of Engineers WES, Vicksburg. — [U] original not seen; forms via [2], [6]
[2] Mathias, S.A. & Butler, A.P. (2006). An improvement on Hvorslev's shape factors. Géotechnique 56(10), 705–706. https://luk.staff.ugm.ac.id/jurnal/freepdf/MathiasButler-Geotech2006-AnImprovementOnHvorslevShapeFactors.pdf — [V] eqs. 1, 10, 12
[3] Bouwer, H. & Rice, R.C. (1976). A slug test for determining hydraulic conductivity of unconfined aquifers with completely or partially penetrating wells. Water Resources Research 12(3), 423–428. https://doi.org/10.1029/WR012i003p00423 — [V] citation; equation [U]
[4] Houlsby, A.C. (1976). Routine interpretation of the Lugeon water-test. Q. J. Eng. Geol. 9(4), 303–313. https://doi.org/10.1144/GSL.QJEG.1976.009.04.03 — [V] abstract (five runs, pattern interpretation, 811 tests)
[5] Cooper, H.H. & Jacob, C.E. (1946). A generalized graphical method for evaluating formation constants and summarizing well-field history. Trans. AGU 27(4), 526–534. https://doi.org/10.1029/TR027i004p00526 — [V] via an extract of the source
[6] Freeze, R.A. & Cherry, J.A. (1979). Groundwater. Prentice-Hall (free online edition, The Groundwater Project). https://fc79.gw-project.org/ — [V] §8.5 eq. 8.34 and Table 2.3; Table 2.2 values [U] (image)
[7] Chapuis, R.P. (2004). Predicting the saturated hydraulic conductivity of sand and gravel using effective diameter and void ratio. Can. Geotech. J. 41(5), 787–795. https://doi.org/10.1139/t04-022 — [V] abstract (ranges, error statistics)
[8] Hazen, A. (1892). Some physical properties of sands and gravels… 24th Annual Report, Massachusetts State Board of Health, 539–556. — [V] form and C range via MnDOT NRRA (2020) permeability literature review table, https://www.dot.state.mn.us/mnroad/nrra/structure-teams/geotechnical/files/permeability-base-task-2-lit-review-final-2020-08-24.pdf
[9] Tunbridge, L. (2017). Hydraulic conductivity determination by Lugeon test – testing in practice. NGI workshop slides, Oslo. https://www.nve.no/Media/5313/lloydt-lugeon-test.pdf — [V] Lu formula, five-stage procedure; cites Quiñones-Rozo (2010) table (image, not read)
[10] Helsel, D.R. (2012). Statistics for Censored Environmental Data Using Minitab and R, 2nd ed. Wiley. — [U]
[11] Smith, L. (2021). Hydrogeology and Mineral Resource Development, §5.2. The Groundwater Project. https://books.gw-project.org/hydrogeology-and-mineral-resource-development/?p=75 — [V] eq. 2 (Goodman et al. 1965: Bull. AEG 2, 35–56)
[12] Heuer, R.E. (1995). Estimating rock tunnel water inflow. Proc. Rapid Excavation and Tunneling Conference (RETC) 1995, SME. https://onemine.org/documents/estimating-rock-tunnel-water-inflow — [U] (abstract only; reduction factor not seen)
[13] Duncan, J.M. (2000). Factors of safety and reliability in geotechnical engineering. J. Geotech. Geoenviron. Eng. 126(4), 307–316. https://doi.org/10.1061/(ASCE)1090-0241(2000)126:4(307) — [U] Table 1 values not seen
