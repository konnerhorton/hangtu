# 13 — Intact rock strength

| | |
|---|---|
| **Parameters** | σci (uniaxial compressive strength, UCS), σt (tensile strength; BTS = Brazilian), Is50 (size-corrected point load index), Ia(50) (point load anisotropy index) |
| **Material** | Rock |
| **Constitutive models that use it** | HB (σci), MC equivalent via HB, tension cut-off (σt), TBM performance models |
| **Depends on** | — (direct test); moisture state and loading direction must be known |
| **Feeds** | [15-hoek-brown-mi](15-hoek-brown-mi.md), [14-intact-rock-deformability](14-intact-rock-deformability.md) (MR = Ei/σci), [17-rock-mass-strength](17-rock-mass-strength.md), [18-rock-mass-modulus](18-rock-mass-modulus.md), [16-gsi-and-disturbance](16-gsi-and-disturbance.md) |

## 1. Phenomenon
σci is the peak axial stress of an intact, defect-free core loaded without confinement; σt is the stress at which
intact rock fails in tension, usually inferred indirectly from the Brazilian (diametral splitting) test. Both depend
on mineralogy, grain size, cementation and porosity, and drop with specimen size (more flaws sampled), with
moisture content (strongly in clay-bearing rocks such as shale, which also deteriorate when core dries and rewets)
and with loading direction relative to bedding or foliation (anisotropy). The point load index Is50 is a quick
tensile-splitting index used to classify strength and to interpolate UCS between laboratory tests; it is not a
strength itself. The HB criterion applies to shear failure of intact rock only, so UCS specimens that fail by axial
splitting or along a pre-existing defect do not give a valid σci [1, p. 6].

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| σci, σt, Is50 | MPa | psi, ksi | 1 MPa = 145.04 psi = 0.14504 ksi; 1 ksi = 6.8948 MPa |
| Point load P | kN | lbf | 1 kN = 224.81 lbf |
| Ia(50), σci/σt, K | – | – | dimensionless |

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| Field strength grades R0–R6 | R0 0.25–1, R1 1–5, R2 5–25, R3 25–50, R4 50–100, R5 100–250, R6 > 250 MPa; Is50 R3 1–2, R4 2–4, R5 4–10, R6 > 10 MPa | [2] Table 2 p. 6 (after Brown 1981) [V] |
| Shale, R3–R4 examples | 25–100 MPa (fresh); much lower when weathered or wet | [2] Table 2 p. 6 [V] |
| Coal-measure rocks, US (median of unit medians) | shale 4,367–10,752 psi (30–74 MPa); siltstone 41–92 MPa; sandstone 47–101 MPa; limestone (Midwest) 129 MPa | [3] Table 2 [V] |
| σci/σt ratio (all rocks) | 2.7–39, mean 14.7 (Sheorey 1997 compilation); "most rocks" 10–50 (Vutukuri et al. 1974) | [4] p. 1 [V] |
| σci/σt by texture (brittle rocks) | coarse 20–27, medium 16–20, fine (siltstone, limestone) 11–16 | [4] eq. 6 and text [V] |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Uniaxial compressive strength | D7012-23 Method C (Method D adds moduli) | ISRM SM 1979 [5]; EN 1926:2006 (natural stone) | RUCS: RUCS_UCS, RUCS_SDIA, RUCS_LEN, RUCS_MC, RUCS_COND, RUCS_MODE, RUCS_STRA, RUCS_DURN, RUCS_REM, RUCS_METH | σci per specimen; failure mode |
| Brazilian (splitting) tensile | D3967-23 (now flat loading platens) | ISRM SM 1978 [6] | RTEN: RTEN_TENS, RTEN_SDIA, RTEN_LEN, RTEN_MC, RTEN_COND, RTEN_MODE, RTEN_STRA, RTEN_METH | BTS = 2P/(πDt) |
| Point load | D5731-16 (**withdrawn 2025, no replacement**) | ISRM SM 1985 [7] | RPLT: RPLT_PLS (Is), RPLT_PLSI (Is50), RPLT_PLTF (A/B/D/I + L/P to weakness planes), RPLT_MC, RPLT_METH | Is, Is50, Ia(50) |

Notes: RUCS_MODE codes include AXIAL, SHEAR, DIAGONAL SHEARING, ALONG FOLIATION, MULTIPLE FRACTURING. D7012-23
is active [8]; D3967-23 is active [9]; D5731-16 withdrawn 17 Jun 2025 [10] (ISRM 1985 remains the method
reference). AGS has no heading for loading angle to bedding in RUCS/RTEN; look in SPEC_DESC / *_REM.

## 5. Derivations and correlations

### 5.1 Point load index and equivalent diameter — ISRM (1985), ASTM D5731
$$I_s = P/D_e^2,\quad D_e^2 = D^2\ \text{(diametral)},\quad D_e^2 = 4A/\pi,\ A = WD\ \text{(axial, block, lump)}$$
- **Inputs:** P failure load (N), D platen separation, W width (mm) → MPa
- **Valid for:** fracture through both loading points; D5731 scope says rock with UCS > 15 MPa
- **Source:** [11] §9.1 eq. 1 [V]; [7] [U]

### 5.2 Size correction to 50 mm — ISRM (1985)
$$I_{s(50)} = F\,I_s,\qquad F = (D_e/50)^{0.45}\ \ (\approx \sqrt{D_e/50}\ \text{near } 50\ \text{mm})$$
- **Inputs:** De (mm). F = 1.035 for 54 mm (NX), 0.884 for 38 mm, 1.110 for 63 mm (computed)
- **Valid for:** when tests at a range of De are not available (preferred: log P vs log De² plot)
- **Mean:** delete 2 highest and 2 lowest of ≥ 10 valid tests, average the rest
- **Source:** [11] §9.2 eqs. 4–5, §9.3.2 [V]; [7] [U]

### 5.3 UCS size effect — Hoek & Brown (1980)
$$\sigma_{cd} = \sigma_{c50}\,(50/d)^{0.18}$$
- **Inputs:** d core diameter (mm). σcd/σc50 = 1.05 (38 mm), 0.88 (100 mm), 0.82 (150 mm) (computed)
- **Valid for:** hard rocks in the data set (marble, limestone, granite, basalt, norite …), d ≈ 10–200 mm
- **Source:** [2] eq. 10, Fig. 4, p. 9 [V]

### 5.4 UCS from point load — Broch & Franklin (1972); Bieniawski (1975); ASTM D5731
$$\sigma_{ci} \approx K\,I_{s(50)}$$
- **Inputs:** Is50 (MPa); K dimensionless
- **Values:** K ≈ 24 for hard rock (Broch & Franklin 23.7; Bieniawski 23.9, sandstone) [3] Table 1 [V];
  D5731 generalized C by core size: 20 mm 17.5, 30 mm 19, 40 mm 21, 50 mm 23, 54 mm 24, 60 mm 24.5 [11] Table 1, eq. 6 [V];
  coal-measure rocks (axial tests, 908 units): K 19.6–22.4 by lithology, 21 overall, median Ki falls to 16.9 for UCS < 20 MPa [3] Table 4 [V];
  published sedimentary K 8–30, shale/mudstone 12.6 (lump tests) [3] Table 1 [V]. Kahraman (2001): strong linear
  Is50–UCS relation but coefficients rock-type and test-condition dependent [12] (abstract) [V].
- **Valid for:** axial or diametral tests on hard rock; diametral tests in bedded rock give much lower Is50 and should
  not be converted with the same K [3] Discussion [V]. Point load below UCS ≈ 25 MPa is "highly ambiguous" [2] Table 2 note [V].
- **Scatter:** factor ~ ±30–50 % on individual specimens; site-specific K required for design _[Judgment — for PE review]_.

### 5.5 Brazilian tensile strength — ISRM (1978), ASTM D3967
$$\sigma_t = \frac{2P}{\pi D t} = 0.636\,\frac{P}{D t}$$
- **Inputs:** P failure load (N), D diameter, t thickness (mm)
- **Valid for:** central diametral fracture starting at the disc center; t/D ≈ 0.5 (D3967: 0.2–0.75)
- **Source:** [1] eq. 9, p. 13 [V]; [6] [U]. Direct/Brazilian ratio DTS/BTS ≈ 0.86 (metamorphic), 0.82 (sedimentary),
  0.70 (igneous), wide scatter (Perras & Diederichs 2014) [1] p. 13 [V]; DTS ≈ 0.9 BTS [13] (abstract) [V].

### 5.6 Tensile strength check from mi — Hoek–Brown (1980); Cai (2010); Hoek (2023)
$$\sigma_{t,HB} = \tfrac{1}{2}\sigma_{ci}\left(m_i - \sqrt{m_i^2+4}\right)\approx -\sigma_{ci}/m_i;\quad \text{Cai: } m_i \approx R = \sigma_{ci}/|\sigma_t|\ (R \ge 8);\quad \text{Hoek 2023: } \sigma_t = -\sigma_{ci}/(3.25\,m_i^{0.67})$$
- **Inputs:** σci (MPa), mi from [15](15-hoek-brown-mi.md)
- **Valid for:** check only. Hoek (2023) states the HB intercept overestimates |σt|; his empirical eq. 8 is from 13
  rock types (mi = 10 → σci/|σt| = 15.2 vs HB intercept 10.1, computed). The text of eq. 8 prints 0.325; the
  Fig. 12 label (3.25) is the one consistent with the plotted curves.
- **Source:** [1] eqs. 7–8, Fig. 12, p. 12 [V]; [4] eq. 1, p. 2 [V] (conference version of [14] [U]);
  HB2002 intact/rock-mass σt = −sσci/mb [15] eq. 7 [V]

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Tunnel FE / convergence-confinement (HB) | σci scales mb, s, σcm and the whole envelope | High: σcm ∝ σci; plastic zone and convergence strongly nonlinear in σcm/p0 |
| Equivalent MC (c′, φ′) | c′ ∝ σci at fixed GSI, mi, σ3max/σci | High on c′, low–moderate on φ′ |
| Tension cut-off / spalling | σt sets tensile yield; σci/|σt| controls spalling depth | Moderate–high near the face and crown |
| TBM penetration, cutter forces (e.g. CSM model uses σc and σt) | Normal force per cutter rises with σc, σt | High: penetration rate falls roughly in proportion to strength _[Judgment — for PE review]_ |
| Cutter/tool wear, excavatability | UCS with abrasivity (CAI) | Moderate |
| Block / wedge stability | Not used (joint strength governs, see [22](22-discontinuity-shear-strength.md)) | Low |

**Typical variability:** within a rock unit, UCS COV ≈ 35 % (shale, limestone) and ≈ 19 % (siltstone,
sandstone) (median SD/mean); Is50 COV 20 % (sandstone) to 35 % (shale) [3] text to Fig. 4 [V]. Hoek's example
input uses σci COV 25 % [2] Fig. 12, p. 29 [V]. Transformation error of UCS from Is50 is additional to the inherent
COV (K varies 8–30 between studies [3]). Aladejare & Wang (2017) compile rock-property COVs by rock type [16] [U].

## 7. Pitfalls and QA checks
- Check RUCS_MODE: exclude axial splitting, failure along a defect, crumbling from σci used for HB fitting [1, p. 6].
- Report moisture state (RUCS_MC, RUCS_COND); dried shale core can read much stronger or slake [1, App. 2 p. 24; 2, p. 4].
- Specimen L/D 2.5–3 (ISRM), ≥ 2 minimum; flag RUCS_REM notes on non-standard geometry [1, p. 25].
- Anisotropic rock: record angle to bedding; UCS of a phyllite varied by a factor ≈ 5 with loading direction [2, p. 8].
- Point load: use RPLT_PLSI as reported, check RPLT_PLTF (axial vs diametral, L vs P to bedding); compute Ia(50).
- Do not convert diametral Is50 in bedded sedimentary rock to UCS with a hard-rock K [3].
- BTS: reject tests where fracture did not run along the loaded diameter (RTEN_MODE); BTS is not true σt.
- Check σci/BTS ratio against 5–30; ratios < 5 suggest invalid BTS (weak or weathered rock) _[Judgment — for PE review]_.
- Size: 38 mm vs 63 mm cores differ by ~5–10 % in UCS from the size effect alone (5.3).

## References
[1] Hoek, E. (2023). Practical Rock Engineering, ch. 3 "Intact rock strength". Rocscience. https://static.rocscience.cloud/assets/resources/learning/hoek/3.-Intact-rock-strength_2023-06-30-120556_xiuv.pdf — [V] eqs. 7–9, Fig. 12, pp. 6, 12–13, 24–25
[2] Hoek, E. (2007). Practical Rock Engineering, ch. 11 "Rock mass properties". Rocscience. https://www.rocscience.com/assets/resources/learning/hoek/Practical-Rock-Engineering-Chapter-11-Rock-Mass-Properties.pdf — [V] Table 2 p. 6, eq. 10 p. 9, p. 4, p. 8, Fig. 12 p. 29
[3] Rusnak, J. & Mark, C. (2000). Using the point load test to determine the uniaxial compressive strength of coal measure rock. Proc. 19th Int. Conf. Ground Control in Mining, Morgantown WV, 362–371. https://stacks.cdc.gov/view/cdc/9302 — [V] Tables 1, 2, 4, text
[4] Cai, M. (2009). A simple method to estimate tensile strength and Hoek-Brown strength parameter mi of brittle rocks. ROCKENG09, Toronto, paper 4063. https://geogroup.utoronto.ca/wp-content/uploads/RockEng09/PDF/Session21/4063%20PAPER.pdf — [V] eqs. 1, 6, pp. 1–2
[5] ISRM (1979). Suggested methods for determining the uniaxial compressive strength and deformability of rock materials. IJRMMS 16(2), 135–140. https://doi.org/10.1016/0148-9062(79)91451-7 — [U] (bibliographic details [V] via TRID)
[6] ISRM (1978). Suggested methods for determining tensile strength of rock materials. IJRMMS 15(3), 99–103. https://doi.org/10.1016/0148-9062(78)90003-7 — [U]
[7] ISRM (1985). Suggested method for determining point load strength. IJRMMS 22(2), 51–60. https://doi.org/10.1016/0148-9062(85)92327-7 — [U] (equations [V] via [11])
[8] ASTM D7012-23. Standard test methods for compressive strength and elastic moduli of intact rock core specimens under varying states of stress and temperatures. https://store.astm.org/d7012-23.html — [V] status, Methods A–D
[9] ASTM D3967-23. Standard test method for splitting tensile strength of intact rock core specimens with flat loading platens. https://store.astm.org/d3967-23.html — [V] status, title
[10] ASTM D5731-16 (withdrawn 2025). Determination of the point load strength index of rock and application to rock strength classifications. https://store.astm.org/d5731-16.html — [V] withdrawn, no replacement
[11] ASTM D5731-95. Standard test method for determination of the point load strength index of rock. — [V] eqs. 1, 4–6, §9.3.2, Table 1 (read from a hosted copy)
[12] Kahraman, S. (2001). Evaluation of simple methods for assessing the uniaxial compressive strength of rock. IJRMMS 38(7), 981–994. https://doi.org/10.1016/S1365-1609(01)00039-9 — [V] abstract only
[13] Read, S.A.L. (2015). Guidelines for use of tensile data in the calculation of the Hoek-Brown constant mi. CIM. https://onemine.org/documents/guidelines-for-use-of-tensile-data-in-the-calculation-of-the-hoekbrown-constant-mi — [V] abstract only
[14] Cai, M. (2010). Practical estimates of tensile strength and Hoek–Brown strength parameter mi of brittle rocks. Rock Mech. Rock Eng. 43(2), 167–184. https://doi.org/10.1007/s00603-009-0053-1 — [U]
[15] Hoek, E., Carranza-Torres, C. & Corkum, B. (2002). Hoek-Brown failure criterion – 2002 edition. Proc. NARMS-TAC, Toronto, 267–273. https://www.eoas.ubc.ca/courses/eosc433/lecture-material/2002-HoekBrownCriterion.pdf — [V] eqs. 6–7
[16] Aladejare, A.E. & Wang, Y. (2017). Evaluation of rock property variability. Georisk 11(1), 22–41. https://doi.org/10.1080/17499518.2016.1207784 — [U]
