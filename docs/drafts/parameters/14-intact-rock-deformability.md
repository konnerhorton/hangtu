# 14 — Intact rock deformability

| | |
|---|---|
| **Parameters** | Ei (intact Young's modulus: tangent at 50 % σci, average of the linear portion, secant to 50 % σci), νi (intact Poisson's ratio: tangent, average, secant), MR = Ei/σci (modulus ratio) |
| **Material** | Rock |
| **Constitutive models that use it** | Linear elastic, MC, HB (elastic part), ubiquitous joint (matrix); input to Erm (Hoek & Diederichs 2006) |
| **Depends on** | [13-intact-rock-strength](13-intact-rock-strength.md) (same RUCS specimen; σci for MR) |
| **Feeds** | [18-rock-mass-modulus](18-rock-mass-modulus.md), [17-rock-mass-strength](17-rock-mass-strength.md) (indirectly, via model stiffness), [09-dilatancy](09-dilatancy.md) |

## 1. Phenomenon
Ei and νi describe the elastic response of intact rock pieces between the closure of micro-cracks (initial concave
part of the axial stress–strain curve) and the onset of unstable crack growth (lateral strain accelerates, ν rises,
volumetric strain reverses). They are measured in the same uniaxial test as σci, so the reported value depends on
how the slope is defined (tangent at 50 % σci, average over the linear part, or secant from zero) and on the strain
measurement (platen-to-platen readings overstate strain). Ei is controlled by mineralogy, porosity and
micro-cracking, and is more sensitive than σci to sampling damage and stress relief [1, p. 25]. In bedded or
foliated rock Ei and ν are anisotropic (stiffer parallel to bedding), and in shales they fall with increasing water
content _[Judgment — for PE review]_.

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| Ei | GPa (MPa) | ksi, Msi (10⁶ psi) | 1 GPa = 145.04 ksi = 0.14504 Msi; 1 Msi = 6.8948 GPa |
| νi | – | – | dimensionless |
| MR = Ei/σci | – | – | dimensionless; take Ei and σci in the same unit |

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| MR = Ei/σci, by rock type | ≈ 150–1000+; e.g. shale 150–250, sandstone 200–350, granite 300–550, micritic limestone 800–1000; values by rock type in [1] Table 8 | [1] Table 8, p. 24 (after Deere 1968; Palmstrom & Singh 2001) [V] |
| Ei, typical by rock type | 42 rock types, Ei, σci, mi averages, sorted by Ei (chart) | [2] Fig. 18, p. 17 (after Carter & Marinos 2020) [V — chart, values not transcribed] |
| νi | about 0.1–0.4 for most rocks; strong scatter within a lithology | Gercek (2007) [3] [U] |

Example (computed): σci = 50 MPa, MR = 200 → Ei = 10 GPa (1.45 Msi).

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Uniaxial compression with axial and lateral strain | D7012-23 Method D (Method B in triaxial) | ISRM SM 1979 [4] (in Ulusay & Hudson 2007); EN 14580:2005 (natural stone, static E) | RUCS: RUCS_ETAN, RUCS_EAVG, RUCS_ESEC (GPa); RUCS_STAN, RUCS_SAVG, RUCS_SSEC (stress level text, e.g. "50% UCS"); RUCS_MUT, RUCS_MUAV, RUCS_MUS | Ei (three definitions), νi |
| Triaxial with strain gauges | D7012-23 Method B | ISRM SM 1983 (triaxial) [5] | no standard AGS 4.2 rock-triaxial group | E, ν at confinement |

D7012-23 is the active standard (Methods A–D) [6]. The AGS RUCS heading pairs (*_STAN etc.) record the stress level
at which each modulus was taken; read them before pooling ETAN from different labs.

## 5. Derivations and correlations

### 5.1 Modulus and Poisson's ratio definitions — ISRM (1979); ASTM D7012 Method D
$$E_t = \left.\frac{d\sigma_a}{d\varepsilon_a}\right|_{0.5\sigma_{ci}},\quad E_{av} = \text{slope of linear part},\quad E_s = \frac{0.5\,\sigma_{ci}}{\varepsilon_a(0.5\,\sigma_{ci})},\qquad \nu = -\frac{\text{slope}_{\sigma\text{–}\varepsilon_a}}{\text{slope}_{\sigma\text{–}\varepsilon_d}}$$
- **Inputs:** axial stress σa, axial strain εa, diametral (lateral) strain εd
- **Valid for:** intact specimens, L/D 2.5–3; strain gauges or LVDTs on the specimen
- **Note:** Es ≤ Et in rocks with an initial crack-closure phase (concave-up start of the curve)
- **Source:** [4] [U] (definitions as widely reproduced); Hoek (2023) defines Ei as the tangent "at 50% strain to failure" [2] p. 16 [V]

### 5.2 Modulus ratio — Deere (1968); Hoek & Diederichs (2006)
$$E_i = MR \cdot \sigma_{ci}$$
- **Inputs:** σci (MPa) → Ei (MPa); MR from §3
- **Valid for:** estimate when Ei is not measured or is suspect from specimen damage; Hoek considers measured σci
  more reliable than measured Ei [1] p. 25 [V]
- **Scatter:** MR ranges in Table 8 span about ±25–40 % around the mid value; anisotropic rocks (shale, slate,
  schist, gneiss) have high MR parallel and low MR perpendicular to weakness planes [1] Table 8 notes [V]
- **Source:** [1] eq. 26, p. 23; Table 8, p. 24 [V]; [7] [U]

### 5.3 Check of measured MR
$$MR_{meas} = E_{t,50}/\sigma_{ci}\ \text{(same specimen)}$$
- **Use:** compare with Table 8 for the lithology; MR far below the range points to bedding-parallel micro-cracks,
  damage, wet clay-rich specimens or platen-based strain _[Judgment — for PE review]_.

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Rock mass modulus (HD2006 generalized) | Erm = Ei·f(GSI, D) — Erm scales linearly with Ei | High for Erm and thus for elastic displacements |
| Tunnel FE / convergence-confinement | Through Erm: elastic convergence ∝ 1/Erm; also the ground reaction curve slope | High on convergence; low on yield (strength-controlled) |
| Lining loads (stiffness ratio ground/lining) | Stiffer ground → less load shed to lining before support | Moderate |
| Ubiquitous-joint / anisotropic elastic models | Ei, νi of matrix; anisotropy ratio E∥/E⊥ | Moderate |
| ν in FE | Lateral strain ratio, K0-type elastic stress change (ν/(1−ν)) | Low–moderate |
| TBM penetration | Not a direct input (σci, σt govern) | Low |

**Typical variability:** within-unit COV of Ei is often of the order of σci's (≈ 20–40 %); Hoek's probabilistic
example treats σci with COV 25 % [1] Fig. 12, p. 29 [V]. MR from Table 8 adds a transformation uncertainty of
about ±25–40 % (range half-width/mid) _[Judgment — for PE review]_. Rock-property COV compilations: Aladejare &
Wang (2017) [8] [U].

## 7. Pitfalls and QA checks
- Do not pool RUCS_ETAN with RUCS_EAVG/ESEC; check RUCS_STAN/SAVG/SSEC for the stress level used.
- Ei from platen displacement (no strain gauges) is too low; check RUCS_REM / RUCS_METH.
- Reject Ei from specimens with non-valid failure modes only if the curve is affected below 50 % σci.
- ν > 0.5 or ν < 0 reported: check whether taken past crack damage (dilatant) or from noisy gauges.
- Record loading direction relative to bedding; report E∥ and E⊥ separately for shale.
- Moisture state (RUCS_MC, RUCS_COND) must match field conditions [1, p. 4].
- MR outside Table 8 range by > 2× → query the test before use.

## References
[1] Hoek, E. (2007). Practical Rock Engineering, ch. 11 "Rock mass properties". Rocscience. https://www.rocscience.com/assets/resources/learning/hoek/Practical-Rock-Engineering-Chapter-11-Rock-Mass-Properties.pdf — [V] eq. 26 p. 23, Table 8 p. 24, p. 25, p. 4, Fig. 12 p. 29
[2] Hoek, E. (2023). Practical Rock Engineering, ch. 3 "Intact rock strength". Rocscience. https://static.rocscience.cloud/assets/resources/learning/hoek/3.-Intact-rock-strength_2023-06-30-120556_xiuv.pdf — [V] p. 16 (Ei definition), Fig. 18 p. 17
[3] Gercek, H. (2007). Poisson's ratio values for rocks. IJRMMS 44(1), 1–13. https://doi.org/10.1016/j.ijrmms.2006.04.011 — [U] (bibliography [V] via Crossref)
[4] ISRM (1979). Suggested methods for determining the uniaxial compressive strength and deformability of rock materials. IJRMMS 16(2), 135–140. https://doi.org/10.1016/0148-9062(79)91451-7 — [U]
[5] ISRM (1983). Suggested methods for determining the strength of rock materials in triaxial compression: revised version (Kovari et al.). IJRMMS 20(6), 285–290. https://doi.org/10.1016/0148-9062(83)90598-3 — [U]
[6] ASTM D7012-23. Standard test methods for compressive strength and elastic moduli of intact rock core specimens under varying states of stress and temperatures. https://store.astm.org/d7012-23.html — [V] status, Methods A–D
[7] Hoek, E. & Diederichs, M.S. (2006). Empirical estimation of rock mass modulus. IJRMMS 43(2), 203–215. https://doi.org/10.1016/j.ijrmms.2005.06.005 — [U] (MR table [V] via [1])
[8] Aladejare, A.E. & Wang, Y. (2017). Evaluation of rock property variability. Georisk 11(1), 22–41. https://doi.org/10.1080/17499518.2016.1207784 — [U]
[9] Ulusay, R. & Hudson, J.A. (eds) (2007). The complete ISRM suggested methods for rock characterization, testing and monitoring: 1974–2006. ISRM, Ankara. — [U]
[10] EN 14580:2005. Natural stone test methods — Determination of static elastic modulus. CEN. — [V] title/status via standards shop
