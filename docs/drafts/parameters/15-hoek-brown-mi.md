# 15 — Hoek-Brown constant mi

| | |
|---|---|
| **Parameters** | mi (Hoek-Brown intact rock material constant), with σci fitted or fixed |
| **Material** | Rock |
| **Constitutive models that use it** | HB (intact and generalized), MC equivalent via HB, strain-softening HB (with residual mr) |
| **Depends on** | [13-intact-rock-strength](13-intact-rock-strength.md) (σci, σt) |
| **Feeds** | [17-rock-mass-strength](17-rock-mass-strength.md) (mb), [19-post-peak-rock-mass](19-post-peak-rock-mass.md) (mr), [09-dilatancy](09-dilatancy.md) (via φ′) |

## 1. Phenomenon
mi sets the curvature of the intact-rock Hoek-Brown envelope, i.e. how fast strength rises with confinement; it is
roughly the ratio of compressive to tensile strength, so high-mi rocks (coarse crystalline, e.g. granite ≈ 32) are
brittle and frictional and low-mi rocks (fine clastics, e.g. claystone ≈ 4, shale ≈ 6) are weaker in confinement.
It depends on mineralogy, grain size and texture, and on direction: tabulated values are for loading normal to
bedding/foliation and change if failure runs along a weakness plane [1, Table 3 note, p. 7]. mi is only meaningful
for brittle shear failure, between σ3 = 0 and the brittle–ductile transition (σ1/σ3 ≈ 3–5) [2, p. 6]; fitted
values therefore depend on the σ3 range tested.

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| mi | – | – | dimensionless (unit-independent if σ1, σ3, σci share a unit) |
| σ1, σ3, σci in the fit | MPa | psi, ksi | 1 MPa = 145.04 psi = 0.14504 ksi |

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| Claystone / shale / siltstone / marl | 4 ± 2 / (6 ± 2) / 7 ± 2 / (7 ± 2) | [1] Table 3, p. 7 (Hoek 2007; values in brackets are estimates) [V] |
| Sandstone / greywacke / conglomerate | 17 ± 4 / (18 ± 3) / (21 ± 3) in [1], (22 ± 3) in [3] | [1] Table 3 [V]; [3] Table 1 [V] |
| Limestone by texture | crystalline (12 ± 3), sparitic (10 ± 2), micritic (9 ± 2); dolomite (9 ± 3); chalk 7 ± 2 | [1] Table 3 [V]; [3] Table 1 [V] |
| Evaporites | gypsum 8 ± 2, anhydrite 12 ± 2 | [3] Table 1 [V] |
| Granite (for scale) | 32 ± 3 | [1] Table 3 [V] |

Tables originate with Hoek & Brown (1997) and Marinos & Hoek (2000, 2001) [4, 5] [U for the originals]. A check
band of "limestone 8–12" spans micritic to crystalline means; the ± ranges reach 7–15.

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Triaxial compression, intact core (no pore pressure) | D7012-23 Method A (Method B with moduli) | ISRM SM 1983 revised (Kovari et al.) [6] | **No rock-triaxial group in the AGS 4.2 standard dictionary** (checked). Some files use TRIG/TRIT (TRIT_CELL, TRIT_DEVF in kPa; TRIT_MODE) or a user-defined group (e.g. "RTRI", non-standard headings) | (σ3, σ1) pairs |
| UCS (σ3 = 0 point) | D7012-23 Method C | ISRM SM 1979 | RUCS: RUCS_UCS, RUCS_MODE | σci |
| Brazilian / direct tension (σ3 < 0 point, check) | D3967-23 | ISRM SM 1978 | RTEN: RTEN_TENS, RTEN_MODE | σt |

Program: ≥ 3, preferably ≥ 5 triaxial tests plus UCS tests, ideally several per σ3 level [2, p. 6]; at least five
well-spaced points over 0 < σ3 < 0.5 σci [1, p. 2].

## 5. Derivations and correlations

### 5.1 Intact Hoek-Brown criterion — Hoek & Brown (1980)
$$\sigma_1 = \sigma_3 + \sigma_{ci}\left(m_i\,\frac{\sigma_3}{\sigma_{ci}} + 1\right)^{0.5}$$
- **Source:** [1] eq. 5, p. 2 [V]; [2] eq. 1, p. 3 [V]; [7] [U]

### 5.2 Linear regression for σci and mi — Hoek & Brown (1980); Hoek (2007)
$$y = m_i\sigma_{ci}\,x + \sigma_{ci}^2,\quad x=\sigma_3,\ y=(\sigma_1-\sigma_3)^2$$
$$\sigma_{ci}^2 = \frac{\sum y}{n} - \frac{\sum xy - \sum x\sum y/n}{\sum x^2 - (\sum x)^2/n}\cdot\frac{\sum x}{n},\qquad m_i = \frac{1}{\sigma_{ci}}\cdot\frac{\sum xy - \sum x\sum y/n}{\sum x^2 - (\sum x)^2/n}$$
- **Inputs:** n pairs (σ3, σ1), MPa; UCS tests enter as σ3 = 0
- **Valid for:** 0 < σ3 < 0.5 σci; ≥ 5 points; shear failures only (remove splitting / defect failures) [2, p. 6]
- **Scatter:** good data give r² > 0.9 [1] eq. 9, p. 4 [V]
- **Source:** [1] eqs. 6–9, p. 4 [V]; RocLab/RocData "Hoek" regression [U]

### 5.3 Fit with σci fixed (e.g. to the UCS median)
$$m_i = \frac{\sum x\,(y-\sigma_{ci}^2)}{\sigma_{ci}\sum x^2}$$
- **Use:** when triaxial data are few or the free fit returns σci far from the UCS data; least squares on mi only
  (derived from 5.2). Report both the free and fixed fits.

### 5.4 Per-specimen back-calculation (spread of mi)
$$m_i = \frac{(\sigma_1-\sigma_3)^2 - \sigma_{ci}^2}{\sigma_{ci}\,\sigma_3}\qquad (\sigma_3 > 0)$$
- **Caution:** ill-conditioned at small σ3/σci. Computed example (σci = 50 MPa, mi = 8): a +5 % error in σ1 gives
  mi = 19.2 at σ3 = 0.5 MPa, 14.1 at 1 MPa, 10.0 at 5 MPa, 9.3 at 25 MPa. Weight or exclude σ3 < ~0.1 σci
  _[Judgment — for PE review]_.

### 5.5 mi from UCS / tensile ratio — Cai (2009/2010); Read (2015); Hoek (2023)
$$m_i \approx R = \sigma_{ci}/|\sigma_t|\ \ (R \ge 8);\qquad \text{Hoek (2023): } |\sigma_t| = \sigma_{ci}/(3.25\,m_i^{0.67}) \Rightarrow m_i = (R/3.25)^{1/0.67}$$
- **Inputs:** σci, σt (MPa); preferably direct tension; DTS ≈ 0.9 BTS [8] [V abstract]
- **Values (computed, Hoek 2023):** R = 10 → mi 5.4; R = 15 → 9.8; R = 20 → 15.1. Cai's mi ≈ R gives larger mi at the
  same R; the two differ most for low-R (weak, fine-grained) rocks.
- **Valid for:** Cai: strong brittle rocks; holds for fitted, not tested, σc and σt [3] p. 6 [V]. Cai also gives
  mi = 8σc/σci,crack-init (low confinement) and mi = 12σc/σci,crack-init (high confinement) [3] eq. 9, p. 6 [V].
  Read (2015): include tensile data in the curve fit; R alone gives practical mi estimates more robust than
  guideline tables [8] [V abstract]. Hoek (2023) eq. 8 printed as 0.325 in the text; the Fig. 12 label 3.25 is the
  one consistent with the curves [2] p. 12 [V]. Read & Richards (2014) / Richards & Read correction: not located [U].
- **Source:** [3] eq. 1, p. 2 [V]; [9] [U]; [2] eq. 8, Fig. 12, p. 12 [V]; [8] [V abstract]

### 5.6 Multistage triaxial tests — caveat
- One specimen is loaded to near-peak at successive σ3 stages; damage accumulates, so later-stage σ1 tends to be
  low and mi from multistage data biased low unless stages are stopped at the onset of dilatancy (volumetric strain
  reversal) [6, 10] [U]. Fit with and without multistage points; flag the difference _[Judgment — for PE review]_.

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Rock mass HB (HB2002) | mb = mi·exp((GSI−100)/(28−14D)); mb/mi = 0.24 at GSI 60, 0.34 at GSI 70 (D = 0, computed) | High: mb ∝ mi |
| Equivalent MC (tunnel FE, limit equilibrium) | φ′ rises steeply with mi; c′ mildly | High on φ′ (and thus plastic radius, convergence) |
| Convergence-confinement / plastic zone | Envelope curvature at low σ3 around the opening | Moderate–high |
| Rock mass tensile strength | σt,mass = −sσci/mb ∝ 1/mi [11] eq. 7 [V] | Moderate |
| Strain-softening (residual mr) | mr scaled from mi | Moderate |
| TBM penetration, block stability | Not used directly | Low |

**Typical variability:** Hoek's probabilistic example uses mi mean 8, SD 1 (COV 12.5 %) [1] Fig. 12, p. 29 [V].
Table 3 ± half-ranges are 20–50 % of the tabulated value (sparitic limestone 20 %, sandstone 24 %, shale 33 %,
claystone 50 %; computed) — a measure of the uncertainty when mi is taken from tables rather than tests.

## 7. Pitfalls and QA checks
- Restrict to 0 < σ3 < 0.5 σci; data beyond the brittle–ductile transition (σ1/σ3 < 3–5) flatten the fit.
- Remove non-shear failures (axial splitting, failure along bedding or veins) before fitting [2, p. 6].
- Fit per lithology and per loading direction; do not pool shale and limestone interbeds.
- Free-fit σci should be close to the UCS mean; if not, report the fixed-σci fit and explain.
- Compare fitted mi with Table 3 and with R = σci/|σt| (5.5); disagreement > ±50 % → investigate.
- Flag multistage stages; run the fit with and without them.
- Check r² (> 0.9 expected for good data) and n ≥ 5.

## References
[1] Hoek, E. (2007). Practical Rock Engineering, ch. 11 "Rock mass properties". Rocscience. https://www.rocscience.com/assets/resources/learning/hoek/Practical-Rock-Engineering-Chapter-11-Rock-Mass-Properties.pdf — [V] eq. 5 and σ3 range p. 2, eqs. 6–9 p. 4, Table 3 p. 7, Fig. 12 p. 29
[2] Hoek, E. (2023). Practical Rock Engineering, ch. 3 "Intact rock strength". Rocscience. https://static.rocscience.cloud/assets/resources/learning/hoek/3.-Intact-rock-strength_2023-06-30-120556_xiuv.pdf — [V] eq. 1 p. 3, p. 6, eqs. 7–8 and Fig. 12 p. 12
[3] Cai, M. (2009). A simple method to estimate tensile strength and Hoek-Brown strength parameter mi of brittle rocks. ROCKENG09, Toronto, paper 4063. https://geogroup.utoronto.ca/wp-content/uploads/RockEng09/PDF/Session21/4063%20PAPER.pdf — [V] eqs. 1, 6, 9; Table 1 (Hoek 2007 mi)
[4] Hoek, E. & Brown, E.T. (1997). Practical estimates of rock mass strength. IJRMMS 34(8), 1165–1186. https://doi.org/10.1016/S1365-1609(97)80069-X — [U]
[5] Marinos, P. & Hoek, E. (2001). Estimating the geotechnical properties of heterogeneous rock masses such as flysch. Bull. Eng. Geol. Env. 60(2), 85–92. https://doi.org/10.1007/s100640000090 — [U]; also Marinos & Hoek (2000), GSI: a geologically friendly tool for rock mass strength estimation, GeoEng2000, Melbourne, 1422–1446 — [U]
[6] ISRM (1983). Suggested methods for determining the strength of rock materials in triaxial compression: revised version. IJRMMS 20(6), 285–290. https://doi.org/10.1016/0148-9062(83)90598-3 — [U]
[7] Hoek, E. & Brown, E.T. (1980). Empirical strength criterion for rock masses. J. Geotech. Eng. Div. ASCE 106(GT9), 1013–1035. https://doi.org/10.1061/AJGEB6.0001029 — [U]
[8] Read, S.A.L. (2015). Guidelines for use of tensile data in the calculation of the Hoek-Brown constant mi. CIM. https://onemine.org/documents/guidelines-for-use-of-tensile-data-in-the-calculation-of-the-hoekbrown-constant-mi — [V] abstract only
[9] Cai, M. (2010). Practical estimates of tensile strength and Hoek–Brown strength parameter mi of brittle rocks. Rock Mech. Rock Eng. 43(2), 167–184. https://doi.org/10.1007/s00603-009-0053-1 — [U]
[10] Youn, H. & Tonon, F. (2010). Multi-stage triaxial test on brittle rock. IJRMMS 47(4), 678–684. https://doi.org/10.1016/j.ijrmms.2009.12.017 — [U]
[11] Hoek, E., Carranza-Torres, C. & Corkum, B. (2002). Hoek-Brown failure criterion – 2002 edition. Proc. NARMS-TAC, Toronto, 267–273. https://www.eoas.ubc.ca/courses/eosc433/lecture-material/2002-HoekBrownCriterion.pdf — [V] eq. 7
[12] ASTM D7012-23. https://store.astm.org/d7012-23.html — [V] status, Methods A–D
