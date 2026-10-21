# 16 — GSI and disturbance

| | |
|---|---|
| **Parameters** | GSI (Geological Strength Index), D (disturbance factor), RQD (Rock Quality Designation), JCond89 (joint condition rating, Bieniawski 1989) |
| **Material** | Rock |
| **Constitutive models that use it** | Generalized Hoek-Brown (HB2002); equivalent MC through HB; rock mass modulus (HD2006); residual HB (Cai 2007) |
| **Depends on** | [13-intact-rock-strength](13-intact-rock-strength.md) (context only), [22-discontinuity-shear-strength](22-discontinuity-shear-strength.md) |
| **Feeds** | [17-rock-mass-strength](17-rock-mass-strength.md), [18-rock-mass-modulus](18-rock-mass-modulus.md), [19-post-peak-rock-mass](19-post-peak-rock-mass.md), [09-dilatancy](09-dilatancy.md) |

## 1. Phenomenon
GSI rates how much a jointed rock mass is weaker and softer than intact rock, from two observations: blockiness
(interlocking of blocks) and discontinuity surface condition [1][2]. It applies only where the joints are closely
spaced compared with the structure, so the mass behaves as homogeneous and isotropic. Where block size is comparable
to the opening, or one joint set dominates, the mass should be analyzed as discrete blocks, not by GSI [2][3].
GSI is not meant for massive rock that fails by stress-induced spalling [3][4]. D (0 to 1) reduces mb, s and Erm
for blast damage and stress relaxation. It applies only to the damaged zone next to the excavation face, never to
the whole rock mass [2][4]. RQD and JCond89 are the two logged indices that quantify GSI [3].

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| GSI | – (0–100) | – | – |
| D | – (0–1) | – | – |
| RQD | % (of core-run length) | % | – (100 mm = 4 in. piece threshold [3]) |
| JCond89 | – (rating 0–30) | – | – |
| Jv (volumetric joint count) | joints/m³ | joints/yd³ | 1 joint/m³ = 0.7646 joints/yd³ _(computed)_ |
| λ (fracture frequency) | 1/m | 1/ft | 1 /m = 0.3048 /ft |

## 3. Typical values

| Material / case | Range | Source |
|---|---|---|
| GSI chart span (blocky masses) | ≈ 5–100. Top row (intact/massive) and bottom row (laminated/sheared) dropped in the quantified chart | [1], [3] Fig. 5 [V] |
| Flysch / heterogeneous sediments, chart types A–H | A–B (sandstone-dominated) high; G–H (sheared clayey shale) low. Read from Marinos & Hoek chart | [5] Table 3 [V] |
| D by excavation method | 0 (TBM, excellent controlled blasting, mechanical excavation in poor rock) to 0.8 (very poor blasting in a hard-rock tunnel) for tunnels; 0.7–1.0 for slopes and open pits, with blasting quality; guidelines by case in [6] Table 1 | [6] Table 1 [V]; [2] Table 7 [V]; [4] Table 2 [V] |
| RQD classes (Deere) | <25 very poor; 25–50 poor; 50–75 fair; 75–90 good; 90–100 excellent | [7] [U] |
| JCond89 | 0–30. 30 = very rough, not continuous, no separation, unweathered [V]; 0 = soft gouge or separation > 5 mm, continuous [U] | [8] via [3] App. 1 Table 1 |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| RQD on rock core | D6032/D6032M-17 [U: edition] | ISO 14689:2017 (core description) [U]; ISRM 1978 SM, quantitative description of discontinuities [9] [U] | CORE: CORE_RQD, CORE_PREC (TCR), CORE_SREC (SCR), CORE_DIAM | RQD per run (pieces ≥ 100 mm, ≥ NW/NX core, double-tube barrel [3] [V]) |
| Fracture frequency / spacing | – | ISRM 1978 SM [9] [U] | FRAC: FRAC_FI, FRAC_IAVE, FRAC_IMIN, FRAC_IMAX, FRAC_SET | λ → RQD (Priest & Hudson); spacing |
| Discontinuity logging (JCond89 inputs) | – | ISO 14689:2017 [U]; ISRM 1978 SM [9] [U] | DISC: DISC_PERS, DISC_APT, DISC_RGH, DISC_PLAN, DISC_JRC, DISC_INFM, DISC_WETH, DISC_TYPE | Persistence, aperture, roughness, infill, weathering → JCond89 rating |
| Rock mass classification | D5878 (guide to rock mass classification systems) [U: edition] | – | **No GSI / RMR / JCond89 heading in AGS 4.2** (checked) | GSI, RMR89; carry in a user-defined group or project config |
| D | no test; judgement from excavation method and observed damage | – | none | D per zone |

## 5. Derivations and correlations

### 5.1 Quantified GSI from JCond89 and RQD — Hoek, Carter & Diederichs (2013)
$$\mathrm{GSI} = 1.5\,J_{Cond89} + \mathrm{RQD}/2$$
- **Inputs:** JCond89 (0–30), RQD (%).
- **Valid for:** jointed, blocky masses only. The intact/massive top row and the sheared/laminated bottom row of the
  chart are excluded. Not for spalling or structurally controlled failure [3].
- **Scatter:** checked against one data set only (mapped GSI in a drill-and-blast tunnel), "reasonably close" to
  1:1. Published as *proposed*, not *recommended* [3]. Later studies report it under-predicts for poor (GSI < 45)
  and over-predicts for good (GSI > 65) masses [14] [U].
- **Source:** [3], eq. (1), Fig. 5 [V]

### 5.2 Alternative joint-condition scales — Hoek et al. (2013)
$$\mathrm{GSI} = 2\,J_{Cond76} + \mathrm{RQD}/2 \quad (J_{Cond89}=1.3\,J_{Cond76})$$
$$J_{Cond89} = 35\,\frac{J_r/J_a}{1+J_r/J_a} \;\Rightarrow\; \mathrm{GSI} \approx 52\,\frac{J_r/J_a}{1+J_r/J_a} + \mathrm{RQD}/2$$
- **Inputs:** JCond76 (Bieniawski 1976) or the Q-system Jr, Ja.
- **Scatter:** the Jr/Ja form fits the mapped GSI less well than eq. (1) but is "acceptable" [3].
- **Source:** [3], eq. (2) [V]. Eq. (3): the substitution is [V]. The printed coefficient (52 vs 1.5 × 35 = 52.5) is [U].

### 5.3 GSI from RMR
$$\mathrm{GSI} = \mathrm{RMR}_{76}\ (\text{pre-1990 data}),\qquad \mathrm{GSI} = \mathrm{RMR}_{89} - 5\ (\text{post-1990})$$
- **Inputs:** RMR with groundwater rating set dry (10 in RMR76, 15 in RMR89) and joint-orientation adjustment 0 [2].
- **Valid for:** RMR > ~23 (RMR76) / > ~18 (RMR89) per Hoek & Brown 1997 [10] [U]. Hoek now advises estimating
  GSI directly from the charts, because the RMR route "has proved to be unreliable" for poor masses [2] [V].
- **Source:** [11] p. 206 (citing [10]) [V]. [2] ch. 11, "Geological strength Index" [V].

### 5.4 RQD from fracture frequency or Jv
$$\mathrm{RQD} = 100\,e^{-0.1\lambda}(0.1\lambda+1)\ \text{(Priest \& Hudson 1976)}$$
$$\mathrm{RQD} = 115 - 3.3\,J_v\ \text{(Palmström 1982)},\qquad \mathrm{RQD} = 110 - 2.5\,J_v\ \text{(Palmström 2005)}$$
- **Inputs:** λ = discontinuities per m along a scanline/core. Jv = joints per m³.
- **Valid for:** RQD clipped to 0–100. Palmström (2005) gives the second form as an improvement on the first [3].
- **Source:** [3] eqs. (4)–(6) [V]. The Priest-Hudson form is confirmed with threshold t = 0.1 m in [12], footnote 1 [V].

### 5.5 Heterogeneous rock masses (flysch, interbedded strong/weak) — Marinos & Hoek (2001)
- GSI is read from the flysch chart (types A–H, by the proportion of strong to weak beds and the degree of
  tectonic disturbance) [5] Table 3 [V].
- Intact σci and mi are a weighted mix of the two rock types. A–B: sandstone values. C: sandstone values reduced
  20 %, full siltstone values. D, E: sandstone reduced 40 %. F: reduced 60 %. G–H: siltstone/shale values only [5]
  Table 4 [V].
- An extended chart was published by V. Marinos (2017, 2019) [13] [U]. Using these charts for interbedded
  **shale–limestone** is by analogy (limestone in place of sandstone). _[Judgment — for review]_

### 5.6 Disturbance factor D — Hoek, Carranza-Torres & Corkum (2002)
- D enters $m_b = m_i\exp[(\mathrm{GSI}-100)/(28-14D)]$ and $s=\exp[(\mathrm{GSI}-100)/(9-3D)]$ ([6] eqs. 3–4
  [V]), and Erm (sheet 18).
- Guidance values are in §3 ([6] Table 1 [V]). Hoek's caution: "the factor D applies only to the blast damaged
  zone and it should not be applied to the entire rock mass". In tunnels this is a 1–2 m zone, to be modeled as a
  separate weaker material ([2] ch. 11, after eqs. 11–13 [V]). The 2018 edition repeats it in its Table 2 heading:
  D "should never be applied to the entire rock mass", and gives examples of 2–3 m damaged zones with D grading
  linearly to 0 [4] §8 [V].
- **TBM tunnels:** D = 0 [6] Table 1 [V]; [4] Table 2 [V].

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| HB strength (mb, s, a, σcm) | exponentially through mb, s | **High.** s rises × ≈ 3 per +10 GSI (s = e^(ΔGSI/9)). Global strength σcm/σci goes 0.14 → 0.22 for GSI 40 → 60 (mi 10, D 0, computed) |
| Equivalent MC c′, φ′ (tunnel FE) | via mb, s, a | Moderate for φ′, high for c′. Worked example σci 50 MPa, mi 10, H 100 m: GSI 40/45/50 → c′ 0.51/0.58/0.67 MPa, φ′ 45.7/47.2/48.5° (computed with HB2002 eqs.) |
| Rock mass modulus Erm → convergence, lining loads | sigmoid in GSI (sheet 18) | **High.** Simplified HD2006 Erm × ≈ 2.3 for GSI 40 → 50 (3.99 → 9.34 GPa, computed) |
| Plastic zone / convergence-confinement | through σcm and Erm together | **High.** Lower GSI gives both lower strength and lower stiffness, which compound |
| D in the damaged zone | reduces mb, s, Erm | High within the zone. Applied wrongly to the whole mass it gives "extremely conservative" results [4] |
| Residual strength (sheet 19) | GSIr = f(GSI) | Low for GSI > 60 (GSIr flattens at ≈ 27) |

**Typical variability:** an experienced geologist's GSI is about ±5 at 90 % confidence (SD ≈ 2.5) for a given
description ([2] ch. 11, Fig. 11 text [V]). That is a COV of ≈ 10 % at GSI 25 and ≈ 5 % at GSI 50 (computed from
SD 2.5). Cai et al. (2004) got GSI COV 2–3.2 % by point-estimate propagation of block-volume and joint-condition
uncertainty [12] §"Application", Table 6 text [V]. That is the propagated *input* uncertainty only, not the scatter between observers or
the spatial variability. Treat GSI as a distribution, with the same statistics as intact properties [4] §11 [V].
The transformation error of eq. 5.1 (RQD, JCond89 → GSI) adds to this. RQD and JCond89 themselves scatter
significantly [14] [U]. _[Judgment — for review: use SD 3–5 for GSI unless site data justify less]_

## 7. Pitfalls and QA checks
- Do not use GSI/HB where block size ≈ opening size or one joint set dominates. Use block/wedge analysis [2][3].
- Massive, sparsely jointed rock (GSI > ~65 under high stress) may need modified HB parameters [4] §5 [V].
- RQD depends on direction and on handling and drilling breaks. Exclude mechanical breaks. Core-run RQD averaged
  over a stratum hides weak seams.
- JCond89 = 15 (mid-range) assumed for lack of data gives GSI = 22.5 + RQD/2. State this, and test JCond89 ± 5
  (GSI ± 7.5). _[Judgment — for review]_
- Estimate GSI on undamaged faces. Blast-damaged faces understate it [2].
- Apply D only to a damaged ring (1–3 m), never to the whole model. D = 0 for TBM and road-header [4][6].
- GSI = RMR89 − 5 only with groundwater = 15 and orientation adjustment = 0.
- Interbedded strong/weak rock: use the heterogeneous chart and weighted σci, mi. Do not use the strong layer's
  properties alone [5].
- AGS 4.2 has no GSI/RMR/JCond89 headings. Record how these were derived in method remarks.

## References
[1] Hoek, E., Marinos, P. (2000). Predicting tunnel squeezing. Tunnels and Tunnelling International, Nov–Dec 2000. — [U] (cited in [3], [4])
[2] Hoek, E. (2007). Practical Rock Engineering, ch. 11 "Rock mass properties". RocScience. https://www.rocscience.com/assets/resources/learning/hoek/Practical-Rock-Engineering-Chapter-11-Rock-Mass-Properties.pdf — [V] GSI/RMR text, D caution, Table 7, GSI ±5 text
[3] Hoek, E., Carter, T.G., Diederichs, M.S. (2013). Quantification of the Geological Strength Index chart. ARMA 13-672, 47th US Rock Mech. Symp., San Francisco. https://www.rocscience.com/assets/resources/learning/hoek/2013-Quantification-of-the-GSI-Chart.pdf — [V] eqs. (1), (2), (4)–(6), App. 1 RQD definition and JCond89 table
[4] Hoek, E., Brown, E.T. (2019). The Hoek-Brown failure criterion and GSI – 2018 edition. J. Rock Mech. Geotech. Eng. 11(3), 445–463. https://doi.org/10.1016/j.jrmge.2018.08.001 — [V] §5, §6, §8, Table 2 heading, §11
[5] Marinos, P., Hoek, E. (2001). Estimating the geotechnical properties of heterogeneous rock masses such as flysch. Bull. Eng. Geol. Env. 60, 85–92. https://doi.org/10.1007/s100640000090 — [V] Table 3 (chart), Table 4 (weighting) in the rocscience reprint
[6] Hoek, E., Carranza-Torres, C., Corkum, B. (2002). Hoek-Brown failure criterion – 2002 edition. Proc. NARMS-TAC, Toronto, 1, 267–273. https://www.eoas.ubc.ca/courses/eosc433/lecture-material/2002-HoekBrownCriterion.pdf — [V] eqs. 3–5, Table 1
[7] Deere, D.U., Deere, D.W. (1988). The rock quality designation (RQD) index in practice. ASTM STP 984, 91–101. — [U]
[8] Bieniawski, Z.T. (1989). Engineering Rock Mass Classifications. Wiley, New York. — [V] JCond89 table as reproduced in [3] App. 1
[9] ISRM (1978). Suggested methods for the quantitative description of discontinuities in rock masses. Int. J. Rock Mech. Min. Sci. 15(6), 319–368. — [U]
[10] Hoek, E., Brown, E.T. (1997). Practical estimates of rock mass strength. Int. J. Rock Mech. Min. Sci. 34(8), 1165–1186. — [U] (GSI–RMR validity limits)
[11] Hoek, E., Diederichs, M.S. (2006). Empirical estimation of rock mass modulus. Int. J. Rock Mech. Min. Sci. 43, 203–215. https://doi.org/10.1016/j.ijrmms.2005.06.005 — [V] p. 206 GSI–RMR relations
[12] Cai, M., Kaiser, P.K., Uno, H., Tasaka, Y., Minami, M. (2004). Estimation of rock mass deformation modulus and strength of jointed hard rock masses using the GSI system. Int. J. Rock Mech. Min. Sci. 41(1), 3–19. — [V] GSI COV 2–3.2 %, RQD–λ footnote
[13] Marinos, V. (2019). A revised, geotechnical classification GSI system for tectonically disturbed heterogeneous rock masses, such as flysch. Bull. Eng. Geol. Env. 78, 899–912. — [U]
[14] Secondary reports of eq. 5.1 bias and RQD/JCond89 scatter: Springer Geotech. Geol. Eng. 2017 (s10706-017-0279-8) and Bull. Eng. Geol. Env. 2020 (s10064-020-01739-5), as summarized in search results only. — [U]
