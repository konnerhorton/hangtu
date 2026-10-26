# 08 — Elastic stiffness of soil

Promoted to the docs site as [`docs/site/parameters/08-elastic-stiffness-soil.md`](../../site/parameters/08-elastic-stiffness-soil.md) (M13 b3); the page is current where they differ.

| | |
|---|---|
| **Parameters** | E (Young's modulus, drained E′ or undrained Eu; MC input), ν (Poisson's ratio, ν′ or νu) |
| **Material** | Soil |
| **Constitutive models that use it** | Linear elastic, MC (E, ν); HS/HS-small use Eur, νur instead (sheet 11) |
| **Depends on** | [01-unit-weight-and-vertical-stress](01-unit-weight-and-vertical-stress.md), [02-index-properties](02-index-properties.md), [05-undrained-shear-strength](05-undrained-shear-strength.md), [06-preconsolidation-and-compressibility](06-preconsolidation-and-compressibility.md), [10-small-strain-stiffness](10-small-strain-stiffness.md) |
| **Feeds** | [07-at-rest-earth-pressure](07-at-rest-earth-pressure.md) (ν–K0 check), [11-hardening-soil-stiffness](11-hardening-soil-stiffness.md) |

## 1. Phenomenon
Soil is not linear elastic: its secant stiffness falls by one to two orders of magnitude from very small strains
(G0, sheet 10) to failure, and rises with mean effective stress. A single E for the Mohr-Coulomb model is a secant
value that only applies at one strain level, stress level and stress path. Primary loading needs about E50;
unloading problems such as tunneling and excavations need an unload-reload modulus Eur [3, §3.3.1]. Drained (E′, ν′)
and undrained (Eu, νu → 0.5) parameters describe the same skeleton: the shear modulus G is the same in both, and
undrained behavior comes from the pore water stopping volume change. ν′ is low (0.1–0.2) at small strain and in
unloading, and rises toward 0.3–0.4 when chosen to match K0 in 1-D loading [3, §3.3.2][4, §8.9.2].

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| E, G, Eu | kPa, MPa | psf, ksf, tsf, psi, ksi | 1 tsf = 95.76 kPa = 2.0 ksf; 1 ksf = 47.88 kPa; 1 ksi = 6 894.76 kPa; 1 MPa = 20.885 ksf = 145.04 psi = 10.443 tsf |
| ν | – | – | – |

**Unit trap.** FHWA NHI-06-088 Table 5-16 gives Es = 4, 7, 10, 12 × N1,60 in **tsf** [2]. Read as **ksf**,
the same factors halve E. Correct factors (computed):

| Soil (AASHTO / FHWA wording) | tsf per blow | ksf per blow | ksi per blow | MPa per blow | MPa if wrongly read as ksf |
|---|---|---|---|---|---|
| Silts, sandy silts, slightly cohesive mixtures | 4 | 8 | 0.0556 | 0.383 | 0.192 |
| Clean fine to medium sands, slightly silty sands | 7 | 14 | 0.0972 | 0.670 | 0.335 |
| Coarse sands, sands with little gravel | 10 | 20 | 0.1389 | 0.958 | 0.479 |
| Sandy gravel and gravels | 12 | 24 | 0.1667 | 1.149 | 0.575 |

The ksi column matches AASHTO (2014) [1] as given in GEC 5 Table 8-11 (0.056, 0.097, 0.139, 0.167 ksi) [4].

## 3. Typical values

| Material | Range E (tsf) | E (MPa, computed) | ν | Source |
|---|---|---|---|---|
| Clay, soft sensitive | 25–150 | 2.4–14.4 | 0.4–0.5 (undrained) | [2] Table 5-16 [V] |
| Clay, medium stiff to stiff | 150–500 | 14.4–47.9 | 0.4–0.5 (undrained) | [2] [V] |
| Clay, very stiff | 500–1000 | 47.9–95.8 | 0.4–0.5 (undrained) | [2] [V] |
| Loess | 150–600 | 14.4–57.5 | 0.1–0.3 | [2] [V] |
| Silt | 20–200 | 1.9–19.2 | 0.3–0.35 | [2] [V] |
| Fine sand, loose / medium / dense | 80–120 / 120–200 / 200–300 | 7.7–11.5 / 11.5–19.2 / 19.2–28.7 | 0.25 | [2] [V] |
| Sand, loose / medium / dense | 100–300 / 300–500 / 500–800 | 9.6–28.7 / 28.7–47.9 / 47.9–76.6 | 0.2–0.36 (loose), 0.3–0.4 (dense) | [2] [V] |
| Gravel, loose / medium / dense | 300–800 / 800–1000 / 1000–2000 | 28.7–76.6 / 76.6–95.8 / 95.8–191.5 | 0.2–0.35 (loose), 0.3–0.4 (dense) | [2] [V] |
| Drained ν′, coarse-grained, small strain | – | – | 0.1–0.2 | [4] §8.9.2 p. 8-26 [V] |
| ν′ for MC, 1-D loading (match K0) / unloading | – | – | 0.3–0.4 / 0.15–0.25 | [3] §3.3.2 p. 36 [V] |

The same ranges in ksi are in GEC 5 Table 8-10 [4] [V]. Rate of increase of E with depth for sands, nh: [2] Table 5-17.

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Triaxial CU / CD (local strain gauges for small strain) | D4767; D7181 | ISO 17892-9; BS 1377-8 | TREG/TRET: TRET_E50, TRET_EP50, TRET_DEVF, TRET_CONP | E50 (secant at 50 % qf), Eu (CU), Eur from loops (curves not in AGS 4.2) |
| Triaxial UU / unconfined | D2850; D2166/D2166M | ISO 17892-8, -7; BS 1377-7 | TRIG/TRIT: TRIT_DEVF, TRIT_STRN, TRIT_CU; LUCT: LUCT_UCS, LUCT_STRA | Eu (secant, disturbed: low) |
| Oedometer | D2435/D2435M | ISO 17892-5; BS 1377-5 | CONG/CONS: CONS_INMV, CONS_INCF | Eoed = 1/mv → E via ν (sheet 11) |
| Pressuremeter (pre-bored, self-boring) | D4719 | ISO 22476-4, -6 | PMTG/PMTP: PMTP_GI; PMTL: PMTL_GAA; PMMG/PMMC | G from first loading and from unload-reload loops |
| Flat dilatometer | D6635 | ISO 22476-11 | DMTG/DMTP: DMTP_ED, DMTP_VDM | ED, constrained modulus M |
| Plate load | D1196/D1196M | DIN 18134 (national) | PLTG: PLTG_EMOD, PLTG_EV2, PLTG_SMOD | E (EV2) under plate |
| CPT / SPT (correlation only) | D5778; D1586/D1586M | ISO 22476-1, -3 | SCPT; ISPT; CPTP: CPTP_E1, CPTP_M1 | qc, N → E (section 5) |
| Seismic (Vs) | D4428/D4428M; D7400/D7400M | – | ISTG/ISTA: ISTA_WVL | G0 → E0 (sheet 10) |

## 5. Derivations and correlations

### 5.1 E from SPT — AASHTO (2004/2014) via FHWA NHI-06-088
$$E_s\,[\text{tsf}] = C\,(N_1)_{60},\quad C = 4,\,7,\,10,\,12\ \text{(see section 2)};\qquad E_s\,[\text{tsf}] = 2\,q_c\,[\text{tsf}]\ \text{(sands)}$$
- **Inputs:** (N1)60 (blows/ft); qc (tsf)
- **Valid for:** silts to gravels as listed; preliminary estimates only [4, §8.9.1]
- **Scatter:** not given; GEC 5 says these are only approximate and Es/qc depends on many other factors [4]
- **Source:** [2] Table 5-16 p. 5-85 [V], "for preliminary design" (p. 5-83); ksi form [4] Table 8-11 p. 8-26 [V]
- **Also:** Kulhawy & Mayne (1990), EPRI EL-6800, Eqs. 5-26a–c, pp. 5-17 to 5-18 [V]: E/pa ≈ 5 N60 (sands with
  fines), 10 N60 (clean NC sands), 15 N60 (clean OC sands), "as a first order estimator". Built in M13 b3.

### 5.2 Eu from Su — Duncan & Buchignani (1976)
$$E_u = K\,S_u,\quad K = f(PI,\ OCR)$$

| OCR | PI < 30 | PI 30–50 | PI > 50 |
|---|---|---|---|
| < 3 | 600 | 300 | 125 |
| 3–5 | 400 | 200 | 75 |
| > 5 | 150 | 75 | 50 |

- **Inputs:** Su (kPa), PI (%), OCR (–)
- **Valid for:** saturated clays, undrained loading; secant modulus at an unstated strain level (likely moderate)
- **Scatter:** not given; K varies with strain level and stress level
- **Source:** [5] [U]. The original is a chart; the values above are the commonly reproduced table, not checked against
  the source. USACE EM 1110-1-1904 Fig. D-2 reproduces the chart as Kc vs PI and OCR [6] [U].

### 5.3 E from Vs with strain reduction — GEC 5 §8.9.2 (Burns & Mayne 1996 [8])
$$G_0=\rho V_s^2,\quad E_0 = 2G_0(1+\nu),\quad E_s = \left(\frac{E}{E_{max}}\right)2\rho V_s^2(1+\nu),\quad \frac{E}{E_0}=1-\left(\frac{q}{q_{ult}}\right)^{0.3}$$
- **Inputs:** Vs (m/s), ρ = γt/g (Mg/m³), ν (0.1–0.2 drained coarse soils), q/qult = 1/FOS
- **Valid for:** intact clays and uncemented sands under foundations; conservative in structured clays or cemented
  sands [4]. For tunnels, an alternative is E/E0 = G/G0 at the expected shear strain from a reduction curve (sheet 10,
  Hardin-Drnevich with γ0.7) _[Judgment — for review]_.
- **Scatter:** not given (first-order approximation)
- **Source:** [4] Eqs. 8.17, 8.18 and Fig. 8-15, pp. 8-25 to 8-27 [V]

### 5.4 Drained ↔ undrained elastic constants (isotropic elasticity, G unchanged)
$$E_u = \frac{2(1+\nu_u)}{2(1+\nu')}E' = \frac{3E'}{2(1+\nu')}\ (\nu_u = 0.5);\qquad G = \frac{E}{2(1+\nu)}$$
- Computed Eu/E′: ν′ = 0.2 → 1.25; 0.25 → 1.20; 0.3 → 1.15; 0.35 → 1.11. With νu = 0.495 the ratio is 1.495/(1+ν′)
  (≤ 0.4 % lower).
- νu = 0.5 makes the FE stiffness matrix singular; PLAXIS uses νu = 0.495 by default and needs ν′ < 0.35 for
  Undrained (A)/(B) [3, §2.4 p. 21; §3.3.2 p. 36] [V].
- **Source:** [3] §2.4 Eq. 2–49 (with Skempton B), §3.3.3 Eq. 3–12 [V]

### 5.5 ν from K0 in 1-D compression (elastic)
$$K_0 = \frac{\nu}{1-\nu}\quad\Leftrightarrow\quad \nu = \frac{K_0}{1+K_0}$$
- Computed: ν = 0.2, 0.25, 0.3, 0.35, 0.4 → K0 = 0.25, 0.33, 0.43, 0.54, 0.67. Cannot give K0 > 1 [3].
- **Source:** [3] §3.3.2 p. 36 [V]

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Tunnel FE, MC | Single E scales all elastic displacements; a stiff layer under the tunnel controls heave | High for displacement magnitude; MC gives troughs that are too wide and shallow, whatever E [3, §3.3.1] _[Judgment — for review]_ |
| Settlement / volume loss (empirical Gaussian) | Not used directly; volume loss is an input | Low |
| Face stability / support pressure (limit equilibrium) | Not used | Low (strength governs) |
| Lining loads (continuum or bedded beam) | Ground-lining stiffness ratio; subgrade reaction ks ∝ E/R | Moderate: bending moments rise with lining/ground flexibility ratio _[Judgment — for review]_ |
| Undrained short-term FE | Eu or E′ + ν′ with drainage type | Moderate; ν′ choice changes K0 at initialization in 1-D gravity loading |
| Shallow foundation settlement | s ∝ qB(1−ν²)/E | High (inversely proportional) |

**Typical variability:** inherent COV of in situ moduli (PMT, DMT) is commonly quoted as high, of order 20–60 %
_[Judgment — for review]_; Phoon & Kulhawy (1999a) tabulate PMT and DMT modulus COVs [7] [U]. The transformation
error of SPT- or Su-based E correlations is larger than the inherent COV: the tables give only ranges, often a factor of 2
or more [2][4].

## 7. Pitfalls and QA checks
- Check the unit of any E-from-N table: tsf vs ksf is a factor of 2.0 (section 2).
- Check that E matches the strain level: E0 from Vs is much larger than working-strain E; from the GEC 5 Fig. 8-15
  equation, E/E0 = 0.38 at q/qult = 0.2 and 0.19 at q/qult = 0.5 (computed) [4].
- Unloading (tunnel crown, invert, excavation base) needs Eur, not E50 [3].
- Using UU or unconfined Eu from disturbed samples underestimates stiffness; check against Vs-based E0 [4, §8.5.4].
- Eu from 5.2 and E′ from 5.1 are not interchangeable; convert with 5.4.
- ν′ ≥ 0.35 with an undrained (A)/(B) material: the skeleton is not compressible enough [3].
- Check ν against K0 (section 5.5) if gravity loading is used to set initial stresses.
- E from correlations increases with depth/stress; one E per thick layer hides this (use nh or HS).

## References
[1] AASHTO (2014). *LRFD Bridge Design Specifications*, 7th ed., Table C10.4.6.3-1. — [V] via [4] Tables 8-10, 8-11
(not seen in the original)
[2] FHWA (2006). *Soils and Foundations Reference Manual, Vol. I*, FHWA-NHI-06-088, Tables 5-16 and 5-17 (after
AASHTO 2004). — [V] via an extract of the source and its page image
[3] Bentley/Seequent (2025). *PLAXIS 2D 2025.1 Material Models Manual*, §2.4, §3.3 (pp. 19–37).
https://files.seequent.com/PLAXIS/Manuals/PLAXIS_2D/English/PLAXIS_2D_3_Material%20Models%20Manual.pdf — [V] text
and equations read
[4] Loehr, J.E., Lutenegger, A., Rosenblad, B.L., Boeckmann, A. (2016). *Geotechnical Site Characterization*, GEC 5,
FHWA-NHI-16-072, Ch. 8 (§8.9, Tables 8-10, 8-11, Eqs. 8.16–8.18, Fig. 8-15).
https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi16072.pdf — [V] pages 8-24 to 8-27 read
[5] Duncan, J.M., Buchignani, A.L. (1976). *An Engineering Manual for Settlement Studies*. Geotechnical Engineering
Report, Univ. of California, Berkeley. — [U] (K table not checked against the source)
[6] USACE (1990). *Settlement Analysis*, EM 1110-1-1904, Appendix D, Fig. D-2. — [U]
[7] Phoon, K.K., Kulhawy, F.H. (1999a). Characterization of geotechnical variability. *Can. Geotech. J.* 36(4),
612–624. https://doi.org/10.1139/t99-038 — [U] (COV values not read)
[8] Burns, S.E., Mayne, P.W. (1996). Small- and high-strain measurements of in situ soil properties using the seismic
cone penetrometer. *Transp. Res. Rec.* 1548, 81–88. — [U] (cited via [4])
