# 06 — Preconsolidation and compressibility

| | |
|---|---|
| **Parameters** | σ′p (preconsolidation / yield stress), OCR = σ′p/σ′v0, Cc (compression index), Cs / Cr (swelling / recompression index) |
| **Material** | Soil (mainly fine-grained) |
| **Constitutive models that use it** | Soft Soil / Modified Cam Clay (λ* = Cc/(2.3(1+e)), κ*), HS (OCR or POP sets the initial cap), SHANSEP su |
| **Depends on** | [01 Unit weight and vertical stress](01-unit-weight-and-vertical-stress.md) (σ′v0), [02 Index properties](02-index-properties.md) (LL, PI), [03 Specific gravity and void ratio](03-specific-gravity-and-void-ratio.md) (e0) |
| **Feeds** | [05 Undrained shear strength](05-undrained-shear-strength.md) (SHANSEP), [07 At-rest earth pressure](07-at-rest-earth-pressure.md) (K0 from OCR), [11 Hardening Soil stiffness](11-hardening-soil-stiffness.md) (Eoed, POP) |

## 1. Phenomenon
In one-dimensional compression a soil is stiff (recompression, slope Cr; unloading slope Cs) up to the largest
effective stress it has carried or the yield stress created by aging and cementation (σ′p), then compresses
along the much steeper virgin line (slope Cc) in e–log σ′v. OCR = σ′p/σ′v0 summarises stress history and controls
K0, su and stiffness. σ′p is a yield point, not a sharp break: its value depends on the interpretation method,
loading rate (higher in CRS), temperature and above all sample disturbance, which rounds the curve, lowers σ′p and
raises Cr. Cc depends on mineralogy, water content and structure (sensitive clays show Cc decreasing after yield).

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| σ′p, σ′v0 | kPa | psf, tsf | 1 kPa = 20.8854 psf = 0.01044 tsf; 1 tsf = 95.761 kPa |
| OCR | – | – | dimensionless |
| Cc, Cs, Cr | – (per log10 cycle of stress) | same | unit-independent; CR = Cc/(1+e0) |

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| Cc, compressibility slight (low) / moderate / high | < 0.2 / 0.2–0.4 / > 0.4 | [1] Table 6-1, p. 6-4 [V] |
| Cc from LL (NC clay) LL 30 / 50 / 80 % | ≈ 0.18 / 0.36 / 0.63 (computed from 5.7) | [1] Eq. 6-5 [V] |
| Cs/Cc (via Λ = 1 − Cs/Cc ≈ 0.8 ± 0.1) | ≈ 0.1–0.3 | [2] p. 2789 [V] |
| OCR, NC / lightly OC / heavily OC clay | 1 / ≈ 1–4 / > 4 | _[Judgment — for review]_ |
| σ′p/(qt − σv0) (k) | 0.2–0.5, average 0.33 | [3] p. 44 [V] |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Incremental-load oedometer | D2435/D2435M | ISO 17892-5; BS 1377-5 | CONG: CONG_TYPE, CONG_COND, CONG_IVR, CONG_HIGT, CONG_MCI; CONS: CONS_INCN, CONS_INCF, CONS_IVR, CONS_INCE, CONS_INMV | e vs σ′v points → σ′p, Cc, Cs |
| Constant rate of strain (CRS) / effective-stress consolidation (Rowe cell) | D4186/D4186M | BS 1377-6 | ESCG: ESCG_PCP, ESCG_YSR, ESCG_CC, ESCG_CS, ESCG_ISVS, ESCG_ISVR, ESCG_IVR; ESCT: ESCT_INCF, ESCT_VR0, ESCT_VRE | continuous curve; lab-reported σ′p, Cc, Cs |
| CPTu (correlation) | D5778 | ISO 22476-1 | CPTT: CPTT_QT, CPTT_CPO; CPTP: CPTP_P01, CPTP_CC1 | σ′p from qnet |
| DMT (correlation) | D6635 | ISO 22476-11 | DMTP: DMTP_MPS | σ′p estimate |
| SPT (correlation) | D1586/D1586M | ISO 22476-3 | ISPT: ISPT_NVAL, ISPT_N60 | OCR / σ′p estimate |

ASTM designations without year — confirm the current edition before citing.

## 5. Derivations and correlations

### 5.1 Bilinear e–log σ′v fit
$$e = \begin{cases} e_1 - C_r\log\sigma'_v & \sigma'_v<\sigma'_p\\ e_2 - C_c\log\sigma'_v & \sigma'_v\ge\sigma'_p\end{cases},\qquad \log\sigma'_p = \frac{e_2-e_1}{C_c-C_r}$$
- **Inputs:** CONS_INCF (σ′v, kPa), CONS_INCE (e at end of increment); loading branch only. Breakpoint searched
  by least squares (two lines). Cs = slope of the unload branch. OCR = σ′p/σ′v0 at specimen depth.
- **Valid for:** curves with ≥ 2–3 points on each branch; deterministic and reproducible (unlike 5.2).
- **Source:** standard construction (e.g. [1] Section 6) [U].

### 5.2 Casagrande (1936) graphical construction
- Point of maximum curvature → horizontal, tangent, bisector; σ′p where bisector meets the virgin line.
- Operator-dependent; listed for comparison only. **Source:** [4] [U].

### 5.3 Pacheco Silva (1970)
- Horizontal through e0 meets virgin line; vertical down to curve, horizontal back to virgin line → σ′p. More
  reproducible than Casagrande; used as a check. **Source:** [5] [U].

### 5.4 Work (strain-energy) method — Becker et al. (1987)
$$W = \sum \sigma'_v\,\Delta\varepsilon_v\ \text{(per unit volume)};\ \ \sigma'_p = \text{intersection of the two straight lines in } W\text{–}\sigma'_v\ (\text{arithmetic})$$
- Avoids log-scale judgement; sensitive to the stress range chosen for each line.
- **Source:** [6] (method per abstract) [V bibliographic; equation form U].

### 5.5 SPT — Mayne & Kemper (1988), in Kulhawy & Mayne (1990)
$$OCR = 0.58\,\frac{N\,p_a}{\sigma'_{v0}}\quad\Leftrightarrow\quad \sigma'_p\approx 0.58\,N\,p_a$$
- **Inputs:** N (blows/0.3 m), pa ≈ 100 kPa. **Valid for:** clays (n = 110). **Scatter:** r² = 0.766, S.D. = 3.82.
- **Source:** [1] Fig. 3-18, p. 3-18 [V]. Later generalized form σ′p = 0.47 (N60)^m pa with m depending on soil
  type (Mayne) [U — exponents not verified].

### 5.6 CPTu
$$\sigma'_p \approx 0.33\,(q_t-\sigma_{v0})\quad(k=0.2\text{–}0.5)$$
- **Source:** [2] Eq. 4.15, p. 2832 [V]; [3] p. 44 [V]. Intact clays; underestimates in fissured clays.

### 5.7 Cc from index properties
$$C_c = 0.009\,(LL-10)\ \ (\text{NC clays, Terzaghi \& Peck 1967}),\qquad C_c\approx 0.5\,G_s\,\frac{PI}{100}\approx \frac{PI}{74}\ (G_s=2.7)$$
- Skempton (1944), remolded: Cc = 0.007 (LL − 10) [U]; T&P ≈ 1.3 × Skempton.
- **Source:** [1] Eqs. 6-5 to 6-7, p. 6-4 [V]. Scatter ±30 % or more (figure 6-3 band) [U].

### 5.8 Sample quality — Lunne et al. (1997)
$$\Delta e/e_0 = (e_0 - e_{\sigma'_{v0}})/e_0$$

| OCR | Very good–excellent | Good–fair | Poor | Very poor |
|---|---|---|---|---|
| 1–2 | < 0.04 | 0.04–0.07 | 0.07–0.14 | > 0.14 |
| 2–4 | < 0.03 | 0.03–0.05 | 0.05–0.10 | > 0.10 |

- **Source:** [7]; outer bands [V] via Amundsen et al. (2016) Table 1 [8]; intermediate bands [U]. Alternative
  SQD by εv0 at σ′v0 (< 1 % very good; > 8 % very poor; Terzaghi et al. 1996) [V] via [8].

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Long-term consolidation settlement above tunnels (drainage into lining, drawdown) | Δe = Cr log(σ′p/σ′v0) + Cc log(σ′vf/σ′p) | **High** — whether σ′vf exceeds σ′p changes settlement by ~an order of magnitude |
| Tunnel FE (Soft Soil, HS) | λ*, κ*; OCR/POP sets cap, so initial stiffness and yield | High for clay-hosted tunnels |
| K0 and initial stresses | K0 = (1 − sin φ′) OCR^sin φ′ (07) | Moderate–high (lining loads, face pressure) |
| su (SHANSEP) | su ∝ OCR^m | High (face stability, undrained FE) |
| Groundwater inflow | via k(e) only | Low |

**Typical variability:** Cc COV ≈ 10–37 %, σ′p COV ≈ 10–35 % (Duncan 2000 [9]) [U]. Correlations (5.5–5.7) add
large transformation uncertainty (5.5: S.D. of OCR = 3.82 for n = 110). Method choice alone (5.1–5.4) commonly
moves σ′p by 10–20 % _[Judgment — for review]_.

## 7. Pitfalls and QA checks
- Grade every specimen by Δe/e0 (5.8) before using σ′p; poor samples bias σ′p low and Cr high.
- Use the loading branch for σ′p and Cc; Cs from a clear unload–reload loop; do not use reload slope as Cc.
- Check σ′v0 at specimen depth (water table, unit weight) — OCR errors often come from σ′v0, not σ′p.
- OCR < 1 means disturbance, wrong σ′v0 or underconsolidation — flag, don't clip.
- CRS σ′p is rate-dependent (higher than IL); do not mix without comment.
- Lab-printed σ′p / OCR (ESCG_PCP, ESCG_YSR) — recompute from CONS data and compare.
- Too few points beyond σ′p (max stress < 2–3 σ′p) → Cc and σ′p unreliable.
- Cc in e–log σ′v vs CR in ε–log σ′v: check which the lab reports.

## References
[1] Kulhawy, F.H. & Mayne, P.W. (1990). Manual on Estimating Soil Properties for Foundation Design. EPRI EL-6800.
https://restservice.epri.com/publicdownload/EL-6800/0/Product — [V] Fig. 3-18 (p. 3-18), Eqs. 6-5–6-7 (p. 6-4).
[2] Mayne, P.W., Coop, M.R., Springman, S.M., Huang, A.-B. & Zornberg, J.G. (2009). Geomaterial behavior and
testing. Proc. 17th ICSMGE, Alexandria, 2777–2872. https://doi.org/10.3233/978-1-60750-031-5-2777 — [V] Eq. 1.3
discussion (p. 2789), Eq. 4.15 (p. 2832).
[3] Robertson, P.K. & Cabal, K. (2022). Guide to Cone Penetration Testing, 7th ed. Gregg Drilling. — [V] p. 44.
[4] Casagrande, A. (1936). The determination of the pre-consolidation load and its practical significance. Proc.
1st ICSMFE, Cambridge MA, Vol. 3, 60–64. — [U]
[5] Pacheco Silva, F. (1970). Uma nova construção gráfica para a determinação da pressão de pré-adensamento de
uma amostra de solo. Proc. 4th Brazilian Conf. Soil Mech. Found. Eng., Rio de Janeiro, Vol. 2. — [U]
[6] Becker, D.E., Crooks, J.H.A., Been, K. & Jefferies, M.G. (1987). Work as a criterion for determining in situ
and yield stresses in clays. Can. Geotech. J. 24(4), 549–564. https://doi.org/10.1139/t87-070 — [V] bibliographic
and method summary (TRID abstract); DOI [U].
[7] Lunne, T., Berre, T. & Strandvik, S. (1997). Sample disturbance effects in soft low plastic Norwegian clay.
Proc. Symp. Recent Developments in Soil and Pavement Mechanics, Rio de Janeiro, 81–102. — [V] via [8].
[8] Amundsen, H.A., Thakur, V. & Emdal, A. (2016). Sample disturbances in block samples on low plastic soft clays.
Proc. 17th Nordic Geotech. Meeting (NGM 2016), Reykjavik, 159–166.
https://www.issmge.org/publications/online-library — [V] Table 1 (p. 160–161); page range [U].
[9] Duncan, J.M. (2000). Factors of safety and reliability in geotechnical engineering. J. Geotech. Geoenviron.
Eng. 126(4), 307–316. https://doi.org/10.1061/(ASCE)1090-0241(2000)126:4(307) — [U]
[10] Terzaghi, K. & Peck, R.B. (1967). Soil Mechanics in Engineering Practice, 2nd ed. Wiley. — [V] via [1] Eq. 6-5.
