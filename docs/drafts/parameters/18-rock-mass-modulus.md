# 18 — Rock mass modulus

| | |
|---|---|
| **Parameters** | Em / Erm (rock mass deformation modulus) |
| **Material** | Rock |
| **Constitutive models that use it** | Linear elastic part of HB and MC rock mass models; elastic-plastic / strain-softening HB in FE and convergence-confinement |
| **Depends on** | [14-intact-rock-deformability](14-intact-rock-deformability.md) (Ei), [13-intact-rock-strength](13-intact-rock-strength.md) (σci for the MR route), [16-gsi-and-disturbance](16-gsi-and-disturbance.md) (GSI, D) |
| **Feeds** | [17-rock-mass-strength](17-rock-mass-strength.md) (shares GSI, D), [19-post-peak-rock-mass](19-post-peak-rock-mass.md) (convergence), [20-in-situ-stress-rock](20-in-situ-stress-rock.md) (overcoring interpretation uses E) |

## 1. Phenomenon
Joints make a rock mass much more deformable than intact rock. Closure and shear on joints add to the elastic
strain of the blocks, so Em falls steeply with GSI from about Ei (massive rock) to a few percent of Ei
(disintegrated rock) [1]. Em also depends on scale. A test must load a volume large enough to contain the joint
fabric, so small borehole tests in jointed hard rock scatter widely [1]. Blast damage and stress relaxation near
the excavation lower Em further. D captures this, but only within the damaged zone [1][2]. HD2006 values are an
isotropic, upper-bound-type estimate for confined, undisturbed rock (D = 0). Bedded or foliated rock is
anisotropic [1].

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| Em, Ei | GPa (HD2006 works in MPa) | ksi | 1 GPa = 145.04 ksi; 1 MPa = 0.14504 ksi = 145.04 psi |
| MR = Ei/σci | – | – | – |

## 3. Typical values
Computed with HD2006 (D = 0 unless stated). Illustrative only.

| GSI | Erm/Ei, generalized (D = 0) | Erm/Ei, generalized (D = 1) | Erm simplified, D = 0 | Source |
|---|---|---|---|---|
| 30 | 0.081 | 0.028 | 1.6 GPa (239 ksi) | computed, [1] eqs. (2), (4) |
| 50 | 0.307 | 0.067 | 9.3 GPa (1355 ksi) | computed |
| 70 | 0.733 | 0.214 | 38.8 GPa (5631 ksi) | computed |

| Case | Range | Source |
|---|---|---|
| HD2006 database | 494 in situ tests (China 457, Taiwan 37). Plate 423, flat jack 53, back-analysis 18. GSI 0–100, most data GSI 40–80 | [1] Table 2 [V] |
| MR = Ei/σci | ~100–1000 by rock type [U: overall span]; e.g. tuff 200–400, agglomerate 400–600 [V] | [1] Table 3; [2] Table 8 |
| TBM vs blasted tunnels, GSI 50–70 | measured Em 2–3 × higher for TBM (D = 0) than blasted (D = 0.5–1) | [1] p. 209, citing Palmström & Singh [V] |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Flexible borehole dilatometer (rock) | D4719-20 covers prebored pressuremeter **in soils** and excludes high-pressure testing in rock [V] | ISRM SM flexible dilatometer (1987) [7] [V]; ISO 22476-5:2012 flexible dilatometer (2023 edition retitled "prebored pressuremeter") [V, listings] | PMTG: PMTG_TYPE (e.g. HPD high-pressure dilatometer), PMTG_DIAM, PMTG_GI, PMTG_METH. PMTL: PMTL_GAA (unload/reload G). PMTP: PMTP_GI. PMTD (raw data) | Load and unload–reload modulus of a ~1 m test section |
| Borehole jack (Goodman jack) | D4971-16, **withdrawn 2025** [V, listings] | ISO 22476-7:2012 borehole jack [V, listings] | PMTG / PMTP (no dedicated group) [checked] | Directional modulus. Needs correction factors [U] |
| Plate loading (rigid / flexible) in adit | D4394-17 (rigid), D4395-17 (flexible) [V, listings] | ISRM SM in situ deformability (1979) [U] | PLTG: PLTG_EMOD, PLTG_PDIA, PLTG_CYC, PLTG_METH (group oriented to DIN 18134 surface tests) | Em of a ~1 m³ volume. Measure displacement at depth with an extensometer [1] |
| Flat jack | D4729 [U: edition] | ISRM SM large flat jack (1986) [U] | none [checked] | Em, stress |
| Radial jacking | D4506-21 [V, listings] | – | none | Em of a tunnel-scale volume |
| Intact Ei (lab) | D7012 [U: edition] | ISRM SM UCS/deformability (1979/2007) [U] | RUCS: RUCS_ETAN, RUCS_ESEC, RUCS_EAVG | Ei for 5.1 (sheet 14) |

## 5. Derivations and correlations

### 5.1 Generalized Hoek & Diederichs (2006)
$$E_{rm}=E_i\left(0.02+\frac{1-D/2}{1+e^{(60+15D-\mathrm{GSI})/11}}\right)$$
- **Inputs:** Ei (MPa or GPa), GSI, D. If Ei is not measured: Ei = MR·σci ([1] eq. (3), Table 3).
- **Valid for:** isotropic masses. The 0.02 term is the modulus of fully broken rock (GSI = 0). Use where reliable
  Ei or σci data exist [1].
- **Scatter:** fitted to site-average data. Excellent agreement with averages at D = 0.5 [1] Fig. 12 [V]. Lab Ei
  can be reduced up to 50 % by core damage, and is less reliable than σci [1] [V].
- **Source:** [1] eq. (4), p. 209 [V]. Same as [3] eq. (9) [V].

### 5.2 Simplified Hoek & Diederichs (2006)
$$E_{rm}\,(\mathrm{MPa})=100\,000\,\frac{1-D/2}{1+e^{(75+25D-\mathrm{GSI})/11}}$$
- **Inputs:** GSI, D.
- **Valid for:** when no reliable intact data exist. The D = 0 curve is a "reliable upper bound" [1].
- **Scatter:** the D = 0 and D = 1 curves bound >90 % of the 494 data points. D = 0.5 is the average [1] p. 208 [V].
  Test errors are large near GSI 90–100 (deformations near instrument resolution) [1].
- **Source:** [1] eq. (2), p. 208 [V]. Same as [3] eq. (10) [V].

### 5.3 Hoek, Carranza-Torres & Corkum (2002)
$$E_m\,(\mathrm{GPa})=\left(1-\frac D2\right)\sqrt{\frac{\sigma_{ci}}{100}}\;10^{(\mathrm{GSI}-10)/40}$$
- **Inputs:** σci (MPa) ≤ 100 MPa. For σci > 100 MPa the √ term is dropped (Hoek & Brown 1997) [U].
- **Note:** superseded by 5.1 and 5.2. At GSI > ~70 it overestimates (no upper limit).
- **Source:** [4] eq. 11 [V]. Listed in [1] Table 1 [V].

### 5.4 Serafim & Pereira (1983); Bieniawski (1978)
$$E_m\,(\mathrm{GPa})=10^{(\mathrm{RMR}-10)/40}\quad\text{(Serafim \& Pereira)},\qquad E_m\,(\mathrm{GPa})=2\,\mathrm{RMR}-100\quad\text{(Bieniawski)}$$
- **Valid for:** Bieniawski: RMR > ~50 (gives ≤ 0 below RMR 50) [U]. Serafim & Pereira: mainly dam foundations,
  RMR76 [U]. The data sets [5][6] fit the HD2006 D = 0 curve [1] Fig. 10 [V].
- **Source:** [1] Table 1 [V] (as reproduced). Primary sources [5], [6] [U] for locators.

### 5.5 In situ tests and scale
- HD2006 found "down-hole jacks and borehole pressure meters" the least reliable data. They are hard to
  interpret in hard jointed rock, where the stressed volume is "obviously too small", and their scatter follows "no
  logical pattern". HD2006 excluded them [1] p. 206 [V].
- Plate tests: measure at depth with a multi-point extensometer. Plate-face displacements include plate bending,
  gap closure and blast-damaged rock [1] §2 [V]. Distinguish the initial tangent, elastic (unload–reload) and
  secant deformation moduli [1] Fig. 4.
- Dilatometer and Goodman-jack Em are local, section-scale values (≈ borehole diameter × 1 m). Use them as a check
  on, or a lower bound for, the GSI-based mass Em, not as a direct replacement. Expect a scale ratio that depends on
  joint spacing relative to the test volume. _[Judgment — for review]_
- Cai et al. (2004): GSI-based E vs 29 plate tests agreed in mean and spread for most zones, but overestimated one
  (CH) zone by ~29 % [8] [V].

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Tunnel FE (HB or MC) | elastic stiffness of the mass. ν usually 0.25–0.3 | **High** for displacements and convergence (∝ 1/Em in the elastic part). Low for stresses in a homogeneous elastic mass |
| Convergence-confinement (closed form) | elastic radial displacement u = p0 a (1+ν)/E before yield, and scales the plastic displacement | **High**. Halving Em roughly doubles convergence for a given plastic radius |
| Support / lining loads (GRC–SCC intersection) | stiffer ground takes more load before contact | Moderate. Lining load falls as Em falls relative to the lining stiffness |
| Surface settlement (shallow tunnels) | volume loss through Em and plastic zone | Moderate–high |
| Overcoring stress interpretation (sheet 20) | stress = strain × E | **High** (linear) |
| GSI → Em | sigmoid. Steepest near GSI = 60 (gen.) / 75 (simp.) at D = 0 | ≈ ×2.3 per +10 GSI at GSI 40–50 (simplified, computed) |

**Typical variability:** Em prediction error is large. Individual measurements scatter roughly between the D = 0
and D = 1 curves, a factor of ≈ 13–19 at GSI 40–70 in the simplified eq. and ≈ 3.4–4.6 in the generalized eq.
(computed) [1] Figs. 9, 13. In situ plate
test data at one site and zone commonly scatter with COV of tens of percent [8] Table 6 [U: COV not computed].
Inherent spatial variability (joint spacing, weathering) and transformation error (GSI → Em) are separate. HD2006
shows the transformation error as error ratios against GSI [1] eq. (5), Fig. 13. _[Judgment — for review:
carry Em as a range (D = 0 to D = 0.5 curves) rather than a single value]_

## 7. Pitfalls and QA checks
- HD2006 eq. (2) returns **MPa**. Eq. (4) returns the units of Ei. HB2002 eq. 11 returns **GPa**.
- The equation numbers in HD2006 are (2) simplified and (4) generalized. HB2019 renumbers them (10) and (9).
- Lab Ei on damaged core is too low. Prefer MR·σci, or the simplified eq., when Ei looks low against Table 3 MR.
- Anisotropic shale: Ei and MR depend on loading direction relative to bedding [2] Table 8 note.
- D only in the damaged ring. TBM: D = 0. Do not take an average D = 0.5 for the whole mass.
- Report which modulus a field test gives (loading, unload–reload, secant), and at what stress level.
- Use upper-bound (D = 0) values for confined deep tunnels [1] §8 [V]. Check against any dilatometer data.

## References
[1] Hoek, E., Diederichs, M.S. (2006). Empirical estimation of rock mass modulus. Int. J. Rock Mech. Min. Sci. 43, 203–215. https://doi.org/10.1016/j.ijrmms.2005.06.005 (reprint: https://www.rocscience.com/assets/resources/learning/hoek/2006-Hoek-and-Diederichs-estimating-rock-mass-modulus.pdf) — [V] eqs. (1)–(5), Tables 1–3, §2, §4, §5, §8
[2] Hoek, E. (2007). Practical Rock Engineering, ch. 11 "Rock mass properties". https://www.rocscience.com/assets/resources/learning/hoek/Practical-Rock-Engineering-Chapter-11-Rock-Mass-Properties.pdf — [V] Table 8 notes, D caution
[3] Hoek, E., Brown, E.T. (2019). The Hoek-Brown failure criterion and GSI – 2018 edition. J. Rock Mech. Geotech. Eng. 11(3), 445–463. https://doi.org/10.1016/j.jrmge.2018.08.001 — [V] §7 eqs. (9), (10)
[4] Hoek, E., Carranza-Torres, C., Corkum, B. (2002). Hoek-Brown failure criterion – 2002 edition. Proc. NARMS-TAC, 267–273. https://www.eoas.ubc.ca/courses/eosc433/lecture-material/2002-HoekBrownCriterion.pdf — [V] eq. 11
[5] Serafim, J.L., Pereira, J.P. (1983). Considerations of the geomechanics classification of Bieniawski. Proc. Int. Symp. Eng. Geol. Underground Construction, Lisbon, 1(II), 33–44. — [V] bibliographic data via [1]; [U] content
[6] Bieniawski, Z.T. (1978). Determining rock mass deformability – experience from case histories. Int. J. Rock Mech. Min. Sci. 15(5), 237–247. — [V] bibliographic data via [3]; [U] content
[7] ISRM Commission on Testing Methods (Ladanyi, B., coord.) (1987). Suggested methods for deformability determination using a flexible dilatometer. Int. J. Rock Mech. Min. Sci. 24(2), 123–134. — [V] citation via Springer reference-work listing; [U] content
[8] Cai, M., Kaiser, P.K., Uno, H., Tasaka, Y., Minami, M. (2004). Estimation of rock mass deformation modulus and strength of jointed hard rock masses using the GSI system. Int. J. Rock Mech. Min. Sci. 41(1), 3–19. — [V] 29 plate tests, CH zone +29 %
[9] ASTM D4394-17, D4395-17, D4506-21, D4719-20, D4971-16 (withdrawn 2025); ISO 22476-5:2012, ISO 22476-7:2012. — [V] designations and status via standards-catalogue listings (ASTM site not reachable)
